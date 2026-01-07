# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
import babel
import time
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

from odoo import models, fields, api, tools, _
from odoo.tools.misc import format_date

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        # use partner of salary rule or fallback on employee's address
        partner_id = False
        if self.salary_rule_id.fetch_partner and credit_account != False :
            partner_id = self.employee_id.work_contact_id.id
        return partner_id

class Inherit_salary_rule(models.Model):
    _inherit = "hr.salary.rule"
    fetch_partner = fields.Boolean('Fetch Partner (Credit Journal Entry Line)',default=False)

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    loan_ids = fields.One2many('hr.loan.line', 'payslip_id', string="Loans", readonly=True)
    # def _prepare_line_values(self, line, account_id, date, debit, credit):
    #     partner = line.partner_id.id
    #     if line.salary_rule_id.fetch_partner and credit != 0 :
    #         # partner=line.slip_id.employee_id.user_partner_id.id
    #         partner=line.slip_id.employee_id.work_contact_id.id
    #     return {
    #         'name': line.name,
    #         'partner_id': partner,
    #         'account_id': account_id,
    #         'journal_id': line.slip_id.struct_id.journal_id.id,
    #         'date': date,
    #         'debit': debit,
    #         'credit': credit,
    #         'analytic_distribution': (line.salary_rule_id.analytic_account_id and {line.salary_rule_id.analytic_account_id.id: 100}) or
    #                                  (line.slip_id.contract_id.analytic_account_id.id and {line.slip_id.contract_id.analytic_account_id.id: 100})
    #     }
    def get_loan(self):
        """
        A method to get posted and approved employee's loan
        """
        for rec in self:
            rec.loan_ids.write({'payslip_id': False})
            loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', rec.employee_id.id),
                                                        ('paid', '=', False), ('date', '>=', rec.date_from),
                                                        ('date', '<=', rec.date_to),
                                                        # ('loan_id.move_id.state', '=', 'posted'),
                                                        # ('loan_id.state', '=', 'approve'),
                                                        # ('loan_id.installment_type', '=', 'base_on'),
                                                        ])
            loan_ids.write({'payslip_id': rec.id})
        return True
    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee_loans(self):
    #     for record in self:
    #         lon_obj = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
    #                                                 ('state', '=', 'approve'),
    #                                                 ('installment_type', '=', 'base_on'),
    #                                                 ])
            
    #         # for lo in lon_obj.loan_lines.filtered(lambda x:x.paid == False and 
    #         #     record.date_from <= x.date <= record.date_to) :
    #         loans = lon_obj.loan_lines.filtered(lambda x:x.paid == False and 
    #             record.date_from <= x.date <= record.date_to)
    #         total = sum([line.amount for line in loans])
    #         if  total !=0: 
    #             exit_loan = record.input_line_ids.filtered(lambda x:x.loan_line_id.id)
    #             if len(exit_loan)!=0:
    #                 exit_loan.amount = total
    #             else:
    #                 # input_lines = record.input_line_ids.browse([])
    #                 input_type_id = self.env.ref('sharek_hr_employee_loan.hr_rule_input_loan')
    #                 input_data = {
    #                     'name': input_type_id.name,
    #                     'code': input_type_id.code,
    #                     'amount': total,
    #                     'contract_id': record.contract_id.id,
    #                     'input_type_id': input_type_id.id,
    #                     'loan_line_id': loans[0].id,
    #                 }
    #                 rec.write({'input_line_ids':(0,0,input_data)})
                    # input_lines += input_lines.new(input_data)
                    # record.input_line_ids += input_lines
    def compute_sheet(self):
        """
        inherit from compute_sheet to compute loan from payslip
        """
        # self.get_loan()
        # self.onchange_employee_loans()
        # for rec in self:
        #     rec.onchange_employee()
        # for rec in self:
            
            # lon_obj = self.env['hr.loan'].search([('employee_id', '=', rec.employee_id.id),
            #                                         ('state', '=', 'approve'),
            #                                         ('installment_type', '=', 'base_on'),
            #                                         ])
            # input_line_ids = []
            # for loan in lon_obj:
            #     for loan_line in loan.loan_lines:
            #         if rec.date_from <= loan_line.date <= rec.date_to and not loan_line.paid == False and and loan_line.id not in rec.input_line_ids.loan_line_id.ids :
            #             inout_type = self.env.ref('sharek_hr_employee_loan.hr_rule_input_loan')
            #             data = {'amount': loan_line.amount, 'input_type_id': inout_type.id,
            #                                    'loan_line_id': loan_line.id, 'code': inout_type.code,
            #                                    'name': 'loan', 'contract_id': rec.contract_id}
            #             input_line_ids.append((0,0,data))
                        # input_line_ids.append({'amount': loan_line.amount, 'input_type_id': inout_type.id,
                        #                        'loan_line_id': loan_line.id, 'code': inout_type.code,
                        #                        'name': 'loan', 'contract_id': contract_ids[0]})
            # rec.write({'input_line_ids':input_line_ids})
        for record in self:
            lon_obj = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                    ('state', '=', 'approve'),
                                                    ('installment_type', '=', 'base_on'),
                                                    ])
            
            # for lo in lon_obj.loan_lines.filtered(lambda x:x.paid == False and 
            #     record.date_from <= x.date <= record.date_to) :
            loans = lon_obj.loan_lines.filtered(lambda x:x.paid == False and 
                record.date_from <= x.date <= record.date_to)
            total = sum([line.amount for line in loans])
            if  total !=0: 
                exit_loan = record.input_line_ids.filtered(lambda x:x.loan_line_id.id)
                if len(exit_loan)!=0:
                    exit_loan.amount = total
                else:
                    # input_lines = record.input_line_ids.browse([])
                    # input_type_id = self.env.ref('sharek_hr_employee_loan.hr_rule_input_loan')
                    input_data = {
                        # 'name': input_type_id.name,
                        # 'code': input_type_id.code,
                        'name': 'Loan',
                        'code': 'LO',
                        'amount': total,
                        'contract_id': record.contract_id.id,
                        # 'input_type_id': input_type_id.id,
                        'loan_line_id': loans[0].id,
                    }
                    record.write({'input_line_ids':[(0,0,input_data)]})
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_cancel(self):
        for record in self:
            lon_obj = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                    ('state', '=', 'approve'),
                                                    ('installment_type', '=', 'base_on'),
                                                    ])
            loans = lon_obj.loan_lines.filtered(lambda x:x.paid == True and 
                record.date_from <= x.date <= record.date_to)
            for line in loans:
                line.paid = False
                line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_cancel()
    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        for rec in self:
            rec.input_line_ids = False
            if (not rec.employee_id) or (not rec.date_from) or (not rec.date_to):
                return
            employee = rec.employee_id
            date_from = rec.date_from
            date_to = rec.date_to
            contract_ids = []

            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            rec.name = _('Salary Slip of %s for %s') % (
                employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
            rec.company_id = employee.company_id

            if not self.env.context.get('contract') or not rec.contract_id:
                contract_ids = rec.get_contract(employee, date_from, date_to)
                if not contract_ids:
                    return
                rec.contract_id = self.env['hr.contract'].browse(contract_ids[0])


            # if not rec.contract_id.structure_type_id.default_struct_id:
            #     return
            # rec.struct_id = rec.contract_id.structure_type_id.default_struct_id
            rec.struct_id = rec.contract_id.struct_id.id


            return

    def action_payslip_done(self):
        for record in self:
            lon_obj = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                    ('state', '=', 'approve'),
                                                    ('installment_type', '=', 'base_on'),
                                                    ])
            loans = lon_obj.loan_lines.filtered(lambda x:x.paid == False and 
                record.date_from <= x.date <= record.date_to)
            for line in loans:
                line.paid = True
                line.loan_id._compute_loan_amount()
        # for line in self.input_line_ids:
        #     if line.loan_line_id:
        #         line.loan_line_id.paid = True
        #         line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()

    @api.model
    def get_contract(self, employee, date_from, date_to):

        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids


# class HrPayslipEmployees(models.TransientModel):
#     _inherit = 'hr.payslip.employees'

#     def compute_sheet(self):
#         # self.ensure_one()
#         if not self.env.context.get('active_id'):
#             from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
#             end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
#             today = fields.date.today()
#             first_day = today + relativedelta(day=1)
#             last_day = today + relativedelta(day=31)
#             if from_date == first_day and end_date == last_day:
#                 batch_name = from_date.strftime('%B %Y')
#             else:
#                 batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
#             payslip_run = self.env['hr.payslip.run'].create({
#                 'name': batch_name,
#                 'date_start': from_date,
#                 'date_end': end_date,
#             })
#         else:
#             payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

#         employees = self.with_context(active_test=False).employee_ids
#         if not employees:
#             raise UserError(_("You must select employee(s) to generate payslip(s)."))

#         # Prevent a payslip_run from having multiple payslips for the same employee
#         employees -= payslip_run.slip_ids.employee_id
#         success_result = {
#             'type': 'ir.actions.act_window',
#             'res_model': 'hr.payslip.run',
#             'views': [[False, 'form']],
#             'res_id': payslip_run.id,
#         }
#         if not employees:
#             return success_result

#         payslips = self.env['hr.payslip']
#         Payslip = self.env['hr.payslip']

#         contracts = employees._get_contracts(
#             payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
#         ).filtered(lambda c: c.active)
#         # contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
#         # new code
#         datetime_str = payslip_run.date_start.strftime('%Y-%m-%d')
#         generate_from =datetime.strptime(datetime_str, '%Y-%m-%d').date()
#         datetime_str = payslip_run.date_end.strftime('%Y-%m-%d')
#         generate_to =datetime.strptime(datetime_str, '%Y-%m-%d').date()
#         contracts.generate_work_entries(generate_from, generate_to)
#         # ennd new code
#         work_entries = self.env['hr.work.entry'].search([
#             ('date_start', '<=', payslip_run.date_end),
#             ('date_stop', '>=', payslip_run.date_start),
#             ('employee_id', 'in', employees.ids),
#         ])
#         # self._check_undefined_slots(work_entries, payslip_run)
#         time_intervals_str = ''
#         if (self.structure_id.type_id.default_struct_id == self.structure_id):
#             work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
#             if work_entries._check_if_error():
#                 work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

#                 for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
#                     work_entries_by_contract[work_entry.contract_id] |= work_entry

#                 for contract, work_entries in work_entries_by_contract.items():
#                     conflicts = work_entries._to_intervals()
#                     time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
#                 return {
#                     'type': 'ir.actions.client',
#                     'tag': 'display_notification',
#                     'params': {
#                         'title': _('Some work entries could not be validated.'),
#                         'message': _('Time intervals to look for:%s', time_intervals_str),
#                         'sticky': False,
#                     }
#                 }

#         default_values = Payslip.default_get(Payslip.fields_get())
#         payslips_vals = []
#         for contract in contracts:
#             values = dict(default_values, **{
#                 'name': _('New Payslip'),
#                 'employee_id': contract.employee_id.id,
#                 # 'credit_note': payslip_run.credit_note,
#                 'payslip_run_id': payslip_run.id,
#                 'date_from': payslip_run.date_start,
#                 'date_to': payslip_run.date_end,
#                 'contract_id': contract.id,
#                 'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
#             })
#             payslips_vals.append(values)
#         payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
#         # payslips.onchange_employee()
#         payslips._compute_name()
#         payslips.compute_sheet()
#         payslip_run.state = 'verify'
#         return success_result
