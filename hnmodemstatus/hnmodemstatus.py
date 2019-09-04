""" hnmodemstatus-

    Read current usage status from a Hughsnet Modem """

# pylint: disable=wrong-import-order, bare-except

from humanfriendly import format_size
import requests
from datetime import datetime
from calendar import monthrange


class HnModemStatus:

    """ Gather usage statistics from a HughesNet Modem """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, ip='192.168.0.1', state_codes=None):
        self.wan = "http://{}/api/home/status/wan".format(ip)
        self.satellite = "http://{}/api/home/status/satellite".format(ip)
        self.usage = "http://{}/api/home/usage".format(ip)
        self.association = "http://{}/api/home/status/association".format(ip)

        self._status = None
        self._data_remaining = None
        self._anytime_allowance = None
        self._anytime_remaining = None
        self._bonus_allowance = None
        self._bonus_remaining = None
        self._tokens_available = None
        self._allowance_reset = None
        self._bonus_start = None
        self._page = None
        self._ss_page = None
        self._wan = None
        self._satellite = None
        self._usage = None
        self._last_error = None
        self._signal_strength = None
        self._association = {}
        self.last_rx = 0
        self.last_tx = 0
        self._last_rx_period = 0
        self._last_tx_period = 0
        self._fap_status = -1
        self.estimated_use = 0
        self.state_codes = state_codes
        self.fap_codes = {0: 'OK',
                          1: 'Bonus',
                          2: 'Unknown',
                          3: 'Throttled',
                          4: 'Not Associated'}

        if not self.state_codes:
            self.state_codes = {
                '0.0.0': 'Fully operational',
                '24.1.1': 'Download throttled',
                'unknown': ''}

    def get_json(self, json_page=None):
        """ Read a json page and handle errors """
        json = None
        error = None

        try:
            json = requests.get(json_page, timeout=(0.45, .45)).json()
        except ConnectionError:
            error = 'Connection Error'
        except OSError:
            error = 'OS Error'
        except Exception:
            error = 'Other Error'

        return json, error

    def _get_estimated_use(self):
        now = datetime.now()
        days_in_month = monthrange(now.year, now.month)[1]
        mins_in_month = days_in_month * 24 * 60
        current_min = ((now.day - 1) * 24 * 60) + (now.hour * 60) + now.minute
        self.estimated_use = 100 - ((current_min / mins_in_month) * 100)

    def fetch_current_stats(self):
        """ Get the current stats from the modem, no parsing of the stats """

        wan = self.get_json(self.wan)
        satellite = self.get_json(self.satellite)
        usage = self.get_json(self.usage)
        association = self.get_json(self.association)
        self._get_estimated_use()

        for r in (wan[1], satellite[1], usage[1], association[1]):
            if r:
                if r != self._last_error:
                    self._clear_stats(reason=r)
                self._last_error = r
                return

        self._last_error = None
        self._wan = wan[0]
        self._satellite = satellite[0]
        self._usage = usage[0]
        self._association = association[0]
        self._status = None

        # Uncomment these lines to see the amount to data read from the modem
        # bytes_returned = len(str(wan[0])) + \
        #    len(str(satellite[0])) + \
        #    len(str(usage[0])) + \
        #    len(str(association[0]))
        # print('Total bytes from last read:', bytes_returned)

        MB = 1000 * 1000
        usage = self._usage
        self._tokens_available_bytes = usage['tokens']['remaining_mb'] * MB
        self._anytime_allowance_bytes = usage['anytime']['total_mb'] * MB
        self._anytime_remaining_bytes = usage['anytime']['remaining_mb'] * MB
        self._bonus_remaining_bytes = usage['bonus']['remaining_mb'] * MB
        self._bonus_allowance_bytes = usage['bonus']['total_mb'] * MB
        try:
            self._bonus_start = usage['bonus_reset']
        except Exception:
            self._bonus_start = None
        self._fap_status = usage['FAP_Status']
        self._last_rx = self._satellite['bytes_rx'] - self._last_rx_period
        self.last_rx = "{}/sec".format(format_size(self._last_rx))
        self._last_rx_period = self._satellite['bytes_rx']
        self._last_tx = self._satellite['bytes_tx'] - self._last_tx_period
        self.last_tx = "{}/sec".format(format_size(self._last_tx))
        self._last_tx_period = self._satellite['bytes_tx']

    def _clear_stats(self, reason=None):
        """ Clear the current statistics """

        print('Clearing stats', reason)

        if not reason:
            self._status = '<Unknown>'
        else:
            self._status = reason

        self._data_remaining = 0
        self._anytime_allowance = 0
        self._anytime_remaining = 0
        self._bonus_allowance = 0
        self._bonus_remaining = 0
        self._tokens_available = 0
        self._allowance_reset = None
        self._bonus_start = None
        self._signal_strength = 0
        self._fap_status = -1
        self._last_rx = self.last_rx = ''
        self._last_tx = self.last_tx = ''
        self._association['association_state_code'] = 'unknown'

    def _format_time(self, time):
        """ Format user friendly time string """

        if 'days' not in time:
            time['days'] = 0

        s = ""
        if time['days'] > 0:
            s += "{days} days".format(**time)
        if time['hrs'] > 0:
            if time['days'] > 0:
                s += ', '
            s += "{hrs} hours ".format(**time)
        if time['mins'] > 0:
            if time['hrs'] > 0:
                s += " and "
            else:
                s += " "
            s += "{mins} minutes".format(**time)
        return s

    @property
    def association_status(self):
        """ Association status"""

        if self._last_error:
            return self._last_error

        ac = self._association['association_state_code']
        if ac in self.state_codes:
            sc = self.state_codes[ac]
        else:
            sc = "Unknown: {}".format(ac)
        return sc

    @property
    def fap_status(self):
        """ FAP status"""

        if self._last_error:
            return self._last_error

        fc = self._association['fap_state_code']
        fs = self._fap_status

        if fc == '0.0.0' and fs == 0:  # Normal FAP Status
            return 'OK'

        if fc in self.state_codes:
            sc = self.state_codes[fc]
        else:
            sc = fc
        if fs in self.fap_codes:
            sc += " - " + self.fap_codes[fs]
        else:
            sc += " - " + str(fs)
        return sc

    @property
    def update_time(self):
        """ Time of last update """
        return datetime.now().strftime("%I:%M:%S %p")

    @property
    def status_raw(self):
        """ Current modem status """
        return self._status

    @property
    def tokens_available(self):
        """ The human formatted value """
        if self._last_error:
            return 'Unknown'
        return format_size(self._tokens_available_bytes)

    @property
    def data_remaining(self):
        """ The human formatted value """
        if self._last_error:
            return 'Unknown'
        return format_size(self.data_remaining_bytes)

    @property
    def data_remaining_bytes(self):
        """ In bytes """
        if self._last_error:
            return 0
        DRB = self._tokens_available_bytes
        DRB += self._anytime_remaining_bytes
        DRB += self._bonus_remaining_bytes
        return DRB

    @property
    def anytime_allowance(self):
        """ The human formatted value """
        if self._last_error:
            return 'Unknown'
        return format_size(self._anytime_allowance_bytes)

    @property
    def anytime_remaining(self):
        """ The human formatted value """
        if self._last_error:
            return 'Unknown'
        return format_size(self._anytime_remaining_bytes)

    @property
    def anytime_info(self):
        """ A nice representation of anytime information """
        if self._last_error:
            return 'Anytime Data: Unknown'
        return 'Anytime Data: {} of {} ({:0.2f}%) Remaining'.format(
            self.anytime_remaining,
            self.anytime_allowance,
            self.anytime_percent_remaining)

    @property
    def anytime_percent_remaining(self):
        """ Percent of anytime """
        try:
            return (self._anytime_remaining_bytes /
                    self._anytime_allowance_bytes) * 100
        except ZeroDivisionError:
            return 0
        except AttributeError:
            return 0

    @property
    def bonus_allowance(self):
        """ The human formatted value """
        return format_size(self._bonus_allowance_bytes)

    @property
    def bonus_remaining(self):
        """ The human formatted value """
        try:
            return format_size(self._bonus_remaining_bytes)
        except Exception:
            return 0

    @property
    def bonus_start(self):
        """ Human format """
        try:
            start = self._bonus_start['reset_string'].split('_')[1].title()
        except Exception:
            return 'Unknown'

        if int(self._bonus_start['hrs']) >= 23 and start == 'Starts':
            self._bonus_start = {'hrs': 6, 'mins': 0}
            start = 'Ends'
        return "{} in {}".format(
            start,
            self._format_time(self._bonus_start)
        )

    @property
    def bonus_percent_remaining(self):
        """ Percentage of bonus """
        try:
            return (self._bonus_remaining_bytes /
                    self._bonus_allowance_bytes) * 100
        except ZeroDivisionError:
            return 0
        except AttributeError:
            return 0

    @property
    def bonus_info(self):
        """ A nice representation of bonus information """
        if self._last_error:
            return 'Bonus Data: Unknown'
        return 'Bonus Data: {} of {} ({:0.2f}%) Remaining'.format(
            self.bonus_remaining,
            self.bonus_allowance,
            self.bonus_percent_remaining,
            )

    @property
    def allowance_reset(self):
        """ Human time """
        if self._last_error:
            return 'Unknown'
        return self._format_time(self._usage['allowance_reset'])

    @property
    def last_error(self):
        """ The last error """
        return self._last_error

    @property
    def signal_strength(self):
        """ Current Signal Strength """
        if self._last_error:
            return 'Unknown'
        return str(self._wan['sat_rx_ss'])

