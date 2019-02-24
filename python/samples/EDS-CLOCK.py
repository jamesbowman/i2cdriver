import sys
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = EDS.Clock(i2)
    d.set()
    while 1:
        print(d.read())
        time.sleep(1)
