# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sharek_payroll_batch_run(models.Model):
    _inherit = 'hr.payslip.run'
    def action_cancel_done_batch(self):
        done_slips = self.mapped('slip_ids').filtered(
            lambda slip: slip.state  in ['done'])
        payslip_cancel_result = done_slips.action_payslip_cancel()
        post_moves = done_slips.mapped('move_id')
        done_slips.unlink()
        post_moves.button_draft()
        post_moves.button_cancel()
        self.write({'state': 'cancel'})
        return payslip_cancel_result