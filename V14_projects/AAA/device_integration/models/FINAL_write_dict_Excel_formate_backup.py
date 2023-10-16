import xlsxwriter

workbook = xlsxwriter.Workbook('my_dict_excel.xlsx')
worksheet = workbook.add_worksheet()
dc_vals = {
    'ProductName': 'GSA3_Part side',
    'OperatorName': 'Administrator',
    'TimeIn': '2021_07_31_05_19_29',
    'Equipment Name': 'CAM_I42M_ICI_0000',
    'PCBBarcode': '5678',
    'PCBFiducial1': '(FID1)_0#A0',
    'PCBFiducial2': '(FID2)_0#A0',
    'PCBFiducial3': '(FID3)_0#A0',
    'data': [
        [
            {'Caption': '(FID1)#A0'},
            {'PCBFiducial1checkresult': 'false'},
            {},
            {'Resolution': '600'},
            {'FailureInfoFlags1': [
                {'TestObjectID': '14'},
                {'FailureTypeID': '2'},
                {'FailureInfoFlags': '0'}
            ]},
            {'measurement1': [
                {'dx': 0.0},
                {'dy': -0.021166666666666667},
                {'dL': 0.021166666666666667}
            ]}],
        [
            {'Caption': '(FID2)#A0'},
            {'PCBFiducial2checkresult': 'false'},
            {},
            {'Resolution': '600'},
            {'FailureInfoFlags2': [
                {'TestObjectID': '14'},
                {'FailureTypeID': '2'},
                {'FailureInfoFlags': '0'}
            ]},
            {'measurement2': [
                {'dx': 0.0},
                {'dy': 0.021166666666666667},
                {'dL': 0.021166666666666667}
            ]}],
        [
            {'Caption': '(FID3)#A0'},
            {'PCBFiducial3checkresult': 'false'},
            {},
            {'Resolution': '600'},
            {'FailureInfoFlags3': [
                {'TestObjectID': '14'},
                {'FailureTypeID': '2'},
                {'FailureInfoFlags': '0'}
            ]},
            {'measurement3': [
                {'dx': 0.0},
                {'dy': 0.021166666666666667},
                {'dL': 0.021166666666666667}
            ]}],
        [
            {'Caption': '(CUT2)#A0'},
            {'PCBFiducial4checkresult': 'false'},
            {'PCBCutSetting': [
                {
                    'SettingLimitMinLength': '-7.086614e+00',
                    'SettingLimitMaxLength': '7.086614e+00',
                    'SettingLimitMinPeak': '-7.086614e+00',
                    'SettingLimitMaxPeak': '3.543307e+00'
                }]},
            {'Resolution': '600'},
            {'FailureInfoFlags4': [
                {'TestObjectID': '-2'},
                {'FailureTypeID': '-1'},
                {'FailureInfoFlags': '0'}
            ]},
            {'measurement4': [
                {'lf0': -0.162139249},
                {'lf1': -0.26455873766666665},
                {'lf2': 0.04004816306666666}
            ]}],
        [
            {'Caption': '(CUT1)#A0'},
            {'PCBFiducial5checkresult': 'true'},
            {'PCBCutSetting': [
                {
                    'SettingLimitMinLength': '-4.724409e+00',
                    'SettingLimitMaxLength': '7.086614e+00',
                    'SettingLimitMinPeak': '-4.724409e+00',
                    'SettingLimitMaxPeak': '7.086614e+00'}]},
            {'Resolution': '600'},
            {'FailureInfoFlags5': [
                {'TestObjectID': '-2'},
                {'FailureTypeID': '-1'},
                {'FailureInfoFlags': '3221225473'}
            ]},
            {'measurement5': [
                {'lf0': -0.17850840599999998},
                {'lf1': -0.275564854},
                {'lf2': 0.13886196933333333}
            ]}],
        [
            {'Caption': '(CUT4)#A0'},
            {'PCBFiducial6checkresult': 'false'},
            {'PCBCutSetting': [
                {
                    'SettingLimitMinLength': '-7.086614e+00',
                    'SettingLimitMaxLength': '7.086614e+00',
                    'SettingLimitMinPeak': '-7.086614e+00',
                    'SettingLimitMaxPeak': '3.543307e+00'}
            ]},
            {'Resolution': '600'},
            {'FailureInfoFlags6': [
                {'TestObjectID': '-2'},
                {'FailureTypeID': '-1'},
                {'FailureInfoFlags': '0'}]},
            {'measurement6': [
                {'lf0': 0.07119590366666667},
                {'lf1': 0.014153570033333332},
                {'lf2': 0.12400517066666668}
            ]}],
        [
            {'Caption': '(CUT3)#A0'},
            {'PCBFiducial7checkresult': 'true'},
            {'PCBCutSetting': [
                {
                    'SettingLimitMinLength': '-7.086614e+00',
                    'SettingLimitMaxLength': '7.086614e+00',
                    'SettingLimitMinPeak': '-7.086614e+00',
                    'SettingLimitMaxPeak': '3.543307e+00'}
            ]},
            {'Resolution': '600'},
            {'FailureInfoFlags7': [
                {'TestObjectID': '-2'},
                {'FailureTypeID': '-1'},
                {'FailureInfoFlags': ['Has errors', 'Was edited by operator']}
            ]},
            {'measurement7': [
                {'lf0': 0.12664537366666667},
                {'lf1': 0.03692524153333333},
                {'lf2': 0.20496978733333335}
            ]}],
        [
            {'Caption': '(DTM)#A0'},
            {'PCBFiducial8checkresult': 'false'},
            {},
            {'Resolution': '600'},
            {'FailureInfoFlags8': [
                {'TestObjectID': '0'},
                {'FailureTypeID': '0'},
                {'FailureInfoFlags': '64'}
            ]},
            {'measurement8': [
                {'li0': 0.0},
                {'li1': 0.0},
                {'li2': 0.0},
                {'li3': 0.0},
                {'li4': 0.0}
            ]
            }
        ]
    ]
}
row = 0
for tag, value in dc_vals.items():
    if tag == 'data':
        worksheet.write(row, 0, tag)
        for data in value:
            for pcb_data in data:
                for pcb_fd_result, res_value in pcb_data.items():
                    print("pcbbbbbb", pcb_fd_result)
                    print("bcccc", res_value)
                    if pcb_fd_result.startswith('PCBCutSetting'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for valuessss in res_value:
                            print("sdssdsdd", valuessss)
                            for all_key, all_val in valuessss.items():
                                print("mmmmmmmmm", all_key)
                                print("nnnnnnnnn", all_val)
                                # for er_msg in all_val:
                                worksheet.write(row, 2, all_key)
                                worksheet.write(row, 3, all_val)
                                row += 1
                            row += 1
                    elif pcb_fd_result.startswith('FailureInfoFlags'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for valuessss in res_value:
                            print("sdssdsdd", valuessss)
                            for all_key, all_val in valuessss.items():
                                print("mmmmmmmmm", all_key)
                                print("nnnnnnnnn", all_val)
                                for er_msg in all_val:
                                    worksheet.write(row, 2, all_key)
                                    worksheet.write(row, 3, er_msg)
                                row += 1
                    elif pcb_fd_result.startswith('measurement'):
                        worksheet.write(row, 1, pcb_fd_result)
                        for valuessss in res_value:
                            print("sdssdsdd", valuessss)
                            for all_key, all_val in valuessss.items():
                                print("mmmmmmmmm", all_key)
                                print("nnnnnnnnn", all_val)
                                worksheet.write(row, 2, all_key)
                                worksheet.write(row, 3, all_val)
                                row += 1
                    else:
                        worksheet.write(row, 1, pcb_fd_result)
                        worksheet.write(row, 2, res_value)
                        row += 1
            row += 1
        row -= 1
    else:
        worksheet.write(row, 0, tag)
        worksheet.write(row, 1, value)
    row += 1

workbook.close()

# dc = {'ProductName': 'GSA3_Part side', 'OperatorName': 'Administrator', 'TimeIn': '2021_07_31_05_19_29',
#       'Equipment Name': 'CAM_I42M_ICI_0000', 'PCBBarcode': '5678', 'PCBFiducial1': '(FID1)_0#A0',
#       'PCBFiducial2': '(FID2)_0#A0', 'PCBFiducial3': '(FID3)_0#A0', 'data': [
#         [{'Caption': '(FID1)#A0'}, {'PCBFiducial1checkresult': 'false'},
#          {'FailureInfoFlags1': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
#          {'Resolution': '600'},
#          {'measurement1': [{'dx': '0.000000e+00'}, {'dy': '-5.000000e-01'}, {'dL': '5.000000e-01'}]}],
#         [{'Caption': '(FID2)#A0'}, {'PCBFiducial2checkresult': 'false'},
#          {'FailureInfoFlags2': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
#          {'Resolution': '600'},
#          {'measurement2': [{'dx': '0.000000e+00'}, {'dy': '5.000000e-01'}, {'dL': '5.000000e-01'}]}],
#         [{'Caption': '(FID3)#A0'}, {'PCBFiducial3checkresult': 'false'},
#          {'FailureInfoFlags3': [{'TestObjectID': '14'}, {'FailureTypeID': '2'}, {'FailureInfoFlags': '0'}]},
#          {'Resolution': '600'},
#          {'measurement3': [{'dx': '0.000000e+00'}, {'dy': '5.000000e-01'}, {'dL': '5.000000e-01'}]}],
#         [{'Caption': '(CUT2)#A0'}, {'PCBFiducial4checkresult': 'false'},
#          {'FailureInfoFlags4': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '0'}]},
#          {'Resolution': '600'},
#          {'measurement4': [{'lf0': '-3.830061e+00'}, {'lf1': '-6.249419e+00'}, {'lf2': '9.460196e-01'}]}],
#         [{'Caption': '(CUT1)#A0'}, {'PCBFiducial5checkresult': 'true'},
#          {'FailureInfoFlags5': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '3221225473'}]},
#          {'Resolution': '600'},
#          {'measurement5': [{'lf0': '-4.216734e+00'}, {'lf1': '-6.509406e+00'}, {'lf2': '3.280204e+00'}]}],
#         [{'Caption': '(CUT4)#A0'}, {'PCBFiducial6checkresult': 'false'},
#          {'FailureInfoFlags6': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '0'}]},
#          {'Resolution': '600'},
#          {'measurement6': [{'lf0': '1.681793e+00'}, {'lf1': '3.343363e-01'}, {'lf2': '2.929256e+00'}]}],
#         [{'Caption': '(CUT3)#A0'}, {'PCBFiducial7checkresult': 'true'},
#          {'FailureInfoFlags7': [{'TestObjectID': '-2'}, {'FailureTypeID': '-1'}, {'FailureInfoFlags': '3221225472'}]},
#          {'Resolution': '600'},
#          {'measurement7': [{'lf0': '2.991623e+00'}, {'lf1': '8.722498e-01'}, {'lf2': '4.841806e+00'}]}],
#         [{'Caption': '(DTM)#A0'}, {'PCBFiducial8checkresult': 'false'},
#          {'FailureInfoFlags8': [{'TestObjectID': '0'}, {'FailureTypeID': '0'}, {'FailureInfoFlags': '64'}]},
#          {'Resolution': '600'},
#          {'measurement8': [{'li0': '0.000000e+00'}, {'li1': '0'}, {'li2': '0'}, {'li3': '0'}, {'li4': '0'}]}]]}

#  {
#     'ProductName': 'GSA3_Part side',
#     'OperatorName': 'Administrator',
#     'TimeIn': '2021_07_31_05_19_29',
#     'Equipment Name': 'CAM_I42M_ICI_0000',
#     'PCBBarcode': '5678',
#     'PCBFiducial1': '(FID1)_0#A0',
#     'PCBFiducial2': '(FID2)_0#A0',
#     'PCBFiducial3': '(FID3)_0#A0',
#     'data': [
#         [
#             {'Caption': '(FID1)#A0'},
#             {'PCBFiducial1checkresult': 'false'},
#             {},
#             {'Resolution': '600'},
#             {'FailureInfoFlags1': [
#                 {'TestObjectID': '14'},
#                 {'FailureTypeID': '2'},
#                 {'FailureInfoFlags': '0'}
#             ]},
#             {'measurement1': [
#                 {'dx': 0.0},
#                 {'dy': -0.021166666666666667},
#                 {'dL': 0.021166666666666667}
#             ]}],
#         [
#             {'Caption': '(FID2)#A0'},
#             {'PCBFiducial2checkresult': 'false'},
#             {},
#             {'Resolution': '600'},
#             {'FailureInfoFlags2': [
#                 {'TestObjectID': '14'},
#                 {'FailureTypeID': '2'},
#                 {'FailureInfoFlags': '0'}
#             ]},
#             {'measurement2': [
#                 {'dx': 0.0},
#                 {'dy': 0.021166666666666667},
#                 {'dL': 0.021166666666666667}
#             ]}],
#         [
#             {'Caption': '(FID3)#A0'},
#             {'PCBFiducial3checkresult': 'false'},
#             {},
#             {'Resolution': '600'},
#             {'FailureInfoFlags3': [
#                 {'TestObjectID': '14'},
#                 {'FailureTypeID': '2'},
#                 {'FailureInfoFlags': '0'}
#             ]},
#             {'measurement3': [
#                 {'dx': 0.0},
#                 {'dy': 0.021166666666666667},
#                 {'dL': 0.021166666666666667}
#             ]}],
#         [
#             {'Caption': '(CUT2)#A0'},
#             {'PCBFiducial4checkresult': 'false'},
#             {'PCBCutSetting': [
#                 {
#                     'SettingLimitMinLength': '-7.086614e+00',
#                     'SettingLimitMaxLength': '7.086614e+00',
#                     'SettingLimitMinPeak': '-7.086614e+00',
#                     'SettingLimitMaxPeak': '3.543307e+00'
#                 }]},
#             {'Resolution': '600'},
#             {'FailureInfoFlags4': [
#                 {'TestObjectID': '-2'},
#                 {'FailureTypeID': '-1'},
#                 {'FailureInfoFlags': '0'}
#             ]},
#             {'measurement4': [
#                 {'lf0': -0.162139249},
#                 {'lf1': -0.26455873766666665},
#                 {'lf2': 0.04004816306666666}
#             ]}],
#         [
#             {'Caption': '(CUT1)#A0'},
#             {'PCBFiducial5checkresult': 'true'},
#             {'PCBCutSetting': [
#                 {
#                     'SettingLimitMinLength': '-4.724409e+00',
#                     'SettingLimitMaxLength': '7.086614e+00',
#                     'SettingLimitMinPeak': '-4.724409e+00',
#                     'SettingLimitMaxPeak': '7.086614e+00'}]},
#             {'Resolution': '600'},
#             {'FailureInfoFlags5': [
#                 {'TestObjectID': '-2'},
#                 {'FailureTypeID': '-1'},
#                 {'FailureInfoFlags': '3221225473'}
#             ]},
#             {'measurement5': [
#                 {'lf0': -0.17850840599999998},
#                 {'lf1': -0.275564854},
#                 {'lf2': 0.13886196933333333}
#             ]}],
#         [
#             {'Caption': '(CUT4)#A0'},
#             {'PCBFiducial6checkresult': 'false'},
#             {'PCBCutSetting': [
#                 {
#                     'SettingLimitMinLength': '-7.086614e+00',
#                     'SettingLimitMaxLength': '7.086614e+00',
#                     'SettingLimitMinPeak': '-7.086614e+00',
#                     'SettingLimitMaxPeak': '3.543307e+00'}
#             ]},
#             {'Resolution': '600'},
#             {'FailureInfoFlags6': [
#                 {'TestObjectID': '-2'},
#                 {'FailureTypeID': '-1'},
#                 {'FailureInfoFlags': '0'}]},
#             {'measurement6': [
#                 {'lf0': 0.07119590366666667},
#                 {'lf1': 0.014153570033333332},
#                 {'lf2': 0.12400517066666668}
#             ]}],
#         [
#             {'Caption': '(CUT3)#A0'},
#             {'PCBFiducial7checkresult': 'true'},
#             {'PCBCutSetting': [
#                 {
#                     'SettingLimitMinLength': '-7.086614e+00',
#                     'SettingLimitMaxLength': '7.086614e+00',
#                     'SettingLimitMinPeak': '-7.086614e+00',
#                     'SettingLimitMaxPeak': '3.543307e+00'}
#             ]},
#             {'Resolution': '600'},
#             {'FailureInfoFlags7': [
#                 {'TestObjectID': '-2'},
#                 {'FailureTypeID': '-1'},
#                 {'FailureInfoFlags': ['Has errors', 'Was edited by operator']}
#             ]},
#             {'measurement7': [
#                 {'lf0': 0.12664537366666667},
#                 {'lf1': 0.03692524153333333},
#                 {'lf2': 0.20496978733333335}
#             ]}],
#         [
#             {'Caption': '(DTM)#A0'},
#             {'PCBFiducial8checkresult': 'false'},
#             {},
#             {'Resolution': '600'},
#             {'FailureInfoFlags8': [
#                 {'TestObjectID': '0'},
#                 {'FailureTypeID': '0'},
#                 {'FailureInfoFlags': '64'}
#             ]},
#             {'measurement8': [
#                 {'li0': 0.0},
#                 {'li1': 0.0},
#                 {'li2': 0.0},
#                 {'li3': 0.0},
#                 {'li4': 0.0}
#             ]
#             }
#         ]
#     ]
# }
