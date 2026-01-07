from datetime import datetime
from odoo import _, api, fields, models
import pytz
from odoo.tools import date_utils

import logging
_logger = logging.getLogger(__name__)

    
class SaEmployeeReportExtended(models.AbstractModel):
    _inherit = 'report.softatt_attendance.employee_report'
    
    def _absence_str(self, employee_id, _date):
        # Call the super method to check if it's a working day or off day
        result = super(SaEmployeeReportExtended, self)._absence_str(employee_id, _date)

        # Only proceed with further checks if the result is 'Absent'
        if result == 'Absent':
            employee = self.env['hr.employee'].browse(employee_id)
            calendar = employee.resource_calendar_id
            if not calendar:
                return 'No schedule defined'

            # Convert string _date to a datetime object
            date = datetime.strptime(_date, '%Y-%m-%d')
            weekday = date.weekday()

            # Check if it's a working day from the resource calendar
            is_working_day = any(
                work_day.dayofweek == str(weekday)
                for work_day in calendar.attendance_ids
            )

            # Check if there is approved time off for this employee on the given date
            time_off = self.env['hr.leave'].search([
                ('employee_id', '=', employee_id),
                ('state', 'in', ['validate', 'validate1']),  # Approved or partially approved time off
                ('request_date_from', '<=', date.date()),  # Time off starts on or before the date
                ('request_date_to', '>=', date.date())  # Time off ends on or after the date
            ], limit=1)

            # If the employee has approved time off for the given date, return 'Time Off'
            if time_off:
                return time_off.holiday_status_id.name

            # If the date is today, return Off Day if not a working day, otherwise Absent
            if date.date() == datetime.now().date():
                return 'Off Day' if not is_working_day else 'Absent'

            # Return Absent if it's a working day, otherwise Off Day
            return 'Absent' if is_working_day else 'Off Day'

        # Return the original result from super
        return result
