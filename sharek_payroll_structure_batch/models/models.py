
from odoo.osv import expression
from odoo import api, fields, models, _
class payroll_structure_batch(models.TransientModel):
    _inherit = 'hr.payslip.employees'


    @api.depends('department_id','structure_id')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', self.department_id.id)]
                ])
            if wizard.structure_id:
                domain = expression.AND([
                    domain,
                    [('contract_ids.struct_id', '=', wizard.structure_id.id)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)
