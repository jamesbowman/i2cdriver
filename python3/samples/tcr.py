import sys
import struct
from i2cdriver import I2CDriver

class TCR:
    pass

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])
    i2.setspeed(400)
    i2.scan()
    while 1:
        i2.start(0x0c, 1)
        b = i2.read(256)
        i2.stop()
        (l, ) = struct.unpack("<H", b[0:2])
        s = b[2:2+l]
        if l:
            print(s)
        else:
            print('nothing')
