from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['approval.mixin']
    _order = 'request_date desc, id desc'

    name = fields.Char(string='Tham chiếu', required=True, copy=False, readonly=True, default='New')
    request_date = fields.Date(string='Ngày yêu cầu', default=fields.Date.today)
    expected_date = fields.Date(string='Ngày cần hàng')
    requester_id = fields.Many2one('res.users', string='Người yêu cầu', default=lambda self: self.env.user)
    approver_id = fields.Many2one('hr.employee', string='Người phê duyệt', readonly=True)
    approval_date = fields.Datetime(string='Thời gian phê duyệt', readonly=True)
    approval_note = fields.Text(string='Ghi chú phê duyệt', readonly=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('to_approve', 'Chờ phê duyệt'),
        ('approved', 'Đã phê duyệt'),
        ('done', 'YCBG'),
        ('cancel', 'Từ chối'),
        ('rejected', 'Đã hủy'),
    ], string='Trạng thái', default='draft', tracking=True)
    statusbar_state = fields.Selection(selection=lambda self: self._fields['state'].selection,
                                   compute='_compute_statusbar_state', store=False)
    statusbar_steps = fields.Char(compute='_compute_statusbar_steps', store=False)
    category_type = fields.Selection([
        ('product', 'Sản phẩm'),
        ('nvl', 'Nguyên vật liệu'),
        ('all', 'Tất cả')
    ], string='Phân loại')
    line_ids = fields.One2many('purchase.request.line', 'request_id', string='Chi tiết sản phẩm')
    rfq_id = fields.Many2one('purchase.order', string='RFQ liên quan', readonly=True)

    approval_id = fields.Many2one('approval.request', string='Yêu cầu phê duyệt', readonly=True)
    approver_id = fields.Many2one(related='approval_id.approver_id', string='Người phê duyệt', readonly=True)
    approval_date = fields.Datetime(related='approval_id.approval_date', string='Ngày phê duyệt', readonly=True)
    approval_note = fields.Text(related='approval_id.approval_note', string='Ghi chú phê duyệt')


    # ===============================
    #         ACTION METHODS
    # ===============================

    def action_submit(self):
        """Chuyển sang trạng thái chờ phê duyệt, có kiểm tra lỗi"""
        for rec in self:
            errors = []

            # 1. Ngày cần hàng bắt buộc phải có
            if not rec.expected_date:
                errors.append("• Vui lòng nhập ngày cần hàng.")

            # 2. Phải có ít nhất 1 dòng sản phẩm
            if not rec.line_ids:
                errors.append("• Vui lòng thêm ít nhất một dòng sản phẩm.")

            # 3. Từng dòng phải có số lượng > 0
            for line in rec.line_ids:
                if line.quantity <= 0:
                    product_name = line.product_id.display_name or 'Sản phẩm chưa chọn'
                    errors.append("• Số lượng của sản phẩm '%s' phải lớn hơn 0." % product_name)

            # Nếu có lỗi → chặn lại và hiển thị thông báo dạng danh sách
            if errors:
                raise UserError("\n" + "\n".join(errors))

            # Nếu không lỗi → chuyển trạng thái và tạo yêu cầu phê duyệt
            approval = rec.need_approval()
            rec.write({
                'state': 'to_approve',
                'approval_id': approval.id
            })


    def generate_rfq(self):
        self.ensure_one()
        # Tìm nhà cung cấp mẫu để tạo RFQ
        supplier = self.env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)
        if not supplier:
            raise UserError(_("Không tìm thấy nhà cung cấp nào."))

        rfq = self.env['purchase.order'].create({
            'partner_id': supplier.id,
            'origin': self.name,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'price_unit': line.product_id.standard_price or 0.0,
                'product_uom': line.uom_id.id,
                'name': line.product_id.name,
                'date_planned': self.expected_date or fields.Date.today(),
            }) for line in self.line_ids],
        })

        self.write({
            'rfq_id': rfq.id,
            'state': 'done',
        })

        # Trả về hành động mở form của RFQ vừa tạo
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': rfq.id,
            'target': 'current',  
        }

    def action_rejected(self):
        self.write({'state': 'rejected'})
    
    def action_draft(self):
        self.write({'state': 'draft'})
    # ===============================
    #            CREATE
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super().create(vals_list)
    
    def action_merge_requests(self):
        """Gộp nhiều PR đã được phê duyệt thành 1 yêu cầu mới, gom sản phẩm trùng nhau"""
        if len(self) < 2:
            raise UserError(_("Vui lòng chọn ít nhất 2 yêu cầu để gộp."))

        base = self[0]

        # Kiểm tra điều kiện hợp lệ
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_("Tất cả yêu cầu phải ở trạng thái 'Đã phê duyệt'."))
            if rec.requester_id != base.requester_id:
                raise UserError(_("Tất cả yêu cầu phải cùng một người yêu cầu."))

        # Tính ngày cần hàng sớm nhất
        min_expected_date = min(r.expected_date for r in self if r.expected_date)

        # Gom dòng sản phẩm theo product_id
        product_quantities = {}
        for rec in self:
            for line in rec.line_ids:
                if line.product_id.id in product_quantities:
                    product_quantities[line.product_id.id]['quantity'] += line.quantity
                else:
                    product_quantities[line.product_id.id] = {
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'uom_id': line.uom_id.id,
                    }

        # Tạo PR mới
        merged_pr = self.env['purchase.request'].create({
            'requester_id': base.requester_id.id,
            'expected_date': min_expected_date,
            'state': 'approved',
        })

        # Tạo dòng sản phẩm từ dict đã gom
        for data in product_quantities.values():
            self.env['purchase.request.line'].create({
                'request_id': merged_pr.id,
                'product_id': data['product_id'],
                'quantity': data['quantity'],
                'uom_id': data['uom_id'],
            })

        # Xoá các PR cũ (trừ bản mới tạo)
        self.exclude(merged_pr).unlink()

        # Mở form PR mới
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request',
            'view_mode': 'form',
            'res_id': merged_pr.id,
            'target': 'current',
        }

    
class PurchaseRequestLine(models.Model):                    
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    request_id = fields.Many2one('purchase.request', string='Purchase Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True)
    quantity = fields.Float(string='Số lượng', default=0.0)
    uom_id = fields.Many2one('uom.uom', string='Đơn vị tính', related='product_id.uom_id', readonly=True)

