# -- coding: utf-8 --
######################################################################################
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class EmployeeEndOfServicesSummary(models.Model):
    _name = 'hr.employee.end.services.summary'
    _description = 'Employee Summary'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.today)
    line_ids = fields.One2many('hr.employee.end.services.summary.line', 'summary_id', string='Employee Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
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
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.end.services.summary') or 'New'
        return super(EmployeeEndOfServicesSummary, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('You can only delete records that are darft.')
        return super(EmployeeEndOfServicesSummary, self).unlink()


    def compute_employee_summary(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('Please add employee lines before computing the summary.'))
            for line in record.line_ids:
                vals = line.prepare_line_vals()
                print ("------vals",vals)
                line.write(vals)
                line._compute_last_service()
                
class EmployeeEndOfServicesSummaryLine(models.Model):
    _name = 'hr.employee.end.services.summary.line'
    _description = 'Employee Summary Line'

    summary_id = fields.Many2one('hr.employee.end.services.summary', string='Summary', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_no = fields.Char(related='employee_id.employee_no', string='Employment ID', store=True)
    job_id = fields.Char(related=False, string='Job Position', store=True)
    department_id = fields.Char(related=False, string='Department', store=True)
    join_date = fields.Date(related='employee_id.join_date', string='Join Date', store=True)
    contract_id = fields.Many2one('hr.contract', related=False, string='Contract', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", store=True)
    basic_salary = fields.Monetary(
        related=False,
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
    service_days = fields.Float(string='Service Days')
    total_service_balance = fields.Monetary(
        string='Total Service Balance',
        compute='_compute_total_service_balance',
        store=True,
        currency_field='currency_id',
    )
    last_service_days = fields.Float(compute='_compute_last_service', string='Last Service Days', store=True)
    last_total_service_balance = fields.Monetary(string='Last Total Service Balance', compute='_compute_last_service',store=True, )
    difference_days = fields.Float(string='Difference Days', compute='_compute_difference_days', store=True)

    @api.depends('service_days', 'last_service_days')
    def _compute_difference_days(self):
        for record in self:
            record.difference_days = record.service_days - record.last_service_days
            
    
    @api.depends('total_gross_salary', 'service_days')
    def _compute_total_service_balance(self):
        for record in self:
            if record.total_gross_salary and record.service_days:
                record.total_service_balance = record.service_days * (record.total_gross_salary / 720)
            else:
                record.total_service_balance = 0.0
         
                
    @api.depends('employee_id', 'summary_id')
    def _compute_last_service(self):
        for record in self:
            if not record.employee_id or not record.summary_id:
                record.last_service_days = 0.0
                record.last_total_service_balance = 0.0
                continue
            summary_date = record.summary_id.date
            last_service= self.env['hr.employee.end.services.summary'].search([('id','!=',record.summary_id.id),
                                                                 ('date', '<=', summary_date)], order='date desc', limit=1)
            last_service = last_service.line_ids.filtered(lambda emp: emp.employee_id.id == record.employee_id.id)

            record.last_service_days = last_service and last_service.service_days or 0.0
            record.last_total_service_balance = last_service and last_service.total_service_balance or 0.0


    def prepare_line_vals(self):
        """
        Prepare values for the line based on the employee's leave allocations and taken leaves.
        """
        self.ensure_one()
        contract_id = self.employee_id.contract_id
        return {
            'contract_id': self.contract_id.id,
            'department_id': self.employee_id.department_id.name,
            'job_id': self.employee_id.job_id.name,
            'basic_salary': contract_id.wage,
            'hra': contract_id.hra,
            'transport_allowance': contract_id.transport_allowance,
            'other_allowance': contract_id.other_allowance,
            'total_gross_salary': contract_id.total_gross_salary,
            'service_days': self.get_service_days(),  # This will be computed later
        }
        
        
    def get_service_days(self):
        for record in self:
            service_days = 0
            join_date = record.join_date or record.employee_id.contract_id.date_start
            summary_date = record.summary_id.date
            if record.employee_id and date:
                service_days = (summary_date - join_date).days
            return service_days
    

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
