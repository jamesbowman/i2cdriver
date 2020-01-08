import sys
import time
import struct
import random

import i2cdriver
import unittest

DUT = "dut" # grn0
AGG = "agg" # blk1

def bit(b, x):
    return 1 & (x >> b)

class TestDUT(unittest.TestCase):
    def setUp(self):
        self.i2 = i2cdriver.I2CDriver(DUT)
        self.ag = i2cdriver.I2CDriver(AGG)

    def init(self):
        self.i2.reboot()
        self.i2.setspeed(400)
        self.i2.getstatus()
        return self.i2

    def lm75_read(self, i, reg):
        (tr,) = struct.unpack(">h", i.regrd(0x48, reg, 2))
        return tr

    def lm75_slow_read(self, i, reg):
        i.start(0x48, 0)
        i.write(struct.pack("B", reg))
        i.start(0x48, 1)
        (tr,) = struct.unpack(">h", i.read(2))
        i.stop()
        return tr

    def lm75_write(self, i, reg, v):
        i.start(0x48, 0)
        i.write(struct.pack(">Bh", reg, v))
        i.stop()

    def stack0(self):
        self.s0 = self.i2.introspect()

    def stacksame(self):
        s1 = self.i2.introspect()
        for i in ("ds", "sp"):
            self.assertEqual(self.s0[i], s1[i])

    def confirm(self):
        # Basic i2c confirmation
        self.assertEqual(self.lm75_read(self.i2, 2), 0x4b00)

    def confirm_sampling(self):
        # Check that analog sampling is happening
        econvs = {
            "i2cdriver1" : {0,1,2},
            "i2cdriverm" : {0}
        }[self.i2.product]
        s = set()
        while len(s) < len(econvs):
            s.add(self.i2.introspect()["convs"])
        self.assertEqual(s, econvs)

    def test_temperature(self):
        # Confirm onboard temperature sensor is reasonable and changing
        i2 = self.i2
        i2.getstatus()
        onboard = i2.temp
        external = (self.lm75_read(i2, 0) >> 5) * 0.125
        self.assertTrue(abs(onboard - external) < 10)

        # Wait up to 10 seconds for temperature to change
        t0 = time.time()
        while onboard == i2.temp:
            i2.getstatus()
            self.assertTrue(time.time() < (t0 + 10))

    def test_coldstart(self):
        i2 = self.init()
        s = i2.introspect()
        self.assertEqual(i2.scl, 1)
        self.assertEqual(i2.sda, 1)

    def test_scan(self):
        i2 = self.init()
        def det(a):
            r = i2.start(a, 0)
            i2.stop()
            return r
        scan = [det(a) for a in range(128)]
        e = [(i == 0x48) for i in range(128)]
        self.assertEqual(scan, e)

    def test_lm75_reg(self):
        i2 = self.i2
        self.stack0()
        vals = (0, -128, 0x7f80)
        for a in vals:
            self.lm75_write(i2, 2, a)
            for b in vals:
                self.lm75_write(i2, 3, b)
                self.assertEqual(self.lm75_read(i2, 2), a)
                self.assertEqual(self.lm75_read(i2, 3), b)
                self.assertEqual(self.lm75_slow_read(i2, 2), a)
                self.assertEqual(self.lm75_slow_read(i2, 3), b)
        self.lm75_write(i2, 2, 0x4b00)
        self.lm75_write(i2, 3, 0x5000)
        self.assertEqual(self.lm75_read(i2, 2), 0x4b00)
        self.assertEqual(self.lm75_read(i2, 3), 0x5000)
        self.stacksame()

    def test_regrd256(self):
        i2 = self.i2
        reg = 3
        self.lm75_write(i2, reg, 0x7480)
        for n in (127, 128, 129):
            self.assertEqual(i2.regrd(0x48, reg, ">" + str(n) + "h"), (0x7480,) * n)

    def test_setspeed(self):
        i2 = self.init()
        self.stack0()
        for s in (100, 400, 400, 100, 400):
            i2.setspeed(s)
            i2.getstatus()
            self.assertEqual(i2.speed, s)
            self.confirm()
        self.stacksame()
        
    def test_cap_idle(self):
        i2 = self.init()
        c = i2.capture_start()
        t0 = time.time()
        d = i2.ser.read(15)
        t1 = time.time()
        i2.capture_stop()

        self.assertEqual(d, bytes(15))
        self.assertTrue(0.4 < (t1 - t0) < 0.6)

    def test_cap_0(self):
        def test_0():
            self.lm75_write(ag, 2, 0x4b00)
            return [
                i2cdriver.START(0x48, 0, 1),
                i2cdriver.BYTE(0x02, 0, True),
                i2cdriver.BYTE(0x4b, 0, True),
                i2cdriver.BYTE(0x00, 0, True),
                i2cdriver.STOP()
            ]
        def test_1():
            self.lm75_slow_read(ag, 2)
            return [
                i2cdriver.START,
                (0x90, True),
                (0x02, True),
                i2cdriver.START,
                (0x91, True),
                (0x4b, True),
                (0x00, False),
                i2cdriver.STOP
            ]

        i2 = self.init()
        ag = self.ag
        for t in (test_0, ): # test_1):
            c = i2.capture_start()
            time.sleep(.1)
            ee = t()
            for e,a in zip(ee, c()):
                self.assertEqual(a, e)
            i2.capture_stop()

    def test_pullups(self):
        i2 = self.init()
        i2.getstatus()
        self.assertEqual(i2.pullups, 0b100100)

        rr = random.sample(list(range(64)), 64)
        if i2.product == "i2cdriver1":
            respins = (0, 1, 3, 13, 14, 16)
        else:
            respins = (10, 11, 12,  6, 7, 8)
        for r in rr:
            i2.setpullups(r)
            i2.getstatus()
            self.assertEqual(i2.pullups, r)
            s = i2.introspect()
            p = s["P0"] + (s["P1"] << 8) + (s["P2"] << 16)
            d = s["P0MDOUT"] + (s["P1MDOUT"] << 8) + (s["P2MDOUT"] << 16)
            for b,pb in enumerate(respins):
                self.assertEqual(bit(pb, p), 1)
                self.assertEqual(bit(b, r), bit(pb, d))

    def test_zz5s(self):
        i2 = self.init()
        time.sleep(5)
        i2.getstatus()
        self.assertTrue(i2.uptime in (4,5,6))

    def checkmode(self, c):
        self.i2.getstatus()
        self.assertEqual(self.i2.mode, c)

    def test_bitbang(self):
        i2 = self.init()
        self.checkmode('I')
        self.stack0()
        i2.ser.write(b'b')
        for i in range(1000):                           # Square wave for a while
            i2.ser.write(bytes([0b1111, 0b0101]))
        i2.ser.write(bytes([0b1010, 0b11010]))          # Float, request a byte
        self.assertEqual(i2.ser.read(1), bytes([3]))    # both should be high
        i2.ser.write(bytes([0b0101]))                   # Leave driven low
        i2.ser.write(b'@')
        self.checkmode('B')
        i2.restore()
        self.checkmode('I')
        self.stacksame()
        self.assertEqual(self.lm75_read(i2, 2), 0x4b00)

    def test_bitbang_idem(self):
        # Confirm bitbang mode idempotence
        i2 = self.init()
        if i2.product != "spidriver1":
            return
        for n in [0b1101, 0b1011, 0b0000, 0b1111] + list(range(16)):
            i2.ser.write(b'b' + bytes([n, 0x40]))
            s1 = i2.introspect()
            self.assertEqual(bit(0, n), bit(2, s1["P0MDOUT"]))
            self.assertEqual(bit(1, n), bit(2, s1["P0"]))
            self.assertEqual(bit(2, n), bit(4, s1["P1MDOUT"]))
            self.assertEqual(bit(3, n), bit(4, s1["P1"]))
            i2.ser.write(b'b' + bytes([0x40]))
            s2 = i2.introspect()
            for i in ("P0", "P1", "P0MDOUT", "P1MDOUT"):
                self.assertEqual(s1[i], s2[i])
        self.assertEqual(i2.introspect()["SMB0CF"], 0x00)
        i2.restore()
        self.assertEqual(i2.introspect()["SMB0CF"], 0xd8)

    def test_bitbang_bidir(self):
        self.stack0()
        dd = (self.i2, self.ag)
        [i2.ser.write(b'b') for i2 in dd]
        LOW     = 0b01
        HIGH    = 0b11
        INPUT   = 0b10
        def port(d, sda, scl, read = False):
            d.ser.write(bytes([sda | (scl << 2) | (int(read) << 4)]))
            if read:
                (r,) = d.ser.read(1)
                return (r & 1, (r >> 1) & 1)

        for sda in (LOW, HIGH, LOW):
            for scl in (HIGH, LOW, HIGH):
                expected = (int(sda == HIGH), int(scl == HIGH))

                for (tx,rx) in [(0,1), (1,0)]:
                    port(dd[tx], sda, scl)
                    port(dd[rx], INPUT, INPUT)
                    self.assertEqual(expected, port(dd[rx], INPUT, INPUT, True))

        [i2.ser.write(b'@') for i2 in dd]
        [i2.restore() for i2 in dd]
        self.stacksame()

    def test_reset(self):
        i2 = self.init()
        self.stack0()
        i2.reset()
        self.stacksame()
        for i in range(100):
            i2.reset()
        self.stacksame()
        self.confirm()

    def test_sampling(self):
        self.confirm_sampling()

    def test_weigh(self):
        # Confirm resistance measurement
        i2 = self.init()
        ag = self.ag
        self.stack0()

        def sample(p, pv):
            i2.setpullups(p)
            i2.ser.write(b'v' + bytes([pv]))
            while True:
                i2.ser.write(b'w')
                r = i2.ser.read(1)
                if r[0] == 0:
                    break
            return struct.unpack("2B", i2.ser.read(2))

        def estimate(a, hi, res):
            if a == 0:
                return 0
            v = a / hi
            return (res / v) - res
        def mean(s):
            return sum(s) / len(s)
        def resistance(rr):
            if rr == []:
                return 0
            return 1 / sum([1/r for r in rr])
        def pullups():
            sHH = sample(0b111111, 0b111111)
            sAA = sample(0b001001, 0b110110)
            sBB = sample(0b010010, 0b101101)
            sCC = sample(0b100100, 0b011011)
            sda_r = mean((estimate(sAA[0], sHH[0], 2200),
                          estimate(sBB[0], sHH[0], 4300),
                          estimate(sCC[0], sHH[0], 4700)))
            scl_r = mean((estimate(sAA[1], sHH[1], 2200),
                          estimate(sBB[1], sHH[1], 4300),
                          estimate(sCC[1], sHH[1], 4700)))
            return (sda_r, scl_r)

        for x in range(64):
            # print(x)
            ag.setpullups(x)
            esda = resistance([r for i,r in enumerate([2200, 4300, 4700]) if bit(i, x)])
            escl = resistance([r for i,r in enumerate([2200, 4300, 4700]) if bit(3 + i, x)])
            # print("expected %d" % esda, escl)
            sda,scl = pullups()
            # print("SDA pullup %d, SCL pullup %d" % (sda,scl))

            def close(e, a):
                margin = max(100, e / 10)
                return abs(a - e) < margin
            self.assertTrue(close(esda, sda))
            self.assertTrue(close(escl, scl))
        self.confirm_sampling()

        self.init() # restore pullups

if __name__ == '__main__':
    unittest.main()
