# In The Beginning -- Rust CLI

A cosmic evolution simulator written in Rust. Simulates the universe from the
Big Bang through the emergence of life, with modular physics subsystems.

## Prerequisites

- Rust toolchain (rustc, cargo) -- 2021 edition
- No external runtime dependencies for the CLI build
- Optional: SDL2 + OpenGL for the GUI feature (`--features gui`)

## Project Structure

```
rust/
  src/
    main.rs                # Entry point
    simulator/
      mod.rs               # Module declarations
      constants.rs         # Physical constants and epoch definitions
      quantum.rs           # Quantum field simulation
      atomic.rs            # Atomic nucleosynthesis
      chemistry.rs         # Chemical bonding and molecule formation
      biology.rs           # Biological emergence
      environment.rs       # Environmental conditions
      universe.rs          # Top-level simulation orchestrator
  Cargo.toml
  Cargo.lock
  target/                  # Build output (created by cargo)
```

## Build

Debug build:

```sh
cargo build
```

Release build (optimized, LTO enabled, symbols stripped):

```sh
cargo build --release
```

The release binary is at `target/release/inthebeginning-rust`.

## Static Linking (musl)

```sh
rustup target add x86_64-unknown-linux-musl
cargo build --release --target x86_64-unknown-linux-musl
```

Binary at `target/x86_64-unknown-linux-musl/release/inthebeginning-rust`.

## Run

```sh
cargo run --release
```

Or run the binary directly:

```sh
./target/release/inthebeginning-rust
```

## GUI Build (Optional)

Requires SDL2 and OpenGL development libraries:

```sh
cargo build --release --features gui
```

## Testing

```sh
cargo test
```

## Dependencies

- `rand` 0.8 -- random number generation
- `sdl2` 0.37 (optional, `gui` feature) -- windowing and input
- `gl` 0.14 (optional, `gui` feature) -- OpenGL bindings

## Notes

- Release profile uses `opt-level = 3`, LTO, single codegen unit, and symbol stripping.
- The `gui` feature is disabled by default; the CLI build has no system dependencies beyond libc.
