import xlsxwriter

workbook = xlsxwriter.Workbook('my_dict1.xlsx')
worksheet = workbook.add_worksheet()
dict = {
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
for key, value in dict.items():
    if key == 'PCBCutSetting':
        print(key)
        worksheet.write(row, 0, key)
        for key3 in value:
            print("KEY3", key3)
            for k4, v4 in key3.items():
                worksheet.write(row, 1, k4)
                worksheet.write(row, 2, v4)
                row += 1
        row -= 1
    elif key == 'PCBFiducialcheckresult':
        worksheet.write(row, 0, key)
        for key1 in value:
            for k1, v1 in key1.items():
                worksheet.write(row, 1, k1)
                worksheet.write(row, 2, v1)
                row += 1
        row -= 1

    elif key == 'measurements':
        worksheet.write(row, 0, key)
        for key2 in value:
            for k2, v2 in key2.items():
                worksheet.write(row, 1, k2)
                for all_items in v2:
                    for k3, v3 in all_items.items():
                        worksheet.write(row, 2, k3)
                        worksheet.write(row, 3, v3)
                        row += 1
        row -= 1
    elif key == 'FailureInfoFlags':
        worksheet.write(row, 0, key)
        for key3 in value:
            print("KEY3", key3)
            for k4, v4 in key3.items():
                worksheet.write(row, 1, k4)
                worksheet.write(row, 2, v4)
                row += 1
        row -= 1
    else:
        worksheet.write(row, 0, key)
        worksheet.write(row, 1, value)
    row += 1
workbook.close()

