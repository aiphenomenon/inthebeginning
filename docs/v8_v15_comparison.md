# V8 vs V15 Bit-Identity Investigation (V17)

## Date: 2026-03-07

## The Claim Under Test

> "V15 should sound closest to the original V8 — same factory.synthesize_colored_note(),
> same 537 instruments, same 5 families. Only the tempo differs (1.1-1.7x vs V8's
> 1.5-2.5x). A tempo-matched V15 variant should be bit-identical to the original V8
> seed-42."

This document investigates that claim using git archaeology, AST analysis, structural
code comparison, and empirical audio rendering with controlled variants.

---

## 1. Existing MP3 File Comparison

Both files exist in the repo, both rendered with seed 42, 30-minute duration:

| File | Size | MD5 |
|------|------|-----|
| `cosmic_radio_v8.mp3` | 43,201,768 | `8ee37d1065ff443c03a3457187bbad2a` |
| `cosmic_radio_v15.mp3` | 43,201,768 | `08dc1c37eb5c7d2396c9f289acb41e1d` |

**Same size, different content.** 42,689,046 bytes differ — 98.8% of the file.

---

## 2. Was numpy Available When V8 Was Rendered?

### The Honest Answer: Unknown

The v0.8.0 session log was **reconstructed retroactively** from git history (the
original session crashed due to a Claude Code iOS app UI bug). The reconstructed log
claims "Render time: ~6 minutes (numpy-accelerated)" but this is an inference, not
an observation.

### Evidence For numpy Being Available

- v0.6.0 session log references "numpy-accelerated pitch shifting" and "Numpy-vectorized
  pitch shifting, mixing, and filtering" — numpy was in use by v0.6.0
- Commit 45791bd (numpy acceleration) was made 9 minutes before commit 88a543d
  (V8 MP3 render) — the numpy code was in place
- The reconstructed session log specifically claims numpy was used for the render

### Evidence Against

- The reconstructed log is speculative, not contemporaneous
- Claude Code sessions run in sandboxed gVisor environments — package availability
  depends on the specific container image, which may differ between sessions
- No `pip install numpy` command is recorded in the session log

### Why This Matters

numpy and pure Python synthesis produce **numerically different output** (confirmed
empirically — see Section 5). If the original V8 MP3 was rendered with numpy,
comparing it against a pure-Python V15 render is comparing apples to oranges
regardless of tempo matching.

**The empirical approach resolves this**: render both numpy-on and numpy-off variants
and compare against the existing MP3.

---

## 3. Code Path Analysis

### AST Structure

```
RadioEngineV8 (line 3356) — inherits from RadioEngine:
  __init__, _plan_segments_v8, _render_segment, _patch_mood_init, render, render_streaming

RadioEngineV15 (line 6193) — inherits from RadioEngineV8:
  _compute_tempo_multiplier, _render_segment
```

V15 inherits `__init__`, `_plan_segments_v8`, `_patch_mood_init`, `render`, and
`render_streaming` from V8. It overrides only two methods.

### Three Code Differences Found

#### Difference 1: Tempo Formula (Intentional)

V8 inherits `RadioEngine._compute_tempo_multiplier`:
```python
# Range: 1.5-2.5x (hash-based)
return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)
```

V15 overrides with V12's density-aware tempo:
```python
# Range: 1.1-1.7x, further clamped by density
base = 1.1 + 0.6 * (int(h, 16) / 0xFFFFFFFF)
```

#### Difference 2: Variable Naming (Cosmetic)

```
V8:  cg = min(int(0.002 * SAMPLE_RATE), len(samps) // 4)
V15: click_guard = min(int(0.002 * SAMPLE_RATE), len(samps) // 4)
```

Same computation, different variable name. No impact on output.

#### Difference 3: Double Anti-Hiss/Subsonic Filter (BUG — Fixed in V17)

V15's `_render_segment` applied `anti_hiss` and `subsonic_filter` per-segment.
V8's `_render_segment` does NOT — V8 applies them once in `render()` at the master
level.

Since V15 inherits V8's `render()`, the filters were applied **twice**:
1. Per-segment inside `_render_segment`
2. Once more at master level in `render()`

This bug was discovered and **fixed in V17** by removing the per-segment filter
application from V15's `_render_segment`.

**Streaming path nuance**: For 30-minute renders (duration > 660s), the code uses
`render_streaming()` which does NOT call `render()`. In the streaming path:
- V8: No anti-hiss/subsonic at any level
- V15 (pre-fix): Anti-hiss/subsonic per-segment only
- V15 (post-fix): No anti-hiss/subsonic (matching V8's streaming behavior)

---

## 4. Render Path Summary

### `render()` path (clips ≤ 660s, used by comparison script)

| Engine | Synthesis | Tempo | Per-segment filters | Master filters |
|--------|-----------|-------|---------------------|----------------|
| V8 (numpy on) | `_synth_colored_note_np` | 1.5-2.5x | None | anti-hiss + subsonic |
| V8 (numpy off) | `factory.synthesize_colored_note` | 1.5-2.5x | None | anti-hiss + subsonic |
| V15 (pre-fix) | `factory.synthesize_colored_note` | 1.1-1.7x | anti-hiss + subsonic | anti-hiss + subsonic |
| V15 (post-fix) | `factory.synthesize_colored_note` | 1.1-1.7x | None | anti-hiss + subsonic |

### `render_streaming()` path (30-min MP3s in repo)

| Engine | Synthesis | Tempo | Per-segment filters | Master filters |
|--------|-----------|-------|---------------------|----------------|
| V8 | depends on HAS_NUMPY | 1.5-2.5x | None | None |
| V15 (pre-fix) | `factory.synthesize_colored_note` | 1.1-1.7x | anti-hiss + subsonic | None |
| V15 (post-fix) | `factory.synthesize_colored_note` | 1.1-1.7x | None | None |

---

## 5. Empirical Results

### Test Configuration

- Duration: 30 seconds per variant (via `render()` path)
- Seed: 42
- numpy version: 2.4.2
- Six variants rendered, compared pairwise

### Variant Descriptions

| Label | Engine | numpy | Tempo | Segment filters |
|-------|--------|-------|-------|-----------------|
| V8+numpy | RadioEngineV8 | ON | V8 (1.5-2.5x) | None |
| V8 pure | RadioEngineV8 | OFF | V8 (1.5-2.5x) | None |
| V15 own | RadioEngineV15 | OFF | V15 (1.1-1.7x) | anti-hiss+subsonic (pre-fix) |
| V15+V8tempo | RadioEngineV15 | OFF | V8 (1.5-2.5x) | anti-hiss+subsonic (pre-fix) |
| V15+V8full | RadioEngineV15 | OFF | V8 (1.5-2.5x) | V8's _render_segment used |
| V15+V8tempo+numpy | RadioEngineV15 | ON | V8 (1.5-2.5x) | anti-hiss+subsonic (pre-fix) |

### Pairwise Comparison Results

#### V8+numpy vs V8 pure Python

| Metric | Value |
|--------|-------|
| **Bit-identical** | **NO** |
| Left max sample diff | 0.3487 |
| Right max sample diff | 0.2656 |
| Left RMS diff | 0.0361 |
| PCM16 differ | 2,636,568 (99.6%) |

**numpy and pure Python produce materially different audio.** The harmonic summation
order and floating-point accumulation differ, producing audibly identical but
numerically distinct output.

#### V8 pure vs V15 (own tempo, pre-fix)

| Metric | Value |
|--------|-------|
| **Bit-identical** | **NO** |
| Left max sample diff | 1.5838 |
| Right max sample diff | 1.1643 |
| Left RMS diff | 0.2089 |
| PCM16 differ | 2,644,758 (100.0%) |

Largest differences — tempo + double-filter both contributing.

#### V8 pure vs V15+V8tempo (tempo matched, pre-fix)

| Metric | Value |
|--------|-------|
| **Bit-identical** | **NO** |
| Left max sample diff | 0.5534 |
| Right max sample diff | 0.3950 |
| Left RMS diff | 0.0697 |
| PCM16 differ | 2,643,231 (99.9%) |

Tempo matched but double-filter still causes differences.

#### V8 pure vs V15+V8tempo+V8render (tempo matched, V8's render_segment)

| Metric | Value |
|--------|-------|
| **Bit-identical** | **YES** |
| Max sample diff | 0.0000000000 |
| RMS diff | 0.0000000000 |
| PCM16 differ | 0 (0.0%) |

**PERFECT BIT-IDENTITY.** When all code paths are matched (same tempo, same
`_render_segment` without double-filter), V15 produces output identical to V8
at every single sample.

#### V8+numpy vs V15+V8tempo+numpy

| Metric | Value |
|--------|-------|
| **Bit-identical** | **NO** |
| Left max sample diff | 0.5702 |
| Right max sample diff | 0.4168 |
| Left RMS diff | 0.0774 |
| PCM16 differ | 2,643,801 (99.9%) |

Even with numpy on both sides and tempo matched, V15's double-filter (pre-fix)
causes near-total divergence.

---

## 6. Conclusions

### The Original Claim

> "A tempo-matched V15 variant should be bit-identical to the original V8 seed-42."

**Verdict: Conditionally TRUE.**

The claim is correct **in principle** — the synthesis path is identical (pure Python
or numpy, whichever is used). When tempo AND the filter pipeline are both matched,
the output is bit-for-bit identical (zero sample difference).

However, V15 as shipped had a double-filter bug that caused per-segment anti-hiss
and subsonic application on top of V8's master-level application. This bug was the
remaining difference after tempo matching. **Fixed in V17.**

### Key Findings

1. **numpy vs pure Python produces different audio** (max diff 0.35, RMS diff 0.036).
   Whether the original V8 MP3 used numpy is unknown — the session log was reconstructed.

2. **The double-filter bug in V15** was the hidden barrier to bit-identity. With it
   fixed, tempo is the ONLY functional difference between V8 and V15.

3. **V15's raison d'être was partially a red herring**: V15 claimed to restore "true
   original V8 synthesis" by forcing the pure Python path. But if numpy was unavailable
   (as may have been the case), V8 was already using that path. If numpy WAS available,
   then V15 correctly forces a different (pure Python) path — but one that produces
   different audio from what V8 actually rendered.

### What Would Be Needed for True V8 MP3 Reproduction

To produce an MP3 bit-identical to `cosmic_radio_v8.mp3` in the repo:

1. Determine whether numpy was available during the original render (unknown)
2. Use the same numpy version if it was (unknown which version)
3. Use V8's tempo formula (1.5-2.5x)
4. Use `render_streaming()` path (30-min duration > 660s threshold)
5. Same ffmpeg/lame version for WAV→MP3 encoding
6. MP3 metadata (timestamps, encoder version) would still differ

**Full reproduction is likely impossible** due to the lost session context and
potential environment differences.

---

## 7. Comparison Script

```bash
# Run the full comparison suite
python apps/audio/compare_v8_v15.py --duration 30 --seed 42

# Include MP3 comparison (requires ffmpeg)
python apps/audio/compare_v8_v15.py --duration 30 --seed 42 --compare-mp3
```

---

## Appendix: File Ancestry

```
commit 348bf29  V8 created (pure Python synthesis)
commit 45791bd  numpy acceleration added to V8 (~7x speedup)
commit 56ba114  V9 (expanded instruments)
commit c882380  V10 (GM-timbre-aware)
commit 48b0457  V11 (audio quality overhaul)
commit 38dec25  V12 (natural instrument character, parallel render)
commit 3a582f3  V13 (V8 core restoration + V12 tempo)
commit 8ec9882  V14 (full palette serial render)
commit e4058ff  V15 + V16 (true original V8 synthesis)
```

## Appendix: numpy Availability Timeline

| Version | Session Log | numpy Evidence |
|---------|-------------|----------------|
| v0.6.0 | Contemporaneous | "numpy-accelerated pitch shifting" — numpy was in use |
| v0.7.0 | Contemporaneous | No numpy mention |
| v0.8.0 | **Reconstructed** | Claims "numpy-accelerated" render (~6 min) — speculative |
| v0.9.0+ | Contemporaneous | numpy code present but HAS_NUMPY fallback in place |
| v0.15.0 | Contemporaneous | Forces pure Python path regardless of numpy |
| v0.17.0 | Contemporaneous | numpy 2.4.2 installed; empirical comparison performed |
