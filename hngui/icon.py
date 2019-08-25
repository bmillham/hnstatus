import os
import subprocess
import io
import gi

gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf  # noqa: E402
try:
    from PIL import Image, ImageDraw, ImageColor  # noqa: E402
except ModuleNotFoundError:
    print('WARNING: Unable to import PIL.')
    print('WARNING: StatusIcon will not be updated with current status')
    print('WARNING: Please run pip3 install pillow')
    Image = None
except Exception:
    raise


class Icon(object):
    def __init__(self,
                 iheight=100,
                 iwidth=100,
                 space=0,
                 width=33,
                 arrowheight=15,
                 bonus_color=None,
                 anytime_color=None,
                 ss_colors=None,
                 tx_rx_colors=None,
                 background_color=None,
                 indicator=None,
                 downicon=None,
                 defaulticon=None):
        self._width = iwidth
        self._height = iheight
        self.space = space
        self.width = width
        self.arrowheight = arrowheight
        self.icon_name_template = "b_{}_a_{}_s_{}_t_{}_r_{}"
        self.icon_name = None
        self.last_icon = None

        self.bonus_color = self._verify_color([bonus_color], ['blue'])
        self.anytime_color = self._verify_color([anytime_color], ['green'])
        self.ss_colors = self._verify_color(ss_colors.split(','), ['black',
                                                                   'fuchsia',
                                                                   'gray'])
        self.tx_rx_colors = self._verify_color(tx_rx_colors.split(','),
                                               ['red',
                                                'white'])
        self.background_color = self._verify_color([background_color],
                                                   ['white'])

        self.downicon = downicon
        self.defaulticon = defaulticon
        self.indicator = indicator

    def _verify_color(self, color, default):
        """ Verify if the colors in a list are valid HTML colors """
        if not Image:
            return color  # Do nothing if PIL wasn't found
        fixed_color = []
        i = 0
        for c in color:
            c = c.strip()  # Get rid of extra spaces
            try:
                ImageColor.getrgb(c)
            except ValueError:
                print('{} is not a valid color. Defaulting to {}'.format(
                    c,
                    default[i]))
                fixed_color.append(default[i])
            else:
                fixed_color.append(c)
            i += 1

        if len(fixed_color) == 1:
            return fixed_color[0]
        else:
            return fixed_color

    def pixbuf(self):
        """Convert Pillow image to GdkPixbuf"""

        file1 = io.BytesIO()
        ico = self.img.resize((64, 64))
        ico.save(file1, "ppm")
        contents = file1.getvalue()
        file1.close()
        loader = GdkPixbuf.PixbufLoader.new_with_type('pnm')
        loader.write(contents)
        pixbuf = loader.get_pixbuf()
        loader.close()
        return pixbuf

    def new(self,
            bonus,
            anytime,
            ss,
            tx,
            rx,
            status):
        if not self.indicator:  # No nothing if there is no statusicon
            return

        self.bonus = self._sanitize(bonus)
        self.anytime = self._sanitize(anytime)
        self.real_ss = self.ss = self._sanitize(ss)

        # Check for down status
        #if not self.bonus and not self.anytime and not self.ss:
        if status:
            if self.last_icon != self.downicon:
                self.indicator.set_from_pixbuf(self.downicon.get_pixbuf())
                self.last_icon = self.downicon
            return

        # If PIL was not imported, display the stock icon
        if not Image:
            if self.last_icon != self.defaulticon:
                self.indicator.set_from_pixbuf(self.defaulticon.get_pixbuf())
                self.last_icon = self.defaulticon
            return

        if self.ss > 100:  # Cap SS to 100
            self.ss = 100

        tx = self._sanitize(tx)
        rx = self._sanitize(rx)
        self.tx = 1 if int(tx) else 0
        self.rx = 1 if int(rx) else 0

        self.icon_name = self.icon_name_template.format(self.bonus,
                                                        self.anytime,
                                                        self.ss,
                                                        self.tx,
                                                        self.rx
                                                        )

        # Do nothing if trying to use the last used icon

        if self.icon_name == self.last_icon:
            return

        self.last_icon = self.icon_name
        self.create_icon()  # Create the icon in memory
        self.indicator.set_from_pixbuf(self.pixbuf())

    def create_icon(self):
        self.img = Image.new('RGB', (self._width, self._height),
                             self.background_color)
        self.draw = ImageDraw.Draw(self.img)
        self._bonusline()
        self._anytimeline()
        self._ssline()
        self._tx()
        self._rx()

    def _sanitize(self, value):
        try:
            v = int(value)
        except Exception:
            v = 0
        return v

    def _bonusline(self):
        self.draw.rectangle((self.space,
                             100-self.bonus,
                             self.width,
                             100),
                            fill=self.bonus_color)

    def _anytimeline(self):
        offset = self.width + self.space
        self.draw.rectangle((offset,
                             100-self.anytime,
                             self.width + offset - self.space,
                             100),
                            fill=self.anytime_color)

    def _ssline(self):
        if self.ss < (self.arrowheight * 2):
            self.ss = (self.ss * 2) + (self.arrowheight * 2)
        color = self.ss_colors[0].strip()
        if self.real_ss < 50:
            color = self.ss_colors[1].strip()
        if self.real_ss < (self.arrowheight * 2):
            color = self.ss_colors[2].strip()

        offset = (self.width * 2) + self.space
        self.draw.rectangle((offset,
                             (100 - self.ss) + self.arrowheight,
                             self.width + offset - self.space,
                             100 - self.arrowheight),
                            fill=color)

    def _arrow(self, top, bottom, color):
        self.offset = (self.width * 2) + self.space
        end = self.width + self.offset - self.space
        mid = self.offset + (self.width / 2)

        self.draw.polygon([
                           (self.offset, bottom),
                           (mid, top),
                           (end, bottom)
                          ],
                          fill=color,
                          outline='black')

    def _tx(self):
        if self.tx:
            color = self.tx_rx_colors[0]
        else:
            color = self.tx_rx_colors[1]
        top = 1
        bottom = top + self.arrowheight
        self._arrow(top, bottom, color)

    def _rx(self):
        if self.rx:
            color = self.tx_rx_colors[0]
        else:
            color = self.tx_rx_colors[1]
        top = 99
        bottom = top - self.arrowheight
        self._arrow(top, bottom, color)
