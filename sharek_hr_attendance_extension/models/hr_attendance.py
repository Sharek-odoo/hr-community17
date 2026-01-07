# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import api, fields, models
from datetime import datetime, date,timedelta
import math
import pytz


class HrAttendance(models.Model):

    _inherit = 'hr.attendance'

    pl_check_in = fields.Float(string='Planned Check-In', compute="compute_check_time")
    pl_check_out = fields.Float(string='Planned Check-Out', compute="compute_check_time")
    late_in = fields.Float(string='Late In', readonly=True, compute="compute_late_time")
    early_exit = fields.Float(string='Early Exit', readonly=True, compute="compute_late_time")
    pl_hours = fields.Float(string='Planned Hours', readonly=True)
    diff_time = fields.Float(string='Diff Time', compute='compute_diff_time')
    overtime = fields.Float(string='Overtime', compute='compute_overtime')
    check_in = fields.Datetime(string="Check In",index=True, default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out",index=True)

    @api.depends('employee_id', 'check_in', 'check_in')
    def compute_check_time(self):
        for record in self:
            dayofweek = record.check_in.weekday()
            calendar_id = record.employee_id.resource_calendar_id
            check_in_time = record.check_in.time()
            afternoon_cutoff = datetime.strptime('12:00:00', "%H:%M:%S").time()
            if check_in_time < afternoon_cutoff :
                period = 'morning'
            else :
                period = 'afternoon'

            attendance_day = calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == str(dayofweek) and line.day_period ==period)
            record.pl_check_in = attendance_day.hour_from
            record.pl_check_out = attendance_day.hour_to
            record.pl_hours = attendance_day.hour_to - attendance_day.hour_from

    @api.depends('check_in', 'check_out')
    def compute_late_time(self):
        for record in self:
            lat_in = 0.0
            early_exit = 0.0
            ac_sign_in = 0.0
            ac_sign_out = 0.0
            tzinfo = pytz.timezone(record.employee_id.tz)
            if record.check_in and record.pl_check_in:
                check_in_time_str = record.check_in.astimezone(tzinfo).time().strftime('%H:%M:%S')
                check_in_time_float = self.time_string_to_float(check_in_time_str)
                ac_sign_in = check_in_time_float
                lat_in = ac_sign_in - record.pl_check_in
                record.early_exit = 0.0
            if record.check_out and record.pl_check_out:
                check_out_time_str = record.check_out.astimezone(tzinfo).time().strftime('%H:%M:%S')
                check_out_time_float = self.time_string_to_float(check_out_time_str)
                ac_sign_out = check_out_time_float
                early_exit = ac_sign_out - record.pl_check_out
            record.early_exit = abs(early_exit) if record.pl_check_out > float(ac_sign_out) else 0.0
            record.late_in = lat_in if record.pl_check_in < float(ac_sign_in) else 0.0            


    def float_to_time_string(self,f):
        hours = int(f)
        minutes = int(round((f - hours),2) * 60)
        return '{:02d}:{:02d}'.format(hours, minutes)
    
    def time_string_to_float(self,s):
        parts = s.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours + (minutes / 60)

    @api.depends('pl_hours', 'worked_hours','check_out')
    def compute_diff_time(self):
        for record in self:
            record.diff_time = record.pl_hours - record.worked_hours


    @api.depends('check_in', 'check_out')
    def compute_overtime(self):
        for record in self:
            overtime = 0.0
            if record.check_in and record.check_out:
                employee = record.employee_id
                employee_rule = self.env['hr.attendance.rule'].search([('employee_id', '=', employee.id), ('rule_type', '=', 'employee')]) or \
                                self.env['hr.attendance.rule'].search([('department_id', '=', employee.department_id.id), ('rule_type', '=', 'department')]) or \
                                self.env['hr.attendance.rule'].search([('company_id', '=', employee.company_id.id), ('rule_type', '=', 'company')])
                if employee_rule:
                    tzinfo = pytz.timezone(record.employee_id.tz)
                    check_out = record.check_out.astimezone(tzinfo)
                    check_out = float(str(check_out.hour) + '.' + str(check_out.minute))
                    overtime_end = employee_rule.overtime_end
                    overtime_start = employee_rule.overtime_start
                    if check_out > overtime_start:
                        overtime_end = overtime_end if check_out > overtime_end else check_out
                        overtime = round((overtime_end - overtime_start), 3)
            record.overtime = overtime


