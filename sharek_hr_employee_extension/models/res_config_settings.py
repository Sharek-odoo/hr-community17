# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_id_option = fields.Selection( [('manual', 'Manual Entry'),('auto', 'Auto Generation')],
                               string='Employee ID Generation Method', config_parameter='sharek_hr_employee_extension.employee_id_option')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param_setting = self.env['ir.config_parameter'].sudo()
        param_setting.set_param('sharek_hr_employee_extension.employee_id_option', self.employee_id_option)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_setting = self.env['ir.config_parameter'].sudo()
        employee_id_option = param_setting.get_param('sharek_hr_employee_extension.employee_id_option')
        res.update(employee_id_option=employee_id_option)
        return res
