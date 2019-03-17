import sys
import serial
import time
import struct
from collections import OrderedDict

__version__ = '0.0.4'

PYTHON2 = (sys.version_info < (3, 0))

import EDS

class I2CTimeout(Exception):
    pass

class InternalState(OrderedDict):
    def __repr__(self):
        return "".join(["%8s %4x\n" % (k, v) for (k, v) in self.items()])

class START:
    pass

class STOP:
    pass

class I2CDriver:
    """
    I2CDriver interface.

    The following variables are available:

        product     product code e.g. 'i2cdriver1'
        serial      serial string of I2CDriver
        uptime      time since I2CDriver boot, in seconds
        voltage     USB voltage, in V
        current     current used by attached device, in mA
        temp        temperature, in degrees C
        scl         state of SCL
        sda         state of SDA
        speed       current device speed in KHz (100 or 400)
        mode        IO mode (I2C or bitbang)
        pullups     programmable pullup enable pins
        ccitt_crc   CCITT-16 CRC of all transmitted and received bytes

    """
    def __init__(self, port = "/dev/ttyUSB0", reset = True):
        self.ser = serial.Serial(port, 1000000, timeout = 1)

        # May be in capture or monitor mode, send char and wait for 50 ms
        self.ser.write(b'@')
        time.sleep(.050)

        # May be waiting up to 64 bytes of input (command code 0xff)
        self.ser.write(b'@' * 64)
        self.ser.flush()

        while self.ser.inWaiting():
            self.ser.read(self.ser.inWaiting())

        for c in [0x55, 0x00, 0xff, 0xaa]:
            r = self.__echo(c)
            if r != c:
                print('Echo test failed - not attached?')
                print('Expected %r but received %r' % (c, r))
                raise IOError
        self.getstatus()
        if reset == "never":
            return
        if reset or (self.scl, self.sda) != (1, 1):
            if self.reset() != 3:
                assert 0, "I2C bus is busy"
            self.getstatus()
        self.setspeed(100)

    if PYTHON2:
        def __ser_w(self, s):
            if isinstance(s, list) or isinstance(s, tuple):
                s = "".join([chr(c) for c in s])
            self.ser.write(s)
    else:
        def __ser_w(self, s):
            if isinstance(s, list) or isinstance(s, tuple):
                s = bytes(s)
            self.ser.write(s)

    def __echo(self, c):
        self.__ser_w([ord('e'), c])
        r = self.ser.read(1)
        if PYTHON2:
            return ord(r[0])
        else:
            return r[0]

    def setspeed(self, s):
        assert s in (100, 400)
        c = {100:b'1', 400:b'4'}[s]
        self.__ser_w(c)

    def setpullups(self, s):
        assert 0 <= s < 64
        self.__ser_w([ord('u'), s])

    def start(self, b, rw):
        """ start the i2c transaction """
        self.__ser_w([ord('s'), (b << 1) | rw])
        return self.ack()

    def ack(self):
        a = ord(self.ser.read(1))
        if a & 2:
            raise I2CTimeout
        return (a & 1) != 0

    def stop(self):
        """ stop the i2c transaction """
        self.ser.write(b'p')

    def read(self, l):
        """ Read l bytes from the I2C device, and NAK the last byte """
        r = []
        if l >= 64:
            bulkpart = (l-1) // 64
            for i in range(bulkpart):
                self.__ser_w([ord('a'), 64])
                r.append(self.ser.read(64))
            l -= 64 * bulkpart
        assert 0 <= l <= 64
        self.__ser_w([0x80 + l - 1])
        r.append(self.ser.read(l))
        return b''.join(r)

    def write(self, bb):
        """ Write bb to the I2C device """
        ack = True
        for i in range(0, len(bb), 64):
            sub = bb[i:i + 64]
            self.__ser_w([0xc0 + len(sub) - 1])
            self.__ser_w(sub)
            ack = self.ack()
        return ack

    def monitor(self, s):
        if s:
            self.__ser_w(b'm')
            time.sleep(.1)
        else:
            self.__ser_w(b' ')
            time.sleep(.1)
            self.__echo(0x40)

    def reboot(self):
        self.__ser_w(b'_')
        time.sleep(.5)

    def reset(self):
        self.__ser_w(b'x')
        return struct.unpack("B", self.ser.read(1))[0] & 3

    def regrd(self, dev, reg, fmt = "B"):
        if isinstance(fmt, str):
            n = struct.calcsize(fmt)
            self.__ser_w(b'r' + struct.pack("BBB", dev, reg, n))
            r = struct.unpack(fmt, self.ser.read(n))
            if len(r) == 1:
                return r[0]
            else:
                return r
        else:
            n = fmt
            self.__ser_w(b'r' + struct.pack("BBB", dev, reg, n))
            return self.ser.read(n)

    def regwr(self, dev, reg, *vv):
        r = self.start(dev, 0)
        if r:
            r = self.write(struct.pack("B", reg))
            if r:
                r = self.write(vv)
        self.stop()
        return r

    def getstatus(self):
        """ Update all status variables """
        self.ser.write(b'?')
        r = self.ser.read(80)
        body = r[1:-1].decode() # remove [ and ]
        (self.product,
         self.serial,
         uptime,
         voltage,
         current,
         temp,
         mode,
         sda,
         scl,
         speed,
         pullups,
         ccitt_crc) = body.split()
        self.uptime = int(uptime)
        self.voltage = float(voltage)
        self.current = float(current)
        self.temp = float(temp)
        self.mode = mode
        self.scl = int(scl)
        self.sda = int(sda)
        self.speed = int(speed)
        self.pullups = int(pullups, 16)
        self.ccitt_crc = int(ccitt_crc, 16)
        return repr(self)

    def introspect(self):
        """ Update all status variables """
        self.ser.write(b'J')
        r = self.ser.read(80)
        assert len(r) == 80, r
        body = r[1:-1].decode() # remove [ and ]
        nn = (
            "id ds sp SMB0CF SMB0CN T2 T3 IE EIE1 P0 P0MDIN P0MDOUT P1 P1MDIN P1MDOUT P2 P2MDOUT".split() +
            "convs".split()
        )
        bb = [int(w, 16) for w in body.split()]
        assert len(nn) == len(bb)
        return InternalState(zip(nn, bb))

    def restore(self):
        self.ser.write(b'i')

    def __repr__(self):
        return "<%s serial=%s uptime=%d, SCL=%d, SDA=%d>" % (
            self.product,
            self.serial,
            self.uptime,
            self.scl,
            self.sda)

    def scan(self, silent = False):
        """ Performs an I2C bus scan.
        If silent is False, prints a map of devices.
        Returns a list of the device addresses. """
        self.ser.write(b'd')
        d = struct.unpack("112c", self.ser.read(112))
        if not silent:
            for a,p in enumerate(d, 8):
                if p == b"1":
                    st = "%02X" % a
                else:
                    st = "--"
                sys.stdout.write(st + " ")
                if (a % 8) == 7:
                    sys.stdout.write("\n")
        return [a for a,p in enumerate(d, 8) if p == b"1"]

    def capture_start(self):
        self.__ser_w([ord('c')])
        def nstream():
            while 1:
                for b in self.ser.read(256):
                    yield (b >> 4) & 0xf
                    yield b        & 0xf
        def parser():
            for n in nstream():
                if n == 0:
                    pass
                elif n == 1:
                    yield START
                    bits = []
                elif n == 2:
                    yield STOP
                    bits = []
                elif n in (8,9,10,11,12,13,14,15):
                    # w(str(n&7))
                    bits.append(n & 7)
                    if len(bits) == 3:
                        b9 = (bits[0] << 6) | (bits[1] << 3) | bits[2]
                        b8 = (b9 >> 1)
                        ack = b9 & 1
                        yield (b8, ack == 0)
                        bits = []
                else:
                    assert 0, "unexpected token"
        return parser

    def capture_stop(self):
        while self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
        self.__ser_w([ord('c')])
        while self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)
        self.__echo(0x40)

    def capture(self):
        self.__ser_w([ord('c')])
        while 0:
            b = self.ser.read(1)
            for c in b:
                print("%02x" % c)
        w = sys.stdout.write
        def nstream():
            while 1:
                for b in self.ser.read(256):
                    yield (b >> 4) & 0xf
                    yield b        & 0xf
        bits = []
        for n in nstream():
            if n == 0:
                w(".")
            elif n == 1:
                w("S")
                bits = []
            elif n == 2:
                w("P\n")
                bits = []
            elif n in (8,9,10,11,12,13,14,15):
                # w(str(n&7))
                bits.append(n & 7)
                if len(bits) == 3:
                    b9 = (bits[0] << 6) | (bits[1] << 3) | bits[2]
                    b8 = (b9 >> 1)
                    ack = b9 & 1
                    w('%02x%s' % (b8, " !"[ack]))
                    bits = []
            else:
                assert 0, "unexpected token"
