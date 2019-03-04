"""
Example for LCD1602, in which a PCF8574 I/O expander drives a HD44780
Available from various vendors.
"""

import sys
import time
import struct

from i2cdriver import I2CDriver

class HD44780:

    def __init__(self, i2, a = 0x27):
        self.i2 = i2
        self.a = a

        # Command (0) / Data (1) (aka RS) (D0)
        # R/W                             (D1)
        # Enable/CLK                      (D2) 
        # Backlight control               (D3)

        self.nybble(3)
        self.nybble(3)
        self.nybble(3)
        self.nybble(2)

        self.cmd(0x28)  # 2 lines, 5x8 dot matrix
        self.cmd(0x0c)  # display on
        self.cmd(0x06)  # inc cursor to right when writing and don't scroll
        self.cmd(0x80)  # set cursor to row 1, column 1

        time.sleep(.2)
        self.data(0x42)

        while 0:
            self.port(0)
            time.sleep(.1)
            self.port(8)
            time.sleep(.1)
        # self.clear()

    def clear(self):
        """ Blank / Reset LCD """
        self.cmd(0x33) # $33 8-bit mode
        self.cmd(0x32) # $32 8-bit mode
        self.cmd(0x28) # $28 8-bit mode
        self.cmd(0x0C | 3) # $0C 8-bit mode
        self.cmd(0x06) # $06 8-bit mode
        self.cmd(0x01) # $01 8-bit mode

    def port(self, *bb):
        # Write byte to port
        if 0:
            self.i2.start(self.a, 0)
            self.i2.write(bb)
            self.i2.stop()
            time.sleep(.000500)
            time.sleep(.050)
        else:
            for b in bb:
                self.i2.start(self.a, 0)
                self.i2.write([b])
                self.i2.stop()
                time.sleep(.005000)

    def nybble(self, n, rs = 0):
        print("   nyb %x" % n)
        bl = 8 | rs
        self.port(
            bl | (n << 4),
            bl | (n << 4) | 4,
            bl | (n << 4)
        )

    def cmd(self, b):
        print("cmd %02x" % b)
        self.nybble(b >> 4)
        self.nybble(b & 0xf)
        time.sleep(.004100)

    def data(self, b):
        print("DAT %02x" % b)
        self.nybble(b >> 4, 1)
        self.nybble(b & 0xf, 1)
        time.sleep(.004100)

    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""

        for char in text:
            if char == '\n':
                self.cmd(0xC0) # next line
            else:
                self.data(ord(char))

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.scan()
    d = HD44780(i2)
    d.message("HELLO WORLD")
