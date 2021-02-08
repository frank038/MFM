#!/usr/bin/env python3
"""
module for extract compressed files also with password
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio
import subprocess
import os

# 1 = on selected item(s); 2 = on background; 3 = both
mtype = 1
# this name appears in the menu
name = "Extract here..."
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
# one item at time
def enabled(fpath):
    if len(fpath) == 1:
        # if the mimetype is supported
        file = Gio.File.new_for_path(fpath[0])
        file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
        ftype = Gio.FileInfo.get_content_type(file_info)
        #print("ftype::", ftype)
        if ftype in ["application/x-compressed-tar", "application/zip", "application/x-cd-image", "application/x-tar",
                    "application/vnd.comicbook+zip", "application/x-7z-compressed", "application/x-bzip-compressed-tar"]:
            # the folder must be writable
            if os.access(os.path.dirname(fpath[0]), os.R_OK):
                return 1
        else:
            return 0
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
        self.connect ('delete-event', lambda w,e: self.destroy())
        ########
        self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.mainbox)
        # get the password
        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.mainbox.add(self.entry)
        self.ckb = Gtk.CheckButton.new_with_label("Hide/Show the password")
        self.ckb.connect("toggled", self.on_ckb_toggle)
        self.mainbox.add(self.ckb)
        self.btnbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.mainbox.add(self.btnbox)
        self.btncancel = Gtk.Button(label="Cancel")
        self.btncancel.connect("clicked", lambda w: self.destroy())
        self.btnbox.add(self.btncancel)
        self.btnok = Gtk.Button(label="Ok")
        self.btnbox.add(self.btnok)
        self.btnbox.set_homogeneous(True)
        ########
        iterpath = self.wiconview.IV.get_selected_items()[0]
        model = self.wiconview.IV.get_model()
        # file name
        fname = model[iterpath][1]
        # path
        dname = model[iterpath][3]
        # full path and file name
        item_path = os.path.join(dname, fname)
        (nroot, suffix) = os.path.splitext(fname)
        # the folder only name in which extract the archive
        ndir_name = nroot
        if os.path.exists(os.path.join(dname, ndir_name)):
            i = 1
            while i:
                if os.path.exists(os.path.join(dname, ndir_name+"_("+str(i)+")")):
                    i += 1
                else:
                    ndir_name = ndir_name+"_("+str(i)+")"
                    i = 0
        #
        # test the archive for password
        ret = self.test_archive(item_path)
        
        if ret == 1:
            try:
                ret = subprocess.check_output('7z x "-o{}" -y -aou -- "{}"'.format(os.path.join(dname, ndir_name), item_path), shell=True)
                if "Everything is Ok" in ret.decode():
                    self.generic_dialog1("Info", "Archive extracted.")
                else:
                    self.generic_dialog1("ERROR", "Issues while extracting the archive.")
            except Exception as E:
                self.generic_dialog1("ERROR", "Issues while extracting the archive:\n{}.".format(str(E)))
                self.destroy()
            self.destroy()
        # ask for the password
        elif ret == 2:
            self.btnok.connect("clicked", self.on_btn_ok, dname, ndir_name, item_path)
            self.show_all()
        #
        elif ret == 0:
            self.generic_dialog1("ERROR", "Issues while checking the archive.")
            self.destroy()
    
    # 
    def test_archive(self, path):
        szdata = None
        try:
            szdata = subprocess.check_output('7z l -slt -bso0 -- "{}"'.format(path), shell=True)
        except:
            return 0
        
        if szdata != None:
            szdata_decoded = szdata.decode()
            ddata = szdata_decoded.splitlines()
            if "Encrypted = +" in ddata:
                return 2
            else:
                return 1
    
    #
    def on_btn_ok(self, button, dname, ndir_name, item_path):
        self.spswd = self.entry.get_text()
        self.hide()
        if not self.spswd:
            self.destroy()
        
        try:
            ret = subprocess.check_output('7z x "-p{}" "-o{}" -y -aou -- "{}"'.format(self.spswd, os.path.join(dname, ndir_name), item_path), shell=True)
            if "Everything is Ok" in ret.decode():
                self.generic_dialog1("Info", "Archive extracted.")
            else:
                self.generic_dialog1("ERROR", "Issues while extracting the archive.")
        except Exception as E:
            self.generic_dialog1("ERROR", "Issues while extracting the archive:\n{}.".format(str(E)))
            self.destroy()
        self.destroy()
        
    #
    def on_ckb_toggle(self, widget):
        if widget.get_active():
            self.entry.set_visibility(True)
        else:
            self.entry.set_visibility(False)

    # generic ok dialog 
    def generic_dialog1(self, message1, message2):
        dialog = Gtk.MessageDialog(parent=self.wiconview.window, flags=0, message_type=Gtk.MessageType.ERROR,
            buttons=(Gtk.STOCK_OK, Gtk.ButtonsType.OK), text=message1)
        dialog.format_secondary_text("{}".format(message2))
        dialog.run()
        dialog.destroy()
