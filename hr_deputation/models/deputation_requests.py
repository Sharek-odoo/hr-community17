from odoo import models, fields, api, _,Command
from odoo.exceptions import ValidationError,UserError


class HrDeputations(models.Model):
    _name = 'hr.deputations'
    _description = 'Employee Business Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = 'id desc'

    name = fields.Char(string='Name', default='New')
    # deputations_allownce_id = fields.Many2one('hr.deputations.allownce',string="Deputation",required=True)


    deputation_type = fields.Selection([('work_deputations', 'Work Deputations'), ('training_deputations', 'Training Deputations')], 
        string='Deputation Type',default='work_deputations')
    travel_type = fields.Selection([('internal', 'Internal'),('gcc', 'Gulf Cooperation Council'), ('national', 'National')], string='Travel Type',
        default='internal')

    employee_no = fields.Char(related='employee_id.employee_no', string='Employee No')

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
                                #   states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    grade_id = fields.Many2one('grade.grade', string='Grade', related='employee_id.grade_id', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country', string='Country',)
                                #  states={'draft': [('readonly', False)]})
    destination_country = fields.Many2one('res.country', string='Destination Country',)
                                        #   states={'draft': [('readonly', False)]})
    from_city = fields.Many2one('res.city', string='From City',)
        # states={'draft': [('readonly', False)]})
    to_city = fields.Many2one('res.city', string='To City',)
        # states={'draft': [('readonly', False)]})

    request_date = fields.Date('Request Date', default=fields.Datetime.now,)
                            #    states={'draft': [('readonly', False)]})
    end_date = fields.Date('End Date',)
                        #    states={'draft': [('readonly', False)]})
    from_date = fields.Date('From Date',)
                            # states={'draft': [('readonly', False)]})
    to_date = fields.Date('To Date')
        # states={'draft': [('readonly', False)]})
    duration = fields.Integer(string='Duration', compute='_compute_duration')
    days_before = fields.Integer(string='Days Before',)
        #  states={'draft': [('readonly', False)]})
    days_after = fields.Integer(string='Days after')
        #  states={'draft': [('readonly', False)]})
    travel_by = fields.Selection([('land', 'By Land'), ('air', 'By Air')], string='Travel By',required=True)
                                #  states={'draft': [('readonly', False)]}, required=True)
    # housing_by = fields.Selection(
    #     [('company', 'By Company'), ('employee', 'Cash On Hand'), ('half_day', 'Half Day')], string='Hotel Reservation',
    #      required=True,)
        # states={'draft': [('readonly', False)]})
    # tansp_cost = fields.Selection([('company', 'By Company'), ('employee', 'Cash On Hand')],
    #                               string='Transportation', required=True,)
                                #   states={'draft': [('readonly', False)]})
    description = fields.Text(string='Description')
    end_report = fields.Text(string='Task Report')
    basic_allownce = fields.Float('Basic Allowance', compute="_compute_allownces", store=True)
    other_allownce = fields.Float('Other Allowance', compute="_compute_allownce_amount")
    total_amount = fields.Float('Total Amount', compute="_compute_allownce_amount")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),('manager', 'Direct Manager'),('sector_manager', 'Sector Manager'),('hr_manager', 'HR Manager'),
                              ('approve', 'Approved'), ('cancel', 'Canceled')],
                             string='Status', required=True, default='draft', track_visibility='onchange')
    deputation_account = fields.Many2one('account.analytic.account', string="Analytic Account")
    line_ids = fields.One2many('hr.deputations.allownce.lines', 'deputation_id',
                               string='Deputation Lines', tracking=True, track_visibility='onchange',)
                            #    states={'draft': [('readonly', False)]})
    # attachment_number = fields.Integer( string='Number of Attachments')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    payment_ids = fields.One2many('account.payment', 'deputation_id')
    payment_count = fields.Integer(string='Payment count', default=0, compute='count_payments')
    ticket_count = fields.Integer(string='Tickets count', default=0, compute='count_tickets')
    move_id = fields.Many2one('account.move', string='Deputation Receipt', copy=False)
    receipt_count = fields.Integer(string="Receipts", default=1)

    has_tickit =fields.Boolean("Book a ticket")
    has_housing =fields.Boolean("Housing")
    has_transport =fields.Boolean("Transportation")
    has_pay_advance =fields.Boolean(help="Pay the daily allowance in advance")

    @api.depends('payment_ids')
    def count_payments(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    def count_tickets(self):
        for rec in self:
            rec.ticket_count = len(self.env['hr.ticketing'].search([('deputation_id', '=', self.id)]))

    @api.onchange('duration')
    def onchange_duration(self):
        self._compute_allownce_amount()
        # self._onchange_to_city()

    # @api.onchange('deputation_type','travel_type')
    # def _onchange_to_city(self):
    # #     for rec in self:
    # #         rec.line_ids = None
    # #         lines = []
    # #         basic_allow = self.env['hr.deputations.allownce'].search([('id', '>=', 0)])
    # #         for basic in basic_allow:

    # #             if rec.to_city.country_id in basic.counter_group.country_ids:
    # #                 for allownce_type in basic.other_allownce_ids:
    # #                     amount = 0.0
    # #                     if allownce_type.amount_type == 'amount':
    # #                         amount = allownce_type.amount
    # #                     if allownce_type.amount_type == 'percentage':
    # #                         if allownce_type.percentage_type == 'basic':
    # #                             amount = (self.employee_id.contract_id.wage * allownce_type.percentage) / 100
    # #                         if allownce_type.percentage_type == 'allownce':
    # #                             amount = (self.basic_allownce * allownce_type.percentage) / 100

    # #                     line_vals = {'allownce_type': allownce_type.id,
    # #                                  'amount': amount,
    # #                                  }
    # #                     lines.append((0, 0, line_vals))
    # #         rec.line_ids = lines

    @api.onchange('deputation_type','travel_type','employee_id')
    def onchange_deputation_type(self):
            basic_allow = self.env['hr.deputations.allownce'].search([('deputation_type', '=', rec.deputation_type),('travel_type','=',rec.travel_type)],limit=1)
            # grade_ids = basic_allow..filtered(lambda m: m.grade_ids.ids in )
            print("*"*50,"basic_allow duration ------>", basic_allow)
            print("*"*50,"basic_allow duration ------>", basic_allow.grade_ids.ids)
            basic_allow = basic_allow.filtered(lambda m: rec.grade_id.id in m.grade_ids.ids )
            self.line_ids = False
            
            if basic_allow:
                self.write({'line_ids': [Command.set(basic_allow.other_allownce_ids.ids)]})
            else:
                rec.basic_allownce = 0
                rec.other_allownce = 0

            
    @api.depends('employee_id','employee_id.grade_id', 'deputation_type', 'duration', 'days_after', 'days_before')
    def _compute_allownces(self):
        for rec in self:
            # print("*"*50)
            basic_allow = self.env['hr.deputations.allownce'].search([('deputation_type', '=', rec.deputation_type),('travel_type','=',rec.travel_type)],limit=1)
            print("*"*50,"basic_allow compute ------>", basic_allow.grade_ids.ids)
            basic_allow = basic_allow.filtered(lambda m: rec.grade_id.id in m.grade_ids.ids )
            rec.line_ids = False
            
            print("*"*50,"basic_allow compute ------>", basic_allow)

            for basic in basic_allow:
                for other_line in basic_allow.other_allownce_ids:

                    rec.write({
                        'line_ids': [(0, 0, {
                            # 'name': other_line.name,
                            'deputation_id': rec.id,
                            'amount': other_line.amount,
                            'allownce_type': other_line.id
                        })]
                    })

                # if rec.to_city.country_id in basic.counter_group.country_ids:
                for line in basic.line_ids:
                    if rec.grade_id in line.grade_ids:
                        days_no = rec.duration + rec.days_before + rec.days_after
                        rec.basic_allownce = line.amount * days_no

            # rec._onchange_to_city()

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can delete record in draft state only!"))
        return super(HrDeputations, self).unlink()

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and not self.employee_id.grade_id:
            raise ValidationError(_("Please Set Grade for this employee!!"))
        

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.deputations'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for dept in self:
            dept.attachment_number = attachment.get(dept._origin.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.deputations'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.deputations', 'default_res_id': self.id}
        return res

    def attach_document(self, **kwargs):
        pass

    @api.depends('line_ids', 'basic_allownce')
    def _compute_allownce_amount(self):
        for rec in self:
            total = 0.0
            for line in rec.line_ids:
                total += line.amount
            rec.other_allownce = total

            total_amount = rec.other_allownce + rec.basic_allownce

            rec.total_amount = total_amount

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id.partner_id.country_id:
            self.write({'country_id': self.company_id.partner_id.country_id,
                        'destination_country': self.company_id.partner_id.country_id})
        if self.company_id.partner_id.city_id:
            self.write({'from_city': self.company_id.partner_id.city_id})

        acc_id = self.env['ir.config_parameter'].get_param('hr_deputation.hr_deputation_account')
        if acc_id:
            acc = self.env['account.analytic.account'].browse(int(acc_id))
            if acc.exists():
                self.deputation_account = acc
        #
        # deputation_account = self.env['ir.config_parameter'].get_param('hr_deputation.hr_deputation_account')
        # acc = int(deputation_account)
        # self.write({'deputation_account': acc})

    @api.onchange('deputation_type')
    def onchange_deputation_type(self):
        if self.deputation_type == 'external':
            self.write({'destination_country': False, 'to_city': False})
        if self.deputation_type == 'internal':
            self.onchange_company_id()

    def action_confirm(self):
        seq = self.env['ir.sequence'].next_by_code('hr.deputations')

        self.write({'state': 'confirm', 'name': seq})
    #
    # def action_approve(self):
    #
    #     if not self.employee_id.user_partner_id:
    #         raise ValidationError(_("Please add partner to selected employee firstly and try again."))
    #     elif not self.company_id.account_id:
    #         raise ValidationError(_("Please add deputation account in settings and try again."))
    #     move_id = self.env['account.move'].sudo().create([
    #         {
    #             'invoice_date': self.request_date,
    #             'partner_id': self.employee_id.user_partner_id.id,
    #             'date': self.request_date,
    #             'move_type': 'in_receipt',
    #             'ref': _('Deputation Cost For: {}').format(self.employee_id.name),
    #
    #             'line_ids': [
    #                 (0, 0, {
    #                     'name': _('Deputation Cost For: {} - Period {} - {}').format(self.employee_id.name, self.from_date, self.to_date),
    #                     'partner_id': self.employee_id.user_partner_id.id,
    #                     'account_id': self.employee_id.user_partner_id.property_account_payable_id.id,
    #                     'analytic_account_id': self.deputation_account.id,
    #                     'price_unit': self.total_amount,
    #                     'credit': self.total_amount,
    #                     'exclude_from_invoice_tab': True,
    #                 }
    #                  ),
    #                 (0, 0, {
    #                     'name': _('Deputation Cost For: {} - Period {} - {}').format(self.employee_id.name, self.from_date, self.to_date),
    #                     'partner_id': self.employee_id.user_partner_id.id,
    #                     'account_id': self.company_id.account_id.id,
    #                     'analytic_account_id': self.deputation_account.id,
    #                     'price_unit': self.total_amount,
    #                     'debit': self.total_amount,
    #                     'account_internal_type': 'payable',
    #                 }
    #                  ),
    #             ],
    #         }
    #     ])
    #     self.move_id = move_id.id
    #     self.write({'state': 'approve'})
    def action_approve(self):
        if not self.employee_id.user_partner_id:
            raise ValidationError(_("Please add partner to selected employee firstly and try again."))
        if not self.company_id.account_id:
            raise ValidationError(_("Please add deputation account in settings and try again."))

        payable_account = self.employee_id.user_partner_id.property_account_payable_id
        if not payable_account:
            raise ValidationError(_("The employee's partner does not have a payable account."))

        maturity_date = self.to_date or self.request_date
        if not maturity_date:
            raise ValidationError(_("Please set a due date (to_date or request_date) for the payable line."))

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',  # ✅ Vendor bill (not in_receipt)
            'invoice_date': self.request_date,
            'date': self.request_date,
            'partner_id': self.employee_id.user_partner_id.id,
            'ref': _('Deputation Cost For: {}').format(self.employee_id.name),
            'invoice_payment_term_id': None,  # to avoid overwriting date_maturity
            'invoice_line_ids': [
                (0, 0, {
                    'name': _('Deputation Cost For: {} - Period {} - {}').format(
                        self.employee_id.name, self.from_date, self.to_date),
                    'account_id': self.company_id.account_id.id,
                    'quantity': 1.0,
                    'price_unit': self.total_amount,
                    'analytic_distribution': {self.deputation_account.id: 100},
                })
            ],
        })

        # ensure correct due date on payable line
        for line in move.line_ids:
            if line.account_id.account_type == 'payable':
                line.date_maturity = maturity_date

        self.write({
            'move_id': move.id,
            'state': 'approve',
        })

    def action_view_receipt(self):
        move_obj = self.env.ref('account.view_move_form')
        return {'name': _("Deputation Cost Receipt"),
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': move_obj.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': self.move_id.id,
                'context': {}}

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.depends('from_date', 'to_date')
    def _compute_duration(self):
        for record in self:
            if record.from_date and record.to_date:
                record.duration = (record.to_date - record.from_date).days + 1
            else:
                record.duration = 0

    # def action_register_payment(self):
    #     action = self.env.ref('account.action_account_payments').read()[0]
    #     view_id = self.env.ref('account.view_account_payment_form').id
    #     action.update({'views': [(view_id, 'form')], })
    #     action['context'] = {
    #         'default_partner_id': self.employee_id.user_partner_id.id,
    #         'default_payment_type': 'outbound',
    #         'default_amount': self.total_amount,
    #         'default_deputation_id': self.id,
    #         'default_journal_id': 11, 'default_ref': 'Business Trip %s' % self.name
    #     }
    #     return action

    def action_create_ticket(self):

        return {
            'name': _('Book Ticket'),
            'res_model': 'hr.ticketing',
            'view_mode': 'form',
            'context': {
                'default_employee_id': self.employee_id.id,
                'default_deputation_id': self.id

            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_payment_view(self):
        pay_obj = self.env.ref('account.view_account_payment_form')
        paymemt = self.env['account.payment'].search_count([('deputation_id', '=', self.id)])
        payment_id = self.env['account.payment'].search([('deputation_id', '=', self.id)])
        if paymemt == 1:
            return {'name': _("Deputation Payment"),
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'view_id': pay_obj.id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'res_id': payment_id.id,
                    'context': {}}

    def action_ticket_view(self):
        ticket_obj = self.env.ref('hr_deputation.hr_ticketing_form')
        ticket = self.env['hr.ticketing'].search_count([('deputation_id', '=', self.id)])
        ticket_id = self.env['hr.ticketing'].search([('deputation_id', '=', self.id)])
        if ticket == 1:
            return {'name': _("Deputation Ticket"),
                    'view_mode': 'form',
                    'res_model': 'hr.ticketing',
                    'view_id': ticket_obj.id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'current',
                    'res_id': ticket_id.id,
                    'context': {}}


class AccountPayment(models.Model):
    _inherit = "account.payment"

    deputation_id = fields.Many2one('hr.deputations',
                                    string="Deputation", store=True)


class HrDeputationLines(models.Model):
    _name = 'hr.deputations.allownce.lines'

    _inherit = ['mail.thread']

    allownce_type = fields.Many2one('hr.deput.other.allownce')

    deputation_id = fields.Many2one('hr.deputations', 'Deputation')

    amount = fields.Float('Amount')

    @api.onchange('allownce_type')
    def onchange_allownce_type(self):
        if not self.allownce_type:
            return

        if self.allownce_type.amount_type == 'amount':
            self.amount = self.allownce_type.amount

        elif self.allownce_type.amount_type == 'percentage':
            if self.allownce_type.percentage_type == 'basic':
                if self.deputation_id and self.deputation_id.employee_id and self.deputation_id.employee_id.contract_id:
                    wage = self.deputation_id.employee_id.contract_id.wage or 0.0
                    self.amount = (wage * self.allownce_type.percentage) / 100

            elif self.allownce_type.percentage_type == 'allownce':
                if self.deputation_id and self.deputation_id.basic_allownce:
                    self.amount = (self.deputation_id.basic_allownce * self.allownce_type.percentage) / 100
