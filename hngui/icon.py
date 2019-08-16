import os
import subprocess
import io
import gi

gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf  # noqa: E402
try:
    from PIL import Image, ImageDraw, ImageFont  # noqa: E402
except ModuleNotFoundError:
    print('WARNING: Unable to import PIL.')
    print('WARNING: StatusIcon will not be updated with current status')
    print('WARNING: Please run pip3 install pillow')
    Image = None
    ImageDraw = None
except Exception:
    raise

class Icon(object):
    def __init__(self,
                 iheight=100,
                 iwidth=100,
                 space=0,
                 width=33,
                 arrowheight=15,
                 indicator=None,
                 icon_cache=None,
                 icon_file_template='b_{}_a_{}_s_{}_t_{}_r_{}.png',
                 font_name='Arial',
                 downicon=None,
                 defaulticon=None):
        self._width = iwidth
        self._height = iheight
        self.space = space
        self.width = width
        self.arrowheight = arrowheight
        self.match_list = range(0, 101, 5)  # For finding icons
        self.icon_cache = icon_cache
        self.icon_file_template = icon_file_template
        self.icon_file = None
        self.font_name = font_name
        self.font_file = None
        self.last_icon = None
        self.downicon = downicon
        self.defaulticon = defaulticon
        self.indicator = indicator

    def show(self):
        try:
            self.img.show()
        except Exception:
            print('Unable to show icon, getting presaved')
            self.img = Image.open(self.fname)
            self.img.show()

    def save(self):
        print('Saved:', self.icon_file)
        ico = self.img.resize((32, 32))
        ico.save(self.fname)
        ico.close()
        self.img.close()

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
            pixbuf=False,
            create=True,
            save=True):
        self.bonus = self._sanitize(bonus)
        self.anytime = self._sanitize(anytime)
        self.real_ss = self.ss = self._sanitize(ss)

        # Check for down status
        if not self.bonus and not self.anytime and not self.ss:
            if self.indicator:
                self.indicator.set_from_file(self.downicon)
                return
            
        if self.ss > 100:
            self.ss = 100
        tx = self._sanitize(tx)
        rx = self._sanitize(rx)

        #self.bonus = self._find_closest(bonus, self.match_list)
        #self.anytime = self._find_closest(anytime, self.match_list)
        #self.ss = self._find_closest(ss, self.match_list)
        self.tx = 1 if int(tx) else 0
        self.rx = 1 if int(rx) else 0

        self.icon_file = self.icon_file_template.format(self.bonus,
                                                        self.anytime,
                                                        self.ss,
                                                        self.tx,
                                                        self.rx
                                                        )

        self.fname = os.path.join(self.icon_cache, self.icon_file)

        # Do nothing if trying to use the last used icon

        if self.fname == self.last_icon:
            return
        self.last_icon = self.fname

        # Check if the icon already exists
        if os.path.isfile(self.fname) and not pixbuf:
            if self.indicator:
                self.indicator.set_from_file(self.fname)

            self.img = None
            return  # Do nothing if the icon was already created
        if create or save:  # if save is set, always create the icon
            self.create_icon()
        if save:
            print('save icon')
            self.save()
        if self.indicator:
            if pixbuf:
                self.indicator.set_from_pixbuf(self.pixbuf())
            else:
                self.indicator.set_from_file(self.fname)

    def create_icon(self):
        self.img = Image.new('RGB', (self._width, self._height), 'white')
        self.draw = ImageDraw.Draw(self.img)
        ah = self.arrowheight * 2
        if self.bonus == 0 and self.anytime == 0 and self.real_ss <= ah:
            self._unknown()
        else:
            self._bonusline()
            self._anytimeline()
            self._ssline()
        self._tx()
        self._rx()

    def _unknown(self):
        text = "!?"
        if not self.font_file:
            args = ['fc-match', '-f', '%{file}']
            try:
                self.font_file = subprocess.check_output(
                    args + [self.font_name])
            except Exception:
                # Use system default font
                self.font_file = subprocess.check_output(args + ['default'])
            print("Using font:", self.font_file)

        font = ImageFont.truetype(self.font_file, size=99)
        self.draw.text((10, 0), text, fill='black', font=font)

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
                            fill='blue')

    def _anytimeline(self, color='green'):
        offset = self.width + self.space
        self.draw.rectangle((offset,
                             100-self.anytime,
                             self.width + offset - self.space,
                             100),
                            fill=color)

    def _ssline(self, color='black'):
        if self.ss < (self.arrowheight * 2):
            self.ss = (self.ss * 2) + (self.arrowheight * 2)
        if self.real_ss < 50:
            color = 'fuchsia'
        if self.real_ss < (self.arrowheight * 2):
            color = 'gray'

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
            color = 'red'
        else:
            color = 'white'
        top = 1
        bottom = top + self.arrowheight
        self._arrow(top, bottom, color)

    def _rx(self):
        if self.rx:
            color = 'red'
        else:
            color = 'white'
        top = 99
        bottom = top - self.arrowheight
        self._arrow(top, bottom, color)

    def _find_closest(self, val, m_list):
        return min(m_list, key=lambda x: abs(x-val))
