# -- coding: utf-8 --
######################################################################################
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date,datetime


class EmployeeSummary(models.Model):
    _name = 'hr.employee.summary'
    _description = 'Employee Summary'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.today)
    line_ids = fields.One2many('hr.employee.summary.line', 'summary_id', string='Employee Lines')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', tracking=True)

    def get_all_employee(self):
        for record in self:
            contract_ids = self.env['hr.contract'].search([('state','=','open')])
            for contract in contract_ids:
                if contract.employee_id.id not in record.line_ids.mapped('employee_id.id') :
                    record.write({"line_ids":[(0, 0, {'employee_id':contract.employee_id.id})]})
            if record.line_ids:
                record.compute_employee_summary()
                
                
    def action_submit(self):
        for record in self:
            record.state = 'submitted'

    def action_approve(self):
        for record in self:
            record.state = 'approved'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for record in self:
            record.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.summary') or 'New'
        return super(EmployeeSummary, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('You can only delete records that are darft.')
        return super(EmployeeSummary, self).unlink()
    
    def compute_employee_summary(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('Please add employee lines before computing the summary.'))
            for line in record.line_ids:
                vals = line.prepare_line_vals()
                line.write(vals)
                line._compute_remaining_leaves()
                line._compute_last_leave()


class EmployeeSummaryLine(models.Model):
    _name = 'hr.employee.summary.line'
    _description = 'Employee Summary Line'

    summary_id = fields.Many2one('hr.employee.summary', string='Summary', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_no = fields.Char(related='employee_id.employee_no', string='Employment ID', store=True)
    job_id = fields.Char(related='employee_id.job_id.name', string='Job Position', store=True)
    department_id = fields.Char(related='employee_id.department_id.name', string='Department', store=True)
    join_date = fields.Date(related='employee_id.join_date', string='Join Date', store=True)
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id', string='Contract', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", store=True)
    basic_salary = fields.Monetary(
        related='contract_id.wage',
        currency_field='currency_id',
        string='Basic Salary',
        store=True
    )
    hra = fields.Monetary(
        related=False,
        currency_field='currency_id',
        string='Housing Allowance',
        store=True
    )
    transport_allowance = fields.Monetary(
        related=False,
        currency_field='currency_id',
        string='Transportation Allowance',
        store=True
    )
    other_allowance = fields.Monetary(
        related=False,
        currency_field='currency_id',
        string='Other Allowance',
        store=True
    )
    total_gross_salary = fields.Monetary(
        related=False,
        currency_field='currency_id',
        string='Total Salary',
        store=True
    )
    remaining_leaves = fields.Float(compute='_compute_remaining_leaves', string='Remaining Leaves', store=True)
    total_leave_balance = fields.Monetary(string='Total Leave Balance', compute='_compute_total_leave_balance',
                                          store=True, currency_field='currency_id',
                                          )


    last_remaining_leaves = fields.Float(compute='_compute_last_leave', string='Last Remaining Leaves', store=True)
    last_total_leave_balance = fields.Monetary(string='Last Total Leave Balance', compute='_compute_last_leave',store=True)

    
    def prepare_line_vals(self):
        """
        Prepare values for the line based on the employee's leave allocations and taken leaves.
        """
        self.ensure_one()
        return {
           'basic_salary': self.contract_id.wage,
            'hra': self.contract_id.hra,
            'transport_allowance': self.contract_id.transport_allowance,
            'other_allowance': self.contract_id.other_allowance,
            'total_gross_salary': self.contract_id.total_gross_salary,
            
        }
        
    
    @api.depends('employee_id', 'summary_id')
    def _compute_last_leave(self):
        for record in self:
            if not record.employee_id or not record.summary_id:
                record.last_remaining_leaves = 0.0
                record.last_total_leave_balance = 0.0
                continue            
            summary_date = record.summary_id.date
            last_leave = self.env['hr.employee.summary'].search([('id','!=',record.summary_id.id),
                                                                 ('date', '<=', summary_date)], order='date desc', limit=1)
            last_leave = last_leave.line_ids.filtered(lambda emp: emp.employee_id.id == record.employee_id.id)

            record.last_remaining_leaves = last_leave and last_leave.remaining_leaves or 0.0
            record.last_total_leave_balance = last_leave and last_leave.total_leave_balance or 0.0


    @api.depends('remaining_leaves', 'total_gross_salary')
    def _compute_total_leave_balance(self):
        for record in self:
            if record.total_gross_salary and record.remaining_leaves:
                record.total_leave_balance = record.remaining_leaves * (record.total_gross_salary / 22)
            else:
                record.total_leave_balance = 0.0


    @api.depends('employee_id')
    def _compute_remaining_leaves(self):
        LeaveAllocation = self.env['hr.leave.allocation']
        Leave = self.env['hr.leave']
        for record in self:
            print ("----record",record)
            if not record.employee_id or not record.summary_id.date:
                record.remaining_leaves = 0
                continue
            
            # Get employee and summary date
            employee = record.employee_id
            summary_date = record.summary_id.date
            
            # Get first and last date of the year
            first_date = date(summary_date.year, 1, 1)
            last_date = date(summary_date.year, 12, 31)

            timeoff_days = record.contract_id.timeoff_days or 0.0
            # per_day = timeoff_days / 360

            # Transferred allocations
            transferred_allocs = LeaveAllocation.search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('transfered', '=', True),
                ('date_from', '>=', first_date),
                ('date_to', '>=', summary_date),
            ])
            transferred_days = sum(transferred_allocs.mapped('number_of_days'))
            print("transferred_days", transferred_days)

            # Accrued allocations (not transferred) in same year
            accrued_allocs = LeaveAllocation.search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('transfered', '=', False),
                ('date_from', '>=', first_date),
                ('date_to', '<=', last_date),
            ])
            prorated_days = 0.0
            for alloc in accrued_allocs:
                days_difference = (summary_date - alloc.date_from).days
                alloc_difference = (alloc.date_to - alloc.date_from).days
                per_day = alloc.number_of_days / alloc_difference if alloc.number_of_days else 0
                prorated_days += days_difference * per_day

            # Leaves taken from start of leave year to summary date
            leaves_taken = Leave.search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', first_date),
                ('request_date_from', '<=', summary_date),
            ])
            taken_days = sum(leaves_taken.mapped('number_of_days'))

            # Final computation
            record.remaining_leaves = (transferred_days + prorated_days) - taken_days

            
            
    @api.constrains('employee_id', 'summary_id')
    def _check_employee_summary_month(self):
        for line in self:
            if not line.employee_id or not line.summary_id or not line.summary_id.date:
                continue

            summary_date = line.summary_id.date
            month_start = summary_date.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

            existing_lines = self.search([
                ('id', '!=', line.id),
                ('employee_id', '=', line.employee_id.id),
                ('summary_id.date', '>=', month_start),
                ('summary_id.date', '<=', month_end),
            ], limit=1)

            if existing_lines:
                raise ValidationError(_(
                    "The employee %s already has a summary in %s."
                ) % (line.employee_id.name, summary_date.strftime('%B %Y')))
