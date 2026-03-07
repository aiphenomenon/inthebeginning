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
