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

- [ ] Housekeeping complete (session log, future memories, release history)
- [ ] TTS engines installed (flite, festival, pico2wave)
- [ ] PyTorch + Silero downloaded and configured
- [ ] SoundFonts downloaded (~100 instruments)
- [ ] MIDI files downloaded (~1000 files)
- [ ] Volume normalization fixed
- [ ] Solo instrument mood added
- [ ] Seed-42 MP3 generated
- [ ] Random-seed MP3 generated
- [ ] Golden test evidence captured
- [ ] Post-execution verification complete
