from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    is_approval = fields.Boolean(string='Có quyền phê duyệt', default=False,
                                help='Nhân viên có quyền phê duyệt các yêu cầu')
