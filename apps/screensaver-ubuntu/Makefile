CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -O2 -pedantic
LDFLAGS = -lX11 -lGL -lGLX -lm

TARGET  = inthebeginning-screensaver
SRCS    = inthebeginning-screensaver.c simulator/universe.c
OBJS    = $(SRCS:.c=.o)

PREFIX  ?= /usr/local

TEST_TARGET = test_simulator
TEST_SRCS   = test_simulator.c simulator/universe.c
TEST_OBJS   = $(TEST_SRCS:.c=.o)

.PHONY: all clean install uninstall test

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

test: $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(TEST_SRCS)
	$(CC) $(CFLAGS) -o $@ $(TEST_SRCS) -lm

clean:
	rm -f $(TARGET) $(OBJS) $(TEST_TARGET) $(TEST_OBJS)
