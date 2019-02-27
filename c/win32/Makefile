CC = /usr/bin/i686-w64-mingw32-g++
CFLAGS += -I common -static-libgcc -static-libstdc++

all: build/i2ccl.exe

build/i2ccl.exe: win32/i2c.c common/i2cdriver.c
	mkdir -p build/
	$(CC) -o $@ $(CPPFLAGS) $(CFLAGS) $^
