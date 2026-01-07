from odoo import models


class PayrollBatchReportXlsx(models.AbstractModel):
    _name = 'report.sharek_xlsx_payroll_report.payroll_batch_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, payslip_run):
        sheet = workbook.add_worksheet('Payroll  Bank Report')

        # Formats
        header_style = workbook.add_format({
            'bold': True, 'bg_color': '#D9D9D9', 'font_size': 12, 'align': 'center'
        })
        money_format = workbook.add_format({
            'num_format': '#,##0.00', 'font_size': 11, 'align': 'right'
        })
        text_format = workbook.add_format({
            'font_size': 12, 'align': 'center'
        })

        # Header and column widths
        headers = [
            'Emp.ID.No.', 'Employee', 'Emp. Bank Code', 'IBAN',
            'Salary Amount', 'Basic Salary', 'Housing Allowance', 'Other Earnings',
            'Deductions', 'Payment Description',
            'Employee Address 1', 'Employee Address 2', 'Employee Address 3'
        ]
        column_widths = [12, 20, 20, 25, 16, 16, 20, 17, 13, 22, 20, 20, 20]

        for col, (header, width) in enumerate(zip(headers, column_widths)):
            sheet.set_column(col, col, width)
            sheet.write(0, col, header, header_style)

        sheet.set_row(0, 25)

        row = 1
        for payslip in payslip_run.slip_ids:
            emp = payslip.employee_id

            # Extract salary rule lines
            basic = sum(line.total for line in payslip.line_ids if line.category_id.code == 'BASIC')
            hra = sum(line.total for line in payslip.line_ids if line.code == 'HRA')
            net = payslip.net_wage or 0.0

            # Allowances: sum of positive earnings except deductions
            allowances = sum(
                line.total
                for line in payslip.line_ids
                if line.total > 0 and
                line.category_id.code in ['ALW'] and
                line.code != 'HRA'
            )

            # Deductions: sum of negative lines or lines in DED category
            deduction = sum(abs(line.total) for line in payslip.line_ids
                            if line.total < 0 or line.category_id.code == 'DED')

            sheet.set_row(row, 20)

            sheet.write(row, 0, emp.identification_id or '', text_format)
            sheet.write(row, 1, emp.name or '', text_format)
            sheet.write(row, 2, emp.bank_account_id.bank_id.bic or '', text_format)
            sheet.write(row, 3, emp.bank_account_id.acc_number or '', text_format)
            sheet.write(row, 4, net, money_format)
            sheet.write(row, 5, basic, money_format)
            sheet.write(row, 6, hra, money_format)
            sheet.write(row, 7, allowances, money_format)
            sheet.write(row, 8, deduction, money_format)
            sheet.write(row, 9, 'salary', text_format)
            sheet.write(row, 10, 'Riyadh', text_format)
            sheet.write(row, 11, 'Riyadh', text_format)
            sheet.write(row, 12, 'Riyadh', text_format)
            row += 1
