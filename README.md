# MFM2
A file manager written in python and gtk3.
(work in testing)

Free to use and modify.

Features:
- drag and drop;
- copy/cut/paste (within the same program due to inexistent methods in pygtk3), the copying operation can be interrupted by the user (only for the items not copied yet);
- thumbnails and thumbnailers (require PIL for images, pdftocairo for pdf files and ffmpegthumbnailer for video files), 7z for extracting archives (also with password); more can be added for supporting almost all kind of files;
- trash (of the home dir) with items sorted by deletion data or name;
- custom modules;
- a lot of options can be enabled or disabled in the config file (cfg.py);
- some kind of customization.

Under Wayland, the option UPDATE_PROGRAM_SIZE must be 0.

![My image](https://github.com/frank038/MFM/blob/main/screenshot1.png)
