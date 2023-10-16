import xlsxwriter
from datetime import datetime

workbook = xlsxwriter.Workbook('my_dict_excel.xlsx')
worksheet = workbook.add_worksheet()
dc_vals = {'ProductName': 'GSA3_Part side', 'OperatorName': 'Administrator', 'TimeIn': '2021_07_31_05_19_29',
           'Equipment Name': 'CAM_I42M_ICI_0000', 'PCBBarcode': '5678', 'PCBFiducial1': '(FID1)_0#A0',
           'PCBFiducial2': '(FID2)_0#A0', 'PCBFiducial3': '(FID3)_0#A0',
           'data': [
               [{'Caption': '(FID1)#A0'}, {'PCBFiducial1checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags1': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
                {'measurement1': [{'dx': 0.0}, {'dy': -0.021166666666666667}, {'dL': 0.021166666666666667}]}],
               [{'Caption': '(FID2)#A0'}, {'PCBFiducial2checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags2': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
                {'measurement2': [{'dx': 0.0}, {'dy': 0.021166666666666667}, {'dL': 0.021166666666666667}]}],
               [{'Caption': '(FID3)#A0'}, {'PCBFiducial3checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags3': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
                {'measurement3': [{'dx': 0.0}, {'dy': 0.021166666666666667}, {'dL': 0.021166666666666667}]}],
               [{'Caption': '(CUT2)#A0'}, {'PCBFiducial4checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags4': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '0'}]},
                {'measurement4': [{'lf0': -0.162139249}, {'lf1': -0.26455873766666665}, {'lf2': 0.04004816306666666}]}],
               [{'Caption': '(CUT1)#A0'}, {'PCBFiducial5checkresult': 'true'}, {'Resolution': '600'},
                {'FailureInfoFlags5': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'},
                                       {'FailureInfoFlags': '3221225473'}]},
                {'measurement5': [{'lf0': -0.17850840599999998}, {'lf1': -0.275564854}, {'lf2': 0.13886196933333333}]}],
               [{'Caption': '(CUT4)#A0'}, {'PCBFiducial6checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags6': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '0'}]},
                {'measurement6': [{'lf0': 0.07119590366666667}, {'lf1': 0.014153570033333332},
                                  {'lf2': 0.12400517066666668}]}],
               [{'Caption': '(CUT3)#A0'}, {'PCBFiducial7checkresult': 'true'}, {'Resolution': '600'}, {
                   'FailureInfoFlags7': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'},
                                         {'FailureInfoFlags': ['Has errors', 'Was edited by operator']}]},
                {'measurement7': [{'lf0': 0.12664537366666667}, {'lf1': 0.03692524153333333},
                                  {'lf2': 0.20496978733333335}]}],
               [{'Caption': '(DTM)#A0'}, {'PCBFiducial8checkresult': 'false'}, {'Resolution': '600'},
                {'FailureInfoFlags8': [{'TestObjectID': '0'}, {'FailureTypeID': '0'}, {'FailureInfoFlags': '64'}]},
                {'measurement8': [{'li0': 0.0}, {'li1': 0.0}, {'li2': 0.0}, {'li3': 0.0}, {'li4': 0.0}]}]]}
row = 0
BOLD = workbook.add_format({'bold': True})
for tag, value in dc_vals.items():
    if tag == 'data':
        worksheet.write(row, 0, tag, BOLD)
        for data in value:
            for pcb_data in data:
                for pcb_fd_result, res_value in pcb_data.items():
                    if pcb_fd_result.startswith('PCBCutSetting'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for values in res_value:
                            for pcbcut_res, pcbcut_value in values.items():
                                worksheet.write(row, 2, pcbcut_res)
                                worksheet.write(row, 3, pcbcut_value)
                                row += 1
                            row += 1
                    elif pcb_fd_result.startswith('FailureInfoFlags'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for values in res_value:
                            for FailureInfoFlags_res, FailureInfoFlags_res_value in values.items():
                                if FailureInfoFlags_res == 'FailureInfoFlags':
                                    worksheet.write(row, 2, FailureInfoFlags_res)
                                    worksheet.write(row, 3,
                                                    str(FailureInfoFlags_res_value).replace("'", "").replace("[",
                                                                                                             "").replace(
                                                        "]", ""))
                                else:
                                    worksheet.write(row, 2, FailureInfoFlags_res)
                                    worksheet.write(row, 3, FailureInfoFlags_res_value)

                                row += 1
                    elif pcb_fd_result.startswith('measurement'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for values in res_value:
                            for measure_res, measure_res_value in values.items():
                                worksheet.write(row, 2, measure_res)
                                worksheet.write(row, 3, measure_res_value)
                                row += 1
                    else:
                        if res_value == 'false':
                            cb = workbook.add_format({'font_color': 'red'})
                            worksheet.write(row, 1, pcb_fd_result)
                            worksheet.write(row, 2, res_value, cb)
                            row += 1
                        elif res_value == 'true':
                            cb = workbook.add_format({'font_color': 'green'})
                            worksheet.write(row, 1, pcb_fd_result)
                            worksheet.write(row, 2, res_value, cb)
                            row += 1
                        else:
                            worksheet.write(row, 1, pcb_fd_result)
                            worksheet.write(row, 2, res_value)
                            row += 1

            row += 1
        row -= 1
    else:
        worksheet.write(row, 0, tag, BOLD)
        worksheet.write(row, 1, value)
        row += 1
    row += 1
workbook.close()
