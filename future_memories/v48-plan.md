# V48 Plan: WASM+ HiFi — True Album-Quality Music in the Browser

## Date: 2026-04-05

## Context
Port the Python radio_engine's album-quality music generation to the
browser using SpessaSynth (Apache-2.0, pure TS SoundFont synthesizer)
and FluidR3_GM.sf2 (MIT, 142MB GM SoundFont). The result should sound
identical to the V8 Sessions MP3 album (seed 42).

## Architecture
HiFiGenerator (JS port of radio_engine) → composes notes via MIDI
fragment sampling from 1,800+ classical pieces → SpessaSynth renders
through FluidR3_GM.sf2 → Web Audio API output.

## Key Components
1. spessasynth_lib (npm, Apache-2.0) — full SoundFont synthesizer
2. spessa-bridge.js (~200 lines) — adapter to our game interfaces
3. hifi-generator.js (~1500 lines) — radio_engine algorithm port
4. FluidR3_GM.sf2 (142MB, MIT) — GM SoundFont for instrument quality
5. UI: HiFi option in dropdown, seed input, SF2 loading progress
