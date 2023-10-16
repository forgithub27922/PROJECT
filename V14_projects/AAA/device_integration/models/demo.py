def pixeltomm(resolution_value, file_dictionary):
    new_dictionary = {}
    for key, value in file_dictionary.items():
        mm_value = value * (25.4 / resolution_value)
        new_dictionary.update({key: mm_value})
    print("New Dictionary ::::>", new_dictionary)
    return new_dictionary


pixeltomm(resolution_value=1200.00, file_dictionary={'a': -4.56E+00, 'b': -7.96E+00, 'c': 1.26E+00})
