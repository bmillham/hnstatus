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
    parser = argparse.ArgumentParser(
        description='Monitor a HT2000w Modem for status information',
        epilog='''When specifying color names, they must conform to
                  HTML names. See https://html-color-codes.info/color-names/
                  for a list of valid names''')
    parser.add_argument('-i', '--ip', help='IP address of the HN Modem')
    parser.add_argument('-b',
                        '--bonus-color',
                        default='blue',
                        help='Color of the bonus bar (Default: blue)')
    parser.add_argument('-a',
                        '--anytime-color',
                        default='green',
                        help='Color of the anytime bar (Default: green)')
    parser.add_argument('-s',
                        '--ss-colors',
                        default='black,fuchsia,gray',
                        help='''Comma separated list of the signal strength
                        bar colors.
                        The first value is for SS > 50,
                        The second value is for SS > 35 < 50
                        and the final value is for SS < 35.
                        (Default: black,fuchsia,gray)''')
    parser.add_argument('-t',
                        '--tx-rx-colors',
                        default='red,white',
                        help='''Comma separated list of the tx/rx indicator
                        colors. First value is for active, second value is
                        inactive. (Default: red,white)''')
    parser.add_argument('-g',
                        '--background-color',
                        default='white',
                        help='''Color of the statusicon background''')
    args = parser.parse_args()
    if not args.ip:
        args.ip = '192.168.0.1'
    try:
        ipaddress.ip_address(args.ip)
    except ValueError:
        print('IP address is invalid:', args.ip)
        exit(1)

    try:
        n, w, c = args.ss_colors.split(',')
    except ValueError:
        print('SS colors must be a comma separated list of 3 colors')
        exit(1)

    try:
        a, i = args.tx_rx_colors.split(',')
    except ValueError:
        print('Tx/Rx colors must be a comma separated list of 2 colors')

    hn = HnModemStatus(ip=args.ip)

    # Get the directory of this file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    glade_file = os.path.join(dir_path, 'hnstatus.glade')

    # Build the GUI
    gui = HnGui(path=dir_path,
                file=glade_file,
                bonus_color=args.bonus_color,
                anytime_color=args.anytime_color,
                ss_colors=args.ss_colors,
                tx_rx_colors=args.tx_rx_colors,
                background_color=args.background_color,
                hnstat=hn)

    # Display the GUI
    gui.window1.show_all()

    # Set autorefresh
    gui.auto_refresh_button.set_active(True)

    # Run Gtk
    gui.gtk.main()
