#!/usr/bin/env python3
"""
trash module
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, Pango, GObject
from gi.repository.GdkPixbuf import Pixbuf
import os
import sys
from urllib.parse import unquote, quote
import shutil
import time
import getpass

from cfg import *

try:
    from functions import compare as ccompare
    from functions import dcompare
except:
    pass

# language module
from lang import *

HOME = os.getenv("HOME")

USER = getpass.getuser()
USER_UID = os.getuid()

TRASH_FOLDER = os.path.join(HOME, ".local/share/Trash")
TRASH_FOLDER_FILES = os.path.join(TRASH_FOLDER, "files")
TRASH_FOLDER_INFO = os.path.join(TRASH_FOLDER, "info")

tmodel = object

ICON_SIZE = ICON_SIZE2
LINK_SIZE = LINK_SIZE2
THUMB_SIZE = THUMB_SIZE2

class TrashItems():
    def __init__(self):
        self.mountpoint = ""
        self.fakename = ""
        self.realname = ""
        self.deletiondate = ""


class CellRenderer(Gtk.CellRendererPixbuf):
    pixbuflink = GObject.property(type=str, default="")
    pixbufaccess = GObject.property(type=str, default="")
    
    def __init__(self):
        super().__init__()
        self.set_fixed_size(THUMB_SIZE2+2, THUMB_SIZE2+2)
        
    def do_render(self, cr, widget, background_area, cell_area, flags):
        
        x_offset = cell_area.x 
        y_offset = cell_area.y
        
        PPIXBUF = self.props.pixbuf
        
        xadd = 0
        if PPIXBUF.get_width() < cell_area.width:
            xadd = (cell_area.width - PPIXBUF.get_width())/2
        yadd = 0
        if PPIXBUF.get_height() < cell_area.height:
            yadd = (cell_area.height - PPIXBUF.get_height())
        pixbufimage = PPIXBUF
        Gdk.cairo_set_source_pixbuf(cr, pixbufimage, x_offset+xadd, y_offset+yadd)
        #
        cr.paint()
        
        xpad = cell_area.width-10
        ypad = THUMB_SIZE2-LINK_SIZE2
        
        if self.pixbuflink == "True":
            pixbuf11 = Gtk.IconTheme.get_default().load_icon("emblem-symbolic-link", LINK_SIZE2, 0)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf11, cell_area.x+xpad-LINK_SIZE2, y_offset+ypad)
            cr.paint()
        
        if self.pixbufaccess == "False":
            pixbuf12 = Gtk.IconTheme.get_default().load_icon("emblem-readonly", LINK_SIZE2, 0)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf12, cell_area.x+10, y_offset+ypad)
            cr.paint()

class CellArea(Gtk.CellAreaBox):
    
    def __init__(self):
        super().__init__()
        
        renderer_thumb = CellRenderer()
        self.pack_start(renderer_thumb, False, False, 0)
        self.attribute_connect(renderer_thumb, "pixbuf", 0)
        self.attribute_connect(renderer_thumb, "pixbuflink", 5)
        self.attribute_connect(renderer_thumb, "pixbufaccess", 6)
        
        renderer = Gtk.CellRendererText()
        renderer.props.xalign = 0.5
        renderer.props.yalign = 0
        renderer.props.wrap_width = 15
        renderer.props.wrap_mode = 1
        self.pack_end(renderer, True, True, 0)
        self.add_attribute(renderer, 'text', 1)
        
        if TR_DATE == 1:
            renderer1 = Gtk.CellRendererText()
            self.pack_end(renderer1, False, False, 0)
            renderer1.props.xalign = 0.5
            renderer1.props.yalign = 0
            renderer1.props.wrap_width = 15
            renderer1.props.wrap_mode = 1
            renderer1.props.style = 1
            self.add_attribute(renderer1, 'text', 9)


class wtrash():
    def __init__(self, window):
        self.window = window
        # the main notebook from the main module
        self.notebook = window.notebook
        IVBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # scrolled window
        scrolledwindow = Gtk.ScrolledWindow()
        IVBox.add(scrolledwindow)
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        scrolledwindow.set_policy(Gtk.PolicyType.NEVER,  Gtk.PolicyType.AUTOMATIC)
        
        # iconview
        self.iconview = Gtk.IconView.new_with_area(CellArea())
        scrolledwindow.add(self.iconview)
        self.iconview.set_item_width(IV_ITEM_WIDTH)
        #item icon - item name - is_folder - working_dir - is_hidden - is_link - access - mountpoint - fake name - deletion date
        # 
        self.model = Gtk.ListStore(Pixbuf, str, str, str, str, str, str, str, str, str)
        global tmodel
        tmodel = self.model
        
        if TR_SORT == 0:
            self.model.set_sort_func(2, ccompare, None)
            self.model.set_sort_column_id(2, Gtk.SortType.ASCENDING)
        elif TR_SORT == 1:
            self.model.set_sort_func(10, dcompare, None)
            self.model.set_sort_column_id(10, Gtk.SortType.ASCENDING)
        elif TR_SORT == 2:
            self.model.set_sort_func(10, dcompare, None)
            self.model.set_sort_column_id(10, Gtk.SortType.DESCENDING)
        self.iconview.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.iconview.set_model(self.model)
        ########
        lpartitions = ["/"]
        self.lista = self.trashed_items(lpartitions)
        
        # items from trashinfos
        for elem in self.lista:
            # mount point - /
            mmountp = elem.mountpoint
            # fake name
            ritem = elem.fakename
            # real name with full path
            iitem = elem.realname
            # real path only
            wpath = os.path.dirname(iitem)
            # real name only
            ffile = os.path.basename(iitem)
            # deletion date
            ddate_d, ddate_t = elem.deletiondate.split("T")
            ddate = ddate_d+" "+ddate_t
            #
            self.populate_view(mmountp, ritem, wpath, ffile, ddate)
        
        ## add items that dont have associated trashinfo files for some reasons
        ck_orphan_items_temp = os.listdir(TRASH_FOLDER_FILES)
        ck_orphan_items = []
        for item in ck_orphan_items_temp:
            for row in self.model:
                if row[1] == item:
                    ck_orphan_items.append(item)
                    break
        #
        orphan_items = []
        for item in ck_orphan_items_temp:
            if item not in ck_orphan_items:
                orphan_items.append(item)
        # add them to the view
        for item in orphan_items:
            ddate = TIFILEMD
            self.populate_view("/", item, HOME, item, ddate)
        #
        #### NOTEBOOK2
        notebook2 = Gtk.Notebook()
        notebook2.set_scrollable(True)
            # notebook 2 - page 1
        pagen = Gtk.Box()
        # INFO BOX
        self.npmainbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        pagen.add(self.npmainbox)
        # find the stock icon
        self.infoimage = Gtk.Image.new_from_pixbuf(Gtk.IconTheme.get_default().load_icon("user-trash", NB2_ICON_SIZE, 0))
        self.npmainbox.pack_start(self.infoimage, False, False, 20)
        grid301 = Gtk.Grid()
        grid301.set_row_spacing(5)
        # labels for names
            # number of items find and name of item
        self.label300name = Gtk.Label("")
        grid301.attach(self.label300name, 0, 0, 1, 1)
        self.label300name.props.xalign = 1
        self.label300name.props.valign = 1
            # nothing and path of the selected item
        self.label300path = Gtk.Label("")
        grid301.attach(self.label300path, 0, 1, 1, 1)
        self.label300path.props.xalign = 1
        self.label300path.props.valign = 1
            # nothing and type of the selected item
        self.label300type = Gtk.Label("")
        grid301.attach(self.label300type, 0, 2, 1, 1)
        self.label300type.props.xalign = 1
        self.label300type.props.valign = 1
            # nothing and size of the selected item
        self.label300size = Gtk.Label("")
        grid301.attach(self.label300size, 0, 3, 1, 1)
        self.label300size.props.xalign = 1
        self.label300size.props.valign = 1
            # nothing and deletion date of the selected item
        self.label300date = Gtk.Label("")
        if TR_DATE == 0:
            grid301.attach(self.label300date, 0, 4, 1, 1)
            self.label300date.props.xalign = 1
            self.label300date.props.valign = 1
            #
        self.label301name = Gtk.Label("")
        grid301.attach(self.label301name, 1, 0, 1, 1)
        self.label301name.props.xalign = 0
        self.label301name.set_selectable(True)
        self.label301name.set_line_wrap(True)
        self.label301name.set_line_wrap_mode(1)
            #
        self.label302path = Gtk.Label("")
        grid301.attach(self.label302path, 1, 1, 1, 1)
        self.label302path.props.xalign = 0
        self.label302path.set_selectable(True)
        self.label302path.set_line_wrap(True)
            #
        self.label303type = Gtk.Label("")
        grid301.attach(self.label303type, 1, 2, 1, 1)
        self.label303type.props.xalign = 0
        self.label303type.set_line_wrap(True)
        self.label303type.set_line_wrap_mode(1)
            #
        self.label304size = Gtk.Label("")
        grid301.attach(self.label304size, 1, 3, 1, 1)
        self.label304size.props.xalign = 0
            #
        self.label304date = Gtk.Label("")
        if TR_DATE == 0:
            grid301.attach(self.label304date, 1, 4, 1, 1)
            self.label304date.props.xalign = 0
        ###
        self.brd = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.npmainbox.pack_end(self.brd, False, False, 5)
        # fake
        fklabel = Gtk.Label(label="")
        self.brd.add(fklabel)
        # button restore
        self.button_restore = Gtk.Button(TRESTORE)
        self.brd.add(self.button_restore)
        self.button_restore.set_size_request(-1, HTB_SSR)
        # button delete
        self.button_delete = Gtk.Button(TDELETE)
        self.brd.add(self.button_delete)
        self.button_delete.set_size_request(-1, HTB_SSR)
        
        grid301.props.halign = 1
        grid301.props.valign = 3
        grid301.props.hexpand = True
        self.npmainbox.pack_end(grid301, True, True, 5)
        
        try:
            notebook2.remove_page(0)
        except:
            pass
        self.npmainbox.show()
        labelinfo = Gtk.Label()
        labelinfo.set_markup("<span size='small'>"+INFO_NAME+"</span>")
        #
        notebook2.append_page(pagen, labelinfo) 
        notebook2.show_all()
        self.button_restore.hide()
        self.button_delete.hide()
        #### NOTEBOOK2 END
        
        ## create the notebook page
        page = Gtk.Box()
        page.set_orientation(orientation=Gtk.Orientation.VERTICAL)
        page.show()
        page.pack_start(IVBox, True, True, 0)
        page.add(notebook2)

        ############

        # CREATE LABEL FOR THE PAGE
        lbox = Gtk.Box()
        lbox.set_orientation(orientation=Gtk.Orientation.HORIZONTAL)
        label200h = Gtk.Label("hTrash")
        lbox.pack_start(label200h, False, False, 0)
        label200h.hide()
        label200 = Gtk.Label(TLABEL)
        label200.set_hexpand(True)
        label200.set_justify(Gtk.Justification.CENTER)
            # add image to close button
        image = Gtk.Image(stock=Gtk.STOCK_CLOSE)
        buttonclose = Gtk.Button()
        buttonclose.set_image(image)
        buttonclose.set_relief(Gtk.ReliefStyle.NONE)
        buttonclose.connect("clicked", self.on_buttonclose_clicked, page)
        lbox.pack_start(label200, True, True, 0)
        lbox.add(buttonclose)
        label200.show()
        buttonclose.show()
            # add the page to the notebook
        self.notebook.append_page(page, lbox)
        self.notebook.set_tab_reorderable(page, True)
        #
        numpage = self.notebook.get_n_pages()
        if numpage > 1:
            self.notebook.set_show_tabs(True)
        elif numpage == 1:
            self.notebook.set_show_tabs(False)
        # last page is shown
        self.notebook.set_current_page(numpage-1)
        ########
        ## single click on item
        self.iconview.connect("selection-changed", self.on_selection_changed_trash)
        # double click on item
        self.iconview.connect("item-activated", self.on_double_click_trash)
        #
        self.iconview.connect("unselect-all", self.on_unselect_all_trash)
        #
        self.button_restore.connect("clicked", self.on_button_restore) 
        self.button_delete.connect("clicked", self.on_button_delete) 
        #
        IVBox.show_all()
        # only one trash tab can be open
        self.window.IS_TRASH_OP = 1
        #
        ## trash directory monitor - the files
        if TR_UPD:
            self.monitor_dir(TRASH_FOLDER_FILES)

    # populate this module view by the trashinfo files
    def populate_view(self, mmountp, ritem, wpath, ffile, ddate):
        # only the home dir
        if wpath[0:5] == "/home":
            # check if the item exists in TRASH_FOLDER_FILES
            if not os.path.exists(os.path.join(TRASH_FOLDER_FILES, ritem)):
                return
            
            # check the access of the item
            file_acc = None
            if os.access(TRASH_FOLDER_FILES+"/"+ritem, os.W_OK) == False:
                file_acc = "False"
            
            # if broken link
            if os.path.islink(TRASH_FOLDER_FILES+"/"+ritem) and not os.path.exists(os.readlink(TRASH_FOLDER_FILES+"/"+ritem)):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file("empty.svg")
                self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
            # if link
            elif os.path.islink(TRASH_FOLDER_FILES+"/"+ritem):
                # if dir
                if os.path.isdir(TRASH_FOLDER_FILES+"/"+ritem):
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "a", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                # if file
                elif os.path.isfile(TRASH_FOLDER_FILES+"/"+ritem):
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                # if else
                else:
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
            # if dir
            elif os.path.isdir(TRASH_FOLDER_FILES+"/"+ritem):
                pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                self.model.append([pixbuf, ffile, "a", wpath, "False", None, file_acc, mmountp, ritem, ddate])
            # if file
            elif os.path.isfile(TRASH_FOLDER_FILES+"/"+ritem):
                pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                self.model.append([pixbuf, ffile, "b", wpath, "False", None, file_acc, mmountp, ritem, ddate])
            # if other kind of item
            else:
                pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                self.model.append([pixbuf, ffile, "b", wpath, "False", None, file_acc, mmountp, ritem, ddate])
    
################ trash folder monitor

    # start a monitor
    def monitor_dir(self, path):
        gio_dir = Gio.File.new_for_path(path)
        self.monitor = gio_dir.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        # 
        self.monitor.props.rate_limit = 100
        self.monitor.connect("changed", self.dir_changed)
    
    # the monitor
    def dir_changed(self, monitor, file, other_file, event):
        ## the item has been restored or deleted
        if event == Gio.FileMonitorEvent.MOVED_OUT or event == Gio.FileMonitorEvent.DELETED:
            name_file = os.path.basename(file.get_path())
            for row in self.model:
                if row[8] == name_file:
                    self.model.remove(row.iter)
        ## - an item has been moved into the trashcan
        elif event == Gio.FileMonitorEvent.MOVED_IN:
            name_file = os.path.basename(file.get_path())
            #### add the item in the list of items
            ret = 0
            info_path = TRASH_FOLDER_INFO+"/"+name_file+".trashinfo"
            iit = 0
            got_info = 0
            ret = os.path.exists(info_path)
            # check three times the trashinfo
            while ret == False:
                iit += 1
                time.sleep(0.5)
                if iit == 3:
                    break
            else:
                got_info = 1
                with open(info_path, 'r') as ii:
                    # first line
                    ii.readline()
                    # second line
                    second_ii = unquote(ii.readline()).rstrip()
                    if second_ii[0:5] == "Path=":
                        path_line = second_ii[5:]
                    elif second_ii[0:14] == "DeletionDate=":
                        date_line = second_ii[14:]
                    # third line
                    third_ii = unquote(ii.readline()).rstrip()
                    if third_ii[0:5] == "Path=":
                        path_line = third_ii[5:]
                    elif third_ii[0:13] == "DeletionDate=":
                        date_line = third_ii[13:]
                    #
                    diskpart = TrashItems()
                    diskpart.mountpoint = "/home"
                    diskpart.fakename = name_file
                    diskpart.realname = path_line
                    diskpart.deletiondate = date_line
                    self.lista.append(diskpart)
                    
                    ret = 0
            
            ##### add the item in self.model
            # only home dir
            if file.get_path()[0:5] == "/home":
                # no trashinfo no some infos
                if got_info == 0:
                    ddate = TIFILEMD
                    # realname cannot be get
                    ffile = os.path.basename(file.get_path())
                    #
                    wpath = HOME
                else:
                    for item in self.lista:
                        # cancel date 
                        ddate_a, ddate_b = item.deletiondate.split("T")
                        ddate = ddate_a+" "+ddate_b
                        # realname
                        ffile = os.path.basename(item.realname)
                        # real path
                        wpath = os.path.dirname(item.realname)
                # only /home is supported
                mmountp = "/"
                # fakename
                ritem = name_file
                # check the access of the item
                file_acc = None
                #
                if os.access(TRASH_FOLDER_FILES+"/"+ritem, os.W_OK) == False:
                    file_acc = "False"
                
                # if broken link
                if os.path.islink(TRASH_FOLDER_FILES+"/"+ritem) and not os.path.exists(os.readlink(TRASH_FOLDER_FILES+"/"+ritem)):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file("empty.svg")
                    self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                # if link
                elif os.path.islink(TRASH_FOLDER_FILES+"/"+ritem):
                    # if dir
                    if os.path.isdir(TRASH_FOLDER_FILES+"/"+ritem):
                        pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                        self.model.append([pixbuf, ffile, "a", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                    # if file
                    elif os.path.isfile(TRASH_FOLDER_FILES+"/"+ritem):
                        pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                        self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                    # other
                    else:
                        pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                        self.model.append([pixbuf, ffile, "b", wpath, "False", "True", file_acc, mmountp, ritem, ddate])
                # if dir
                elif os.path.isdir(TRASH_FOLDER_FILES+"/"+ritem):
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "a", wpath, "False", None, file_acc, mmountp, ritem, ddate])
                # if file
                elif os.path.isfile(TRASH_FOLDER_FILES+"/"+ritem):
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "b", wpath, "False", None, file_acc, mmountp, ritem, ddate])
                # other kind of item
                else:
                    pixbuf = self.evaluate_pixbuf(os.path.join(TRASH_FOLDER_FILES, ritem), ICON_SIZE2)
                    self.model.append([pixbuf, ffile, "b", wpath, "False", None, file_acc, mmountp, ritem, ddate])

    # stop a monitor
    def monitor_stop(self):
        self.monitor_dir.cancel()
        
########################
    
    # double click on an item open it - only files
    def on_double_click_trash(self, iconview, treepath):
        
        if self.model[treepath][2] == "b":
            path = ""
            if self.model[treepath][7] == "/":
                path = os.path.join(TRASH_FOLDER_FILES, self.model[treepath][8])
            #
            uri = "file://"+path
            ret = Gio.app_info_launch_default_for_uri(uri, None)
            #
            if ret == False:
                self.generic_dialog(IERROR2, path)
        
    def on_selection_changed_trash(self, iconview):
        #
        self.button_restore.show()
        self.button_delete.show()
        #
        if len(iconview.get_selected_items()) == 1:
            rrow = iconview.get_selected_items()[0]
            self.npmainbox.remove(self.npmainbox.get_children()[0])
            item_path = ""
            item_mime = ""
            #
            if self.model[rrow][7] == "/":
                #
                item_path = os.path.join(TRASH_FOLDER_FILES, self.model[rrow][8])
                item_mime = self.item_mime(item_path)
            #
            isize = ""
            if self.model[rrow][2] == "a":
                isize = self.folder_size(item_path)
            elif self.model[rrow][2] == "b":
                isize = self.file_size(item_path)
            #
            idate = self.model[rrow][9]
            #
            infopixbuf = self.model[rrow][0]
            infoimage = Gtk.Image.new_from_pixbuf(infopixbuf)
            self.npmainbox.pack_start(infoimage, False, False, 20)
            infoimage.show()
            self.label300name.set_markup("<i>"+TNAME+"</i>")
            self.label301name.set_label("{}".format(self.model[rrow][1]))
            self.label300path.set_markup("<i>"+TPATH+"</i>")
            self.label302path.set_label("{}".format(self.model[rrow][3]))
            self.label300type.set_markup("<i>"+TTYPE+"</i>")
            self.label303type.set_label("{}".format(item_mime))
            self.label300size.set_markup("<i>"+TSIZE+"</i>")
            self.label304size.set_label("{}".format(isize))
            self.label300date.set_markup("<i>"+TDATE+"</i>")
            self.label304date.set_label("{}".format(idate))
        #
        elif len(iconview.get_selected_items()) > 1:
            self.npmainbox.remove(self.npmainbox.get_children()[0])
            infoimage = Gtk.Image.new_from_pixbuf(Gtk.IconTheme.get_default().load_icon("user-trash", NB2_ICON_SIZE, 0))
            self.npmainbox.pack_start(infoimage, False, False, 20)
            infoimage.show()
            self.label300name.set_label("")
            self.label301name.set_label("")
            self.label300path.set_label("")
            self.label302path.set_label(TSELITEM+str(len(iconview.get_selected_items())))
            self.label300type.set_label("")
            self.label303type.set_label("")
            self.label300size.set_label("")
            self.label304size.set_label("")
            self.label300date.set_label("")
            self.label304date.set_label("")

        elif len(iconview.get_selected_items()) == 0:
            self.button_restore.hide()
            self.button_delete.hide()
            self.unselect_all_common_trash(iconview)

    # when CTRL+ALT+A 
    def on_unselect_all_trash(self, iconview):
        self.unselect_all_common_trash(iconview)
    
    # the common part of the two functions above
    def unselect_all_common_trash(self, iconview):
        iconview.unselect_all()
        self.npmainbox.remove(self.npmainbox.get_children()[0])
        infoimage = Gtk.Image.new_from_pixbuf(Gtk.IconTheme.get_default().load_icon("user-trash", NB2_ICON_SIZE, 0))
        self.npmainbox.pack_start(infoimage, False, False, 20)
        infoimage.show()
        self.label300name.set_label("")
        self.label301name.set_label("")
        self.label300path.set_label("")
        self.label302path.set_label("")
        self.label300type.set_label("")
        self.label303type.set_label("")
        self.label300size.set_label("")
        self.label304size.set_label("")
        self.label300date.set_label("")
        self.label304date.set_label("")

    def folder_size(self, path):
        if os.path.islink(path):
            return TLINK
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if not os.path.exists(flp):
                    continue
                total_size += os.path.getsize(flp)
         
        if total_size == 0 or total_size == 1:
            total_size = str(total_size)+" byte"
        elif total_size//1024 == 0:
            total_size = str(total_size)+" bytes"
        elif total_size//1048576 == 0:
            total_size = str(round(total_size/1024, 3))+" KB"
        elif total_size//1073741824 == 0:
            total_size = str(round(total_size/1048576, 3))+" MB"
        elif total_size//1099511627776 == 0:
            total_size = str(round(total_size/1073741824, 3))+" GiB"
        else:
            total_size = str(round(total_size/1099511627776, 3))+" GiB"
        
        return total_size

    #  find the size of selected item
    def file_size(self, path):
        if os.path.islink(path):
            return TLINK
        # calculate the size of the file
        try:
            fsize2 = os.path.getsize(path)
        except:
            fsize2 = 0
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1073741824 == 0:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize
    
    # find the mimetype of selected item
    def item_mime(self, path):
        imime = ''
        try:
            file = Gio.File.new_for_path(path)
            file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
            ftype = Gio.FileInfo.get_content_type(file_info)
            imime = ftype
        except:
            pass
        return imime

    # close button in page of notebook1
    def on_buttonclose_clicked(self, buttonclose, page):
        self.iconview.unselect_all()
        curpage = self.notebook.page_num(page)
        numpage = self.notebook.get_n_pages()
        if numpage > 1:
            page.destroy()
        
        if (numpage - 1) == 1:
            self.notebook.set_show_tabs(False)
        
        self.window.IS_TRASH_OP = 0
        
        global tmodel
        tmodel.clear()
        
    def trashed_items(self, lpartitions):
        
        list_fakereal = []
        
        for tpath in lpartitions:
            if tpath == "/":
                if os.access(TRASH_FOLDER, os.R_OK):
                    files_path = os.path.join(TRASH_FOLDER, "files")
                    info_path = os.path.join(TRASH_FOLDER, "info")
                    info_items = os.listdir(info_path)
                    for iitem in info_items:
                        with open(os.path.join(info_path, iitem), 'r') as ii:
                            # first line
                            ii.readline()
                            # second line
                            second_ii = unquote(ii.readline()).rstrip()
                            if second_ii[0:5] == "Path=":
                                path_line = second_ii[5:]
                            elif second_ii[0:14] == "DeletionDate=":
                                date_line = second_ii[14:]
                            # third line
                            third_ii = unquote(ii.readline()).rstrip()
                            if third_ii[0:5] == "Path=":
                                path_line = third_ii[5:]
                            elif third_ii[0:13] == "DeletionDate=":
                                date_line = third_ii[13:]
                            #
                            spath = unquote(path_line).rstrip()
                            path = os.path.join(tpath, spath)
                            diskpart = TrashItems()
                            diskpart.mountpoint = tpath
                            diskpart.fakename = os.path.splitext(iitem)[0]
                            diskpart.realname = path
                            diskpart.deletiondate = date_line
                            list_fakereal.append(diskpart)
                #
                else:
                    self.generic_dialog("Error", "Trash not readable.")
        #
        return list_fakereal             

    # find the right pixbuf for all folder and file
    def evaluate_pixbuf(self, path, iicon_size):
        if not os.path.exists(path):
            return
        #
        f = Gio.file_new_for_path(path)
        info = f.query_info(Gio.FILE_ATTRIBUTE_STANDARD_ICON,
                    Gio.FileQueryInfoFlags.NONE, None)
        gicon = info.get_icon()
        #####
        if path:
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(gicon.get_names()[0], iicon_size, 0)
                return pixbuf
            except:
                try:
                    pixbuf = Gtk.IconTheme.get_default().load_icon(gicon.get_names()[1], iicon_size, 0)
                    return pixbuf
                except:
                    pass
                    if os.path.isdir(path):
                        pixbuf = Gtk.IconTheme.get_default().load_icon("folder", ICON_SIZE2, 0)   
                        return pixbuf
                    elif os.path.isfile(path):
                        pixbuf = Gtk.IconTheme.get_default().load_icon("empty", ICON_SIZE2, 0)   
                        return pixbuf
                    else:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("empty", ICON_SIZE2, 0)
                        return pixbuf
    
    def on_button_restore(self, button_restore):
        rrows = self.iconview.get_selected_items()
        
        dresponse = 0
        if rrows:
            dialog = DialogYN(self.window, "Message", TRESTOREMSG2)
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                dresponse = 1
                dialog.destroy()
            elif response == Gtk.ResponseType.CANCEL:
                dialog.destroy()
        
        if dresponse == 0:
            return
        
        for rrow in rrows:
            src = ""
            if self.model[rrow][7] == "/":
                src = os.path.join(TRASH_FOLDER_FILES, self.model[rrow][8])
            #
            dst = os.path.join(self.model[rrow][3], self.model[rrow][1])
            name_file = self.model[rrow][1]
            if os.path.exists(dst):
                nroot, suffix = os.path.splitext(name_file)
                new_name_file = ""
                ii = 1
                while ii:
                    if os.path.exists(os.path.join(self.model[rrow][3], nroot+"_("+str(ii)+")")):
                        ii += 1
                    else:
                        new_name_file = nroot+"_("+str(ii)+")"
                        ii = 0
                dst = os.path.join(self.model[rrow][3], new_name_file)
                rv = self.trash_restore(src, dst)
            else:
                rv = self.trash_restore(src, dst)
            if rv == dst:
                try:
                    if self.model[rrow][7] == "/":
                        info_path = os.path.join(TRASH_FOLDER_INFO, self.model[rrow][8])+".trashinfo"
                    #
                    os.remove(info_path)
                    iter = self.model.get_iter(rrow)
                    if TR_UPD == 0:
                        self.model.remove(iter)
                except Exception as e:
                    self.generic_dialog("", str(e))
            else:
                pass
    
    # restore the item from the program
    def on_button_delete(self, button_delete):
        rrows = self.iconview.get_selected_items()
        dresponse = 0
        if rrows:
            dialog = DialogYN(self.window, "Message", TDELETEMSG2)
            response = dialog.run()
            #
            if response == Gtk.ResponseType.OK:
                dresponse = 1
                dialog.destroy()
            elif response == Gtk.ResponseType.CANCEL:
                dialog.destroy()
        
        if dresponse == 0:
            return
        for rrow in rrows:
            ###
            file_path = ""
            if self.model[rrow][7] == "/":
                file_path = os.path.join(TRASH_FOLDER_FILES, self.model[rrow][8])
            #
            name_file = self.model[rrow][1]
            info_path = ""
            if self.model[rrow][7] == "/":
                info_path = os.path.join(TRASH_FOLDER_INFO, self.model[rrow][8])+".trashinfo"
            #
            try:
                os.remove(info_path)
                os.remove(file_path)
                if TR_UPD == 0:
                    iter = self.model.get_iter(rrow)
                    self.model.remove(iter)
            except Exception as e:
                self.generic_dialog("", str(e))

    # restore the item
    def trash_restore(self, src, dst):
        try:
            rv = shutil.move(src, dst)
            return rv
        except Exception as e:
            self.generic_dialog("", str(e))

    # check if the recycle bin is empty or not
    # on the trash tab it performs a global action on all partitions and volumes
    def trash_is_empty(notebook):
        #
        page_pos = notebook.get_current_page()
        curr_page = notebook.get_nth_page(page_pos)
        curr_tab_label = notebook.get_tab_label(curr_page)
        hlabel = curr_tab_label.get_children()[0].get_label()
        is_trash_empty = False
        llpartitions = ["/"]
        
        if hlabel == "hTrash":
            #
            for tpath in llpartitions:
                if tpath == "/":
                    if os.access(TRASH_FOLDER, os.R_OK):
                        files_path = os.path.join(TRASH_FOLDER, "files")
                        info_path = os.path.join(TRASH_FOLDER, "info")
                        if os.listdir(files_path):
                            is_trash_empty = True
        # if it is a custom tab
        elif hlabel == "CUSTOM":
            pass
        # if it is HOME
        elif hlabel[0:5] == "/home":
            for tpath in llpartitions:
                
                if os.access(os.path.join(tpath, TRASH_FOLDER), os.R_OK):
                    files_path = os.path.join(TRASH_FOLDER, "files")
                    info_path = os.path.join(TRASH_FOLDER, "info")
                    if os.listdir(files_path):
                        is_trash_empty = True
        return is_trash_empty

    ## called from mfm
    def request_empty_trash(notebook):
        # the current page of the notebook
        page_pos = notebook.get_current_page()
        curr_page = notebook.get_nth_page(page_pos)
        curr_tab_label = notebook.get_tab_label(curr_page)
        hlabel = curr_tab_label.get_children()[0].get_label()
        
        if hlabel == "hTrash":
            wtrash.trash_empty_all()
        # for custom tabs
        elif "WZCUSTOMWZ" in hlabel:
            return
        else:
            wtrash.partition_trash_empty(hlabel)
    
    ## used by function request_empty_trash
    def partition_trash_empty(tpath):
        
        ret = 0
        
        if tpath[0:5] == "/home":
            if os.access(TRASH_FOLDER, os.W_OK):
                files_path = os.path.join(TRASH_FOLDER, "files")
                info_path = os.path.join(TRASH_FOLDER, "info")
                ret = wtrash.ftrash_empty(files_path, info_path)
                wtrash.delete_from_model("/")

    # empty the recycle bin - all partitions
    def trash_empty_all():
        lpartitions = ["/"]
        #
        for tpath in lpartitions:
            if tpath == "/":
                files_path = os.path.join(TRASH_FOLDER, "files")
                info_path = os.path.join(TRASH_FOLDER, "info")
                ret = wtrash.ftrash_empty(files_path, info_path)
        #
        if TR_UPD == 0:
            global tmodel
            tmodel.clear()

    # empty the trashcan
    def ftrash_empty(trash_folder_files, trash_folder_info):
        ret = 1
        for ffile in os.listdir(trash_folder_files):
            ffile_path = os.path.join(trash_folder_files, ffile)
            if os.path.isfile(ffile_path) or os.path.islink(ffile_path):
                try:
                    os.unlink(ffile_path)
                except:
                    ret = -1
            elif os.path.isdir(ffile_path):
                try:
                    shutil.rmtree(ffile_path)
                except:
                    ret = -1
        
        for ffile in os.listdir(trash_folder_info):
            ffile_path = os.path.join(trash_folder_info, ffile)
            try:
                os.unlink(ffile_path)
            except:
                ret = -1

        return ret

    ## used in function partition_trash_empty
    # delete the item from the model
    # if the trash tab is open
    def delete_from_model(ttpath):
        if tmodel != object:
            for rrow in tmodel:
                if ttpath == rrow[7]:
                    tmodel.remove(rrow.iter)

    # generic dialog
    def generic_dialog(self, message1, message2):
        dialog = Gtk.MessageDialog(parent=self.window, 
                                   modal=0,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=message1)
        dialog.format_secondary_text("{}".format(message2))
        dialog.run()
        dialog.destroy()


# yes/no generic dialog
class DialogYN(Gtk.Dialog):
    def __init__(self, parent, title, msg):
        Gtk.Dialog.__init__(self, title=title, transient_for=parent, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.set_default_size(150, 100)

        label = Gtk.Label(label=msg)

        box = self.get_content_area()
        box.add(label)
        self.show_all()
