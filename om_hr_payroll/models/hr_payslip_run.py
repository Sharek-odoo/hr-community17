# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrPayslipRun(models.Model):
    _name = "hr.payslip.run"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Payslip Batches"
    _order = "id desc"

    name = fields.Char(required=True, readonly=True)
    slip_ids = fields.One2many(
        "hr.payslip",
        "payslip_run_id",
        string="Payslips",
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    date_start = fields.Date(
        string="Date From",
        required=True,
        readonly=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_end = fields.Date(
        string="Date To",
        required=True,
        readonly=True,
        default=lambda self: fields.Date.today().replace(day=1)
        + relativedelta(months=+1, day=1, days=-1),
    )
    credit_note = fields.Boolean(
        readonly=True,
        help="If its checked, indicates that all payslips generated from here "
        "are refund payslips.",
    )
    struct_id = fields.Many2one(
        "hr.payroll.structure",
        string="Structure",
        readonly=True,
        help="Defines the rules that have to be applied to this payslip batch, "
        "accordingly to the contract chosen. If you let empty the field "
        "contract, this field isn't mandatory anymore and thus the rules "
        "applied will be all the rules set on the structure of all contracts "
        "of the employee valid for the chosen period",
    )

    def draft_payslip_run(self):
        return self.write({"state": "draft"})

    def close_payslip_run(self):
        return self.write({"state": "close"})

    def done_payslip_run(self):
        for line in self.slip_ids:
            line.action_payslip_done()
        return self.write({'state': 'done'})

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('You Cannot Delete Done Payslips Batches'))
        return super(HrPayslipRun, self).unlink()

