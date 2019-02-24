import sys
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1], True)

    d = EDS.Remote(i2)

    print("Press a remote button")
    while 1:
        k = d.key()
        if k is not None:
            print("Key     : %r" % k)
        r = d.raw()
        if r is not None:
            (code, timestamp) = r
            print("Raw code: %02x %02x %02x %02x (time %.2f)" % (code[0], code[1], code[2], code[3], timestamp))
