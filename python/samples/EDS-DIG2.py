import sys
import serial
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = EDS.Dig2(i2)
    for i in range(100):
        d.dec(i)
        time.sleep(.05)
