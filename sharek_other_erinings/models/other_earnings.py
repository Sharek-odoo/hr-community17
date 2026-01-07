# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import random

class OtherEarnings(models.Model):
    _name = "other.earnings"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Other Earnings"
    
    name = fields.Char(default="New", readonly=True, copy=False)
    start_date = fields.Date(default=fields.Date.today(), string="Create Date")
    amount = fields.Float("Amount")
    type = fields.Selection([('allowance', 'Allowance'),('deduction', 'Deduction')], string="Type", default='')
    applied_to = fields.Selection([
        ('emplopyee', 'Employee'),
        ('department', 'Department'),
        ('project', 'Project'),
        ('task', 'Task'),
        ('company', 'Company')], string="Applied To")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_approval', 'Under Approval'),
        ('approve', 'Approved'),
        ('confirm', 'Confirm'),
        ('paid', 'Paid'),
        ('cancel', 'Cancel')], string="State", default='draft',tracking=True)
    company_ids = fields.Many2many('res.company')
    department_ids = fields.Many2many('hr.department')
    employee_ids = fields.Many2many('hr.employee')
    project_ids = fields.Many2many('project.project')
    task_ids = fields.Many2many('project.task')
    earnings_ids = fields.One2many('other.earnings.line', 'earnings_line_id')
    journal_count = fields.Integer('Journal Entries', compute="_get_earning_journal_count")
    journal_id = fields.Many2one('account.journal')
    description = fields.Text(string="Description")
    earnings_type = fields.Selection([('receipt','Receipt'),('payroll','Payroll')],string="Earnings Type")
     
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('other.earning.seq') or ('New')
        return super(OtherEarnings, self).create(vals)

    @api.onchange('applied_to')
    def onchange_applied(self):
        self.employee_ids = self.department_ids = self.company_ids = self.project_ids = self.task_ids = self.earnings_ids = [(5, 0, 0)]

    def update_earning_ids(self, employee_ids):
        earnings_lines = [(5, 0, 0)]
        for emp in employee_ids:
            earnings_lines.append((0, 0, {
                'employee_id': emp.id,
                'date': fields.Date.today(),
                'earnings_line_id': self.id,
            }))
        self.earnings_ids = earnings_lines

    @api.onchange('company_ids')
    def onchange_company_ids(self):
        emp_ids = self.env['hr.employee'].search([('company_id', '=', self.company_ids.ids)])
        self.update_earning_ids(emp_ids)

    @api.onchange('department_ids')
    def onchange_department_ids(self):
        emp_ids = self.env['hr.employee'].search([('department_id', '=', self.department_ids.ids)])
        self.update_earning_ids(emp_ids)

    @api.onchange('employee_ids')
    def onchange_employee_ids(self):
        emp_ids = self.env['hr.employee'].search([('id', '=', self.employee_ids.ids)])
        self.update_earning_ids(emp_ids)

    @api.onchange('project_ids')
    def onchange_project_ids(self):
        project_ids = self.env['project.project'].search([('id', 'in', self.project_ids.ids)])
        self.update_earning_ids(project_ids.mapped('task_ids').mapped('timesheet_ids').mapped('employee_id'))

    @api.onchange('task_ids')
    def onchange_task_ids(self):
        task_ids = self.env['project.task'].search([('id', 'in', self.task_ids.ids)])
        self.update_earning_ids(task_ids.mapped('timesheet_ids').mapped('employee_id'))

    def action_under_approval(self):
        if not self.earnings_ids:
            raise ValidationError(_("Please select some employees"))
        self.write({'state': 'under_approval'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def compute_amount(self):
        for rec in self.earnings_ids:
            if not rec.amount:
                rec.amount = self.amount
            if not rec.date:
                rec.date = fields.Date.today()

    def action_paid(self):
        if self.earnings_ids:
            self.create_extra_journal_entries()
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def _get_earning_journal_count(self):
        for rec in self:
            journal_ids = self.env['account.move'].search([('other_earnings_id', '=', rec.id)])
            rec.journal_count = len(journal_ids.ids)

    def action_journal_entries(self):
        journal_ids = self.env['account.move'].search([('other_earnings_id', '=', self.id)])
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', journal_ids.ids)],
        }

    #Create Journal Entries 
    def create_extra_journal_entries(self):
        move_line_ids = []
        move_id = self.env['account.move'].search([('other_earnings_id', '=', self.id)], limit=1)
        if move_id:
            return True

        move_obj = self.env['account.move']
        journal_id = self.journal_id
        timenow = fields.Date.today()
        company_id = self.env.user.company_id
        credit_account_id = company_id.credit_account_id
        debit_account_id = company_id.debit_account_id
        earnings_type = self.type

        #Earnings Entry Create Journal
        for earnings in self.earnings_ids:
            employee_id = earnings.employee_id
            partner_id = employee_id.user_id.partner_id
            move = {
                'ref': "%s -> %s"%(self.name, "Other Earnings"),
                'journal_id': journal_id and journal_id.id,
                'date': timenow,
                'state': 'draft',
                'other_earnings_id': self.id,
                'move_type': 'entry',
            }
            if earnings_type == 'allowance':
                # debit move lines
                move_line_ids.append((0, 0, {
                    'name': "%s - %s"%(employee_id.name, "Other Earnings"),
                    'partner_id': partner_id and partner_id.id,
                    'account_id': debit_account_id.id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': earnings.amount > 0.0 and earnings.amount or 0.0,
                    'credit': earnings.amount < 0.0 and -earnings.amount or 0.0,
                }))

                # credit move lines
                move_line_ids.append((0, 0, {
                    'name': "%s - %s"%(employee_id.name, "Other Earnings"),
                    'partner_id': partner_id and partner_id.id,
                    'account_id': credit_account_id.id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': earnings.amount < 0.0 and -earnings.amount or 0.0,
                    'credit': earnings.amount > 0.0 and earnings.amount or 0.0,
                }))

            if earnings_type == 'deduction':
                # debit move lines
                move_line_ids.append((0, 0, {
                    'name': "%s - %s"%(employee_id.name, "Other Earnings"),
                    'partner_id': partner_id and partner_id.id,
                    'account_id': credit_account_id.id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': earnings.amount > 0.0 and earnings.amount or 0.0,
                    'credit': earnings.amount < 0.0 and -earnings.amount or 0.0,
                }))

                # credit move lines
                move_line_ids.append((0, 0, {
                    'name': "%s - %s"%(employee_id.name, "Other Earnings"),
                    'partner_id': partner_id and partner_id.id,
                    'account_id': debit_account_id.id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': earnings.amount < 0.0 and -earnings.amount or 0.0,
                    'credit': earnings.amount > 0.0 and earnings.amount or 0.0,
                }))
            move.update({'line_ids': move_line_ids})
        move_id = move_obj.create(move)
        return True


class OtherEarningsLine(models.Model):
    _name = "other.earnings.line"
    _description = 'Other Earnings Lines'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount')
    date = fields.Date(string='Date')
    earnings_line_id = fields.Many2one('other.earnings', ondelete='cascade', select=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    other_earnings_id = fields.Many2one('other.earnings')


class HRPayrollAllow(models.Model):
    _inherit = 'hr.payslip'


    incentive_amount = fields.Float(compute="_compute_incentive_amount")
    deduction_amount = fields.Float(compute="_compute_deduction_amount")

    def _compute_incentive_amount(self):
        incentive = 0.0
        for pay in self:
            incentive_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','allowance')])
            for rec in incentive_line:
                incentive += rec.amount
        self.incentive_amount = incentive

    def _compute_deduction_amount(self):
        ded = 0.0
        for pay in self:
            incentive_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','deduction')])
            for rec in incentive_line:
                ded += rec.amount
        self.deduction_amount = ded        


    def compute_sheet(self):
        for rec in self:
            rec._compute_incentive_amount()
            rec._compute_deduction_amount()
        return super(HRPayrollAllow,self).compute_sheet()
