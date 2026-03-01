CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -O2 -pedantic
LDFLAGS = -lX11 -lGL -lGLX -lm

TARGET  = inthebeginning-screensaver
SRCS    = inthebeginning-screensaver.c simulator/universe.c
OBJS    = $(SRCS:.c=.o)

PREFIX  ?= /usr/local

.PHONY: all clean install uninstall

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

install: $(TARGET)
	install -Dm755 $(TARGET) $(DESTDIR)$(PREFIX)/libexec/xscreensaver/$(TARGET)
	install -Dm644 inthebeginning.desktop $(DESTDIR)$(PREFIX)/share/applications/screensavers/inthebeginning.desktop

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/libexec/xscreensaver/$(TARGET)
	rm -f $(DESTDIR)$(PREFIX)/share/applications/screensavers/inthebeginning.desktop

clean:
	rm -f $(TARGET) $(OBJS)
