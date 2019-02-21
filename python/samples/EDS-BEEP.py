import sys
import serial
import time
import struct
import random

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1], True)

    d = EDS.Beep(i2)

    for note in range(55, 127):
        d.beep(100, note)
        time.sleep(.100)
