"""
Example for 128X64OLED Module 
Available from multiple vendors, e.g. DIYMall

This example loads the I2CDriver logo onto the display,
and flashes it four times.

"""

import sys
import time

from PIL import Image, ImageChops

from i2cdriver import I2CDriver

SETCONTRAST         = 0x81
DISPLAYALLON_RESUME = 0xA4
DISPLAYALLON        = 0xA5
NORMALDISPLAY       = 0xA6
INVERTDISPLAY       = 0xA7
DISPLAYOFF          = 0xAE
DISPLAYON           = 0xAF
SETDISPLAYOFFSET    = 0xD3
SETCOMPINS          = 0xDA
SETVCOMDETECT       = 0xDB
SETDISPLAYCLOCKDIV  = 0xD5
SETPRECHARGE        = 0xD9
SETMULTIPLEX        = 0xA8
SETLOWCOLUMN        = 0x00
SETHIGHCOLUMN       = 0x10
SETSTARTLINE        = 0x40
MEMORYMODE          = 0x20
COLUMNADDR          = 0x21
PAGEADDR            = 0x22
COMSCANINC          = 0xC0
COMSCANDEC          = 0xC8
SEGREMAP            = 0xA0
CHARGEPUMP          = 0x8D

class OLED:
    def __init__(self, i2, a = 0x3c):
        self.i2 = i2
        self.a = a

        self.command(DISPLAYOFF)
        self.command(SETDISPLAYCLOCKDIV, 0x80)       # the suggested ratio 0x80

        self.command(SETMULTIPLEX, 0x3f)

        self.command(SETDISPLAYOFFSET, 0)
        self.command(SETSTARTLINE | 0x0)
        self.command(CHARGEPUMP, 0x14)
        self.command(MEMORYMODE, 0)
        self.command(SEGREMAP | 0x1)
        self.command(COMSCANDEC)

        self.command(SETCOMPINS, 0x12)
        self.command(SETCONTRAST, 0xcf)

        self.command(SETVCOMDETECT, 0x40)
        self.command(DISPLAYALLON_RESUME)
        self.command(NORMALDISPLAY)

        self.im = Image.new("1", (128,64), 1)
        self.cls()

    def command(self, *c):
        assert(self.i2.start(self.a, 0))
        assert(self.i2.write((0,) + c))
        self.i2.stop()

    def image(self, im):
        for p in range(8):
            pr = self.im.crop((0,8*p,128,8*p+8)).transpose(Image.ROTATE_270)
            bb = im.crop((0,8*p,128,8*p+8)).transpose(Image.ROTATE_270)
            diff = ImageChops.difference(pr, bb)
            di = diff.getbbox()
            if di is not None:
                (x0, y0, x1, y1) = di
                self.command(COLUMNADDR)
                self.command(y0)
                self.command(y1 - 1)
                self.command(PAGEADDR)
                self.command(p)
                self.command(p + 1)
                self.i2.start(self.a, 0)
                self.i2.write([0x40])
                self.i2.write(bb.tobytes()[y0:y1])
                self.i2.stop()
        self.im = im
        self.command(DISPLAYON)

    def cls(self):
        self.image(Image.new("1", (128,64), 0))

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    d = OLED(i2)

    d.image(Image.open("logo.png").convert("1"))

    for i in range(4):
        d.command(INVERTDISPLAY)
        time.sleep(.5)
        d.command(NORMALDISPLAY)
        time.sleep(.5)
