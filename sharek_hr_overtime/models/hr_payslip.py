# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, api, fields


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_overtime(self):
        for record in self:
            overtime_id = self.env['hr.overtime'].search([('employee_id', '=', record.employee_id.id),
                                                          ('contract_id', '=', record.contract_id.id),
                                                           ('date_from', '>=', record.date_from),
                                                            ('date_to', '<=', record.date_to),
                                                          ('state', '=', 'approved'), ('payslip_paid', '=', False)])
            cash_amount = sum(overtime_id.mapped('total_amount'))
            input_lines = self.input_line_ids.browse([])
            if overtime_id:
                input_type_id = self.env.ref('sharek_hr_overtime.input_overtime')
                input_data = {
                    'name': input_type_id.name,
                    'code': input_type_id.code,
                    'amount': cash_amount,
                    'contract_id': record.contract_id.id,
                    'input_type_id': input_type_id.id,
                }
                input_lines += input_lines.new(input_data)
            record.input_line_ids += input_lines


    # @api.model
    # def get_inputs(self, contracts, date_from, date_to):
    #     """
    #     function used for writing overtime record in payslip
    #     input tree.
    #
    #     """
    #     res = super(PayslipOverTime, self).get_inputs(contracts, date_to, date_from)
    #     print("*********************************")
    #     overtime_type = self.env.ref('ohrms_overtime.hr_salary_rule_overtime')
    #     contract = self.contract_id
    #     overtime_id = self.env['hr.overtime'].search([('employee_id', '=', self.employee_id.id),
    #                                                   ('contract_id', '=', self.contract_id.id),
    #                                                   ('state', '=', 'approved'), ('payslip_paid', '=', False)])
    #     cash_amount = overtime_id.mapped('total_amount')
    #     if overtime_id:
    #         self.overtime_ids = overtime_id
    #         input_type_id = self.env.ref('hr_attendance_extension.input_overtime')
    #         input_data = {
    #             'name': input_type_id.name,
    #             'code': input_type_id.code,
    #             'amount': cash_amount,
    #             'contract_id': record.contract_id.id,
    #             'input_type_id': input_type_id.id,
    #         }
    #         res.append(input_data)
    #     return res

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self:
            for ovt in recd.overtime_ids:
                recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()
