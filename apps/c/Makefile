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

# Test sources (test_simulator.c replaces main.c)
TEST_SRC = test_simulator.c \
           $(SRCDIR)/quantum.c \
           $(SRCDIR)/atomic.c \
           $(SRCDIR)/chemistry.c \
           $(SRCDIR)/biology.c \
           $(SRCDIR)/environment.c \
           $(SRCDIR)/universe.c

TEST_OBJ = $(BUILDDIR)/test_simulator.o \
           $(BUILDDIR)/quantum.o \
           $(BUILDDIR)/atomic.o \
           $(BUILDDIR)/chemistry.o \
           $(BUILDDIR)/biology.o \
           $(BUILDDIR)/environment.o \
           $(BUILDDIR)/universe.o

TEST_BIN = $(BUILDDIR)/test_simulator

.PHONY: all clean static test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

static: $(OBJECTS)
	$(CC) $(CFLAGS) -static -o $(STATIC) $(OBJECTS) $(LDFLAGS)

$(BUILDDIR)/test_simulator.o: test_simulator.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(TEST_BIN): $(TEST_OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test: $(TEST_BIN)
	./$(TEST_BIN)

clean:
	rm -rf $(BUILDDIR)
