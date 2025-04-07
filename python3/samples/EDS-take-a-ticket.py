"""
Demo of a simple combination of parts from Electric Dollar Store:

* REMOTE - remote control receiver
* DIG2 - 2-digit display
* BEEP - piezo beeper

This demo runs a take-a-ticket display for a store or deli counter.

It shows 2-digit "now serving" number, and each time '+' is
pressed on the remote it increments the counter and
makes a beep, so the next customer can be served.
Pressing '-' turns the number back one.

https://electricdollarstore.com

"""
import sys

from i2cdriver import I2CDriver, EDS

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    remote = EDS.Remote(i2)
    beep   = EDS.Beep(i2)
    dig2   = EDS.Dig2(i2)

    counter = 0
    while True:
        k = remote.key()
        if k == '+':
            beep.beep(255, 90)
            counter = (counter + 1) % 100
        if k == '-':
            beep.beep(100, 80)
            counter = (counter - 1) % 100
        dig2.dec(counter)
