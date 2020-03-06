#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <memory.h>
#include <fcntl.h>
#if !defined(WIN32)
#include <sys/ioctl.h>
#include <unistd.h>
#endif
#include <errno.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#include <string.h>

#include "i2cdriver.h"

// ****************************   Serial port  ********************************

#if defined(WIN32)  // {

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

void ErrorExit(const char *func_name) 
{ 
    // Retrieve the system error message for the last-error code

    LPVOID lpMsgBuf;
    DWORD dw = GetLastError(); 

    FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | 
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR) &lpMsgBuf,
        0, NULL );

    // Display the error message and exit the process

    char mm[256];
    snprintf(mm, sizeof(mm), "%s failed with error %lu:\n%s", func_name, dw, (char*)lpMsgBuf); 
    MessageBox(NULL, (LPCTSTR)mm, TEXT("Error"), MB_OK); 

    LocalFree(lpMsgBuf);
    ExitProcess(dw); 
}

HANDLE openSerialPort(const char *portname)
{
    char fullname[10];
    const char *fmt;
    if (portname[0] == 'C')
        fmt = "\\\\.\\%s";
    else
        fmt = "%s";
    snprintf(fullname, sizeof(fullname), fmt, portname);
    DWORD  accessdirection = GENERIC_READ | GENERIC_WRITE;
    HANDLE hSerial = CreateFile((LPCSTR)fullname,
        accessdirection,
        0,
        0,
        OPEN_EXISTING,
        0,
        0);
    if (hSerial == INVALID_HANDLE_VALUE) {
        ErrorExit("CreateFile");
    }
    DCB dcbSerialParams = {0};
    dcbSerialParams.DCBlength=sizeof(dcbSerialParams);
    if (!GetCommState(hSerial, &dcbSerialParams)) {
         ErrorExit("GetCommState");
    }
    dcbSerialParams.BaudRate = 1000000;
    dcbSerialParams.ByteSize = 8;
    dcbSerialParams.StopBits = ONESTOPBIT;
    dcbSerialParams.Parity = NOPARITY;
    if (!SetCommState(hSerial, &dcbSerialParams)) {
         ErrorExit("SetCommState");
    }
    COMMTIMEOUTS timeouts = {0};
    timeouts.ReadIntervalTimeout = 50;
    timeouts.ReadTotalTimeoutConstant = 50;
    timeouts.ReadTotalTimeoutMultiplier = 10;
    timeouts.WriteTotalTimeoutConstant = 50;
    timeouts.WriteTotalTimeoutMultiplier = 10;
    if (!SetCommTimeouts(hSerial, &timeouts)) {
        ErrorExit("SetCommTimeouts");
    }
    return hSerial;
}

DWORD readFromSerialPort(HANDLE hSerial, uint8_t * buffer, int buffersize)
{
    DWORD dwBytesRead = 0;
    if (!ReadFile(hSerial, buffer, buffersize, &dwBytesRead, NULL)) {
        ErrorExit("ReadFile");
    }
    return dwBytesRead;
}

DWORD writeToSerialPort(HANDLE hSerial, const uint8_t * data, int length)
{
    DWORD dwBytesRead = 0;
    if (!WriteFile(hSerial, data, length, &dwBytesRead, NULL)) {
        ErrorExit("WriteFile");
    }
    return dwBytesRead;
}

void closeSerialPort(HANDLE hSerial)
{
    CloseHandle(hSerial);
}

#else               // }{

#include <termios.h>

int openSerialPort(const char *portname)
{
  struct termios Settings;
  int fd;
  
  fd = open(portname, O_RDWR | O_NOCTTY);
  if (fd == -1) {
    perror(portname);
    return -1;
  }
  tcgetattr(fd, &Settings);

#if defined(__APPLE__) && !defined(B1000000)
  #include <IOKit/serial/ioss.h>
#else
  cfsetispeed(&Settings, B1000000);
  cfsetospeed(&Settings, B1000000);
#endif


  cfmakeraw(&Settings);
  Settings.c_cc[VMIN] = 1;
  if (tcsetattr(fd, TCSANOW, &Settings) != 0) {
    perror("Serial settings");
    return -1;
  }

#if defined(__APPLE__) && !defined(B1000000)
  speed_t speed = (speed_t)1000000;
  ioctl(fd, IOSSIOSPEED, &speed);
#endif

  return fd;
}

int readFromSerialPort(int fd, uint8_t *b, size_t s)
{
  ssize_t n, t;
  t = 0;
  while (t < s) {
    n = read(fd, b + t, s);
    if (n > 0)
      t += n;
  }
#ifdef VERBOSE
  printf(" READ %d %d: ", (int)s, (int)n);
  int i;
  for (i = 0; i < s; i++)
    printf("%02x ", 0xff & b[i]);
  printf("\n");
#endif
  return s;
}

void writeToSerialPort(int fd, const uint8_t *b, size_t s)
{
  write(fd, b, s);
#ifdef VERBOSE
  printf("WRITE %u: ", (int)s);
  int i;
  for (i = 0; i < s; i++)
    printf("%02x ", 0xff & b[i]);
  printf("\n");
#endif
}
#endif              // }

// ******************************  CCITT CRC  *********************************

static const uint16_t crc_table[256] = {
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
    0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
    0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
    0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
    0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
    0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
    0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
    0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
    0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
    0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
    0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
    0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
    0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
    0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
    0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
    0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
    0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
    0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
    0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
    0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
    0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
    0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
    0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
};

static void crc_update(I2CDriver *sd, const uint8_t *data, size_t data_len)
{
    unsigned int tbl_idx;
    uint16_t crc = sd->e_ccitt_crc;

    while (data_len--) {
        tbl_idx = ((crc >> 8) ^ *data) & 0xff;
        crc = (crc_table[tbl_idx] ^ (crc << 8)) & 0xffff;
        data++;
    }
    sd->e_ccitt_crc = crc;
}

// ******************************  I2CDriver  *********************************

void i2c_connect(I2CDriver *sd, const char* portname)
{
  int i;

  sd->connected = 0;
  sd->port = openSerialPort(portname);
#if !defined(WIN32)
  if (sd->port == -1)
    return;
#endif
  writeToSerialPort(sd->port,
    (uint8_t*)"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", 64);

  const uint8_t tests[] = "A\r\n\0xff";
  for (i = 0; i < 4; i++) {
    uint8_t tx[2] = {'e', tests[i]};
    writeToSerialPort(sd->port, tx, 2);
    uint8_t rx[1];
    int n = readFromSerialPort(sd->port, rx, 1);
    if ((n != 1) || (rx[0] != tests[i]))
      return;
  }

  sd->connected = 1;
  i2c_getstatus(sd);
  sd->e_ccitt_crc = sd->ccitt_crc;
}

static void charCommand(I2CDriver *sd, char c)
{
  writeToSerialPort(sd->port, (uint8_t*)&c, 1);
}

static int i2c_ack(I2CDriver *sd)
{
  uint8_t a[1];
  if (readFromSerialPort(sd->port, a, 1) != 1)
    return 0;
  return (a[0] & 1) != 0;
}

void i2c_getstatus(I2CDriver *sd)
{
  uint8_t readbuffer[100];
  int bytesRead;
  uint8_t mode[80];

  charCommand(sd, '?');
  bytesRead = readFromSerialPort(sd->port, readbuffer, 80);
  readbuffer[bytesRead] = 0;
  // printf("%d Bytes were read: %.*s\n", bytesRead, bytesRead, readbuffer);
  sscanf((char*)readbuffer, "[%15s %8s %" SCNu64 " %f %f %f %c %d %d %d %d %x ]",
    sd->model,
    sd->serial,
    &sd->uptime,
    &sd->voltage_v,
    &sd->current_ma,
    &sd->temp_celsius,
    mode,
    &sd->sda,
    &sd->scl,
    &sd->speed,
    &sd->pullups,
    &sd->ccitt_crc
    );
    sd->mode = mode[0];
}

void i2c_scan(I2CDriver *sd, uint8_t devices[128])
{
  charCommand(sd, 'd');
  (void)readFromSerialPort(sd->port, devices + 8, 112);
}

uint8_t i2c_reset(I2CDriver *sd)
{
  charCommand(sd, 'x');
  uint8_t a[1];
  if (readFromSerialPort(sd->port, a, 1) != 1)
    return 0;
  return a[0];
}

int i2c_start(I2CDriver *sd, uint8_t dev, uint8_t op)
{
  uint8_t start[2] = {'s', (uint8_t)((dev << 1) | op)};
  writeToSerialPort(sd->port, start, sizeof(start));
  return i2c_ack(sd);
}

void i2c_stop(I2CDriver *sd)
{
  charCommand(sd, 'p');
}

int i2c_write(I2CDriver *sd, const uint8_t bytes[], size_t nn)
{
  size_t i;
  int ack = 1;

  for (i = 0; i < nn; i += 64) {
    size_t len = ((nn - i) < 64) ? (nn - i) : 64;
    uint8_t cmd[65] = {(uint8_t)(0xc0 + len - 1)};
    memcpy(cmd + 1, bytes + i, len);
    writeToSerialPort(sd->port, cmd, 1 + len);
    ack = i2c_ack(sd);
  }
  crc_update(sd, bytes, nn);
  return ack;
}

void i2c_read(I2CDriver *sd, uint8_t bytes[], size_t nn)
{
  size_t i;

  for (i = 0; i < nn; i += 64) {
    size_t len = ((nn - i) < 64) ? (nn - i) : 64;
    uint8_t cmd[1] = {(uint8_t)(0x80 + len - 1)};
    writeToSerialPort(sd->port, cmd, 1);
    readFromSerialPort(sd->port, bytes + i, len);
    crc_update(sd, bytes + i, len);
  }
}

void i2c_monitor(I2CDriver *sd, int enable)
{
  charCommand(sd, enable ? 'm' : '@');
}

void i2c_capture(I2CDriver *sd)
{
  printf("Capture started\n");
  charCommand(sd, 'c');
  uint8_t bytes[1];

  int starting = 0;
  int nbits = 0, bits = 0;
  while (1) {
    int i;
    readFromSerialPort(sd->port, bytes, 1);
    for (i = 0; i < 2; i++) {
      int symbol = (i == 0) ? (bytes[0] >> 4) : (bytes[0] & 0xf);
      switch (symbol) {
        case 0:
          break;
        case 1:
          starting = 1;
          break;
        case 2:
          printf("STOP\n");
          starting = 1;
          break;
        case 8:
        case 9:
        case 10:
        case 11:
        case 12:
        case 13:
        case 14:
        case 15:
          bits = (bits << 3) | (symbol & 7);
          nbits += 3;
          if (nbits == 9) {
            int b8 = (bits >> 1), ack = !(bits & 1);
            if (starting) {
              starting = 0;
              printf("START %02x %s", b8 >> 1, (b8 & 1) ? "READ" : "WRITE");
            } else {
              printf("BYTE %02x", b8);
            }
            printf(" %s\n", ack ? "ACK" : "NAK");
            nbits = 0;
            bits = 0;
          }
      }
    }
  }
}

int i2c_commands(I2CDriver *sd, int argc, char *argv[])
{
  int i;

  for (i = 0; i < argc; i++) {
    char *token = argv[i];
    // printf("token [%s]\n", token);
    if (strlen(token) != 1)
      goto badcommand;
    switch (token[0]) {

    case 'i':
      i2c_getstatus(sd);
      printf("uptime %" SCNu64"  %.3f V  %.0f mA  %.1f C SDA=%d SCL=%d speed=%d kHz\n",
        sd->uptime,
        sd->voltage_v,
        sd->current_ma,
        sd->temp_celsius,
        sd->sda,
        sd->scl,
        sd->speed
        );
      break;

    case 'x':
      {
        uint8_t sda_scl = i2c_reset(sd);
        printf("Bus reset. SDA = %d, SCL = %d\n",
               1 & (sda_scl >> 1),
               1 & sda_scl);
      }
      break;

    case 'd':
      {
        uint8_t devices[128];
        int i;

        i2c_scan(sd, devices);
        printf("\n");
        for (i = 8; i < 0x78; i++) {
          if (devices[i] == '1')
            printf("%02x  ", i);
          else
            printf("--  ");
          if ((i % 8) == 7)
            printf("\n");
        }
        printf("\n");
      }
      break;
    
    case 'w':
      {
        token = argv[++i];
        unsigned int dev = strtol(token, NULL, 0);

        token = argv[++i];
        uint8_t bytes[8192];
        char *endptr = token;
        size_t nn = 0;
        while (nn < sizeof(bytes)) {
          bytes[nn++] = strtol(endptr, &endptr, 0);
          if (*endptr == '\0')
            break;
          if (*endptr != ',') {
            fprintf(stderr, "Invalid bytes '%s'\n", token);
            return 1;
          }
          endptr++;
        }

        i2c_start(sd, dev, 0);
        i2c_write(sd, bytes, nn);
      }
      break;

    case 'r':
      {
        token = argv[++i];
        unsigned int dev = strtol(token, NULL, 0);

        token = argv[++i];
        size_t nn = strtol(token, NULL, 0);
        uint8_t bytes[8192];

        i2c_start(sd, dev, 1);
        i2c_read(sd, bytes, nn);
        i2c_stop(sd);

        size_t i;
        for (i = 0; i < nn; i++)
          printf("%s0x%02x", i ? "," : "", 0xff & bytes[i]);
        printf("\n");
      }
      break;

    case 'p':
      i2c_stop(sd);
      break;

    case 'm':
      {
        char line[100];

        i2c_monitor(sd, 1);
        printf("[Hit return to exit monitor mode]\n");
        fgets(line, sizeof(line) - 1, stdin);
        i2c_monitor(sd, 0);
      }
      break;

    case 'c':
      {
        i2c_capture(sd);
      }
      break;

    default:
    badcommand:
      fprintf(stderr, "Bad command '%s'\n", token);
      fprintf(stderr, "\n");
      fprintf(stderr, "Commands are:");
      fprintf(stderr, "\n");
      fprintf(stderr, "  i              display status information (uptime, voltage, current, temperature)\n");
      fprintf(stderr, "  x              I2C bus reset\n");
      fprintf(stderr, "  d              device scan\n");
      fprintf(stderr, "  w dev <bytes>  write bytes to I2C device dev\n");
      fprintf(stderr, "  p              send a STOP\n");
      fprintf(stderr, "  r dev N        read N bytes from I2C device dev, then STOP\n");
      fprintf(stderr, "  m              enter I2C bus monitor mode\n");
      fprintf(stderr, "  c              enter I2C bus capture mode\n");
      fprintf(stderr, "\n");

      return 1;
    }
  }

  return 0;
}
