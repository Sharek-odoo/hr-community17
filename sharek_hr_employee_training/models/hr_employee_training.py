# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError

class HrEmployeeTraining(models.Model):
    _name = 'hr.employee.training'
    _description = 'Employee Training'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, default="New", tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)

    job_title = fields.Many2one('hr.job', string="Job Title", compute='_compute_employee_fields')
    employee_number = fields.Char(string="Emp. No.", compute='_compute_employee_fields')
    email = fields.Char(string="Email", compute='_compute_employee_fields')
    department_id = fields.Many2one('hr.department', string="Department", compute='_compute_employee_fields')
    manager_id = fields.Many2one('hr.employee', string="Manager", compute='_compute_employee_fields')

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager', 'Direct Manager Approved'),
        ('hr', 'HR Approved'),
        ('hr_final', 'Final HR Approved'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], string="Status", default="draft", tracking=True)

    in_company = fields.Boolean(string="In Company")
    out_company = fields.Boolean(string="Out of Company")
    out_country = fields.Boolean(string="Out of Country")
    workshop = fields.Boolean(string="Workshop")
    training_course = fields.Boolean(string="Training Course")
    conference = fields.Boolean(string="Conference")
    webinar = fields.Boolean(string="Online")
    seminar = fields.Boolean(string="Seminar")
    expo = fields.Boolean(string="Global Exhibition")
    other = fields.Boolean(string="Other")

    need_request_id = fields.Many2one(
        'training.needs.request',
        string="Training Needs Request",
        compute='_compute_need_request_id',
        store=True,
    )

    training_course_ids = fields.Many2many(
        'training.course',
        string="Available Courses",
        compute='_compute_training_course_ids'
    )
    refuse_reason = fields.Text(string="Refusal Reason")

    
    line_ids = fields.One2many('hr.employee.training.line', 'employee_training_id', string="Training Lines")
    total_training_cost = fields.Float(
        string="Total Training Cost",
        compute="_compute_total_training_cost"
        
    )

    # remaining_cost = fields.Float(
    #     string="Remaining Cost from Needs Request",
    #     compute="_compute_remaining_cost"
    # )

    remaining_after = fields.Float(string="Remaining After", compute="_compute_remaining_costs")
    remaining_before = fields.Float(string="Remaining Before", compute="_compute_remaining_costs")

    @api.depends('line_ids.cost')
    def _compute_total_training_cost(self):
        for rec in self:
            rec.total_training_cost = sum(rec.line_ids.mapped('cost'))

    @api.depends('need_request_id', 'create_date', 'total_training_cost')
    def _compute_remaining_costs(self):
        for rec in self:
            if not rec.need_request_id:
                rec.remaining_before = 0.0
                rec.remaining_after = 0.0
                continue

            domain = [('need_request_id', '=', rec.need_request_id.id)]
            if rec.id and isinstance(rec.id, int):
                domain.append(('id', '!=', rec.id))

            trainings = self.env['hr.employee.training'].search(domain)

            earlier_trainings = trainings.filtered(
                lambda r: r.create_date and rec.create_date and r.create_date < rec.create_date
            )

            earlier_cost = sum(t.total_training_cost for t in earlier_trainings)

            rec.remaining_before = rec.need_request_id.total_cost - earlier_cost
            rec.remaining_after = rec.remaining_before - rec.total_training_cost



    @api.depends('line_ids.cost')
    def _compute_total_training_cost(self):
        for rec in self:
            rec.total_training_cost = sum(rec.line_ids.mapped('cost'))

    # @api.depends('need_request_id', 'total_training_cost', 'need_request_id.training_ids.total_training_cost')
    # def _compute_remaining_cost(self):
    #     for rec in self:
    #         if not rec.need_request_id:
    #             rec.remaining_cost = 0.0
    #             continue

    #         all_trainings = rec.need_request_id.training_ids.filtered(lambda r: r.id != rec.id)

    #         if rec.create_date:
    #             # Compare by creation date
    #             earlier_trainings = all_trainings.filtered(
    #                 lambda r: r.create_date and r.create_date < rec.create_date
    #             )
    #         else:
    #             # If unsaved, fallback to "all previous saved trainings"
    #             earlier_trainings = all_trainings.filtered(lambda r: isinstance(r.id, int))

    #         used_before = sum(earlier_trainings.mapped('total_training_cost'))
    #         rec.remaining_cost = rec.need_request_id.total_cost - used_before - rec.total_training_cost

    @api.depends('need_request_id')
    def _compute_training_course_ids(self):
        for rec in self:
            if rec.need_request_id:
                rec.training_course_ids = rec.need_request_id.line_ids.mapped('training_course_id')
            else:
                rec.training_course_ids = False

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_need_request_id(self):
        for rec in self:
            rec.need_request_id = False
            if rec.employee_id and rec.date_from and rec.date_to:
                request = self.env['training.needs.request'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('request_date_from', '<=', rec.date_from),
                    ('request_date_to', '>=', rec.date_to),
                    ('state', '=', 'approved'),
                ], limit=1)
                rec.need_request_id = request.id if request else False


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.training') or 'New'
        return super().create(vals)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You cannot delete a Employee Training unless it is in draft state."))
        return super().unlink()  



    @api.onchange('total_training_cost', 'need_request_id')
    def _onchange_check_training_cost_vs_remaining(self):
        if self.need_request_id:
            remaining = self.need_request_id.remaining_cost or 0.0
            if self.total_training_cost > remaining:
                return {
                    'warning': {
                        'title': "Cost exceeds remaining budget",
                        'message': f"Training cost ({self.total_training_cost:.2f}) exceeds remaining budget ({remaining:.2f}) of the training need."
                    }
                }


    @api.depends('employee_id')
    def _compute_employee_fields(self):
        for rec in self:
            emp = rec.employee_id
            rec.job_title = emp.job_id.id
            rec.employee_number = emp.employee_no
            rec.email = emp.work_email
            rec.department_id = emp.department_id.id
            rec.manager_id = emp.parent_id.id    


    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError("You cannot confirm the training request without at least one training line.")
            record.state = 'direct_manager'

    def action_approve_direct_manager(self):
        for record in self:
            record.state = 'hr'

    def action_approve_hr(self):
        for record in self:
            record.state = 'hr_final'

    def action_approve_hr_final(self):
        for record in self:
            record.state = 'approved'

    def action_set_draft(self):
        for rec in self:
            rec.state = 'draft'         


class HrEmployeeTrainingLine(models.Model):
    _name = 'hr.employee.training.line'
    _description = 'Employee Training Line'

    employee_training_id = fields.Many2one('hr.employee.training', string="Training Request", required=True, ondelete='cascade')
    
    training_course_id = fields.Many2one('training.course', string="Training Course",required=True)
    domain_id = fields.Many2one('training.domain', string="Domain")
    impact_id = fields.Many2one('training.impact', string="Impact")
    academy_id = fields.Many2one('training.academy', string="Academy")
    cost = fields.Float(string="Cost",required=True)

    start_date = fields.Date(string="Start Date",required=True)
    end_date = fields.Date(string="End Date",required=True)
    number_of_days = fields.Integer(string="Number of Days", compute="_compute_number_of_days", store=True)

    @api.onchange('training_course_id')
    def _onchange_training_course_id(self):
        if self.training_course_id:
            self.domain_id = self.training_course_id.domain_id
            self.impact_id = self.training_course_id.impact_id
            self.cost = self.training_course_id.cost

    @api.depends('start_date', 'end_date')
    def _compute_number_of_days(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date >= rec.start_date:
                rec.number_of_days = (rec.end_date - rec.start_date).days + 1
            else:
                rec.number_of_days = 0
            

    @api.constrains('start_date', 'end_date')
    def _check_line_dates_within_parent(self):
        for rec in self:
            parent = rec.employee_training_id
            if rec.start_date and (rec.start_date < parent.date_from or rec.start_date > parent.date_to):
                raise ValidationError(f"Start Date in line must be within the parent training period: {parent.date_from} to {parent.date_to}.")
            if rec.end_date and (rec.end_date < parent.date_from or rec.end_date > parent.date_to):
                raise ValidationError(f"End Date in line must be within the parent training period: {parent.date_from} to {parent.date_to}.")
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date must be after or equal to Start Date.")



