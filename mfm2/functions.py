#!/usr/bin/env python3

# convert the size into readable string
def convert_size2(fsize2):
    
    if fsize2 == 0 or fsize2 == 1:
        sfsize = str(fsize2)+" byte"
    elif fsize2//1024 == 0:
        sfsize = str(fsize2)+" bytes"
    elif fsize2//1048576 == 0:
        sfsize = str(round(fsize2/1024, 3))+" KB"
    elif fsize2//1073741824 == 0:
        sfsize = str(round(fsize2/1048576, 3))+" MB"
    elif fsize2//1099511627776 == 0:
        sfsize = str(round(fsize2/1073741824, 3))+" GiB"
    else:
        sfsize = str(round(fsize2/1099511627776, 3))+" GiB"
    
    return sfsize

def compare(model, row1, row2, user_data):
    value1 = model.get_value(row1, 2)
    value2 = model.get_value(row2, 2)
    if value1 < value2:
        return -1
    elif value1 == value2:
        value1 = model.get_value(row1, 1).lower()
        value2 = model.get_value(row2, 1).lower()
        return (value1 > value2) - (value1 < value2)
    else:
        return 1

# ascending order
def dcompare(model, row1, row2, user_data):
    value1 = model.get_value(row1, 9)
    value2 = model.get_value(row2, 9)
    if value1 < value2:
        return -1
    elif value1 == value2:
        return 0
    else:
        return 1

## descending order
# def dcompare2(model, row1, row2, user_data):
    # value1 = model.get_value(row1, 9)
    # value2 = model.get_value(row2, 9)
    # if value1 < value2:
        # return -1
    # elif value1 == value2:
        # return 0
    # else:
        # return 1
