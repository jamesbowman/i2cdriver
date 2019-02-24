import sys
import struct
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = EDS.Magnet(i2)
    while 1:
        print(d.measurement())
