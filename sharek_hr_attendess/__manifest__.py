# -*- coding: utf-8 -*-
{
    'name': "Sharek HR Attendance Report",
    'summary': " add custom hr attendance report ",
    'description': """ add custom hr attendance report """,
    'author': "Hamid",
    'website': "https://www.yourcompany.com",
    'category': 'HR',
    'version': '0.1',
    'depends': ['base','hr','hr_attendance','softatt_attendance','sharek_hr_employee_extension','report_xlsx','hr_exception','hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'wizard/hr_attendess_report_wizard.xml',
        'report/report.xml'
    ],
}

