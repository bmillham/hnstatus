""" Build the GUI and handle the signals """

import gi

gi.require_version('Gtk', '3.0')

from .icon import Icon  # noqa: E402
from hnlog.logging import Log  # noqa: E402
from gi.repository import Gtk, GObject, Gdk  # noqa: E402

try:
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify  # noqa: E402
except (ImportError, ValueError):
    print('WARNING: gi.repository.Notify not available.')
    print('Notifications will not be displayed.')
    Notify = None


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


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
                 config_file=None,
                 start_position=None,
                 update_interval=1000):
        """ Create the GUI, but do not display it """

        signals = {
            'on_window1_destroy': self.quit,
            'on_auto_refresh_button_toggled': self.toggle_refresh,
            'populate': self.populate,
            'window_state_event': self.window_state_event,
            'on_check_resize_event': self.resize_event,
            'about_item': self.about,
            'about-close-handler': self.about_close_handler,
            'set-tooltip': self._set_tooltip,
            'popup-menu': self.right_click_event,
            'button-press-event': self.button_press_event
        }

        self._last_status_warning = None
        self.hnstat = hnstat
        self.auto_update_source = None
        self.config_file = config_file
        self.first_resize = True

        self.gtk = Gtk
        self.__o = AttrDict()

        builder = self.gtk.Builder()
        builder.add_from_file(file)
        builder.connect_signals(signals)

        # Get all named objects
        for obj in builder.get_objects():
            self.o = obj

        self.update_interval = update_interval
        self.icon = None

        template = ["hnStatus",
                    "Association Status: {}",
                    "FAP Status {}",
                    "Signal Strength: {}",
                    "Anytime Remaining: {} ({:.02f}%)",
                    "Bonus Remaining: {} ({:.02f}%)",
                    "Estimated: {:.04f}%"]
        self.tooltip_template = '\n'.join(template)
        self.bonus_color = bonus_color
        self.anytime_color = anytime_color
        self.ss_colors = ss_colors
        self.tx_rx_colors = tx_rx_colors
        self.background_color = background_color
        self.highlight_color = Gdk.RGBA()
        self.highlight_color.parse('red')
        self.normal_color = None
        self.saved_window_position = start_position

        # Setup the StatusIcon

        # Have to create a new instance to prevent a Gdk errorn
        self.statusicon = self.o.StatusIcon.new()
        self.statusicon.set_visible(True)
        # Manually connect the signals
        self.statusicon.connect("popup-menu", self.right_click_event)
        self.statusicon.connect("button-press-event", self.button_press_event)

        if Notify:
            Notify.init('hnstatus-appindicator')

        self.log = Log('db.db', commit_after=60)
        self.log.open()
        self.update_interval = update_interval  # Update interval 1s

    @property
    def o(self):
        return self.__o

    @o.setter
    def o(self, object):
        try:
            name = object.get_name()
        except AttributeError:
            name = type(object).__name__
        self.__o[name] = object

    def about(self, widget):
        widget.show()

    def about_close_handler(self, widget, status):
        widget.hide()

    def right_click_event(self, icon, button, time):
        self.o.ind_menu.show_all()

        def pos(menu, x, y, icon):
            p = Gtk.StatusIcon.position_menu(menu, x, y, icon)
            return p

        self.o.ind_menu.popup(None,
                              None,
                              pos,
                              self.statusicon,
                              button,
                              time)

    def resize_event(self, w):
        if self.first_resize:
            self.o.window1.move(self.saved_window_position.root_x,
                                self.saved_window_position.root_y)
            self.first_resize = False
            return

        p = self.o.window1.get_position()
        if p != self.saved_window_position:
            self.saved_window_position = p

    def window_state_event(self, w, s):
        if 'iconified' in s.new_window_state.value_nicks:
            p = w.get_position()
            w.set_visible(False)
            w.move(p.root_x, p.root_y)
            self.saved_window_position = p

    def button_press_event(self, icon, button):
        b = button.get_button()[1]
        if b == 1:
            if self.o.window1.is_visible():
                self.hide(icon)
            else:
                self.show(icon)

    def quit(self, widget):
        """ Exit the program """

        # pylint: disable=no-self-use, unused-argument
        if Notify:
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
        self.o.window1.deiconify()
        self.o.window1.set_visible(True)

        self.o.window1.move(self.saved_window_position.root_x,
                            self.saved_window_position.root_y)

    def hide(self, widget):
        p = self.o.window1.get_position()
        self.o.window1.set_visible(False)
        self.o.window1.move(p.root_x, p.root_y)
        self.saved_window_position = p

    def set_icon(self):
        if not self.icon:
            self.icon = Icon(space=0,
                             width=33,
                             arrowheight=15,
                             indicator=self.statusicon,
                             downicon=self.o['network_down_image'],
                             bonus_color=self.bonus_color,
                             anytime_color=self.anytime_color,
                             ss_colors=self.ss_colors,
                             tx_rx_colors=self.tx_rx_colors,
                             background_color=self.background_color,
                             defaulticon=self.o['modem_image'])

        self.icon.new(self.hnstat.bonus_percent_remaining,
                      self.hnstat.anytime_percent_remaining,
                      self.hnstat.signal_strength,
                      self.hnstat._last_tx,
                      self.hnstat._last_rx,
                      self.hnstat.status_raw)

    def _set_tooltip(self, widget, x, y, keyboard, tooltip):
        txt = widget.get_text()
        if txt == 'OK':
            txt = None
        widget.set_tooltip_text(txt)

    def populate(self, force=False):
        """ Populate the GUI with the current status """

        h = self.hnstat
        h.fetch_current_stats()

        self.o.association_status_label.set_text(h.association_status)
        self.o.fap_status_label.set_text(h.fap_status)
        self.o.data_remaining_label.set_text(h.data_remaining)
        self.o.tokens_available_label.set_text(h.tokens_available)
        self.o.allowance_resets_label.set_text(h.allowance_reset)
        self.o.anytime_progress.set_fraction(
            h.anytime_percent_remaining / 100)

        if h.anytime_percent_remaining < h.estimated_use:
            color = self.highlight_color
        else:
            color = self.normal_color
        self.o.anytime_progress.override_color(Gtk.StateType.NORMAL, color)
        self.o.anytime_progress.set_text(h.anytime_info)
        self.o.bonus_progress.set_fraction(h.bonus_percent_remaining / 100)

        if h.bonus_percent_remaining < h.estimated_use:
            color = self.highlight_color
        else:
            color = self.normal_color
        self.o.bonus_progress.override_color(Gtk.StateType.NORMAL, color)

        self.o.bonus_progress.set_text(h.bonus_info)
        self.o.bonus_start_label.set_text(h.bonus_start)
        self.o.signal_strength_label.set_text(h.signal_strength)
        self.o.rx_label.set_text(self.hnstat.last_rx)
        self.o.tx_label.set_text(self.hnstat.last_tx)
        self.o.update_time_label.set_text(h.update_time)
        if self.hnstat._last_tx == 0:
            self.o.up_image.set_from_pixbuf(
                self.o.up_off_image.get_pixbuf())
        else:
            self.o.up_image.set_from_pixbuf(
                self.o.up_on_image.get_pixbuf())
        if self.hnstat._last_rx == 0:
            self.o.down_image.set_from_pixbuf(
                self.o.down_off_image.get_pixbuf())
        else:
            self.o.down_image.set_from_pixbuf(
                self.o.down_on_image.get_pixbuf())
        self.o.estimated_label.set_text("{:.04f}%".format(
            self.hnstat.estimated_use))
        self.set_icon()

        self.statusicon.set_tooltip_text(self.tooltip_template.format(
            self.hnstat.association_status,
            self.hnstat.fap_status,
            self.hnstat.signal_strength,
            self.hnstat.anytime_remaining,
            self.hnstat.anytime_percent_remaining,
            self.hnstat.bonus_remaining,
            self.hnstat.bonus_percent_remaining,
            self.hnstat.estimated_use))

        self.log.adddata(h)

        # Notify about connection errors.
        if self.hnstat.status_raw and Notify:
            if self.hnstat.status_raw != self._last_status_warning:
                status = "Association: {}, FAP: {}".format(
                    self.hnstat.association_status,
                    self.hnstat.fap_status)
                n = Notify.Notification.new('hn Modem Status:', status)
                n.set_image_from_pixbuf(self.o.network_down_image.get_pixbuf())
                n.set_timeout(10000)
                n.show()
                self._last_status_warning = self.hnstat.status_raw
        elif Notify:
            if self._last_status_warning:
                status = "Association: {}, FAP: {}".format(
                    self.hnstat.association_status,
                    self.hnstat.fap_status)
                n = Notify.Notification.new('hn Modem Status:', status)
                n.set_image_from_pixbuf(self.o.modem_image.get_pixbuf())
                n.set_timeout(10000)
                n.show()
            self._last_status_warning = None

        return True
