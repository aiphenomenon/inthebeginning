# In The Beginning -- C CLI

A cosmic evolution simulator written in C11. Simulates the universe from the
Big Bang through the emergence of life.

## Prerequisites

- GCC (or any C11-compatible compiler)
- GNU Make
- Standard C library with math support (`-lm`)

## Project Structure

```
c/
  simulator/
    main.c                 # Entry point
    constants.h            # Physical constants and epoch definitions
    quantum.c / quantum.h  # Quantum field simulation
    atomic.c / atomic.h    # Atomic nucleosynthesis
    chemistry.c / chemistry.h  # Chemical bonding
    biology.c / biology.h  # Biological emergence
    environment.c / environment.h  # Environmental conditions
    universe.c / universe.h  # Top-level simulation orchestrator
  build/                   # Build output directory
    simulator              # Compiled binary
  Makefile
```

## Build

Standard build:

```sh
make
```

Static linking (produces `build/simulator-static`):

```sh
make static
```

Clean build artifacts:

```sh
make clean
```

## Run

```sh
./build/simulator
```

## Compiler Flags

The default build uses:

- `-std=c11` -- C11 standard
- `-Wall -Wextra` -- comprehensive warnings
- `-O2` -- optimization level 2
- `-lm` -- links math library

## Notes

- No external dependencies beyond the C standard library and libm.
- The `build/` directory is created automatically by `make`.
- To use a different compiler, override `CC`: `make CC=clang`.
