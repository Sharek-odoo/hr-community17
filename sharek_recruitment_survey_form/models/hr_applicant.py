# -*- coding: utf-8 -*-

from odoo import models, fields, api



class Applicant(models.Model):
    _inherit = "hr.applicant"

    nationality = fields.Char()
    
    interview_form_id = fields.Many2one('hr.interview.form',string="Interview Form",required=True)
    all_interview_form_count = fields.Integer(compute="_compute_all_interview_form_count")

    def _compute_all_interview_form_count(self):
        for rec in self:
            rec.all_interview_form_count = self.env['hr.interview.form'].search_count([('applicant_id','=',self.id)])

    def create_candidit(self):
        for interviewer in self.interviewer_ids:
            job = self.job_id
            factor_lines = []
            for line in job.factor_indicator_line_ids:
                factor_lines.append((0, 0, {
                    'factor': line.factor,
                    'indicator': line.indicator
                }))

            interview_form_id = self.env['hr.interview.form'].create({
                'candidate_name': self.name,
                'nationality': self.nationality,
                'applicant_id': self.id,
                'applied_job_id': job.id,
                'interviewer_ids': interviewer.ids,
                'recruiter_id': self.user_id.id,
                'criteria_ids': factor_lines,
                'factor_notes': job.factor_notes,
            })


    def action_view_interview_form(self):
        return {
            'type':'ir.actions.act_window',
            'name':'Interview Form',
            'res_model':'hr.interview.form',
            'view_mode':'tree,form',
            'domain':[('applicant_id','=',self.id)]
        }


class Jops(models.Model):
    _inherit = "hr.job"
    interview_form_id = fields.Many2one('hr.interview.form',string="Interview Form",required=True)
    all_interview_form_count = fields.Integer(compute="_compute_all_interview_form_count")

    def _compute_all_interview_form_count(self):
        for rec in self:
            rec.all_interview_form_count = self.env['hr.interview.form'].search_count([('applied_job_id','=',self.id)])

    def create_candidit(self):
        for interviewer in self.interviewer_ids:
            interview_form_id = self.env['hr.interview.form'].create({
                'candidate_name':interviewer.name,
                'applied_job_id':self.id,
                'applied_job_name':self.name,
                'interviewer_ids':self.interviewer_ids.ids,
                'recruiter_id':self.user_id.id,
            })


    def action_view_interview_form(self):
        return {
            'type':'ir.actions.act_window',
            'name':'Interview Form',
            'res_model':'hr.interview.form',
            'view_mode':'tree,form',
            'domain':[('applied_job_id','=',self.id)]
        }