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

1. **Copied 1,771 MIDI files** to `deploy/shared/audio/midi/` (120 composer directories)
2. **Copied 60 instrument samples** to `deploy/shared/audio/instruments/`
3. **Copied midi_catalog.json** alongside MIDIs for correct base URL resolution
4. **Added `loadMidiCatalog()` method** to MusicSync class (was completely missing)
5. **Fixed MIDI catalog fallback paths** in game and visualizer to include
   `../../shared/audio/midi/midi_catalog.json`
6. **Fixed instrument sample paths** in both synth-engine.js files to include
   `../../shared/audio/instruments/`
7. **Synced source files** in `apps/cosmic-runner-v5/js/` with deploy path fixes
8. **Created 108 tests** across two test files:
   - `tests/test_deploy_assets.py` (78 tests): Asset completeness, MIDI/instrument
     presence, path resolution simulation, HTML integrity, JS path validation,
     cross-version strategy, full catalog consistency
   - `tests/test_deploy_app_flows.py` (30 tests): Album loading flow, MIDI mode
     initialization, instrument sample loading, mode switching, cross-app sharing,
     end-to-end MIDI playback simulation
9. **Updated CLAUDE.md** with complete asset manifest table, shared folder versioning
   strategy documentation, detailed deploy layout, new test commands
10. **Created READMEs** for deploy/shared/, game app, and visualizer

### Test Results

```
tests/test_deploy_assets.py:    78 passed
tests/test_deploy_app_flows.py: 30 passed
Total:                         108 passed in 1.54s
```

### Files Changed

- `deploy/shared/audio/midi/` — 1,771 MIDI files + midi_catalog.json + ATTRIBUTION.md
- `deploy/shared/audio/instruments/` — 60 instrument MP3s
- `deploy/v5/inthebeginning-bounce/js/music-sync.js` — added loadMidiCatalog()
- `deploy/v5/inthebeginning-bounce/js/app.js` — updated MIDI catalog paths
- `deploy/v5/inthebeginning-bounce/js/synth-engine.js` — updated sample paths
- `deploy/v5/visualizer/js/app.js` — updated MIDI catalog paths
- `deploy/v5/visualizer/js/synth-engine.js` — updated sample paths
- `apps/cosmic-runner-v5/js/music-sync.js` — added loadMidiCatalog() (source sync)
- `apps/cosmic-runner-v5/js/app.js` — updated MIDI catalog paths (source sync)
- `apps/cosmic-runner-v5/js/synth-engine.js` — updated sample paths (source sync)
- `tests/test_deploy_assets.py` — 78 deployment validation tests (NEW)
- `tests/test_deploy_app_flows.py` — 30 application flow tests (NEW)
- `CLAUDE.md` — asset manifest, versioning strategy, test commands
- `deploy/shared/README.md` — shared directory documentation (NEW)
- `deploy/v5/inthebeginning-bounce/README.md` — game app documentation (NEW)
- `deploy/v5/visualizer/README.md` — visualizer documentation (NEW)
- `future_memories/v27-deploy-shared-assets-plan.md` — session plan (NEW)
- `session_logs/v27-session.md` — this session log (NEW)

### Commits

1. `969c6ff` — Add MIDI library + instrument samples to deploy/shared/ and fix asset paths
2. `09b98ce` — Add comprehensive deploy asset validation and app flow tests
3. `58773a4` — Update steering docs, READMEs, and source paths for shared deploy assets
