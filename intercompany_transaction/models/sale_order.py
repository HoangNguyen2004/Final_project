from odoo import api, fields, models, _
from odoo.exceptions import UserError  # Dự phòng nếu bạn muốn xử lý lỗi

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    auto_generated = fields.Boolean(
        string='Tự động tạo',
        copy=False,
        help='Đơn bán được tạo tự động từ đơn mua',
    )
    auto_purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Đơn mua nguồn',
        copy=False,
        readonly=True,
    )
    has_intercompany_po = fields.Boolean(
        string='Có đơn mua liên công ty',
        compute='_compute_has_intercompany_po',
        store=True,
        help='Chỉ ra rằng đơn bán này có liên kết đến đơn mua liên công ty',
    )
    intercompany_source = fields.Char(
        string='Nguồn intercompany',
        compute='_compute_intercompany_source',
        store=True,
        help='Thông tin nguồn gốc của giao dịch intercompany',
    )

    @api.depends('auto_purchase_order_id')
    def _compute_has_intercompany_po(self):
        """Tính toán xem có đơn mua liên kết hay không"""
        for order in self:
            order.has_intercompany_po = bool(order.auto_purchase_order_id)

    @api.depends('auto_purchase_order_id', 'auto_generated')
    def _compute_intercompany_source(self):
        """Tính toán chuỗi mô tả nguồn intercompany"""
        for order in self:
            if order.auto_generated and order.auto_purchase_order_id:
                order.intercompany_source = _('Được tạo từ đơn mua: %s') % order.auto_purchase_order_id.name
            else:
                order.intercompany_source = False

    def action_view_purchase_order(self):
        """Hiển thị đơn mua gốc từ đơn bán"""
        self.ensure_one()
        if not self.auto_purchase_order_id:
            return {
                'type': 'ir.actions.act_window_close',
            }

        return {
            'type': 'ir.actions.act_window',
            'name': _('Đơn mua liên kết'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.auto_purchase_order_id.id,
            'context': {'create': False, 'show_sale': True},
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    auto_generated = fields.Boolean(
        string='Tự động tạo',
        copy=False,
        help='Dòng đơn bán được tạo từ dòng đơn mua',
    )
    purchase_line_id = fields.Many2one(
        'purchase.order.line',
        string='Dòng đơn mua gốc',
        copy=False,
        readonly=True,
    )
