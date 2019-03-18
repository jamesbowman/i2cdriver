import time
import struct
import sys
import os
import re
import threading
from functools import partial

import serial.tools.list_ports as slp

import wx
import wx.lib.newevent as NE

from i2cdriver import I2CDriver

PingEvent, EVT_PING = NE.NewEvent()

def ping_thr(win):
    while True:
        wx.PostEvent(win, PingEvent())
        time.sleep(1)

class HexTextCtrl(wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        super(HexTextCtrl, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_TEXT, self.on_text)
    def on_text(self, event):
        event.Skip()
        selection = self.GetSelection()
        value = self.GetValue().upper()
        hex = " 0123456789ABCDEF"
        value = "".join([c for c in value if c in hex])
        self.ChangeValue(value)
        self.SetSelection(*selection)

class Frame(wx.Frame):
    def __init__(self, preferred = None):

        self.sd = None

        def widepair(a, b):
            r = wx.BoxSizer(wx.HORIZONTAL)
            r.Add(a, 1, wx.LEFT)
            r.AddStretchSpacer(prop=1)
            r.Add(b, 1, wx.RIGHT)
            return r

        def pair(a, b):
            r = wx.BoxSizer(wx.HORIZONTAL)
            r.Add(a, 1, wx.LEFT)
            r.Add(b, 0, wx.RIGHT)
            return r

        def rpair(a, b):
            r = wx.BoxSizer(wx.HORIZONTAL)
            r.Add(a, 0, wx.LEFT)
            r.Add(b, 1, wx.RIGHT)
            return r

        def label(s):
            return wx.StaticText(self, label = s)

        def button(s, f):
            r = wx.Button(self, label = s)
            r.Bind(wx.EVT_BUTTON, f)
            return r

        def hbox(items):
            r = wx.BoxSizer(wx.HORIZONTAL)
            [r.Add(i, 0, wx.EXPAND) for i in items]
            return r

        def hcenter(i):
            r = wx.BoxSizer(wx.HORIZONTAL)
            r.AddStretchSpacer(prop=1)
            r.Add(i, 2, wx.CENTER)
            r.AddStretchSpacer(prop=1)
            return r

        def vbox(items):
            r = wx.BoxSizer(wx.VERTICAL)
            [r.Add(i, 0, wx.EXPAND) for i in items]
            return r

        wx.Frame.__init__(self, None, -1, "I2CDriver")

        self.bold = self.GetFont().Bold()
        self.addrfonts = [
            self.GetFont(),
            self.bold
        ]

        self.label_serial = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_voltage = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_current = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_temp = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_speed = wx.Choice(self, choices = ["100", "400"])
        self.label_speed.Bind(wx.EVT_CHOICE, self.set_speed)
        self.label_sda = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_scl = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)
        self.label_uptime = wx.StaticText(self, label = "-", style = wx.ALIGN_RIGHT)

        self.dynamic = [
            self.label_voltage,
            self.label_current,
            self.label_temp,
            self.label_speed,
            self.label_sda,
            self.label_scl,
            self.label_uptime
        ]

        self.Bind(EVT_PING, self.refresh)

        def addrbutton(s):
            r = wx.RadioButton(self, label = s)
            r.Bind(wx.EVT_RADIOBUTTON, self.choose_addr)
            return r
        self.heat = {i:addrbutton("%02X" % i) for i in range(8, 112)}
        devgrid = wx.GridSizer(8, wx.Size(4, 6))
        for i,l in sorted(self.heat.items()):
            devgrid.Add(l)

        self.monitor = False
        self.ckM = wx.ToggleButton(self, label = "Monitor mode")
        self.ckM.Bind(wx.EVT_TOGGLEBUTTON, self.check_m)

        self.txVal = HexTextCtrl(self, size=wx.DefaultSize, style=0)

        self.rxVal = HexTextCtrl(self, size=wx.DefaultSize, style=wx.TE_READONLY)

        txButton = wx.Button(self, label = "write")
        txButton.Bind(wx.EVT_BUTTON, partial(self.write, self.txVal))

        self.rxCount = wx.SpinCtrl(self, min = 1)
        rxButton = wx.Button(self, label = "read")
        rxButton.Bind(wx.EVT_BUTTON, self.read)

        self.dev_widgets = [txButton, rxButton]

        self.reset_button = button("i2c reset", self.reset)

        self.stop_button = button("stop", self.stop)
        self.stop_button.Enable(False)

        self.allw = [self.ckM, self.reset_button]
        [w.Enable(False) for w in self.allw]
        self.devs = self.devices()
        cb = wx.ComboBox(self, choices = sorted(self.devs.keys()), style = wx.CB_READONLY)
        cb.Bind(wx.EVT_COMBOBOX, self.choose_device)

        self.no_addr()
        [self.hot(i, False) for i in self.heat]
        self.started = False

        info = vbox([
        pair(label("Serial"),   self.label_serial),
        pair(label("Voltage"),  self.label_voltage),
        pair(label("Current"),  self.label_current),
        pair(label("Temp."),    self.label_temp),
        pair(label("SDA"),      self.label_sda),
        pair(label("SCL"),      self.label_scl),
        pair(label("Running"),  self.label_uptime),
        pair(label("Speed"),    self.label_speed),
        ])

        vb = vbox([
            label(""),
            hcenter(cb),
            label(""),
            hcenter(self.ckM),
            hcenter(self.reset_button),
            label(""),
            hcenter(info),
            # hcenter(pair(
            #     vbox([
            #         label("Serial"),
            #         label("Voltage"),
            #         label("Current"),
            #         label("Temp."),
            #         label("Speed"),
            #         label("SDA"),
            #         label("SCL"),
            #         label("Running"),
            #     ]),
            #     vbox([
            #         self.label_serial,
            #         self.label_voltage,
            #         self.label_current,
            #         self.label_temp,
            #         self.label_speed,
            #         self.label_sda,
            #         self.label_scl,
            #         self.label_uptime,
            #     ])
            # )),

            label(""),
            hcenter(devgrid),
            label(""),
            hcenter(pair(self.txVal, txButton)),
            hcenter(pair(self.rxVal, hbox([self.rxCount, rxButton]))),
            label(""),
            hcenter(self.stop_button),

            label(""),
        ])
        self.SetSizerAndFit(vb)
        self.SetAutoLayout(True)

        if len(self.devs) > 0:
            if preferred in self.devs:
                d1 = preferred
            else:
                d1 = min(self.devs)
            self.connect(self.devs[d1])
            cb.SetValue(d1)

        t = threading.Thread(target=ping_thr, args=(self, ))
        t.setDaemon(True)
        t.start()

    def start(self, rw):
        self.sd.start(self.addr, rw)
        self.started = True
        self.stop_button.Enable(True)

    def stop(self, e = None):
        self.sd.stop()
        self.started = False
        self.stop_button.Enable(False)

    def reset(self, e = None):
        self.sd.reset()
        self.started = False

    def write(self, htc, e):
        if (self.addr is not None) and htc.GetValue():
            vv = [int(c,16) for c in htc.GetValue().split()]
            self.start(0)
            self.sd.write(vv)

    def read(self, e):
        n = int(self.rxCount.GetValue())
        if self.addr is not None:
            self.start(1)
            r = self.sd.read(n)
            bb = struct.unpack("B"*n, r)
            self.rxVal.SetValue(" ".join(["%02X" % b for b in bb]))
            self.stop()

    def devices(self):
        if sys.platform in ('win32', 'cygwin'):
            return {pi.device: pi.device for pi in slp.comports()}
        elif sys.platform == 'darwin':
            devdir = "/dev/"
            pattern = "^cu.usbserial-(.*)"
        else:
            devdir = "/dev/serial/by-id/"
            pattern = "^usb-FTDI_FT230X_Basic_UART_(........)-"

        if not os.access(devdir, os.R_OK):
            return {}
        devs = os.listdir(devdir)
        def filter(d):
            m = re.match(pattern, d)
            if m:
                return (m.group(1), devdir + d)
        seldev = [filter(d) for d in devs]
        return dict([d for d in seldev if d])

    def connect(self, dev):
        self.sd = I2CDriver(dev)
        [w.Enable(True) for w in self.allw]
        self.refresh(None)

    def refresh(self, e):
        if self.sd and not self.monitor:
            lowhigh = ["LOW", "HIGH"]
            self.sd.getstatus()
            self.label_serial.SetLabel(self.sd.serial)
            self.label_voltage.SetLabel("%.2f V" % self.sd.voltage)
            self.label_current.SetLabel("%d mA" % self.sd.current)
            self.label_temp.SetLabel("%.1f C" % self.sd.temp)
            self.label_speed.SetSelection({100:0, 400:1}[self.sd.speed])

            self.label_sda.SetLabel(lowhigh[self.sd.sda])
            self.label_scl.SetLabel(lowhigh[self.sd.scl])
            days = self.sd.uptime // (24 * 3600)
            rem = self.sd.uptime % (24 * 3600)
            hh = rem // 3600
            mm = (rem // 60) % 60
            ss = rem % 60;
            self.label_uptime.SetLabel("%d:%02d:%02d:%02d" % (days, hh, mm, ss))

            if not self.started:
                devs = self.sd.scan(True)
                for i,l in self.heat.items():
                    self.hot(i, i in devs)

    def choose_device(self, e):
        self.connect(self.devs[e.EventObject.GetValue()])

    def no_addr(self):
        self.addr = None
        [w.Enable(False) for w in self.dev_widgets]

    def choose_addr(self, e):
        o = e.EventObject
        v = o.GetValue()
        if v:
            self.addr = int(o.GetLabel(), 16)
            [w.Enable(True) for w in self.dev_widgets]

    def check_m(self, e):
        self.monitor = e.EventObject.GetValue()
        self.sd.monitor(self.monitor)
        [d.Enable(not self.monitor) for d in self.dynamic]
        if self.monitor:
            [self.hot(i, False) for i in self.heat]

    def set_speed(self, e):
        w = e.EventObject
        s = int(w.GetString(w.GetCurrentSelection()))
        self.sd.setspeed(s)

    def hot(self, i, s):
        l = self.heat[i]
        if s:
            l.SetForegroundColour((0,0,0))
            l.SetFont(self.addrfonts[1])
        else:
            l.SetForegroundColour((160,) * 3)
            l.SetFont(self.addrfonts[0])
            if i == self.addr:
                self.no_addr()
        l.Enable(s)

if __name__ == '__main__':
    app = wx.App(0)
    f = Frame(*sys.argv[1:])
    f.Show(True)
    app.MainLoop()
