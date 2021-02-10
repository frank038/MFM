#!/usr/bin/env python3


class copyClip:
    def __init__(self, IV):
        self.IV = IV
    
    # set the clipboard with the items and the action 
    def on_cc_copycut(self):
        # return: [1, ""] if success with setting the clipboard otherwise [False, "msg"]
        # return [2, ""] to use the internal method
        return [2, ""]
    
    # get the items and the action from the clipboard (or the internal module)
    def on_cc_paste(self):
        # if no data: [0, ""]
        # if got data from the clipboard: [1, "data"]
        # if the internal function must be used: [2, ""]
        if self.IV.window.ITEMS_TO_COPY:
            return [2, ""]
        else:
            return [0, ""]
    
    # # perform some tasks in the end
    # def end_cc(self):
        # return
    
