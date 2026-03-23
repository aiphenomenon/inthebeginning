# V27 Session Log — Deploy Shared Assets (MIDI + Instruments + Path Fixes)

## Turn 1 [2026-03-23 09:22 CT (14:22 UTC)]

### Request
User requested that the ~1,800 MIDI files, instrument sample files, and SoundFont files
be included in the deploy folder for GitHub Pages. Also requested:
- Verify all relative references from HTML/JS are correct for both apps
- Build comprehensive tests for deployment validation
- Update steering docs and per-app READMEs with complete asset manifests
- Create a robust shared folder strategy across versions
- Ensure thorough test coverage around deployment and app flows

### Audit Findings

1. **MIDI files**: 1,771 files across 120 composer directories (25MB total) exist in
   `apps/audio/midi_library/` and were deployed to `deploy/v4/cosmic-runner/midi/` but
   are completely missing from `deploy/shared/` and `deploy/v5/`

2. **Instrument samples**: 60 MP3 files (2.5MB total) exist in `apps/audio/samples/`
   but are not in `deploy/shared/` or `deploy/v5/`

3. **SoundFonts**: No .sf2 files in the repository. Browser synth uses Web Audio API
   with the 60 instrument sample MP3s instead. FluidR3_GM.sf2 exists at system level
   but is 142MB and not suitable for web deployment.

4. **Path resolution bug**: Game's `musicSync.loadMidiCatalog()` method doesn't exist —
   the call at app.js:485 silently fails. This means `midiBaseUrl` is never set from the
   shared catalog path, and the game falls back to `audio/midi_library/` which doesn't
   exist in deploy/v5.

5. **Missing shared directories**: `deploy/shared/audio/midi/` and
   `deploy/shared/audio/instruments/` are empty placeholders.

### Actions Taken
