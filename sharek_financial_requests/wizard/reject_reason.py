from odoo import models, fields, api
from odoo.exceptions import UserError

class RejectReasonWizard(models.TransientModel):
    _name = 'advance.salary.reject.wizard'
    _description = 'Reject Reason Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_rejection(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if not active_model or not active_id:
            raise UserError("Missing context for model or ID.")

        record = self.env[active_model].browse(active_id)
        if not record.exists():
            raise UserError("No record found.")

        # Make sure the model has a 'state' and 'rejection_reason' field
        if 'state' not in record and 'rejection_reason' not in record:
            raise UserError(f"The model {active_model} must have 'state' and 'rejection_reason' fields.")

        record.write({
            'state': 'rejected',
            'rejection_reason': self.reason,
        })