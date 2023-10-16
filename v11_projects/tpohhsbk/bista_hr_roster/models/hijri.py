#!/usr/bin/env python

import math
from datetime import datetime

DATE_FORMAT = '%Y-%m-%d'


def intPart(floatNum):
    if floatNum < -0.0000001:
        return math.ceil(floatNum - 0.0000001)
    return math.floor(floatNum + 0.0000001)


def Gregorian2Hijri(yr, mth, day):
    if ((yr > 1582) or ((yr == 1582) and (mth > 10)) or ((yr == 1582) and (
            mth == 10) and (day > 14))):
        jd1 = intPart((1461 * (yr + 4800 +
                               intPart((mth - 14) / 12.0))) / 4)
        jd2 = intPart((367 * (mth - 2 - 12 *
                              (intPart((mth - 14) / 12.0)))) / 12)
        jd3 = intPart((3 * (intPart((yr + 4900 +
                                     intPart((mth - 14) / 12.0)) / 100))) / 4)
        jd = jd1 + jd2 - jd3 + day - 32075
    else:
        jd1 = intPart((7 * (yr + 5001 +
                            intPart((mth - 9) / 7.0))) / 4)
        jd2 = intPart((275 * mth) / 9.0)
        jd = 367 * yr - jd1 + jd2 + day + 1729777

    length = jd - 1948440 + 10632
    n = intPart((length - 1) / 10631.0)
    length = length - 10631 * n + 354
    j1 = (intPart((10985 - length) / 5316.0)) * (intPart((
        50 * length) / 17719.0))
    j2 = (intPart(length / 5670.0)) * (intPart((43 * length) / 15238.0))
    j = j1 + j2
    l1 = (intPart((30 - j) / 15.0)) * (intPart((17719 * j) / 50.0))
    l2 = (intPart(j / 16.0)) * (intPart((15238 * j) / 43.0))
    length = length - l1 - l2 + 29
    m = intPart((24 * length) / 709.0)
    d = length - intPart((709 * m) / 24.0)
    y = 30 * n + j - 30

    return int(y), int(m), int(d)


def Hijri2Gregorian(yr, mth, day):
    jd1 = intPart((11 * yr + 3) / 30.0)
    jd2 = intPart((mth - 1) / 2.0)
    jd = jd1 + 354 * yr + 30 * mth - jd2 + day + 1948440 - 385

    if jd > 2299160:
        length = jd + 68569
        n = intPart((4 * length) / 146097.0)
        length = length - intPart((146097 * n + 3) / 4.0)
        i = intPart((4000 * (length + 1)) / 1461001.0)
        length = length - intPart((1461 * i) / 4.0) + 31
        j = intPart((80 * length) / 2447.0)
        d = length - intPart((2447 * j) / 80.0)
        length = intPart(j / 11.0)
        m = j + 2 - 12 * length
        y = 100 * (n - 49) + i + length
    else:
        j = jd + 1402
        k = intPart((j - 1) / 1461.0)
        length = j - 1461 * k
        n = intPart((length - 1) / 365.0) - intPart(length / 1461.0)
        i = length - 365 * n + 30
        j = intPart((80 * i) / 2447.0)
        d = i - intPart((2447 * j) / 80.0)
        i = intPart(j / 11.0)
        m = j + 2 - 12 * i
        y = 4 * k + n + i - 4716

    return int(y), int(m), int(d)


def Convert_Date(lang_date, from_lang, to_lang):
    date_list = str(lang_date).split('-')
    yr = int(date_list[0])
    mth = int(date_list[1])
    day = int(date_list[2])
    convert_function = (0, 0, 0)
    if to_lang:
        if to_lang == 'islamic' and from_lang == 'english':
            convert_function = Gregorian2Hijri(yr, mth, day)

        elif to_lang == 'english' and from_lang == 'islamic':
            convert_function = Hijri2Gregorian(yr, mth, day)

        if convert_function:
            current_date = convert_function
            curr_year = str(current_date[0])
            curr_mth = str(current_date[1])
            curr_day = str(current_date[2])
            current_date = str(curr_year + '-' + curr_mth + '-' + curr_day)
            current_date = str(datetime.strptime(current_date,
                                                 DATE_FORMAT).date())
            return current_date
    else:
        return None
