# V34 Plan — MP3 Note/MIDI Source Reconstruction + Effects Display

## Date: 2026-03-30

## Overview

Three interconnected deliverables for deploy/v10:

1. **MP3 Album: Reconstruct per-note MIDI source provenance**
   Re-run RadioEngineV8 (seed=42) and RadioEngineV15_V8Tempo (seed=42) to
   capture which MIDI file was sampled for each note/section. Embed this in
   the per-track JSON files so the game can show "sampled from Bach — Prelude
   in C Major" in the lower-left note info boxes during MP3 playback.

2. **WASM mode: Show MIDI source in note info boxes**
   Since WASM mode now uses MusicGenerator (Approach C), and MusicGenerator
   doesn't sample from MIDIs (it's procedural with motifs), show the motif
   source and epoch info in the boxes. If MIDI sampling is added later, show
   the actual MIDI source.

3. **Effects display boxes for all modes**
   Add boxes in the lower-left showing active effects (reverb, filter, pitch
   shift, tempo mult, vibrato, etc.) per note/chord. For Synth and WASM this
   is known at runtime. For MP3 Album, embed in the per-track JSON.

## Step 1: Re-run RadioEngineV8 to capture MIDI provenance

The engine uses `sample_bars_seeded()` which selects MIDIs deterministically
via SHA256 of sim_state. By re-running with seed=42 and capturing the
`midi_info` dict returned by each call, we get per-section MIDI file paths.

Need to:
- Read `apps/audio/generate_v8_album.py` to understand the generation flow
- Read `apps/audio/radio_engine.py` sample_bars_seeded() return format
- Either re-run the engine or trace the selection logic manually
- Output: enhanced per-track JSON with `midi_source` per note event

## Step 2: Enhance note event JSON format

Current format per note: `{ t, note, dur, vel, ch, inst }`
Enhanced format: `{ t, note, dur, vel, ch, inst, midi_source?, effects? }`

Where:
- `midi_source`: "Bach/adl_Prelude_in_C_Major.mid" (the MIDI file sampled)
- `effects`: { reverb: 0.3, filter: "lowpass", pitchShift: 0, vibrato: true }

## Step 3: Update display in app.js

The lower-left boxes currently show note events (pitch + instrument name).
Add:
- MIDI source box: "Sampled from: Bach — Prelude in C Major"
- Effects box: "Reverb 0.3 · Lowpass · Vibrato"

These should update in real-time as the playhead moves, staying in sync
with the grid visualization.

## Step 4: Create deploy/v10

Copy deploy/v9, apply changes, test with Playwright.

## Testing

- Playwright: verify all modes show correct info boxes
- Verify boxes update when playhead moves
- Verify boxes update on track change
- Verify no JS errors across all 12 mode combos
- Screenshots for report
