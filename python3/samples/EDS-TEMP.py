import sys
import time

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = EDS.Temp(i2)
    for i in range(20):
        celsius = d.read()
        fahrenheit = celsius * 9/5 + 32
        sys.stdout.write("%.1f C  %.1f F\n" % (celsius, fahrenheit))
        time.sleep(.1)
