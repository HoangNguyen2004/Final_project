from odoo import models, fields, api

class ApprovalMixin(models.AbstractModel):
    _name = 'approval.mixin'
    _description = 'Approval Mixin'
    
    def _check_approval_rights(self):
        """Kiểm tra người dùng hiện tại có quyền phê duyệt hay không"""
        self.ensure_one()
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee and employee.is_approval
        
    def need_approval(self):
        """Tạo yêu cầu phê duyệt cho bản ghi hiện tại"""
        self.ensure_one()
        vals = {
            'model': self._name,
            'res_id': self.id,
            'requester_id': self.env.user.id,
            'state': 'to_approve',
        }
        return self.env['approval.request'].create(vals)
        
    def get_approval_status(self):
        """Lấy trạng thái phê duyệt của bản ghi hiện tại"""
        self.ensure_one()
        domain = [('model', '=', self._name), ('res_id', '=', self.id)]
        approval = self.env['approval.request'].search(domain, limit=1, order='id desc')
        return approval and approval.state or False
