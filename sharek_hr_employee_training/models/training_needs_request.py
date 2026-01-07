# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2025 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError




class TrainingNeedsRequest(models.Model):
    _name = 'training.needs.request'
    _description = 'Training Needs Request Form'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_date_to(self):
        today = date.today()
        return date(today.year, 12, 31)  # December 31st

    def _default_date_from(self):
        today = date.today()
        return date(today.year, 1, 1)  # January 1st

    name = fields.Char(string="Request No.", required=True, copy=False, readonly=True, default='New')
    request_date = fields.Date(string="Request Date", default=fields.Date.today())

    request_date_from = fields.Date( string="Date From", default=_default_date_from,tracking=True)
    request_date_to = fields.Date(string="Date To",default=_default_date_to,tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    job_title = fields.Many2one('hr.job', string="Job Title", compute='_compute_employee_fields')
    employee_number = fields.Char(string="Employee. No.", compute='_compute_employee_fields')
    email = fields.Char(string="Email", compute='_compute_employee_fields')
    department_id = fields.Many2one('hr.department', string="Department", compute='_compute_employee_fields')
    manager_id = fields.Many2one('hr.employee', string="Manager", compute='_compute_employee_fields')

    @api.depends('employee_id')
    def _compute_employee_fields(self):
        for rec in self:
            employee = rec.employee_id
            rec.job_title = employee.job_id.id
            rec.employee_number = employee.employee_no
            rec.email = employee.work_email
            rec.department_id = employee.department_id.id
            rec.manager_id = employee.parent_id.id

    line_ids = fields.One2many('training.needs.line', 'request_id', string="Training Lines")
    last_appraisal_id = fields.Many2one('hr.appraisal.employee', string='Last Appraisal',
                                        compute='_compute_last_appraisal')
    last_overall_grade = fields.Float(string='Last Appraisal Grade', compute='_compute_last_appraisal')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager', 'Direct Manager Approval'),
        ('hr', 'HR Approval'),
        ('ceo', 'CEO Approval'),
        ('hr_final', 'HR Final Review'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], string='Status', default='draft', tracking=True)
    total_cost = fields.Float(string="Total Cost", compute="_compute_total_cost")
    training_ids = fields.One2many(
        'hr.employee.training',
        'need_request_id',
        string="Employee Trainings"
    )

    remaining_cost = fields.Float(
        string="Remaining Cost",
        compute="_compute_remaining_cost"
    )
    refuse_reason = fields.Text(string="Refusal Reason")

    @api.depends('line_ids.cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = sum(rec.line_ids.mapped('cost'))

    @api.depends('training_ids.total_training_cost')
    def _compute_remaining_cost(self):
        for rec in self:
            rec.remaining_cost = rec.total_cost - sum(rec.training_ids.mapped('total_training_cost'))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('training.needs.request') or '/'
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You cannot delete a Training Needs Request unless it is in draft state."))
        return super().unlink()

    def action_submit_to_manager(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("You cannot confirm the training needs without at least one needs line.")
            rec.state = 'manager'

    def action_approve_manager(self):
        for rec in self:
            rec.state = 'hr'

    def action_approve_hr(self):
        for rec in self:
            rec.state = 'ceo'

    def action_ceo_approve(self):
        for rec in self:
            rec.state = 'hr_final'

    def action_hr_final_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('employee_id')
    def _compute_last_appraisal(self):
        for rec in self:
            if not rec.employee_id:
                rec.last_appraisal_id = False
                rec.last_overall_grade = 0.0
                continue

            appraisal = self.env['hr.appraisal.employee'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'done'),
            ], order='appraisal_date desc', limit=1)

            rec.last_appraisal_id = appraisal.id
            rec.last_overall_grade = appraisal.overall_grade or 0.0

    def action_open_trainings_employee(self):
        self.ensure_one()
        print("\n\n\n\n\n")
        print("*************self", self.id, self.name)
        return {
            'name': _('Employee Trainings'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.training',
            'view_mode': 'tree,form',
            'domain': [('need_request_id', '=', self.id)],
            'context': {'default_need_request_id': self.id},
            'target': 'current',
        }
