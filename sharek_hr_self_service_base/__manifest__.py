# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    "name": "Self Service Portal Base",
    "version": "0.1",
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    "description": "",
    "depends": ['portal', 'website','web', 'hr', ],
    "external_dependencies": {"python": ["geocoder"]},
    "data" : [
        'views/assets.xml',
        'views/hr_self_service_template.xml',
        'views/portal.xml',
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'sharek_hr_self_service_base/static/src/js/hr_selfservice.js',
    #     ],
    # },

    'qweb': [],
    'installable': True,
    'application': True,
}
