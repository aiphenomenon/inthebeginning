# WASM Synth — Rust WebAssembly Audio Engine

Rust-compiled WebAssembly synthesizer for in-browser audio synthesis.
Used by the `inthebeginning bounce` game's WASM sound mode.

## Features

- 13 instrument timbres (piano, violin, cello, flute, oboe, trumpet, harp, bell, gamelan, choir, warm_pad, cosmic, sine)
- 64-voice polyphony with oldest-voice stealing
- ADSR envelopes
- GM program mapping (128 programs → 13 timbres)
- SoundFont 2 (.sf2) parser (optional sample-based fallback)
- AudioWorklet integration for real-time rendering

## Build

```bash
wasm-pack build --target web
```

Produces `wasm_synth_bg.wasm` (~40KB) for use in the game's `js/` directory.

## Integration

The JS bridge (`wasm-synth.js`) loads the WASM binary into an AudioWorklet
processor (`wasm-synth-processor.js`). Falls back to SynthEngine if WASM
is unavailable.
