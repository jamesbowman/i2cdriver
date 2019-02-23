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
  unsigned int
            ccitt_crc,    // Hardware CCITT CRC
            e_ccitt_crc;  // Host CCITT CRC, should match
} I2CDriver;

void i2c_connect(I2CDriver *sd, const char* portname);
void i2c_getstatus(I2CDriver *sd);
void i2c_write(I2CDriver *sd, const char bytes[], size_t nn);
void i2c_read(I2CDriver *sd, char bytes[], size_t nn);

int i2c_commands(I2CDriver *sd, int argc, char *argv[]);

#endif
