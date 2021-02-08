### main program
# the size of this program icon
ITSIZE = 24
# use the headbar instead of the window manager: 0 no - 1 yes
# buggy - use 0
USE_HEADB = 0
### iconview module
# icon size
ICON_SIZE2 = 48
# link symbol size
LINK_SIZE2 = 24
# icon size in notebook2 - actually do nothing
NB2_ICON_SIZE = 96
# use thumbnailers: 0 No - 1 Yes
USE_THUMB = 0
# thumbnail image size
THUMB_SIZE2 = 64
# iconview item with - -1 automatic
IV_ITEM_WIDTH = 128
# size of the notebook2 buttons
HTB_SSR = 24
# double click on a folder: 1 open a new tab - 0 close the parent tab
IV_OPEN_FOLDER = 0
# add optional text to each icon other then name: 0 NO, 1 Yes
IV_USE_OPT_INFO = 0
# calculate the total size of the selected items in multiselection: 0 disabled
IV_MULTI_SIZE = 1
# multiselection: 0 dinamic - 1 static
IV_MULTI_SEL = 0
# use the drag and drop: 0 no - 1 yes 
IV_DND = 1
# creation data and time of the item: 0 use os.stat - 1 use functions from bash (should be precise)
DATE_TIME = 1
# Theme to use: e.g. "Adwaita" - use "" to use the default one
USE_THEME = ""
# use dark variant: 0 no - 1 yes
USE_THEME_DARK = 0
# use an icon theme: e.g. "Papirus" - use "" to use the default one
USE_ICONS = ""
# update the program size automarically (some wm creates bug): 0 no - 1 yes
UPDATE_PROGRAM_SIZE = 1

### trash module
# date: 0 no - 1 yes
TR_DATE = 1
# how to sort the items in the trashcan: 0 by name - 1 by date - 2 by inverted date
TR_SORT = 2
# real time update: 0 no - 1 yes
TR_UPD = 1

### items_copy
# 0 use number _(#) - 1 use date (do not check) 
USE_DATE = 0

### needed by pythumb
# border color of thumbnail
BORDER_COLOR = 'black'
#
XDG_CACHE_LARGE = "sh_thumbnails/large/"
