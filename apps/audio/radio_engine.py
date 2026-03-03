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
    - Hartmann consonance enforcement on all chord voicings
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
    """Text-to-speech engine using Silero (preferred) or espeak-ng (fallback).

    Generates spoken word segments from project source code phrases,
    with voice characteristics chosen based on simulation epoch.

    Silero TTS: Apache 2.0 license, multiple English voices.
    espeak-ng: GPL, fallback when Silero unavailable.
    """

    # espeak-ng voice variants by epoch character
    ESPEAK_VOICES = [
        'en-us', 'en-gb', 'en-gb-scotland', 'en-gb-x-rp',
        'en-gb-x-gbclan', 'en-gb-x-gbcwmd', 'en-029',
    ]

    # Silero speaker IDs (v3_en model has ~100+ speakers)
    SILERO_SPEAKERS = [f'en_{i}' for i in range(118)]

    def __init__(self):
        self._silero_model = None
        self._silero_available = False
        self._try_load_silero()

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

    def generate_speech(self, text, voice_seed=0, epoch_idx=0):
        """Generate speech audio from text.

        Returns (samples_list, sample_rate) or (None, None) on failure.
        Voice selection is influenced by epoch_idx for simulation coherence.
        """
        if self._silero_available:
            return self._generate_silero(text, voice_seed, epoch_idx)
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

    def _generate_espeak(self, text, voice_seed, epoch_idx):
        """Generate speech using espeak-ng (fallback)."""
        import tempfile
        voice_idx = (voice_seed + epoch_idx * 3) % len(self.ESPEAK_VOICES)
        voice = self.ESPEAK_VOICES[voice_idx]

        # Vary speech parameters based on epoch
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
                with wave.open(tmp_path, 'rb') as wf:
                    sr = wf.getframerate()
                    frames = wf.readframes(wf.getnframes())
                    samples = []
                    for i in range(0, len(frames), 2):
                        if i + 1 < len(frames):
                            val = struct.unpack('<h', frames[i:i+2])[0]
                            samples.append(val / 32768.0)
                return samples, sr
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
    7 rondo forms with 6 arpeggio variations, Hartmann consonance enforcement,
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

        # v7: Enhanced Hartmann consonance enforcement
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
    args = parser.parse_args()
    generate_radio_mp3(args.output, args.duration, args.seed)
