from odoo import _, api, fields, models
from odoo.tools import date_utils


class SaAttendance(models.Model):
    _inherit = "hr.attendance"
    
    location_id         = fields.Many2one('hr.work.location', pre_compute=True,compute="_compute_location", string="Location", tracking=True, store=True)
    resource_calendar_id= fields.Many2one('resource.calendar', string="Assigned Shift", compute="_compute_assigned_shift", store=True, tracking=True)
    department_id       = fields.Many2one(related="employee_id.department_id", readonly=True, store=True, tracking=True)
    late_minutes        = fields.Integer(readonly=False, pre_compute=True,  store=True, compute="_compute_late_minutes", tracking=True)
    late_hours          = fields.Float(string="Late Hours", store=True, compute="_compute_late_minutes", tracking=True)
    late_duration = fields.Char("Late Duration", compute="_compute_late_minutes", store=True)

    @api.depends("employee_id")
    def _compute_location(self):
        for r in self:
            r.location_id           =r.employee_id.work_location_id.id      if r.employee_id.work_location_id\
                else None
            
    @api.depends("employee_id")
    def _compute_assigned_shift(self):
        for r in self:
            r.resource_calendar_id  =r.employee_id.resource_calendar_id.id  if r.employee_id.resource_calendar_id\
                else None

    @api.model_create_multi
    def create(self, vals_list):
        result = super(SaAttendance, self).create(vals_list)
        result._compute_late_minutes()
        return result

    # @api.depends("employee_id", "check_in")
    # def _compute_late_minutes(self):
    #     for r in self:
    #         r.late_minutes = 0
    #         if not r.resource_calendar_id or not r.check_in or not r.employee_id:
    #             r.late_minutes = 0
    #             continue
    #         if not r.employee_id.tz:
    #             r.late_minutes = 0
    #             continue
    #         working_hours   = r.resource_calendar_id
    #         check_in        = date_utils._softatt_localize(r.check_in, r.employee_id.tz)
    #         current_day     = check_in.weekday()
    #         result          = working_hours._softatt_get_shift_start_and_end_bot(current_day, check_in)
    #         if not result:
    #             r.late_minutes = 0
    #             return
    #         shift_start_datetime    = result[0]
    #         time_difference         = check_in - shift_start_datetime
    #         difference_in_minutes   = time_difference.total_seconds() / 60
    #         r.late_minutes          = difference_in_minutes

    @api.depends("employee_id", "check_in")
    def _compute_late_minutes(self):
        for r in self:
            r.late_minutes = 0
            r.late_duration = "00:00"
            r.late_hours = 0.0  # ← Add this

            if not r.resource_calendar_id or not r.check_in or not r.employee_id:
                continue
            if not r.employee_id.tz:
                continue

            working_hours = r.resource_calendar_id
            check_in = date_utils._softatt_localize(r.check_in, r.employee_id.tz)
            current_day = check_in.weekday()
            result = working_hours._softatt_get_shift_start_and_end_bot(current_day, check_in)

            if not result:
                continue

            shift_start_datetime = result[0]
            time_difference = check_in - shift_start_datetime
            difference_in_minutes = time_difference.total_seconds() / 60

            if difference_in_minutes > 0:
                r.late_minutes = round(difference_in_minutes, 2)
                r.late_hours = round(difference_in_minutes / 60, 2)  # ← Late in hours
                hours = int(difference_in_minutes // 60)
                minutes = int(difference_in_minutes % 60)
                r.late_duration = f"{hours:02}:{minutes:02}"
            else:
                r.late_minutes = 0
                r.late_hours = 0.0
                r.late_duration = "00:00"