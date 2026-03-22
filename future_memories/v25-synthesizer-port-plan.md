# V25 Plan: Synthesizer Port + Visualizer V3 Upgrade

**Created**: 2026-03-22 17:35 CT (22:35 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe

## Overview

Major upgrade to both the standalone Visualizer app and Cosmic Runner V3:
1. Port the Python synthesizer engine to JavaScript Web Audio API
2. Add Web Worker-based concurrent synthesis for performance
3. Add MIDI mode with full catalog (1,854 files) to the visualizer standalone app
4. Add MP3 album playback to the visualizer
5. Add synthesizer coloring/bending/mutation controls (16 flavors)
6. Make both apps fully deployable to GitHub Pages with all accoutrements

## Architecture

### Synthesizer Port (synth-engine.js)
- Port AdditiveSynth from composer.py → Web Audio API oscillator bank
- 16+ instrument timbres with harmonic profiles (violin, cello, flute, etc.)
- ADSR envelopes, vibrato, tremolo
- Percussion synthesis (kick, snare, hihat, rim)
- Pitch bend support with real-time frequency modulation
- Color mapping: instrument → HSL hue (matching grid.js color scheme)

### Web Workers (synth-worker.js)
- Offload MIDI parsing to a worker thread
- Worker handles: MIDI binary parsing, note event building, tempo mapping
- Main thread handles: AudioContext scheduling, UI updates, grid rendering
- MessagePort protocol: {type: 'parse', buffer} → {type: 'notes', notes, duration}
- Fallback to main thread if Workers unavailable

### Visualizer V3 Upgrade
- Add synth-engine.js, synth-worker.js, midi-player.js to visualizer
- New mode: "Synth" alongside Album/Single/Stream
- MIDI catalog integration with infinite shuffle
- 16 mutation presets (from config.js MIDI_MUTATIONS)
- Synthesizer coloring: real-time hue mapping from instrument families
- Pitch bending visualization: pulsing glow animation on bent notes
- Full MIDI library access via audio/midi_catalog.json

### Cosmic Runner V3 Integration
- Replace basic oscillator MidiPlayer with new SynthEngine
- Share synth-engine.js and synth-worker.js between both apps
- Consistent mutation/coloring/bending UI across both apps

## File Plan

### New Files (Visualizer)
- apps/visualizer/js/synth-engine.js — Full synthesizer port
- apps/visualizer/js/synth-worker.js — Web Worker for MIDI parsing
- apps/visualizer/js/midi-player-v2.js — Enhanced MIDI player using SynthEngine
- apps/visualizer/test/test_synth_engine.js — Synth engine tests
- apps/visualizer/test/test_midi_player.js — MIDI player tests

### Modified Files (Visualizer)
- apps/visualizer/index.html — Add synth mode UI, MIDI controls
- apps/visualizer/js/app.js — Integrate synth mode, MIDI catalog
- apps/visualizer/js/grid.js — Pitch bend visualization
- apps/visualizer/js/player.js — Synth playback support
- apps/visualizer/js/score.js — MIDI score support
- apps/visualizer/css/visualizer.css — Synth mode styles

### Modified Files (Cosmic Runner V3)
- apps/cosmic-runner-v3/js/midi-player.js — Upgrade with SynthEngine
- apps/cosmic-runner-v3/js/app.js — Integrate enhanced synth

### Build/Deploy
- apps/visualizer/build.py — Build script for GitHub Pages
- apps/cosmic-runner-v3/build.py — Updated build script

## Deployment Guide (GitHub Pages)

Both apps deploy as static sites:
1. Run build.py to produce dist/ with all assets
2. Copy dist/ to GitHub Pages repo
3. For MP3s: include audio/ directory with MP3s + note JSON
4. For MIDI: include midi/ directory with MIDI files + midi_catalog.json
5. For synth: no additional assets needed (pure Web Audio)

Options for users:
- MP3 only: Just include audio/ directory
- Synth only: No audio files needed, smallest deployment
- MIDI mode: Include midi/ directory (25MB for full library)
- Full: All of the above
