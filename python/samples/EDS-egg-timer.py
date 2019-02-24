"""
Demo of a simple combination of parts from Electric Dollar Store:

* POT - potentiometer
* DIG2 - 2-digit display
* BEEP - piezo beeper

This demo simulates a kitchen egg-timer.
Twisting the POT sets a countdown time in seconds,
and after it's released the ticker starts counting.
When it reaches "00" it flashes and beeps.

https://electricdollarstore.com

"""
import sys
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
