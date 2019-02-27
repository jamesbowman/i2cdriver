#include <stdio.h>
#include <stdlib.h>

#include "i2cdriver.h"

int main(int argc, char *argv[])
{
  I2CDriver sd;
  if (argc < 2) {
    printf("Usage: i2ccl <PORTNAME> <commands>\n");
    exit(1);
  } else {
    i2c_connect(&sd, argv[1]);
    if (!sd.connected)
      exit(1);
    return i2c_commands(&sd, argc - 2, argv + 2);
  }
}
