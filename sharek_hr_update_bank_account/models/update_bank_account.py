from odoo import api, fields, models
from odoo.exceptions import ValidationError

class BankAccountUpdateRequest(models.Model):
    _name = 'bank.account.update.request'
    _description = 'Bank Account Update Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Request Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('bank.account.update.request')
    )
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    employee_partner = fields.Many2one('res.partner',related="employee_id.work_contact_id")
    iban_number = fields.Char(string="IBAN Number", required=True, tracking=True)
    account_number = fields.Char(string="Account Number", required=True, tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank", required=True, tracking=True)
    bank_account_id = fields.Many2one('res.partner.bank', string="Created Bank Account", readonly=True, tracking=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'bank_update_request_attachment_rel',
        'request_id', 'attachment_id', string="Attachments", required=True
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_approval', 'Waiting HR Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)

    def action_submit(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError("Attachments are required before submitting.")
            rec.state = 'hr_approval'

    def action_approve(self):
        for rec in self:
            if not rec.employee_partner:
                raise ValidationError("No partner found for the selected employee.")

            # Create bank account record linked to partner
            bank_account = self.env['res.partner.bank'].create({
                'acc_number': rec.account_number,
                'partner_id': rec.employee_partner.id,
                'bank_id': rec.bank_id.id,
            })

            # Save the created bank account in the request
            rec.bank_account_id = bank_account.id

            # Update employee's bank account
            rec.employee_id.bank_account_id = bank_account.id

            rec.state = 'approved'

    def action_open_bank_account(self):
        """Open the created bank account record."""
        self.ensure_one()
        if not self.bank_account_id:
            raise ValidationError("No bank account linked to this request.")
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner.bank',
            'view_mode': 'form',
            'res_id': self.bank_account_id.id,
            'target': 'current',
        }        

    def action_reject(self):
        self.state = 'rejected'

    @api.constrains('iban_number', 'account_number', 'bank_id')
    def _check_required_fields(self):
        for rec in self:
            if not rec.iban_number or not rec.account_number or not rec.bank_id:
                raise ValidationError("Please complete all required fields before submitting.")
