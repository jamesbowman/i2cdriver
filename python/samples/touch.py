"""
Example for MPR121 Capacitive Touch Sensor.
Available from multiple vendors.
"""

import sys
import serial
import time
import struct
import random

from i2cdriver import I2CDriver

class MPR121:
    def __init__(self, i2, a = 0x5a):
        self.i2 = i2
        self.a = a
        self.i2.regwr(self.a, 0x5e, 0x0c)

    def read(self):
        """ Return 12 touch detection flags """
        (tb,) = struct.unpack("<H", self.i2.regrd(0x5a, 0, 2))
        return [((tb >> i) & 1) for i in range(12)]

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    i2.reset()

    d = MPR121(i2)
    while 1:
        print(d.read())
        time.sleep(.1)
