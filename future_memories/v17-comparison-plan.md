# v0.17.0 Plan — V8 vs V15 Bit-Identity Investigation

## Date: 2026-03-07 06:22 CT (UTC 12:22)

## Context

User's fuller quote from a previous session claimed: "A tempo-matched V15 variant
should be bit-identical to the original V8 seed-42." This turn investigates whether
that claim holds.

## COMPLETED — Milestone: Empirical Results [06:53 CT]

### Empirical Comparison Results (30s clips, seed 42)

| Comparison | Bit-identical? | Max diff |
|------------|----------------|----------|
| V8+numpy vs V8 pure Python | NO | 0.3487 |
| V8 pure vs V15 (own tempo) | NO | 1.5838 |
| V8 pure vs V15+V8tempo (pre-fix) | NO | 0.5534 |
| **V8 pure vs V15+V8tempo+V8render** | **YES** | **0.0000** |
| V8+numpy vs V15+V8tempo+numpy | NO | 0.5702 |

### Key Findings

1. **The claim is conditionally TRUE**: When all code paths are matched (same tempo,
   same _render_segment), V15 produces bit-identical output to V8 at every sample.

2. **Double-filter bug discovered and fixed**: V15's `_render_segment` applied
   `anti_hiss` + `subsonic_filter` per-segment, but V8's inherited `render()` also
   applied them at master level → double application. Fixed by removing per-segment.

3. **numpy vs pure Python: materially different audio** (max diff 0.35, RMS 0.036).
   Whether original V8 MP3 used numpy is unknown — session log was reconstructed.

4. **numpy availability during V8 render: unknowable from existing records**.
   v0.6.0 logs confirm numpy was in use earlier. v0.8.0 log is reconstructed.

### Bug Fix

Removed lines 6412-6413 from `RadioEngineV15._render_segment`:
```python
# REMOVED — causes double-filter with V8's render():
left, right = self.anti_hiss.apply_stereo(left, right)
left, right = self.subsonic_filter.apply_stereo(left, right)
```

V16 inherits the fix via inheritance.

### Render Path Analysis

For `render()` (clips ≤ 660s): V8 applies anti-hiss/subsonic in `render()` only.
For `render_streaming()` (30-min MP3s): NO anti-hiss/subsonic at any level in V8.
V15 pre-fix: applied per-segment in _render_segment (streaming) or double in render().

### User Observations

- "Soft keyboards!" (autocorrect changed "fuller" to "filler")
- User confirmed the double-filter fix is important regardless of bit-identity test
- User noted 30-minute renders have more behavioral diversity (instrument rotation,
  TTS transitions, time sig windows) than 30s clips
- numpy was available at v0.6.0; unclear if available during v0.8.0 render
- User wants Central Time timestamps in responses (per steering)

## Deliverables (All Complete)

1. **Comparison script**: `apps/audio/compare_v8_v15.py` — 6 variant renders
2. **Evaluation document**: `docs/v8_v15_comparison.md` — full investigation
3. **Results file**: `docs/v8_v15_results.md` — machine-generated tables
4. **Bug fix**: V15 double-filter removal
5. **Tests**: 6 new regression tests
6. **Version bump**: v0.17.0

## Milestone: Turn 3 — 2026-03-07 08:32 CT (14:32 UTC)

### Gold Standard Tests + MP3 Generation + Steering Enshrinement

User wants a comprehensive "gold standard" test run with visual evidence (screenshots,
snippets) composited into the version cut journal. Also wants two 30-minute MP3
renders — one with original V8 tempo clamping (1.5x-2.5x) and one with new V15
tempo clamping (1.1x-1.7x) — pushed to GitHub with clickable raw file URLs.

New steering rules to enshrine in triple-check:
- UTC datetime stamps in all session + transcript journaling
- Gold standard test screenshots/snippets as part of version cut journaling
- Central Time datetime stamps in chat dialog progress
- Future memories generation enshrined in triple-check
- More frequent commits (every significant milestone)
- ~2-minute user update cadence in chat dialog

## Milestone: Infinity Radio Stream Design — 2026-03-07 08:48 CT (14:48 UTC)

### User Requests (speech-to-text, preserved as-is)

1. "How will the infinity radio stream work when we get beyond 30 minutes?"
   - Shuffle ordering of spacetime events (higher-dimensional reality concept)
   - Modify seed for each 30-min segment so it's random after first
   - Keep TTS interspersed within any 10-min range
   - CLI parameter for seed selection
   - Ensure variety after initial deterministic segment

2. Non-audio simulations should also run indefinitely:
   - No memory leaks
   - No fizzling out to blank screen / static / heat death
   - Must remain "healthy and vibrant"
   - Some transform to prevent entropy death

### Research Findings: Current State

**Audio (infinity radio)**:
- `generate.py --radio --duration 0` already runs forever via HTTP
- Uses `seed + tick` for new universe when completing
- But this is a full restart, not continuous unfold
- `render_streaming()` handles any duration with rolling buffer
- CLI params `--seed` and `--duration` exist

**Non-audio simulations**:
- All simulators have a fixed tick count (~300,000)
- None currently loop or restart
- Go SSE server streams state but doesn't loop

### Proposed Architecture: Infinite Radio v18

1. **Multi-epoch seed cycling**: After each 30-min "era", derive next seed from
   `hash(prev_seed, final_state_summary)` — deterministic but unpredictable
2. **Epoch shuffling**: In eras beyond the first, shuffle the ordering of cosmic
   epochs (user's "higher dimensionality" concept) — e.g., start from nucleosynthesis
   or even reverse some progressions
3. **TTS windows**: Rolling 10-min window for TTS announcements, independent of
   total duration
4. **CLI**: `--infinite` flag + `--initial-seed` parameter
5. **Memory**: Rolling buffer already ensures O(1) memory for audio

### Proposed Architecture: Perpetual Non-Audio Simulations

1. **Cycle detection**: When simulation reaches "Present" epoch, trigger renewal
2. **Renewal options**:
   a. Re-seed with derived seed, restart from Planck epoch
   b. "Heat death -> Big Bounce" — simulate contraction and restart
   c. "Multiverse fork" — branch into parallel universe with different constants
3. **Anti-entropy guard**: Detect low-activity state (all counts stable for N ticks)
   and inject a "cosmic event" (supernova, gamma-ray burst, new particle)
4. **Memory safety**: Reset accumulators periodically, cap list sizes

---

## Turn 3 Milestone — 2026-03-07 09:30 CT (15:30 UTC)

### Big Bounce: COMPLETE across all 13 languages

Every implementation now has `bigBounce()` / `big_bounce()` / `universe_big_bounce()`:
- Python, Go, Node.js, Rust, C, C++, Perl, PHP, Java, TypeScript, WASM, Swift, Kotlin
- Plus both screensavers (macOS Swift, Ubuntu C)
- Go SSE server runs in perpetual Big Bounce loop automatically
- 4,149+ tests pass across 9 testable languages, 0 failures

### MP3 Renders: In Progress
- MP3 #1 (V8 tempo): Done, 42MB
- MP3 #2 (V15 tempo): Rendering, ~58% at 09:30 CT

### MP3 Renders: COMPLETE
- MP3 #1 (V8 tempo): 42MB, pushed to GitHub
- MP3 #2 (V15 tempo): 42MB, pushed to GitHub
- Raw URLs provided to user (no markdown formatting)

### Swift on Linux Investigation — 2026-03-07 09:45 CT (15:45 UTC)

**Cannot install Swift in this sandbox:**
- download.swift.org is blocked (403 host_not_allowed)
- GitHub releases for swiftlang/swift have zero downloadable assets
- swiftlang/swiftly installer also has no GitHub release assets
- clang 18.1.3 is available but cannot compile Swift (separate frontend needed)
- No apt packages for Apple Swift exist

**Architecture analysis:**
- 7 simulator files use only Foundation + Observation (Linux-compatible with Swift 5.9+)
- 6 UI files require SwiftUI/MetalKit/AVFoundation (Apple-only)
- Tests use XCTest (Linux-compatible)
- Package.swift already separates simulator into its own target

**User preference:** Official Apple tools over Homebrew for macOS builds.
Use xcodebuild or swift build via Xcode CLI tools.

**Feedback:** download.swift.org should be added to sandbox trusted domains.

---

## Turn 4 Plan — 2026-03-07 10:22 CT (16:22 UTC)

### Context (speech-to-text from user, preserved as-is)

User wants 5 MP3s total:
1. V8-style seed=42 with reduced instruments/MIDI (original V8 set)
2. V8-style random seed with reduced instruments (original V8 set)
3. Latest bug-fixed version, seed=42, new tempo (1.1x-1.45x)
4. Latest bug-fixed version, random seed, new tempo
5. "Orchestra variety" — wider instrument variety, NOT sounding like organs/synths

### Key Findings from Research

**V17 MP3s already used V8's reduced instrument set** (5 families, no MIDI library).
V15 inherits V8, which has 5 family pools and 537 synth instruments. The expanded
set (V9+) has 15 families and 744 MIDI files from 26 composers.

**Static/noise sources identified:**
1. `noise_perc` instruments (~54 of 537) generate raw white noise
2. V8's `_mix_mono` overloads pan param with gain: `pan * voice_gain * 4`
3. No post-render limiter in V8 path — voices sum without ceiling
4. `distortion` param via tanh adds harsh overtones on summation
5. V11 already fixed these with separate gain/pan, quality gating (no noise_perc
   in harmonic voices), soft-knee limiting

**Static fix approach:**
- For V8-faithful renders: use V15 as-is (already V8 reduced set)
- For "latest" renders: create V18 engine = V15 synthesis + V11 mixing fixes +
  tempo clamped to 1.1x-1.45x
- For "orchestra variety": create V18 variant using V16's expanded palette +
  V11's instrument character preservation + wider family rotation

### Implementation Plan

1. Create `RadioEngineV18` subclassing `RadioEngineV15`:
   - Override `_compute_tempo_multiplier` → 1.1x-1.45x range
   - Override `_mix_mono` → separate gain/pan (from V11)
   - Quality-gate instrument selection: skip `noise_perc` for melodic voices
   - Apply soft-knee limiting on master bus

2. Create `RadioEngineV18Orchestra` subclassing `RadioEngineV18`:
   - Use V9's expanded 15 family pools
   - Use 744 MIDI files
   - Enforce instrument variety per segment (like V14's approach)
   - Preserve instrument character: keep original harmonic profiles, limit
     color_amount blending to preserve xylophone/strings/horn identity

3. Generate 5 MP3s via script:
   - V8-style seed=42 (V15 with V8 tempo 1.5-2.5x) — ALREADY EXISTS as v17_v8tempo
   - V8-style random (V15 with V8 tempo, random seed)
   - V18 seed=42 (1.1-1.45x, clean mixing)
   - V18 random seed (1.1-1.45x, clean mixing)
   - V18Orchestra random seed (expanded palette, 1.1-1.45x, character preservation)

4. Tempo: 1.1x-1.45x per user request (narrower than V15's 1.1-1.7x)

## Turn 4 Continued — 2026-03-07 10:56 CT (16:56 UTC)

### Session Resumed After Context Compaction

**V18 implementation COMPLETE** (committed as `13b5b1c`):
- `RadioEngineV18`: clean mixing, 1.1x-1.45x tempo, noise gating, soft-knee limiting
- `RadioEngineV18Orchestra`: expanded 15-family palette, character preservation
- 21 new tests (14 V18 + 7 V18Orchestra)
- `generate_v18_mp3s.py`: 5-variant generation script with CLI targeting

**MP3 renders in progress** (background, ~30 min each):
- V8-42: started this turn
- V8-random: DONE (43MB)
- V18-42: encoding to MP3
- V18-random: WAV rendering
- V18-orchestra: WAV rendering

**Swift toolchain**: BLOCKED — `download.swift.org` returns 403 despite user's
wildcard allowlist update. Proxy does not honor `*.swift.org` — only `www.swift.org`
is in the JWT. User needs to add `download.swift.org` explicitly.

### Next Steps
1. Wait for all 5 MP3 renders to complete
2. Commit and push MP3s to GitHub
3. Provide raw download URLs to user
4. Resume Swift investigation if domain becomes available
5. Update version, session log, release history
