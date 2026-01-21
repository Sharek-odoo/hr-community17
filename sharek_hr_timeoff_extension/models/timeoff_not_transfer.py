from odoo import models, fields, api

class TimeoffNotTransfer(models.Model):
    _name = 'timeoff.not.transfer'
    _description = 'Not Transferred Leave Balance'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', required=True)
    not_transfer_balance = fields.Float(required=True)
    time_off_transfer = fields.Many2one('timeoff.transfer',string="Time Off Transfer")
    taken = fields.Boolean(string="taken")


    