# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
import babel
import time
from datetime import date, datetime, time

from odoo import models, api, fields, tools, _
from odoo.exceptions import UserError
from collections import defaultdict
from odoo.tools import float_compare, float_is_zero, plaintext2html
from markupsafe import Markup

class HrLoanAcc(models.Model):
    _inherit = 'hr.loan'

    employee_account_id = fields.Many2one('account.account',  string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', 
                                          string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal",  )
    move_id = fields.Many2one("account.move", string="Receipt", required=False, )
    paid_journal_id = fields.One2many("account.move", 'loan_id', string="Journal Paid", required=False, )
    # employee_account_id = fields.Many2one('account.account', related="loan_type_id.account_id", string="Loan Account")
    # treasury_account_id = fields.Many2one('account.account', related="loan_type_id.treasury_account_id",
    #                                       string="Treasury Account")
    # journal_id = fields.Many2one('account.journal', string="Journal", related="loan_type_id.journal_id", )
    # move_id = fields.Many2one("account.move", string="Receipt", required=False, )
    # paid_journal_id = fields.One2many("account.move", 'loan_id', string="Journal Paid", required=False, )

    def button_open_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('loan_id', '=', self.id)],
        }

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('wait_financial_manager', 'Waiting Financial Manager'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    def action_hr_manager_approve(self):
        self.write({'state': 'wait_financial_manager'})

    def action_approve(self):
        """This create account move for request.
            """
        loan_approve = self.env['ir.config_parameter'].sudo().get_param('account.loan_approve')
        contract_obj = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        if not contract_obj:
            raise UserError('You must Define a contract for employee')
        if not self.loan_lines:
            raise UserError('You must compute installment before Approved')
        if loan_approve:
            self.write({'state': 'wait_financial_manager'})
        else:
            if not self.employee_account_id or not self.treasury_account_id or not self.journal_id:
                raise UserError("You must enter employee account & Treasury account and journal to approve ")
            if not self.loan_lines:
                raise UserError('You must compute Loan Request before Approved')
            timenow = date.today()
            for loan in self:
                amount = loan.loan_amount
                loan_name = loan.employee_id.name
                reference = loan.name
                journal_id = loan.journal_id.id
                partner_id=loan.employee_id.work_contact_id.id
                debit_account_id = loan.employee_account_id.id
                credit_account_id = loan.treasury_account_id.id
                debit_vals = {
                    'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'loan_id': loan.id,
                }
                credit_vals = {
                    'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'loan_id': loan.id,
                }
                vals = {
                    # 'name': 'Loan For' + ' ' + loan_name +' '+reference,
                    'narration': loan_name,
                    'ref': 'Loan For' + ' ' + loan_name+' '+reference,
                    'journal_id': journal_id,
                    'date': timenow,
                    'loan_id': self.id,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                # move.post()
                move._post()
                loan.write({'state': 'approve', 'move_id': move.id, })
        return True

    def action_double_approve(self):
        """This create account move for request in case of double approval.
            """
        if not self.employee_account_id or not self.treasury_account_id or not self.journal_id:
            raise UserError("You must enter employee account & Treasury account and journal to approve ")
        if not self.loan_lines:
            raise UserError('You must compute Loan Request before Approved')
        timenow = date.today()
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.treasury_account_id.id
            credit_account_id = loan.employee_account_id.id
            partner_id=loan.employee_id.work_contact_id.id
            if not partner_id :
                    raise UserError('Employee %s must be link with Address '%loan.employee_id.name)
                    
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': loan.id,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': loan.id,
            }
            vals = {
                # 'name': 'Loan For' + ' ' + loan_name + ' ' + reference,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            # move.post()
            move._post()
        self.write({'state': 'approve'})

        return True


# class HrLoanLineAcc(models.Model):
#     _inherit = "hr.loan.line"

#     def action_paid_amount(self, month):
#     # def action_paid_amount(self, month,line_ids):
        
#         """This create the account move line for payment of each installment.
#             """
#         timenow = date.today()
#         data = []
#         for line in self:
#             if line.loan_id.state != 'approve':
#                 raise UserError("Loan Request must be approved")
#             amount = line.amount
#             loan_name = line.employee_id.name
#             partner = line.employee_id.user_partner_id.id
#             reference = line.loan_id.name
#             journal_id = line.loan_id.journal_id.id
#             debit_account_id = line.loan_id.treasury_account_id.id
#             credit_account_id = line.loan_id.employee_account_id.id
#             # debit_account_id = line.loan_id.employee_account_id.id
#             # credit_account_id = line.loan_id.treasury_account_id.id
#             name = 'LOAN/' + ' ' + loan_name + '/' + month
#             debit_vals = {
#                 # 'name': loan_name,
#                 'name': name,
#                 'account_id': debit_account_id,
#                 'journal_id': journal_id,
#                 'date': timenow,
#                 'debit': amount > 0.0 and amount or 0.0,
#                 'credit': amount < 0.0 and -amount or 0.0,
#             }
#             credit_vals = {
#                 # 'name': loan_name,
#                 'name': name,
#                 'account_id': credit_account_id,
#                 'partner_id':partner,
#                 'journal_id': journal_id,
#                 'date': timenow,
#                 'debit': amount < 0.0 and -amount or 0.0,
#                 'credit': amount > 0.0 and amount or 0.0,
#             }
#             data.append(debit_vals)
#             data.append(credit_vals)
#             print('******************************************',data,partner)
#             return data
            # vals = {
            #     'name': name,
            #     'narration': loan_name,
            #     'ref': reference,
            #     'journal_id': journal_id,
            #     'date': timenow,
            #     'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            # }

        #     move = self.env['account.move'].create(vals)
        #     move.post()
        # return True


# class HrPayslipAcc(models.Model):
#     _inherit = 'hr.payslip'

    # def _action_create_account_move(self):
    #     precision = self.env['decimal.precision'].precision_get('Payroll')

    #     # Add payslip without run
    #     payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

    #     # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
    #     payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
    #     for run in payslip_runs:
    #         if run._are_payslips_ready():
    #             payslips_to_post |= run.slip_ids

    #     # A payslip need to have a done state and not an accounting move.
    #     payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

    #     # Check that a journal exists on all the structures
    #     if any(not payslip.struct_id for payslip in payslips_to_post):
    #         raise ValidationError(_('One of the contract for these payslips has no structure type.'))
    #     if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
    #         raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

    #     # Map all payslips by structure journal and pay slips month.
    #     # {'journal_id': {'month': [slip_ids]}}
    #     slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
    #     for slip in payslips_to_post:
    #         slip_mapped_data[slip.struct_id.journal_id.id][slip.date or fields.Date().end_of(slip.date_to, 'month')] |= slip
    #     for journal_id in slip_mapped_data: # For each journal_id.
    #         for slip_date in slip_mapped_data[journal_id]: # For each month.
    #             line_ids = []
    #             debit_sum = 0.0
    #             credit_sum = 0.0
    #             date = slip_date
    #             move_dict = {
    #                 'narration': '',
    #                 'ref': fields.Date().end_of(slip.date_to, 'month').strftime('%B %Y'),
    #                 'journal_id': journal_id,
    #                 'date': date,
    #             }

    #             for slip in slip_mapped_data[journal_id][slip_date]:
    #                 move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
    #                 move_dict['narration'] += Markup('<br/>')
    #                 slip_lines = slip._prepare_slip_lines(date, line_ids)
    #                 line_ids.extend(slip_lines)

    #             for line_id in line_ids: # Get the debit and credit sum.
    #                 debit_sum += line_id['debit']
    #                 credit_sum += line_id['credit']

    #             # The code below is called if there is an error in the balance between credit and debit sum.
    #             if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
    #                 slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
    #             elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
    #                 slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)

    #             # new code
    #             for one_slip in self:
    #                 for line in one_slip.input_line_ids:
    #                     date_from = one_slip.date_from
    #                     tym = datetime.combine(fields.Date.from_string(date_from), time.min)
    #                     locale = self.env.context.get('lang') or 'en_US'
    #                     month = tools.ustr(babel.dates.format_date(date=tym, format='MMMM-y', locale=locale))
    #                     if line.loan_line_id:
    #                         new_data_lines = line.loan_line_id.action_paid_amount(month)
    #                         line_ids.extend(new_data_lines)
    #             # Add accounting lines in the move
    #             move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
    #             move = self._create_account_move(move_dict)
    #             for slip in slip_mapped_data[journal_id][slip_date]:
    #                 slip.write({'move_id': move.id, 'date': date})
    #     return True
    # def action_payslip_done(self):
    #     for record in self:
    #         for line in record.input_line_ids:
    #             date_from = record.date_from
    #             tym = datetime.combine(fields.Date.from_string(date_from), time.min)
    #             locale = self.env.context.get('lang') or 'en_US'
    #             month = tools.ustr(babel.dates.format_date(date=tym, format='MMMM-y', locale=locale))
    #             if line.loan_line_id:
    #                 line.loan_line_id.action_paid_amount(month)
    #     return super(HrPayslipAcc, self).action_payslip_done()
