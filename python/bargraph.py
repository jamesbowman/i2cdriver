import sys
import serial
import time
import struct
import random

from ht16k33 import HT16K33

class bargraph(HT16K33):
    def image(self, bb):
        def swiz(b):
            bs = [str((b >> n) & 1) for n in range(8)]
            return int(bs[7] + bs[0] + bs[1] + bs[2] + bs[3] + bs[4] + bs[5] + bs[6], 2)
        bb = [swiz(b) for b in bb]
        self.load([b for s in zip(bb,bb) for b in s])

    def char(self, c):
        n = ord(c)
        ch = font[n * 8:n * 8 + 8]
        self.image(ch)

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
