# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    allowed_loan = fields.Integer("max allowed Loans", default=1)

    @api.constrains('allowed_loan')
    def _allowed_loan(self):
        if not self.allowed_loan >= 1:
            raise ValidationError(_('The Maximum loan amount must be grater than 0.'))


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    @api.depends('loan_lines')
    def _compute_loan_amount(self):
        
        for loan in self:
            total_paid = 0.0
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    date_confirm = fields.Date(string="Date", readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "paymemt")
    last_payment_date = fields.Date(string="Last Payment Date", readonly=True, help="Payment Last Date",
                                    compute='_compute_last_payment_date')
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount',
                                  help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount',
                                     help="Total paid amount")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'paid')
    ], string='Payment Status', default='not_paid', readonly=True)
    loan_type_id = fields.Many2one("loan.type", string="Loan Type", index=True, required=True, ondelete='restrict')
    installment_type = fields.Selection([('non_base', 'Non Base On Payroll'),
                                         ('base_on', 'Base On Payroll')]
                                        , 'Type', default='non_base', required=True)

    @api.depends('loan_lines.date')
    def _compute_last_payment_date(self):
        self.last_payment_date = 0.0
        for rec in self:
            payment_date = self.env['hr.loan.line'].search([('loan_id', '=', rec.id)], order="date DESC", limit=1)
            for line in payment_date:
                rec.last_payment_date = line.date

    @api.onchange('loan_type_id')
    def _onchange_loan_type_id(self):
        self.installment = self.loan_type_id.installment
        self.employee_account_id = self.loan_type_id.account_id.id
        self.treasury_account_id = self.loan_type_id.treasury_account_id.id
        self.journal_id = self.loan_type_id.journal_id.id

    def action_register_payment(self):
        ''' Open the hr.loan.payment.wizard to pay the selected journal entries.
        :return: An action opening the hr.loan.payment.wizard wizard.
        '''
        return {
            'name': _('Register Payment'),
            'res_model': 'hr.loan.payment.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'hr.loan',
                'active_ids': self.ids,
                'default_ref': self.name,
                'default_partner_id': self.employee_id.user_partner_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        employee = self.env['hr.employee'].search([('id', '=', values['employee_id'])])
        # if loan_count >= employee.allowed_loan:
        #     raise ValidationError(_("The employee has consumed all allowed loans"))
        # else:
        #     values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        res = super(HrLoan, self).create(values)
        return res

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1',
                    'date_confirm': fields.Date.today()})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"
    _order = 'installment_number, date'

    _rec_name = 'loan_id'
    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")
    installment_number = fields.Integer()

    @api.model
    def create(self, values):
        # Get the next installment number
        loan_id = values.get('loan_id')
        last_installment = self.search([('loan_id', '=', loan_id)], order='installment_number desc', limit=1)
        values['installment_number'] = last_installment.installment_number + 1 if last_installment else 1
        return super(InstallmentLine, self).create(values)

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('payment'):
                result.append((record.id,
                               'Installment Number (%s): %s SR' % (record.installment_number, round(record.amount, 2))))
            else:
                result.append((record.id, 'Installment Number (%s)' % record.installment_number))
        return result


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
