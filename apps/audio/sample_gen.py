#!/usr/bin/env python3
"""
Generate synthetic instrument samples for the cosmic music engine.

Creates 40+ high-quality instrument samples using additive/FM/physical-modeling
synthesis. Each sample is a single note (C4 = MIDI 60, 261.63 Hz) rendered as
a mono WAV file at 44100 Hz / 16-bit. The music engine transposes these at
playback time using resampling.

All samples are generated algorithmically — no external data, no licensing
concerns, no network access.

Categories:
    - Piano / keyboard (4 samples)
    - Strings (5 samples)
    - Woodwinds (4 samples)
    - Brass (3 samples)
    - Bells / metallic (4 samples)
    - Percussion (6 samples)
    - World instruments (6 samples)
    - Pads / synth (5 samples)
    - Bass (3 samples)

Each sample includes natural attack, sustain, and release characteristics
modeled after the real instrument's acoustic behavior.
"""

import math
import os
import random
import struct
import wave

SAMPLE_RATE = 44100
BASE_FREQ = 261.63  # C4


def _write_wav(path, samples, sample_rate=SAMPLE_RATE):
    """Write mono float samples to 16-bit WAV."""
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        peak = max(abs(s) for s in samples) if samples else 1.0
        if peak < 1e-10:
            peak = 1.0
        norm = 0.95 / peak
        data = b''
        for s in samples:
            val = int(s * norm * 32767)
            val = max(-32767, min(32767, val))
            data += struct.pack('<h', val)
        wf.writeframes(data)


def _adsr(n, attack, decay, sustain_level, release, sample_rate=SAMPLE_RATE):
    """Generate ADSR envelope."""
    env = [0.0] * n
    a_samples = int(attack * sample_rate)
    d_samples = int(decay * sample_rate)
    r_samples = int(release * sample_rate)
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


# ---------------------------------------------------------------------------
# PIANO / KEYBOARD
# ---------------------------------------------------------------------------

def gen_piano(duration=2.0):
    """Grand piano — struck string model with detuned partials."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    # Harmonic amplitudes modeled after piano string
    harmonics = [
        (1, 1.0, 8.0),    # fundamental, decay rate
        (2, 0.50, 7.0),
        (3, 0.28, 6.5),
        (4, 0.20, 6.0),
        (5, 0.14, 5.5),
        (6, 0.10, 5.0),
        (7, 0.07, 4.5),
        (8, 0.05, 4.0),
        (9, 0.03, 3.5),
        (10, 0.02, 3.0),
    ]
    # Piano strings are slightly inharmonic (stiffness)
    inharmonicity = 0.0003
    for h, amp, decay in harmonics:
        h_freq = freq * h * math.sqrt(1 + inharmonicity * h * h)
        if h_freq >= SAMPLE_RATE / 2:
            break
        phase = random.random() * 2 * math.pi
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            # Hammer strike attack
            if t < 0.003:
                env *= t / 0.003
            samples[i] += env * math.sin(2 * math.pi * h_freq * t + phase)
    return samples


def gen_electric_piano(duration=2.0):
    """Rhodes-style electric piano — FM synthesis."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    mod_ratio = 14.0  # Characteristic tine sound
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 3.0)
        # FM with decaying modulation index
        mod_idx = 2.5 * math.exp(-t * 8.0)
        mod = mod_idx * math.sin(2 * math.pi * mod_ratio * t)
        samples[i] = env * math.sin(2 * math.pi * freq * t + mod)
        # Add warmth
        samples[i] += 0.15 * env * math.sin(2 * math.pi * freq * 2 * t)
    return samples


def gen_harpsichord(duration=1.5):
    """Harpsichord — plucked string with bright attack."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    for h in range(1, 13):
        h_freq = freq * h
        if h_freq >= SAMPLE_RATE / 2:
            break
        # Harpsichord has strong upper harmonics
        amp = 1.0 / h * (1.0 if h % 2 == 1 else 0.7)
        decay = 4.0 + h * 1.5  # Higher harmonics decay faster
        phase = random.random() * 0.5
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * h_freq * t + phase)
    return samples


def gen_celesta(duration=2.0):
    """Celesta — bell-like keyboard instrument."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 2  # Celesta sounds an octave higher
    samples = [0.0] * n
    # Inharmonic partials like bells
    partials = [(1.0, 1.0), (2.76, 0.5), (5.4, 0.3), (8.93, 0.15), (13.3, 0.08)]
    for ratio, amp in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        decay = 2.5 / ratio
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.002:
                env *= t / 0.002
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


# ---------------------------------------------------------------------------
# STRINGS
# ---------------------------------------------------------------------------

def gen_violin(duration=2.5):
    """Violin — bowed string with vibrato."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.08, 0.05, 0.85, 0.3)
    # Violin has odd and even harmonics
    harmonics = [1.0, 0.5, 0.33, 0.25, 0.20, 0.16, 0.14, 0.12, 0.10, 0.08]
    for i in range(n):
        t = i / SAMPLE_RATE
        # Vibrato (5-6 Hz, grows in)
        vib_depth = 0.003 * min(1.0, t / 0.3)
        vib = vib_depth * math.sin(2 * math.pi * 5.5 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        # Bow noise
        s += 0.02 * (random.random() * 2 - 1) * env[i]
        samples[i] = s * env[i] * 0.3
    return samples


def gen_cello(duration=3.0):
    """Cello — warm, rich bowed tone."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 2  # Cello is lower
    samples = [0.0] * n
    env = _adsr(n, 0.12, 0.08, 0.85, 0.5)
    harmonics = [1.0, 0.70, 0.45, 0.30, 0.20, 0.15, 0.10, 0.08]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.004 * min(1.0, t / 0.4) * math.sin(2 * math.pi * 5.0 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.35
    return samples


def gen_viola(duration=2.5):
    """Viola — between violin and cello."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 0.75
    samples = [0.0] * n
    env = _adsr(n, 0.10, 0.06, 0.82, 0.4)
    harmonics = [1.0, 0.55, 0.38, 0.28, 0.18, 0.13, 0.09, 0.06]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.003 * min(1.0, t / 0.35) * math.sin(2 * math.pi * 5.2 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.32
    return samples


def gen_harp(duration=3.0):
    """Harp — plucked string with quick attack and long decay."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    harmonics = [1.0, 0.30, 0.10, 0.05, 0.03, 0.02]
    for h_idx, h_amp in enumerate(harmonics):
        h_num = h_idx + 1
        h_freq = freq * h_num
        if h_freq >= SAMPLE_RATE / 2:
            break
        decay = 1.5 + h_num * 0.8
        for i in range(n):
            t = i / SAMPLE_RATE
            env = h_amp * math.exp(-t * decay)
            if t < 0.002:
                env *= t / 0.002
            samples[i] += env * math.sin(2 * math.pi * h_freq * t)
    return samples


def gen_pizzicato(duration=1.0):
    """Pizzicato string — short plucked."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    harmonics = [1.0, 0.4, 0.2, 0.1, 0.05]
    for h_idx, h_amp in enumerate(harmonics):
        h_num = h_idx + 1
        h_freq = freq * h_num
        if h_freq >= SAMPLE_RATE / 2:
            break
        decay = 6.0 + h_num * 3.0
        for i in range(n):
            t = i / SAMPLE_RATE
            env = h_amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * h_freq * t)
    return samples


# ---------------------------------------------------------------------------
# WOODWINDS
# ---------------------------------------------------------------------------

def gen_flute(duration=2.0):
    """Flute — breathy, pure tone."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 2  # Flute range
    samples = [0.0] * n
    env = _adsr(n, 0.06, 0.02, 0.9, 0.15)
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.003 * min(1.0, t / 0.2) * math.sin(2 * math.pi * 5.0 * t)
        f = freq * (1 + vib)
        # Mostly fundamental with slight 2nd harmonic
        s = math.sin(2 * math.pi * f * t)
        s += 0.3 * math.sin(2 * math.pi * f * 2 * t)
        s += 0.08 * math.sin(2 * math.pi * f * 3 * t)
        # Breath noise
        s += 0.04 * (random.random() * 2 - 1)
        samples[i] = s * env[i] * 0.25
    return samples


def gen_clarinet(duration=2.0):
    """Clarinet — odd harmonics dominate."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.04, 0.03, 0.9, 0.12)
    # Odd harmonics (characteristic of cylindrical bore)
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.002 * min(1.0, t / 0.3) * math.sin(2 * math.pi * 5.0 * t)
        f = freq * (1 + vib)
        s = math.sin(2 * math.pi * f * t)          # 1st
        s += 0.05 * math.sin(2 * math.pi * f * 2 * t)  # 2nd (weak)
        s += 0.65 * math.sin(2 * math.pi * f * 3 * t)  # 3rd
        s += 0.03 * math.sin(2 * math.pi * f * 4 * t)  # 4th (weak)
        s += 0.35 * math.sin(2 * math.pi * f * 5 * t)  # 5th
        s += 0.02 * math.sin(2 * math.pi * f * 6 * t)  # 6th (weak)
        s += 0.18 * math.sin(2 * math.pi * f * 7 * t)  # 7th
        samples[i] = s * env[i] * 0.2
    return samples


def gen_oboe(duration=2.0):
    """Oboe — reedy, rich in harmonics."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.03, 0.02, 0.85, 0.1)
    harmonics = [1.0, 0.60, 0.80, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.003 * min(1.0, t / 0.25) * math.sin(2 * math.pi * 5.5 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.2
    return samples


def gen_bassoon(duration=2.5):
    """Bassoon — low reedy tone."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 2
    samples = [0.0] * n
    env = _adsr(n, 0.05, 0.04, 0.85, 0.2)
    harmonics = [1.0, 0.65, 0.55, 0.45, 0.35, 0.28, 0.20, 0.15, 0.10, 0.07]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.002 * min(1.0, t / 0.35) * math.sin(2 * math.pi * 4.5 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.25
    return samples


# ---------------------------------------------------------------------------
# BRASS
# ---------------------------------------------------------------------------

def gen_french_horn(duration=2.5):
    """French horn — warm, mellow brass."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.08, 0.05, 0.85, 0.3)
    harmonics = [1.0, 0.80, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.003 * min(1.0, t / 0.4) * math.sin(2 * math.pi * 4.5 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.25
    return samples


def gen_trumpet(duration=2.0):
    """Trumpet — bright, punchy brass."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.03, 0.03, 0.9, 0.15)
    harmonics = [1.0, 0.90, 0.70, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.15]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.003 * min(1.0, t / 0.3) * math.sin(2 * math.pi * 5.5 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.22
    return samples


def gen_trombone(duration=2.5):
    """Trombone — warm, slide-capable brass."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 2
    samples = [0.0] * n
    env = _adsr(n, 0.06, 0.04, 0.85, 0.25)
    harmonics = [1.0, 0.85, 0.65, 0.55, 0.45, 0.35, 0.25, 0.18, 0.12, 0.08]
    for i in range(n):
        t = i / SAMPLE_RATE
        vib = 0.002 * min(1.0, t / 0.35) * math.sin(2 * math.pi * 5.0 * t)
        f = freq * (1 + vib)
        s = 0.0
        for h_idx, h_amp in enumerate(harmonics):
            h_num = h_idx + 1
            h_freq = f * h_num
            if h_freq >= SAMPLE_RATE / 2:
                break
            s += h_amp * math.sin(2 * math.pi * h_freq * t)
        samples[i] = s * env[i] * 0.28
    return samples


# ---------------------------------------------------------------------------
# BELLS / METALLIC
# ---------------------------------------------------------------------------

def gen_tubular_bell(duration=4.0):
    """Tubular bell — orchestral chime."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 2
    samples = [0.0] * n
    # Inharmonic partials characteristic of tubes
    partials = [
        (1.0, 1.0, 1.2), (2.0, 0.6, 1.8), (3.0, 0.4, 2.5),
        (4.17, 0.3, 3.0), (5.43, 0.2, 3.5), (6.8, 0.12, 4.0),
    ]
    for ratio, amp, decay in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


def gen_glockenspiel(duration=2.0):
    """Glockenspiel — bright metallic bell."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 4  # Very high
    samples = [0.0] * n
    partials = [(1.0, 1.0), (2.71, 0.35), (5.28, 0.15), (8.57, 0.07)]
    for ratio, amp in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        decay = 3.0 * ratio
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


def gen_vibraphone(duration=3.0):
    """Vibraphone — metallic with tremolo from motor."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    partials = [(1.0, 1.0), (4.0, 0.3), (10.0, 0.1)]
    for i in range(n):
        t = i / SAMPLE_RATE
        tremolo = 0.7 + 0.3 * math.sin(2 * math.pi * 5.5 * t)  # Motor tremolo
        s = 0.0
        for ratio, amp in partials:
            p_freq = freq * ratio
            if p_freq >= SAMPLE_RATE / 2:
                continue
            env = amp * math.exp(-t * (1.0 + ratio * 0.3))
            s += env * math.sin(2 * math.pi * p_freq * t)
        if t < 0.003:
            tremolo *= t / 0.003
        samples[i] = s * tremolo * 0.3
    return samples


def gen_singing_bowl(duration=5.0):
    """Tibetan singing bowl — long sustain, beating partials."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 0.5  # Lower
    samples = [0.0] * n
    # Close but not exact integer ratios create beating
    partials = [
        (1.0, 1.0, 0.4), (2.003, 0.7, 0.5), (3.009, 0.4, 0.7),
        (4.02, 0.25, 0.9), (5.04, 0.15, 1.2),
    ]
    for ratio, amp, decay in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


# ---------------------------------------------------------------------------
# PERCUSSION
# ---------------------------------------------------------------------------

def gen_kick_drum(duration=0.4):
    """Kick drum — sine with pitch drop."""
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n
    freq = 55.0
    phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        f = freq + freq * 4 * math.exp(-t * 30)
        phase += f / SAMPLE_RATE
        env = math.exp(-t * 8)
        s = math.sin(2 * math.pi * phase) * env
        samples[i] = math.tanh(s * 2.5) * 0.8
    return samples


def gen_snare_drum(duration=0.3):
    """Snare drum — body tone + noise."""
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(42)
    samples = [0.0] * n
    freq = 200.0
    phase = 0.0
    lpf = 0.0
    alpha = min(1.0, 2 * math.pi * 5000 / SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Body
        body_env = math.exp(-t * 20)
        phase += freq / SAMPLE_RATE
        body = math.sin(2 * math.pi * phase) * body_env * 0.5
        # Noise
        noise_env = math.exp(-t * 12)
        noise = (rng.random() * 2 - 1) * noise_env * 0.7
        lpf += alpha * (noise - lpf)
        samples[i] = (body + lpf) * 0.7
    return samples


def gen_hi_hat_closed(duration=0.08):
    """Closed hi-hat — filtered noise."""
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(43)
    samples = [0.0] * n
    hp = 0.0
    hp_alpha = min(1.0, 2 * math.pi * 7000 / SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 40)
        noise = rng.random() * 2 - 1
        hp += hp_alpha * (noise - hp)
        samples[i] = (noise - hp) * env * 0.4
    return samples


def gen_hi_hat_open(duration=0.3):
    """Open hi-hat — longer filtered noise."""
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(44)
    samples = [0.0] * n
    hp = 0.0
    hp_alpha = min(1.0, 2 * math.pi * 6000 / SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 8)
        noise = rng.random() * 2 - 1
        hp += hp_alpha * (noise - hp)
        samples[i] = (noise - hp) * env * 0.35
    return samples


def gen_cymbal_crash(duration=2.0):
    """Crash cymbal — noise with metallic ring."""
    n = int(SAMPLE_RATE * duration)
    rng = random.Random(45)
    samples = [0.0] * n
    # Metallic components
    freqs = [340, 683, 1020, 1505, 2100, 3200]
    hp = 0.0
    hp_alpha = min(1.0, 2 * math.pi * 4000 / SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 2.0)
        noise = (rng.random() * 2 - 1) * 0.5
        hp += hp_alpha * (noise - hp)
        metal = sum(0.1 * math.exp(-t * (1.5 + f / 1000)) *
                     math.sin(2 * math.pi * f * t) for f in freqs)
        samples[i] = ((noise - hp) * 0.5 + metal) * env * 0.4
    return samples


def gen_tom(duration=0.5):
    """Floor tom — pitched drum."""
    n = int(SAMPLE_RATE * duration)
    samples = [0.0] * n
    freq = 80.0
    phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        f = freq + freq * 1.5 * math.exp(-t * 20)
        phase += f / SAMPLE_RATE
        env = math.exp(-t * 5)
        samples[i] = math.sin(2 * math.pi * phase) * env * 0.7
    return samples


# ---------------------------------------------------------------------------
# WORLD INSTRUMENTS
# ---------------------------------------------------------------------------

def gen_sitar(duration=3.0):
    """Sitar — plucked with sympathetic resonance."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    # Main string + buzz bridge distortion
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 1.5)
        if t < 0.002:
            env *= t / 0.002
        s = math.sin(2 * math.pi * freq * t)
        # Add harmonics with slight nonlinearity (buzz bridge)
        for h in range(2, 10):
            h_freq = freq * h
            if h_freq >= SAMPLE_RATE / 2:
                break
            h_env = env * (0.3 / h)
            s += h_env * math.sin(2 * math.pi * h_freq * t)
        # Sympathetic string resonance
        s += 0.05 * env * math.sin(2 * math.pi * freq * 1.5 * t)
        s += 0.03 * env * math.sin(2 * math.pi * freq * 2.0 * t)
        # Buzz: mild clipping
        s = math.tanh(s * 2.0) * 0.5
        samples[i] = s * env * 0.4
    return samples


def gen_koto(duration=2.0):
    """Koto — Japanese plucked zither."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    harmonics = [1.0, 0.25, 0.12, 0.06, 0.03]
    for h_idx, h_amp in enumerate(harmonics):
        h_num = h_idx + 1
        h_freq = freq * h_num
        if h_freq >= SAMPLE_RATE / 2:
            break
        decay = 2.5 + h_num * 1.2
        for i in range(n):
            t = i / SAMPLE_RATE
            env = h_amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * h_freq * t)
    return samples


def gen_kalimba(duration=2.0):
    """Kalimba (thumb piano / mbira) — bright metallic pluck."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 2
    samples = [0.0] * n
    partials = [(1.0, 1.0), (5.42, 0.3), (11.3, 0.1)]
    for ratio, amp in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        decay = 3.0 * ratio
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.001:
                env *= t / 0.001
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


def gen_gamelan_gong(duration=5.0):
    """Gamelan gong — complex inharmonic spectra."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 0.5
    samples = [0.0] * n
    partials = [
        (1.0, 1.0, 0.5), (1.52, 0.6, 0.6), (2.1, 0.35, 0.8),
        (3.38, 0.2, 1.0), (4.7, 0.12, 1.3), (6.3, 0.07, 1.6),
    ]
    for ratio, amp, decay in partials:
        p_freq = freq * ratio
        if p_freq >= SAMPLE_RATE / 2:
            continue
        for i in range(n):
            t = i / SAMPLE_RATE
            env = amp * math.exp(-t * decay)
            if t < 0.005:
                env *= t / 0.005
            samples[i] += env * math.sin(2 * math.pi * p_freq * t)
    return samples


def gen_shakuhachi(duration=2.5):
    """Shakuhachi (bamboo flute) — breathy with pitch bends."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.1, 0.05, 0.8, 0.3)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Characteristic pitch wobble
        bend = 0.005 * math.sin(2 * math.pi * 3.0 * t) * min(1.0, t / 0.2)
        f = freq * (1 + bend)
        s = 0.7 * math.sin(2 * math.pi * f * t)
        s += 0.2 * math.sin(2 * math.pi * f * 2 * t)
        s += 0.05 * math.sin(2 * math.pi * f * 3 * t)
        # Air noise
        noise = (random.random() * 2 - 1) * 0.08
        s += noise * env[i]
        samples[i] = s * env[i] * 0.3
    return samples


def gen_didgeridoo(duration=4.0):
    """Didgeridoo — low drone with formant resonances."""
    n = int(SAMPLE_RATE * duration)
    freq = 65.0  # Low B1
    samples = [0.0] * n
    env = _adsr(n, 0.15, 0.1, 0.9, 0.4)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Fundamental + strong harmonics
        s = math.sin(2 * math.pi * freq * t)
        s += 0.5 * math.sin(2 * math.pi * freq * 2 * t)
        s += 0.4 * math.sin(2 * math.pi * freq * 3 * t)
        s += 0.3 * math.sin(2 * math.pi * freq * 4 * t)
        # Formant resonance (mouth cavity)
        formant = 0.15 * math.sin(2 * math.pi * 400 * t) * math.sin(2 * math.pi * 1.5 * t)
        s += formant
        # Breath modulation
        breath = 1.0 + 0.1 * math.sin(2 * math.pi * 2.0 * t)
        samples[i] = s * env[i] * breath * 0.25
    return samples


# ---------------------------------------------------------------------------
# PADS / SYNTH
# ---------------------------------------------------------------------------

def gen_warm_pad(duration=4.0):
    """Warm analog pad — detuned saws with filter."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.5, 0.2, 0.8, 1.0)
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for detune in [-0.03, -0.01, 0.01, 0.03]:
            f = freq * (1 + detune / 12)
            # Saw approximation (4 harmonics for smoothness)
            saw = 0.0
            for h in range(1, 5):
                h_freq = f * h
                if h_freq >= SAMPLE_RATE / 2:
                    break
                saw += math.sin(2 * math.pi * h_freq * t) / h
            s += saw * 0.25
        samples[i] = s * env[i] * 0.2
    return samples


def gen_string_ensemble(duration=4.0):
    """String ensemble pad — multiple detuned strings."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.4, 0.15, 0.85, 0.8)
    rng = random.Random(100)
    num_voices = 6
    detunes = [(rng.random() - 0.5) * 0.06 for _ in range(num_voices)]
    for i in range(n):
        t = i / SAMPLE_RATE
        s = 0.0
        for d in detunes:
            f = freq * (1 + d / 12)
            vib = 0.003 * math.sin(2 * math.pi * (4.5 + d * 10) * t)
            f *= (1 + vib)
            s += math.sin(2 * math.pi * f * t)
            s += 0.3 * math.sin(2 * math.pi * f * 2 * t)
        s /= num_voices
        samples[i] = s * env[i] * 0.3
    return samples


def gen_choir_pad(duration=4.0):
    """Choir "aah" pad — formant synthesis."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ
    samples = [0.0] * n
    env = _adsr(n, 0.5, 0.2, 0.85, 1.0)
    # "Aah" vowel formants (F1~800, F2~1200, F3~2500)
    formant_freqs = [800, 1200, 2500]
    formant_bw = [80, 90, 120]
    for i in range(n):
        t = i / SAMPLE_RATE
        # Source: pulse train
        source = 0.0
        for h in range(1, 12):
            h_freq = freq * h
            if h_freq >= SAMPLE_RATE / 2:
                break
            source += math.sin(2 * math.pi * h_freq * t) / h
        # Apply formant shaping (simplified)
        s = source
        # Weight harmonics by formant proximity
        amp_mod = 0.0
        for ff, bw in zip(formant_freqs, formant_bw):
            for h in range(1, 8):
                h_freq = freq * h
                dist = abs(h_freq - ff)
                amp_mod += 0.3 * math.exp(-dist * dist / (2 * bw * bw))
        s *= (0.3 + amp_mod * 0.3)
        samples[i] = s * env[i] * 0.15
    return samples


def gen_glass_pad(duration=4.0):
    """Glass / crystalline pad — high, pure tones."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 2
    samples = [0.0] * n
    env = _adsr(n, 0.8, 0.2, 0.7, 1.5)
    for i in range(n):
        t = i / SAMPLE_RATE
        s = math.sin(2 * math.pi * freq * t)
        s += 0.4 * math.sin(2 * math.pi * freq * 2.01 * t)  # Slight detune for shimmer
        s += 0.15 * math.sin(2 * math.pi * freq * 3.02 * t)
        samples[i] = s * env[i] * 0.2
    return samples


def gen_cosmic_drone(duration=5.0):
    """Cosmic space drone — evolving, mysterious."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ * 0.5
    samples = [0.0] * n
    env = _adsr(n, 1.0, 0.3, 0.8, 1.5)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Slow LFO modulating pitch
        lfo = 0.01 * math.sin(2 * math.pi * 0.1 * t)
        f = freq * (1 + lfo)
        s = math.sin(2 * math.pi * f * t)
        s += 0.5 * math.sin(2 * math.pi * f * 1.5 * t)  # Perfect 5th
        s += 0.3 * math.sin(2 * math.pi * f * 2.0 * t)
        # Add mysterious overtone
        s += 0.15 * math.sin(2 * math.pi * f * 3.14 * t)  # Non-integer ratio
        samples[i] = s * env[i] * 0.2
    return samples


# ---------------------------------------------------------------------------
# BASS
# ---------------------------------------------------------------------------

def gen_acoustic_bass(duration=2.0):
    """Acoustic upright bass."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 4  # Low
    samples = [0.0] * n
    harmonics = [1.0, 0.7, 0.4, 0.25, 0.15, 0.08]
    for h_idx, h_amp in enumerate(harmonics):
        h_num = h_idx + 1
        h_freq = freq * h_num
        if h_freq >= SAMPLE_RATE / 2:
            break
        decay = 2.0 + h_num * 0.5
        for i in range(n):
            t = i / SAMPLE_RATE
            env = h_amp * math.exp(-t * decay)
            if t < 0.008:
                env *= t / 0.008
            samples[i] += env * math.sin(2 * math.pi * h_freq * t)
    return samples


def gen_synth_bass(duration=1.5):
    """Synth bass — fat saw with filter sweep."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 4
    samples = [0.0] * n
    env = _adsr(n, 0.01, 0.1, 0.7, 0.2)
    for i in range(n):
        t = i / SAMPLE_RATE
        # Filter sweep: starts open, closes
        cutoff_ratio = 8.0 * math.exp(-t * 5.0) + 2.0
        s = 0.0
        for h in range(1, 15):
            h_freq = freq * h
            if h_freq >= SAMPLE_RATE / 2:
                break
            # Simple filter: attenuate above cutoff
            atten = 1.0 / (1.0 + (h / cutoff_ratio) ** 2)
            s += atten * math.sin(2 * math.pi * h_freq * t) / h
        samples[i] = math.tanh(s * 2.0) * env[i] * 0.4
    return samples


def gen_electric_bass(duration=1.5):
    """Electric bass — plucked."""
    n = int(SAMPLE_RATE * duration)
    freq = BASE_FREQ / 4
    samples = [0.0] * n
    harmonics = [1.0, 0.5, 0.3, 0.15, 0.08, 0.04]
    for h_idx, h_amp in enumerate(harmonics):
        h_num = h_idx + 1
        h_freq = freq * h_num
        if h_freq >= SAMPLE_RATE / 2:
            break
        decay = 3.0 + h_num * 1.5
        for i in range(n):
            t = i / SAMPLE_RATE
            env = h_amp * math.exp(-t * decay)
            if t < 0.003:
                env *= t / 0.003
            samples[i] += env * math.sin(2 * math.pi * h_freq * t)
    return samples


# ---------------------------------------------------------------------------
# MASTER CATALOG
# ---------------------------------------------------------------------------

SAMPLE_CATALOG = {
    # Piano / keyboard
    "piano": gen_piano,
    "electric_piano": gen_electric_piano,
    "harpsichord": gen_harpsichord,
    "celesta": gen_celesta,
    # Strings
    "violin": gen_violin,
    "viola": gen_viola,
    "cello": gen_cello,
    "harp": gen_harp,
    "pizzicato": gen_pizzicato,
    # Woodwinds
    "flute": gen_flute,
    "clarinet": gen_clarinet,
    "oboe": gen_oboe,
    "bassoon": gen_bassoon,
    # Brass
    "french_horn": gen_french_horn,
    "trumpet": gen_trumpet,
    "trombone": gen_trombone,
    # Bells / metallic
    "tubular_bell": gen_tubular_bell,
    "glockenspiel": gen_glockenspiel,
    "vibraphone": gen_vibraphone,
    "singing_bowl": gen_singing_bowl,
    # Percussion
    "kick_drum": gen_kick_drum,
    "snare_drum": gen_snare_drum,
    "hi_hat_closed": gen_hi_hat_closed,
    "hi_hat_open": gen_hi_hat_open,
    "cymbal_crash": gen_cymbal_crash,
    "tom": gen_tom,
    # World
    "sitar": gen_sitar,
    "koto": gen_koto,
    "kalimba": gen_kalimba,
    "gamelan_gong": gen_gamelan_gong,
    "shakuhachi": gen_shakuhachi,
    "didgeridoo": gen_didgeridoo,
    # Pads / synth
    "warm_pad": gen_warm_pad,
    "string_ensemble": gen_string_ensemble,
    "choir_pad": gen_choir_pad,
    "glass_pad": gen_glass_pad,
    "cosmic_drone": gen_cosmic_drone,
    # Bass
    "acoustic_bass": gen_acoustic_bass,
    "synth_bass": gen_synth_bass,
    "electric_bass": gen_electric_bass,
}


def generate_all_samples(output_dir):
    """Generate all instrument samples and write to WAV files.

    Returns dict mapping instrument name to file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = {}
    for name, gen_fn in SAMPLE_CATALOG.items():
        path = os.path.join(output_dir, f"{name}.wav")
        samples = gen_fn()
        _write_wav(path, samples)
        paths[name] = path
        print(f"  Generated: {name}.wav ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.1f}s)")
    return paths


def compress_to_mp3(wav_dir, mp3_dir=None, bitrate='128k'):
    """Convert all WAV samples to MP3 for smaller repo size.

    Requires ffmpeg.
    """
    import subprocess
    if mp3_dir is None:
        mp3_dir = wav_dir
    os.makedirs(mp3_dir, exist_ok=True)
    for name in SAMPLE_CATALOG:
        wav_path = os.path.join(wav_dir, f"{name}.wav")
        mp3_path = os.path.join(mp3_dir, f"{name}.mp3")
        if os.path.exists(wav_path):
            subprocess.run([
                'ffmpeg', '-y', '-i', wav_path,
                '-codec:a', 'libmp3lame', '-b:a', bitrate,
                mp3_path
            ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    print(f"  Compressed {len(SAMPLE_CATALOG)} samples to MP3")


if __name__ == '__main__':
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'samples'
    )
    print(f"Generating {len(SAMPLE_CATALOG)} instrument samples...")
    generate_all_samples(out_dir)
    print(f"\nDone. {len(SAMPLE_CATALOG)} samples written to {out_dir}/")
    print("Run with ffmpeg to compress: python sample_gen.py && python -c \"from sample_gen import *; compress_to_mp3('samples')\"")
