# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
import werkzeug
from odoo import http
from odoo.http import request, route
# from datetime import datetime
from odoo import models, fields,tools, _
from datetime import date, datetime, time
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import UserError
import warnings
import babel

class HrSelfService(CustomerPortal):
    
    @http.route(['/my/time_off'], type='http', auth="user",  website=True)
    def portal_my_time_off(self, **post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
        time_off = request.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee.id)])
        types = request.env['hr.leave.type'].sudo().search(
            [('allocation_validation_type', 'in', ['officer', 'no', 'set']),('requires_allocation','=','no')])
        # types = request.env['hr.leave.type'].sudo().search(['&',('virtual_remaining_leaves','>',0),'|',('allocation_validation_type','in',['yes','no']),('max_leaves','>','0')])
        error = []
        if 'submit' in post:
            time_off_type_options = []
            for option in types:
                time_off_type_options.append(_(option.id))
            print('tiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii',time_off_type_options,post)
            if post.get('time_off_type'):
                time_off_type = post['time_off_type'].strip()
                if int(time_off_type) not in time_off_type_options:
                    raise UserError(_('Please choose a valid time off type.'))
                    # error["time_off_type"] = _('Please choose a valid time off type')
            if error:
                pass

            else:
                # try :
                    date_to = datetime.strptime(post['date_to'], '%Y-%m-%d')
                    date_from = datetime.strptime(post['date_from'], '%Y-%m-%d')
                    m = date_to - date_from
                    print('...................................',post,employee)
                    time_off_id = request.env['hr.leave'].sudo().create({
                        'request_date_from': date_from.date(),
                        'request_date_to': date_to.date(),
                        'holiday_status_id': int(time_off_type),
                        'employee_id': employee.id,
                        'number_of_days': m.total_seconds() / (60 * 60 * 24),
                        'name': post['name'],
                    })
                # except:
                #     raise UserError(_('Set Correct  information'))
                    return request.redirect('/my/time_off')

        values.update({
            'page_name': 'time_off',
            'error': error,
            'types': types,
            'time_off': time_off,
            'page_name': 'time off',
            'default_url': '/my/time_off',
        })
        return request.render("sharek_hr_self_service_timeoff.portal_my_time_off", values)

    @http.route(['/my/leave_allocation'], type='http', auth="user",  website=True)
    def portal_my_leave_allocation(self, **post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
        leave_allocation = request.env['hr.leave.allocation'].sudo().search(
            [('employee_id', '=', employee.id)])
        types = request.env['hr.leave.type'].sudo().search(
            [('allocation_validation_type', '!=', 'no'),('requires_allocation','=','yes')])
        error = []
        if 'submit' in post:
            time_off_type_options = []
            for option in types:
                time_off_type_options.append(_(option.id))
            if post.get('time_off_type'):
                time_off_type = post['time_off_type'].strip()
                if int(time_off_type) not in time_off_type_options:
                    raise UserError(_('Please choose a valid time off type.'))
                    # error["time_off_type"] = _('Please choose a valid time off type')
            if error:
                pass
            else:
                try:
                    leave_allocation_id = request.env['hr.leave.allocation'].sudo().create({
                        'name': post['name'],
                        'notes': post['reason'],
                        'holiday_status_id': int(time_off_type),
                        'employee_id': employee.id
                    })
                    print('\n\n\n\n\n\n\n\n', post['number_of_days_display'])
                    if leave_allocation_id.type_request_unit == 'hour':
                        leave_allocation_id.number_of_days = int(
                            post['number_of_days_display'])
                    if leave_allocation_id.type_request_unit == 'day':
                        leave_allocation_id.number_of_days = int(
                            post['number_of_days_display'])
                except:
                    raise UserError(_('Set Correct  information'))
                return request.redirect('/my/leave_allocation')

        values.update({
            'page_name': 'leave_allocation',
            'types': types,
            'leave_allocation': leave_allocation,
            'page_name': 'leave allocation',
            'default_url': '/my/leave_allocation',
        })
        return request.render("sharek_hr_self_service_timeoff.portal_my_leave_allocation", values)