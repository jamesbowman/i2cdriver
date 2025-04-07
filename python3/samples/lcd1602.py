"""
Example for LCD1602, in which a PCF8574 I/O expander drives a HD44780.
Available from various vendors.

Note that the modules require a 5V VCC; they don't function using the
3.3V VCC of I2CDriver.

"""

import sys
import time
import struct

from i2cdriver import I2CDriver

class HD44780:

    def __init__(self, i2, a = 0x27):
        self.i2 = i2
        self.a = a

        self.nybble(3)  # Enter 4-bit mode
        self.nybble(3)
        self.nybble(3)
        self.nybble(2)

        self.cmd(0x28)  # 2 lines, 5x8 dot matrix
        self.cmd(0x0c)  # display on
        self.cmd(0x06)  # inc cursor to right when writing and don't scroll
        self.cmd(0x80)  # set cursor to row 1, column 1

        self.clear()

    def clear(self):
        """ Clear the screen """
        self.cmd(0x01)
        time.sleep(.003)

    def show(self, line, text):
        """ Send string to LCD. Newline wraps to second line"""
        self.cmd({0:0x80, 1:0xc0}[line])
        for c in text:
            self.data(ord(c))

    def cmd(self, b):
        self.nybble(b >> 4)
        self.nybble(b & 0xf)
        time.sleep(.000053)

    def data(self, b):
        self.nybble(b >> 4, 1)
        self.nybble(b & 0xf, 1)

    # The PCF8574 outputs are connected to the HD44780
    # pins as follows:

    # P0    RS (0: command, 1: data)
    # P1    R/W (0: write, 1: read)
    # P2    Enable/CLK
    # P3    Backlight control
    # P4-7  D4-D7

    def nybble(self, n, rs = 0):
        bl = 8 | rs
        self.port(
            bl | (n << 4),
            bl | (n << 4) | 4,
            bl | (n << 4)
        )

    def port(self, *bb):
        # Write bytes to port, setting the PCF8574 outputs
        self.i2.start(self.a, 0)
        self.i2.write(bb)
        self.i2.stop()

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    d = HD44780(i2)
    d.show(0, "HELLO WORLD")
    time.sleep(.5)
    d.show(1, "0123456789012345")
