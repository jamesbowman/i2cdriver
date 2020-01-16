.. i2cdriver documentation master file, created by
   sphinx-quickstart on Thu Jan 16 10:21:28 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Excamera I2CDriver Python API
=============================


zxxx

.. toctree::
   :maxdepth: 2

xxcc

Official packages are available on PyPI.

https://pypi.org/project/i2cdriver/


The main page for I2CDriver includes the complete User Guide:

https://i2cdriver.com


System Requirements
-------------------

Because it is a pure Python module, ``i2cdriver`` can run on any system supported by ``pyserial``.
This includes:

- Windows 7 or 10
- Mac OS
- Linux, including all Ubuntu distributions

Both Python 2.7 and 3.x are supported.

Installation
------------

The ``i2cdriver`` package can be installed from PyPI using ``pip``::

    $ pip install i2cdriver

Quick start
-----------

To connect to the I2CDriver and scan the bus for connected devices::

    >>> import i2cdriver
    >>> i2c = i2cdriver.I2CDriver("/dev/ttyUSB0")
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

To read the temperature in Celsius from a connected LM75 sensor:

    >>> d=i2cdriver.EDS.Temp(i2c)
    >>> d.read()
    17.875
    >>> d.read()
    18.0

The User Guide at https://i2cdriver.com has more examples.

Module Contents
---------------

.. autoclass:: i2cdriver.I2CDriver
   :member-order: bysource
   :members:
      setspeed,
      setpullups,
      scan,
      reset,
      start,
      read,
      write,
      stop,
      regwr,
      regrd,
      getstatus,
      monitor

.. autoclass:: i2cdriver.START
.. autoclass:: i2cdriver.STOP
.. autoclass:: i2cdriver.BYTE
