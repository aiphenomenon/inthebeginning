# V20 Future Memories — Audio Engine Overhaul Plan

**Created**: 2026-03-07 14:24 CT (20:24 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Session**: V20 Audio Engine Overhaul

---

## Context

User listened to the latest V18 Orchestra MP3 and liked it overall but identified:
1. **Low overall volume** — track is too quiet
2. **High-volume spikes** — blasts of noise later in the recording
3. Wants dramatically expanded instrument palette (~100 more SoundFonts)
4. Wants dramatically expanded MIDI sampling library (~1000 more files)
5. Wants 10-20% of moods to be "solo instrument" — just play the sampled arrangement
   on a single instrument, no chords/arpeggios/runs, let the brain reset
6. Wants more TTS engines (flite, festival, pico2wave via apt)
7. Wants Silero TTS + PyTorch installed and working
8. Wants two final MP3s: seed=42 and random seed

## Architecture Decisions

### Volume Fix Strategy
- **Root cause of low volume**: voice_gain = 0.25/n_voices means 2-4 voices get
  0.06-0.125 gain each. Combined with soft-knee at 0.75 and tanh in render_to_wav,
  this triple-limits the signal.
- **Root cause of spikes**: TTS injection and FluidSynth rendering (if enabled) may
  bypass the per-voice gain normalization.
- **Fix**: Add a final master normalization stage that:
  1. Scans for peak amplitude after all rendering
  2. Normalizes to -1dB (target peak 0.89)
  3. Applies a lookahead limiter to catch transients
  4. This replaces the current tanh in render_to_wav with proper normalization

### Solo Instrument Mood (10-20%)
- When selected (RNG roll), mood uses exactly 1 voice
- Plays the sampled MIDI arrangement directly (no chord building, no arpeggios)
- Picks one instrument from the expanded palette
- Applies normal coloring/note-bending
- Duration: standard mood duration (42-210s)

### Instrument/MIDI Sourcing
- GitHub repos with openly licensed SoundFonts and MIDI files
- All pre-1900 classical compositions are public domain worldwide
- Focus on .sf2 SoundFonts that are freely redistributable
- Key repos: FluidR3_GM, GeneralUser_GS, MuseScore soundfonts
- MIDI: Mutopia Project, Kunst der Fuge collections on GitHub

### Domain Requirements
- github.com (already allowed via settings)
- raw.githubusercontent.com (may need adding)
- objects.githubusercontent.com (may need adding)
- GitHub releases use github.com domain

## Milestones

- [x] Housekeeping complete (session log, future memories, release history) — 14:25 CT
- [x] TTS engines installed (flite, festival, pico2wave) — 14:26 CT
- [x] FluidSynth + FluidR3_GM/GS SoundFonts installed (128 GM instruments) — 14:26 CT
- [x] PyTorch 2.10.0 installed — 15:48 CT
- [ ] Silero model download BLOCKED (models.silero.ai inaccessible from sandbox proxy)
- [x] MIDI files downloaded (947 ADL + 80 Nottingham = 1,027 new) — 14:44 CT
- [x] Total MIDI library: 1,771 files from 121 directories
- [x] Volume normalization fixed (V20 engine) — 14:30 CT
- [x] Solo instrument mood added (15% chance) — 14:30 CT
- [x] Golden test evidence captured in session log — 14:40 CT
- [x] Reference tests: 295 passed — 14:58 CT
- [x] Golden output tests: 23 passed — 14:39 CT
- [x] Cross-language parity: 10 passed — 14:39 CT
- [x] Shell injection protection added to TTSEngine — 15:52 CT
- [x] Multi-TTS: espeak-ng + flite + festival + pico2wave all working — 15:52 CT
- [x] Domain approval steering added (triple cross-check) — 15:55 CT
- [x] Screen capture testing: 14 tests, 13 passed, 24 evidence files — 16:06 CT
- [x] Screen capture steering added (triple cross-check) — 16:10 CT
- [x] Seed-42 MP3 render COMPLETE — 16:14 CT (41.2 MB, mean -15.5dB, peak -0.3dB)
- [ ] Random-seed MP3 render — started 16:15 CT, ETA ~16:31 CT
- [ ] Post-execution verification + push
