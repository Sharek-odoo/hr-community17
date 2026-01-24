from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import date,timedelta

class FinancialClaimAllowance(models.Model):
    _name = 'financial.claim'
    _description = 'Financial Claim'
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
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments",required=True)
    state = fields.Selection([
        ('draft', 'Applicant Submitted'),
        ('direct_manager', 'Direct Manager Approval'),
        ('department_manager', 'Department Manager Approval'),
        ('hr', 'HR Manager Approval'),
        ('ceo', 'CEO Approval'),
        ('finance', 'Finance Team Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel','Cancel'),
    ], default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company.id
    )
    amount = fields.Float(string="Amount",required=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)
    first_approve_id = fields.Many2one('res.users',string='First Approve',copy=False)
    
    vendor_bill_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)

    def create_vendor_bill(self):
        for rec in self:
            if not rec.employee_id.address_id:
                raise ValidationError("The employee must have a Vendor (Home Address) set to create the vendor bill.")

            # Get configuration
            account_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.financial_claim_account_id')
            journal_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.financial_request_journal_id')

            if not account_id or not journal_id:
                raise ValidationError("Please configure both Financial Claim Account and Journal in Settings.")

            account_id = int(account_id)
            journal_id = int(journal_id)

            move_vals = {
                'move_type': 'in_invoice',
                'partner_id': rec.employee_id.work_contact_id.id,
                'journal_id': journal_id,
                'invoice_date': fields.Date.context_today(rec),
                # 'first_approve_id':rec.first_approve_id.id,
                'ref': rec.name,
                'invoice_origin': rec.name,
                'invoice_line_ids': [],
            }

            lines = []
            lines.append((0, 0, {
                'name': f'Financial Claim for {rec.employee_id.name}',
                'account_id': account_id,
                'quantity': 1.0,
                'price_unit': rec.amount,
            }))

            move_vals['invoice_line_ids'] = lines

            bill = self.env['account.move'].create(move_vals)
            rec.vendor_bill_id = bill.id
            bill.message_post(body=f"Vendor bill created from Financial Claim {rec.name}")


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('financial.claim.allowance') or 'New'
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete record in draft state only!"))
        return super(FinancialClaimAllowance, self).unlink()
            


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
        

    def action_submit(self):
        for rec in self.sudo():
            rec.state = 'direct_manager'
            # direct manager
            direct_manager_user = rec.employee_id.parent_id.sudo().user_id
            if direct_manager_user:
                rec.sudo()._create_activity(
                    direct_manager_user.id,
                    _("Financial Claim Request: Direct Manager Approval"),
                    _("A new request is waiting for your approval.")
                )
            else:
                raise ValidationError(_("This employee does not have a direct manager assigned."))


    def action_direct_manager_approve(self):
        for rec in self.sudo():
            rec.state = 'department_manager'
            # department manager (manager of the direct manager)
            dept_manager_user = rec.employee_id.parent_id.parent_id.user_id
            if dept_manager_user:
                rec._create_activity(
                    dept_manager_user.id,
                    _("Financial Claim Request: Department Manager Approval"),
                    _("Please review and approve this request.")
                )
            else:
                raise ValidationError(_("This employee does not have a department manager assigned."))

    def action_department_manager_approve(self):
        self.state = 'hr'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_hr_manager').users
        self._create_activity(users.ids,
                              _("Financial Claim Request: HR Approval"),
                              _("Please review and approve this request."))

    def action_hr_approve(self):
        self.state = 'ceo'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_ceo').users
        self._create_activity(users.ids,
                              _("Financial Claim Request: CEO Approval"),
                              _("Please review and approve this request."))

    def action_ceo_approve(self):
        self.state = 'finance'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_finance').users
        self._create_activity(users.ids,
                              _("Financial Claim Request: Finance Approval"),
                              _("Please review and approve this request."))

    def action_finance_approve(self):
        self.create_vendor_bill()
        self.state = 'approved'
        # Notify employee
        if self.employee_id.user_id:
            self._create_activity(self.employee_id.user_id.id,
                                  _("Financial Claim Request Approved"),
                                  _("Your Financial Claim request has been approved."))


    def action_reject(self):
        self.state = 'rejected'    

    def action_cancel(self):
        self.state = 'cancel' 

    def action_set_draft(self):
        self.state = 'draft'    


    def action_view_vendor_bill_claim(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            raise UserError("No Vendor Bill linked.")
        return {
            'name': 'Vendor Bill',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.vendor_bill_id.id,
            'domain':[('id','=',self.vendor_bill_id.id)],
            'target': 'current',
        }    