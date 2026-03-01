# In The Beginning -- WebAssembly + WebGPU

A cosmic evolution simulator compiled to WebAssembly with real-time WebGPU
particle rendering. Simulates the universe from the Big Bang through the
emergence of life, with GPU-accelerated visualization in the browser.

## Prerequisites

- Rust toolchain (2021 edition)
- `wasm-pack` (`cargo install wasm-pack`)
- A WebGPU-capable browser (Chrome 113+, Edge 113+, or Firefox Nightly with
  `dom.webgpu.enabled`)

## Project Structure

```
wasm/
  src/
    lib.rs                 # WASM entry point and bindings
    constants.rs           # Physical constants and epoch definitions
    quantum.rs             # Quantum field simulation
    atomic.rs              # Atomic nucleosynthesis
    chemistry.rs           # Chemical bonding
    biology.rs             # Biological emergence
    environment.rs         # Environmental conditions
    universe.rs            # Top-level simulation orchestrator
    renderer.rs            # WebGPU rendering pipeline
    shaders/
      particle.wgsl        # WGSL particle shader
  index.html               # Browser entry point
  build.sh                 # Build helper script
  Cargo.toml
  Cargo.lock
  pkg/                     # wasm-pack output (generated)
```

## Build

Using the build script:

```sh
bash build.sh
```

Or manually with wasm-pack:

```sh
wasm-pack build --target web
```

This produces the `pkg/` directory containing the compiled `.wasm` file and
JavaScript bindings.

## Run

1. Build the project (see above).
2. Serve the directory with any static file server:

```sh
python3 -m http.server 8080
```

3. Open http://localhost:8080 in a WebGPU-capable browser.

A direct `file://` open will not work due to WASM/ES module CORS restrictions.

## Key Dependencies

- `wasm-bindgen` -- Rust/JS interop
- `wgpu` 28.0 -- WebGPU abstraction
- `web-sys` -- DOM and browser API bindings
- `bytemuck` -- safe transmutation for GPU buffer data
- `rand` 0.8 -- random number generation

## Notes

- The crate type is `cdylib` for WASM output.
- Release profile uses `opt-level = "s"` (size optimization) and LTO.
- The WGSL shader at `src/shaders/particle.wgsl` handles particle rendering.
- `console_error_panic_hook` is included for better panic messages in the
  browser console.
