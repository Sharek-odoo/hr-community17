# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    "name": "Employee Additional Information",
    "summary": "Employee Additional Information(Saudi)",
    'category': 'Human Resources',
    "description": """
        Additional Information.
         
    """,
    
    "author": "Sharek",
    "license": "OPL-1",
    'website': "https://sharek.com.sa",
    "version": "17.0",
    "installable": True,
    
    "depends": [
        'hr','hr_contract'
    ],
    "data": [
        'security/ir.model.access.csv',
        'view/hr_employee.xml',
        'view/res_config_settings.xml',
        'data/data.xml',
        'report/employee_details_report.xml',
    ],
    'images': [
        
    ],
  
}

