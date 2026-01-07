# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import api, fields, models, _
import datetime
import pytz
from odoo.tools.misc import format_date
from odoo.exceptions import UserError, ValidationError


class HrAttendanceSheet(models.Model):
    _name = 'hr.attendance.sheet'
    _description = 'HR Attendance Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(struct='Name', compute='_compute_name', store=True, )
    date_from = fields.Date(string='Date From',required=True,)
    date_to = fields.Date(string='Date To',required=True)
    state = fields.Selection([('draft', 'Draft'), ('submit','Submit'), ('confirm', 'Confirmed'),
                              ('approve', 'Approve'), ('cancel', 'Cancel')], default='draft', string='State',track_visibility='onchange')

    line_ids = fields.One2many('hr.attendance.sheet.line', 'sheet_id', string='Lines')
    deducted = fields.Boolean(string='Deducted')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department',string="Department")
    sheet_type = fields.Selection([('manual','Manual'),('computed','Compute From Sheet')])


    @api.depends('date_from')
    def _compute_name(self):
        for sheet in self.filtered(lambda p: p.date_from):
            lang = self.env.user.lang
            context = {'lang': lang}
            sheet_name = _('Attendance Sheet')
            del context
            sheet.name = '%(sheet_name)s - %(dates)s' % {
                'sheet_name': sheet_name,
                'dates': format_date(self.env, sheet.date_from, date_format="MMMM y", lang_code=lang)
            }


    @api.constrains('department_id','date_from','date_to')
    def _check_same_department_attend_sheet(self):
        for rec in self:
            if rec.department_id:
                last_sheet = self.env['hr.attendance.sheet'].search([('department_id','=',rec.department_id.id),('date_from','=',rec.date_from),('date_to','=',rec.date_to),('id','!=',rec.id)])
                if last_sheet:
                    raise ValidationError(_("You can not create 2 sheet for same department in same period"))


    def compute_attendance_emp(self):
        sheet_period = self.get_days_and_names(self.date_from,self.date_to)
        self.line_ids = None
        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id','=',self.department_id.id)])
        else:
            employees = self.env['hr.employee'].search([])
        lines = []
        for emp in employees:
            calendar_id = emp.resource_calendar_id
            emp_planned_hours = 0
            emp_act_hours = 0
            emp_absence_days = 0
            # minutes = ((int(late[0]) + int(early[0])) * 60) + int(late[1][:2]) + int(early[1][:2])
            
            # attendance_line = self.env['hr.attendance.sheet.line'].search([('employee_id', '=', emp.id)])
            # late_in = (((attendance_line.mapped('late_in') / 30 ) * calendar_id.hours_per_day)* 60)
            # early_exit = (((attendance_line.mapped('early_exit') / 30 ) * calendar_id.hours_per_day)* 60)
            # late = str(late_in).split('.')
            # early = str(early_exit).split('.')
            # minutes = ((int(late[0]) + int(early[0])) * 60) + int(late[1][:2]) + int(early[1][:2])

            month_days = emp.contract_id.get_days_of_month(self.date_from.year,self.date_from.month)
            emp_working_days = calendar_id.attendance_ids.mapped('dayofweek')
            # calculate employee planned hours within selected period
            for period_day in sheet_period :
                emp_work_days = calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(sheet_period[period_day]))
                working_hours = sum([(day.hour_to - day.hour_from) for day in emp_work_days])   
                # emp_planned_hours +=  working_hours
                # emp_planned_hours = calendar_id.hours_per_day * 30 
                emp_planned_hours = calendar_id.hours_per_day * month_days 
                if str(sheet_period[period_day]) in emp_working_days:
                    emp_absence_days += 1 
                emp_act_hours =  emp_planned_hours 
                
    
            new_line = {
                'employee_id': emp.id,
                'planned_hours': emp_planned_hours,
                'act_hours': emp_act_hours,
                'absence_days': 0,
                # 'deduction_amount': minutes* ((((emp.contract_id.wage)/30)/calendar_id.hours_per_day)/60)
            }

            lines.append((0, 0, new_line))

        self.write({'line_ids': lines})
                

    def compute_attendance(self):
        sheet_period = self.get_days_and_names(self.date_from,self.date_to)
        self.line_ids = None
        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id','=',self.department_id.id)])
        else:
            employees = self.env['hr.employee'].search([])
        lines = []
        attendance_dict = {}
        for emp in employees:
            calendar_id = emp.resource_calendar_id
            emp_planned_hours = 0
            emp_act_hours = 0
            emp_absence_days = 0
            attendance = self.env['hr.attendance'].search([('employee_id', '=', emp.id)])
            attendance = attendance.filtered(
                lambda a: self.date_from <= a.check_in.date() <= self.date_to)
            act_hours = sum(attendance.mapped('worked_hours')) or 0.0
            late_in = sum(attendance.mapped('late_in')) or 0.0
            early_exit = sum(attendance.mapped('early_exit')) or 0.0
            diff_time = sum(attendance.mapped('diff_time')) or 0.0
            overtime = sum(attendance.mapped('overtime')) or 0.0
            late = str(late_in).split('.')
            early = str(early_exit).split('.')
            minutes = ((int(late[0]) + int(early[0])) * 60) + int(late[1][:2]) + int(early[1][:2])


            emp_working_days = calendar_id.attendance_ids.mapped('dayofweek')
            # calculate employee planned hours within selected period
            for period_day in sheet_period :
                emp_work_days = calendar_id.attendance_ids.filtered(lambda a: a.dayofweek == str(sheet_period[period_day]))
                working_hours = sum([(day.hour_to - day.hour_from) for day in emp_work_days])   
                emp_planned_hours +=  working_hours
                # emp_planned_hours = calendar_id.hours_per_day * 30    
                check_attendance = attendance.filtered(lambda a: period_day  == a.check_in.date())  
                if str(sheet_period[period_day]) in emp_working_days and not check_attendance :
                    emp_absence_days += 1
                if check_attendance :
                    emp_act_hours += sum(check_attendance.mapped('worked_hours'))
            month_days = emp.contract_id.get_days_of_month(self.date_from.year,self.date_from.month)   
            # new_line = {
            #     'employee_id': emp.id,
            #     'planned_hours': emp_planned_hours,
            #     'act_hours': emp_act_hours,
            #     'late_in': late_in,
            #     'early_exit': early_exit,
            #     'diff_time': diff_time,
            #     'overtime': overtime,
            #     'absence_days': emp_absence_days,
            #     'deduction_amount': minutes* ((((emp.contract_id.wage)/30)/calendar_id.hours_per_day)/60)
            # }
            new_line = {
                'employee_id': emp.id,
                'planned_hours': emp_planned_hours,
                'act_hours': emp_act_hours,
                'late_in': late_in,
                'early_exit': early_exit,
                'diff_time': diff_time,
                'overtime': overtime,
                'absence_days': emp_absence_days,
                'deduction_amount': minutes* ((((emp.contract_id.wage)/month_days)/calendar_id.hours_per_day)/60)
            }

            lines.append((0, 0, new_line))

        self.write({'line_ids': lines})


    def get_days_and_names(self,start_date, end_date):
        """
        Returns a dictionary containing days and their corresponding day names for the given period.
        """
        days_and_names = {}
        delta = datetime.timedelta(days=1)
        while start_date <= end_date:
            day_name = start_date.weekday()
            days_and_names[start_date] = day_name
            start_date += delta
        return days_and_names

    def action_confirm(self):
        if not self.line_ids:
            raise UserError('You cannot confirm sheet has no lines')
        else:
            self._check_employee_state_type()    
            self.state = 'confirm'


    def action_submit(self):
        self.state = 'submit'        

    # @api.constrains('date_from', 'date_to','line_ids')
    def _check_employee_state_type(self):
        confirmed_sheet = self.env['hr.attendance.sheet'].search([('state','not in',('draft','submit')),('date_from','=',self.date_from),('date_to','=',self.date_to)])
        for rec in confirmed_sheet:
            for record in rec.line_ids:
                if any(line.employee_id.id == record.employee_id.id for line in self.line_ids):
                    raise ValidationError(_("You can not confirm 2 sheet for same employee"))
                        

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'    


    def unlink(self):
        for sheet in self:
            if sheet.state != 'draft':
                raise UserError(
                    'You cannot delete a attendance sheet which is not in draft state')
        return super(HrAttendanceSheet, self).unlink()
    


class HrAttendanceLines(models.Model):
    _name = 'hr.attendance.sheet.line'

    employee_id = fields.Many2one('hr.employee', readonly=0)
    employee_no = fields.Char(related="employee_id.employee_no",string="Employee NO")
    planned_hours = fields.Float(string='PL-Hours', readonly=0)
    act_hours = fields.Float(string='ACT-Hours', readonly=0)
    absence_days = fields.Integer(string='Absence Days', readonly=0)
    late_in = fields.Float(string='Late In', readonly=0)
    early_exit = fields.Float(string='Early Exit', readonly=0)
    diff_time = fields.Float(string='Diff Time', readonly=0)
    overtime = fields.Float(string='OverTime', readonly=0)
    deduction_amount = fields.Float(string='Deduction Amount')
    # check_emp_sheet = fields.Boolean(compute="_compute_emp_sheet")
    sheet_id = fields.Many2one('hr.attendance.sheet', ondelete='cascade')
    overtime_amount = fields.Float(string='OverTime Amount', )


    # def _compute_emp_sheet(self):
    #     self.check_emp_sheet = False
    #     lines = self.env['hr.attendance.sheet.line'].search([])
    #     for line in lines:
    #         if line.employee_id == self.employee_id.id and line.sheet_id.state == 'confirm':
    #             self.check_emp_sheet == True
    #         else:
    #             self.check_emp_sheet == False    

    # @api.depends('employee_id')
    # def compute_hours(self):
    #     for line in self:
    #         attendance = self.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id)])
    #         attendance = attendance.filtered(lambda a: line.sheet_id.date_from <= a.check_in.date() <= line.sheet_id.date_to)
    #         line. act_hours = sum(attendance.mapped('worked_hours'))
    #         line. late_in = sum(attendance.mapped('late_in'))
    #         line. early_exit = sum(attendance.mapped('early_exit'))
    #         line. diff_time = sum(attendance.mapped('diff_time'))
    #         line.overtime = sum(attendance.mapped('overtime'))



    @api.onchange('late_in','early_exit','absence_days')
    def _onchange_late_in_early_exit(self):
        absence_hours = 0.0
        month_days = self.employee_id.contract_id.get_days_of_month(self.sheet_id.date_from.year,self.sheet_id.date_from.month)
        calendar_id = self.employee_id.resource_calendar_id
        if self.sheet_id.sheet_type == 'manual' and (self.late_in != 0.0 or self.early_exit != 0.0 or self.absence_days > 0):
            # absence_hours = (self.planned_hours / 30) * self.absence_days
            absence_hours = (self.planned_hours / month_days) * self.absence_days
            self.act_hours = self.planned_hours - self.late_in - self.early_exit - absence_hours
            late = str(self.late_in).split('.')
            early = str(self.early_exit).split('.')
            # minutes = ((int(late[0]) + int(early[0])) * 60) + int(late[1][:2]) + int(early[1][:2])
            minutes = self.late_in + self.early_exit
            # self.deduction_amount = minutes * ((((self.employee_id.contract_id.wage + self.employee_id.contract_id.transport_allowance + self.employee_id.contract_id.hra +
            #     self.employee_id.contract_id.other_allowance)/30)*calendar_id.hours_per_day)*60)
            self.deduction_amount = minutes * ((((self.employee_id.contract_id.wage + self.employee_id.contract_id.transport_allowance + self.employee_id.contract_id.hra +
                self.employee_id.contract_id.other_allowance)/month_days)*calendar_id.hours_per_day)*60)


    @api.depends('employee_id')
    def compute_absence_days(self):
        for line in self:
            attendance = self.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id)])
            attendances = attendance.filtered(
                lambda a: line.sheet_id.date_from <= a.check_in.date() <= line.sheet_id.date_to)
            calendar_id = line.employee_id.resource_calendar_id
            attendance_day = calendar_id.attendance_ids.mapped('dayofweek')
            day_generator = (line.sheet_id.date_from + datetime.timedelta(x + 1) for x in range(
                (line.sheet_id.date_to - line.sheet_id.date_from).days))
            delta_days = sum(1 for day in day_generator if str(day.weekday()) in attendance_day)
            line.absence_days = delta_days - len(attendances)


