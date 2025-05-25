from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    auto_generated = fields.Boolean(
        string='Tự động tạo',
        copy=False,
        help='Đơn mua được tạo tự động từ đơn bán',
    )
    auto_sale_order_id = fields.Many2one(
        'sale.order',
        string='Đơn bán gốc',
        copy=False,
        readonly=True,
    )
    has_intercompany_so = fields.Boolean(
        string='Có đơn bán liên công ty',
        compute='_compute_has_intercompany_so',
        store=True,
        help='Chỉ ra rằng đơn mua này đã sinh ra đơn bán liên công ty',
    )
    intercompany_sale_order_id = fields.Many2one(
        'sale.order',
        string='Đơn bán liên công ty',
        copy=False,
        readonly=True,
        help='Đơn bán được tạo từ đơn mua này',
    )

    @api.depends('intercompany_sale_order_id')
    def _compute_has_intercompany_so(self):
        for order in self:
            order.has_intercompany_so = bool(order.intercompany_sale_order_id)

    def button_confirm(self):
        """Khi xác nhận đơn mua, tạo đơn bán liên công ty nếu cần"""
        for po in self:
            if po.auto_generated:
                continue  # Bỏ qua nếu là đơn mua được tạo tự động từ đơn bán

            # Tìm xem đối tác (vendor) có phải là công ty trong hệ thống không
            company_partner = self.env['res.company'].sudo().search(
                [('partner_id', '=', po.partner_id.id)], limit=1)
            if not company_partner:
                continue

            # Tạo đơn bán
            try:
                sale_order = po._create_sale_order(company_partner)
                if sale_order:
                    po.intercompany_sale_order_id = sale_order.id

                    # Nếu có cấu hình tự động xác nhận, thì xác nhận đơn bán
                    if po.company_id.po_to_so_auto_validation:
                        sale_order.with_company(company_partner.id).action_confirm()

            except Exception as e:
                # Thay vì chỉ log, hiển thị thông báo lỗi ra giao diện
                raise UserError(_("Lỗi khi tạo đơn bán liên công ty: %s") % str(e))

        # Gọi super để xác nhận đơn hàng mua
        return super(PurchaseOrder, self).button_confirm()

    def _create_sale_order(self, company):
        """Tạo đơn bán từ đơn mua"""
        self.ensure_one()
        SaleOrder = self.env['sale.order'].sudo().with_company(company.id)

        warehouse = self.company_id.po_to_so_warehouse_id or self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', company.id)], limit=1)
        if not warehouse:
            raise UserError(_("Không tìm thấy kho hàng cho công ty %s") % company.name)

        pricelist = self.env['product.pricelist'].sudo().with_company(company.id).search(
            [('company_id', '=', company.id)], limit=1)
        if not pricelist:
            pricelist = self.env['product.pricelist'].sudo().with_company(company.id).search([], limit=1)

        sale_order_vals = {
            'partner_id': self.company_id.partner_id.id,
            'company_id': company.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': pricelist.id,
            'client_order_ref': self.name,
            'auto_generated': True,
            'auto_purchase_order_id': self.id,
            'user_id': self.env.user.id,
            'team_id': self.env['crm.team'].sudo().with_company(company.id).search(
                [('company_id', '=', company.id)], limit=1).id,
            'payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'date_order': self.date_order,
            'fiscal_position_id': self.fiscal_position_id.id if self.fiscal_position_id else False,
        }

        sale_order = SaleOrder.create(sale_order_vals)

        # Tạo các dòng đơn bán từ dòng đơn mua
        for line in self.order_line:
            product = self.env['product.product'].sudo().with_company(company.id).search(
                [('id', '=', line.product_id.id)], limit=1)
            if not product:
                raise UserError(_("Không tìm thấy sản phẩm %s trong công ty %s") % (line.product_id.name, company.name))

            price_unit = line.price_unit if self.company_id.po_to_so_sync_price else product.list_price
            product_qty = line.product_qty if self.company_id.po_to_so_sync_quantity else 1.0

            sale_line_vals = {
                'order_id': sale_order.id,
                'product_id': product.id,
                'name': line.name,
                'product_uom_qty': product_qty,
                'product_uom': line.product_uom.id,
                'price_unit': price_unit,
                'tax_id': [(6, 0, product.taxes_id.ids)],
                'auto_generated': True,
                'purchase_line_id': line.id,
            }

            if hasattr(line, 'analytic_distribution') and line.analytic_distribution:
                sale_line_vals['analytic_distribution'] = line.analytic_distribution

            self.env['sale.order.line'].sudo().with_company(company.id).create(sale_line_vals)

        return sale_order


    def write(self, vals):
        """Khi đơn mua thay đổi, cập nhật đơn bán tương ứng"""
        res = super().write(vals)

        for po in self:
            if po.intercompany_sale_order_id and po.company_id.po_to_so_update_so:
                if 'order_line' in vals:
                    po._update_sale_order()

        return res

    def _update_sale_order(self):
        """Cập nhật đơn bán khi đơn mua thay đổi"""
        self.ensure_one()
        if not self.intercompany_sale_order_id:
            return

        sale_order = self.intercompany_sale_order_id.sudo().with_company(
            self.intercompany_sale_order_id.company_id.id)

        if sale_order.state != 'draft':
            raise UserError(_("Không thể cập nhật đơn bán %s vì không ở trạng thái nháp.") % sale_order.name)

        for po_line in self.order_line:
            so_line = sale_order.order_line.filtered(lambda l: l.purchase_line_id.id == po_line.id)

            if so_line:
                update_vals = {}
                if self.company_id.po_to_so_sync_quantity:
                    update_vals['product_uom_qty'] = po_line.product_qty
                if self.company_id.po_to_so_sync_price:
                    update_vals['price_unit'] = po_line.price_unit
                if update_vals:
                    so_line.write(update_vals)
            else:
                product = self.env['product.product'].sudo().with_company(
                    sale_order.company_id.id).search([('id', '=', po_line.product_id.id)], limit=1)
                if not product:
                    continue

                price_unit = po_line.price_unit if self.company_id.po_to_so_sync_price else product.list_price
                product_qty = po_line.product_qty if self.company_id.po_to_so_sync_quantity else 1.0

                sale_line_vals = {
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'name': po_line.name,
                    'product_uom_qty': product_qty,
                    'product_uom': po_line.product_uom.id,
                    'price_unit': price_unit,
                    'tax_id': [(6, 0, product.taxes_id.ids)],
                    'auto_generated': True,
                    'purchase_line_id': po_line.id,
                }

                if hasattr(po_line, 'analytic_distribution') and po_line.analytic_distribution:
                    sale_line_vals['analytic_distribution'] = po_line.analytic_distribution

                self.env['sale.order.line'].sudo().with_company(sale_order.company_id.id).create(sale_line_vals)

        po_line_ids = self.order_line.ids
        for so_line in sale_order.order_line:
            if so_line.auto_generated and so_line.purchase_line_id.id not in po_line_ids:
                so_line.unlink()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    auto_generated = fields.Boolean(
        string='Tự động tạo',
        copy=False,
        help='Dòng đơn hàng được tạo từ dòng đơn bán',
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Dòng đơn bán gốc',
        copy=False,
        readonly=True,
    )
