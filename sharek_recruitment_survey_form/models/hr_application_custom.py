# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrInterviewForm(models.Model):
    _name = 'hr.interview.form'
    _description = 'Job Interview Form'
    _rec_name = 'candidate_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Interview Ref", readonly=True, copy=False, default='New')

    candidate_name = fields.Char(string="Candidate Full Name")
    applied_job_id = fields.Many2one('hr.job', string="Applied Job")
    applicant_id = fields.Many2one('hr.applicant', string="Applied Job")

    applied_job_name = fields.Char()
    nationality = fields.Char()
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    criteria_ids = fields.One2many('hr.interview.criteria', 'form_id', string="Evaluation Criteria")

    # Comments
    strengths = fields.Text(string="Strengths")
    weaknesses = fields.Text(string="Weaknesses")
    recommendations = fields.Selection([
        ('recommend_hire', 'Recommend Hiring'),
        ('not_suitable', 'Not Suitable for Position'),
        ('on_hold', 'On Hold'),
    ], string="Post-Interview Recommendation")

    # Committee Review
    interviewer_ids = fields.Many2many('res.users', string="Interviewers")
    recruiter_id = fields.Many2one('res.users')
    factor_notes = fields.Text(string="Factor Notes")
    # Total score

    total_score = fields.Integer(
        string="Total Evaluation Score",
        compute="_compute_total_score"
    )
    department_id = fields.Many2one('hr.department', string="Department", compute="_compute_department")

    date = fields.Date(string="Interview Date", default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
    ], string='Status', default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.interview.form') or 'New'
        return super().create(vals)

    @api.depends('criteria_ids.score')
    def _compute_total_score(self):
        for rec in self:
            total = 0
            for line in rec.criteria_ids:
                if line.score:
                    total += int(line.score)
            rec.total_score = total

    @api.depends('applied_job_id')
    def _compute_department(self):
        for rec in self:
            rec.department_id = rec.applied_job_id.department_id

    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'
             

class HrInterviewCriteria(models.Model):
    _name = 'hr.interview.criteria'
    _description = 'Interview Evaluation Criteria'

    form_id = fields.Many2one('hr.interview.form', string="Interview Form")
    factor = fields.Char(string="Factor")
    indicator = fields.Char(string="Indicator")
    score = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ], string="Score")
    

# class HrInterviewInterviewer(models.Model):
#     _name = 'hr.interview.interviewer'
#     _description = 'Interview Committee Member'

#     form_id = fields.Many2one('hr.interview.form', string="Interview Form")
#     name = fields.Char(string="Name")
#     signature_date = fields.Date(string="Signature & Date")



class HrJobInherit(models.Model):
    _inherit = 'hr.job'

    factor_indicator_line_ids = fields.One2many(
        'job.factor.indicator.line',
        'job_id',
        string='Factors & Indicators'
    )

    factor_notes = fields.Text(string="Factor/Indicator Notes")





class JobFactorIndicatorLineInherit(models.Model):
    _name = 'job.factor.indicator.line'
    _description = 'Job Factor & Indicator Line'

    job_id = fields.Many2one('hr.job', string="Job Position", ondelete='cascade')
    factor = fields.Char(string="Factor", required=True)
    indicator = fields.Char(string="Indicator", required=True)   



