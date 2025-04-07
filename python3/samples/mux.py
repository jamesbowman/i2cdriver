import sys
from i2cdriver import I2CDriver, EDS

# Using a TCA9548A Low-Voltage 8-Channel I2C Switch
# Three LM75B temperature sensors are connected to 
# channels 0,1 and 2. All are at address 0x48.

class Mux:
    def __init__(self, i2, a = 0x70):
        self.i2 = i2
        self.a = a

    def select(self, n):
        assert n in range(8)
        self.i2.start(self.a, 0)
        self.i2.write([1 << n])
        self.i2.stop()

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    mux = Mux(i2)
    sensors = [
        (0, EDS.Temp(i2)),
        (1, EDS.Temp(i2)),
        (2, EDS.Temp(i2))
        ]

    # Reset all 8 channels
    for chan in range(8):
        mux.select(chan)
        i2.reset()

    def read(chan, dev):
        mux.select(chan)
        celsius = dev.read()
        return celsius

    while 1:
        print(" ".join(["%.1f" % read(chan, dev) for chan,dev in sensors]))
