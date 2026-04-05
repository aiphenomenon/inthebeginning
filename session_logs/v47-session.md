# V47 Session Log — WASM Overhaul + Seek Tests + Mobile Viewports

## Session Start
- **Date**: 2026-04-05
- **Branch**: develop
- **Previous**: v46 (journal capture hook)

---

## Turn 1: Planning

**Requested**: Fix Bug #6 (WASM HUD), Bug #7 (raw instrument names),
#10 (GM in WASM), #13 (WASM music parity), T4 (playhead seeking tests).
Add mobile viewport tests, WORKLOG items for Firefox/WebKit, 2P touch,
3D player movement, object vanishing.

**Done**: Explored WASM architecture (3 parallel agents), Python radio
engine, playhead seeking, mobile CSS. Designed hybrid approach:
MusicGenerator composes, JS SampleBank plays with 60 MP3 samples.

---

## Turn 2: Implementation

### Phase 1: Plan + WORKLOG Items
- future_memories/v47-plan.md, session log, 6 new WORKLOG items
- #14 (2P touch zones), #15 (3D movement), #16 (object vanishing)
- T9 (Firefox/WebKit), T10 (mobile viewports), T11 (touch tests)

### Phase 2: Bug #6 — WASM HUD Fix
- app.js `_onTrackChange()`: added 'wasm' to MIDI/Synth condition
- app.js `_initSoundMode()`: set initial HUD track name for WASM
- music-sync.js: WASM time routes through MusicGenerator
- **Before**: empty HUD, "0:00 / 0:00"
- **After**: "Quantum Fluctuation" + "0:06 / 5:00"
- Screenshot evidence: e2e-wasm-hud.png

### Phase 3: Bug #7 — Clean Instrument Names
- music-sync.js: added `cleanInstrumentName()` static method
- Strips `_v0_additive_N`, `_v0_bell_N` suffixes, title-cases
- **Before**: "koto_v0_additive_32", "bass_v0_bell_432"
- **After**: "Koto", "Bass", "Warm Pad", "Cosmic"

### Phase 4-5: GM Instruments + Music Parity
- Verified WASM mode uses JS SampleBank (60 MP3 samples)
- MusicGenerator → SynthEngine → SampleBank pipeline shared across modes
- Audio output identical: WASM RMS=0.020, JS Synth RMS=0.020
- All 3 WASM display modes verified with screenshots:
  - e2e-wasm-game-v47.png (runner + obstacles + HUD)
  - e2e-wasm-grid-v47.png (2D grid + note blocks)
  - e2e-wasm-hud.png (player HUD with track info)

### Phase 6-7: Seek Tests + Mobile/Tablet
- 5 playhead seeking tests across all modes
- Synth: time advances 0:05→0:08, programmatic seek works
- MIDI: time advances 0:06→0:09, shows duration 1:18
- WASM: time advances 0:04→0:07, shows duration 5:00
- MP3: shows 0:04/4:11
- 11 mobile/tablet tests: iPhone 16 portrait/landscape + iPad
- Screenshots: e2e-mobile-*.png, e2e-tablet-*.png

### Phase 8: Deploy v12
- Created deploy/v12/inthebeginning-bounce/
- Also fixed synth mode initial track name (same gap as WASM)
- All 4 modes verified on v12: MP3, MIDI, Synth, WASM

### Phase 9: Version Cut
- 809 Python tests pass, 72 E2E tests pass
- WORKLOG updated: items #6, #7, #10, #13, T4, T10 marked Done
- RELEASE_HISTORY updated with v0.47.0

---

## Files Modified
- deploy/v11/inthebeginning-bounce/js/app.js (WASM HUD + synth HUD)
- deploy/v11/inthebeginning-bounce/js/music-sync.js (clean names + WASM time)
- deploy/v12/inthebeginning-bounce/ (new deploy version)
- tests/e2e/game.spec.mjs (seek tests, mobile/tablet, WASM combos)
- tests/e2e/wasm.spec.mjs (HUD content test)
- WORKLOG.md (6 new items, 6 items marked done)
- RELEASE_HISTORY.md (v0.47.0)

## Test Results
- 809 Python tests pass, 0 failures
- 72 E2E tests pass (was 47): +5 seek, +11 mobile, +3 WASM combos, +1 HUD, +5 misc
- 6 audio E2E tests pass (with xvfb-run)
