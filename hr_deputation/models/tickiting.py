from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class HrTickiting(models.Model):
    _name = 'hr.ticketing'
    _inherit = ['mail.thread']
    _rec_name = "name"

    name = fields.Char('Name')

    employee_id = fields.Many2one('hr.employee', string='Employee')
                                #   states={'draft': [('readonly', False)]})
    from_date = fields.Date('Start Date',)
                            # states={'draft': [('readonly', False)]})
    to_date = fields.Date('Return Date',)
                        #   states={'draft': [('readonly', False)]})
    ticket_type = fields.Selection(
        [('economy', 'Economy'), ('premium', 'Premium'), ('business', 'Business'), ('first', 'First Class')],
        string='Tiket Type')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('approve', 'Approved'), ('cancel', 'Canceled')],
                             string='Status', required=True, default='draft', track_visibility='onchange')
    cost = fields.Float('Cost')
                        # states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', related="employee_id.work_contact_id", string='Partner',)
    payment_created = fields.Boolean(string='Payment created', default=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    deputation_id = fields.Many2one('hr.deputation')

    # Add By Hamid A Mohamed
    round_trip = fields.Boolean()
    departure_city = fields.Char()
    destination = fields.Char()

    def action_confirm(self):
        seq = self.env['ir.sequence'].next_by_code('hr.ticketing')

        self.write({'state': 'confirm', 'name': seq})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can delete record in draft state only!"))
        return super(HrTickiting, self).unlink()

    def action_create_bill(self):
        if not self.partner_id:
            raise UserError(_('Please set a partner id!!'))

        vals = {'partner_id': self.partner_id.id,
                'invoice_date': datetime.today(),
                'ticket_id': self.id,
                'move_type': 'in_invoice',
                'payment_reference': self.name
                }
        invoice_line = []
        ticket_product = self.env['ir.config_parameter'].get_param('hr_deputation.hr_ticket_product')
        Ticketing_product = int(ticket_product)

        invoice_line_vals = {'name': _('Boocking Tiket'),
                             'product_id': Ticketing_product,
                             'quantity': 1.000,
                             'price_unit': self.cost}
        invoice_line.append((0, 0, invoice_line_vals))
        vals.update({'invoice_line_ids': invoice_line})
        ticket_invoice = self.env['account.move'].create(vals)
        # ticket_invoice.action_post()
        self.write({'payment_created': True})
        return {
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': ticket_invoice.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_bill_view(self):
        invoice_obj = self.env.ref('account.view_move_form')
        invoice = self.env['account.move'].search_count([('ticket_id', '=', self.id)])
        invoice_id = self.env['account.move'].search([('ticket_id', '=', self.id)])
        if invoice == 1:
            return {'name': _("Boocking Tiket Bill"),
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': invoice_obj.id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'res_id': invoice_id.id,
                    'context': {}}


class AccountPayment(models.Model):
    _inherit = "account.move"

    ticket_id = fields.Many2one('hr.ticketing',
                                string="Ticket", store=True)
