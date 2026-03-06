# v0.13.0 Plan — Audio Engine V13: V8 Core Restoration with V12 Tempo

## Date: 2026-03-06 15:40 CT

## Context

User reports that v12 has a pronounced, distracting bitcrusher/spiky effect compared to v8.
The v8 audio was acceptable — less pronounced bitcrusher artifacts. The v12 is too loud and
harsh in comparison.

## Root Cause Analysis (from code review)

RadioEngineV12 inherits from RadioEngineV8 but adds:
1. **Double soft-knee limiting**: `master_limit(knee=0.80)` applied per-segment in
   `_render_segment`, THEN again in the streaming WAV writer. This double compression
   is the primary bitcrusher cause.
2. **Expanded instrument palette**: 15 family pools vs V8's 5 — more spectral energy
   accumulates, hitting the limiter harder.
3. **Slower tempo** (1.1-1.7x vs V8's 1.5-2.5x): Notes sustain longer, more overlap,
   more amplitude accumulation.

## Plan

### What to keep from v12
- V12's tempo multiplier (1.1-1.7x range, density-aware) — user explicitly wants "newer tempo"

### What to revert to v8
- V8's instrument families (5 pools, not 15)
- V8's synthesis algorithms (no per-segment limiting, no double limiting)
- V8's volume/gain characteristics (no GainStage.master_limit per segment)
- V8's mixing approach

### Implementation: RadioEngineV13
- Inherit from RadioEngineV8 (same as v12 did)
- Override ONLY `_compute_tempo_multiplier` to use v12's density-aware tempo
- Do NOT override `_render_segment` (use v8's version directly — no master_limit)
- Do NOT override `_choose_gm_instruments` (use v8's 5-pool version)
- Keep v8 fade/morph durations
- Use v8's `render()` method (anti-hiss + subsonic but no per-segment limiting)

### Version bump
- Bump to v0.13.0

### Render
- Two MP3s: seed 42 and random seed
- Push to branch and provide raw GitHub URLs

## Milestones
- [ ] Housekeeping complete
- [ ] Spectral analysis confirms issue
- [ ] V13 engine implemented
- [ ] Tests pass
- [ ] MP3s rendered and pushed
- [ ] URLs provided
