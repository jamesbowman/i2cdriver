"""
Example for Qwiic Joystick
Available from Sparkfun.
"""

import sys
import time
import struct

from i2cdriver import I2CDriver

class Joystick:
    def __init__(self, i2, a = 0x20):
        self.i2 = i2
        self.a = a

    def axis(self, i):
        self.i2.start(self.a, 0)
        self.i2.write([i])
        self.i2.stop()              # Note: their firmware cannot handle an I2C restart
        self.i2.start(self.a, 1)
        (r,) = struct.unpack(">H", self.i2.read(2))
        self.i2.stop()
        return r

    def read(self):
        """
        return the joystick (x,y) position. The range is 0-1023.
        The center position of the joystick is approximately 512.
        """

        # Note: their firmware requires two separate reads

        return (self.axis(0), self.axis(2))

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = Joystick(i2)

    while 1:
        print(d.read())
        time.sleep(.1)
