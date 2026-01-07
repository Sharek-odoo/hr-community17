# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date

from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class HRTicketRequest(models.Model):
    """"""
    _name = 'hr.ticket.request'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    TICKET_DEGREE = [
        ('first', 'First'),
        ('first_reduced', 'First Reduced'),
        ('economic', 'Economic'),
        ('business', 'Business'),
        ('other', 'Other')]

    def _get_logged_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)])

    state = fields.Selection(string='State', selection=[('draft', 'Draft'), ('hr_manager', 'KR Manager'),
                                                        ('finance_manager', 'Finance Manager'), ('done', 'Done'),
                                                        ('cancel', 'Cancel')], default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id, store=True,
                                 string="Company")
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    from_hr = fields.Boolean(string='Another Employee', default=False)
    employee_id = fields.Many2one('hr.employee', default=_get_logged_employee, string='Employee')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job')
    nationality_id = fields.Many2one('res.country', related='employee_id.country_id', string='Nationality')
    passport_no = fields.Char(related='employee_id.passport_id', string='Passport Number')
    # passport_expiry_date = fields.Date(related='employee_id.passport_expiry_date', string='Passport Expiration')
    passport_expiry_date = fields.Date(related='employee_id.passport_end_date', string='Passport Expiration')
    request_for = fields.Selection([('employee', 'Employee'), ('family', 'Family'), ('all', 'All')], default='employee',
                                   string='Request For')
    request_type = fields.Many2one('hr.ticket.request.type', string='Request Type')
    mission_check = fields.Boolean(string='Mission/Training Not Holiday')
    leave_id = fields.Many2one("hr.leave", string="Leave", tracking=True)
    leave_date_from = fields.Date(related="leave_id.request_date_from", string="Leave Form")
    leave_date_to = fields.Date(related="leave_id.request_date_to", string="Leave To")
    air_line = fields.Many2one('hr.airline', string='Air Line')
    ticket_degree = fields.Selection(TICKET_DEGREE, default='first', string='Ticket Degree')
    travel_agent = fields.Many2one('res.partner', string='Travel Agent')
    ticket_cost = fields.Float(string='Ticket Cost')
    destination_id = fields.Many2one('hr.destination', string='Destination')
    deputation_id = fields.Many2one('hr.deputations', string='Deputation')
    ticket_date = fields.Date(string='Ticket Date', default=fields.Date.today())
    move_id = fields.Many2one("account.move", string="Journal Entry", copy=False)
    note = fields.Text(string='Notes')

    @api.onchange('from_hr')
    def onchange_from_hr(self):
        if self.from_hr == False:
            emp = self.env["hr.employee"].search([('user_id', '=', self.env.user.id)],limit=1).id
            self.employee_id = emp
            self._origin.employee_id = emp
    def action_submit(self):
        self.state = 'hr_manager'

    def action_hr_manager_approve(self):
        self.state = 'finance_manager'

    def action_cancel(self):
        self.state = 'cancel'

    def action_finance_manager_approve(self):
        for rec in self:
            contract_id = self.env['hr.contract'].search(
                [('state', '=', 'open'), ('employee_id', '=', rec.employee_id.id)], limit=1)
            if contract_id:
                if not rec.request_type.account_debit_id:
                    raise ValidationError(_("Please add debit account in request type form"))
                elif not rec.request_type.journal_id:
                    raise ValidationError(_("Please add ticket journal in request type form"))
                elif not rec.employee_id.address_id:
                    raise ValidationError(
                        _("Please add partner to {} firstly and try again.".format(rec.employee_id.name)))
                elif rec.ticket_cost <= 0:
                    raise ValidationError(_("Total ticket cost for employee: ({}) must be greater than zero.".format(
                        rec.employee_id.name)))

                move_id = self.env['account.move'].sudo().create([
                    {
                        'invoice_date': fields.Date.today(),
                        'partner_id': rec.employee_id.address_id.id,
                        'date': fields.Date.today(),
                        'move_type': 'in_invoice',
                        'ref': _('Ticket Cost For: {}'.format(rec.employee_id.name)),

                        'line_ids': [
                            (0, 0, {
                                'name': _('Ticket Cost For: {}'.format(rec.employee_id.name)),
                                'partner_id': rec.employee_id.address_id.id,
                                'account_id': rec.employee_id.address_id.property_account_payable_id.id,
                                'price_unit': rec.ticket_cost,
                                'credit': rec.ticket_cost,
                            }
                             ),
                            (0, 0, {
                                'name': _('Ticket Cost For: {}'.format(rec.employee_id.name)),
                                'partner_id': rec.employee_id.address_id.id,
                                'account_id': rec.request_type.account_debit_id.id,
                                'price_unit': rec.ticket_cost,
                                'debit': rec.ticket_cost,
                                # 'account_internal_type': 'payable',
                                'account_type': 'payable',
                            }
                             ),
                        ],
                    }
                ])
                if move_id:
                    rec.move_id = move_id.id
                    self.state = 'done'
            else:
                raise ValidationError(_("{} haven't running contract.".format(rec.employee_id.name)))

    def action_draft(self):
        self.state = 'draft'


class AirLine(models.Model):
    _name = 'hr.airline'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    code = fields.Char('Code')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id, sgtore=True,
                                 string="Company")


class HRTicketRequestType(models.Model):
    """"""
    _name = 'hr.ticket.request.type'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    account_debit_id = fields.Many2one('account.account', string='Account Debit')
    journal_id = fields.Many2one("account.journal", string="Tickets Journal")


class HRDestination(models.Model):
    """"""
    _name = 'hr.destination'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    code = fields.Char('Code')
    country_id = fields.Many2one('res.country', string='Counter')
    destination_line_ids = fields.One2many('hr.destination.line', 'destination_id', string='Destination Line')


class HRDestinationLine(models.Model):
    """"""
    _name = 'hr.destination.line'
    _inherit = 'mail.thread'

    destination_id = fields.Many2one('hr.destination', string='Destination')
    class_id = fields.Many2one('hr.destination.class', string='Ticket Class')
    price = fields.Float(string='Price')


class HRDestinationClass(models.Model):
    _name = 'hr.destination.class'

    name = fields.Char(string='Class Name')
