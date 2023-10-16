import xlsxwriter

workbook = xlsxwriter.Workbook('my_dict1.xlsx')
worksheet = workbook.add_worksheet()
dict = {'ProductName': 'GSA3_Part side', 'OperatorName': 'Administrator', 'TimeIn': '2021_07_31_05_19_29',
        'Equipment Name': 'CAM_I42M_ICI_0000', 'PCBBarcode': '5678', 'PCBFiducial1': '(FID1)_0#A0',
        'PCBFiducial2': '(FID2)_0#A0', 'PCBFiducial3': '(FID3)_0#A0',
        'PCBFiducialcheckresult': [{'PCBFiducial1checkresult': 'false'},
                                   {'PCBFiducial2checkresult': 'false'},
                                   {'PCBFiducial3checkresult': 'false'},
                                   {'PCBFiducial4checkresult': 'false'},
                                   {'PCBFiducial5checkresult': 'true'},
                                   {'PCBFiducial6checkresult': 'false'},
                                   {'PCBFiducial7checkresult': 'true'},
                                   {'PCBFiducial8checkresult': 'false'}],
        'MeasurementsResult': [{'Caption': '(FID1)#A0'}, {'Caption': '(FID2)#A0'}, {'Caption': '(FID3)#A0'},
                               {'Caption': '(CUT2)#A0'}, {'Caption': '(CUT1)#A0'}, {'Caption': '(CUT4)#A0'},
                               {'Caption': '(CUT3)#A0'}, {'Caption': '(DTM)#A0'}],
        'measurements': [{'measurement1': [{'dx': 0.0},
                                           {'dy': -0.021166666666666667},
                                           {'dL': 0.021166666666666667}]},
                         {'measurement2': [{'dx': 0.0},
                                           {'dy': 0.021166666666666667},
                                           {'dL': 0.021166666666666667}]},
                         {'measurement3': [{'dx': 0.0},
                                           {'dy': 0.021166666666666667},
                                           {'dL': 0.021166666666666667}]},
                         {'measurement4': [{'lf0': -0.162139249},
                                           {'lf1': -0.26455873766666665},
                                           {'lf2': 0.04004816306666666}]},
                         {'measurement5': [{'lf0': -0.17850840599999998},
                                           {'lf1': -0.275564854},
                                           {'lf2': 0.13886196933333333}]},
                         {'measurement6': [{'lf0': 0.07119590366666667},
                                           {'lf1': 0.014153570033333332},
                                           {'lf2': 0.12400517066666668}]},
                         {'measurement7': [{'lf0': 0.12664537366666667},
                                           {'lf1': 0.03692524153333333},
                                           {'lf2': 0.20496978733333335}]},
                         {'measurement8': [{'li0': 0.0},
                                           {'li1': 0.0},
                                           {'li2': 0.0},
                                           {'li3': 0.0},
                                           {'li4': 0.0}]}],
        'Failureinfoflags': [
            {'Failureinfoflag1': [{'TestObjectID': '14', 'FailureTypeID': '2', 'FailureInfoFlags': '0'}]},
            {'Failureinfoflag2': [{'TestObjectID': '14', 'FailureTypeID': '2', 'FailureInfoFlags': '0'}]},
            {'Failureinfoflag3': [{'TestObjectID': '14', 'FailureTypeID': '2', 'FailureInfoFlags': '0'}]},
            {'Failureinfoflag4': [{'TestObjectID': '-2', 'FailureTypeID': '-1', 'FailureInfoFlags': '0'}]},
            {'Failureinfoflag5': [{'TestObjectID': '-2', 'FailureTypeID': '-1',
                                   'FailureInfoFlags': 'Has errors , Was edited by operator,pseudo errors'}]},
            {'Failureinfoflag6': [{'TestObjectID': '-2', 'FailureTypeID': '-1', 'FailureInfoFlags': '0'}]},
            {'Failureinfoflag7': [{'TestObjectID': '-2', 'FailureTypeID': '-1',
                                   'FailureInfoFlags': 'Has errors, Was edited by operator'}]},
            {'Failureinfoflag8': [{'TestObjectID': '0', 'FailureTypeID': '0', 'FailureInfoFlags': '64'}]}]

        }

row = 0
for tag, value in dict.items():
    if tag == 'PCBFiducialcheckresult':
        worksheet.write(row, 0, tag)
        for pcb_result in value:
            for pcb_res, res_val in pcb_result.items():
                worksheet.write(row, 1, pcb_res)
                worksheet.write(row, 2, res_val)
                row += 1
        row -= 1
    elif tag == 'MeasurementsResult':
        worksheet.write(row, 0, tag)
        for measurement_results in value:
            for caption, res_mr_val in measurement_results.items():
                worksheet.write(row, 1, caption)
                worksheet.write(row, 2, res_mr_val)
                row += 1
        row -= 1
    elif tag == 'measurements':
        worksheet.write(row, 0, tag)
        for measurement_result in value:
            for measurement_res, res_val in measurement_result.items():
                worksheet.write(row, 1, measurement_res)
                for meas_res in res_val:
                    for result, res_value in meas_res.items():
                        worksheet.write(row, 2, result)
                        worksheet.write(row, 3, res_value)
                        row += 1
        row -= 1
    elif tag == 'Failureinfoflags':
        worksheet.write(row, 0, tag)
        for Failureinfoflags_result in value:
            for Finfoflags_res, f_res_value in Failureinfoflags_result.items():
                worksheet.write(row, 1, Finfoflags_res)
                for f_info_res in f_res_value:
                    for res, val in f_info_res.items():
                        worksheet.write(row, 2, res)
                        worksheet.write(row, 3, val)
                        row += 1
        row -= 1

    else:
        worksheet.write(row, 0, tag)
        worksheet.write(row, 1, value)
    row += 1

workbook.close()
