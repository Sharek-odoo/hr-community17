# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    "name": "Recruitment extension (Saudi)",
    "summary": "",
    "version": "0.1",
    'category': 'Human Resources/Recruitment',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    "description": """
    """,

    "license": "OPL-1",
    "installable": True,
    "depends": [
        'hr_recruitment','website_hr_recruitment','website'
    ],
    "data": [
        'data/hr_whitelist.xml',
        'view/hr_applicant.xml',
        'view/website_hr_recruitment.xml'
    ],
    'assets': {
    'web.assets_frontend': [
        # 'sharek_hr_recruitment_extension/static/src/xml/*.xml',
        'sharek_hr_recruitment_extension/static/src/js/hr_recruitment_linkedin_optional.js'
    ],
},
}
