#!/usr/bin/env python3
"""
dialog for item properties
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
import sys


# 1 = on selected item(s); 2 = on background; 3 = both
mtype = 1
# this name appears in the menu
name = "Property"
## not implemented
#icon = "icon"
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
    if len(fpath) > 0:
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

# language module
try:
    from menu_property_lang import *
except:
    print("lang module for the module menu_property required. Exiting...")
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
        # the notebook
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.add(self.notebook)
        # the page
        self.page1 = Gtk.Box()
        self.notebook.add(self.page1)
        self.notebook.set_tab_label_text(self.page1, MPR_PAGE1)
        # the grid
        self.prop_grid = Gtk.Grid()
        self.prop_grid.set_border_width(10)
        self.prop_grid.set_row_spacing(5)
        self.prop_grid.set_column_spacing(10)
        self.page1.add(self.prop_grid)
        # label number of items
        label_item = Gtk.Label()
        label_item.set_markup("<i>"+MPR_SEL_ITEMS+"</i>")
        self.prop_grid.attach(label_item, 0,0,1,1)
        label_item.props.xalign = 1
            #
        label_nitem = Gtk.Label()
        self.prop_grid.attach(label_nitem, 1,0,1,1)
        label_nitem.props.xalign = 0
        label_nitem.set_label(str(self.num_items()))
        # label size
        label_size = Gtk.Label()
        label_size.set_markup("<i>"+MPR_IT_SIZE+"</i>")
        self.prop_grid.attach(label_size, 0,1,1,1)
        label_size.props.xalign = 1
            #
        n_s = self.siz_items()
        label_nsize = Gtk.Label()
        self.prop_grid.attach(label_nsize, 1,1,1,1)
        label_nsize.props.xalign = 0
        label_nsize.set_label(str(n_s))
        #
        self.connect ('delete-event', lambda w,e: self.destroy())
        self.show_all()
        
        
    # number of selected items
    def num_items(self):
        n_i = len(self.wiconview.IV.get_selected_items())
        return n_i
        
    # size of the selected items
    def siz_items(self):
        from functions import convert_size2 as convert_size2
        total_items_size = 0
        modello = self.wiconview.modello
        for rrow in self.wiconview.IV.get_selected_items():
            item_path = os.path.join(modello[rrow][3], modello[rrow][1])
            # if folder
            if modello[rrow][2] == "a":
                if os.path.exists(item_path):
                    f_item_dim = self.folder_size(item_path)
                    total_items_size += f_item_dim
                else:
                    total_items_size += 0
            # if file
            elif modello[rrow][2] == "b":
                if os.path.exists(item_path):
                    i_item_dim = os.stat(item_path).st_size
                    total_items_size += i_item_dim
                else:
                    total_items_size += 0
        r_total_items_size = convert_size2(total_items_size)
        return r_total_items_size
    
    # find the size of folders
    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    if os.path.islink(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size
