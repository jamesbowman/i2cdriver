"""
Example Xtrinsic MAG3110 Three-Axis Digital Magnetometer
Breakout available from Sparkfun.
"""

import sys
import struct
import time

from i2cdriver import I2CDriver, EDS

class MAG3110:
    def __init__(self, i2, a = 0x0e):
        self.i2 = i2
        self.a = a
        self.i2.regwr(self.a, 0x10, 0b00000001) # CTRL_REG1. ACTIVE mode, 80 Hz conversions

    def rd(self):
        """ Read the measurement STATUS_REG and OUT_X,Y,Z """
        return self.i2.regrd(self.a, 0x00, ">B3h")

    def measurement(self):
        """ Wait for a new field reading, return the (x,y,z) """
        while True:
            (status, x, y, z) = self.rd()
            if status & 8:
                return (x, y, z)

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.scan()

    d = MAG3110(i2)
    while 1:
        print(d.measurement())
