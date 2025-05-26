from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    po_to_so_auto_validation = fields.Boolean(
        string='Auto-validate SO on PO confirmation',
        default=True,
        help='When a Purchase Order is confirmed, the corresponding Sale Order will be automatically confirmed',
    )
    po_to_so_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse for created SO',
        domain="[('company_id', '=', id)]",
        help='Warehouse used in created SO',
    )
    po_to_so_sync_price = fields.Boolean(
        string='Sync price from PO to SO',
        default=True,
        help='Keep the same price from the Purchase Order to the Sale Order',
    )
    po_to_so_sync_quantity = fields.Boolean(
        string='Sync quantity from PO to SO',
        default=True,
        help='Keep the same quantity from the Purchase Order to the Sale Order',
    )
    po_to_so_update_so = fields.Boolean(
        string='Update SO when PO changes',
        default=True,
        help='When the Purchase Order changes, update the linked Sale Order',
    )

