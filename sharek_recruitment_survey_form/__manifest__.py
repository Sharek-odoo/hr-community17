# -*- coding: utf-8 -*-
{
    'name': "sharek_recruitment_survey_form",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','hr_recruitment','hr_recruitment_survey'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_applicant.xml',
        'views/viwes.xml',
        'reports/report_hr_job_interview.xml',
    ],
}

