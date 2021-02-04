#!/usr/bin/env python3
from urllib.parse import unquote, quote

class copyClip:
    def __init__(self, working_path, list_file, flag):
        self.working_path = working_path
        self.list_file = list_file
        self.list_items = unquote(self.list_file.decode()).split('\n')
    
    # list to return, -1 disable internal paste code
    def listReturn(self):
        return self.list_file
    
    # use the clipboard
    def useClipboard(self):
        pass
