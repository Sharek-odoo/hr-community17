# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api, _
from datetime import datetime, date
import logging
from markupsafe import Markup
from collections import defaultdict
from odoo.tools import float_compare, float_is_zero, plaintext2html

from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'New'),
        ('verify', 'Waiting'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('close', 'Done'),
        ('paid', 'Paid'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    structure_id = fields.Many2one(
        'hr.payroll.structure',
        string='Salary Structure',
    )

    first_payslip_move_id = fields.Many2one(
        'account.move',
        string="Accounting Entry",
        compute="_compute_first_payslip_move_id",
        readonly=True
    )
    payslip_count = fields.Integer(compute='_compute_payslip_count')

    def _compute_payslip_count(self):
        for payslip_run in self:
            payslip_run.payslip_count = len(payslip_run.slip_ids)

    @api.depends('slip_ids')
    def _compute_first_payslip_move_id(self):
        for run in self:
            first_slip = run.slip_ids.filtered(lambda slip: slip.move_id)[:1]
            run.first_payslip_move_id = first_slip.move_id if first_slip else False



    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_start:
            self.name = 'Monthly payroll of ' + (self.date_start).strftime('%B %Y')

    name = fields.Char(default=lambda self: 'Monthly payroll of ' + (date.today()).strftime('%B %Y'))


    def action_validate(self):
        payslip_done_result = self.mapped('slip_ids').filtered(lambda slip: slip.state not in ['draft', 'cancel']).action_payslip_done()
        self.action_close()
        return payslip_done_result

    def action_confirm(self):
        payslip_confirm_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state in ['verify']).action_confirm()
        self.write({'state': 'confirm'})
        return payslip_confirm_result

    def action_approve(self):
        for record in self:
            self.action_validate()
            record.write({'state': 'approve'})
        # return payslip_approve_result
    def close_payslip_run(self):
        return self.write({'state': 'close'})
    def action_post(self):
        # payslip_post_result = self.mapped('slip_ids').filtered(lambda slip: slip.state in ['approve']).action_post()
        # payslip_post_result = self.mapped('slip_ids').filtered(lambda slip: slip.state in ['done']).action_post()
        payslip_post_result = self.slip_ids[0].move_id.action_post()
        self.write({'state': 'close'})
        return payslip_post_result

    def action_refuse(self):
        payslip_refuse_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state not in ['done', 'paid', 'cancel', 'refuse']).action_refuse()
        self.write({'state': 'refuse'})
        return payslip_refuse_result

    def action_cancel(self):
        payslip_cancel_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state not in ['done', 'paid', 'cancel', 'refuse']).action_payslip_cancel()
        self.write({'state': 'cancel'})
        return payslip_cancel_result

    def action_draft(self):
        payslip_draft_result = self.mapped('slip_ids').filtered(lambda slip: slip.
                                                                state not in ['done', 'paid']).action_payslip_draft()
        self.write({'state': 'draft'})
        return payslip_draft_result

    def action_paid(self):
        self.mapped('slip_ids').action_payslip_paid()
        self.write({'state': 'paid'})

class Inherit_salary_rule(models.Model):
    _inherit = "hr.salary.rule"
    
    fetch_partner = fields.Boolean('Fetch Partner (Credit Journal Entry Line)',default=False)
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=True)



class HRPayslip(models.Model):
    _inherit = 'hr.payslip'


    employee_no = fields.Char(related="employee_id.employee_no",string="Employee NO",store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed then status is set to \'Done\'.
                    \n* When user cancel payslip the status is \'Rejected\'.""")

    def action_payslip_paid(self):
        if any(slip.state != 'done' for slip in self):
            raise UserError(_('Cannot mark payslip as paid if not confirmed.'))
        # self.write({'state': 'paid'})

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirm'})

    def action_approve(self):
        for record in self:
            record.action_payslip_done()
            record.write({'state': 'approve'})

    def action_post(self):
        for record in self:
            record.move_id.action_post()
            record.write({'state': 'done'})

    def action_refuse(self):
        for record in self:
            record.write({'state': 'refuse'})

    def action_payslip_cancel(self):
        for record in self:
            if not self.env.user._is_system() and self.filtered(lambda slip: slip.state in ['done', 'paid']):
                raise UserError(_("Cannot cancel a payslip that is done."))
            record.move_id.button_cancel()
            record.write({'state': 'cancel'})
            record.mapped('payslip_run_id').action_close()


    def _get_existing_adjust_line(self, line_ids, line, account_id, debit, credit):
        existing_lines = (
            line_id for line_id in line_ids if
            # line_id['name'] ==  line['name']
            line_id['account_id'] == account_id
            and line_id['partner_id'] == False
            # and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
            # and line_id['analytic_account_id'] == (line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id)
            )
        return next(existing_lines, False)

    def _prepare_slip_lines(self, date, line_ids):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Payroll')
        new_lines = []
        for line in self.line_ids.filtered(lambda line: line.category_id):
            amount = line.total
            if line.code == 'NET': # Check if the line is the 'Net Salary'.
                for tmp_line in self.line_ids.filtered(lambda line: line.category_id):
                    if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                        if amount > 0:
                            amount -= abs(tmp_line.total)
                        elif amount < 0:
                            amount += abs(tmp_line.total)
            if float_is_zero(amount, precision_digits=precision):
                continue
            debit_account_id = line.salary_rule_id.account_debit.id
            credit_account_id = line.salary_rule_id.account_credit.id

            if debit_account_id: # If the rule has a debit account.
                debit = amount if amount > 0.0 else 0.0
                credit = -amount if amount < 0.0 else 0.0

                debit_line = self._get_existing_lines(
                    line_ids + new_lines, line, debit_account_id, debit, credit)

                if not debit_line:
                    debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
                    debit_line['tax_ids'] = [(4, tax_id) for tax_id in line.salary_rule_id.account_debit.tax_ids.ids]
                    new_lines.append(debit_line)
                else:
                    debit_line['debit'] += debit
                    debit_line['credit'] += credit
                    if not line['name'] in debit_line['name']:
                        debit_line['name'] =  line.slip_id.payslip_run_id.name

            if credit_account_id: # If the rule has a credit account.
                debit = -amount if amount < 0.0 else 0.0
                credit = amount if amount > 0.0 else 0.0
                credit_line = self._get_existing_lines(
                    line_ids + new_lines, line, credit_account_id, debit, credit)

                if not credit_line:
                    credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
                    credit_line['tax_ids'] = [(4, tax_id) for tax_id in line.salary_rule_id.account_credit.tax_ids.ids]
                    new_lines.append(credit_line)
                else:
                    credit_line['debit'] += debit
                    credit_line['credit'] += credit
                    if not line['name'] in credit_line['name']:
                        credit_line['name'] = line.slip_id.payslip_run_id.name
        return new_lines

    def _prepare_adjust_line(self, line_ids, adjust_type, debit_sum, credit_sum, date):
        acc_id = self.sudo().journal_id.default_account_id.id
        if not acc_id:
            raise UserError(_('The Expense Journal "%s" has not properly configured the default Account!') % (self.journal_id.name))
        existing_adjustment_line = (
            line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
        )
        adjust_credit = next(existing_adjustment_line, False)

        if not adjust_credit:
            adjust_credit = {
                'name': _('Adjustment Entry'),
                'partner_id': False,
                'account_id': acc_id,
                'journal_id': self.journal_id.id,
                'date': date,
                'debit': 0.0 if adjust_type == 'credit' else credit_sum - debit_sum,
                'credit': debit_sum - credit_sum if adjust_type == 'credit' else 0.0,
            }
            # new
            result = self._get_existing_adjust_line(line_ids,adjust_credit,acc_id,adjust_credit.get('debit'),adjust_credit.get('credit'))
            if result == False:
                line_ids.append(adjust_credit)
            else:    
                for line_id in line_ids :
                    if line_id['account_id'] == acc_id:

                        if line_id['credit'] == 0 and adjust_credit['credit'] == 0 :
                            line_id['debit'] = line_id['debit'] + adjust_credit['debit']

                        if line_id['debit'] == 0 and adjust_credit['debit'] == 0 : 
                            line_id['credit'] = line_id['credit'] + adjust_credit['credit']

                        if line_id['debit'] == 0 and adjust_credit['debit'] > 0 : 
                            if line_id['credit'] > adjust_credit['debit']:
                                line_id['credit'] = line_id['credit'] - adjust_credit['debit']
                            else :
                                line_id['debit'] = adjust_credit['debit'] - line_id['credit'] 
                                line_id['credit'] = 0

                        else:
                            if line_id['debit'] > adjust_credit['credit']:
                                line_id['debit'] = line_id['debit'] - adjust_credit['credit'] 
                            else :
                                line_id['debit'] = 0 
                                line_id['credit'] = adjust_credit['credit'] - line_id['debit']
                # line_ids.append(line_id)
            # line_ids.append(adjust_credit)
        else:
            adjust_credit['credit'] = debit_sum - credit_sum

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        # analytic_restrict = self.company_id.restrict_analytic_account
        # if analytic_restrict:
        #     analytic_account_id = False 
        # else:    
        #     analytic_account_id = line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id
        department = line.slip_id.employee_id.department_id
        analytic_account_id = department.analytic_account_id.id if department and department.analytic_account_id else False
        analytic_restrict = self.company_id.restrict_analytic_account
        account_type_ids =  self.company_id.account_type_ids
        if analytic_restrict:
            account = self.env['account.account'].browse(account_id)
            allowed_account_types = account_type_ids.mapped('account_type')
            if  account.account_type in allowed_account_types:
                analytic_account_id = False
           
        existing_lines = (
            line_id for line_id in line_ids if
            # line_id['name'] == line.name
            # and line_id['account_id'] == account_id
            line_id['account_id'] == account_id
            and line_id['partner_id'] == False
            and line_id['analytic_distribution'] == ({analytic_account_id:100} if analytic_account_id else False)
            # and line_id['analytic_account_id'] == (line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id)
            and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
        
        return next(existing_lines, False)

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        account=self.env['account.account'].search([('id','=',account_id)])
        analytic_restrict = self.company_id.restrict_analytic_account
        account_type_ids =  self.company_id.account_type_ids
        department = line.slip_id.employee_id.department_id
        partner = False
        analytic_account_id = department.analytic_account_id.id if department and department.analytic_account_id else False
        if analytic_restrict:
            if not account_type_ids:
                raise UserError(_("Analytic account should be restricted to special account types. \n"
                                  "Please configure account types under payroll settings"))
            
            account = self.env['account.account'].browse(account_id)
            allowed_account_types = account_type_ids.mapped('account_type')
            if account.account_type in allowed_account_types:
                analytic_account_id = False

        # if not self.company_id.batch_payroll_move_lines and line.code == "NET":
        #     partner = self.employee_id.work_contact_id
        if line.salary_rule_id.fetch_partner :
            partner= self.employee_id.work_contact_id.id  
        else:
            partner = partner
        return {
            'name': line.slip_id.payslip_run_id.name,
            'partner_id': partner,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_distribution': {analytic_account_id:100} if analytic_account_id else False ,
        }        
    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][slip.date or fields.Date().end_of(slip.date_to, 'month')] |= slip
        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': fields.Date().end_of(slip.date_to, 'month').strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }
                if slip.payslip_run_id :
                    move_dict['ref'] = slip.payslip_run_id.name
                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
                    move_dict['narration'] += Markup('<br/>')
                    slip_lines = slip._prepare_slip_lines(date, line_ids)
                    line_ids.extend(slip_lines)

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                # The code below is called if there is an error in the balance between credit and debit sum.
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)

                # Add accounting lines in the move
                move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                move = self._create_account_move(move_dict)
                for slip in slip_mapped_data[journal_id][slip_date]:
                    slip.write({'move_id': move.id, 'date': date})
        return True


class HrDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")


