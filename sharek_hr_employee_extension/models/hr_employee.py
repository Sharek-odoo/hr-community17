# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,AccessError


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def _get_default_employee_id_method(self):
        return self.env['ir.config_parameter'].sudo().get_param('sharek_hr_employee_extension.employee_id_option')

    employee_no = fields.Char(string='Employee ID', copy=False)
    arabic_name = fields.Char('Employee arabic name', copy=False)
    join_date = fields.Date('Joining date')
    identification_end_date = fields.Date('ID End Date')
    passport_end_date = fields.Date('Passport Expiry Date')
    visa_type = fields.Selection([("visit", "Visit"), ("iqama", "Iqama")], string="Visa Type", default="iqama")
    visit_id = fields.Char('Visit Visa Number')
    iqama_id = fields.Many2one('hr.employee.iqama', string='Iqama Number')
    visit_end_date = fields.Date('Visit Expiry Date')
    iqama_end_date = fields.Date('Iqama Expiry Date', related="iqama_id.expiry_date")
    border_no = fields.Char('Border Number')
    is_stranger = fields.Boolean(string="Is not saudi", default=False)
    employee_id_option = fields.Selection([('manual', 'Manual Entry'), ('auto', 'Auto Generation')],
                                          string='Employee ID Generation Method',
                                          default=lambda self: self._get_default_employee_id_method())
    country_code = fields.Char(related='country_id.code')
    have_gosi = fields.Boolean('Have Gosi',default =False)
    gender = fields.Selection(
        selection=[('male', 'Male'), ('female', 'Female')],
        string='Gender',
        required=False
    )
    certificate_two = fields.Selection([
        ('primary', 'Primary School '),
        ('middle', 'Middle School '),
        ('high', 'High School '),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ], 'Certificate Level', default='other', groups="hr.group_hr_user", tracking=True)

    internal_experience = fields.Float(string='Internal Experience',compute='_compute_experience', store=True)
    external_experience_years = fields.Float(string='External Experience')
    external_experience_months = fields.Float(string='External Experience')
    total_experience = fields.Float(string='Total Experience',compute='_compute_experience', store=True)
    display_internal_experience = fields.Char(string='Internal Experience', compute='_compute_display_internal_experience', store=False)
    total_experience_text = fields.Char(string='Total Experience',compute='_compute_display_total_experience',store=False)
    exempt_from_attendance = fields.Boolean(string='Exempt Attendance')
    gosi_percentage = fields.Float(string='Gosi Percentage %', store=True)


    @api.depends('join_date', 'external_experience_years', 'external_experience_months')
    def _compute_experience(self):
        today = date.today()
        for rec in self:
            internal = 0.0
            if rec.join_date:
                try:
                    delta = today - rec.join_date
                    internal = round(delta.days / 365.0, 2)
                except Exception:
                    internal = 0.0
            rec.internal_experience = internal

            external_years = rec.external_experience_years or 0.0
            external_months = rec.external_experience_months or 0.0

            external_total = external_years + (external_months / 12.0)
            rec.total_experience = internal + external_total

    @api.depends('join_date', 'external_experience_years', 'external_experience_months')
    def _compute_display_total_experience(self):
        today = date.today()
        for rec in self:
            # Internal days from join_date
            internal_days = 0
            if rec.join_date:
                internal_days = (today - rec.join_date).days

            # External days from years + months (approximate: 1 year = 365 days, 1 month = 30 days)
            external_days = int(
                (rec.external_experience_years or 0.0) * 365 + (rec.external_experience_months or 0.0) * 30)

            total_days = internal_days + external_days

            # Use a dummy start date to calculate relativedelta
            base_date = date(2000, 1, 1)
            result_date = base_date + timedelta(days=total_days)
            diff = relativedelta(result_date, base_date)

            rec.total_experience_text = f"{diff.years} سنوات, {diff.months} أشهر, {diff.days} يوم "

    @api.depends('join_date')
    def _compute_display_internal_experience(self):
        today = date.today()
        for rec in self:
            if rec.join_date:
                diff = relativedelta(today, rec.join_date)
                rec.display_internal_experience = f"{diff.years} Years {diff.months} Months{diff.days} Day"
            else:
                rec.display_internal_experience = "N/A"


    @api.onchange("country_id","visa_type","iqama_id")
    def _check_iqama_duplication(self):
        for rec in self:
            employee_iqama_ids = self.env["hr.employee"].search([("iqama_id", "!=", False)]).mapped("iqama_id.id")
            available_iqama_ids = self.env["hr.employee.iqama"].search([("id", "not in", employee_iqama_ids)]).mapped("id")

            return {'domain': {'iqama_id': [('id', 'in', available_iqama_ids)]}}


    @api.model
    def create(self, vals):
        result = super(HREmployee, self).create(vals)
        employee_id_option = self.env['ir.config_parameter'].sudo().get_param('sharek_hr_employee_extension.employee_id_option')
        if employee_id_option == 'auto':
            result['employee_no'] = self.env['ir.sequence'].next_by_code('hr.employee.id')
        return result

    @api.constrains('employee_no', 'company_id')
    def _check_unique_employee_no(self):
        for record in self:
            if record.employee_no:
                domain = [
                    ('employee_no', '=', record.employee_no),
                    ('company_id', '=', record.company_id.id),
                    ('id', '!=', record.id),
                ]
                duplicate_count = self.env['hr.employee'].search_count(domain)
                if duplicate_count > 0:
                    raise ValidationError(_("Employee number must be unique within the company."))

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()

        search_limit = limit
        sort_by_search_input = self.env['ir.config_parameter'].sudo().get_param(
            'employee_name_search_sort_by_search_input') == 'True'
        if sort_by_search_input:
            search_limit = None

        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=search_limit)

        if name and sort_by_search_input:
            recs = recs.sorted(key=lambda rec: (1 if rec.name.lower().startswith(name.lower()) else 2, rec.name))

        recs = recs[:limit]

        return recs.name_get()

    # def get_formview_action(self, access_uid=None):
    #     self.ensure_one()
    #
    #     # Allow HR (Officer/Manager) to open anyone
    #     if self.env.user.has_group('hr.group_hr_manager'):
    #         # Non-HR: only allowed to open their own employee record
    #         my_emp = self.env.user.employee_id
    #         if not my_emp or self.id != my_emp.id:
    #             # Optional: if you previously redirected to kanban, block that too
    #             if self.env.context.get('open_employees_kanban'):
    #                 # remove redirection path entirely
    #                 raise AccessError(_("You are not allowed to open other employees' profiles."))
    #
    #             raise AccessError(_("You are not allowed to open other employees' profiles."))
    #
    #     return super().get_formview_action(access_uid=access_uid)
    def get_formview_action(self, access_uid=None):
        self.ensure_one()

        # Only HR users can open other employees
        if not self.env.user.has_group('hr.group_hr_manager'):
            my_emp = self.env.user.employee_id
            if not my_emp or self.id != my_emp.id:
                raise AccessError(_("You are not allowed to open other employees' profiles."))

        return super().get_formview_action(access_uid=access_uid)


class HREmployeeIqama(models.Model):
    _name = "hr.employee.iqama"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Iqama"

    def _get_default_expiry_date(self):
        date_to = fields.Date.today() + relativedelta(months=3)
        return date_to

    def _get_default_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee.id    

    

    name = fields.Char(string="Name")
    copy_number = fields.Integer(string="Copy Number", default="1")
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=_get_default_employee,
        tracking=True,
    )
    # department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    job_id = fields.Many2one("hr.job", related="employee_id.job_id", store= True,string="Job Position")
    partner_id = fields.Many2one("res.partner", string="Guarantor")
    issuing_date = fields.Date(string="Issuing Date", default=fields.Date.today())
    expiry_date = fields.Date(string="Expiry Date", default=_get_default_expiry_date)
    date_of_birth = fields.Date(string="Birth Date",related="employee_id.birthday", store= True,)
    entry_date = fields.Date(string="KSA Entry Date", default=fields.Date.today())
    place_of_issue = fields.Char(string="Place Of Issue")
    # blood_group = fields.Selection(BLOOD_GROUP, string="Blood Group", default="a+")
    employee_id_no = fields.Char(string="Employee ID",related="employee_id.identification_id",store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)



    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('expired', 'Expired')
    ], string="Status", default='draft', tracking=True)

    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    def action_start_iqama(self):
        self.write({'state': 'running'})

    def action_expire_iqama(self):
        self.write({'state': 'expired'})

    def unlink(self):
        """
        A method to delete employee iqama.
        """
        for rec in self:
            employee_iqama_ids = self.env["hr.employee"].search([("iqama_id", "!=", False)]).mapped("iqama_id.id")
            if rec.id in employee_iqama_ids:
                raise ValidationError(_("You can't delete iqama that's already linked with active employee record."))
        return super(HREmployeeIqama, self).unlink()


    @api.model
    def check_and_expire_iqamas(self):
        """Mark all Iqamas as expired if expiry date is in the past."""
        today = fields.Date.today()
        expired_records = self.search([
            ('expiry_date', '<', today),
            ('state', '!=', 'expired')
        ])
        for rec in expired_records:
            rec.state = 'expired'
    
