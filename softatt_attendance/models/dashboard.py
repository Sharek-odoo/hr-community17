from odoo import _, fields, models
from datetime import datetime
from odoo.tools import date_utils
from odoo.exceptions import ValidationError


import logging

_logger = logging.getLogger(__name__)


class saAttendanceDashboard(models.Model):
    _name = "sa.attendance.dashboard"
    _description = "sa Attendance Dashboard"

            
    def convert_time_to_float(self, time_str):
        if ':' in time_str:
            hours, minutes = map(int, time_str.split(':'))
            return hours + round(minutes / 60, 2)
        return 0.0  # Or handle invalid input as per your requirement



    def _get_dashboard_summary(self, _time=None, location_ids=None, department_ids=None, shift_ids=None, employee_ids=None):
        locations        =   [location_id['id'] for location_id in location_ids]
        departments     =   [department_id['id'] for department_id in department_ids]
        shifts          =   [shift_id['id'] for shift_id in shift_ids]
        employees       =   [employee_id['id'] for employee_id in employee_ids]
        user_tz         =   self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")
        now             = fields.Datetime.now() if not _time else _time
        att_domain      = [('check_in', '>=', datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.min.time())), 
                           ('check_in', '<=',datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.max.time()))]
        emp_domain      = []
        
        if locations:
            emp_domain.append(('work_location_id.id','in',locations))
            att_domain.append(('location_id.id','in',locations))
        if departments:
            emp_domain.append(('department_id.id','in',departments))
            att_domain.append(('department_id.id','in',departments))
        if shifts:
            emp_domain.append(('resource_calendar_id.id','in',shifts))
            att_domain.append(('resource_calendar_id.id','in',shifts))
        if employees:
            emp_domain.append(('id','in',employees))
            att_domain.append(('employee_id.id','in',employees))
            
        att_records     = self.env['hr.attendance'].search(att_domain)
        total           = self.env['hr.employee'].search_count(emp_domain)
        attended        = len(set(att_records.mapped('employee_id.id')))
        late            = len(set(att_records.filtered(lambda x: x.late_hours > 0).mapped('employee_id.id')))
        return [total, attended, late]

    def get_permission_employee(self,_time=None):
        user_tz = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")

        now = fields.Datetime.now() if not _time else _time
        today = date_utils._softatt_localize(now, user_tz).date()

        # Search for approved leaves that include today
        domain = [
            ('state', '=', 'done'),
            ('request_date', '=', today),
        ]

        permissions = self.env['hr.permission.request'].search(domain)
        employee_ids = permissions.mapped('employee_id.id')

        return [len(employee_ids), employee_ids]

    def get_exempt_employee(self,_time=None):
        employees = self.env['hr.employee'].search([('exempt_from_attendance', '=', True)])
        return [len(employees), employees.ids]

    def get_time_off_employee(self, _time=None):
        user_tz = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")

        now = fields.Datetime.now() if not _time else _time
        today = date_utils._softatt_localize(now, user_tz).date()

        # Search for approved leaves that include today
        domain = [
            ('state', '=', 'validate'),
            ('request_date_from', '<=', today),
            ('request_date_to', '>=', today),
        ]

        time_offs = self.env['hr.leave'].search(domain)
        employee_ids = time_offs.mapped('employee_id.id')

        return [len(employee_ids), employee_ids]

    def get_present_employee(self, _time=None):
        user_tz         = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")
        now             = fields.Datetime.now() if not _time else _time
        total           =  self.env['hr.employee'].search_count([])
        employees       = set(self.env['hr.attendance'].search([
            ('check_in', '>=', datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.min.time())), 
            ('check_in', '<=',datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.max.time()))]).mapped('employee_id.id'))
        unique_employee        = len(employees)
        return (unique_employee, tuple(employees), total)

    # added by alkhatim

    def get_absent_employee(self, _time=None):
        user_tz = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")

        now = fields.Datetime.now() if not _time else _time
        dt = date_utils._softatt_localize(now, user_tz)
        today = dt.date()

        # Get shift IDs active before this hour
        domain = [('hour_from', '<', self.convert_time_to_float(dt.strftime('%H:%M')))]
        shift_ids = tuple(set(self.env['resource.calendar.attendance'].search(domain).mapped('calendar_id.id')))

        # Employees who checked in today
        attendance_employees = set(self.env['hr.attendance'].search([
            ('employee_id', '!=', False),
            ('check_in', '>=', datetime.combine(today, datetime.min.time())),
            ('check_in', '<=', datetime.combine(today, datetime.max.time()))
        ]).mapped('employee_id.id'))

        # Employees under this shift
        all_employees = self.env['hr.employee'].search([
            ('resource_calendar_id.id', 'in', shift_ids),
            ('exempt_from_attendance', '=', False)
        ])

        # --- Exclude employees who have approved permission today ---
        permission_employees = self.env['hr.permission.request'].search([
            ('state', '=', 'done'),
            ('request_date', '=', today),
        ]).mapped('employee_id.id')

        # --- Exclude employees who are on validated leave today ---
        leave_employees = self.env['hr.leave'].search([
            ('state', '=', 'validate'),
            ('request_date_from', '<=', today),
            ('request_date_to', '>=', today),
        ]).mapped('employee_id.id')

        # Combine exclusion lists
        excluded_employees = set(permission_employees + leave_employees + list(attendance_employees))

        # Employees who are absent (not in excluded list)
        absent_emps = all_employees.filtered(lambda e: e.id not in excluded_employees)

        return len(absent_emps), absent_emps.ids


    # added by alkhatim
    def absent_employee_per_location(self):
        user_tz = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")

        now = fields.Datetime.now()
        dt = date_utils._softatt_localize(now, user_tz)

        domain = [('hour_from', '<', self.convert_time_to_float(dt.strftime('%H:%M')))]
        shift_ids = tuple(set(self.env['resource.calendar.attendance'].search(domain).mapped('calendar_id.id')))

        employees = set(self.env['hr.attendance'].search([
            ('employee_id', '!=', False),
            ('check_in', '>=', datetime.combine(dt.date(), datetime.min.time())),
            ('check_in', '<=', datetime.combine(dt.date(), datetime.max.time()))
        ]).mapped('employee_id.id'))

        # ✅ تعديل الدومين لاستثناء المعفيين
        absent_domain = [
            ('id', 'not in', tuple(employees)),
            ('resource_calendar_id.id', 'in', shift_ids),
            ('exempt_from_attendance', '=', False),  # استثناء المعفيين
        ]

        absent_emps = self.env['hr.employee'].read_group(
            domain=absent_domain,
            fields=['department_id'],
            groupby=['department_id']
        )
        return absent_emps


    # added by alkhatim


    # # commit by alkhatim
    # def absent_employee_per_location(self):
    #     user_tz         = self.env.user.tz
    #     if not user_tz:
    #         raise ValidationError("Please Set up Your Timezone")
    #     now             = fields.Datetime.now()
    #     dt              = date_utils._softatt_localize(now ,user_tz)
    #     domain          = [('hour_from','<',self.convert_time_to_float(dt.strftime('%H:%M')))]
    #     shift_ids       = tuple(set(self.env['resource.calendar.attendance'].search(domain).mapped('calendar_id.id')))
    #     employees       = set(self.env['hr.attendance'].search([
    #         ('employee_id','!=',False),
    #         ('check_in', '>=', datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.min.time())),
    #         ('check_in', '<=',datetime.combine(date_utils._softatt_localize(now, user_tz).date(), datetime.max.time()))]).mapped('employee_id.id'))
    #     absent_emps             = self.env['hr.employee'].read_group(domain=[('id','not in', tuple(employees)), ('resource_calendar_id.id', 'in', shift_ids)],
    #                                                                              fields=['department_id'],
    #                                                                              groupby=['department_id'])
    #     return absent_emps

        # commit by alkhatim

    def get_last_ten_logs(self):
        current_datetime    = fields.Datetime.now()
        user_tz         = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")
        last_ten_logs       = self.env['sa.attendance.log'].search([
            ('employee_id', '!=',   False),
            ('punch_time',  '>=',   datetime.combine(date_utils._softatt_localize(current_datetime, user_tz).date(), datetime.min.time())), 
            ('punch_time',  '<=',   datetime.combine(date_utils._softatt_localize(current_datetime, user_tz).date(), datetime.max.time()))], limit=5)
        last_ten_logs = [{'id': rec.id, 'employee': rec.employee_id.name, 'department': rec.department_id.name, 'location': rec.location_id.name, 'punch_time':date_utils._softatt_localize(rec.punch_time, user_tz), 'check_in_check_out': rec.check_in_check_out} for rec in last_ten_logs]
        return last_ten_logs
    





    def get_late_today(self):
        current_datetime    = fields.Datetime.now()
        user_tz             = self.env.user.tz
        if not user_tz:
            raise ValidationError("Please Set up Your Timezone")
        late_today          = self.env['hr.attendance'].search([
            ('check_in', '>=', datetime.combine(date_utils._softatt_localize(current_datetime, user_tz).date(), datetime.min.time())), 
            ('check_in', '<=',datetime.combine(date_utils._softatt_localize(current_datetime, user_tz).date(), datetime.max.time())),('late_hours','>', 0)], limit=5)
        late_today          = [{'id': rec.id, 'employee': rec.employee_id.name, 'department': rec.department_id.name, 'late_hours':rec.late_hours, 'location': rec.location_id.name, 'check_in':date_utils._softatt_localize(rec.check_in, user_tz)} for rec in late_today]
        return late_today
        