# V11 Radio Engine Plan — Comprehensive Audio Quality Overhaul

**Date**: 2026-03-06
**Author**: Claude (session claude/resume-v9-document-v8-6yhAe)
**Status**: PLAN — awaiting user approval before code mutation

---

## 1. Problem Summary (from user feedback on v10 random-seed output)

The user reported these issues with `cosmic_radio_v10_random.mp3`:

1. **Excessive dissonance** — not enough harmonic consonance enforcement
2. **Instruments not playing together well** — voices not aligning rhythmically
3. **Poor harmony usage** — chords not forming coherent harmonic progressions
4. **Beat/bar misalignment** — notes not snapping to expected metric grid
5. **Loud sharp noise bursts** ("like tuning past a radio station at full volume") — sudden volume spikes / harsh transients even within a mood segment
6. **Multiple instruments not layering properly** — voices not blending, competing instead of complementing

---

## 2. Root Cause Analysis (from full code audit of radio_engine.py, 4768 lines)

### 2.1 The "Radio Static at Full Volume" Problem — CRITICAL

**Root cause**: The `_mix_mono()` method (line 2727) applies `pan * v_gain * 4` as the pan parameter. When `pan` values range from -0.6 to +0.6 (v10, line 4110) and `v_gain` = `voice_gain * 2.5` (for solo sections, line 4282), and `voice_gain = 0.25 / n_voices`, the effective pan parameter fed to `_mix_mono` can be:

```
pan * v_gain * 4 = 0.6 * (0.25/4 * 2.5) * 4 = 0.6 * 0.625 = 0.375
```

But `_mix_mono` (line 2727) uses this value as:
```python
l_gain = math.cos((pan + 1) * math.pi / 4)
r_gain = math.sin((pan + 1) * math.pi / 4)
```

When the pan value passed is `pan * v_gain * 4`, this creates a **multiplicative gain chain** that's inconsistent:
- The `0.25` at line 2737-2738 is an additional scaling factor
- Combined with multiple voices adding to the same buffer positions
- With 4-6 voices each contributing, summed amplitude can easily exceed 1.0 before the final limiter

The **real danger** is at segment boundaries and during loop crossfade (lines 4345-4361): if loop content has high amplitude and the crossfade zones overlap, the additive nature causes sudden volume spikes. The `math.tanh()` in the streaming renderer (line 2212) soft-clips, but this creates the characteristic "radio static" distortion — a hard `tanh` on a sudden +3dB spike sounds like clipping/static.

**Additionally**: The reverb (Schroeder, lines 1760-1809) uses comb filter feedback gains of 0.75, 0.72, 0.70, 0.68. These are quite high — they can cause resonant peaks that amplify certain frequencies dramatically, especially when the input already has stacked harmonics from 4-6 simultaneous voices.

### 2.2 The Dissonance Problem

**Root cause**: Multiple voices independently build chords at different octave registers (line 4301-4305), each snapped to scale individually. However, the snap-to-scale operation doesn't consider **inter-voice consonance**. Voice 1 might play C-E-G at -24 semitones offset while Voice 3 plays D-F#-A at +12 offset — these are in the same scale but form a dissonant composite when stacked vertically.

The Helmholtz/Hartmann consonance enforcement (lines 2356-2382) only checks **within a single chord**, not across multiple voices playing simultaneously. When 4-6 voices each build independent chords from the same MIDI note, the resulting composite harmony is random — sometimes consonant, sometimes extremely dissonant.

**The `freq_mult` problem**: InstrumentFactory (line 668) assigns random `freq_mult` values from `[0.25, 0.5, 0.5, 1.0, 1.0, 1.0, 2.0, 2.0, 4.0]`. A `freq_mult` of 0.25 shifts the fundamental **two octaves down**, while 4.0 shifts it **two octaves up**. When `synthesize_colored_note` (line 787) applies `f = freq` for the base tone but `freq * instr['freq_mult']` for the color tone, the coloring can add frequencies that are octaves away from the intended note, creating phantom fundamentals and inter-voice beating.

### 2.3 The Beat/Bar Alignment Problem

**Root cause**: The v10 `_render_segment` (line 4166) quantizes notes to a bar grid, BUT the quantization happens BEFORE the rondo section builder spreads notes across multiple sections. The rondo builder (line 4236) then offsets each section by `segment_duration` seconds (line 4317: `section_offset_sec += segment_duration`). This means:

1. Notes are quantized to bars
2. Then redistributed across rondo sections (ABACA etc.)
3. Each section starts at an offset of `sec_start = int(section_offset_sec * SAMPLE_RATE)`
4. BUT `section_offset_sec` accumulates by `segment_duration` (the MIDI segment duration), not by the quantized bar duration

If `segment_duration` doesn't align exactly with a whole number of bars, each rondo section starts slightly off-grid. Over 5-7 rondo sections, the drift accumulates to audible misalignment.

**The arpeggio timing issue**: Arpeggiated sections (lines 2463-2476) divide each chord's duration equally among arpeggio notes: `arp_dur = dur / max(n_arp, 1)`. This doesn't respect the beat grid — a quarter-note chord arpeggiated into 3 notes gives triplet timing, but if the bar is in 4/4, these triplets don't align with the 16th-note grid.

### 2.4 The "Instruments Not Playing Together" Problem

**Root cause**: Each voice in v10 is assigned a **random** coloring instrument from the full 537-instrument pool (v8, line 3558: `voice_instruments = [rng.choice(self.instruments) for _ in voice_configs]`). But v10 bypasses this — it uses `_synth_gm_note_np` (line 4310) instead of `synthesize_colored_note`. The GM timbre profiles (line 3871) are well-designed BUT:

1. **No shared ADSR coordination**: A `synth_pad` voice has attack=0.2s while a `mallets` voice has attack=0.001s. Playing the same chord simultaneously, the mallet note punches through immediately while the pad swells in over 200ms. This creates the impression of instruments not "playing together" — their note onsets don't align perceptually.

2. **No velocity balancing across families**: All voices get the same velocity from MIDI data. But a brass profile with 8 harmonics at high amplitude will be perceptually much louder than a pipe profile with 4 harmonics.

3. **Register conflicts**: The fixed offset pool `[-24, -12, 0, 0, 12, 24]` (line 4222) means two voices always share the `0` offset, playing in the same register. With different timbres but same frequency range, they create masking and muddiness rather than blend.

### 2.5 The Harmony Problem

**Root cause**: The chord progression system (lines 2300-2383) builds chords from scale degrees using a lookup table, which is sound. However:

1. **No voice leading**: When moving from chord 1 to chord 2, each note is independently snapped to scale. There's no attempt at smooth voice leading (moving each note to the nearest available note in the new chord). This creates jagged leaps in all voices simultaneously.

2. **No harmonic rhythm**: Chords change whenever MIDI notes change (determined by source MIDI timing), not on beat boundaries. A chord can change on the "and" of beat 3, which sounds unstable without intentional syncopation.

3. **Parallel motion**: All voices move in parallel (same chord for all), which sounds like a block harmonium rather than independent orchestral parts.

---

## 3. V11 Architecture — Proposed Changes

### 3.1 Master Gain Architecture (fixes "radio static" + volume spikes)

**New approach**: Per-voice peak-normalized gain staging with a master bus limiter.

```python
class GainStage:
    """Per-voice gain normalization + master bus limiting."""

    def __init__(self, n_voices, headroom_db=-3.0):
        self.n_voices = n_voices
        self.headroom = 10 ** (headroom_db / 20.0)  # -3dB = 0.708
        self.voice_gain = self.headroom / max(n_voices, 1)

    def normalize_voice(self, samples, target_rms=0.15):
        """Normalize a voice to target RMS, then apply voice gain."""
        rms = sqrt(sum(s*s for s in samples) / len(samples))
        if rms > 0.001:
            scale = target_rms / rms
            scale = min(scale, 2.0)  # Don't boost more than 6dB
            return [s * scale * self.voice_gain for s in samples]
        return [s * self.voice_gain for s in samples]

    def master_limit(self, left, right, threshold=0.85, release_ms=50):
        """Brick-wall lookahead limiter on the master bus."""
        # ...
```

Key changes:
- **Remove the `pan * v_gain * 4` multiplication** in `_mix_mono` calls — this is the primary gain confusion
- Each voice is RMS-normalized to a target level before mixing
- Voices are summed, then a master limiter keeps peaks under -1dB
- Reverb send is post-gain, not post-mix (prevents resonant amplification)

### 3.2 Harmonic Consonance Engine (fixes dissonance)

**New approach**: Inter-voice consonance checking, not just intra-chord.

```python
class ConsonanceEngine:
    """Manages harmonic relationships between simultaneous voices."""

    # Consonance scores (0=dissonant, 1=perfect)
    INTERVAL_CONSONANCE = {
        0: 1.0,   # unison
        1: 0.05,  # minor 2nd (harsh)
        2: 0.3,   # major 2nd
        3: 0.7,   # minor 3rd
        4: 0.75,  # major 3rd
        5: 0.8,   # perfect 4th
        6: 0.15,  # tritone
        7: 0.95,  # perfect 5th
        8: 0.7,   # minor 6th
        9: 0.75,  # major 6th
        10: 0.3,  # minor 7th
        11: 0.2,  # major 7th
    }

    def score_composite(self, all_voice_notes):
        """Score the consonance of all notes sounding simultaneously."""
        all_notes = []
        for voice_notes in all_voice_notes:
            all_notes.extend(voice_notes)

        if len(all_notes) < 2:
            return 1.0

        total_score = 0
        pairs = 0
        for i in range(len(all_notes)):
            for j in range(i+1, len(all_notes)):
                interval = abs(all_notes[i] - all_notes[j]) % 12
                total_score += self.INTERVAL_CONSONANCE[interval]
                pairs += 1

        return total_score / max(pairs, 1)

    def adjust_for_consonance(self, voice_chords, root, scale, min_score=0.55):
        """Adjust voice chords until composite consonance exceeds threshold."""
        # ... iterative adjustment
```

Key changes:
- Before rendering, compute composite consonance across all voices
- If score < 0.55, adjust the most dissonant voice by shifting it to a consonant voicing
- Bass voice always gets the root or fifth (no exceptions)
- Eliminate `freq_mult` from coloring — use it only for octave transposition (1.0, 0.5, 2.0 only)

### 3.3 Bar-Aligned Rendering (fixes beat/bar alignment)

**New approach**: All timing goes through a `BarGrid` that enforces metric regularity.

```python
class BarGrid:
    """Absolute time grid for bar/beat alignment."""

    def __init__(self, tempo, beats_per_bar, beat_unit=4):
        self.beat_dur = 60.0 / tempo
        self.bar_dur = self.beat_dur * beats_per_bar
        self.sixteenth = self.beat_dur / 4

    def snap_onset(self, t_sec, resolution='16th'):
        """Snap a time to the nearest grid position."""
        if resolution == '16th':
            grid = self.sixteenth
        elif resolution == '8th':
            grid = self.beat_dur / 2
        elif resolution == 'beat':
            grid = self.beat_dur
        elif resolution == 'bar':
            grid = self.bar_dur
        return round(t_sec / grid) * grid

    def section_start(self, section_idx, bars_per_section):
        """Get exact bar-aligned start time for a rondo section."""
        return section_idx * bars_per_section * self.bar_dur
```

Key changes:
- Rondo sections start at bar boundaries, not at accumulated `segment_duration` offsets
- All note onsets are snapped to the 16th-note grid
- Arpeggio subdivisions are quantized to grid subdivisions (8th or 16th)
- `section_offset_sec` is replaced by `grid.section_start()`

### 3.4 Orchestral Voice Coordination (fixes "not playing together")

**New approach**: Voices are assigned complementary roles with coordinated envelopes.

```python
class OrchestratorV11:
    """Coordinates multiple voices into a coherent ensemble."""

    ROLE_ASSIGNMENTS = {
        # (register_offset, rhythmic_role, gain_weight)
        'foundation':  (-12, 'sustained', 0.8),   # Bass/cello
        'harmony_low': (0,   'chordal',   0.6),    # Viola/horn
        'harmony_mid': (0,   'chordal',   0.5),    # Violin 2/clarinet
        'melody':      (12,  'melodic',   1.0),    # Violin 1/flute
        'color':       (12,  'textural',  0.3),    # Bells/pad
    }

    def assign_roles(self, voice_configs):
        """Assign orchestral roles ensuring complementary voicing."""
        roles = list(self.ROLE_ASSIGNMENTS.keys())
        for i, vc in enumerate(voice_configs):
            role = roles[i % len(roles)]
            role_cfg = self.ROLE_ASSIGNMENTS[role]
            vc['register_offset'] = role_cfg[0]
            vc['rhythmic_role'] = role_cfg[1]
            vc['gain_weight'] = role_cfg[2]

    def coordinate_attacks(self, voice_profiles):
        """Ensure all voices have compatible attack times.

        Foundation and melody get fast attacks.
        Harmony voices get slightly slower to avoid masking.
        """
        # ...
```

Key changes:
- Fixed role assignment (foundation, harmony_low, harmony_mid, melody, color) instead of random assignment
- Each role has a specific register offset — no more two voices at offset 0
- Gain weights: melody=1.0, foundation=0.8, harmony=0.5-0.6, color=0.3
- Attack coordination: all voices within 50ms of each other (except color, which swells)
- **Voice leading**: When chords change, each voice moves to the nearest available note

### 3.5 Reverb & Effects Overhaul (fixes resonant peaks)

Key changes:
- Reduce comb filter feedback from 0.70-0.75 to 0.55-0.65 (less resonance)
- Apply reverb AFTER per-voice normalization, not after summing
- Cap reverb wet at 0.20 (from 0.30) to prevent washout
- Add a pre-reverb highpass at 150 Hz (prevent low-frequency mud)
- Reduce early reflection amplitudes from 0.08-0.35 to 0.05-0.20

### 3.6 Instrument Selection Quality Gate

Key changes:
- **Eliminate `noise_perc` instruments from harmonic voices** — only allow in rhythm role
- **Cap `noise_level` at 0.02** for melodic/harmonic instruments (currently 0.0-0.06, line 681)
- **Eliminate `distortion > 0.5`** for instruments used in non-solo voices
- **Fix `freq_mult`**: Only allow `[0.5, 1.0, 2.0]` for v11 (remove 0.25 and 4.0 which cause extreme register shifts that clash)
- **GM timbre selection**: Prefer high-quality families (strings, brass, woodwinds, keys, synth_pad) — avoid `synth_fx` (which has inharmonic partials) except in designated "texture" voice slots

### 3.7 Streaming Renderer Fix

The streaming renderer (line 2105) applies `math.tanh()` directly to each sample before writing. This is a **hard nonlinearity** that introduces harmonics (distortion) proportional to how much the input exceeds 1.0. Replace with:

```python
# Instead of: li = int(_tanh(lv) * 32767)
# Use soft-knee limiter:
def _soft_limit(x, knee=0.8):
    ax = abs(x)
    if ax <= knee:
        return x
    sign = 1 if x >= 0 else -1
    excess = ax - knee
    return sign * (knee + (1.0 - knee) * (1.0 - math.exp(-excess * 3.0)))
```

---

## 4. Implementation Order

### Phase 1: Gain Architecture (most impactful — fixes noise bursts)
1. Create `GainStage` class with per-voice normalization + master limiting
2. Remove `pan * v_gain * 4` from `_mix_mono` calls in V10's `_render_segment`
3. Replace `tanh` in streaming renderer with soft-knee limiter
4. Lower reverb feedback gains

### Phase 2: Harmonic Consonance (fixes dissonance)
5. Create `ConsonanceEngine` with inter-voice consonance scoring
6. Add composite consonance check before rendering each time-slice
7. Restrict `freq_mult` to `[0.5, 1.0, 2.0]`
8. Cap `noise_level` and `distortion` for harmonic voices

### Phase 3: Rhythmic Alignment (fixes beat/bar issues)
9. Create `BarGrid` class for absolute metric timing
10. Fix rondo section start times to use bar-aligned offsets
11. Fix arpeggio timing to use grid-quantized subdivisions
12. Ensure `segment_duration` is always a whole number of bars

### Phase 4: Orchestral Coordination (fixes "not playing together")
13. Create `OrchestratorV11` with role assignments
14. Implement voice leading (min-movement between chords)
15. Add attack coordination across voices
16. Add perceptual loudness balancing (not just amplitude)

### Phase 5: Polish & Quality
17. Reduce reverb wet mix and early reflection amplitudes
18. Add pre-reverb highpass filter at 150 Hz
19. Instrument quality gate: exclude noisy/harsh instruments from harmonic roles
20. Increase crossfade duration at loop boundaries to 4-6 seconds
21. Add a final multiband compressor on the master bus

---

## 5. New Class: RadioEngineV11

```python
class RadioEngineV11(RadioEngineV10):
    """V11: Gain-staged, harmonically coherent, bar-aligned orchestral radio.

    Key improvements over v10:
    - Per-voice RMS normalization + master bus limiting (no more clipping/static)
    - Inter-voice consonance engine (no more random dissonance)
    - BarGrid-aligned rendering (notes/sections land on beat grid)
    - Orchestral role assignment (voices complement, not compete)
    - Reduced reverb resonance + pre-reverb highpass
    - Soft-knee limiting in streaming renderer (replaces tanh distortion)
    - Quality-gated instrument selection (no noise_perc in harmonic voices)
    """
```

---

## 6. Testing Strategy

1. **Generate 30-second test clip** with seed=42, analyze spectrally
2. **Compare v10 vs v11** peak levels, RMS, zero-crossing rates, HF/LF ratios
3. **Verify beat alignment**: Check that note onsets fall on 16th-note grid
4. **Verify consonance**: Score all simultaneously-sounding notes
5. **Verify no clipping**: Peak < 0.95 at all points
6. **Generate full 30-minute MP3** with seed=42 and random seed
7. Run existing test suite: `python -m pytest apps/audio/test_radio_engine.py -v`

---

## 7. Estimated Size

- New classes: `GainStage`, `ConsonanceEngine`, `BarGrid`, `OrchestratorV11`, `RadioEngineV11`
- Modifications to: `_mix_mono`, streaming renderer, `SmoothingFilter.apply_reverb`, `InstrumentFactory.generate_instrument`
- New helper function: `generate_radio_v11_mp3`
- Estimated: ~400-500 new lines, ~50 modified lines
- The file will grow from ~4768 to ~5250 lines

---

## 8. Risk Assessment

- **Low risk**: Gain staging changes — straightforward math
- **Medium risk**: Consonance engine — could over-constrain harmony if threshold too high
- **Medium risk**: BarGrid — must handle time signatures correctly (especially compound/complex)
- **Low risk**: Orchestral roles — well-defined assignment, no complex logic
- **Migration**: v10 is preserved unchanged; v11 is a new subclass
