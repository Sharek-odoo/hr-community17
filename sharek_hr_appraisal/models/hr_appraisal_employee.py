# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class hr_appraisal_employee(models.Model):
    _name = 'hr.appraisal.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Employee Appraisal'

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
         ('confirm', 'Confirmed'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        string='Status',
        default='draft',
        tracking=True,
        readonly=True,
        copy=False,
    )
    appraisal_goal_line_ids = fields.One2many(
        'hr.appraisal.goal.line',
        'appraisal_id',
        string='Appraisal Goal Lines',
        copy=True,
    )
    appraisal_competence_line_ids = fields.One2many(
        'hr.appraisal.competence.line',
        'appraisal_id',
        string='Appraisal Competence Lines',
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
    appraisal_criteria_assignmet_id = fields.Many2one(
        'hr.appraisal.criteria.assignment',
        string='Appraisal Criteria Assignment',
    )
    goal_percentage = fields.Float(string='Goal Percentage (%)')
    competence_percentage = fields.Float(string='Competence Percentage (%)')
    goal_weighted_grade = fields.Float(string='Goals Weighted Grade', compute='_compute_goal_weighted_grade', store=True)
    competence_weighted_grade = fields.Float(string='Competences Weighted Grade', compute='_compute_competence_weighted_grade', store=True)
    overall_grade = fields.Float(string='Overall Grade', compute='_compute_overall_grade', store=True)
    appraisal_competence_total_line_ids = fields.One2many(
        'hr.appraisal.competence.total.line',
        'appraisal_id',
        string='Appraisal Competence Total Lines',
        copy=False,
        compute=False,
        store=True,
    )
    allowed_competence_ids = fields.Many2many(
        'hr.appraisal.job.competence',
        string='Allowed Competences',
        compute='_compute_allowed_competence_ids',)
    
    
    @api.depends('appraisal_competence_total_line_ids','appraisal_competence_total_line_ids.competence_id')
    def _compute_allowed_competence_ids(self):
        for record in self:
            record.allowed_competence_ids = record.appraisal_competence_total_line_ids.mapped('competence_id')
            
    
    
    @api.depends('appraisal_goal_line_ids.weight_grade')
    def _compute_goal_weighted_grade(self):
        for record in self:
            total_weighted_grade = sum(line.weight_grade for line in record.appraisal_goal_line_ids) if record.appraisal_goal_line_ids else 0.0
            record.goal_weighted_grade = total_weighted_grade
    
    
    @api.depends('appraisal_competence_total_line_ids.weight_grade','appraisal_competence_total_line_ids.weight')
    def _compute_competence_weighted_grade(self):
        for record in self:
            total_weighted_grade = sum(line.weight_grade * (line.weight/100) for line in record.appraisal_competence_total_line_ids) if record.appraisal_competence_total_line_ids else 0.0
            record.competence_weighted_grade = total_weighted_grade
    
    
    @api.depends('goal_weighted_grade', 'competence_weighted_grade')
    def _compute_overall_grade(self):
        for record in self:
            if record.goal_percentage and record.competence_percentage:
                record.overall_grade = (record.goal_weighted_grade * record.goal_percentage / 100) + (record.competence_weighted_grade * record.competence_percentage / 100)
            else:
                record.overall_grade = 0.0
    
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.job_id = self.employee_id.job_id
            self.appraisal_manager_id = self.employee_id.parent_id
        else:
            self.department_id = False
            self.job_id = False
            self.appraisal_manager_id = False
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            self_comp = self.with_company(company_id)
            seq_date = None
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('employee.appraisal', sequence_date=seq_date) or '/'
        return super(hr_appraisal_employee, self).create(vals_list)
    
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError("You cannot delete a record that is not in draft state.")
        return super(hr_appraisal_employee, self).unlink()
    
    
    def action_confirm(self):
        for record in self:
            if not record.appraisal_goal_line_ids:
                raise ValidationError("Please add at least one goal.")
            if not record.appraisal_competence_line_ids:
                raise ValidationError("Please add at least one competence.")
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'confirm'
            record.message_post(body="Appraisal Confirmed")
    
    
    def action_done(self):
        for record in self:
            # Check if the total weight of goals and competences is 100%
            record._check_weight_sum()
            record._check_weight_sum_competence()
            record._check_weight_sum_competence_line()
            record.state = 'done'
            record.message_post(body="Appraisal Completed")
    
    
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
            record.message_post(body="Appraisal Cancelled")
    
    
    def action_draft(self):
        for record in self:
            record.state = 'draft'
            record.message_post(body="Appraisal Reset to Draft")
            
            
    def _check_weight_sum(self):
        for record in self:
            total_weight = sum(line.weight for line in record.appraisal_goal_line_ids)
            if total_weight != 100:
                raise ValidationError(_("The total weight of goals must be 100%."))
            
    
    def _check_weight_sum_competence(self):
        for record in self:
            total_weight = sum(line.weight for line in record.appraisal_competence_total_line_ids)
            if total_weight != 100:
                raise ValidationError(_("The total weight of competences must be 100%."))
            
    
    def _check_weight_sum_competence_line(self):
        for record in self:
            competences = record.appraisal_competence_total_line_ids.mapped('competence_id')
            for competence in competences:
                total_weight = sum(line.weight for line in record.appraisal_competence_line_ids.filtered(lambda l: l.competence_id.id == competence.id))
                if total_weight != 100:
                    raise ValidationError(_("The total weights of indexes related to the competence: %s must be 100%.", competence.name))
    
    
    @api.onchange('appraisal_criteria_assignmet_id')
    def _onchange_appraisal_criteria_assignmet_id(self):
        self.goal_percentage = self.appraisal_criteria_assignmet_id.goal_percentage
        self.competence_percentage = self.appraisal_criteria_assignmet_id.competence_percentage
        if self.appraisal_criteria_assignmet_id:
            appraisal_goal_line_ids = [(5, 0, 0)]
            appraisal_competence_line_ids = [(5, 0, 0)]
            appraisal_competence_total_line_ids = [(5, 0, 0)]
            for line in self.appraisal_criteria_assignmet_id.assignment_goal_line_ids:
                appraisal_goal_line_ids += [(0, 0, {
                    'goal_id': line.goal_id.id,
                    'weight': line.weight,
                    'evaluation_standard': line.evaluation_standard,
                })]
            for line in self.appraisal_criteria_assignmet_id.assignment_competence_line_ids:
                appraisal_competence_line_ids += [(0, 0, {
                    'competence_id': line.competence_id.id,
                    'weight': line.weight,
                    'competence_index_id': line.competence_index_id.id,
                })]
            for line in self.appraisal_criteria_assignmet_id.assignment_competence_ids:
                appraisal_competence_total_line_ids += [(0, 0, {
                    'competence_id': line.competence_id.id,
                    'weight': line.weight,
                })]
            # Set the appraisal goal and competence lines
            self.appraisal_competence_total_line_ids = appraisal_competence_total_line_ids
            self.appraisal_goal_line_ids = appraisal_goal_line_ids
            self.appraisal_competence_line_ids = appraisal_competence_line_ids
        else:
            self.appraisal_goal_line_ids = [(5, 0, 0)]
            self.appraisal_competence_line_ids = [(5, 0, 0)]
            self.appraisal_competence_total_line_ids = [(5, 0, 0)]
    
    
    @api.constrains('goal_percentage', 'competence_percentage')
    def _check_percentage(self):
        for record in self:
            if record.goal_percentage + record.competence_percentage != 100 and record.state not in ['draft', 'cancel']:
                raise ValidationError(_("The total percentage of goals and competences must be 100%."))
    
    
    def write(self, vals):
        res = super(hr_appraisal_employee, self).write(vals)
        self.update_competence_lines()
        return res
    
    
    def update_competence_lines(self):
        for record in self:
            for competence in record.allowed_competence_ids:
                existing_line = record.appraisal_competence_line_ids.filtered(lambda l: l.competence_id.id == competence.id)
                # If the competence line already exists, skip creating a new one
                if not existing_line:
                    appraisal_competences = self.env['hr.appraisal.job.competence.index'].search([
                        ('competence_level_id', '=', self.employee_id.competence_level_id.id),
                        ('competence_id', '=', competence.id),
                        ('company_id', '=', self.company_id.id),
                    ], order='sequence')
                    weight = 100 / len(appraisal_competences) if appraisal_competences else 0
                    for index in appraisal_competences:
                        self.env['hr.appraisal.competence.line'].create({
                            'appraisal_id': record.id,
                            'competence_id': competence.id,
                            'weight': weight,
                            'competence_index_id': index.id,
                        })
            # Remove lines for competences that are no longer in the record
            to_delete_lines = record.appraisal_competence_line_ids.filtered(
                lambda l: l.competence_id.id not in record.allowed_competence_ids.ids
            )
            if to_delete_lines:
                to_delete_lines.unlink()

class hr_appraisal_goal_line(models.Model):
    _name = 'hr.appraisal.goal.line'    
    _description = 'HR Appraisal Goal Line'
    
    appraisal_id = fields.Many2one(
        'hr.appraisal.employee',
        string='Employee Appraisal',
        ondelete='cascade',
    )
    goal_id = fields.Many2one(
        'hr.appraisal.goal',
        string='Goal',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)
    actual_result = fields.Float(string='Actual Result (%)', required=True)
    difference = fields.Float(string='Difference (%)', compute='_compute_difference', store=True)
    grade = fields.Selection(
        [('1', '1'),
         ('2', '2'),
         ('3', '3'),
         ('4', '4'),
         ('5', '5')],
        string='Grade',
    )
    weight_grade = fields.Float(string='Weighted Grade (%)', compute='_compute_weight_grade', store=True)
    evaluation_standard = fields.Text(string='Evaluation Standard')
    
    @api.depends('weight', 'grade')
    def _compute_weight_grade(self):
        for line in self:
            if line.weight and line.grade:
                line.weight_grade = (line.weight * int(line.grade)) / 100
            else:
                line.weight_grade = 0.0
    
    @api.depends('actual_result')
    def _compute_difference(self):
        for line in self:
            if line.actual_result:
                line.difference = line.actual_result - 100
            else:
                line.difference = 0.0
                
    
    @api.onchange('actual_result')
    def onchange_actual_result(self):
        grade = False
        if self.actual_result > 100:
            grade = '5'
        elif 100 >= self.actual_result >= 90:
            grade = '4'
        elif 89 >= self.actual_result >= 80:
            grade = '3'
        elif 79 >= self.actual_result >= 60:
            grade = '2'
        else:
            grade = '1'
        self.grade = grade
    
    
class hr_appraisal_competence_line(models.Model):
    _name = 'hr.appraisal.competence.line'
    _description = 'HR Appraisal Assignment Competence Line'
    
    appraisal_id = fields.Many2one(
        'hr.appraisal.employee',
        string='Appraisal Criteria Assignment',
        ondelete='cascade',
    )
    competence_id = fields.Many2one(
        'hr.appraisal.job.competence',
        string='Competence',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)
    # competence_description = fields.Text(string='Behavioral Indicators of Competences',
    #                                      )
    actual_result = fields.Float(string='Actual Result (%)')
    grade = fields.Selection(
        [('1', '1'),
         ('2', '2'),
         ('3', '3'),
         ('4', '4'),
         ('5', '5')],
        string='Grade',
    )
    weight_grade = fields.Float(string='Weighted Grade (%)', compute='_compute_weight_grade', store=True)
    competence_index_id = fields.Many2one(
        'hr.appraisal.job.competence.index',
        string='Behavioral Indicators of Competences',
    )
    
    @api.depends('weight', 'grade')
    def _compute_weight_grade(self):
        for line in self:
            if line.weight and line.grade:
                line.weight_grade = (line.weight * int(line.grade)) / 100
            else:
                line.weight_grade = 0.0
                
    @api.onchange('competence_id')
    def _onchange_competence_id(self):
        self.competence_index_id = False
        
        
class hr_appraisal_competence_total_line(models.Model):
    _name = 'hr.appraisal.competence.total.line'
    _description = 'HR Appraisal Assignment Competence Total Line'
    
    appraisal_id = fields.Many2one(
        'hr.appraisal.employee',
        string='Appraisal Criteria Assignment',
        ondelete='cascade',
    )
    competence_id = fields.Many2one(
        'hr.appraisal.job.competence',
        string='Competence',
        required=True,
    )
    weight = fields.Float(string='Weighted Value (%)', required=True)
    
    weight_grade = fields.Float(string='Weighted Grade (%)', compute='_compute_weight_grade', store=True)


    @api.depends('appraisal_id', 'appraisal_id.appraisal_competence_line_ids')
    def _compute_weight_grade(self):
        for line in self:
            competence_lines = line.appraisal_id.appraisal_competence_line_ids.filtered(lambda l: l.competence_id == line.competence_id)
            if competence_lines:
                total_weight_grade = sum(competence_lines.mapped('weight_grade'))
                line.weight_grade = total_weight_grade
            else:
                line.weight_grade = 0.0