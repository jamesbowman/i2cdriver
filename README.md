![logo](/images/logo.png)

[![Build Status](https://travis-ci.org/jamesbowman/i2cdriver.svg?branch=master)](https://travis-ci.org/jamesbowman/i2cdriver)

I2CDriver is a tool for controlling any I2C device from your PC's USB port,
and can also monitor and capture I2C traffic.
It connects as a standard USB serial device, so there are no drivers to install.
The serial protocol is [very simple](/protocol.md),
and there are included drivers for

* Windows/Mac/Linux GUI
* Windows/Mac/Linux command-line
* Python 2 and 3
* Windows/Mac/Linux C/C++

![front](/images/hero.jpg)

Full documentation is at
[i2cdriver.com](http://i2cdriver.com).

How to release
--------------

To release Python:

  rm -rf dist/*
  python setup.py dist
  twine upload/dist/*

To build the Windows installer:

On Linux cross-compile ``i2ccl``:
  
    cd c
    make -f win32/Makefile

On Windows build the GUI exeutable:

    cd python\samples
    pyinstaller --onefile --windowed --icon=../../images/i2cdriver.ico i2cgui.py

Then build the installer with NSIS:

    cd nsis
    go.bat
