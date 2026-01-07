# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    end_of_service_id = fields.Many2one('hr.end_of_service', string='End of Service', readonly = True, copy = False)
    end_of_service = fields.Many2one('hr.end_of_service', compute = '_calc_end_of_service', compute_sudo = True)
    
    service_year = fields.Float('Total Service Years', compute = '_calc_end_of_service', compute_sudo = True, readonly = True, store = True)
    
    @api.depends('end_of_service_id', 'employee_id', 'date_to')
    def _calc_end_of_service(self):
        for record in self:
            record.end_of_service = record.end_of_service_id or self.env['hr.end_of_service'].new({'employee_id' : record.employee_id.id, 'date' : record.date_to})
            record.service_year = record.end_of_service.service_year
    #REVIEW
    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee(self):
    #     super(HrPayslip, self).onchange_employee()
    #     if self.end_of_service_id:
    #         self.name = 'End of Service of %s' % self.employee_id.name
            
    
    def compute_sheet(self):
        self._calc_end_of_service()
        return super(HrPayslip, self).compute_sheet()            
            
    
    def unlink(self):
        if any(self.filtered('end_of_service_id')):
            raise ValidationError(_('Pay Slip link to End of Service'))
        return super(HrPayslip, self).unlink()