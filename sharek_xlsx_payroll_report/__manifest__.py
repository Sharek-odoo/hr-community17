# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Sharek Excel Payroll Report",
    "summary": "A payroll report in xlsx format",
    "version": "17.0",
    "author": "Sharek",
    "website": "www.sharek.com.sa",
    'support': 'support@sharek.com.sa',
    "license": "LGPL-3",
    "category": "Human Resources/Payroll",
    "depends": ['base','om_hr_payroll','sharek_hr_employee_extension','report_xlsx'],
    "data": [
        'report/payroll_report.xml',
    ],
    "images": [
        'images/main_screenshot.png'
        ],
    "installable": True,
}