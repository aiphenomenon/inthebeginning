# Work To Be Done

Outstanding work items organized by facet. Updated at each solution cut.
Referenced from `CLAUDE.md` — check this file at session start to understand
current priorities.

---

## Cosmic Runner (inthebeginning-bounce)

### Outstanding Bugs

| # | Category | Issue | Status | Notes |
|---|----------|-------|--------|-------|
| 1 | UI | MIDI track listing: show next/prev 12 tracks | Open | V36 #14 |
| 2 | Mobile | Multiple taps spawns track listing unexpectedly | Open | V36 #16 |
| 3 | Gameplay | Grid mode: no final score when non-infinite ends | Open | V36 #7 |
| 4 | Gameplay | Emoji should not cross lanes (stay in their lane) | Open | V36 #11 |
| 5 | Gameplay | Key 3 (grid mode switch) doesn't work in gameplay | Done | V45 E2E confirms key 3 works |
| 6 | WASM | WASM mode: no track info or time displayed | Open | V45 BUG 1 — HUD empty, 0:00/0:00 |
| 7 | UI | MP3 player note info shows raw internal instrument names | Open | V45 BUG 2 — e.g. "koto_v0_additive_32" |
| 8 | UI | Voice/Choir instrument family unchecked by default | Open | V45 BUG 3 — may be intentional |

### Audio / Instruments

| # | Category | Issue | Status | Notes |
|---|----------|-------|--------|-------|
| 9 | MIDI | General MIDI instrument quality — proper GM mapping | Done | V45 verified: 128 programs → 60 MP3 samples |
| 10 | WASM | General MIDI instruments in WASM mode | Open | WASM has only 13 additive timbres, no MP3 samples |
| 11 | Synth | Evaluate GM instrument quality in Synth mode | Done | V45: Synth routes through SynthEngine → same sample bank |
| 12 | Audio | Instrument Soundbank modal text improvements | Open | V36 #21 |
| 13 | WASM | WASM-to-Python music parity — full album-quality generation | Open | Priority future work; see note below |

**WASM Music Parity Note**: The Python radio_engine produces album-quality
30-minute music renders (now 12 MP3 tracks). A future WASM implementation
should replicate this quality level: FluidSynth-like synthesis with GM
instrument samples, cosmic coloring/mood approaches, statistical MIDI
sampling from 1,800+ MIDIs, and the same epoch-driven generation that
produced the V8 Sessions album. This would enable real-time album-quality
music generation directly in the browser. Different seeds to the same
algorithm would generate similarly high quality music, influenced by
different statistical samples from the MIDI library.

### Mobile / Touch / Multi-Player

| # | Category | Issue | Status | Notes |
|---|----------|-------|--------|-------|
| 14 | Touch | 2P flick-up: allow from lower 1/9th of each player's corner | Open | V47 — don't require precise tap, allow proximity |
| 15 | 3D | 3D mode: player movement farther/nearer in manifold | Open | V47 — move up-screen = farther in 3D; jumps score relative to 3D position |
| 16 | 3D | Objects vanishing at manifold edge where player is | Open | V47 — objects must disappear at player's Y, not just screen bottom; coordinate with #15 |

### Known Issues (browser limitations, not fixable from JS)

| # | Issue | Workaround |
|---|-------|------------|
| K1 | Double pause icon (Unicode rendering at certain viewports) | Resize or use P key |
| K2 | Minimize stops MIDI playback (Firefox/Ubuntu Web Audio) | Alt-tab instead; use MP3 mode |

---

## Testing Infrastructure

| # | Item | Status | Notes |
|---|------|--------|-------|
| T1 | Local-first testing — avoid burning GitHub CI minutes | Done | V45: tools/quick-test.sh, pytest.ini |
| T2 | End-to-end visual testing with Playwright | Done | V45: 47 game tests + 11 audio/WASM tests |
| T3 | Audio waveform driver for headless testing | Done | V45: PulseAudio virtual sink + spectral analysis |
| T4 | Playhead seeking in MP3 mode (requires audio loaded) | Open | Now possible with PulseAudio; needs test |
| T5 | Note data completeness tests | Done | 112 tests, v43 |
| T6 | Targeted test execution via blast radius analysis | Done | V45: tools/quick-test.sh with git diff |
| T7 | Pytest markers (unit, integration, e2e, audio, wasm) | Done | V45: pytest.ini + conftest.py |
| T8 | Pre-existing test fix: 12 vs 24 note JSONs | Done | V46: test_notes_files expects 24 (v3+v4) |
| T9 | Firefox + WebKit browser verification | Open | V47: Playwright can test Firefox + WebKit on Linux |
| T10 | Mobile/tablet viewport E2E tests | Open | V47: iPhone 16 (390×844), iPad (820×1180) |
| T11 | Touch interaction E2E tests | Open | V47: tap, swipe, seek via touch on mobile viewports |

---

## Python Simulator (Reference Implementation)

| # | Item | Status | Notes |
|---|------|--------|-------|
| P1 | Physics engine stable | Done | All 350+ tests pass |
| P2 | Cross-language parity verified | Done | 13 languages match |

No outstanding items. Physics engine is stable.

---

## Node.js (apps/nodejs/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| N1 | Unit tests pass | Done | node --test apps/nodejs/test/test_simulator.js |
| N2 | Golden output parity | Done | Matches reference |

---

## Go (apps/go/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| G1 | Unit tests pass | Done | go test ./... |
| G2 | SSE server smoke test | Done | test_server_smoke.py |
| G3 | Golden output parity | Done | Matches reference |

---

## Rust (apps/rust/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| R1 | Unit tests pass | Done | cargo test |
| R2 | Golden output parity | Done | Matches reference |

---

## C (apps/c/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| C1 | Unit tests pass | Done | make test |
| C2 | Golden output parity | Done | Matches reference |

---

## C++ (apps/cpp/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| X1 | Unit tests pass | Done | cmake + ctest |
| X2 | Golden output parity | Done | Matches reference |

---

## Java (apps/java/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| J1 | Unit tests pass | Done | JUnit via javac/java |
| J2 | Headless GUI test | Done | test_screen_capture.py |
| J3 | Missing: standalone unit test runner | Open | Currently requires manual classpath |

---

## Perl (apps/perl/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| L1 | Unit tests pass | Done | prove -v apps/perl/t/ |
| L2 | Golden output parity | Done | Matches reference |

---

## PHP (apps/php/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| H1 | Unit tests pass | Done | php tests/run_tests.php |
| H2 | Server smoke test | Done | test_server_smoke.py |
| H3 | Golden output parity | Done | Matches reference |

---

## TypeScript (apps/typescript/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| S1 | Unit tests pass | Done | npm test |
| S2 | Browser build | Done | npm run build:browser |

---

## Kotlin (apps/kotlin/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| K3 | Unit tests | Open | Requires Android SDK or ./gradlew test |
| K4 | Test coverage gap | Open | No standalone unit tests outside Android |

---

## Swift (apps/swift/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| W1 | Simulator library (7 files) | Done | Linux-compatible via swift-corelibs |
| W2 | Unit tests | Open | Requires Swift 5.9+ toolchain |
| W3 | iOS app testing | Open | Requires Xcode on macOS |

---

## WASM (apps/wasm/ + apps/wasm-synth/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| M1 | Simulator WASM (apps/wasm/) | Done | cargo test (native) |
| M2 | WASM Synth (apps/wasm-synth/) | Done | 40KB binary, verified in browser |
| M3 | WASM synth quality gap: 13 timbres vs 60 samples | Open | See item #10 above |
| M4 | WASM mode HUD/metadata display | Open | See BUG #6 above |
| M5 | Full Python music parity in WASM | Open | See item #13 above |

---

## Screensaver macOS (apps/screensaver-macos/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| SM1 | Requires macOS + Xcode for testing | Open | Cannot test on Linux CI |

---

## Screensaver Ubuntu (apps/screensaver-ubuntu/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| SU1 | Unit tests | Done | test_simulator.c |
| SU2 | Xvfb screenshot test | Done | test_screen_capture.py |

---

## Audio Composition Engine (apps/audio/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| A1 | Unit tests pass | Done | 4 test files, all pass |
| A2 | Golden audio snapshot | Done | test_audio_golden.py |
| A3 | Radio engine validation | Done | test_radio_engine.py |

---

## Cosmic Runner Variants

| # | App | Status | Notes |
|---|-----|--------|-------|
| CR1 | cosmic-runner (v1) | Archived | No tests, superseded |
| CR2 | cosmic-runner-v2 | Archived | Has pytest tests (test_cosmic_runner_v2.py) |
| CR3 | cosmic-runner-v3 | Active | 3 JS test files, used for V4-V7 deploys |
| CR4 | cosmic-runner-v5 | **Stale** | Diverged from apps/inthebeginning-bounce/ |
| CR5 | inthebeginning-bounce | **Active** | Latest source = deploy/v11/ (verified) |

**Important**: apps/cosmic-runner-v5/ is STALE — checksums differ from
apps/inthebeginning-bounce/ and deploy/v11/. All game development should
use apps/inthebeginning-bounce/ as the canonical source.

---

## Visualizer (deploy/v5/visualizer/)

| # | Item | Status | Notes |
|---|------|--------|-------|
| V1 | 5 modes (Album, MIDI, Synth, Stream, Single) | Done | |
| V2 | JS test files | Done | 5 test files in apps/visualizer/test/ |
| V3 | Visual golden tests | Done | test_visualizer_golden.py |

---

## Architecture / Infrastructure

| # | Item | Status | Notes |
|---|------|--------|-------|
| A1 | Work-to-be-done tracking (this file) + steering | Done | V44+V45 |
| A2 | Turn-by-turn journal protocol | Done | v37-v42 |
| A3 | Journal content validation hook | Done | v41 |
| A4 | Topical index for future_memories | Open | Navigate by topic, not just time |

---

## Steering / Hooks

| # | Item | Status | Notes |
|---|------|--------|-------|
| S1 | CLAUDE.md references WORKLOG.md | Done | V44 |
| S2 | Session-start hook shows top work items | Done | V44 |
| S3 | Stop hook verifies WORKLOG.md updated on game changes | Open | |
| S4 | CLAUDE.md test tier documentation | Done | V45 |

---

## Deploy / GitHub Pages

| # | Item | Status | Notes |
|---|------|--------|-------|
| D1 | v4 note data deployed to v10, v11, shared | Done | v43 |
| D2 | Verify deploy works end-to-end on GitHub Pages | Open | Manual check |
| D3 | Sync cosmic-runner-v5 with inthebeginning-bounce | Open | V45 finding: v5 is stale |

---

## Last Updated

v46 — 2026-04-05
