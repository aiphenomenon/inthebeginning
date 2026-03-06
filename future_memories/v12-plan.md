# V12 Radio Engine Plan -- Future Memory

**Created**: 2026-03-06 19:02 UTC (13:02 CT)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Session**: Resume from v11, user requested v12 overhaul

## User Intent (from speech-to-text, preserved as-is)

The user reported v9-v11 have drifted toward harsh, synthy, "Zelda and 80s synth"
character with ear-piercing high-pitched noises. They want to return to v8's more
natural instrument character while keeping the improvements from v9-v11 (gain staging,
consonance, bar grid, orchestration, expanded MIDI library, instrument diversity).

Key requirements:
- Instruments should sound "true to form" -- more like actual high-quality MIDI instruments
- Many instruments employed across different moods
- No unpleasant highs and lows
- Not too fast tempo, not jarring
- Nice arpeggios, runs, rondos in conventional time signatures (2/4, 3/4, 4/4 mostly)
- MIDI scores lined up to bars (especially 4/4)
- Color and bend notes from original instruments but NOT excessively
- Multiple instruments playing together like a band or orchestra sections
- NOT undue emphasis on piano/keyboard/organ only
- Bass instruments need more presence
- Infinite radio station quality -- pleasant to work/listen to
- Draw on great composers and their work
- Central Time timestamps in all responses and script output
- UTC timestamps in logs/future memories
- Regular progress updates

## Root Cause Analysis

### Why v11 sounds harsh/synthy:
1. `_synth_gm_note_np()` brightness control adds 5th harmonic emphasis for bright instruments (>0.6 brightness). At high MIDI notes with octave shifts, this creates piercing frequencies.
2. All harmonics perfectly tuned -- no natural detuning = synthetic character
3. No noise/breath components -- lacks organic quality of real instruments
4. synth_lead/synth_fx/synth_pad = ~17 GM programs heavily represented
5. MIDI note ceiling at 108 (C8) allows fundamentals over 4kHz; with harmonics, reaches ear-piercing territory
6. Short attack times (1ms for synth_lead, mallets) create sharp transients
7. v11's OrchestratorV11 shifts melody voice +12 semitones -- combined with already-high MIDI notes, this pushes into painful frequency range

### What v8 did right:
- InstrumentFactory generated 500+ instruments with 10 synthesis techniques
- `_synth_colored_note_np()` blended clean base with instrument-specific coloring
- More varied instrument families and synthesis approaches
- Natural-sounding envelopes with variation
- Orchestral layering at 75% with register offsets [-12, 0, 0, 12, 24]

### What v9-v11 improvements to KEEP:
- v9: 50 expanded GM instruments, 15 family pools, density-aware tempo
- v10: GM timbre profiles (each family has distinct synthesis), 744 MIDI files
- v10: 85% orchestral layering, 4-6 voices per segment
- v11: GainStage (per-voice RMS norm + master bus limiting) -- ESSENTIAL
- v11: ConsonanceEngine (inter-voice consonance scoring) -- ESSENTIAL
- v11: BarGrid (metric alignment) -- ESSENTIAL
- v11: OrchestratorV11 (role assignment with voice leading) -- ESSENTIAL
- v11: Separated pan/gain mixing (fixes phase inversion) -- ESSENTIAL
- v11: Reduced reverb (comb feedback 0.55-0.65)
- v11: Pre-reverb highpass, soft-knee limiting

## V12 Implementation Plan

### 1. New synthesis function `_synth_gm_note_v12_np()`
- Add slight harmonic detuning (±0.1-0.3%) per harmonic -- creates natural beating/warmth
- Remove brightness-based 5th harmonic emphasis entirely
- Add per-instrument noise layer (breath for woodwinds, bow noise for strings, hammer for piano)
- Cap fundamental frequency at mtof(84) = 1047 Hz (C6) -- no higher
- Natural vibrato with randomized rate (4-7 Hz) and delayed onset
- Frequency-dependent timbre: higher notes slightly purer (fewer harmonics)

### 2. Revised `GM_TIMBRE_PROFILES_V12`
- Richer harmonic profiles with more harmonics per family
- Slower attacks for most instruments (more natural)
- Add 'noise_amount' parameter per profile (0.0-0.1)
- Add 'detune_cents' parameter per profile (0.5-3.0)
- Lower 'brightness' values across the board
- Add separate profiles for acoustic vs. electric vs. synth variants

### 3. `RadioEngineV12` class
- Inherit from RadioEngineV11 (keep all mixing improvements)
- Override instrument selection: bias 70% toward acoustic families
  (strings, brass, woodwinds, bass, piano, guitar, ensemble, world)
- Cap MIDI notes at 84 in voice rendering (prevents ear-piercing highs)
- Reduce orchestrator melody offset from +12 to +7 (a fifth, not an octave)
- Master lowpass at 7kHz (down from 8kHz) for gentler highs
- Ensure every ensemble has at least one bass/foundation instrument
- Longer minimum note durations (0.15s minimum, promotes legato)
- Reduce synth voice weight to 30% of acoustic voice weight

### 4. `generate_radio_v12_mp3()` entry point
- Print timestamps in CT format for user, UTC in logs
- Progress reporting at each segment

### 5. Tests
- Unit tests for new synthesis function
- Integration test for full v12 render
- Verify frequency ceiling enforcement
- Verify acoustic instrument bias

## Milestone Tracking

- [ ] Future memories plan written and pushed
- [ ] V12 code implementation
- [ ] Tests passing
- [ ] MP3 generation (seed 42)
- [ ] MP3 generation (random seed)
- [ ] Steering updates
- [ ] Session log updates
- [ ] Final push

## Recovery Notes

If session is interrupted:
- The v12 code lives in apps/audio/radio_engine.py after the v11 section
- Key new items: _synth_gm_note_v12_np(), RadioEngineV12, generate_radio_v12_mp3()
- All v8-v11 code remains intact for comparison
- The branch is claude/resume-v9-document-v8-6yhAe
