# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HRExitReturn(models.Model):
    """"""
    _name = 'hr.exit.return'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'
    _description = "Exit and Return"

    REQUEST_FOR = [
        ('employee', 'Fot Employee Only'),
        ('family', 'For Family Only'),
        ('all', 'For Employee and Family')
    ]
    EXIT_RETURN_TYPE = [
        ('one', 'One Travel'),
        ('multi', 'Multi Travel'),
        ('final', 'Final Exit')
    ]

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'),
                              ('cancel', 'Cancel')], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    job_id = fields.Many2one("hr.job", related="employee_id.job_id", string="Job Position")
    manager_id = fields.Many2one("hr.employee", related="employee_id.parent_id", string="Manager")
    employee_no = fields.Char(related="employee_id.employee_no", string="Employee No")
    without_leave = fields.Boolean(string="Without Leave", tracking=True)
    request_for = fields.Selection(REQUEST_FOR, default='employee', string="Request For", tracking=True)
    leave_request_id = fields.Many2one("hr.leave", string="Leave Request", tracking=True)
    vacation_start_date = fields.Date(related="leave_request_id.request_date_from",
                                      string="Vacation Start Date")
    vacation_end_date = fields.Date(related="leave_request_id.request_date_to", string="Vacation End Date")
    vacation_duration = fields.Float(related="leave_request_id.number_of_days", string="Vacation Duration")
    visa_no = fields.Char(string="Visa No")
    visa_duration = fields.Float(string="Visa Duration")
    exit_return_type = fields.Selection(EXIT_RETURN_TYPE, default='one', string="Exit Type", tracking=True)
    cost_by_employee = fields.Boolean(string="Cost By Employee", default=False)
    cost = fields.Float(string="Cost")
    move_id = fields.Many2one("account.move", string="Vendor Bill", copy=False)
    travel_before_date = fields.Date(string="Travel Before Date", default=fields.Date.today())
    arrival_before_date = fields.Date(string="Arrival Before Date", copy=False)
    bill_count = fields.Integer(string="Bills", default=1)
    note = fields.Text(string="Description")
    family_ids = fields.One2many('exit.return.line', 'exit_return_id', string='Family')

    @api.onchange('employee_id')
    def _onchange_employee(self):
        self.family_ids = False

    def unlink(self):
        """
        A method to delete exit and return request.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please reset exit and return request to draft first and try again."))
        return super(HRExitReturn, self).unlink()

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):

        # Create vendor bill with exit and return cost.
        contract_id = self.env['hr.contract'].search(
            [('state', '=', 'open'), ('employee_id', '=', self.employee_id.id)], limit=1)
        if contract_id and not self.cost_by_employee:
            if not self.company_id.exit_return_account_id:
                raise ValidationError(_("Please add exit and return account in settings"))
            elif not contract_id.analytic_account_id:
                raise ValidationError(_("Please add analytic account in employee contract"))
            elif not self.company_id.exit_return_journal_id:
                raise ValidationError(_("Please add exit and return Journal in settings"))
            elif not self.employee_id.address_id:
                raise ValidationError(_("Please add partner to selected employee firstly and try again."))
            elif self.cost <= 0:
                raise ValidationError(_("Cost must be greater than zero."))

            move_id = self.env['account.move'].sudo().create([
                {
                    'invoice_date': fields.Date.today(),
                    'partner_id': self.employee_id.address_id.id,
                    'date': fields.Date.today(),
                    'move_type': 'in_invoice',
                    'ref': _('Exit And Return Cost For: {}').format(self.employee_id.name),

                    'line_ids': [
                        (0, 0, {
                            'name': _('Exit And Return Cost For: {}').format(self.employee_id.name),
                            'partner_id': self.employee_id.address_id.id,
                            'account_id': self.employee_id.address_id.property_account_payable_id.id,
                            'analytic_distribution': {contract_id.analytic_account_id.id :100},
                            'price_unit': self.cost,
                            'credit': self.cost,
                            # 'exclude_from_invoice_tab': True
                        }
                         ),
                        (0, 0, {
                            'name': _('Exit And Return Cost For: {}').format(self.employee_id.name),
                            'partner_id': self.employee_id.address_id.id,
                            'account_id': self.company_id.exit_return_account_id.id,
                            'analytic_distribution': {contract_id.analytic_account_id.id :100},
                            'price_unit': self.cost,
                            'debit': self.cost,
                            'account_type': 'liability_payable',
                        }
                         ),
                    ],
                }
            ])
            if move_id:
                self.move_id = move_id.id
                self.state = 'done'
        else:
            raise ValidationError(_("This employee haven't running contract."))

    def action_view_bill(self):
        invoice_obj = self.env.ref('account.view_move_form')
        return {'name': _("Exit and Return Bill"),
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': invoice_obj.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': self.move_id.id,
                'context': {}}

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'


class HRLeave(models.Model):
    _inherit = 'hr.leave'

    issuing_exit_return = fields.Boolean(string="Issuing Exit & Return", default=False)


class ExitReturnLine(models.Model):
    _name = 'exit.return.line'

    exit_return_id = fields.Many2one("hr.exit.return", string="Exit and Returns")
    dependant_id = fields.Many2one("hr.family", string="Name")
    relationship = fields.Selection(
        [('father', 'Father'), ('mother', 'Mother'), ('wife', 'Wife'), ('son', 'Son'), ('daughter', 'Daughter'),
         ('other', 'Other')], string='Relationship', related="dependant_id.relationship")
    id_no = fields.Char('ID Number', related="dependant_id.id_no")
    birth_date = fields.Date('Date of Birth', related="dependant_id.birth_date")
    phone = fields.Char('Phone', related="dependant_id.phone")
    is_emergency = fields.Boolean('Emergency', related="dependant_id.is_emergency")
