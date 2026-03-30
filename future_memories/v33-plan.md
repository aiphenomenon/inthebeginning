# V33 Plan — Approach C WASM Compositional Engine + MP3 Album Reconstruction

## Date: 2026-03-30

## Overview

Two major workstreams:

1. **Approach C WASM**: Transform WASM mode from raw MIDI playback into a hybrid
   compositional engine. WASM handles sample-level synthesis (Rust), JS handles
   compositional intelligence (rondo patterns, consonance engine, MIDI bar sampling,
   epoch-based orchestration). This brings browser audio toward parity with the
   Python RadioEngineV8.

2. **MP3 Album Reconstruction**: The 12-track V8 Sessions album comes from two
   30-minute renders (RadioEngineV8 seed=42 and RadioEngineV15_V8Tempo seed=42),
   split into ~5-minute tracks at natural energy boundaries. These MP3s need to
   be present in deploy/v9 or accessible via shared/ for MP3 mode to work.

---

## Workstream 1: Approach C WASM Compositional Engine

### What exists
- music-generator.js: 44 scales, 15 progressions, 25 rhythms, 30 motifs, 9 layers
- wasm-synth.js: WASM binary loading, AudioWorklet, fallback to SynthEngine
- synth-engine.js: 16 timbres, ADSR, vibrato, reverb, sample playback

### What's missing (vs Python RadioEngineV8)
- Rondo patterns (ABACA, AABA, etc.) with section-level variation
- Consonance engine (interval scoring, iterative voice adjustment)
- MIDI bar sampling (sample_bars_seeded — real phrasing from classical works)
- Diatonic chord quality (scale-degree-specific voicing)
- Voice orchestration (ensemble selection per epoch)
- Arpeggio forms (alberti, broken, pendulum)

### Phase 1: Compositional Logic Port to music-generator.js

1a. **Rondo Pattern System**
   - Port 7 patterns: ABACA, ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA
   - Each section gets different arpeggio form and transposition
   - Sections B/C/D transpose: +5, -3, +7 semitones

1b. **Consonance Engine** (new class in music-generator.js)
   - Port interval consonance table (12 pitch classes → 0-1 scores)
   - score_composite(): average pairwise consonance of simultaneous notes
   - adjust_for_consonance(): iterative adjustment (up to 5 passes, min 0.55)

1c. **Arpeggio Forms** (6 forms)
   - block, ascending, descending, alberti, broken, pendulum
   - Applied per rondo section for variety

1d. **Diatonic Chord Quality**
   - Map scale degrees to chord quality (major/minor/dim per mode)
   - Generate chord voicings that respect the harmonic function

1e. **Voice Orchestration**
   - Select 2-4 instrument ensemble per epoch
   - Assign roles: melody, bass, harmony, texture
   - Prevent timbral clashes between simultaneous layers

### Phase 2: WASM Mode Integration

2a. **HybridWasmMode** in wasm-synth.js
   - Instead of loading raw MIDI files, use music-generator.js to produce notes
   - Feed generated notes to the WASM AudioWorklet for synthesis
   - Fall back to SynthEngine if WASM unavailable

2b. **Instrument-to-program mapping**
   - Map JS instrument names (violin, piano, etc.) to GM program numbers
   - AudioWorklet receives program info per note_on

2c. **Mode switching**
   - WASM mode in the dropdown now uses compositional generation
   - Preserves all existing controls (speed, mutation, style sliders)

### Phase 3: MIDI Bar Sampling (stretch goal)

3a. **JS MIDI Sampler**
   - Load MIDI files from catalog
   - sample_bars_seeded(): hash seed → pick MIDI → extract bars → transpose
   - Loop-friendliness scoring (3 candidates)

3b. **Integration**
   - Replace melody layer with sampled MIDI phrases
   - Fall back to procedural if MIDI loading fails

---

## Workstream 2: MP3 Album Reconstruction

### Source Files
- **Render 1**: RadioEngineV8, seed=42, 30 minutes
  - File: apps/audio/cosmic_radio_v8.mp3 (42 MB)
  - Git commit: 88a543d

- **Render 2**: RadioEngineV15_V8Tempo, seed=42, 30 minutes
  - File: apps/audio/cosmic_radio_v18_v8-42.mp3 (42 MB)
  - Git commit: 3c362af

### Track Structure (12 tracks, ~5 min each)
- Tracks 1-6: From render 1 (RadioEngineV8)
  - Ember, Torrent, Quartz, Tide, Root, Glacier
- Tracks 7-12: From render 2 (RadioEngineV15_V8Tempo)
  - Bloom, Dusk, Coral, Moss, Thunder, Horizon

### Split Strategy
- Split at natural energy boundaries (low-energy windows)
- Preserve play order for arrangement continuity
- ~5 minutes per track (4:12 to 6:18 based on boundary detection)

### Deployment
- MP3 files go to deploy/shared/audio/tracks/ (shared across versions)
- album.json references them with correct audioFile paths
- Note event JSONs already exist in deploy/v9/inthebeginning-bounce/audio/

### Steps
1. Verify source MP3s exist in apps/audio/
2. If not, check if they're in deploy/v5/ (which has the full 84MB of MP3s)
3. Copy track MP3s to deploy/shared/audio/tracks/
4. Verify deploy/v9 album.json paths resolve correctly
5. Test MP3 mode with Playwright

---

## Testing Plan

- Playwright: all 12 mode combos (4 sound × 3 display)
- WASM compositional mode: verify rondo sections, consonance scoring
- MP3 mode: verify tracks load and play in order
- Visual: screenshots of all new features
- Session log with tool call transcript
