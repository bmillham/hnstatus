""" Handle options for hnstatus """
try:
    import yaml
except Exception:
    print('Unable to import yaml to read configuration files.')
    print('Using hard coded defaults.')
    yaml = None
else:
    try:
        loader = yaml.FullLoader
    except AttributeError:
        print('This version of Yaml does not support FullLoader.')
        loader = None

class HnOptions(object):
    
    def __init__(self,
                 config_file=None,
                 statecode_file=None,
                 position_file=None):

        self.config_file = config_file
        self.statecode_file = statecode_file
        self.position_file = position_file

        # The default colors
        self.default_colors = {
            'bonus_color': 'blue',
            'anytime_color': 'green',
            'ss_colors': ['black', 'fuchsia', 'gray'],
            'tx_rx_colors': ['red', 'white'],
            'background_color': 'white',
        }
        # Default program options
        self.default_program = {
            'update_interval': 1000,
            'IP': '192.168.0.1',
            'auto_update': True,
            'start_minimized': False,
        }

        self._config = {}
        self._statecodes = {}
        self._position = {}

    def _load_yaml(self, file):
        if not file or not yaml:
            return {}

        content = {}

        try:
            with open(file) as f:
                if loader:
                    content = yaml.load(f, Loader=loader)
                else:
                    content = yaml.load(f)
        except FileNotFoundError:
            print('Unable to open configuration file:', file)
            self.config_file = None
        except AttributeError:
            print('Error in file:', file)
            self.config_file = None

        return content

    @property
    def colors(self):
        if not self._config:
            self._config = self._load_yaml(self.config_file)

        # Merge the colors from the yaml with the defaults
        # yaml colors override the defaults.
        try:
            colors = {**self.default_colors, **self._config['colors']}
        except KeyError:
            print('No color information in config file')
            colors = self.default_colors
        return colors

    @property
    def program_options(self):
        if not self._config:
            self._config = self._load_yaml(self.config_file)

        try:
            program = {**self.default_program, **self._config['program']}
        except KeyError:
            print('No program options in config file')
            program = self.default_program
        return program

    @property
    def statecodes(self):
        if not self._statecodes:
            self._statecodes = self._load_yaml(self.statecode_file)
        return self._statecodes

    @property
    def position(self):
        if not self._position:
            self._position = self._load_yaml(self.position_file)
        return self._position

    @position.setter
    def position(self, x):
        if not yaml:
            print('Unable to save window position')
            return
        with open(self.position_file, "w") as f:
            yaml.dump(x, f)
