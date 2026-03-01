# In The Beginning -- C++ CLI

A cosmic evolution simulator written in C++20. Simulates the universe from the
Big Bang through the emergence of life, with an optional SDL2+OpenGL GUI.

## Prerequisites

- CMake 3.16 or later
- g++ or clang++ with C++20 support
- On Linux: pthreads (usually available by default)
- Optional (GUI build): SDL2 and OpenGL development libraries

## Project Structure

```
cpp/
  simulator/
    main.cpp               # CLI entry point
    constants.hpp          # Physical constants and epoch definitions
    quantum.cpp / quantum.hpp      # Quantum field simulation
    atomic.cpp / atomic.hpp        # Atomic nucleosynthesis
    chemistry.cpp / chemistry.hpp  # Chemical bonding
    biology.cpp / biology.hpp      # Biological emergence
    environment.cpp / environment.hpp  # Environmental conditions
    universe.cpp / universe.hpp    # Top-level simulation orchestrator
  CMakeLists.txt
  build/                   # Build output directory
    inthebeginning         # Compiled CLI binary
```

## Build

```sh
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

The CLI binary is produced at `build/inthebeginning`.

## GUI Build (Optional)

Requires SDL2 and OpenGL:

```sh
# Install dependencies (Ubuntu/Debian)
sudo apt install libsdl2-dev

mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_GUI=ON
make -j$(nproc)
```

Produces `build/inthebeginning-gui` in addition to the CLI binary.

## Run

```sh
./build/inthebeginning
```

## Clean

```sh
rm -rf build
```

## Compiler Flags

Default flags applied by CMake:

- `-Wall -Wextra -Wpedantic` -- comprehensive warnings
- `-O2` -- optimization level 2

## Notes

- The CLI target has no external dependencies.
- C++20 is required (`CMAKE_CXX_STANDARD 20`).
- Compile commands are exported to `build/compile_commands.json` for IDE integration.
- On Linux, the CLI links against `m` and `pthread`.
