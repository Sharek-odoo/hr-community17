# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


STATES = [('draft','Draft'),('submitted','Submitted'),('confirm','Confirmed'),('approved','approved'),('cancel','Cancelled')]

class EmployeeDirectWork(models.Model):
    _name = 'employee.direct.work'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Direct Work'



    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New',tracking=True,)
    employee_id = fields.Many2one('hr.employee', string="Employee",required=True, ondelete='cascade', index=True)
    employee_no = fields.Char(string='Employee ID', related='employee_id.employee_no')
    state =  fields.Selection(STATES, required=True, default='draft',tracking=True,)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True)
    date = fields.Date('Date',default=fields.Date.today())
    direct_work_date = fields.Date('Start Work Date',default=fields.Date.today(),tracking=True,)
    last_start_date = fields.Date('Last Start Date')


    note = fields.Text(tracking=True,)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('employee_direct_work.seq') or 'New'
        # Create the record first
        record = super(EmployeeDirectWork, self).create(vals)
        return record


    def _send_template_to_group(self, group_xmlid):
        """Send email using mail.template to all users in a group"""
        self.ensure_one()

        template = self.env.ref('sharek_employee_direct_work.employee_direct_work_mail_template_approve')
        group = self.env.ref(group_xmlid, raise_if_not_found=False)

        if not template or not group:
            return

        partners = group.users.mapped('partner_id').filtered(lambda p: p.email)
        if not partners:
            return

        email_values = {
            'email_from': self.env.user.partner_id.email or self.company_id.email,
            'email_to': ','.join(partners.mapped('email')),
        }

        template.send_mail(
            self.id,
            force_send=True,
            email_values=email_values
        )



    def action_draft(self):
        for record in self:
            record.state = 'draft'

    def action_submitted(self):
        for record in self:
            record.last_start_date = record.employee_id.direct_work_date
            record.state = 'submitted'
            record._send_template_to_group(
                'sharek_employee_direct_work.group_hr_department_manager'
            )

    def action_confirmed(self):
        for record in self:
            record.state = 'confirm'
            record._send_template_to_group(
                'sharek_employee_direct_work.group_hr_direct_manager'
            )

    def action_approved(self):
        for record in self:
            record.employee_id.direct_work_date = record.direct_work_date
            record.state = 'approved'


    def action_cancel(self):
        for record in self:
            record.employee_id.direct_work_date = record.last_start_date
            record.state = 'cancel'

    def unlink(self):
        for record in self:
            if record.state != 'cancel':
                raise UserError("You can only delete records that are in the 'Cancelled' state.")
        return super(EmployeeDirectWork, self).unlink()


