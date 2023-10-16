from odoo import models, fields
import os
from os import listdir
from os.path import isfile, join
import shutil
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd
from lxml import etree


class MachineType(models.Model):
    _name = 'machine.type'
    _description = 'Machine Type'

    name = fields.Char('Name')
    pr_method = fields.Selection([('process_laser_marker', 'Process Laser Marker'),
                                  ('process_solder_paste_printing', 'Process Solder Paste Printing'),
                                  ('process_solder_paste_inspection', 'Process Solder Paste Inspection'),
                                  ('process_placement', 'Process Placement'),
                                  ('process_oven', 'Process Oven'),
                                  ('process_aoi', 'Process AOI'),
                                  ('process_ctm', 'Process Coating Machine')
                                  ], 'Process Method')


class Machine(models.Model):
    _name = 'machine.machine'
    _description = 'Machines'

    name = fields.Char('Machine')
    machine_type_id = fields.Many2one('machine.type', 'Machine Type')
    process_path = fields.Char('Process Path',
                               help='This will be the path of the directory from which the files will be parsed')
    failure_path = fields.Char('Failure Path',
                               help='In case of erorr while parsing the file will be moved to this directory')
    success_path = fields.Char('Success Path',
                               help='In case of successful parsing the file will be moved to this directory')
    last_process_timestamp = fields.Datetime('Last Process Timestamp')
    process_log_ids = fields.One2many('machine.process.log', 'machine_id', 'Process Logs')
    file_type = fields.Selection([('csv', 'CSV'), ('xml', 'XML')], 'File Type')
    is_header_line = fields.Boolean('Header line Exists?', help='If the file has a header line')

    def machine_routecheck(self):
        print("Yes RouteCheck Called")


    def process_ctm(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the coating machine files
        --------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        """
        print("process_ctm method call--->>>>")
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            if fl.endswith('.txt'):
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                f_str = f1.readlines()
                f_str = [ele.replace('\n', '') for ele in f_str]
                print("f_str--->>>>>", f_str)

                try:
                    error_flag = False
                    defect_collect_dict = {}
                    for line in f_str:
                        if line.find('=') == -1:
                            defect_collect_dict = {}
                            # TODO: Process heading line
                            print("\n\nYES line--->>>>>>", line)
                            barcode = line[line.find('"') + 1: line.rfind('"')]
                            defect_collect_dict.update(
                                {'Barcode': barcode,
                                 'StationName': 'Coating Machine',
                                 'SubUnits': [
                                     {
                                         'Barcode': barcode,
                                         'ReferenceNo': "0",
                                         'Side': "",
                                         'Defects': []
                                     }
                                 ]
                                 }
                            )

                        else:
                            # TODO : Prepare a dictionary for the heading line
                            if line.find('Serial No') == 0:
                                start = line.find('=')
                                user_name = line[start + 1:].strip()

                                defect_collect_dict.update({'UserName': user_name})

                                defect_collect_dict['SubUnits'][0]['Defects'].append({
                                    'AttributeName': "Coating Machine",
                                    'FailCode': "121",
                                    'FailReason': "Failure Reason",
                                })
                                print("\n\ndefect_collect_dict--->>>>>", defect_collect_dict)
                                print("\n\nstr(f_str.index(line))", str(f_str.index(line)))
                                print("\n\nstr(line[0])", str(line[0]))

                                # TODO: send dictionary data to defect collection api
                                response = requests.post("http://192.168.1.114:7201/api/PT/DefectCollection",
                                                         json=defect_collect_dict)
                                res = response.json()
                                if res.get('Result', {}) and res['Result']['ErrorCode'] != '0':
                                    error_flag = True
                                    # Add Process Log
                                    log_desc += "\n" + str(f_str.index(line)) + ", " + str(line[0]) + ", " + \
                                                res['Result']['ErrorCode'] + res['Result']['ErrorText']

                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))

                else:
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

    def process_laser_marker(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the laser marker machine files
        -------------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            # Open file
            f1 = open(join(process_dir, fl), 'r')
            if fl.endswith('.xml'):

                # TODO: Process XML File
                pass
            elif fl.endswith('.csv'):
                # Process CSV File
                if self.is_header_line:
                    # Fetch Headers
                    header_line = f1.readline()
                    headers = header_line.split(',')
                # Fetch lines
                lines = f1.readlines()
                lines_lst = [line.split(',') for line in lines]
                error_flag = False
                # Process Lines
                try:
                    for line in lines_lst:
                        # Process lines
                        create_unit_vals = {
                            'Program': line[6],
                            'AllowScrapPattern': "false",
                            'Units': [{
                                'Barcode': line[1],
                                'Side': "",
                                'Quality': line[5] == "P" and "Pass" or "Fail",
                            }],
                            "Batch": None,
                            "WorkOrder": None
                        }
                        # response = requests.post("http://192.168.1.114:7201/api/WIPProxy/CreateUnit",
                        #                          json=create_unit_vals)
                        # res = response.json()
                        # if res.get('error_code', False) and res['error_code'] != '0':
                        #     error_flag = True
                        #     # Add Process Log
                        #     # TODO Add the actual Error Log
                        #     log_desc += "\n" + str(lines_lst.index(line)) + ", " + str(line[0]) + ", " + res[
                        #         'error_code']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    # Add the Process log and move the file to success dir
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                f1.close()

    def process_solder_paste_printing(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the solder paste printing files
        ---------------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            if fl.endswith('.xml'):
                # TODO: Process XML File
                pass
            elif fl.endswith('.csv'):
                # Process CSV File
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                if self.is_header_line:
                    # Fetch Headers
                    header_line = f1.readline()
                    headers = header_line.split(',')
                # Fetch lines
                lines = f1.readlines()
                lines_lst = [line.split(',') for line in lines]
                error_flag = False
                # Process Lines
                try:
                    for line in lines_lst:
                        st_dt = datetime.strptime(line[headers.index('DateTime')], "%d/%m/%Y %H:%M:%S")
                        en_dt = st_dt + rd(hours=2)

                        data_collection_vals = {
                            'Barcode': line[headers.index('Product ID')],
                            'StationName': "SOLDERPASTEPRINTING",
                            "UserName": line[headers.index('Operator ID')],
                            "StartDateTime": st_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "EndDateTime": en_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "SubUnits": [{
                                "Barcode": "",
                                "ReferenceNumber": "0",
                                "Side": "",
                                "KeyValues": [{
                                    "GroupKey": "Print",
                                    "Value": [
                                        {
                                            "Value": [
                                                {
                                                    "Key": "PrintPass",
                                                    "Value": line[headers.index('PrintPass')]
                                                },
                                                {
                                                    "Key": "PrintPassDescription",
                                                    "Value": line[headers.index('PrintPassDescription')]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                    {
                                        "GroupKey": "Specs",
                                        "Value": [
                                            {
                                                "Value": [
                                                    {
                                                        "Key": "Squeegee",
                                                        "Value": line[headers.index('Squeegee')],
                                                    },
                                                    {
                                                        "Key": "Front Pressure (Kg)",
                                                        "Value": line[headers.index('Front Pressure (Kg)')],
                                                    },
                                                    {
                                                        "Key": "Rear Pressure (Kg)",
                                                        "Value": line[headers.index('Rear Pressure (Kg)')],
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }],
                        }
                        response = requests.post("http://192.168.1.114:7201/api/PT/DataCollection",
                                                 json=data_collection_vals)
                        res = response.json()
                        if res.get('error_code', False) and res['error_code'] != '0':
                            error_flag = True
                            # Add Process Log
                            # TODO Add the actual Error Log
                            log_desc += "\n" + str(lines_lst.index(line)) + ", " + str(line[0]) + ", " + res[
                                'error_code']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    # Add the Process log and move the file to success dir
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                f1.close()

    def process_solder_paste_inspection(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the solder paste inspection files
        -----------------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            error_flag = False
            if fl.endswith('.xml') or fl.endswith('.XML'):
                # TODO: Process XML File
                f1 = open(join(process_dir, fl), 'r')
                xml_data = f1.read()
                dom = etree.fromstring(xml_data.encode())
                insp_dt = ''
                panel_barcode = ''

                def parse_xml(dm):
                    dc_vals = {}
                    global insp_dt
                    if dm.getparent() and dm.getparent().tag == 'Board':
                        if dm.tag == 'MasterBarcode':
                            global panel_barcode
                            panel_barcode = dm.text,
                            dc_vals.update({
                                'Barcode': panel_barcode[0],
                                'StationName': 'SOLDERPASTEINSPECTION',
                            })
                        elif dm.tag == 'InspectionDate':
                            insp_dt = dm.text
                        elif dm.tag == 'InspectionStartTime':
                            dc_vals.update({
                                'StartDateTime': insp_dt + " " + dm.text
                            })
                        elif dm.tag == 'InspectionEndTime':
                            dc_vals.update({
                                'EndDateTime': insp_dt + " " + dm.text
                            })

                        elif dm.tag == 'PCBResult':
                            if dm.text == 'GOOD':
                                dc_vals.update({
                                    'SubUnits': [
                                        {
                                            'ReferenceNumber': 0,
                                            'Barcode': '',
                                            'Side': 'Top',
                                            'Defects': []
                                        }
                                    ]
                                })
                            else:
                                pass
                    dm = dm.getchildren()
                    if dm:
                        if isinstance(dm, list):
                            for child_dm in dm:
                                dc_vals.update(parse_xml(child_dm))
                        else:
                            dc_vals.update(parse_xml(dm))
                    return dc_vals

                try:
                    defect_collection_vals = parse_xml(dom)
                    response = requests.post("http://192.168.1.114:7201/api/PT/DefectCollection",
                                             json=defect_collection_vals)
                    res = response.json()
                    if res.get('error_code', False) and res['error_code'] != '0':
                        error_flag = True
                        # Add Process Log
                        # TODO Add the actual Error Log
                        log_desc += "\n" + str(lines_lst.index(line)) + ", " + str(line[0]) + ", " + res['error_code']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    # Add the Process log and move the file to success dir
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
            elif fl.endswith('.csv'):
                # Process CSV File
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                if self.is_header_line:
                    # Fetch Headers
                    header_line = f1.readline()
                    headers = header_line.split(',')
                # Fetch lines
                lines = f1.readlines()
                lines_lst = [line.split(',') for line in lines]
                try:
                    # TODO : Process Lines
                    for line in lines_lst:
                        pass
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    shutil.move(join(process_dir, fl), failure_dir)
                else:
                    # Add the Process log and move the file to success dir
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

    def process_placement(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the placement files
        ---------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            if fl.endswith('.xml'):
                # TODO: Process XML File
                pass
            elif fl.endswith('.csv'):
                # Process CSV File
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                if self.is_header_line:
                    # Fetch Headers
                    header_line = f1.readline()
                    headers = header_line.split(',')
                # Fetch lines
                lines = f1.readlines()
                lines_lst = [line.split(',') for line in lines]
                error_flag = False
                try:
                    # TODO : Process Lines
                    for line in lines_lst:
                        dispatch_unit_vals = {
                            'Barcode': line[1],
                            'StationName': "PLACEMENT",
                            'OperatorName': "Anup",
                            "UserInput": "",
                        }
                        response = requests.post("http://192.168.1.114:7201/api/PT/DispatchUnit",
                                                 json=dispatch_unit_vals)
                        res = response.json()
                        if res.get('Error', {}) and res['Error']['ErrorCode'] != 0:
                            error_flag = True
                            # Add Process Log
                            # TODO Add the actual Error Log
                            log_desc += "\n" + str(lines_lst.index(line)) + ", " + str(line[0]) + ", " + res['Error'][
                                'ErrorCode']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    # Add the Process log and move the file to success dir
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

    def process_oven(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the solder paste oven files
        -----------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            if fl.endswith('.xml'):
                # TODO: Process XML File
                pass
            elif fl.endswith('.csv'):
                # TODO: Process CSV File
                pass
            elif fl.endswith('.txt'):
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                lines_lst = f1.readlines()
                line_list = [line.split('=') for line in lines_lst]
                result = dict([(line[0], line[1]) for line in line_list if len(line) == 2])
                # Process Lines
                try:
                    error_flag = False
                    # Process File
                    dt = result['Date'].replace('\n', '')
                    st_tm = result['Time board entered oven'].replace('\n', '')
                    en_tm = result['Time board exited oven'].replace('\n', '')

                    st_dt = dt + " " + st_tm
                    en_dt = dt + " " + en_tm
                    st_dtm = datetime.strptime(st_dt, "%d-%m-%Y %H:%M:%S")
                    en_dtm = datetime.strptime(en_dt, "%d-%m-%Y %H:%M:%S")

                    data_collection_vals = {
                        'Barcode': result['Board_Barcode'].replace('\n', ''),
                        "StationName": "REFLOWOVEN",
                        "StartDateTime": st_dtm.strftime("%Y-%m-%d %H:%M:%S"),
                        "EndDateTime": en_dtm.strftime("%Y-%m-%d %H:%M:%S"),
                        "SubUnits": [
                            {
                                'Barcode': "",
                                'ReferenceNumber': 0,
                                'Side': "",
                                'KeyValues': [
                                    {
                                        'Key': "Max Rising Slope Low",
                                        'Value': result['Max_Rising_Slope_LOW']
                                    },
                                    {
                                        'Key': "Max Rising Slope Target",
                                        'Value': result['Max_Rising_Slope_TARGET']
                                    }
                                ]
                            }
                        ]
                    }

                    response = requests.post("http://192.168.1.114:7201/api/PT/DataCollection",
                                             json=data_collection_vals)
                    res = response.json()
                    if res.get('Result', {}) and res['Result']['ErrorCode'] != '0':
                        error_flag = True
                        # Add Process Log
                        log_desc += "\n" + res['Result']['ErrorCode'] + res['Result']['ErrorText']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

    def process_aoi(self, files, process_dir, success_dir, failure_dir):
        """
        This method will process the oven inspection files
        ---------------------------------------------------
        @param self: object pointer
        @param files: The files in the process directory to process
        @param process_dir: The path of the process directory
        @param success_dir: The path of the success directory
        @param failure_dir: The path of the failure directory
        :return:
        """
        process_log_obj = self.env['machine.process.log']
        for fl in files:
            log_vals = {
                'date': fields.Datetime.now(),
                'file_name': fl,
                'machine_id': self.id,
            }
            log_desc = ''
            error_flag = False
            if fl.endswith('.xml'):
                # TODO: Process XML File
                # TODO: Process Log
                pass
            elif fl.endswith('.csv'):
                # Process CSV File
                # Open file
                f1 = open(join(process_dir, fl), 'r')
                i = 9

                defect_collection_vals = {}
                user_name = ''
                while (i > 0):
                    line_1 = f1.readline()
                    line_lst = line_1.split(',')
                    if line_lst[0] == 'Operator name':
                        user_name = line_lst[1]
                    i -= 1
                headers = f1.readline()
                header_list = headers.split(',')
                lines = f1.readlines()
                lines_list = [line.split(',') for line in lines]
                # Process Lines
                try:
                    error_flag = False
                    # TODO : Process Lines
                    for line in lines_list:
                        defect_collection_vals = {
                            'Barcode': line[header_list.index('Block No.')],
                            'StationName': 'AOI',
                            'UserName': user_name,
                            'SubUnits': [
                                {
                                    'Barcode': line[header_list.index('Block No.')],
                                    'ReferenceNo': "0",
                                    'Side': "",
                                    'Defects': []
                                }
                            ]
                        }

                        if line[headers.index('Judgment result')] == 'NG':
                            exp_value = line[header_list.index('NG Upper Limit')] + '-' + line[
                                header_list.index('NG Lower Limit')]
                            defect_collection_vals['SubUnits'][0]['Defects'].append({
                                'AttributeName': "Area",
                                "FailCode": "121",
                                "FailReason": "The Area is not between the limits!",
                                "ExpectedValue": exp_value,
                                "ActualValue": line[header_list.index('Volume')],
                                'PartNumber': line[header_list.index('Pad No.')]

                            })
                        response = requests.post("http://192.168.1.114:7201/api/PT/DefectCollection",
                                                 json=defect_collection_vals)
                        res = response.json()
                        if res.get('Result', {}) and res['Result']['ErrorCode'] != '0':
                            error_flag = True
                            # Add Process Log
                            log_desc += "\n" + str(lines_list.index(line)) + ", " + str(line[0]) + ", " + res['Result'][
                                'ErrorCode'] + res['Result']['ErrorText']
                except Exception as e:
                    # Add the Process log and stop further execution
                    log_vals.update({
                        'error_code': '99',
                        'state': 'fail',
                        'description': str(e),
                    })
                    process_log_obj.create(log_vals)
                    # shutil.move(join(process_dir, fl), failure_dir)
                    shutil.copy(join(process_dir, fl), failure_dir)
                    f1.close()
                    os.remove(join(process_dir, fl))
                else:
                    if error_flag:
                        # Add the Process log and move the file to failure dir
                        log_vals.update({
                            'error_code': '98',
                            'state': 'fail',
                            'description': log_desc,
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), failure_dir)
                        shutil.copy(join(process_dir, fl), failure_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))
                    else:
                        # Add the Process log and move the file to success dir
                        log_vals.update({
                            'error_code': '0',
                            'state': 'pass',
                            'description': 'The file processed Successfully',
                        })
                        process_log_obj.create(log_vals)
                        # shutil.move(join(process_dir, fl), success_dir)
                        shutil.copy(join(process_dir, fl), success_dir)
                        f1.close()
                        os.remove(join(process_dir, fl))

    def process_files(self):
        """
        This method will be used to process the files available in the process path directory
        -------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for machine in self:
            # Open the directory
            process_dir = machine.process_path
            failure_dir = machine.failure_path
            success_dir = machine.success_path
            files = [f for f in listdir(process_dir) if isfile(join(process_dir, f))]
            method = machine.machine_type_id.pr_method
            prc_mtd = getattr(self, method)
            prc_mtd(files, process_dir, success_dir, failure_dir)


class MachineProcessLog(models.Model):
    _name = 'machine.process.log'
    _description = 'Machine Process Log'
    _order = 'date desc'
    _rec_name = 'file_name'

    date = fields.Datetime('Process Date')
    machine_id = fields.Many2one('machine.machine', 'Machine')
    error_code = fields.Char('Error Code')
    file_name = fields.Char('File Name')
    description = fields.Text('Description')
    state = fields.Selection([('pass', 'Passed'), ('fail', 'Failed')], 'Status')
