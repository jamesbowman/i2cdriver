import sys
import time

from i2cdriver import I2CDriver, LM75B

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = LM75B(i2)
    for i in range(100):
        print(d.read())
        time.sleep(.1)
