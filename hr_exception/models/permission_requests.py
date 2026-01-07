from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime,timedelta,date
import calendar


class HrPermissionRequest(models.Model):
    _name = 'hr.permission.request'
    _description = 'Permission Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Reference", default="New", readonly=True, copy=False)
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", required=True,
        default=lambda self: self.env.user.employee_id)
    request_date = fields.Date(
        string="Permission Date", required=True)
    time_from = fields.Float(string="From Time", required=True,copy=False)
    time_to = fields.Float(string="To Time", required=True,copy=False)

    duration = fields.Float(
        string="Total Hours", compute="_compute_duration",copy=False)
    monthly_balance = fields.Float(
        string="Monthly Balance", readonly=True,copy=False)
    after_balance = fields.Float(
        string="Balance After Request",  readonly=True,copy=False)
    # compute="_compute_after_balance", store=True,

    reason = fields.Text(string="Reason", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager', 'Manager Approval'),
        ('hr', 'HR Approval'),
        ('done', 'Approved'),
        ('refused', 'Refused'),
    ], default='draft', string="Status", tracking=True)

    @api.depends('time_from', 'time_to')
    def _compute_duration(self):
        for rec in self:
            if rec.time_from is not None and rec.time_to is not None:
                rec.duration = round(rec.time_to - rec.time_from, 2)
            else:
                rec.duration = 0.0


                

    @api.model
    def _get_current_monthly_balance(self, employee_id, request_date_str):
        """Return monthly balance for the month of request_date (or today by default)."""
        if isinstance(request_date_str, str):
            request_date = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        else:
            request_date = request_date_str
        first_day = request_date.replace(day=1)
        last_day = request_date.replace(
            day=calendar.monthrange(request_date.year, request_date.month)[1]
        )

        # 1. Get allocation balance
        allocation = self.env['permission.allocation'].search([
            ('employee_id', '=', employee_id)
        ], limit=1)
        total_allocated = allocation.hour_balance if allocation else 0.0

        # # 2. Get month range for request_date
        # first_day = request_date.replace(day=1)
        # last_day = request_date.replace(day=calendar.monthrange(request_date.year, request_date.month)[1])

        # 3. Get all approved requests for this employee in that month
        used_requests = self.search([
            ('employee_id', '=', employee_id),
            ('state', '=', 'done'),
            ('request_date', '>=', first_day),
            ('request_date', '<=', last_day),
        ])

        used_hours = sum(req.duration for req in used_requests)

        return round(total_allocated - used_hours, 2)        


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.permission.request') or 'New'
            
        if vals.get('employee_id') and vals.get('request_date') and not vals.get('monthly_balance'):
            balance = self._get_current_monthly_balance(
                vals['employee_id'], fields.Date.from_string(vals['request_date']))
            vals['monthly_balance'] = balance
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if 'employee_id' in vals or 'request_date' in vals:
                employee_id = vals.get('employee_id', rec.employee_id.id)
                request_date = fields.Date.from_string(vals.get('request_date', rec.request_date))
                balance = self._get_current_monthly_balance(employee_id, request_date)
                vals['monthly_balance'] = balance
        return super().write(vals)



    def _create_activity(self, user_ids, summary, note):
        if not user_ids:
            return
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            # 1. Create activity (Bell notification)
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user_id,
                summary=summary,
                note=note,
                date_deadline=fields.Date.today()
            )

            # 2. Send email through message_post
            partner = self.env['res.users'].sudo().browse(user_id).partner_id
            if partner and partner.email:
                self.message_post(
                    body=f"<p>{note}</p><p>Record: {self.display_name}</p>",
                    subject=summary,
                    partner_ids=[partner.id],   # recipient(s)
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )    




    # def _create_activity(self, user_ids, summary, note):
    #     """Create activity (bell + email notification)"""
    #     if not user_ids:
    #         return
    #     if isinstance(user_ids, int):
    #         user_ids = [user_ids]

    #     MailActivity = self.env['mail.activity']

    #     for user_id in user_ids:
    #         # 1. Create activity (shows in bell)
    #         activity = self.activity_schedule(
    #             'mail.mail_activity_data_todo',
    #             user_id=user_id,
    #             summary=summary,
    #             note=note,
    #             date_deadline=fields.Date.today()
    #         )

    #         # 2. Send email notification immediately
    #         if activity and activity.user_id.partner_id.email:
    #             template = self.env.ref('mail.mail_activity_data_todo')  # fallback if no custom template
    #             mail_values = {
    #                 'subject': summary,
    #                 'body_html': f"<p>{note}</p><p>Record: {self.display_name}</p>",
    #                 'email_to': activity.user_id.partner_id.email,
    #                 'author_id': self.env.user.partner_id.id,
    #                 'model': self._name,
    #                 'res_id': self.id,
    #             }
    #             mail = self.env['mail.mail'].create(mail_values)
    #             mail.send()    



    # def _create_activity(self, user_ids, summary, note):
    #     """Helper to create activities for one or multiple users"""
    #     if not user_ids:
    #         return
    #     if isinstance(user_ids, int):
    #         user_ids = [user_ids]

    #     for user_id in user_ids:
    #         self.activity_schedule(
    #             'mail.mail_activity_data_todo',   # standard To Do activity
    #             user_id=user_id,
    #             summary=summary,
    #             note=note,
    #             date_deadline=fields.Date.today()  # today deadline (shows as red in bell)
    #         )

    def _check_balance_valid(self):
        """Check that approving/submitting does not exceed monthly balance."""
        for rec in self:
            if not rec.employee_id or not rec.request_date:
                continue

            # Get current remaining balance
            current_balance = rec._get_current_monthly_balance(rec.employee_id.id, rec.request_date)
            after_balance = round(current_balance - (rec.duration or 0.0), 2)

            if after_balance < 0:
                raise ValidationError(_(
                    "Permission request exceeds available balance for %s. "
                    "Remaining balance after this request would be %.2f hours."
                ) % (rec.employee_id.name, after_balance))
    



    @api.depends('monthly_balance', 'duration')
    def _compute_after_balance(self):
        for rec in self:
            rec.after_balance = rec.monthly_balance - rec.duration if rec.duration else rec.monthly_balance

    @api.onchange('employee_id', 'request_date')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id and rec.request_date:
                rec.monthly_balance = rec._get_current_monthly_balance(
                    rec.employee_id.id, rec.request_date)

    @api.constrains('time_from', 'time_to')
    def _check_time_validity(self):
        for rec in self:
            if rec.time_from is not None and rec.time_to is not None and rec.time_to <= rec.time_from:
                raise ValidationError(_("End time must be after start time."))


    

    @api.constrains('request_date', 'duration')
    def _check_conditions(self):
        for rec in self:
            if rec.request_date and rec.request_date < fields.Date.today():
                raise ValidationError(_("Permission date must not be in the past."))
            if rec.duration > 4:
                raise ValidationError(_("Permission duration must not exceed 4 hours."))
            allocation = self.env['permission.allocation'].search([
                ('employee_id', '=', rec.employee_id.id)
            ], limit=1)
            balance = allocation.hour_balance if allocation else 0.0


            if rec.duration > balance or rec.duration > rec.monthly_balance:
                raise ValidationError(_("Permission duration must not be greater than balance."))

    def action_submit(self):
        for rec in self:
            rec._check_balance_valid()
            rec.state = 'manager'
            if rec.employee_id.parent_id.user_id:
                rec.sudo()._create_activity(
                    rec.employee_id.parent_id.user_id.id,
                    _("Permission Request: Manager Approval"),
                    _("Please review and approve this request.")
                )

    def action_manager_approve(self):
        for rec in self:
            rec._check_balance_valid()
            rec.state = 'hr'
            hr_group = self.env.ref('hr_exception.group_hr_user_exception')
            hr_users = hr_group.users
            rec._create_activity(
                hr_users.ids,
                _("Permission Request: HR Approval"),
                _("Please review and approve this request.")
            )

    def action_hr_approve(self):
        for rec in self:
            rec._check_balance_valid()
            rec._compute_after_balance()
            rec.state = 'done'
            if rec.employee_id.user_id:
                rec.sudo()._create_activity(
                    rec.employee_id.user_id.id,
                    _("Permission Request Approved"),
                    _("Your request has been approved by HR.")
                )


    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'




    # @api.model
    # def _get_current_monthly_balance(self, employee_id, request_date_str):
    #     # Convert string to date object
    #     request_date = fields.Date.from_string(request_date_str)

    #     first_day = request_date.replace(day=1)
    #     last_day = request_date.replace(
    #         day=calendar.monthrange(request_date.year, request_date.month)[1]
    #     )

    #     # 1. Get allocation for that employee and month
    #     allocation = self.env['permission.allocation'].search([
    #         ('employee_id', '=', employee_id)
    #     ], limit=1)

    #     allocation_balance = allocation.total_hours if allocation else 0.0

    #     # 2. Sum used requests only for that month
    #     used_requests = self.search([
    #         ('employee_id', '=', employee_id),
    #         ('state', '=', 'done'),
    #         ('request_date', '>=', first_day),
    #         ('request_date', '<=', last_day),
    #     ])

    #     used_hours = sum(req.duration for req in used_requests)

    #     return round(allocation_balance - used_hours, 2)           