#!/usr/bin/env python3

"""
module for cutting/copying - a dialog appears
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject
import time
import shutil
import os
from urllib.parse import unquote, quote
import threading

from cfg import USE_DATE
from lang import *

if USE_DATE == 1:
    import datetime


class SignalObject(GObject.Object):
    
    def __init__(self):
        GObject.Object.__init__(self)
        self._name = ""
        self.value = -99
        self._list = []
    
    @GObject.Property(type=str)
    def propName(self):
        'Read-write integer property.'
        return self._name

    @propName.setter
    def propName(self, name):
        self._name = name
    
    @GObject.Property(type=int)
    def propInt(self):
        'Read-write integer property.'
        return self.value

    @propInt.setter
    def propInt(self, value):
        self.value = value
    
    @GObject.Property(type=object)
    def propList(self):
        'Read-write integer property.'
        return self._list

    @propList.setter
    def propList(self, data):
        self._list.append(data)
    

class cThread(threading.Thread):
    
    def __init__(self, ssignal, item_list, action, pathdest, atype):
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.signal = ssignal
        self.item_list = item_list
        self.action = action
        self.pathdest = pathdest
        # action to perform if an item with the same name is found at destination
        # 1 automatic suffix - 2 overwrite - 3 rename or merge - 4 backup the existet file at destination
        # 5 ignore the item(s) - 6 means no same filename at destination
        self.atype = atype

    
    def run(self):
        time.sleep(1)
        # 0 means cancel was pressed in the dialog that checked a file with the same name was present at destination
        if self.signal.propInt == 0:
            return
        else:
            self.item_op()
        
    
    ## self.atype 1 or 3 or 4
    # add a suffix to the filename if the file exists at destination
    def faddSuffix(self, dest):
        # it exists or it is a broken link
        if os.path.exists(dest) or os.path.islink(dest):
            i = 1
            dir_name = os.path.dirname(dest)
            bname = os.path.basename(dest)
            dest = ""
            while i:
                nn = bname+"_("+str(i)+")"
                if os.path.exists(os.path.join(dir_name, nn)):
                    i += 1
                else:
                    dest = os.path.join(dir_name, nn)
                    i = 0
            
            return dest
    
    # add the suffix to the name
    def faddSuffix2(self, dts, dest):
        new_name = os.path.basename(dest)+dts
        dest = os.path.join(os.path.dirname(dest), new_name)
        return dest
    
    # 
    def item_op(self):
        #
        if not self.atype in [1,2,3,4,5,6]:
            return
        
        #
        self.items_skipped = ""
        # action: copy 1 - cut 2
        action = self.action
        # common suffix if date - the same date for all the items
        commSfx = ""
        if USE_DATE:
            z = datetime.datetime.now()
            #dY, dM, dD, dH, dm, ds, dms
            commSfx = "_{}.{}.{}_{}.{}.{}".format(z.year, z.month, z.day, z.hour, z.minute, z.second)
        #
        for dfile in self.item_list:
            self.event.wait(1.0)
            
            # interrupted by the user
            if self.signal.propInt == -1:
                return
            
            self.signal.propName = str(dfile)
            
            self.on_item(dfile, action, commSfx)
            
        
        # all tasks finished
        self.signal.propInt = -2
        if self.items_skipped:
            self.signal.propList = self.items_skipped

    # operation on single item
    def on_item(self, dfile, action_type, commSfx):
        #
        action = 0
        if action_type == "copy":
            action = 1
        elif action_type == "cut":
            action = 2
        # elif action_type == "link":
            # action = 4
        
        # dir
        if os.path.isdir(dfile):
            #
            if os.path.isdir(dfile):
                # full path at destination
                tdest = os.path.join(self.pathdest, os.path.basename(dfile))
                #
                # for the items in the dir: 1 automatic - 2 overwrite - 3 new name - 4 backup - 5 ignore
                #dcode = self.atype
                #
                # if not the exactly same item
                if dfile != tdest:
                    # the dir doesnt exist at destination or it is a broken link
                    if not os.path.exists(tdest):
                        try:
                            # link
                            if os.path.islink(tdest):
                                ret = ""
                                if USE_DATE:
                                    ret = self.faddSuffix2(commSfx, tdest)
                                else:
                                    ret = self.faddSuffix(tdest)
                                shutil.move(tdest, ret)
                            #
                            if action == 1:
                                shutil.copytree(dfile, tdest, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                            elif action == 2:
                                shutil.move(dfile, tdest)
                        except Exception as E:
                            self.items_skipped += "{}\n{}\n------------\n".format(tdest, str(E))
                    #
                    # exists at destination an item with the same name
                    elif os.path.exists(tdest):
                        # 1 automatic - add a suffix to folders (and files - not here)
                        if self.atype == 1:
                            if USE_DATE:
                                ret = self.faddSuffix2(commSfx, tdest)
                            else:
                                ret = self.faddSuffix(tdest)
                            try:
                                # link or broken link or file or not dir
                                if os.path.exists(tdest) or os.path.islink(tdest):
                                    if action == 1:
                                        shutil.copytree(dfile, ret, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                                    elif action == 2:
                                        shutil.move(dfile, ret)
                            except Exception as E:
                                self.items_skipped += "{}\n{}\n------------\n".format(tdest, str(E))
                        # 2 folder merged (later) - files overwritten
                        elif self.atype == 2:
                            try:
                                # remove any item already present at destination
                                if os.path.islink(tdest):
                                    os.unlink(tdest)
                                elif not os.path.isdir(tdest):
                                    os.remove(tdest)
                            except Exception as E:
                                self.items_skipped += "{}\n{}\n------------\n".format(tdest, str(E))
                        ## for atype 2 or 4 folders will be merged
                        # merge the folders: 2 overwrite - 4 backup existen files
                        if self.atype == 2 or self.atype == 4:
                            base_src = os.path.dirname(dfile)
                            base_dst = os.path.dirname(tdest)
                            # make the dirs and copy the relatives files in them
                            for sdir,ddir,ffile in os.walk(dfile):
                                for item in ddir:
                                    a = os.path.join(sdir, item)
                                    a_temp = a[len(base_src)+1:]
                                    b = os.path.join(base_dst, a_temp)
                                    #
                                    if os.path.exists(b) or os.path.islink(b):
                                        if not os.path.isdir(b):
                                            if USE_DATE:
                                                ret = self.faddSuffix2(commSfx, tdest)
                                            else:
                                                ret = self.faddSuffix(tdest)
                                            try:
                                                shutil.move(b, ret)
                                            except Exception as E:
                                                self.items_skipped += "{}\n{}\n------------\n".format(a, str(E))
                                                continue
                                    # 
                                    try:
                                        os.makedirs(b, exist_ok=False)
                                    except Exception as E: 
                                        self.items_skipped += "{}\n{}\n------------\n".format(a, str(E))
                                #
                                for item in ffile:
                                    a = os.path.join(sdir, item)
                                    a_temp = a[len(base_src)+1:]
                                    b = os.path.join(base_dst, a_temp)
                                    ## rename the files if they exists at destination 
                                    if self.atype == 4:
                                        if os.path.exists(b) or os.path.islink(b):
                                            if USE_DATE:
                                                ret = self.faddSuffix2(commSfx, b)
                                            else:
                                                ret = self.faddSuffix(b)
                                            try:
                                                shutil.move(b, ret)
                                            except  Exception as E:
                                                self.items_skipped += "{}\n{}\n------------\n".format(a, str(E))
                                                continue
                                    ## copy or move the files
                                    try:
                                        if action == 1:
                                            shutil.copy2(a, b, follow_symlinks=False)
                                        elif action == 2:
                                            shutil.move(a, b)
                                    except Exception as E:
                                        self.items_skipped += "{}\n{}\n------------\n".format(a, str(E))
                            # check il the folder is empty and if so remove it
                            if action == 2:
                                IS_NOT_EMPTY = 0
                                for sdir,ddir,ffile in os.walk(dfile):
                                    if ffile:
                                        IS_NOT_EMPTY = 1
                                        break
                                #
                                if IS_NOT_EMPTY:
                                    self.items_skipped += "{}\n{}\n------------\n".format(dfile, "Cannot remove it: not empty")
                                else:
                                    try:
                                        shutil.rmtree(dfile)
                                    except  Exception as E:
                                        self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))
                # origin and destination are exactly the same directory
                else:
                    # 1 automatic
                    if self.atype == 1:
                        ret = self.faddSuffix(dfile)
                        try:
                            if action == 1:
                                shutil.copytree(dfile, ret, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                            elif action == 2:
                                self.items_skipped += "{}\nExactly the same folder:\n{}\n------------\n".format(os.path.basename(tdest), "Skipped")
                        except Exception as E:
                                self.items_skipped += "{}\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    # 2 overwrite
                    elif self.atype == 2:
                        self.items_skipped += "{}\nExactly the same folder:\n{}\n------------\n".format(os.path.basename(tdest), "Skipped")
                    # 3 rename - 4 backup
                    elif self.atype == 4:
                        if action == 1 or action == 2:
                            try:
                                ret = self.faddSuffix(dfile)
                                shutil.copytree(dfile, ret, symlinks=True, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False)
                            except Exception as E:
                                self.items_skipped += "{}\n{}\n------------\n".format(os.path.basename(dfile), str(E))
                    # 5 ignore
                    elif self.atype == 5:
                        pass
        # file or link/broken link or else
        else:
            tdest = os.path.join(self.pathdest, os.path.basename(dfile))
            #
            if os.path.exists(tdest):
                # 1 automatic - add a suffix to files and folders to be copied
                if self.atype == 1:
                    try:
                        ret = ""
                        if USE_DATE:
                            ret = self.faddSuffix2(commSfx, tdest)
                        else:
                            ret = self.faddSuffix(tdest)
                        #
                        if action == 1:
                            shutil.copy2(dfile, ret, follow_symlinks=False)
                        elif action == 2:
                            if dfile != tdest:
                                shutil.move(dfile, ret)
                            else:
                                self.items_skipped += "{}\nExactly the same file:\n{}\n------------\n".format(dfile, "Skipped")
                    except Exception as E:
                        self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))
                # 2 overwrite
                elif self.atype == 2:
                    try:
                        if dfile != tdest:
                            if action == 1:
                                shutil.copy2(dfile, tdest, follow_symlinks=False)
                            elif action == 2:
                                shutil.move(dfile, tdest)
                        else:
                            self.items_skipped += "{}\nExactly the same file:\n{}\n------------\n".format(dfile, "Skipped")
                    except Exception as E:
                        self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))
                # 4 backup the existent file at destination 
                elif self.atype == 4:
                    if USE_DATE:
                        ret = self.faddSuffix2(commSfx, tdest)
                    else:
                        ret = self.faddSuffix(tdest)
                    try:
                        if dfile != tdest:
                            shutil.move(tdest, ret)
                            if action == 1:
                                shutil.copy2(dfile, tdest, follow_symlinks=False)
                            elif action == 2:
                                shutil.move(dfile, tdest)
                        else:
                            shutil.copy2(dfile, ret, follow_symlinks=False)
                    except Exception as E:
                        self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))
                # 5 ignore
                elif self.atype == 5:
                    pass
            # it doesnt exist at destination
            else:
                # if broken link rename
                if os.path.islink(tdest):
                    try:
                        ret = ""
                        if USE_DATE:
                            ret = self.faddSuffix2(commSfx, tdest)
                        else:
                            ret = self.faddSuffix(tdest)
                        shutil.move(tdest, ret)
                    except Exception as E:
                        self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))
                #
                try:
                    if action == 1:
                        shutil.copy2(dfile, tdest, follow_symlinks=False)
                    elif action == 2:
                        shutil.move(dfile, tdest)
                except Exception as E:
                    self.items_skipped += "{}\n{}\n------------\n".format(dfile, str(E))


# main dialog
class CopyDialog(Gtk.Window):
    def __init__(self, destpath, list_data, window, flag):
        # the destination path
        self.destpath = destpath
        # the data passed
        self.list_data = list_data
        self.window = window
        #
        self.data = unquote(self.list_data.decode()).split("\n")
        #
        # the operation to perform: copy - cut - link
        self.CONACT = self.data[0]
        # the list of all items
        self.list_items = []
        for item in self.data[1:]:
            self.list_items.append(item[7:])
        #
        if self.list_items == []:
            self.generic_dialog("Message", "No items.")
            return
        #
        # one item can be renamed within this module
        if len(self.list_items) == 1:
            rett = self.one_item_rename()
            if rett == 1:
                # empty
                self.list_items = []
                return
            elif rett == -6:
                return
        #
        # the copying dialog can be closed: 0 yes - 1 no
        self.can_close = 0
        #
        Gtk.Window.__init__(self, title="")
        self.set_transient_for(window)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_skip_taskbar_hint(True)
        self.set_modal(True)
        self.set_size_request(500, 100)
        self.set_border_width(10)
        self.connect ('delete-event', self.devnt)
        
        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox1)
        
        # self.label1 = Gtk.Label(label="1")
        # vbox1.add(self.label1)
        self.nlabel = Gtk.Label(label="")
        vbox1.pack_start(self.nlabel, True, True, 0)
        self.nlabel.set_line_wrap(True)
        self.nlabel.set_line_wrap_mode(2)
        # self.label = Gtk.Label(label="3")
        # vbox1.add(self.label)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox1.add(vbox)
        self.button3 = Gtk.Button(ICCANCEL)
        self.button3.connect("clicked", self.on_cancel)
        vbox1.add(self.button3)
        self.button4 = Gtk.Button(ICCLOSE)
        self.button4.connect("clicked", self.on_close)
        self.button4.set_sensitive(False)
        vbox1.add(self.button4)
        #
        # check if at least one item is at destination with the same name
        if self.list_items:
            ret = self.check_item_dest()
            if ret == 0:
                return
            else:
                self.can_close = 1
        # the report - self.items_skipped
        self.freport = []
        #
        self.signal = SignalObject()
        self.signal.connect("notify::propInt", self.on_notify_foo_int)
        self.signal.connect("notify::propList", self.on_notify_foo_list)
        self.signal.connect("notify::propName", self.on_notify_foo)
        thread = cThread(self.signal, self.list_items, self.CONACT, self.destpath, ret)
        thread.start()
        #
        self.show_all()


    def on_notify_foo_int(self, obj, gparamstring):
        # -2 all tasks finished, -1 tasks interrupted by the user
        ret_sig = self.signal.propInt
        
        if ret_sig == -2:
            self.button3.set_sensitive(False)
            self.button4.set_sensitive(True)
            self.nlabel.set_text("Done")
            self.can_close = 0
            return
        # -1 tasks interrupted by the user
        elif ret_sig == -1:
            self.button3.set_sensitive(False)
            self.button4.set_sensitive(True)
            self.nlabel.set_text("Interrupted")
            self.can_close = 0
            return
    
    def on_notify_foo_list(self, obj, gparamstring):
        self.freport = self.signal.propList
        
    def on_report(self):
        if self.freport:
            # get the new name from the dialog
            winr = gDialog(self, self.freport[0], self.window)
            response = winr.run()
            if response == Gtk.ResponseType.OK:
                winr.destroy()
            else:
                winr.destroy()

    
    def on_notify_foo(self, obj, gparamstring):
        # -2 all tasks finished, -1 tasks interrupted by the user
        #ret_sig = self.signal.propInt
        ret_sig_name = self.signal.propName
        self.nlabel.set_text(os.path.basename(str(ret_sig_name)))
    
    #
    def on_cancel(self, widget):
        self.signal.propInt = -1
        self.can_close = 0
        
    #
    def on_close(self, widget):
        self.on_report()
        self.close()
    
    #
    def devnt(self, widget, event):
        return self.can_close
    
    # check if at least one item is at destination with the same name
    # a choises will be asked
    def check_item_dest(self):
        # 6 means no same filename at destination
        ret = 6
        for item in self.list_items:
            name_item = os.path.basename(item)
            dest_path = os.path.join(self.destpath, name_item)
            # exists or broken link
            if os.path.exists(dest_path) or os.path.islink(dest_path):
                ret = self.on_name_choise()
                break
        return ret
            
    
    # only for one item
    def one_item_rename(self):
        NAME = os.path.basename(self.list_items[0])
        new_dest_name = os.path.join(self.destpath, NAME)
        
        # folder skipped (both must be folder)
        if os.path.isdir(self.list_items[0]):
            if os.path.isdir(new_dest_name):
                return
        
        if os.path.exists(new_dest_name):
        
            ret = self.on_new_name("The name", NAME, "already exists.")
            if ret == -6:
                return ret
            #
            while os.path.exists(os.path.join(os.path.dirname(self.list_items[0]), ret)):
                ret = self.on_new_name("The name", ret, "already exists.")
                if ret == -6:
                    return ret
            #
            npath = os.path.join(self.destpath, ret)
            try:
                shutil.copy2(self.list_items[0], npath, follow_symlinks=False)
            except Exception as E:
                self.generic_dialog("Error", str(E))
            
            # the item has been renamed
            return 1
        else:
            return 0

    
    # generic dialog
    def generic_dialog(self, message1, message2):
        dialog = Gtk.MessageDialog(parent=self.window, 
                                   modal=0, 
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK, 
                                   text=message1)
        dialog.set_default_size(1, 1)
        dialog.format_secondary_text("{}".format(message2))
        dialog.show_all()
        
        dialog.run()
        dialog.destroy()

    
    #
    def on_name_choise(self):
        RET = None
        win3 = DialogChoose(self, self.window)
        response = win3.run()
        if response == Gtk.ResponseType.CANCEL:
            RET = win3.VALUE
            win3.destroy()
        else:
            RET = 0
            win3.destroy()
        return RET


    def on_new_name(self, message1, ndata, message2):
        NEW_NAME = None
        # get the new name from the dialog
        win2 = DialogRename(self, message1, ndata, message2, self.window)
        response = win2.run()
        if response == Gtk.ResponseType.OK:
            NEW_NAME = win2.entry.get_text()
            win2.destroy()
        else:
            NEW_NAME = -6
            win2.destroy()
        return NEW_NAME


# dialogo di scelta se un elemento con lo stesso nome esiste a destinazione
class DialogChoose(Gtk.Dialog):
    def __init__(self, parent, window):
        
        Gtk.Dialog.__init__(self, title="", transient_for=window, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL
        )
        self.set_default_size(100, 100)
        
        # return value
        self.VALUE = 0
        
        box = self.get_content_area()
        message1 = "An item with the same name already exists."
        label1 = Gtk.Label(label="\n{}\n".format(message1))
        box.add(label1)
        
        self.bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.add(self.bbox)
        
        self.button1 = Gtk.Button(label="AUTOMATIC")
        self.button1.set_tooltip_text("Make a backup adding a suffix")
        self.button1.connect("clicked", self.on_button1)
        self.bbox.add(self.button1)
        
        self.button2 = Gtk.Button(label="OVERWRITE AND MERGE")
        self.button2.set_tooltip_text("Folders will be merged")
        self.button2.connect("clicked", self.on_button2)
        self.bbox.add(self.button2)
        
        # self.button3 = Gtk.Button(label="RENAME AND MERGE")
        # self.button3.set_tooltip_text("Files will be renamed, Folders will be merged")
        # self.button3.connect("clicked", self.on_button3)
        # self.bbox.add(self.button3)
        
        self.button4 = Gtk.Button(label="BACKUP AND MERGE")
        self.button4.set_tooltip_text("The same items at destination will be renamed\nFolders will be merged")
        self.button4.connect("clicked", self.on_button4)
        self.bbox.add(self.button4)
        
        self.button5 = Gtk.Button(label="IGNORE")
        self.button5.set_tooltip_text("Items will be ignored")
        self.button5.connect("clicked", self.on_button5)
        self.bbox.add(self.button5)
        
        self.show_all()
        
    def on_enter(self, entry):
        self.response(Gtk.ResponseType.CANCEL)

    def on_button1(self, widget):
        self.VALUE = 1
        self.response(Gtk.ResponseType.CANCEL)
    
    def on_button2(self, widget):
        self.VALUE = 2
        self.response(Gtk.ResponseType.CANCEL)
    
    # def on_button3(self, widget):
        # self.VALUE = 3
        # self.response(Gtk.ResponseType.CANCEL)
    
    def on_button4(self, widget):
        self.VALUE = 4
        self.response(Gtk.ResponseType.CANCEL)
    
    def on_button5(self, widget):
        self.VALUE = 5
        self.response(Gtk.ResponseType.CANCEL)


class DialogRename(Gtk.Dialog):
    def __init__(self, parent, message1, nname, message2, window):
        
        Gtk.Dialog.__init__(self, title=IENTERNEWNAME, transient_for=window, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        self.set_default_size(700, 100)

        label1 = Gtk.Label("\n{}:".format(message1))
        label2 = Gtk.Label("{}\n{}".format(nname, message2))
        self.entry = Gtk.Entry()
        self.entry.connect("activate", self.on_enter)
        self.entry.set_text(nname)
        box = self.get_content_area()
        box.add(label1)
        box.add(label2)
        box.add(self.entry)
        self.show_all()

    def on_enter(self, entry):
        self.response(Gtk.ResponseType.OK)


class gDialog(Gtk.Dialog):
    def __init__(self, parent, message, window):
        Gtk.Dialog.__init__(self, title="REPORT", transient_for=window, flags=0)
        self.add_buttons(
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        self.set_default_size(500, 400)
        
        self.box = self.get_content_area()
        
        self.create_textview(message)
        
        self.show_all()
        
    
    def on_enter(self, entry):
        self.response(Gtk.ResponseType.OK)

    def create_textview(self, message):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.box.add(scrolledwindow)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(message)
        scrolledwindow.add(self.textview)
        
