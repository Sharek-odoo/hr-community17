from odoo import models, fields,api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class HrProbationEvaluation(models.Model):
    _name = 'hr.probation.evaluation'
    _description = 'Employee Probation Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", default=lambda self: _('New'), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,domain="[('contract_id.need_trial_period', '=', True)]")
    employee_number = fields.Char(string="Employee Number", related='employee_id.employee_no', readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id', readonly=True)
    designation = fields.Many2one(string="Designation", related='employee_id.job_id', readonly=True)
    starting_date = fields.Date(string="Sart Work Date", related='employee_id.direct_work_date')
    # probation_period = fields.Char(string="Probation Period")  # or computed from contract
    contract_id = fields.Many2one('hr.contract', string="Contract")
    previous_end_trial_period = fields.Date(string="Previous Trial End Date")

    date = fields.Date(string="Evaluation Date", default=fields.Date.context_today)  # today by default
    
    end_trial_period = fields.Date(
        string="End of Trial Period",
        related='employee_id.contract_id.end_trial_period',
        readonly=True
    )
    line_ids = fields.One2many('hr.probation.evaluation.line', 'evaluation_id', string="Evaluation Lines")

    recommendation = fields.Selection([
        ('confirm', 'Confirm Employee'),
        ('extend', 'Extension of Probation Period'),
        ('reject', 'Do Not Confirm')
    ], string="Recommendation")

    notes = fields.Text(string="General Notes")
    evaluation_date = fields.Date(string="Evaluation Date", default=fields.Date.today)
    evaluator_id = fields.Many2one('hr.employee', string="Evaluator")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)
    average_score = fields.Float(string="Average Grade", compute='_compute_average_score',tracking=True)   
    current_user_can_grade = fields.Boolean(compute='_compute_current_user_can_grade')

    @api.depends('employee_id')
    def _compute_current_user_can_grade(self):
        for rec in self:
            rec.current_user_can_grade = (
                self.env.user == rec.employee_id.parent_id.user_id and rec.state == 'submit'
            )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.probation.evaluation') or _('New')

        if 'employee_id' in vals:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            if employee.contract_id:
                vals['contract_id'] = employee.contract_id.id
                vals['previous_end_trial_period'] = employee.contract_id.end_trial_period

        return super().create(vals)



    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    def action_confirm(self):
        for rec in self:
            if rec.employee_id.parent_id.user_id != self.env.user:
                raise ValidationError("Only the direct manager of the employee can confirm this request.")
            rec.state = 'confirmed'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            if rec.employee_id.contract_id:
                rec.contract_id = rec.employee_id.contract_id

                # End trial if recommendation is confirm
                if rec.recommendation == 'confirm':
                    rec.employee_id.contract_id.in_trial_period = False

                elif rec.recommendation == 'extend':
                    if rec.contract_id.trial_period == 'three_month':
                        rec.contract_id.trial_extension_months += 3
                    elif rec.contract_id.trial_period == 'six_month':
                        rec.contract_id.trial_extension_months += 6

                elif rec.recommendation == 'reject':
                    # Cancel contract
                    contract = rec.employee_id.contract_id
                    contract.state = 'cancel'  # or 'terminated' if you have that state
                    contract.date_end = fields.Date.today()

                    # Archive the employee
                    rec.employee_id.active = False




    @api.depends('line_ids.grade')
    def _compute_average_score(self):
        for rec in self:
            grades = [int(line.grade) for line in rec.line_ids if line.grade]
            rec.average_score = sum(grades) / len(grades) if grades else 0.0
            





class HrProbationEvaluationLine(models.Model):
    _name = 'hr.probation.evaluation.line'
    _description = 'Probation Evaluation Line'

    evaluation_id = fields.Many2one('hr.probation.evaluation', string="Evaluation")
    element_g = fields.Many2one('hr.appraisal.goal',string="Element")  
    grade = fields.Selection(
        selection=[('0','No Grade'),('1', '1 - Failed to meet target.'), ('2', '2 - Slightly below target'), ('3', '3 - Met target'), ('4', '4 - Exceeded target')],
        string="Grade",
        default='0'
    )
    notes = fields.Text(string="Notes")  
