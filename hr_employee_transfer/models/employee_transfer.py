from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class HREmployeeTransfer(models.Model):
    _name = 'hr.employee.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Employee Promotion'

    name = fields.Char(default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_no = fields.Char(related='employee_id.employee_no', string='Employee ID')
    current_job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    join_date = fields.Date(related='employee_id.join_date', string='Joint Date')
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    current_department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    state = fields.Selection([
        ('draft', 'Waiting Employee Approval'),
        ('employee_approval','Waiting Current Department Manager Approval'),
        ('current_department_manager', 'Waiting New Department Manager Approval'),
        ('new_department_manager', 'Waiting HR Approval'),
        ('hr', 'Waiting CEO Approval'),
        ('ceo', 'Waiting HR Manager Approval'),
        ('hr_manager', 'Approved'),
        # ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
        ('refuse', 'Refused')
    ], string='Status', default='draft', tracking=True)

    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True)
    salary = fields.Monetary(string='Salary', readonly=True)
    request_date = fields.Date(string='Date', default=fields.Date.today())
    effective_date = fields.Date(string='Effective Date')
    new_manager_id = fields.Many2one('hr.employee', string='Manager')
    new_department_id = fields.Many2one('hr.department', string='Department')
    new_contract_id = fields.Many2one('hr.contract', string='Contract')
    new_salary = fields.Float(string='Salary',readonly=True)
    new_job_id = fields.Many2one('hr.job', string='Job Position')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', compute='_compute_company', store=True, readonly=False,
                                 default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    image_128 = fields.Image(related='employee_id.image_128')
    image_1920 = fields.Image(related='employee_id.image_1920')
    avatar_128 = fields.Image(related='employee_id.avatar_128')
    avatar_1920 = fields.Image(related='employee_id.avatar_1920')
    promotion_url = fields.Char('URL', compute='get_url')
    grade_id = fields.Many2one("grade.grade", "Grade", readonly=True)
    new_grade = fields.Many2one("grade.grade", "Grade")
    need_new_department_approval = fields.Boolean(compute='_compute_need_new_department_approval')
    need_show_submit_hr = fields.Boolean(compute='_compute_need_show_submit_hr')

    @api.depends('state', 'need_new_department_approval')
    def _compute_need_show_submit_hr(self):
        for rec in self:
            if rec.state == 'current_department_manager' and not rec.need_new_department_approval:
                rec.need_show_submit_hr = True
            elif rec.state == 'new_department_manager':
                rec.need_show_submit_hr = True
            else:
                rec.need_show_submit_hr = False


    @api.onchange('employee_id')
    def onchange_employee(self):
        self.current_job_id = self.employee_id.job_id
        self.current_department_id = self.employee_id.department_id
        self.manager_id = self.employee_id.parent_id
        self.contract_id = self.employee_id.contract_id
        self.salary = self.employee_id.contract_id.wage
        self.grade_id = self.employee_id.grade_id
        self.new_contract_id = self.employee_id.contract_id
        self.new_salary = self.employee_id.contract_id.wage


    @api.constrains('employee_id', 'effective_date')
    def _check_unique_employee_effective_month(self):
        for rec in self:
            if not rec.employee_id or not rec.effective_date:
                continue

            start_of_month = rec.effective_date.replace(day=1)
            end_of_month = (start_of_month + relativedelta(months=1)) - relativedelta(days=1)

            domain = [
                ('employee_id', '=', rec.employee_id.id),
                ('effective_date', '>=', start_of_month),
                ('effective_date', '<=', end_of_month),
                ('id', '!=', rec.id),
            ]
            existing = self.env['hr.employee.transfer'].search(domain, limit=1)

            if existing:
                raise ValidationError(_(
                    "A Transfer already exists for employee %s in the month of %s." % (
                        rec.employee_id.name, rec.effective_date.strftime('%B %Y')
                    )
                ))    

    def get_url(self):
        for record in self:
            ir_param = self.env['ir.config_parameter'].sudo()
            base_url = ir_param.get_param('web.base.url')
            action_id = self.env.ref('hr_employee_transfer.action_employee_transfer').id
            menu_id = self.env.ref('hr_employee_transfer.menu_view_transfer_evaluation').id
            if base_url:
                base_url += '/web#id=%s&action=%s&model=%s&view_type=form&cids=&menu_id=%s' % (
                    record.id, action_id, 'hr.employee.transfer', menu_id)
            record.promotion_url = base_url

    @api.depends('employee_id')
    def _compute_company(self):
        for record in self.filtered('employee_id'):
            record.company_id = record.employee_id.company_id

    @api.model
    def create(self, values):
        if not values.get('name') or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('employee.transfer')
        return super(HREmployeeTransfer, self).create(values)

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError(_("You can't delete record not in draft state"))
        return super(HREmployeeTransfer, self).unlink()

    @api.depends('current_department_id', 'new_department_id')
    def _compute_need_new_department_approval(self):
        for rec in self:
            rec.need_new_department_approval = rec.current_department_id != rec.new_department_id

    
    def _send_template_to_group(self, group_xmlid):
        """Send email using mail.template to all users in a group"""
        self.ensure_one()

        template = self.env.ref('hr_employee_transfer.employee_transfer_mail_template_approve')
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


    def action_employee_approve(self):
        self.state = 'employee_approval'
        self._send_template_to_group(
            'hr_employee_transfer.group_employee_transfer_manager'
        )

    def action_approve_current_department_manager(self):
        self.ensure_one()
        self.state = 'current_department_manager'
        self._send_template_to_group(
            'hr_employee_transfer.group_transfer_department_manager'
        )

    # Approve new department manager (only if departments differ)
    def action_approve_new_department_manager(self):
        self.ensure_one()
        self.state = 'new_department_manager'
        self._send_template_to_group(
            'hr_employee_transfer.group_transfer_hr'
        )


    # Submit to HR from current_department_manager or new_department_manager
    def action_submit_hr(self):
        self.ensure_one()
        self.state = 'hr'
        self._send_template_to_group(
            'hr_employee_transfer.group_transfer_ceo'
        )

    # Submit to CEO
    def action_submit_ceo(self):
        self.ensure_one()
        self.state = 'ceo'
        self._send_template_to_group(
            'hr_employee_transfer.group_transfer_hr_manager'
        )

    # Submit to HR Manager
    def action_submit_hr_manager(self):
        self.ensure_one()
        self.state = 'hr_manager'
        self.effective_date = fields.Date.today()
        self.employee_info_update()
        self._email_notification()

    # Final approval by HR Manager
    # def action_approve(self):
    #     self.ensure_one()
    #     self.state = 'approved'
    #     self.effective_date = fields.Date.today()
    #     self.employee_info_update()
    #     self._email_notification()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_refuse(self):
        self.write({'state': 'refuse'})

    def action_set_draft(self):
        self.write({'state':'draft'})

    def _email_notification(self):
        template_id = self.env.ref('hr_employee_transfer.employee_transfer_mail_template')
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id.id)
        if self.employee_id.work_email or self.employee_id.user_id.partner_id.email:
            email_values = {
                'email_from': self.env.user.partner_id.email or self.company_id.email,
            }
            template_id.send_mail(self.id, force_send=True, email_values=email_values)

    def employee_info_update(self):
        for record in self:
            contract = record.contract_id

            # Create promotion log entry
            self.env['hr.contract.transfer.log'].create({
                'contract_id': contract.id,
                'promotion_id': record.id,
                'old_wage': record.salary,
                'new_wage': record.new_salary,
                'old_grade': record.grade_id.id,
                'new_grade': record.new_grade.id,
            })

            # Now apply the changes to the employee
            record.employee_id.job_id = record.new_job_id or record.current_job_id
            record.employee_id.grade_id = record.new_grade or record.grade_id
            record.employee_id.department_id = record.new_department_id or record.current_department_id
            record.employee_id.parent_id = record.new_manager_id or record.manager_id
            record.employee_id.contract_id = record.new_contract_id or record.contract_id
            record.employee_id.contract_id.wage = record.new_salary or record.salary




class HrContractPromotionLog(models.Model):
    _name = 'hr.contract.transfer.log'
    _description = 'Transfer Log for Contract'

    contract_id = fields.Many2one('hr.contract', string="Contract", ondelete='cascade')
    promotion_id = fields.Many2one('hr.employee.transfer', string="Transfer Record")
    employee_id = fields.Many2one('hr.employee', string="Employee", related='promotion_id.employee_id')
    promotion_date = fields.Date(string="Transfer Date", related='promotion_id.request_date')
    effective_date = fields.Date(string="Effective Date", related='promotion_id.effective_date')

    old_wage = fields.Float(string="Old Wage")
    new_wage = fields.Float(string="New Wage")

    old_grade = fields.Many2one('grade.grade', string="Old Grade")
    new_grade = fields.Many2one('grade.grade', string="New Grade")



class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    transfer_log_ids = fields.One2many('hr.contract.transfer.log', 'contract_id', string="Promotion History")



class HrPayslipInherit(models.Model):
    _inherit = 'hr.payslip'

    transfer_id = fields.Many2one(
        'hr.employee.transfer',
        string="Transfer",
        compute='_compute_transfer_id',
        readonly=True
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_transfer_id(self):
        for payslip in self:
            transfer = self.env['hr.employee.transfer'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'approve'),
                ('effective_date', '>=', payslip.date_from.replace(day=1)),
                ('effective_date', '<=', payslip.date_to),
            ], order="effective_date desc", limit=1)

            payslip.transfer_id = transfer.id if transfer else False
