#!/usr/bin/env python3

"""
DEMO: add the mimetype above the file name
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio
import os

M1NAME = "Module1"

# mime type of the file
def add_description(model):
    for row in model:
        path = os.path.join(row[3], row[1])
        file = Gio.File.new_for_path(path)
        file_info = file.query_info('standard::content-type', Gio.FileQueryInfoFlags.NONE, None)
        mime = Gio.FileInfo.get_content_type(file_info)
        row[7] = mime.split("/")[1]
    

