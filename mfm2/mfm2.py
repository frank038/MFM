#!/usr/bin/env python3
"""
main program - v 0.3
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, Gio, Pango, GObject
from gi.repository.GdkPixbuf import Pixbuf
import os
import sys
from stat import *
from urllib.parse import unquote, quote
import shutil
import stat
import time
import glob
import importlib
import subprocess
from stat import *
import threading
import datetime

# generic dialog
def generic_dialog(message1, message2):
    dialog = Gtk.MessageDialog(parent=None, modal=0, message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK, text=message1)
    dialog.format_secondary_text("{}".format(message2))
    dialog.run()
    dialog.destroy()

# config module
try:
    from cfg import *
except Exception as E:
    generic_dialog("Message", str(E))
    sys.exit()

if USE_THEME:
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-theme-name", USE_THEME)
    settings.set_property("gtk-application-prefer-dark-theme", USE_THEME_DARK)

if USE_ICONS:
    Gtk.Settings.get_default().set_property("gtk-icon-theme-name", USE_ICONS)

# language module
try:
    from lang import *
except Exception as E:
    generic_dialog("Message", str(E))
    sys.exit()

# external modules

try:
    import trash_module
except Exception as E:
    generic_dialog("Message", str(E))
    sys.exit()

# import optional custom modules
sys.path.append("modules_custom")
mmod_custom = glob.glob("modules_custom/*.py")
# list of the filenames
list_custom_modules_win = []
for el in reversed(mmod_custom):
    try:
        ee = importlib.import_module(os.path.basename(el)[:-3])
        list_custom_modules_win.append(ee)
    except ImportError as ioe:
        generic_dialog("Message", str(ioe))
# remove the alien modules
for el in list_custom_modules_win[:]:
    if el.mmodule_type() == 2:
        list_custom_modules_win.remove(el)

# home dir
HOME = os.getenv("HOME")

# 
WORKING_DIR = HOME

# global variable
wworking_dir = WORKING_DIR

starting_item = ""

if len(sys.argv) > 1:
    if sys.argv[1] == "-F":
        arg_item = " ".join(sys.argv[2:])
        #
        wworking_dir = arg_item
    elif sys.argv[1] == "-U":
        arg_item = " ".join(sys.argv[2:])
        if arg_item[0:7] == "file://":
            wworking_dir = unquote(arg_item)[6:]

################################

class mainwindow(Gtk.Window):
    
    def __init__(self):
        # main window
        Gtk.Window.__init__(self, title="mfm2")
                
        self.wwidth = 800
        self.hheight = 600
        self.is_max = "False"
        try:
            sfile = open("progsize.cfg", "r")
            self.wwidth, self.hheight, self.is_max = sfile.readline().split(";")
            sfile.close()
        except:
            pass
        self.set_default_size(int(self.wwidth), int(self.hheight))
        # if the window should be maximized
        if self.is_max == "True":
            self.maximize()
        
        # this program icon
        pixbufs = Gtk.IconTheme.get_default().load_icon("folder", ITSIZE, 0)
        self.set_icon(pixbufs)
        # window at center of the screen
        self.set_position(1)
        # vertical box - main - everything inside
        self.vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox1)
        
        if USE_HEADB:
            header = Gtk.HeaderBar(title="mfm2")
            header.props.show_close_button = True
            self.set_titlebar(header)
            header.show()
        
        ###
        # horizontal box for paned
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.vbox1.pack_start(hbox2, True, True, 0)
            # paned for placessidebar and notebook
        paned = Gtk.Paned()
        hbox2.pack_start(paned, False, True, 0)
            # PLACESSIDEBAR
        self.placessidebar = Gtk.PlacesSidebar()
        self.placessidebar.set_property("populate-all", True)
        self.placessidebar.set_show_recent(False)
        # self.placessidebar.set_show_trash(False)
        # self.placessidebar.set_show_trash(True)
        gte = Gtk.TargetEntry.new("text/uri-list", 0, 0)
        targets = [gte]
        actions_drop = Gdk.DragAction.COPY
        self.placessidebar.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, targets, actions_drop)
        self.placessidebar.connect("drag-perform-drop", self.psb_drop)
            # placessidebar in the left
        paned.pack1(self.placessidebar, False, False)
            # the paned width
        self.paned_width = 350
        try:
            pfile = open("panedsize.cfg", "r")
            self.paned_width = pfile.readline()
            pfile.close()
        except:
            pass
        paned.set_position(int(self.paned_width))
            # NOTEBOOK
        self.notebook = Gtk.Notebook()
            # add a scrollbar for the pages
        self.notebook.set_scrollable(True)
            # notebook in the right
        paned.pack2(self.notebook, False, False)
        
        # when an item is left-clicked
        self.placessidebar.connect("open-location", self.on_open_location)
        # when right-click on one item
        self.placessidebar.connect("populate-popup", self.on_populate_popup)
        # # an unmout action has been performed
        # self.placessidebar.connect("unmount", self.on_placessidebar_unmount)
        #
        # if the Trash folder is open: 0 NO - 1 YES
        self.IS_TRASH_OP = 0
        # if the System folder is open: 0 NO - 1 YES
        self.IS_SYSTEM_OP = 0
                
        self.vbox1.show_all()
        # add the custom modules
        for el in list_custom_modules_win:
            if el.mmodule_type() == 1:
                el.ModuleCustom(self)
        paned.connect("size-allocate", self.on_size_allocate_paned)
        if UPDATE_PROGRAM_SIZE:
            self.connect("size-allocate", self.on_size_allocate, paned)
        
        #
        # combobox for visited folders
        self.fcb_store = Gtk.ListStore(str)
    
    # store the paned width
    def on_size_allocate_paned(self, widget, allocation):
        
        if widget.get_position() != int(self.paned_width):
            with open("panedsize.cfg", "w") as ffile:
                ffile.write("{}".format(widget.get_position()))

    # store the window dimensions
    def on_size_allocate(self, widget, allocation, paned):
        
        if self.props.is_maximized:
            if self.is_max == "False":
                with open("progsize.cfg", "w") as ffile:
                    ffile.write("{0};{1};{2}".format(self.wwidth, self.hheight, "True"))
                self.is_max = "True"
            paned.set_position(int(self.paned_width))
        else:
            if self.is_max ==  "True":
                self.is_max = "False"
                with open("progsize.cfg", "w") as ffile:
                    ffile.write("{0};{1};{2}".format(self.wwidth, self.hheight, "False"))
                paned.set_position(int(self.paned_width))
                return
            if allocation.width != int(self.wwidth) or allocation.height != int(self.hheight):
                with open("progsize.cfg", "w") as ffile:
                    ffile.write("{0};{1};{2}".format(allocation.width, allocation.height, False))
                paned.set_position(int(self.paned_width))
        
    # placessidebar drop
    def psb_drop(self, widget):
        pass


#####################
#      SIDEBAR      #
#####################

    # when a sidebar item is clicked
    def on_open_location(self, placessidebar, location, flags):
        if location:
            # if it is a valid path
            if location.get_path():
                # if it exists
                if os.path.exists(location.get_path()):
                    wiconview(location.get_path(), self, 1, "")
                else:
                    self.generic_dialog(MISSED_PATH, location.get_path())
            if location.get_uri() == "trash:///":
                if self.IS_TRASH_OP == 0:
                    trash_module.wtrash(self)
    
    # when right-mouse button is clicked on an item in the placesidebar
    # if it is the recycle bin a new entry is added to the menu
    def on_populate_popup(self, placesidebar, container, selected_item, selected_volume):
        
        if  (selected_item != None) and (selected_item.get_uri() == "trash:///"):
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            button_trash = Gtk.ModelButton(label=TEMPTY_RBIN)
            
            if trash_module.wtrash.trash_is_empty(self.notebook) == True:
                button_trash.set_sensitive(True)
            elif trash_module.wtrash.trash_is_empty(self.notebook) == False:
                button_trash.set_sensitive(False)
            button_trash.get_children()[0].set_xalign(0.0)
            button_trash.connect("clicked", self.on_button_trash)
            separator.show()
            button_trash.show()
            container.pack_start(separator, False, False, 4)
            container.pack_start(button_trash, False, False, 0)
    
    
    # confirm to empty the recycle bin
    def on_button_trash(self, button):
        messagedialog = Gtk.MessageDialog(parent=self,
                                          modal=True,
                                          message_type=Gtk.MessageType.WARNING,
                                          buttons=Gtk.ButtonsType.OK_CANCEL,
                                          text=TMESS_EMPTY)
        messagedialog.connect("response", self.dialog_response)
        messagedialog.show()


    def dialog_response(self, messagedialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            self.on_empty_clicked()
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.CANCEL:
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            messagedialog.destroy()      


    def on_empty_clicked(self):
        trash_module.wtrash.request_empty_trash(self.notebook)


    # def on_placessidebar_unmount(self, placessidebar, mount_operation):
        # try:
            # placessidebar_location = placessidebar.get_location()
            # if placessidebar_location:
                # unmounted_path = placessidebar_location().get_path()
                # self.fcheck_opened_volumes(unmounted_path)
        # except Exception as E:
            # self.generic_dialog("Message", str(E))
    
    
    # # close the tab of unmounted volume if open
    # def fcheck_opened_volumes(self, unmounted_path):
        
        # num_pages = self.notebook.get_n_pages()
        
        # if num_pages == 1:
            
            # hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(0)).get_children()[0].get_label()
            # if unmounted_path[0:len(hlabel)]:
                # if unmounted_path == hlabel[0:len(unmounted_path)]:
                    
                    # wiconview(HOME, self, 1, "")
                    # self.notebook.remove_page(0)
                    # self.notebook.set_show_tabs(False)
                    # return
        # elif num_pages > 1:
            # for i in reversed(range(num_pages)):

                # hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(i)).get_children()[0].get_label()
                
                # if unmounted_path[0:len(hlabel)]:
                    # if unmounted_path == hlabel[0:len(unmounted_path)]:
                        # self.notebook.remove_page(i)
                        # if self.notebook.get_n_pages() == 1:
                            # self.notebook.set_show_tabs(False)

    # generic message dialog
    def generic_dialog(self, message1, message2):
        messagedialog = Gtk.MessageDialog(parent=self,
                                          modal=True,
                                          message_type=Gtk.MessageType.WARNING,
                                          buttons=Gtk.ButtonsType.OK,
                                          text=message1)
        messagedialog.format_secondary_text("{}".format(message2))
        messagedialog.connect("response", self.generic_dialog_response)
        messagedialog.show()

    def generic_dialog_response(self, messagedialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            messagedialog.destroy()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            messagedialog.destroy()  

##################################
#            ICONVIEW            #
##################################

# optional modules
try:
    import modules_addon.module1 as module1
except Exception as E:
    generic_dialog("Message", str(E))

# modules and functions
# DnD
try:
    import items_copy
except Exception as E:
    generic_dialog("Message", str(E))
    sys.exit()
# copy/cut/paste
try:
    import items_copy_clip
except Exception as E:
    generic_dialog("Message", str(E))
    sys.exit()

try:
    from functions import compare as ccompare
except Exception as E:
    generic_dialog("Message", str(E))

try:
    from functions import convert_size2 as convert_size2
except Exception as E:
    generic_dialog("Message", str(E))

# thumbnailer module
if USE_THUMB == 1:
    try:
        from pythumb import *
    except Exception as E:
        generic_dialog("Message", str(E))
        sys.exit()

# items are hidden - global variable
hidden_state = True

# import optional modules for the menus
sys.path.append("modules_menu")
mmod_bg = glob.glob("modules_menu/*.py")
# list of the filenames of the menu modules
menu_bg_module = []
for el in mmod_bg:
    try:
        ee = importlib.import_module(os.path.basename(el)[:-3])
        menu_bg_module.append(ee)
    except ImportError as ioe:
        generic_dialog("Message", str(ioe))

# import optional custom modules
sys.path.append("modules_custom")
mmod_custom = glob.glob("modules_custom/*.py")
# list of the filenames
list_custom_modules = []
for el in reversed(mmod_custom):
    try:
        ee = importlib.import_module(os.path.basename(el)[:-3])
        list_custom_modules.append(ee)
    except ImportError as ioe:
        generic_dialog("Message", str(ioe))

# remove the alien modules
for el in list_custom_modules[:]:
    if el.mmodule_type() == 1:
        list_custom_modules.remove(el)

#
ICON_SIZE = ICON_SIZE2
LINK_SIZE = LINK_SIZE2
THUMB_SIZE = THUMB_SIZE2
NB2_ICON_SIZE = ICON_SIZE2

# items to copy with copy or cut/paste
ITEMS_TO_COPY = None


class CellRenderer(Gtk.CellRendererPixbuf):
    pixbuflink = GObject.Property(type=str, default="")
    pixbufaccess = GObject.Property(type=str, default="")
    
    def __init__(self):
        super().__init__()
        self.set_fixed_size(THUMB_SIZE+2, THUMB_SIZE+2)
        
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
        ypad = THUMB_SIZE-LINK_SIZE
        
        if self.pixbuflink == "True":
            pixbuf11 = Gtk.IconTheme.get_default().load_icon("emblem-symbolic-link", LINK_SIZE, 0)
            Gdk.cairo_set_source_pixbuf(cr, pixbuf11, cell_area.x+xpad-LINK_SIZE, y_offset+ypad)
            cr.paint()
        
        if self.pixbufaccess == "False":
            pixbuf12 = Gtk.IconTheme.get_default().load_icon("emblem-readonly", LINK_SIZE, 0)
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
        self.pack_end(renderer, True, True, 0)
        renderer.props.xalign = 0.5
        renderer.props.yalign = 0
        renderer.props.wrap_width = 15
        renderer.props.wrap_mode = 1
        self.add_attribute(renderer, 'text', 1)
        
        if IV_USE_OPT_INFO == 1:
            renderer1 = Gtk.CellRendererText()
            self.pack_end(renderer1, False, False, 0)
            renderer1.props.xalign = 0.5
            renderer1.props.yalign = 0
            renderer1.props.wrap_width = 15
            renderer1.props.wrap_mode = 1
            renderer1.props.style = 1
            self.add_attribute(renderer1, 'text', 7)

#
class ThumbPix(threading.Thread):
    def __init__(self, working_path, model, IV):
        threading.Thread.__init__(self)
        self.working_path = working_path
        self.model = model
        self.IV = IV

    def run(self):
        wiconview.evaluate_pixbuf_t(None, self.working_path, self.model, self.IV)


class wiconview():
    def __init__(self, working_dir, window, NEW_PAGE, FNAV):
        time.sleep(0.01)
        self.window = window
        # 0 = same page, 1 = new_page
        self.new_page = NEW_PAGE
        # the main notebook from the main module
        self.notebook = window.notebook
        #
        IV_ICON_SIZE = ICON_SIZE
        IV_LINK_SIZE = LINK_SIZE
        IV_THUMB_SIZE = THUMB_SIZE
        #
        self.IS_CHANGED = 0
        self.IS_CREATED = 0
        self.CNG_DONE_HINT = 0
        #
        self.working_path = ""
        if os.path.isdir(working_dir):
            self.working_path = working_dir
        elif os.path.isfile(working_dir):
            self.working_path = os.path.dirname(working_dir)
        else:
            sys.exit()
        #
        self.IV_selected_items = []
        self.list_clip = []
        self.current_filter_func = "False"
        #
        # main box
        self.IVBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        ## box at top for history and buttons
        self.tbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.IVBox.add(self.tbox)
        # combobox for visited folders
        self.window.fcb_store.prepend([self.working_path])
        self.fcb = Gtk.ComboBox.new_with_model(self.window.fcb_store)
        self.fcb.set_hexpand(True)
        self.tbox.add(self.fcb)
        renderer_text = Gtk.CellRendererText()
        self.fcb.pack_start(renderer_text, True)
        self.fcb.add_attribute(renderer_text, "text", 0)
        self.fcb.set_active(0)
        self.fcb.connect("changed", self.on_folder_changed)
        # up button
        try:
            pixbuf = Gtk.IconTheme.get_default().load_icon("go-up", ITSIZE, 0)
        except:
            pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-go-up", ITSIZE, 0)
        up_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.up_button = Gtk.Button(label="", image=up_image)
        self.up_button.set_tooltip_text(UPPER_FOLDER)
        self.tbox.pack_end(self.up_button, False, False, 5)
        self.up_button.connect("clicked", self.on_up_folder)
        
        # scrolled window
        scrolledwindow = Gtk.ScrolledWindow()
        self.IVBox.add(scrolledwindow)
        scrolledwindow.set_overlay_scrolling(True)
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        scrolledwindow.set_policy(Gtk.PolicyType.NEVER,  Gtk.PolicyType.AUTOMATIC)
        ################
        
        # item icon - item name - is_folder - working_dir - is_hidden - is_link - is_not_readable - description - emblem
        tmodel = Gtk.ListStore(Pixbuf, str, str, str, str, str, str, str, str)
        self.model = self.fill_model(tmodel, self.working_path)
        
        #
        self.model_filter = self.model.filter_new()
        self.model_filter.set_visible_func(self.filter_func, data=None)
        self.modello = Gtk.TreeModelSort(model=self.model_filter)
        self.modello.set_sort_func(2, ccompare, None)
        self.modello.set_sort_column_id(2, Gtk.SortType.ASCENDING)
        #
        self.IV = Gtk.IconView.new_with_area(CellArea())
        scrolledwindow.add(self.IV)
        #
        self.IV.set_model(self.modello)
        self.IV.set_item_width(IV_ITEM_WIDTH)
        #
        if USE_THUMB:
            thumbs = ThumbPix(self.working_path, self.model, self.IV)
            thumbs.start()
        
        # 
        self.IV.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        
        ###### NOTEBOOK2
        self.notebook2 = Gtk.Notebook()
        self.notebook2.set_scrollable(True)
        pagen = Gtk.Box()
        ### notebook 2 - page 1
        # INFO BOX
        self.npmainbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        pagen.add(self.npmainbox)
        #
        infopixbuf = Gtk.Image.new_from_pixbuf(self.evaluate_pixbuf(self.working_path, NB2_ICON_SIZE))
        self.npmainbox.pack_start(infopixbuf, False, False, 20)
        self.grid301 = Gtk.Grid()
        
        # button group: hidden - invert_selection
        self.tbbox = self.ftbbox()
        self.npmainbox.pack_end(self.tbbox, True, True, 10)
        self.npmainbox.pack_end(self.grid301, True, True, 0)
        
        self.grid301.set_row_spacing(5)
        
        self.tbbox.props.halign = 2
        self.tbbox.props.valign = 3
        
        ### the four labels box
        self.grid301.props.halign = 1
        self.grid301.props.valign = 3
        self.grid301.props.hexpand = True
        ## labels
        # number of items found and name of the item
        self.label300name = Gtk.Label(label="")
        self.grid301.attach(self.label300name, 0, 0, 1, 1)
        self.label300name.props.xalign = 1
        self.label300name.props.valign = 1 
        # nothing and path of selected item
        self.label300path = Gtk.Label(label="")
        self.grid301.attach(self.label300path, 0, 1, 1, 1)
        self.label300path.props.xalign = 1
        self.label300path.props.valign = 1
        # nothing and type of selected item
        self.label300type = Gtk.Label(label="")
        self.grid301.attach(self.label300type, 0, 2, 1, 1)
        self.label300type.props.xalign = 1
        self.label300type.props.valign = 1
        # nothing and size of selected item
        self.label300size = Gtk.Label(label="")
        self.grid301.attach(self.label300size, 0, 3, 1, 1)
        self.label300size.props.xalign = 1
        self.label300size.props.valign = 1
        # 
        self.label301name = Gtk.Label(label="")
        self.grid301.attach(self.label301name, 1, 0, 1, 1)
        self.label301name.props.xalign = 0
        self.label301name.set_selectable(True)
        self.label301name.set_line_wrap(True)
        self.label301name.set_line_wrap_mode(2)
        self.label301name.props.can_focus = False
        # 
        self.label302path = Gtk.Label(label="")
        self.grid301.attach(self.label302path, 1, 1, 1, 1)
        self.label302path.props.xalign = 0
        self.label302path.set_selectable(True)
        self.label302path.set_line_wrap(True)
        self.label302path.set_line_wrap_mode(2)
        self.label302path.props.can_focus = False
        # 
        self.label303type = Gtk.Label(label="")
        self.grid301.attach(self.label303type, 1, 2, 1, 1)
        self.label303type.props.xalign = 0
        self.label303type.set_line_wrap(True)
        self.label303type.set_line_wrap_mode(1)
        # 
        self.label304size = Gtk.Label(label="")
        self.grid301.attach(self.label304size, 1, 3, 1, 1)
        self.label304size.props.xalign = 0
        
        ########
        
        labelinfo = Gtk.Label()
        labelinfo.set_markup("<span size='small'>"+INFO_NAME+"</span>")
        self.notebook2.append_page(pagen, labelinfo) 
        #
        self.meta_page = Gtk.Box()
        self.meta_page.set_orientation(orientation=Gtk.Orientation.VERTICAL)
        self.meta_page.show()
        self.meta_label = Gtk.Label()
        self.meta_label.set_markup("<span size='small'>"+IDATE+"</span>")
        self.notebook2.append_page(self.meta_page, self.meta_label)
        ##### NOTEBOOK2 END
        
        ##### the notebook page
        page = Gtk.Box()
        page.set_orientation(orientation=Gtk.Orientation.VERTICAL)
        page.show()
        # 
        page.pack_start(self.IVBox, True, True, 0)
        page.add(self.notebook2)
        # the label for the page
        lbox = self.create_nlabel(page)
        # next to (1) or instead of (0) the current tab
        if NEW_PAGE == 1:
            self.notebook.append_page(page, lbox)
            numpage = self.notebook.get_n_pages()
            self.notebook.set_current_page(numpage-1)
        elif NEW_PAGE == 0:
            curr_page = self.notebook.get_current_page()
            try:
                self.notebook.insert_page(page, lbox, curr_page)
                self.notebook.set_current_page(curr_page)
                self.notebook.remove_page(curr_page+1)
            except Exception as e:
                self.generic_dialog("\n"+str(e), "")
        self.notebook.set_tab_reorderable(page, True)
         
        numpage = self.notebook.get_n_pages()
        if numpage > 1:
            self.notebook.set_show_tabs(True)
        elif numpage == 1:
            self.notebook.set_show_tabs(False)
        #
        if IV_DND == 1:
            start_button_mask = Gdk.ModifierType.BUTTON1_MASK
            gte = Gtk.TargetEntry.new("text/uri-list", Gtk.TargetFlags.OTHER_APP, 0)
            gte1 = Gtk.TargetEntry.new("text/uri-list", Gtk.TargetFlags.SAME_WIDGET, 0)
            targets = [gte, gte1]
            actions = Gdk.DragAction.MOVE | Gdk.DragAction.COPY | Gdk.DragAction.LINK
            self.IV.enable_model_drag_source(start_button_mask, targets, actions)
            self.IV.connect_after("drag-begin", self.on_drag_begin)
            self.IV.connect("drag-data-get", self.on_drag_data_get)
            self.IV.connect("drag-end", self.on_drag_end)
            self.IV.connect("drag-failed", self.on_drag_failed)
            self.IV.connect("drag-motion", self.on_drag_motion)
            actions_drop = Gdk.DragAction.COPY | Gdk.DragAction.MOVE | Gdk.DragAction.LINK
            self.IV.enable_model_drag_dest(targets, actions_drop)
            self.IV.connect("drag-drop", self.on_drag_drop)
            self.IV.connect("drag-data-received", self.on_drag_data_received)
        #
        self.IV.connect("selection-changed", self.on_selection_changed)
        self.IV.connect("item-activated", self.on_double_click)
        self.IV.connect("button-press-event", self.on_mouse_button_pressed)
        self.IV.connect("button-release-event", self.on_mouse_release)
        #
        self.IV.set_events (Gdk.EventMask.BUTTON_PRESS_MASK)
        self.IV.connect('key-press-event', self.on_key_pressed)
        self.ppoint = 0
        #
        visible_item, hidden_item = self.num_itemh(self.working_path)
        self.label300name.set_markup("<i>"+IPATH+"</i>")
        self.label301name.set_text(self.working_path)
        self.label300path.set_markup("<i>"+IITEMS+"</i>")
        self.label302path.set_text("{}".format(visible_item))
        self.label300type.set_markup("<i>"+IHIDDEN+"</i>")
        self.label303type.set_text("{}".format(hidden_item))
        self.label300size.set_markup("<i>"+ISIZE2+"</i>")
        self.label304size.set_text("{}".format(convert_size2(shutil.disk_usage(self.working_path).free)))
        #### optional module1
        if IV_USE_OPT_INFO == 1:
            # description
            module1.add_description(self.model)
        ##
        self.notebook2.show_all()
        self.notebook2.set_current_page(0)
        self.IVBox.show_all()
        self.monitor_dir(self.working_path)
        #
        # if the opening path is a file, it is highlighted
        if os.path.isfile(working_dir):
            
            for rrow in self.modello:
                if rrow[1] == os.path.basename(working_dir):
                    self.IV.select_path(rrow.path)
                    self.IV.set_cursor(rrow.path, None, False)
                    self.IV.scroll_to_path(rrow.path, True, 0.5, 0.5)
                    # 
                    self.IV.grab_focus()
                    break
        
        # highlight the parent folder when going up
        if FNAV != "":
            for rrow in self.modello:
                if rrow[2] == "a":
                    if rrow[1] == os.path.basename(FNAV):
                        self.IV.select_path(rrow.path)
                        self.IV.set_cursor(rrow.path, None, False)
                        self.IV.scroll_to_path(rrow.path, True, 0.5, 0.5)
                        # 
                        self.IV.grab_focus()
                        break
        
        # add the custom modules
        for el in list_custom_modules:
            if el.mmodule_type() == 2:
                el.ModuleCustom(self)
    

    #
    def on_folder_changed(self, combo):
        
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            name = model[tree_iter][:2]
            new_path = name[0]
            #
            if os.access(new_path, os.R_OK):
                if IV_OPEN_FOLDER == 1:
                    wiconview(new_path, self.window, 1, "")
                    self.model_filter.refilter()
                elif IV_OPEN_FOLDER == 0:
                    wiconview(new_path, self.window, 0, "")
                    self.model_filter.refilter()
                    self.fcb_store.append([new_path])

    
    # up button is clicked - go up in the filesystem
    def on_up_folder(self, up_button):
        up_dir = os.path.dirname(self.working_path)
        if os.access(up_dir, os.R_OK):
            wiconview(up_dir, self.window, 0, "")
        else:
            self.generic_dialog("Error", "Cannot change folder.")
    
    
    # 
    def fill_model(self, model, npath):
        
        try:
            file_folder = os.listdir(npath)
        except Exception as e:
            file_folder = []
            self.generic_dialog("\n"+str(e), "")
            sys.exit()

        model.clear()
        
        for ffile in file_folder:

            path = os.path.join(npath, ffile)
            file_acc = None
            if os.access(path, os.W_OK) == False or os.access(path, os.R_OK) == False:
                file_acc = "False"
            
            pixbuf = self.evaluate_pixbuf(path, ICON_SIZE)
            
            if os.path.isdir(path):
                
                if os.path.islink(path):
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "a", npath, "True", "True", file_acc, None, None])
                    else:
                        model.append([pixbuf, ffile, "a", npath, "False", "True", file_acc, None, None])
                
                else:
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "a", npath, "True", None, file_acc, None, None])
                    else:
                        model.append([pixbuf, ffile, "a", npath, "False", None, file_acc, None, None])   
            
            elif os.path.isfile(path):

                pixbuf = self.evaluate_pixbuf(path, ICON_SIZE)
                
                if os.path.islink(path):
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "b", npath, "True", "True", file_acc, None, None])
                    else:    
                        model.append([pixbuf, ffile, "b", npath, "False", "True", file_acc, None, None])
                
                else:
                    
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "b", npath, "True", None, file_acc, None, None])
                    else:    
                        model.append([pixbuf, ffile, "b", npath, "False", None, file_acc, None, None])
            
            else:
                
                if os.path.islink(path) and not os.path.exists(os.readlink(path)):
                    
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file("empty.svg")
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "b", npath, "True", "True", file_acc, None, None])
                    else:    
                        model.append([pixbuf, ffile, "b", npath, "False", "True", file_acc, None, None])
                
                else:
                    if pixbuf == None:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("empty", ICON_SIZE, 0)
                    if ffile.startswith('.'):
                        model.append([pixbuf, ffile, "b", npath, "True", None, file_acc, None, None])
                    else:    
                        model.append([pixbuf, ffile, "b", npath, "False", None, file_acc, None, None])
        
        return model
    
    
    # events for keyboard actions
    def on_key_pressed(self, IV, event):
        keyname = Gdk.keyval_name(event.keyval)
        # move to trash
        if keyname == "Delete":
            self.trash_item(None)
        # button navigation
        elif keyname == "Left" or keyname == "Right" or keyname == "Up" or keyname == "Down":
            self.IV_selected_items = []
        # keypad button navigation
        elif keyname == "KP_Left" or keyname == "KP_Right" or keyname == "KP_Up" or keyname == "KP_Down":
            self.IV_selected_items = []
    
    
    # find the visible and hidden items or the working_dir
    def num_itemh(self, working_dir):
        if working_dir != "hTrash":
            file_folder = os.listdir(working_dir)
            total_item = len(file_folder)
            for el in file_folder[:]:
                if el.startswith("."):
                  file_folder.remove(el)
            visible_item = len(file_folder)
            hidden_item = total_item - visible_item
            return visible_item, hidden_item
    
    
    # start a monitor
    def monitor_dir(self, path):
        gio_dir = Gio.File.new_for_path(path)
        self.monitor = gio_dir.monitor_directory(Gio.FileMonitorFlags.WATCH_MOVES, None)
        # 
        self.monitor.props.rate_limit = 100
        self.monitor.connect("changed", self.dir_changed)


    #
    def fcheck_opened_folders(self, file_path):
        
        num_pages = self.notebook.get_n_pages()
        
        if num_pages == 1:
            
            hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(0)).get_children()[0].get_label()
            if hlabel == file_path:
                wiconview(HOME, self.window, 1, "")
                self.notebook.remove_page(0)
                self.notebook.set_show_tabs(False)
                return
        elif num_pages > 1:
            for i in range(num_pages):
                hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(i)).get_children()[0].get_label()
                
                if hlabel == file_path:
                    self.notebook.remove_page(i)
                    if self.notebook.get_n_pages() == 1:
                        self.notebook.set_show_tabs(False)
                    break
                    return
    
    
    # the monitor
    def dir_changed(self, monitor, file, other_file, event):
        
        if event == Gio.FileMonitorEvent.CHANGED:
            if self.IS_CREATED == 1:
                return
            file_path = file.get_path()
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            for row in self.model:
                if row[1] == ibasename:
                    self.model.remove(row.iter)
                    self.IS_CHANGED = 1
        
        elif event == Gio.FileMonitorEvent.CHANGES_DONE_HINT:
            
            file_path = file.get_path()
            
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            if self.IS_CHANGED == 1:
                self.CNG_DONE_HINT = 1
                pixbuf = self.evaluate_pixbuf(file_path, ICON_SIZE)
                
                file_acc = None
                if os.access(file_path, os.W_OK) == False or os.access(file_path, os.R_OK) == False:
                    file_acc = "False"
                
                if os.path.islink(file_path):
                    # if it is a dir
                    if os.path.isdir(file_path):
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "a", idirname, "True", "True", file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "a", idirname, "False", "True", file_acc, None, None])
                    # if it is a file
                    elif os.path.isfile(file_path):
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
                        # create or use the thumbnail
                        thumbs = ThumbPix(self.working_path, self.model, self.IV)
                        thumbs.start()
                        thumbs.join()
                    else:
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
                
                elif not os.path.islink(file_path):
                    # if it is a dir
                    if os.path.isdir(file_path):
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "a", idirname, "True", None, file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "a", idirname, "False", None, file_acc, None, None])
                    # if it is a file
                    elif os.path.isfile(file_path):
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])
                        # create or use the thumbnail
                        thumbs = ThumbPix(self.working_path, self.model, self.IV)
                        thumbs.start()
                        thumbs.join()
                    # if it is else
                    else:
                        if file_path.startswith("."):
                            self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                        else:
                            self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])

            self.IS_CREATED = 0
            self.IS_CHANGED = 0
            #CNG_DONE_HINT = 0
        
        elif event == Gio.FileMonitorEvent.ATTRIBUTE_CHANGED:
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            file_acc = None
            if os.access(file_path, os.W_OK) == False or os.access(file_path, os.R_OK) == False:
                file_acc = "False"
            for row in self.model:
                if row[1] == ibasename:
                    row[6] = file_acc
        
        elif event == Gio.FileMonitorEvent.RENAMED:
            file_path = file.get_path()

            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            #
            new_file_path = other_file.get_path()
            new_ibasename = os.path.basename(new_file_path)
            new_idirname = os.path.dirname(new_file_path)
            
            for row in self.model:
                
                if self.CNG_DONE_HINT == 1:
                    if row[1] == ibasename:
                        self.model.remove(row.iter)
                        self.CNG_DONE_HINT = 0
                        return
                elif self.CNG_DONE_HINT == 0:
                    if row[1] == ibasename:
                        
                        rrow = [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]]
                        self.model.remove(row.iter)
                        self.model.append([rrow[0], new_ibasename, rrow[2], rrow[3], rrow[4], rrow[5], rrow[6], rrow[7], rrow[8]])
                        self.IV.set_model(self.modello)
                        
            self.fcheck_opened_folders(file_path)
            
        elif event == Gio.FileMonitorEvent.MOVED_OUT:
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            for row in self.model:
                if row[1] == ibasename:
                    
                    self.model.remove(row.iter)
                    
            self.fcheck_opened_folders(file_path)
        
        elif event == Gio.FileMonitorEvent.DELETED:
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            for row in self.model:
                if row[1] == ibasename:
                    
                    self.model.remove(row.iter)
                     
            self.fcheck_opened_folders(file_path)
        
        elif event == Gio.FileMonitorEvent.MOVED_IN:
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            # find the pixbuf
            pixbuf = self.evaluate_pixbuf(file_path, ICON_SIZE)
            
            # check the access of the item
            file_acc = None
            if os.access(file_path, os.W_OK) == False or os.access(file_path, os.R_OK) == False:
                file_acc = "False"
            
            if os.path.islink(file_path):
                # if it is a dir
                if os.path.isdir(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "a", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "a", idirname, "False", "True", file_acc, None, None])
                # if it is a file
                elif os.path.isfile(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
                    # create or use the thumbnail
                    thumbs = ThumbPix(self.working_path, self.model, self.IV)
                    thumbs.start()
                    thumbs.join()
                # if broken link
                elif not os.path.exists(os.path.realpath(file_path)):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file("empty.svg")
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
                # if it is else
                else:
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
            elif not os.path.islink(file_path):
                # if it is a dir
                if os.path.isdir(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "a", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "a", idirname, "False", None, file_acc, None, None])
                # if it is a file
                elif os.path.isfile(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])
                    # create or use the thumbnail
                    thumbs = ThumbPix(self.working_path, self.model, self.IV)
                    thumbs.start()
                    thumbs.join()
                # if it is else
                else:
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])
        
        elif event == Gio.FileMonitorEvent.CREATED:
            
            self.IS_CREATED = 1
            file_path = file.get_path()
            ibasename = os.path.basename(file_path)
            idirname = os.path.dirname(file_path)
            
            # find the pixbuf
            pixbuf = self.evaluate_pixbuf(file_path, ICON_SIZE)
            
            # check the access of the item
            file_acc = None
            if os.access(file_path, os.W_OK) == False or os.access(file_path, os.R_OK) == False:
                file_acc = "False"
            
            if os.path.islink(file_path):
                # if it is a dir
                if os.path.isdir(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "a", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "a", idirname, "False", "True", file_acc, None, None])
                # if it is a file
                elif os.path.isfile(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None])
                    # create or use the thumbnail
                    thumbs = ThumbPix(self.working_path, self.model, self.IV)
                    thumbs.start()
                    thumbs.join()
                # if it is else
                else:
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", "True", file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", "True", file_acc, None, None]) 
            elif not os.path.islink(file_path):
                # if it is a dir
                if os.path.isdir(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "a", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "a", idirname, "False", None, file_acc, None, None])
                # if it is a file
                elif os.path.isfile(file_path):
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])
                    # create or use the thumbnail
                    thumbs = ThumbPix(self.working_path, self.model, self.IV)
                    thumbs.start()
                    thumbs.join()
                # if it is else
                else:
                    if file_path.startswith("."):
                        self.model.append([pixbuf, ibasename, "b", idirname, "True", None, file_acc, None, None])
                    else:
                        self.model.append([pixbuf, ibasename, "b", idirname, "False", None, file_acc, None, None])
        
        if event in [Gio.FileMonitorEvent.CHANGED, Gio.FileMonitorEvent.CHANGES_DONE_HINT, Gio.FileMonitorEvent.ATTRIBUTE_CHANGED,
                     Gio.FileMonitorEvent.RENAMED, Gio.FileMonitorEvent.MOVED_OUT, Gio.FileMonitorEvent.DELETED,
                     Gio.FileMonitorEvent.MOVED_IN, Gio.FileMonitorEvent.CREATED]:
            
            if IV_USE_OPT_INFO == 1:
                module1.add_description(self.model)
            
            # deselect everything
            if len(self.IV.get_selected_items()) > 0:
                self.ppoint = 1
                self.IV_selected_items = []
                for rrow in self.IV.get_selected_items():
                    self.IV.unselect_path(rrow)
                self.ppoint = 0
            
            # restore the labels
            if os.path.exists(self.working_path):
                visible_item, hidden_item = self.num_itemh(self.working_path)
                self.label300name.set_label(IPATH)
                # 
                self.label301name.set_line_wrap_mode(0)
                self.label301name.set_label(self.working_path)
                self.label300path.set_label(IITEMS)
                self.label302path.set_label("{}".format(visible_item))
                self.label300type.set_label(IHIDDEN)
                self.label303type.set_label("{}".format(hidden_item))
                self.label300size.set_label("")
                self.label304size.set_label("")
                self.label300size.set_label(ISIZE2)
                self.label304size.set_label("{}".format(convert_size2(shutil.disk_usage(self.working_path).free)))
        # check if a tab is open when a volume is unmounted
        elif event == Gio.FileMonitorEvent.UNMOUNTED:
            self.fcheck_opened_volumes(file.get_path())
        
        self.IV.grab_focus()
    
    
    # close the tab of unmounted volume if open
    def fcheck_opened_volumes(self, unmounted_path):
        num_pages = self.notebook.get_n_pages()
        if num_pages == 1:
            hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(0)).get_children()[0].get_label()
            if unmounted_path == hlabel:
                wiconview(HOME, self.window, 1, "")
                self.notebook.remove_page(0)
                self.notebook.set_show_tabs(False)
                return
        elif num_pages > 1:
            for i in reversed(range(num_pages)):
                hlabel = self.notebook.get_tab_label(self.notebook.get_nth_page(i)).get_children()[0].get_label()
                if unmounted_path == hlabel:
                    self.notebook.remove_page(i)
                    if self.notebook.get_n_pages() == 1:
                        self.notebook.set_show_tabs(False)
    

    # stop a monitor
    def monitor_stop(self):
        self.monitor.cancel()
    
    
    #
    def on_double_click(self, IV, treepath):
        # if folder
        if self.modello[treepath][2] == "a":
            new_path = os.path.join(self.modello[treepath][3], self.modello[treepath][1])
            if os.path.exists(new_path):
                if IV_OPEN_FOLDER == 1:
                    wiconview(new_path, self.window, 1, "")
                    self.model_filter.refilter()
                elif IV_OPEN_FOLDER == 0:
                    wiconview(new_path, self.window, 0, "")
                    self.model_filter.refilter()
                
                self.IV.grab_focus()
                self.notebook.grab_focus()
            else:
                self.generic_dialog("\n"+"ERROR", "")
        
        elif self.modello[treepath][2] == "b":
            new_path = os.path.join(self.modello[treepath][3], self.modello[treepath][1])
            if not os.access(new_path, os.X_OK):
                uri = "file://"+new_path
                try:
                    ret = Gio.app_info_launch_default_for_uri(uri, None)
                    if ret == False:
                        self.generic_dialog(IERROR2, os.path.basename(new_path))
                except Exception as e:
                    self.generic_dialog(IERROR2, os.path.basename(new_path))

            else:
                self.execwindow(new_path)
    
    def execwindow(self, path):
        win = Gtk.Window()
        win.set_title("mfm")
        win.set_transient_for(self.window)
        win.set_modal(True)
        win.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        win.set_skip_taskbar_hint(True)
        #
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=IEXECFILE)
        vbox.add(label)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # button cancel
        buttonc = Gtk.Button(label=IBUTTONC)
        buttonc.connect("clicked", lambda w: win.close())
        # button exec
        buttone = Gtk.Button(label=IBUTTONE)
        buttone.connect("clicked", self.ew_exec, path, win)
        # button open
        buttono = Gtk.Button(label=IBUTTONO)
        buttono.connect("clicked", self.ew_open, path, win)
        
        hbox.pack_start(buttonc, True, True, 0)
        hbox.pack_start(buttone, True, True, 0)
        hbox.pack_start(buttono, True, True, 0)
        vbox.add(hbox)
        
        win.add(vbox)
        win.connect ('delete-event', self.close_execwindow)
        win.show_all()
    
    # close the window
    def close_execwindow(self, widget, event):
        return False

    # exec the file
    def ew_exec(self, widget, new_path, win):
        try:
            subprocess.Popen([new_path], universal_newlines = True)
        except Exception as e:
            self.generic_dialog("\n"+str(e), "")
        win.close()
    
    # open the file
    def ew_open(self, widget, new_path, win):
        uri = "file://"+new_path
        ret = Gio.app_info_launch_default_for_uri(uri, None)
        if ret == False:
            self.generic_dialog(IERROR2, new_path)
            win.close()
        win.close()
    
    
    def evaluate_pixbuf(self, path, iicon_size):
        f = Gio.file_new_for_path(path)
        try:
            info = f.query_info(Gio.FILE_ATTRIBUTE_STANDARD_ICON,
                        Gio.FileQueryInfoFlags.NONE, None)
        except:
            return
        gicon = info.get_icon()
        gicon.get_names()
        # 
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
                        pixbuf = Gtk.IconTheme.get_default().load_icon("folder", ICON_SIZE, 0)   
                        return pixbuf
                    elif os.path.isfile(path):
                        pixbuf = Gtk.IconTheme.get_default().load_icon("empty", ICON_SIZE, 0)   
                        return pixbuf
                    else:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("empty", ICON_SIZE, 0)   
                        return pixbuf
    
    
    def evaluate_pixbuf_t(self, working_path, model, IV):
        time.sleep(0.001)
        iitem = os.listdir(working_path)
        hmd5 = "Null"
        #
        for item in iitem:
            path = os.path.join(working_path, item)
            # mime type of the file
            file = Gio.File.new_for_path(path)
            file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
            imime = Gio.FileInfo.get_content_type(file_info)
            if os.path.islink(path):
                rpath = os.readlink(path)
                if os.path.exists(rpath):
                    try:
                        hmd5 = create_thumbnail(os.path.basename(rpath), os.path.dirname(rpath), imime)
                    except:
                        pass

                    if hmd5 != "Null":
                        for row in model:
                            if row[1] == os.path.basename(path):
                                row[0] = GdkPixbuf.Pixbuf.new_from_file_at_size("sh_thumbnails/large/"+str(hmd5)+".png", THUMB_SIZE, THUMB_SIZE)
            elif os.path.isfile(path):
                
                try:
                    hmd5 = create_thumbnail(os.path.basename(path), os.path.dirname(path), imime)
                except:
                    pass
                
                if hmd5 != "Null":
                    for row in model:
                        if row[1] == os.path.basename(path):
                            row[0] = GdkPixbuf.Pixbuf.new_from_file_at_size("sh_thumbnails/large/"+str(hmd5)+".png", THUMB_SIZE, THUMB_SIZE)

        IV.grab_focus()           
                    
    
    def filter_func(self, model, iter, data):
        
        if self.current_filter_func is None or self.current_filter_func == "None":
            return True
        else:
            return model[iter][4] == self.current_filter_func


    def on_toggle_htb(self, htb):
        
        if self.current_filter_func == "False":
            self.current_filter_func = None
        elif self.current_filter_func == None:
            self.current_filter_func = "False"
        
        self.model_filter.refilter()
        self.IV_selected_items = []
        self.IV.unselect_all()

    
    # show hidden items - invert the selection
    def ftbbox(self):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("add.svg", HTB_SSR, HTB_SSR)
        imagel = Gtk.Image.new_from_pixbuf(pixbuf)
        htb = Gtk.ToggleButton(label="", image=imagel)
        htb.set_tooltip_text(I_SHOW_HID)
        htb.set_size_request(HTB_SSR, HTB_SSR)
        if hidden_state == True:
            htb.set_active(False)
        elif hidden_state == False:
            htb.set_active(True)
        htb.connect("toggled", self.on_toggle_htb)
        # box for the three buttons
        tbbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tbbox.pack_start(htb, False, False, 5)
        #
        # invert the selection
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("invert.svg", HTB_SSR, HTB_SSR)
        invsel_image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.invsel_button = Gtk.Button(label="", image=invsel_image)
        self.invsel_button.set_tooltip_text(I_INV_SEL)
        tbbox.pack_end(self.invsel_button, False, False, 5)
        self.invsel_button.connect("clicked", self.on_invsel_button)
        
        return tbbox

    
    # the tab page label
    def create_nlabel(self, page):
        box200 = Gtk.Box()
        box200.set_orientation(orientation=Gtk.Orientation.HORIZONTAL)
        
        label200h = Gtk.Label(label=self.working_path)
        box200.pack_start(label200h, False, False, 0)
        label200h.hide()
        
        self.label200 = Gtk.Label()
        
        if self.working_path == "/":
            self.label200.set_text("ROOT")
        else:
            self.label200 = Gtk.Label(label=os.path.basename(self.working_path))
        
        self.label200.set_max_width_chars(15)
        self.label200.set_width_chars(15)
        self.label200.set_ellipsize(Pango.EllipsizeMode.END)
        self.label200.set_hexpand(True)
        self.label200.set_justify(Gtk.Justification.CENTER)
        
        image = Gtk.Image(stock=Gtk.STOCK_CLOSE)
        buttonclose = Gtk.Button()
        buttonclose.set_image(image)
        buttonclose.set_relief(Gtk.ReliefStyle.NONE)
        buttonclose.connect("clicked", self.on_buttonclose_clicked, page)
        box200.pack_start(self.label200, True, True, 0)
        box200.add(buttonclose)
        self.label200.show()
        buttonclose.show()
        return box200


    def create_info_page(self, item_name, working_dir):
        # create a new box
        self.npmainbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        l201=INAME+item_name+"\n"+IPATH+working_dir
        label201 = Gtk.Label(label=l201)
        label201.set_line_wrap(True)
        self.npmainbox.pack_end(label201, False, False, 20)
        infopixbuf = Gtk.Image.new_from_pixbuf(self.evaluate_pixbuf(item_name, working_dir, NB2_ICON_SIZE))
        self.npmainbox.pack_start(infopixbuf, False, False, 20)
        pagen = Gtk.Box()
        pagen.add(self.npmainbox)
        try:
            # Infos is at position 1
            self.notebook2.remove_page(0)
        except:
            pass
        self.npmainbox.show_all()
        pagen.show()
        labelinfo = Gtk.Label()
        labelinfo.set_markup("<span size='small'>"+INFO_NAME+"</span>")
        self.notebook2.append_page(pagen, labelinfo)


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


    #  find the size of selected item
    def item_size(self, path):
        try:
            fsize2 = os.stat(path).st_size
        except:
            fsize2 = 0
        if fsize2 == 0 or fsize2 == 1:
            sfsize = str(fsize2)+" byte"
        elif fsize2//1024 == 0:
            sfsize = str(fsize2)+" bytes"
        elif fsize2//1048576 == 0:
            sfsize = str(round(fsize2/1024, 3))+" KB"
        elif fsize2//1048576 < 100:
            sfsize = str(round(fsize2/1048576, 3))+" MB"
        else:
            sfsize = str(round(fsize2/1048576))+" MB"
        
        return sfsize


    # find the size of folders
    def folder_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for fl in filenames:
                flp = os.path.join(dirpath, fl)
                if os.access(flp, os.R_OK):
                    # if link skip it
                    if os.path.islink(flp):
                        continue
                    total_size += os.path.getsize(flp)
        return total_size


    # close button in the page of notebook1
    def on_buttonclose_clicked(self, buttonclose, page):
        self.IV.unselect_all()
        curpage = self.notebook.page_num(page)
        numpage = self.notebook.get_n_pages()
        if numpage > 1:
            self.monitor_stop()
            page.destroy()
        if (numpage - 1) == 1:
            self.notebook.set_show_tabs(False)


    # when CTRL+ALT+A 
    def on_unselect_all(self, infopixbuf, visible_item, hidden_item):
        self.unselect_all_common(infopixbuf, visible_item, hidden_item)


    def unselect_all_common(self, infopixbuf, visible_item, hidden_item):
        self.IV.unselect_all()
        
        self.npmainbox.remove(self.npmainbox.get_children()[0])
        infopixbuf = Gtk.Image.new_from_pixbuf(self.evaluate_pixbuf(working_dir, NB2_ICON_SIZE))
        self.npmainbox.pack_start(infopixbuf, False, False, 20)
        infopixbuf.show()


    # invert the selection
    def on_invsel_button(self, invsel_button):
        selected_treepath = self.IV.get_selected_items()
        self.IV_selected_items = []
        self.IV.select_all()
        if selected_treepath:
            for tp in selected_treepath:
                self.IV_selected_items = []
                self.IV.unselect_path(tp)
        self.IV.grab_focus()
    
############# MOUSE functions ###############
    
    def on_selection_changed(self, IV):
        
        if self.ppoint == 1:
            return
        
        if IV_MULTI_SEL == 0:
            for tpath in self.IV_selected_items:
                IV.select_path(tpath)
        elif IV_MULTI_SEL == 1:
            for tpath in IV.get_selected_items():
                 if not tpath in self.IV_selected_items:
                    self.IV_selected_items.append(tpath)
            for ppath in self.IV_selected_items:
                if ppath != None:
                    IV.select_path(ppath)
        
        if len(IV.get_selected_items()) == 1:
            rrow = IV.get_selected_items()[0]
            row = IV.get_selected_items()[0]
            pixbuf = self.modello[row][0]
            infopixbuf = Gtk.Image.new_from_pixbuf(pixbuf)
            self.npmainbox.remove(self.npmainbox.get_children()[0])
            self.npmainbox.pack_start(infopixbuf, False, False, 20)
            infopixbuf.show()
            # the labels
            item_path = os.path.join(self.modello[rrow][3], self.modello[rrow][1])
            self.label300name.set_markup("<i>"+INAME+"</i>")
            #
            self.label301name.set_line_wrap_mode(2)
            if os.path.islink(item_path):
                link_realpath = os.path.realpath(item_path)
                if os.path.exists(link_realpath):
                    self.label301name.set_label("{}\n(Link to: {})".format(self.modello[rrow][1], link_realpath))
                else:
                    self.label301name.set_label("{}\n(Broken link to: {})".format(self.modello[rrow][1], link_realpath))
            else:
                self.label301name.set_label("{}".format(self.modello[rrow][1]))
            self.label300path.set_markup("<i>"+IPATH+"</i>")
            self.label302path.set_label("{}".format(self.modello[rrow][3]))
            item_mime = self.item_mime(item_path)
            self.label300type.set_markup("<i>"+ITYPE+"</i>")
            self.label303type.set_label("{}".format(item_mime))
            # size or number of items
            type_of_item = self.modello[rrow][2]
            if type_of_item == "a":
                try:
                    num_of_item = len(os.listdir(item_path))
                    self.label300size.set_markup("<i>"+IITEMS+"</i>")
                except:
                    self.label300size.set_markup("<i>"+IITEMS+"</i>")
                    num_of_item = 0
                item_dim = self.folder_size(item_path)
                r_item_dim = convert_size2(item_dim)
                self.label304size.set_label("{}  ({})".format(num_of_item, r_item_dim))
            elif type_of_item == "b":
                isize = self.item_size(item_path)
                self.label300size.set_markup("<i>"+ISIZE+"</i>")
                self.label304size.set_label("{}".format(isize))
            # the Data page
            if self.meta_page.get_children():
                self.meta_page.remove(self.meta_page.get_children()[0])
            meta_box = self.metadata_box(item_path)
            self.meta_page.pack_start(meta_box, True, True, 0)
        
        elif len(IV.get_selected_items()) > 1:
            if self.meta_page.get_children():
                self.meta_page.remove(self.meta_page.get_children()[0])
            self.npmainbox.remove(self.npmainbox.get_children()[0])
            infopixbuf = Gtk.Image.new_from_pixbuf(self.evaluate_pixbuf(self.working_path, NB2_ICON_SIZE))
            self.npmainbox.pack_start(infopixbuf, False, False, 20)
            infopixbuf.show()
            
            self.label300name.set_markup("<i>"+IPATH+"</i>")
            self.label301name.set_line_wrap_mode(0)
            self.label301name.set_text("{}".format(self.working_path))
            self.label300path.set_markup("<i>"+ISELITM+"</i>")
            self.label302path.set_text("{}".format(len(IV.get_selected_items())))
            
            if IV_MULTI_SIZE == 1:
                total_items_size = 0
                for rrow in IV.get_selected_items():
                    item_path = os.path.join(self.modello[rrow][3], self.modello[rrow][1])
                    if self.modello[rrow][2] == "a":
                        f_item_dim = self.folder_size(item_path)
                        total_items_size += f_item_dim
                    elif self.modello[rrow][2] == "b":
                        i_item_dim = os.stat(item_path).st_size
                        total_items_size += i_item_dim
                r_total_items_size = convert_size2(total_items_size)
                self.label300type.set_label(ITMSIZE)
                self.label303type.set_label("{}".format(r_total_items_size))
            else:
                self.label300type.set_label("")
                self.label303type.set_label("")
            
            self.label300size.set_label("")
            self.label304size.set_label("")
        
        else:
            if self.meta_page.get_children():
                self.meta_page.remove(self.meta_page.get_children()[0])
            self.npmainbox.remove(self.npmainbox.get_children()[0])
            infopixbuf = Gtk.Image.new_from_pixbuf(self.evaluate_pixbuf(self.working_path, NB2_ICON_SIZE))
            self.npmainbox.pack_start(infopixbuf, False, False, 20)
            infopixbuf.show()
            visible_item, hidden_item = self.num_itemh(self.working_path)
            self.label300name.set_markup("<i>"+IPATH+"</i>")
            self.label301name.set_line_wrap_mode(0)
            self.label301name.set_text(self.working_path)
            self.label300path.set_markup("<i>"+IITEMS+"</i>")
            self.label302path.set_text("{}".format(visible_item))
            self.label300type.set_markup("<i>"+IHIDDEN+"</i>")
            self.label303type.set_text("{}".format(hidden_item))
            self.label300size.set_text("")
            self.label304size.set_text("")
            self.label300size.set_markup("<i>"+ISIZE2+"</i>")
            self.label304size.set_text("{}".format(convert_size2(shutil.disk_usage(self.working_path).free)))
        
        # add the custom modules
        for el in list_custom_modules:
            if el.mmodule_type() == 2:
                el.on_change_npage(self)

    
    # for data page of notebook2
    def metadata_box(self, item_path):
        meta_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        mbsw = Gtk.ScrolledWindow()
        mbsw.set_policy(Gtk.PolicyType.NEVER,  Gtk.PolicyType.AUTOMATIC)
        meta_box.pack_start(mbsw, True, True, 0)
        
        # grid
        meta_grid = Gtk.Grid()
        meta_grid.set_border_width(10)
        meta_grid.set_row_spacing(10)
        meta_grid.set_column_spacing(10)
        mbsw.add(meta_grid)

        if DATE_TIME == 0:
            try:
                mctime = datetime.datetime.fromtimestamp(os.stat(item_path).st_ctime).strftime('%c')
            except:
                mctime = 0
        elif DATE_TIME == 1:
            try:
                mctime1 = subprocess.check_output(["stat", "-c", "%W", item_path], universal_newlines=False).decode()
                mctime2 = subprocess.check_output(["date", "-d", "@{}".format(mctime1)], universal_newlines=False).decode()
                mctime = mctime2.strip("\n")
            except:
                mctime = 0
        
        label20 = Gtk.Label()
        label20.set_markup("<i>"+ICREATED+"</i>")
        label20.props.xalign = 1
        meta_grid.attach(label20, 0,1,1,1)
        label21 = Gtk.Label(label=mctime)
        label21.props.xalign = 0
        meta_grid.attach(label21, 1,1,1,1)
        #
        try:
            mmtime = datetime.datetime.fromtimestamp(os.stat(item_path).st_mtime).strftime('%c')
        except:
            mmtime = 0
        label30 = Gtk.Label()
        label30.set_markup("<i>"+IMODIFIED+"</i>")
        label30.props.xalign = 1
        meta_grid.attach(label30, 0,2,1,1)
        label31 = Gtk.Label(label=mmtime)
        label31.props.xalign = 0
        meta_grid.attach(label31, 1,2,1,1)
        #
        try:
            matime = datetime.datetime.fromtimestamp(os.stat(item_path).st_atime).strftime('%c')
        except:
            matime = 0
        label40 = Gtk.Label()
        label40.set_markup("<i>"+ILASTACCESS+"</i>")
        label40.props.xalign = 1
        meta_grid.attach(label40, 0,3,1,1)
        label41 = Gtk.Label(label=matime)
        label41.props.xalign = 0
        meta_grid.attach(label41, 1,3,1,1)
        #
        meta_box.show_all()
        
        return meta_box
    
    
    def on_mouse_button_pressed(self, IV, event):
        
        if event.button == 1:
            target = IV.get_path_at_pos(int(event.x), int(event.y))
            if target == None:
                IV.unselect_all()
                self.IV_selected_items = []
            
            Ctrl = (event.state & Gdk.ModifierType.CONTROL_MASK)
            if Ctrl:
                if target in self.IV_selected_items:
                    self.IV_selected_items.remove(target)
                else:
                    self.IV_selected_items.append(target)
            elif not Ctrl:
                if not target in self.IV_selected_items:
                    self.IV_selected_items = []
        
        # unselect all with the middle mouse button
        elif event.button == 2:
            self.IV_selected_items = []
            IV.unselect_all()
        
        elif event.button == 3:
            target = IV.get_path_at_pos(int(event.x), int(event.y))
            all_target = IV.get_selected_items()
            if target == None:
                IV.unselect_all()
                mpop = Gtk.Menu()
                self.populate_background_menu(mpop)
            else:
                if target in all_target:
                    mpop = Gtk.Menu()
                    self.populate_menu(mpop)
                else:
                    self.IV_selected_items = []
                    IV.unselect_all()
                    IV.select_path(target)
                    mpop = Gtk.Menu()
                    self.populate_menu(mpop) 
    
    
    def on_mouse_release(self, IV, event):
        for tpath in IV.get_selected_items():
            if not tpath in self.IV_selected_items:
                self.IV_selected_items.append(tpath)
    
    
    # right click menu on background
    def populate_background_menu(self, mpop):
        #
        ### new folder
        item0001 = Gtk.MenuItem(label=INEWFOLDER)
        mpop.append(item0001)
        item0001.connect("activate", self.new_folder)
        ### new file
        item0002 = Gtk.MenuItem(label=INEWFILE)
        mpop.append(item0002)
        item0002.connect("activate", self.new_file)
        # separator
        mpop.append(Gtk.SeparatorMenuItem())
        ### file from template
        dir_templates = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES)
        # if the Templates path is not set fallback to Templates
        if not dir_templates:
            dir_templates = HOME+"/"+"Templates"
        
        try:
            list_templates = os.listdir(dir_templates.strip("\n"))
        except:
            list_templates = []
        if dir_templates:
            
            if list_templates:
                item0010 = Gtk.MenuItem(label=os.path.basename(dir_templates.strip("\n")))
                mpop.append(item0010)
                # submenu
                mpop2 = Gtk.Menu()
                for el in list_templates:
                    itemsm = Gtk.MenuItem(label=el)
                    itemsm.connect("activate", self.template_activated, dir_templates.strip("\n"), el)
                    mpop2.append(itemsm)
                #
                item0010.props.submenu = mpop2
                
                mpop.append(Gtk.SeparatorMenuItem())
        #
        ### paste
        item0020 = Gtk.MenuItem(label=IPASTE)
        mpop.append(item0020)
        # if no data to paste set item to insensitive
        item0020.set_sensitive(False)
        # 
        if ITEMS_TO_COPY:
            item0020.set_sensitive(True)
            item0020.connect("activate", self.on_paste)
        ### custom modules
        if menu_bg_module:
            for el in menu_bg_module:
                # avoid errors
                try:
                    if el.enabled(None) == 1:
                        if el.ttype() == 2 or el.ttype() == 3:
                            
                            mcommand = el.ccommand(self)
                            mposition = el.pposition()
                            
                            item =  Gtk.MenuItem(label=el.nname())
                            if mposition == -1:
                                # separator
                                mpop.append(Gtk.SeparatorMenuItem())
                                mpop.append(item)
                            else:
                                mvalue = int(mposition[0])
                                mpos = int(mposition[1:])
                                if mvalue == 1:
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos)
                                    mpop.insert(item, mpos+1)
                                elif mvalue == 2:
                                    mpop.insert(item, mpos)
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos+1)
                                if mvalue == 3:
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos)
                                    mpop.insert(item, mpos+1)
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos+2)
                                else:
                                    mpop.insert(item, mpos)

                            #
                            item.connect("activate", self.item_connect, mcommand, el)
                            
                except:
                    pass
        
        mpop.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        time.sleep(0.3)
        mpop.show_all()
        self.IV.grab_focus()


    # create a new folder
    def new_folder(self, widget):
        dest_dir = os.path.join(self.working_path, INEWFOLDER2) 
        try:
            # list the items in the current dir
            NAMES = os.listdir(self.working_path)
        except:
            NAMES = []
        ret = ""
        
        while ret in NAMES or ret == None or ret == "":
            
            ret = self.on_new_name(ICHOOSENAMEFOLD, os.path.basename(dest_dir), "")
            if ret == -6:
                return
            
        fpath = os.path.join(self.working_path, ret)
        
        try:
            os.makedirs(fpath)
        except Exception as e:
            self.generic_dialog("\n"+str(e), "")
        
        self.IV.grab_focus()
    
    
    # create a new file
    def new_file(self, widget):
        dest_file = os.path.join(self.working_path, INEWFILE)
        try:
            # list the items in the current dir
            NAMES = os.listdir(self.working_path)
        except:
            NAMES = []
        ret = ""
        
        while ret in NAMES or ret == None or ret == "":
            
            ret = self.on_new_name(ICHOOSENAMEFILE, os.path.basename(dest_file), "")
            if ret == -6:
                return
            
        fpath = os.path.join(self.working_path, ret)
        
        try:
            os.mknod(fpath, mode=0o644)
        except Exception as e:
            self.generic_dialog("\n"+str(e), "")
        
        self.IV.grab_focus()
    
    
    # copy the template at destination
    def template_activated(self, widget, dir_templates, model):
        src = os.path.join(dir_templates, model)
        dest = self.working_path
        if os.path.isdir(src):
            try:
                dest_dir = dest+"/"+os.path.basename(src)
                shutil.copytree(src, dest_dir, symlinks=True, ignore=None)
            except:
                pass
        elif os.path.isfile(src):
            try:
                shutil.copy2(src, dest)
            except Exception as e:
                self.generic_dialog("\n"+str(e), "")
        
        self.IV.grab_focus()
    
    
    # open with other applications
    def on_other_applications(self, widget, fpath):
        # find the mimetype
        file = Gio.File.new_for_path(fpath)
        file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
        fmime = Gio.FileInfo.get_content_type(file_info)
        #
        dialog = Gtk.AppChooserDialog.new_for_content_type(self.window, 0, fmime)
        if (dialog.run () == Gtk.ResponseType.OK):
            appinfo = dialog.get_app_info()
            alist = appinfo.get_recommended_for_type(fmime)
            if appinfo:
                # open the file
                gpath = Gio.File.new_for_path(fpath)
                appinfo.launch((gpath,), None)
            
            dialog.destroy()
        else:
            dialog.destroy()
    
    
    # open the file with the program choosen
    def on_open_aa(self, widget, executable, fpath):
        if shutil.which(executable):
            try:
                subprocess.Popen([executable, fpath])
            except Exception as e:
                self.generic_dialog("\n"+str(e), "")


    # open the selected folder in a new tab
    def on_open_in_a_new_tab(self, widget, fpath):
        wiconview(fpath, self.window, 1, "")
    
    
    # RMB menu
    def populate_menu(self, mpop):
        #
        multi_fpath = []
        for arow in self.IV.get_selected_items():
            fname = self.modello[arow][1]
            dname = self.modello[arow][3]
            multi_fpath.append(os.path.join(dname, fname))
        #
        rrow = self.IV.get_selected_items()[0]
        #
        nfile = self.modello[rrow][1]
        fpath = os.path.join(self.working_path, nfile)
        #
        if self.modello[rrow][2] == "a":
            itemnf = Gtk.MenuItem(label=IOPENNT)
            mpop.append(itemnf)
            # open the folder into a new tab
            itemnf.connect("activate", self.on_open_in_a_new_tab, fpath)

        # Open With
        item0000 = Gtk.MenuItem(label=IOPENWITH)
        mpop.append(item0000)
        # other applications submenu
        mpopaa = Gtk.Menu()
        # other applications
          # find the mimetype
        file = Gio.File.new_for_path(fpath)
        try:
            file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
        except Exception as e:
            self.generic_dialog("\n"+str(e), "")
            return
        fmime = Gio.FileInfo.get_content_type(file_info)
          #
        dialog = Gtk.AppChooserDialog.new_for_content_type(self.window, 0, fmime)
        #
        item0000.props.submenu = mpopaa
        appinfo = dialog.get_app_info()
        if appinfo:
            alist = appinfo.get_recommended_for_type(fmime)
            for el in alist:
                item = Gtk.MenuItem(label=el.get_display_name())
                mpopaa.append(item)
                # open the file
                item.connect("activate", self.on_open_aa, el.get_executable(), fpath)
            # separator
            mpopaa.append(Gtk.SeparatorMenuItem())
        
        # other applications dialog
        itemaa = Gtk.MenuItem(label=IOTHERAPP)
        itemaa.connect("activate", self.on_other_applications, fpath)
        mpopaa.append(itemaa)
        
        # separator
        mpop.append(Gtk.SeparatorMenuItem())
        
        # new folder
        item0001 = Gtk.MenuItem(label=INEWFOLDER)
        mpop.append(item0001)
        item0001.connect("activate", self.new_folder)
        
        # new file
        item0002 = Gtk.MenuItem(label=INEWFILE)
        mpop.append(item0002)
        item0002.connect("activate", self.new_file)
        
        # make a link
        item0006 = Gtk.MenuItem(label=IMAKELINK)
        mpop.append(item0006)
        #
        if len(multi_fpath) > 1:
            item0006.set_sensitive(False)
        item0006.connect("activate", self.make_link, nfile)
        
        # separator
        mpop.append(Gtk.SeparatorMenuItem())
        
        # cut
        item0011 = Gtk.MenuItem(label=ICUT)
        mpop.append(item0011)
        item0011.connect("activate", self.on_copy, "cut")
        
        # copy
        item0010 = Gtk.MenuItem(label=ICOPY)
        mpop.append(item0010)
        item0010.connect("activate", self.on_copy, "copy")
        
        # paste
        item0020 = Gtk.MenuItem(label=IPASTE)
        mpop.append(item0020)
        # if no data to paste set item to insensitive
        item0020.set_sensitive(False)
        
        #
        if ITEMS_TO_COPY:
            item0020.set_sensitive(True)
            item0020.connect("activate", self.on_paste)
        
        # separator
        mpop.append(Gtk.SeparatorMenuItem())
        
        # rename
        item01 = Gtk.MenuItem(label=IRENAME)
        mpop.append(item01)
        item01.connect("activate", self.rename_item, fpath)
        
        # move to trashcan
        if fpath[0:5] == "/home":
            item10 = Gtk.MenuItem(label=IMOVETOTRASH)
            mpop.append(item10)
            item10.connect("activate", self.trash_item)
        
        # delete
        item11 = Gtk.MenuItem(label=IDELETE)
        mpop.append(item11)
        item11.connect("activate", self.delete_item)
        
        #
        if len(self.IV.get_selected_items()) > 1:
            item0000.destroy()
            item01.destroy()
        
        # custom modules
        if menu_bg_module:
            #for mods in mmod_bg:
            for el in menu_bg_module:
                # avoid errors
                try:
                    if el.enabled(multi_fpath) == 1:
                        if el.ttype() == 1 or el.ttype() == 3:
                            
                            mcommand = el.ccommand(self)
                            # position in the menu
                            mposition = el.pposition()
                            
                            item =  Gtk.MenuItem(label=el.nname())
                            if mposition == -1:
                                # separator
                                mpop.append(Gtk.SeparatorMenuItem())
                                mpop.append(item)
                            else:
                                mvalue = int(mposition[0])
                                mpos = int(mposition[1:])
                                if mvalue == 1:
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos)
                                    mpop.insert(item, mpos+1)
                                elif mvalue == 2:
                                    mpop.insert(item, mpos)
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos+1)
                                if mvalue == 3:
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos)
                                    mpop.insert(item, mpos+1)
                                    mpop.insert(Gtk.SeparatorMenuItem(), mpos+2)
                                else:
                                    mpop.insert(item, mpos)
                            
                            item.connect("activate", self.item_connect, mcommand, el)
                        
                except:
                    pass
        
        mpop.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        time.sleep(0.3)
        mpop.show_all()
        self.IV.grab_focus()

    
    # the command to execute for the selected item in the menu
    def item_connect(self, widget, mcommand, el):
        if mcommand:
            subprocess.Popen(mcommand, universal_newlines=True)
        else:
            el.ModuleClass(self)
    
    
    # make a link
    def make_link(self, widget, nfile):
        if os.access(self.working_path, os.W_OK):
            dest = os.path.join(self.working_path, ILINKTO+nfile)
            if os.path.exists(dest):
                ii = 1
                while ii:
                    nn = ILINKTO+"("+str(ii)+") "+nfile
                    dst = os.path.join(self.working_path, nn)
                    if os.path.exists(dst):
                        ii += 1
                    else:
                        dest = os.path.join(self.working_path, ILINKTO+"("+str(ii)+") "+nfile)
                        ii = 0
            os.symlink(os.path.join(self.working_path, nfile), dest)

############## RENAME

    def rename_item(self, widget, fpath):
        try:
            # list the items in the dir
            NAMES = os.listdir(os.path.dirname(fpath))
        except:
            NAMES = []
        ret = ""
        if NAMES:
            while ret in NAMES or ret == None or ret == "":
                ret = self.on_new_name(IENTERNNAMEFOR, os.path.basename(fpath), "")
                if ret == -6:
                    return
                
            dest = os.path.join(os.path.dirname(fpath), ret)
            try:
                os.rename(fpath, dest)
            except Exception as e:
                self.generic_dialog("\n"+str(e), "")

############## DELETE

    def trash_item(self, widget):
        dialog = DialogYN(self.window, "Message", IMOVETOTRASHMSG)
        response = dialog.run()
        self.IV.grab_focus()
        #
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        #
        for i in range(len(self.IV.get_selected_items())):
            rrow = self.IV.get_selected_items()[i]
            nfile = self.modello[rrow][1]
            path = os.path.join(self.working_path, nfile)
            # only the home trashcan is handled
            if path[0:5] != "/home":
                return
            gio_file = Gio.File.new_for_path(path)
            try:
                ret = gio_file.trash()
                if ret == False:
                    self.generic_dialog(IRECBIN1, IRECBIN2)
            except Exception as E:
                self.generic_dialog("Message", str(E))
        
        self.IV_selected_items = []
        if self.IV.get_selected_items():
            self.IV.unselect_all()
        self.IV.grab_focus()

    
    # delete the items by RMB menu
    def delete_item(self, widget):
        dialog = DialogYN(self.window, "Message", IDELETEMSG2)
        response = dialog.run()
        self.IV.grab_focus()
        #
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return
        #
        for i in range(len(self.IV.get_selected_items())):
            rrow = self.IV.get_selected_items()[i]
            nfile = self.modello[rrow][1]
            path = os.path.join(self.working_path, nfile)
            
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception as E:
                    self.generic_dialog("Message", str(E))
            elif os.path.isdir(path):
                try:
                    shutil.rmtree(path)
                except Exception as E:
                    self.generic_dialog("Message", str(E))
        
        self.IV_selected_items = []
        if self.IV.get_selected_items():
            self.IV.unselect_all()
        self.IV.grab_focus()

################## copy/cut functions ##############
    
    # called on copy or cut from RMB (no DnD)
    def on_copy(self, widget, operation):
        
        cc_list = ''
        
        cc_list += operation
        
        sel_item = self.IV.get_selected_items()
        model = self.IV.get_model()
        for irow in range(len(self.IV.get_selected_items())):
            
            rrow = self.IV.get_selected_items()[irow]
            sfile = model[rrow][1]
            path = os.path.join(self.working_path, sfile)
            
            # only if items are links or regular files or folders
            if os.path.isfile(path) or os.path.isdir(path) or os.path.islink(path):
                cc_list += "\n"
                qpath = quote("file://{}".format(path), safe='/:?=&')
                cc_list += qpath
        if cc_list != "copy" or cc_list != "cut":
            sent_items = cc_list.encode()
            
            try:
                # add to list
                global ITEMS_TO_COPY
                ITEMS_TO_COPY = items_copy_clip.copyClip(self.working_path, sent_items, 0).listReturn()
            except Exception as e:
                self.generic_dialog("\n"+str(e), "")
        
        self.IV.grab_focus()
  
################## past functions ##################
  
    def paste_operation(self):
        global ITEMS_TO_COPY
        #
        if ITEMS_TO_COPY:
            if ITEMS_TO_COPY != -1:
                # or_dir = os.path.dirname(DATA2[0])
                items_copy.CopyDialog(self.working_path, ITEMS_TO_COPY, self.window, 0)
                # reset
                ITEMS_TO_COPY = None
            # with clipboard in the module
            else:
                items_copy_clip.copyClip(self.working_path, ITEMS_TO_COPY, 0)
        
        #self.IV.grab_focus()


    # paste item(s)
    def on_paste(self, widget):
        self.paste_operation()


################# DRAG n DROP ################

### DRAG

    def on_drag_data_get(self, IV, context, selection, info, time):
        
        lfpath = ""
                
        model = IV.get_model()
        
        if IV.get_selected_items() != None:
            for ii in range(len(IV.get_selected_items())):
                
                rrow = IV.get_selected_items()[ii]
                sfile = model[rrow][1]
                path = os.path.join(self.working_path, sfile)
                
                #if os.access(path, os.R_OK):
                # only if items are links or regular files or folders
                if os.path.isfile(path) or os.path.isdir(path) or os.path.islink(path):
                    lfpath += "\n"
                    lfpath += quote("file://{}".format(os.path.join(self.working_path, path)), safe='/:?=&')
        selection.set(selection.get_target(), 8, lfpath.encode())
    
    
    def on_drag_begin(self, IV, context):
        if len(IV.get_selected_items()) > 1:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file('items_multi.svg')
            Gtk.drag_set_icon_pixbuf(context, pixbuf, 10, 10)
        elif len(IV.get_selected_items()) == 1:
            model = IV.get_model()
            row = IV.get_selected_items()[0]
            pixbuf = model[row][0]
            Gtk.drag_set_icon_pixbuf(context, pixbuf, 10, 10)
            

    def on_drag_end(self, IV, context):
        return True

    def on_drag_failed(self, IV, context, result):
        pass

    def on_drag_data_delete(self, IV, context):
        pass

#### DROP

    def on_drag_drop(self, IV, context, x, y, time):
        IV.stop_emission_by_name('drag-drop')
        IV.drag_get_data(context, Gdk.Atom.intern('text/uri-list', False), time)
        return True

    def on_drag_motion(self, IV, context, x, y, time):
        return False
    
    # drop
    def on_drag_data_received(self, IV, context, x, y, selection, info, time):
        
        IV.stop_emission_by_name('drag-data-received')
        
        DATA = selection.get_uris()
        
        if len(DATA) > 0:
            
            CON_ACT = context.get_selected_action()
            
            #### manage the data
            # not in the same folder
            dest_path = os.path.dirname(DATA[0])
            #
            if dest_path[7:] == self.working_path:
                context.finish(False, False, time)
                return
            
            if DATA:
                if CON_ACT == 2:
                    CONACT = "copy"
                elif CON_ACT == 4:
                    CONACT = "cut"
                elif CON_ACT == 8:
                    CONACT = "link"
                #
                list_items_temp = ""
                list_items_temp += CONACT
                #
                for item in DATA:
                    list_items_temp += "\n"+item
                list_items = list_items_temp.encode()
                items_copy.CopyDialog(self.working_path, list_items, self.window, 0)
                #
                context.finish(True, False, time)
            else:
                context.finish(False, False, time)
        else:
            context.finish(False, False, time)


##################### COMMON OPERATIONS ####################
    
    # if destination has already an item
    # with the same name of the dropped one
    # a dialog appears
    def on_new_name(self, message1, ndata, message2):
        NEW_NAME = None
        # get the new name from the dialog
        win2 = DialogRename(self.window, message1, ndata, message2)
        
        response = win2.run()
        if response == Gtk.ResponseType.OK:
            NEW_NAME = win2.entry.get_text()
            win2.destroy()
        else:
            NEW_NAME = -6
            win2.destroy()
        return NEW_NAME


    # generic dialog
    def generic_dialog(self, message1, message2):
        dialog = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=message1)
        dialog.format_secondary_text("{}".format(message2))
        dialog.run()
        dialog.destroy()


# the dialog for changing the name of files and links
# if already present at destination
class DialogRename(Gtk.Dialog):
    
    def __init__(self, parent, message1, nname, message2):
        
        Gtk.Dialog.__init__(self, title=IENTERNEWNAME, transient_for=parent, flags=0)
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.set_default_size(700, 100)

        label1 = Gtk.Label(label="\n{}:".format(message1))
        label2 = Gtk.Label(label="{}\n{}".format(nname, message2))
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

    def on_return(self):
        return self.IVBox


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

#############

def win_quit(widget):
    Gtk.main_quit()

app = mainwindow()
app.connect("destroy", win_quit)
wiconview(wworking_dir, app, 1, "")
app.show()
Gtk.main()
