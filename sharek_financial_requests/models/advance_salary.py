from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import date,timedelta

class AdvanceSalaryAllowance(models.Model):
    _name = 'advance.salary'
    _description = 'Advance Salary'
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
        ('draft', 'Applicant Submitted'),
        ('direct_manager', 'Direct Manager Approval'),
        ('department_manager', 'Department Manager Approval'),
        ('hr', 'HR Manager Approval'),
        ('ceo', 'CEO Approval'),
        ('finance', 'Finance Team Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel',  'Cancel'),
    ], default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company.id
    )
    salary_taken = fields.Float(string="Number of salaries to be taken",required=True)
    total_gross_salary = fields.Float(string="total_gross_salary")
    gross_salary = fields.Float(
        string="Gross Salary",
        compute="_compute_gross_salary",
    )
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    first_approve_id = fields.Many2one('res.users',string='First Approve',copy=False)

    @api.depends('salary_taken', 'employee_id.contract_id.total_gross_salary')
    def _compute_gross_salary(self):
        for rec in self:
            rec.gross_salary = rec.salary_taken *  rec.total_gross_salary

    
    vendor_bill_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)

    def create_vendor_bill(self):
        for rec in self:
            if not rec.employee_id.address_id:
                raise ValidationError("The employee must have a Vendor (Home Address) set to create the vendor bill.")

            # Get configuration
            account_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.advance_salary_account_id')
            journal_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.financial_request_journal_id')

            if not account_id or not journal_id:
                raise ValidationError("Please configure both Advance Salary Account and Journal in Settings.")

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
                'name': f'Advance Salary for {rec.employee_id.name}',
                'account_id': account_id,
                'quantity': 1.0,
                'price_unit': rec.gross_salary,
            }))

            move_vals['invoice_line_ids'] = lines

            bill = self.env['account.move'].create(move_vals)
            rec.vendor_bill_id = bill.id
            bill.message_post(body=f"Vendor bill created from Advance Salary {rec.name}")


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('salary.advance.allowance') or 'New'
        return super().create(vals)


    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete record in draft state only!"))
        return super(AdvanceSalaryAllowance, self).unlink()
    


    @api.onchange('employee_id')
    def onchange_employee(self):
        self.current_job_id = self.employee_id.job_id
        self.current_department_id = self.employee_id.department_id
        self.manager_id = self.employee_id.parent_id
        self.total_gross_salary = self.employee_id.contract_id.total_gross_salary
     

    def _create_activity(self, user_ids, summary, note):
        """Helper to create activity (bell + email)"""
        if not user_ids:
            return
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            # 1. Schedule activity (shows in bell)
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user_id,
                summary=summary,
                note=note,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )

            # 2. Send email
            partner = self.env['res.users'].browse(user_id).partner_id
            if partner and partner.email:
                self.message_post(
                    body=f"<p>{note}</p><p>Request: {self.display_name}</p>",
                    subject=summary,
                    partner_ids=[partner.id],
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )    

    def action_submit(self):
        for rec in self:
            rec.state = 'direct_manager'

            # get direct manager (employee's parent)
            direct_manager_user = rec.employee_id.parent_id.sudo().user_id
            if direct_manager_user:
                rec.sudo()._create_activity(
                    direct_manager_user.id,
                    _("Advance Salary Request: Direct Manager Approval"),
                    _("Please review and approve the request.")
                )
            else:
                raise ValidationError(_("No direct manager is assigned to this employee."))


    def action_direct_manager_approve(self):
        for rec in self:
            rec.state = 'department_manager'

            # get department manager (parent of parent)
            dept_manager_user = rec.employee_id.parent_id.parent_id.user_id
            if dept_manager_user:
                rec._create_activity(
                    dept_manager_user.id,
                    _("Advance Salary Request: Department Manager Approval"),
                    _("Please review and approve the request.")
                )
            else:
                raise ValidationError(_("No department manager is assigned for this employee."))

    def action_department_manager_approve(self):
        self.state = 'hr'
        users = self.env.ref('sharek_hr_employee_loan.group_loan_hr_manager').users
        self._create_activity(users.ids, _("Advance Salary Request: HR Approval"),
                              _("Please review and approve the request."))

    def action_hr_approve(self):
        self.state = 'ceo'
        users = self.env.ref('sharek_hr_employee_loan.group_loan_ceo').users
        self._create_activity(users.ids, _("Advance Salary Request: CEO Approval"),
                              _("Please review and approve the request."))

    def action_ceo_approve(self):
        self.state = 'finance'
        users = self.env.ref('sharek_hr_employee_loan.group_loan_finance').users
        self._create_activity(users.ids, _("Advance Salary Request: Finance Approval"),
                              _("Please review and approve the request."))

    def action_finance_approve(self):
        self.create_vendor_bill()
        self.state = 'approved'
        # Notify the employee back
        if self.employee_id.user_id:
            self._create_activity(self.employee_id.user_id.id,
                                  _("Advance Salary Request Approved"),
                                  _("Your advance salary request has been approved."))

    def action_cancel(self):
        self.state = 'cancel' 


    def action_reject(self):
        self.state = 'rejected'    

    def action_set_draft(self):
        self.state = 'draft'       


    def action_view_vendor_bill_advance(self):
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