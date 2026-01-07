from odoo import models, fields


class DeputationSummary(models.TransientModel):
    _name = 'deputation.summary.wizard'
    _description = 'Deputation Summary Wizard'

    summary = fields.Text(required=True)

    def action_add(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        record.write({'end_report': self.summary,
                      'end_date': fields.Date.today()})

        