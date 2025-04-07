import sys
import time
import random
import struct

from i2cdriver import I2CDriver

class PCA9685:
    def __init__(self, i2, a = 0x40):
        self.i2 = i2
        self.a = a
        self.i2.regwr(self.a, 0x00, 0x20)  # auto-increment mode

    def set(self, channel, t_on, t_off):
        assert 0 <= channel < 16
        assert 0 <= t_on <= 0x1000
        assert 0 <= t_off <= 0x1000
        self.i2.regwr(self.a,
                       0x06 + 4 * channel,
                       struct.pack("<HH", t_on, t_off))

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    print(i2.scan())
    d = PCA9685(i2)

    for channel in range(16):
        d.set(channel, 4096, 0)

    while True:
        for channel in range(16):
            d.set(channel, random.randrange(4096), random.randrange(4096))
            time.sleep(.3)
