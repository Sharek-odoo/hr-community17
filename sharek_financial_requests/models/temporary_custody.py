from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import date,timedelta

class TemporaryCustodyAllowance(models.Model):
    _name = 'temporary.custody'
    _description = 'Temporary Custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Request Number", required=True, copy=False, readonly=True, default='New')
    request_date = fields.Date(
        string="Request Date",
        default=fields.Date.context_today,
        required=True
    )
    employee_id = fields.Many2one('hr.employee', string="Applicant", required=True, default=lambda self: self.env.user.employee_id)
    employee_no = fields.Char(related='employee_id.employee_no', string='Employee ID')
    current_job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    current_department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    reason = fields.Text(string="Reason for applying", required=True)
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager', 'Direct Manager'),
        ('finance_1', 'Finance Review'),
        ('ceo', 'CEO Approval'),
        ('finance_2', 'Finance Final Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel','Cancel'),
    ], default='draft', tracking=True)
    amount = fields.Float(string="Amount",required=True)
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company.id
    )
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)
    custody_account_id = fields.Many2one('account.account',string="Temporary Custody Account")
    custody_jouranl_id = fields.Many2one('account.journal',string="Temporary Custody Journal",domain="[('type','=','general')]")
    
    vendor_bill_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)

    first_approve_id = fields.Many2one('res.users',string='First Approve',copy=False)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('temporary.custody') or 'New'
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete record in draft state only!"))
        return super(TemporaryCustodyAllowance, self).unlink()
    


    @api.onchange('employee_id')
    def onchange_employee(self):
        self.current_job_id = self.employee_id.job_id
        self.current_department_id = self.employee_id.department_id
        self.manager_id = self.employee_id.parent_id
        

    def _create_activity(self, user_ids, summary, note):
        """Create bell notification + email"""
        if not user_ids:
            return
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            # Bell notification
            self.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user_id,
                summary=summary,
                note=note,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )
            # Email notification
            partner = self.env['res.users'].browse(user_id).partner_id
            if partner and partner.email:
                self.sudo().message_post(
                    body=f"<p>{note}</p><p>Request: {self.display_name}</p>",
                    subject=summary,
                    partner_ids=[partner.id],
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )

    def action_submit(self):
        for rec in self.sudo():
            rec.state = 'direct_manager'

            # direct manager (employee's parent)
            direct_manager_user = rec.employee_id.parent_id.sudo().user_id
            if direct_manager_user:
                rec.sudo()._create_activity(
                    direct_manager_user.id,
                    _("Temporary Custody Request: Direct Manager Approval"),
                    _("A new request is waiting for your approval.")
                )
            else:
                raise ValidationError(_("This employee does not have a direct manager assigned."))

    def action_direct_manager_approve(self):
        self.state = 'finance_1'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_finance').users
        self._create_activity(users.ids,
                              _("Temporary Custody Request: Finance Review Approval"),
                              _("Please review and approve this request."))

    def action_finance1_approve(self):
        self.state = 'ceo'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_ceo').users
        self._create_activity(users.ids,
                              _("Temporary Custody Request: CEO Approval"),
                              _("Please review and approve this request."))

    def action_ceo_approve(self):
        self.state = 'finance_2'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_finance_manager').users
        self._create_activity(users.ids,
                              _("Temporary Custody Request: Final Finance Approval"),
                              _("Please review and approve this request."))

    def action_finance2_approve(self):
        self.create_vendor_bill()
        self.state = 'approved'
        # Notify employee on final approval
        if self.employee_id.user_id:
            self._create_activity(self.employee_id.user_id.id,
                                  _("Temporary Custody Request Approved"),
                                  _("Your Temporary Custody request has been approved."))


    def action_reject(self):
        self.state = 'rejected'

    def action_cancel(self):
        self.state = 'cancel' 

    def action_set_draft(self):
        self.state = 'draft'    


    def create_vendor_bill(self):
        for rec in self:
            if not rec.employee_id.work_contact_id:
                raise ValidationError("The employee must have a Vendor (Home Address) set to create the vendor bill.")

            # Get configuration
            account_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.temporary_custody_account_id')

            if not account_id:
                raise ValidationError("Please configure Temporary Custody Account in Settings.")

            account_id = int(account_id)

            move_vals = {
                'move_type': 'entry',
                'journal_id': rec.custody_jouranl_id.id,
                'invoice_date': fields.Date.context_today(rec),
                # 'first_approve_id':rec.first_approve_id.id,
                'ref': rec.name,
                'invoice_origin': rec.name,
                'line_ids': [],
            }

            lines = []
            lines.append((0, 0, {
                'name': f'Temporary Custody for {rec.employee_id.name}',
                'account_id': account_id,
                'debit': rec.amount,
                'credit':0.0,
                'partner_id': rec.employee_id.work_contact_id.id,
            }))
            lines.append((0, 0, {
                'name': f'Temporary Custody for - {rec.employee_id.name}',
                'account_id': rec.custody_account_id.id,
                'credit': rec.amount,
                'debit': 0.0,
            }))

            move_vals['line_ids'] = lines

            bill = self.env['account.move'].create(move_vals)
            rec.vendor_bill_id = bill.id
            bill.message_post(body=f"Journal Entry created from Temporary Custody {rec.name}")
    


    def action_view_vendor_bill_custody_2(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            raise UserError("No Journal Entry linked.")
        return {
            'name': 'Journal Entry Bill',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.vendor_bill_id.id,
            'domain':[('id','=',self.vendor_bill_id.id)],
            'target': 'current',
        }    
