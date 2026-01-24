from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
from datetime import date,timedelta


class ChildrenEducationAllowance(models.Model):
    _name = 'children.education.allowance'
    _description = 'Children Education Allowance'
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
    reason = fields.Text(string="Reason for Application", required=True)
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    state = fields.Selection([
        ('draft', 'Applicant'),
        ('hr_approved', 'HR Manager'),
        ('finance_approved', 'Finance Team'),
        ('approved','Approved'),
        ('rejected', 'Rejected'),
        ('cancel','Cancel'),
    ], default='draft', tracking=True)

    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        default=lambda self: self.env.company.id
    )
    grade_id = fields.Many2one('grade.grade',string="Grade",readonly=True)
    academic_year = fields.Many2one('academic.year',string="Academic Year",required=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)
    vendor_bill_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)
    line_ids = fields.One2many('children.education.allowance.line', 'education_id', string="Children Lines")
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)
    first_approve_id = fields.Many2one('res.users',string='First Approve',copy=False)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('children.education.allowance') or 'New'
        return super().create(vals)
        

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete record in draft state only!"))
        return super(ChildrenEducationAllowance, self).unlink()
        


    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('amount'))
    

    @api.constrains('employee_id', 'academic_year', 'line_ids')
    def _check_total_children_per_year(self):
        for record in self:
            if not record.employee_id or not record.academic_year:
                continue

            # Get all other requests for same employee and academic year
            existing_requests = self.env['children.education.allowance'].search([
                ('employee_id', '=', record.employee_id.id),
                ('academic_year', '=', record.academic_year.id),
                ('id', '!=', record.id),
                ('state','!=','cancel')
            ])

            # All family_ids already used in other requests
            existing_family_ids = set(
                existing_requests.mapped('line_ids.family_id.id')
            )

            # Family IDs used in current request
            current_family_ids = [line.family_id.id for line in record.line_ids]

            # Check for duplicates within current request
            if len(current_family_ids) != len(set(current_family_ids)):
                raise ValidationError("Duplicate children found in the same request.")

            # Check for any overlap with existing requests
            overlap = existing_family_ids.intersection(current_family_ids)
            if overlap:
                raise ValidationError("Some children are already requested in another request for the same academic year.")

            # Total children across all requests
            total_children = len(existing_family_ids.union(current_family_ids))
            if total_children > 3:
                raise ValidationError("You can only request education allowance for up to 3 children per academic year.")

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.current_job_id = self.employee_id.job_id
        self.current_department_id = self.employee_id.department_id
        self.manager_id = self.employee_id.parent_id
        self.grade_id = self.employee_id.grade_id
        

    def _create_activity(self, user_ids, summary, note):
        """Helper to create activity (bell + email)"""
        if not user_ids:
            return
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            # Bell notification
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user_id,
                summary=summary,
                note=note,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )

            # Email
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
        self.sudo().state = 'hr_approved'
        # Notify HR group
        users = self.sudo().env.ref('sharek_hr_employee_loan.group_loan_hr_manager').users
        self.sudo()._create_activity(users.ids, _("Chilfern Education Request: HR Approval"),
                              _("A new Chilfern Education request is waiting for your approval."))

    def action_hr_approve(self):
        self.state = 'finance_approved'
        # Notify Finance group
        users = self.env.ref('sharek_hr_employee_loan.group_loan_finance').users
        self._create_activity(users.ids, _("Chilfern Education Request: Finance Approval"),
                              _("This Chilfern Education request is waiting for your finance approval."))

    def action_finance_approve(self):
        self.create_vendor_bill()
        self.state = 'approved'
        # Notify employee (applicant)
        if self.employee_id.user_id:
            self._create_activity(self.employee_id.user_id.id,
                                  _("Chilfern Education Request Approved"),
                                  _("Your Chilfern Education request has been approved."))

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
            account_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.education_child_account_id')
            journal_id = self.env['ir.config_parameter'].sudo().get_param('sharek_financial_requests.financial_request_journal_id')

            if not account_id or not journal_id:
                raise ValidationError("Please configure both Education Allowance Account and Journal in Settings.")

            account_id = int(account_id)
            journal_id = int(journal_id)

            move_vals = {
                'move_type': 'in_invoice',
                'partner_id': rec.employee_id.work_contact_id.id,
                'journal_id': journal_id,
                # 'first_approve_id':rec.first_approve_id.id,
                'invoice_date': fields.Date.context_today(rec),
                'ref': rec.name,
                'invoice_origin': rec.name,
                'invoice_line_ids': [],
            }

            lines = []
            for line in rec.line_ids:
                lines.append((0, 0, {
                    'name': f'Education Allowance for {line.family_id.name}',
                    'account_id': account_id,
                    'quantity': 1.0,
                    'price_unit': line.amount,
                }))

            move_vals['invoice_line_ids'] = lines

            bill = self.env['account.move'].create(move_vals)
            rec.vendor_bill_id = bill.id
            bill.message_post(body=f"Vendor bill created from Education Allowance Request {rec.name}")

    


    def action_view_vendor_bill(self):
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


class ChildrenEducationAllowanceLine(models.Model):
    _name = 'children.education.allowance.line'
    _description = 'Children Education Allowance Line'

    education_id = fields.Many2one('children.education.allowance', string="Allowance Request", ondelete='cascade')
    employee_id = fields.Many2one('hr.employee',related="education_id.employee_id")
    family_id = fields.Many2one(
        'hr.family',
        string='Child',
        domain="[('employee_id', '=', employee_id),('relationship','in',('son','daughter'))]",
        required=True
    )
    relationship = fields.Selection(related="family_id.relationship")
    id_no = fields.Char('ID Number',related="family_id.id_no")
    birth_date = fields.Date('Date of Birth',related="family_id.birth_date")
    marital = fields.Selection(related="family_id.marital")
    marital = fields.Selection(related="family_id.marital", store=True)

    amount = fields.Float(
        string="Amount",
        compute="_compute_amount",
        readonly=False
    )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            parent = self.env['children.education.allowance'].browse(vals.get('education_id'))
            if parent.state != 'draft':
                raise UserError(_("You can only add lines in Draft state."))
        return super().create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.education_id.state != 'draft':
                raise UserError(_("You can only delete lines in Draft state."))
        return super().unlink()

    # compute default amount from grade
    @api.depends('education_id.grade_id')
    def _compute_amount(self):
        for line in self:
            line.amount = line.education_id.grade_id.educ_allowance or 0.0
