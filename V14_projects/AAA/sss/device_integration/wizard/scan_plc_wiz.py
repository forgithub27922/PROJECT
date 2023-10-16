from odoo import models, fields
import csv


class ScanPLCWizard(models.TransientModel):
    _inherit = ['barcodes.barcode_events_mixin']
    _name = 'scan.plc.wizard'
    _description = 'Scan PLC Wizard'

    date = fields.Datetime('Date', default=fields.Datetime.now())
    program_name = fields.Char('Program')
    panel_barcode = fields.Char('Panel Barcode')

    def on_barcode_scanned(self, barcode):
        """
        This method is used to scan the barcode and assign it to the panel barcode
        --------------------------------------------------------------------------
        :param barcode: the barcode used for panel will be added to the field panel barcode when scanned.
        """
        for wiz in self:
            wiz.panel_barcode = barcode

    def scan_pattern(self):
        """
        This will open a new wizard with existing information.
        ------------------------------------------------------
        @param self: object pointer
        :return: Action of the next wizard
        """
        data = self.read()[0]
        view = self.env.ref('device_integration.view_scan_pattern_wiz_form')
        action = {
            'name': 'Scan Pattern Barcode',
            'type': 'ir.actions.act_window',
            'res_model': 'scan.pattern.wizard',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_date': data['date'],
                'default_program_name': data['program_name'],
                'default_panel_barcode': data['panel_barcode'],
            },
        }
        return action

    def generate(self):
        """
        This method will be used to generate the csv fields with panels without patterns
        -------------------------------------------------------------------------------
        @param self: object pointer
        """
        csv_list = [
            [
                self.panel_barcode,
                '',
                '1',
                '999',
                '-',
                'P',
                self.program_name,
                '-',
                self.date.strftime('%Y-%m-%d %H:%M:%S')
            ]
        ]
        f1 = open('/home/parth/Downloads/smt/lm/process_dir/' + fields.Datetime.now().strftime(
            '%d_%b_%Y_%H_%M_%S') + '.csv', 'w')
        csvw = csv.writer(f1)
        csvw.writerows(csv_list)


class ScanPatternWizard(models.TransientModel):
    _inherit = ['barcodes.barcode_events_mixin']
    _name = 'scan.pattern.wizard'
    _description = 'Scan Pattern Wizard'

    date = fields.Datetime('Date')
    program_name = fields.Char('Program')
    panel_barcode = fields.Char('Panel Barcode')
    pattern_barcode_ids = fields.One2many('pattern.barcode', 'wiz_id', 'Pattern Barcodes')

    def on_barcode_scanned(self, barcode):
        """
        This method is used to scan the barcode and assign it to the pattern barcodes
        ------------------------------------------------------------------------------------------------------
        :param barcode: the barcode used for patterns will be added to the field pattern barcodes when scanned.
        """
        # TODO: Check if the line is already existing raise warning
        # Add a line in the Pattern Barcode O2M field
        self.write({'pattern_barcode_ids': [(0, 0, {'barcode': barcode})]})

    def generate(self):
        """
        This method will be used to generate the csv fields with panels with patterns
        -----------------------------------------------------------------------------
        @param self: object pointer
        """
        csv_list = []
        for pt_bc in self.pattern_barcode_ids:
            csv_list.append([
                self.panel_barcode,
                pt_bc.pattern_barcode,
                '1',
                '999',
                '-',
                'P',
                self.program_name,
                '-',
                self.date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        f1 = open('/Users/anupchavda/workspace/projects/smt/lm/process_dir/' + fields.Datetime.now().strftime(
            '%d_%b_%Y_%H_%M_%S') + '.csv', 'w')
        csvw = csv.writer(f1)
        csvw.writerows(csv_list)


class PatternBarcode(models.TransientModel):
    _name = 'pattern.barcode'
    _description = 'Pattern Barcode'

    wiz_id = fields.Many2one('scan.pattern.wizard')
    pattern_barcode = fields.Char('Barcode')
