# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "Employee Other Earnings",
    'summary': "Any kind of deduction or fine or allowance in form of money can given to employees based on different filter like department, project, job position or all",
    'description': "Employee Other Earnings",
    'category': 'Generic Modules/Human Resources',
    'version': '0.1',
    'author':'Sharek',
    'website': "https://sharek.com.sa",
    'depends': ['project', 'hr_work_entry_contract', 'account','sharek_hr_payroll_extension','hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/other_earnings.xml',
        'views/res_config_settings_view.xml'
    ],
    'installable': True,
    'application': True,
}
