# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import ValidationError,UserError
from datetime import timedelta, datetime, time
from math import ceil
from odoo.addons.resource.models.utils import HOURS_PER_DAY
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG


class ResUsers(models.Model):
    _inherit = "res.users"

    def write(self, vals):
        res = super().write(vals)
        if "groups_id" in vals:
            self.env['ir.ui.view'].clear_caches()
        return res


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    state = fields.Selection(
        [
            ('draft', 'Employee (Requester)'),
            ('manager', 'Direct Manager'),
            ('sector_manager', 'Sector Manager'),
            ('ceo', 'CEO'),
            ('validate1', 'HR Team'),
            ('refuse', 'Refused'),
            ('cancel', 'Cancelled'),
            ('validate', 'Approved'),
            ('done','Done'),
            ('hr','HR')
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
        readonly=False
    )

    # ('hr', 'HR Team'),


    _available_leave_types = fields.Many2many(
        'hr.leave.type',
        compute='_compute_from_employee_id',
        string="Available Leave Types",
    )

    @api.constrains('employee_id', 'holiday_status_id', 'request_date_from', 'request_date_to')
    def _check_leave_allocation_constraint(self):
        for leave in self:
            # Only employee leaves that require allocation
            if leave.holiday_type != 'employee':
                continue
            if leave.holiday_status_id.requires_allocation != 'yes':
                continue
            if leave.state in ('cancel', 'refuse'):
                continue
            if not leave.request_date_from or not leave.request_date_to:
                continue

            # ✅ Manually compute requested days
            if leave.leave_type_request_unit == 'day':
                requested_days = (leave.request_date_to - leave.request_date_from).days + 1
            elif leave.leave_type_request_unit == 'hour':
                # Convert hours to days based on working hours per day
                requested_days = leave.number_of_hours / leave.employee_id.contract_id.resource_calendar_id.hours_per_day
            else:
                requested_days = 0

            # ✅ Get allocation data
            employees = leave._get_employees_from_holiday_type()
            leave_data = leave.holiday_status_id.get_allocation_data(employees, leave.request_date_from)

            for employee in employees:
                if employee not in leave_data or not leave_data[employee]:
                    raise ValidationError(_(
                        "You do not have any allocation for this leave type. "
                        "Please request an allocation before submitting your leave."
                    ))

                virtual_remaining = leave_data[employee][0][1]['virtual_remaining_leaves']
                allows_negative = leave_data[employee][0][1]['allows_negative']
                max_neg = leave_data[employee][0][1]['max_allowed_negative']

                # ✅ Check allocation
                if virtual_remaining - requested_days < 0:
                    if not allows_negative or virtual_remaining - requested_days < -max_neg:
                        raise ValidationError(_(
                            "You do not have enough balance for %s days of %s leave. "
                            "Your remaining allocation is %.2f days."
                        ) % (requested_days, leave.holiday_status_id.name, virtual_remaining))




    def _force_cancel(self, reason, msg_subtype='mail.mt_comment'):
        recs = self.browse() if self.env.context.get(MODULE_UNINSTALL_FLAG) else self
        for leave in recs:
            leave.message_post(
                body=_('The time off has been canceled: %s', reason),
                subtype_xmlid=msg_subtype
            )

            responsibles = self.env['res.partner']
            # manager
            if (leave.holiday_status_id.leave_validation_type == 'manager' and leave.state == 'validate') or (leave.holiday_status_id.leave_validation_type == 'both' and leave.state == 'validate1'):
                responsibles = leave.employee_id.leave_manager_id.partner_id
            # officer
            elif leave.holiday_status_id.leave_validation_type == 'hr' and leave.state == 'validate':
                responsibles = leave.holiday_status_id.responsible_ids.partner_id
            # both
            elif leave.holiday_status_id.leave_validation_type == 'both' and leave.state == 'validate':
                responsibles = leave.employee_id.leave_manager_id.partner_id
                responsibles |= leave.holiday_status_id.responsible_ids.partner_id

            if responsibles:
                self.env['mail.thread'].sudo().message_notify(
                    partner_ids=responsibles.ids,
                    model_description='Time Off',
                    subject=_('Canceled Time Off'),
                    body=_(
                        "%(leave_name)s has been cancelled with the justification: <br/> %(reason)s.",
                        leave_name=leave.display_name,
                        reason=reason
                    ),
                    email_layout_xmlid='mail.mail_notification_light',
                )
        leave_sudo = self.sudo()
        leave_sudo.write({'state':'cancel'})
        # leave_sudo.with_context(from_cancel_wizard=True).active = False
        leave_sudo.meeting_id.active = False
        leave_sudo._remove_resource_leave()

    @api.depends('employee_id')
    def _compute_from_employee_id(self):
        """Extend standard compute to apply gender & religion-based filtering."""
        # Keep the base Odoo behavior
        super(HolidaysRequest, self)._compute_from_employee_id()

        for leave in self:
            if not leave.employee_id:
                leave._available_leave_types = self.env['hr.leave.type']
                continue

            emp = leave.employee_id
            gender = emp.gender
            religion = emp.religion_id
            company_id = emp.company_id.id

            # Get all time-off types that are normally valid
            leave_types = self.env['hr.leave.type'].search([
                ('company_id', 'in', [company_id, False]),
            ])

            # ✅ Filter by gender if applicable
            leave_types = leave_types.filtered(
                lambda lt: (not lt.for_specific_gender) or (lt.gender == gender)
            )

            # ✅ Filter by religion if applicable
            leave_types = leave_types.filtered(
                lambda lt: not lt.religion_ids or religion in lt.religion_ids
            )

            # Assign final filtered leave types
            leave._available_leave_types = leave_types


    # override this function to make cancel in approve state just
    @api.depends_context('uid')
    @api.depends('state', 'employee_id')
    def _compute_can_cancel(self):
        for leave in self:
            # Only check if state is 'validate'
            leave.can_cancel = leave.state == 'validate'


    @api.model_create_multi
    def create(self, vals_list):
        """Extra safety: block creation of mismatched gender or religion."""
        for vals in vals_list:
            emp_id = vals.get('employee_id')
            leave_type_id = vals.get('holiday_status_id')
            if emp_id and leave_type_id:
                emp = self.env['hr.employee'].browse(emp_id)
                leave_type = self.env['hr.leave.type'].browse(leave_type_id)

                # 🚫 Gender restriction check
                if leave_type.for_specific_gender and leave_type.gender != emp.gender:
                    raise UserError(_("You cannot request this leave type due to gender restriction."))

                # 🚫 Religion restriction check
                if leave_type.religion_ids and emp.religion_id not in leave_type.religion_ids:
                    raise UserError(_("You cannot request this leave type due to religion restriction."))

        res = super(HolidaysRequest,self).create(vals_list)
        # res._check_validity()
        return res



    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        # _get_view returns (arch, view) where arch is an etree element
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)

        # Only change the search view
        if view_type == 'search' and arch is not None:
            user = self.env.user
            nodes = arch.xpath("//filter[@name='waiting_for_me']")
            if nodes:
                node = nodes[0]

                if user.has_group("sharek_hr_time_off.group_direct_manager"):
                    node.set(
                        "domain",
                        "[ '|', '&', ('employee_id.user_id','=',uid), ('state','=','draft'), '&', ('employee_id.parent_id.user_id','=',uid), ('state','=','manager') ]"
                    )


                elif user.has_group("sharek_hr_time_off.group_sector_manager"):
                    node.set(
                        "domain",
                        "[ '|', '&', ('employee_id.user_id','=',uid), ('state','=','draft'), '&', ('employee_id.parent_id.user_id','=',uid), ('state','=','sector_manager') ]"
                    )  

                elif user.has_group("sharek_hr_time_off.group_hr_timeoff"):
                    node.set(
                        "domain",
                        "[ '|', '&', ('employee_id.user_id','=',uid), ('state','=','draft'), '&', ('employee_id.parent_id.user_id','=',uid), ('state','=','validate1') ]"
                    ) 

                elif user.has_group("sharek_hr_time_off.group_ceo"):
                    node.set(
                        "domain",
                        "[ '|', '&', ('employee_id.user_id','=',uid), ('state','=','draft'), '&', ('employee_id.parent_id.user_id','=',uid), ('state','=','ceo') ]"
                    )           

                # STRICT: if user is ONLY employee_submit -> only own drafts
                elif user.has_group("sharek_hr_time_off.group_employee_submit"):
                    node.set("domain", "[('employee_id.user_id','=',uid), ('state','=','draft')]")

                # USER IN BOTH employee_submit AND manager-like groups -> choose BEHAVIOR:
                # Option A (union): show both my drafts OR records for managers
                

                

                # Else: normal manager/CEO/HR domain
                else:
                    node.set(
                        "domain",
                        "['|', '&', ('state', '=', 'manager'), ('employee_id.parent_id.user_id','=',uid),"
                        " '&', ('state', '=', 'sector_manager'), '|', ('employee_id.parent_id.parent_id.user_id','=',uid), ('employee_id.parent_id.user_id','=',uid),"
                        " '|', ('state', '=', 'ceo'), '|', '&', ('state','in',('draft','validate')), ('employee_id.user_id','=',uid), ('state','=','validate1') ]"
                    )

        return arch, view


    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        """Force can_approve to always True"""
        for holiday in self:
            holiday.can_approve = True

    def _check_approval_update(self, state):
        """Disable access/group restrictions"""
        return True

    @api.depends('holiday_status_id')
    def _compute_state(self):
        for leave in self:
            leave.state = 'draft'


    def _create_activity(self, user_ids, summary, note):
        """Create bell notification + email"""
        if not user_ids:
            return
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            # 1. Bell notification
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user_id,
                summary=summary,
                note=note,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )
            # 2. Email
            partner = self.env['res.users'].browse(user_id).partner_id
            if partner and partner.email:
                self.sudo().message_post(
                    body=f"<p>{note}</p><p>Request: {self.display_name}</p>",
                    subject=summary,
                    partner_ids=[partner.id],
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )    

    def action_confirm(self):
        """Employee submits → Direct Manager"""
        for leave in self:
            if leave.state != 'draft':
                raise UserError(_("Only draft requests can be submitted."))
            leave.state = 'manager'
            direct_manager_user = leave.employee_id.parent_id.sudo().user_id
            if direct_manager_user:
                leave.sudo()._create_activity(
                    direct_manager_user.id,
                    _("Leave Request: Direct Manager Approval"),
                    _("A new request is waiting for your approval.")
                )
            else:
                raise ValidationError(_("This employee does not have a direct manager assigned."))
    
        # self.activity_update()
        return True

    def action_approve(self):
        """Direct Manager → Sector Manager"""
        for leave in self:
            if leave.state != 'manager':
                raise UserError(_("Only Direct Manager stage can be approved here."))
            if self.env.user != leave.employee_id.parent_id.user_id:
                raise UserError(_("Only the direct manager can approve this request."))
            if leave.holiday_status_id.timeoff_normal_type in ('annual','sick', 'bereavement_first', 'bereavement_secondary','maternity_men','haj','widow_leave','marriage_leave','remote_work','compensatory_leave'):
                leave.state = 'validate1'
                users = self.env.ref('sharek_hr_time_off.group_hr_timeoff').users
                self._create_activity(users.ids,
                              _("Leave Request: HR Approval"),
                              _("Please review and approve this request."))

            else:    
                leave.state = 'sector_manager'
                dept_manager_user = leave.employee_id.parent_id.parent_id.user_id
                if dept_manager_user:
                    leave._create_activity(
                        dept_manager_user.id,
                        _("Leave Request: Sector Manager Approval"),
                        _("Please review and approve this request.")
                    )
                else:
                    raise ValidationError(_("This employee does not have a sector manager assigned."))

        # self.activity_update()
        return True


    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

        for leave in self:
            if leave.state != 'sector_manager':
                raise UserError(_("Only Sector Manager stage can be validated here."))
            if not leave.employee_id.parent_id.parent_id:
                raise UserError(_("This employee does not have a sector manager."))
            if self.env.user != leave.employee_id.parent_id.parent_id.user_id:
                raise UserError(_("Only the sector manager can validate this request."))

            if leave.holiday_type != 'employee' or\
                (leave.holiday_type == 'employee' and len(leave.employee_ids) > 1):
                employees = leave._get_employees_from_holiday_type()

                conflicting_leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True
                ).search([
                    ('date_from', '<=', leave.date_to),
                    ('date_to', '>', leave.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('holiday_type', '=', 'employee'),
                    ('employee_id', 'in', employees.ids)])

                if conflicting_leaves:
                    # YTI: More complex use cases could be managed in master
                    if leave.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                        raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

                    conflicting_leaves._split_leaves(leave.request_date_from, leave.request_date_to + timedelta(days=1))

                values = leave._prepare_employees_holiday_values(employees)
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    no_calendar_sync=True,
                    leave_skip_state_check=True,
                    # date_from and date_to are computed based on the employee tz
                    # If _compute_date_from_to is used instead, it will trigger _compute_number_of_days
                    # and create a conflict on the number of days calculation between the different leaves
                    leave_compute_date_from_to=True,
                ).create(values)

                leaves._validate_leave_request()
        if self.holiday_status_id.timeoff_normal_type in ('maternity','study_leave','work_leave'):
            self.write({'state':'validate1'})   
            users = self.env.ref('sharek_hr_time_off.group_hr_timeoff').users
            self._create_activity(users.ids,
                          _("Leave Request: HR Approval"),
                          _("Please review and approve this request."))

        else:         
            self.write({'state': 'ceo'})
            users = self.env.ref('sharek_hr_time_off.group_ceo').users
            self._create_activity(users.ids,
                          _("Leave Request: HR Approval"),
                          _("Please review and approve this request."))

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True    


    def action_ceo_approve(self):
        """CEO → HR"""
        for leave in self:
            if leave.state != 'ceo':
                raise UserError(_("Only CEO stage can be approved here."))
            if not self.env.user.has_group('sharek_hr_time_off.group_ceo'):
                raise UserError(_("Only CEO group members can approve this request."))
            leave.state = 'validate1'
            users = self.env.ref('sharek_hr_time_off.group_hr_timeoff').users
            self._create_activity(users.ids,
                          _("Leave Request: HR Approval"),
                          _("Please review and approve this request."))

        # self.activity_update()
        return True

    def action_hr_approve(self):
        """HR → validate"""
        for leave in self:
            if leave.state != 'validate1':
                raise UserError(_("Only HR stage can be approved here."))
            if not self.env.user.has_group('hr.group_hr_user'):
                raise UserError(_("Only HR team can approve this request."))
            leave.state = 'validate'
            if leave.delegated_id:
                delegation = leave.env['delegate.access'].create({
                    'from_employee_id': leave.employee_id.id,
                    'to_employee_id': leave.delegated_id.id,
                    'until_date': leave.date_to,
                })
                delegation.action_submit()
        self.activity_update()
        return True

    def action_refuse(self):
        """Refuse from any stage"""
        for leave in self:
            if leave.state not in ['draft', 'manager', 'sector_manager', 'ceo', 'validate1']:
                raise UserError(_("Only pending requests can be refused."))
            leave.state = 'refuse'
        self.activity_update()
        return True

    def action_draft(self):
        self.write({
            'state': 'draft',
        })
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True



    