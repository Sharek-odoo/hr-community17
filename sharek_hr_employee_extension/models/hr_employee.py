# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    #
    # _sql_constraints = [
    #     ('employee_no_unqiue', 'unique(company_id, employee_no)','Employee ID Company must be unique!')
    # ]
    #
    @api.constrains('employee_no')
    def unique_employee_no(self):
        for record in self:
            x = self.env['hr.employee'].search_count([('company_id','=',record.company_id.id),
                ('employee_no','=',record.employee_no)])
            if x and x >1:
                raise ValidationError(_("Employee ID must be unique In Company!."))
    



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


class HREmployeeIqama(models.Model):
    _name = "hr.employee.iqama"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Iqama"

    def _get_default_expiry_date(self):
        date_to = fields.Date.today() + relativedelta(months=3)
        return date_to

    BLOOD_GROUP = [
        ("a+", "A+"),
        ("b+", "B+"),
        ("o+", "O+"),
        ("ab+", "AB+"),
        ("a-", "A-"),
        ("b-", "B-"),
        ("o-", "O-"),
        ("ab-", "AB-"),
    ]

    name = fields.Char(string="Name")
    copy_number = fields.Integer(string="Copy Number", default="1")
    # employee_id = fields.Many2one("hr.employee", string="Employee")
    # department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    # job_id = fields.Many2one("hr.job", related="employee_id.job_id", string="Job")
    partner_id = fields.Many2one("res.partner", string="Guarantor")
    issuing_date = fields.Date(string="Issuing Date", default=fields.Date.today())
    expiry_date = fields.Date(string="Expiry Date", default=_get_default_expiry_date)
    date_of_birth = fields.Date(string="Birth Date", default=fields.Date.today())
    entry_date = fields.Date(string="KSA Entry Date", default=fields.Date.today())
    place_of_issue = fields.Char(string="Place Of Issue")
    blood_group = fields.Selection(BLOOD_GROUP, string="Blood Group", default="a+")

    def unlink(self):
        """
        A method to delete employee iqama.
        """
        for rec in self:
            employee_iqama_ids = self.env["hr.employee"].search([("iqama_id", "!=", False)]).mapped("iqama_id.id")
            if rec.id in employee_iqama_ids:
                raise ValidationError(_("You can't delete iqama that's already linked with active employee record."))
        return super(HREmployeeIqama, self).unlink()
