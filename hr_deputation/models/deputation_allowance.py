from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrDeputationsAllownce(models.Model):
    _name = 'hr.deputations.allownce'
    _inherit = ['mail.thread']
    _rec_name = 'deputation_type'

    # counter_group = fields.Many2one('country.groups', string='Country Group')
    name = fields.Char(required=True)
    deputation_type = fields.Selection([('work_deputations', 'Work Deputations'), ('training_deputations', 'Training Deputations')], 
        string='Deputation Type',default='work_deputations')
    travel_type = fields.Selection([('internal', 'Internal'),('gcc', 'Gulf Cooperation Council'), ('national', 'National')], string='Travel Type',
        default='internal')
    
    days_before = fields.Integer(string='Days Before')
    days_after = fields.Integer(string='Days After')
    line_ids = fields.One2many('hr.basic.allownce.lines', 'allownce_id',
                               string='Allownce Lines', tracking=True, track_visibility='onchange')
    grade_ids = fields.Many2many('grade.grade', string='Grade', compute="compute_jobs", store=True)
    other_allownce_ids = fields.One2many('hr.deput.other.allownce', 'basic_allownce_id',
                                         string='Allownce Lines', tracking=True, track_visibility='onchange')

    @api.model
    def create(self, vals):
        deputation_type = vals.get('deputation_type')
        travel_type = vals.get('travel_type')

        # Check for existing record with same type
        existing = self.search([
            ('deputation_type', '=', deputation_type),
            ('travel_type', '=', travel_type)
        ], limit=1)

        if existing:
            raise UserError(
                _("A Deputation Allowance already exists with the same Deputation Type and Travel Type.")
            )

        return super().create(vals)

    @api.depends('deputation_type')
    def _compute_display_name(self):
        for deputation in self:
            deputation.display_name = 'Work Deputations' if deputation.deputation_type == 'work_deputations' else 'Training Deputations'

    @api.depends('line_ids')
    def compute_jobs(self):
        jobs = []
        for record in self:
            for rec in record.line_ids:
                for job in rec.grade_ids:
                    jobs.append(job.id)
            record.write({'grade_ids': jobs})

    @api.constrains('line_ids')
    def _check_exist_product_in_line(self):
        jobs = []
        for allownce in self:
            for line in allownce.line_ids:
                for l in line.grade_ids:
                    if l in jobs:
                        raise UserError(
                            _('Sorry !!The Grade %s \n is repeated in the jobs!! The job position must not be repeated!!') % l.name)
                    else:
                        jobs.append(l)


class HrDeputationsAllownce(models.Model):
    _name = 'hr.basic.allownce.lines'
    _inherit = ['mail.thread']

    allownce_id = fields.Many2one('hr.deputations.allownce', string='Allownce')
    grade_ids = fields.Many2many('grade.grade', string='Grade')
    amount = fields.Float('Amount per day')

# @api.onchange('grade_ids')
# def _check_exist_product_in_line (self):
# 	jobs=[]
# 	for allownce in self.parent.line_ids:

# 		for l in allownce.grade_ids:
# 			if l in jobs:
# 				raise UserError(_('Sorry !!The job position %s \n is repeated in the jobs!! The job position must not be repeated!!')%l.name)
# 			else:
# 				jobs.append(l)
