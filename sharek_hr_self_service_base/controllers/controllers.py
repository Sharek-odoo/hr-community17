# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
import werkzeug
from odoo import http
from odoo.http import request, route
from datetime import datetime
from odoo import models, fields, _

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import UserError
# from odoo.exceptions import UserError, Warning
import warnings


class HrSelfService(CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth="public", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        is_employee = 0
        if employee:
            is_employee = 1
        values['is_employee'] = is_employee
        values.update({
            'employee': employee,
        })
        return request.render("sharek_hr_self_service_base.portal_my_home_noptech", values)

    @route(['/hr/self/service'], type='http', auth="user", website=True)
    def hr_self_service(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)])
        if not employee:
            return request.render("sharek_hr_self_service_base.not_employee_template")

       
        render_values = {
            'employee': employee,
            'partner': user,
          
        }

        return request.render("sharek_hr_self_service_base.my_account", render_values)