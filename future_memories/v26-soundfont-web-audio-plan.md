# V26 Plan: SoundFont Integration + MIDI Source Display + Web Audio Enhancements

**Created**: 2026-03-23 06:52 CT (11:52 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe

## User Direction (Paraphrased)

The user wants several enhancements to the web-based audio experiences:

1. **MIDI source display**: When playing music, show which MIDI file the sample was
   taken from, and the given note arrangement, BEFORE the effects are applied.

2. **Instrument-based playback**: The Python version uses instruments to produce played
   notes before applying coloring/imprinting/bending. The web version should similarly
   use instruments. The user noted the Python audio engine uses FluidSynth + FluidR3_GM.sf2
   SoundFont for instrument rendering.

3. **SoundFont integration**: FluidR3_GM.sf2 exists on the system at
   `/usr/share/sounds/sf2/FluidR3_GM.sf2` (142MB). For web, we need a lightweight
   approach. We can't ship 142MB. Options:
   - Use the existing additive synthesis SynthEngine (already works across browsers)
   - Consider loading smaller SF2 subsets via Web Audio API AudioBuffer
   - Browser built-in MIDI instruments via Web MIDI API (limited browser support)
   - The user is OK with browser synth approach if SF2 is too resource intensive

4. **Coloring/imprinting/bending library (~538 effects)**: The user said this should
   be documented as a future consideration for web. The Python engine has clamped
   mechanisms to keep sounds palatable for human hearing.

5. **Instrument substitution**: Sometimes use a different GM instrument but same
   note/intensity/duration for variety.

6. **SoundFont files in repo**: There are NO .sf2 files in the repo itself. The system
   has FluidR3_GM.sf2 at /usr/share/sounds/sf2/. The repo has 60 pre-rendered MP3
   instrument samples in apps/audio/samples/ (violin, cello, piano, etc.).

## Architecture Decisions

### SoundFont Approach: Hybrid
- **Primary**: Keep additive synthesis SynthEngine (works everywhere, zero dependencies)
- **Enhancement**: Load the 60 MP3 instrument samples from apps/audio/samples/ as
  AudioBuffers. These are real instrument recordings that can be pitched to any note.
- **GM mapping**: Map GM program numbers to the closest available sample instrument
- **Fallback**: If sample loading fails, fall back to additive synthesis (already works)
- This gives us REAL instrument sounds without shipping a 142MB SF2 file

### MIDI Source Display
- Add an info panel that shows: MIDI file name, composer, era, and the raw note
  arrangement from the MIDI before effects
- Show this in both visualizer and cosmic-runner-v5

### Instrument Substitution
- Maintain a substitution table: GM program → primary sample + alternatives
- When playing, occasionally substitute with a compatible instrument
- Same note, intensity, duration — just different timbre

### Coloring/Imprinting/Bending (Future)
- Document the ~538 effect library from Python as a future enhancement
- The existing 16 mutation presets (pitchShift, tempoMult, reverb, filter) provide
  a subset of this capability
- Full port would require careful clamping for human hearing comfort

## File Changes

### Modified Files
- `apps/visualizer/js/synth-engine.js` — Add sample-based instrument playback
- `apps/visualizer/js/midi-player.js` — Add MIDI source info display
- `apps/visualizer/js/app.js` — Wire up MIDI info panel
- `apps/visualizer/index.html` — Add MIDI source info panel UI
- `apps/cosmic-runner-v5/js/synth-engine.js` — Same SynthEngine updates
- `apps/cosmic-runner-v5/js/midi-player.js` — Same MIDI info updates
- `apps/cosmic-runner-v5/js/app.js` — Wire up MIDI info panel
- `apps/cosmic-runner-v5/index.html` — Add MIDI source info panel UI

### Deploy Updates
- `deploy/v5/visualizer/` — Updated build
- `deploy/v5/inthebeginning-bounce/` — Updated build

## Milestone Checkpoints
- [ ] Plan committed and pushed
- [ ] SynthEngine sample loading implemented
- [ ] MIDI source info panel added to visualizer
- [ ] MIDI source info panel added to cosmic-runner-v5
- [ ] Deploy updated
- [ ] Tests passing
