#!/usr/bin/env python3
"""
Radio engine for 'In The Beginning Radio' -- a cosmic simulation music station.

This engine generates continuously evolving music that shifts mood, instruments,
time signature, scale, and tempo every 42 seconds, driven by the physics
simulation state. It features:

    - 500+ synthesized instruments with runtime instrument rotation
    - 42-second mood segments with crossfading between them
    - Classical music scales and well-known time signatures (from Wikipedia)
    - Fade-in at start, crossfade between segments, fade-out at end
    - Smoothing/dampening to reduce MIDI-like artifacts
    - EDM-influenced beat patterns blended with classical harmony
    - TTS voice injection using Silero (preferred) or espeak-ng (fallback)
      with phrases sampled from project source code
    - MIDI note sampling from 249 public domain classical works (1600-1900)
    - Simulation-driven parameters sampled from different space regions
    - 1-16 concurrent instruments per segment based on sine characteristics

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
}

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

        # Vibrato
        vib_rate = rng.uniform(3.0, 7.0)
        vib_depth = rng.uniform(0.001, 0.008)
        vib_delay = rng.uniform(0.1, 0.5)

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
                    self._note_sequences.append({
                        'path': path,
                        'composer': composer,
                        'notes': notes,
                    })
            except Exception:
                continue

        self._loaded = True

    def _extract_notes(self, midi_file):
        """Extract (pitch, duration_ticks, velocity) tuples from MIDI."""
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
                        notes.append((msg.note, dur, vel))
        return notes

    def sample_phrase(self, rng, length=8, root=60, scale=None):
        """Sample a phrase from a random MIDI file and transpose to root.

        Returns list of (midi_note, duration_beats, velocity) tuples.
        The notes are projected onto the given scale if provided.
        """
        if not self._note_sequences:
            return self._generate_fallback_phrase(rng, length, root, scale)

        seq = rng.choice(self._note_sequences)
        notes = seq['notes']

        # Pick a random starting point
        if len(notes) <= length:
            phrase_notes = notes
        else:
            start = rng.randint(0, len(notes) - length)
            phrase_notes = notes[start:start + length]

        # Transpose to root and project onto scale
        if not phrase_notes:
            return self._generate_fallback_phrase(rng, length, root, scale)

        # Find the phrase's center pitch
        pitches = [n[0] for n in phrase_notes]
        center = sum(pitches) / len(pitches)
        offset = root - center

        result = []
        for pitch, dur_ticks, vel in phrase_notes:
            new_pitch = int(pitch + offset)
            # Project onto scale if provided
            if scale:
                new_pitch = self._snap_to_scale(new_pitch, root, scale)
            # Convert ticks to approximate beats (assume 480 ticks/beat)
            dur_beats = max(0.125, dur_ticks / 480.0)
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
            group = [notes[i][0]]
            j = i + 1
            while j < min(i + 6, len(notes)):
                group.append(notes[j][0])
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


# ---------------------------------------------------------------------------
# MOOD SEGMENT -- Encapsulates 42 seconds of musical character
# ---------------------------------------------------------------------------
class MoodSegment:
    """Represents a 42-second musical mood with specific characteristics.

    All parameters are derived from the simulation state at the moment
    the segment begins, sampling from different regions of space.
    """

    def __init__(self, segment_idx, epoch, epoch_idx, sim_state, rng_seed):
        self.segment_idx = segment_idx
        self.epoch = epoch
        self.epoch_idx = epoch_idx
        self.rng = random.Random(rng_seed)

        epoch_music = EPOCH_MUSIC.get(epoch, EPOCH_MUSIC['Present'])

        # Time signature (from Wikipedia-documented set)
        available_ts = epoch_music['time_sigs']
        # Blend in some EDM time sigs for variety
        if self.rng.random() < 0.3:
            available_ts = available_ts + EDM_TIME_SIGS
        self.time_sig = self.rng.choice(available_ts)
        ts_info = TIME_SIGNATURES.get(self.time_sig, TIME_SIGNATURES['4/4'])
        self.beats_per_bar = ts_info['beats']

        # Tempo (BPM) from simulation conditions
        tempo_lo, tempo_hi = epoch_music['tempo']
        # Use simulation density/temperature to modulate within range
        temp = sim_state.get('temperature', 1e6)
        temp_factor = clamp(math.log10(max(1, temp)) / 15.0, 0.0, 1.0)
        self.tempo = tempo_lo + (tempo_hi - tempo_lo) * temp_factor
        # Add EDM influence: occasionally push tempo up
        if self.rng.random() < 0.2:
            self.tempo = min(self.tempo * 1.2, 160)

        # Scale (from well-known harmonic systems)
        self.scale_name = self.rng.choice(epoch_music['scales'])
        self.scale = SCALES.get(self.scale_name, SCALES['ionian'])

        # Root note
        root = EPOCH_ROOTS.get(epoch, 60)
        # Sample from different space regions: shift root
        particles = sim_state.get('particles', 0)
        region_shift = (particles * 7) % 12
        self.root = root + region_shift - 6  # +/- 6 semitones

        # Chord progression
        prog_name = self.rng.choice(list(PROGRESSIONS.keys()))
        self.progression = PROGRESSIONS[prog_name]
        self.progression_name = prog_name

        # Number of concurrent instruments: 1-16 based on sine of simulation
        density = epoch_music['density']
        atoms = sim_state.get('atoms', 0)
        sine_val = math.sin(segment_idx * 0.7 + atoms * 0.001)
        instrument_factor = (sine_val + 1) / 2  # 0..1
        self.n_instruments = clamp(
            int(1 + instrument_factor * density * 15), 1, 16
        )

        # Scale family for mashup blending
        self.family = epoch_music['family']

        # Whether to apply dampening/smoothing
        self.dampen = self.rng.random() < 0.4  # 40% chance

        # EDM beat style flag
        self.edm_beats = self.rng.random() < 0.35  # 35% chance


# ---------------------------------------------------------------------------
# RADIO ENGINE -- The main music generation engine
# ---------------------------------------------------------------------------
class RadioEngine:
    """In The Beginning Radio -- Cosmic simulation music station.

    Generates continuously evolving music with 42-second mood shifts,
    500+ instruments, classical/EDM fusion, MIDI sampling, and TTS.
    """

    SEGMENT_DURATION = 42.0  # seconds per mood shift
    CROSSFADE_DURATION = 3.0  # seconds of crossfade between segments
    FADE_IN_DURATION = 5.0   # seconds of fade-in at start
    FADE_OUT_DURATION = 8.0  # seconds of fade-out at end

    def __init__(self, seed=42, total_duration=600.0):
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

        # Track which segment gets TTS injection
        total_segments = int(total_duration / self.SEGMENT_DURATION) + 1
        if total_segments >= 3:
            # TTS happens once per 10 minutes, between two mood shifts
            self.tts_segment = self.rng.randint(
                max(1, total_segments // 4),
                min(total_segments - 2, total_segments * 3 // 4)
            )
        else:
            self.tts_segment = -1  # No TTS for very short pieces

    def render(self, sim_states=None):
        """Render the full audio piece.

        Args:
            sim_states: Optional list of dicts with simulation state per segment.
                        If None, generates synthetic simulation data.

        Returns:
            (left_channel, right_channel) as lists of float samples.
        """
        total_samples = int(self.total_duration * SAMPLE_RATE)
        left = [0.0] * total_samples
        right = [0.0] * total_samples

        # How many segments?
        n_segments = int(math.ceil(self.total_duration / self.SEGMENT_DURATION))
        segment_samples = int(self.SEGMENT_DURATION * SAMPLE_RATE)
        crossfade_samples = int(self.CROSSFADE_DURATION * SAMPLE_RATE)

        # Generate simulation states if not provided
        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        prev_segment_audio = None

        for seg_idx in range(n_segments):
            seg_start_sample = seg_idx * segment_samples
            if seg_start_sample >= total_samples:
                break

            # Determine epoch from time position
            time_pos = seg_idx * self.SEGMENT_DURATION
            epoch_idx = int(time_pos / self.total_duration * 12.999)
            epoch_idx = clamp(epoch_idx, 0, 12)
            epoch = EPOCH_ORDER[epoch_idx]

            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

            # Create mood segment
            mood = MoodSegment(
                seg_idx, epoch, epoch_idx, sim_state,
                self.seed + seg_idx * 31337
            )

            # Select instruments for this segment
            selected = self._select_instruments(mood)

            # Render the segment
            seg_left, seg_right = self._render_segment(
                mood, selected, segment_samples, sim_state
            )

            # Apply smoothing/dampening if mood says so
            if mood.dampen:
                seg_left = self.smoother.apply_lowpass(seg_left, 5000)
                seg_right = self.smoother.apply_lowpass(seg_right, 5000)
                seg_left = self.smoother.apply_gentle_compression(seg_left)
                seg_right = self.smoother.apply_gentle_compression(seg_right)

            # Inject TTS if this is the designated segment
            if seg_idx == self.tts_segment:
                seg_left, seg_right = self._inject_tts(
                    seg_left, seg_right, mood, epoch_idx
                )

            # Apply crossfade with previous segment
            seg_end = min(seg_start_sample + len(seg_left), total_samples)
            seg_len = seg_end - seg_start_sample

            for i in range(seg_len):
                fade = 1.0
                # Crossfade-in from previous segment
                if i < crossfade_samples and seg_idx > 0:
                    fade = i / crossfade_samples
                # Crossfade-out to next segment
                remaining = seg_len - i
                if remaining < crossfade_samples and seg_idx < n_segments - 1:
                    fade *= remaining / crossfade_samples

                left[seg_start_sample + i] += seg_left[i] * fade
                right[seg_start_sample + i] += seg_right[i] * fade

            # Rotate instruments every 10 minutes (approx 14 segments)
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

        This avoids holding the full piece in memory, making it suitable
        for long-form renders (60+ minutes). Each 42-second segment is
        rendered, crossfaded, and written immediately.

        Args:
            wav_file: An open wave.Wave_write object (stereo, 16-bit, 44100).
            sim_states: Optional list of dicts with simulation state per segment.
        """
        total_samples = int(self.total_duration * SAMPLE_RATE)
        n_segments = int(math.ceil(self.total_duration / self.SEGMENT_DURATION))
        segment_samples = int(self.SEGMENT_DURATION * SAMPLE_RATE)
        crossfade_samples = int(self.CROSSFADE_DURATION * SAMPLE_RATE)
        fade_in_samples = int(self.FADE_IN_DURATION * SAMPLE_RATE)
        fade_out_samples = int(self.FADE_OUT_DURATION * SAMPLE_RATE)

        if sim_states is None:
            sim_states = self._generate_sim_states(n_segments)

        # We keep a rolling output buffer that accumulates overlapping segments.
        # When a segment's non-overlapping region is complete, we flush it.
        # Buffer is 2 segments wide to handle crossfade overlap.
        buf_len = segment_samples + crossfade_samples
        buf_left = [0.0] * buf_len
        buf_right = [0.0] * buf_len
        buf_global_start = 0   # global sample index of buf[0]
        samples_written = 0

        _tanh = math.tanh
        _pack = struct.pack

        for seg_idx in range(n_segments):
            seg_global_start = seg_idx * segment_samples
            if seg_global_start >= total_samples:
                break

            # Determine epoch
            time_pos = seg_idx * self.SEGMENT_DURATION
            epoch_idx = int(time_pos / self.total_duration * 12.999)
            epoch_idx = clamp(epoch_idx, 0, 12)
            epoch = EPOCH_ORDER[epoch_idx]
            sim_state = sim_states[min(seg_idx, len(sim_states) - 1)]

            mood = MoodSegment(
                seg_idx, epoch, epoch_idx, sim_state,
                self.seed + seg_idx * 31337
            )
            selected = self._select_instruments(mood)
            seg_left, seg_right = self._render_segment(
                mood, selected, segment_samples, sim_state
            )

            if mood.dampen:
                seg_left = self.smoother.apply_lowpass(seg_left, 5000)
                seg_right = self.smoother.apply_lowpass(seg_right, 5000)
                seg_left = self.smoother.apply_gentle_compression(seg_left)
                seg_right = self.smoother.apply_gentle_compression(seg_right)

            if seg_idx == self.tts_segment:
                seg_left, seg_right = self._inject_tts(
                    seg_left, seg_right, mood, epoch_idx
                )

            # Add segment into the rolling buffer with crossfade
            seg_end_global = min(seg_global_start + len(seg_left), total_samples)
            seg_len = seg_end_global - seg_global_start

            for i in range(seg_len):
                global_i = seg_global_start + i
                buf_i = global_i - buf_global_start
                # Grow buffer if needed
                while buf_i >= len(buf_left):
                    buf_left.append(0.0)
                    buf_right.append(0.0)

                fade = 1.0
                if i < crossfade_samples and seg_idx > 0:
                    fade = i / crossfade_samples
                remaining = seg_len - i
                if remaining < crossfade_samples and seg_idx < n_segments - 1:
                    fade *= remaining / crossfade_samples

                # Master fade-in / fade-out
                if global_i < fade_in_samples:
                    fade *= global_i / fade_in_samples
                elif global_i >= total_samples - fade_out_samples:
                    fade *= (total_samples - global_i) / fade_out_samples

                buf_left[buf_i] += seg_left[i] * fade
                buf_right[buf_i] += seg_right[i] * fade

            # Flush the non-overlapping portion to WAV
            # The next segment starts at seg_global_start + segment_samples,
            # and its crossfade reaches back crossfade_samples. So we can
            # safely flush up to (next_seg_start - crossfade_samples).
            if seg_idx < n_segments - 1:
                next_seg_start = (seg_idx + 1) * segment_samples
                flush_up_to = next_seg_start - crossfade_samples
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
                    # Soft limit + stereo smooth
                    lv, rv = lv * 0.9 + rv * 0.1, rv * 0.9 + lv * 0.1
                    li = int(_tanh(lv) * 32767)
                    ri = int(_tanh(rv) * 32767)
                    struct.pack_into('<hh', data, j * 4,
                                   max(-32767, min(32767, li)),
                                   max(-32767, min(32767, ri)))
                wav_file.writeframes(bytes(data))
                samples_written = flush_end

                # Shift buffer: keep only the overlap region
                keep_from = flush_end - buf_global_start
                if keep_from > 0 and keep_from < len(buf_left):
                    buf_left = buf_left[keep_from:] + [0.0] * keep_from
                    buf_right = buf_right[keep_from:] + [0.0] * keep_from
                    buf_global_start = flush_end
                elif keep_from >= len(buf_left):
                    buf_left = [0.0] * buf_len
                    buf_right = [0.0] * buf_len
                    buf_global_start = flush_end

            # Rotate instruments periodically
            if seg_idx > 0 and seg_idx % 14 == 0:
                self._generation += 1
                self.instruments = self.factory.rotate_instruments(
                    self.instruments, n_swap=50, generation=self._generation
                )

            if seg_idx % 3 == 0:
                elapsed_min = seg_idx * self.SEGMENT_DURATION / 60
                print(f"  [Streaming] Segment {seg_idx+1}/{n_segments} "
                      f"({elapsed_min:.1f}min) epoch={epoch} "
                      f"written={samples_written/SAMPLE_RATE:.0f}s",
                      flush=True)

        # Flush any remaining samples
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

        # Pick from the full instrument set
        selected = rng.sample(self.instruments, min(n, len(self.instruments)))
        return selected

    def _render_segment(self, mood, instruments, n_samples, sim_state):
        """Render a 42-second mood segment.

        Uses bar-based rendering with the segment's time signature,
        scale, and tempo. Blends algorithmic composition with MIDI
        sampling from classical works.
        """
        left = [0.0] * n_samples
        right = [0.0] * n_samples

        rng = mood.rng
        tempo = mood.tempo
        beats_per_bar = mood.beats_per_bar
        scale = mood.scale
        root = mood.root

        # Beat duration in samples
        beat_dur = 60.0 / tempo  # seconds per beat
        beat_samples = int(beat_dur * SAMPLE_RATE)
        bar_samples = beat_samples * beats_per_bar

        # Number of bars in segment
        n_bars = max(1, n_samples // bar_samples)

        # Get MIDI phrases for this segment
        midi_phrases = []
        for _ in range(min(4, len(instruments))):
            phrase = self.midi_lib.sample_phrase(rng, length=8, root=root, scale=scale)
            midi_phrases.append(phrase)

        # Get a chord pattern from MIDI if available
        midi_chords = self.midi_lib.sample_chord_pattern(rng, root, scale, length=8)

        # Assign roles to instruments
        n_instr = len(instruments)
        melody_instrs = instruments[:max(1, n_instr // 4)]
        harmony_instrs = instruments[n_instr // 4:n_instr // 2]
        bass_instrs = instruments[n_instr // 2:n_instr * 3 // 4]
        rhythm_instrs = instruments[n_instr * 3 // 4:]

        # Render bar by bar
        for bar_idx in range(n_bars):
            bar_offset = bar_idx * bar_samples
            if bar_offset >= n_samples:
                break

            # Progress through chord progression
            prog_idx = bar_idx % len(mood.progression)
            chord_root_offset, chord_type = mood.progression[prog_idx]
            chord_root = root + chord_root_offset
            chord_intervals = CHORD_INTERVALS.get(chord_type, [0, 4, 7])
            chord_notes = [chord_root + ci for ci in chord_intervals]

            # --- MELODY ---
            for instr in melody_instrs:
                if rng.random() < 0.7:  # 70% chance of playing
                    # Use MIDI phrase or generate algorithmically
                    if midi_phrases and rng.random() < 0.5:
                        phrase = rng.choice(midi_phrases)
                    else:
                        phrase = self._generate_melody(rng, root, scale, beats_per_bar)

                    note_offset = bar_offset
                    for midi_note, dur_beats, vel in phrase:
                        note_dur = dur_beats * beat_dur
                        # Add humanization flex
                        note_dur *= rng.uniform(0.92, 1.08)
                        timing_flex = int(rng.uniform(-0.01, 0.01) * SAMPLE_RATE)

                        note_samples = self.factory.synthesize_note(
                            instr, mtof(midi_note), note_dur, vel
                        )
                        write_offset = note_offset + timing_flex
                        self._mix_mono(left, right, note_samples, write_offset,
                                      n_samples, rng.uniform(-0.5, 0.5))
                        note_offset += int(note_dur * SAMPLE_RATE)
                        if note_offset >= bar_offset + bar_samples:
                            break

            # --- HARMONY (chord pads) ---
            for instr in harmony_instrs:
                if rng.random() < 0.6:
                    # Use MIDI chords or progression chords
                    if midi_chords and rng.random() < 0.4:
                        bar_chord = midi_chords[bar_idx % len(midi_chords)]
                    else:
                        bar_chord = chord_notes

                    # Render sustained chord
                    chord_dur = beats_per_bar * beat_dur * rng.uniform(0.8, 1.0)
                    for cn in bar_chord[:4]:
                        note_samples = self.factory.synthesize_note(
                            instr, mtof(cn), chord_dur, rng.uniform(0.3, 0.6)
                        )
                        pan = rng.uniform(-0.7, 0.7)
                        self._mix_mono(left, right, note_samples, bar_offset,
                                      n_samples, pan)

            # --- BASS ---
            for instr in bass_instrs:
                if rng.random() < 0.65:
                    bass_note = chord_root - 12  # One octave down
                    if rng.random() < 0.5:
                        bass_note -= 12  # Two octaves down
                    bass_note = clamp(bass_note, 24, 60)

                    # Bass pattern: on beats
                    for beat in range(beats_per_bar):
                        if rng.random() < 0.6:
                            beat_offset = bar_offset + beat * beat_samples
                            bass_dur = beat_dur * rng.uniform(0.5, 0.9)
                            note_samples = self.factory.synthesize_note(
                                instr, mtof(bass_note), bass_dur, rng.uniform(0.5, 0.8)
                            )
                            self._mix_mono(left, right, note_samples, beat_offset,
                                          n_samples, 0.0)
                            # Walk the bass
                            if rng.random() < 0.3:
                                bass_note += rng.choice([-2, -1, 1, 2, 5, 7])
                                bass_note = clamp(bass_note, 24, 60)

            # --- RHYTHM / DRUMS ---
            if mood.edm_beats or rng.random() < 0.5:
                self._render_beat_pattern(
                    left, right, rhythm_instrs, bar_offset, bar_samples,
                    beats_per_bar, beat_samples, n_samples, rng, mood
                )

        return left, right

    def _generate_melody(self, rng, root, scale, n_notes):
        """Generate a melodic phrase algorithmically."""
        intervals = [int(round(s)) for s in scale]
        notes = []
        current_degree = rng.randint(0, len(intervals) - 1)
        octave = 0

        for _ in range(n_notes):
            # Step motion with occasional leaps
            step = rng.choice([-2, -1, -1, 0, 1, 1, 2, 3])
            current_degree += step
            if current_degree < 0:
                current_degree += len(intervals)
                octave -= 1
            elif current_degree >= len(intervals):
                current_degree -= len(intervals)
                octave += 1
            octave = clamp(octave, -1, 2)

            midi_note = root + intervals[current_degree % len(intervals)] + octave * 12
            midi_note = clamp(midi_note, 36, 96)

            # Duration with variety
            dur = rng.choice([0.25, 0.25, 0.5, 0.5, 0.5, 1.0, 1.0, 1.5, 2.0])
            vel = rng.uniform(0.5, 0.9)
            notes.append((midi_note, dur, vel))

        return notes

    def _render_beat_pattern(self, left, right, instrs, bar_offset,
                            bar_samples, beats_per_bar, beat_samples,
                            total_samples, rng, mood):
        """Render a drum/rhythm pattern."""
        if not instrs:
            return

        # EDM four-on-the-floor or classical rhythm
        for beat in range(beats_per_bar):
            beat_offset = bar_offset + beat * beat_samples

            # Kick on downbeats
            if beat % 2 == 0 or (mood.edm_beats and mood.time_sig == '4/4'):
                if instrs:
                    kick = instrs[0]
                    note = self.factory.synthesize_note(kick, 55.0, 0.15, 0.7)
                    self._mix_mono(left, right, note, beat_offset,
                                  total_samples, 0.0)

            # Snare on backbeats
            if beat % 2 == 1 and len(instrs) > 1:
                snare = instrs[1 % len(instrs)]
                note = self.factory.synthesize_note(snare, 200.0, 0.1, 0.6)
                self._mix_mono(left, right, note, beat_offset,
                              total_samples, rng.uniform(-0.2, 0.2))

            # Hi-hat subdivisions
            if len(instrs) > 2:
                hihat = instrs[2 % len(instrs)]
                for sub in range(2 if not mood.edm_beats else 4):
                    sub_offset = beat_offset + sub * (beat_samples // (2 if not mood.edm_beats else 4))
                    if rng.random() < 0.7:
                        note = self.factory.synthesize_note(hihat, 8000.0, 0.05, 0.3)
                        self._mix_mono(left, right, note, sub_offset,
                                      total_samples, rng.uniform(-0.5, 0.5))

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
                left[i] += samples[si] * l_gain * 0.3
                right[i] += samples[si] * r_gain * 0.3

    def _inject_tts(self, left, right, mood, epoch_idx):
        """Inject spoken word segment into the audio.

        Places TTS in the middle of the segment, followed by
        'In The Beginning Radio' station identification.
        """
        rng = mood.rng

        # Get phrases from source code
        phrases = self.tts.get_source_phrases(rng, count=2)
        speech_text = '. '.join(phrases)

        # Add station ID
        full_text = speech_text + '. In the beginning radio.'

        # Generate TTS audio
        voice_seed = rng.randint(0, 100)
        tts_samples, tts_sr = self.tts.generate_speech(
            full_text, voice_seed, epoch_idx
        )

        if tts_samples is None:
            return left, right

        # Resample TTS to match our sample rate if needed
        if tts_sr != SAMPLE_RATE:
            tts_samples = self._resample(tts_samples, tts_sr, SAMPLE_RATE)

        # Normalize TTS
        peak = max(abs(s) for s in tts_samples) if tts_samples else 1.0
        if peak > 0:
            tts_samples = [s / peak * 0.7 for s in tts_samples]

        # Place TTS in the middle of the segment
        mid = len(left) // 2
        tts_start = max(0, mid - len(tts_samples) // 2)

        # Duck the music under the speech
        duck_start = max(0, tts_start - int(0.5 * SAMPLE_RATE))
        duck_end = min(len(left), tts_start + len(tts_samples) + int(0.5 * SAMPLE_RATE))
        duck_ramp = int(0.3 * SAMPLE_RATE)

        for i in range(duck_start, duck_end):
            # Compute duck envelope
            if i < duck_start + duck_ramp:
                duck = 1.0 - 0.6 * ((i - duck_start) / duck_ramp)
            elif i > duck_end - duck_ramp:
                duck = 1.0 - 0.6 * ((duck_end - i) / duck_ramp)
            else:
                duck = 0.4  # Music at 40% during speech
            left[i] *= duck
            right[i] *= duck

        # Mix TTS into both channels (centered)
        for i in range(len(tts_samples)):
            si = tts_start + i
            if 0 <= si < len(left):
                left[si] += tts_samples[i] * 0.5
                right[si] += tts_samples[i] * 0.5

        return left, right

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


def generate_radio_mp3(output_path, duration=600.0, seed=42):
    """Generate the radio MP3 file.

    This is the main entry point for producing the 10-minute cosmic
    radio station MP3 with all features enabled.
    """
    import tempfile

    print(f"[RadioEngine] Initializing (seed={seed}, duration={duration}s)...")
    engine = RadioEngine(seed=seed, total_duration=duration)

    print(f"[RadioEngine] {len(engine.instruments)} instruments loaded")
    print(f"[RadioEngine] {len(engine.midi_lib._note_sequences)} MIDI sequences loaded")
    print(f"[RadioEngine] TTS engine: {'Silero' if engine.tts._silero_available else 'espeak-ng'}")
    print(f"[RadioEngine] TTS segment: {engine.tts_segment}")

    n_segments = int(math.ceil(duration / engine.SEGMENT_DURATION))
    print(f"[RadioEngine] {n_segments} mood segments x {engine.SEGMENT_DURATION}s each")

    print(f"[RadioEngine] Rendering audio...")
    t0 = _time.time()

    # Import simulator for real simulation data
    try:
        sys.path.insert(0, PROJECT_ROOT)
        from simulator.universe import Universe
        universe = Universe(seed=seed, max_ticks=999999999)

        # Run simulation to collect states at segment boundaries
        sim_states = []
        ticks_per_segment = int(duration / n_segments * 50)  # 50 ticks/sec
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
    parser.add_argument('--duration', '-d', type=float, default=600.0,
                       help='Duration in seconds (default: 600)')
    parser.add_argument('--seed', '-s', type=int, default=42,
                       help='Random seed')
    args = parser.parse_args()
    generate_radio_mp3(args.output, args.duration, args.seed)
