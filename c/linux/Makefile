CFLAGS += -I common

all: build/i2ccl

install: all
	cp build/i2ccl /usr/local/bin

build/i2ccl: linux/i2c.c common/i2cdriver.c
	mkdir -p build/
	$(CC) -o $@ $(CPPFLAGS) $(CFLAGS) $^
