#!/usr/bin/env python3
"""
dialog for item permissions
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import os
from pwd import getpwuid
import subprocess
import sys


# 1 = on selected item(s); 2 = on background; 3 = both
mtype = 1
# this name appears in the menu
name = "Permissions"
# the command to launch
command = ""
# position in the menu: int -1 means append only
# or in this string form: "pN"
# p: 0 or 1 or 2 or 3: 0 no separators, 1 separator above, 2 separator below, 3 both separator
# N: position, suggested > 4
# some menu items could be hidden so the position must consider them
position = -1

# enabled: if return is equal to 1 this script will be enabled
def enabled(fpath):
    if len(fpath) == 1:
        return 1
    else:
        return 0

def nname():
    return name

# if this returns "" the ModuleClass will be executed
def ccommand(IV):
    return command

def ttype():
    return mtype

def pposition():
    return position

sys.path.append("modules_menu/mod_lang")

# the language module
try:
    from menu_permissions_lang import *
except:
    print("lang module for the module menu_permissions required. Exiting...")
    sys.exit()

class ModuleClass(Gtk.Window):
    def __init__(self, wiconview):
        self.wiconview = wiconview
        # the main dialog
        Gtk.Window.__init__(self, title="")
        # center this window to parent
        self.set_transient_for(self.wiconview.window)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        # skip the taskbar
        self.set_skip_taskbar_hint(True)
        #
        self.set_default_size(500, 100)
        self.set_border_width(10)
        ########
        
        # home dir
        HOME = os.getenv("HOME")
        # 1 shows the button in the permission tab that lets me
        # restore the owner of the item if it not me - otherwise 0
        # the external program pkexec is used
        CAN_CHANGE_OWNER = 1
        #
        iterpath = self.wiconview.IV.get_selected_items()[0]
        model = self.wiconview.IV.get_model()
        fname = model[iterpath][1]
        dname = model[iterpath][3]
        item_path = os.path.join(dname, fname)
        per_grid = Gtk.Grid()
        per_grid.set_border_width(10)
        per_grid.set_row_spacing(5)
        per_grid.set_column_spacing(10)
        label_owner = Gtk.Label()
        label_owner.set_markup("<i>"+POWNER+"</i>")
        label_owner.props.xalign = 1
        label_owner_access = Gtk.Label()
        label_owner_access.set_markup("<i>"+PACCESS+"</i>")
        label_group = Gtk.Label()
        label_group.set_markup("<i>"+PGROUP+"</i>")
        label_group.props.xalign = 1
        label_group_access = Gtk.Label()
        label_group_access.set_markup("<i>"+PACCESS+"</i>")
        label_other = Gtk.Label()
        label_other.set_markup("<i>"+POTHERS+"</i>")
        label_other.props.xalign = 1
        label_other_access = Gtk.Label()
        label_other_access.set_markup("<i>"+PACCESS+"</i>")
        per_grid.attach(label_owner, 0,0,1,1)
        per_grid.attach(label_owner_access, 2,0,1,1)
        per_grid.attach(label_group, 0,1,1,1)
        per_grid.attach(label_group_access, 2,1,1,1)
        per_grid.attach(label_other, 0,2,1,1)
        per_grid.attach(label_other_access, 2,2,1,1)
        #
        l_combo_owner = Gtk.Label()   
        per_grid.attach(l_combo_owner, 1,0,1,1)
        combo_owner_access = Gtk.ComboBoxText()
        combo_owner_access.append_text(PREONLY)
        combo_owner_access.append_text(PWRONLY)
        combo_owner_access.append_text(PREWR)
        per_grid.attach(combo_owner_access, 3,0,1,1)
          #
        combo_group_access = Gtk.ComboBoxText()
        combo_group_access.append_text(PNONE)
        combo_group_access.append_text(PREONLY)
        combo_group_access.append_text(PWRONLY)
        combo_group_access.append_text(PREWR)
        per_grid.attach(combo_group_access, 3,1,1,1)
          #
        combo_other_access = Gtk.ComboBoxText()
        combo_other_access.append_text(PNONE)
        combo_other_access.append_text(PREONLY)
        combo_other_access.append_text(PWRONLY)
        combo_other_access.append_text(PREWR)
        per_grid.attach(combo_other_access, 3,2,1,1)
          # if the selected item is a file
        exec_cb = Gtk.CheckButton(PEXECASPROG)
        if os.path.isfile(item_path):
            per_grid.attach(exec_cb, 4,1,1,1)
        #
        # if the owner of the item is not me nothing can be changed
        # using pkexec
        if getpwuid(os.stat(item_path).st_uid).pw_name == os.path.basename(HOME):
            l_combo_owner.set_text(PME)
        else:
            l_combo_owner.set_text(PNOTME)
            combo_owner_access.set_sensitive(False)
            combo_group_access.set_sensitive(False)
            combo_other_access.set_sensitive(False)
            exec_cb.set_sensitive(False)
            if CAN_CHANGE_OWNER:
                pkexec_button = Gtk.Button(PCHOWNER)
                widget_tuple = (l_combo_owner, combo_owner_access, combo_group_access, combo_other_access, exec_cb, pkexec_button)
                pkexec_button.connect("clicked", self.on_pkexec, item_path, widget_tuple)
                per_grid.attach(pkexec_button, 4,0,1,1)
        # set the permissions
        try:
            pperms = oct(os.stat(item_path).st_mode)[-3:]
        except:
            pperms = -1
        if pperms != -1:
            ddata = self.set_permissions(pperms)
        permissions = ddata
        combo_owner_access.set_active(permissions[0])
        combo_group_access.set_active(permissions[1])
        combo_other_access.set_active(permissions[2])
        # user changes the permissions
        combo_owner_access.connect("changed", self.on_combo_access, item_path, 0)
        combo_group_access.connect("changed", self.on_combo_access, item_path, 1)
        combo_other_access.connect("changed", self.on_combo_access, item_path, 2)
        # if the selected item is a file
        if os.path.isfile(item_path):
            exec_cb.set_active(permissions[3])
            exec_cb.connect("toggled", self.on_exec_cb, item_path)
        #
        self.add(per_grid)
        # connect the close event to function
        self.connect ('delete-event', lambda w,e: self.destroy())
        self.show_all()
    
    # restore the permission of the item using pkexec
    def on_pkexec(self, pkexec_button, item_path, widget_tuple):
        # home dir
        HOME = os.getenv("HOME")
        me = os.path.basename(HOME)
        ret = None
        try:
            ret = subprocess.run(["pkexec", "chown", me, item_path])
        except:
            pass
        # if success
        if ret.returncode == 0:
            widget_tuple[0].set_text(PME)
            widget_tuple[1].set_sensitive(True)
            widget_tuple[2].set_sensitive(True)
            widget_tuple[3].set_sensitive(True)
            widget_tuple[4].set_sensitive(True)
            widget_tuple[5].destroy()
    
    # if user changes the permissions within this program
    def on_combo_access(self, cb, item_path, num):
        # 0 None - 1 read - 2 write - 3 read and write
        chs = cb.get_active()
        old_perms = oct(os.stat(item_path).st_mode)[-3:]
        new_perms = ""
        if chs == 0:
            if num == 0:
                # if the file has the execute bit restore it
                if int(old_perms[0])%2:
                    new_perms = "5"+old_perms[1]+old_perms[2]
                else:
                    new_perms = "4"+old_perms[1]+old_perms[2]
            if num == 1:
                new_perms = old_perms[0]+"0"+old_perms[2]
            elif num == 2:
                new_perms = old_perms[0]+old_perms[1]+"0"
        elif chs == 1:
            if num == 0:
                if int(old_perms[0])%2:
                    new_perms = "3"+old_perms[1]+old_perms[2]
                else: 
                    new_perms = "2"+old_perms[1]+old_perms[2]
            elif num == 1:
                new_perms = old_perms[0]+"4"+old_perms[2]
            elif num == 2:
                new_perms = old_perms[0]+old_perms[1]+"4"
        elif chs == 2:
            if num == 0:
                if int(old_perms[0])%2:
                    new_perms = "7"+old_perms[1]+old_perms[2]
                else: 
                    new_perms = "6"+old_perms[1]+old_perms[2]
            elif num == 1:
                new_perms = old_perms[0]+"2"+old_perms[2]
            elif num == 2:
                new_perms = old_perms[0]+old_perms[1]+"2"
        elif chs == 3:
            if num == 1:
                new_perms = old_perms[0]+"6"+old_perms[2]
            elif num == 2:
                new_perms = old_perms[0]+old_perms[1]+"6"
        # change the permissions
        os.chmod(item_path, int("{}".format(new_perms), 8))

    # toggle execute or not execute in the permissions tab 
    def on_exec_cb(self, cb, item_path):
        # get the state
        cb_state = cb.get_active()
        # get the permissions on the item
        old_perms = oct(os.stat(item_path).st_mode)[-3:]
        #
        aa = -1
        if cb_state:
            aa = 1
        else:
            aa = -1
        new_perms = str(int(old_perms[0])+aa)+old_perms[1]+old_perms[2]
        os.chmod(item_path, int("{}".format(new_perms), 8))
    
    # return a list of file or folder permissions
    def set_permissions(self, data):
        ldata = []
        is_exec = 0
        # read 0 - write 1 - read and write 2
        # first number
        if int(data[0]) == 7:
            ldata.append(2)
            is_exec = 1
        elif int(data[0]) == 6:
            ldata.append(2)
        elif int(data[0]) == 5:
            ldata.append(0)
            is_exec = 1
        elif int(data[0]) == 4:
            ldata.append(0)
        elif int(data[0]) == 3:
            ldata.append(1)
            is_exec = 1
        elif int(data[0]) == 2:
            ldata.append(1)
        elif int(data[0]) == 1:
            ldata.append(0)
            is_exec = 1
        elif int(data[0]) == 0:
            ldata.append(0)
        # second number
        if int(data[1]) == 7:
            ldata.append(3)
        elif int(data[1]) == 6:
            ldata.append(3)
        elif int(data[1]) == 5:
            ldata.append(1)
        elif int(data[1]) == 4:
            ldata.append(1)
        elif int(data[1]) == 3:
            ldata.append(2)
        elif int(data[1]) == 2:
            ldata.append(2)
        elif int(data[1]) == 1:
            ldata.append(0)
        elif int(data[1]) == 0:
            ldata.append(0)
        # third number
        if int(data[2]) == 7:
            ldata.append(3)
        elif int(data[2]) == 6:
            ldata.append(3)
        elif int(data[2]) == 5:
            ldata.append(1)
        elif int(data[2]) == 4:
            ldata.append(1)
        elif int(data[2]) == 3:
            ldata.append(2)
        elif int(data[2]) == 2:
            ldata.append(2)
        elif int(data[2]) == 1:
            ldata.append(0)
        elif int(data[2]) == 0:
            ldata.append(0)
        # if odd added the exec bit
        if int(data[0])%2 or is_exec == 1:
            ldata.append(1)
        else:
            ldata.append(0)
        
        return ldata
