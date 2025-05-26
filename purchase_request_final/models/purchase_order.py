from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request')
