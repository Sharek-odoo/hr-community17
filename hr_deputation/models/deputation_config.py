
from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    deputation_account = fields.Many2one('account.analytic.account',string="Analytic Account for deputations", config_parameter='hr_deputation.hr_deputation_account')
    
    ticket_product = fields.Many2one('product.product', string="Tickets Product", config_parameter='hr_deputation.hr_ticket_product')

    account_id = fields.Many2one("account.account", string="Deputation Account",
                                 related="company_id.account_id", readonly=False, store=True)


class ResCompany(models.Model):
    """"""
    _inherit = 'res.company'

    account_id = fields.Many2one("account.account", string="Account")
