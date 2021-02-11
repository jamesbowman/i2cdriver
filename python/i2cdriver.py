import sys
import serial
import time
import struct
from collections import OrderedDict

__version__ = '1.0.0'

PYTHON2 = (sys.version_info < (3, 0))

import EDS

class I2CTimeout(Exception):
    pass

class InternalState(OrderedDict):
    def __repr__(self):
        return "".join(["%8s %4x\n" % (k, v) for (k, v) in self.items()])

class _I2CEvent:
    def rrw(self):
        return ["WRITE", "READ"][self.rw]
    def rack(self):
        return ["NACK", "ACK"][self.ack]

class START(_I2CEvent):
    def __init__(self, addr, rw, ack):
        self.addr = addr
        self.rw = rw
        self.ack = ack
    def __repr__(self):
        return "<START 0x%02x %s %s>" % (self.addr, self.rrw(), self.rack())
    def dump(self, f, fmt):
        if fmt == "csv":
            f.writerow(("START", self.rrw(), str(self.addr), self.rack()))
        else:
            assert False, "unsupported format"
    def __eq__(self, other):
        return (self.addr, self.rw, self.ack) == (other.addr, other.rw, other.ack)

class STOP(_I2CEvent):
    def __repr__(self):
        return "<STOP>"
    def dump(self, f, fmt):
        if fmt == "csv":
            f.writerow(("STOP", None, None, None))
        else:
            assert False, "unsupported format"
    def __eq__(self, other):
        return isinstance(other, STOP)

class BYTE(_I2CEvent):
    def __init__(self, b, rw, ack):
        self.b = b
        self.rw = rw
        self.ack = ack
    def __repr__(self):
        return "<%s 0x%02x %s>" % (self.rrw(), self.b, self.rack())
    def dump(self, f, fmt):
        if fmt == "csv":
            f.writerow(("BYTE", self.rrw(), str(self.b), self.rack()))
        else:
            assert False, "unsupported format"
    def __eq__(self, other):
        return (self.b, self.rw, self.ack) == (other.b, other.rw, other.ack)

class I2CDriver:
    """
    A connected I2CDriver.

    :param port: The USB port to connect to
    :type port: str
    :param reset: Issue an I2C bus reset on connection
    :type reset: bool

    After connection, the following object variables reflect the current values of the I2CDriver.
    They are updated by calling :py:meth:`getstatus`.

    :ivar product: product code e.g. 'i2cdriver1' or 'i2cdriverm'
    :ivar serial: serial string of I2CDriver
    :ivar uptime: time since I2CDriver boot, in seconds
    :ivar voltage: USB voltage, in V
    :ivar current: current used by attached device, in mA
    :ivar temp: temperature, in degrees C
    :ivar scl: state of SCL
    :ivar sda: state of SDA
    :ivar speed: current device speed in KHz (100 or 400)
    :ivar mode: IO mode (I2C or bitbang)
    :ivar pullups: programmable pullup enable pins
    :ivar ccitt_crc: CCITT-16 CRC of all transmitted and received bytes

    """
    def __init__(self, port = "/dev/ttyUSB0", reset = True):
        """
        Connect to a hardware i2cdriver.

        :param port: The USB port to connect to
        :type port: str
        :param reset: Issue an I2C bus reset on connection
        :type reset: bool

        """
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
                raise I2CTimeout("Bus failed to reset - check connected devices")
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
        """
        Set the I2C bus speed.

        :param s: speed in KHz, either 100 or 400
        :type s: int
        """
        assert s in (100, 400)
        c = {100:b'1', 400:b'4'}[s]
        self.__ser_w(c)
        self.speed = s

    def setpullups(self, s):
        """
        Set the I2CDriver pullup resistors

        :param s: 6-bit pullup mask
        """
        assert 0 <= s < 64
        self.__ser_w([ord('u'), s])
        self.pullups = s

    def scan(self, silent = False):
        """ Performs an I2C bus scan.
        If silent is False, prints a map of devices.
        Returns a list of the device addresses.

        >>> i2c.scan()
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- 1C -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        48 -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        68 -- -- -- -- -- -- -- 
        -- -- -- -- -- -- -- -- 
        [28, 72, 104]
        """

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

    def reset(self):
        """ Send an I2C bus reset """
        self.__ser_w(b'x')
        return struct.unpack("B", self.ser.read(1))[0] & 3

    def start(self, dev, rw):
        """
        Start an I2C transaction

        :param dev: 7-bit I2C device address
        :param rw: read (1) or write (0)

        To write bytes ``[0x12,0x34]`` to device ``0x75``:

        >>> i2c.start(0x75, 0)
        >>> i2c.write([0x12,034])
        >>> i2c.stop()

        """
        self.__ser_w([ord('s'), (dev << 1) | rw])
        return self.ack()

    def ack(self):
        a = ord(self.ser.read(1))
        if a & 2:
            raise I2CTimeout
        return (a & 1) != 0

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
        """
        Write bytes to the selected I2C device

        :param bb: sequence to write
        """
        ack = True
        for i in range(0, len(bb), 64):
            sub = bb[i:i + 64]
            self.__ser_w([0xc0 + len(sub) - 1])
            self.__ser_w(sub)
            ack = self.ack()
        return ack

    def stop(self):
        """ stop the i2c transaction """
        self.ser.write(b'p')

    def reboot(self):
        self.__ser_w(b'_')
        time.sleep(.5)

    def regrd(self, dev, reg, fmt = "B"):
        """
        Read a register from a device.

        :param dev: 7-bit I2C device address
        :param reg: register address 0-255
        :param fmt: :py:func:`struct.unpack` format string for the register contents, or an integer byte count

        If device 0x75 has a 16-bit unsigned big-endian register 102, it can be read with:

        >>> i2c.regrd(0x75, 102, ">H")
        4999
        """

        if isinstance(fmt, str):
            r = struct.unpack(fmt, self.regrd(dev, reg, struct.calcsize(fmt)))
            if len(r) == 1:
                return r[0]
            else:
                return r
        else:
            n = fmt
            if n <= 256:
                self.__ser_w(b'r' + struct.pack("BBB", dev, reg, n & 0xff))
                return self.ser.read(n)
            else:
                self.start(dev, 0)
                self.write([reg])
                self.start(dev, 1)
                r = self.read(n)
                self.stop()
                return r

    def regwr(self, dev, reg, vv):
        """Write a device's register.

        :param dev: 7-bit I2C device address
        :param reg: register address 0-255
        :param vv: value to write. Either a single byte, or a sequence

        To set device 0x34 byte register 7 to 0xA1:

        >>> i2c.regwr(0x34, 7, 0xa1)

        If device 0x75 has a big-endian 16-bit register 102 you can set it to 4999 with:

        >>> i2c.regwr(0x75, 102, struct.pack(">H", 4999))

        """
        r = self.start(dev, 0)
        if r:
            r = self.write(struct.pack("B", reg))
            if r:
                if isinstance(vv, int):
                    vv = struct.pack("B", vv)
                r = self.write(vv)
        self.stop()
        return r

    def monitor(self, s):
        """ Enter or leave monitor mode

        :param s: ``True`` to enter monitor mode, ``False`` to leave
        """

        if s:
            self.__ser_w(b'm')
            time.sleep(.1)
        else:
            self.__ser_w(b' ')
            time.sleep(.1)
            self.__echo(0x40)

    def introspect(self):
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

    def capture_start(self, idle=False, start = START, abyte = BYTE, stop = STOP):
        """Enter I2C capture mode, capturing I2C transactions.
        :param idle: If ``True`` the generator returns ``None`` when the bus is idle. If ``False`` the generator does nothing during bus idle.

        :return: a generator which returns an object for each I2C primitive captured.
        """
        self.__ser_w([ord('c')])
        def nstream():
            while True:
                bb = self.ser.read(256)
                if PYTHON2:
                    for b in bb:
                        yield (ord(b) >> 4) & 0xf
                        yield ord(b)        & 0xf
                else:
                    for b in bb:
                        yield (b >> 4) & 0xf
                        yield b        & 0xf
        def parser():
            starting = False
            rw = 0
            for n in nstream():
                if n == 0:
                    if idle:
                        yield None
                elif n == 1:
                    starting = True
                    bits = []
                elif n == 2:
                    yield stop()
                    starting = True
                    bits = []
                elif n in (8,9,10,11,12,13,14,15):
                    # w(str(n&7))
                    bits.append(n & 7)
                    if len(bits) == 3:
                        b9 = (bits[0] << 6) | (bits[1] << 3) | bits[2]
                        b8 = (b9 >> 1)
                        ack = b9 & 1
                        if starting:
                            rw = b8 & 1
                            yield start(b8 >> 1, rw, ack == 0)
                            starting = False
                        else:
                            yield abyte(b8, rw, ack == 0)
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
