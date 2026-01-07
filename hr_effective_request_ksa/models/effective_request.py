from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class EffectiveRequest(models.Model):
    _name = "effective.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Leave Effective Request'

    STATE = [
        ('draft', 'Draft'),
        ('waiting_approval', 'Submitted'),
        ('waiting_approval_2', 'Waiting Finance Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ]

    def _get_logged_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)])

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection(STATE, default='draft', string='State', tracking=True)
    name = fields.Char(string="Name", readonly=True, copy=False, default='New')
    another_employee = fields.Boolean(string="Another Employee", default=False)
    employee_id = fields.Many2one("hr.employee", default=_get_logged_employee, string="Employee", tracking=True)
    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    manager_id = fields.Many2one("hr.employee", related="employee_id.parent_id", string="Manager")
    employee_job = fields.Many2one("hr.job", related="employee_id.job_id", string="Job Position")
    request_date = fields.Date(string="Request Date", default=fields.Date.today(), tracking=True)
    leave_id = fields.Many2one("hr.leave", string="Leave", tracking=True)
    leave_date_from = fields.Date(related="leave_id.request_date_from", string="Leave Form")
    leave_date_to = fields.Date(related="leave_id.request_date_to", string="Leave To")
    effective_date = fields.Date(string="Effective Date", tracking=True)
    note = fields.Text(string="Notes")

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('effective.request.sequence') or 'New'
        return super(EffectiveRequest, self).create(vals)

    def action_submit(self):
        if not self.leave_id.have_effective:
            self.leave_id.have_effective = True
        else:
            self.leave_id = False
        self.state = 'waiting_approval'

    def action_double_approve(self):
        self.state = 'waiting_approval_2'

    def action_approve(self):
        self.employee_id.suspend_salary = False
        self.employee_id.effective_date = self.effective_date
        self.state = 'approve'

    def action_refuse(self):
        self.leave_id.have_effective = False
        self.state = 'refuse'

    def action_cancel(self):
        self.leave_id.have_effective = False
        self.state = 'cancel'

    def unlink(self):
        for effective in self:
            if effective.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete request which is not in draft or cancelled state'))
        return super(EffectiveRequest, self).unlink()


class Employee(models.AbstractModel):
    _inherit = "hr.employee"

    effective_date = fields.Date(string="Effective Date", tracking=True)
    suspend_salary = fields.Boolean(string="Suspend Salary", tracking=True)


class Leave(models.AbstractModel):
    _inherit = "hr.leave"

    need_effective = fields.Boolean(string="Need Effective", tracking=True)
    suspend_salary = fields.Boolean(string="Suspend Salary", tracking=True)
    have_effective = fields.Boolean(string="Have Salary")

    def action_approve(self):
        res = super(Leave, self).action_approve()
        if self.suspend_salary :
            self.employee_id.suspend_salary = True
        # self.employee_id.suspend_salary = True
        return res


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_available_contracts_domain(self):
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id), ('suspend_salary', '=', False)]

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
                                    default=lambda self: self._get_employees(), required=True,
                                    compute='_compute_employee_ids', store=True, readonly=False, domain="[('suspend_salary', '=', False)]")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, readonly=True,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('suspend_salary', '=', False), '|', ('active', '=', True), ('active', '=', False)]")

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        worked_days = 0
        effective_date = self.employee_id.effective_date
        first_day_of_month = (self.date_from + relativedelta(day=1)).day
        last_day_of_month = (self.date_to + relativedelta(months=+1, day=1, days=-1)).day
        if self.date_from.day == 1 and self.date_to.day == last_day_of_month:
            if effective_date:
                if self.date_to >= effective_date > self.date_from:
                    worked_days = (30 - effective_date.day) + 1
                else:
                    worked_days = 30
            else:
                worked_days = 30
        elif (self.date_from.day == first_day_of_month and self.date_to.day == first_day_of_month) or (self.date_from.day == last_day_of_month and self.date_to.day == last_day_of_month):
            worked_days = 1
        elif self.date_from.day != 1 and self.date_to.day == last_day_of_month:
            worked_days = (30 - self.date_from.day) + 1
        else:
            worked_days = (self.date_to.day - self.date_from.day) + 1
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        date_from = datetime.combine(self.date_from, datetime.min.time())
        date_to = datetime.combine(self.date_to, datetime.max.time())
        work_hours = self.contract_id._get_work_hours(date_from,date_to , domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            if work_entry_type.code == "WORK100":
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': worked_days,
                    'number_of_hours': worked_days * hours_per_day,
                }
            else:
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                }
            res.append(attendance_line)
        return res


# class HrPayslipWorkedDays(models.Model):
#     _inherit = 'hr.payslip.worked_days'

#     @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'payslip_id.wage', 'payslip_id.sum_worked_hours')
#     def _compute_amount(self):
#         for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
#             if not worked_days.contract_id or worked_days.code == 'OUT':
#                 worked_days.amount = 0
#                 continue
#             if worked_days.payslip_id.wage_type == "hourly":
#                 worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
#             else:
#                 if worked_days.code == "WORK100":
#                     worked_days.amount = (worked_days.payslip_id.wage / 30) * worked_days.number_of_days
#                 else:
#                     worked_days.amount = worked_days.payslip_id.wage * worked_days.number_of_hours / (
#                             worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
