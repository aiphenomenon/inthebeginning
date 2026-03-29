# V31 Plan — Web Game & Visualizer Bug Fixes + Approach C Hybrid Audio

## Date: 2026-03-29

## Overview

Systematic bug hunting and fixing across the web game (inthebeginning-bounce) and
visualizer, plus beginning Approach C hybrid audio enhancements (WASM for sample-level
synthesis, JS for scheduling/structure, Web Audio for effects).

## Context

- User's prior session (PDF pages 448-453) analyzed three approaches to close the gap
  between Python radio engine and browser audio. User chose **Approach C: Hybrid**.
- Deploy versions: v5 (game+visualizer), v6 (game only), v7 (world music), v8 (WASM synth)
- Latest deploy is v8 with 4 sound modes: MP3, MIDI, Synth, WASM
- Visualizer exists in v5 but was dropped from v6+

## Phase 1: Testing Infrastructure (Playwright + Local Server)
- Install Playwright, Chromium, and dependencies
- Set up local HTTP server to serve deploy/v5/ and deploy/v8/
- Create automated test scripts that exercise all modes
- Screenshot every mode combination

## Phase 2: Bug Discovery
- Test all 3 display modes × 3-4 sound modes
- Test keyboard controls in each mode
- Test mode switching mid-playback
- Test track navigation (prev/next)
- Test mutation switching in MIDI mode
- Test 2D/3D toggle
- Test responsive layout
- Test the visualizer (deploy/v5/visualizer/)
- Document all bugs found

## Phase 3: Bug Fixes
- Fix each discovered bug
- Ensure fixes propagate to all deploy versions (v5, v6, v7, v8)
- Run tests after each fix

## Phase 4: Approach C Enhancements (if time permits)
- Enhance WASM synth: vibrato, FM synthesis, note coloring
- Enhance JS music generator: rondo patterns, consonance engine, scale expansion
- Wire Web Audio DSP chain: reverb, filters, compression

## Phase 5: Verification
- Re-run all Playwright tests
- Screenshot all modes post-fix
- Update session log and release history

---

## Progress (2026-03-29)

### Completed
- Installed Playwright + Chromium for automated browser testing
- Created comprehensive Playwright test suite (tests/test_web_game.mjs)
- Tested all 9 mode combinations (3 display × 3 sound modes) — all pass
- Visual inspection of all screenshots — rendering correct

### Bugs Found and Fixed
1. **Key "2" doesn't switch to Game mode** — duplicate `case '2'` in switch statement;
   first match was numpad P2 fast-drop which broke before mode-switching case.
   Fixed across v4-v8 + source copies.

2. **Visualizer FAMILY_HUES redeclaration error** — both grid.js and synth-engine.js
   declared `const FAMILY_HUES` at global scope. Changed to `var` with merge pattern
   so they coexist. This was cascading and also caused "SynthEngine is not defined."
   Fixed across v4-v5 + source copies.

3. **Visualizer generateCycle not a function** — app.js called
   `musicGenerator.generateCycle()` but MusicGenerator only has `generate(seed)`.
   Fixed to call `generate(seed)`.

4. **MIDI info panel empty on first track** — `startMidiMode()` called
   `setMode(MIDI)` which fires `onTrackChange` before any MIDI loads, so
   `trackInfo` was still null. Added `onTrackChange` call after initial
   `loadNextRandom()` completes. Fixed across v5-v8 + source copies.

### Code Review (verified false positives)
- Jump physics Math.min: CORRECT (jumpPower is negative)
- generatePlayerName undefined: FALSE (defined in characters.js, global scope)
- Synth mode not initialized: FALSE (setMode called at line 614 before _initSoundMode)
- Duplicate keydown listeners: NOT A BUG (separate concerns, idempotent)

### Test Results
- Playwright: 38 PASS, 0 FAIL, 3 WARN (warnings are test introspection limits)
- Python core tests: 283 passed in 0.56s
- No JS errors in either game or visualizer (excluding expected 404s for shared assets)

### CI Fixes (2026-03-29 morning continued)
- Fixed GitHub CI python-tests: excluded integration tests (covered by golden.yml)
- Regenerated golden snapshots for token count drift
- Added token count normalization to golden comparison
- Fixed Swift: added `import InTheBeginningSimulator` to all 6 Apple-only files
- Set up Apple CI daily schedule, monitoring 11:00 AM CT run
- Cleaned up .gitignore for Swift .build/

### V9 Game Release Plan (2026-03-29 afternoon)
1. Research: Read PLAN.md, RELEASE_HISTORY.md, all future_memories,
   docs/ pertaining to game/music/audio, session_logs archive,
   and git history to understand v7→v8 regressions
2. Comparative Playwright testing across v5/v6/v7/v8 deploy versions
   to identify all gameplay, audio, and visual regressions
3. Fix all regressions + bring game to v9 quality
4. Rename all "Cosmic Runner" references to "inthebeginning bounce"
5. Create deploy/v9 with all fixes
6. Visual test report: screenshots + animated GIFs in session log
7. Make gameplay capture reproducible for future releases
8. Update deploy/shared if audio/MIDI assets changed
9. Approach C hybrid audio enhancements (WASM + JS)
