"""
Example for Qwiic Keypad
Available from Sparkfun.
"""

import sys
import time
import struct

from i2cdriver import I2CDriver

class Keypad:
    def __init__(self, i2, a = 0x4b):
        self.i2 = i2
        self.a = a

    def read_ts(self):
        """
        Return (key, timestamp) if pressed, or None.
        """

        self.i2.start(self.a, 1)
        (k, age_in_ms) = struct.unpack(">BH", self.i2.read(3))
        self.i2.stop()
        if k != 0:
            return (chr(k), time.time() - age_in_ms * .001)
        else:
            return None

    def read(self):
        r = self.read_ts()
        if r:
            return r[0]
        else:
            return None

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = Keypad(i2)

    while 1:
        print(d.read())
        time.sleep(.1)
