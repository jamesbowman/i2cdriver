import struct

class Dig2:
    def __init__(self, i2, a = 0x14):
        self.i2 = i2
        self.a = a

    def raw(self, b0, b1):
        self.i2.regwr(self.a, 0, b0, b1)

    def hex(self, b):
        self.i2.regwr(self.a, 1, b)

    def dec(self, b):
        self.i2.regwr(self.a, 2, b)

    def dp(self, p0, p1):
        self.i2.regwr(self.a, 3, (p1 << 1) | p0)

    def brightness(self, b):
        self.i2.regwr(self.a, 4, b)

class LED:
    def __init__(self, i2, a = 0x08):
        self.i2 = i2
        self.a = a

    def rgb(self, r, g, b, t = 0):
        if t == 0:
            self.i2.start(self.a, 0)
            self.i2.write(bytes((0, r, g, b)))
            self.i2.stop()
        else:
            self.i2.start(self.a, 0)
            self.i2.write(bytes((1, r, g, b, t)))
            self.i2.stop()
        
    def hex(self, hhh, t = 0):
        r = (hhh >> 16) & 0xff
        g = (hhh >> 8) & 0xff
        b = hhh & 0xff
        self.rgb(r, g, b, t)

class Pot:
    def __init__(self, i2, a = 0x28):
        self.i2 = i2
        self.a = a

    def read(self):
        self.i2.start(self.a, 1)
        (r,) = struct.unpack("B", self.i2.read(1))
        self.i2.stop()
        return r

    def raw(self):
        return self.i2.regrd(self.a, 0, "H")

    def rd(self, r):
        return self.i2.regrd(self.a, r)

class Beep:
    def __init__(self, i2, a = 0x30):
        self.i2 = i2
        self.a = a

    def beep(self, dur, note):
        self.i2.regwr(self.a, dur, note)

class Remote:
    def __init__(self, i2, a = 0x60):
        self.i2 = i2
        self.a = a

    def key(self):
        while True:
            r = self.i2.regrd(self.a, 0)
            if r != 0:
                return chr(r)

    def raw(self):
        r = self.i2.regrd(self.a, 1, "4BH")
        if r[:4] != (0xff, 0xff, 0xff, 0xff):
            return r
        else:
            return None

class Temp:
    def __init__(self, i2, a = 0x48):
        self.i2 = i2
        self.a = a

    def reg(self, r):
        return self.i2.regrd(self.a, r, ">h")
        
    def read(self):
        return (self.reg(0) >> 5) * 0.125
