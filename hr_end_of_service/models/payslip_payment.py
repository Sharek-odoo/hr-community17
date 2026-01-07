# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmpPayslipPayment(models.TransientModel):
    _inherit = 'emp.payslip.payment'

    def do_confirm_payslip_payment(self):
        res = super(EmpPayslipPayment, self).do_confirm_payslip_payment()
        
        for emp in self.emp_payslip_payment_lines:
            if emp.payslip_id.end_of_service_id :
                emp.employee_id.contract_id.write({'state': 'close'})
                emp.mapped("employee_id").write({'active': False,'contract_id': False,})
       
        return res