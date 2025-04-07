"""
Example for Bi-Color (Red/Green) 24-Bar Bargraph, based on HT16K33.
Available from Adafruit.
"""

import sys
import time
import random

from i2cdriver import I2CDriver

from ht16k33 import HT16K33

class bargraph(HT16K33):
    def set(self, pix):
        rr = pix
        def paint(r, i):
            """ Paint pixel i """
            blk = i // 12
            i %= 12
            b = i // 4
            m = 1 << ((i % 4) + 4 * blk)
            r[b] |= m
        red = [0,0,0]
        grn = [0,0,0]
        [paint(red, i) for i in range(24) if (pix[i] & 1)]
        [paint(grn, i) for i in range(24) if (pix[i] & 2)]
        self.load([red[0], grn[0], red[1], grn[1], red[2], grn[2]])

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d0 = bargraph(i2)

    for i in range(60):
        d0.set([random.choice((0,1,2,3)) for i in range(24)])
        time.sleep(.08)
