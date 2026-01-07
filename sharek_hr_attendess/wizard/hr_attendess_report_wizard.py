# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, date, time
import calendar, io, xlsxwriter
from babel.dates import format_datetime
from datetime import timedelta
import base64


class HrAttendessReportWiz(models.TransientModel):
    _name = 'hr.attendess.wizard'
    _description = 'HR Attendance Report Wizard'

    start_date = fields.Date(required=True, default=fields.Date.today)
    end_date = fields.Date(required=True, default=fields.Date.today)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company,required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError(_("Start Date must be before or equal to End Date."))

    def action_export_to_excel(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
                'employee_id': self.employee_id.id,
                'department_id': self.department_id.id,
                'company_id': self.company_id.id,
            },
        }
        return {
            'type': 'ir.actions.report',
            'report_name': 'sharek_hr_attendess.hr_attendess_report_xlsx',
            'report_type': 'xlsx',
            'data': data
        }


class HrAttendessReport(models.AbstractModel):
    _name = "report.sharek_hr_attendess.hr_attendess_report_xlsx"
    _description = "HR Attendance Report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def create_xlsx_report(self, docids, data):
        file_data = io.BytesIO()
        workbook = xlsxwriter.Workbook(file_data, self.get_workbook_options())
        self.generate_xlsx_report(workbook, data)
        workbook.close()
        file_data.seek(0)
        return file_data.read(), "xlsx"

    def get_report_values(self, data=None):
        start_date = datetime.strptime(data['form']['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(data['form']['end_date'], "%Y-%m-%d").date()

        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)

        domain = [
            ('check_in', '>=', start_datetime),
            ('check_in', '<=', end_datetime),
            ('employee_id.company_id', '=', data['form']['company_id']),
        ]

        if data['form'].get('employee_id'):
            domain.append(('employee_id', '=', data['form']['employee_id']))

        if data['form'].get('department_id'):
            domain.append(('employee_id.department_id', '=', data['form']['department_id']))



        docs = self.env['hr.attendance'].sudo().search(domain)

        return {
            'doc_ids': self.ids,
            'doc_model': 'hr.attendess.wizard',
            'docs': docs,
            'data': data['form'],
            'start_date': start_date,
            'end_date': end_date,
        }

    def generate_xlsx_report(self, workbook, data):
        results = self.get_report_values(data)
        start_date = results['start_date']
        end_date = results['end_date']
        sheet = workbook.add_worksheet(f'{start_date} - {end_date}')
        sheet.right_to_left()

        bold = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        header_style = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'border': 1, 'bg_color': '#B0C4DE'
        })
        normal = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })

        headers = [
            'رقم الموظف', 'الاسم الكامل', 'القسم', 'المسمى الوظيفي',
            'التاريخ', 'اليوم', 'وقت تسجيل الدخول', 'وقت تسجيل الخروج',
            'وقت العمل الإجمالي', 'تأخير الحضور', 'المغادرة مبكرا', 'المعفيين',
            'غياب', 'إجازة', 'الاستئذان المعتمد'
        ]

        sheet.merge_range('A1:R5', "King Abdullah International Foundation", bold)
        if self.env.company.logo:
            image_data = io.BytesIO(base64.b64decode(self.env.company.logo))
            sheet.insert_image('P1', 'logo.png', {
                'image_data': image_data, 'x_scale': 0.30, 'y_scale': 0.25
            })
        sheet.merge_range('A6:R6', "وقت العمل الإجمالي", bold)

        for col, header in enumerate(headers):
            sheet.write(6, col, header, header_style)
            sheet.set_column(col, col, 20)

        row = 7
        from pytz import timezone, UTC
        user_tz = self.env.user.tz or 'UTC'
        tz = timezone(user_tz)

        # Get all employees by wizard filter
        emp_domain = []
        emp_domain = [('company_id', '=', data['form']['company_id'])]

        if data['form'].get('employee_id'):
            emp_domain.append(('id', '=', data['form']['employee_id']))
        if data['form'].get('department_id'):
            emp_domain.append(('department_id', '=', data['form']['department_id']))

        employees = self.env['hr.employee'].sudo().search(emp_domain)

        current_date = start_date
        while current_date <= end_date:
            for emp in employees:
                # Look for attendance for this employee on current date
                start_dt = datetime.combine(current_date, time.min)
                end_dt = datetime.combine(current_date, time.max)
                attendance = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', emp.id),
                    ('check_in', '>=', start_dt),
                    ('check_in', '<=', end_dt),
                ], limit=1)

                check_in = check_out = worked_str = ''
                if attendance:
                    check_in = attendance.check_in
                    check_out = attendance.check_out

                    if check_in:
                        check_in = UTC.localize(check_in).astimezone(tz)
                    if check_out:
                        check_out = UTC.localize(check_out).astimezone(tz)

                    if check_in and check_out:
                        worked = check_out - check_in
                        total_seconds = int(worked.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        worked_str = f"{hours:02}:{minutes:02}"


                permission = self.env['hr.permission.request'].sudo().search([
                    ('employee_id', '=', emp.id),
                    ('request_date', '=', current_date),
                    ('state', '=', 'done'),   # make sure you have "state" field workflow
                ], limit=1)

                permission_val = 'نعم' if permission else 'لا'

                # --------------------------
                # Leave check
                # --------------------------
                leave = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', current_date),
                    ('request_date_to', '>=', current_date),
                ], limit=1)

                leave_val = 'نعم' if leave else 'لا'
                # Write to sheet
                sheet.write(row, 0, emp.employee_no or '', normal)
                sheet.write(row, 1, emp.arabic_name or '', normal)
                sheet.write(row, 2, emp.department_id.name or '', normal)
                sheet.write(row, 3, emp.job_id.name or '', normal)
                sheet.write(row, 4, str(current_date), normal)
                sheet.write(row, 5, format_datetime(current_date, "EEEE", locale='ar'), normal)
                sheet.write(row, 6, str(check_in.time()) if check_in else '', normal)
                sheet.write(row, 7, str(check_out.time()) if check_out else '', normal)
                sheet.write(row, 8, worked_str, normal)

                def duration_to_str(duration):
                    if not duration:
                        return ''
                    if isinstance(duration, float) or isinstance(duration, int):
                        # Assume duration is in hours (e.g., 1.25 hours)
                        total_seconds = int(duration * 3600)
                    else:
                        # Assume duration is a timedelta
                        total_seconds = int(duration.total_seconds())

                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    return f"{hours:02}:{minutes:02}"

                sheet.write(row, 9, duration_to_str(attendance.late_in), normal)
                sheet.write(row, 10, duration_to_str(attendance.early_exit), normal)

                # sheet.write(row, 9,  attendance.late_in if attendance.late_in else '', normal)
                # sheet.write(row, 10, attendance.early_exit if attendance.early_exit else '', normal)
                sheet.write(row, 11, 'نعم' if emp.exempt_from_attendance else 'لا', normal)

                weekday_ar = format_datetime(current_date, "EEEE", locale='ar')
                if weekday_ar in ['الجمعة', 'السبت']:
                    absence_note = 'إجازة نهاية الأسبوع'
                elif attendance.check_in and attendance.check_out:
                    absence_note = 'لا'
                elif leave or permission:
                    absence_note = 'لا'
                else:
                    absence_note = 'نعم'

                sheet.write(row, 12, absence_note, normal)
                sheet.write(row, 13, leave_val, normal)
                sheet.write(row, 14, permission_val, normal)
                row += 1
            current_date += timedelta(days=1)
