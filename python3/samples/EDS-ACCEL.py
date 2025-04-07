import sys
import struct
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.scan()

    d = EDS.Accel(i2)
    while True:
        print("x=%+.3f  y=%+.3f  z=%+.3f" % d.measurement())
