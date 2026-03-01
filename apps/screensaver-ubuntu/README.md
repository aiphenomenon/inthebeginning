# In The Beginning -- Ubuntu/Linux Screensaver

A screensaver for Linux/X11 that displays the cosmic evolution simulation
using OpenGL rendering. Designed for use as an XScreenSaver module.

## Prerequisites

- GCC (or any C11-compatible compiler)
- GNU Make
- Development libraries:
  - `libx11-dev` -- X11 client library
  - `libgl1-mesa-dev` -- OpenGL development files
  - `libglu1-mesa-dev` -- GLU (OpenGL Utility) development files

Install on Ubuntu/Debian:

```sh
sudo apt install gcc make libx11-dev libgl1-mesa-dev libglu1-mesa-dev
```

## Project Structure

```
screensaver-ubuntu/
  inthebeginning-screensaver.c     # Screensaver main (X11 + OpenGL)
  simulator/
    constants.h                    # Physical constants and epoch definitions
    universe.c                     # Simulation engine
    universe.h                     # Universe header
  inthebeginning.desktop           # XScreenSaver desktop entry
  Makefile
```

## Build

```sh
make
```

Produces the `inthebeginning-screensaver` binary in the project directory.

## Install

Install as an XScreenSaver module:

```sh
sudo make install
```

This copies:
- The binary to `/usr/local/libexec/xscreensaver/`
- The desktop entry to `/usr/local/share/applications/screensavers/`

To install to a custom prefix:

```sh
sudo make install PREFIX=/usr
```

## Uninstall

```sh
sudo make uninstall
```

## Run Standalone

Test the screensaver in a window without installing:

```sh
./inthebeginning-screensaver
```

## Clean

```sh
make clean
```

## Compiler Flags

- `-std=c11 -Wall -Wextra -O2 -pedantic`
- Links: `-lX11 -lGL -lGLX -lm`

## Notes

- The screensaver renders directly to an X11 window using OpenGL via GLX.
- The `.desktop` file registers the screensaver with XScreenSaver and
  compatible screensaver managers.
- The `PREFIX` variable defaults to `/usr/local` and can be overridden at
  install time.
