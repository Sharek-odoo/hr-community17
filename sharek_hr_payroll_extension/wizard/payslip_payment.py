# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class EmpPayslipPayment(models.TransientModel):
    _name = 'emp.payslip.payment'
    _description = 'Employee Payslip Payment'

    payment_date = fields.Date(string="Payment Date", default=fields.date.today())
    emp_payslip_payment_lines = fields.One2many('emp.payslip.payment.line', 'emp_payslip_payment_id',
                                                string="Payment Line", copy=False)
    journal_id = fields.Many2one('account.journal', string="Payment Journal", domain=[('type', 'in', ['cash', 'bank'])])
    batch_id = fields.Many2one('hr.payslip.run', string='Batch')

    @api.model
    def default_get(self, fields):
        res = super(EmpPayslipPayment, self).default_get(fields)
        if self._context.get('payslip_ids') and self._context.get('active_model') == 'hr.payslip':
            payslip_lst = []
            payslip_ids = self.env['hr.payslip'].browse(self._context.get('payslip_ids'))
            for payslip in payslip_ids.filtered(lambda l: l.state == 'done'):
                due_amount = sum(
                    payslip.payment_move_ids.filtered(lambda l: l.state == 'posted').mapped('amount_total'))
                payment_lines = {'employee_id': payslip.employee_id.id,
                                 'number': payslip.number,
                                 'payslip_id': payslip.id,
                                 'payslip_due_amount': (payslip.pay_amount - due_amount),
                                 'company_id': payslip.company_id.id,
                                 'paid_amount': (payslip.pay_amount - due_amount),
                                 'currency_id': payslip.company_id.currency_id.id}
                payslip_lst.append((0, 0, payment_lines))
            res.update({'emp_payslip_payment_lines': payslip_lst})
        return res

    def do_confirm_payslip_payment(self):
        if not self.emp_payslip_payment_lines:
            raise ValidationError(_('No payment lines found.'))
        if self.batch_id:
            for line in self.emp_payslip_payment_lines.filtered(lambda l: l.payslip_id):
                if not line.journal_id:
                    raise ValidationError(_('Please configured payment journal in payment lines.'))
                if line.payslip_due_amount < 0:
                    raise ValidationError(_('Payslip due amount should be positve.'))
                if line.paid_amount <= 0:
                    raise ValidationError(_('Please enter payslip paid amount.'))
            self.generate_payment_move()
        else:
            for line in self.emp_payslip_payment_lines.filtered(lambda l: l.payslip_id):
                if not line.journal_id:
                    raise ValidationError(_('Please configured payment journal in payment lines.'))
                if line.payslip_due_amount < 0:
                    raise ValidationError(_('Payslip due amount should be positve.'))
                if line.paid_amount <= 0:
                    raise ValidationError(_('Please enter payslip paid amount.'))
                # if not line.journal_id.default_credit_account_id:
                #     raise ValidationError(_("Please Configured Payment Journal Credit Account!"))
                line.generate_payment_move()

    def generate_payment_move(self):
        self.ensure_one()
        move_lines = []
        batch_id = self.batch_id
        net_rule = batch_id.slip_ids[0].struct_id.rule_ids.filtered(lambda line: line.code == 'NET')
        if batch_id.slip_ids[0].journal_id and not net_rule[0].account_credit:
            raise ValidationError(
                _('Payslip Salary rule "%s" should be configured Credit Account.!') % net_rule)

        credit_note = batch_id.slip_ids[0].credit_note
        name = 'Pay Salary'
        payslip_name = batch_id.name
        credit_account_id = self.journal_id.default_account_id.id
        debit_account_id = net_rule[0].account_credit.id
        paid_amount = sum(self.emp_payslip_payment_lines.filtered(lambda l: l.payslip_id).mapped('paid_amount'))
        credit_vals = {
            'name': name if not credit_note else payslip_name,
            'debit': 0.0,
            'credit': abs(paid_amount),
            'account_id': credit_account_id if not credit_note else debit_account_id,
        }
        move_lines.append((0, 0, credit_vals))
        debit_vals = {
            'name': payslip_name if not credit_note else name,
            'debit': abs(paid_amount),
            'credit': 0.0,
            'account_id': debit_account_id if not credit_note else credit_account_id,
        }
        move_lines.append((0, 0, debit_vals))
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.payment_date or fields.date.today(),
            'line_ids': move_lines,
            'ref': self.batch_id.name,
        }
        move = self.env['account.move'].sudo().create(vals)
        # move.post()
        move.action_post()
        batch_id.payment_move_ids += move
        slip_ids = batch_id.slip_ids.filtered(lambda line: line.state not in ['draft', 'cancel'])
        slip_ids.state = 'paid'
        if len(slip_ids) >= len(batch_id.slip_ids):
            batch_id.state = 'paid'
        return True

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            for line in self.emp_payslip_payment_lines:
                line.journal_id = self.journal_id.id


class EmpPayslipPaymentLine(models.TransientModel):
    _name = 'emp.payslip.payment.line'
    _description = 'employee payslip payment line'

    emp_payslip_payment_id = fields.Many2one('emp.payslip.payment', string="Payslip Payment")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    paid_amount = fields.Monetary(string="Amount To Pay")
    payslip_due_amount = fields.Monetary(string="Due Amount")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    journal_id = fields.Many2one('account.journal', string="Payment Journal")
    company_id = fields.Many2one('res.company', string="Company")
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    number = fields.Char(string="Reference")

    def generate_payment_move(self):
        self.ensure_one()
        move_lines = []
        payslip_id = self.payslip_id
        net_rule = payslip_id.struct_id.rule_ids.filtered(lambda line: line.code == 'NET')
        if payslip_id.journal_id and not net_rule[0].account_credit:
            raise ValidationError(
                _('Payslip Salary rule "%s" should be configured Credit Account.!') % net_rule)

        credit_note = payslip_id.credit_note
        name = 'Pay Salary'
        payslip_name = payslip_id.name
        credit_account_id = self.journal_id.default_account_id.id
        debit_account_id = net_rule[0].account_credit.id
        credit_vals = {
            'name': name if not credit_note else payslip_name,
            'debit': 0.0,
            'credit': abs(self.paid_amount),
            'account_id': credit_account_id if not credit_note else debit_account_id,
        }
        move_lines.append((0, 0, credit_vals))
        debit_vals = {
            'name': payslip_name if not credit_note else name,
            'debit': abs(self.paid_amount),
            'credit': 0.0,
            'account_id': debit_account_id if not credit_note else credit_account_id,
        }
        move_lines.append((0, 0, debit_vals))
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.emp_payslip_payment_id.payment_date or fields.date.today(),
            'line_ids': move_lines,
            'ref': payslip_id.number,
        }
        move = self.env['account.move'].sudo().create(vals)
        # move.post()
        move._post()
        payslip_id.payment_move_ids += move
        total_payments = sum(payslip_id.payment_move_ids.mapped('amount_total'))
        if total_payments >= payslip_id.pay_amount:
            payslip_id.state = 'paid'
        return True


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('line_ids')
    def compute_pay_amount(self):
        for rec in self:
            pay_amount = sum(rec.line_ids.filtered(lambda l: l.category_id.code == 'NET').mapped('total')) or 0.00
            rec.pay_amount = pay_amount

    pay_amount = fields.Float('Payable Amount', compute='compute_pay_amount', store=True)
    payment_move_ids = fields.Many2many('account.move', string="Journal Entries", copy=False)

    def compute_sheet(self):
        for payslip in self:
            payslip.compute_pay_amount()
        return super(HrPayslip, self).compute_sheet()

    def action_view_entries(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', 'in', self.payment_move_ids.ids)]
        action['context'] = {}
        return action

    def action_register_payment(self):
        due_amount = sum(self.payment_move_ids.filtered(lambda l: l.state == 'posted').mapped('amount_total'))
        payment_lines = [{'employee_id': self.employee_id.id, 'payslip_id': self.id,
                          'number': self.number,
                          'payslip_due_amount': (self.pay_amount - due_amount),
                          'company_id': self.company_id.id,
                          'currency_id': self.company_id.currency_id.id,
                          'paid_amount': (self.pay_amount - due_amount)}]
        ctx = {'default_company_id': self.company_id.id,
               'default_emp_payslip_payment_lines': payment_lines}
        return {
            'name': 'Payslip Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'emp.payslip.payment',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': ctx
        }


class HrPayslipBatch(models.Model):
    _inherit = 'hr.payslip.run'

    payment_move_ids = fields.Many2many('account.move', string="Journal Entries", copy=False)

    def action_view_entries(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', 'in', self.payment_move_ids.ids)]
        action['context'] = {}
        return action
    def action_view_payments(self):
        self.ensure_one()
        action =self.env.ref('sharek_hr_payroll_extension.action_emp_payslip_payment').read()[0]
        action['domain'] = [('batch_id', '=', self.id)]
        action['context'] = {}
        return action
    def action_register_payment(self):
        payment_lines = []
        for slip in self.slip_ids:
            due_amount = sum(slip.payment_move_ids.filtered(lambda l: l.state == 'posted').mapped('amount_total'))
            payment_lines.append(
                {'employee_id': slip.employee_id.id, 'payslip_id': slip.id,
                 'number': slip.number,
                 'payslip_due_amount': (slip.pay_amount - due_amount),
                 'company_id': slip.company_id.id,
                 'currency_id': slip.company_id.currency_id.id,
                 'paid_amount': (slip.pay_amount - due_amount)}
            )
        ctx = {'default_company_id': self.company_id.id,
               'default_batch_id': self.id,
               'default_emp_payslip_payment_lines': payment_lines}
        return {
            'name': 'Payslip Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'emp.payslip.payment',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': ctx
        }
