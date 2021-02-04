#!/usr/bin/env python3
"""
this opens a terminal - xterm
"""
import shutil

# 1 = on selected item(s); 2 = on background; 3 = both
mtype = 3

# this name appears in the menu
name = "Terminal"
# the command to launch
command = "xterm"
# position in the menu: int -1 means append only
# or in this string form: "pN"
# p: 0 or 1 or 2 or 3: 0 no separators, 1 separator above, 2 separator below, 3 both separator
# N: position, suggested > 4
# some menu items could be hidden so the position must consider them
position = -1

# enabled: if return is equal to 1 this script will be enabled

""" 
path is the full path (path and name) list of selected items
if this script is called from the selected item(s),
or the working dir if it is called clicking in the background
"""

def enabled(fpath):
    if shutil.which(command):
        return 1
    else:
        return 0

def nname():
    return name

# if this returns "" the ModuleClass will be executed
def ccommand(wiconview):
    path = wiconview.working_path
    comm = "cd '{}' && /bin/bash".format(path)
    command2 = ['xterm', '-fa', 'Monospace', '-fs', '12', '-fg', 'white', '-bg', 'black', '-geometry', '70x18', '-e', comm]
    return command2

def ttype():
    return mtype

def pposition():
    return position
