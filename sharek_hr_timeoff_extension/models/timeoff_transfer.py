from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError,UserError

class TimeoffTransfer(models.Model):
    _name = 'timeoff.transfer'
    _description = 'Time Off Transfer'

    name = fields.Char(default=lambda self: 'New', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, required=True)
    year_from = fields.Selection([(str(y), str(y)) for y in range(2000, 2101)], string="Transfer From Year", required=True)
    year_to = fields.Selection([(str(y), str(y)) for y in range(2000, 2101)], string="Transfer To Year", required=True)
    max_days = fields.Float(string="Max Transferable Days", required=True)
    allocation_date = fields.Date(string="Allocation Date")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], default='draft', tracking=True)

    not_transfer_ids = fields.One2many(
        'timeoff.not.transfer', 'time_off_transfer', string="Not Transferred Records"
    )

    employee_line_ids = fields.One2many('timeoff.transfer.line', 'transfer_id', string="Employees")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('timeoff.transfer') or 'New'
        return super().create(vals)


    @api.constrains('allocation_date', 'year_to')
    def _check_allocation_date_year(self):
        for rec in self:
            if rec.allocation_date:
                allocation_year = rec.allocation_date.year
                if allocation_year != int(rec.year_to):
                    raise ValidationError("Allocation Date year must be equal to 'Transfer Year To'.")
    


    @api.constrains('year_from', 'year_to')
    def _check_years_order(self):
        for rec in self:
            if rec.year_from and rec.year_to:
                if int(rec.year_to) < int(rec.year_from):
                    raise ValidationError("Transfer To Year must be equal or greater than Transfer From Year.")
    


    def action_compute_employees(self):
        """Fill employee_line_ids with employees from the selected company and compute transfer + not transfer balance"""
        for rec in self:
            rec.employee_line_ids.unlink()  # Clear previous lines

            if not rec.company_id or not rec.year_from:
                continue

            from_year = int(rec.year_from)
            from_date = date(from_year, 1, 1)
            to_date = date(from_year, 12, 31)

            employees = self.env['hr.employee'].search([('company_id', '=', rec.company_id.id)])

            for emp in employees:
                # Get allocations where either date_from or date_to is within the year
                allocations = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    '|',
                        '&', ('date_from', '>=', from_date), ('date_from', '<=', to_date),
                        '&', ('date_to', '>=', from_date), ('date_to', '<=', to_date),
                ])
                allocated = sum(allocations.mapped('number_of_days'))

                # Get leaves taken within the year
                leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '>=', from_date),
                    ('request_date_to', '<=', to_date),
                ])
                taken = sum(leaves.mapped('number_of_days'))

                balance = allocated - taken
                transfer_balance = min(balance, rec.max_days) if balance > 0 else 0.0
                not_transfer_balance = balance - transfer_balance if balance > 0 else 0.0

                self.env['timeoff.transfer.line'].create({
                    'transfer_id': rec.id,
                    'employee_id': emp.id,
                    'leave_allocated': allocated,
                    'leave_taken': taken,
                    'transfer_balance': transfer_balance,
                    'not_transfer_balance': not_transfer_balance,
                })

    def action_view_not_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Not Transferred Balances',
            'res_model': 'timeoff.not.transfer',
            'view_mode': 'tree,form',
            'domain': [('time_off_transfer', '=', self.id)],
            'context': {'default_time_off_transfer': self.id},
        }            


    def action_approve(self):
        """Approve the transfer: create allocations and not-transfer records"""
        LeaveAllocation = self.env['hr.leave.allocation']
        NotTransfer = self.env['timeoff.not.transfer']

        for rec in self:
            if not rec.employee_line_ids:
                raise UserError("You cannot approve a transfer without any employee lines. Please compute employees first.")

            for line in rec.employee_line_ids:
                # Transfer Balance > 0 → create allocation
                if line.transfer_balance > 0:
                    LeaveAllocation.create({
                        'name': f"Transferred Leave {rec.year_from} → {rec.year_to}",
                        'employee_id': line.employee_id.id,
                        'holiday_status_id': self.env.ref('hr_holidays.holiday_status_cl').id,  # Adjust as needed
                        'number_of_days': line.transfer_balance,
                        'allocation_type': 'regular',
                        'date_from': rec.allocation_date,
                        'date_to': rec.allocation_date,
                        'transfered': True,
                    })
                # Not Transfer Balance > 0 → log to separate model
                if line.not_transfer_balance > 0:
                    NotTransfer.create({
                        'employee_id': line.employee_id.id,
                        'not_transfer_balance': line.not_transfer_balance,
                        'time_off_transfer':rec.id,
                    })
            rec.state = 'approved'   


    def action_view_allocations(self):
        self.ensure_one()
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', 'in', self.employee_line_ids.mapped('employee_id').ids),
            ('transfered', '=', True),
            ('date_from', '=', self.allocation_date),
        ])
        return {
            'name': 'Transferred Allocations',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.allocation',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', allocations.ids)],
            'context': dict(self.env.context),
        }               



class TimeoffTransferLine(models.Model):
    _name = 'timeoff.transfer.line'
    _description = 'Time Off Transfer Line'

    transfer_id = fields.Many2one('timeoff.transfer', string="Transfer")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_no = fields.Char(string="Employee No", related='employee_id.employee_no', readonly=True)
    leave_allocated = fields.Float(string="Allocated Days", readonly=False)
    leave_taken = fields.Float(string="Taken Days", readonly=False)
    transfer_balance = fields.Float(string="Transfer Balance", readonly=False)
    not_transfer_balance = fields.Float(string="Not Transferred Days")
    