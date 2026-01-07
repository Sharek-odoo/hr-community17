# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IqamaRenewalBatch(models.Model):
    """"""
    _name = 'iqama.renewal.batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = "Exit and Return"

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'),
                              ('cancel', 'Cancel')], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    name = fields.Char(string="Name")
    date = fields.Date(string="Request Date", default=fields.Date.today())
    line_ids = fields.One2many("batch.lines", "batch_id", string="Employees")

    def unlink(self):
        """
        A method to delete iqama renewal batch request.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please reset iqama renewal batch request to draft first and try again."))
        return super(IqamaRenewalBatch, self).unlink()

    def action_confirm(self):
        # batch_renewal_confirm = self.mapped('line_ids').filtered(
        #     lambda iqama: iqama.state in ['draft']).action_confirm()
        self.write({'state': 'confirm'})
        # return batch_renewal_confirm

    def action_approve(self):
        # batch_renewal_approve = self.mapped('line_ids').filtered(
        #     lambda iqama: iqama.state in ['confirm']).action_approve()
        # self.write({'state': 'done'})
        # return batch_renewal_approve

        for rec in self.line_ids:
            contract_id = self.env['hr.contract'].search(
                [('state', '=', 'open'), ('employee_id', '=', rec.employee_id.id)], limit=1)
            if contract_id:
                if not rec.company_id.iqama_renewal_account_id:
                    raise ValidationError(_("Please add iqama renewal account in settings"))
                elif not contract_id.analytic_account_id:
                    raise ValidationError(_("Please add analytic account in {} contract".format(rec.employee_id.name)))
                elif not rec.company_id.iqama_renewal_journal_id:
                    raise ValidationError(_("Please add iqama renewal Journal in settings"))
                elif not rec.employee_id.address_id:
                    raise ValidationError(
                        _("Please add partner to {} firstly and try again.".format(rec.employee_id.name)))
                elif rec.total_fees <= 0:
                    raise ValidationError(_("Total fees for employee: ({}) must be greater than zero.".format(rec.employee_id.name)))

                move_id = self.env['account.move'].sudo().create([
                    {
                        'invoice_date': fields.Date.today(),
                        'partner_id': rec.employee_id.address_id.id,
                        'date': fields.Date.today(),
                        'move_type': 'in_invoice',
                        'ref': _('Iqama Renewal Cost For: {}'.format(rec.employee_id.name)),

                        'line_ids': [
                            (0, 0, {
                                'name': _('Iqama Renewal Cost For: {}'.format(rec.employee_id.name)),
                                'partner_id': rec.employee_id.address_id.id,
                                'account_id': rec.employee_id.address_id.property_account_payable_id.id,
                                'analytic_distribution': {contract_id.analytic_account_id.id:100} if contract_id.analytic_account_id else {},
                                'price_unit': rec.total_fees,
                                'credit': rec.total_fees,
                                # 'exclude_from_invoice_tab': True,
                            }
                             ),
                            (0, 0, {
                                'name': _('Iqama Renewal Cost For: {}'.format(rec.employee_id.name)),
                                'partner_id': rec.employee_id.address_id.id,
                                'account_id': rec.company_id.exit_return_account_id.id,
                                'analytic_distribution': {contract_id.analytic_account_id.id:100}if contract_id.analytic_account_id else {},
                                'price_unit': rec.total_fees,
                                'debit': rec.total_fees,
                                'account_type': 'liability_payable',
                            }
                             ),
                        ],
                    }
                ])
                if move_id:
                    rec.employee_id.iqama_end_date = rec.new_expiration_date
                    rec.move_id = move_id.id
                    self.state = 'done'
            else:
                raise ValidationError(_("{} haven't running contract.".format(rec.employee_id.name)))

    def action_draft(self):
        # batch_renewal_draft = self.mapped('line_ids').filtered(
        #     lambda iqama: iqama.state in ['confirm', 'cancel']).action_draft()
        self.write({'state': 'draft'})
        # return batch_renewal_draft

    def action_cancel(self):
        # batch_renewal_cancel = self.mapped('line_ids').filtered(
        #     lambda iqama: iqama.state in ['confirm']).action_cancel()
        self.write({'state': 'cancel'})
        # return batch_renewal_cancel


class IqamaRenewal(models.Model):
    _name = 'iqama.renewal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    PERIOD = [
        ('3', 'Three Months'),
        ('6', 'Six Months'),
        ('12', 'One Year')
    ]

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'),
                              ('cancel', 'Cancel')], string='Status', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    employee_id = fields.Many2one("hr.employee", string="Employee")
    iqama_no = fields.Many2one('hr.employee.iqama', related="employee_id.iqama_id")
    iqama_expire_date = fields.Date(related="employee_id.iqama_end_date")
    period = fields.Selection(PERIOD, default="3", string="Renew To")
    new_expiration_date = fields.Date(string="New Expiration date")
    renewal_fees = fields.Monetary(string="Renewal Fees")
    work_permit_fees = fields.Monetary(string="Work Permit Fees")
    total_fees = fields.Monetary(string="Total Fees", compute="_get_total_fees")
    move_id = fields.Many2one("account.move", string="Vendor Bill", copy=False)
    bill_count = fields.Integer(string="Bills", default=1)

    # @api.onchange('employee_id')
    # def _get_employee_iqama_expired(self):
    #     employee_list = []
    #     employees = self.env['hr.employee'].search([('iqama_end_date', '<', fields.Date.today())])
    #     if employees:
    #         for employee in employees:
    #             employee_list.append(employee.id)
    #     return {'domain': {'employee_id': [('id', 'in', employee_list)]}}

    @api.depends('renewal_fees', 'work_permit_fees')
    def _get_total_fees(self):
        for rec in self:
            rec.total_fees = rec.renewal_fees + rec.work_permit_fees

    @api.onchange('period', 'employee_id')
    def _change_new_expiration_date(self):
        for rec in self:
            if rec.iqama_expire_date:
                if rec.period == '3':
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(months=3)
                elif rec.period == '6':
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(months=6)
                else:
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(years=1)

    def unlink(self):
        """
        A method to delete iqama renewal request.
        """
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please reset iqama renewal request to draft first and try again."))
        return super(IqamaRenewal, self).unlink()

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):

        # Create vendor bill with exit and return cost.
        contract_id = self.env['hr.contract'].search(
            [('state', '=', 'open'), ('employee_id', '=', self.employee_id.id)], limit=1)
        if contract_id:
            if not self.company_id.iqama_renewal_account_id:
                raise ValidationError(_("Please add iqama renewal account in settings"))
            elif not contract_id.analytic_account_id:
                raise ValidationError(_("Please add analytic account in employee contract"))
            elif not self.company_id.iqama_renewal_journal_id:
                raise ValidationError(_("Please add iqama renewal Journal in settings"))
            elif not self.employee_id.address_id:
                raise ValidationError(_("Please add partner to selected employee firstly and try again."))
            elif self.total_fees <= 0:
                raise ValidationError(_("Total fees must be greater than zero."))

            move_id = self.env['account.move'].sudo().create([
                {
                    'invoice_date': fields.Date.today(),
                    'partner_id': self.employee_id.address_id.id,
                    'date': fields.Date.today(),
                    'move_type': 'in_invoice',
                    'ref': _('Iqama Renewal Cost For: {}'.format(self.employee_id.name)),

                    'line_ids': [
                        (0, 0, {
                            'name': _('Iqama Renewal Cost For: {}'.format(self.employee_id.name)),
                            'partner_id': self.employee_id.address_id.id,
                            'account_id': self.employee_id.address_id.property_account_payable_id.id,
                            'analytic_distribution': {contract_id.analytic_account_id.id:100},
                            'price_unit': self.total_fees,
                            'credit': self.total_fees,
                            # 'exclude_from_invoice_tab': True,
                        }
                         ),
                        (0, 0, {
                            'name': _('Iqama Renewal Cost For: {}'.format(self.employee_id.name)),
                            'partner_id': self.employee_id.address_id.id,
                            'account_id': self.company_id.exit_return_account_id.id,
                            'analytic_distribution': {contract_id.analytic_account_id.id :100},
                            'price_unit': self.total_fees,
                            'debit': self.total_fees,
                            'account_type': 'liability_payable',
                        }
                         ),
                    ],
                }
            ])
            if move_id:
                self.employee_id.iqama_end_date = self.new_expiration_date
                self.move_id = move_id.id
                self.state = 'done'
        else:
            raise ValidationError(_("This employee haven't running contract."))

    def action_view_bill(self):
        invoice_obj = self.env.ref('account.view_move_form')
        return {'name': _("Exit and Return Bill"),
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': invoice_obj.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': self.move_id.id,
                'context': {}}

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'


class BatchLines(models.Model):
    _name = 'batch.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    PERIOD = [
        ('3', 'Three Months'),
        ('6', 'Six Months'),
        ('12', 'One Year')
    ]

    batch_id = fields.Many2one('iqama.renewal.batch', string="Batch")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'),
                              ('cancel', 'Cancel')], string='Status', related='batch_id.state', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', related="batch_id.company_id")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    employee_id = fields.Many2one("hr.employee", string="Employee")
    iqama_no = fields.Many2one('hr.employee.iqama', related="employee_id.iqama_id")
    iqama_expire_date = fields.Date(related="employee_id.iqama_end_date")
    period = fields.Selection(PERIOD, default="3", string="Renew To")
    new_expiration_date = fields.Date(string="New Expiration date")
    renewal_fees = fields.Monetary(string="Renewal Fees")
    work_permit_fees = fields.Monetary(string="Work Permit Fees")
    total_fees = fields.Monetary(string="Total Fees", compute="_get_total_fees")
    move_id = fields.Many2one("account.move", string="Vendor Bill", copy=False)
    bill_count = fields.Integer(string="Bills", default=1)

    @api.depends('renewal_fees', 'work_permit_fees')
    def _get_total_fees(self):
        for rec in self:
            rec.total_fees = rec.renewal_fees + rec.work_permit_fees

    @api.onchange('period', 'employee_id')
    def _change_new_expiration_date(self):
        for rec in self:
            if rec.iqama_expire_date:
                if rec.period == '3':
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(months=3)
                elif rec.period == '6':
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(months=6)
                else:
                    rec.new_expiration_date = rec.iqama_expire_date + relativedelta(years=1)

    # @api.onchange('employee_id','state')
    # def _get_employee_iqama_expired(self):
    #     employee_list = []
    #     employees = self.env['hr.employee'].search([('iqama_end_date', '<', fields.Date.today())])
    #     if employees:
    #         for employee in employees:
    #             employee_list.append(employee.id)
    #     return {'domain': {'employee_id': [('id', 'in', employee_list)]}}