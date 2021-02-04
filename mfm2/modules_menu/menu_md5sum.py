#!/usr/bin/env python3
"""
dialog for the checksums
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from gi.repository.GdkPixbuf import Pixbuf
import os
import subprocess

# 1 = on selected item(s); 2 = on background; 3 = both
mtype = 1
# this name appears in the menu
name = "Checksum"
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
        #
        iterpath = self.wiconview.IV.get_selected_items()[0]
        model = self.wiconview.IV.get_model()
        fname = model[iterpath][1]
        dname = model[iterpath][3]
        item_path = os.path.join(dname, fname)
        #
        # identifiers and names of the checksum programs
        chks_list = ["MD5", "SHA256", "SHA1"]
        self.chks_exec = ["md5sum", "sha256sum", "sha1sum"]
        #
        chks_grid = Gtk.Grid()
        chks_grid.set_border_width(10)
        chks_grid.set_row_spacing(10)
        chks_grid.set_column_spacing(10)
        #
        label_checksum = Gtk.Label()
        label_checksum.set_markup("<i>"+"Checksum"+"</i>")
        label_checksum.props.xalign = 0
        chks_grid.attach(label_checksum, 0,0,1,1)
        #
        checksum_combo = Gtk.ComboBoxText()
        # populate from list
        for membr in chks_list:
            checksum_combo.append_text(membr)
        checksum_combo.set_active(0)
        chks_grid.attach(checksum_combo, 1,0,1,1)
        #
        checksum_button = Gtk.Button("HASH")
        chks_grid.attach(checksum_button, 2,0,1,1)
        #
        checksum_label = Gtk.Label()
        checksum_label.set_line_wrap(True)
        checksum_label.set_line_wrap_mode(1)
        checksum_label.props.xalign = 0
        checksum_label.set_selectable(True)
        chks_grid.attach(checksum_label, 0,1,6,1)
        # yes and no images
        checksum_pixbuf_yes = GdkPixbuf.Pixbuf.new_from_file_at_size("yes.svg", 32, 32)
        checksum_image_yes = Gtk.Image.new_from_pixbuf(checksum_pixbuf_yes)
        chks_grid.attach(checksum_image_yes, 9,1,1,1)
        checksum_pixbuf_no = GdkPixbuf.Pixbuf.new_from_file_at_size("no.svg", 32, 32)
        checksum_image_no = Gtk.Image.new_from_pixbuf(checksum_pixbuf_no)
        chks_grid.attach(checksum_image_no, 9,1,1,1)
        #
        verify_entry = Gtk.Entry()
        chks_grid.attach(verify_entry, 0,2,8,1)
        #
        verify_button = Gtk.Button("Verify")
        chks_grid.attach(verify_button, 9,2,1,1)
        #
        checksum_button.connect("clicked", self.on_checksum_button, item_path, checksum_combo, checksum_label, verify_entry, verify_button, checksum_image_yes, checksum_image_no)
        verify_button.connect("clicked", self.on_verify_button, checksum_label, verify_entry, checksum_image_yes, checksum_image_no)
        #
        self.add(chks_grid)
        self.show_all()
        # hide the images
        checksum_image_yes.hide()
        checksum_image_no.hide()
        
    # calculate the checksum
    def on_checksum_button(self, checksum_button, item_path, checksum_combo, checksum_label, verify_entry, verify_button, checksum_image_yes, checksum_image_no):
        if os.path.isfile(item_path):
            cb_selected = checksum_combo.get_active()
            the_exec = self.chks_exec[cb_selected]
            checksum = subprocess.check_output([the_exec, item_path], universal_newlines=True)
            checksum_label.set_text(checksum.split(" ")[0])
            verify_entry.set_text("")
            checksum_image_yes.hide()
            checksum_image_no.hide()
        
    # verify the checksum
    def on_verify_button(self, verify_button, checksum_label, verify_entry, checksum_image_yes, checksum_image_no):
        if checksum_label.get_text() != "":
            if (checksum_label.get_text() == verify_entry.get_text()):
                checksum_image_no.hide()
                checksum_image_yes.show()
            else:
                checksum_image_yes.hide()
                checksum_image_no.show()
