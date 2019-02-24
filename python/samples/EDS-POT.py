import sys
import struct
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.scan()

    d = EDS.Pot(i2)

    while 1:
        percentage = d.rd(100)
        r = d.raw()

        print("%3d/100   raw=%3d" % (percentage, r))
        time.sleep(.05)
