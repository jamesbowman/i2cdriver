import sys
import struct
import time

from i2cdriver import I2CDriver, EDS

def millis():
    return int(time.time() * 1000)

def eggtimer(i2c):
    pot = EDS.Pot(i2c)
    beep = EDS.Beep(i2c)
    digits = EDS.Dig2(i2c)

    ticking = False
    v0 = pot.rd(99)
    next = millis() + 4000
    digits.brightness(50)
    t = 0

    while True:
        v = pot.rd(99)
        if v0 != v:
            if v0 < v:
                beep.beep(2, 80)
            else:
                beep.beep(1, 117)
            ticking = False
            next = millis() + 1000
            v0 = v
            digits.brightness(255)
            t = v
        digits.dec(t)
        digits.dp(0, ticking)
        if millis() > next and (t != 0):
            ticking = True
        if ticking and millis() > next:
            next = millis() + 1000
            beep.beep(1, 120)
            if t:
                t -= 1
            else:
                for i in range(21):
                    digits.brightness(255)
                    beep.beep(75, 107)
                    time.sleep(.1)
                    digits.brightness(0)
                    time.sleep(.05)
                digits.brightness(50)
                ticking = False

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1], True)
    eggtimer(i2)
