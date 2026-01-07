# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class hr_appraisal_criteria_assignment(models.Model):
    _name = 'hr.appraisal.criteria.assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Appraisal Criteria Assignment'

    name = fields.Char(string='Name', required=True, tracking=True, default='New')
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        tracking=True,
    )
    employee_no = fields.Char(string='Employee ID', related='employee_id.employee_no', store=True)
    department_id = fields.Many2one('hr.department',string='Department')
    job_id = fields.Many2one('hr.job',string='Job Position')
    appraisal_manager_id = fields.Many2one('hr.employee', string='Appraisal Manager',tracking=True)
    appraisal_date = fields.Date(string='Appraisal Date',tracking=True)
    date = fields.Date(string='Date', default=fields.Date.today(), tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Waiting Direct Manager'),
         ('validate', 'Waiting Employee'),
         ('hr', 'Waiting HR'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        string='Status',
        default='draft',
        tracking=True,
        readonly=True,
        copy=False,
    )
    assignment_goal_line_ids = fields.One2many(
        'hr.appraisal.assignment.goal.line',
        'appraisal_criteria_assignmet_id',
        string='Assignment Goal Lines',
        copy=True,
    )
    assignment_competence_line_ids = fields.One2many(
        'hr.appraisal.assignment.competence.line',
        'appraisal_criteria_assignmet_id',
        string='Assignment Competence Lines',
        copy=True,
    )
    assignment_competence_ids = fields.One2many(
        'hr.appraisal.assignment.competence',
        'appraisal_criteria_assignmet_id',
        string='Assignment Competence Lines',
        copy=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        tracking=True,
    )
    goal_percentage = fields.Float(string='Goal Percentage (%)')
    competence_percentage = fields.Float(string='Competence Percentage (%)')
    allowed_competence_ids = fields.Many2many(
        'hr.appraisal.job.competence',
        string='Allowed Competences',
        compute='_compute_allowed_competence_ids',)
    
    @api.depends('assignment_competence_ids','assignment_competence_ids.competence_id')
    def _compute_allowed_competence_ids(self):
        for record in self:
            record.allowed_competence_ids = record.assignment_competence_ids.mapped('competence_id')
            
            
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.job_id = self.employee_id.job_id
            self.appraisal_manager_id = self.employee_id.parent_id
            self.assignment_goal_line_ids = [(5, 0, 0)]
            self.assignment_competence_line_ids = [(5, 0, 0)]
            # if self.employee_id.competence_level_id:
            #     appraisal_competences = self.env['hr.appraisal.job.competence.index'].search([
            #         ('competence_level_id', '=', self.employee_id.competence_level_id.id),
            #         ('company_id', '=', self.company_id.id),
            #     ])
            #     for competence_index in appraisal_competences:
            #         assignment_competence_line_ids += [(0, 0, {
            #             'competence_id': competence_index.competence_id.id,
            #             'weight': competence_index.competence_id.weight,
            #             'competence_index_id': competence_index.id,
            #         })]
            # self.assignment_competence_line_ids = assignment_competence_line_ids
        else:
            self.department_id = False
            self.job_id = False
            self.appraisal_manager_id = False
            self.assignment_competence_line_ids = [(5, 0, 0)]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            self_comp = self.with_company(company_id)
            seq_date = None
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('appraisal.assignment', sequence_date=seq_date) or '/'
        records = super(hr_appraisal_criteria_assignment, self).create(vals_list)
        records.update_competence_lines()  # Update competence lines after creation
        return records
    
    
    def write(self, vals):
        res = super(hr_appraisal_criteria_assignment, self).write(vals)
        self.update_competence_lines()
        return res
    
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError("You cannot delete a record that is not in draft state.")
        return super(hr_appraisal_criteria_assignment, self).unlink()
    
    
    def action_confirm(self):
        for record in self:
            if not record.assignment_goal_line_ids:
                raise ValidationError("Please add at least one goal.")
            if not record.assignment_competence_line_ids:
                raise ValidationError("Please add at least one competence.")
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'confirm'
            record.message_post(body="Appraisal Assignment is waiting for Direct Manager Approval")
    
    def action_direct_manager(self):
        for record in self:
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'validate'
            record.message_post(body="Appraisal Assignment is waiting for Employee Approval")
    
    def action_employee(self):
        for record in self:
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'hr'
            record.message_post(body="Appraisal Assignment is waiting for HR Approval")
    
    def action_done(self):
        for record in self:
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'done'
            record.message_post(body="Appraisal Assignment Completed")
    
    
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
            record.message_post(body="Appraisal Assignment Cancelled")
    
    
    def action_draft(self):
        for record in self:
            record.state = 'draft'
            record.message_post(body="Appraisal Assignment Reset to Draft")
            
    def _check_weight_sum(self):
        for record in self:
            total_weight = sum(line.weight for line in record.assignment_goal_line_ids)
            if total_weight != 100:
                raise ValidationError(_("The total weight of goals must be 100%."))
    
    def _check_weight_sum_competence(self):
        for record in self:
            total_weight = sum(line.weight for line in record.assignment_competence_ids)
            if total_weight != 100:
                raise ValidationError(_("The total weight of competences must be 100%."))
            
    def _check_weight_sum_competence_line(self):
        for record in self:
            competences = record.assignment_competence_line_ids.mapped('competence_id')
            for competence in competences:
                total_weight = sum(line.weight for line in record.assignment_competence_line_ids.filtered(lambda l: l.competence_id.id == competence.id))
                if total_weight != 100:
                    raise ValidationError(_("The total weights of indexes related to the competence: %s must be 100%.") % competence.name)
    
    @api.constrains('goal_percentage', 'competence_percentage')
    def _check_percentage(self):
        for record in self:
            if record.goal_percentage + record.competence_percentage != 100 and record.state not in ['draft', 'cancel']:
                raise ValidationError(_("The total percentage of goals and competences must be 100%."))
    
    def update_competence_lines(self):
        for record in self:
            for competence in record.allowed_competence_ids:
                existing_line = record.assignment_competence_line_ids.filtered(lambda l: l.competence_id.id == competence.id)
                # If the competence line already exists, skip creating a new one
                if not existing_line:
                    appraisal_competences = self.env['hr.appraisal.job.competence.index'].search([
                        ('competence_level_id', '=', self.employee_id.competence_level_id.id),
                        ('competence_id', '=', competence.id),
                        ('company_id', '=', self.company_id.id),
                    ], order='sequence')
                    weight = 100 / len(appraisal_competences) if appraisal_competences else 0
                    for index in appraisal_competences:
                        self.env['hr.appraisal.assignment.competence.line'].create({
                            'appraisal_criteria_assignmet_id': record.id,
                            'competence_id': competence.id,
                            'weight': weight,
                            'competence_index_id': index.id,
                        })
            # Remove lines for competences that are no longer in the record
            to_delete_lines = record.assignment_competence_line_ids.filtered(
                lambda l: l.competence_id.id not in record.allowed_competence_ids.ids
            )
            if to_delete_lines:
                to_delete_lines.unlink()
                
                    
class hr_appraisal_assignment_goal_line(models.Model):
    _name = 'hr.appraisal.assignment.goal.line'    
    _description = 'HR Appraisal Assignment Goal Line'
    
    appraisal_criteria_assignmet_id = fields.Many2one(
        'hr.appraisal.criteria.assignment',
        string='Appraisal Criteria Assignment',
        ondelete='cascade',
    )
    goal_id = fields.Many2one(
        'hr.appraisal.goal',
        string='Goal',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)

    evaluation_standard = fields.Text(string='Evaluation Standard', required=True)


class hr_appraisal_assignment_competence(models.Model):
    _name = 'hr.appraisal.assignment.competence'
    _description = 'HR Appraisal Assignment Competence'

    appraisal_criteria_assignmet_id = fields.Many2one(
        'hr.appraisal.criteria.assignment',
        string='Appraisal Criteria Assignment',
        ondelete='cascade',
    )
    competence_id = fields.Many2one(
        'hr.appraisal.job.competence',
        string='Competence',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)

class hr_appraisal_assignment_competence_line(models.Model):
    _name = 'hr.appraisal.assignment.competence.line'
    _description = 'HR Appraisal Assignment Competence Line'
    
    appraisal_criteria_assignmet_id = fields.Many2one(
        'hr.appraisal.criteria.assignment',
        string='Appraisal Criteria Assignment',
        ondelete='cascade',
    )
    competence_id = fields.Many2one(
        'hr.appraisal.job.competence',
        string='Competence',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)

    competence_index_id = fields.Many2one(
        'hr.appraisal.job.competence.index',
        string='Behavioral Indicators of Competences',
    )
                
    @api.onchange('competence_id')
    def _onchange_competence_id(self):
        self.competence_index_id = False
            
            