from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    weekday_hour_rate_sa = fields.Float(string='Weekday OT Hour Rate SA')
    weekday_hour_rate = fields.Float(string='Weekday OT Hour Rate')
    weekend_hour_rate = fields.Float(string='Weekend OT Hour Rate')
    holiday_hour_rate = fields.Float(string='Holiday OT Hour Rate')
