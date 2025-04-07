"""
Example for 8x8 LED Matrix modules, based on HT16K33.
Available from multiple vendors.
"""

import sys
import time

from i2cdriver import I2CDriver

font = open("cp437-8x8", "rb").read()

from ht16k33 import HT16K33

class led8x8(HT16K33):
    def image(self, bb):
        """ Set the pixels to the bytes bb """
        def swiz(b):
            bs = [str((b >> n) & 1) for n in range(8)]
            return int(bs[7] + bs[0] + bs[1] + bs[2] + bs[3] + bs[4] + bs[5] + bs[6], 2)
        bb = [swiz(b) for b in bb]
        self.load([b for s in zip(bb,bb) for b in s])

    def char(self, c):
        """ Set the pixels to character c """
        n = ord(c)
        ch = font[n * 8:n * 8 + 8]
        self.image(ch)

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = led8x8(i2)

    for c in "I2C":
        d.char(c)
        time.sleep(1)
