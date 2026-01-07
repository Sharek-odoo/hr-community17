# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class LoanType(models.Model):
    _inherit = 'loan.type'
    _description = 'Hr Loan Type'
    medical = fields.Boolean(string="medical", default=False, copy=False)
class InsuranceMembership(models.Model):
    _inherit = 'hr.loan'
    insurance_id = fields.Many2one('insurance.membership',string="Insurance")
class InsuranceMembership(models.Model):
    """"""
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'insurance.membership'
    _rec_name = 'employee_id'
    _description = "Insurance Membership"

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('expire', 'Expired')],
                             default='draft', string='State')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id,
                                 store=True)
    membership_type = fields.Selection([('employee', 'Employee'), ('family_member', 'Family Member')],
                                       string='Membership Type', default='employee')
    loan_type_id = fields.Many2one("loan.type", string="Loan Type", index=True, required=True, ondelete='restrict')

    employee_id = fields.Many2one('hr.employee', string='Employee')
    agent_employee_id = fields.Many2one('hr.employee', string='Agent')
    family_id = fields.Many2one('hr.family', string='Agent', copy=False)
    membership_date = fields.Date(string="Joining Date", default=fields.Date.today())
    policy_id = fields.Many2one('insurance.policy', string='Policy')
    insurance_company_id = fields.Many2one("res.partner", related="policy_id.insurance_company_id")
    start_date = fields.Date(string="Start Date", related="policy_id.start_date")
    end_date = fields.Date(string="End Date", related="policy_id.end_date")
    allowed_class_id = fields.Many2one("insurance.class", string="Allowed Class")
    allowed_class_amount = fields.Float(string="Allowed Class Amount")
    selected_class_id = fields.Many2one("insurance.class", string="Selected Class")
    selected_class_amount = fields.Float(string="Selected Class Amount")
    amount_difference = fields.Monetary(string='Amount Difference', compute="_get_amount_difference")
    currency_id = fields.Many2one('res.currency', string='Currency', related="policy_id.currency_id")
    loan_count = fields.Integer(string="Loan", compute="compute_loan_count")
    loan_id = fields.Many2one('hr.loan', string='Insurance Deficits', copy=False)
    cost_to_employee = fields.Boolean(string="Cost To The Employee", default=False)
    need_loan = fields.Boolean(string="Need Loan", default=False, copy=False)

    def compute_loan_count(self):
        for rec in self:
            rec.loan_count  = len(self.env['hr.loan'].search([('insurance_id', '=', rec.id)]))
    @api.onchange("employee_id")
    def _onchange_employee(self):
        self.family_id = False
        self.agent_employee_id = self.employee_id

    def unlink(self):
        """
        A method to delete membership.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please reset membership to draft first and try again."))
        return super(InsuranceMembership, self).unlink()

    @api.onchange('policy_id', 'state')
    def _get_confirmed_policy(self):
        for rec in self:
            policies = self.env['insurance.policy'].search([('state', '=', 'bill')]).mapped('id')
            return {'domain': {'policy_id': [('id', 'in', policies)]}}

    @api.onchange('policy_id', 'state')
    def _get_allowed_class(self):
        for rec in self:
            class_ids = rec.policy_id.policy_class_ids.mapped('class_id.id')
            return {'domain': {'allowed_class_id': [('id', 'in', class_ids)]},
                    'value': {'allowed_class_id': class_ids[0] if len(class_ids) > 0 else None}}

    @api.onchange('policy_id', 'state')
    def _get_selected_class(self):
        for rec in self:
            class_ids = rec.policy_id.policy_class_ids.mapped('class_id.id')
            return {'domain': {'selected_class_id': [('id', 'in', class_ids)]},
                    'value': {'selected_class_id': class_ids[0] if len(class_ids) > 0 else None}}

    # @api.onchange('policy_id', 'allowed_class_id','selected_class_id')
    # def _get_amounts(self):
    # self.allowed_class_amount = 0.0
    # self.selected_class_amount = 0.0
    # if self.allowed_class_id:
    #     self.allowed_class_amount = self.env['insurance.policy.class'].search([('class_id', '=', self.allowed_class_id.id),('policy_id', '=', self.policy_id.id)]).amount
    # if self.selected_class_id:
    #     self.selected_class_amount = self.env['insurance.policy.class'].search([('class_id', '=', self.selected_class_id.id),('policy_id', '=', self.policy_id.id)]).amount

    def _get_amount_difference(self):
        for rec in self:
            rec.amount_difference = rec.selected_class_amount - rec.allowed_class_amount
            rec._check_need_loan()

    def action_confirm(self):
        self.state = 'confirm'
        self._check_need_loan()

    @api.onchange('cost_to_employee')
    def _check_need_loan(self):
        # Function to check if membership should pay loan

        for rec in self:
            rec.need_loan = False
            if rec.state == 'confirm':
                if rec.cost_to_employee or rec.amount_difference > 0.0:
                    rec.need_loan = True

    def action_create_loan(self):
        loan_obj = self.env['hr.loan']
        loan_amount = 0.0
        if self.cost_to_employee:
            loan_amount = self.selected_class_amount
        elif self.amount_difference > 0.0:
            loan_amount = self.amount_difference

        if loan_amount > 0:
            loan_id = loan_obj.create({
                "name": _("{} - Insurance Difference Amount".format(
                    self.employee_id.name or self.family_id.employee_id.name)),
                "date": fields.Date.today(),
                "employee_id": self.employee_id.id or self.family_id.employee_id.id,
                "company_id": self.company_id.id,
                "loan_type_id": self.loan_type_id.id,
                "currency_id": self.currency_id.id,
                "loan_amount": loan_amount,
                "state": "draft",
                "insurance_id":self.id,
            })
            if loan_id:
                loan_id._onchange_loan_type_id()
                self.compute_loan_count()
                self.loan_id = loan_id.id
                self.need_loan = False

    def action_draft(self):
        self.state = 'draft'
        self.need_loan = False

    def action_view_loan(self):
        # loan_obj = self.env.ref('sharek_hr_employee_loan.hr_loan_form_view')
        return {
            'name': _('Membership Loans'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.loan',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('insurance_id', '=', self.id)],
        }
        # return {'name': _("{} Membership Difference").format(self.employee_id.name or self.family_id.employee_id.name),
        #         # 'view_mode': 'form',
        #         'view_mode': 'tree,form',
        #         'domain': [('insurance_id', '=', self.id)],
        #         'res_model': 'hr.loan',
        #         'view_id': loan_obj.id,
        #         'type': 'ir.actions.act_window',
        #         'nodestroy': True,
        #         'target': 'current',
        #         'res_id': self.loan_id.id,
        #         'context': {}}
