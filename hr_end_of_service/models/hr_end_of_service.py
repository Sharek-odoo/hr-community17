# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError

# _states = {'draft': [('readonly', False)]}


def relativeDelta(enddate, startdate):
    if not startdate or not enddate:
        return relativedelta()
    startdate = fields.Datetime.from_string(startdate)
    enddate = fields.Datetime.from_string(enddate) + relativedelta(days=1)
    return relativedelta(enddate, startdate)


def delta_desc(delta):
    res = []
    if delta.years:
        res.append('%s Years' % delta.years)
    if delta.months:
        res.append('%s Months' % delta.months)
    if delta.days:
        res.append('%s Days' % delta.days)
    return ', '.join(res)


class EndOfService(models.Model):
    _name = 'hr.end_of_service'
    _description = 'End of Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default=_('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, domain=[('contract_ids', '!=', False)])
    date = fields.Date('End of Service Date', required=True)

    department_id = fields.Many2one('hr.department', related='employee_id.department_id', readonly=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', readonly=True)
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', readonly=True)
    reason_id = fields.Many2one('hr.end_of_service.reason', string='End of Service Reason', required=True, )
    termination_reason_id = fields.Many2one('hr.end_of_service.termination_reason', string='Termination Reason')
    company_id = fields.Many2one('res.company', required=True, string='Company', default=lambda self: self.env.company)
    comments = fields.Text()
    join_date = fields.Date('Join Date', compute='_calc_join_date', store=True)
    service_year = fields.Float('Total Service Years', compute='_calc_service_year', store=True)
    service_month = fields.Float('Total Service Months', compute='_calc_service_year', store=True)
    service_desc = fields.Char('Total Service', compute='_calc_service_year', store=True)
    unpaid_leave_month = fields.Float('Unpaid Leave Months', compute='_calc_service_year', store=True)
    unpaid_leave_desc = fields.Char('Unpaid Leave', compute='_calc_service_year', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', ondelete='restrict')
    remaining_leaves = fields.Float('Remaining Leaves', compute='_calc_remaining_leaves')
    leave_compensation = fields.Float('Leaves Compensation', compute='_calc_remaining_leaves')
    amount = fields.Float(compute='_calc_amount', store=True)
    reward_amount = fields.Float(compute='_calc_reward_amount', store=True, string='Reward Amount')
    state = fields.Selection([('new', 'Draft'), ('confirm', 'Confirmed'),
                              ('approve', 'Approved'), ('refuse', 'Refused'),
                              ('cancel', 'Cancelled'), ('paid', 'Paid')], default='new', tracking=True)
    salary_compensation = fields.Float(string='Salary Compensation')
    remaining_leaves_snapshot = fields.Float(
        string='Remaining Leaves (Approved)', readonly=True)
    leave_compensation_snapshot = fields.Float(
        string='Leaves Compensation (Approved)', readonly=True)
    not_transfer_used = fields.Float(
        string='Not-Transfer Balance Used', readonly=True)



    @api.constrains("employee_id", "state")
    def _check_duplication(self):
        for rec in self:
            if self.env['hr.end_of_service'].search([('id', '!=', rec.id), ('employee_id', '=', rec.employee_id.id),
                                                     ('state', 'not in', ('refuse', 'cancel'))]):
                raise ValidationError(_("You can't create more than one end of service per employee."))

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):
        for rec in self:
            # Compute current components explicitly (same logic as compute)
            year = rec.date.year
            allocs = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('date_from', '>=', f'{year}-01-01'),
                ('date_to', '<=', f'{year}-12-31'),
                ('holiday_status_id.requires_allocation', '=', 'yes'),
            ])
            total_alloc = sum(allocs.mapped('number_of_days'))

            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('date_from', '>=', f'{year}-01-01'),
                ('date_to', '<=', f'{year}-12-31'),
                ('holiday_status_id.requires_allocation', '=', 'yes'),
            ])
            total_taken = sum(leaves.mapped('number_of_days'))

            nt_records = self.env['timeoff.not.transfer'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('taken', '=', False),
            ])
            nt_balance = sum(nt_records.mapped('not_transfer_balance'))

            remaining = (total_alloc - total_taken) + nt_balance
            salary = rec.employee_id.contract_id.total_gross_salary or 0.0
            comp = (salary / 30.0) * remaining

            # Freeze (snapshot) first
            rec.write({
                'remaining_leaves_snapshot': remaining,
                'leave_compensation_snapshot': comp,
                'not_transfer_used': nt_balance,
                'state': 'approve',
            })

            # Now mark the not-transfer balances as taken
            if nt_records:
                nt_records.write({'taken': True})

            # Chatter log
            rec.message_post(body=(
                f"EOS approved. Frozen remaining leaves: {remaining:.2f} days, "
                f"leave compensation: {comp:.2f}. "
                f"Consumed not-transfer balance: {nt_balance:.2f} days."
            ))


    def action_reject(self):
        self.state = 'refuse'

    def action_draft(self):
        self.state = 'new'

    def action_cancel(self):
        self.state = 'cancel'

    @api.depends('employee_id', 'date', 'state')
    def _calc_remaining_leaves(self):
        for rec in self:
            rec.remaining_leaves = 0.0
            rec.leave_compensation = 0.0

            if not rec.employee_id or not rec.date:
                continue

            # Freeze values after approval/payment
            if rec.state in ('approve', 'paid') and rec.remaining_leaves_snapshot:
                rec.remaining_leaves = rec.remaining_leaves_snapshot
                rec.leave_compensation = rec.leave_compensation_snapshot
                continue

            year_start = f'{rec.date.year}-01-01'
            year_end = f'{rec.date.year}-12-31'

            Allocation = self.env['hr.leave.allocation']
            Leave = self.env['hr.leave']

            allocs = Allocation.search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.requires_allocation', '=', True),
                ('date_from', '<=', year_end),
                ('date_to', '>=', year_start),
            ])
            total_alloc = sum(allocs.mapped('number_of_days'))

            leaves = Leave.search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.requires_allocation', '=', True),
                ('date_from', '<=', year_end),
                ('date_to', '>=', year_start),
            ])
            total_taken = sum(leaves.mapped('number_of_days'))

            nt_balance = sum(self.env['timeoff.not.transfer'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('taken', '=', False),
            ]).mapped('not_transfer_balance'))

            remaining = (total_alloc - total_taken) + nt_balance
            rec.remaining_leaves = remaining

            contract = rec.employee_id.contract_id
            salary = contract.total_gross_salary if contract else 0.0
            rec.leave_compensation = (salary / 30.0) * remaining

    # @api.depends('employee_id')
    # def _calc_remaining_leaves(self):
        
    #     for rec in self:
    #         rec.remaining_leaves = 0
    #         rec.leave_compensation = 0

    #         if rec.employee_id:
    #             rec.remaining_leaves = rec.employee_id.remaining_leaves
    #             rec.leave_compensation = (rec.employee_id.contract_id.total_gross_salary / 30) * rec.remaining_leaves


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.company_id != self.company_id:
            self.company_id = self.employee_id.company_id

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].with_company(vals.get('company_id')).next_by_code(self._name)
        return super(EndOfService, self).create(vals_list)

    @api.depends('payslip_id.line_ids.amount')
    def _calc_amount(self):
        for record in self:
            record.amount = record.mapped('payslip_id.line_ids').filtered(lambda line: line.code == 'NET').amount

    @api.depends('reason_id', 'join_date', 'date', 'employee_id','reward_amount')
    def _calc_reward_amount(self):
        for record in self:
            contract_id = record.employee_id.contract_id
            record.reward_amount = self.reason_id.get_reward_amount(record.service_month, contract_id)

    @api.depends('employee_id.contract_ids.date_start')
    def _calc_join_date(self):
        for record in self:
            # Review
            # date_start = record.mapped('employee_id.contract_ids.date_start')
            date_start = record.mapped('employee_id.join_date')
            record.join_date = min(date_start) if date_start else False

    @api.depends('join_date', 'date', 'employee_id')
    def _calc_service_year(self):
        for record in self:
            unpaid_leave_delta = relativedelta()
            unpaid_leave_ids = self.env['hr.leave'].sudo().search([('employee_id', '=', record.employee_id.id),
                                                                   ('state', '=', 'validate'),
                                                                   ('holiday_status_id.unpaid', '=', True)])
            for leave_id in unpaid_leave_ids:
                unpaid_leave_delta += relativeDelta(leave_id.date_to, leave_id.date_from)

            delta = relativeDelta(record.date, record.join_date)
            record.service_desc = delta_desc(delta)

            if self.env['ir.config_parameter'].sudo().get_param('hr.end_of_service.unpaid_leave') == 'True':
                delta -= unpaid_leave_delta

            record.unpaid_leave_desc = delta_desc(unpaid_leave_delta)
            record.unpaid_leave_month = (unpaid_leave_delta.years * 12) + (unpaid_leave_delta.months) + (
                    unpaid_leave_delta.days / 30.0)

            service_month = (delta.years * 12) + (delta.months) + (delta.days / 30.0)
            service_year = service_month / 12.0
            record.service_year = service_year
            record.service_month = service_month

    def unlink(self):
        if any(self.filtered(lambda record: record.state != 'new')):
            raise ValidationError(_('You can delete draft status only'))
        return super(EndOfService, self).unlink()

    def _on_approve(self):
        if not self.payslip_id:
            raise ValidationError(_('No Pay Slip'))
        if not self.payslip_id.state != 'done':
            self.payslip_id.action_payslip_done()
        super(EndOfService, self)._on_approve()

    def action_payslip(self):
        if not self.payslip_id:
            date_from = fields.Date.from_string(self.date) + relativedelta(day=1)
            date_to = date_from + relativedelta(day=31)
            date_from = fields.Date.to_string(date_from)
            payslip = self.env['hr.payslip'].sudo().create({'employee_id': self.employee_id.id,
                                                            'date_from': date_from,
                                                            'date_to': date_to,
                                                            'name': 'Test',
                                                            'end_of_service_id': self.id})
            # Review
            # payslip.onchange_employee()
            payslip.compute_sheet()
            self.write({'payslip_id': payslip.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'name': 'Pay slip',
            'res_id': self.payslip_id.id,
            'view_mode': 'form',
        }
