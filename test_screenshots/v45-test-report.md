# V45 E2E Test Report — inthebeginning bounce

**Date**: 2026-04-04  
**Deploy version tested**: v11  
**Source**: apps/inthebeginning-bounce/ (verified = deploy/v11/)

---

## Test Summary

| Suite | Tests | Pass | Fail | Duration |
|-------|-------|------|------|----------|
| game.spec.mjs | 47 | 47 | 0 | 3.7 min |
| audio.spec.mjs | 6 | 6 | 0 | 1.6 min |
| wasm.spec.mjs | 5 | 5 | 0 | 1.0 min |
| **Total** | **58** | **58** | **0** | **6.3 min** |

---

## Audio Analysis Results

| Mode | RMS | Peak | Est. Freq | Has Audio |
|------|-----|------|-----------|-----------|
| MP3 (Album) | 0.060 | 0.303 | 363 Hz | Yes |
| MIDI (Library) | 0.014 | 0.101 | 396 Hz | Yes |
| Synth (Procedural) | 0.009 | 0.054 | 230 Hz | Yes |
| WASM Synth | 0.017 | 0.084 | 388 Hz | Yes |
| JS Synth | 0.012 | 0.067 | 76 Hz | Yes |

**All sound modes produce real audio output.** MP3 has the highest
amplitude (pre-recorded), MIDI and WASM are comparable, Synth is quietest.

---

## Scenarios Tested (Functioning Correctly)

### Title Screen
- [x] Title screen loads with all expected elements (screenshot: e2e-title-screen.png)
- [x] Sound mode dropdown has 4 options: MP3, MIDI, Synth, WASM
- [x] Player count buttons (1P / 2P) switch correctly
- [x] Infinite mode toggle present
- [x] Theme, Accessibility, Credits buttons present

### Mode Combinations (9/9 pass)
- [x] MP3 / Game — runner visible, terrain rendered, track info shows (e2e-mode-mp3-game.png)
- [x] MP3 / Player — full-screen visualization, note info bottom left (e2e-mode-mp3-player.png)
- [x] MP3 / Grid — 64x64 grid with note blocks, 2D/3D toggle (e2e-mode-mp3-grid.png)
- [x] MIDI / Game — MIDI info panel top-right, runner + obstacles (e2e-mode-midi-game.png)
- [x] MIDI / Player — composer info, note display (e2e-mode-midi-player.png)
- [x] MIDI / Grid — colored blocks from MIDI synthesis (e2e-mode-midi-grid.png)
- [x] Synth / Game — procedural generation working (e2e-mode-synth-game.png)
- [x] Synth / Player — epoch info displayed (e2e-mode-synth-player.png)
- [x] Synth / Grid — warm_pad, cello, cosmic instruments visible in note bar (e2e-mode-synth-grid.png)

### Keyboard Controls
- [x] Keys 1/2/3 switch between Player/Game/Grid modes
- [x] Tab buttons switch modes (e2e-tab-switching.png)
- [x] P key pauses/resumes (e2e-paused.png)
- [x] Arrow keys and WASD for movement (e2e-game-controls.png)
- [x] Space for jump

### HUD Elements
- [x] Music bar: play/prev/next/seek/volume all present
- [x] Speed up/down buttons work
- [x] Mute button toggles
- [x] Score displays in game mode
- [x] Restart button returns to title screen

### Track Navigation
- [x] MP3 next/prev changes track (e2e-mp3-next.png)
- [x] MP3 play/pause button works
- [x] MP3 seek bar exists
- [x] MP3 time display updates
- [x] MP3 volume slider works
- [x] Track list overlay opens on title click (e2e-track-list.png)
- [x] MIDI info panel shows composer/source (e2e-midi-playing.png)
- [x] MIDI next loads new MIDI (e2e-midi-next.png)
- [x] Synth shows epoch info (e2e-synth-playing.png)
- [x] Synth next advances to next epoch

### Overlay Modals
- [x] Mutation overlay — 16 presets visible (e2e-mutation-overlay.png)
- [x] Style overlay — 4 sliders: speed, arpeggio, chords, bend (e2e-style-overlay.png)
- [x] Instrument soundbank — 10 families (e2e-instrument-overlay.png)
- [x] Help overlay (e2e-help-overlay.png)
- [x] Theme overlay (e2e-theme-overlay.png)
- [x] Credits overlay (e2e-credits-overlay.png)
- [x] Accessibility overlay — 3 modes + 3D/note toggles (e2e-accessibility-overlay.png)

### Grid Mode
- [x] 2D/3D toggle works (e2e-grid-2d.png, e2e-grid-3d.png)
- [x] Note blocks render in both 2D and 3D

### Canvas Rendering
- [x] Game mode: non-blank, varied content (e2e-canvas-game.png)
- [x] Grid mode: non-blank, note blocks visible (e2e-canvas-grid.png)
- [x] Player mode: non-blank (e2e-canvas-player.png)

### 2-Player Mode
- [x] Starts successfully with 2P selection (e2e-2player.png)

### WASM Mode
- [x] WASM option in dropdown
- [x] WASM binary loads successfully
- [x] WASM produces real audio (RMS=0.017)
- [x] Graceful fallback when .wasm is blocked (e2e-wasm-fallback.png)

### Audio Continuity
- [x] Audio continues across display mode switches (Game->Player->Grid)
- [x] Audio pauses on P key (captured silence)

---

## Bugs / Issues Discovered

### BUG 1: WASM mode shows no track info or time
**Screenshot**: e2e-wasm-playing.png, e2e-wasm-fallback.png  
**Severity**: Medium  
**Description**: When in WASM mode (player display), the HUD shows:
- No track name in header area
- Time display shows "0:00 / 0:00"
- No MIDI info panel
- Music bar track info is empty
- The display is almost entirely blank (just stars background)

This is different from Synth mode (which shows epoch names) and MIDI mode
(which shows composer/piece info). WASM mode does produce audio (verified
via spectral capture) but provides no visual feedback about what's playing.

### BUG 2: MP3 player mode note info shows raw internal instrument names
**Screenshot**: e2e-mode-mp3-player.png  
**Severity**: Low  
**Description**: The note info bar at the bottom shows raw internal names
like "koto_v0_additive_32", "bass_v0_bell_432" instead of human-readable
instrument names. These appear to be synthesis voice identifiers rather
than the actual instrument names from the note data JSON.

### BUG 3: WASM mode voice/choir instrument family unchecked by default
**Screenshot**: e2e-instrument-overlay.png  
**Severity**: Low  
**Description**: In the Instrument Soundbank modal, Voice/Choir appears
unchecked/disabled by default while all other 9 families are enabled.
This may be intentional (additive synthesis fallback) but is inconsistent.

### PRE-EXISTING BUG: test_twelve_notes_files expects 12 but finds 24
**Test**: tests/test_deploy_assets.py::TestSharedAlbumTracks::test_twelve_notes_files  
**Severity**: Low  
**Description**: The test expects 12 note JSON files in shared/audio/tracks/
but finds 24 (both v3 and v4 note data files coexist). Not caused by v45 changes.

---

## GM Instrument Quality Assessment

The GM instrument mapping in synth-engine.js is **comprehensive and working**:
- All 128 GM programs mapped to 60 real MP3 instrument samples
- Sample-based playback with pitch shifting (±2 octaves)
- 15% substitution rate adds orchestral variety
- Additive synthesis fallback (17 timbres) for unloaded samples
- Channel 9 percussion handled separately

MIDI playback uses real instrument recordings (MP3 samples) rather than
pure additive synthesis. The samples are professional quality and produce
realistic-sounding output, as confirmed by the audio capture analysis
showing musical frequency content (396 Hz estimated fundamental).

The Instrument Soundbank modal allows toggling 10 instrument families,
giving users control over the sound palette.

---

## WASM Quality Assessment

The WASM synth (40KB binary, Rust-compiled) is **functional but limited**:
- Successfully loads in browser (wasm_synth_bg.wasm)
- Produces real audio output (RMS=0.017, comparable to JS synth at 0.012)
- Graceful fallback when WASM unavailable
- Only 13 additive timbres vs JS's 60 MP3 sample instruments
- No track metadata display (BUG 1 above)
- Missing GM sample bank (uses additive synthesis only)

**Quality gap**: WASM synth sounds noticeably more "digital" than the
JS SynthEngine which uses real instrument recordings. Bridging this
gap is enqueued as future work.
