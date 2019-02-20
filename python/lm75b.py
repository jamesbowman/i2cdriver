class LM75B:
    def __init__(self, i2, a = 0x48):
        self.i2 = i2
        self.a = a

    def reg(self, r):
        return self.i2.regrd(self.a, r, ">h")
        
    def read(self):
        return (self.reg(0) >> 5) * 0.125
