#include <stdio.h>
#include <stdlib.h>

#include "i2cdriver.h"

int main(int argc, char *argv[])
{
  I2CDriver i2c;
  if (argc < 2) {
    printf("Usage: i2ccl <PORTNAME> <commands>\n");
    exit(1);
  } else {
    i2c_connect(&i2c, argv[1]);
    if (!i2c.connected)
      exit(1);
    return i2c_commands(&i2c, argc - 2, argv + 2);
  }
}
