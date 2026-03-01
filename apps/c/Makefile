# Makefile for the Cosmic Evolution Simulator (C implementation)

CC       = gcc
CFLAGS   = -std=c11 -Wall -Wextra -O2
LDFLAGS  = -lm

SRCDIR   = simulator
BUILDDIR = build

SOURCES  = $(SRCDIR)/main.c \
           $(SRCDIR)/quantum.c \
           $(SRCDIR)/atomic.c \
           $(SRCDIR)/chemistry.c \
           $(SRCDIR)/biology.c \
           $(SRCDIR)/environment.c \
           $(SRCDIR)/universe.c

OBJECTS  = $(patsubst $(SRCDIR)/%.c,$(BUILDDIR)/%.o,$(SOURCES))

TARGET   = $(BUILDDIR)/simulator
STATIC   = $(BUILDDIR)/simulator-static

.PHONY: all clean static

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

static: $(OBJECTS)
	$(CC) $(CFLAGS) -static -o $(STATIC) $(OBJECTS) $(LDFLAGS)

clean:
	rm -rf $(BUILDDIR)
