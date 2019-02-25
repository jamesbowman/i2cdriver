"""
Demo of a simple combination of parts from Electric Dollar Store:

* MAGNET - 3-axis magnetometer
* LED - RGB LED

This demo takes the compass direction, and uses it to set the LED's
color. So as you move the module around, the color changes according to
its direction.  There is a direction that is pure red, another that is
pure green, etc.

https://electricdollarstore.com

"""
import sys

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    magnet = EDS.Magnet(i2)
    led = EDS.LED(i2)

    while True:
        (x, y, z) = magnet.measurement()
        r = max(0, min(255, (x + 4000) // 32))
        g = max(0, min(255, (y + 4000) // 32))
        b = max(0, min(255, (z + 4000) // 32))
        led.rgb(r, g, b)
