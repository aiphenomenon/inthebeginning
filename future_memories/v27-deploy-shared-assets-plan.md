# V27 Plan: Deploy Shared Assets (MIDI, Instruments, Path Fixes)

**Started**: 2026-03-23 09:28 CT (14:28 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe

## Problem

The deploy/shared/ folder is missing critical assets:
- 1,771 MIDI files (25MB) — exist in apps/audio/midi_library/ and deploy/v4/
- 60 instrument sample MP3s (2.5MB) — exist in apps/audio/samples/
- ATTRIBUTION.md for MIDI library

The v5 game and visualizer JS code has path fallbacks but:
- `musicSync.loadMidiCatalog()` method doesn't exist, call silently fails
- Default MIDI base `audio/midi_library/` points to a non-existent local dir
- Instrument sample paths try `../audio/samples/` which doesn't exist in deploy
- No SoundFont files needed (synth is Web Audio API based)

## Plan

### 1. Copy Assets to deploy/shared/
- `deploy/shared/audio/midi/` — all 1,771 MIDI files organized by composer
- `deploy/shared/audio/midi/ATTRIBUTION.md` — license/attribution info
- `deploy/shared/audio/instruments/` — 60 instrument sample MP3s

### 2. Fix JS Path References
Both apps need updated fallback chains that include shared paths:

**Game (inthebeginning-bounce):**
- Add `loadMidiCatalog` method to MusicSync or fix calling code
- Add `../../shared/audio/midi/` to MIDI file base URL fallback
- Add `../../shared/audio/instruments/` to sample path fallback
- Update `_initSoundMode` to use discovered shared base URL

**Visualizer:**
- Add `../../shared/audio/midi/` to MIDI base URL fallback
- Add `../../shared/audio/instruments/` to sample path fallback
- Ensure catalog base URL derivation works with shared paths

### 3. Path Resolution Strategy (GitHub Pages)
```
<gh-pages-root>/
  shared/
    audio/
      tracks/          12 album MP3s + notes JSON (exists)
      metadata/v1/     album.json + midi_catalog.json (exists)
      interstitials/   station ID MP3 (exists)
      midi/            1,771 MIDI files by composer (NEW)
      instruments/     60 instrument sample MP3s (NEW)
  v5/
    inthebeginning-bounce/
      audio/           local copies of album tracks + notes (exists)
    visualizer/
```

From game: `../../shared/audio/midi/Bach/xxx.mid`
From visualizer: `../../shared/audio/midi/Bach/xxx.mid`

### 4. Tests
- Deployment structure validation test
- Asset completeness test (all MIDIs, all instruments, all metadata)
- Path resolution simulation test (verify JS paths resolve correctly)
- Application flow tests (mode switching, catalog loading)
- Cross-version shared asset test (verify v5, future v6 can both access shared)

### 5. Documentation Updates
- CLAUDE.md: Add complete asset manifest to GitHub Pages section
- deploy/v5/inthebeginning-bounce/README.md: Document asset structure
- deploy/v5/visualizer/README.md: Document asset structure
- deploy/shared/README.md: Document shared asset versioning strategy

## Milestones
- [ ] Assets copied to deploy/shared/
- [ ] JS paths fixed in both apps
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Committed and pushed
