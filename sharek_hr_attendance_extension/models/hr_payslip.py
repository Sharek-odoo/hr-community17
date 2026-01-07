# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models,_
import calendar
from dateutil.relativedelta import relativedelta

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    # absence_days = fields.Float()

    def compute_sheet(self):
        for record in self:
            current_month_attendance = self.env['hr.attendance.sheet'].search([('state', '=', 'approve'),
                                                                               ('date_from', '>=', record.date_from),
                                                                               ('date_to', '<=', record.date_to)
                                                                               ])
            if not current_month_attendance:
                raise ValidationError(_("Attendance sheet for %s has not been approved") %(record.date_from).strftime('%B %Y'))
            if record.payslip_run_id:
                record.onchange_employee_get_inputs()
            else :
                record.onchange_employee_get_inputs()
        return super(HrPayslip, self).compute_sheet()
    # input_type_overtime = self.env.ref('sharek_hr_attendance_extension.hr_rule_input_overtime_amount') 
    # @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_get_inputs(self):
        for record in self:
            sheet_id = self.env['hr.attendance.sheet'].search([('state', '=', 'approve'),
                                                               ('date_from', '>=', record.date_from),
                                                               ('date_to', '<=', record.date_to)])
            employee_attendance = sheet_id.line_ids.filtered(lambda line: line.employee_id.id == record.employee_id.id)
            print(employee_attendance)
            input_lines = record.input_line_ids.browse([])
            if employee_attendance:
                # if employee_attendance.overtime:
                #     input_type_id = self.env.ref('sharek_hr_attendance_extension.input_overtime_hours')
                #     input_data = {
                #         'name': input_type_id.name,
                #         'code': input_type_id.code,
                #         'amount': employee_attendance.overtime*((record.contract_id.wage +
                #                 record.contract_id.transport_allowance + record.contract_id.hra +
                #                 record.contract_id.other_allowance) / 30) /
                #                 (record.contract_id.resource_calendar_id.hours_per_day),
                #         'contract_id': record.contract_id.id,
                #         'input_type_id': input_type_id.id,
                #     }
                #     input_lines += input_lines.new(input_data)
                if employee_attendance.overtime_amount :
                    input_type_id = self.env.ref('sharek_hr_attendance_extension.hr_rule_input_overtime_amount')
                    input_data = {
                        'name': input_type_id.name,
                        'code': input_type_id.code,
                        'amount':  employee_attendance.overtime_amount,
                        'contract_id': record.contract_id.id,
                        'input_type_id': input_type_id.id,
                    }
                    if  input_type_id.id  in record.input_line_ids.input_type_id.ids:
                        update = record.input_line_ids.search([('input_type_id','=',input_type_id.id)],limit=1)
                        # print('######################################',update)
                        update.amount = employee_attendance.overtime_amount
                    else:
                        input_lines += input_lines.new(input_data)
                    # check=0
                    record.input_line_ids += input_lines
                    # for line in record.input_line_ids:
                    #     if line.contract_id.id == record.contract_id.id:
                    #         line.write(input_data)
                    #         check=1  
                    # if check == 0:
                    #     record.input_line_ids += input_lines
            # for line in record.input_line_ids:
            #     input_type_id = self.env.ref('sharek_hr_attendance_extension.hr_rule_input_overtime_amount')
            #     if line.input_type_id.id == input_type_id.id and line.contract_id.id != record.contract_id.id:
            #         record.write({
            #             'input_line_ids': [3, line.id] 
            #             })
                    # record.write({
                    #     'input_line_ids': [[3, id] for id in order_line_rm]
                    #     })
                    # line.unlink()
                    # recorde.input_line_ids = [(2, line.id)]
                        # line.unlink()
                # record.input_line_ids += input_lines

    # @api.onchange('employee_id', 'date_from', 'date_to')
    # def onchange_employee_get_inputs(self):
    #     for record in self:
    #         sheet_id = self.env['hr.attendance.sheet'].search([('state', '=', 'approve'),
    #                                                            ('date_from', '>=', record.date_from),
    #                                                            ('date_to', '<=', record.date_to)])
    #         employee_attendance = sheet_id.line_ids.filtered(lambda line: line.employee_id.id == record.employee_id.id)
    #         print(employee_attendance)
    #         input_lines = self.input_line_ids.browse([])
    #         if employee_attendance:
    #             # if employee_attendance.overtime:
    #             #     input_type_id = self.env.ref('sharek_hr_attendance_extension.input_overtime_hours')
    #             #     input_data = {
    #             #         'name': input_type_id.name,
    #             #         'code': input_type_id.code,
    #             #         'amount': employee_attendance.overtime*((record.contract_id.wage +
    #             #                 record.contract_id.transport_allowance + record.contract_id.hra +
    #             #                 record.contract_id.other_allowance) / 30) /
    #             #                 (record.contract_id.resource_calendar_id.hours_per_day),
    #             #         'contract_id': record.contract_id.id,
    #             #         'input_type_id': input_type_id.id,
    #             #     }
    #             #     input_lines += input_lines.new(input_data)
    #             if employee_attendance.late_in or employee_attendance.early_exit:
    #                 input_type_id = self.env.ref('sharek_hr_attendance_extension.input_late_hours')
    #                 input_data = {
    #                     'name': input_type_id.name,
    #                     'code': input_type_id.code,
    #                     'amount':  employee_attendance.deduction_amount,
    #                     'contract_id': record.contract_id.id,
    #                     'input_type_id': input_type_id.id,
    #                 }
    #                 input_lines += input_lines.new(input_data)
    #             record.input_line_ids += input_lines


    
    def get_days_of_month(self,year,month):
        return calendar._monthlen( year,  month)
    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        worked_days = 0
        emp_sheet = self.env['hr.attendance.sheet.line'].search([('employee_id','=',self.employee_id.id),('sheet_id.date_from','>=',self.date_from),('sheet_id.date_to','<=',self.date_to),('sheet_id.state','=','approve')])
        absence_days = emp_sheet.absence_days
        overtime = emp_sheet.overtime
        late_in = emp_sheet.late_in
        early_exit = emp_sheet.early_exit
        # act_hours = emp_sheet.act_hours
        first_day_of_month = (self.date_from + relativedelta(day=1)).day
        last_day_of_month = (self.date_to + relativedelta(months=+1, day=1, days=-1)).day
        # worked_days = 30
        # # if self.date_from.day == 1 and self.date_to.day == last_day_of_month:
        # #     # if act_hours:
        # #     #     worked_days = act_hours / 8
        # #     # else:
        # #     #     worked_days = 30
        # #     if absence_days:
        # #         worked_days = 30 - absence_days
        # #     else:
        # #         worked_days = 30
        # # elif (self.date_from.day == first_day_of_month and self.date_to.day == first_day_of_month) or (self.date_from.day == last_day_of_month and self.date_to.day == last_day_of_month):
        # #     worked_days = 1
        # # elif self.date_from.day != 1 and self.date_to.day == last_day_of_month:
        # #     worked_days = (30 - self.date_from.day) + 1
        # # else:
        # #     worked_days = (self.date_to.day - self.date_from.day) + 1
        # res = []
        # hours_per_day = self._get_worked_day_lines_hours_per_day()
        # date_from = datetime.combine(self.date_from, datetime.min.time())
        # date_to = datetime.combine(self.date_to, datetime.max.time())
        # work_hours = self.contract_id._get_work_hours(date_from, date_to, domain=domain)
        # # work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
        # work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        # biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        # add_days_rounding = 0
        # for work_entry_type_id, hours in work_hours_ordered:
        #     work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
        #     days = round(hours / hours_per_day, 5) if hours_per_day else 0
        #     if work_entry_type_id == biggest_work:
        #         days += add_days_rounding
        #     day_rounded = self._round_days(work_entry_type, days)
        #     # new edit
        #     day_rounded = day_rounded - absence_days
        #     hours = hours - (absence_days*hours_per_day)
        #     # 
        #     add_days_rounding += (days - day_rounded)
        # 
        contract = self.contract_id
        out_days, out_hours = 0, 0
        reference_calendar = self._get_out_of_contract_calendar()
        if self.date_from < contract.date_start:
            start = fields.Datetime.to_datetime(self.date_from)
            stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
            out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False, domain=['|', ('work_entry_type_id', '=', False), ('work_entry_type_id.is_leave', '=', False)])
            out_days += out_time['days']
            out_hours += out_time['hours']
        if contract.date_end and contract.date_end < self.date_to:
            start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
            stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
            out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False, domain=['|', ('work_entry_type_id', '=', False), ('work_entry_type_id.is_leave', '=', False)])
            out_days += out_time['days']
            out_hours += out_time['hours']
            # 
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id.get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        print('work_hours_orderedwork_hours_orderedwork_hours_ordered',self.date_to,self.date_from,work_hours_ordered,biggest_work,work_hours)
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            # print('++++++++++++++++++++++++++++++++++++',hours,hours / hours_per_day,late_in,early_exit,absence_days)
            days_of_month = self.get_days_of_month(self.date_from.year,self.date_from.month)
            hours = hours_per_day  * days_of_month
            hours = hours - late_in - early_exit - ( absence_days * hours_per_day ) - out_hours
            # print('-----------------------------------------',hours)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            # print('////////////////////////////////////////////',day_rounded)
            add_days_rounding += (days - day_rounded)
            # print('afteeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',work_hours_ordered)
            if work_entry_type.code == "WORK100":
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                }
            # if work_entry_type.code == "WORK100":
            #     attendance_line = {
            #         'sequence': work_entry_type.sequence,
            #         'work_entry_type_id': work_entry_type_id,
            #         'number_of_days': worked_days,
            #         'number_of_hours': worked_days * hours_per_day,
            #     }   
            # else:
            #     attendance_line = {
            #         'sequence': work_entry_type.sequence,
            #         'work_entry_type_id': work_entry_type_id,
            #         'number_of_days': day_rounded,
            #         'number_of_hours': hours,
            #     }
                res.append(attendance_line)
            if absence_days:
                work_entry_type = self.env.ref('sharek_hr_attendance_extension.work_entry_type_absenace')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': absence_days,
                    'number_of_hours': absence_days * hours_per_day,
                })
            if overtime:
                work_entry_type = self.env.ref('sharek_hr_attendance_extension.work_entry_overtime_hours')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': overtime / hours_per_day,
                    'number_of_hours': overtime ,
                }) 
            if late_in:
                work_entry_type = self.env.ref('sharek_hr_attendance_extension.work_entry_late_in_hours')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': late_in / hours_per_day,
                    'number_of_hours': late_in ,
                }) 
            if early_exit:
                work_entry_type = self.env.ref('sharek_hr_attendance_extension.work_entry_early_hours')
                res.append({
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type.id,
                    'number_of_days': early_exit / hours_per_day,
                    'number_of_hours': early_exit ,
                })            
        return res
            

