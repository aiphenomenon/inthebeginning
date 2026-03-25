# V30 Plan — WebAssembly Audio Synthesis Mode

**Created**: 2026-03-25 10:04 CT (15:04 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Scope**: Add WebAssembly as a 4th sound mode in the web game/player

## User Direction

> Move soundfont-related WebAssembly to the end. Do intermediate commits.
> The WebAssembly mode should be its own mode, even though all the other things
> should be capable of being used without WebAssembly (but when the WebAssembly
> option is used, the other "knobs" should affect it). The WebAssembly piece
> probably needs to be done one file at a time, with intermediate steps to verify
> consistency and functioning interfaces and actual functioning software.

## Architecture Overview

### Current Sound Modes (3)
1. **MP3 (Album)** — HTML5 Audio element plays 12-track album, note event JSONs drive visualization
2. **MIDI Library** — MidiPlayer parses .mid files, SynthEngine renders via Web Audio API oscillators/samples
3. **Synth Generator** — MusicGenerator produces procedural compositions, SynthEngine renders

### New Mode: WASM Synth (4th mode)
4. **WASM Synth** — WebAssembly module handles audio synthesis with higher performance.
   When active, the existing knobs (mutation presets, style sliders, volume) still work
   by sending parameters to the WASM module. The WASM mode is a **drop-in replacement
   for the SynthEngine's audio rendering**, not a separate music generation system.

### Key Files (touch order)
1. `music-sync.js` — Add `AUDIO_MODE.WASM` constant
2. `wasm-synth.js` — NEW: WASM loader, JS bridge, AudioWorklet integration
3. `player.js` — Add WASM case to play/pause/prev/next/setMode
4. `app.js` — Add WASM case to _initSoundMode, _updateID3Display
5. `index.html` — Add WASM option to sound mode dropdown
6. Rust WASM crate — `apps/wasm-synth/` — actual synthesis in Rust compiled to WASM
7. SoundFont WASM integration — LAST (FluidSynth-lite or custom SF2 parser in Rust)

### Design Principles
- **Graceful degradation**: If WASM fails to load, fall back to existing SynthEngine
- **Same interface**: WasmSynth implements the same noteOn/noteOff/setVolume API as SynthEngine
- **Knob compatibility**: Mutation presets, style sliders, volume all affect WASM mode
- **No new dependencies**: WASM is compiled from Rust (already used for apps/wasm/)
- **Incremental verification**: Each file committed and tested independently

## Phase 1: JS Infrastructure (no WASM binary needed yet)

### Step 1.1: Add AUDIO_MODE.WASM to music-sync.js
- Add `WASM: 'wasm'` to AUDIO_MODE constant
- No other changes needed in music-sync.js

### Step 1.2: Create wasm-synth.js — JS bridge
- WasmSynth class with same API as SynthEngine:
  - `init()`, `resume()`, `noteOn(note, vel, ch)`, `noteOff(note, ch)`
  - `setVolume(v)`, `setMutation(preset)`, `destroy()`
- WASM loader: fetch .wasm file, instantiate, wire to AudioWorklet
- Fallback: if WASM unavailable, delegate to SynthEngine
- Initially: stub implementation that just delegates to SynthEngine
  (this lets us verify the plumbing works before writing Rust)

### Step 1.3: Wire into player.js
- Add WASM cases to play(), pause(), prevTrack(), nextTrack(), setMode()
- WasmSynth gets its own MidiPlayer-like flow (load MIDI → send to WASM)

### Step 1.4: Wire into app.js
- Add 'wasm' case to _initSoundMode()
- Add 'wasm' case to _updateID3Display()
- WASM mode uses MIDI catalog (same as MIDI mode) but renders via WASM

### Step 1.5: Update index.html
- Add `<option value="wasm">WASM Synth</option>` to sound mode dropdown
- Commit and test: app loads, WASM mode selectable, falls back to SynthEngine

## Phase 2: Rust WASM Synth Crate

### Step 2.1: Create apps/wasm-synth/ crate
- Cargo.toml with wasm-bindgen, js-sys, web-sys (AudioWorklet)
- Basic additive synthesis in Rust (port from synth-engine.js TIMBRES)
- WASM entry points: init, note_on, note_off, render_audio_block

### Step 2.2: AudioWorklet processor
- wasm-synth-processor.js: AudioWorkletProcessor that calls WASM render
- Runs in audio thread for low-latency synthesis

### Step 2.3: Build and integrate
- wasm-pack build → produces .wasm + .js glue
- Copy to deploy directory
- Verify: WASM mode plays MIDI files through Rust synthesizer

## Phase 3: SoundFont Integration (LAST)

### Step 3.1: SF2 parser in Rust
- Parse SoundFont 2.0 format (.sf2) in Rust
- Extract sample data, instrument presets, generators
- No external crate — implement from spec

### Step 3.2: Sample-based synthesis in WASM
- Use SF2 samples for high-fidelity instrument rendering
- Pitch shifting, filtering, envelope from SF2 generators
- Memory-conscious: stream samples, don't load entire SF2

### Step 3.3: Integration
- Download FluidR3_GM.sf2 subset (most-used instruments only, ~20MB)
- Or: use the existing 60 MP3 instrument samples as a lightweight alternative
- Wire SF2 rendering into the WasmSynth AudioWorklet pipeline

## Completion Criteria
- [ ] WASM is a 4th sound mode in the dropdown
- [ ] Without WASM binary, gracefully falls back to SynthEngine
- [ ] With WASM binary, all existing knobs (mutation, style, volume) work
- [ ] MIDI files play through WASM synthesis
- [ ] Procedural music can optionally render through WASM
- [ ] deploy/v8 created with WASM mode
- [ ] SoundFont integration (Phase 3) done last
