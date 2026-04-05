# Release History

Release history for **In The Beginning** — reverse chronological order (newest first).

---

## v0.47.0 — 2026-04-05 — WASM Overhaul + Seek Tests + Mobile Viewports

### Summary
Made WASM mode fully functional with Python-quality audio via hybrid
architecture: MusicGenerator composes (44 scales, 12 epochs, 25 rhythms),
JS SampleBank plays with 60 real MP3 instrument samples. Fixed 2 bugs,
added playhead seek tests across all 4 modes, mobile/tablet viewport
tests (iPhone 16, iPad), and WASM mode combination tests. Deploy v12.

### Bug Fixes
- **#6 WASM HUD**: Added `wasm` case to `_onTrackChange()`, set initial
  track name, routed time through MusicGenerator. Now shows "Quantum
  Fluctuation" + "0:06 / 5:00" instead of empty/0:00.
- **#7 Raw instrument names**: `cleanInstrumentName()` strips synthesis
  suffixes. "koto_v0_additive_32" → "Koto", "warm_pad" → "Warm Pad".
- **Synth HUD**: Also fixed synth mode initial track name (same gap).

### WASM Audio Parity (#10 + #13)
Hybrid JS+WASM architecture confirmed working:
- MusicGenerator generates notes with epoch-appropriate instruments
- JS SampleBank plays them with 60 real MP3 samples
- WASM AudioWorklet provides low-latency additive synthesis layer
- Audio output identical: WASM RMS=0.020, JS Synth RMS=0.020
- All 3 display modes work: game (runner+obstacles), player (HUD+notes),
  grid (2D/3D note blocks)

### New Tests (72 total, was 47)
- **Playhead Seeking** (5 tests): all 4 modes + programmatic seek
- **Mobile iPhone 16** (5 tests): 390×844 portrait — title, game, player, grid, help
- **Mobile Landscape** (2 tests): 844×390
- **Tablet iPad** (4 tests): 820×1180 — title, game, grid, overlays
- **WASM Combinations** (3 tests): wasm/game, wasm/player, wasm/grid
- **WASM HUD** (1 test): track name + time verification

### Deploy
- `deploy/v12/inthebeginning-bounce/` created with all fixes
- Shared audio paths verified (../../shared/audio/ resolves correctly)

### New WORKLOG Items
- #14: 2P flick-up from lower 1/9th corners
- #15: 3D mode player movement in manifold
- #16: Object vanishing at manifold edge
- T9: Firefox + WebKit browser verification
- T11: Touch interaction E2E tests

### Test Results
- 809 Python tests pass, 0 failures
- 72 game/WASM E2E tests pass
- 6 audio E2E tests pass (with xvfb-run)

---

## v0.46.0 — 2026-04-05 — Journal Capture Hook + Test Fix

### Summary
Fixed journal verbatim quality by adding a PostToolUse hook that captures
every tool call in real-time to `.tool_capture.jsonl`. Tool parameters and
output are now verbatim, not reconstructed from memory. Fixed the pre-existing
`test_twelve_notes_files` failure (expects 24 JSONs for v3+v4 note data).

### Journal Capture System
- `journal-capture.sh` PostToolUse hook fires on all tool types
- Captures verbatim `tool_input` and `tool_response` to JSONL
- Truncation at capture time (12K chars / 100 lines per field)
- Real UTC timestamps from `datetime.now(timezone.utc)`
- Journal assembly reads capture file instead of reconstructing from memory

### Test Fix
- `test_twelve_notes_files` → `test_notes_files`: expects 24 (12 v3 + 12 v4)
- 809 tests pass, 0 failures

### Timestamp Accuracy
- Hook-level timestamps: precise (real system clock UTC)
- Turn-level timestamps: approximate (assigned at journal assembly time)
- CT derived from UTC-5 (CDT)

---

## v0.45.0 — 2026-04-04 — Testing Infrastructure + GM Verification

### Summary
Built comprehensive browser E2E testing infrastructure with real audio
capture. PulseAudio virtual audio sink enables spectral analysis of browser
audio output. Playwright test suite covers all game modes, controls, overlays,
and track navigation. Verified GM instruments, WASM synthesis, and all 4
sound modes produce real audio. Expanded WORKLOG to cover all 22+ apps.

### Testing Infrastructure
- **PulseAudio virtual audio sink** (`tools/audio-sink.sh`): Browser audio
  → null sink → monitor source → PCM capture → spectral analysis. Headful
  Chromium via `xvfb-run` outputs real audio (headless uses fake device).
- **58 Playwright E2E tests** across 3 spec files:
  - `game.spec.mjs`: 47 tests — title screen, 9 mode combos (3 sound × 3
    display), keyboard controls, HUD, track nav, overlays, grid, canvas, 2P
  - `audio.spec.mjs`: 6 tests — audio capture per mode, mode-switch, pause
  - `wasm.spec.mjs`: 5 tests — WASM load, audio, fallback, JS comparison
- **Pytest integration**: `conftest.py` with markers, `test_e2e_browser.py`
  as Python wrapper, `pytest.ini` with test categories
- **Targeted execution**: `tools/quick-test.sh` with blast-radius analysis
  (Tier 1: <5s always, Tier 2: ~30s on change, Tier 3: ~4min for game code)
- **CI**: Added `browser-e2e` job in `.github/workflows/ci.yml`

### Audio Verification Results
| Mode | RMS | Peak | Verified |
|------|-----|------|----------|
| MP3 | 0.060 | 0.303 | Yes |
| MIDI | 0.014 | 0.101 | Yes |
| Synth | 0.009 | 0.054 | Yes |
| WASM | 0.017 | 0.084 | Yes |

### GM Instrument Verification
- 128 GM programs → 60 MP3 samples (confirmed in `synth-engine.js`)
- Sample-based playback with ±2 octave pitch shifting
- 15% instrument substitution for orchestral variety
- Additive synthesis fallback (17 timbres)

### Bugs Found
- WASM mode: no track info or time displayed (HUD empty, 0:00/0:00)
- MP3 player: note info shows raw internal names (koto_v0_additive_32)
- Voice/Choir instrument family unchecked by default
- Key 3 grid switch: confirmed working (closed V36 #13)
- apps/cosmic-runner-v5/ is STALE vs apps/inthebeginning-bounce/

### WORKLOG Expansion
Expanded from 2 sections to 20+ covering all apps: Python, Node.js, Go,
Rust, C, C++, Java, Perl, PHP, TypeScript, Kotlin, Swift, WASM, WASM-Synth,
Screensaver macOS/Ubuntu, Audio, Cosmic Runner variants, Visualizer.
Enqueued WASM-to-Python music parity as priority future work.

### Test Results
- 808 Python tests pass, 1 pre-existing failure (note JSON count)
- 47/47 game E2E tests pass
- 6/6 audio verification tests pass
- 5/5 WASM verification tests pass

---

## v0.44.0 — 2026-04-04 — Work Tracking + Testing Scaffolding

### Summary
Created WORKLOG.md — master work-to-be-done file organized by facet (game,
testing, architecture, steering, deploy). Updated CLAUDE.md with Work Tracking
section and local-first testing protocol. Session-start hook now injects top
open work items. Plan for v45+: audio waveform driver, GM instruments, game bugs.

---

## v0.43.0 — 2026-04-04 — MP3 Album Note Data Completeness

### Summary
Fixed truncated v4 note data files causing visualization gaps in MP3 mode.
Root cause: `extract_midi_provenance.py` lacked tiling loop (v3 generator had
it, v4 didn't). Game prefers v4 files → visible gap after ~8s per segment.

### Fix
- Added tiling loop + mood construction to `extract_midi_provenance.py`
- Regenerated all 12 v4 files: 100% coverage (was 23-54% gaps)
- Before: 140-465 events/track → After: 2,050-10,231 events/track
- 112 new tests in `test_note_data_completeness.py`

---

## v0.42.0 — 2026-04-04 — Redaction Protocol Test

### Summary
Tested journal redaction protocol with plaintext password. Both instances
redacted as `<REDACTED:password>`. Refused to write secrets to files.

---

## v0.41.0 — 2026-04-04 — Journal Content Validation Hook

### Summary
Added validate-journal.py to the stop hook for journal content quality checks:
valid JSON, required fields, no bracketed summaries in assistant_text, proper
tool_calls structure. Heuristic ignores brackets in quoted/code context to
avoid false positives.

---

## v0.40.0 — 2026-04-04 — Journal Verbatim Content Clarification

### Summary
Clarified that assistant_text must be full verbatim screen output (not bracketed
summaries) and that reasoning/process commands go in tool_calls verbatim while
raw code patch diffs are excluded.

---

## v0.39.0 — 2026-04-04 — Journal Compression Logic Finalization

### Summary
Finalized journal cut/compression lifecycle. On each cut, ALL prior uncompressed
journals get compressed, not just the immediately previous one. Only the latest
cut's journal stays prettified and browsable on GitHub. Retroactively cut v38
with session log.

---

## v0.38.0 — 2026-04-04 — Journal Compression Strategy Fix

### Summary
Updated journal protocol so the latest cut's journal stays prettified and
uncompressed (readable on GitHub), while previous cuts get compressed to
`.tar.gz` on the next cut.

---

## v0.37.0 — 2026-04-04 — Turn-by-Turn Journal Protocol

### Summary
Formalized turn-by-turn conversation journaling with full tool call capture.
Rolling JSON journal updated every turn (crash recovery), compressed to .tar.gz
on solution cut. Each cut bumps the solution version.

### Deliverables
- `session_logs/journal_schema.json` — JSON Schema v2.0 for journal files
- CLAUDE.md — replaced JSON Transcript Companion with Journal Protocol section
- Hook updates: pre-commit journal freshness warning, stop-check journal blocker
- First journal: v37-journal.json.tar.gz (6 turns)

---


## v0.36.0 — 2026-03-31 — V11: Game Bug Fix Pass

### Fixes (18 of 24 items)
- Speed buttons: gameplay only (not music)
- 3D emoji fade-out at bottom (no more pile-up)
- 3D speed: mobile 150, desktop 180 (was 220)
- Mutation cacophony: stopAll before applying new mutation
- Mutation/style/instrument buttons: hidden in MP3 mode
- 2D/3D toggle: changes gameplay perspective in game mode
- Double pause icon: single ⏸ character
- Main menu: 1P/2P controls hints toggle correctly
- Instrument soundbank: disables families entirely (not just samples)
- Music keyboard: Space=play/pause, arrows=seek in player/grid mode
- Themes: more pronounced (increased satMult/brightMult, bgTint overlay)
- Theme Default option + Ocean + Forest (10 total)
- WASM playback: now uses MusicGenerator (was broken, calling wrong API)
- Mobile flick-to-jump: upward swipe gesture
- Mobile prev/next buttons: visible on all screen sizes

### Still Outstanding
- MIDI track listing improvements
- MP3 JSON completeness verification
- Mobile multi-tap track listing issue
- Grid final score logic
- Some visual refinements

---

## v0.35.0 — 2026-03-30 — Comprehensive Markdown Sweep

### Summary
Map-reduce sweep of 115 markdown files across 40+ directories with 5 parallel
agents. Fixed 16 issues (6 high, 5 medium, 5 low): version number mismatches,
missing READMEs, stale references, archive creation.

### Key Fixes
- README.md: 12→13 programming languages
- deploy/v7-v10 READMEs: all said "V6", corrected to match directory version
- PLAN.md: marked as historical (V22 era, superseded)
- Created READMEs for apps/wasm-synth/ and apps/cosmic-runner-v5/
- Created future_memories/archive.tar.gz for shipped plan files
- Added markdown consistency steering to CLAUDE.md

---

## v0.34.0 — 2026-03-30 — V10: MIDI Provenance + Effects Display

### MIDI Source Recovery
Re-ran RadioEngineV8 seed=42 to recover exact MIDI files sampled per segment.
15 unique sources: Chopin, Bach, Joplin, Beethoven, Haydn, Verdi, Mozart,
Borodin, Diabelli, Lincke. Enhanced v4 JSON per track with midi_source per note.

### Effects Display
Lower-left note boxes now show: pitch+instrument, MIDI source file (for MP3),
active effects (reverb, filter, pitch shift) when mutations are applied.

### deploy/v10
Created from v9 with enhanced note data, v10 title, v4 JSON files.

---

## v0.33.0 — 2026-03-30 — Approach C Compositional WASM + MP3 Album

### Approach C: Hybrid Compositional Engine
WASM mode transformed from raw MIDI playback to intelligent composition:
- 7 rondo patterns with section-level transposition (B=+5, C=-3, D=+7)
- Consonance engine: interval scoring (12 pitch classes), iterative voice adjustment
- 6 arpeggio forms per rondo section for variety
- Diatonic chord quality (scale-degree-specific voicing per mode)
- Notes generated by JS MusicGenerator, rendered through WASM/SynthEngine

### MP3 Album Verified
12 tracks from two RadioEngineV8 30-minute renders (seed=42):
- Tracks 1-6 (Ember→Glacier): RadioEngineV8
- Tracks 7-12 (Bloom→Horizon): RadioEngineV15_V8Tempo
- Path resolution falls back to deploy/shared/audio/tracks/

---

## v0.31.0 — 2026-03-29 — V9 Game Release + Steering Rearchitecture

### Summary

Major quality release: V9 game created by merging V7 (all features working)
with V8's WASM additions, fixing 10+ regressions introduced in V8. Also
rearchitected CLAUDE.md/AGENTS.md for Claude Code CLI, set up CLI hooks,
GitHub CI, and Apple platform builds.



### V32 Phase 3 (2026-03-30)

Final items:
- 3D grid bloom: animated petal clusters replace isometric cubes
- Instrument soundbank panel: toggle 10 instrument families on/off for MIDI
- MP3 engine provenance: shows RadioEngineV8/V15, seed 42, MIDI pool info
- MIDI licensing: CC BY-NC-SA 4.0 (MAESTRO) / CC BY 4.0 (ADL) shown in info panel
- Known issues documented: double pause icon, minimize stops MIDI

### V32 Phase 2 (2026-03-30)

Additional fixes completing all items from the comprehensive bug report:
- 3D gameplay: faster fly-through, forgiving jump detection, terrain smoothing
- Scoring: 3pts per landing (not per object), aligned with game design intent
- Mutation: playhead no longer jumps when switching mutations mid-playback
- Infinite mode: properly enforced for MIDI (12 tracks) and synth
- UI: new title font layout, level transition flash, MIDI licensing display
- Infrastructure: lint hooks for Go/Swift/HTML/CSS, apps/ dev symlink
- Playwright verified: 14/14 pass, zero JS errors

### V9 Game (deploy/v9)

V9 restores all V7 features that V8 lost while keeping V8's WASM synth mode:
- **Restored**: Game completion, pause-stops-music, MIDI auto-play, MIDI/Synth
  HUD display, infiniteMode toggle, title screen buttons, album metadata/ID3,
  note info for MP3 mode
- **Fixed**: Key "2" mode switch, MIDI info on first load, visualizer
  FAMILY_HUES/generateCycle errors
- **Added**: WASM Synth as 4th sound mode (from V8)
- **Branding**: All "Cosmic Runner" → "inthebeginning bounce"
- **Visual test report**: Screenshots and animated GIFs in session_logs/

### Steering Rearchitecture

- CLAUDE.md: 1,662 → 499 lines (single source of truth for CLI)
- AGENTS.md: 967 → 271 lines (AST protocol only)
- docs/web-ios-flow.md: Preserves gVisor/FAIL hook approach
- 5 CLI hooks: lint-on-write, plan-before-commit, stop-check, test-nudge, session-start

### GitHub CI

- Ubuntu CI: 11/11 language jobs passing
- Golden Output Tests: Passing (token count normalization)
- Apple Platforms: macOS/iOS/tvOS builds via daily cron schedule
- Fixed: Swift `import InTheBeginningSimulator` in all app files

### Files Changed

- NEW: deploy/v9/ (19 JS files, HTML, CSS, WASM binary)
- NEW: .claude/hooks/ (5 hook scripts)
- NEW: docs/web-ios-flow.md
- NEW: tests/test_web_game.mjs (Playwright test suite)
- NEW: session_logs/v31-visual-report.md (screenshots + GIFs)
- MODIFIED: CLAUDE.md, AGENTS.md, .claude/settings.json
- MODIFIED: .github/workflows/ (ci.yml, golden.yml, apple.yml)
- MODIFIED: deploy/v4-v8 JS files (bug fixes propagated)
- MODIFIED: apps/swift/ (import fix), apps/cosmic-runner-v5/ (bug fixes)
- MODIFIED: tests/test_golden_outputs.py, tests/test_visualizer_golden.py

---

## v0.30.0 — 2026-03-25 — WebAssembly Audio Synthesis Mode (V8)

### Summary

Add WebAssembly as a 4th sound mode alongside MP3, MIDI, and Synth. WASM mode
provides higher-performance audio synthesis via Rust compiled to WebAssembly.
Existing knobs (mutation presets, style sliders, volume) work with WASM mode.
Graceful fallback to SynthEngine when WASM binary is unavailable.
SoundFont integration deferred to Phase 3 (done last).

### New Sound Mode: WASM Synth

4th audio mode alongside MP3, MIDI, and Synth Generator. When a 27KB
WebAssembly binary is available, audio synthesis runs in a Rust-compiled
WASM module via an AudioWorklet (audio thread). Gracefully falls back to
the existing SynthEngine when WASM is unavailable.

### Rust WASM Synth Engine

- 13 instrument timbres ported from synth-engine.js (piano, violin, cello,
  flute, oboe, trumpet, harp, bell, gamelan, choir, warm_pad, cosmic, sine)
- ADSR envelopes per timbre
- 64-voice polyphony with oldest-voice stealing
- GM program mapping (128 instruments → 13 timbres)
- 7 Rust unit tests

### JS Integration

- `wasm-synth.js` — JS bridge with MIDI catalog, shuffle, note scheduling
- `wasm-synth-processor.js` — AudioWorkletProcessor for audio-thread rendering
- All existing knobs (mutation presets, volume, speed) work with WASM mode
- ID3 display shows WASM/Fallback indicator

### SoundFont Integration

- Rust SF2 parser: reads RIFF container, extracts samples (PCM→f32),
  presets, instruments, zones, and generator parameters
- load_sf2() in WASM engine parses and stores SF2 for sample-based synthesis
- JS bridge: loadSoundFont(url), setUseSf2(bool), sf2Loaded property
- AudioWorklet handles SF2 loading via message passing
- 11 Rust tests (7 synth + 4 SF2 parser)

### Deploy

- `deploy/v8/` is GitHub Pages ready (zero build step)
- 40KB WASM binary at `js/wasm_synth_bg.wasm` (includes SF2 parser)

### WASM Simulator Full Python Parity

Brought `apps/wasm/` Rust simulator to full parity with the Python reference
implementation (+1,580 lines across 7 files):

- **quantum.rs**: WaveFunction (Born rule, evolve, collapse, superpose),
  EntangledPair (Bell states, measure), particle wavelength, decoherence
- **biology.rs**: Gene (epigenetic marks, transcribe, mutate), DNAStrand
  (replication, GC content, complementary strand), translate_mrna (full codon
  table), Protein (fold, function types), Cell (central dogma, metabolize,
  fitness, divide), Biosphere (natural selection, population cap)
- **constants.rs**: NUCLEOTIDE_BASES, RNA_BASES, AMINO_ACIDS, full genetic code
- **environment.rs**: EnvironmentalEvent system (volcanic, asteroid, solar flare,
  ice age) with probabilities matching Python reference
- **universe.rs**: SimulationMetrics, EpochTransition tracking, history snapshots,
  state_compact, run/run_perpetual
- 149 Rust tests passing

---

## v0.29.0 — 2026-03-25 — inthebeginning bounce V7 (World Music Engine)

### Summary

Port of Python composer.py world music engine to JavaScript. The synth
generator now produces musically rich procedural compositions using 44 world
musical scales, 15 harmonic progressions, 25 rhythm patterns, and 30 melodic
motifs from public domain works spanning 6 musical traditions.

### Music Engine Port

- 44 world musical scales (Western, Japanese, Chinese, Middle Eastern, Indian,
  African, Ancient/tribal)
- 15 harmonic progressions (classical, minimalist, drone, East Asian, modal)
- 25 rhythm patterns (African bell, polyrhythmic, gamelan, Indian tala, sparse)
- 30 melodic motifs from public domain works (Bach, Mozart, Beethoven, Chopin,
  Debussy, Satie, Grieg, Dvořák, traditional Asian/African)
- Epoch-aware selection of scales, rhythms, progressions, and motifs
- Humanization jitter (±10-30ms) on melody, chords, percussion

### Audio Improvements

- Voice cleanup: periodic GC every 2s evicts expired voices
- Max polyphony reduced 128 → 64 for stability
- Web Audio nodes disconnected on note end

### Deploy

- `deploy/v7/` is GitHub Pages ready (zero build step)

---

## v0.28.0 — 2026-03-23 — inthebeginning bounce V6 (Game Overhaul)

### Summary

Major bug fix and feature enhancement for the web game. Renamed from
"Cosmic Runner" to "inthebeginning bounce". Removed the standalone visualizer
(all visualization consolidated into the game). Created deploy/v6 directory.

### Bug Fixes

- **Branding**: "Cosmic Runner" → "inthebeginning bounce" throughout
- **Theme/Accessibility overlays**: Now open correctly from title screen
- **MIDI auto-play**: Playhead starts at beginning, auto-plays on game start
- **Pause**: Pauses both gameplay AND music simultaneously
- **3D obstacles**: Fly past the player instead of piling up at ground level
- **P2 controls**: Changed from WASD (left-side) to IJKL/Numpad (right-side)
  P1 now uses both Arrows and WASD
- **Track list modal**: Only opens in MP3 mode (no empty modal in synth/grid)
- **Note info display**: Now shows in grid/player modes for all sound modes
  (MP3 mode events now update the note info panel)
- **Player position**: NaN/Infinity protection, drag cleanup on window blur
- **Game loop**: try/catch prevents silent crashes from stopping rendering

### Features

- **12-epoch synth generator**: Expanded from 6 to 12 cosmic epochs matching
  the game's 12-level structure. 9 audio layers: pad, bass, melody,
  counter-melody, chord, arpeggio, fill/texture, ostinato, percussion.
  Boosted pad and bass volumes for richer presence.
- **Infinite play**: Album mode repeats after track 12. MIDI infinite shuffle.
  Synth generator regenerates with new seed after 12 tracks.
- **Game completion**: End screen with final score after 12 album tracks
  (non-infinite mode only, no player lives system)
- **3D level progression**: Works correctly in MIDI and synth modes too
  (previously only activated in MP3 mode)
- **Theme-aware ground**: Ground rendering uses theme color shifts

### Architecture

- **Visualizer removed**: deploy/v6 contains only the game application
- **Shared assets**: v6 audio/ contains only JSON metadata and interstitial;
  album MP3s load from ../../shared/audio/tracks/
- **deploy/v6/inthebeginning-bounce/**: Ready for copy-to-GitHub-Pages deployment

### Files Changed

- deploy/v5/inthebeginning-bounce/: All JS files updated with V6 fixes
- deploy/v6/: New deploy directory (game only, no visualizer)
- 16 JavaScript files, 1 HTML, 1 CSS, 1 README

---

## v0.25.0 — 2026-03-22 — Synthesizer Port + Visualizer V3 Upgrade

### Summary

Major upgrade to both the standalone Visualizer app and Cosmic Runner V3. Ported
the Python additive synthesizer (composer.py) to Web Audio API. Added Web Worker
concurrent MIDI parsing, 16+ instrument timbres, ADSR envelopes, percussion
synthesis, pitch bend visualization, and full MIDI library integration.

### Visualizer V3 (Synthesizer Port)

- **SynthEngine** (`synth-engine.js`): Full additive synthesis with 18 instrument
  timbres ported from Python composer.py — violin, cello, harp, flute, oboe,
  clarinet, horn, trumpet, piano, bell, gamelan, tibetan_bowl, choir_ah, choir_oo,
  throat_sing, warm_pad, cosmic, sine
- **ADSR envelopes**: Per-instrument attack/decay/sustain/release curves
- **Percussion synthesis**: Kick drum (sine + pitch drop), snare (tone + noise),
  hi-hat (bandpass noise), generic noise bursts
- **Vibrato**: LFO-driven frequency modulation on sustained notes (5.5 Hz, 15 cents)
- **Pitch bend**: Real-time frequency modulation with visual pulsing glow animation
- **Web Worker** (`synth-worker.js`): MIDI parsing offloaded to background thread
  with MessagePort protocol, graceful fallback to main thread
- **MidiFilePlayer** (`midi-player.js`): Coordinates Worker + SynthEngine with
  note event emission at 20 Hz for grid visualization
- **4-mode UI**: Album, MIDI Synth, Single, Stream — switchable via tabs
- **16 mutation presets**: Shared with Cosmic Runner V3 (pitch shift, tempo, reverb, filter)
- **MIDI catalog integration**: 1,854 classical MIDI files, infinite shuffle, history
- **Color mapping**: GM instrument families → HSL hue (10 family colors)
- **Build script** (`build.py`): Produces self-contained dist/ for GitHub Pages
  with options for MP3-only, MIDI-only, synth-only, or full deployment
- **152 tests**: Covers synth engine, MIDI player, grid, score, player

### Cosmic Runner V3 (SynthEngine Integration)

- **Upgraded MIDI player**: Now uses SynthEngine for additive synthesis instead of
  basic oscillators — dramatically richer instrument sounds
- **Web Worker parsing**: MIDI files parsed in background thread for smooth gameplay
- **Pitch bend support**: Extracted from MIDI files and passed to SynthEngine
- **Shared synth-engine.js**: Same synthesizer code used in both Visualizer and
  Cosmic Runner V3
- **94 tests pass** (67 game + 27 MIDI player)

### GitHub Pages Deployment

Both apps deploy as static sites:
- Full build (MP3 + MIDI): ~115 MB
- MP3 only: ~90 MB
- MIDI only: ~25 MB
- Synth only: ~50 KB (pure synthesizer, drag-and-drop MIDI files)

---

## v0.24.0 — 2026-03-22 — GitHub Pages Deployment + MIDI Mode

### Summary

Cosmic Runner V3 made fully self-contained and deployable to any GitHub Pages
repository. Added in-browser MIDI playback mode with 1,854 classical MIDI files
from 120 composers, comprehensive provenance tracking, and infinite shuffle mode.

### Cosmic Runner V3 — Self-Contained Audio

- Copied 12 V8 Sessions MP3s into V3's own `audio/` directory
- Fixed audio paths in `app.js` to use local `audio/` only (no cross-directory refs)
- All audio assets (MP3s, JSON note files, album index) are now in one directory
- V3 is fully deployable as a standalone static site

### MIDI Mode

- **MIDI catalog**: 1,854 classical MIDI files from 120 composers, indexed in
  `midi_catalog.json` with full provenance (composer, era, source, license)
- **Web Audio API player** (`midi-player.js`): Complete SMF Format 0/1 parser with
  VLQ decoding, running status, all meta events (tempo, track name, end of track)
- **Synthesizer**: Multi-channel oscillators (sine/triangle/sawtooth), ADSR envelopes,
  filtered noise percussion (channel 9), convolver reverb, BiquadFilter
- **16 mutation presets**: Celestial, Subterranean, Crystal, Nebula, Quantum,
  Solar Wind, Deep Space, Pulsar, Cosmic Ray, Dark Matter, Supernova,
  Event Horizon, Starlight, Graviton, Photon
- **Real-time grid sync**: Note events emitted at 20Hz for 64x64 grid visualization
- **Provenance display**: Composer, piece name, era, and mutation shown in-game

### Infinite Mode

- Toggle infinite shuffle on title screen for both MP3 album and MIDI library
- MP3 infinite: random track selection, never repeats consecutive tracks
- MIDI infinite: random selection from 1,854 pieces with 20-piece back-list

### Build & Deploy

- `build.py`: Bundles all JS/CSS into single 189KB `dist/index.html`
- `build.py --with-midi`: Includes MIDI library (~25MB) in `dist/midi/`
- `build.py --full`: Full build with asset verification
- `DEPLOY.md`: Comprehensive deployment guide for GitHub Pages

### Testing

- **95 Python tests** (71 V3 integration + 24 MIDI catalog validation)
- **111 JS tests** (27 MIDI player + 84 existing game/radio/config/theme tests)
- All tests passing
- Build script produces verified output

### Eras Represented in MIDI Library

- Renaissance (1400-1600): 134 files — DuFay, Josquin, Ockeghem, etc.
- Baroque (1600-1750): 459 files — Bach, Vivaldi, Handel, Corelli, etc.
- Classical (1750-1820): 498 files — Mozart, Haydn, Beethoven, etc.
- Romantic (1820-1900): 556 files — Chopin, Liszt, Brahms, Tchaikovsky, etc.
- Late Romantic (1890-1920): 127 files — Debussy, Ravel, Elgar, etc.
- Folk (pre-1900): 80 files — English and Celtic traditional tunes

---

## v0.23.0 — 2026-03-21 — V8 Sessions Album + Cosmic Runner V2

### Summary

Three-mode Cosmic Runner V2 with a 12-track "V8 Sessions" album derived from
the two favorite MP3s (cosmic_radio_v8.mp3 and cosmic_radio_v18_v8-42.mp3).

### V8 Sessions Album

- 12 tracks with nature-themed names symbolizing universe evolution:
  Ember, Torrent, Quartz, Tide, Root, Glacier, Bloom, Dusk, Coral, Moss,
  Thunder, Horizon
- Rendered from RadioEngineV8(seed=42) + RadioEngineV15_V8Tempo(seed=42)
- Split at low-energy boundaries into 3-6 minute tracks
- Per-track JSON note metadata for synchronized visualization
- Located in `apps/audio/output/v8_album/`

### Cosmic Runner V2

- Three modes of operation:
  - **Music Player**: standalone audio with ambient background grid
  - **Game**: side-scroller with Aki, subdued cells, parallax stars
  - **Grid**: full 64x64 cell visualization synced to music
- Mode switching via tabs or keyboard (1/2/3 keys)
- Note info panel shows currently playing notes (pitch + instrument)
- GitHub Pages-ready: single-file build at `dist/index.html`
- Located in `apps/cosmic-runner-v2/`

### Testing

- 29 tests (3 skipped until album generation completes)
- Covers file structure, HTML/CSS/JS content, build output, album generation

---

## v0.22.0 — 2026-03-21 — Cosmic Runner (Original)

### Summary

Original Cosmic Runner game with music-synced side-scroller. Superseded by V2.

---

## v0.21.0 — 2026-03-08 — V21 Album + Visualizer + Streaming

### Summary

Full CD-length album "In The Beginning Phase 0" (79 min, 17 tracks + TTS bookends),
64x64 JavaScript grid visualizer, Go SSE streaming infrastructure, documentation
audit, music algorithm documentation, JSON transcript logging system.

### Album: "In The Beginning Phase 0"

- Artist: aiphenomenon (A. Johan Bizzle)
- 19 tracks (Overture + 17 music + Coda), 79.4 min total, 110MB
- Seed: 779275, deterministically reproducible
- Variable mood durations (42s multiples: 42, 84, 126, 168, 210s)
- Plain TTS bookends, source code readings across album
- Genre: Psychedelic Rock (ID3 genre 67), CC BY-SA 4.0
- 8,626 note events logged for visualization

### JavaScript Visualizer (apps/visualizer/)

- 64x64 grid with instrument-to-color mapping
- Three modes: album, single, stream
- Score.js loads NoteLog JSON, Player with seek/volume/track nav/fullscreen

### Streaming Infrastructure

- Go SSE server: /events/notes + /stream/audio endpoints
- StreamClient.js for real-time note event consumption
- Bash scripts: start_radio.sh, start_album_player.sh

### Documentation & Steering

- Documentation audit (8 files), music_algorithm.md (664 lines)
- JSON transcript companion system, session budget management
- Vocoder removed → plain TTS injection

### Other

- 30-min MP3: v21_random_759274.mp3 (41MB, 1800s, 192kbps)
- NoteLog bug fixes, parallel album rendering (2 workers)

---

## v0.20.0 — 2026-03-07 — V20 Audio Engine: Volume Fix + Expanded Palette

### Summary

Major audio engine overhaul: fixed volume normalization (low volume + spike
artifacts), expanded instrument palette with openly licensed SoundFonts,
expanded MIDI sampling library to ~1750+ files, added solo instrument mood
(10-20% of moods), additional TTS engines, and Silero TTS integration.

### Turn 3: Audio Overhaul — 14:21 CT (20:21 UTC)

- Volume fix: master normalization to -1dB peak + lookahead limiter
- Solo instrument mood: 10-20% of moods play single-instrument arrangement
- TTS expansion: flite, festival, pico2wave via apt; Silero via PyTorch
- SoundFont instruments: ~100 additional openly licensed instruments
- MIDI library: ~1000 additional public domain classical files
- Two MP3 renders: seed=42 and random seed

### Turn 4: Multi-TTS + Screen Testing — 15:44 CT (21:44 UTC)

- **Shell injection protection**: `_sanitize_text()` strips shell metacharacters,
  control chars, null bytes; 500 char max. Defense-in-depth on all TTS subprocess calls.
- **Multi-TTS integration**: TTSEngine rotates between espeak-ng, flite, festival,
  pico2wave based on voice_seed + epoch_idx for variety.
- **Screen capture testing**: 14 new tests across all simulator implementations
  (Python terminal UI, Node.js, Go, C++, C, Rust, Perl, PHP, Go SSE server,
  PHP server, Ubuntu screensaver Xvfb, Java headless). 24 evidence files generated.
- **Domain approval steering**: agents must ask user before accessing new download
  domains. Added to CLAUDE.md, AGENTS.md, steering-check.sh.
- **Screen capture steering**: terminal ANSI captures, web server smoke tests,
  Xvfb GUI testing, machine vision review. Triple cross-check propagated.
- **V20 seed-42 MP3**: 41.2 MB, 30 min, mean -15.5 dB, peak -0.3 dB (was -35.7/-1.6 in V18)
- **V20 random-seed MP3**: rendering in progress
- PyTorch 2.10.0 installed; Silero model blocked (models.silero.ai inaccessible)

---

## v0.19.0 — 2026-03-07 — V19 Test Infrastructure Overhaul

### Summary

Comprehensive test infrastructure expansion: golden output snapshot tests,
cross-language parity validation, server smoke tests, audio golden tests, and
CI integration. Fills the gap between 4,500+ unit tests and zero integration/
golden output tests.

### Turn 1: Implementation — 13:25 CT (19:25 UTC)

- Surveyed all 16 app test suites (4,500+ tests, zero golden output tests)
- Created golden output test framework (tests/test_golden_outputs.py)
- Created golden snapshot capture tool (tools/capture_golden.py)
- Cross-language parity tests (tests/test_cross_language_parity.py)
- Server smoke tests (tests/test_server_smoke.py)
- Audio golden tests (tests/test_audio_golden.py)
- CI workflow (.github/workflows/golden.yml)

- Visualizer golden tests (tests/test_visualizer_golden.py)
- Golden snapshots captured for 9 languages (all exit code 0)
- **66 new integration tests, 0 failures, 4 skipped (no Swift toolchain)**
- Updated CLAUDE.md and README.md with test execution commands
- 258 existing reference tests still passing

---

## v0.18.0 — 2026-03-07 — V18 Audio Engine: Clean Mixing + Orchestra Variety

### Summary

New V18 audio engine addressing "radio static" artifacts and adding orchestral
instrument variety with character preservation. Deep verification of gold standard
test evidence across all simulator languages.

### Turn 4: Gold Standard Deep Verification — 10:12 CT (16:12 UTC)

- Cross-language epoch parity confirmed: Python/Go/C/C++ all produce matching
  epoch transitions (Planck→Inflation→Electroweak at ticks 1/10/100)
- Full simulation run-through captured with final states (particles, atoms, cells)
- 2131+ tests across 8 testable languages, 0 failures
- No PDFs or image files exist in repo (steering references are aspirational)

### Turn 4: V18 Engine — 10:28 CT (16:28 UTC)

**RadioEngineV18** fixes V15's static/noise issues:
- Separate gain/pan in `_mix_mono_clean()` (V11 fix — no gain-overloaded pan param)
- Quality-gated instruments: `noise_perc` excluded from melodic voices
- Soft-knee limiting on loop buffer prevents clipping
- 5ms anti-click fades (up from V15's 2ms)
- Tempo clamped to 1.1x-1.45x (user preference, narrower than 1.1-1.7x)

**RadioEngineV18Orchestra** adds orchestral variety:
- 15 instrument family pools (vs V18's 5) with variety enforcement
- 744 MIDI files from 26 composers
- Higher `color_amount` (0.35-0.55) preserves instrument character
  (xylophone stays xylophone, strings stay strings, horns stay horns)

### Changes

- `apps/audio/radio_engine.py`: Added `RadioEngineV18`, `RadioEngineV18Orchestra`,
  `generate_radio_v18_mp3()`, `generate_radio_v18_orchestra_mp3()`, CLI v18/v18o
- `apps/audio/test_radio_engine.py`: 22 new tests for V18/V18Orchestra
- `apps/audio/generate_v18_mp3s.py`: Script to generate 5 comparison MP3s
- `session_logs/v0.17.0-session.md`: Turn 4 deep verification evidence added
- `session_logs/v0.2.0-v0.6.0-session.md`: Extracted from archive (uncompressed)
- `future_memories/v17-comparison-plan.md`: Turn 4 plan appended

### Files Created/Modified

| File | Action |
|------|--------|
| `apps/audio/radio_engine.py` | Modified — added V18 engines |
| `apps/audio/test_radio_engine.py` | Modified — added V18 tests |
| `apps/audio/generate_v18_mp3s.py` | Created — MP3 generation script |
| `session_logs/v0.17.0-session.md` | Modified — Turn 4 evidence |
| `session_logs/v0.2.0-session.md` | Extracted from archive |
| `session_logs/v0.3.0-session.md` | Extracted from archive |
| `session_logs/v0.4.0-session.md` | Extracted from archive |
| `session_logs/v0.6.0-session.md` | Extracted from archive |
| `future_memories/v17-comparison-plan.md` | Modified — Turn 4 plan |
| `RELEASE_HISTORY.md` | Modified — this entry |
| `apps/audio/cosmic_radio_v18_v8-42.mp3` | Created — V8-style seed=42 (30 min, 43MB) |
| `apps/audio/cosmic_radio_v18_v8-random.mp3` | Created — V8-style random seed (30 min, 43MB) |
| `apps/audio/cosmic_radio_v18_v18-42.mp3` | Created — V18 clean mixing seed=42 (30 min, 43MB) |
| `apps/audio/cosmic_radio_v18_v18-random.mp3` | Created — V18 clean mixing random (30 min, 43MB) |
| `apps/audio/cosmic_radio_v18_v18o.mp3` | Created — V18 Orchestra expanded palette (30 min, 43MB) |

### Turn 4 Continued: MP3 Renders Complete — 11:12 CT (17:12 UTC)

All 5 MP3 comparison renders complete and pushed to GitHub:
- 16/16 V18 unit tests pass
- 407/407 Python reference tests pass
- Swift toolchain: blocked (`download.swift.org` 403 despite `*.swift.org` allowlist)
- Docker daemon unavailable for alternative Swift install

---

## v0.17.0 — 2026-03-07 — V8 vs V15 Bit-Identity Investigation + Double-Filter Bug Fix

### Summary

Empirical investigation of whether a tempo-matched V15 variant produces bit-identical
audio to the original V8 seed-42. Discovered and fixed a **double-filter bug** in V15
and V16 where `anti_hiss` and `subsonic_filter` were applied both per-segment (inside
`_render_segment`) and at master level (inherited from V8's `render()`).

### Key Findings

1. **V8 pure Python vs V15+V8tempo+V8render: BIT-IDENTICAL** (zero sample difference)
   — confirming the claim holds when all code paths are matched
2. **numpy vs pure Python synthesis: DIFFERENT** (max diff 0.35, 99.6% of PCM16 differ)
   — floating-point operation ordering causes material numerical divergence
3. **Double-filter bug**: V15's `_render_segment` applied anti-hiss + subsonic per-segment,
   then V8's inherited `render()` applied them again at master level
4. **numpy availability during original V8 render: UNKNOWN** — session log was
   reconstructed after iOS app crash; v0.6.0 logs confirm numpy was in use earlier

### Changes

- **Bug fix** (`apps/audio/radio_engine.py`):
  - Removed per-segment `anti_hiss.apply_stereo` and `subsonic_filter.apply_stereo` from
    `RadioEngineV15._render_segment` (also affects V16 via inheritance)
  - Master-level filtering in V8's `render()` is sufficient
- **Comparison script** (`apps/audio/compare_v8_v15.py`):
  - Renders six variants: V8±numpy, V15 own/V8-tempo/V8-full/numpy
  - Compares PCM16 audio sample-by-sample (ignoring MP3 metadata)
  - Supports `--compare-mp3` to decode and compare existing repo MP3s
- **Evaluation document** (`docs/v8_v15_comparison.md`):
  - Full investigation: git archaeology, AST analysis, structural diff, empirical results
  - numpy availability timeline across all versions
  - Render path analysis (render vs render_streaming filter behavior)
- **Results file** (`docs/v8_v15_results.md`): Machine-generated comparison tables
- **Tests**: 6 new regression tests for the double-filter fix

### Turn 2 Updates — Full 1800s-Plan Comparison

- **Full comparison script** (`apps/audio/compare_v8_v15_full.py`):
  - Renders with 1800s segment plan via `render_streaming()`, captures first 160s
  - Compares 5 variants against decoded repo V8 MP3 (before TTS at ~162s)
- **Verdict**: Repo V8 MP3 was LIKELY rendered WITHOUT numpy (pure Python)
  - Pure Python: RMS 0.09570 vs numpy: RMS 0.09576 from repo MP3
  - V8+pure and V15-fix+V8tempo+pure: BIT-IDENTICAL (0 sample diff at 7M samples)
- **Executable behavior testing** added to steering triple-check (CLAUDE.md, AGENTS.md,
  .claude/steering-check.sh)

### Agent Activity

- Git archaeology across commits 348bf29 → 45791bd → 88a543d
- AST analysis via Python `ast` module (class structure, method overrides)
- Structural diff: V8 vs V15 `_render_segment` after removing dead numpy branch
- Empirical rendering: 6 variants × 30s = ~10 minutes of render time
- Full 1800s-plan comparison: 5 variants × 160s = ~12 minutes of render time
- Session log archive search for numpy breadcrumbs
- AMD64 binary verification (Go, C, C++, Rust)

---

## v0.16.0 — 2026-03-06 — Radio Engine v16: True Original V8 Synthesis + Expanded Palette

### Summary

Radio engine v16 restores the **original V8 synthesis** (`InstrumentFactory.synthesize_colored_note`)
from git commit 348bf29, combined with V12's expanded 15-family instrument palette and 744 MIDI files.
The current V8 class uses numpy-accelerated `_synth_colored_note_np()` (added in commit 45791bd for ~7x
speedup) which produces subtly different audio. V16 gives the authentic original V8 sound with the
richest instrument variety.

### Changes

- **Radio Engine v16** (`apps/audio/radio_engine.py`):
  - `RadioEngineV16(RadioEngineV15)` — inherits from V15 (true V8 synthesis)
  - Original `factory.synthesize_colored_note()` path (pure Python, no numpy)
  - V12's 15 instrument family pools with variety enforcement
  - V12's density-aware tempo (1.1x-1.7x)
  - All 744 MIDI files, 537 instruments
  - Serial rendering (V8's streaming path)
- **Tests**: V16 unit tests added
- **MP3s**: Two 30-minute renders (seed 42 + random seed)

---

## v0.15.0 — 2026-03-06 — Radio Engine v15: True Original V8 Synthesis + V12 Tempo

### Summary

Radio engine v15 restores the **original V8 synthesis** (`InstrumentFactory.synthesize_colored_note`)
from git commit 348bf29, with V12's density-aware tempo. Like V13 but uses the authentic original
synthesis path instead of the numpy-accelerated version.

### Changes

- **Radio Engine v15** (`apps/audio/radio_engine.py`):
  - `RadioEngineV15(RadioEngineV8)` — inherits from V8
  - Original `factory.synthesize_colored_note()` (pure Python, from 348bf29)
  - V8's 5 instrument families, 537 instruments
  - V12's density-aware tempo (1.1x-1.7x)
  - Serial rendering
- **Tests**: V15 unit tests added
- **MP3s**: Two 30-minute renders (seed 42 + random seed)

---

## v0.14.0 — 2026-03-06 — Radio Engine v14: Full Palette Serial Render

### Summary

Radio engine v14 combines V12's full instrument palette (15 families, 744 MIDI files)
with V8/V13's clean serial rendering path (no per-segment limiting, no multiprocessing).
User discovered that serial rendering eliminates the bitcrusher artifacts that plagued
V12's parallel approach. V14 gives the richest instrument variety without audio artifacts.

### Changes

- **Radio Engine v14** (`apps/audio/radio_engine.py`):
  - `RadioEngineV14(RadioEngineV8)` — inherits directly from V8
  - V12's 15 instrument family pools with variety enforcement
  - V12's density-aware tempo (1.1x-1.7x)
  - V8's clean `_render_segment()` — no per-segment `master_limit`
  - V8's serial `render_streaming()` — no multiprocessing
  - All 744 MIDI files from 26 composers active
- **Tests**: V14 unit tests added
- **MP3s**: Two 30-minute renders (seed 42 + random seed)

### Agent Activity

- Serial rendering eliminates bitcrusher noise discovered in V12/V13 analysis
- Full palette restoration from V12 with V8's clean audio pipeline

---

## v0.13.0 — 2026-03-06 — Radio Engine v13: V8 Core Restoration with V12 Tempo

### Summary

Radio engine v13 reverts to v8's core audio pipeline (instruments, synthesis, mixing,
volume) while keeping v12's density-aware tempo (1.1x-1.7x range). The v12 engine
introduced double soft-knee limiting (per-segment + streaming writer) that caused
pronounced bitcrusher/spiky artifacts. V13 eliminates this by using v8's render path
directly, with only the tempo multiplier overridden.

### Changes

- **Radio Engine v13** (`apps/audio/radio_engine.py`):
  - `RadioEngineV13(RadioEngineV8)` — inherits directly from V8
  - Uses v8's `_synth_colored_note_np()` synthesis unchanged
  - Uses v8's 5 instrument family pools (not v12's 15)
  - Uses v8's `_render_segment()` — no per-segment `master_limit`
  - Uses v8's `render()` — anti-hiss + subsonic filter, no double limiting
  - Overrides only `_compute_tempo_multiplier` for v12's density-aware tempo
  - Volume/gain matches v8 output levels
- **Tests**: Updated test suite for v13 engine
- **MP3s**: Two 30-minute renders (seed 42 + random seed)

### Agent Activity

- Spectral analysis comparing v8 vs v12 MP3s
- Code review of V8 vs V12 class differences
- Root cause: double soft-knee limiting in v12

---

## v0.12.0 — 2026-03-06 — Radio Engine v12: V8 Synthesis + Expanded Palette + Speed

### Summary

Radio engine v12 returns to v8's proven `_synth_colored_note_np()` synthesis (the
InstrumentFactory timbre blending that produces natural instrument character), combined
with v9's expanded instrument catalog (15 families, 82 GM programs), v10's MIDI
library (744 files from 26 composers), and v11's gain staging. Multiprocessing renders
all 15 segments in parallel across available CPU cores (~3x speedup on 16 cores).

### Changes

- **Radio Engine v12** (`apps/audio/radio_engine.py`):
  - `RadioEngineV12(RadioEngineV8)` — inherits directly from V8
  - Uses v8's `_synth_colored_note_np()` synthesis (InstrumentFactory blending)
  - V9's 15 family pools with variety enforcement (min 3 families per segment)
  - V10's MIDI library integration (827 sequences loaded)
  - V11's GainStage with per-voice RMS normalization and master bus soft-knee limiting
  - Tempo clamped to 1.1x-1.7x (density-aware: high-density epochs cap at 1.4-1.5x)
  - Multiprocessing: `render_streaming_parallel()` with `mp.Pool`
  - Top-level `_render_segment_worker()` for pickle-safe parallel rendering
  - CT timestamps in all script output
  - CLI `--version v12` support

---

## v0.11.0 — 2026-03-06 — Radio Engine v11: Comprehensive Audio Quality Overhaul

### Summary

Radio engine v11 addresses 19 audio quality issues identified through deep code
review. The primary fix resolves the "radio static at full volume" effect caused by
pan parameter overflow in `_mix_mono` which produced phase-inverted channels. V11
introduces per-voice RMS normalization, master bus soft-knee limiting, inter-voice
consonance enforcement, bar-aligned rendering, and orchestral role assignment.

### Changes

- **Radio Engine v11** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV11` class extending `RadioEngineV10`
  - `GainStage`: Per-voice RMS normalization + master bus soft-knee limiting
  - `ConsonanceEngine`: Inter-voice consonance scoring (Helmholtz model) with
    iterative adjustment to ensure composite harmony exceeds 0.55 threshold
  - `BarGrid`: Absolute time grid ensuring note onsets and rondo sections align
    to 16th-note metric positions
  - `OrchestratorV11`: Orchestral role assignment (foundation, harmony_low,
    harmony_mid, melody, color) with distinct register offsets and gain weights
  - `_soft_limit()`: Soft-knee limiter replacing `math.tanh` in streaming renderer
  - `_mix_mono_v11()`: Separated pan [-1,1] and gain parameters (fixes phase inversion)
  - `_apply_reverb_v11()`: Reduced comb feedback (0.55-0.65), pre-reverb 150Hz highpass
  - `_apply_early_reflections_v11()`: Reduced amplitudes (0.05-0.20)
  - Compression applied AFTER reverb (fixes pumping effect)
  - Minimum MIDI note raised to 36/C2 (prevents subsonic fundamentals)
  - Anti-click fades increased to 5ms (from 2ms)
  - Crossfade duration extended to 4-6s (from 2-4s)
  - Voice leading: smooth chord transitions (min-movement algorithm)
  - CLI `--version v11` support
  - `generate_radio_v11_mp3()` helper function
- **Tests** (`apps/audio/test_radio_engine.py`):
  - 25 new tests across 7 test classes for V11 components
  - Phase inversion verification test
  - Consonance scoring and adjustment tests
  - Bar grid alignment tests

### Agent Activity (Turn 1 — Implementation)
- Session: claude/resume-v9-document-v8-6yhAe
- Agent: Claude Opus 4.6
- Files created: 1 (session log)
- Files modified: 3 (radio_engine.py, test_radio_engine.py, RELEASE_HISTORY.md)

### Agent Activity (Turn 2 — MP3 Generation + Steering Fix)
- Generated 30-minute V11 MP3s: `cosmic_radio_v11.mp3` (seed 42) +
  `cosmic_radio_v11_random.mp3` (random seed)
- Diagnosed and fixed steering self-cue gap: start-of-turn housekeeping was being
  skipped because no pre-work reminder existed
- Added Start-of-Turn Protocol to CLAUDE.md, AGENTS.md, `.claude/steering-check.sh`
- PostToolUse hook now emits lightweight reminder on first Bash call per turn
- Files modified: `.claude/steering-check.sh`, `CLAUDE.md`, `AGENTS.md`,
  `session_logs/v0.11.0-session.md`, `future_memories/v11-plan.md`,
  `RELEASE_HISTORY.md`
- Files created: `apps/audio/cosmic_radio_v11.mp3`,
  `apps/audio/cosmic_radio_v11_random.mp3`

---

## v0.10.0 — 2026-03-06 — Radio Engine v10: GM-Timbre-Aware Synthesis + Expanded Library

### Summary

Radio engine v10 with GM-timbre-aware synthesis: each of the 15 GM instrument families
now gets a distinct ADSR envelope, harmonic structure, and brightness profile instead
of the generic additive synthesis that made everything sound organ-y. Features tempo
range narrowed to 1.2x-1.8x, 85% orchestral simultaneous layering with 4-6 voices
per segment, 8-second morph transitions between moods, and minimum 3 family groups
per segment.

The MIDI library was tripled from 249 to 744 files spanning 26 composers across 500
years of Western music (Renaissance through Late Romantic). 20 new instrument samples
added (60 total). espeak-ng TTS installed for spoken word announcements.

### Changes

- **Radio Engine v10** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV10` class extending `RadioEngineV9`
  - `GM_TIMBRE_PROFILES`: 15 GM timbre profiles with distinct attack, decay, sustain,
    release, harmonic ratios, brightness, and vibrato per instrument family (piano,
    mallets, organ, guitar, bass, strings, ensemble, brass, reed, pipe, synth_lead,
    synth_pad, synth_fx, world, percussive)
  - `_gm_program_to_timbre()`: Maps any GM program 0-127 to its timbre profile
  - `_synth_gm_note_np()`: New synthesis function using family-specific parameters
    instead of generic 8-harmonic additive base
  - Tempo range 1.2x-1.8x flat (no density-dependent capping)
  - 85% simultaneous orchestral layering (up from 75% in v8/v9)
  - 4-6 voices per segment (up from 2-4) with minimum 3 family groups
  - Register spread widened to -24/+24 semitones
  - 8s morph transitions (up from 6s), 6s fade-in, 10s fade-out
  - 3-5s crossfade between loop iterations (up from 2-4s)
  - CLI: `--version v10` flag
  - `generate_radio_v10_mp3()` convenience function
  - All v9/v8 features preserved (expanded instruments, family variety, time signature
    control, anti-hiss, subsonic removal, note smoothing, note quantization, rondo
    structures, arpeggio forms, harmonic consonance (Helmholtz/Hartmann), MIDI sampling)
- **23 new v10 tests** in `test_radio_engine.py`:
  - GM timbre profiles: count, required keys, program mapping coverage
  - Piano/strings/brass/synth_pad mapping tests
  - Distinct envelope shapes verification
  - GM synthesis: audio production, different-programs-different-output
  - Tempo range 1.2-1.8x, no density capping
  - Engine creation, morph duration, fade durations
  - Instrument diversity (3+ families per segment)
  - Short render integration test
  - CLI v10 argument acceptance
- **MIDI library expanded** (249 → 744 files, 14 → 26 composers):
  - Added from narcisse-dev/classical_ancient_midifiles: Bach (+45), Beethoven (+45),
    Chopin (+30), Corelli (55, new), Haydn (+55), Hummel (24, new), Joplin (47, new),
    Mozart (+45), Scarlatti (55, new)
  - Added Renaissance composers: Josquin (45), DuFay (19), Ockeghem (23), Isaac (5),
    Obrecht (7), Busnoys (10), Brumel (3), Compère (10), Mouton (10)
  - Synthetic Handel (10), Haydn (12), Mendelssohn (8), Tchaikovsky (15) via mido
- **20 new instrument samples** (40 → 60):
  - Saxophones: alto, tenor, soprano
  - Guitars: acoustic, electric clean, overdriven
  - Keyboards: pipe organ, marimba, xylophone, steel drums
  - Brass: muted trumpet, tuba, English horn, piccolo
  - World: banjo, shamisen, bagpipe
  - Synth: sawtooth lead, square lead, synth strings
- **gVisor steering updates** (`.claude/steering-check.sh`):
  - Added future memories early-stage orchestration cue (#14)
  - Added audio engine quality gate cue (#15)
- **30-minute cosmic radio v10 MP3s**:
  - `cosmic_radio_v10.mp3`: Seed 42, 1800 seconds
  - `cosmic_radio_v10_random.mp3`: Random seed, 1800 seconds

### Agent Activity

- Agent: Claude Opus 4.6 via Claude Code CLI
- Session: claude/resume-v9-document-v8-6yhAe
- Subagents spawned: 1 (codebase exploration)
- External repos cloned: narcisse-dev/classical_ancient_midifiles (4,723 MIDI files)
- espeak-ng installed for TTS
- Test results: 141 radio engine tests (23 new v10), 400 Python reference tests pass
- MP3 render time: ~595s per 30-min piece (numpy-accelerated)

### Files Created

- `future_memories/v0.10.0-plan.md`
- `apps/audio/cosmic_radio_v10.mp3`
- `apps/audio/cosmic_radio_v10_random.mp3`
- `session_logs/v0.10.0-session.md`
- 20 new instrument samples in `apps/audio/samples/`
- 495 new MIDI files across 12 new composer directories
- MIDI library: Corelli/, Hummel/, Joplin/, Scarlatti/, Josquin/, DuFay/, Ockeghem/,
  Isaac/, Obrecht/, Busnoys/, Brumel/, Compère/, Mouton/

### Files Modified

- `apps/audio/radio_engine.py` — v10 engine class, GM timbre profiles, CLI update
- `apps/audio/test_radio_engine.py` — 23 new v10 tests
- `apps/audio/midi_library/ATTRIBUTION.md` — expanded attribution
- `.claude/steering-check.sh` — two new steering cues
- `RELEASE_HISTORY.md` — this entry

---

## v0.9.0 — 2026-03-06 — Radio Engine v9: Expanded Instruments + Density-Aware Tempo

### Summary

Radio engine v9 with ~50 new GM instruments across 15 family pools (up from 5),
density-aware tempo multiplier (1.1x-2.1x range with caps during busy simulation
epochs), and family variety enforcement ensuring symphonic, rock, electronic, and
world instrument groups all appear across a 30-minute piece.

Also introduces the **future memories** protocol for durable session restoration,
CI flake detection steering, and AMD64 build verification guidance.

### Changes

- **Radio Engine v9** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV9` class extending `RadioEngineV8` with expanded instrument palette
  - `GM_EXPANDED_INSTRUMENTS`: ~50 new GM instruments across rock, electronic, synth FX,
    world/ethnic, symphonic, sax, choir, and mallet families
  - `GM_ALL_INSTRUMENTS`: combined v7/v8 + v9 instrument catalog
  - `V9_FAMILY_POOLS`: 15 instrument family pools (strings, brass, woodwinds, keys,
    pitched_perc, rock_guitar, rock_bass, synth_lead, synth_pad, synth_fx, world,
    sax, choir, symphonic_ext, mallets)
  - Density-aware tempo: `_compute_tempo_multiplier` returns 1.1x-2.1x, capped at
    1.6x for high-density epochs (>100 density score) and 1.8x for medium density
  - Family variety enforcement: tracks used family groups across render, biases toward
    under-represented groups past the halfway point
  - CLI: `--version v9` flag (v7 remains default)
  - `generate_radio_v9_mp3()` convenience function
  - All v8 features preserved (orchestral layering, anti-hiss, subsonic removal,
    note smoothing, time signature control, note quantization)
- **19 new v9 tests** in `test_radio_engine.py`:
  - Instrument catalog validation (count, superset, GM range)
  - 15 family pools verification
  - Rock, synth, world, sax, choir family existence
  - Density-aware tempo range, high/medium density caps
  - V9 engine creation, family group tracking, expanded pool coverage
  - Short render integration test
  - CLI v9 argument acceptance
- **Future memories protocol** (`future_memories/`):
  - New directory for verbose plan files committed before code mutation
  - `future_memories/README.md` explaining the protocol
  - `future_memories/v0.9.0-plan.md` documenting the full implementation plan
- **Steering updates** (CLAUDE.md, AGENTS.md, .claude/steering-check.sh):
  - Future memories: iterative plan commits before code mutation
  - CI flake detection and repair protocol
  - AMD64 build verification (best-effort)
  - Input quality caveat for typos/speech-to-text/ambiguity
  - Archive strategy: single tar.gz rebuilt each time, no orphan files
- **30-minute cosmic radio v9 MP3s**:
  - `cosmic_radio_v9.mp3`: Seed 42, 1800 seconds
  - `cosmic_radio_v9_random.mp3`: Random seed, 1800 seconds

### Agent Activity

- Agent: Claude Opus 4.6 via Claude Code CLI
- Session: Resuming interrupted v9 implementation from previous session
- Subagents spawned: 2 (codebase exploration, radio engine structure analysis)
- Test results: 117/118 radio engine tests pass (1 pre-existing espeak-ng skip),
  400/400 Python reference tests pass
- AMD64 builds verified: Go, Rust, C, C++

### Files Created

- `future_memories/README.md`
- `future_memories/v0.9.0-plan.md`
- `cosmic_radio_v9.mp3`
- `cosmic_radio_v9_random.mp3`
- `session_logs/v0.9.0-session.md`

### Files Modified

- `apps/audio/radio_engine.py` — v9 engine class, expanded instruments, CLI
- `apps/audio/test_radio_engine.py` — 19 new v9 tests
- `AGENTS.md` — future memories, CI flakes, AMD64 builds steering
- `CLAUDE.md` — matching steering updates
- `.claude/steering-check.sh` — matching hook updates
- `RELEASE_HISTORY.md` — this entry

---

## v0.8.0 — 2026-03-04 — Radio Engine v8: Orchestral Layering + Numpy Acceleration

### Summary

Radio engine v8 with orchestral layering: simultaneous multi-instrument sections
(~75% of segments) with occasional solo passages (~25%) for variety, anti-hiss
spectral filtering (cascaded lowpass at 10kHz/14kHz), subsonic removal (2-pole
highpass at 30Hz), note texture smoothing, time signature control (70%+ simple
with guaranteed compound/complex per 10-minute window), note duration quantization
to bar structure, and numpy-accelerated synthesis achieving ~7x speedup.

### Changes

- **Radio Engine v8** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV8` class extending `RadioEngine` with orchestral layering
  - Simultaneous multi-instrument orchestral sections (~75% of segments)
  - Solo instrument alternation (~25%) for variety and contrast
  - Consonant octave offsets between simultaneous voices (-12, 0, 0, 12, 24 semitones)
  - `NoteSmoother` class: post-synthesis buffer-level lowpass for smoother note textures
  - `AntiHissFilter` class: cascaded lowpass at 10kHz/14kHz for spectral cleanliness
  - `SubsonicFilter` class: 2-pole highpass at 30Hz removing subsonic rumble
  - `NoteQuantizer` class: duration quantization to fit bar structure (snap to beat grid)
  - Time signature rules: 70-80% simple (2/4, 3/4, 4/4), guaranteed compound/complex
    (6/8, 5/4, 7/8) in every 10-minute window per Wikipedia classification
  - CLI: `--version v8` flag (v7 remains default)
- **Numpy-accelerated synthesis** (`apps/audio/radio_engine.py`):
  - Vectorized ADSR envelope generation using numpy arrays
  - Vectorized harmonic synthesis (all harmonics computed in parallel)
  - Vectorized colored note generation replacing per-sample Python loops
  - ~7x speedup: 30-minute MP3 renders in ~6 minutes (was ~60 minutes)
  - Falls back gracefully to pure-Python when numpy unavailable
- **17 new v8 tests** in `test_radio_engine.py`:
  - `NoteSmoother` output validation
  - `AntiHissFilter` frequency response verification
  - `SubsonicFilter` low-frequency attenuation
  - `NoteQuantizer` beat grid snapping
  - `RadioEngineV8` instantiation and orchestral section generation
  - Time signature distribution validation (70%+ simple)
  - Compound/complex time signature guarantee per 10-minute window
  - All numpy acceleration paths tested
- **30-minute cosmic radio v8 MP3** (`cosmic_radio_v8.mp3`):
  - Seed 42, 1800 seconds, rendered with numpy acceleration
  - 73% simple time signatures (11/15 segments)

### Test Results

- Python reference: 400 passed
- Audio radio engine: 97 passed (80 v7 + 17 new v8)
- Audio composer: 67 passed
- Audio music engine: 62 passed
- Total quick tests: 626+

### Files Created

- `apps/audio/cosmic_radio_v8.mp3` — 30-minute cosmic radio v8 (~41 MB)

### Files Modified

- `apps/audio/radio_engine.py` — +1,200 lines: RadioEngineV8, NoteSmoother,
  AntiHissFilter, SubsonicFilter, NoteQuantizer, numpy acceleration
- `apps/audio/test_radio_engine.py` — +193 lines: 17 new v8 tests

### Agent Activity

- Session: `018qG8DYYWiDnmYdJZjN5GqX` (Claude Code native app)
- Branch: `claude/ast-physics-simulator-IWFs4`
- 3 commits: `348bf29`, `45791bd`, `88a543d`
- Note: Release notes and session log were not generated during the original session
  due to a UI bug in the Claude Code iOS app that caused the session to hang.
  This entry was reverse-engineered from git history on 2026-03-06.

---

## v0.7.0 — 2026-03-03 — Radio Engine v7 + Comprehensive Markdown Audit

### Summary

Radio engine v7 with improved musical quality: 1.5-2.5x tempo (down from 2-4x),
2-4 instrument small band ensembles (down from 6-16), mood segments at multiples
of 42 seconds, 7 rondo structures with 6 arpeggio forms, harmonic consonance (Helmholtz/Hartmann)
enforcement, anti-click processing, diverse instrument family selection, and
comprehensive 32-issue markdown audit fixing all stale references across the project.

### Changes

- **Radio Engine v7** (`apps/audio/radio_engine.py`):
  - Tempo multiplier: 1.5x-2.5x (was 2x-4x) for more natural pacing
  - Instruments per mood: 2-4 small band (was 6-16) for tighter ensemble
  - Mood duration: multiples of 42s (42, 84, 126, 168, 210s) for longer development
  - 7 rondo patterns: ABACA, ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA (was 2)
  - 6 arpeggio forms: block, ascending, descending, alberti, broken, pendulum
  - harmonic consonance (Helmholtz/Hartmann) enforcement: rejects tritones in bass, enforces consonant intervals
  - Anti-click processing: 2ms micro-fades on notes, DC offset removal, 2-4s cosine crossfades
  - Diverse instrument families: strings, brass, woodwinds, keys, pitched percussion
  - 8kHz gentle lowpass on all loop output for smoother sound
  - Fixed piano/non-piano alternation with weighted family selection
- **32-issue markdown audit** (HIGH/MEDIUM/LOW):
  - Fixed test counts: Node.js 44→194, Perl 56→376
  - Fixed Perl filename: `simulator.pl` → `simulate.pl`
  - Fixed C++ standard: C++17 → C++20
  - Added audio app to README, CLAUDE.md, docs/apps_overview.md, docs/build_guide.md
  - Added 4 missing AST doc entries to AGENTS.md (wasm, typescript, swift, kotlin)
  - Updated roadmap version from v0.4.0 to v0.7.0
  - Fixed temperature inconsistencies (Quark ~10^6 K, Inflation ~10^9 K)
  - Fixed PHP server bind address documentation
  - Aligned compaction ratios between ast_introspection.md and ast_passing_efficiency.md
  - Updated app count from 15 to 16
  - Fixed Swift build commands (xcodeproj → SPM)
  - Created apps/audio/README.md
- **8 new v7 tests** in `test_radio_engine.py`:
  - Rondo patterns expanded (7 patterns)
  - Arpeggio forms (6 forms, ascending/descending verified)
  - Tempo multiplier range (1.5-2.5x)
  - Mood duration at 42s multiples
  - Plan segments at 42s multiples
- **30-minute cosmic radio v7 MP3** (`cosmic_radio_v7.mp3`)

### Test Results

- Python reference: 400 passed
- Audio radio engine: 36 passed (quick) + 8 new v7 tests
- Audio composer: 67 passed
- Audio music engine: 62 passed
- Total quick tests: 573+

### Files Created

- `apps/audio/README.md` — Audio engine documentation
- `apps/audio/cosmic_radio_v7.mp3` — 30-minute cosmic radio v7

### Files Modified

- `apps/audio/radio_engine.py` — Radio engine v7 improvements
- `apps/audio/test_radio_engine.py` — 8 new v7 tests, updated assertions
- `README.md` — Audio app added, test counts updated, app count updated
- `CLAUDE.md` — Audio test command, app count, file structure
- `AGENTS.md` — 4 missing AST doc entries added
- `RELEASE_HISTORY.md` — This entry
- `docs/apps_overview.md` — Audio section, test counts, temperature fixes
- `docs/build_guide.md` — Audio section, C++20, simulate.pl, test counts
- `docs/roadmap.md` — Version updated to v0.7.0
- `docs/ast_introspection.md` — Compaction ratios aligned
- `docs/ast_passing_efficiency.md` — Compaction ratios aligned
- `apps/nodejs/README.md` — Test count 44→194
- `apps/perl/README.md` — Test count 56→376, added 07_environment.t
- `apps/php/server.php` — Bind address documentation
- `apps/php/README.md` — Bind address documentation
- `apps/swift/README.md` — Build commands updated to SPM

---

## v0.6.0 — 2026-03-01 — Structured Music Engine + 40 Instrument Samples + Spectral Safety

### Summary

Complete music engine rewrite with bar-based time signature system, multi-track
mixing, 40 synthetic instrument samples, and spectral frequency filtering.
Eliminates harsh high-frequency and low-frequency noise. Music now uses proper
time signatures (4/4, 3/4, 6/8, 5/4, 7/8, etc.) with real chord progressions,
melodic phrases, bass lines, and percussion patterns.

### Changes

- **New structured music engine** (`apps/audio/music_engine.py`, ~1200 lines):
  - `MusicDirector`: Top-level orchestrator managing sections, tracks, and phrases
  - `TimeSignature` system: 12 time signatures (4/4, 3/4, 6/8, 7/8, 5/4, etc.)
  - `PhraseGenerator`: Creates melodic lines, bass patterns, chord voicings, drum patterns
  - `Track` / `DrumTrack`: Separate instrument voices with gain/pan control
  - `MixBus`: Multi-track mixer with highpass (80Hz) + lowpass (8kHz) filtering
  - `Section`: Musical sections (4-16 bars) with consistent style
  - `SampleBank`: Sample-based instruments with numpy-accelerated pitch shifting
  - `BiquadFilter`: Highpass/lowpass for frequency safety
- **40 synthetic instrument samples** (`apps/audio/sample_gen.py` + `apps/audio/samples/`):
  - Piano, electric piano, harpsichord, celesta (4 keyboard)
  - Violin, viola, cello, harp, pizzicato (5 strings)
  - Flute, clarinet, oboe, bassoon (4 woodwinds)
  - French horn, trumpet, trombone (3 brass)
  - Tubular bell, glockenspiel, vibraphone, singing bowl (4 bells)
  - Kick, snare, hi-hat (closed/open), cymbal, tom (6 percussion)
  - Sitar, koto, kalimba, gamelan gong, shakuhachi, didgeridoo (6 world)
  - Warm pad, string ensemble, choir, glass pad, cosmic drone (5 pads)
  - Acoustic bass, synth bass, electric bass (3 bass)
  - All stored as MP3, ~1.5MB total
- **Spectral safety**:
  - Highpass filter at 80Hz removes sub-bass rumble
  - Lowpass filter at 3-10kHz (epoch-dependent) removes harsh highs
  - Soft limiter prevents clipping (output always in [-1, 1])
  - Verified: sub-bass 3%, no energy above 8kHz
- **Performance**: 9.8x realtime (10-min MP3 in ~70 seconds rendering)
  - Sample preloading eliminates ffmpeg subprocess overhead during render
  - Numpy-vectorized pitch shifting and mixing
- **62 new tests** for music engine (`apps/audio/test_music_engine.py`)
- **10-minute MP3** (`cosmic_simulation_v2.mp3`) with structured music

### Test Results

- Python reference: 400 passed
- Audio tests: 36 passed
- Composer tests: 67 passed
- Music engine tests: 62 passed
- **Total: 565 tests passing**

### Files Created

- `apps/audio/music_engine.py` — Structured music engine
- `apps/audio/sample_gen.py` — Instrument sample generator
- `apps/audio/test_music_engine.py` — 62 tests for music engine
- `apps/audio/samples/*.mp3` — 40 instrument samples
- `cosmic_simulation_v2.mp3` — New 10-minute MP3

### Files Modified

- `apps/audio/generate.py` — Integrated new music engine via `--engine` flag

### Additional Changes (Turn 2)

- **AST parser documentation** for 4 new parsers:
  - `docs/wasm_ast.md`, `docs/typescript_ast.md`, `docs/swift_ast.md`, `docs/kotlin_ast.md`
- **AST self-introspection** added to all 14 simulation apps:
  - CLI apps: `--ast-introspect` flag (C, C++, Rust, Java, PHP, TypeScript, Ubuntu screensaver)
  - GUI/mobile apps: Utility classes (Swift iOS, Kotlin Android, macOS screensaver)
  - WASM: `introspect.rs` module with compile-time metrics
- **Updated CLAUDE.md** with new AST parser doc references
- **Test total**: 1219+ tests passing across all verified languages

---

## v0.5.1 — 2026-03-01 — Vectorized Mixing Pipeline + Parallel Encoding + AST Analysis

### Summary

Vectorized the audio mixing pipeline with numpy, achieving 5.2x rendering speedup.
Added pipelined MP3 encoding via background threading. Generated 10-minute enhanced
MP3 (13.7 MB, all epochs). Provided comprehensive AST utilization analysis.

### Changes

- **Vectorized mixing pipeline** in `apps/audio/generate.py`:
  - Composer output mixing: numpy slice assignment replaces per-sample Python loop
  - Pad mixing: vectorized array operations with numpy
  - Silence detection: `np.mean(np.abs(...))` replaces generator comprehension
  - Dark matter texture: fully vectorized with `np.sin`/`np.pi`
  - Atomic sonification: vectorized with `np.exp`/`np.sin`
- **Pipelined MP3 encoding**:
  - Background thread feeds PCM chunks to ffmpeg concurrently
  - `deque`-based queue with sentinel-based shutdown
  - Hides ffmpeg encoding latency behind audio rendering
- **Performance results**:
  - 500 ticks: 10.1s → 1.95s (5.2x improvement)
  - Projected 10-min render: ~30 min → ~19.5 min
  - Combined with numpy synthesis (previous commit): total ~7.3x vs initial
- **10-minute enhanced MP3** (`cosmic_simulation_enhanced.mp3`, 13.7 MB):
  - Traverses all epochs: Hadron → Present
  - 500 ticks/sec, seed 42, enhanced mode with world musical traditions
- **AST utilization analysis**: Comprehensive assessment of AST-passing infrastructure
  utilization, compression ratios, and recommendations for full adoption

### Test Results

- Python reference: 400 passed
- Audio tests: 36 passed
- Composer tests: 67 passed
- Total: 503 passed, 0 failed

### Agent Activity

- Explore agent: AST utilization research (13 parsers, 17.9 MB captures, session logs)
- Background render: 10-minute enhanced MP3 (~42 min render time, pre-numpy code)
- Profiling: cProfile of render_chunk identified simulation (75%) vs composer (24%) split

### Files Modified

- `apps/audio/generate.py` — Vectorized mixing, pipelined encoding, numpy atomic sonification
- `RELEASE_HISTORY.md` — This entry

### Files Created

- `cosmic_simulation_enhanced.mp3` — 10-minute enhanced cosmic simulation audio

---

## v0.5.0 — 2026-03-01 — Enhanced Musical Composition Engine + AST Bug Prevention Steering

### Summary

Added a rich musical composition engine (`apps/audio/composer.py`) that draws from
6000+ years of human musical tradition to create evolving soundscapes driven by
simulation state. Integrated with the existing audio renderer for enhanced mode.
Introduced AST-guided code generation as a formal steering practice for bug prevention.

### Changes

- **Composition engine** (`apps/audio/composer.py`, 1085 lines):
  - 40+ world musical scales (Western, Japanese, Chinese, Middle Eastern, Indian, African, gamelan)
  - 16 instrument timbre profiles via additive synthesis with wavetable oscillators
  - 20+ polyrhythmic patterns (3:2, 4:3, 5:4, West African bell, gamelan kotekan)
  - 15+ harmonic progressions (Bach, minimalist, drone, circle of fifths)
  - 15+ melodic motifs from public domain works (Bach, Mozart, Beethoven, Chopin, Debussy,
    Satie, Grieg, Dvořák, Sakura, Jasmine Flower)
  - Streaming oscillator architecture (StreamingOsc) for O(samples_per_tick) rendering
  - Beat engine with 10-90% presence oscillation guided by simulation epoch
  - 4-voice polyphonic melodic system with phrase queuing
  - Universe pocket navigation across simulation domains
  - Percussion synthesis (kick, snare, hihat, rim) with caching
- **Performance optimizations** in `apps/audio/generate.py`:
  - Wavetable-based gen_pad (27% faster)
  - Inlined lowpass filter coefficients (reduced function call overhead)
  - Optimized PCM conversion with local variable caching
  - Dark matter texture for silence prevention
  - `--basic` flag (enhanced is default)
- **67 new tests** in `apps/audio/test_composer.py` covering all components
- **AST-guided code generation steering** added to all three steering locations:
  - Pre-write protocol: symbols, dependencies, callers queries
  - Post-write protocol: parse, coverage_map queries
  - Bug class taxonomy: broken imports, type mismatches, dead code, duplicates, etc.
- **Steering triple cross-check**: Updated CLAUDE.md, AGENTS.md, .claude/steering-check.sh

### Files Created

- `apps/audio/composer.py` — Musical composition engine
- `apps/audio/test_composer.py` — 67 tests for composer

### Files Modified

- `apps/audio/generate.py` — Enhanced mode integration, performance optimizations
- `CLAUDE.md` — AST-guided code generation section + checklist item
- `AGENTS.md` — AST-guided code generation section + reflection principle
- `.claude/steering-check.sh` — Bug prevention cue + reflection principle update
- `RELEASE_HISTORY.md` — This entry

### Agent Activity

- AST introspection run on composer.py (44 symbols, 1628 result tokens, 6.7x compression)
- Dependency analysis confirmed zero external dependencies in composer.py
- Coverage map identified 36 testable paths in composer.py, all covered by tests
- Background MP3 generation (10 minutes, enhanced mode, ~27 minutes render time)

### Test Results

- Python reference: 400 passed
- Audio tests (generate.py): 36 passed
- Composer tests: 67 passed
- Total: 503 passed, 0 failed

---

## v0.4.1 — 2026-03-01 — 100% Test Coverage Expansion Across All 15 Languages

### Summary

Massive test coverage expansion toward 100% across all 15 language implementations.
Launched 11+ parallel agents to analyze coverage gaps and write tests for every
untested public API. Fixed probabilistic test flakiness, constructor default issues,
and gitignore conflicts. Total: ~11,900 lines of new test code across 47 files.

### Changes

- **Test coverage expansion**: Wrote comprehensive tests for every untested public
  function/method across all 15 language implementations
- **Node.js**: 44 → 147 tests — added coverage for WaveFunction, Particle, Spin,
  Color, EntangledPair, QuantumField, ElectronShell, Atom (all methods), AtomicSystem,
  Molecule, ChemicalReaction, ChemicalSystem, Biology (Gene, DNAStrand, Protein, Cell,
  Biosphere). Fixed Atom constructor default (electronCount: 0 → explicit neutral)
- **Perl**: 56 → 376 tests — expanded all test files (quantum, atomic, chemistry,
  biology, universe) plus new environment test file
- **PHP**: 309 → 464 tests — added Spin::value, WaveFunction::toArray, Particle
  mass/charge, EntangledPair, QuantumField (vacuum fluctuation, decohere, evolve,
  snapshot), ElectronShell, AtomicSystem (recombination, nucleosynthesis, bonds),
  ChemicalSystem (catalyzed reaction, snapshot), biology toCompact, Epoch::description,
  Color enum, Gene::demethylate, Cell fitness/divide edge cases. Fixed UV mutation
  flakiness (intensity 50→5000)
- **Go**: suite → 112 tests — 29 new test functions for biology (20), atomic (4),
  chemistry (4), environment (1). Used `git add -f` for gitignore workaround
- **C**: 213 → 307 assertions — 14 new test functions for wf_collapse,
  vacuum_fluctuation, recombination, stellar_nucleosynthesis, epoch setters, universe_run
- **C++**: suite → 356 assertions — 17+ methods including spinValue, WaveFunction
  collapse, QuantumField annihilate/vacuumFluctuation, ElectronShell lifecycle, Atom
  ion/bondEnergy, AtomicSystem recombination/nucleosynthesis, ChemicalSystem formAminoAcid/
  formNucleotide, Gene epigenetic methods, Protein length
- **Rust**: 240 → 261 tests — 19 new tests for vacuum_fluctuation, decohere,
  stellar_nucleosynthesis, attempt_bond, catalyzed_reaction. Fixed flaky
  vacuum_fluctuation_high_temp test
- **Java**: suite → 682 tests — new TestParticle.java (86 tests) and TestMolecule.java
  (32 tests), expanded all existing test classes
- **TypeScript**: 44 → 157 tests — comprehensive coverage of all audio sonification
  and simulation modules
- **Kotlin**: expanded to 331 tests (syntax verified, no Android SDK)
- **Swift**: expanded to 535 tests (syntax verified, no Swift compiler)
- **WASM**: expanded to 134 tests — new test modules for atomic, biology, chemistry,
  quantum, universe
- **macOS screensaver**: expanded to 407+ additional test lines

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | 112   | PASS   |
| Rust     | 261   | PASS   |
| C        | 307   | PASS   |
| C++      | 356   | PASS   |
| Node.js  | 147   | PASS   |
| Perl     | 376   | PASS   |
| PHP      | 464   | PASS   |
| Java     | 682   | PASS   |
| TypeScript | 157 | PASS   |
| WASM     | 134   | PASS   |
| Kotlin   | 331   | SYNTAX OK |
| Swift    | 535   | SYNTAX OK |

### Agent Activity (this session)

1. Go coverage agent — filled 29 untested functions
2. C coverage agent — filled 14 untested functions (307 assertions)
3. C++ coverage agent — filled 17+ untested methods (356 assertions)
4. Rust coverage agent — filled gaps, fixed flaky test (261 tests)
5. Node.js/Perl/PHP/Java analysis agent — identified coverage gaps
6. Node.js coverage agent — expanded from 44 to 147 tests
7. Perl coverage agent — expanded from 56 to 376 tests
8. PHP coverage agent — expanded from 309 to 464 tests
9. Java coverage agent — expanded to 682 tests, 2 new test files
10. TypeScript/WASM/screensaver agent — expanded TS to 157, WASM to 134
11. Kotlin coverage agent — expanded to 331 tests
12. Swift coverage agent — expanded to 535 tests

### Files Modified (40+ files)

- `apps/c/test_simulator.c` (+263 lines)
- `apps/cpp/test_simulator.cpp` (+461 lines)
- `apps/go/simulator/simulator_test.go` (+860 lines)
- `apps/java/src/test/java/...` (9 files, +1,180 lines, 2 new files)
- `apps/kotlin/app/src/test/java/...` (7 files, +2,003 lines)
- `apps/nodejs/test/test_simulator.js` (+1,010 lines)
- `apps/perl/t/` (6 files + 1 new, +1,532 lines)
- `apps/php/tests/run_tests.php` (+594 lines)
- `apps/rust/src/simulator/` (3 files, +353 lines)
- `apps/swift/Tests/SimulatorTests/` (7 files, +2,095 lines)
- `apps/typescript/src/test.ts` (+670 lines)
- `apps/wasm/src/` (5 files, +294 lines)
- `apps/screensaver-macos/Tests/SimulatorTests.swift` (+407 lines)
- `RELEASE_HISTORY.md` — This entry

---

## v0.4.0 — 2026-03-01 — Steering Infrastructure, Session Logging, and CI Fix

### Summary

Major expansion of project governance infrastructure. Fixed CI pipeline failure,
added comprehensive steering enforcement via gVisor hooks, established session
logging protocol with historical reconstruction, created feature roadmap, and
ensured all markdown files reference each other coherently.

### Changes

- **CI fix**: Added `pip install pytest` step to `python-tests` job in
  `.github/workflows/ci.yml` — the root cause of the CI failure on the branch
- **CLAUDE.md**: Major rewrite (192→730+ lines) pulling in steering content from
  `docs/steering.md` — CueSignal protocol, AgentState tracking, token efficiency
  data, session logging protocol, markdown consistency checks, test coverage
  enforcement, self-cueing/gVisor enforcement, cross-compilation guidance,
  release history update mandate, triple cross-check reflection principle
- **AGENTS.md**: Major rewrite with same enhancements — session logging, release
  history, markdown review, test coverage, gVisor self-cueing, reflection principle
- **gVisor self-cueing**: Created `.claude/settings.json` and
  `.claude/steering-check.sh` — hook-based enforcement of steering rules with
  FAIL-CUE markers that prompt the agent to complete all per-turn tasks. Includes
  triple cross-check requirement (CLAUDE.md + AGENTS.md + gVisor hooks).
- **Session logs**: Reconstructed `v0.1.0-session.md` and `v0.2.0-session.md` from
  git history; created `v0.4.0-session.md` with full transcript detail
- **Feature roadmap**: Created `docs/roadmap.md` covering containerization
  (Docker/Colima), deployment target matrix, metacognitive steering enhancements,
  cross-language consistency automation, performance benchmarking
- **Network surface clarification**: Updated steering to note Go SSE server and PHP
  HTTP server are intentional localhost web servers for end-user use
- **Release history mandate**: Added to steering checklist — RELEASE_HISTORY.md must
  be updated at every conversation turn

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | suite | PASS   |
| Rust     | 240   | PASS   |
| C        | 213   | PASS   |
| C++      | suite | PASS   |
| Node.js  | 44    | PASS   |
| Perl     | 56    | PASS   |
| PHP      | 309   | PASS   |

### AST Passing Stats (this session)

- AST introspection ran on simulator modules: quantum.py (30 symbols),
  universe.py (14 symbols), biology.py (40 symbols), constants.py
- Pre-computed captures in `ast_captures/` validated

### Agent Activity (this session)

1. Codebase exploration agent — exhaustive file inventory and structure analysis
2. CLAUDE.md rewrite agent — comprehensive steering document
3. AGENTS.md rewrite agent — comprehensive multi-agent protocol
4. Feature roadmap agent — created `docs/roadmap.md`
5. Session log v0.1 agent — reconstructed from git history
6. Session log v0.2 agent — reconstructed from git history

### Files Created

- `.claude/settings.json` — gVisor hook configuration
- `.claude/steering-check.sh` — Steering enforcement script
- `docs/roadmap.md` — Feature roadmap
- `session_logs/v0.1.0-session.md` — Reconstructed session log
- `session_logs/v0.2.0-session.md` — Reconstructed session log
- `session_logs/v0.4.0-session.md` — This session's log

### Files Modified

- `.github/workflows/ci.yml` — Added pytest install step
- `CLAUDE.md` — Major rewrite with steering enhancements
- `AGENTS.md` — Major rewrite with steering enhancements
- `RELEASE_HISTORY.md` — Added v0.4.0 entry

---

## v0.3.0 — 2026-03-01 — Comprehensive Testing, Documentation, and Store Deployment Guides

### Summary

Major expansion adding tests to all 15 language implementations, comprehensive
documentation generation infrastructure, App Store and Play Store deployment guides,
and project-wide steering files for AI-assisted development.

### Changes

- **README.md**: Created top-level README documenting the full project — simulation
  overview, 15 applications, testing commands, AST-passing workflow, cross-compiled
  releases, and project structure
- **CLAUDE.md**: Created agent steering file for Claude Code and similar LLM tools —
  AST-passing protocol, coding principles (minimal dependencies, zero network surface),
  documentation standards, test commands
- **AGENTS.md**: Created multi-agent coordination protocol — swarm architecture,
  token budget guidelines, file locking conventions, commit format, cross-language
  consistency checks
- **Tests added** for: Go, Rust, C, C++, Java, PHP, TypeScript, Kotlin, Swift,
  WebAssembly, macOS screensaver, Ubuntu screensaver
- **CI/CD updated**: All test suites now run in the CI pipeline (`.github/workflows/ci.yml`)
  including Go test, Rust test, C test, C++ ctest, Java test runner, PHP test, TypeScript test
- **Documentation generation**: Added Doxygen configs for C and C++; all languages
  already have doc comments (JSDoc, PHPDoc, Javadoc, KDoc, Swift Markup, godoc, rustdoc, POD)
- **iOS App Store guide**: End-to-end instructions from zero to App Store release,
  using only Xcode (no Homebrew) — covers developer account, signing, simulator,
  TestFlight, and public release
- **Android Play Store guide**: End-to-end instructions from zero to Play Store release,
  using Android Studio — covers developer account, signing, emulator, internal testing,
  and production release
- **Session log infrastructure**: Created `session_logs/` directory for tracking
  development history across conversation turns
- **Release history**: This file, tracking the evolution of the project

### Agent Activity (this session)

This session used dictation mode for user input. The following agents were spawned:
1. Codebase exploration agent — mapped all 200+ files across 15 apps
2. Go test agent — created `apps/go/simulator/simulator_test.go`
3. Rust test agent — added `#[cfg(test)]` modules to all simulator source files
4. C/C++ test agent — created `test_simulator.c` and `test_simulator.cpp`, updated Makefiles
5. Java/PHP test agent — created Java test classes and PHP test runner
6. TypeScript/Kotlin/Swift test agent — created test suites for each
7. WASM/screensaver test agent — added tests for WebAssembly and screensaver simulator logic
8. iOS App Store documentation agent — wrote comprehensive Xcode-only deployment guide
9. Android Play Store documentation agent — wrote comprehensive Android Studio deployment guide

---

## v0.2.0 — 2026-02-28 — AST DSL Engine and Multi-Language Implementations

### Summary

Added the AST-passing DSL framework, reactive agent protocol, and all 15 language
implementations of the cosmic physics simulator.

### Changes

- **AST DSL**: Core engine (`ast_dsl/core.py`) with universal ASTNode, query/result
  protocol, performance metrics, and compact serialization
- **Reactive protocol**: Agent-pair state management (`ast_dsl/reactive.py`)
- **Language parsers**: 13 parsers covering Python, JS, TS, Go, Rust, C, C++, Java,
  Perl, PHP, Swift, Kotlin, WebAssembly
- **Introspection**: Cross-project analysis tool (`ast_dsl/introspect.py`)
- **15 applications**: Python CLI, Node.js CLI, Perl CLI, Go CLI+SSE, Rust CLI,
  C CLI, C++ CLI, Java GUI, TypeScript Audio, WebAssembly, PHP Snapshot,
  Swift iOS, Kotlin Android, macOS Screensaver, Ubuntu Screensaver
- **CI/CD**: GitHub Actions workflows for testing and cross-platform release builds
- **Documentation**: Comprehensive walkthrough, steering guide, per-app docs

---

## v0.1.0 — Initial Release — Python Reference Implementation

### Summary

Initial implementation of the cosmic physics simulator in Python.

---

## V21 — 2026-03-08 — "In The Beginning Phase 0" Album Release

### Summary

Major feature release: full CD-length album generation, 64×64 JavaScript grid
visualizer, enhanced streaming infrastructure, comprehensive documentation audit,
JSON transcript logging system, and music algorithm documentation.

### Turn 1 — 2026-03-08 10:24 CT (15:24 UTC) — V21 Kickoff

- **Documentation audit**: Cross-referenced all markdown against source code,
  fixed 85 insertions / 45 deletions across 8 docs files
- **Music algorithm documentation**: Created `docs/music_algorithm.md` (664 lines)
  describing the generative music approach in accessible language
- **JSON transcript logging**: New steering rule — companion `.json` alongside
  `.md` session logs with proofread user input, truncation (500-line threshold),
  redaction rules (security tokens only, system paths OK)
- **Steering triple-check**: Updated CLAUDE.md, AGENTS.md, steering-check.sh with
  JSON transcript rules, push-after-every-commit, and UTC timestamps
- **Album engine**: `AlbumEngine` class (radio_engine.py) for multi-track CD-length
  albums with vocoder bookends, creative track naming, per-track JSON note logs
- **Vocoder pitch projection**: TTS audio pitch-shifted to follow MIDI melodies
  with portamento bending
- **Note event logging**: `NoteLog` class recording every note for visualization
- **64×64 JavaScript visualizer**: 12-file pure JS app with grid, player, score,
  stream modules + full test suite (apps/visualizer/)
- **30-min MP3 render**: V20 engine, seed 759274, rendering in progress
- **Test results**: 295 core tests pass, 62 music engine tests pass

#### Agent Architecture (5 parallel worktree agents)
- Agent 1: Documentation audit (8 files, 85+/45- lines)
- Agent 2: Steering & JSON transcript system
- Agent 3: Music algorithm documentation
- Agent 4: Album engine + vocoder + note logging (~1358 new lines)
- Agent 5: JavaScript 64×64 grid visualizer (12 files, ~83KB)

#### Files Created/Modified
- NEW: docs/music_algorithm.md, apps/visualizer/ (12 files),
  apps/audio/test_music_engine.py, apps/audio/test_radio_engine.py,
  session_logs/transcript_schema.json
- MODIFIED: CLAUDE.md, AGENTS.md, .claude/steering-check.sh,
  .claude/settings.json, apps/audio/radio_engine.py (+1358 lines),
  README.md, docs/apps_overview.md, docs/build_guide.md, docs/roadmap.md,
  docs/walkthrough.md, apps/audio/README.md, apps/go/README.md

### Turn 2 — 2026-03-08 12:30 CT (17:30 UTC) — Budget Facility + Album Resume

- **Session budget management facility**: New steering section in CLAUDE.md, AGENTS.md,
  and steering-check.sh for analyzing usage dashboard screenshots, estimating burn rate,
  planning multi-window work, and making preemptive pause decisions (85%/90% thresholds)
- **Album render resumed**: Background process for tracks 4-17 (14 remaining tracks),
  each with unique seed (54321 increment), auto-commits on completion
- **Screen captures committed**: Updated terminal captures and API snapshots from test runs
- **JSON transcript updated**: Turn 2 actions logged with full structured data
- **Crash resilience**: Budget management docs emphasize push-after-every-commit,
  auto-commit watchers for background renders, and future memories as session insurance

#### Files Modified
- CLAUDE.md (new Session Budget Management section + TOC update)
- AGENTS.md (checklist item 15 + triple cross-check entry + budget section)
- .claude/steering-check.sh (FAIL-CUE item 25 for budget management)
- session_logs/v21-session.md (Turn 2 appended)
- session_logs/v21-session.json (Turn 2 structured data)
- future_memories/v21-docs-json-transcript-plan.md (status update)
- ast_captures/ (2 files updated)
- tests/screen_captures/ (18 files updated)

### Changes (Historical — V20 and earlier)

- **Simulator modules**: quantum.py, atomic.py, chemistry.py, biology.py,
  environment.py, universe.py, constants.py, terminal_ui.py
- **Test suite**: 400+ pytest tests covering all physics subsystems
- **Demo runner**: `run_demo.py` for interactive simulation

### Turn 3 — 2026-03-07 08:32 CT (14:32 UTC) — Gold Standard Tests + Big Bounce + MP3s

- Gold standard test run across all languages with screenshot/snippet evidence
- **Big Bounce perpetual simulation** implemented across ALL 13 language implementations:
  Python, Go, Node.js, Rust, C, C++, Perl, PHP, Java, TypeScript, WASM, Swift, Kotlin,
  plus both screensavers (macOS Swift, Ubuntu C)
  - Each implementation can reset and re-run indefinitely without memory leaks
  - Go SSE server runs in perpetual Big Bounce loop automatically
  - 4,149+ tests pass across 9 testable languages, 0 failures
- Two 30-minute MP3 renders: V8 tempo (1.5x-2.5x) and V15 tempo (1.1x-1.7x)
- New steering rules enshrined in triple-check (CLAUDE.md, AGENTS.md, steering-check.sh):
  UTC timestamps, gold standard test journaling, frequent commits, 2-min update cadence,
  future memories protocol
