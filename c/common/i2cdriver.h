#ifndef I2CDRIVER_H
#define I2CDRIVER_H

#include <stdint.h>

#if defined(WIN32)
#include <windows.h>
#else
#define HANDLE int
#endif

typedef struct {
  int connected;          // Set to 1 when connected
  HANDLE port;
  char      model[16],
            serial[9];    // Serial number of USB device
  uint64_t  uptime;       // time since boot (seconds)
  float     voltage_v,    // USB voltage (Volts)
            current_ma,   // device current (mA)
            temp_celsius; // temperature (C)
  unsigned int mode;      // I2C 'I' or bitbang 'B' mode
  unsigned int sda;       // SDA state, 0 or 1
  unsigned int scl;       // SCL state, 0 or 1
  unsigned int speed;     // I2C line speed (in kHz)
  unsigned int pullups;   // pullup state (6 bits, 1=enabled)
  unsigned int
            ccitt_crc,    // Hardware CCITT CRC
            e_ccitt_crc;  // Host CCITT CRC, should match
} I2CDriver;

void i2c_connect(I2CDriver *sd, const char* portname);
void i2c_getstatus(I2CDriver *sd);
int  i2c_write(I2CDriver *sd, const uint8_t bytes[], size_t nn);
void i2c_read(I2CDriver *sd, uint8_t bytes[], size_t nn);
int  i2c_start(I2CDriver *sd, uint8_t dev, uint8_t op);
void i2c_stop(I2CDriver *sd);

void i2c_monitor(I2CDriver *sd, int enable);
void i2c_capture(I2CDriver *sd);

int i2c_commands(I2CDriver *sd, int argc, char *argv[]);

#endif
