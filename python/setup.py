# coding=utf-8
from setuptools import setup

LONG = """\
I2CDriver is a tool for controlling, monitoring and capturing I2C from your PC's USB port. It connects as a standard USB serial device, so there are no drivers to install."""

for l in open("i2cdriver.py", "rt"):
    if l.startswith("__version__"):
        exec(l)

setup(name='i2cdriver',
      version=__version__,
      author='James Bowman',
      author_email='jamesb@excamera.com',
      url='http://i2cdriver.com',
      description='I2CDriver is a desktop I2C interface',
      long_description=LONG,
      license='GPL',
      install_requires=['pyserial'],
      py_modules = [
        'i2cdriver',
        'EDS',
      ],
      scripts=['samples/i2cgui.py'],
      project_urls={
        'Documentation': 'https://i2cdriver.readthedocs.io/en/latest/',
      }
      )
