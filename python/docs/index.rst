i2cdriver
=========

.. image:: /images/i2cdriver-hero-800.jpg
   :target: https://i2cdriver.com

`I²CDriver <https://i2cdriver.com>`_
is an easy-to-use, open source tool for controlling I²C devices over USB.
It works with Windows, Mac, and Linux, and has a built-in color screen
that shows a live "dashboard" of all the I²C activity.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

The I²CDriver User Guide has complete information on the hardware:

https://i2cdriver.com/i2cdriver.pdf

System Requirements
===================

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
