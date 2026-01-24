from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import date,timedelta

class OvertimeRequestAllowance(models.Model):
    _name = 'overtime.request'
    _description = 'Overtime Request'
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
        ('cancel','Cancel'),
    ], default='draft', tracking=True)
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company.id
    )

    working_hours_line_ids = fields.One2many('overtime.request.line', 'request_id', string="Working Hours")
    total_hours = fields.Float(string="Total Hours", compute="_compute_total_hours")
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)
    overtime_hour_wage = fields.Float(string="Overtime Hour Wage")
    vendor_bill_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)
    total_hours_wage = fields.Float(string="Total",compute="_compute_total_hours_wage")
    first_approve_id = fields.Many2one('res.users',string='First Approve',copy=False)

    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('overtime.request') or 'New'
        return super().create(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete record in draft state only!"))
        return super(OvertimeRequestAllowance, self).unlink()    

    @api.depends('working_hours_line_ids.number_of_hours')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = sum(rec.working_hours_line_ids.mapped('number_of_hours'))
    
    @api.depends('total_hours','overtime_hour_wage')
    def _compute_total_hours_wage(self):
        for rec in self:
            rec.total_hours_wage = rec.total_hours * rec.overtime_hour_wage
    

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.current_job_id = self.employee_id.job_id
        self.current_department_id = self.employee_id.department_id
        self.manager_id = self.employee_id.parent_id
        self.overtime_hour_wage = self.employee_id.contract_id.over_hour
        

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
            if not rec.working_hours_line_ids:
                raise ValidationError(_("You must add at least one Working Hours line before submitting."))

            rec.state = 'direct_manager'

            # direct manager (employee's parent)
            direct_manager_user = rec.employee_id.parent_id.sudo().user_id
            if direct_manager_user:
                rec.sudo()._create_activity(
                    direct_manager_user.id,
                    _("Overtime Request: Direct Manager Approval"),
                    _("A new request is waiting for your approval.")
                )
            else:
                raise ValidationError(_("This employee does not have a direct manager assigned."))


    def action_direct_manager_approve(self):
        for rec in self.sudo():
            rec.state = 'department_manager'

            # department manager (manager of direct manager)
            dept_manager_user = rec.employee_id.parent_id.parent_id.user_id
            if dept_manager_user:
                rec._create_activity(
                    dept_manager_user.id,
                    _("Overtime Request: Department Manager Approval"),
                    _("Please review and approve this request.")
                )
            else:
                raise ValidationError(_("This employee does not have a department manager assigned."))

    def action_department_manager_approve(self):
        self.state = 'hr'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_hr_manager').users
        self._create_activity(users.ids,
                              _("Overtime Request: HR Approval"),
                              _("Please review and approve this request."))

    def action_hr_approve(self):
        self.state = 'ceo'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_ceo').users
        self._create_activity(users.ids,
                              _("Overtime Request: CEO Approval"),
                              _("Please review and approve this request."))

    def action_ceo_approve(self):
        self.state = 'finance'
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_finance').users
        self._create_activity(users.ids,
                              _("Overtime Request: Finance Approval"),
                              _("Please review and approve this request."))

    def action_finance_approve(self):
        self.create_vendor_bill()
        self.state = 'approved'
        # Notify employee (applicant)
        if self.employee_id.user_id:
            self._create_activity(self.employee_id.user_id.id,
                                  _("Overtime Request Approved"),
                                  _("Your Overtime Request has been approved."))


    def action_reject(self):
        self.state = 'rejected'    

    def action_cancel(self):
        self.state = 'cancel' 

    def action_set_draft(self):
        self.state = 'draft'    

    def create_vendor_bill(self):
        for rec in self:
            if not rec.employee_id.address_id:
                raise ValidationError("The employee must have a Vendor (Home Address) set to create the vendor bill.")

            # Get configuration
            account_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.overtime_request_account_id')
            journal_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.financial_request_journal_id')

            if not account_id or not journal_id:
                raise ValidationError("Please configure both Overtime Request Account and Journal in Settings.")

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
            for line in rec.working_hours_line_ids:
                lines.append((0, 0, {
                    'name': f'Overtime Allowance for {line.day_type}',
                    'account_id': account_id,
                    'quantity': 1.0,
                    'price_unit': line.number_of_hours * rec.employee_id.contract_id.over_hour,
                }))

            move_vals['invoice_line_ids'] = lines

            bill = self.env['account.move'].create(move_vals)
            rec.vendor_bill_id = bill.id
            bill.message_post(body=f"Vendor bill created from Overtime Request {rec.name}")

    


    def action_view_vendor_bill_overtime(self):
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




class OvertimeRequestLine(models.Model):
    _name = 'overtime.request.line'
    _description = 'Overtime Working Hours Line'

    request_id = fields.Many2one('overtime.request', string="Overtime Request", ondelete='cascade')
    date = fields.Date(string="Date", required=True)
    day_type = fields.Selection([
        ('call', 'By Call'),
        ('holiday', 'Holiday'),
        ('working_day', 'Working Day')
    ], string="Type", required=True)
    hour_from = fields.Float(string="Hour From", required=True)
    hour_to = fields.Float(string="Hour To", required=True)
    number_of_hours = fields.Float(string="Number of Hours", compute='_compute_hours')

    @api.depends('hour_from', 'hour_to')
    def _compute_hours(self):
        for line in self:
            if line.hour_to and line.hour_from:
                duration = line.hour_to - line.hour_from
                line.number_of_hours = duration if duration > 0 else 0
            else:
                line.number_of_hours = 0
