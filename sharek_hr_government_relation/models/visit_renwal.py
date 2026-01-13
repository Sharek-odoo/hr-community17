from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class VisaRenewal(models.Model):
    _name = 'visa.renewal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Visa Renewal Request'
    _rec_name = 'applicant_id'

    state = fields.Selection([
        ('draft', 'Submitted'),
        ('manager', 'Direct Manager Approval'),
        ('sector_manager', 'Sector Manager Approval'),
        ('hr_manager', 'HR Manager Approval'),
        ('done', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string="Status", default="draft", tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    applicant_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_ids[:1])

    visa_type_id = fields.Many2one('visa.type', string='Visa Type' )
    name_ar = fields.Char(string='Name in Arabic')
    name_en = fields.Char(string='Name in English' )

    passport_number = fields.Char(string='Passport Number' )
    passport_expiry_date = fields.Date(string='Passport Expiry Date' )

    nationality = fields.Char(string='Nationality')
    visa_country = fields.Char(string='Visa Country')

    duration_months = fields.Integer(string="Duration (Months)")

    # State transitions
    def action_submit(self):
        self.state = 'manager'

    def action_manager_approve(self):
        self.state = 'sector_manager'

    def action_sector_manager_approve(self):
        self.state = 'hr_manager'

    def action_hr_manager_approve(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset_draft(self):
        self.state = 'draft'

    # Deletion restriction
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Only draft records can be deleted."))
        return super().unlink()