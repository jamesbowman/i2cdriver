"""
Example for BNO080 integrated IMU.
Available from Sparkfun.
"""

import sys
import serial
import time
import struct
import random
import math

from i2cdriver import I2CDriver
def hexdump(s):
    def toprint(c):
        if 32 <= c < 127:
            return chr(c)
        else:
            return "."
    def hexline(s):
        return (" ".join(["%02x" % c for c in s]).ljust(49) +
                "|" +
                "".join([toprint(c) for c in s]).ljust(16) +
                "|")
    return "\n".join([hexline(s[i:i+16]) for i in range(0, len(s), 16)])

CHANNEL_COMMAND = 0
CHANNEL_EXECUTABLE = 1
CHANNEL_CONTROL = 2
CHANNEL_REPORTS = 3
CHANNEL_WAKE_REPORTS = 4
CHANNEL_GYRO = 5

# All the ways we can configure or talk to the BNO080, figure 34, page 36 reference manual
# These are used for low level communication with the sensor, on channel 2
SHTP_REPORT_COMMAND_RESPONSE = 0xF1
SHTP_REPORT_COMMAND_REQUEST = 0xF2
SHTP_REPORT_FRS_READ_RESPONSE = 0xF3
SHTP_REPORT_FRS_READ_REQUEST = 0xF4
SHTP_REPORT_PRODUCT_ID_RESPONSE = 0xF8
SHTP_REPORT_PRODUCT_ID_REQUEST = 0xF9
SHTP_REPORT_BASE_TIMESTAMP = 0xFB
SHTP_REPORT_SET_FEATURE_COMMAND = 0xFD

# All the different sensors and features we can get reports from
# These are used when enabling a given sensor
SENSOR_REPORTID_ACCELEROMETER = 0x01
SENSOR_REPORTID_GYROSCOPE = 0x02
SENSOR_REPORTID_MAGNETIC_FIELD = 0x03
SENSOR_REPORTID_LINEAR_ACCELERATION = 0x04
SENSOR_REPORTID_ROTATION_VECTOR = 0x05
SENSOR_REPORTID_GRAVITY = 0x06
SENSOR_REPORTID_GAME_ROTATION_VECTOR = 0x08
SENSOR_REPORTID_GEOMAGNETIC_ROTATION_VECTOR = 0x09
SENSOR_REPORTID_TAP_DETECTOR = 0x10
SENSOR_REPORTID_STEP_COUNTER = 0x11
SENSOR_REPORTID_STABILITY_CLASSIFIER = 0x13
SENSOR_REPORTID_PERSONAL_ACTIVITY_CLASSIFIER = 0x1E

# Record IDs from figure 29, page 29 reference manual
# These are used to read the metadata for each sensor type
FRS_RECORDID_ACCELEROMETER = 0xE302
FRS_RECORDID_GYROSCOPE_CALIBRATED = 0xE306
FRS_RECORDID_MAGNETIC_FIELD_CALIBRATED = 0xE309
FRS_RECORDID_ROTATION_VECTOR = 0xE30B

# Command IDs from section 6.4, page 42
# These are used to calibrate, initialize, set orientation, tare etc the sensor
COMMAND_ERRORS = 1
COMMAND_COUNTER = 2
COMMAND_TARE = 3
COMMAND_INITIALIZE = 4
COMMAND_DCD = 6
COMMAND_ME_CALIBRATE = 7
COMMAND_DCD_PERIOD_SAVE = 9
COMMAND_OSCILLATOR = 10
COMMAND_CLEAR_DCD = 11

CALIBRATE_ACCEL = 0
CALIBRATE_GYRO = 1
CALIBRATE_MAG = 2
CALIBRATE_PLANAR_ACCEL = 3
CALIBRATE_ACCEL_GYRO_MAG = 4
CALIBRATE_STOP = 5

def normalize(v, tolerance=0.00001):
    mag2 = sum(n * n for n in v)
    if abs(mag2 - 1.0) > tolerance:
        mag = math.sqrt(mag2)
        v = tuple(n / mag for n in v)
    return v

class BNO080:
    def __init__(self, i2, a = 0x4b):
        self.i2 = i2
        self.a = a
        self.seqno = [0] * 8

        if 1:
            self.sendPacket(CHANNEL_EXECUTABLE, [1])
            time.sleep(0.150)
            while True:
                if not self.receivePacket():
                    break

        self.setFeature(SENSOR_REPORTID_ROTATION_VECTOR, 50000)

    def read_quaternion(self):
        while True:
            r = self.receivePacket()
            while r:
                tag = r[0]
                r = r[1:]
                if tag == 0xfb:
                    # print("Time %d" % struct.unpack("I", r[:4]))
                    r = r[4:]
                elif tag == SHTP_REPORT_COMMAND_RESPONSE:
                    r = r[16:]
                elif tag == 0xfc:
                    # print("Get Feature Response")
                    r = r[17:]
                elif tag == SENSOR_REPORTID_ACCELEROMETER:
                    r = r[10:]
                elif tag == SENSOR_REPORTID_ROTATION_VECTOR:
                    (_,_,_,i,j,k,w,_) = struct.unpack("<BBBhhhhh", r[:14])
                    Q14 = 2 ** -14
                    # print((i * Q14, j * Q14, k * Q14, w * Q14))
                    return (w * Q14, i * Q14, j * Q14, k * Q14)
                    r = r[14:]
                else:
                    assert 0, "Bad tag %#x" % tag

    def setFeature(self, reportID, timeBetweenReports, specificConfig = 0):
        p = struct.pack("<BBBHIII",
            SHTP_REPORT_SET_FEATURE_COMMAND,
            reportID, 
            0, 0,
            timeBetweenReports,
            0, specificConfig)
        # print(hexdump(p))

        self.sendPacket(CHANNEL_CONTROL, p)

    def sendPacket(self, channel, data):
        # print('send on', channel, 'seq', self.seqno[channel])
        self.i2.start(self.a, 0)
        self.i2.write(struct.pack("<HBB", 4 + len(data), channel, self.seqno[channel]))
        self.i2.write(data)
        self.i2.stop()
        self.seqno[channel] += 1

    def receivePacket(self):
        if not self.i2.start(self.a, 1):
            self.i2.stop()
            return None
        hdr = self.i2.read(4)
        self.i2.stop()
        length, channel, sequence = (struct.unpack("<HBB", hdr))
        length &= 0x7fff
        # print()
        # print('length', length)
        # print('channel', channel)
        # print('sequence', sequence)
        if length == 0 or channel not in range(8):
            return None

        # self.seqno[channel] = sequence + 1

        self.i2.start(self.a, 1)
        data = self.i2.read(length)
        self.i2.stop()
        # print(len(data), repr(data))
        # print(hexdump(data[4:]))
        return data[4:]
    
    def showpacket(self, data):
        tag = data[0]
        print('tag', tag)
        r = data[1:]
        if tag == 0:
            self.showpacket_00(r)
        else:
            assert False, "Cannot show packet %02x" % tag

    def showpacket_00(self, ad):
        while ad:
            (T, L) = struct.unpack("BB", ad[:2])
            V = ad[2:2+L]
            decoder = {
            1:    lambda: ("GUID", struct.unpack("I", V)),
            2:    lambda: ("MaxCargoPlusHeaderWrite", struct.unpack("H", V)),
            3:    lambda: ("MaxCargoPlusHeaderRead", struct.unpack("H", V)),
            4:    lambda: ("MaxTransferWrite", struct.unpack("H", V)),
            5:    lambda: ("MaxTransferRead", struct.unpack("H", V)),
            6:    lambda: ("NormalChannel", struct.unpack("B", V)),
            7:    lambda: ("WakeChannel", struct.unpack("B", V)),
            8:    lambda: ("AppName", (V[:-1].decode(), )),
            9:    lambda: ("ChannelName", (V[:-1].decode(), )),
            0x80: lambda: ("SHTP Version", (V[:-1].decode(), )),
            }.get(T, lambda: (str(T), (V,)))
            (nm,f) = decoder()
            print("%5d %-26s: %r" % ((len(ad), nm, ) + f))
            ad = ad[2+L:]

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    d = BNO080(i2)
    while True:
        print('quaternion:', d.read_quaternion())
