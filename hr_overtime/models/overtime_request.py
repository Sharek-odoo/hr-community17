# -*- coding: utf-8 -*-

from dateutil import relativedelta
# import pandas as pd
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.addons.resource.models.utils import HOURS_PER_DAY
from datetime import datetime, timedelta


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def btn_cancel(self):
        self.state = 'cancel'
    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date to')
    hours_per_day = fields.Float(string='Hours Per Day')
    total_hours = fields.Float('Total Hours', compute="_get_total_hours", store=True)
    total_hours_weekend = fields.Float(string='Total Hours Weekend')
    total_hours_holiday = fields.Float(string='Total Hours Holiday')
    days_no = fields.Float('No. of Days', store=True, compute="_get_days")
    desc = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'),
                              ('m_approve', 'Waiting For Manager Approval'),
                              ('hr_approve', 'Waiting For HR Approval'),
                              ('ceo', 'Waiting For CEO Approval'),
                              ('approved', 'Approved'), ('refused', 'Refused'),
                              ('cancel', 'Cancelled')
                              ], string="state",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave ID")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    weekday_hour_rate_sa = fields.Float(string='Weekday OT Hour Rate SA', )
    weekday_hour_rate = fields.Float(string='Weekday OT Hour Rate', )
    weekend_hour_rate = fields.Float(string='Weekend OT Hour Rate')
    holiday_hour_rate = fields.Float(string='Holiday OT Hour Rate')
    overtime_line_ids = fields.One2many('hr.overtime.line', 'overtime_id', string='Overtime Lines')
    total_actual_hours = fields.Float(string='Total Actual Hours', compute="_compute_hours_total")
    total_workday_hours = fields.Float(string='Hours Working Day', compute="_compute_hours_total")
    total_weekend_hours = fields.Float(string='Hours Weekend', compute="_compute_hours_total")
    total_holiday_hours = fields.Float(string='Hours Holiday', compute="_compute_hours_total")
    total_amount = fields.Float(string='Total Amount', currency_field='currency_id', compute="_compute_total_amount")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('overtime_line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum([line.amount for line in record.overtime_line_ids])

    @api.depends('overtime_line_ids.actual_hours', 'overtime_line_ids.category')
    def _compute_hours_total(self):
        for overtime in self:
            hours = 0
            weekend_hours = 0
            holiday_hours = 0
            working_day_hours = 0
            for line in overtime.overtime_line_ids:
                hours += line.actual_hours
                if line.category == 'weekend':
                    weekend_hours += line.actual_hours
                if line.category == 'workday':
                    working_day_hours += line.actual_hours
                elif line.category == 'holiday':
                    holiday_hours += line.actual_hours
            overtime.total_actual_hours = hours
            overtime.total_weekend_hours = weekend_hours
            overtime.total_holiday_hours = holiday_hours
            overtime.total_workday_hours = working_day_hours

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('days_no', 'hours_per_day')
    def _get_total_hours(self):
        for record in self:
            record.total_hours = record.days_no * record.hours_per_day

    @api.depends('date_from', 'date_to')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            days_no = 0
            if sheet.date_from and sheet.date_to:
                start_dt = sheet.date_from
                finish_dt = sheet.date_to + timedelta(days=1)
                days_no = (finish_dt - start_dt).days
            sheet.days_no = days_no

    def compute_work_sheet(self):
        delta = self.date_to - self.date_from
        lines = []
        self.overtime_line_ids = None
        dayofweek = self.work_schedule.mapped('dayofweek')
        global_leaves = [line.date_to.date().weekday() for line in self.global_leaves]
        for i in range(delta.days + 1):
            day = self.date_from + timedelta(days=i)
            if day.weekday() in global_leaves:
                category = 'holiday'
            elif str(day.weekday()) in dayofweek:
                category = 'workday'
            else:
                category = 'weekend'
            overtime_type_id = self.env['overtime.type'].search([('category', '=', category)], limit=1)
            overtime_type_id_hour_rate = 0
            if overtime_type_id.category =='workday' and self.employee_id.sudo().country_id.code == 'SA':
                overtime_type_id_hour_rate = self.employee_id.company_id.weekday_hour_rate_sa
            else:
                overtime_type_id_hour_rate = overtime_type_id.hour_rate or 0.0
            val = (0, 0, {'working_date': day,
                          'weekday': str(day.weekday()),
                          'number_of_hours': self.hours_per_day,
                          'actual_hours': self.hours_per_day,
                          'category': category,
                          'overtime_type_id': overtime_type_id.id or False,
                          'hour_rate': overtime_type_id_hour_rate,
                          # 'hour_rate': overtime_type_id.hour_rate or 0.0,
                          'hour_cost': self.contract_id.over_hour,})
            lines.append(val)
        self.overtime_line_ids = lines

    def action_submit(self):
        # # notification to employee
        # recipient_partners = [(4, self.current_user.partner_id.id)]
        # body = "Your OverTime Request Waiting Finance Approve .."
        # msg = _(body)
        #
        # # notification to finance :
        # group = self.env.ref('account.group_account_invoice', False)
        # recipient_partners = []
        #
        # body = "You Get New Time in Lieu Request From Employee : " + str(
        #     self.employee_id.name)
        # msg = _(body)
        return self.sudo().write({
            'state': 'm_approve'
        })

    def action_manager_approval(self):
        return self.sudo().write({'state': 'hr_approve'})

    def action_hr_approve(self):
        return self.sudo().write({'state': 'ceo'})

    def ceo_approve(self):
        return self.sudo().write({
            'state': 'approved',

        })

    def reject(self):

        self.state = 'refused'

    # @api.constrains('date_from', 'date_to')
    # def _check_date(self):
    #     for req in self:
    #         domain = [
    #             ('date_from', '<=', req.date_to),
    #             ('date_to', '>=', req.date_from),
    #             ('employee_id', '=', req.employee_id.id),
    #             ('id', '!=', req.id),
    #             ('state', 'not in', ['refused']),
    #         ]
    #         nholidays = self.search_count(domain)
    #         if nholidays:
    #             raise ValidationError(_(
    #                 'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(HrOverTime, self.sudo()).create(values)

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        return super(HrOverTime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.write({'public_holiday': ' '})
            hr_attendance = self.env['hr.attendance'].search(
                [('check_in', '>=', self.date_from),
                 ('check_in', '<=', self.date_to),
                 ('employee_id', '=', self.employee_id.id)])
            self.update({
                'attendance_ids': [(6, 0, hr_attendance.ids)]
            })


class HrOvertimeLines(models.Model):
    _name = 'hr.overtime.line'

    working_date = fields.Date(string='Date')
    category = fields.Selection([('workday', 'Workday'),
                                 ('weekend', 'Weekend'),
                                 ('holiday', 'Holiday'),
                                 ], defautl='workday', string='Category', required=True)
    number_of_hours = fields.Float(string='Number Of Hours')
    actual_hours = fields.Float(string='Actual Hours')
    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    hour_rate = fields.Float(string='Hour Rate')
    hour_cost = fields.Float(string='Hour Cost')
    amount = fields.Float(string='Amount', compute='compute_amount')
    overtime_id = fields.Many2one('hr.overtime', string='Overtime', ondelete='cascade')
    overtime_type_id = fields.Many2one('overtime.type', ondelete="restrict")

    @api.depends('hour_rate', 'hour_cost', 'actual_hours')
    def compute_amount(self):
        for record in self:
            record.amount = record.actual_hours * record.hour_rate * record.hour_cost

