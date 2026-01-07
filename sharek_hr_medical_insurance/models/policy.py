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


class InsurancePolicy(models.Model):
    """"""
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'insurance.policy'
    _rec_name = 'name'
    _description = "Insurance Policy"

    def _get_default_end_date(self):
        date_to = fields.Date.today() + relativedelta(years=1)
        return date_to

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('bill', 'Billed'), ('expire', 'Expired')],
                             default='draft', string='State')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id, store=True)
    name = fields.Char(string="Policy Number", translate=True)
    insurance_company_id = fields.Many2one("res.partner", string="Insurance Company")
    invoice_payment_term_id = fields.Many2one("account.payment.term", string="Payment Term")
    amount = fields.Float(string='Amount')
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]",)
    total_amount = fields.Monetary(string="Total Amount", store=True, readonly=True, compute='_compute_tax_total_amount',
                                help="Total Insurance amount")
    tax_amount = fields.Monetary(string="Tax Amount", store=True, readonly=True, compute='_compute_tax_total_amount',
                                help="Tax amount")

    paid_amount = fields.Monetary(string="Paid Amount", compute='_compute_insurance_amount', help="Paid Amount")
    balance_amount = fields.Monetary(string="Remaining Amount", compute='_compute_insurance_amount', help="Remaining Amount")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    start_date = fields.Date(string="Start Date", default=fields.Date.today())
    end_date = fields.Date(string="End Date", default=_get_default_end_date)
    beneficiary_number = fields.Integer(string="No. of Beneficiaries")
    payment_type = fields.Selection([('fixed', 'Fixed'), ('installment', 'Installment')], default='fixed',
                                    string="Payment Type")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", default=fields.Date.today(), help="Date of the paymemt")
    advance_payment = fields.Boolean(string="Advance Payment", default=False)
    advance_amount = fields.Monetary(string="Advance Amount")
    advance_payment_date = fields.Date(string="Advance Payment Date", default=fields.Date.today())
    invoice_id = fields.Many2one('account.move', string='Invoices', readonly=True, copy=False)
    bill_count = fields.Integer(string="Bills", default=1)
    insurance_installment_ids = fields.One2many('insurance.policy.installment', 'insurance_id', string="Installments",
                                                index=True)
    policy_class_ids = fields.One2many("insurance.policy.class", "policy_id", string="Classes")
    notes = fields.Text(string="Notes")

    def unlink(self):
        """
        A method to delete policy.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please reset policy to draft first and try again."))
        return super(InsurancePolicy, self).unlink()

    def compute_installment(self):
        """This automatically create the installment the company need to pay to
        insurance company based on payment start date and the no of installments.
            """
        for insurance in self:
            insurance.insurance_installment_ids.unlink()
            date_start = datetime.strptime(str(insurance.payment_date), '%Y-%m-%d')
            amount = (insurance.total_amount - insurance.advance_amount) / insurance.installment
            for i in range(1, insurance.installment + 1):
                self.env['insurance.policy.installment'].create({
                    'date': date_start,
                    'amount': amount,
                    'currency_id': insurance.currency_id.id,
                    'insurance_id': insurance.id})
                date_start = date_start + relativedelta(months=1)
        return True

    def _compute_insurance_amount(self):
        for insurance in self:
            insurance.paid_amount = 0.0
            insurance.balance_amount = 0.0
            if insurance.invoice_id:
                insurance.paid_amount = insurance.total_amount - insurance.invoice_id.amount_residual
                insurance.balance_amount = insurance.total_amount - insurance.paid_amount
            else:
                insurance.paid_amount = 0.0
                insurance.balance_amount = insurance.total_amount

    def action_confirm(self):
        if not self.policy_class_ids:
            raise ValidationError(_("You must add one policy class at least!"))
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    @api.model
    def scheduler_manage_contract_expiration(self):
        # This method is called by a cron task
        # It manages the state of a policy.

        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('company_id.period_before_notification', default=30))
        date_today = fields.Date.from_string(fields.Date.today())
        outdated_days = fields.Date.to_string(date_today + relativedelta(days=+delay_alert_contract))

        reminder_activity_type = self.env.ref('hr_medical_insurance.mail_act_insurance_policy_to_expire', raise_if_not_found=False) or self.env['mail.activity.type']
        nearly_expired_policies = self.search([
            ('state', '=', 'draft'),
            ('end_date', '<', outdated_days)
        ]
        ).filtered(
            lambda nec: reminder_activity_type not in nec.activity_ids.activity_type_id
        )

        for policy in nearly_expired_policies:
            policy.activity_schedule(
                'hr_medical_insurance.mail_act_insurance_policy_to_expire', policy.end_date,
                user_id=self.env.user.id)

        expired_policies = self.search([('state', 'not in', ['expire']), ('end_date', '<',fields.Date.today())])
        expired_policies.write({'state': 'expire'})

    def run_scheduler(self):
        self.scheduler_manage_contract_expiration()

    def action_create_bill(self):

        if not self.company_id.product_id:
            raise ValidationError(_("Please add insurance product in settings"))
        elif not self.company_id.analytic_account_id:
            raise ValidationError(_("Please add insurance analytic account in settings"))
        elif not self.company_id.journal_id:
            raise ValidationError(_("Please add insurance Journal in settings"))

        vals = {'partner_id': self.insurance_company_id.id,
                'invoice_date': datetime.today(),
                'invoice_origin': _('{} - Insurance Policy - {}').format(self.insurance_company_id.name, self.name),
                'move_type': 'in_invoice',
                'invoice_payment_term_id':  self.invoice_payment_term_id.id,
                'journal_id':  self.company_id.journal_id.id,
                'currency_id':  self.currency_id.id,
                'payment_reference': _('{} - Insurance Policy - {}').format(self.insurance_company_id.name, self.name),
                }

        invoice_line = []
        invoice_line_vals = {'name': _('{} - Insurance Policy - {}').format(self.insurance_company_id.name, self.name),
                             'product_id': self.company_id.product_id.id,
                             'analytic_distribution': {self.company_id.analytic_account_id.id: 100},
                             'quantity': 1.000,
                             'price_unit': self.amount,
                             'tax_ids': [(6, 0, self.tax_ids.ids)]}
        invoice_line.append((0, 0, invoice_line_vals))
        vals.update({'invoice_line_ids': invoice_line})
        insurance_invoice = self.env['account.move'].create(vals)
        if insurance_invoice:
            self.invoice_id = insurance_invoice.id
            self.state = 'bill'

        return {
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': insurance_invoice.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'edit': False},
        }

    @api.constrains('beneficiary_number','amount')
    def _check_beneficiary_number_amount(self):
        if self.beneficiary_number <= 0:
            raise ValidationError(_("Beneficiaries number must be more than zero."))
        elif self.amount <= 0:
            raise ValidationError(_("Amount must be more than zero."))

    # @api.constrains('policy_class_ids')
    # def _check_policy_class_amount(self):
    #     if self.policy_class_ids:
    #         for rec in self.policy_class_ids:
    #             if rec.amount <= 0:
    #                 raise ValidationError(_("Class amount must be more than zero."))

    @api.constrains('name')
    def _check_name(self):
        for rec in self:
            if self.env['insurance.policy'].search([('id', '!=', rec.id), ('name', '=', rec.name)]):
                raise ValidationError(_("Policy number must be unique."))

    @api.depends('amount','tax_ids')
    def _compute_tax_total_amount(self):
        """"""
        for rec in self:
            tax_amount = 0.0
            tax_amount = rec.amount * (sum(self.env['account.tax'].search([('id', 'in', rec.tax_ids.ids)]).mapped('amount')) / 100)
            rec.tax_amount = tax_amount
            rec.total_amount = rec.amount + tax_amount

    def action_view_bill(self):
        invoice_obj = self.env.ref('account.view_move_form')
        return {'name': _("Boocking Tiket Bill"),
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': invoice_obj.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': self.invoice_id.id,
                'context': {}}


class InsurancePolicyClass(models.Model):
    """"""
    _name = 'insurance.policy.class'
    _description = "Insurance Policy Class"

    class_id = fields.Many2one("insurance.class", string="Insurance Class")
    # amount = fields.Float(string='Amount')
    policy_id = fields.Many2one("insurance.policy", string="Insurance Policy")

class InsuranceClass(models.Model):
    """"""
    _name = 'insurance.class'
    _rec_name = 'name'
    _description = "Insurance Class"

    name = fields.Char(string="Class", translate=True)


class InsurancePolicyInstallment(models.Model):
    _name = "insurance.policy.installment"
    _description = "Insurance Policy Installment"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    insurance_id = fields.Many2one('insurance.policy', string='Insurance')
