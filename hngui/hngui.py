""" Build the GUI and handle the signals """

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from hngui.icon import Icon  # noqa: E402
from gi.repository import Gtk, GObject, Notify, Gdk  # noqa: E402



class HnGui():
    """ Builds the Gtk GUI """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, path=None,
                 file=None,
                 hnstat=None,
                 bonus_color=None,
                 anytime_color=None,
                 ss_colors=None,
                 tx_rx_colors=None,
                 background_color=None,
                 window_x=0,
                 window_y=0,
                 config_file=None,
                 update_interval=1000):
        """ Create the GUI, but do not display it """

        signals = {
            'on_window1_destroy': self.quit,
            'on_auto_refresh_button_toggled': self.toggle_refresh,
            'populate': self.populate,
            'window_state_event': self.window_state_event,
            'about_item': self.about,
            'about-close-handler': self.about_close_handler,
        }

        self._last_status_warning = None
        self.hnstat = hnstat
        self.auto_update_source = None
        self.config_file = config_file

        self.gtk = Gtk

        builder = self.gtk.Builder()
        builder.add_from_file(file)
        builder.connect_signals(signals)

        # Get the objects that we will use
        self.window1 = builder.get_object('window1')
        self.about_window = builder.get_object('abouthnstatus')
        self.status_label = builder.get_object('status_label')
        self.data_remaining_label = builder.get_object('data_remaining_label')
        self.tokens_available_label = builder.get_object('tokens_available_label')  # noqa: E501
        self.anytime_remaining_label = builder.get_object('anytime_remaining_label')  # noqa: E501
        self.allowance_resets_label = builder.get_object('allowance_resets_label')  # noqa: E501
        self.bonus_progress = builder.get_object('bonus_progress')
        self.anytime_progress = builder.get_object('anytime_progress')
        self.bonus_start_label = builder.get_object('bonus_start_label')
        self.signal_strength_label = builder.get_object('signal_strength_label')  # noqa: E501
        self.auto_refresh_button = builder.get_object('auto_refresh_button')
        self.rx_label = builder.get_object('rx_label')
        self.tx_label = builder.get_object('tx_label')
        self.up_image = builder.get_object('up_image')
        self.up_off_image = builder.get_object('up_off')
        self.up_on_image = builder.get_object('up_on')
        self.down_image = builder.get_object('down_image')
        self.down_off_image = builder.get_object('down_off')
        self.down_on_image = builder.get_object('down_on')
        self.update_time_label = builder.get_object('update_time_label')
        self.estimated_use_label = builder.get_object('estimated_label')
        self.menu = builder.get_object('ind_menu')
        self.update_interval = update_interval
        self.icon = None

        template = ["hnStatus",
                    "Status: {}",
                    "Signal Strength: {}",
                    "Anytime Remaining: {} ({:.02f}%)",
                    "Bonus Remaining: {} ({:.02f}%)",
                    "Estimated: {:.02f}%"]
        self.tooltip_template = '\n'.join(template)
        self.bonus_color = bonus_color
        self.anytime_color = anytime_color
        self.ss_colors = ss_colors
        self.tx_rx_colors = tx_rx_colors
        self.background_color = background_color
        self.highlight_color = Gdk.RGBA()
        self.highlight_color.parse('red')
        self.normal_color = Gdk.RGBA()
        self.normal_color.parse('black')

        # Setup the appindicator
        self.downicon = os.path.join(path,
                                     'resources/icons/hnmodem-down100x100.png')
        self.defaulticon = os.path.join(path,
                                        'resources/icons/hnmodem100x100.png')
        self.statusicon = Gtk.StatusIcon()
        self.statusicon.connect("popup-menu", self.right_click_event)
        self.statusicon.connect("button-press-event", self.button_press_event)
        self.statusicon.set_tooltip_text("hnstatus")
        self.statusicon.set_from_file(self.defaulticon)

        Notify.init('hnstatus-appindicator')

        self.update_interval = update_interval  # Update interval 1s
        self.window1_is_moving = False
        self.window1_disable_move = False
        self.window1_coords = (True, window_x, window_y)

    def about(self, widget):
        self.about_window.show_all()

    def about_close_handler(self, widget, status):
        self.about_window.hide()

    def right_click_event(self, icon, button, time):
        self.menu.show_all()

        def pos(menu, x, y, icon):
            return (Gtk.StatusIcon.position_menu(menu, x, y, icon))

        self.menu.popup(None, None, pos, self.statusicon, button, time)

    def window_state_event(self, w, s):
        if 'iconified' in s.new_window_state.value_nicks:
            w.set_visible(False)

    def button_press_event(self, icon, button):
        b = button.get_button()[1]
        if b == 1:
            if self.window1.is_visible():
                self.hide(icon)
            else:
                self.show(icon)

    def quit(self, widget):
        """ Exit the program """

        # pylint: disable=no-self-use, unused-argument
        self.window_disable_move = True
        self.window1_is_moving = True
        if self.config_file:
            import yaml
            with open(self.config_file) as f:
                config = yaml.load(f)
            pos = self.window1.get_position()
            if config['program']['y_pos'] - pos.root_y:
                config['program']['y_pos'] = pos.root_y + 5
            config['program']['x_pos'] = pos.root_x
            with open(self.config_file, "w") as f:
                yaml.dump(config, f)

        Notify.uninit()
        self.gtk.main_quit()

    def toggle_refresh(self, widget):
        """ Toggle auto refresh """

        if widget.get_active():
            print('Starting auto-update')
            if self.auto_update_source is None:
                self.populate()  # Force a single update
                self.auto_update_source = GObject.timeout_add(
                    self.update_interval, self.populate)
        else:
            print('Stop auto-update')
            if self.auto_update_source is not None:
                GObject.source_remove(self.auto_update_source)
                self.auto_update_source = None

    def show(self, widget):
        self.window1_disable_move = True
        self.window1_is_moving = False
        self.window1.deiconify()
        self.window1.set_visible(True)
        self.window1.move(self.window1_coords[1], self.window1_coords[2])
        self.window1_is_moving = False
        self.window1_disable_move = False

    def hide(self, widget):
        self.window1_disable_move = True
        self.window1.set_visible(False)
        self.window1_is_moving = False

    def set_icon(self):
        if not self.icon:
            self.icon = Icon(space=0,
                             width=33,
                             arrowheight=15,
                             indicator=self.statusicon,
                             downicon=self.downicon,
                             bonus_color=self.bonus_color,
                             anytime_color=self.anytime_color,
                             ss_colors=self.ss_colors,
                             tx_rx_colors=self.tx_rx_colors,
                             background_color=self.background_color,
                             defaulticon=self.defaulticon)

        self.icon.new(self.hnstat.bonus_percent_remaining,
                      self.hnstat.anytime_percent_remaining,
                      self.hnstat.signal_strength,
                      self.hnstat._last_tx,
                      self.hnstat._last_rx)

    def populate(self, force=False):
        """ Populate the GUI with the current status """

        self.hnstat.fetch_current_stats()

        self.status_label.set_text(self.hnstat.status)
        self.data_remaining_label.set_text(self.hnstat.data_remaining)
        self.tokens_available_label.set_text(self.hnstat.tokens_available)
        self.allowance_resets_label.set_text(self.hnstat.allowance_reset)
        self.anytime_progress.set_fraction(
            self.hnstat.anytime_percent_remaining / 100)

        if self.hnstat.anytime_percent_remaining < self.hnstat.estimated_use:
            color = self.highlight_color
        else:
            color = self.normal_color
        self.anytime_progress.override_color(Gtk.StateType.NORMAL,
                                             color)
        self.anytime_progress.set_text(self.hnstat.anytime_info)
        self.bonus_progress.set_fraction(
            self.hnstat.bonus_percent_remaining / 100)

        if self.hnstat.bonus_percent_remaining < self.hnstat.estimated_use:
            color = self.highlight_color
        else:
            color = self.normal_color
        self.bonus_progress.override_color(Gtk.StateType.NORMAL,
                                           color)

        self.bonus_progress.set_text(self.hnstat.bonus_info)
        self.bonus_start_label.set_text(self.hnstat.bonus_start)
        self.signal_strength_label.set_text(self.hnstat.signal_strength)
        self.rx_label.set_text(self.hnstat.last_rx)
        self.tx_label.set_text(self.hnstat.last_tx)
        self.update_time_label.set_text(self.hnstat.update_time)
        if self.hnstat._last_tx == 0:
            self.up_image.set_from_pixbuf(self.up_off_image.get_pixbuf())
        else:
            self.up_image.set_from_pixbuf(self.up_on_image.get_pixbuf())
        if self.hnstat._last_rx == 0:
            self.down_image.set_from_pixbuf(self.down_off_image.get_pixbuf())
        else:
            self.down_image.set_from_pixbuf(self.down_on_image.get_pixbuf())
        self.estimated_use_label.set_text("{:.02f}%".format(
            self.hnstat.estimated_use))
        self.set_icon()

        self.statusicon.set_tooltip_text(self.tooltip_template.format(
            self.hnstat.status,
            self.hnstat.signal_strength,
            self.hnstat.anytime_remaining,
            self.hnstat.anytime_percent_remaining,
            self.hnstat.bonus_remaining,
            self.hnstat.bonus_percent_remaining,
            self.hnstat.estimated_use))
        # Notify about connection errors.
        if self.hnstat.status_raw != 'OK':
            if self.hnstat.status_raw != self._last_status_warning:
                Notify.Notification.new('hn Modem Status:',
                                        self.hnstat.status, None).show()
                self._last_status_warning = self.hnstat.status_raw
        else:
            self._last_status_warning = None

        return True
