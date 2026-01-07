from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime,timedelta,date
import calendar


class HrBusinessVisitRequest(models.Model):
    _name = 'hr.business.visit.request'
    _description = 'Business Visit Request'
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
        string="Total Hours", compute="_compute_duration",copy=False
)
    before_balance = fields.Float(
        string="Balance Before", readonly=True,copy=False)
    after_balance = fields.Float(
        string="Balance After Request", compute="_compute_after_balance", store=True, readonly=True,copy=False)

    reason = fields.Text(string="Reason", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager', 'Manager Approval'),
        ('hr', 'HR Approval'),
        ('done', 'Approved'),
        ('refused', 'Refused'),
    ], default='draft', string="Status", tracking=True)
    replacement = fields.Many2one(string='Replacement Employee')

    @api.depends('time_from', 'time_to')
    def _compute_duration(self):
        for rec in self:
            if rec.time_from is not None and rec.time_to is not None:
                rec.duration = round(rec.time_to - rec.time_from, 2)
            else:
                rec.duration = 0.0             

    @api.model
    def _get_current_before_balance(self, employee_id, request_date_str, exclude_id=None):
        """Return total hours of all requests for the month of request_date, optionally excluding one record."""
        if isinstance(request_date_str, str):
            request_date = datetime.strptime(request_date_str, "%Y-%m-%d").date()
        else:
            request_date = request_date_str

        first_day = request_date.replace(day=1)
        last_day = request_date.replace(
            day=calendar.monthrange(request_date.year, request_date.month)[1]
        )

        domain = [
            ('employee_id', '=', employee_id),
            ('request_date', '>=', first_day),
            ('request_date', '<=', last_day),
        ]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))

        # Get all requests for this employee in that month, excluding current record if given
        used_requests = self.search(domain)

        total_duration = sum(req.duration for req in used_requests)
        return round(total_duration, 2)


    @api.depends('duration')
    def _compute_after_balance(self):
        for rec in self:
            rec.after_balance = (rec.before_balance or 0.0) + (rec.duration or 0.0)      


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.business.visit.request') or 'New'
            
        if vals.get('employee_id') and vals.get('request_date') and not vals.get('before_balance'):
            before = self._get_current_before_balance(
                vals['employee_id'],
                fields.Date.from_string(vals['request_date']),
            )
            vals['before_balance'] = before
        return super().create(vals)


    def write(self, vals):
        for rec in self:
            if 'employee_id' in vals or 'request_date' in vals:
                employee_id = vals.get('employee_id', rec.employee_id.id)
                request_date = fields.Date.from_string(vals.get('request_date', rec.request_date))
                before = self._get_current_before_balance(employee_id, request_date, exclude_id=rec.id)
                vals['before_balance'] = before
        return super().write(vals)


    @api.onchange('employee_id', 'request_date')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id and rec.request_date:
                rec.before_balance = rec._get_current_before_balance(
                    rec.employee_id.id, rec.request_date)

    @api.constrains('time_from', 'time_to')
    def _check_time_validity(self):
        for rec in self:
            if rec.time_from is not None and rec.time_to is not None and rec.time_to <= rec.time_from:
                raise ValidationError(_("End time must be after start time."))

    def action_submit(self):
        for rec in self:
            rec.state = 'manager'
            if rec.employee_id.parent_id.user_id:
                rec.sudo()._create_activity(
                    rec.employee_id.parent_id.user_id.id,
                    _("Business Vist Request: Manager Approval"),
                    _("Please review and approve this request.")
                )

    def action_manager_approve(self):
        for rec in self:
            rec.state = 'hr'
            hr_group = self.env.ref('hr_exception.group_hr_user_exception')
            hr_users = hr_group.users
            rec._create_activity(
                hr_users.ids,
                _("Business Vist Request: HR Approval"),
                _("Please review and approve this request.")
            )

    def action_hr_approve(self):
        for rec in self:
            rec.state = 'done'
            if rec.employee_id.user_id:
                rec.sudo()._create_activity(
                    rec.employee_id.user_id.id,
                    _("Business Vist Request Approved"),
                    _("Your request has been approved by HR.")
                )

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'



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