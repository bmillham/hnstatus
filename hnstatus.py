#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" Read status from a HN Modem """

# pylint: disable=invalid-name

from hnmodemstatus.hnmodemstatus import HnModemStatus
from hngui.hngui import HnGui
import os
import argparse
import ipaddress

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', help='IP address of the HN Modem')
    args = parser.parse_args()
    if not args.ip:
        args.ip = '192.168.0.1'
    try:
        ipaddress.ip_address(args.ip)
    except ValueError:
        print('IP address is invalid:', args.ip)
        exit(1)

    hn = HnModemStatus(ip=args.ip)

    # Get the directory of this file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    glade_file = os.path.join(dir_path, 'hnstatus.glade')

    # Build the GUI
    gui = HnGui(path=dir_path,
                file=glade_file,
                hnstat=hn)

    # Display the GUI
    gui.window1.show_all()

    # Set autorefresh
    gui.auto_refresh_button.set_active(True)

    # Run Gtk
    gui.gtk.main()
