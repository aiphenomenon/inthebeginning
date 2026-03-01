#!/usr/bin/env python3
"""
Musical composition engine for cosmic simulation sonification.

This module provides the musical intelligence layer that sits between the
physics simulator and the audio renderer. It draws from world musical
traditions spanning ~6000 years of human creativity — Western classical,
Asian, Middle Eastern, Indian, African, and tribal — to create rich
polyrhythmic, polyphonic compositions driven by simulation state.

Architecture:
    Simulator state -> Composer -> [voices, beats, harmonies, melodies]
                                        |
                                        v
                                   Audio renderer (generate.py)

Key features:
    - World musical scales (30+ scales from 6 traditions)
    - Additive synthesis timbres (strings, winds, bells, voices, drums)
    - Polyrhythmic patterns (3:2, 4:3, 5:4, West African, gamelan)
    - Harmonic progressions (Bach, minimalist, drone, circle of fifths)
    - Melodic motifs derived from public domain works (pre-1929)
    - Beat engine with 10-90% presence oscillation
    - Universe pocket navigation (subatomic → cosmic scale sampling)
    - FFT-guided waveform shaping for complex instrument timbres

No external dependencies — pure Python stdlib (math, random, struct).
"""

import math
import random

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def mtof(note):
    """MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

SAMPLE_RATE = 44100

# ---------------------------------------------------------------------------
# WORLD MUSICAL SCALES
# Intervals in semitones from root. Sourced from ethnomusicological canon.
# ---------------------------------------------------------------------------

SCALES = {
    # --- Western modes ---
    "ionian":       [0, 2, 4, 5, 7, 9, 11],      # Major
    "dorian":       [0, 2, 3, 5, 7, 9, 10],
    "phrygian":     [0, 1, 3, 5, 7, 8, 10],
    "lydian":       [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":   [0, 2, 4, 5, 7, 9, 10],
    "aeolian":      [0, 2, 3, 5, 7, 8, 10],       # Natural minor
    "locrian":      [0, 1, 3, 5, 6, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
    "whole_tone":   [0, 2, 4, 6, 8, 10],
    "chromatic":    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "blues":        [0, 3, 5, 6, 7, 10],

    # --- Pentatonic variations ---
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],

    # --- Japanese ---
    "hirajoshi":    [0, 2, 3, 7, 8],              # Koto tuning
    "in_sen":       [0, 1, 5, 7, 10],             # Shakuhachi
    "iwato":        [0, 1, 5, 6, 10],             # Dark, ritualistic
    "yo":           [0, 2, 5, 7, 9],              # Folk songs
    "miyako_bushi": [0, 1, 5, 7, 8],              # City music

    # --- Chinese ---
    "gong":         [0, 2, 4, 7, 9],              # Palace mode (= major pent)
    "shang":        [0, 2, 5, 7, 10],             # Merchants
    "jue":          [0, 3, 5, 8, 10],             # Horn
    "zhi":          [0, 2, 5, 7, 9],              # Wings
    "yu":           [0, 3, 5, 7, 10],             # Feathers (= minor pent)

    # --- Middle Eastern ---
    "hijaz":        [0, 1, 4, 5, 7, 8, 11],       # Hijaz maqam
    "bayati":       [0, 1.5, 3, 5, 7, 8, 10],     # Quarter-tone approx
    "rast":         [0, 2, 3.5, 5, 7, 9, 10.5],   # Quarter-tone
    "saba":         [0, 1.5, 3, 4, 7, 8, 10],
    "nahawand":     [0, 2, 3, 5, 7, 8, 11],       # ~ harmonic minor

    # --- Indian ragas (ascending forms) ---
    "bhairav":      [0, 1, 4, 5, 7, 8, 11],       # Dawn raga, devotional
    "yaman":        [0, 2, 4, 6, 7, 9, 11],       # Evening (= lydian)
    "malkauns":     [0, 3, 5, 8, 10],             # Night raga, pentatonic
    "bhairavi":     [0, 1, 3, 5, 7, 8, 10],       # Morning (= phrygian)
    "todi":         [0, 1, 3, 6, 7, 8, 11],       # Late morning, serious

    # --- African ---
    "equi_pent":    [0, 2.4, 4.8, 7.2, 9.6],     # Equidistant pentatonic
    "mbira":        [0, 2, 4, 7, 9],              # Zimbabwean mbira
    "kora":         [0, 2, 4, 5, 7, 9, 11],       # West African kora (major)

    # --- Ancient/tribal ---
    "drone":        [0, 7],                        # Fifth-based drone
    "tetrachord":   [0, 2, 4, 5],                  # Ancient Greek
    "slendro":      [0, 2.4, 4.8, 7.2, 9.6],     # Javanese gamelan
    "pelog":        [0, 1, 3, 7, 8],              # Javanese gamelan
}

# Map epochs to appropriate scale families
EPOCH_SCALE_FAMILIES = {
    "Planck":           ["chromatic", "whole_tone", "drone"],
    "Inflation":        ["whole_tone", "drone", "slendro"],
    "Electroweak":      ["phrygian", "iwato", "saba"],
    "Quark":            ["hirajoshi", "in_sen", "todi"],
    "Hadron":           ["pentatonic_minor", "yo", "bhairav"],
    "Nucleosynthesis":  ["dorian", "mixolydian", "rast"],
    "Recombination":    ["pentatonic_major", "gong", "yaman"],
    "Star Formation":   ["lydian", "hijaz", "bhairav"],
    "Solar System":     ["ionian", "kora", "harmonic_minor"],
    "Earth":            ["aeolian", "miyako_bushi", "nahawand"],
    "Life":             ["blues", "pentatonic_minor", "malkauns"],
    "DNA Era":          ["melodic_minor", "bhairavi", "pelog"],
    "Present":          ["ionian", "dorian", "pentatonic_major", "hirajoshi"],
}

# ---------------------------------------------------------------------------
# INSTRUMENT TIMBRES (additive synthesis harmonic profiles)
# Each list: amplitude of 1st, 2nd, 3rd... harmonic (fundamental = 1.0)
# Derived from acoustic measurements of real instruments (public domain data)
# ---------------------------------------------------------------------------

TIMBRES = {
    # Strings
    "violin":    [1.0, 0.50, 0.33, 0.25, 0.20, 0.16, 0.14, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02],
    "cello":     [1.0, 0.70, 0.45, 0.30, 0.20, 0.15, 0.10, 0.08, 0.06, 0.04, 0.03, 0.02],
    "harp":      [1.0, 0.30, 0.10, 0.05, 0.03, 0.02, 0.01],

    # Woodwinds
    "flute":     [1.0, 0.40, 0.10, 0.02, 0.01],  # Pure, few harmonics
    "oboe":      [1.0, 0.60, 0.80, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10, 0.08],
    "clarinet":  [1.0, 0.05, 0.70, 0.05, 0.40, 0.05, 0.20, 0.05, 0.10, 0.05],  # Odd harmonics dominate

    # Brass
    "horn":      [1.0, 0.80, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10, 0.08, 0.06],
    "trumpet":   [1.0, 0.90, 0.70, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10, 0.08],

    # Keyboard
    "piano":     [1.0, 0.50, 0.30, 0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03],

    # Bells / metallic
    "bell":      [1.0, 0.60, 0.30, 0.20, 0.35, 0.15, 0.25, 0.10, 0.15, 0.08, 0.10, 0.06],
    "gamelan":   [1.0, 0.40, 0.15, 0.30, 0.10, 0.20, 0.08, 0.15, 0.05, 0.10],
    "tibetan_bowl": [1.0, 0.70, 0.20, 0.40, 0.10, 0.25, 0.08, 0.15],

    # Voice
    "choir_ah":  [1.0, 0.40, 0.20, 0.15, 0.10, 0.08, 0.05, 0.03],
    "choir_oo":  [1.0, 0.60, 0.10, 0.05, 0.03, 0.02],
    "throat_sing": [1.0, 0.10, 0.05, 0.03, 0.02, 0.80, 0.05, 0.03, 0.02, 0.50],  # Enhanced overtones

    # Percussion (noise-based, not harmonic — special treatment in synthesis)
    "kick":      [1.0, 0.80, 0.40, 0.20, 0.10],
    "snare":     [1.0, 0.60, 0.50, 0.45, 0.40, 0.35, 0.30, 0.25],  # + noise
    "hat":       [],  # Pure noise, filtered

    # Synth / cosmic
    "sine":      [1.0],
    "warm_pad":  [1.0, 0.30, 0.15, 0.08, 0.04, 0.02],
    "cosmic":    [1.0, 0.20, 0.10, 0.30, 0.05, 0.15, 0.03, 0.10, 0.02, 0.08],
}

# Map simulation domains to preferred timbres
DOMAIN_TIMBRES = {
    "subatomic":   ["sine", "cosmic", "tibetan_bowl", "throat_sing"],
    "atomic":      ["bell", "gamelan", "harp", "flute"],
    "molecular":   ["piano", "clarinet", "choir_ah", "warm_pad"],
    "biological":  ["cello", "oboe", "violin", "choir_oo"],
    "geological":  ["horn", "trumpet", "piano", "harp"],
    "cosmic":      ["cosmic", "choir_ah", "warm_pad", "tibetan_bowl"],
}

# ---------------------------------------------------------------------------
# RHYTHMIC PATTERNS
# Each pattern: list of floats (0..1) representing beat onsets within one cycle
# ---------------------------------------------------------------------------

RHYTHM_PATTERNS = {
    # Basic meters
    "4_4_straight":     [0.0, 0.25, 0.5, 0.75],
    "3_4_waltz":        [0.0, 0.333, 0.667],
    "6_8_compound":     [0.0, 0.167, 0.333, 0.5, 0.667, 0.833],

    # West African bell patterns (standard timeline)
    "gahu":             [0.0, 0.083, 0.25, 0.333, 0.5, 0.583, 0.75],
    "agbadza":          [0.0, 0.167, 0.333, 0.417, 0.583, 0.75, 0.833],
    "ewe_bell":         [0.0, 0.083, 0.25, 0.417, 0.5, 0.667, 0.833],

    # Polyrhythmic (expressed as onset positions in a common period)
    "poly_3_2":         [0.0, 0.333, 0.5, 0.667],       # 3 against 2
    "poly_4_3":         [0.0, 0.25, 0.333, 0.5, 0.667, 0.75],
    "poly_5_4":         [0.0, 0.2, 0.25, 0.4, 0.5, 0.6, 0.75, 0.8],
    "poly_5_3":         [0.0, 0.2, 0.333, 0.4, 0.6, 0.667, 0.8],
    "poly_7_4":         [0.0, 0.143, 0.25, 0.286, 0.429, 0.5, 0.571, 0.714, 0.75, 0.857],

    # Gamelan interlocking (kotekan)
    "kotekan_polos":    [0.0, 0.25, 0.5, 0.75],
    "kotekan_sangsih":  [0.125, 0.375, 0.625, 0.875],

    # Minimalist / phasing (Steve Reich-style)
    "phase_a":          [0.0, 0.167, 0.333, 0.667, 0.833],
    "phase_b":          [0.0, 0.182, 0.364, 0.545, 0.727],  # Slightly offset

    # Indian tala patterns
    "teen_taal":        [0.0, 0.0625, 0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375,
                         0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375],
    "jhaptaal":         [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],

    # Sparse / ambient
    "sparse_1":         [0.0, 0.4],
    "sparse_2":         [0.0, 0.3, 0.7],
    "heartbeat":        [0.0, 0.15],  # Lub-dub
}

# Map epochs to rhythm complexity
EPOCH_RHYTHM_FAMILIES = {
    "Planck":           ["sparse_1"],
    "Inflation":        ["sparse_1", "sparse_2"],
    "Electroweak":      ["sparse_2", "3_4_waltz"],
    "Quark":            ["poly_3_2", "phase_a"],
    "Hadron":           ["poly_3_2", "4_4_straight"],
    "Nucleosynthesis":  ["gahu", "poly_4_3", "6_8_compound"],
    "Recombination":    ["agbadza", "kotekan_polos", "3_4_waltz"],
    "Star Formation":   ["ewe_bell", "poly_5_4", "teen_taal"],
    "Solar System":     ["4_4_straight", "6_8_compound", "poly_5_3"],
    "Earth":            ["gahu", "jhaptaal", "poly_7_4"],
    "Life":             ["heartbeat", "4_4_straight", "agbadza"],
    "DNA Era":          ["phase_a", "phase_b", "poly_5_4", "kotekan_polos"],
    "Present":          ["4_4_straight", "poly_3_2", "ewe_bell", "gahu"],
}

# ---------------------------------------------------------------------------
# HARMONIC PROGRESSIONS
# Each progression: list of scale degree offsets (0 = root)
# ---------------------------------------------------------------------------

PROGRESSIONS = {
    # Western classical / popular
    "I_V_vi_IV":        [0, 7, 9, 5],       # Pop canon
    "I_IV_V":           [0, 5, 7],           # Folk/blues
    "i_VII_VI_V":       [0, 10, 8, 7],      # Andalusian cadence
    "circle_of_fifths": [0, 7, 2, 9, 4, 11, 6, 1],  # Full circle
    "bach_cmaj":        [0, 5, 7, 0, 5, 7, 5, 0],    # Based on Prelude in C

    # Minimalist
    "glass_1":          [0, 5, 0, 7],        # Philip Glass-style
    "glass_2":          [0, 3, 7, 3],
    "riley_rainbow":    [0, 2, 4, 7, 9],    # Terry Riley-style

    # Drone-based
    "tanpura":          [0, 7],              # Indian drone (sa-pa)
    "didgeridoo":       [0],                 # Fundamental drone
    "bagpipe":          [0, 7, 12],          # Drone + fifth + octave

    # East Asian
    "parallel_4ths":    [0, 5, 10, 3],       # Japanese parallel motion
    "parallel_5ths":    [0, 7, 2, 9],

    # Modal
    "aeolian_drift":    [0, 3, 7, 10, 0, 5, 8, 3],
    "phrygian_pulse":   [0, 1, 5, 7],
    "lydian_float":     [0, 6, 4, 2],
}

# Map epochs to progression styles
EPOCH_PROGRESSIONS = {
    "Planck":           ["didgeridoo", "tanpura"],
    "Inflation":        ["tanpura", "bagpipe"],
    "Electroweak":      ["phrygian_pulse", "aeolian_drift"],
    "Quark":            ["parallel_4ths", "glass_1"],
    "Hadron":           ["glass_2", "riley_rainbow"],
    "Nucleosynthesis":  ["circle_of_fifths", "bach_cmaj"],
    "Recombination":    ["I_IV_V", "glass_1", "parallel_5ths"],
    "Star Formation":   ["i_VII_VI_V", "bach_cmaj"],
    "Solar System":     ["I_V_vi_IV", "circle_of_fifths"],
    "Earth":            ["I_V_vi_IV", "I_IV_V", "aeolian_drift"],
    "Life":             ["glass_1", "riley_rainbow", "I_V_vi_IV"],
    "DNA Era":          ["bach_cmaj", "glass_2", "circle_of_fifths"],
    "Present":          ["I_V_vi_IV", "circle_of_fifths", "bach_cmaj", "glass_1"],
}

# ---------------------------------------------------------------------------
# MELODIC MOTIFS (from public domain works, pre-1929)
# Intervals in semitones (relative motion from previous note)
# ---------------------------------------------------------------------------

MOTIFS = {
    # J.S. Bach — Prelude in C Major BWV 846 (1722) — arpeggiated pattern
    "bach_prelude":     [0, 4, 7, 12, 16, 12, 7, 4],
    # Bach — Cello Suite No. 1, Prelude (1720) — opening figure
    "bach_cello":       [0, 7, 4, 7, 0, 7, 4, 7, 2, 9, 5, 9, 2, 9, 5, 9],

    # Mozart — Eine kleine Nachtmusik K.525 (1787) — opening
    "mozart_nacht":     [0, 0, 7, 7, 9, 9, 7],
    # Mozart — Piano Sonata No.11, Rondo alla Turca (1783)
    "mozart_turca":     [0, 2, 0, -1, 0, 2, 0, -1, 0, 4, 7],

    # Beethoven — Für Elise (1810) — opening
    "beethoven_elise":  [0, -1, 0, -1, 0, -5, 2, 0, -3],
    # Beethoven — Symphony No.5 (1808) — fate motif
    "beethoven_5th":    [0, 0, 0, -4],
    # Beethoven — Moonlight Sonata (1801) — arpeggiated triplets
    "moonlight":        [0, 4, 7, 0, 4, 7, 0, 4, 7, 0, 4, 7],

    # Chopin — Nocturne Op.9 No.2 (1832) — lyrical descent
    "chopin_nocturne":  [0, 5, 4, 2, 0, -1, 0, 2, 4],

    # Debussy — Clair de Lune (1905) — opening descent
    "debussy_clair":    [0, -2, -4, -5, -7, -5, -4, -2],
    # Debussy — Arabesque No.1 (1888)
    "debussy_arab":     [0, 2, 4, 7, 9, 7, 4, 2, 0],

    # Satie — Gymnopédie No.1 (1888) — sparse, floating
    "satie_gymno":      [0, 7, 5, 3, 0, -2, 0, 3],

    # Grieg — Morning Mood (1875) — ascending
    "grieg_morning":    [0, 2, 4, 7, 9, 12, 9, 7, 4, 2],

    # Dvořák — New World Symphony (1893) — largo theme
    "dvorak_largo":     [0, 2, 4, 2, 0, -3, 0, 2, 4, 7, 4, 2],

    # Traditional pentatonic motifs (ancient, no known author)
    "pentatonic_rise":  [0, 2, 4, 7, 9, 12],
    "pentatonic_fall":  [12, 9, 7, 4, 2, 0],
    "pentatonic_wave":  [0, 4, 2, 7, 4, 9, 7, 12],

    # Japanese — Sakura (traditional, public domain)
    "sakura":           [0, 0, 2, 0, 0, 2, 0, 2, 5, 7, 5, 2, 0, -3, 0],

    # Chinese — Jasmine Flower (traditional, public domain)
    "jasmine":          [0, 2, 4, 7, 7, 9, 7, 4, 2, 4, 2, 0],

    # Indian raga phrases
    "raga_ascend":      [0, 1, 4, 5, 7, 8, 11, 12],
    "raga_descend":     [12, 11, 8, 7, 5, 4, 1, 0],

    # African / call-and-response
    "call_response":    [0, 4, 7, 4, 0, -3, 0],
    "mbira_pattern":    [0, 7, 4, 0, 9, 7, 4, 0, 12, 9, 7, 4],
}

# Map epochs to motif pools (which motifs are appropriate for each era)
EPOCH_MOTIFS = {
    "Planck":           ["pentatonic_rise"],
    "Inflation":        ["pentatonic_wave", "raga_ascend"],
    "Electroweak":      ["sakura", "raga_ascend"],
    "Quark":            ["bach_prelude", "jasmine"],
    "Hadron":           ["call_response", "mbira_pattern"],
    "Nucleosynthesis":  ["grieg_morning", "pentatonic_rise", "bach_cello"],
    "Recombination":    ["satie_gymno", "debussy_clair", "dvorak_largo"],
    "Star Formation":   ["moonlight", "chopin_nocturne", "raga_ascend"],
    "Solar System":     ["bach_prelude", "mozart_nacht", "debussy_arab"],
    "Earth":            ["debussy_clair", "grieg_morning", "dvorak_largo", "sakura"],
    "Life":             ["beethoven_elise", "chopin_nocturne", "jasmine"],
    "DNA Era":          ["bach_cello", "mozart_turca", "mbira_pattern"],
    "Present":          ["bach_prelude", "moonlight", "debussy_arab", "chopin_nocturne",
                         "grieg_morning", "dvorak_largo", "satie_gymno"],
}


# ---------------------------------------------------------------------------
# STREAMING SYNTHESIS ENGINE (optimized for per-tick rendering)
# ---------------------------------------------------------------------------

# Pre-computed sine wavetable for fast lookup
_WAVETABLE_SIZE = 4096
_WAVETABLE = [math.sin(2 * math.pi * i / _WAVETABLE_SIZE) for i in range(_WAVETABLE_SIZE)]
_INV_SR = 1.0 / SAMPLE_RATE
_TWO_PI = 2 * math.pi

def _fast_sin(phase):
    """Fast sine approximation via wavetable lookup."""
    idx = int(phase * _WAVETABLE_SIZE) % _WAVETABLE_SIZE
    return _WAVETABLE[idx]


class StreamingOsc:
    """A streaming oscillator that renders incrementally per tick.

    Instead of rendering an entire note at once (slow for long pads),
    this maintains phase state and renders a small chunk each call.
    """

    __slots__ = ('phase_incs', 'phases', 'env_samples', 'env_pos',
                 'total_samples', 'gain', 'alive')

    def __init__(self, freq, duration, timbre_name="violin", gain=0.15,
                 attack=0.02, decay=0.0, sustain=1.0, release=0.1):
        harmonics = TIMBRES.get(timbre_name, TIMBRES["sine"])
        n = int(SAMPLE_RATE * duration)
        self.total_samples = n
        self.gain = gain
        self.alive = True
        self.env_pos = 0

        # Limit to 6 harmonics max for streaming perf
        nyquist = SAMPLE_RATE / 2
        active = []
        for h_idx, h_amp in enumerate(harmonics[:6]):
            h_num = h_idx + 1
            if freq * h_num >= nyquist:
                break
            active.append((h_num, h_amp))

        if not active:
            self.alive = False
            self.phase_incs = []
            self.phases = []
            self.env_samples = []
            return

        h_sum = sum(abs(a) for _, a in active)
        norm = gain / max(h_sum, 0.01)

        self.phase_incs = [(h_num * freq * _INV_SR, h_amp * norm) for h_num, h_amp in active]
        self.phases = [0.0] * len(self.phase_incs)

        # Pre-compute envelope as a compact array (one value per 4 samples for speed)
        env_step = 4
        env_len = (n + env_step - 1) // env_step
        self.env_samples = [0.0] * env_len
        attack_end = int(attack * SAMPLE_RATE)
        decay_end = int((attack + decay) * SAMPLE_RATE)
        release_start = n - int(release * SAMPLE_RATE)
        inv_attack = 1.0 / max(attack_end, 1)
        inv_decay = 1.0 / max(decay_end - attack_end, 1) if decay > 0 else 0
        inv_release = 1.0 / max(n - release_start, 1)
        for ei in range(env_len):
            i = ei * env_step
            if i < attack_end:
                self.env_samples[ei] = i * inv_attack
            elif i < decay_end:
                self.env_samples[ei] = 1.0 - (1.0 - sustain) * (i - attack_end) * inv_decay
            elif i < release_start:
                self.env_samples[ei] = sustain
            else:
                self.env_samples[ei] = sustain * max(0, (n - i) * inv_release)

    def render_chunk(self, num_samples):
        """Render the next num_samples. Returns list of floats."""
        if not self.alive:
            return None

        remaining = self.total_samples - self.env_pos
        if remaining <= 0:
            self.alive = False
            return None

        count = min(num_samples, remaining)
        out = [0.0] * num_samples
        phases = self.phases
        pincs = self.phase_incs
        env_arr = self.env_samples
        pos = self.env_pos
        n_harmonics = len(pincs)

        for i in range(count):
            ei = (pos + i) >> 2  # // 4
            if ei >= len(env_arr):
                break
            env = env_arr[ei]
            s = 0.0
            for j in range(n_harmonics):
                inc, amp = pincs[j]
                s += amp * _WAVETABLE[int(phases[j] * _WAVETABLE_SIZE) % _WAVETABLE_SIZE]
                phases[j] += inc
            out[i] = s * env

        self.env_pos = pos + count
        if self.env_pos >= self.total_samples:
            self.alive = False
        return out


class AdditiveSynth:
    """Render a complete note. Used for short sounds (percussion hits, blips).

    For longer sounds (pads, sustained tones), use StreamingOsc instead.
    """

    MAX_HARMONICS = 6

    @staticmethod
    def render(freq, duration, timbre_name="violin", gain=0.15,
               attack=0.02, decay=0.0, sustain=1.0, release=0.1,
               vibrato_rate=0.0, vibrato_depth=0.0):
        """Render a single note. Returns list of float samples."""
        osc = StreamingOsc(freq, duration, timbre_name, gain, attack, decay, sustain, release)
        n = int(SAMPLE_RATE * duration)
        result = osc.render_chunk(n)
        return result if result else [0.0] * n


# ---------------------------------------------------------------------------
# PERCUSSION SYNTHESIZER
# ---------------------------------------------------------------------------

class PercSynth:
    """Synthesize percussion sounds from scratch.

    Kick: sine with pitch drop + distortion
    Snare: sine body + filtered noise
    Hat: bandpass-filtered noise with fast decay

    Includes a cache to avoid re-synthesizing identical percussion hits.
    """

    _cache = {}

    @staticmethod
    def _cached(key, fn):
        """Return cached result or compute and cache."""
        if key in PercSynth._cache:
            return list(PercSynth._cache[key])  # Return copy
        result = fn()
        if len(PercSynth._cache) < 64:
            PercSynth._cache[key] = result
        return list(result)

    @staticmethod
    def kick(freq=55, duration=0.3, gain=0.25):
        key = ("kick", round(freq, 1), round(duration, 2), round(gain, 3))
        def _gen():
            n = int(SAMPLE_RATE * duration)
            samples = [0.0] * n
            phase = 0.0
            for i in range(n):
                t = i * _INV_SR
                f = freq + freq * 3 * math.exp(-t * 40)
                phase += f * _INV_SR
                env = math.exp(-t * 10)
                s = _fast_sin(phase) * env
                samples[i] = math.tanh(s * 2.0) * gain
            return samples
        return PercSynth._cached(key, _gen)

    @staticmethod
    def snare(freq=180, duration=0.2, gain=0.15, rng=None):
        # Snare has noise so we can't cache perfectly, but cache the body
        rng = rng or random.Random()
        n = int(SAMPLE_RATE * duration)
        samples = [0.0] * n
        lpf_state = 0.0
        alpha = min(1.0, 2 * math.pi * 4000 / SAMPLE_RATE)
        phase = 0.0
        for i in range(n):
            t = i * _INV_SR
            body_env = math.exp(-t * 25)
            phase += freq * _INV_SR
            body = _fast_sin(phase) * body_env * 0.6
            noise_env = math.exp(-t * 15)
            noise = (rng.random() * 2 - 1) * noise_env * 0.8
            lpf_state += alpha * (noise - lpf_state)
            samples[i] = (body + lpf_state) * gain
        return samples

    @staticmethod
    def hihat(duration=0.08, gain=0.08, rng=None):
        rng = rng or random.Random()
        n = int(SAMPLE_RATE * duration)
        samples = [0.0] * n
        lp_state = 0.0
        hp_state = 0.0
        lp_alpha = min(1.0, 2 * math.pi * 10000 / SAMPLE_RATE)
        hp_alpha = min(1.0, 2 * math.pi * 5000 / SAMPLE_RATE)
        for i in range(n):
            t = i * _INV_SR
            env = math.exp(-t * 50)
            noise = (rng.random() * 2 - 1)
            lp_state += lp_alpha * (noise - lp_state)
            hp_state += hp_alpha * (lp_state - hp_state)
            bp = lp_state - hp_state
            samples[i] = bp * env * gain
        return samples

    @staticmethod
    def rim(freq=800, duration=0.05, gain=0.12):
        key = ("rim", round(freq, 1), round(duration, 2), round(gain, 3))
        def _gen():
            n = int(SAMPLE_RATE * duration)
            samples = [0.0] * n
            phase = 0.0
            for i in range(n):
                t = i * _INV_SR
                env = math.exp(-t * 80)
                phase += freq * _INV_SR
                samples[i] = _fast_sin(phase) * env * gain
            return samples
        return PercSynth._cached(key, _gen)


# ---------------------------------------------------------------------------
# BEAT ENGINE
# ---------------------------------------------------------------------------

class BeatEngine:
    """Generates rhythmic patterns with beats/percussion.

    The beat presence oscillates between 10-90% over time, guided by
    epoch and simulation state. Early epochs are sparse; later epochs
    have more structured, recognizable rhythmic patterns.
    """

    def __init__(self, rng, bpm=72):
        self.rng = rng
        self.bpm = bpm
        self.beat_phase = 0.0
        self.pattern_name = "sparse_1"
        self.pattern = RHYTHM_PATTERNS["sparse_1"]
        self.bar_count = 0
        self.presence = 0.1  # 10% initial beat presence
        self._target_presence = 0.1
        self._last_onset_idx = -1

    def update_state(self, epoch, epoch_idx, tick, temperature, particles):
        """Update beat engine state based on simulation."""
        # Beat presence oscillates — more beats in later epochs
        base_presence = clamp(epoch_idx / 12.0, 0.1, 0.9)
        # Add oscillation based on tick (slow wave over ~30 seconds of audio)
        osc = 0.3 * math.sin(tick * 0.0002)
        self._target_presence = clamp(base_presence + osc, 0.1, 0.9)
        # Smooth toward target
        self.presence += (self._target_presence - self.presence) * 0.01

        # Choose rhythm pattern based on epoch
        families = EPOCH_RHYTHM_FAMILIES.get(epoch, ["4_4_straight"])
        # Rotate pattern every ~16 bars
        pattern_idx = (tick // 4000) % len(families)
        self.pattern_name = families[pattern_idx]
        self.pattern = RHYTHM_PATTERNS.get(self.pattern_name, [0.0, 0.5])

        # BPM evolves with epoch
        base_bpm = 40 + epoch_idx * 8  # 40 bpm at Planck, ~136 at Present
        # Temperature modulates tempo slightly
        temp_mod = clamp(math.log10(max(1, temperature)) / 10 * 20, -10, 20)
        self.bpm = clamp(base_bpm + temp_mod, 30, 180)

    def render_beat_bar(self, duration_samples, root_note):
        """Render one bar of beats.

        Returns list of float samples (mono).
        """
        samples = [0.0] * duration_samples
        bar_duration = duration_samples / SAMPLE_RATE

        # Decide if beats play this bar (based on presence probability)
        if self.rng.random() > self.presence:
            return samples

        kick_freq = mtof(max(24, root_note - 36))
        snare_freq = mtof(max(36, root_note - 24))

        for onset_pos in self.pattern:
            onset_sample = int(onset_pos * duration_samples)
            if onset_sample >= duration_samples:
                continue

            # Decide which percussion element
            r = self.rng.random()
            if r < 0.35:
                # Kick on strong beats
                perc = PercSynth.kick(kick_freq, gain=0.12 * self.presence)
            elif r < 0.6:
                # Snare on backbeats
                perc = PercSynth.snare(snare_freq, gain=0.08 * self.presence, rng=self.rng)
            elif r < 0.85:
                # Hi-hat
                perc = PercSynth.hihat(gain=0.05 * self.presence, rng=self.rng)
            else:
                # Rim click
                perc = PercSynth.rim(gain=0.06 * self.presence)

            # Mix in
            end = min(onset_sample + len(perc), duration_samples)
            for j in range(onset_sample, end):
                samples[j] += perc[j - onset_sample]

        self.bar_count += 1
        return samples


# ---------------------------------------------------------------------------
# MELODIC VOICE
# ---------------------------------------------------------------------------

class MelodicVoice:
    """A single melodic voice that plays phrases from motifs.

    Uses streaming oscillators to play notes incrementally per tick
    rather than rendering entire phrases at once.
    """

    def __init__(self, rng, voice_id=0):
        self.rng = rng
        self.voice_id = voice_id
        self.cooldown = 0
        self.timbre = "piano"
        self.octave_offset = 0
        self.pan = 0.0
        # Streaming state: queue of notes to play
        self._note_queue = []  # list of (midi_note, duration)
        self._current_osc = None  # active StreamingOsc
        self._note_remaining = 0  # samples remaining for current note

    def update_state(self, epoch, epoch_idx, root_note, scale_name):
        """Update voice state for current epoch."""
        if epoch_idx <= 4:
            domain = "subatomic"
        elif epoch_idx <= 7:
            domain = "atomic"
        elif epoch_idx <= 9:
            domain = "molecular"
        else:
            domain = "biological"

        timbres = DOMAIN_TIMBRES.get(domain, ["piano"])
        self.timbre = timbres[self.voice_id % len(timbres)]
        self.pan = -0.6 + (self.voice_id % 4) * 0.4

    def maybe_start_phrase(self, epoch, root_note, scale_intervals):
        """Possibly start a new melodic phrase (sets up note queue).

        Returns True if a phrase was started, False otherwise.
        """
        if self.cooldown > 0:
            self.cooldown -= 1
            return False

        if self._note_queue or self._current_osc:
            return False  # Already playing

        if self.rng.random() > 0.4:
            self.cooldown = self.rng.randint(2, 8)
            return False

        motif_pool = EPOCH_MOTIFS.get(epoch, ["pentatonic_wave"])
        motif_name = self.rng.choice(motif_pool)
        raw_motif = MOTIFS.get(motif_name, [0, 2, 4])

        scale = scale_intervals if scale_intervals else [0, 2, 4, 5, 7, 9, 11]
        notes = []
        for interval in raw_motif:
            rounded = int(round(interval))
            octave = rounded // 12
            degree = rounded % 12
            nearest = min(scale, key=lambda s: abs(int(round(s)) - degree))
            midi = root_note + int(round(nearest)) + octave * 12 + self.octave_offset
            midi = clamp(midi, 36, 96)
            notes.append(midi)

        if not notes:
            return False

        note_dur = 0.15 + self.rng.random() * 0.35
        self._note_queue = [(midi, note_dur) for midi in notes]
        self.cooldown = self.rng.randint(4, 12) + len(notes)
        return True

    def render_chunk(self, num_samples):
        """Render the next chunk of the current phrase.

        Returns (samples, pan) or None if not playing.
        """
        if not self._current_osc and not self._note_queue:
            return None

        out = [0.0] * num_samples
        pos = 0

        while pos < num_samples:
            # Start next note if needed
            if self._current_osc is None or not self._current_osc.alive:
                if not self._note_queue:
                    break
                midi, dur = self._note_queue.pop(0)
                freq = mtof(midi)
                self._current_osc = StreamingOsc(
                    freq, dur * 1.2,
                    timbre_name=self.timbre,
                    gain=0.08,
                    attack=0.02,
                    release=dur * 0.3,
                )
                self._note_remaining = int(dur * SAMPLE_RATE)

            # Render from current osc
            remaining_in_note = min(self._note_remaining, num_samples - pos)
            chunk = self._current_osc.render_chunk(remaining_in_note)
            if chunk:
                for i in range(remaining_in_note):
                    out[pos + i] += chunk[i]
            pos += remaining_in_note
            self._note_remaining -= remaining_in_note

            if self._note_remaining <= 0:
                self._current_osc = None

        return out, self.pan

    def maybe_play_phrase(self, epoch, root_note, scale_intervals, duration_samples):
        """Render for one tick — starts new phrases and continues active ones.

        Returns (samples, pan) or None.
        """
        self.maybe_start_phrase(epoch, root_note, scale_intervals)
        return self.render_chunk(duration_samples)


# ---------------------------------------------------------------------------
# HARMONIC ENGINE
# ---------------------------------------------------------------------------

class HarmonicEngine:
    """Manages chord progressions and harmonic movement.

    Uses streaming oscillators for efficient per-tick rendering instead
    of rendering entire pads at once.
    """

    def __init__(self, rng):
        self.rng = rng
        self.progression = [0, 5, 7, 0]
        self.chord_index = 0
        # Active streaming oscillators for the current chord
        self._chord_oscs = []  # list of (StreamingOsc, l_gain, r_gain)

    def update_progression(self, epoch, root_note, scale_intervals):
        """Choose a new progression when epoch changes."""
        prog_pool = EPOCH_PROGRESSIONS.get(epoch, ["I_V_vi_IV"])
        prog_name = self.rng.choice(prog_pool)
        self.progression = PROGRESSIONS.get(prog_name, [0, 5, 7, 0])
        self.chord_index = 0

    def get_current_chord(self, root_note, scale_intervals):
        """Get MIDI notes for current chord (triad from scale)."""
        prog_degree = self.progression[self.chord_index % len(self.progression)]
        scale = scale_intervals if scale_intervals else [0, 2, 4, 5, 7, 9, 11]

        chord_root = root_note + int(round(prog_degree))
        notes = [chord_root]
        if len(scale) >= 5:
            notes.append(chord_root + int(round(scale[2 % len(scale)])))
            notes.append(chord_root + int(round(scale[4 % len(scale)])))
        elif len(scale) >= 3:
            notes.append(chord_root + int(round(scale[1])))
            notes.append(chord_root + int(round(scale[2])))
        else:
            notes.append(chord_root + 7)

        return notes

    def advance_chord(self):
        """Move to next chord in progression."""
        self.chord_index = (self.chord_index + 1) % len(self.progression)

    def start_chord_pad(self, chord_notes, duration, timbre="warm_pad"):
        """Start streaming oscillators for a chord pad."""
        self._chord_oscs = []
        gain_per_note = 0.06 / max(1, len(chord_notes))

        for note_idx, midi in enumerate(chord_notes):
            freq = mtof(midi)
            osc = StreamingOsc(
                freq, duration,
                timbre_name=timbre,
                gain=gain_per_note,
                attack=0.4,
                sustain=0.8,
                release=0.6,
            )
            pan = -0.4 + note_idx * 0.3
            l_gain = math.cos((pan + 1) * math.pi / 4)
            r_gain = math.sin((pan + 1) * math.pi / 4)
            self._chord_oscs.append((osc, l_gain, r_gain))

    def render_pad_chunk(self, num_samples):
        """Render the next chunk of the active chord pad.

        Returns (left, right) sample lists.
        """
        left = [0.0] * num_samples
        right = [0.0] * num_samples
        alive = []

        for osc, lg, rg in self._chord_oscs:
            if not osc.alive:
                continue
            chunk = osc.render_chunk(num_samples)
            if chunk:
                for i in range(num_samples):
                    left[i] += chunk[i] * lg
                    right[i] += chunk[i] * rg
                if osc.alive:
                    alive.append((osc, lg, rg))

        self._chord_oscs = alive
        return left, right

    def has_active_pad(self):
        """Check if any chord pad oscillators are still playing."""
        return any(osc.alive for osc, _, _ in self._chord_oscs)


# ---------------------------------------------------------------------------
# UNIVERSE POCKET NAVIGATOR
# ---------------------------------------------------------------------------

class PocketNavigator:
    """Navigates to different 'pockets' of the simulation for inspiration.

    Samples from subatomic, atomic, molecular, biological, geological,
    and cosmic domains to find different tonal inspiration at each moment.
    This creates the wandering, explorative quality of the soundscape.
    """

    DOMAINS = ["subatomic", "atomic", "molecular", "biological", "geological", "cosmic"]

    def __init__(self, rng):
        self.rng = rng
        self.current_domain = "subatomic"
        self.domain_weights = {d: 1.0 for d in self.DOMAINS}
        self.dwell_time = 0

    def update(self, epoch_idx, particles, atoms, molecules, cells, temperature):
        """Update domain weights based on simulation state."""
        # Weight domains by what's actually present in the simulation
        self.domain_weights["subatomic"] = clamp(particles / 100, 0.1, 1.0)
        self.domain_weights["atomic"] = clamp(atoms / 30, 0.0, 1.0)
        self.domain_weights["molecular"] = clamp(molecules / 20, 0.0, 1.0)
        self.domain_weights["biological"] = clamp(cells / 3, 0.0, 1.0)
        self.domain_weights["geological"] = 1.0 if epoch_idx >= 8 else 0.1
        self.domain_weights["cosmic"] = 0.5  # Always somewhat present

        # Navigate to new domain periodically
        self.dwell_time -= 1
        if self.dwell_time <= 0:
            self._navigate()
            self.dwell_time = self.rng.randint(30, 120)  # Dwell for 30-120 ticks

    def _navigate(self):
        """Pick a new domain weighted by what's happening in the sim."""
        total = sum(self.domain_weights.values())
        if total <= 0:
            return
        r = self.rng.random() * total
        cumulative = 0
        for domain, weight in self.domain_weights.items():
            cumulative += weight
            if r <= cumulative:
                self.current_domain = domain
                return

    def get_timbre_for_domain(self):
        """Get appropriate timbres for current domain."""
        return DOMAIN_TIMBRES.get(self.current_domain, ["piano"])

    def get_octave_shift(self):
        """Different domains operate in different pitch ranges."""
        shifts = {
            "subatomic": 24,    # Very high — particle chirps
            "atomic": 12,       # High — electron shells
            "molecular": 0,     # Middle — bonds, reactions
            "biological": -12,  # Low-mid — cellular rhythms
            "geological": -24,  # Low — tectonic rumbles
            "cosmic": 0,        # Full range
        }
        return shifts.get(self.current_domain, 0)


# ---------------------------------------------------------------------------
# MAIN COMPOSER
# ---------------------------------------------------------------------------

class Composer:
    """Top-level composition engine.

    Orchestrates all musical components — scales, rhythms, harmonies,
    melodies, beats, and timbres — into a cohesive, evolving soundscape
    driven by the physics simulation.
    """

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.seed = seed

        # Sub-engines
        self.beat_engine = BeatEngine(random.Random(seed + 10))
        self.harmonic_engine = HarmonicEngine(random.Random(seed + 20))
        self.navigator = PocketNavigator(random.Random(seed + 30))

        # Melodic voices (polyphonic — up to 4 simultaneous)
        self.voices = [
            MelodicVoice(random.Random(seed + 100 + i), voice_id=i)
            for i in range(4)
        ]

        # State
        self.current_scale_name = "pentatonic_major"
        self.current_scale = SCALES["pentatonic_major"]
        self.current_root = 60
        self.last_epoch = ""
        self.chord_timer = 0
        self.chord_duration_ticks = 40  # Change chord every ~40 ticks

    def get_scale_for_state(self, epoch, epoch_idx, temperature, rng):
        """Choose a musical scale based on simulation state."""
        families = EPOCH_SCALE_FAMILIES.get(epoch, ["ionian"])
        # Rotate through available scales based on time
        scale_name = rng.choice(families)
        return scale_name, SCALES.get(scale_name, [0, 2, 4, 5, 7, 9, 11])

    def compose_tick(self, epoch, epoch_idx, root_note, temperature,
                     particles, atoms, molecules, cells, generation,
                     samples_per_tick):
        """Compose audio for one simulation tick.

        Uses streaming oscillators so per-tick cost is O(samples_per_tick)
        regardless of note/chord duration.

        Returns (left_samples, right_samples) as float lists.
        """
        left = [0.0] * samples_per_tick
        right = [0.0] * samples_per_tick

        # --- Update state ---
        if epoch != self.last_epoch:
            self.last_epoch = epoch
            self.current_scale_name, self.current_scale = \
                self.get_scale_for_state(epoch, epoch_idx, temperature, self.rng)
            self.harmonic_engine.update_progression(epoch, root_note, self.current_scale)
            for v in self.voices:
                v.update_state(epoch, epoch_idx, root_note, self.current_scale_name)

        self.navigator.update(epoch_idx, particles, atoms, molecules, cells, temperature)
        self.beat_engine.update_state(epoch, epoch_idx, 0, temperature, particles)

        # --- Harmonic pad (streaming) ---
        self.chord_timer -= 1
        if self.chord_timer <= 0:
            chord_notes = self.harmonic_engine.get_current_chord(root_note, self.current_scale)
            domain_timbres = self.navigator.get_timbre_for_domain()
            pad_timbre = domain_timbres[0] if domain_timbres else "warm_pad"
            pad_dur = samples_per_tick / SAMPLE_RATE * self.chord_duration_ticks
            self.harmonic_engine.start_chord_pad(chord_notes, pad_dur, timbre=pad_timbre)
            self.harmonic_engine.advance_chord()
            self.chord_timer = self.chord_duration_ticks

        # Render current pad chunk
        if self.harmonic_engine.has_active_pad():
            pad_l, pad_r = self.harmonic_engine.render_pad_chunk(samples_per_tick)
            for i in range(samples_per_tick):
                left[i] += pad_l[i]
                right[i] += pad_r[i]

        # --- Beats ---
        beat_samples = self.beat_engine.render_beat_bar(samples_per_tick, root_note)
        for i in range(samples_per_tick):
            left[i] += beat_samples[i] * 0.6
            right[i] += beat_samples[i] * 0.4

        # --- Melodic voices (streaming) ---
        for voice in self.voices:
            result = voice.maybe_play_phrase(
                epoch, root_note + self.navigator.get_octave_shift(),
                self.current_scale, samples_per_tick
            )
            if result:
                phrase_samples, pan = result
                l_gain = math.cos((pan + 1) * math.pi / 4)
                r_gain = math.sin((pan + 1) * math.pi / 4)
                end = min(len(phrase_samples), samples_per_tick)
                for i in range(end):
                    left[i] += phrase_samples[i] * l_gain
                    right[i] += phrase_samples[i] * r_gain

        return left, right
