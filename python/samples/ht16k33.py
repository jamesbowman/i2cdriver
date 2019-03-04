class HT16K33:
    def __init__(self, i2, a = 0x70):
        self.i2 = i2
        self.a = a
        self.command(0x21)      # Clock on
        self.command(0x81)      # Display on
        self.bright(15)
        self.load([0] * 16)

    def bright(self, n):
        assert 0 <= n < 16
        self.command(0xe0 + n)

    def command(self, b):
        assert(self.i2.start(self.a, 0))
        assert(self.i2.write([b]))
        self.i2.stop()

    def load(self, b128):
        self.i2.start(self.a, 0)
        self.i2.write([0] + b128)
        self.i2.stop()
