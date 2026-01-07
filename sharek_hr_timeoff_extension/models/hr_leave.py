# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import ValidationError


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    number = fields.Char(index=True, readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    balance = fields.Float(compute="_compute_employee_balance", store=True)
    required_delegation = fields.Boolean(related='holiday_status_id.required_delegation')
    required_ticket = fields.Boolean(related='holiday_status_id.required_ticket')
    delegated_id = fields.Many2one('hr.employee', string='Delegation')

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            # vals['number'] = self.env['ir.sequence'].with_company(employee.company_id).next_by_code(self._name)
            vals['number'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(HolidaysRequest, self).create(vals_list)

    # def _get_number_of_days(self, date_from, date_to, employee_id):
    #     res = super(HolidaysRequest, self)._get_number_of_days(date_from, date_to, employee_id)
    #     if self.holiday_status_id.calc_type == 'calendar':
    #         days = (date_to - date_from).days + 1
    #         print(days, "*****************", res)
    #         return {'days': days, 'hours': HOURS_PER_DAY * days}
    #     return res

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                holiday.number_of_days = \
                holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
                if holiday.holiday_status_id.calc_type == 'calendar':
                    holiday.number_of_days = (holiday.date_to - holiday.date_from).days + 1
            else:
                holiday.number_of_days = 0

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_employee_balance(self):
        for rec in self:
            balance = self.env['hr.leave.balance'].search(
                [('employee_id', '=', rec.employee_id.id), ('leave_type', '=', rec.holiday_status_id.id)])
            rec.balance = balance.remaining
            # rec.balance = rec.employee_id.allocation_count - rec.employee_id.allocation_used_count

    @api.constrains('employee_id', 'holiday_status_id', 'start_date', 'end_date')
    def _check_negative_leave(self):
        for record in self:
            if record.state not in ['draft', 'cancel',
                                    'refuse'] and record.holiday_status_id.allow_negative:
                if 0 < record.holiday_status_id.negative_limit < record.number_of_days:
                    raise ValidationError(_('You cannot take a(an) %s leave more than %s day(s).' % (
                        record.holiday_status_id.name, record.holiday_status_id.negative_limit)))

    @api.onchange('employee_id')
    def _onchange_employee(self):
        """override onchange of employee to add domain on holiday_status_id based on emp_type of employee"""
        domain = {}
        type_ids = []
        if self.employee_id and self.employee_id.gender:
            leave_types = self.env['hr.leave.type'].search(
                ['|', ('for_specific_gender', '=', False), ('gender', '=', self.employee_id.gender)])
            type_ids += leave_types and leave_types.ids
        if self.employee_id and self.employee_id.religion_id:
            leave_types = self.env['hr.leave.type'].search(
                ['|', ('religion_ids', '=', False), ('religion_ids', 'in', self.employee_id.religion_id.ids)])
            type_ids += leave_types and leave_types.ids

        if len(type_ids) > 0:
            domain.update({'holiday_status_id': [('id', 'in', list(set(type_ids)))]})
            return {'domain': domain}
