from odoo import models, fields, api
import xlsxwriter
import base64


class WarehouseDailyOperationsWizard(models.TransientModel):
    _name = 'warehouse.daily.operations.wiz'
    _description = 'Movements of the Products'

    date = fields.Date('Date', default=fields.Date.today())
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    def print_xls_report(self):
        st_time = self.date.strftime('%Y-%m-%d') + ' 00:00:00'
        en_time = self.date.strftime('%Y-%m-%d') + ' 23:59:59'
        attach_obj = self.env['ir.attachment']
        workbook = xlsxwriter.Workbook('/tmp/Product Movements.xlsx')
        worksheet = workbook.add_worksheet('Daily Operation of a Warehouse')
        warehouse = self.env['stock.warehouse'].search([('id', '=', self.warehouse_id.id)])
        row = 2
        col = 0
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({
            'bold':
                True,
            'border':
                6,
            'align':
                'center',
            'valign':
                'vcenter',
            'fg_color': '#D7E4BC',
        })
        cell_format = workbook.add_format({'bold': True, 'font_color': 'black'})
        cell_format1 = workbook.add_format({'bold': True, 'font_color': 'black'})
        cell_format2 = workbook.add_format({'bold': True, 'font_color': 'blue'})
        cell_format3 = workbook.add_format({'bold': True, 'font_color': 'green'})
        cell_format.set_bg_color('yellow')
        cell_format1.set_bg_color('gray')
        cell_format2.set_bg_color('silver')
        cell_format3.set_bg_color('silver')
        worksheet.merge_range('A1:H2', 'Daily Operation of a Warehouse', merge_format)
        worksheet.write(row, col, 'Warehouse', bold)
        worksheet.set_column(row-2, col, 12)
        worksheet.write(row+1, col, 'Date', bold)
        col += 1
        worksheet.write(row, col, warehouse.name)
        worksheet.write(row+1, col, self.date.strftime('%Y-%m-%d'))
        col -= 1
        row += 3
        location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        move_obj = self.env['stock.move']
        for location in location_ids:
            worksheet.write(row, col, 'Location', cell_format1)
            worksheet.write(row, col+1, location.name_get()[0][1],cell_format1)
            product_inc = move_obj.search([('location_dest_id', '=', location.id),
                                           ('date', '>=', st_time),
                                           ('date', '<=', en_time)])
            worksheet.write(row + 1, col, 'InComing', cell_format2)
            worksheet.write(row + 2, col + 1, 'From', cell_format)
            worksheet.write(row + 2, col + 2, 'Product', cell_format)
            worksheet.write(row + 2, col + 3, 'Quantity', cell_format)
            worksheet.write(row + 2, col + 4, 'UoM ', cell_format)
            row += 2
            if product_inc:
                for prod in product_inc:
                    row += 1
                    worksheet.write(row, col + 1, prod.location_id.name_get()[0][1])
                    worksheet.write(row, col + 2, prod.name)
                    worksheet.write(row, col + 3, prod.product_uom_qty)
                    worksheet.write(row, col + 4, prod.product_uom.name)
            else:
                row += 1
                worksheet.write(row, col + 1, "N/A")
                worksheet.write(row, col + 2, "N/A")
                worksheet.write(row, col + 3, "0")
                worksheet.write(row, col + 4, "N/A")

            product_out = move_obj.search([('location_id', '=', location.id),
                                           ('date', '>=', st_time),
                                           ('date', '<=', en_time)])
            worksheet.write(row + 1, col, 'OutGoing', cell_format3)
            worksheet.write(row + 2, col + 1, 'To', cell_format)
            worksheet.write(row + 2, col + 2, 'Product', cell_format)
            worksheet.write(row + 2, col + 3, 'Quantity', cell_format)
            worksheet.write(row + 2, col + 4, 'UoM ', cell_format)
            row += 2
            if product_out:
                for prod in product_out:
                    row += 1
                    worksheet.set_column(row, col + 1, 30)
                    worksheet.write(row, col + 1, prod.location_dest_id.name_get()[0][1])
                    worksheet.write(row, col + 2, prod.name)
                    worksheet.write(row, col + 3, prod.product_uom_qty)
                    worksheet.write(row, col + 4, prod.product_uom.name)
            else:
                row += 1
                worksheet.write(row, col + 1, "N/A")
                worksheet.set_column(row, col + 1, 30)
                worksheet.write(row, col + 2, "N/A")
                worksheet.write(row, col + 3, "0")
                worksheet.write(row, col + 4, "N/A")
            row += 3

        workbook.close()
        f1 = open('/tmp/Product Movements.xlsx', 'rb')
        xls_data = f1.read()
        buf = base64.encodestring(xls_data)
        doc_id = attach_obj.create({'name': '%s.xlsx' % ('Product Movement'),
                                    'datas': buf,
                                    'res_model': 'warehouse.daily.operations.wiz'
                                                 'wizard',
                                    'store_fname': '%s.xlsx' % ('Product Movement'),
                                    })
        return {'type': 'ir.actions.act_url',
                'url': 'web/content/%s?download=true' % (doc_id.id),
                'target': 'current',
                }
