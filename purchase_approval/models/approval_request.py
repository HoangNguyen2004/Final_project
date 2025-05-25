from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ApprovalRequest(models.Model):
    _name = 'approval.request'
    _description = 'Approval Request'
    _order = 'request_date desc, id desc'
    name = fields.Char(string='Tham chiếu', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    model = fields.Char(string='Model', required=True, readonly=True)
    res_id = fields.Integer(string='Record ID', required=True, readonly=True)
    requester_id = fields.Many2one('res.users', string='Người yêu cầu', readonly=True,
                                  default=lambda self: self.env.user)
    request_date = fields.Datetime(string='Ngày yêu cầu', default=fields.Datetime.now, readonly=True)
    approver_id = fields.Many2one('hr.employee', string='Người phê duyệt', readonly=True)
    approval_date = fields.Datetime(string='Thời gian phê duyệt', readonly=True)
    approval_note = fields.Text(string='Ghi chú')

    state = fields.Selection([
        ('to_approve', 'Chờ phê duyệt'),
        ('approved', 'Đã phê duyệt'),
        ('rejected', 'Đã từ chối')
    ], default='to_approve', string='Trạng thái', readonly=True)

    # Các trường liên quan đến Purchase Request
    pr_name = fields.Char(string='Tham chiếu PR', compute='_compute_pr_fields', store=False, readonly=True)
    pr_request_date = fields.Date(string='Ngày yêu cầu PR', compute='_compute_pr_fields', store=False, readonly=True)
    pr_expected_date = fields.Date(string='Hạn đặt hàng PR', compute='_compute_pr_fields', store=False, readonly=True)
    pr_product_type = fields.Selection([
        ('consu', 'Hàng hóa'),
        ('service', 'Dịch vụ'),
        ('bundle', 'Combo')  
        ], string='Loại sản phẩm PR', compute='_compute_pr_fields', store=False, readonly=True)
    pr_category_type = fields.Selection([
        ('product', 'Sản phẩm'),
        ('nvl', 'Nguyên vật liệu'),
        ('all', 'Tất cả')
    ], string='Phân loại PR', compute='_compute_pr_fields', store=False, readonly=True)

    is_current_user_approver = fields.Boolean(
        string='Người dùng có quyền phê duyệt',
        compute='_compute_is_current_user_approver',
        store=False
    )

    @api.depends_context('uid')
    def _compute_is_current_user_approver(self):
        current_employee = self.env.user.employee_id
        for rec in self:
            rec.is_current_user_approver = bool(current_employee and current_employee.is_approval)

    @api.depends('model', 'res_id')
    def _compute_pr_fields(self):
        """Lấy thông tin từ Purchase Request"""
        for record in self:
            if record.model == 'purchase.request' and record.res_id:
                pr = self.env['purchase.request'].browse(record.res_id).exists()
                if pr:
                    record.pr_name = pr.name
                    record.pr_request_date = pr.request_date
                    record.pr_expected_date = pr.expected_date
                    record.pr_product_type = pr.product_type
                    record.pr_category_type = pr.category_type
                else:
                    record.pr_name = False
                    record.pr_request_date = False
                    record.pr_expected_date = False
                    record.pr_product_type = False
                    record.pr_category_type = False
            else:
                record.pr_name = False
                record.pr_request_date = False
                record.pr_expected_date = False
                record.pr_product_type = False
                record.pr_category_type = False

    def action_view_pr(self):
        """Mở popup hiển thị Purchase Request liên quan (readonly)"""
        self.ensure_one()
        if self.model == 'purchase.request' and self.res_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Chi tiết yêu cầu mua hàng'),
                'res_model': 'purchase.request',
                'res_id': self.res_id,
                'view_mode': 'form',
                'target': 'new',  # Mở ở chế độ popup
                'context': {
                    'create': False,
                    'edit': False,
                }
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_approve(self):
        """Phê duyệt yêu cầu"""
        for record in self:
            employee = self.env.user.employee_id
            if not employee or not employee.is_approval:
                raise UserError(_("Bạn không có quyền phê duyệt yêu cầu này."))

            now = fields.Datetime.now()

            record.write({
                'state': 'approved',
                'approver_id': employee.id,
                'approval_date': now
            })

            if record.model == 'purchase.request' and record.res_id:
                try:
                    pr = self.env['purchase.request'].browse(record.res_id)
                    pr.write({
                        'state': 'approved',
                        'approver_id': employee.id,
                        'approval_date': now,
                        'approval_note': record.approval_note,
                    })
                except Exception:
                    pass



    def action_reject(self):
        """Từ chối yêu cầu"""
        for record in self:
            employee = self.env.user.employee_id

            # Kiểm tra quyền phê duyệt
            if not employee or not employee.is_approval:
                raise UserError(_("Bạn không có quyền từ chối yêu cầu này."))

            # Bắt buộc ghi chú từ chối
            if not record.approval_note or not record.approval_note.strip():
                raise UserError(_("Vui lòng nhập Lý do từ chối vào phần Ghi chú."))

            now = fields.Datetime.now()

            # Cập nhật trạng thái trong approval.request
            record.write({
                'state': 'rejected',
                'approver_id': employee.id,
                'approval_date': now
            })

            # Ghi lại thông tin trạng thái vào model gốc
            if record.model == 'purchase.request' and record.res_id:
                try:
                    pr = self.env['purchase.request'].browse(record.res_id)
                    pr.write({
                        'state': 'cancel',
                        'approver_id': employee.id,
                        'approval_date': now,
                        'approval_note': record.approval_note,
                    })
                except Exception:
                    pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('approval.request') or _('New')
        return super().create(vals_list)
