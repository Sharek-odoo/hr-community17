# -*- coding: utf-8 -*-
{
    'name': "HR Exception",

    'summary': "",

    'description': """

    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/permission_requests.xml',
        'views/permission_allocation.xml',
        'views/business_visit_requests.xml',
    ],
    
}

