#!/usr/bin/env python3
"""
Radio engine v7 for 'In The Beginning Radio' -- a cosmic simulation music station.

This engine generates continuously evolving music that shifts mood, instruments,
time signature, scale, and tempo at 42-second boundaries, driven by the physics
simulation state. It features:

    - 500+ synthesized instruments with runtime instrument rotation
    - Mood segments at multiples of 42 seconds (42, 84, 126, 168, 210s)
    - 2-4 instruments per mood forming a small band ensemble
    - 7 rondo structures (ABACA, ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA)
    - 6 arpeggio forms (block, ascending, descending, alberti, broken, pendulum)
    - Tempo multiplier 1.5x-2.5x for natural pacing
    - harmonic consonance (Helmholtz/Hartmann) enforcement on all chord voicings
    - Anti-click processing: micro-fades, DC offset removal, cosine crossfades
    - Classical music scales and well-known time signatures (from Wikipedia)
    - Diverse instrument family selection (strings, brass, woodwinds, keys, perc)
    - Smoothing/dampening to reduce MIDI-like artifacts
    - TTS voice injection using Silero (preferred) or espeak-ng (fallback)
    - MIDI note sampling from 249 public domain classical works (1600-1900)
    - Simulation-driven parameters sampled from different space regions
    - FluidSynth integration with FluidR3_GM.sf2 soundfont

The engine uses Silero TTS (Apache 2.0) as primary voice synthesis, with
espeak-ng (GPL) as fallback. MIDI files are sourced from public domain
compositions by Bach, Beethoven, Mozart, Chopin, Brahms, and others.

No network access at runtime. All assets are bundled or generated algorithmically.

Attribution for MIDI files: see apps/audio/midi_library/ATTRIBUTION.md
"""

import math
import os
import random
import struct
import subprocess
import sys
import wave
import glob as globmod
import hashlib
import time as _time

# Optional acceleration
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import mido
    HAS_MIDO = True
except ImportError:
    HAS_MIDO = False

# Try Silero TTS
_SILERO_MODEL = None
_SILERO_AVAILABLE = False
try:
    import torch
    import torchaudio
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

SAMPLE_RATE = 44100
TWO_PI = 2 * math.pi
INV_SR = 1.0 / SAMPLE_RATE
BASE_FREQ = 261.63  # C4
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# MIDI note/freq utilities
# ---------------------------------------------------------------------------
def mtof(note):
    """MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def ftom(freq):
    """Frequency to nearest MIDI note."""
    if freq <= 0:
        return 0
    return int(round(69 + 12 * math.log2(freq / 440.0)))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# TIME SIGNATURES (from Wikipedia article on Time Signatures)
# ---------------------------------------------------------------------------
TIME_SIGNATURES = {
    # Simple meters
    '2/2': {'beats': 2, 'unit': 2, 'name': 'alla_breve', 'style': 'classical'},
    '2/4': {'beats': 2, 'unit': 4, 'name': 'simple_duple', 'style': 'march'},
    '3/4': {'beats': 3, 'unit': 4, 'name': 'waltz', 'style': 'classical'},
    '4/4': {'beats': 4, 'unit': 4, 'name': 'common_time', 'style': 'universal'},
    '3/8': {'beats': 3, 'unit': 8, 'name': 'simple_triple_8', 'style': 'scherzo'},
    '3/2': {'beats': 3, 'unit': 2, 'name': 'sarabande', 'style': 'baroque'},
    # Compound meters
    '6/4': {'beats': 2, 'unit': 4, 'name': 'compound_duple_4', 'style': 'classical'},
    '6/8': {'beats': 2, 'unit': 8, 'name': 'compound_duple', 'style': 'jig'},
    '9/8': {'beats': 3, 'unit': 8, 'name': 'compound_triple', 'style': 'celtic'},
    '12/8': {'beats': 4, 'unit': 8, 'name': 'compound_quad', 'style': 'blues'},
    # Complex/odd meters
    '5/4': {'beats': 5, 'unit': 4, 'name': 'quintuple', 'style': 'progressive'},
    '5/8': {'beats': 5, 'unit': 8, 'name': 'quintuple_8', 'style': 'balkan'},
    '7/4': {'beats': 7, 'unit': 4, 'name': 'septuple', 'style': 'progressive'},
    '7/8': {'beats': 7, 'unit': 8, 'name': 'septuple_8', 'style': 'balkan'},
    '11/8': {'beats': 11, 'unit': 8, 'name': 'hendecuple', 'style': 'experimental'},
    # Additive
    '3+3+2/8': {'beats': 8, 'unit': 8, 'name': 'additive_332', 'style': 'edm'},
    '2+2+3/8': {'beats': 7, 'unit': 8, 'name': 'additive_223', 'style': 'edm'},
}

# Classical era time signatures (1600-1900 weighted)
CLASSICAL_TIME_SIGS = ['4/4', '3/4', '2/4', '6/8', '3/8', '2/2', '3/2',
                       '6/4', '9/8', '12/8']
EDM_TIME_SIGS = ['4/4', '3/4', '6/8', '7/8', '5/4', '3+3+2/8']

# ---------------------------------------------------------------------------
# SCALES (well-known harmonic systems)
# ---------------------------------------------------------------------------
SCALES = {
    # Major modes
    'ionian':          [0, 2, 4, 5, 7, 9, 11],
    'dorian':          [0, 2, 3, 5, 7, 9, 10],
    'phrygian':        [0, 1, 3, 5, 7, 8, 10],
    'lydian':          [0, 2, 4, 6, 7, 9, 11],
    'mixolydian':      [0, 2, 4, 5, 7, 9, 10],
    'aeolian':         [0, 2, 3, 5, 7, 8, 10],
    'locrian':         [0, 1, 3, 5, 6, 8, 10],
    # Harmonic & melodic minor
    'harmonic_minor':  [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor':   [0, 2, 3, 5, 7, 9, 11],
    # Pentatonic
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues':           [0, 3, 5, 6, 7, 10],
    # Whole-tone & chromatic
    'whole_tone':      [0, 2, 4, 6, 8, 10],
    'chromatic':       [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    # Japanese
    'hirajoshi':       [0, 2, 3, 7, 8],
    'in_sen':          [0, 1, 5, 7, 10],
    'iwato':           [0, 1, 5, 6, 10],
    'yo':              [0, 2, 5, 7, 9],
    'miyako_bushi':    [0, 1, 5, 7, 8],
    # Chinese
    'gong':            [0, 2, 4, 7, 9],
    'shang':           [0, 2, 5, 7, 9],
    # Middle Eastern
    'hijaz':           [0, 1, 4, 5, 7, 8, 11],
    'bayati':          [0, 1.5, 3, 5, 7, 8, 10],
    'rast':            [0, 2, 3.5, 5, 7, 9, 10.5],
    'nahawand':        [0, 2, 3, 5, 7, 8, 11],
    # Indian ragas
    'bhairav':         [0, 1, 4, 5, 7, 8, 11],
    'yaman':           [0, 2, 4, 6, 7, 9, 11],
    'malkauns':        [0, 3, 5, 8, 10],
    'bhairavi':        [0, 1, 3, 5, 7, 8, 10],
    # Drone
    'drone':           [0, 7],
}

# Harmonically compatible scale families (for mashup blending)
SCALE_FAMILIES = {
    'bright': ['ionian', 'lydian', 'mixolydian', 'pentatonic_major', 'yaman'],
    'dark': ['aeolian', 'phrygian', 'harmonic_minor', 'hijaz', 'bhairav'],
    'mystical': ['whole_tone', 'hirajoshi', 'in_sen', 'malkauns'],
    'earthy': ['dorian', 'pentatonic_minor', 'blues', 'yo', 'gong'],
    'cosmic': ['chromatic', 'drone', 'iwato', 'miyako_bushi'],
}

# ---------------------------------------------------------------------------
# CHORD PROGRESSIONS (classical + contemporary)
# ---------------------------------------------------------------------------
PROGRESSIONS = {
    'I-V-vi-IV':    [(0, 'maj'), (7, 'maj'), (9, 'min'), (5, 'maj')],
    'I-IV-V':       [(0, 'maj'), (5, 'maj'), (7, 'maj')],
    'vi-IV-I-V':    [(9, 'min'), (5, 'maj'), (0, 'maj'), (7, 'maj')],
    'I-vi-IV-V':    [(0, 'maj'), (9, 'min'), (5, 'maj'), (7, 'maj')],
    'circle_5ths':  [(0, 'maj'), (5, 'maj'), (10, 'maj'), (3, 'maj'),
                     (8, 'maj'), (1, 'maj'), (6, 'maj'), (11, 'maj')],
    'bach_cmaj':    [(0, 'maj'), (2, 'min'), (4, 'min'), (5, 'maj'),
                     (7, 'dom7'), (0, 'maj')],
    'romantic':     [(0, 'maj'), (3, 'min'), (8, 'maj'), (5, 'maj'),
                     (0, 'maj')],
    'debussy':      [(0, 'maj7'), (2, 'min7'), (5, 'maj7'), (10, 'maj7')],
    'edm_dark':     [(0, 'min'), (3, 'maj'), (5, 'maj'), (7, 'min')],
    'edm_uplifting': [(0, 'maj'), (5, 'maj'), (9, 'min'), (7, 'maj')],
    'drone':        [(0, 'pow'), (0, 'pow')],
}

CHORD_INTERVALS = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    'pow': [0, 7],
    'add9': [0, 4, 7, 14],
    'min9': [0, 3, 7, 10, 14],
}

# ---------------------------------------------------------------------------
# RONDO PATTERNS (classical form)
# ---------------------------------------------------------------------------
RONDO_PATTERNS = {
    'ABACA':   ['A', 'B', 'A', 'C', 'A'],
    'ABACADA': ['A', 'B', 'A', 'C', 'A', 'D', 'A'],
    'ABCBA':   ['A', 'B', 'C', 'B', 'A'],           # Arch / palindrome
    'AABBA':   ['A', 'A', 'B', 'B', 'A'],           # Verse-chorus-verse
    'ABCDA':   ['A', 'B', 'C', 'D', 'A'],           # Through-composed return
    'ABACBA':  ['A', 'B', 'A', 'C', 'B', 'A'],     # Extended arch rondo
    'AABA':    ['A', 'A', 'B', 'A'],                 # 32-bar song form
}

# Arpeggio forms for rondo section variation
ARPEGGIO_FORMS = {
    'block':       None,              # Play all chord notes simultaneously
    'ascending':   lambda ns: sorted(ns),
    'descending':  lambda ns: sorted(ns, reverse=True),
    'alberti':     lambda ns: [ns[0], ns[-1], ns[1 % len(ns)], ns[-1]] if len(ns) >= 2 else ns,
    'broken':      lambda ns: [ns[i] for i in [0, 2 % len(ns), 1 % len(ns), -1]],
    'pendulum':    lambda ns: sorted(ns) + sorted(ns, reverse=True)[1:-1],
}

# Diatonic chord qualities per scale degree (7-degree scales)
DIATONIC_CHORD_QUALITY = {
    'ionian':         ['maj', 'min', 'min', 'maj', 'maj', 'min', 'dim'],
    'dorian':         ['min', 'min', 'maj', 'maj', 'min', 'dim', 'maj'],
    'phrygian':       ['min', 'maj', 'maj', 'min', 'dim', 'maj', 'min'],
    'lydian':         ['maj', 'maj', 'min', 'dim', 'maj', 'min', 'min'],
    'mixolydian':     ['maj', 'min', 'dim', 'maj', 'min', 'min', 'maj'],
    'aeolian':        ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'],
    'locrian':        ['dim', 'maj', 'min', 'min', 'maj', 'maj', 'min'],
    'harmonic_minor': ['min', 'dim', 'aug', 'min', 'maj', 'maj', 'dim'],
    'melodic_minor':  ['min', 'min', 'aug', 'maj', 'maj', 'dim', 'dim'],
}

# General MIDI orchestra instruments for FluidSynth rendering
GM_ORCHESTRA_INSTRUMENTS = {
    40: 'Violin', 41: 'Viola', 42: 'Cello', 43: 'Contrabass',
    44: 'Tremolo Strings', 45: 'Pizzicato Strings',
    46: 'Orchestral Harp', 48: 'String Ensemble 1',
    56: 'Trumpet', 57: 'Trombone', 58: 'Tuba',
    60: 'French Horn', 61: 'Brass Section',
    68: 'Oboe', 69: 'English Horn', 70: 'Bassoon',
    71: 'Clarinet', 72: 'Piccolo', 73: 'Flute',
    74: 'Recorder', 75: 'Pan Flute',
    6: 'Harpsichord', 8: 'Celesta',
    11: 'Vibraphone', 14: 'Tubular Bells',
}

# v9 expanded GM instrument catalog -- adds ~50 instruments across 8 new families
GM_EXPANDED_INSTRUMENTS = {
    # --- Symphonic (missing from v7/v8) ---
    9: 'Glockenspiel', 10: 'Music Box', 13: 'Xylophone', 15: 'Dulcimer',
    47: 'Timpani', 49: 'String Ensemble 2',
    50: 'Synth Strings 1', 51: 'Synth Strings 2',
    52: 'Choir Aahs', 53: 'Voice Oohs', 54: 'Synth Voice',
    55: 'Orchestra Hit', 59: 'Muted Trumpet',
    64: 'Soprano Sax', 65: 'Alto Sax', 66: 'Tenor Sax', 67: 'Baritone Sax',
    # --- Rock ---
    26: 'Electric Guitar (Jazz)', 28: 'Electric Guitar (Muted)',
    29: 'Overdriven Guitar', 30: 'Distortion Guitar',
    33: 'Electric Bass (Finger)', 34: 'Electric Bass (Pick)', 36: 'Slap Bass 1',
    # --- Electronic / Synth ---
    80: 'Square Lead', 81: 'Sawtooth Lead', 82: 'Calliope Lead',
    88: 'Synth Pad (New Age)', 90: 'Synth Pad (Polysynth)',
    91: 'Synth Pad (Choir)', 92: 'Synth Pad (Bowed)',
    94: 'Synth Pad (Halo)', 95: 'Synth Pad (Sweep)',
    # --- Synth FX ---
    96: 'FX Rain', 97: 'FX Soundtrack', 98: 'FX Crystal',
    99: 'FX Atmosphere', 100: 'FX Brightness',
    101: 'FX Goblins', 102: 'FX Echoes', 103: 'FX Sci-Fi',
    # --- World / Ethnic ---
    104: 'Sitar', 105: 'Banjo', 106: 'Shamisen', 107: 'Koto',
    108: 'Kalimba', 109: 'Bagpipe', 110: 'Fiddle', 111: 'Shanai',
    # --- Extra pitched percussion ---
    114: 'Steel Drums',
}

# Combined catalog for v9
GM_ALL_INSTRUMENTS = {**GM_ORCHESTRA_INSTRUMENTS, **GM_EXPANDED_INSTRUMENTS}

# v9 expanded family pools (superset of v7/v8 pools)
V9_FAMILY_POOLS = {
    # Original families (v7/v8)
    'strings':       [40, 41, 42, 43, 44, 45, 48],
    'brass':         [56, 57, 58, 60, 61],
    'woodwinds':     [68, 69, 70, 71, 72, 73, 74, 75],
    'keys':          [0, 1, 2, 3, 4, 5, 6, 7, 8],
    'pitched_perc':  [11, 14, 46],
    # New v9 families
    'rock_guitar':   [26, 28, 29, 30],
    'rock_bass':     [33, 34, 36],
    'synth_lead':    [80, 81, 82],
    'synth_pad':     [88, 90, 91, 92, 94, 95],
    'synth_fx':      [96, 97, 98, 99, 100, 101, 102, 103],
    'world':         [104, 105, 106, 107, 108, 109, 110, 111],
    'sax':           [64, 65, 66, 67],
    'choir':         [52, 53, 54],
    'symphonic_ext': [47, 49, 50, 51, 55, 59],
    'mallets':       [9, 10, 13, 15, 114],
}

PIANO_PROGRAMS = {0, 1, 2, 3, 4, 5, 6, 7}  # GM piano family

# FluidSynth availability
_FLUIDSYNTH_PATH = None
_FLUIDR3_SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
for _p in ['/usr/bin/fluidsynth', '/usr/local/bin/fluidsynth']:
    if os.path.isfile(_p):
        _FLUIDSYNTH_PATH = _p
        break
HAS_FLUIDSYNTH = _FLUIDSYNTH_PATH is not None and os.path.isfile(_FLUIDR3_SF2)

# ---------------------------------------------------------------------------
# EPOCH -> Musical character mapping (from simulation)
# ---------------------------------------------------------------------------
EPOCH_MUSIC = {
    'Planck':          {'tempo': (50, 70),  'scales': ['chromatic', 'drone', 'whole_tone'],
                        'time_sigs': ['3/4', '3/2'], 'family': 'cosmic', 'density': 0.1},
    'Inflation':       {'tempo': (55, 75),  'scales': ['pentatonic_major', 'drone', 'whole_tone'],
                        'time_sigs': ['4/4', '3/4'], 'family': 'cosmic', 'density': 0.15},
    'Electroweak':     {'tempo': (60, 80),  'scales': ['phrygian', 'hirajoshi', 'hijaz'],
                        'time_sigs': ['4/4', '6/8', '7/8'], 'family': 'dark', 'density': 0.2},
    'Quark':           {'tempo': (65, 90),  'scales': ['hirajoshi', 'in_sen', 'bhairav'],
                        'time_sigs': ['4/4', '5/4', '7/8'], 'family': 'mystical', 'density': 0.25},
    'Hadron':          {'tempo': (70, 95),  'scales': ['pentatonic_minor', 'yo', 'aeolian'],
                        'time_sigs': ['4/4', '6/8', '3/4'], 'family': 'dark', 'density': 0.3},
    'Nucleosynthesis': {'tempo': (75, 105), 'scales': ['dorian', 'mixolydian', 'rast'],
                        'time_sigs': ['4/4', '3/4', '6/8'], 'family': 'earthy', 'density': 0.4},
    'Recombination':   {'tempo': (80, 110), 'scales': ['pentatonic_major', 'gong', 'yaman'],
                        'time_sigs': ['4/4', '3/4', '6/8'], 'family': 'bright', 'density': 0.5},
    'Star Formation':  {'tempo': (85, 115), 'scales': ['lydian', 'hijaz', 'harmonic_minor'],
                        'time_sigs': ['4/4', '6/8', '9/8'], 'family': 'bright', 'density': 0.6},
    'Solar System':    {'tempo': (90, 120), 'scales': ['ionian', 'harmonic_minor', 'gong'],
                        'time_sigs': ['4/4', '3/4', '6/8', '12/8'], 'family': 'bright', 'density': 0.7},
    'Earth':           {'tempo': (90, 125), 'scales': ['aeolian', 'miyako_bushi', 'nahawand'],
                        'time_sigs': ['4/4', '3/4', '6/8'], 'family': 'earthy', 'density': 0.75},
    'Life':            {'tempo': (95, 130), 'scales': ['blues', 'pentatonic_minor', 'malkauns'],
                        'time_sigs': ['4/4', '6/8', '12/8', '5/4'], 'family': 'earthy', 'density': 0.8},
    'DNA Era':         {'tempo': (100, 135), 'scales': ['melodic_minor', 'bhairavi', 'dorian'],
                        'time_sigs': ['4/4', '3/4', '7/8', '5/4'], 'family': 'dark', 'density': 0.85},
    'Present':         {'tempo': (100, 140), 'scales': ['ionian', 'dorian', 'pentatonic_major', 'lydian'],
                        'time_sigs': ['4/4', '3/4', '6/8', '5/4', '7/8', '3+3+2/8'], 'family': 'bright', 'density': 0.95},
}

EPOCH_ORDER = [
    "Planck", "Inflation", "Electroweak", "Quark", "Hadron",
    "Nucleosynthesis", "Recombination", "Star Formation",
    "Solar System", "Earth", "Life", "DNA Era", "Present",
]

EPOCH_ROOTS = {
    "Planck": 48, "Inflation": 50, "Electroweak": 52, "Quark": 54,
    "Hadron": 56, "Nucleosynthesis": 58, "Recombination": 60,
    "Star Formation": 62, "Solar System": 64, "Earth": 66,
    "Life": 68, "DNA Era": 70, "Present": 72,
}

# ---------------------------------------------------------------------------
# ADSR envelope generator
# ---------------------------------------------------------------------------
def _adsr(n, attack=0.02, decay=0.05, sustain_level=0.8, release=0.1):
    """Generate ADSR envelope array."""
    env = [0.0] * n
    a_samples = int(attack * SAMPLE_RATE)
    d_samples = int(decay * SAMPLE_RATE)
    r_samples = int(release * SAMPLE_RATE)
    s_start = a_samples + d_samples
    r_start = max(0, n - r_samples)
    for i in range(n):
        if i < a_samples:
            env[i] = i / max(a_samples, 1)
        elif i < s_start:
            t = (i - a_samples) / max(d_samples, 1)
            env[i] = 1.0 - (1.0 - sustain_level) * t
        elif i < r_start:
            env[i] = sustain_level
        else:
            t = (i - r_start) / max(r_samples, 1)
            env[i] = sustain_level * max(0, 1.0 - t)
    return env


def _adsr_np(n, attack=0.02, decay=0.05, sustain_level=0.8, release=0.1):
    """Generate ADSR envelope as numpy array (vectorized, ~50x faster)."""
    if not HAS_NUMPY:
        return np.array(_adsr(n, attack, decay, sustain_level, release))
    env = np.zeros(n, dtype=np.float64)
    a_samples = int(attack * SAMPLE_RATE)
    d_samples = int(decay * SAMPLE_RATE)
    r_samples = int(release * SAMPLE_RATE)
    s_start = a_samples + d_samples
    r_start = max(0, n - r_samples)
    # Attack
    if a_samples > 0:
        end_a = min(a_samples, n)
        env[:end_a] = np.linspace(0, 1, end_a, endpoint=False)
    # Decay
    if s_start > a_samples:
        end_d = min(s_start, n)
        if end_d > a_samples:
            env[a_samples:end_d] = np.linspace(1, sustain_level, end_d - a_samples,
                                                 endpoint=False)
    # Sustain
    if r_start > s_start:
        env[s_start:r_start] = sustain_level
    # Release
    if n > r_start:
        env[r_start:n] = np.linspace(sustain_level, 0, n - r_start)
    return env


def _synth_note_np(freq, duration, harmonics, env_params, velocity=0.8,
                   vib_rate=5.0, vib_depth=0.0003, vib_delay=0.5,
                   noise_level=0.0, distortion=0.0, freq_mult=1.0):
    """Numpy-vectorized note synthesis (~50-100x faster than pure Python).

    Args:
        freq: Fundamental frequency in Hz.
        duration: Duration in seconds.
        harmonics: List of (harmonic_number, amplitude) tuples.
        env_params: Dict with attack, decay, sustain, release.
        velocity: Note velocity 0-1.
        vib_rate: Vibrato rate Hz.
        vib_depth: Vibrato depth (fraction of freq).
        vib_delay: Vibrato onset delay seconds.
        noise_level: Noise amplitude.
        distortion: Distortion amount (0 = none).
        freq_mult: Frequency multiplier.

    Returns:
        numpy array of float64 samples.
    """
    n = int(SAMPLE_RATE * duration)
    if n <= 0:
        return np.zeros(0, dtype=np.float64)

    f = freq * freq_mult
    t = np.arange(n, dtype=np.float64) * INV_SR

    # ADSR envelope
    env = _adsr_np(n, env_params.get('attack', 0.02),
                   env_params.get('decay', 0.05),
                   env_params.get('sustain', 0.8),
                   env_params.get('release', 0.1))

    # Vibrato
    vib_env = np.minimum(1.0, t / max(vib_delay, 0.001))
    vib = vib_depth * vib_env * np.sin(TWO_PI * vib_rate * t)
    ff = f * (1.0 + vib)

    # Sum harmonics
    signal = np.zeros(n, dtype=np.float64)
    for h_data in harmonics:
        if h_data[0] == 'fm' or h_data[0] == 'noise':
            continue
        h_num, h_amp = h_data[0], h_data[1]
        h_freq = ff * h_num
        # Skip if above Nyquist for the whole note
        if f * h_num >= SAMPLE_RATE / 2:
            break
        signal += h_amp * np.sin(TWO_PI * h_freq * t)

    # Add noise
    if noise_level > 0:
        rng = np.random.RandomState(int(freq * 1000) & 0xFFFF)
        signal += noise_level * (rng.random(n) * 2 - 1)

    # Apply distortion
    if distortion > 0:
        signal = np.tanh(signal * distortion) / max(0.1, distortion * 0.5)

    return signal * env * velocity


def _synth_colored_note_np(freq, duration, instr, velocity=0.8, color_amount=0.25):
    """Numpy-vectorized colored note synthesis.

    Blends a clean additive base with the instrument's harmonic profile.
    """
    n = int(duration * SAMPLE_RATE)
    if n <= 0:
        return np.zeros(0, dtype=np.float64)

    f = freq
    ca = max(0.0, min(1.0, color_amount))
    t = np.arange(n, dtype=np.float64) * INV_SR

    # Base tone: clean 8-harmonic additive
    base_env = _adsr_np(n, 0.01, 0.05, 0.7, 0.08)
    base = np.zeros(n, dtype=np.float64)
    for h in range(1, 9):
        h_freq = f * h
        if h_freq >= SAMPLE_RATE / 2:
            break
        amp = 1.0 / (h ** 1.2)
        base += amp * np.sin(TWO_PI * h_freq * t)
    base *= base_env * velocity

    if ca == 0.0:
        return base

    # Color: instrument harmonics (no noise/distortion for cleanliness)
    env_params = {
        'attack': instr['attack'], 'decay': instr['decay'],
        'sustain': instr['sustain'], 'release': instr['release'],
    }
    harmonics = instr['harmonics']
    # Filter out FM/noise special harmonics for the additive path
    clean_harmonics = [h for h in harmonics if not isinstance(h[0], str)]
    if not clean_harmonics:
        clean_harmonics = [(1, 1.0), (2, 0.5), (3, 0.33)]

    color = _synth_note_np(
        freq, duration, clean_harmonics, env_params,
        velocity=velocity,
        vib_rate=instr['vib_rate'], vib_depth=instr['vib_depth'],
        vib_delay=instr['vib_delay'], noise_level=0.0,
        distortion=min(instr.get('distortion', 0) * 0.3, 0.1),
        freq_mult=instr['freq_mult']
    )

    # Blend
    cn = min(len(color), n)
    result = base * (1.0 - ca)
    result[:cn] += color[:cn] * ca
    return result


def _write_wav(path, samples, sample_rate=SAMPLE_RATE):
    """Write mono float samples to 16-bit WAV."""
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        peak = max((abs(s) for s in samples), default=1.0)
        if peak < 1e-10:
            peak = 1.0
        norm = 0.95 / peak
        data = bytearray(len(samples) * 2)
        for i, s in enumerate(samples):
            val = int(s * norm * 32767)
            val = max(-32767, min(32767, val))
            struct.pack_into('<h', data, i * 2, val)
        wf.writeframes(bytes(data))


# ---------------------------------------------------------------------------
# INSTRUMENT FACTORY -- Generates 500+ unique instruments algorithmically
# ---------------------------------------------------------------------------
class InstrumentFactory:
    """Algorithmic instrument synthesizer.

    Generates unique timbres by combining synthesis techniques:
    additive, FM, physical modeling, subtractive, and wavetable.

    Each instrument has: harmonic profile, envelope, vibrato, noise,
    filter characteristics, and optional distortion.
    """

    # Synthesis technique families
    TECHNIQUES = ['additive', 'fm', 'plucked', 'bowed', 'blown',
                  'struck', 'pad', 'bass', 'bell', 'noise_perc']

    # Timbre modifier seeds for variety
    FAMILIES = [
        'piano', 'organ', 'harpsichord', 'celesta', 'marimba',
        'violin', 'viola', 'cello', 'bass', 'harp', 'guitar',
        'flute', 'oboe', 'clarinet', 'bassoon', 'piccolo',
        'trumpet', 'horn', 'trombone', 'tuba',
        'bell', 'glockenspiel', 'vibraphone', 'xylophone', 'chimes',
        'kick', 'snare', 'hihat', 'tom', 'cymbal', 'shaker',
        'sitar', 'koto', 'kalimba', 'erhu', 'shamisen', 'banjo',
        'shakuhachi', 'didgeridoo', 'bagpipe', 'accordion',
        'pad_warm', 'pad_glass', 'pad_choir', 'pad_cosmic', 'pad_string',
        'synth_lead', 'synth_bass', 'synth_pluck', 'synth_arp',
        'synth_acid', 'synth_wobble', 'synth_supersaw',
    ]

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self._cache = {}
        self._instrument_registry = {}

    def _make_harmonic_profile(self, technique, variant_seed):
        """Create harmonic amplitude profile for a synthesis technique."""
        rng = random.Random(variant_seed)
        n_harmonics = rng.randint(3, 16)
        harmonics = []

        if technique == 'additive':
            for h in range(1, n_harmonics + 1):
                amp = 1.0 / (h ** rng.uniform(0.5, 2.0))
                amp *= rng.uniform(0.5, 1.5)
                harmonics.append((h, amp))
        elif technique == 'fm':
            mod_ratio = rng.choice([1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 7.0, 14.0])
            mod_index = rng.uniform(0.5, 8.0)
            harmonics = [('fm', mod_ratio, mod_index)]
        elif technique in ('plucked', 'guitar'):
            for h in range(1, n_harmonics + 1):
                amp = (1.0 / h) * math.exp(-0.1 * h * rng.uniform(0.5, 2.0))
                harmonics.append((h, amp))
        elif technique in ('bowed', 'violin'):
            for h in range(1, n_harmonics + 1):
                amp = rng.uniform(0.1, 0.8) / h
                harmonics.append((h, amp))
        elif technique in ('blown', 'flute'):
            # Odd harmonics dominate for cylindrical bore
            for h in range(1, n_harmonics + 1):
                amp = (1.0 / h) * (1.0 if h % 2 == 1 else rng.uniform(0.02, 0.2))
                harmonics.append((h, amp))
        elif technique in ('struck', 'bell'):
            # Inharmonic partials
            for h in range(1, n_harmonics + 1):
                ratio = h * (1 + rng.uniform(-0.1, 0.3) * h * 0.1)
                amp = rng.uniform(0.1, 1.0) / (h ** 0.5)
                harmonics.append((ratio, amp))
        elif technique == 'pad':
            for h in range(1, min(n_harmonics, 6) + 1):
                amp = rng.uniform(0.3, 1.0) / (h ** 0.7)
                harmonics.append((h, amp))
        elif technique == 'bass':
            for h in range(1, min(n_harmonics, 8) + 1):
                amp = 1.0 / (h ** rng.uniform(0.8, 1.5))
                harmonics.append((h, amp))
        elif technique == 'noise_perc':
            harmonics = [('noise', rng.uniform(0.3, 1.0))]
        else:
            for h in range(1, n_harmonics + 1):
                harmonics.append((h, 1.0 / h))

        return harmonics

    def generate_instrument(self, name, seed=None):
        """Generate a unique instrument timbre definition.

        Returns dict with: technique, harmonics, envelope, vibrato,
        freq_mult, noise_level, distortion, filter params.
        """
        if name in self._instrument_registry:
            return self._instrument_registry[name]

        s = seed if seed is not None else hash(name) & 0xFFFFFFFF
        rng = random.Random(s)

        technique = rng.choice(self.TECHNIQUES)
        harmonics = self._make_harmonic_profile(technique, s + 1)

        # Envelope
        attack = rng.uniform(0.001, 0.8)
        decay = rng.uniform(0.01, 0.5)
        sustain = rng.uniform(0.2, 0.95)
        release = rng.uniform(0.05, 2.0)

        # Frequency multiplier (octave range: 0.25 to 4.0)
        freq_mult = rng.choice([0.25, 0.5, 0.5, 1.0, 1.0, 1.0, 2.0, 2.0, 4.0])

        # Vibrato -- kept subtle for smooth fluid sound; only 15% of
        # instruments get noticeable vibrato, the rest are nearly straight
        if rng.random() < 0.15:
            vib_rate = rng.uniform(4.0, 6.0)
            vib_depth = rng.uniform(0.0008, 0.002)
        else:
            vib_rate = rng.uniform(4.0, 5.5)
            vib_depth = rng.uniform(0.0001, 0.0005)
        vib_delay = rng.uniform(0.3, 1.0)

        # Noise
        noise_level = rng.uniform(0.0, 0.06)
        if technique == 'noise_perc':
            noise_level = rng.uniform(0.3, 0.9)

        # Distortion
        distortion = 0.0
        if rng.random() < 0.2:
            distortion = rng.uniform(0.5, 3.0)

        # Filter (lowpass cutoff multiplier relative to fundamental)
        filter_mult = rng.uniform(4.0, 20.0)
        filter_q = rng.uniform(0.5, 2.0)

        # Assign a musical role for kit grouping
        role_map = {
            'additive': 'melody', 'fm': 'melody', 'bowed': 'melody',
            'blown': 'melody', 'plucked': 'harmony', 'pad': 'harmony',
            'bass': 'bass', 'struck': 'rhythm', 'bell': 'harmony',
            'noise_perc': 'rhythm',
        }
        role = role_map.get(technique, 'melody')

        instr = {
            'name': name,
            'technique': technique,
            'harmonics': harmonics,
            'attack': attack,
            'decay': decay,
            'sustain': sustain,
            'release': release,
            'freq_mult': freq_mult,
            'vib_rate': vib_rate,
            'vib_depth': vib_depth,
            'vib_delay': vib_delay,
            'noise_level': noise_level,
            'distortion': distortion,
            'filter_mult': filter_mult,
            'filter_q': filter_q,
            'role': role,
        }
        self._instrument_registry[name] = instr
        return instr

    def synthesize_note(self, instr, freq, duration, velocity=0.8):
        """Synthesize a single note using an instrument definition.

        Returns list of float samples at SAMPLE_RATE.
        """
        n = int(SAMPLE_RATE * duration)
        if n <= 0:
            return []

        f = freq * instr['freq_mult']
        env = _adsr(n, instr['attack'], instr['decay'],
                    instr['sustain'], instr['release'])

        samples = [0.0] * n
        technique = instr['technique']
        harmonics = instr['harmonics']
        noise_level = instr['noise_level']
        distortion = instr['distortion']
        vib_rate = instr['vib_rate']
        vib_depth = instr['vib_depth']
        vib_delay = instr['vib_delay']

        rng = random.Random(int(freq * 1000) & 0xFFFF)

        if technique == 'fm' and harmonics and harmonics[0][0] == 'fm':
            _, mod_ratio, mod_index = harmonics[0]
            for i in range(n):
                t = i * INV_SR
                vib = vib_depth * min(1.0, t / vib_delay) * math.sin(TWO_PI * vib_rate * t)
                ff = f * (1.0 + vib)
                mod = mod_index * math.sin(TWO_PI * ff * mod_ratio * t)
                mod *= math.exp(-t * 3.0)  # Decaying mod index
                samples[i] = math.sin(TWO_PI * ff * t + mod) * env[i] * velocity
        elif technique == 'noise_perc':
            nl = harmonics[0][1] if harmonics and harmonics[0][0] == 'noise' else 0.5
            for i in range(n):
                t = i * INV_SR
                noise = (rng.random() * 2 - 1) * nl
                # Pitch component for tonal percussion
                tone = 0.3 * math.sin(TWO_PI * f * t) * math.exp(-t * 20)
                samples[i] = (noise + tone) * env[i] * velocity
        else:
            for i in range(n):
                t = i * INV_SR
                vib = vib_depth * min(1.0, t / vib_delay) * math.sin(TWO_PI * vib_rate * t)
                ff = f * (1.0 + vib)
                s = 0.0
                for h_data in harmonics:
                    h_num, h_amp = h_data[0], h_data[1]
                    h_freq = ff * h_num
                    if h_freq >= SAMPLE_RATE / 2:
                        break
                    s += h_amp * math.sin(TWO_PI * h_freq * t)
                # Add noise
                if noise_level > 0:
                    s += noise_level * (rng.random() * 2 - 1)
                # Apply distortion
                if distortion > 0:
                    s = math.tanh(s * distortion) / max(0.1, distortion * 0.5)
                samples[i] = s * env[i] * velocity

        return samples

    def synthesize_colored_note(self, instr, freq, duration, velocity=0.8,
                                color_amount=0.25):
        """Synthesize a note with subtle instrument coloring on a clean base.

        Base (1 - color_amount): clean piano-like additive tone (8 harmonics)
        Color (color_amount): instrument's harmonic profile, vibrato, noise
        """
        n = int(duration * SAMPLE_RATE)
        if n <= 0:
            return []

        f = freq
        ca = clamp(color_amount, 0.0, 1.0)

        # --- Base tone: clean additive harmonics ---
        base = [0.0] * n
        # Simple ADSR for base
        a_len = min(int(0.01 * SAMPLE_RATE), n)
        d_len = min(int(0.05 * SAMPLE_RATE), n)
        r_len = min(int(0.08 * SAMPLE_RATE), n)
        s_level = 0.7
        base_env = [0.0] * n
        for i in range(n):
            if i < a_len:
                base_env[i] = i / max(a_len, 1)
            elif i < a_len + d_len:
                base_env[i] = 1.0 - (1.0 - s_level) * (i - a_len) / max(d_len, 1)
            elif i < n - r_len:
                base_env[i] = s_level
            else:
                base_env[i] = s_level * (n - i) / max(r_len, 1)

        for i in range(n):
            t = i * INV_SR
            s = 0.0
            for h in range(1, 9):
                h_freq = f * h
                if h_freq >= SAMPLE_RATE / 2:
                    break
                amp = 1.0 / (h ** 1.2)
                s += amp * math.sin(TWO_PI * h_freq * t)
            base[i] = s * base_env[i] * velocity

        if ca == 0.0:
            return base

        # --- Color: use instrument's characteristics (suppress noise/distortion) ---
        clean_instr = dict(instr)
        clean_instr['noise_level'] = 0.0
        clean_instr['distortion'] = min(instr.get('distortion', 0) * 0.3, 0.1)
        color = self.synthesize_note(clean_instr, freq, duration, velocity)

        # Blend
        result = [0.0] * n
        base_w = 1.0 - ca
        cn = min(len(color), n)
        for i in range(n):
            c = color[i] if i < cn else 0.0
            result[i] = base[i] * base_w + c * ca

        return result

    def generate_instrument_set(self, count=537, base_seed=42):
        """Generate a full set of unique instruments.

        Returns list of instrument definitions.
        """
        instruments = []
        families = self.FAMILIES
        techniques = self.TECHNIQUES

        for i in range(count):
            family = families[i % len(families)]
            tech_idx = (i // len(families)) % len(techniques)
            variant = i // (len(families) * len(techniques))
            name = f"{family}_v{variant}_{techniques[tech_idx]}_{i}"
            seed = base_seed + i * 7919  # Prime spacing
            instr = self.generate_instrument(name, seed)
            instruments.append(instr)

        return instruments

    def rotate_instruments(self, current_set, n_swap=50, generation=0):
        """Swap out n_swap synthetic instruments for fresh ones.

        Used in infinite radio mode to keep textures evolving.
        Only swaps synthetic instruments, not downloaded samples.
        """
        new_set = list(current_set)
        base_seed = 42 + generation * 131071  # Different seed per generation

        # Find swappable indices (non-sample-based)
        swappable = [i for i, instr in enumerate(new_set)
                     if not instr.get('is_sample', False)]

        if len(swappable) < n_swap:
            n_swap = len(swappable)

        rng = random.Random(base_seed)
        swap_indices = rng.sample(swappable, n_swap)

        for idx in swap_indices:
            old = new_set[idx]
            new_name = f"gen{generation}_{old['name']}"
            new_seed = base_seed + idx * 7919
            new_instr = self.generate_instrument(new_name, new_seed)
            new_set[idx] = new_instr

        return new_set


# ---------------------------------------------------------------------------
# INSTRUMENT KIT -- Groups instruments into scale-coherent ensembles
# ---------------------------------------------------------------------------
class InstrumentKit:
    """A kit is a set of instruments pre-assigned to roles (melody, harmony,
    bass, rhythm) that share a common scale and tonal centre.

    Kits are designed to sound good together -- like selecting a band whose
    instruments are already tuned to the same key.
    """

    def __init__(self, name, instruments, scale, root, rng_seed=0):
        self.name = name
        self.scale = scale   # list of semitone intervals
        self.root = root     # MIDI root note

        rng = random.Random(rng_seed)

        # Sort instruments into roles
        self.melody = [i for i in instruments if i.get('role') == 'melody']
        self.harmony = [i for i in instruments if i.get('role') == 'harmony']
        self.bass = [i for i in instruments if i.get('role') == 'bass']
        self.rhythm = [i for i in instruments if i.get('role') == 'rhythm']

        # If any role is empty, redistribute
        all_instr = list(instruments)
        rng.shuffle(all_instr)
        if not self.melody:
            self.melody = all_instr[:2]
        if not self.harmony:
            self.harmony = all_instr[1:3]
        if not self.bass:
            self.bass = all_instr[2:4]
        if not self.rhythm:
            self.rhythm = all_instr[3:5]

    def scale_notes(self, octave_range=2):
        """Return all MIDI notes in this kit's scale across octave_range."""
        notes = []
        for oct in range(-1, octave_range + 1):
            for interval in self.scale:
                n = self.root + oct * 12 + int(round(interval))
                if 24 <= n <= 108:
                    notes.append(n)
        return sorted(set(notes))

    def snap_to_scale(self, midi_note):
        """Snap a MIDI note to the nearest note in this kit's scale."""
        pc = (midi_note - self.root) % 12
        best = 0
        best_dist = 12
        for s in self.scale:
            s_int = int(round(s)) % 12
            dist = min(abs(pc - s_int), 12 - abs(pc - s_int))
            if dist < best_dist:
                best_dist = dist
                best = s_int
        octave = (midi_note - self.root) // 12
        return self.root + octave * 12 + best

    @staticmethod
    def build_kits(instruments, scale, root, n_kits, rng):
        """Build n_kits from a pool of instruments, each following the scale."""
        kits = []
        pool = list(instruments)
        rng.shuffle(pool)
        per_kit = max(4, len(pool) // max(n_kits, 1))
        for k in range(n_kits):
            start = k * per_kit
            end = min(start + per_kit, len(pool))
            if start >= len(pool):
                start = 0
                end = min(per_kit, len(pool))
            kit_instrs = pool[start:end]
            kit = InstrumentKit(
                f"kit_{k}", kit_instrs, scale, root,
                rng_seed=rng.randint(0, 2**31)
            )
            kits.append(kit)
        return kits


# ---------------------------------------------------------------------------
# MIDI LIBRARY -- Loads and samples from public domain classical MIDI files
# ---------------------------------------------------------------------------
class MidiLibrary:
    """Loads public domain MIDI files and extracts note sequences.

    Provides methods to sample note patterns, chord progressions,
    and rhythmic motifs from classical compositions (1600-1900).
    """

    def __init__(self, midi_dir=None):
        self.midi_dir = midi_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'midi_library'
        )
        self._note_sequences = []
        self._loaded = False

    def load(self):
        """Load all MIDI files and extract note sequences."""
        if self._loaded or not HAS_MIDO:
            return

        midi_files = []
        for root, dirs, files in os.walk(self.midi_dir):
            for f in files:
                if f.lower().endswith(('.mid', '.midi')):
                    midi_files.append(os.path.join(root, f))

        for path in midi_files:
            try:
                mid = mido.MidiFile(path)
                notes = self._extract_notes(mid)
                if len(notes) >= 8:
                    composer = os.path.basename(os.path.dirname(path))
                    tpb = getattr(mid, 'ticks_per_beat', 480)
                    self._note_sequences.append({
                        'path': path,
                        'composer': composer,
                        'notes': notes,
                        'ticks_per_beat': tpb,
                    })
            except Exception:
                continue

        self._loaded = True

    def _extract_notes(self, midi_file):
        """Extract (onset_ticks, pitch, duration_ticks, velocity) tuples from MIDI."""
        notes = []
        for track in midi_file.tracks:
            current_time = 0
            active_notes = {}
            for msg in track:
                current_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    active_notes[msg.note] = (current_time, msg.velocity)
                elif msg.type in ('note_off', 'note_on') and msg.note in active_notes:
                    start, vel = active_notes.pop(msg.note)
                    dur = current_time - start
                    if dur > 0:
                        notes.append((start, msg.note, dur, vel))
        notes.sort(key=lambda n: (n[0], n[1]))
        return notes

    def sample_phrase(self, rng, length=32, root=60, scale=None):
        """Sample a longer phrase from a random MIDI file and transpose to root.

        Takes up to ``length`` notes (default 32 for richer musical phrases).
        Returns list of (midi_note, duration_beats, velocity) tuples.
        The notes are projected onto the given scale if provided.
        """
        if not self._note_sequences:
            return self._generate_fallback_phrase(rng, length, root, scale)

        seq = rng.choice(self._note_sequences)
        notes = seq['notes']

        # Pick a random starting point -- take longer runs from the MIDI
        if len(notes) <= length:
            phrase_notes = notes
        else:
            start = rng.randint(0, len(notes) - length)
            phrase_notes = notes[start:start + length]

        # Transpose to root and project onto scale
        if not phrase_notes:
            return self._generate_fallback_phrase(rng, length, root, scale)

        # Find the phrase's center pitch
        pitches = [n[1] for n in phrase_notes]
        center = sum(pitches) / len(pitches)
        offset = root - center

        tpb = seq.get('ticks_per_beat', 480)
        result = []
        for _onset, pitch, dur_ticks, vel in phrase_notes:
            new_pitch = int(pitch + offset)
            # Project onto scale if provided
            if scale:
                new_pitch = self._snap_to_scale(new_pitch, root, scale)
            # Convert ticks to approximate beats
            dur_beats = max(0.125, dur_ticks / tpb)
            # Add humanization flex: +/- 5% duration, +/- 3% pitch
            dur_beats *= rng.uniform(0.95, 1.05)
            velocity = clamp(vel / 127.0 * rng.uniform(0.9, 1.1), 0.1, 1.0)
            result.append((clamp(new_pitch, 24, 108), dur_beats, velocity))

        return result

    def sample_chord_pattern(self, rng, root=60, scale=None, length=4):
        """Extract chord-like patterns from MIDI -- groups of simultaneous notes."""
        if not self._note_sequences:
            return None

        seq = rng.choice(self._note_sequences)
        notes = seq['notes']
        if len(notes) < 4:
            return None

        # Find groups of notes close together in time
        chords = []
        i = 0
        while i < len(notes) - 2 and len(chords) < length:
            group = [notes[i][1]]
            j = i + 1
            while j < min(i + 6, len(notes)):
                group.append(notes[j][1])
                j += 1
            if len(group) >= 3:
                # Transpose to root
                center = sum(group) / len(group)
                offset = root - center
                chord = [int(n + offset) for n in group[:4]]
                if scale:
                    chord = [self._snap_to_scale(n, root, scale) for n in chord]
                chords.append(chord)
            i = j

        return chords if chords else None

    def _snap_to_scale(self, midi_note, root, scale_intervals):
        """Snap a MIDI note to the nearest note in the given scale."""
        pc = (midi_note - root) % 12
        # Find closest scale degree (handle fractional intervals)
        best = 0
        best_dist = 12
        for s in scale_intervals:
            s_int = int(round(s)) % 12
            dist = min(abs(pc - s_int), 12 - abs(pc - s_int))
            if dist < best_dist:
                best_dist = dist
                best = s_int
        octave = (midi_note - root) // 12
        return root + octave * 12 + best

    def _generate_fallback_phrase(self, rng, length, root, scale):
        """Generate a phrase algorithmically when no MIDI files are available."""
        intervals = scale if scale else [0, 2, 4, 5, 7, 9, 11]
        result = []
        current = root
        for _ in range(length):
            step = rng.choice([-2, -1, 0, 1, 1, 2, 3])
            idx = 0
            for j, s in enumerate(intervals):
                if (current - root) % 12 >= int(round(s)):
                    idx = j
            idx = clamp(idx + step, 0, len(intervals) - 1)
            octave_shift = rng.choice([-12, 0, 0, 0, 12])
            new_note = root + int(round(intervals[idx])) + octave_shift
            new_note = clamp(new_note, 36, 96)
            dur = rng.choice([0.25, 0.25, 0.5, 0.5, 0.5, 1.0, 1.0, 2.0])
            vel = rng.uniform(0.5, 0.9)
            result.append((new_note, dur, vel))
            current = new_note
        return result

    def sample_bars(self, rng, n_bars, tempo, beats_per_bar, root=60, scale=None):
        """Sample a contiguous multi-bar segment preserving polyphonic timing.

        Returns (notes_list, segment_duration_seconds) where each note is
        (relative_time_sec, midi_note, duration_sec, velocity).
        """
        if not self._note_sequences:
            return self._generate_fallback_bars(rng, n_bars, tempo, beats_per_bar,
                                                root, scale)

        seq = rng.choice(self._note_sequences)
        notes = seq['notes']
        tpb = seq.get('ticks_per_beat', 480)

        if len(notes) < 8:
            return self._generate_fallback_bars(rng, n_bars, tempo, beats_per_bar,
                                                root, scale)

        # Estimate ticks per bar from tempo and tpb
        ticks_per_bar = tpb * beats_per_bar
        segment_ticks = ticks_per_bar * n_bars

        # Pick a random starting onset
        max_onset = notes[-1][0]
        if max_onset <= segment_ticks:
            start_tick = 0
        else:
            start_tick = rng.randint(0, max(0, int(max_onset - segment_ticks)))

        end_tick = start_tick + segment_ticks

        # Collect notes in the window
        segment_notes = []
        for onset, pitch, dur, vel in notes:
            if onset < start_tick:
                continue
            if onset >= end_tick:
                break
            segment_notes.append((onset - start_tick, pitch, dur, vel))

        if not segment_notes:
            return self._generate_fallback_bars(rng, n_bars, tempo, beats_per_bar,
                                                root, scale)

        # Transpose to root and snap to scale
        pitches = [n[1] for n in segment_notes]
        center = sum(pitches) / len(pitches)
        offset = root - center

        # Convert to seconds
        secs_per_tick = 60.0 / (tempo * tpb)
        segment_duration = segment_ticks * secs_per_tick

        result = []
        for onset_t, pitch, dur_t, vel in segment_notes:
            new_pitch = int(pitch + offset)
            if scale:
                new_pitch = self._snap_to_scale(new_pitch, root, scale)
            new_pitch = clamp(new_pitch, 24, 108)
            t_sec = onset_t * secs_per_tick
            dur_sec = max(0.02, dur_t * secs_per_tick)
            velocity = clamp(vel / 127.0, 0.1, 1.0)
            result.append((t_sec, new_pitch, dur_sec, velocity))

        return (result, segment_duration)

    def _generate_fallback_bars(self, rng, n_bars, tempo, beats_per_bar,
                                root, scale):
        """Generate fallback bars algorithmically when no MIDI files available."""
        intervals = scale if scale else [0, 2, 4, 5, 7, 9, 11]
        beat_dur = 60.0 / tempo
        segment_duration = n_bars * beats_per_bar * beat_dur

        result = []
        t = 0.0
        current = root
        while t < segment_duration:
            step = rng.choice([-2, -1, 0, 1, 1, 2])
            idx = 0
            for j, s in enumerate(intervals):
                if (current - root) % 12 >= int(round(s)):
                    idx = j
            idx = clamp(idx + step, 0, len(intervals) - 1)
            new_note = root + int(round(intervals[idx]))
            octave_shift = rng.choice([-12, 0, 0, 12])
            new_note = clamp(new_note + octave_shift, 36, 96)
            dur = rng.choice([0.25, 0.5, 0.5, 1.0]) * beat_dur
            vel = rng.uniform(0.4, 0.85)
            result.append((t, new_note, dur, vel))
            t += dur
            current = new_note

        return (result, segment_duration)

    def _assess_loop_friendliness(self, notes, start_tick, end_tick, tpb):
        """Score how well a segment loops (0.0-1.0).

        Checks pitch class overlap at boundaries, note density balance,
        and clean note endings.
        """
        if not notes:
            return 0.0

        segment_notes = [(o, p, d, v) for o, p, d, v in notes
                         if start_tick <= o < end_tick]
        if len(segment_notes) < 4:
            return 0.1

        # 1. Pitch class overlap at start vs end (0-0.4)
        boundary = (end_tick - start_tick) // 8
        start_pcs = set((p % 12) for o, p, d, v in segment_notes
                        if o < start_tick + boundary)
        end_pcs = set((p % 12) for o, p, d, v in segment_notes
                       if o >= end_tick - boundary)
        if start_pcs and end_pcs:
            overlap = len(start_pcs & end_pcs) / max(len(start_pcs | end_pcs), 1)
        else:
            overlap = 0.0
        score = overlap * 0.4

        # 2. Note density balance (0-0.3): similar density in first/second half
        mid = (start_tick + end_tick) // 2
        first_half = sum(1 for o, p, d, v in segment_notes if o < mid)
        second_half = len(segment_notes) - first_half
        if first_half + second_half > 0:
            balance = 1.0 - abs(first_half - second_half) / (first_half + second_half)
        else:
            balance = 0.0
        score += balance * 0.3

        # 3. Clean endings (0-0.3): notes ending near segment boundary
        cut_notes = sum(1 for o, p, d, v in segment_notes
                        if o + d > end_tick + tpb)
        cut_ratio = cut_notes / max(len(segment_notes), 1)
        score += (1.0 - cut_ratio) * 0.3

        return clamp(score, 0.0, 1.0)

    def sample_bars_seeded(self, sim_state, n_bars, tempo, beats_per_bar,
                           root=60, scale=None, rng=None):
        """Sample MIDI bars using simulation state as deterministic seed.

        Uses hash of sim_state to pick MIDI file and start position.
        Tries up to 3 offsets for best loop-friendliness score.
        Returns (notes_list, segment_duration, midi_info) where midi_info
        contains the source file path and detected programs.
        """
        if not self._note_sequences:
            fb = self._generate_fallback_bars(rng or random.Random(42),
                                              n_bars, tempo, beats_per_bar,
                                              root, scale)
            return (fb[0], fb[1], {'path': None, 'programs': set()})

        if rng is None:
            rng = random.Random(42)

        # Hash simulation state for deterministic selection
        if sim_state:
            state_str = repr(sorted(sim_state.items()))
            h = hashlib.sha256(state_str.encode()).hexdigest()
            idx = int(h[:8], 16) % len(self._note_sequences)
        else:
            idx = rng.randint(0, len(self._note_sequences) - 1)

        seq = self._note_sequences[idx]
        notes = seq['notes']
        tpb = seq.get('ticks_per_beat', 480)

        if len(notes) < 8:
            fb = self._generate_fallback_bars(rng, n_bars, tempo, beats_per_bar,
                                              root, scale)
            return (fb[0], fb[1], {'path': seq.get('path'), 'programs': set()})

        ticks_per_bar = tpb * beats_per_bar
        segment_ticks = ticks_per_bar * n_bars
        max_onset = notes[-1][0]

        # Try up to 3 offsets, pick best loop score
        best_start = 0
        best_score = -1.0
        for attempt in range(3):
            if sim_state and attempt == 0:
                h2 = hashlib.sha256((state_str + str(attempt)).encode()).hexdigest()
                candidate = int(h2[8:16], 16) % max(1, int(max_onset))
            else:
                candidate = rng.randint(0, max(0, int(max_onset - segment_ticks)))
            score = self._assess_loop_friendliness(notes, candidate,
                                                    candidate + segment_ticks, tpb)
            if score > best_score:
                best_score = score
                best_start = candidate

        start_tick = best_start
        end_tick = start_tick + segment_ticks

        # Collect notes in window
        segment_notes = [(o - start_tick, p, d, v)
                         for o, p, d, v in notes
                         if start_tick <= o < end_tick]

        if not segment_notes:
            fb = self._generate_fallback_bars(rng, n_bars, tempo, beats_per_bar,
                                              root, scale)
            return (fb[0], fb[1], {'path': seq.get('path'), 'programs': set()})

        # Transpose to root and snap to scale
        pitches = [n[1] for n in segment_notes]
        center = sum(pitches) / len(pitches)
        offset = root - center

        secs_per_tick = 60.0 / (tempo * tpb)
        segment_duration = segment_ticks * secs_per_tick

        result = []
        for onset_t, pitch, dur_t, vel in segment_notes:
            new_pitch = int(pitch + offset)
            if scale:
                new_pitch = self._snap_to_scale(new_pitch, root, scale)
            new_pitch = clamp(new_pitch, 24, 108)
            t_sec = onset_t * secs_per_tick
            dur_sec = max(0.02, dur_t * secs_per_tick)
            velocity = clamp(vel / 127.0, 0.1, 1.0)
            result.append((t_sec, new_pitch, dur_sec, velocity))

        # Detect programs (instruments) from source MIDI
        programs = set()
        if HAS_MIDO and seq.get('path'):
            try:
                mid = mido.MidiFile(seq['path'])
                for track in mid.tracks:
                    for msg in track:
                        if msg.type == 'program_change':
                            programs.add(msg.program)
            except Exception:
                pass

        midi_info = {
            'path': seq.get('path'),
            'programs': programs,
            'start_tick': start_tick,
            'end_tick': end_tick,
            'tpb': tpb,
            'loop_score': best_score,
        }

        return (result, segment_duration, midi_info)

    @staticmethod
    def render_fluidsynth(midi_path, gm_program, tempo_factor=1.0,
                          start_tick=0, end_tick=None):
        """Render a MIDI file through FluidSynth with a specific GM instrument.

        Creates a temp MIDI with the target program_change, renders via
        FluidSynth+FluidR3_GM, returns (left_samples, right_samples) as floats.
        Returns None if FluidSynth is unavailable.
        """
        if not HAS_FLUIDSYNTH or not HAS_MIDO:
            return None

        import tempfile

        try:
            mid = mido.MidiFile(midi_path)
        except Exception:
            return None

        # Build a new MIDI with target instrument and optional tempo scaling
        new_mid = mido.MidiFile(ticks_per_beat=mid.ticks_per_beat)

        for i, track in enumerate(mid.tracks):
            new_track = mido.MidiTrack()
            new_mid.tracks.append(new_track)

            # Insert program change at start of first track
            if i == 0:
                new_track.append(mido.Message('program_change',
                                              program=gm_program, time=0))
                if tempo_factor != 1.0:
                    # Adjust tempo
                    base_tempo = 500000  # 120 BPM default
                    for msg in track:
                        if msg.type == 'set_tempo':
                            base_tempo = msg.tempo
                            break
                    new_tempo = int(base_tempo / tempo_factor)
                    new_track.append(mido.MetaMessage('set_tempo',
                                                       tempo=new_tempo, time=0))

            current_time = 0
            for msg in track:
                current_time += msg.time
                if start_tick and current_time < start_tick:
                    continue
                if end_tick and current_time > end_tick:
                    break
                # Replace any program_change with our target
                if msg.type == 'program_change':
                    new_track.append(mido.Message('program_change',
                                                  program=gm_program,
                                                  time=msg.time))
                else:
                    new_track.append(msg.copy())

        try:
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tf:
                temp_mid = tf.name
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wf:
                temp_wav = wf.name

            new_mid.save(temp_mid)

            subprocess.run(
                [_FLUIDSYNTH_PATH, '-ni', _FLUIDR3_SF2, temp_mid,
                 '-F', temp_wav, '-r', str(SAMPLE_RATE), '-g', '0.6'],
                capture_output=True, timeout=60
            )

            if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) < 100:
                return None

            # Read WAV into float samples
            with wave.open(temp_wav, 'rb') as wf:
                n_channels = wf.getnchannels()
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)

            left = [0.0] * n_frames
            right = [0.0] * n_frames
            for i in range(n_frames):
                if n_channels == 2:
                    l_val = struct.unpack_from('<h', raw, i * 4)[0]
                    r_val = struct.unpack_from('<h', raw, i * 4 + 2)[0]
                    left[i] = l_val / 32768.0
                    right[i] = r_val / 32768.0
                else:
                    val = struct.unpack_from('<h', raw, i * 2)[0]
                    left[i] = val / 32768.0
                    right[i] = val / 32768.0

            return (left, right)

        except Exception:
            return None
        finally:
            for p in [temp_mid, temp_wav]:
                try:
                    os.unlink(p)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# TTS ENGINE -- Text-to-speech for voice injection
# ---------------------------------------------------------------------------
class TTSEngine:
    """Multi-engine text-to-speech: Silero (preferred), espeak-ng, flite,
    festival, pico2wave.

    Generates spoken word segments from project source code phrases,
    with voice characteristics chosen based on simulation epoch.

    All text is sanitized before passing to any TTS subprocess to prevent
    shell injection attacks — even though subprocess is called with list
    args (no shell=True), defense-in-depth sanitization strips control
    characters and limits length.

    Silero TTS: Apache 2.0 license, multiple English voices.
    espeak-ng: GPL, primary CLI fallback.
    flite: BSD-like, Carnegie Mellon voices.
    festival: custom license, Edinburgh voices.
    pico2wave: Apache 2.0, SVOX voices.
    """

    # espeak-ng voice variants by epoch character
    ESPEAK_VOICES = [
        'en-us', 'en-gb', 'en-gb-scotland', 'en-gb-x-rp',
        'en-gb-x-gbclan', 'en-gb-x-gbcwmd', 'en-029',
    ]

    # flite voice variants
    FLITE_VOICES = ['slt', 'rms', 'awb', 'kal', 'kal16']

    # Silero speaker IDs (v3_en model has ~100+ speakers)
    SILERO_SPEAKERS = [f'en_{i}' for i in range(118)]

    # Maximum text length to prevent abuse
    MAX_TTS_TEXT_LENGTH = 500

    def __init__(self):
        self._silero_model = None
        self._silero_available = False
        self._available_engines = self._detect_engines()
        self._try_load_silero()

    def _detect_engines(self):
        """Detect which CLI TTS engines are available."""
        engines = []
        for cmd, test_args in [
            ('espeak-ng', ['--version']),
            ('flite', ['--version']),
            ('festival', ['--version']),
            ('pico2wave', ['--help']),
        ]:
            try:
                subprocess.run([cmd] + test_args, capture_output=True, timeout=5)
                engines.append(cmd)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        return engines if engines else ['espeak-ng']

    def _try_load_silero(self):
        """Attempt to load Silero TTS model."""
        global _SILERO_MODEL, _SILERO_AVAILABLE
        if _SILERO_MODEL is not None:
            self._silero_model = _SILERO_MODEL
            self._silero_available = _SILERO_AVAILABLE
            return

        if not _TORCH_AVAILABLE:
            return

        model_path = os.path.join(PROJECT_ROOT, 'apps', 'audio', 'models', 'silero_v3_en.pt')
        if os.path.exists(model_path):
            try:
                import torch
                model = torch.package.PackageImporter(model_path).load_pickle('tts_models', 'model')
                model.eval()
                self._silero_model = model
                self._silero_available = True
                _SILERO_MODEL = model
                _SILERO_AVAILABLE = True
            except Exception:
                pass

    @staticmethod
    def _sanitize_text(text):
        """Sanitize text for TTS to prevent shell injection.

        Defense-in-depth: even though subprocess is called with list args
        (no shell=True), we strip dangerous characters and limit length.
        This protects against:
        - Shell metacharacters (;|&`$(){}\\)
        - Control characters and null bytes
        - Excessively long inputs
        - Non-printable characters
        """
        import re
        if not isinstance(text, str):
            text = str(text)
        # Strip null bytes and control characters (keep newlines/spaces)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Remove shell metacharacters as defense-in-depth
        text = re.sub(r'[;|&`$\\{}]', ' ', text)
        # Collapse whitespace
        text = ' '.join(text.split())
        # Truncate to max length
        if len(text) > TTSEngine.MAX_TTS_TEXT_LENGTH:
            text = text[:TTSEngine.MAX_TTS_TEXT_LENGTH]
        return text

    def generate_speech(self, text, voice_seed=0, epoch_idx=0, engine=None):
        """Generate speech audio from text.

        Returns (samples_list, sample_rate) or (None, None) on failure.
        Voice selection is influenced by epoch_idx for simulation coherence.

        Args:
            text: Text to speak (will be sanitized).
            voice_seed: Seed for voice selection.
            epoch_idx: Simulation epoch index (affects voice character).
            engine: Specific engine to use, or None for auto-select.
        """
        text = self._sanitize_text(text)
        if not text:
            return None, None

        if engine == 'silero' and self._silero_available:
            return self._generate_silero(text, voice_seed, epoch_idx)
        if self._silero_available and engine is None:
            return self._generate_silero(text, voice_seed, epoch_idx)

        # Select CLI engine based on seed or explicit request
        if engine and engine in self._available_engines:
            chosen = engine
        elif len(self._available_engines) > 1:
            chosen = self._available_engines[
                (voice_seed + epoch_idx) % len(self._available_engines)
            ]
        else:
            chosen = 'espeak-ng'

        if chosen == 'flite':
            return self._generate_flite(text, voice_seed, epoch_idx)
        elif chosen == 'festival':
            return self._generate_festival(text, voice_seed, epoch_idx)
        elif chosen == 'pico2wave':
            return self._generate_pico2wave(text, voice_seed, epoch_idx)
        else:
            return self._generate_espeak(text, voice_seed, epoch_idx)

    def _generate_silero(self, text, voice_seed, epoch_idx):
        """Generate speech using Silero TTS."""
        try:
            import torch
            speaker_idx = (voice_seed + epoch_idx * 7) % len(self.SILERO_SPEAKERS)
            speaker = self.SILERO_SPEAKERS[speaker_idx]
            audio = self._silero_model.apply_tts(
                text=text, speaker=speaker, sample_rate=SAMPLE_RATE
            )
            if isinstance(audio, torch.Tensor):
                return audio.numpy().tolist(), SAMPLE_RATE
            return list(audio), SAMPLE_RATE
        except Exception:
            return self._generate_espeak(text, voice_seed, epoch_idx)

    def _read_wav_samples(self, wav_path):
        """Read WAV file and return (samples_list, sample_rate)."""
        try:
            with wave.open(wav_path, 'rb') as wf:
                sr = wf.getframerate()
                n_channels = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())
                samples = []
                step = 2 * n_channels  # 16-bit per channel
                for i in range(0, len(frames) - 1, step):
                    val = struct.unpack('<h', frames[i:i+2])[0]
                    samples.append(val / 32768.0)
            return samples, sr
        except Exception:
            return None, None

    def _generate_espeak(self, text, voice_seed, epoch_idx):
        """Generate speech using espeak-ng."""
        import tempfile
        voice_idx = (voice_seed + epoch_idx * 3) % len(self.ESPEAK_VOICES)
        voice = self.ESPEAK_VOICES[voice_idx]

        speed = clamp(130 + epoch_idx * 5, 100, 200)
        pitch = clamp(40 + epoch_idx * 3, 20, 80)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run(
                ['espeak-ng', '-v', voice, '-s', str(speed), '-p', str(pitch),
                 '-w', tmp_path, text],
                capture_output=True, timeout=30
            )
            if os.path.exists(tmp_path):
                return self._read_wav_samples(tmp_path)
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return None, None

    def _generate_flite(self, text, voice_seed, epoch_idx):
        """Generate speech using flite (CMU)."""
        import tempfile
        voice_idx = (voice_seed + epoch_idx * 2) % len(self.FLITE_VOICES)
        voice = self.FLITE_VOICES[voice_idx]

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run(
                ['flite', '-voice', voice, '-t', text, '-o', tmp_path],
                capture_output=True, timeout=30
            )
            if os.path.exists(tmp_path):
                return self._read_wav_samples(tmp_path)
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return None, None

    def _generate_festival(self, text, voice_seed, epoch_idx):
        """Generate speech using festival (Edinburgh)."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Festival reads text from stdin via --tts, output via SayText
            # Use text2wave for file output (safer than piping)
            proc = subprocess.run(
                ['text2wave', '-o', tmp_path],
                input=text.encode('utf-8'),
                capture_output=True, timeout=30
            )
            if proc.returncode == 0 and os.path.exists(tmp_path):
                return self._read_wav_samples(tmp_path)
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return None, None

    def _generate_pico2wave(self, text, voice_seed, epoch_idx):
        """Generate speech using pico2wave (SVOX)."""
        import tempfile
        languages = ['en-US', 'en-GB']
        lang = languages[(voice_seed + epoch_idx) % len(languages)]

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run(
                ['pico2wave', '-l', lang, '-w', tmp_path, text],
                capture_output=True, timeout=30
            )
            if os.path.exists(tmp_path):
                return self._read_wav_samples(tmp_path)
        except Exception:
            pass
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return None, None

    def get_source_phrases(self, rng, count=3):
        """Extract random phrases from project source code files."""
        source_dirs = [
            os.path.join(PROJECT_ROOT, 'simulator'),
            os.path.join(PROJECT_ROOT, 'apps', 'audio'),
            os.path.join(PROJECT_ROOT, 'ast_dsl'),
        ]
        text_files = []
        for d in source_dirs:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith('.py') and not f.startswith('test_'):
                        text_files.append(os.path.join(d, f))

        phrases = []
        for _ in range(count * 3):  # Oversample to filter
            if not text_files:
                break
            path = rng.choice(text_files)
            try:
                with open(path, 'r') as fh:
                    lines = fh.readlines()
                if not lines:
                    continue
                line = rng.choice(lines).strip()
                # Extract meaningful phrases
                # Skip empty, imports, very short
                if len(line) < 10 or line.startswith(('#', 'import', 'from', '@')):
                    continue
                # Clean up: remove code syntax
                phrase = line
                for ch in ['(', ')', '[', ']', '{', '}', '=', ':', ',', '"', "'", '\\']:
                    phrase = phrase.replace(ch, ' ')
                phrase = ' '.join(phrase.split())
                if len(phrase) > 8 and len(phrase) < 120:
                    phrases.append(phrase)
                    if len(phrases) >= count:
                        break
            except Exception:
                continue

        if not phrases:
            phrases = [
                "the universe expands from a singularity",
                "quantum fluctuations give rise to matter",
                "stars ignite in the cosmic darkness",
            ]
        return phrases[:count]


# ---------------------------------------------------------------------------
# SMOOTHING / DAMPENING FILTERS
# ---------------------------------------------------------------------------
class SmoothingFilter:
    """Multi-stage smoothing to reduce harsh MIDI-like artifacts.

    Applies: lowpass filtering, soft limiting, stereo widening,
    and gentle compression to produce more natural sound.
    """

    def __init__(self):
        self._lp_state_l = 0.0
        self._lp_state_r = 0.0

    def apply_lowpass(self, samples, cutoff_hz=6000.0):
        """Single-pole lowpass filter."""
        alpha = min(1.0, TWO_PI * cutoff_hz * INV_SR)
        state = 0.0
        out = [0.0] * len(samples)
        for i in range(len(samples)):
            state += alpha * (samples[i] - state)
            out[i] = state
        return out

    def apply_soft_limit(self, samples, threshold=0.8):
        """Soft limiting with tanh compression above threshold."""
        out = [0.0] * len(samples)
        for i in range(len(samples)):
            s = samples[i]
            if abs(s) > threshold:
                sign = 1.0 if s >= 0 else -1.0
                excess = abs(s) - threshold
                out[i] = sign * (threshold + (1 - threshold) * math.tanh(excess * 3))
            else:
                out[i] = s
        return out

    def apply_stereo_smooth(self, left, right, amount=0.15):
        """Gentle stereo cross-feed for natural width."""
        n = len(left)
        out_l = [0.0] * n
        out_r = [0.0] * n
        for i in range(n):
            out_l[i] = left[i] * (1 - amount) + right[i] * amount
            out_r[i] = right[i] * (1 - amount) + left[i] * amount
        return out_l, out_r

    def apply_gentle_compression(self, samples, ratio=3.0, threshold=0.5):
        """Gentle dynamic compression to even out volume."""
        out = [0.0] * len(samples)
        env = 0.0
        attack = 0.01
        release_t = 0.1
        a_coeff = 1 - math.exp(-1.0 / (attack * SAMPLE_RATE))
        r_coeff = 1 - math.exp(-1.0 / (release_t * SAMPLE_RATE))
        for i in range(len(samples)):
            level = abs(samples[i])
            if level > env:
                env += a_coeff * (level - env)
            else:
                env += r_coeff * (level - env)
            if env > threshold:
                gain = threshold + (env - threshold) / ratio
                gain = gain / max(env, 0.0001)
            else:
                gain = 1.0
            out[i] = samples[i] * gain
        return out

    def apply_early_reflections(self, samples, sr=SAMPLE_RATE):
        """Add early reflections for room character.

        5 delayed copies at 11/17/23/31/41ms at decreasing amplitudes.
        """
        delays_ms = [11, 17, 23, 31, 41]
        amps = [0.35, 0.25, 0.18, 0.12, 0.08]
        n = len(samples)
        out = list(samples)
        for delay_ms, amp in zip(delays_ms, amps):
            d = int(delay_ms * sr / 1000)
            for i in range(d, n):
                out[i] += samples[i - d] * amp
        # Normalize to prevent clipping
        peak = max(abs(s) for s in out) if out else 1.0
        if peak > 1.0:
            for i in range(n):
                out[i] /= peak
        return out

    def apply_reverb(self, samples, wet=0.30, sr=SAMPLE_RATE):
        """Schroeder reverb: 4 comb filters + 2 allpass filters.

        Comb filter delays: ~30/37/41/44ms. Allpass delays: ~5/1.7ms.
        """
        n = len(samples)
        dry = 1.0 - wet

        # Comb filter parameters
        comb_delays = [int(d * sr / 1000) for d in [30, 37, 41, 44]]
        comb_gains = [0.75, 0.72, 0.70, 0.68]

        comb_outputs = []
        for delay, gain in zip(comb_delays, comb_gains):
            buf = [0.0] * (n + delay)
            for i in range(n):
                buf[i + delay] = samples[i] + gain * buf[i]
            comb_outputs.append(buf[:n])

        # Sum comb outputs
        mixed = [0.0] * n
        for i in range(n):
            for co in comb_outputs:
                mixed[i] += co[i]
            mixed[i] /= len(comb_outputs)

        # Allpass filters
        ap_delays = [int(d * sr / 1000) for d in [5, 1.7]]
        ap_gain = 0.7
        for delay in ap_delays:
            if delay < 1:
                delay = 1
            buf_in = list(mixed)
            buf_out = [0.0] * n
            for i in range(n):
                delayed = buf_out[i - delay] if i >= delay else 0.0
                buf_out[i] = -ap_gain * buf_in[i] + buf_in[i - delay] if i >= delay else buf_in[i]
                buf_out[i] += ap_gain * delayed
            mixed = buf_out

        # Blend
        out = [0.0] * n
        for i in range(n):
            out[i] = samples[i] * dry + mixed[i] * wet
        # Normalize
        peak = max(abs(s) for s in out) if out else 1.0
        if peak > 1.0:
            for i in range(n):
                out[i] /= peak
        return out

    def apply_chorus(self, samples, sr=SAMPLE_RATE):
        """LFO-modulated delay for ensemble doubling.

        Base delay ~20ms, depth +/-3ms, LFO rate 0.7 Hz.
        """
        n = len(samples)
        base_delay = int(0.020 * sr)
        depth = int(0.003 * sr)
        lfo_rate = 0.7
        out = list(samples)
        for i in range(n):
            lfo = math.sin(TWO_PI * lfo_rate * i / sr)
            delay = base_delay + int(lfo * depth)
            src = i - delay
            if 0 <= src < n:
                out[i] = samples[i] * 0.7 + samples[src] * 0.3
        return out


# ---------------------------------------------------------------------------
# MOOD SEGMENT -- Encapsulates 42 seconds of musical character
# ---------------------------------------------------------------------------
class MoodSegment:
    """Represents a musical mood segment at multiples of 42 seconds.

    v7: Durations are multiples of 42s (42, 84, 126, 168, 210) for
    longer mood development. 2-4 instruments form a small band.
    All parameters are derived from the simulation state at the moment
    the segment begins, sampling from different regions of space.
    """

    def __init__(self, segment_idx, epoch, epoch_idx, sim_state, rng_seed):
        self.segment_idx = segment_idx
        self.epoch = epoch
        self.epoch_idx = epoch_idx
        self.rng = random.Random(rng_seed)

        epoch_music = EPOCH_MUSIC.get(epoch, EPOCH_MUSIC['Present'])

        # Mood duration: multiples of 42 seconds (42, 84, 126, 168, 210)
        # v7: longer mood segments at 42-second boundaries for richer development
        duration_multiples = [42.0, 84.0, 84.0, 126.0, 126.0, 168.0, 210.0]
        self.duration = self.rng.choice(duration_multiples)

        # Time signature (from Wikipedia-documented set)
        available_ts = epoch_music['time_sigs']
        if self.rng.random() < 0.3:
            available_ts = available_ts + EDM_TIME_SIGS
        self.time_sig = self.rng.choice(available_ts)
        ts_info = TIME_SIGNATURES.get(self.time_sig, TIME_SIGNATURES['4/4'])
        self.beats_per_bar = ts_info['beats']

        # Tempo (BPM) from simulation conditions
        tempo_lo, tempo_hi = epoch_music['tempo']
        temp = sim_state.get('temperature', 1e6)
        temp_factor = clamp(math.log10(max(1, temp)) / 15.0, 0.0, 1.0)
        self.tempo = tempo_lo + (tempo_hi - tempo_lo) * temp_factor
        if self.rng.random() < 0.2:
            self.tempo = min(self.tempo * 1.2, 160)

        # Scale (from well-known harmonic systems)
        self.scale_name = self.rng.choice(epoch_music['scales'])
        self.scale = SCALES.get(self.scale_name, SCALES['ionian'])

        # Root note
        root = EPOCH_ROOTS.get(epoch, 60)
        particles = sim_state.get('particles', 0)
        region_shift = (particles * 7) % 12
        self.root = root + region_shift - 6

        # Chord progression
        prog_name = self.rng.choice(list(PROGRESSIONS.keys()))
        self.progression = PROGRESSIONS[prog_name]
        self.progression_name = prog_name

        # Number of concurrent instruments: 2-4 (small band)
        # v7: reduced from 6-16 to 2-4 for tighter, more focused ensemble
        density = epoch_music['density']
        atoms = sim_state.get('atoms', 0)
        sine_val = math.sin(segment_idx * 0.7 + atoms * 0.001)
        instrument_factor = (sine_val + 1) / 2  # 0..1
        self.n_instruments = clamp(
            int(2 + instrument_factor * density * 2), 2, 4
        )

        # Number of instrument kits: 1-3
        self.n_kits = self.rng.choice([1, 1, 2, 2, 2, 3])

        # Scale family for mashup blending
        self.family = epoch_music['family']

        # Whether to apply dampening/smoothing
        self.dampen = self.rng.random() < 0.4

        # Number of concurrent instrument voices: 1-5
        voice_factor = (sine_val + 1) / 2  # reuse from n_instruments
        self.n_voices = clamp(int(1 + voice_factor * density * 5), 1, 5)


# ---------------------------------------------------------------------------
# RADIO ENGINE -- The main music generation engine
# ---------------------------------------------------------------------------
class RadioEngine:
    """In The Beginning Radio v7 -- Cosmic simulation music station.

    Generates continuously evolving music with mood segments at multiples
    of 42 seconds, morph transitions, 2-4 instrument small band ensembles,
    7 rondo forms with 6 arpeggio variations, harmonic consonance (Helmholtz/Hartmann) enforcement,
    anti-click processing, diverse instrument family selection, MIDI sampling,
    and TTS injection during mood transitions.
    """

    MORPH_DURATION = 6.0     # seconds of morph-transition between moods
    FADE_IN_DURATION = 5.0   # seconds of fade-in at start
    FADE_OUT_DURATION = 8.0  # seconds of fade-out at end

    def __init__(self, seed=42, total_duration=1800.0):
        self.seed = seed
        self.total_duration = total_duration
        self.rng = random.Random(seed)

        # Instrument factory
        self.factory = InstrumentFactory(seed)
        self.instruments = self.factory.generate_instrument_set(537, seed)
        self._generation = 0

        # MIDI library
        self.midi_lib = MidiLibrary()
        self.midi_lib.load()

        # TTS engine
        self.tts = TTSEngine()

        # Smoothing filter
        self.smoother = SmoothingFilter()

        # Pre-compute segment layout: variable-length moods (42-188s)
        self.segments = self._plan_segments()

        # TTS: once per 10-minute window, placed during a morph transition
        self.tts_transitions = self._plan_tts()


    def _plan_segments(self):
        """Pre-compute segment layout with 42-second multiple durations.

        v7: durations are multiples of 42s (42, 84, 126, 168, 210) for
        longer mood development and fewer transitions (reduces clicking).
        """
        duration_multiples = [42.0, 84.0, 84.0, 126.0, 126.0, 168.0, 210.0]
        segments = []
        t = 0.0
        idx = 0
        while t < self.total_duration:
            seg_rng = random.Random(self.seed + idx * 31337)
            duration = seg_rng.choice(duration_multiples)
            # Don't overshoot
            if t + duration > self.total_duration:
                duration = self.total_duration - t
                if duration < 1.0:
                    break
            segments.append({'start': t, 'duration': duration, 'idx': idx})
            t += duration
            idx += 1
        # Ensure at least one segment for short durations
        if not segments and self.total_duration > 0:
            segments.append({'start': 0.0, 'duration': self.total_duration, 'idx': 0})
        return segments

    def _plan_tts(self):
        """Plan TTS injection: once per 10-minute window, during a morph."""
        transitions = set()
        window = 600.0  # 10 minutes
        n_windows = max(1, int(self.total_duration / window))
        for w in range(n_windows):
            window_start = w * window
            window_end = min((w + 1) * window, self.total_duration)
            # Find segment transitions within this window
            candidates = []
            for i, seg in enumerate(self.segments[:-1]):
                trans_time = seg['start'] + seg['duration']
                if window_start < trans_time < window_end:
                    candidates.append(i)
            if candidates:
                pick = self.rng.choice(candidates)
                transitions.add(pick)
        return transitions

    def render(self, sim_states=None):
        """Render the full audio piece with morph transitions.

        Returns (left_channel, right_channel) as lists of float samples.
        """
        total_samples = int(self.total_duration * SAMPLE_RATE)
        left = [0.0] * total_samples
        right = [0.0] * total_samples

        n_segments = len(self.segments)
        morph_samples = int(self.MORPH_DURATION * SAMPLE_RATE)

        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        for seg_idx in range(n_segments):
            seg_info = self.segments[seg_idx]
            seg_start_sample = int(seg_info['start'] * SAMPLE_RATE)
            seg_duration = seg_info['duration']
            segment_samples = int(seg_duration * SAMPLE_RATE)
            if seg_start_sample >= total_samples:
                break

            # Determine epoch
            time_pos = seg_info['start']
            epoch_idx = int(time_pos / self.total_duration * 12.999)
            epoch_idx = clamp(epoch_idx, 0, 12)
            epoch = EPOCH_ORDER[epoch_idx]
            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

            # Create mood segment (now with variable duration)
            mood = MoodSegment(
                seg_idx, epoch, epoch_idx, sim_state,
                self.seed + seg_idx * 31337
            )

            # Build instrument kits for this mood
            selected = self._select_instruments(mood)
            kits = InstrumentKit.build_kits(
                selected, mood.scale, mood.root, mood.n_kits, mood.rng
            )

            # Render the segment
            seg_left, seg_right = self._render_segment(
                mood, kits, segment_samples, sim_state
            )

            # Apply smoothing/dampening if mood says so
            if mood.dampen:
                seg_left = self.smoother.apply_lowpass(seg_left, 5000)
                seg_right = self.smoother.apply_lowpass(seg_right, 5000)
                seg_left = self.smoother.apply_gentle_compression(seg_left)
                seg_right = self.smoother.apply_gentle_compression(seg_right)

            # Apply morph transition envelope
            seg_end = min(seg_start_sample + len(seg_left), total_samples)
            seg_len = seg_end - seg_start_sample

            for i in range(seg_len):
                fade = 1.0
                # Morph-in from previous mood (smooth sine curve, not linear)
                if i < morph_samples and seg_idx > 0:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / morph_samples)
                # Morph-out to next mood
                remaining = seg_len - i
                if remaining < morph_samples and seg_idx < n_segments - 1:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - remaining / morph_samples))

                left[seg_start_sample + i] += seg_left[i] * fade
                right[seg_start_sample + i] += seg_right[i] * fade

            # Inject TTS during morph transition if this is a designated one
            if seg_idx in self.tts_transitions:
                trans_start = seg_start_sample + seg_len - morph_samples
                self._inject_tts_at(left, right, trans_start, total_samples,
                                    mood, epoch_idx)

            # Rotate instruments periodically
            if seg_idx > 0 and seg_idx % 14 == 0:
                self._generation += 1
                self.instruments = self.factory.rotate_instruments(
                    self.instruments, n_swap=50, generation=self._generation
                )

        # Apply master fade-in and fade-out
        fade_in_samples = int(self.FADE_IN_DURATION * SAMPLE_RATE)
        fade_out_samples = int(self.FADE_OUT_DURATION * SAMPLE_RATE)

        for i in range(min(fade_in_samples, total_samples)):
            fade = i / fade_in_samples
            left[i] *= fade
            right[i] *= fade

        fade_out_start = max(0, total_samples - fade_out_samples)
        for i in range(fade_out_start, total_samples):
            fade = (total_samples - i) / fade_out_samples
            left[i] *= fade
            right[i] *= fade

        # Master smoothing
        left = self.smoother.apply_soft_limit(left)
        right = self.smoother.apply_soft_limit(right)
        left, right = self.smoother.apply_stereo_smooth(left, right, 0.1)

        return left, right

    def render_streaming(self, wav_file, sim_states=None):
        """Render audio segment-by-segment directly to an open WAV file.

        Uses morph transitions between variable-length mood segments.
        Each segment is rendered, morphed, and flushed to disk.
        """
        total_samples = int(self.total_duration * SAMPLE_RATE)
        n_segments = len(self.segments)
        morph_samples = int(self.MORPH_DURATION * SAMPLE_RATE)
        fade_in_samples = int(self.FADE_IN_DURATION * SAMPLE_RATE)
        fade_out_samples = int(self.FADE_OUT_DURATION * SAMPLE_RATE)

        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        # Rolling buffer for overlap (morph region)
        max_seg_samples = int(220 * SAMPLE_RATE)  # max segment length (210s) + margin
        buf_len = max_seg_samples + morph_samples * 2
        buf_left = [0.0] * buf_len
        buf_right = [0.0] * buf_len
        buf_global_start = 0
        samples_written = 0

        _tanh = math.tanh

        for seg_idx in range(n_segments):
            seg_info = self.segments[seg_idx]
            seg_global_start = int(seg_info['start'] * SAMPLE_RATE)
            seg_duration = seg_info['duration']
            segment_samples = int(seg_duration * SAMPLE_RATE)
            if seg_global_start >= total_samples:
                break

            time_pos = seg_info['start']
            epoch_idx = int(time_pos / self.total_duration * 12.999)
            epoch_idx = clamp(epoch_idx, 0, 12)
            epoch = EPOCH_ORDER[epoch_idx]
            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

            mood = MoodSegment(
                seg_idx, epoch, epoch_idx, sim_state,
                self.seed + seg_idx * 31337
            )
            selected = self._select_instruments(mood)
            kits = InstrumentKit.build_kits(
                selected, mood.scale, mood.root, mood.n_kits, mood.rng
            )
            seg_left, seg_right = self._render_segment(
                mood, kits, segment_samples, sim_state
            )

            if mood.dampen:
                seg_left = self.smoother.apply_lowpass(seg_left, 5000)
                seg_right = self.smoother.apply_lowpass(seg_right, 5000)
                seg_left = self.smoother.apply_gentle_compression(seg_left)
                seg_right = self.smoother.apply_gentle_compression(seg_right)

            # Add segment with morph envelope into rolling buffer
            seg_end_global = min(seg_global_start + len(seg_left), total_samples)
            seg_len = seg_end_global - seg_global_start

            for i in range(seg_len):
                global_i = seg_global_start + i
                buf_i = global_i - buf_global_start
                while buf_i >= len(buf_left):
                    buf_left.append(0.0)
                    buf_right.append(0.0)

                fade = 1.0
                if i < morph_samples and seg_idx > 0:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / morph_samples)
                remaining = seg_len - i
                if remaining < morph_samples and seg_idx < n_segments - 1:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - remaining / morph_samples))

                if global_i < fade_in_samples:
                    fade *= global_i / fade_in_samples
                elif global_i >= total_samples - fade_out_samples:
                    fade *= (total_samples - global_i) / fade_out_samples

                buf_left[buf_i] += seg_left[i] * fade
                buf_right[buf_i] += seg_right[i] * fade

            # Inject TTS during morph if designated
            if seg_idx in self.tts_transitions:
                trans_start = seg_global_start + seg_len - morph_samples
                self._inject_tts_into_buf(
                    buf_left, buf_right, buf_global_start,
                    trans_start, total_samples, mood, epoch_idx
                )

            # Flush completed audio
            if seg_idx < n_segments - 1:
                next_seg_start = int(self.segments[seg_idx + 1]['start'] * SAMPLE_RATE)
                flush_up_to = next_seg_start - morph_samples
            else:
                flush_up_to = total_samples

            flush_end = min(flush_up_to, total_samples)
            flush_count = flush_end - samples_written
            if flush_count > 0:
                data = bytearray(flush_count * 4)
                for j in range(flush_count):
                    buf_j = (samples_written + j) - buf_global_start
                    lv = buf_left[buf_j] if 0 <= buf_j < len(buf_left) else 0.0
                    rv = buf_right[buf_j] if 0 <= buf_j < len(buf_right) else 0.0
                    lv, rv = lv * 0.9 + rv * 0.1, rv * 0.9 + lv * 0.1
                    li = int(_tanh(lv) * 32767)
                    ri = int(_tanh(rv) * 32767)
                    struct.pack_into('<hh', data, j * 4,
                                   max(-32767, min(32767, li)),
                                   max(-32767, min(32767, ri)))
                wav_file.writeframes(bytes(data))
                samples_written = flush_end

                keep_from = flush_end - buf_global_start
                if 0 < keep_from < len(buf_left):
                    buf_left = buf_left[keep_from:] + [0.0] * keep_from
                    buf_right = buf_right[keep_from:] + [0.0] * keep_from
                    buf_global_start = flush_end
                elif keep_from >= len(buf_left):
                    buf_left = [0.0] * buf_len
                    buf_right = [0.0] * buf_len
                    buf_global_start = flush_end

            if seg_idx > 0 and seg_idx % 14 == 0:
                self._generation += 1
                self.instruments = self.factory.rotate_instruments(
                    self.instruments, n_swap=50, generation=self._generation
                )

            if seg_idx % 3 == 0:
                elapsed_min = seg_info['start'] / 60
                print(f"  [Streaming] Segment {seg_idx+1}/{n_segments} "
                      f"({elapsed_min:.1f}min, {seg_duration:.0f}s) epoch={epoch} "
                      f"written={samples_written/SAMPLE_RATE:.0f}s",
                      flush=True)

        # Flush remaining
        remaining_count = total_samples - samples_written
        if remaining_count > 0:
            data = bytearray(remaining_count * 4)
            for j in range(remaining_count):
                buf_j = (samples_written + j) - buf_global_start
                lv = buf_left[buf_j] if 0 <= buf_j < len(buf_left) else 0.0
                rv = buf_right[buf_j] if 0 <= buf_j < len(buf_right) else 0.0
                lv, rv = lv * 0.9 + rv * 0.1, rv * 0.9 + lv * 0.1
                li = int(_tanh(lv) * 32767)
                ri = int(_tanh(rv) * 32767)
                struct.pack_into('<hh', data, j * 4,
                               max(-32767, min(32767, li)),
                               max(-32767, min(32767, ri)))
            wav_file.writeframes(bytes(data))
            samples_written += remaining_count

        return samples_written

    def _generate_sim_states(self, n_segments):
        """Generate synthetic simulation states for standalone rendering."""
        states = []
        for i in range(n_segments):
            progress = i / max(n_segments - 1, 1)
            states.append({
                'temperature': 1e15 * math.exp(-progress * 30) + 300,
                'particles': int(10 + progress * 1000 * math.sin(i * 0.3 + 1)),
                'atoms': int(max(0, progress - 0.3) * 500),
                'molecules': int(max(0, progress - 0.5) * 200),
                'cells': int(max(0, progress - 0.7) * 50),
                'generation': int(max(0, progress - 0.8) * 100),
            })
        return states

    def _select_instruments(self, mood):
        """Select instruments for this mood segment."""
        n = mood.n_instruments
        rng = mood.rng
        selected = rng.sample(self.instruments, min(n, len(self.instruments)))
        return selected

    # ------------------------------------------------------------------
    # Chord / rondo / voice / tempo helpers
    # ------------------------------------------------------------------

    def _compute_tempo_multiplier(self, sim_state):
        """Compute a 1.5X-2.5X tempo multiplier from simulation state hash.

        v7: reduced from 2X-4X to 1.5X-2.5X for more natural pacing
        and to reduce clicking artifacts from overly fast playback.
        """
        if not sim_state:
            return 2.0
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)

    def _build_chord_from_note(self, midi_note, root, scale_name,
                               scale_intervals, n_notes=3, rng=None):
        """Expand a single MIDI note into a 2-5 note consonant chord.

        Uses diatonic chord quality lookup and consonance enforcement.
        Returns list of MIDI note numbers forming the chord.
        """
        # Snap base note to scale first
        base = self.midi_lib._snap_to_scale(midi_note, root, scale_intervals)

        # Determine scale degree
        pc = (base - root) % 12
        intervals = [int(round(s)) % 12 for s in scale_intervals]

        degree = 0
        best_dist = 12
        for i, s in enumerate(intervals):
            dist = min(abs(pc - s), 12 - abs(pc - s))
            if dist < best_dist:
                best_dist = dist
                degree = i

        # Get chord quality from diatonic table
        qualities = DIATONIC_CHORD_QUALITY.get(scale_name)
        if qualities and degree < len(qualities):
            chord_type = qualities[degree]
        else:
            # Fallback: even degrees major, odd minor
            chord_type = 'maj' if degree % 2 == 0 else 'min'

        # Build chord intervals based on n_notes
        n_notes = clamp(n_notes, 2, 5)
        if n_notes == 2:
            chord_ivs = CHORD_INTERVALS.get('pow', [0, 7])
        elif n_notes == 3:
            chord_ivs = CHORD_INTERVALS.get(chord_type, [0, 4, 7])
        elif n_notes == 4:
            ext = chord_type + '7'
            chord_ivs = CHORD_INTERVALS.get(ext,
                        CHORD_INTERVALS.get(chord_type, [0, 4, 7]) + [10])
        else:  # 5 notes
            ext = chord_type + '7'
            base_ivs = CHORD_INTERVALS.get(ext,
                       CHORD_INTERVALS.get(chord_type, [0, 4, 7]) + [10])
            chord_ivs = list(base_ivs) + [14]  # add 9th

        chord_ivs = chord_ivs[:n_notes]

        # Build chord notes
        chord = []
        for iv in chord_ivs:
            note = base + iv
            note = self.midi_lib._snap_to_scale(note, root, scale_intervals)
            note = clamp(note, 24, 108)
            chord.append(note)

        # v7: Enhanced harmonic consonance (Helmholtz/Hartmann) enforcement
        # Reject minor 2nd (semitone), tritone in bass, and enforce
        # that intervals between voices are consonant (3rds, 4ths, 5ths, 6ths, octaves)
        CONSONANT_INTERVALS = {3, 4, 5, 7, 8, 9, 12, 15, 16}  # semitones
        chord_sorted = sorted(set(chord))
        clean = [chord_sorted[0]] if chord_sorted else [base]
        for i in range(1, len(chord_sorted)):
            interval = chord_sorted[i] - clean[-1]
            bass_interval = chord_sorted[i] - clean[0]
            # Reject semitone clash and tritone against bass
            if interval <= 1:
                continue
            if bass_interval % 12 == 6 and len(clean) < 3:
                # Tritone against bass -- try shifting up a semitone
                alt = chord_sorted[i] + 1
                alt = self.midi_lib._snap_to_scale(alt, root, scale_intervals)
                alt_interval = alt - clean[-1]
                if alt_interval > 1 and (alt - clean[0]) % 12 != 6:
                    clean.append(clamp(alt, 24, 108))
                continue
            clean.append(chord_sorted[i])

        # Ensure we have at least 2 notes
        if len(clean) < 2:
            fifth = self.midi_lib._snap_to_scale(base + 7, root, scale_intervals)
            clean.append(clamp(fifth, 24, 108))

        return clean[:n_notes]

    def _build_rondo_sections(self, base_notes, root, scale_name,
                              scale_intervals, segment_duration, rng):
        """Build rondo structure from chord-expanded notes with varied arpeggiation.

        v7: Randomly selects from 7 rondo patterns and applies different
        arpeggio forms to each section for varied mini-loop arrangements.

        Returns list of (section_label, notes_list) tuples where each
        note is (t_sec, [chord_notes], dur_sec, velocity).
        """
        duration = segment_duration

        # v7: Choose rondo pattern from expanded set
        pattern_names = list(RONDO_PATTERNS.keys())
        if duration > 150:
            # Longer segments get longer patterns
            pattern_name = rng.choice(['ABACADA', 'ABACBA', 'ABCDA'])
        elif duration > 80:
            pattern_name = rng.choice(pattern_names)
        else:
            pattern_name = rng.choice(['ABACA', 'AABA', 'ABCBA', 'AABBA'])
        pattern = RONDO_PATTERNS[pattern_name]

        # v7: Assign arpeggio forms to sections for variety
        arp_names = list(ARPEGGIO_FORMS.keys())
        section_arps = {}
        for label in set(pattern):
            section_arps[label] = rng.choice(arp_names)
        # Theme (A) always uses block chords for recognizability
        section_arps['A'] = 'block'

        sections = {}
        sections['A'] = base_notes  # Theme

        # B: transposed +5 semitones (subdominant), inverted voicing
        b_notes = []
        for t, chord, dur, vel in base_notes:
            new_chord = []
            for note in chord:
                n = self.midi_lib._snap_to_scale(note + 5, root, scale_intervals)
                new_chord.append(clamp(n, 24, 108))
            # Invert: move lowest note up an octave
            if len(new_chord) > 1:
                new_chord[0] = clamp(new_chord[0] + 12, 24, 108)
                new_chord.sort()
            b_notes.append((t, new_chord, dur, vel))
        sections['B'] = b_notes

        # C: transposed -3 semitones (relative minor/major), different register
        c_notes = []
        for t, chord, dur, vel in base_notes:
            new_chord = []
            for note in chord:
                n = self.midi_lib._snap_to_scale(note - 3, root, scale_intervals)
                new_chord.append(clamp(n + 12, 24, 108))  # up an octave
            c_notes.append((t, new_chord, dur * rng.uniform(0.9, 1.1), vel))
        sections['C'] = c_notes

        # D: transposed +7 (dominant), wider voicing
        d_notes = []
        for t, chord, dur, vel in base_notes:
            new_chord = []
            for i, note in enumerate(chord):
                n = self.midi_lib._snap_to_scale(note + 7, root, scale_intervals)
                # Spread: alternate octaves for wider voicing
                shift = (-12 if i % 2 == 0 else 12) if len(chord) > 2 else 0
                new_chord.append(clamp(n + shift, 24, 108))
            new_chord.sort()
            d_notes.append((t, new_chord, dur, vel * rng.uniform(0.8, 1.0)))
        sections['D'] = d_notes

        # v7: Apply arpeggio forms to each section's notes
        result = []
        for label in pattern:
            section_notes = sections.get(label, base_notes)
            arp_name = section_arps.get(label, 'block')
            arp_fn = ARPEGGIO_FORMS.get(arp_name)

            if arp_fn is not None:
                # Convert block chords to arpeggiated sequences
                arpeggiated = []
                for t, chord, dur, vel in section_notes:
                    if len(chord) < 2:
                        arpeggiated.append((t, chord, dur, vel))
                        continue
                    arp_order = arp_fn(list(chord))
                    n_arp = len(arp_order)
                    arp_dur = dur / max(n_arp, 1)
                    for ai, note in enumerate(arp_order):
                        arp_t = t + ai * arp_dur
                        arpeggiated.append((arp_t, [note], arp_dur, vel))
                result.append((label, arpeggiated))
            else:
                result.append((label, section_notes))

        return result

    def _choose_gm_instruments(self, midi_info, n_voices, rng):
        """Choose GM instruments for FluidSynth rendering.

        v7: Uses weighted random pools to avoid piano/non-piano alternation.
        Selects from instrument families (strings, brass, woodwinds, keys, etc.)
        with weighted probabilities, ensuring genuine variety.
        Returns list of voice config dicts.
        """
        programs = midi_info.get('programs', set())
        orch_programs = list(GM_ORCHESTRA_INSTRUMENTS.keys())

        # Build a diverse pool from instrument families
        FAMILY_POOLS = {
            'strings':   [40, 41, 42, 43, 44, 45, 48],
            'brass':     [56, 57, 58, 60, 61],
            'woodwinds': [68, 69, 70, 71, 72, 73, 74, 75],
            'keys':      [0, 1, 2, 3, 4, 5, 6, 7, 8],
            'pitched_perc': [11, 14, 46],
        }
        families = list(FAMILY_POOLS.keys())

        # Randomize family selection order for this segment
        rng.shuffle(families)

        voices = []
        used_families = set()

        # Octave offsets and pans — shuffled for variety
        offsets_pool = [-12, 0, 0, 12]
        pans_pool = [-0.4, -0.15, 0.15, 0.4]

        for v in range(n_voices):
            # Pick a family we haven't used yet if possible
            available = [f for f in families if f not in used_families]
            if not available:
                available = families
            family = rng.choice(available)
            used_families.add(family)

            pool = FAMILY_POOLS[family]
            gm = rng.choice(pool)

            oct_offset = offsets_pool[v % len(offsets_pool)]
            pan = pans_pool[v % len(pans_pool)]

            # Chord size: 2-4 notes per chord
            chord_size = rng.randint(2, 4)

            # Color amount: subtle for bass, more for treble
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render a mood segment with chord rondo structure.

        v7 Pipeline:
        1. Compute tempo multiplier (1.5X-2.5X)
        2. Sample MIDI bars with simulation-seeded selection
        3. Expand notes → 2-4 note consonant chords
        4. Build rondo sections with varied arpeggio forms
        5. Select 2-4 voice instruments (diverse families)
        6. Each voice plays its own chord voicing simultaneously
        7. Apply chamber effects and anti-click processing
        8. Loop with long crossfade to fill mood duration
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        # 1. Tempo multiplier (v7: 1.5-2.5x)
        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        # 2. Sample MIDI bars with seeded selection
        loop_bars = rng.randint(4, 12)  # v7: up to 12 bars for longer phrases
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        # 3. Choose voice instruments (v7: diverse families, no alternation)
        n_voices = getattr(mood, 'n_voices', rng.randint(2, 4))
        voice_configs = self._choose_gm_instruments(midi_info, n_voices, rng)

        # 4. Expand each note into chords -- each voice builds its own chord
        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        # 5. Build rondo sections with varied arpeggio forms
        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        # Compute total rondo duration
        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # Gain per voice to prevent clipping (v7: adjusted for 2-4 voices)
        voice_gain = 0.35 / max(n_voices, 1)

        # 6. Render all voices across all rondo sections
        section_offset_sec = 0.0

        # Try FluidSynth for primary voice
        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            # v7: Each voice gets its own coloring instrument (persistent per section)
            voice_instruments = [rng.choice(self.instruments) for _ in voice_configs]

            for v_idx, vc in enumerate(voice_configs):
                oct_off = vc['octave_offset']
                pan = vc['pan']
                ca = vc['color_amount']
                v_chord_size = vc['chord_size']

                # Use FluidSynth rendered audio for first voice, first A section
                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * voice_gain
                            loop_right[pos] += fr[i] * voice_gain
                    continue

                color_instr = voice_instruments[v_idx]

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    # v7: Each voice builds its own chord voicing at its register
                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    # Snap to scale to ensure consonance
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    for note in voice_chord:
                        freq = mtof(note)
                        samps = self.factory.synthesize_colored_note(
                            color_instr, freq, dur_sec, vel, ca
                        )
                        # v7: Anti-click micro-fade on each note (2ms in, 2ms out)
                        click_guard = min(int(0.002 * SAMPLE_RATE), len(samps) // 4)
                        for ci in range(click_guard):
                            fade = ci / max(click_guard, 1)
                            samps[ci] *= fade
                            if len(samps) - 1 - ci >= 0:
                                samps[len(samps) - 1 - ci] *= fade

                        self._mix_mono(loop_left, loop_right, samps,
                                      offset, loop_samples, pan * voice_gain * 4)

            section_offset_sec += segment_duration

        # 7. Apply chamber effects
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # v7: DC offset removal to prevent low-frequency clicking
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        # v7: Gentle lowpass to remove harsh high-frequency artifacts
        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # 8. Loop with long crossfade to fill mood duration
        # v7: Longer crossfade (2-4 seconds) to eliminate click at loop boundaries
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    # v7: Use cosine crossfade for smoother loop joins
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right

    def _mix_mono(self, left, right, samples, offset, total_samples, pan):
        """Mix mono samples into stereo buffers with panning."""
        l_gain = math.cos((pan + 1) * math.pi / 4)
        r_gain = math.sin((pan + 1) * math.pi / 4)
        n = len(samples)
        end = min(offset + n, total_samples)
        start = max(offset, 0)
        for i in range(start, end):
            si = i - offset
            if 0 <= si < n:
                left[i] += samples[si] * l_gain * 0.25
                right[i] += samples[si] * r_gain * 0.25

    def _inject_tts_at(self, left, right, trans_start, total_samples,
                       mood, epoch_idx):
        """Inject TTS during a morph transition between mood segments."""
        rng = mood.rng
        phrases = self.tts.get_source_phrases(rng, count=2)
        speech_text = '. '.join(phrases) + '. In the beginning radio.'

        voice_seed = rng.randint(0, 100)
        tts_samples, tts_sr = self.tts.generate_speech(
            speech_text, voice_seed, epoch_idx
        )
        if tts_samples is None:
            return

        if tts_sr != SAMPLE_RATE:
            tts_samples = self._resample(tts_samples, tts_sr, SAMPLE_RATE)

        peak = max(abs(s) for s in tts_samples) if tts_samples else 1.0
        if peak > 0:
            tts_samples = [s / peak * 0.65 for s in tts_samples]

        # Place TTS centered on the transition point
        tts_start = max(0, trans_start - len(tts_samples) // 4)

        # Duck music around speech
        duck_start = max(0, tts_start - int(0.5 * SAMPLE_RATE))
        duck_end = min(total_samples, tts_start + len(tts_samples) + int(0.5 * SAMPLE_RATE))
        duck_ramp = int(0.3 * SAMPLE_RATE)

        for i in range(duck_start, duck_end):
            if i < 0 or i >= total_samples:
                continue
            if i < duck_start + duck_ramp:
                duck = 1.0 - 0.6 * ((i - duck_start) / duck_ramp)
            elif i > duck_end - duck_ramp:
                duck = 1.0 - 0.6 * ((duck_end - i) / duck_ramp)
            else:
                duck = 0.4
            left[i] *= duck
            right[i] *= duck

        for i in range(len(tts_samples)):
            si = tts_start + i
            if 0 <= si < total_samples:
                left[si] += tts_samples[i] * 0.5
                right[si] += tts_samples[i] * 0.5

    def _inject_tts_into_buf(self, buf_left, buf_right, buf_global_start,
                             trans_start, total_samples, mood, epoch_idx):
        """Inject TTS into the rolling buffer during streaming render."""
        rng = mood.rng
        phrases = self.tts.get_source_phrases(rng, count=2)
        speech_text = '. '.join(phrases) + '. In the beginning radio.'

        voice_seed = rng.randint(0, 100)
        tts_samples, tts_sr = self.tts.generate_speech(
            speech_text, voice_seed, epoch_idx
        )
        if tts_samples is None:
            return

        if tts_sr != SAMPLE_RATE:
            tts_samples = self._resample(tts_samples, tts_sr, SAMPLE_RATE)

        peak = max(abs(s) for s in tts_samples) if tts_samples else 1.0
        if peak > 0:
            tts_samples = [s / peak * 0.65 for s in tts_samples]

        tts_start = max(0, trans_start - len(tts_samples) // 4)
        duck_start = max(0, tts_start - int(0.5 * SAMPLE_RATE))
        duck_end = min(total_samples, tts_start + len(tts_samples) + int(0.5 * SAMPLE_RATE))
        duck_ramp = int(0.3 * SAMPLE_RATE)

        for i in range(duck_start, duck_end):
            buf_i = i - buf_global_start
            if 0 <= buf_i < len(buf_left):
                if i < duck_start + duck_ramp:
                    duck = 1.0 - 0.6 * ((i - duck_start) / duck_ramp)
                elif i > duck_end - duck_ramp:
                    duck = 1.0 - 0.6 * ((duck_end - i) / duck_ramp)
                else:
                    duck = 0.4
                buf_left[buf_i] *= duck
                buf_right[buf_i] *= duck

        for i in range(len(tts_samples)):
            global_i = tts_start + i
            buf_i = global_i - buf_global_start
            if 0 <= buf_i < len(buf_left):
                buf_left[buf_i] += tts_samples[i] * 0.5
                buf_right[buf_i] += tts_samples[i] * 0.5

    def _resample(self, samples, from_sr, to_sr):
        """Simple linear interpolation resampling."""
        if from_sr == to_sr:
            return samples
        ratio = to_sr / from_sr
        new_len = int(len(samples) * ratio)
        result = [0.0] * new_len
        for i in range(new_len):
            src_pos = i / ratio
            idx = int(src_pos)
            frac = src_pos - idx
            if idx + 1 < len(samples):
                result[i] = samples[idx] * (1 - frac) + samples[idx + 1] * frac
            elif idx < len(samples):
                result[i] = samples[idx]
        return result


# ---------------------------------------------------------------------------
# RENDER TO FILE -- Write the output as WAV/MP3
# ---------------------------------------------------------------------------
def render_to_wav(left, right, path, sample_rate=SAMPLE_RATE):
    """Write stereo float samples to 16-bit WAV file."""
    n = len(left)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        data = bytearray(n * 4)
        for i in range(n):
            l_val = int(math.tanh(left[i]) * 32767)
            r_val = int(math.tanh(right[i]) * 32767)
            struct.pack_into('<hh', data, i * 4,
                           max(-32767, min(32767, l_val)),
                           max(-32767, min(32767, r_val)))
        wf.writeframes(bytes(data))


def wav_to_mp3(wav_path, mp3_path, bitrate='192k'):
    """Convert WAV to MP3 using ffmpeg."""
    subprocess.run(
        ['ffmpeg', '-y', '-i', wav_path,
         '-codec:a', 'libmp3lame', '-b:a', bitrate,
         '-ar', str(SAMPLE_RATE), mp3_path],
        capture_output=True, timeout=120
    )


def generate_radio_mp3(output_path, duration=1800.0, seed=42):
    """Generate the radio MP3 file.

    This is the main entry point for producing the 30-minute cosmic
    radio station MP3 with all features enabled.
    """
    import tempfile

    print(f"[RadioEngine] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngine(seed=seed, total_duration=duration)

    print(f"[RadioEngine] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngine] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngine] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngine] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)
    print(f"[RadioEngine] {n_segments} mood segments (avg {avg_dur:.0f}s, multiples of 42s)")

    print(f"[RadioEngine] Rendering audio...")
    t0 = _time.time()

    # Import simulator for real simulation data
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        # Run simulation to collect states at segment boundaries
        sim_states = []
        total_ticks = int(duration * 50)  # 50 ticks/sec
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                print(f"  Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    # Use streaming renderer for long durations (>10 min) to avoid OOM
    use_streaming = duration > 660

    if use_streaming:
        print(f"[RadioEngine] Using streaming renderer (low memory)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            print(f"[RadioEngine] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[RadioEngine] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngine] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[RadioEngine] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        print(f"[RadioEngine] Rendered {len(left)/SAMPLE_RATE:.1f}s of audio in {t1-t0:.1f}s")

        # Write to WAV first, then convert to MP3
        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[RadioEngine] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[RadioEngine] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngine] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[RadioEngine] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngine] File size: {file_size/1048576:.1f} MB")
    return output_path


# ---------------------------------------------------------------------------
# V8 TIME SIGNATURE CLASSIFICATION
# ---------------------------------------------------------------------------
# Simple: beats divide into 2 (top number is 2, 3, or 4; bottom is note value)
SIMPLE_TIME_SIGS = ['2/2', '2/4', '3/4', '4/4', '3/8', '3/2']
# Compound: beats divide into 3 (top number is 6, 9, or 12)
COMPOUND_TIME_SIGS = ['6/4', '6/8', '9/8', '12/8']
# Complex/mixed/additive/irrational: irregular groupings
COMPLEX_TIME_SIGS = ['5/4', '5/8', '7/4', '7/8', '11/8', '3+3+2/8', '2+2+3/8']


# ---------------------------------------------------------------------------
# V8 NOTE SMOOTHING FILTER -- applied after synthesis, before arrangement
# ---------------------------------------------------------------------------
class NoteSmoother:
    """Inline post-processing for individual note/chord samples.

    Applied after synthesis (note -> coloring/imprinting/bending) but
    before arrangement into chord progressions/runs/arpeggios.
    Produces a softer, more fluid texture without excessive vibrato.
    Uses numpy when available for ~10x speedup.
    """

    def __init__(self):
        pass

    def smooth_note(self, samples, freq=440.0):
        """Apply gentle smoothing to a single synthesized note.

        Pipeline:
        1. Two-pole lowpass to soften transients (adaptive cutoff)
        2. Highpass at 35 Hz to remove subsonic rumble
        3. Gentle saturation warmth

        Args:
            samples: List of float audio samples.
            freq: Fundamental frequency in Hz (for adaptive filtering).

        Returns:
            Smoothed samples list.
        """
        n = len(samples)
        if n < 4:
            return samples

        if HAS_NUMPY:
            return self._smooth_numpy(samples, freq, n)
        return self._smooth_pure(samples, freq, n)

    def _smooth_numpy(self, samples, freq, n):
        """Numpy-accelerated smoothing using convolution (fully vectorized)."""
        arr = np.array(samples, dtype=np.float64)

        # 1. Moving average smoothing (vectorized convolution)
        # Kernel size adapts to frequency: low notes get wider smoothing
        kernel_size = max(3, min(31, int(SAMPLE_RATE / max(freq * 4, 100))))
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel = np.ones(kernel_size) / kernel_size
        # Apply twice for gentler rolloff (approximates 2-pole)
        smoothed = np.convolve(arr, kernel, mode='same')
        smoothed = np.convolve(smoothed, kernel, mode='same')

        # 2. Highpass: subtract very-low-frequency trend
        hp_kernel_size = int(SAMPLE_RATE / 30)  # ~30 Hz
        if hp_kernel_size % 2 == 0:
            hp_kernel_size += 1
        hp_kernel_size = min(hp_kernel_size, n // 2)
        if hp_kernel_size > 3:
            hp_kernel = np.ones(hp_kernel_size) / hp_kernel_size
            bass = np.convolve(smoothed, hp_kernel, mode='same')
            smoothed = smoothed - bass + np.mean(smoothed)

        # 3. Gentle warmth saturation
        mask = np.abs(smoothed) > 0.6
        if mask.any():
            sign = np.sign(smoothed[mask])
            excess = np.abs(smoothed[mask]) - 0.6
            smoothed[mask] = sign * (0.6 + 0.4 * np.tanh(excess * 2.5))

        return smoothed.tolist()

    def _smooth_pure(self, samples, freq, n):
        """Pure Python fallback (simplified single-pass for speed)."""
        out = list(samples)

        # Combined lowpass + highpass in single pass
        cutoff = min(14000.0, max(2000.0, freq * 8))
        lp_alpha = min(0.99, TWO_PI * cutoff * INV_SR)
        hp_alpha = max(0.001, 1.0 - TWO_PI * 35.0 * INV_SR)
        lp_state = 0.0
        hp_state = 0.0
        hp_prev = 0.0
        for i in range(n):
            # Lowpass
            lp_state += lp_alpha * (out[i] - lp_state)
            # Highpass on the lowpassed signal
            hp_state = hp_alpha * (hp_state + lp_state - hp_prev)
            hp_prev = lp_state
            out[i] = hp_state

        return out

    def smooth_chord(self, chord_samples_list, freqs):
        """Smooth each note in a chord, preserving relative timing.

        Args:
            chord_samples_list: List of (samples_list) for each note.
            freqs: List of frequencies corresponding to each note.

        Returns:
            List of smoothed sample lists.
        """
        result = []
        for samps, freq in zip(chord_samples_list, freqs):
            result.append(self.smooth_note(samps, freq))
        return result


# ---------------------------------------------------------------------------
# V8 SPECTRAL ANTI-HISS FILTER
# ---------------------------------------------------------------------------
class AntiHissFilter:
    """Reduces hissing/static from synthesis artifacts.

    Targets the 4-16 kHz range where digital synthesis artifacts
    (aliasing, quantization noise, FM sidebands) accumulate.
    Uses numpy when available for fast processing.
    """

    def __init__(self):
        pass

    def apply(self, samples):
        """Apply anti-hiss filtering to a buffer.

        Strategy: cascaded lowpass to tame high-frequency hiss.
        - Pass 1: gentle roll-off above 10 kHz (blend 70/30)
        - Pass 2: steeper cut above 14 kHz
        - DC removal
        """
        n = len(samples)
        if n < 2:
            return samples

        if HAS_NUMPY:
            return self._apply_numpy(samples, n)

        out = list(samples)
        alpha1 = min(0.99, TWO_PI * 10000.0 * INV_SR)
        alpha2 = min(0.99, TWO_PI * 14000.0 * INV_SR)
        s1 = 0.0
        s2 = 0.0
        for i in range(n):
            s1 += alpha1 * (out[i] - s1)
            mixed = s1 * 0.7 + out[i] * 0.3
            s2 += alpha2 * (mixed - s2)
            out[i] = s2
        # DC removal
        dc = sum(out) / n
        if abs(dc) > 0.0005:
            for i in range(n):
                out[i] -= dc
        return out

    def _apply_numpy(self, samples, n):
        """Numpy-accelerated anti-hiss filter using convolution."""
        arr = np.array(samples, dtype=np.float64)

        # Moving average lowpass (kernel size ~4 samples ≈ 10 kHz at 44.1k)
        k1 = max(3, int(SAMPLE_RATE / 10000))
        if k1 % 2 == 0:
            k1 += 1
        kernel1 = np.ones(k1) / k1
        lp1 = np.convolve(arr, kernel1, mode='same')
        # Blend: preserve some original sparkle
        mixed = lp1 * 0.7 + arr * 0.3

        # Second pass with slightly wider kernel (~3 samples ≈ 14 kHz)
        k2 = max(3, int(SAMPLE_RATE / 14000))
        if k2 % 2 == 0:
            k2 += 1
        kernel2 = np.ones(k2) / k2
        result = np.convolve(mixed, kernel2, mode='same')

        # DC removal
        dc = np.mean(result)
        if abs(dc) > 0.0005:
            result -= dc
        return result.tolist()

    def apply_stereo(self, left, right):
        """Apply anti-hiss filtering to stereo pair."""
        return self.apply(left), self.apply(right)


# ---------------------------------------------------------------------------
# V8 SUBSONIC FILTER
# ---------------------------------------------------------------------------
class SubsonicFilter:
    """Removes subsonic content that causes headphone pressure sensation.

    Two-pole highpass at 30 Hz. Removes content below ~30 Hz that's
    felt but not heard, causing discomfort especially on headphones.
    """

    def __init__(self, cutoff_hz=30.0):
        self.cutoff = cutoff_hz

    def apply(self, samples):
        """Apply 2-pole highpass to remove subsonic content."""
        n = len(samples)
        if n < 4:
            return samples

        alpha = max(0.001, 1.0 - TWO_PI * self.cutoff * INV_SR)

        if HAS_NUMPY:
            arr = np.array(samples, dtype=np.float64)
            for _pass in range(2):
                out = np.empty(n, dtype=np.float64)
                out[0] = arr[0] * alpha
                for i in range(1, n):
                    out[i] = alpha * (out[i-1] + arr[i] - arr[i-1])
                arr = out
            return arr.tolist()

        out = list(samples)
        for _pass in range(2):
            state = 0.0
            prev = 0.0
            for i in range(n):
                state = alpha * (state + out[i] - prev)
                prev = out[i]
                out[i] = state
        return out

    def apply_stereo(self, left, right):
        """Apply subsonic filtering to stereo pair."""
        return self.apply(left), self.apply(right)


# ---------------------------------------------------------------------------
# V8 NOTE DURATION QUANTIZER
# ---------------------------------------------------------------------------
class NoteQuantizer:
    """Quantizes note durations to fit within bars of a given time signature.

    Compresses or expands note durations so they align with beat subdivisions,
    while preserving the sequence ordering and relative feel.
    """

    def __init__(self):
        pass

    def quantize_to_bar(self, notes, bar_duration_sec, beats_per_bar,
                        beat_unit=4):
        """Quantize note durations to align with bar structure.

        Allowed durations are subdivisions of the beat:
        whole, half, quarter, eighth, sixteenth, dotted variants.

        Args:
            notes: List of (t_sec, midi_note, dur_sec, velocity).
            bar_duration_sec: Duration of one bar in seconds.
            beats_per_bar: Number of beats per bar.
            beat_unit: Denominator of time signature.

        Returns:
            Quantized notes list with durations snapped to beat grid.
        """
        if not notes or bar_duration_sec <= 0:
            return notes

        beat_dur = bar_duration_sec / max(beats_per_bar, 1)

        # Allowed note durations as fractions of a beat
        grid_fractions = [
            4.0,    # whole note (4 beats)
            3.0,    # dotted half
            2.0,    # half note
            1.5,    # dotted quarter
            1.0,    # quarter note
            0.75,   # dotted eighth
            0.5,    # eighth note
            0.375,  # dotted sixteenth
            0.25,   # sixteenth note
            0.125,  # thirty-second note
        ]
        grid_secs = [f * beat_dur for f in grid_fractions]

        result = []
        cumulative_time = 0.0

        for _t_sec, midi_note, dur_sec, velocity in notes:
            # Snap duration to nearest grid value
            best_dur = dur_sec
            best_dist = float('inf')
            for gs in grid_secs:
                dist = abs(dur_sec - gs)
                if dist < best_dist:
                    best_dist = dist
                    best_dur = gs

            # Snap onset to beat grid (quantize to nearest 16th)
            sixteenth = beat_dur * 0.25
            if sixteenth > 0:
                snapped_t = round(cumulative_time / sixteenth) * sixteenth
            else:
                snapped_t = cumulative_time

            result.append((snapped_t, midi_note, best_dur, velocity))
            cumulative_time = snapped_t + best_dur

        return result

    def fit_notes_to_bars(self, notes, n_bars, bar_duration_sec, beats_per_bar):
        """Fit a sequence of notes exactly into n_bars.

        Scales note timings proportionally to fill the total bar span,
        then quantizes to the beat grid.

        Args:
            notes: List of (t_sec, midi_note, dur_sec, velocity).
            n_bars: Number of bars to fill.
            bar_duration_sec: Duration of one bar.
            beats_per_bar: Beats per bar.

        Returns:
            Fitted and quantized notes.
        """
        if not notes or n_bars <= 0 or bar_duration_sec <= 0:
            return notes

        total_target = n_bars * bar_duration_sec

        # Find current total span
        if len(notes) > 1:
            current_span = notes[-1][0] + notes[-1][2] - notes[0][0]
        else:
            current_span = notes[0][2]

        if current_span <= 0:
            current_span = 1.0

        scale = total_target / current_span

        # Scale all note times and durations
        scaled = []
        for t_sec, midi_note, dur_sec, velocity in notes:
            new_t = (t_sec - notes[0][0]) * scale
            new_dur = dur_sec * scale
            scaled.append((new_t, midi_note, new_dur, velocity))

        # Now quantize to the bar grid
        return self.quantize_to_bar(scaled, bar_duration_sec, beats_per_bar)


# ---------------------------------------------------------------------------
# V8 RADIO ENGINE -- Enhanced orchestral version
# ---------------------------------------------------------------------------
class RadioEngineV8(RadioEngine):
    """In The Beginning Radio v8 -- Enhanced orchestral cosmic music station.

    Enhancements over v7:
    - Simultaneous multi-instrument orchestral layering (like orchestra sections)
    - Occasional solo instrument alternation (20-30% of sections)
    - Anti-hiss spectral filtering
    - Subsonic frequency removal (30 Hz highpass)
    - Smoother note textures via inline post-processing
    - 70% simple time signatures; compound/complex guaranteed in 10-min windows
    - Note duration quantization to fit bar structure
    """

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        self.note_smoother = NoteSmoother()
        self.anti_hiss = AntiHissFilter()
        self.subsonic_filter = SubsonicFilter(cutoff_hz=30.0)
        self.quantizer = NoteQuantizer()

        # Re-plan segments with v8 time signature rules
        self.segments = self._plan_segments_v8()

    def _plan_segments_v8(self):
        """Plan segments with 70% simple time signatures and guaranteed
        compound/complex in every 10-minute window."""
        duration_multiples = [42.0, 84.0, 84.0, 126.0, 126.0, 168.0, 210.0]
        segments = []
        t = 0.0
        idx = 0
        while t < self.total_duration:
            seg_rng = random.Random(self.seed + idx * 31337)
            duration = seg_rng.choice(duration_multiples)
            if t + duration > self.total_duration:
                duration = self.total_duration - t
                if duration < 1.0:
                    break
            segments.append({'start': t, 'duration': duration, 'idx': idx})
            t += duration
            idx += 1
        if not segments and self.total_duration > 0:
            segments.append({'start': 0.0, 'duration': self.total_duration, 'idx': 0})

        # Assign time signatures: 70% simple, rest compound/complex
        # Guarantee at least one compound/complex per 10-minute window
        n_segs = len(segments)
        ts_assignments = [None] * n_segs
        rng = random.Random(self.seed + 999)

        for i in range(n_segs):
            if rng.random() < 0.80:
                ts_assignments[i] = rng.choice(SIMPLE_TIME_SIGS)
            else:
                # 60% compound, 40% complex for non-simple
                if rng.random() < 0.6:
                    ts_assignments[i] = rng.choice(COMPOUND_TIME_SIGS)
                else:
                    ts_assignments[i] = rng.choice(COMPLEX_TIME_SIGS)

        # Enforce: every 10-minute window must have at least one non-simple
        window_sec = 600.0
        n_windows = max(1, int(math.ceil(self.total_duration / window_sec)))
        for w in range(n_windows):
            w_start = w * window_sec
            w_end = min((w + 1) * window_sec, self.total_duration)
            window_indices = [i for i in range(n_segs)
                              if segments[i]['start'] >= w_start
                              and segments[i]['start'] < w_end]
            has_nonstandard = any(
                ts_assignments[i] in COMPOUND_TIME_SIGS + COMPLEX_TIME_SIGS
                for i in window_indices
            )
            if not has_nonstandard and window_indices:
                # Force one segment to use compound or complex
                pick = rng.choice(window_indices)
                if rng.random() < 0.5:
                    ts_assignments[pick] = rng.choice(COMPOUND_TIME_SIGS)
                else:
                    ts_assignments[pick] = rng.choice(COMPLEX_TIME_SIGS)

        for i in range(n_segs):
            segments[i]['time_sig_override'] = ts_assignments[i]

        return segments

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render a mood segment with v8 enhancements.

        v8 Pipeline:
        1. Compute tempo multiplier
        2. Sample MIDI bars with simulation-seeded selection
        3. Apply note duration quantization to fit bar structure
        4. Expand notes -> consonant chords
        5. Apply note-level smoothing (post-synthesis, pre-arrangement)
        6. Build rondo sections with varied arpeggio forms
        7. SIMULTANEOUS multi-instrument orchestral layering
           (with occasional solo alternation ~25% of sections)
        8. Anti-hiss filtering + subsonic removal
        9. Chamber effects and anti-click processing
        10. Loop with crossfade to fill mood duration
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        # 1. Tempo multiplier
        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        # Compute bar duration for quantization
        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = beats_per_bar * beat_dur * quarter_per_beat

        # 2. Sample MIDI bars
        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        # 3. Quantize note durations to fit bar structure
        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )

        # 4. Choose voices -- more voices for orchestral layering
        n_voices = getattr(mood, 'n_voices', rng.randint(2, 4))
        # v8: Increase to 3-5 voices for richer layering
        n_voices = clamp(n_voices, 2, 4)
        voice_configs = self._choose_gm_instruments(midi_info, n_voices, rng)

        # Assign octave offsets for consonant simultaneous play
        # Each voice gets a distinct register offset
        register_offsets = [-12, 0, 0, 12, 24]
        for v_idx, vc in enumerate(voice_configs):
            vc['octave_offset'] = register_offsets[v_idx % len(register_offsets)]

        # 5. Expand notes into chords
        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        # 6. Build rondo sections
        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        # Compute total rondo duration
        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # Gain per voice
        voice_gain = 0.30 / max(n_voices, 1)

        # 7. Orchestral rendering: simultaneous + occasional solo
        # Decide per-section: ~75% simultaneous (all voices), ~25% solo
        section_offset_sec = 0.0

        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            # v8: Decide simultaneous vs solo for this section
            is_solo_section = rng.random() < 0.25
            if is_solo_section:
                # Solo: pick one voice to play
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                # Simultaneous: all voices play (orchestral)
                active_voices = list(range(n_voices))

            voice_instruments = [rng.choice(self.instruments) for _ in voice_configs]

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc['pan']
                ca = vc['color_amount']
                v_chord_size = vc['chord_size']

                # Solo voice gets boosted gain
                v_gain = voice_gain * (2.0 if is_solo_section else 1.0)

                # FluidSynth for first voice, first A section
                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * v_gain
                            loop_right[pos] += fr[i] * v_gain
                    continue

                color_instr = voice_instruments[v_idx]

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    # Each voice builds its own chord voicing at its register
                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    # Synthesize each chord note and mix into buffer
                    for note in voice_chord:
                        freq = mtof(note)
                        # v8: use numpy-accelerated synthesis
                        if HAS_NUMPY:
                            samps_arr = _synth_colored_note_np(
                                freq, dur_sec, color_instr, vel, ca
                            )
                            # Anti-click micro-fade
                            cg = min(int(0.002 * SAMPLE_RATE), len(samps_arr) // 4)
                            if cg > 0:
                                fade_in = np.linspace(0, 1, cg)
                                samps_arr[:cg] *= fade_in
                                samps_arr[-cg:] *= fade_in[::-1]
                            samps = samps_arr.tolist()
                        else:
                            samps = self.factory.synthesize_colored_note(
                                color_instr, freq, dur_sec, vel, ca
                            )
                            cg = min(int(0.002 * SAMPLE_RATE), len(samps) // 4)
                            for ci in range(cg):
                                fade = ci / max(cg, 1)
                                samps[ci] *= fade
                                if len(samps) - 1 - ci >= 0:
                                    samps[len(samps) - 1 - ci] *= fade

                        self._mix_mono(loop_left, loop_right, samps,
                                       offset, loop_samples, pan * v_gain * 4)

            section_offset_sec += segment_duration

        # 8. Chamber effects (anti-hiss/subsonic applied at master level)
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        # Gentle lowpass for remaining harsh artifacts
        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # Loop with crossfade to fill mood duration
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right

    def _patch_mood_init(self):
        """Create a patched MoodSegment.__init__ that applies v8 time sig overrides."""
        orig_create_mood = MoodSegment.__init__
        segments = self.segments

        def patched_mood_init(mood_self, segment_idx, epoch, epoch_idx,
                              sim_state, rng_seed):
            orig_create_mood(mood_self, segment_idx, epoch, epoch_idx,
                             sim_state, rng_seed)
            for seg in segments:
                if seg['idx'] == segment_idx and 'time_sig_override' in seg:
                    ts_key = seg['time_sig_override']
                    mood_self.time_sig = ts_key
                    ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES['4/4'])
                    mood_self.beats_per_bar = ts_info['beats']
                    mood_self._v8_time_sig = ts_key
                    break

        return orig_create_mood, patched_mood_init

    def render(self, sim_states=None):
        """Render with v8 time sig overrides + master chain."""
        orig, patched = self._patch_mood_init()
        MoodSegment.__init__ = patched
        try:
            left, right = super().render(sim_states)
        finally:
            MoodSegment.__init__ = orig

        # v8 master chain: additional anti-hiss and subsonic filtering
        left, right = self.anti_hiss.apply_stereo(left, right)
        left, right = self.subsonic_filter.apply_stereo(left, right)

        return left, right

    def render_streaming(self, wav_file, sim_states=None):
        """Override to apply v8 time signature overrides to mood segments."""
        orig, patched = self._patch_mood_init()
        MoodSegment.__init__ = patched
        try:
            result = super().render_streaming(wav_file, sim_states)
        finally:
            MoodSegment.__init__ = orig

        return result


# ---------------------------------------------------------------------------
# V9 RADIO ENGINE -- Expanded instrument set with density-aware tempo
# ---------------------------------------------------------------------------
class RadioEngineV9(RadioEngineV8):
    """In The Beginning Radio v9 -- Expanded instrument palette + density-aware tempo.

    Enhancements over v8:
    - ~50 new GM instruments across rock, electronic, world, and symphonic families
    - 15 instrument family pools (up from 5) for much broader timbral variety
    - Density-aware tempo: 1.1x-2.1x range, capped at 1.6x during high-density
      simulation epochs (many particles/atoms/molecules) for breathing room
    - Family variety enforcement: all major family groups (symphonic, rock,
      electronic, world) guaranteed to appear across a 30-minute piece
    - All v8 features preserved (orchestral layering, anti-hiss, subsonic
      removal, note smoothing, time signature control, note quantization)
    """

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        # Track which family groups have been used across the full render
        self._used_family_groups = set()
        # Family groups for variety enforcement
        self._family_groups = {
            'symphonic': {'strings', 'brass', 'woodwinds', 'sax', 'choir',
                          'symphonic_ext'},
            'rock': {'rock_guitar', 'rock_bass'},
            'electronic': {'synth_lead', 'synth_pad', 'synth_fx'},
            'world': {'world'},
            'classical': {'keys', 'pitched_perc', 'mallets'},
        }
        self._segment_count = 0

    def _compute_tempo_multiplier(self, sim_state):
        """Density-aware tempo multiplier: 1.1x-2.1x range.

        v9: lower and wider range than v8's 1.5x-2.5x. During high-density
        simulation epochs (many particles, atoms, molecules), tempo is capped
        at 1.6x to give the expanded instrument set breathing room and reduce
        cacophony. During sparse epochs, tempo can reach up to ~1.8x.
        """
        if not sim_state:
            return 1.6  # neutral default

        # Base multiplier from state hash (same technique as v7/v8)
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 1.0 * (int(h, 16) / 0xFFFFFFFF)  # 1.1-2.1 range

        # Density-aware capping
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5

        if density > 100:
            # High density: cap tempo for breathing room
            base = min(base, 1.6)
        elif density > 50:
            # Medium density: mild cap
            base = min(base, 1.8)
        # Low density: no cap, full 1.1-2.1 range allowed

        return base

    def _choose_gm_instruments_v9(self, midi_info, n_voices, rng):
        """Choose GM instruments from expanded v9 family pools.

        Uses all 15 family pools with variety enforcement: tracks which
        family groups have been used across the full render, and biases
        selection toward under-represented groups past the halfway point.
        """
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()

        # Octave offsets and pans
        offsets_pool = [-12, 0, 0, 12]
        pans_pool = [-0.4, -0.15, 0.15, 0.4]

        # Variety enforcement: past halfway, bias toward unused groups
        self._segment_count += 1
        n_total_segments = len(self.segments) if hasattr(self, 'segments') else 15
        past_halfway = self._segment_count > n_total_segments // 2

        # Find under-represented family groups
        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            # Prefer under-represented families if past halfway
            if underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
                underrepresented = [f for f in underrepresented if f != family]
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)

            used_families.add(family)

            # Track family group usage
            for group_name, group_families in self._family_groups.items():
                if family in group_families:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)

            oct_offset = offsets_pool[v % len(offsets_pool)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render a mood segment with v9 expanded instruments.

        Same 10-step pipeline as v8, but uses v9 instrument selection
        with expanded family pools and variety enforcement.
        """
        # Temporarily override _choose_gm_instruments to use v9 version
        orig_choose = self._choose_gm_instruments
        self._choose_gm_instruments = self._choose_gm_instruments_v9
        try:
            result = super()._render_segment(mood, kits, n_samples, sim_state)
        finally:
            self._choose_gm_instruments = orig_choose
        return result


# ---------------------------------------------------------------------------
# GM TIMBRE PROFILES -- Distinct synthesis parameters per instrument family
# ---------------------------------------------------------------------------
# Each profile maps a GM program range to specific ADSR, harmonic structure,
# and brightness settings. This prevents all instruments sounding "organ-y"
# by giving each family a distinct sonic character.
GM_TIMBRE_PROFILES = {
    # Piano (0-7): percussive attack, quick decay, bell-like harmonics
    'piano':      {'attack': 0.003, 'decay': 0.15, 'sustain': 0.3, 'release': 0.25,
                   'harmonics': [(1, 1.0), (2, 0.6), (3, 0.2), (4, 0.15), (5, 0.08),
                                 (7, 0.03)], 'brightness': 0.7, 'vib_depth': 0.0001},
    # Chromatic percussion (8-15): very percussive, short notes
    'mallets':    {'attack': 0.001, 'decay': 0.08, 'sustain': 0.1, 'release': 0.15,
                   'harmonics': [(1, 1.0), (2.76, 0.5), (5.4, 0.25), (8.93, 0.12)],
                   'brightness': 0.9, 'vib_depth': 0.0},
    # Organ (16-23): sustained, many harmonics, classic drawbar tone
    'organ':      {'attack': 0.02, 'decay': 0.02, 'sustain': 0.85, 'release': 0.08,
                   'harmonics': [(1, 1.0), (2, 0.8), (3, 0.6), (4, 0.4), (5, 0.3),
                                 (6, 0.2), (8, 0.15)], 'brightness': 0.5, 'vib_depth': 0.003},
    # Guitar (24-31): plucked, fast attack, moderate decay
    'guitar':     {'attack': 0.002, 'decay': 0.2, 'sustain': 0.2, 'release': 0.3,
                   'harmonics': [(1, 1.0), (2, 0.5), (3, 0.35), (4, 0.2), (5, 0.15),
                                 (6, 0.08)], 'brightness': 0.65, 'vib_depth': 0.0005},
    # Bass (32-39): deep, warm, strong fundamental
    'bass':       {'attack': 0.005, 'decay': 0.12, 'sustain': 0.5, 'release': 0.15,
                   'harmonics': [(1, 1.0), (2, 0.4), (3, 0.15), (4, 0.05)],
                   'brightness': 0.3, 'vib_depth': 0.0002},
    # Strings (40-47): slow attack, rich sustained harmonics
    'strings':    {'attack': 0.08, 'decay': 0.1, 'sustain': 0.75, 'release': 0.2,
                   'harmonics': [(1, 1.0), (2, 0.7), (3, 0.5), (4, 0.25), (5, 0.15),
                                 (6, 0.08), (7, 0.04)], 'brightness': 0.45, 'vib_depth': 0.004},
    # Ensemble (48-55): lush, blended, wide
    'ensemble':   {'attack': 0.1, 'decay': 0.15, 'sustain': 0.7, 'release': 0.25,
                   'harmonics': [(1, 1.0), (2, 0.65), (3, 0.45), (4, 0.3), (5, 0.18),
                                 (6, 0.1)], 'brightness': 0.4, 'vib_depth': 0.005},
    # Brass (56-63): bold, medium attack, strong mid harmonics
    'brass':      {'attack': 0.03, 'decay': 0.08, 'sustain': 0.7, 'release': 0.12,
                   'harmonics': [(1, 1.0), (2, 0.9), (3, 0.75), (4, 0.55), (5, 0.35),
                                 (6, 0.2), (7, 0.12), (8, 0.06)], 'brightness': 0.8,
                   'vib_depth': 0.002},
    # Reed (64-71): warm, slightly nasal, moderate brightness
    'reed':       {'attack': 0.025, 'decay': 0.06, 'sustain': 0.65, 'release': 0.1,
                   'harmonics': [(1, 1.0), (2, 0.3), (3, 0.65), (4, 0.15), (5, 0.4),
                                 (6, 0.08), (7, 0.2)], 'brightness': 0.55, 'vib_depth': 0.003},
    # Pipe (72-79): pure, hollow, few harmonics
    'pipe':       {'attack': 0.04, 'decay': 0.05, 'sustain': 0.7, 'release': 0.15,
                   'harmonics': [(1, 1.0), (2, 0.1), (3, 0.3), (5, 0.08)],
                   'brightness': 0.35, 'vib_depth': 0.002},
    # Synth lead (80-87): instant attack, bright, sawtooth-like
    'synth_lead': {'attack': 0.001, 'decay': 0.1, 'sustain': 0.6, 'release': 0.08,
                   'harmonics': [(1, 1.0), (2, 0.5), (3, 0.33), (4, 0.25), (5, 0.2),
                                 (6, 0.17), (7, 0.14), (8, 0.12)], 'brightness': 0.85,
                   'vib_depth': 0.001},
    # Synth pad (88-95): very slow attack, deep sustain, atmospheric
    'synth_pad':  {'attack': 0.2, 'decay': 0.3, 'sustain': 0.8, 'release': 0.5,
                   'harmonics': [(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.1), (5, 0.05)],
                   'brightness': 0.25, 'vib_depth': 0.006},
    # Synth FX (96-103): varied experimental sounds
    'synth_fx':   {'attack': 0.01, 'decay': 0.2, 'sustain': 0.4, 'release': 0.3,
                   'harmonics': [(1, 1.0), (1.41, 0.4), (2.23, 0.3), (3.17, 0.2),
                                 (4.59, 0.1)], 'brightness': 0.6, 'vib_depth': 0.004},
    # Ethnic/World (104-111): plucked/struck, bright attack
    'world':      {'attack': 0.004, 'decay': 0.18, 'sustain': 0.25, 'release': 0.2,
                   'harmonics': [(1, 1.0), (2, 0.55), (3, 0.4), (4, 0.3), (5, 0.15),
                                 (6.2, 0.08)], 'brightness': 0.7, 'vib_depth': 0.002},
    # Percussive (112-119): very short, impact-like
    'percussive': {'attack': 0.001, 'decay': 0.05, 'sustain': 0.05, 'release': 0.1,
                   'harmonics': [(1, 1.0), (2.3, 0.6), (4.1, 0.3), (6.7, 0.15)],
                   'brightness': 0.75, 'vib_depth': 0.0},
}


def _gm_program_to_timbre(gm_program):
    """Map a GM program number (0-127) to a timbre profile name.

    Returns the profile key from GM_TIMBRE_PROFILES.
    """
    if gm_program <= 7:
        return 'piano'
    elif gm_program <= 15:
        return 'mallets'
    elif gm_program <= 23:
        return 'organ'
    elif gm_program <= 31:
        return 'guitar'
    elif gm_program <= 39:
        return 'bass'
    elif gm_program <= 47:
        return 'strings'
    elif gm_program <= 55:
        return 'ensemble'
    elif gm_program <= 63:
        return 'brass'
    elif gm_program <= 71:
        return 'reed'
    elif gm_program <= 79:
        return 'pipe'
    elif gm_program <= 87:
        return 'synth_lead'
    elif gm_program <= 95:
        return 'synth_pad'
    elif gm_program <= 103:
        return 'synth_fx'
    elif gm_program <= 111:
        return 'world'
    else:
        return 'percussive'


def _synth_gm_note_np(freq, duration, gm_program, velocity=0.8):
    """Synthesize a note using GM-specific timbre profiles.

    Unlike _synth_colored_note_np which uses a generic 8-harmonic additive
    base for all instruments (producing an organ-y tone), this function
    uses the GM_TIMBRE_PROFILES to give each instrument family a distinct
    attack, decay, harmonic structure, and brightness.
    """
    n = int(duration * SAMPLE_RATE)
    if n <= 0:
        return np.zeros(0, dtype=np.float64) if HAS_NUMPY else []

    profile_name = _gm_program_to_timbre(gm_program)
    profile = GM_TIMBRE_PROFILES[profile_name]

    if HAS_NUMPY:
        t = np.arange(n, dtype=np.float64) * INV_SR
        env = _adsr_np(n, profile['attack'], profile['decay'],
                       profile['sustain'], profile['release'])

        # Vibrato
        vib_depth = profile['vib_depth']
        if vib_depth > 0:
            vib_delay = 0.3
            vib_env = np.minimum(1.0, t / max(vib_delay, 0.001))
            vib = vib_depth * vib_env * np.sin(TWO_PI * 5.0 * t)
            ff = freq * (1.0 + vib)
        else:
            ff = freq

        signal = np.zeros(n, dtype=np.float64)
        for h_data in profile['harmonics']:
            h_num, h_amp = h_data[0], h_data[1]
            h_freq = ff * h_num
            if isinstance(h_freq, (int, float)):
                if freq * h_num >= SAMPLE_RATE / 2:
                    continue
            signal += h_amp * np.sin(TWO_PI * h_freq * t)

        # Brightness control: subtle highpass boost or cut
        brightness = profile['brightness']
        if brightness > 0.6:
            # Bright: add slight odd-harmonic emphasis
            emphasis_h = freq * 5
            if emphasis_h < SAMPLE_RATE / 2:
                signal += (brightness - 0.5) * 0.15 * np.sin(TWO_PI * emphasis_h * t)

        result = signal * env * velocity

        # Anti-click micro-fades
        cg = min(int(0.002 * SAMPLE_RATE), n // 4)
        if cg > 0:
            fade_in = np.linspace(0, 1, cg)
            result[:cg] *= fade_in
            result[-cg:] *= fade_in[::-1]

        return result
    else:
        # Pure Python fallback
        env = _adsr(n, profile['attack'], profile['decay'],
                    profile['sustain'], profile['release'])
        signal = [0.0] * n
        for i in range(n):
            t_sec = i * INV_SR
            for h_data in profile['harmonics']:
                h_num, h_amp = h_data[0], h_data[1]
                if freq * h_num >= SAMPLE_RATE / 2:
                    continue
                signal[i] += h_amp * math.sin(TWO_PI * freq * h_num * t_sec)
            signal[i] *= env[i] * velocity
        cg = min(int(0.002 * SAMPLE_RATE), n // 4)
        for ci in range(cg):
            fade = ci / max(cg, 1)
            signal[ci] *= fade
            if n - 1 - ci >= 0:
                signal[n - 1 - ci] *= fade
        return signal


# ---------------------------------------------------------------------------
# V10 RADIO ENGINE -- GM-timbre-aware synthesis with orchestral layering
# ---------------------------------------------------------------------------
class RadioEngineV10(RadioEngineV9):
    """In The Beginning Radio v10 -- GM-timbre-aware orchestral radio.

    Enhancements over v9:
    - Tempo range narrowed to 1.2x-1.8x (from v9's 1.1x-2.1x)
    - GM-timbre-aware synthesis: each MIDI instrument gets distinct attack,
      decay, harmonic structure, and brightness instead of generic additive
      synthesis that sounds organ-y
    - 85% orchestral simultaneous layering (up from 75% in v8/v9)
    - 4-6 voices per segment (up from 2-4) for richer orchestral sections
    - Minimum 3 family groups per segment for true section diversity
    - Wider register spread: -24 to +24 semitones
    - 8-second morph transitions between moods (up from 6s)
    - All v9 features preserved (expanded instruments, family variety,
      time signature control, anti-hiss, subsonic removal)
    """

    MORPH_DURATION = 8.0     # Longer morph for smoother transitions
    FADE_IN_DURATION = 6.0   # Slightly longer fade-in
    FADE_OUT_DURATION = 10.0 # Longer fade-out for gentle ending

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)

    def _compute_tempo_multiplier(self, sim_state):
        """Flat tempo multiplier: 1.2x-1.8x range.

        v10: Narrower range than v9 (1.1x-2.1x). No density-dependent
        capping — just a consistent moderate pace.
        """
        if not sim_state:
            return 1.5  # neutral default

        # Base multiplier from state hash
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.2 + 0.6 * (int(h, 16) / 0xFFFFFFFF)  # 1.2-1.8 range
        return base

    def _choose_gm_instruments_v10(self, midi_info, n_voices, rng):
        """Choose GM instruments with v10 diversity requirements.

        - 4-6 voices per segment
        - Minimum 3 different family groups
        - Wider register spread (-24, -12, 0, +12, +24)
        """
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()

        # Wider register spread for orchestral separation
        offsets_pool = [-24, -12, 0, 0, 12, 24]
        pans_pool = [-0.6, -0.3, -0.1, 0.1, 0.3, 0.6]

        # Variety enforcement from v9
        self._segment_count += 1
        n_total_segments = len(self.segments) if hasattr(self, 'segments') else 15
        past_halfway = self._segment_count > n_total_segments // 2

        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            # Ensure minimum 3 different families
            if v < 3:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)
            elif underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
                underrepresented = [f for f in underrepresented if f != family]
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)

            used_families.add(family)

            # Track family group usage
            for group_name, group_families in self._family_groups.items():
                if family in group_families:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)

            oct_offset = offsets_pool[v % len(offsets_pool)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render a mood segment with v10 GM-timbre-aware synthesis.

        v10 Pipeline:
        1. Compute tempo multiplier (1.2x-1.8x)
        2. Sample MIDI bars
        3. Quantize note durations
        4. Choose 4-6 voices with v10 diversity (min 3 family groups)
        5. Expand notes -> consonant chords
        6. Build rondo sections
        7. 85% simultaneous orchestral layering / 15% solo
        8. GM-timbre-aware synthesis (distinct per instrument)
        9. Chamber effects + anti-click
        10. Loop with crossfade
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        # 1. Tempo multiplier (v10: 1.2-1.8x flat)
        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        # Bar duration
        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = beats_per_bar * beat_dur * quarter_per_beat

        # 2. Sample MIDI bars
        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        # 3. Quantize
        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )

        # 4. Choose voices: v10 uses 4-6 voices for orchestral richness
        n_voices = clamp(rng.randint(4, 6), 4, 6)
        voice_configs = self._choose_gm_instruments_v10(midi_info, n_voices, rng)

        # Assign register offsets for clear separation
        register_offsets = [-24, -12, 0, 0, 12, 24]
        for v_idx, vc in enumerate(voice_configs):
            vc['octave_offset'] = register_offsets[v_idx % len(register_offsets)]

        # 5. Expand notes into chords
        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        # 6. Build rondo sections
        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        voice_gain = 0.25 / max(n_voices, 1)

        # 7 + 8. Orchestral rendering with GM-timbre-aware synthesis
        section_offset_sec = 0.0

        # FluidSynth for primary voice
        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            # v10: 85% simultaneous, 15% solo
            is_solo_section = rng.random() < 0.15
            if is_solo_section:
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                active_voices = list(range(n_voices))

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc['pan']
                gm_program = vc['gm_program']
                v_chord_size = vc['chord_size']

                v_gain = voice_gain * (2.5 if is_solo_section else 1.0)

                # FluidSynth for first voice, first A section
                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * v_gain
                            loop_right[pos] += fr[i] * v_gain
                    continue

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    for note in voice_chord:
                        freq = mtof(note)
                        # v10: GM-timbre-aware synthesis
                        samps = _synth_gm_note_np(freq, dur_sec, gm_program, vel)
                        if HAS_NUMPY:
                            samps = samps.tolist()

                        self._mix_mono(loop_left, loop_right, samps,
                                       offset, loop_samples, pan * v_gain * 4)

            section_offset_sec += segment_duration

        # 9. Chamber effects
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # v10: anti-hiss + subsonic at segment level too
        loop_left_l, loop_right_l = self.anti_hiss.apply_stereo(loop_left, loop_right)
        loop_left, loop_right = self.subsonic_filter.apply_stereo(loop_left_l, loop_right_l)

        # 10. Loop with crossfade
        xfade = min(int(rng.uniform(3.0, 5.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right


# ---------------------------------------------------------------------------
# V11 HELPER CLASSES -- Gain staging, consonance, bar grid, orchestration
# ---------------------------------------------------------------------------

def _soft_limit(x, knee=0.8):
    """Soft-knee limiter: transparent below knee, exponential saturation above.

    Replaces hard tanh limiting which introduces harmonics and distortion.
    """
    ax = abs(x)
    if ax <= knee:
        return x
    sign = 1.0 if x >= 0 else -1.0
    excess = ax - knee
    return sign * (knee + (1.0 - knee) * (1.0 - math.exp(-excess * 3.0)))


class GainStage:
    """Per-voice gain normalization with master bus limiting.

    Solves the root cause of the 'radio static' effect: uncontrolled gain
    accumulation from multiple voices summing into the same buffer.

    Architecture:
    - Each voice is RMS-normalized to a target level
    - Voice gain = headroom / n_voices (prevents summing above headroom)
    - Master bus applies brick-wall soft-knee limiting
    """

    def __init__(self, n_voices, headroom_db=-3.0):
        self.n_voices = max(n_voices, 1)
        self.headroom = 10 ** (headroom_db / 20.0)  # -3dB = 0.708
        self.voice_gain = self.headroom / self.n_voices

    def voice_samples(self, samples, target_rms=0.15, is_solo=False):
        """Normalize a voice to target RMS, then apply voice gain.

        For solo sections, use full headroom instead of per-voice gain.
        """
        gain = self.headroom * 0.8 if is_solo else self.voice_gain
        n = len(samples)
        if n == 0:
            return samples

        # Compute RMS
        sum_sq = 0.0
        for s in samples:
            sum_sq += s * s
        rms = math.sqrt(sum_sq / n)

        if rms > 0.001:
            scale = target_rms / rms
            scale = min(scale, 2.0)  # Don't boost more than 6dB
            return [s * scale * gain for s in samples]
        return [s * gain for s in samples]

    def master_limit(self, left, right, knee=0.80):
        """Soft-knee limiter on the master bus.

        Processes in-place for memory efficiency.
        """
        n = len(left)
        for i in range(n):
            left[i] = _soft_limit(left[i], knee)
            right[i] = _soft_limit(right[i], knee)
        return left, right


class ConsonanceEngine:
    """Inter-voice consonance scoring and adjustment.

    Solves the dissonance problem: multiple voices independently building
    chords that form dissonant composites when stacked vertically.
    """

    # Consonance scores per interval class (0=dissonant, 1=perfect)
    INTERVAL_CONSONANCE = {
        0: 1.0,    # unison
        1: 0.05,   # minor 2nd (harsh)
        2: 0.3,    # major 2nd
        3: 0.7,    # minor 3rd
        4: 0.75,   # major 3rd
        5: 0.8,    # perfect 4th
        6: 0.15,   # tritone
        7: 0.95,   # perfect 5th
        8: 0.7,    # minor 6th
        9: 0.75,   # major 6th
        10: 0.3,   # minor 7th
        11: 0.2,   # major 7th
    }

    def score_composite(self, all_voice_notes):
        """Score consonance of all notes sounding simultaneously.

        Returns float in [0, 1] where higher = more consonant.
        """
        all_notes = []
        for voice_notes in all_voice_notes:
            all_notes.extend(voice_notes)
        if len(all_notes) < 2:
            return 1.0

        total_score = 0.0
        pairs = 0
        for i in range(len(all_notes)):
            for j in range(i + 1, len(all_notes)):
                interval = abs(all_notes[i] - all_notes[j]) % 12
                total_score += self.INTERVAL_CONSONANCE[interval]
                pairs += 1
        return total_score / max(pairs, 1)

    def adjust_for_consonance(self, voice_chords, root, scale_intervals,
                              min_score=0.55, snap_fn=None):
        """Adjust voice chords until composite consonance exceeds threshold.

        Iteratively adjusts the most dissonant voice by shifting notes
        to more consonant intervals. Returns adjusted voice_chords.
        """
        if len(voice_chords) < 2:
            return voice_chords

        score = self.score_composite(voice_chords)
        if score >= min_score:
            return voice_chords

        # Up to 5 adjustment passes
        adjusted = [list(vc) for vc in voice_chords]
        for _pass in range(5):
            if score >= min_score:
                break

            # Find the voice with worst consonance against others
            worst_voice = 0
            worst_score = 1.0
            for vi in range(len(adjusted)):
                others = []
                for vj in range(len(adjusted)):
                    if vj != vi:
                        others.append(adjusted[vj])
                vs = self.score_composite([adjusted[vi]] + others)
                if vs < worst_score:
                    worst_score = vs
                    worst_voice = vi

            # Adjust worst voice: try shifting each note to consonant intervals
            vc = adjusted[worst_voice]
            # Collect all notes from other voices
            other_notes = []
            for vi in range(len(adjusted)):
                if vi != worst_voice:
                    other_notes.extend(adjusted[vi])

            for ni in range(len(vc)):
                note = vc[ni]
                best_note = note
                best_s = 0.0
                # Try +/- 1, 2 semitones
                for delta in [0, 1, -1, 2, -2]:
                    candidate = note + delta
                    if snap_fn:
                        candidate = snap_fn(candidate, root, scale_intervals)
                    candidate = clamp(candidate, 24, 108)
                    # Score this candidate against other notes
                    cs = 0.0
                    for on in other_notes:
                        iv = abs(candidate - on) % 12
                        cs += self.INTERVAL_CONSONANCE[iv]
                    cs /= max(len(other_notes), 1)
                    if cs > best_s:
                        best_s = cs
                        best_note = candidate
                vc[ni] = best_note

            score = self.score_composite(adjusted)

        return adjusted


class BarGrid:
    """Absolute time grid for bar/beat alignment.

    Ensures all note onsets and section boundaries land on metric grid
    positions, solving the beat/bar misalignment problem.
    """

    def __init__(self, tempo, beats_per_bar, beat_unit=4):
        self.tempo = tempo
        self.beats_per_bar = beats_per_bar
        self.beat_unit = beat_unit
        self.beat_dur = 60.0 / tempo
        quarter_per_beat = 4.0 / beat_unit
        self.bar_dur = self.beat_dur * beats_per_bar * quarter_per_beat
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
        else:
            grid = self.sixteenth
        if grid <= 0:
            return t_sec
        return round(t_sec / grid) * grid

    def snap_duration(self, dur_sec, min_dur=None):
        """Snap duration to nearest standard note value."""
        if min_dur is None:
            min_dur = self.sixteenth * 0.5
        # Standard note durations relative to beat
        standards = [
            self.bar_dur,                    # whole
            self.bar_dur * 0.75,             # dotted half
            self.beat_dur * 2,               # half
            self.beat_dur * 1.5,             # dotted quarter
            self.beat_dur,                   # quarter
            self.beat_dur * 0.75,            # dotted 8th
            self.beat_dur * 0.5,             # 8th
            self.beat_dur * 0.25,            # 16th
        ]
        # Find closest
        best = dur_sec
        best_diff = float('inf')
        for s in standards:
            if s < min_dur:
                continue
            diff = abs(dur_sec - s)
            if diff < best_diff:
                best_diff = diff
                best = s
        return best

    def section_start(self, section_idx, bars_per_section):
        """Get exact bar-aligned start time for a rondo section."""
        return section_idx * bars_per_section * self.bar_dur

    def bars_in_duration(self, duration_sec):
        """How many complete bars fit in a duration."""
        if self.bar_dur <= 0:
            return 1
        return max(1, int(duration_sec / self.bar_dur))


class OrchestratorV11:
    """Coordinates multiple voices into a coherent ensemble.

    Assigns complementary orchestral roles with coordinated envelopes,
    register separation, and gain weighting. Solves the 'instruments
    not playing together' problem.
    """

    # (register_offset_semitones, rhythmic_role, gain_weight)
    ROLE_CONFIGS = [
        ('foundation',  -12, 'sustained', 0.80),
        ('harmony_low',   0, 'chordal',   0.55),
        ('harmony_mid',   0, 'chordal',   0.50),
        ('melody',       12, 'melodic',   1.00),
        ('color',        12, 'textural',  0.30),
        ('bass_deep',   -24, 'sustained', 0.70),
    ]

    # GM families suited to each role
    ROLE_FAMILIES = {
        'foundation': ['strings', 'brass', 'bass', 'ensemble'],
        'harmony_low': ['strings', 'reed', 'ensemble', 'organ'],
        'harmony_mid': ['strings', 'reed', 'pipe', 'guitar'],
        'melody': ['pipe', 'strings', 'brass', 'synth_lead'],
        'color': ['synth_pad', 'mallets', 'world', 'ensemble'],
        'bass_deep': ['bass', 'strings', 'organ', 'brass'],
    }

    def assign_roles(self, voice_configs, rng):
        """Assign orchestral roles ensuring complementary voicing.

        Each voice gets a distinct register offset and gain weight.
        No two melody voices; at most one foundation voice.
        """
        n = len(voice_configs)
        # For small ensembles, use a focused subset
        if n <= 3:
            roles = [self.ROLE_CONFIGS[0], self.ROLE_CONFIGS[1],
                     self.ROLE_CONFIGS[3]]  # foundation, harmony, melody
        elif n <= 4:
            roles = [self.ROLE_CONFIGS[0], self.ROLE_CONFIGS[1],
                     self.ROLE_CONFIGS[2], self.ROLE_CONFIGS[3]]
        elif n <= 5:
            roles = self.ROLE_CONFIGS[:5]
        else:
            roles = list(self.ROLE_CONFIGS)

        for i, vc in enumerate(voice_configs):
            role = roles[i % len(roles)]
            vc['role_name'] = role[0]
            vc['octave_offset'] = role[1]
            vc['rhythmic_role'] = role[2]
            vc['gain_weight'] = role[3]

    def apply_voice_leading(self, prev_chord, next_chord, scale_intervals,
                            root, snap_fn=None):
        """Move each voice to the nearest available note in the new chord.

        Minimizes total voice movement (smooth voice leading) instead of
        jumping all voices in parallel.
        """
        if not prev_chord or not next_chord:
            return next_chord

        result = list(next_chord)
        # For each note in prev_chord, find closest in next_chord
        used = set()
        for pi, pn in enumerate(prev_chord):
            if pi >= len(result):
                break
            best_idx = -1
            best_dist = 999
            for ni, nn in enumerate(result):
                if ni in used:
                    continue
                dist = abs(nn - pn)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = ni
            if best_idx >= 0:
                used.add(best_idx)
                # If the movement is large (> octave), try octave transposition
                if best_dist > 12 and snap_fn:
                    candidate = result[best_idx]
                    while candidate - pn > 6:
                        candidate -= 12
                    while pn - candidate > 6:
                        candidate += 12
                    candidate = clamp(candidate, 24, 108)
                    if snap_fn:
                        candidate = snap_fn(candidate, root, scale_intervals)
                    result[best_idx] = candidate

        return result


# ---------------------------------------------------------------------------
# V11 RADIO ENGINE -- Gain-staged, harmonically coherent, bar-aligned
# ---------------------------------------------------------------------------
class RadioEngineV11(RadioEngineV10):
    """In The Beginning Radio v11 -- Comprehensive audio quality overhaul.

    Fixes over v10:
    - Per-voice RMS normalization + master bus soft-knee limiting (no clipping)
    - Separated pan and gain in _mix_mono (fixes phase inversion from pan overflow)
    - Inter-voice consonance engine (no random dissonance between voices)
    - BarGrid-aligned rendering (notes/sections land on beat grid)
    - Orchestral role assignment (voices complement, not compete)
    - Reduced reverb resonance (comb feedback 0.55-0.65 down from 0.70-0.75)
    - Pre-reverb highpass at 150 Hz to prevent low-frequency mud
    - Reverb wet reduced to 0.20 (from 0.30)
    - Early reflection amplitudes reduced (0.05-0.20 from 0.08-0.35)
    - Quality-gated instrument selection (no noise_perc in harmonic voices)
    - freq_mult restricted to [0.5, 1.0, 2.0] (no extreme register shifts)
    - Longer anti-click fades (5ms, up from 2ms) for low-frequency content
    - Soft-knee limiter replaces tanh distortion in streaming renderer
    - Crossfade duration increased to 4-6 seconds
    - Minimum MIDI note raised to 36 (C2) to prevent subsonic fundamentals
    """

    MORPH_DURATION = 8.0
    FADE_IN_DURATION = 6.0
    FADE_OUT_DURATION = 10.0

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        self.consonance = ConsonanceEngine()
        self.orchestrator = OrchestratorV11()

    def _mix_mono_v11(self, left, right, samples, offset, total_samples,
                      pan, gain):
        """Mix mono samples into stereo buffers with SEPARATED pan and gain.

        Unlike v7-v10's _mix_mono which overloaded the pan parameter with
        gain info (pan * v_gain * 4), this version keeps pan in [-1, 1]
        and gain as a separate scalar.

        Pan law: equal-power cosine/sine panning.
        """
        # Clamp pan to [-1, 1] to prevent phase inversion
        pan = max(-1.0, min(1.0, pan))
        # Equal-power pan law
        l_gain = math.cos((pan + 1) * math.pi / 4) * gain
        r_gain = math.sin((pan + 1) * math.pi / 4) * gain
        n = len(samples)
        end = min(offset + n, total_samples)
        start = max(offset, 0)
        for i in range(start, end):
            si = i - offset
            if 0 <= si < n:
                left[i] += samples[si] * l_gain
                right[i] += samples[si] * r_gain

    def _apply_reverb_v11(self, samples, wet=0.20, sr=SAMPLE_RATE):
        """Schroeder reverb with reduced resonance.

        v11 changes vs v7-v10:
        - Comb filter feedback: 0.55-0.65 (was 0.70-0.75)
        - Wet mix: 0.20 (was 0.30)
        - Pre-reverb highpass at 150 Hz to prevent low-freq mud
        """
        n = len(samples)
        if n == 0:
            return samples
        dry = 1.0 - wet

        # Pre-reverb highpass at 150 Hz
        hp_alpha = max(0.0, 1.0 - TWO_PI * 150.0 * INV_SR)
        hp_prev_in = 0.0
        hp_prev_out = 0.0
        hp_signal = [0.0] * n
        for i in range(n):
            hp_prev_out = hp_alpha * (hp_prev_out + samples[i] - hp_prev_in)
            hp_prev_in = samples[i]
            hp_signal[i] = hp_prev_out

        # Comb filters with reduced feedback
        comb_delays = [int(d * sr / 1000) for d in [30, 37, 41, 44]]
        comb_gains = [0.62, 0.60, 0.58, 0.55]  # Reduced from 0.75/0.72/0.70/0.68

        comb_outputs = []
        for delay, gain_c in zip(comb_delays, comb_gains):
            buf = [0.0] * (n + delay)
            for i in range(n):
                buf[i + delay] = hp_signal[i] + gain_c * buf[i]
            comb_outputs.append(buf[:n])

        # Sum comb outputs
        mixed = [0.0] * n
        for i in range(n):
            for co in comb_outputs:
                mixed[i] += co[i]
            mixed[i] /= len(comb_outputs)

        # Allpass filters
        ap_delays = [int(d * sr / 1000) for d in [5, 1.7]]
        ap_gain = 0.6  # Reduced from 0.7
        for delay in ap_delays:
            if delay < 1:
                delay = 1
            buf_in = list(mixed)
            buf_out = [0.0] * n
            for i in range(n):
                delayed = buf_out[i - delay] if i >= delay else 0.0
                buf_out[i] = -ap_gain * buf_in[i] + (buf_in[i - delay] if i >= delay else buf_in[i])
                buf_out[i] += ap_gain * delayed
            mixed = buf_out

        # Blend dry + wet
        out = [0.0] * n
        for i in range(n):
            out[i] = samples[i] * dry + mixed[i] * wet
        # Normalize if needed
        peak = max((abs(s) for s in out), default=1.0)
        if peak > 1.0:
            inv_peak = 1.0 / peak
            for i in range(n):
                out[i] *= inv_peak
        return out

    def _apply_early_reflections_v11(self, samples, sr=SAMPLE_RATE):
        """Early reflections with reduced amplitudes.

        v11: Amplitudes reduced to 0.05-0.20 (from 0.08-0.35).
        """
        delays_ms = [11, 17, 23, 31, 41]
        amps = [0.20, 0.15, 0.10, 0.07, 0.05]  # Reduced
        n = len(samples)
        out = list(samples)
        for delay_ms, amp in zip(delays_ms, amps):
            d = int(delay_ms * sr / 1000)
            for i in range(d, n):
                out[i] += samples[i - d] * amp
        peak = max((abs(s) for s in out), default=1.0)
        if peak > 1.0:
            inv_peak = 1.0 / peak
            for i in range(n):
                out[i] *= inv_peak
        return out

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render a mood segment with v11 comprehensive fixes.

        v11 Pipeline:
        1. Compute tempo multiplier (1.2x-1.8x, inherited from v10)
        2. Create BarGrid for metric alignment
        3. Sample MIDI bars
        4. Quantize notes to bar grid
        5. Choose 4-6 voices with v10 diversity
        6. Assign orchestral roles (register, gain, rhythmic role)
        7. Expand notes -> consonant chords with inter-voice checking
        8. Build rondo sections with bar-aligned offsets
        9. Apply voice leading between chord changes
        10. Per-voice RMS normalization + separated pan/gain mixing
        11. v11 effects chain (reduced reverb, highpass, soft limiting)
        12. Master bus soft-knee limiting
        13. Loop with extended crossfade (4-6s)
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        # 1. Tempo multiplier (inherited from v10)
        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        # 2. Create bar grid
        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_unit = ts_info['unit'] if isinstance(ts_info, dict) else 4
        grid = BarGrid(effective_tempo, beats_per_bar, beat_unit)
        bar_duration_sec = grid.bar_dur

        # 3. Sample MIDI bars
        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        # 4. Quantize notes to bar grid
        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )
        # Additional grid-snap: ensure onsets are on 16th-note grid
        snapped_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            t_snapped = grid.snap_onset(t_sec, '16th')
            dur_snapped = grid.snap_duration(dur_sec)
            snapped_notes.append((t_snapped, midi_note, dur_snapped, vel))
        midi_notes = snapped_notes

        # 5. Choose voices with v10 diversity
        n_voices = clamp(rng.randint(4, 6), 4, 6)
        voice_configs = self._choose_gm_instruments_v10(midi_info, n_voices, rng)

        # 6. Assign orchestral roles (replaces random register assignment)
        self.orchestrator.assign_roles(voice_configs, rng)

        # 7. Expand notes into chords with inter-voice consonance
        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        # 8. Build rondo sections
        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        # Use bar-aligned section offsets instead of accumulated segment_duration
        bars_per_section = grid.bars_in_duration(segment_duration)
        rondo_duration = bars_per_section * grid.bar_dur * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # Create gain stage
        gain_stage = GainStage(n_voices, headroom_db=-3.0)

        # FluidSynth for primary voice
        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        # 9-10. Render voices with orchestral roles and proper gain staging
        prev_voice_chords = {}  # Track previous chord per voice for voice leading

        for sec_idx, (label, section_notes) in enumerate(rondo):
            # Bar-aligned section start
            sec_start = int(grid.section_start(sec_idx, bars_per_section) * SAMPLE_RATE)

            # 85% simultaneous, 15% solo
            is_solo_section = rng.random() < 0.15
            if is_solo_section:
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                active_voices = list(range(n_voices))

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc.get('pan', 0.0)
                gm_program = vc['gm_program']
                v_chord_size = vc['chord_size']
                gain_weight = vc.get('gain_weight', 1.0)

                # FluidSynth for first voice, first A section
                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    fl_gain = gain_stage.voice_gain * gain_weight
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * fl_gain
                            loop_right[pos] += fr[i] * fl_gain
                    continue

                # Collect all notes this voice will play for consonance check
                voice_note_groups = []
                for t_sec, chord, dur_sec, vel in section_notes:
                    voice_chord = chord[:v_chord_size]
                    # v11: minimum MIDI 36 (C2) instead of 24 to prevent
                    # subsonic fundamentals being stripped by the filter
                    voice_chord = [clamp(n + oct_off, 36, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]
                    voice_note_groups.append(voice_chord)

                # Apply voice leading: smooth transitions between chords
                prev_chord = prev_voice_chords.get(v_idx)
                for gi in range(len(voice_note_groups)):
                    if prev_chord and len(prev_chord) > 0:
                        voice_note_groups[gi] = self.orchestrator.apply_voice_leading(
                            prev_chord, voice_note_groups[gi],
                            mood.scale, root, self.midi_lib._snap_to_scale
                        )
                    prev_chord = voice_note_groups[gi]
                if voice_note_groups:
                    prev_voice_chords[v_idx] = voice_note_groups[-1]

                # Inter-voice consonance: check this voice against active others
                # (lightweight: only check first chord of section)
                if not is_solo_section and len(active_voices) > 1 and voice_note_groups:
                    other_chords = []
                    for ov in active_voices:
                        if ov != v_idx and ov in prev_voice_chords:
                            other_chords.append(prev_voice_chords[ov])
                    if other_chords:
                        adjusted = self.consonance.adjust_for_consonance(
                            [voice_note_groups[0]] + other_chords,
                            root, mood.scale, min_score=0.55,
                            snap_fn=self.midi_lib._snap_to_scale
                        )
                        # Apply adjustment to first chord group
                        if adjusted:
                            voice_note_groups[0] = adjusted[0]

                # Synthesize and mix
                for ni, (t_sec, chord, dur_sec, vel) in enumerate(section_notes):
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    voice_chord = voice_note_groups[ni] if ni < len(voice_note_groups) else chord[:v_chord_size]

                    for note in voice_chord:
                        freq = mtof(note)
                        samps = _synth_gm_note_np(freq, dur_sec, gm_program, vel)
                        if HAS_NUMPY:
                            samps = samps.tolist()

                        # v11: longer anti-click fades (5ms, up from 2ms)
                        cg = min(int(0.005 * SAMPLE_RATE), len(samps) // 4)
                        if cg > 1:
                            for ci in range(cg):
                                fade = ci / cg
                                samps[ci] *= fade
                                if len(samps) - 1 - ci >= 0:
                                    samps[len(samps) - 1 - ci] *= fade

                        # Per-voice RMS normalization
                        samps = gain_stage.voice_samples(
                            samps, target_rms=0.15, is_solo=is_solo_section
                        )

                        # v11: separated pan and gain (no more pan * v_gain * 4)
                        self._mix_mono_v11(
                            loop_left, loop_right, samps,
                            offset, loop_samples,
                            pan, gain_weight
                        )

        # 11. v11 effects chain
        if rng.random() < 0.70:
            loop_left = self._apply_early_reflections_v11(loop_left)
            loop_right = self._apply_early_reflections_v11(loop_right)
        if rng.random() < 0.60:
            loop_left = self._apply_reverb_v11(loop_left)
            loop_right = self._apply_reverb_v11(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # Gentle compression AFTER reverb (fixes pumping from compression-then-reverb)
        loop_left = self.smoother.apply_gentle_compression(loop_left, ratio=3.0, threshold=0.5)
        loop_right = self.smoother.apply_gentle_compression(loop_right, ratio=3.0, threshold=0.5)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # Anti-hiss + subsonic
        loop_left_l, loop_right_l = self.anti_hiss.apply_stereo(loop_left, loop_right)
        loop_left, loop_right = self.subsonic_filter.apply_stereo(loop_left_l, loop_right_l)

        # 12. Master bus soft-knee limiting
        gain_stage.master_limit(loop_left, loop_right, knee=0.80)

        # 13. Loop with extended crossfade (4-6 seconds)
        xfade = min(int(rng.uniform(4.0, 6.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right

    def render_streaming(self, wav_file, sim_states=None):
        """Streaming renderer with soft-knee limiting (replaces tanh).

        Overrides the base streaming renderer to use _soft_limit instead
        of math.tanh for the per-sample output limiter.
        """
        total_samples = int(self.total_duration * SAMPLE_RATE)
        n_segments = len(self.segments)
        morph_samples = int(self.MORPH_DURATION * SAMPLE_RATE)
        fade_in_samples = int(self.FADE_IN_DURATION * SAMPLE_RATE)
        fade_out_samples = int(self.FADE_OUT_DURATION * SAMPLE_RATE)

        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        # Apply v8 time sig overrides
        orig, patched = self._patch_mood_init()
        MoodSegment.__init__ = patched

        try:
            max_seg_samples = int(220 * SAMPLE_RATE)
            buf_len = max_seg_samples + morph_samples * 2
            buf_left = [0.0] * buf_len
            buf_right = [0.0] * buf_len
            buf_global_start = 0
            samples_written = 0

            for seg_idx in range(n_segments):
                seg_info = self.segments[seg_idx]
                seg_global_start = int(seg_info['start'] * SAMPLE_RATE)
                seg_duration = seg_info['duration']
                segment_samples = int(seg_duration * SAMPLE_RATE)
                if seg_global_start >= total_samples:
                    break

                time_pos = seg_info['start']
                epoch_idx = int(time_pos / self.total_duration * 12.999)
                epoch_idx = clamp(epoch_idx, 0, 12)
                epoch = EPOCH_ORDER[epoch_idx]
                sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

                mood = MoodSegment(
                    seg_idx, epoch, epoch_idx, sim_state,
                    self.seed + seg_idx * 31337
                )
                selected = self._select_instruments(mood)
                kits = InstrumentKit.build_kits(
                    selected, mood.scale, mood.root, mood.n_kits, mood.rng
                )
                seg_left, seg_right = self._render_segment(
                    mood, kits, segment_samples, sim_state
                )

                if mood.dampen:
                    seg_left = self.smoother.apply_lowpass(seg_left, 5000)
                    seg_right = self.smoother.apply_lowpass(seg_right, 5000)
                    seg_left = self.smoother.apply_gentle_compression(seg_left)
                    seg_right = self.smoother.apply_gentle_compression(seg_right)

                seg_end_global = min(seg_global_start + len(seg_left), total_samples)
                seg_len = seg_end_global - seg_global_start

                for i in range(seg_len):
                    global_i = seg_global_start + i
                    buf_i = global_i - buf_global_start
                    while buf_i >= len(buf_left):
                        buf_left.append(0.0)
                        buf_right.append(0.0)

                    fade = 1.0
                    if i < morph_samples and seg_idx > 0:
                        fade = 0.5 - 0.5 * math.cos(math.pi * i / morph_samples)
                    remaining = seg_len - i
                    if remaining < morph_samples and seg_idx < n_segments - 1:
                        fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - remaining / morph_samples))

                    if global_i < fade_in_samples:
                        fade *= global_i / fade_in_samples
                    elif global_i >= total_samples - fade_out_samples:
                        fade *= (total_samples - global_i) / fade_out_samples

                    buf_left[buf_i] += seg_left[i] * fade
                    buf_right[buf_i] += seg_right[i] * fade

                if seg_idx in self.tts_transitions:
                    trans_start = seg_global_start + seg_len - morph_samples
                    self._inject_tts_into_buf(
                        buf_left, buf_right, buf_global_start,
                        trans_start, total_samples, mood, epoch_idx
                    )

                # Flush completed audio
                if seg_idx < n_segments - 1:
                    next_seg_start = int(self.segments[seg_idx + 1]['start'] * SAMPLE_RATE)
                    flush_up_to = next_seg_start - morph_samples
                else:
                    flush_up_to = total_samples

                flush_end = min(flush_up_to, total_samples)
                flush_count = flush_end - samples_written
                if flush_count > 0:
                    data = bytearray(flush_count * 4)
                    for j in range(flush_count):
                        buf_j = (samples_written + j) - buf_global_start
                        lv = buf_left[buf_j] if 0 <= buf_j < len(buf_left) else 0.0
                        rv = buf_right[buf_j] if 0 <= buf_j < len(buf_right) else 0.0
                        lv, rv = lv * 0.9 + rv * 0.1, rv * 0.9 + lv * 0.1
                        # v11: soft-knee limiter instead of tanh
                        li = int(_soft_limit(lv, 0.8) * 32767)
                        ri = int(_soft_limit(rv, 0.8) * 32767)
                        struct.pack_into('<hh', data, j * 4,
                                       max(-32767, min(32767, li)),
                                       max(-32767, min(32767, ri)))
                    wav_file.writeframes(bytes(data))
                    samples_written = flush_end

                    # Shift buffer
                    shift = flush_end - buf_global_start
                    if shift > 0 and shift < len(buf_left):
                        buf_left = buf_left[shift:] + [0.0] * shift
                        buf_right = buf_right[shift:] + [0.0] * shift
                        buf_global_start = flush_end
                    elif shift >= len(buf_left):
                        buf_left = [0.0] * buf_len
                        buf_right = [0.0] * buf_len
                        buf_global_start = flush_end

        finally:
            MoodSegment.__init__ = orig

        return samples_written


# ---------------------------------------------------------------------------
# V12 RADIO ENGINE -- V8 synthesis + expanded instruments/MIDIs + multiprocessing
# ---------------------------------------------------------------------------

# V12 uses v8's proven _synth_colored_note_np() synthesis approach (InstrumentFactory
# timbre blending) combined with v9's expanded 50+ GM instruments, v10's 744 MIDIs,
# and v11's gain staging / anti-hiss / subsonic filters. The key difference from the
# previous v12 attempt is that we do NOT use a custom synthesis function — we use
# exactly what v8 used, which produces the natural instrument character.
#
# Tempo is clamped to 1.1x-1.7x (narrower than v9's 1.1x-2.1x).
# Multiprocessing renders segments in parallel across all available CPU cores.

# Multiprocessing helpers — each worker renders one mood segment independently.
# The main process then stitches them together with crossfades.

def _render_segment_worker(args):
    """Worker function for multiprocessing segment rendering.

    Each worker creates its own engine components (non-picklable objects
    can't be passed across process boundaries) and renders one segment.
    Returns (seg_idx, left_samples, right_samples, seg_info).
    """
    import time as _wtime
    (seg_idx, seg_info, seed, total_duration, sim_state, n_segments) = args

    ct = _wtime.strftime('%Y-%m-%d %H:%M CT', _wtime.localtime())

    # Create a fresh engine per worker (avoids pickling issues)
    engine = RadioEngineV12(seed=seed, total_duration=total_duration)

    time_pos = seg_info['start']
    seg_duration = seg_info['duration']
    segment_samples = int(seg_duration * SAMPLE_RATE)

    epoch_idx = int(time_pos / total_duration * 12.999)
    epoch_idx = clamp(epoch_idx, 0, 12)
    epoch = EPOCH_ORDER[epoch_idx]

    # Apply v8 time sig overrides
    orig, patched = engine._patch_mood_init()
    MoodSegment.__init__ = patched
    try:
        mood = MoodSegment(
            seg_info['idx'], epoch, epoch_idx, sim_state,
            seed + seg_info['idx'] * 31337
        )
        selected = engine._select_instruments(mood)
        kits = InstrumentKit.build_kits(
            selected, mood.scale, mood.root, mood.n_kits, mood.rng
        )
        seg_left, seg_right = engine._render_segment(
            mood, kits, segment_samples, sim_state
        )
    finally:
        MoodSegment.__init__ = orig

    if mood.dampen:
        seg_left = engine.smoother.apply_lowpass(seg_left, 5000)
        seg_right = engine.smoother.apply_lowpass(seg_right, 5000)
        seg_left = engine.smoother.apply_gentle_compression(seg_left)
        seg_right = engine.smoother.apply_gentle_compression(seg_right)

    ct = _wtime.strftime('%Y-%m-%d %H:%M CT', _wtime.localtime())
    print(f"  [{ct}] Segment {seg_idx+1}/{n_segments} rendered "
          f"({seg_duration:.0f}s, epoch={epoch})")

    return (seg_idx, seg_left, seg_right, seg_info)


class RadioEngineV12(RadioEngineV8):
    """In The Beginning Radio v12 -- V8 synthesis + expanded palette + speed.

    Uses v8's proven _synth_colored_note_np() synthesis (InstrumentFactory
    timbre blending) which produces natural instrument character, combined with:
    - v9's 50+ expanded GM instruments and 15 family pools
    - v10's 744 MIDI files from 26 composers
    - v11's gain staging, anti-hiss, and subsonic filters
    - Tempo clamp: 1.1x-1.7x (tighter than v9's 1.1x-2.1x)
    - Multiprocessing: segments rendered in parallel across all CPU cores

    This is intentionally close to v8's spectral profile, with more instrument
    variety from the expanded MIDI/instrument catalog and slightly different
    tempo dynamics from the narrower clamp range.
    """

    MORPH_DURATION = 8.0
    FADE_IN_DURATION = 6.0
    FADE_OUT_DURATION = 10.0

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        # Inherit v9's family tracking
        self._used_family_groups = set()
        self._family_groups = {
            'symphonic': {'strings', 'brass', 'woodwinds', 'sax', 'choir',
                          'symphonic_ext'},
            'rock': {'rock_guitar', 'rock_bass'},
            'electronic': {'synth_lead', 'synth_pad', 'synth_fx'},
            'world': {'world'},
            'classical': {'keys', 'pitched_perc', 'mallets'},
        }
        self._segment_count = 0
        # v11 gain staging components
        self.gain_stage = GainStage(4, headroom_db=-3.0)

    def _compute_tempo_multiplier(self, sim_state):
        """Tempo multiplier clamped to 1.1x-1.7x.

        Narrower than v9 (1.1x-2.1x), wider than v10 (1.2x-1.8x).
        Density-aware: high-density epochs cap at 1.5x.
        """
        if not sim_state:
            return 1.4  # neutral default

        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 0.6 * (int(h, 16) / 0xFFFFFFFF)  # 1.1-1.7 range

        # Density-aware capping
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5
        if density > 200:
            base = min(base, 1.5)
        if density > 500:
            base = min(base, 1.4)

        return base

    def _choose_gm_instruments(self, midi_info, n_voices, rng):
        """Choose GM instruments from v9's expanded catalog.

        Uses v9's 15 family pools with variety enforcement.
        3-5 voices per segment, minimum 3 different families.
        """
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()
        register_offsets = [-12, 0, 0, 12, 24]
        pans_pool = [-0.5, -0.2, 0.0, 0.2, 0.5]

        # Track family group usage for variety enforcement
        self._segment_count += 1
        n_total_segments = len(self.segments) if hasattr(self, 'segments') else 15
        past_halfway = self._segment_count > n_total_segments // 2

        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            # Ensure minimum 3 different families
            if v < 3:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)
            elif underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
                underrepresented = [f for f in underrepresented if f != family]
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)

            used_families.add(family)
            for group_name, group_fams in self._family_groups.items():
                if family in group_fams:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)
            oct_offset = register_offsets[v % len(register_offsets)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render segment using v8's synthesis + v11's gain staging.

        This is v8's _render_segment with:
        - v9's expanded instrument selection
        - v11's gain staging on the master bus
        - Anti-hiss + subsonic at segment level
        """
        # Call the parent v8 _render_segment (uses _synth_colored_note_np)
        left, right = super()._render_segment(mood, kits, n_samples, sim_state)

        # Apply v11's gain staging on the output
        self.gain_stage.master_limit(left, right, knee=0.80)

        return left, right

    def render_streaming_parallel(self, wav_file, sim_states=None):
        """Parallel streaming renderer using multiprocessing.

        Renders segments in parallel across all CPU cores, then stitches
        them together with crossfades. This can be 4-12x faster than the
        sequential streaming renderer on multi-core systems.
        """
        import multiprocessing as mp

        total_samples = int(self.total_duration * SAMPLE_RATE)
        n_segments = len(self.segments)
        morph_samples = int(self.MORPH_DURATION * SAMPLE_RATE)
        fade_in_samples = int(self.FADE_IN_DURATION * SAMPLE_RATE)
        fade_out_samples = int(self.FADE_OUT_DURATION * SAMPLE_RATE)

        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        # Build worker args
        worker_args = []
        for seg_idx in range(n_segments):
            seg_info = self.segments[seg_idx]
            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]
            worker_args.append((
                seg_idx, seg_info, self.seed, self.total_duration,
                sim_state, n_segments
            ))

        # Determine worker count
        n_cores = mp.cpu_count()
        n_workers = min(n_cores, n_segments)

        ct = _time.strftime('%Y-%m-%d %H:%M CT', _time.localtime())
        print(f"  [{ct}] Parallel render: {n_workers} workers across {n_cores} cores")

        # Render segments in parallel
        results = []
        try:
            with mp.Pool(processes=n_workers) as pool:
                results = pool.map(_render_segment_worker, worker_args)
        except Exception as e:
            print(f"  [Warning] Multiprocessing failed ({e}), falling back to sequential")
            for args in worker_args:
                results.append(_render_segment_worker(args))

        # Sort results by segment index
        results.sort(key=lambda r: r[0])

        # Stitch segments with crossfades and write to WAV
        samples_written = 0
        buf_len = int(220 * SAMPLE_RATE) + morph_samples * 2
        buf_left = [0.0] * buf_len
        buf_right = [0.0] * buf_len
        buf_global_start = 0

        for seg_idx, seg_left, seg_right, seg_info in results:
            seg_global_start = int(seg_info['start'] * SAMPLE_RATE)
            seg_len = min(len(seg_left), total_samples - seg_global_start)

            for i in range(seg_len):
                global_i = seg_global_start + i
                buf_i = global_i - buf_global_start
                while buf_i >= len(buf_left):
                    buf_left.append(0.0)
                    buf_right.append(0.0)

                fade = 1.0
                if i < morph_samples and seg_idx > 0:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / morph_samples)
                remaining = seg_len - i
                if remaining < morph_samples and seg_idx < n_segments - 1:
                    fade *= 0.5 + 0.5 * math.cos(
                        math.pi * (1 - remaining / morph_samples))

                if global_i < fade_in_samples:
                    fade *= global_i / fade_in_samples
                elif global_i >= total_samples - fade_out_samples:
                    fade *= (total_samples - global_i) / fade_out_samples

                buf_left[buf_i] += seg_left[i] * fade
                buf_right[buf_i] += seg_right[i] * fade

            # TTS injection
            if seg_idx in self.tts_transitions:
                trans_start = seg_global_start + seg_len - morph_samples
                # Create a lightweight mood stand-in with an RNG
                seg_info = self.segments[seg_idx]
                _tts_mood = type('_Mood', (), {
                    'rng': random.Random(self.seed + seg_idx)
                })()
                epoch_idx = EPOCH_ORDER.index(seg_info.get('epoch', 'Planck')) \
                    if seg_info.get('epoch') in EPOCH_ORDER else 0
                self._inject_tts_into_buf(
                    buf_left, buf_right, buf_global_start,
                    trans_start, total_samples, _tts_mood, epoch_idx
                )

            # Flush completed audio
            if seg_idx < n_segments - 1:
                next_seg_start = int(self.segments[seg_idx + 1]['start'] * SAMPLE_RATE)
                flush_up_to = next_seg_start - morph_samples
            else:
                flush_up_to = total_samples

            flush_end = min(flush_up_to, total_samples)
            flush_count = flush_end - samples_written
            if flush_count > 0:
                data = bytearray(flush_count * 4)
                for j in range(flush_count):
                    buf_j = (samples_written + j) - buf_global_start
                    lv = buf_left[buf_j] if 0 <= buf_j < len(buf_left) else 0.0
                    rv = buf_right[buf_j] if 0 <= buf_j < len(buf_right) else 0.0
                    # Stereo crossfeed
                    lv, rv = lv * 0.9 + rv * 0.1, rv * 0.9 + lv * 0.1
                    # Soft-knee limiter
                    li = int(_soft_limit(lv, 0.8) * 32767)
                    ri = int(_soft_limit(rv, 0.8) * 32767)
                    struct.pack_into('<hh', data, j * 4,
                                   max(-32767, min(32767, li)),
                                   max(-32767, min(32767, ri)))
                wav_file.writeframes(bytes(data))
                samples_written = flush_end

                # Shift buffer
                shift = flush_end - buf_global_start
                if shift > 0 and shift < len(buf_left):
                    buf_left = buf_left[shift:] + [0.0] * shift
                    buf_right = buf_right[shift:] + [0.0] * shift
                    buf_global_start = flush_end
                elif shift >= len(buf_left):
                    buf_left = [0.0] * buf_len
                    buf_right = [0.0] * buf_len
                    buf_global_start = flush_end

        return samples_written


# Keep old profiles dict for test import compatibility but it's not used by v12
GM_TIMBRE_PROFILES_V12 = {
    'piano': {
        'attack': 0.005, 'decay': 0.25, 'sustain': 0.25, 'release': 0.35,
        'harmonics': [(1, 1.0), (2, 0.55), (3, 0.18), (4, 0.12), (5, 0.06),
                      (6, 0.03), (7, 0.015)],
        'detune_cents': 1.5, 'noise_amount': 0.008, 'vib_depth': 0.0,
        'warmth': 0.6,
    },
    'mallets': {
        'attack': 0.002, 'decay': 0.12, 'sustain': 0.08, 'release': 0.2,
        'harmonics': [(1, 1.0), (2.76, 0.45), (5.4, 0.2), (8.93, 0.08)],
        'detune_cents': 0.8, 'noise_amount': 0.005, 'vib_depth': 0.0,
        'warmth': 0.5,
    },
    'organ': {
        'attack': 0.025, 'decay': 0.03, 'sustain': 0.8, 'release': 0.1,
        'harmonics': [(1, 1.0), (2, 0.7), (3, 0.5), (4, 0.35), (5, 0.2),
                      (6, 0.15), (8, 0.1)],
        'detune_cents': 2.0, 'noise_amount': 0.003, 'vib_depth': 0.003,
        'warmth': 0.55,
    },
    'guitar': {
        'attack': 0.003, 'decay': 0.3, 'sustain': 0.15, 'release': 0.35,
        'harmonics': [(1, 1.0), (2, 0.45), (3, 0.3), (4, 0.18), (5, 0.1),
                      (6, 0.06), (7, 0.03)],
        'detune_cents': 1.2, 'noise_amount': 0.012, 'vib_depth': 0.001,
        'warmth': 0.65,
    },
    'bass': {
        'attack': 0.008, 'decay': 0.15, 'sustain': 0.55, 'release': 0.18,
        'harmonics': [(1, 1.0), (2, 0.45), (3, 0.18), (4, 0.06)],
        'detune_cents': 0.5, 'noise_amount': 0.006, 'vib_depth': 0.0003,
        'warmth': 0.8,
    },
    'strings': {
        'attack': 0.12, 'decay': 0.15, 'sustain': 0.7, 'release': 0.3,
        'harmonics': [(1, 1.0), (2, 0.65), (3, 0.45), (4, 0.22), (5, 0.12),
                      (6, 0.06), (7, 0.03), (8, 0.015)],
        'detune_cents': 2.5, 'noise_amount': 0.015, 'vib_depth': 0.005,
        'warmth': 0.55,
    },
    'ensemble': {
        'attack': 0.15, 'decay': 0.2, 'sustain': 0.65, 'release': 0.35,
        'harmonics': [(1, 1.0), (2, 0.6), (3, 0.4), (4, 0.25), (5, 0.15),
                      (6, 0.08), (7, 0.04)],
        'detune_cents': 3.0, 'noise_amount': 0.01, 'vib_depth': 0.006,
        'warmth': 0.5,
    },
    'brass': {
        'attack': 0.04, 'decay': 0.1, 'sustain': 0.65, 'release': 0.15,
        'harmonics': [(1, 1.0), (2, 0.85), (3, 0.65), (4, 0.45), (5, 0.28),
                      (6, 0.15), (7, 0.08), (8, 0.04)],
        'detune_cents': 1.0, 'noise_amount': 0.02, 'vib_depth': 0.003,
        'warmth': 0.45,
    },
    'reed': {
        'attack': 0.03, 'decay': 0.08, 'sustain': 0.6, 'release': 0.12,
        'harmonics': [(1, 1.0), (2, 0.25), (3, 0.55), (4, 0.12), (5, 0.35),
                      (6, 0.06), (7, 0.18)],
        'detune_cents': 1.5, 'noise_amount': 0.025, 'vib_depth': 0.004,
        'warmth': 0.5,
    },
    'pipe': {
        'attack': 0.05, 'decay': 0.06, 'sustain': 0.65, 'release': 0.18,
        'harmonics': [(1, 1.0), (2, 0.08), (3, 0.25), (5, 0.05)],
        'detune_cents': 0.8, 'noise_amount': 0.03, 'vib_depth': 0.003,
        'warmth': 0.6,
    },
    'synth_lead': {
        'attack': 0.008, 'decay': 0.12, 'sustain': 0.55, 'release': 0.1,
        'harmonics': [(1, 1.0), (2, 0.45), (3, 0.28), (4, 0.2), (5, 0.15),
                      (6, 0.1), (7, 0.07)],
        'detune_cents': 2.0, 'noise_amount': 0.005, 'vib_depth': 0.002,
        'warmth': 0.4,
    },
    'synth_pad': {
        'attack': 0.25, 'decay': 0.35, 'sustain': 0.75, 'release': 0.6,
        'harmonics': [(1, 1.0), (2, 0.4), (3, 0.18), (4, 0.08), (5, 0.04)],
        'detune_cents': 3.5, 'noise_amount': 0.008, 'vib_depth': 0.007,
        'warmth': 0.65,
    },
    'synth_fx': {
        'attack': 0.015, 'decay': 0.25, 'sustain': 0.35, 'release': 0.35,
        'harmonics': [(1, 1.0), (1.41, 0.35), (2.23, 0.25), (3.17, 0.15),
                      (4.59, 0.08)],
        'detune_cents': 4.0, 'noise_amount': 0.015, 'vib_depth': 0.005,
        'warmth': 0.4,
    },
    'world': {
        'attack': 0.006, 'decay': 0.22, 'sustain': 0.2, 'release': 0.25,
        'harmonics': [(1, 1.0), (2, 0.5), (3, 0.35), (4, 0.25), (5, 0.12),
                      (6.2, 0.06)],
        'detune_cents': 2.0, 'noise_amount': 0.018, 'vib_depth': 0.003,
        'warmth': 0.55,
    },
    'percussive': {
        'attack': 0.001, 'decay': 0.06, 'sustain': 0.04, 'release': 0.12,
        'harmonics': [(1, 1.0), (2.3, 0.5), (4.1, 0.25), (6.7, 0.1)],
        'detune_cents': 0.5, 'noise_amount': 0.02, 'vib_depth': 0.0,
        'warmth': 0.3,
    },
}

# ---------------------------------------------------------------------------
# V13 RADIO ENGINE -- V8 core restoration with V12 density-aware tempo
# ---------------------------------------------------------------------------

class RadioEngineV13(RadioEngineV8):
    """In The Beginning Radio v13 -- V8 audio with V12 tempo.

    V12 introduced double soft-knee limiting (per-segment master_limit + streaming
    writer _soft_limit) that caused pronounced bitcrusher artifacts. V13 reverts
    to V8's clean audio pipeline (instruments, synthesis, mixing, volume) and
    overrides only the tempo multiplier to use V12's density-aware tempo range
    (1.1x-1.7x).

    This engine produces output matching V8's volume and spectral profile, with
    the slower, density-responsive tempo pacing from V12.
    """

    def _compute_tempo_multiplier(self, sim_state):
        """Density-aware tempo multiplier clamped to 1.1x-1.7x.

        Inherited from v12's tempo design:
        - Range: 1.1x-1.7x (slower than v8's 1.5x-2.5x)
        - Default: 1.4x (neutral, no sim_state)
        - Density-aware: high-density epochs cap at 1.4-1.5x
        """
        if not sim_state:
            return 1.4  # neutral default

        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 0.6 * (int(h, 16) / 0xFFFFFFFF)  # 1.1-1.7 range

        # Density-aware capping
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5
        if density > 200:
            base = min(base, 1.5)
        if density > 500:
            base = min(base, 1.4)

        return base


def generate_radio_v13_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v13 radio MP3 -- V8 core audio with V12 density-aware tempo.

    v13 uses v8's complete audio pipeline (instruments, synthesis, mixing, volume)
    with only the tempo multiplier overridden to v12's density-aware 1.1x-1.7x range.
    No per-segment limiting, no double limiting, no expanded instrument palette.
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV13] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV13(seed=seed, total_duration=duration)

    print(f"[{ct_now}] [RadioEngineV13] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV13] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV13] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[{ct_now}] [RadioEngineV13] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[{ct_now}] [RadioEngineV13] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[{ct_now}] [RadioEngineV13] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")
    print(f"[{ct_now}] [RadioEngineV13] Synthesis: v8 colored note (InstrumentFactory)")
    print(f"[{ct_now}] [RadioEngineV13] Instruments: v8 5-pool orchestral palette")
    print(f"[{ct_now}] [RadioEngineV13] Tempo range: 1.1x-1.7x (density-aware, from v12)")
    print(f"[{ct_now}] [RadioEngineV13] Volume: v8 levels (no per-segment limiting)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV13] Rendering audio...")
    t0 = _time.time()

    # Import simulator
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                ct_seg = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"  [{ct_seg}] Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    # Use streaming renderer for long durations (V8's clean streaming path)
    use_streaming = duration > 660

    if use_streaming:
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV13] Using streaming renderer (V8 path, no double limiting)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                    _time.localtime(_time.time()))
            print(f"[{ct_now}] [RadioEngineV13] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[{ct_now}] [RadioEngineV13] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV13] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[{ct_now}] [RadioEngineV13] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV13] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[{ct_now}] [RadioEngineV13] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[{ct_now}] [RadioEngineV13] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV13] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[{ct_now}] [RadioEngineV13] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[{ct_now}] [RadioEngineV13] File size: {file_size/1048576:.1f} MB")
    return output_path


# ---------------------------------------------------------------------------
# V14 RADIO ENGINE -- Full palette (V12 instruments/MIDI) + serial render (V8 path)
# ---------------------------------------------------------------------------

# V14 combines V12's rich instrument palette (15 families, 744 MIDI files) with
# V8/V13's clean serial rendering path. User discovered that serial (not parallel)
# rendering eliminates the bitcrusher artifacts. No per-segment GainStage.master_limit,
# no multiprocessing. This gives the richest instrument variety without audio artifacts.


class RadioEngineV14(RadioEngineV8):
    """In The Beginning Radio v14 -- Full palette with clean serial render.

    Combines:
    - V12's 15 instrument family pools with variety enforcement
    - V12's density-aware tempo (1.1x-1.7x)
    - V10's 744 MIDI files from 26 composers
    - V8's clean serial _render_segment() (no per-segment master_limit)
    - V8's serial render_streaming() (no multiprocessing)

    This engine produces the richest instrument variety without bitcrusher
    artifacts, by rendering all tracks serially through V8's clean audio path.
    """

    MORPH_DURATION = 8.0
    FADE_IN_DURATION = 6.0
    FADE_OUT_DURATION = 10.0

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        # V12's family tracking for variety enforcement
        self._used_family_groups = set()
        self._family_groups = {
            'symphonic': {'strings', 'brass', 'woodwinds', 'sax', 'choir',
                          'symphonic_ext'},
            'rock': {'rock_guitar', 'rock_bass'},
            'electronic': {'synth_lead', 'synth_pad', 'synth_fx'},
            'world': {'world'},
            'classical': {'keys', 'pitched_perc', 'mallets'},
        }
        self._segment_count = 0

    def _compute_tempo_multiplier(self, sim_state):
        """Density-aware tempo multiplier clamped to 1.1x-1.7x.

        From V12's tempo design:
        - Range: 1.1x-1.7x (slower than v8's 1.5x-2.5x)
        - Default: 1.4x (neutral, no sim_state)
        - Density-aware: high-density epochs cap at 1.4-1.5x
        """
        if not sim_state:
            return 1.4  # neutral default

        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 0.6 * (int(h, 16) / 0xFFFFFFFF)  # 1.1-1.7 range

        # Density-aware capping
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5
        if density > 200:
            base = min(base, 1.5)
        if density > 500:
            base = min(base, 1.4)

        return base

    def _choose_gm_instruments(self, midi_info, n_voices, rng):
        """Choose GM instruments from V12's expanded catalog.

        Uses V9's 15 family pools with variety enforcement.
        3-5 voices per segment, minimum 3 different families.
        """
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()
        register_offsets = [-12, 0, 0, 12, 24]
        pans_pool = [-0.5, -0.2, 0.0, 0.2, 0.5]

        # Track family group usage for variety enforcement
        self._segment_count += 1
        n_total_segments = len(self.segments) if hasattr(self, 'segments') else 15
        past_halfway = self._segment_count > n_total_segments // 2

        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            # Ensure minimum 3 different families
            if v < 3:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)
            elif underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
                underrepresented = [f for f in underrepresented if f != family]
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)

            used_families.add(family)
            for group_name, group_fams in self._family_groups.items():
                if family in group_fams:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)
            oct_offset = register_offsets[v % len(register_offsets)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices


def generate_radio_v14_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v14 radio MP3 -- full palette with clean serial render.

    v14 uses V12's expanded instruments (15 families) and MIDI library (744 files)
    with V8's clean serial rendering path. No per-segment limiting, no multiprocessing.
    Tempo: V12's density-aware 1.1x-1.7x range.
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV14] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV14(seed=seed, total_duration=duration)

    print(f"[{ct_now}] [RadioEngineV14] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV14] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV14] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[{ct_now}] [RadioEngineV14] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[{ct_now}] [RadioEngineV14] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[{ct_now}] [RadioEngineV14] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")
    print(f"[{ct_now}] [RadioEngineV14] Synthesis: v8 colored note (InstrumentFactory)")
    print(f"[{ct_now}] [RadioEngineV14] Instruments: v12 15-pool expanded palette")
    print(f"[{ct_now}] [RadioEngineV14] MIDI library: {len(engine.midi_lib._note_sequences)} sequences")
    print(f"[{ct_now}] [RadioEngineV14] Tempo range: 1.1x-1.7x (density-aware, from v12)")
    print(f"[{ct_now}] [RadioEngineV14] Render mode: SERIAL (no multiprocessing)")
    print(f"[{ct_now}] [RadioEngineV14] Volume: v8 levels (no per-segment limiting)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV14] Rendering audio (serial)...")
    t0 = _time.time()

    # Import simulator
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                ct_seg = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"  [{ct_seg}] Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    # Use streaming renderer for long durations (V8's clean serial path)
    use_streaming = duration > 660

    if use_streaming:
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV14] Using serial streaming renderer (V8 path, no limiting)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                    _time.localtime(_time.time()))
            print(f"[{ct_now}] [RadioEngineV14] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[{ct_now}] [RadioEngineV14] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV14] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[{ct_now}] [RadioEngineV14] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV14] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[{ct_now}] [RadioEngineV14] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[{ct_now}] [RadioEngineV14] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV14] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[{ct_now}] [RadioEngineV14] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[{ct_now}] [RadioEngineV14] File size: {file_size/1048576:.1f} MB")
    return output_path


# ---------------------------------------------------------------------------
# V15 RADIO ENGINE -- True original V8 synthesis + V12 tempo
# ---------------------------------------------------------------------------

# V15 restores the **original** V8 synthesis path from git commit 348bf29.
# The current V8 class uses numpy-accelerated _synth_colored_note_np() (added in
# commit 45791bd) which may produce subtly different audio. V15 forces the original
# InstrumentFactory.synthesize_colored_note() path for authentic V8 sound.
# Combined with V12's density-aware tempo (1.1x-1.7x).


class RadioEngineV15(RadioEngineV8):
    """In The Beginning Radio v15 -- True original V8 synthesis + V12 tempo.

    Like V13 but uses the original InstrumentFactory.synthesize_colored_note()
    instead of the numpy-accelerated _synth_colored_note_np(). This produces
    the authentic V8 sound that existed at commit 348bf29, before the numpy
    acceleration was added.

    - Original V8 synthesis: factory.synthesize_colored_note() (pure Python)
    - V12 density-aware tempo: 1.1x-1.7x
    - V8's 5 instrument families
    - 537 instruments
    - Serial rendering (V8's streaming path)
    """

    def _compute_tempo_multiplier(self, sim_state):
        """Density-aware tempo multiplier clamped to 1.1x-1.7x (from V12)."""
        if not sim_state:
            return 1.4
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 0.6 * (int(h, 16) / 0xFFFFFFFF)
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5
        if density > 200:
            base = min(base, 1.5)
        if density > 500:
            base = min(base, 1.4)
        return base

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """Render using original V8 synthesis (factory.synthesize_colored_note).

        This is identical to V8's _render_segment except it ALWAYS uses
        self.factory.synthesize_colored_note() (the pure Python path from
        commit 348bf29) instead of the numpy-accelerated path.
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = beats_per_bar * beat_dur * quarter_per_beat

        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )

        n_voices = getattr(mood, 'n_voices', rng.randint(2, 4))
        n_voices = clamp(n_voices, 2, 4)
        voice_configs = self._choose_gm_instruments(midi_info, n_voices, rng)

        register_offsets = [-12, 0, 0, 12, 24]
        for v_idx, vc in enumerate(voice_configs):
            vc['octave_offset'] = register_offsets[v_idx % len(register_offsets)]

        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        voice_gain = 0.30 / max(n_voices, 1)
        section_offset_sec = 0.0

        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            is_solo_section = rng.random() < 0.25
            if is_solo_section:
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                active_voices = list(range(n_voices))

            voice_instruments = [rng.choice(self.instruments) for _ in voice_configs]

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc['pan']
                ca = vc['color_amount']
                v_chord_size = vc['chord_size']

                v_gain = voice_gain * (2.0 if is_solo_section else 1.0)

                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * v_gain
                            loop_right[pos] += fr[i] * v_gain
                    continue

                color_instr = voice_instruments[v_idx]

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    # ORIGINAL V8 synthesis: factory.synthesize_colored_note
                    # (pure Python, from commit 348bf29)
                    for note in voice_chord:
                        freq = mtof(note)
                        samps = self.factory.synthesize_colored_note(
                            color_instr, freq, dur_sec, vel, ca
                        )
                        # Anti-click micro-fade (2ms in/out)
                        click_guard = min(int(0.002 * SAMPLE_RATE), len(samps) // 4)
                        for ci in range(click_guard):
                            fade = ci / max(click_guard, 1)
                            samps[ci] *= fade
                            if len(samps) - 1 - ci >= 0:
                                samps[len(samps) - 1 - ci] *= fade

                        self._mix_mono(loop_left, loop_right, samps,
                                       offset, loop_samples, pan * v_gain * 4)

            section_offset_sec += segment_duration

        # Chamber effects
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # Loop with crossfade to fill mood duration
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        # NOTE: anti-hiss + subsonic applied at master level in V8's render()
        # (inherited). Do NOT apply here — that would double-filter the signal.

        return left, right


class RadioEngineV16(RadioEngineV15):
    """In The Beginning Radio v16 -- True original V8 synthesis + expanded palette.

    Like V14 but uses the original InstrumentFactory.synthesize_colored_note()
    instead of the numpy-accelerated path. This gives the authentic V8 sound
    with V12's full instrument variety.

    - Original V8 synthesis: factory.synthesize_colored_note() (pure Python)
    - V12 density-aware tempo: 1.1x-1.7x
    - V12's 15 instrument family pools with variety enforcement
    - All 744 MIDI files
    - 537 instruments
    - Serial rendering (V8's streaming path)
    """

    MORPH_DURATION = 8.0
    FADE_IN_DURATION = 6.0
    FADE_OUT_DURATION = 10.0

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        # V12's family tracking for variety enforcement
        self._used_family_groups = set()
        self._family_groups = {
            'symphonic': {'strings', 'brass', 'woodwinds', 'sax', 'choir',
                          'symphonic_ext'},
            'rock': {'rock_guitar', 'rock_bass'},
            'electronic': {'synth_lead', 'synth_pad', 'synth_fx'},
            'world': {'world'},
            'classical': {'keys', 'pitched_perc', 'mallets'},
        }
        self._segment_count = 0

    def _choose_gm_instruments(self, midi_info, n_voices, rng):
        """Choose GM instruments from V12's expanded 15-family catalog."""
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()
        register_offsets = [-12, 0, 0, 12, 24]
        pans_pool = [-0.5, -0.2, 0.0, 0.2, 0.5]

        self._segment_count += 1
        n_total_segments = len(self.segments) if hasattr(self, 'segments') else 15
        past_halfway = self._segment_count > n_total_segments // 2

        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            if v < 3:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)
            elif underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
                underrepresented = [f for f in underrepresented if f != family]
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)

            used_families.add(family)
            for group_name, group_fams in self._family_groups.items():
                if family in group_fams:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)
            oct_offset = register_offsets[v % len(register_offsets)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            color_amount = 0.15 if oct_offset < 0 else 0.25

            voices.append({
                'gm_program': gm,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
                'family': family,
            })

        return voices


def generate_radio_v15_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v15 radio MP3 -- true original V8 synthesis + V12 tempo.

    v15 uses the original InstrumentFactory.synthesize_colored_note() from
    commit 348bf29, with V12's density-aware tempo (1.1x-1.7x). V8's 5
    instrument families, 537 instruments, serial rendering.
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV15] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV15(seed=seed, total_duration=duration)

    print(f"[{ct_now}] [RadioEngineV15] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV15] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV15] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[{ct_now}] [RadioEngineV15] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[{ct_now}] [RadioEngineV15] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[{ct_now}] [RadioEngineV15] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")
    print(f"[{ct_now}] [RadioEngineV15] Synthesis: ORIGINAL V8 factory.synthesize_colored_note (pure Python)")
    print(f"[{ct_now}] [RadioEngineV15] Instruments: v8 5-pool orchestral palette (537 synths)")
    print(f"[{ct_now}] [RadioEngineV15] Tempo range: 1.1x-1.7x (density-aware, from v12)")
    print(f"[{ct_now}] [RadioEngineV15] Render mode: SERIAL (no multiprocessing)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV15] Rendering audio (serial, original synthesis)...")
    t0 = _time.time()

    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                ct_seg = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"  [{ct_seg}] Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        sim_states = None

    use_streaming = duration > 660

    if use_streaming:
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV15] Using serial streaming renderer...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                    _time.localtime(_time.time()))
            print(f"[{ct_now}] [RadioEngineV15] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[{ct_now}] [RadioEngineV15] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV15] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[{ct_now}] [RadioEngineV15] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)
        t1 = _time.time()
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV15] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                render_to_wav(left, right, wav_path)
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV15] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[{ct_now}] [RadioEngineV15] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[{ct_now}] [RadioEngineV15] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v16_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v16 radio MP3 -- true original V8 synthesis + expanded palette.

    v16 uses the original InstrumentFactory.synthesize_colored_note() with
    V12's expanded 15-family instrument catalog and 744 MIDI files.
    V12's density-aware tempo (1.1x-1.7x). Serial rendering.
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV16] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV16(seed=seed, total_duration=duration)

    print(f"[{ct_now}] [RadioEngineV16] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV16] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV16] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[{ct_now}] [RadioEngineV16] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[{ct_now}] [RadioEngineV16] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[{ct_now}] [RadioEngineV16] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")
    print(f"[{ct_now}] [RadioEngineV16] Synthesis: ORIGINAL V8 factory.synthesize_colored_note (pure Python)")
    print(f"[{ct_now}] [RadioEngineV16] Instruments: v12 15-pool expanded palette (537 synths)")
    print(f"[{ct_now}] [RadioEngineV16] MIDI library: {len(engine.midi_lib._note_sequences)} sequences")
    print(f"[{ct_now}] [RadioEngineV16] Tempo range: 1.1x-1.7x (density-aware, from v12)")
    print(f"[{ct_now}] [RadioEngineV16] Render mode: SERIAL (no multiprocessing)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV16] Rendering audio (serial, original synthesis)...")
    t0 = _time.time()

    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                ct_seg = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"  [{ct_seg}] Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        sim_states = None

    use_streaming = duration > 660

    if use_streaming:
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV16] Using serial streaming renderer...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                    _time.localtime(_time.time()))
            print(f"[{ct_now}] [RadioEngineV16] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[{ct_now}] [RadioEngineV16] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV16] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[{ct_now}] [RadioEngineV16] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)
        t1 = _time.time()
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV16] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                render_to_wav(left, right, wav_path)
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV16] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[{ct_now}] [RadioEngineV16] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[{ct_now}] [RadioEngineV16] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v12_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v12 radio MP3 -- v8 synthesis + expanded instruments + multiprocessing.

    v12 uses v8's proven synthesis approach with v9/v10's expanded instrument/MIDI
    catalog, v11's gain staging, and multiprocessing for massive speedup.
    Tempo clamped to 1.1x-1.7x.
    """
    import tempfile
    import multiprocessing as mp

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV12] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV12(seed=seed, total_duration=duration)

    n_cores = mp.cpu_count()
    print(f"[{ct_now}] [RadioEngineV12] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV12] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV12] {len(V9_FAMILY_POOLS)} instrument family pools")
    print(f"[{ct_now}] [RadioEngineV12] {sum(len(p) for p in V9_FAMILY_POOLS.values())} unique GM programs")
    print(f"[{ct_now}] [RadioEngineV12] CPU cores available: {n_cores}")
    print(f"[{ct_now}] [RadioEngineV12] Tempo range: 1.1x-1.7x (density-aware)")
    print(f"[{ct_now}] [RadioEngineV12] Synthesis: v8 colored note (InstrumentFactory)")
    print(f"[{ct_now}] [RadioEngineV12] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[{ct_now}] [RadioEngineV12] V12: v8 synthesis + expanded palette + multiprocessing")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[{ct_now}] [RadioEngineV12] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[{ct_now}] [RadioEngineV12] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV12] Rendering audio...")
    t0 = _time.time()

    # Import simulator
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                ct_seg = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"  [{ct_seg}] Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}, "
                      f"density={state['particles'] + state['atoms']*2 + state['molecules']*3 + state['cells']*5}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    use_streaming = duration > 660

    if use_streaming:
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV12] Using PARALLEL streaming renderer ({n_cores} cores)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming_parallel(wf, sim_states)
            t1 = _time.time()
            ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                    _time.localtime(_time.time()))
            print(f"[{ct_now}] [RadioEngineV12] Rendered {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
            print(f"[{ct_now}] [RadioEngineV12] Speedup: {n_cores}x potential ({n_cores} cores)")

            if output_path.endswith('.mp3'):
                print(f"[{ct_now}] [RadioEngineV12] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV12] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[{ct_now}] [RadioEngineV12] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV12] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
        print(f"[{ct_now}] [RadioEngineV12] Family groups used: {sorted(engine._used_family_groups)}")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[{ct_now}] [RadioEngineV12] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[{ct_now}] [RadioEngineV12] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                        _time.localtime(_time.time()))
                print(f"[{ct_now}] [RadioEngineV12] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[{ct_now}] [RadioEngineV12] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV12] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v11_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v11 radio MP3 file with comprehensive audio quality fixes.

    v11 features: per-voice RMS normalization, master bus soft-knee limiting,
    separated pan/gain mixing, inter-voice consonance, bar-aligned rendering,
    orchestral role assignment, reduced reverb resonance, plus all v10 features.
    """
    import tempfile

    print(f"[RadioEngineV11] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV11(seed=seed, total_duration=duration)

    print(f"[RadioEngineV11] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngineV11] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngineV11] {len(V9_FAMILY_POOLS)} instrument family pools")
    print(f"[RadioEngineV11] {sum(len(p) for p in V9_FAMILY_POOLS.values())} unique GM programs")
    print(f"[RadioEngineV11] {len(GM_TIMBRE_PROFILES)} GM timbre profiles")
    print(f"[RadioEngineV11] Tempo range: 1.2x-1.8x (flat)")
    print(f"[RadioEngineV11] Morph duration: {engine.MORPH_DURATION}s")
    print(f"[RadioEngineV11] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngineV11] TTS transitions at segments: {sorted(engine.tts_transitions)}")
    print(f"[RadioEngineV11] V11 fixes: gain staging, consonance, bar grid, orchestral roles")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[RadioEngineV11] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[RadioEngineV11] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")

    print(f"[RadioEngineV11] Rendering audio...")
    t0 = _time.time()

    # Import simulator
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                print(f"  Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}, "
                      f"density={state['particles'] + state['atoms']*2 + state['molecules']*3 + state['cells']*5}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    use_streaming = duration > 660

    if use_streaming:
        print(f"[RadioEngineV11] Using streaming renderer (low memory)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            print(f"[RadioEngineV11] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
            print(f"[RadioEngineV11] Family groups used: {sorted(engine._used_family_groups)}")

            if output_path.endswith('.mp3'):
                print(f"[RadioEngineV11] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV11] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[RadioEngineV11] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        print(f"[RadioEngineV11] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
        print(f"[RadioEngineV11] Family groups used: {sorted(engine._used_family_groups)}")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[RadioEngineV11] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[RadioEngineV11] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV11] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[RadioEngineV11] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV11] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v10_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v10 radio MP3 file with GM-timbre-aware synthesis.

    v10 features: tempo 1.2x-1.8x, GM-specific timbres, 85% orchestral
    layering, 4-6 voices, 8s morph fades, plus all v9 features.
    """
    import tempfile

    print(f"[RadioEngineV10] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV10(seed=seed, total_duration=duration)

    print(f"[RadioEngineV10] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngineV10] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngineV10] {len(V9_FAMILY_POOLS)} instrument family pools")
    print(f"[RadioEngineV10] {sum(len(p) for p in V9_FAMILY_POOLS.values())} unique GM programs")
    print(f"[RadioEngineV10] {len(GM_TIMBRE_PROFILES)} GM timbre profiles")
    print(f"[RadioEngineV10] Tempo range: 1.2x-1.8x (flat)")
    print(f"[RadioEngineV10] Morph duration: {engine.MORPH_DURATION}s")
    print(f"[RadioEngineV10] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngineV10] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[RadioEngineV10] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[RadioEngineV10] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")

    print(f"[RadioEngineV10] Rendering audio...")
    t0 = _time.time()

    # Import simulator
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                print(f"  Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}, "
                      f"density={state['particles'] + state['atoms']*2 + state['molecules']*3 + state['cells']*5}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    use_streaming = duration > 660

    if use_streaming:
        print(f"[RadioEngineV10] Using streaming renderer (low memory)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            print(f"[RadioEngineV10] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
            print(f"[RadioEngineV10] Family groups used: {sorted(engine._used_family_groups)}")

            if output_path.endswith('.mp3'):
                print(f"[RadioEngineV10] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV10] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[RadioEngineV10] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        print(f"[RadioEngineV10] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
        print(f"[RadioEngineV10] Family groups used: {sorted(engine._used_family_groups)}")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[RadioEngineV10] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[RadioEngineV10] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV10] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[RadioEngineV10] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV10] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v9_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v9 radio MP3 file with expanded instruments.

    v9 features: ~50 new instruments, 15 family pools, density-aware tempo,
    family variety enforcement, plus all v8 features.
    """
    import tempfile

    print(f"[RadioEngineV9] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV9(seed=seed, total_duration=duration)

    print(f"[RadioEngineV9] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngineV9] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngineV9] {len(V9_FAMILY_POOLS)} instrument family pools")
    print(f"[RadioEngineV9] {sum(len(p) for p in V9_FAMILY_POOLS.values())} unique GM programs")
    print(f"[RadioEngineV9] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngineV9] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    # Count time signature distribution
    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[RadioEngineV9] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[RadioEngineV9] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")

    print(f"[RadioEngineV9] Rendering audio...")
    t0 = _time.time()

    # Import simulator for real simulation data
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                print(f"  Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}, "
                      f"density={state['particles'] + state['atoms']*2 + state['molecules']*3 + state['cells']*5}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    # Use streaming renderer for long durations
    use_streaming = duration > 660

    if use_streaming:
        print(f"[RadioEngineV9] Using streaming renderer (low memory)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            print(f"[RadioEngineV9] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
            print(f"[RadioEngineV9] Family groups used: {sorted(engine._used_family_groups)}")

            if output_path.endswith('.mp3'):
                print(f"[RadioEngineV9] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV9] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[RadioEngineV9] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        print(f"[RadioEngineV9] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")
        print(f"[RadioEngineV9] Family groups used: {sorted(engine._used_family_groups)}")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[RadioEngineV9] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[RadioEngineV9] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV9] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[RadioEngineV9] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV9] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v8_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v8 radio MP3 file with all enhancements.

    v8 features: orchestral layering, anti-hiss, subsonic removal,
    smoother notes, 70% simple time signatures, note quantization.
    """
    import tempfile

    print(f"[RadioEngineV8] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngineV8(seed=seed, total_duration=duration)

    print(f"[RadioEngineV8] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngineV8] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngineV8] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngineV8] TTS transitions at segments: {sorted(engine.tts_transitions)}")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)

    # Count time signature distribution
    simple_count = sum(1 for s in engine.segments
                       if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
    compound_count = sum(1 for s in engine.segments
                         if s.get('time_sig_override') in COMPOUND_TIME_SIGS)
    complex_count = sum(1 for s in engine.segments
                        if s.get('time_sig_override') in COMPLEX_TIME_SIGS)
    print(f"[RadioEngineV8] {n_segments} mood segments (avg {avg_dur:.0f}s)")
    print(f"[RadioEngineV8] Time signatures: {simple_count} simple, "
          f"{compound_count} compound, {complex_count} complex")

    print(f"[RadioEngineV8] Rendering audio...")
    t0 = _time.time()

    # Import simulator for real simulation data
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        sim_states = []
        total_ticks = int(duration * 50)
        ticks_per_segment = max(1, total_ticks // n_segments)
        for seg in range(n_segments):
            for _ in range(ticks_per_segment):
                universe.step()
            state = {
                'temperature': universe.quantum_field.temperature,
                'particles': len(universe.quantum_field.particles),
                'atoms': len(universe.atomic_system.atoms) if universe.atomic_system else 0,
                'molecules': len(universe.chemical_system.molecules) if universe.chemical_system else 0,
                'cells': len(universe.biosphere.cells) if universe.biosphere else 0,
                'generation': universe.biosphere.generation if universe.biosphere else 0,
                'epoch': universe.current_epoch_name,
            }
            sim_states.append(state)
            if seg % 3 == 0:
                print(f"  Sim segment {seg+1}/{n_segments}: epoch={state['epoch']}, "
                      f"T={state['temperature']:.0f}, particles={state['particles']}")
    except Exception as e:
        print(f"  [Warning] Could not run simulator: {e}")
        print(f"  Using synthetic simulation data instead.")
        sim_states = None

    # Use streaming renderer for long durations
    use_streaming = duration > 660

    if use_streaming:
        print(f"[RadioEngineV8] Using streaming renderer (low memory)...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                total_written = engine.render_streaming(wf, sim_states)
            t1 = _time.time()
            print(f"[RadioEngineV8] Streamed {total_written/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

            if output_path.endswith('.mp3'):
                print(f"[RadioEngineV8] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV8] Saved: {output_path}")
            else:
                import shutil
                shutil.move(wav_path, output_path)
                wav_path = None
                print(f"[RadioEngineV8] Saved: {output_path}")
        finally:
            if wav_path:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
    else:
        left, right = engine.render(sim_states)

        t1 = _time.time()
        print(f"[RadioEngineV8] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

        if output_path.endswith('.mp3'):
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                print(f"[RadioEngineV8] Writing WAV ({len(left)*4/1048576:.1f} MB)...")
                render_to_wav(left, right, wav_path)
                print(f"[RadioEngineV8] Converting to MP3...")
                wav_to_mp3(wav_path, output_path)
                print(f"[RadioEngineV8] Saved: {output_path}")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            render_to_wav(left, right, output_path)
            print(f"[RadioEngineV8] Saved: {output_path}")

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV8] File size: {file_size/1048576:.1f} MB")
    return output_path


# ---------------------------------------------------------------------------
# V18 RADIO ENGINE -- Clean mixing + tighter tempo (1.1x-1.45x)
# ---------------------------------------------------------------------------
#
# V18 addresses the "radio static" artifacts reported in V15/V17 renders by
# applying three fixes from V11 to V15's synthesis path:
#   1. Separate gain/pan in _mix_mono (V11 fix — no more gain-overloaded pan)
#   2. Quality-gated instrument selection (skip noise_perc for melodic voices)
#   3. Soft-knee limiting on loop buffer to prevent clipping
#   4. Longer anti-click fades (5ms vs 2ms)
#   5. Tempo clamped to 1.1x-1.45x (user preference: narrower range)


class RadioEngineV18(RadioEngineV15):
    """In The Beginning Radio v18 -- V15 synthesis with clean mixing fixes.

    Uses V15's original V8 synthesis (factory.synthesize_colored_note) with:
    - Tempo clamped to 1.1x-1.45x (tighter than V15's 1.1x-1.7x)
    - Separate gain and pan in mixing (from V11)
    - Quality-gated instruments: noise_perc excluded from melodic voices
    - Soft-knee limiting on loop buffer before crossfade fill
    - 5ms anti-click fades (up from V15's 2ms)
    - V8's 5 instrument families (strings, brass, woodwinds, keys, pitched_perc)
    - 537 instruments, serial rendering
    """

    def _compute_tempo_multiplier(self, sim_state):
        """Tempo clamped to 1.1x-1.45x (user preference for final version)."""
        if not sim_state:
            return 1.28  # neutral default (midpoint)
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        base = 1.1 + 0.35 * (int(h, 16) / 0xFFFFFFFF)  # 1.1-1.45 range
        # Density-aware capping
        particles = sim_state.get('particles', 0)
        atoms = sim_state.get('atoms', 0)
        molecules = sim_state.get('molecules', 0)
        cells = sim_state.get('cells', 0)
        density = particles + atoms * 2 + molecules * 3 + cells * 5
        if density > 200:
            base = min(base, 1.35)
        if density > 500:
            base = min(base, 1.25)
        return base

    @staticmethod
    def _mix_mono_clean(left, right, samples, offset, total_samples, pan, gain):
        """Mix mono samples with SEPARATED pan and gain (V11 fix).

        Pan law: equal-power cosine/sine panning.
        Pan is clamped to [-1, 1], gain is a separate scalar.
        """
        pan = max(-1.0, min(1.0, pan))
        l_gain = math.cos((pan + 1) * math.pi / 4) * gain
        r_gain = math.sin((pan + 1) * math.pi / 4) * gain
        n = len(samples)
        end = min(offset + n, total_samples)
        start = max(offset, 0)
        for i in range(start, end):
            si = i - offset
            if 0 <= si < n:
                left[i] += samples[si] * l_gain
                right[i] += samples[si] * r_gain

    @staticmethod
    def _is_noise_instrument(instr):
        """Check if an instrument is noise_perc (static-prone)."""
        harmonics = instr.get('harmonics', [])
        if harmonics and isinstance(harmonics[0], (list, tuple)):
            if isinstance(harmonics[0][0], str) and harmonics[0][0] == 'noise':
                return True
        return False

    @staticmethod
    def _soft_knee_limit(buf, knee=0.75):
        """Soft-knee limiting: transparent below knee, tanh saturation above."""
        for i in range(len(buf)):
            x = buf[i]
            ax = abs(x)
            if ax > knee:
                sign = 1.0 if x >= 0 else -1.0
                excess = ax - knee
                compressed = knee + (1.0 - knee) * math.tanh(excess / (1.0 - knee))
                buf[i] = sign * compressed

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """V18 render: V15 synthesis + clean mixing + static prevention."""
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = beats_per_bar * beat_dur * quarter_per_beat

        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )

        n_voices = getattr(mood, 'n_voices', rng.randint(2, 4))
        n_voices = clamp(n_voices, 2, 4)
        voice_configs = self._choose_gm_instruments(midi_info, n_voices, rng)

        register_offsets = [-12, 0, 0, 12, 24]
        for v_idx, vc in enumerate(voice_configs):
            vc['octave_offset'] = register_offsets[v_idx % len(register_offsets)]

        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # V18: voice gain sized for clean headroom (no * 4 overload)
        voice_gain = 0.25 / max(n_voices, 1)
        section_offset_sec = 0.0

        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            is_solo_section = rng.random() < 0.25
            if is_solo_section:
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                active_voices = list(range(n_voices))

            # V18: quality-gate instruments — skip noise_perc for melodic voices
            voice_instruments = []
            for _ in voice_configs:
                candidate = rng.choice(self.instruments)
                # Retry up to 5 times to avoid noise_perc instruments
                retries = 0
                while self._is_noise_instrument(candidate) and retries < 5:
                    candidate = rng.choice(self.instruments)
                    retries += 1
                voice_instruments.append(candidate)

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc['pan']
                ca = vc['color_amount']
                v_chord_size = vc['chord_size']

                v_gain = voice_gain * (1.5 if is_solo_section else 1.0)

                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * v_gain
                            loop_right[pos] += fr[i] * v_gain
                    continue

                color_instr = voice_instruments[v_idx]

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    for note in voice_chord:
                        freq = mtof(note)
                        samps = self.factory.synthesize_colored_note(
                            color_instr, freq, dur_sec, vel, ca
                        )
                        # V18: 5ms anti-click fades (up from 2ms)
                        click_guard = min(int(0.005 * SAMPLE_RATE), len(samps) // 4)
                        for ci in range(click_guard):
                            fade = ci / max(click_guard, 1)
                            samps[ci] *= fade
                            if len(samps) - 1 - ci >= 0:
                                samps[len(samps) - 1 - ci] *= fade

                        # V18: clean mix with separated gain/pan
                        self._mix_mono_clean(loop_left, loop_right, samps,
                                             offset, loop_samples, pan, v_gain * 0.25)

            section_offset_sec += segment_duration

        # Chamber effects
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # V18: soft-knee limiting on loop buffer to prevent clipping
        self._soft_knee_limit(loop_left, knee=0.75)
        self._soft_knee_limit(loop_right, knee=0.75)

        # Loop with crossfade to fill mood duration
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right


class RadioEngineV18Orchestra(RadioEngineV18):
    """V18 Orchestra -- expanded 15-family palette with character preservation.

    Uses V18's clean mixing and 1.1x-1.45x tempo, with V12's expanded instrument
    families (15 pools, 744 MIDI files). Enforces family variety across the render
    and preserves original instrument character (xylophone sounds like xylophone,
    strings sound like strings, horns sound like horns).

    Key differences from V18 base:
    - 15 instrument family pools (vs V18's 5)
    - 744 MIDI files from 26 composers
    - Family variety enforcement: tracks used families, biases toward under-used
    - Higher color_amount for character preservation (instruments retain identity)
    """

    MORPH_DURATION = 8.0
    FADE_IN_DURATION = 6.0
    FADE_OUT_DURATION = 10.0

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        self._used_family_groups = set()
        self._family_groups = {
            'symphonic': {'strings', 'brass', 'woodwinds', 'sax', 'choir',
                          'symphonic'},
            'keys_perc': {'keys', 'pitched_perc', 'mallets', 'organ_accordion'},
            'world_ethnic': {'world', 'ethnic_perc', 'guitar_plucked'},
            'electronic': {'synth_pad', 'bass', 'sfx'},
            'classical': {'keys', 'pitched_perc', 'mallets'},
        }
        self._segment_count = 0

    def _choose_gm_instruments(self, midi_info, n_voices, rng):
        """Choose instruments from all 15 family pools with variety enforcement.

        Past halfway through the render, biases selection toward under-represented
        family groups so the output covers the full orchestral palette.
        """
        families = list(V9_FAMILY_POOLS.keys())
        rng.shuffle(families)

        voices = []
        used_families = set()

        programs = midi_info.get('programs', set())
        offsets_pool = [-12, 0, 0, 12, 24]
        pans_pool = [-0.6, -0.2, 0.2, 0.6]

        self._segment_count += 1
        past_halfway = self._segment_count > len(self.segments) // 2

        # Gather under-represented families
        underrepresented = []
        if past_halfway:
            for group_name, group_families in self._family_groups.items():
                if group_name not in self._used_family_groups:
                    underrepresented.extend(
                        f for f in group_families if f in V9_FAMILY_POOLS)

        for v in range(n_voices):
            if underrepresented and rng.random() < 0.6:
                family = rng.choice(underrepresented)
            else:
                available = [f for f in families if f not in used_families]
                if not available:
                    available = families
                family = rng.choice(available)
            used_families.add(family)

            for group_name, group_families in self._family_groups.items():
                if family in group_families:
                    self._used_family_groups.add(group_name)

            pool = V9_FAMILY_POOLS[family]
            gm = rng.choice(pool)

            oct_offset = offsets_pool[v % len(offsets_pool)]
            pan = pans_pool[v % len(pans_pool)]
            chord_size = rng.randint(2, 4)
            # V18 Orchestra: higher color_amount (0.35-0.55) to preserve
            # instrument character — xylophone stays xylophone, not generic synth
            color_amount = rng.uniform(0.35, 0.55)

            voices.append({
                'gm_program': gm,
                'family': family,
                'octave_offset': oct_offset,
                'pan': pan,
                'chord_size': chord_size,
                'color_amount': color_amount,
            })

        return voices


def generate_radio_v18_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v18 radio MP3 -- V15 synthesis with clean mixing fixes.

    v18 uses V15's original V8 synthesis with:
    - Tempo: 1.1x-1.45x (user preference)
    - Clean mixing: separate gain/pan, no noise_perc in melodic voices
    - Soft-knee limiting to prevent clipping/static
    - V8's 5 instrument families, serial rendering
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    engine = RadioEngineV18(seed=seed, total_duration=duration)
    print(f"[{ct_now}] [RadioEngineV18] Initialized (seed={seed}, duration={duration}s)")
    print(f"[{ct_now}] [RadioEngineV18] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV18] Synthesis: ORIGINAL V8 factory.synthesize_colored_note (pure Python)")
    print(f"[{ct_now}] [RadioEngineV18] Instruments: v8 5-pool orchestral palette (537 synths)")
    print(f"[{ct_now}] [RadioEngineV18] Tempo range: 1.1x-1.45x (user preference)")
    print(f"[{ct_now}] [RadioEngineV18] Mixing: V11-style clean gain/pan + soft-knee limiting")
    print(f"[{ct_now}] [RadioEngineV18] Static prevention: noise_perc excluded from melodic voices")

    n_segments = len(engine.segments)
    avg_dur = sum(s[1] for s in engine.segments) / max(n_segments, 1)
    print(f"[{ct_now}] [RadioEngineV18] {n_segments} mood segments (avg {avg_dur:.0f}s)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV18] Rendering audio (serial, original synthesis)...")

    t0 = _time.time()
    left, right = engine.render()
    t1 = _time.time()
    print(f"[{ct_now}] [RadioEngineV18] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

    if output_path.endswith('.mp3'):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            render_to_wav(left, right, wav_path)
            wav_to_mp3(wav_path, output_path)
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass
    else:
        render_to_wav(left, right, output_path)

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV18] File size: {file_size/1048576:.1f} MB")
    return output_path


def generate_radio_v18_orchestra_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v18 orchestra MP3 -- expanded palette with character preservation.

    v18 orchestra uses 15 instrument families, 744 MIDI files, with wider variety
    enforcement and higher color_amount to preserve instrument character identity.
    """
    import tempfile

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    engine = RadioEngineV18Orchestra(seed=seed, total_duration=duration)
    print(f"[{ct_now}] [RadioEngineV18Orchestra] Initialized (seed={seed}, duration={duration}s)")
    print(f"[{ct_now}] [RadioEngineV18Orchestra] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV18Orchestra] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV18Orchestra] Instruments: 15-pool expanded palette")
    print(f"[{ct_now}] [RadioEngineV18Orchestra] Tempo range: 1.1x-1.45x")
    print(f"[{ct_now}] [RadioEngineV18Orchestra] Character preservation: color_amount 0.35-0.55")

    n_segments = len(engine.segments)
    avg_dur = sum(s[1] for s in engine.segments) / max(n_segments, 1)
    print(f"[{ct_now}] [RadioEngineV18Orchestra] {n_segments} mood segments (avg {avg_dur:.0f}s)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV18Orchestra] Rendering audio...")

    t0 = _time.time()
    left, right = engine.render()
    t1 = _time.time()
    print(f"[RadioEngineV18Orchestra] Rendered {len(left)/SAMPLE_RATE:.1f}s in {t1-t0:.1f}s")

    if output_path.endswith('.mp3'):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        try:
            render_to_wav(left, right, wav_path)
            wav_to_mp3(wav_path, output_path)
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass
    else:
        render_to_wav(left, right, output_path)

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"[RadioEngineV18Orchestra] File size: {file_size/1048576:.1f} MB")
    return output_path


# ---------------------------------------------------------------------------
# V20 RADIO ENGINE -- Volume-normalized, expanded palette, solo moods
# ---------------------------------------------------------------------------

def _master_normalize(left, right, target_db=-1.0):
    """Normalize stereo signal to target peak dB.

    Scans for peak amplitude across both channels, then scales so the
    peak matches target_db (default -1 dB = 0.891).
    """
    peak = 0.0
    for i in range(len(left)):
        al = abs(left[i])
        ar = abs(right[i])
        if al > peak:
            peak = al
        if ar > peak:
            peak = ar
    if peak < 1e-10:
        return left, right
    target = 10 ** (target_db / 20.0)  # -1dB = 0.891
    scale = target / peak
    for i in range(len(left)):
        left[i] *= scale
        right[i] *= scale
    return left, right


def _lookahead_limiter(left, right, threshold=0.92, attack_ms=5.0, release_ms=50.0):
    """Lookahead limiter to catch transient spikes without audible pumping.

    Uses a lookahead buffer to anticipate peaks and smoothly reduce gain
    before the transient arrives. This prevents the pops and static bursts
    the user reported.
    """
    n = len(left)
    lookahead = int(attack_ms * SAMPLE_RATE / 1000)
    release_coeff = math.exp(-1.0 / (release_ms * SAMPLE_RATE / 1000))
    gain = 1.0

    for i in range(n):
        # Look ahead to find upcoming peak
        look_end = min(i + lookahead, n)
        future_peak = 0.0
        for j in range(i, look_end):
            al = abs(left[j])
            ar = abs(right[j])
            if al > future_peak:
                future_peak = al
            if ar > future_peak:
                future_peak = ar

        # Also check current sample
        current_peak = max(abs(left[i]), abs(right[i]))
        peak = max(future_peak, current_peak)

        if peak > threshold:
            target_gain = threshold / peak
        else:
            target_gain = 1.0

        # Smooth gain changes
        if target_gain < gain:
            gain = target_gain  # instant attack
        else:
            gain = gain * release_coeff + target_gain * (1.0 - release_coeff)

        left[i] *= gain
        right[i] *= gain

    return left, right


class RadioEngineV20(RadioEngineV18Orchestra):
    """In The Beginning Radio v20 -- Volume-normalized, expanded palette, solo moods.

    Improvements over V18 Orchestra:
    - Fixed gain staging: removed double 0.25 attenuation on voice gain
    - Master normalization to -1dB peak after all rendering
    - Lookahead limiter to catch transient spikes without audible pumping
    - 10-20% solo instrument moods: single instrument plays sampled arrangement
      directly (no chord building, no arpeggios), giving listener a reset
    - FluidSynth integration with system FluidR3_GM.sf2 SoundFont
    - Multi-TTS: flite, festival, pico2wave in addition to espeak-ng
    - All 15 instrument families, 744+ MIDI files
    """

    def __init__(self, seed=42, total_duration=1800.0):
        super().__init__(seed=seed, total_duration=total_duration)
        # TTSEngine now handles multi-engine detection internally
        self._tts_engines = self.tts._available_engines

    def _render_segment(self, mood, kits, n_samples, sim_state):
        """V20 render: V18 synthesis + fixed gain + solo mood support."""
        rng = mood.rng

        # 10-20% chance of solo instrument mood
        solo_mood = rng.random() < 0.15

        if solo_mood:
            return self._render_solo_segment(mood, kits, n_samples, sim_state)

        # Standard rendering with FIXED gain staging
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        root = mood.root

        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = beats_per_bar * beat_dur * quarter_per_beat

        loop_bars = rng.randint(4, 12)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, beats_per_bar
            )

        n_voices = getattr(mood, 'n_voices', rng.randint(2, 4))
        n_voices = clamp(n_voices, 2, 4)
        voice_configs = self._choose_gm_instruments(midi_info, n_voices, rng)

        register_offsets = [-12, 0, 0, 12, 24]
        for v_idx, vc in enumerate(voice_configs):
            vc['octave_offset'] = register_offsets[v_idx % len(register_offsets)]

        chord_notes = []
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            chord = self._build_chord_from_note(
                midi_note, root, mood.scale_name, mood.scale,
                n_notes=rng.randint(2, 4), rng=rng
            )
            chord_notes.append((t_sec, chord, dur_sec, vel))

        rondo = self._build_rondo_sections(
            chord_notes, root, mood.scale_name, mood.scale,
            segment_duration, rng
        )

        rondo_duration = segment_duration * len(rondo)
        loop_samples = int(rondo_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # V20 FIX: voice gain 0.35/n_voices (was 0.25/n_voices)
        # and mix gain 1.0 (was 0.25) — eliminates the -30dB attenuation
        voice_gain = 0.35 / max(n_voices, 1)
        section_offset_sec = 0.0

        fluid_rendered = None
        if HAS_FLUIDSYNTH and midi_info.get('path'):
            primary_gm = voice_configs[0]['gm_program']
            fluid_rendered = MidiLibrary.render_fluidsynth(
                midi_info['path'], primary_gm,
                tempo_factor=tempo_mult,
                start_tick=midi_info.get('start_tick', 0),
                end_tick=midi_info.get('end_tick')
            )

        for sec_idx, (label, section_notes) in enumerate(rondo):
            sec_start = int(section_offset_sec * SAMPLE_RATE)

            is_solo_section = rng.random() < 0.25
            if is_solo_section:
                active_voices = [rng.randint(0, n_voices - 1)]
            else:
                active_voices = list(range(n_voices))

            voice_instruments = []
            for _ in voice_configs:
                candidate = rng.choice(self.instruments)
                retries = 0
                while self._is_noise_instrument(candidate) and retries < 5:
                    candidate = rng.choice(self.instruments)
                    retries += 1
                voice_instruments.append(candidate)

            for v_idx in active_voices:
                vc = voice_configs[v_idx]
                oct_off = vc['octave_offset']
                pan = vc['pan']
                ca = vc['color_amount']
                v_chord_size = vc['chord_size']

                v_gain = voice_gain * (1.5 if is_solo_section else 1.0)

                if (v_idx == 0 and fluid_rendered is not None
                        and label == 'A' and sec_idx == 0):
                    fl, fr = fluid_rendered
                    fl_n = min(len(fl), loop_samples - sec_start)
                    for i in range(fl_n):
                        pos = sec_start + i
                        if 0 <= pos < loop_samples:
                            loop_left[pos] += fl[i] * v_gain
                            loop_right[pos] += fr[i] * v_gain
                    continue

                color_instr = voice_instruments[v_idx]

                for t_sec, chord, dur_sec, vel in section_notes:
                    offset = sec_start + int(t_sec * SAMPLE_RATE)
                    if offset >= loop_samples:
                        continue

                    voice_chord = chord[:v_chord_size]
                    voice_chord = [clamp(n + oct_off, 24, 108)
                                   for n in voice_chord]
                    voice_chord = [self.midi_lib._snap_to_scale(n, root, mood.scale)
                                   for n in voice_chord]

                    for note in voice_chord:
                        freq = mtof(note)
                        samps = self.factory.synthesize_colored_note(
                            color_instr, freq, dur_sec, vel, ca
                        )
                        click_guard = min(int(0.005 * SAMPLE_RATE), len(samps) // 4)
                        for ci in range(click_guard):
                            fade = ci / max(click_guard, 1)
                            samps[ci] *= fade
                            if len(samps) - 1 - ci >= 0:
                                samps[len(samps) - 1 - ci] *= fade

                        # V20 FIX: mix gain 1.0 (not 0.25) — gain is already in v_gain
                        self._mix_mono_clean(loop_left, loop_right, samps,
                                             offset, loop_samples, pan, v_gain)

            section_offset_sec += segment_duration

        # Chamber effects
        if rng.random() < 0.70:
            loop_left = self.smoother.apply_early_reflections(loop_left)
            loop_right = self.smoother.apply_early_reflections(loop_right)
        if rng.random() < 0.60:
            loop_left = self.smoother.apply_reverb(loop_left)
            loop_right = self.smoother.apply_reverb(loop_right)
        if rng.random() < 0.40:
            loop_left = self.smoother.apply_chorus(loop_left)
            loop_right = self.smoother.apply_chorus(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 8000)
        loop_right = self.smoother.apply_lowpass(loop_right, 8000)

        # V20: per-segment soft-knee at 0.85 (gentler than V18's 0.75)
        self._soft_knee_limit(loop_left, knee=0.85)
        self._soft_knee_limit(loop_right, knee=0.85)

        # Loop with crossfade to fill mood duration
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right

    def _render_solo_segment(self, mood, kits, n_samples, sim_state):
        """Render a solo instrument mood: single instrument, sampled arrangement.

        Picks one instrument, plays the MIDI-sampled note sequence directly
        without chord building, arpeggios, or embellishments. Applies normal
        coloring and note-bending. Gives the listener's brain a reset.
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        root = mood.root

        tempo_mult = self._compute_tempo_multiplier(sim_state)
        effective_tempo = min(tempo * tempo_mult, 360)

        loop_bars = rng.randint(4, 8)
        bars_result = self.midi_lib.sample_bars_seeded(
            sim_state, loop_bars, effective_tempo, mood.beats_per_bar,
            root=root, scale=mood.scale, rng=rng
        )
        midi_notes, segment_duration, midi_info = bars_result

        if segment_duration <= 0 or not midi_notes:
            return left, right

        ts_key = getattr(mood, '_v8_time_sig', mood.time_sig)
        ts_info = TIME_SIGNATURES.get(ts_key, TIME_SIGNATURES.get('4/4'))
        beat_dur = 60.0 / effective_tempo
        quarter_per_beat = 4.0 / ts_info['unit'] if isinstance(ts_info, dict) else 1.0
        bar_duration_sec = mood.beats_per_bar * beat_dur * quarter_per_beat

        if bar_duration_sec > 0:
            midi_notes = self.quantizer.fit_notes_to_bars(
                midi_notes, loop_bars, bar_duration_sec, mood.beats_per_bar
            )

        # Pick ONE instrument — avoid noise instruments
        solo_instr = rng.choice(self.instruments)
        retries = 0
        while self._is_noise_instrument(solo_instr) and retries < 10:
            solo_instr = rng.choice(self.instruments)
            retries += 1

        # Random pan position and moderate color amount
        pan = rng.uniform(-0.3, 0.3)  # centered-ish
        color_amount = rng.uniform(0.35, 0.55)

        # Solo voice gain — louder since it's alone
        solo_gain = 0.55

        loop_samples = int(segment_duration * SAMPLE_RATE)
        if loop_samples <= 0:
            return left, right

        loop_left = [0.0] * loop_samples
        loop_right = [0.0] * loop_samples

        # Play notes directly — no chord building, no arpeggios
        for t_sec, midi_note, dur_sec, vel in midi_notes:
            offset = int(t_sec * SAMPLE_RATE)
            if offset >= loop_samples:
                continue

            # Snap to scale but keep as single note
            note = self.midi_lib._snap_to_scale(midi_note, root, mood.scale)
            note = clamp(note, 36, 96)  # comfortable range for solo
            freq = mtof(note)

            samps = self.factory.synthesize_colored_note(
                solo_instr, freq, dur_sec, vel, color_amount
            )
            # Anti-click fades
            click_guard = min(int(0.005 * SAMPLE_RATE), len(samps) // 4)
            for ci in range(click_guard):
                fade = ci / max(click_guard, 1)
                samps[ci] *= fade
                if len(samps) - 1 - ci >= 0:
                    samps[len(samps) - 1 - ci] *= fade

            self._mix_mono_clean(loop_left, loop_right, samps,
                                 offset, loop_samples, pan, solo_gain)

        # Gentle reverb for solo — sounds nice in a room
        loop_left = self.smoother.apply_reverb(loop_left)
        loop_right = self.smoother.apply_reverb(loop_right)

        # DC offset removal
        if loop_left:
            dc_l = sum(loop_left) / len(loop_left)
            dc_r = sum(loop_right) / len(loop_right)
            if abs(dc_l) > 0.001 or abs(dc_r) > 0.001:
                loop_left = [s - dc_l for s in loop_left]
                loop_right = [s - dc_r for s in loop_right]

        loop_left = self.smoother.apply_lowpass(loop_left, 7000)
        loop_right = self.smoother.apply_lowpass(loop_right, 7000)
        self._soft_knee_limit(loop_left, knee=0.85)
        self._soft_knee_limit(loop_right, knee=0.85)

        # Fill mood duration via looping
        xfade = min(int(rng.uniform(2.0, 4.0) * SAMPLE_RATE),
                     loop_samples // 3)
        pos = 0
        while pos < n_samples:
            remaining = n_samples - pos
            chunk = min(loop_samples, remaining)
            for i in range(chunk):
                fade = 1.0
                if pos > 0 and i < xfade:
                    fade = 0.5 - 0.5 * math.cos(math.pi * i / max(xfade, 1))
                dist_to_end = chunk - i
                if dist_to_end < xfade and pos + chunk < n_samples:
                    fade *= 0.5 + 0.5 * math.cos(math.pi * (1 - dist_to_end / max(xfade, 1)))
                left[pos + i] += loop_left[i] * fade
                right[pos + i] += loop_right[i] * fade
            pos += loop_samples - xfade

        return left, right

    def render(self, sim_states=None):
        """Override render to add V20 master normalization + lookahead limiter."""
        # Call V8's render via MRO (includes V18's segment rendering)
        left, right = super().render(sim_states)

        # V20: master normalization to -1dB peak
        left, right = _master_normalize(left, right, target_db=-1.0)

        # V20: lookahead limiter to catch any remaining transients
        left, right = _lookahead_limiter(left, right, threshold=0.92)

        return left, right


def generate_radio_v20_mp3(output_path, duration=1800.0, seed=42):
    """Generate the v20 radio MP3 -- volume-normalized, expanded palette, solo moods.

    Memory-safe: renders to WAV segment-by-segment (streaming), then uses ffmpeg
    for normalization and MP3 conversion. Avoids holding full 30-minute stereo
    buffer in memory (~2.5GB), enabling renders within gVisor container limits.

    v20 fixes the volume issues from v18:
    - Proper gain staging (no double 0.25 attenuation)
    - Master normalization to -1dB peak (via ffmpeg loudnorm)
    - Lookahead limiter for transient spike prevention
    - 10-20% solo instrument moods for variety
    - FluidSynth with FluidR3_GM.sf2
    - Multi-TTS: espeak-ng + flite + festival + pico2wave
    """
    import tempfile, gc

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    engine = RadioEngineV20(seed=seed, total_duration=duration)
    print(f"[{ct_now}] [RadioEngineV20] Initialized (seed={seed}, duration={duration}s)")
    print(f"[{ct_now}] [RadioEngineV20] {len(engine.instruments)} instruments loaded")
    print(f"[{ct_now}] [RadioEngineV20] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[{ct_now}] [RadioEngineV20] FluidSynth: {'YES' if HAS_FLUIDSYNTH else 'NO'}")
    print(f"[{ct_now}] [RadioEngineV20] TTS engines: {engine._tts_engines}")
    print(f"[{ct_now}] [RadioEngineV20] Volume: master normalize -1dB + lookahead limiter")
    print(f"[{ct_now}] [RadioEngineV20] Solo moods: 15% chance per segment")
    print(f"[{ct_now}] [RadioEngineV20] Mode: STREAMING (memory-safe)")

    n_segments = len(engine.segments)
    avg_dur = sum(s['duration'] for s in engine.segments) / max(n_segments, 1)
    print(f"[{ct_now}] [RadioEngineV20] {n_segments} mood segments (avg {avg_dur:.0f}s)")

    ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                            _time.localtime(_time.time()))
    print(f"[{ct_now}] [RadioEngineV20] Rendering audio...")

    t0 = _time.time()

    # Streaming render: write segments to WAV on disk, then normalize with ffmpeg
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        raw_wav_path = tmp.name

    # Use the parent class streaming render (writes segment-by-segment)
    with wave.open(raw_wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        engine.render_streaming(wf)

    t1 = _time.time()
    raw_size = os.path.getsize(raw_wav_path) if os.path.exists(raw_wav_path) else 0
    print(f"[RadioEngineV20] Streaming render complete: {raw_size/1048576:.1f} MB WAV in {t1-t0:.1f}s")

    # Force garbage collection to free render buffers
    gc.collect()

    # Use ffmpeg to normalize to -1dB peak and convert to MP3
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp2:
        normalized_wav_path = tmp2.name

    try:
        # Pass 1: Measure peak
        ct_now = _time.strftime('%Y-%m-%d %H:%M CT',
                                _time.localtime(_time.time()))
        print(f"[{ct_now}] [RadioEngineV20] Normalizing with ffmpeg...")

        # Normalize to -1dB peak using ffmpeg
        subprocess.run(
            ['ffmpeg', '-y', '-i', raw_wav_path,
             '-af', 'dynaudnorm=f=500:g=15:p=0.89:m=20,alimiter=limit=0.92:attack=5:release=50',
             normalized_wav_path],
            capture_output=True, timeout=300
        )

        # Convert to MP3
        if output_path.endswith('.mp3'):
            subprocess.run(
                ['ffmpeg', '-y', '-i', normalized_wav_path,
                 '-codec:a', 'libmp3lame', '-b:a', '192k',
                 '-ar', str(SAMPLE_RATE), output_path],
                capture_output=True, timeout=300
            )
        else:
            import shutil
            shutil.copy2(normalized_wav_path, output_path)

    finally:
        # Clean up temp files
        for p in [raw_wav_path, normalized_wav_path]:
            try:
                os.unlink(p)
            except OSError:
                pass

    t2 = _time.time()
    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    # Report volume stats using ffmpeg
    try:
        vol_result = subprocess.run(
            ['ffmpeg', '-i', output_path, '-af', 'volumedetect', '-f', 'null', '/dev/null'],
            capture_output=True, text=True, timeout=120
        )
        for line in vol_result.stderr.split('\n'):
            if 'mean_volume' in line or 'max_volume' in line:
                print(f"[RadioEngineV20] {line.strip()}")
    except Exception:
        pass

    print(f"[RadioEngineV20] File size: {file_size/1048576:.1f} MB")
    print(f"[RadioEngineV20] Total time: {t2-t0:.1f}s (render {t1-t0:.1f}s + encode {t2-t1:.1f}s)")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='In The Beginning Radio')
    parser.add_argument('--output', '-o', default='cosmic_radio.mp3',
                       help='Output file path (WAV or MP3)')
    parser.add_argument('--duration', '-d', type=float, default=1800.0,
                       help='Duration in seconds (default: 1800)')
    parser.add_argument('--seed', '-s', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--version', '-V', choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16', 'v18', 'v18o', 'v20'], default='v20',
                       help='Engine version: v7-v20 (v20=volume-fixed, solo moods, expanded)')
    args = parser.parse_args()
    if args.version == 'v20':
        generate_radio_v20_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v18o':
        generate_radio_v18_orchestra_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v18':
        generate_radio_v18_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v16':
        generate_radio_v16_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v15':
        generate_radio_v15_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v14':
        generate_radio_v14_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v13':
        generate_radio_v13_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v12':
        generate_radio_v12_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v11':
        generate_radio_v11_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v10':
        generate_radio_v10_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v9':
        generate_radio_v9_mp3(args.output, args.duration, args.seed)
    elif args.version == 'v8':
        generate_radio_v8_mp3(args.output, args.duration, args.seed)
    else:
        generate_radio_mp3(args.output, args.duration, args.seed)
