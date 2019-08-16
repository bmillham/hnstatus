#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" Read status from a HN Modem """

# pylint: disable=invalid-name

from hnmodemstatus.hnmodemstatus import HnModemStatus
from hngui.hngui import HnGui
import os

if __name__ == '__main__':
    hn = HnModemStatus(ip='192.168.0.1')

    # Get the directory of this file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    glade_file = os.path.join(dir_path, 'hnstatus.glade')
    icon_cache = os.path.join('/run/user', str(os.getuid()), 'icon_cache')
    if not os.path.exists(icon_cache):
        os.mkdir(icon_cache)

    # Build the GUI
    gui = HnGui(path=dir_path,
                file=glade_file,
                hnstat=hn,
                icon_cache=icon_cache)

    # Display the GUI
    gui.window1.show_all()

    # Set autorefresh
    gui.auto_refresh_button.set_active(True)

    # Run Gtk
    gui.gtk.main()
