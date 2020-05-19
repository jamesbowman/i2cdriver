import sys
import struct
from i2cdriver import I2CDriver

#
# For details see
# https://wiibrew.org/wiki/Wiimote/Extension_Controllers
#

class Wii:
    def __init__(self, i2, a = 0x52):
        self.i2 = i2
        self.a = a

        self.i2.regwr(self.a, 0xf0, 0x55)
        self.i2.regwr(self.a, 0xfb, 0x00)
        idcode = (self.rdreg(0xfa, 6))
        
        devices = {
            bytes([0x01, 0x00, 0xa4, 0x20, 0x01, 0x01]): self.wii_classic_pro,
        }
        if idcode in devices:
            self.rd = devices[idcode]
        else:
            raise IOError("Unrecognised device %r" % idcode)

    def rdreg(self, addr, n):
        self.i2.start(self.a, 0)
        self.i2.write([addr])
        self.i2.stop()

        self.i2.start(self.a, 1)
        r = self.i2.read(n)
        self.i2.stop()
        return r

    def wii_classic_pro(self):
        b = self.rdreg(0x00, 6)
        r4 = '. brt b+ bh b- blt bdd bdr'.split()
        r = {id: 1 & (~b[4] >> i) for i,id in enumerate(r4)}
        r5 = 'bdu bdl bzr bx ba by bb bzl'.split()
        r.update({id: 1 & (~b[5] >> i) for i,id in enumerate(r5)})
        r.update({
            'lx' : b[0] & 63,
            'ly' : b[1] & 63,
            'rx' : (((b[0] >> 6) & 3) << 3) |
                   (((b[1] >> 6) & 3) << 1) |
                   (((b[2] >> 7) & 1)),
            'ry' : b[2] & 31,
            'lt' : (((b[2] >> 5) & 3) << 3) |
                   (((b[3] >> 5) & 7)),
            'rt' : b[3] & 31,
        })
        return r

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.scan()

    d = Wii(i2)
    while True:
        print(d.rd())
