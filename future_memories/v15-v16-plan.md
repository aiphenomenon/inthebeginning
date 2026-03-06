# v0.15.0 + v0.16.0 Plan — True Original V8 Synthesis Engines

## Date: 2026-03-06 17:30 CT

## Context

User noticed V13 (and by extension V14) sounds "a bit off" compared to the original V8.
Investigation revealed the current V8 class uses numpy-accelerated `_synth_colored_note_np()`
(added in commit 45791bd) instead of the original `InstrumentFactory.synthesize_colored_note()`.
The numpy version was added for ~7x speedup but may produce subtly different audio.

User wants to go back to the **true original V8 behavior** from git commit 348bf29.

## Key Difference: Original vs Current V8 Synthesis

- **Original V8** (348bf29): `self.factory.synthesize_colored_note(color_instr, freq, dur_sec, vel, ca)`
  - Pure Python, uses InstrumentFactory timbre blending
  - 537 instruments from `generate_instrument_set(537)`
  - Slower but authentic sound

- **Current V8** (HEAD): `_synth_colored_note_np(freq, dur_sec, color_instr, vel, ca)`
  - Numpy-accelerated, different parameter order
  - Same 537 instruments
  - ~7x faster but potentially different harmonic content

## V15 Design (like V13 but true V8)
- Inherit from RadioEngineV8
- Override `_render_segment` to force original `synthesize_colored_note()` path
- Override `_compute_tempo_multiplier` with V12's density-aware tempo (1.1-1.7x)
- V8's 5 instrument families
- 537 instruments
- Serial rendering

## V16 Design (like V14 but true V8)
- Inherit from RadioEngineV8
- Override `_render_segment` to force original `synthesize_colored_note()` path
- Override `_compute_tempo_multiplier` with V12's density-aware tempo
- Override `_choose_gm_instruments` with V12's 15-family expanded palette
- All 744 MIDI files
- Serial rendering

## Deliverables
- RadioEngineV15 + RadioEngineV16 classes
- generate_radio_v15_mp3() + generate_radio_v16_mp3() functions
- CLI --version v15/v16 support
- Unit tests
- Four 30-min MP3s (V15 seed-42/random, V16 seed-42/random)
- Raw GitHub download URLs
