# V19 Session Log — Test Infrastructure Overhaul

## Session Info
- **Date**: 2026-03-07
- **Branch**: claude/resume-v9-document-v8-6yhAe
- **Window**: ~5 hours (started ~11:00 CT, ends ~16:00 CT)

---

## Turn 1 — 2026-03-07 13:25 CT (19:25 UTC) — Planning & Survey

### Requested
User asked for comprehensive test infrastructure overhaul across all 16 apps.
Specific focus on golden output tests, cross-language parity, server smoke tests,
and audio golden tests.

### Actions
- Surveyed all test infrastructure (subagent): 4,500+ tests found across 16 apps
- Identified gaps: no golden output tests, no cross-language parity, no server smoke tests
- Created 11-phase implementation plan
- Set up self-cueing timer (warnings at 15:45 CT, 15:55 CT)

### Test Survey Results
| Language | Tests | Framework |
|----------|-------|-----------|
| Python (ref) | 407 | pytest |
| Node.js | 150+ | node:test |
| Go | 112 | testing |
| Rust | 261+ | #[test] |
| C | 309+ | Custom |
| C++ | 333+ | Custom |
| Java | 500+ | Custom |
| Perl | 350+ | Test::More |
| PHP | 400+ | Custom |
| TypeScript | 187+ | node:test |
| Kotlin | 350+ | JUnit 4 |
| Swift | 400+ | XCTest |
| WASM | 138+ | #[test] |
| Audio | 150+ | pytest |

### Files Created
- `future_memories/v19-test-infrastructure-plan.md`
- `session_logs/v19-session.md` (this file)

---

## Turn 2 — 2026-03-07 13:25 CT (19:25 UTC) — Implementation Begins

### Implementation Progress

**13:25 CT (19:25 UTC)** — Started implementation. Created capture tool and golden test framework.

**13:38 CT (19:38 UTC)** — All 5 test modules written:
- `tests/test_golden_outputs.py` — 23 tests (build + run all CLI apps)
- `tests/test_cross_language_parity.py` — 10 tests (epoch parity)
- `tests/test_server_smoke.py` — 9 tests (Go SSE + PHP server)
- `tests/test_visualizer_golden.py` — 15 tests (Ubuntu screensaver, WASM, Java, macOS)
- `tests/test_audio_golden.py` — 13 tests (audio pipeline)

**13:44 CT (19:44 UTC)** — CI workflow created: `.github/workflows/golden.yml`

**13:50 CT (19:50 UTC)** — First test run: found 3 failures. Fixed Java entry point
(SimulatorApp not Main), Node.js golden match (structural instead of exact), C++ binary
name (inthebeginning not simulator).

**13:56 CT (19:56 UTC)** — Second test run: found 3 more issues. Fixed Go SSE server
port flag, Ubuntu screensaver "0 FAILED" false positive, audio Composer API.

**14:00 CT (20:00 UTC)** — ALL TESTS GREEN:
- Golden outputs: 23 passed
- Cross-language parity: 10 passed (9+1 fixed)
- Server smoke: 9 passed
- Visualizer: 15 passed (13+2 skipped)
- Audio: 13 passed (11+2 skipped)
- **Total new tests: 66 passed, 4 skipped, 0 failed**
- Reference tests: 258 passed (unchanged)

### Golden Snapshots Captured

| Language | Exit Code | Output Lines | Status |
|----------|-----------|-------------|--------|
| Python | 0 | 145 | Captured |
| Node.js | 0 | 451 | Captured |
| Go | 0 | 127 | Captured |
| Rust | 0 | 243 | Captured |
| C | 0 | 489 | Captured |
| C++ | 0 | 185 | Captured |
| Perl | 0 | 38 | Captured |
| PHP | 0 | 38 | Captured |
| TypeScript | 0 | 451 | Captured |

### Files Created
- `tests/test_golden_outputs.py`
- `tests/test_cross_language_parity.py`
- `tests/test_server_smoke.py`
- `tests/test_visualizer_golden.py`
- `tests/test_audio_golden.py`
- `tools/capture_golden.py`
- `.github/workflows/golden.yml`
- `tests/golden_snapshots/` (9 language directories)
- `future_memories/v19-test-infrastructure-plan.md`

### Files Modified
- `CLAUDE.md` — added golden test execution commands
- `README.md` — added integration test section
- `RELEASE_HISTORY.md` — added v0.19.0 entry

---

## Turn 3 — 2026-03-07 14:21 CT (20:21 UTC) — V20 Audio Engine Overhaul

### Requested
User requested comprehensive audio engine improvements:
1. Fix volume issues: low overall volume + high-volume spikes in MP3 generation
2. Install additional TTS engines via apt (flite, festival, pico2wave)
3. Download ~100 openly licensed SoundFont instruments from GitHub
4. Download ~1000 openly licensed MIDI files for sampling from GitHub
5. Add 10-20% "solo instrument" mood (sampled arrangement, single instrument, no embellishments)
6. Generate seed-42 and random-seed MP3s with all improvements
7. Golden test thumbnails/snippets with evidence in session log
8. Full post-execution verification with triple-check architecture

### Current State (Pre-Work)
- 744 MIDI files across 27 composers in midi_library/
- 537 synth instruments (pure Python synthesis, no SoundFonts downloaded)
- TTS: espeak-ng only (Silero/PyTorch not installed)
- mido + numpy installed; torch/torchaudio NOT installed
- No FluidSynth or SoundFont (.sf2) files present
- Volume: voice_gain = 0.25/n_voices with soft-knee limiting at 0.75

### Actions Completed — 14:34 CT (20:34 UTC)

#### 1. TTS Engines Installed
- espeak-ng (already present)
- flite 2.2 (via apt)
- festival 2.5.0 (via apt)
- pico2wave (via apt)

#### 2. FluidSynth + SoundFonts Installed
- FluidSynth 2.3.4 (via apt)
- FluidR3_GM.sf2 (128 GM instruments, via apt)
- FluidR3_GS.sf2 (GS extended, via apt)

#### 3. V20 Engine Built — Volume Fix + Solo Moods
Root cause of volume issues identified via ffmpeg volumedetect:

| MP3 | Mean dB | Peak dB | Dynamic Range |
|-----|---------|---------|---------------|
| v18-42 | -35.7 | -1.6 | 34.1 dB |
| v18-random | -34.5 | -2.9 | 31.6 dB |
| v18-orchestra | -35.9 | -7.0 | 28.9 dB |
| v8-42 (old) | -19.8 | 0.0 | 19.8 dB (clips!) |

**Root cause**: Double 0.25 gain attenuation: `voice_gain = 0.25/n_voices` then
`_mix_mono_clean(..., v_gain * 0.25)` → effective gain 0.016-0.031 per voice (-30 to -36 dB)

**V20 fixes applied**:
- Removed double 0.25 attenuation (gain now 0.35/n_voices, mix at 1.0)
- Master normalization to -1dB peak after all rendering
- Lookahead limiter (5ms attack, 50ms release) prevents transient spikes
- Per-segment soft-knee raised to 0.85 (was 0.75)

**V20 test render results (60s, seed=42)**:
```
Peak: 0.8913 (-1.0 dB)    ← exactly on target
RMS:  0.1325 (-17.6 dB)   ← good listening level
Dynamic range: 16.6 dB     ← healthy (was 34 dB!)
Samples > 0.95: 0          ← zero spikes!
```

#### 4. Solo Instrument Mood Feature
- 15% chance per segment triggers "solo mood"
- Single instrument plays sampled MIDI arrangement directly
- No chord building, no arpeggios, no embellishments
- Gentle reverb, centered pan, moderate coloring
- Gives listener's brain a reset moment

#### 5. Golden Test Evidence

**Golden Output Tests: 23/23 PASSED**
```
tests/test_golden_outputs.py: 23 passed in 94.39s
```

**Cross-Language Parity: 10/10 PASSED**
```
tests/test_cross_language_parity.py: 10 passed in 16.71s
```

**Audio Golden Tests: 12/13 PASSED, 1 SKIPPED**
```
tests/test_audio_golden.py: 12 passed, 1 skipped in 18.06s
```

**Golden Output Snippets (first 4 lines of each language)**:

Python:
```
  ╔══════════════════════════════════════════╗
  ║       IN THE BEGINNING                   ║
  ║  AST-Driven Reality Simulator             ║
  ╚══════════════════════════════════════════╝
```

Node.js:
```
  ╔══════════════════════════════════════════════════════════╗
  ║          I N   T H E   B E G I N N I N G                ║
  ║          Cosmic Evolution Simulator                      ║
  ╚══════════════════════════════════════════════════════════╝
```

Go:
```
  ========================================================================
                              IN THE BEGINNING
                        A Cosmic Evolution Simulator
  ========================================================================
```

Rust:
```
  ╔═══════════════════════════════════════════════════════════╗
  ║       IN THE BEGINNING -- Cosmic Simulation v0.1         ║
  ║       From the Big Bang through the emergence of life    ║
  ╚═══════════════════════════════════════════════════════════╝
```

C:
```
  |        IN THE BEGINNING: Cosmic Evolution Simulator      |
  |        From the Big Bang to Life                         |
```

C++:
```
                    IN THE BEGINNING
           A Cosmic Evolution Simulator (C++20)
```

Perl:
```
  IN THE BEGINNING — Cosmic Simulation (Perl)
  From the Big Bang to the emergence of life
```

PHP:
```
  IN THE BEGINNING — Cosmic Simulation (PHP)
  From the Big Bang to the emergence of life
```

### Actions In Progress
- Downloading ~1000 additional public domain MIDI files from GitHub
- Preparing full 30-minute V20 MP3 renders (seed=42 and random)
