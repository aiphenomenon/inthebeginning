#!/usr/bin/env python3
"""
Audio renderer for the In The Beginning cosmic physics simulator.

Ports the TypeScript sonification mappings (apps/typescript/src/audio_engine.ts
and instruments.ts) to pure Python using only stdlib modules. Runs the Python
reference simulator and maps physics state to PCM audio samples, then writes
WAV or pipes to ffmpeg for MP3/streaming.

Usage:
    # Generate a 10-minute MP3
    python apps/audio/generate.py --duration 600 --output cosmic.mp3

    # Generate a WAV file
    python apps/audio/generate.py --duration 600 --format wav --output cosmic.wav

    # Stream to stdout (pipe to ffplay, aplay, or ffmpeg)
    python apps/audio/generate.py --duration 0 --format raw --output -

    # Internet radio (Icecast-compatible HTTP stream)
    python apps/audio/generate.py --radio --port 8000

    # Play through local speakers (via ffplay)
    python apps/audio/generate.py --play --duration 600

No external dependencies beyond Python stdlib + ffmpeg (for MP3 encoding).
"""

import argparse
import io
import math
import os
import random
import struct
import subprocess
import sys
import wave
import time
import socket
import threading

# ---------------------------------------------------------------------------
# Add project root to path so we can import the simulator
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from simulator.universe import Universe
from apps.audio.composer import Composer, AdditiveSynth, PercSynth, SCALES, EPOCH_SCALE_FAMILIES

# ---------------------------------------------------------------------------
# Audio constants
# ---------------------------------------------------------------------------
SAMPLE_RATE = 44100
CHANNELS = 2
BITS_PER_SAMPLE = 16
MAX_AMPLITUDE = 32767

# ---------------------------------------------------------------------------
# Epoch -> musical root (MIDI note), matching TypeScript audio_engine.ts
# ---------------------------------------------------------------------------
EPOCH_ROOTS = {
    "Planck": 60,        # C4
    "Inflation": 62,     # D4
    "Electroweak": 64,   # E4
    "Quark": 66,         # F#4
    "Hadron": 68,        # G#4
    "Nucleosynthesis": 70,  # Bb4
    "Recombination": 72,    # C5
    "Star Formation": 74,   # D5
    "Solar System": 76,     # E5
    "Earth": 78,            # F#5
    "Life": 80,             # G#5
    "DNA Era": 82,          # Bb5
    "Present": 84,          # C6
}

EPOCH_ORDER = [
    "Planck", "Inflation", "Electroweak", "Quark", "Hadron",
    "Nucleosynthesis", "Recombination", "Star Formation",
    "Solar System", "Earth", "Life", "DNA Era", "Present",
]


def mtof(note):
    """MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def clamp(v, lo, hi):
    """Clamp value to range."""
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Simple mixing buffer
# ---------------------------------------------------------------------------
class MixBuffer:
    """Stereo float sample buffer that accumulates audio from multiple voices."""

    def __init__(self, num_samples):
        self.left = [0.0] * num_samples
        self.right = [0.0] * num_samples
        self.num_samples = num_samples

    def add_mono(self, samples, offset, pan=0.0, gain=1.0):
        """Add mono samples at offset with stereo panning (-1..1)."""
        l_gain = gain * math.cos((pan + 1) * math.pi / 4)
        r_gain = gain * math.sin((pan + 1) * math.pi / 4)
        end = min(offset + len(samples), self.num_samples)
        for i in range(offset, end):
            s = samples[i - offset]
            self.left[i] += s * l_gain
            self.right[i] += s * r_gain

    def add_stereo(self, left, right, offset, gain=1.0):
        """Add stereo samples at offset."""
        end = min(offset + len(left), self.num_samples)
        for i in range(offset, end):
            self.left[i] += left[i - offset] * gain
            self.right[i] += right[i - offset] * gain

    def to_pcm16(self):
        """Convert to interleaved 16-bit PCM bytes with soft limiting."""
        n = self.num_samples
        data = bytearray(n * 4)  # 2 channels * 2 bytes
        left = self.left
        right = self.right
        amp = MAX_AMPLITUDE
        _tanh = math.tanh
        _pack = struct.pack_into
        for i in range(n):
            _pack('<hh', data, i * 4,
                  int(_tanh(left[i]) * amp),
                  int(_tanh(right[i]) * amp))
        return bytes(data)


# ---------------------------------------------------------------------------
# Instrument voices (ported from instruments.ts)
# ---------------------------------------------------------------------------

def gen_sine_blip(freq, duration=0.08, pan=0.0):
    """Quantum particle creation — rising sine chirp with exponential decay.

    Ports createSineBlip from instruments.ts.
    """
    n = int(SAMPLE_RATE * (duration + 0.01))
    samples = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        # Frequency rises from freq to freq*2.5 over duration
        progress = min(t / duration, 1.0)
        f = freq * (1.0 + 1.5 * progress)
        # Exponential amplitude decay
        amp = 0.25 * math.exp(-t / (duration * 0.3))
        phase = 2 * math.pi * f * t
        samples[i] = amp * math.sin(phase)
    return samples, pan


def gen_bell_tone(freq, decay=1.2):
    """Molecular bond formation — FM synthesis bell.

    Ports createBellTone from instruments.ts.
    Carrier: sine at freq. Modulator: sine at freq*1.4.
    """
    n = int(SAMPLE_RATE * (decay + 0.05))
    samples = [0.0] * n
    mod_freq = freq * 1.4
    for i in range(n):
        t = i / SAMPLE_RATE
        # Modulator with decaying index
        mod_amp = freq * 0.6 * math.exp(-t / (decay * 0.4))
        mod = mod_amp * math.sin(2 * math.pi * mod_freq * t)
        # Carrier frequency modulated
        carrier_phase = 2 * math.pi * (freq + mod) * t
        # Amplitude envelope
        amp = 0.20 * math.exp(-t / (decay * 0.35))
        samples[i] = amp * math.sin(carrier_phase)
    return samples


def gen_pulse(freq, width=0.15):
    """Cell division — square wave pulse with lowpass.

    Ports createPulse from instruments.ts.
    """
    n = int(SAMPLE_RATE * (width + 0.02))
    samples = [0.0] * n
    lpf_state = 0.0
    lpf_cutoff = freq * 4
    lpf_alpha = min(1.0, 2 * math.pi * lpf_cutoff / SAMPLE_RATE)
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = min(t / width, 1.0)
        # Frequency glides down: freq -> freq*0.5
        f = freq * (1.0 - 0.5 * progress)
        # Square wave
        phase = (f * t) % 1.0
        sq = 1.0 if phase < 0.5 else -1.0
        # Envelope
        if t < width * 0.1:
            amp = 0.18
        elif t < width:
            amp = 0.18 * math.exp(-(t - width * 0.1) / (width * 0.3))
        else:
            amp = 0.001
        raw = sq * amp
        # Simple lowpass
        lpf_state += lpf_alpha * (raw - lpf_state)
        samples[i] = lpf_state
    return samples


_PAD_WT_SIZE = 4096
_PAD_WT = [math.sin(2 * math.pi * i / _PAD_WT_SIZE) for i in range(_PAD_WT_SIZE)]
_PAD_INV_SR = 1.0 / SAMPLE_RATE


def gen_pad(notes, sustain=5.0):
    """Epoch ambient drone — layered detuned oscillators.

    Ports createPad from instruments.ts. Optimized with wavetable.
    Returns (left_samples, right_samples).
    """
    fade_in = 0.6
    fade_out = 1.2
    total = fade_in + sustain + fade_out
    n = int(SAMPLE_RATE * total)
    left = [0.0] * n
    right = [0.0] * n
    gain_per_note = 0.10 / max(1, len(notes))

    # Pre-compute envelope as array (shared by all oscillators)
    fade_in_end = int(fade_in * SAMPLE_RATE)
    sustain_end = int((fade_in + sustain) * SAMPLE_RATE)
    inv_fade_in = 1.0 / max(fade_in_end, 1)
    fade_out_tau = fade_out * 0.4

    env_arr = [0.0] * n
    for i in range(n):
        if i < fade_in_end:
            env_arr[i] = i * inv_fade_in
        elif i < sustain_end:
            env_arr[i] = 1.0
        else:
            remaining = (i - sustain_end) * _PAD_INV_SR
            env_arr[i] = max(0.001, math.exp(-remaining / fade_out_tau))

    wt = _PAD_WT
    wt_size = _PAD_WT_SIZE

    for note in notes:
        freq = mtof(note)
        for detune_cents in [-8, 8]:
            det_freq = freq * (2.0 ** (detune_cents / 1200.0))
            pan_l = 0.5 + (0.1 if detune_cents < 0 else -0.1)
            pan_r = 1.0 - pan_l
            phase_inc = det_freq * _PAD_INV_SR
            phase = 0.0
            g_l = gain_per_note * pan_l
            g_r = gain_per_note * pan_r
            for i in range(n):
                s = wt[int(phase * wt_size) % wt_size] * env_arr[i]
                left[i] += s * g_l
                right[i] += s * g_r
                phase += phase_inc

        # Triangle shimmer an octave above
        shimmer_freq = freq * 2
        phase_inc = shimmer_freq * _PAD_INV_SR
        phase = 0.0
        g = gain_per_note * 0.3 * 0.5
        for i in range(n):
            tri = 4.0 * abs((phase % 1.0) - 0.5) - 1.0
            s = tri * env_arr[i] * g
            left[i] += s
            right[i] += s
            phase += phase_inc

    return left, right


def gen_sequence(notes, tempo=8):
    """DNA transcription melody — sequence of sine tones.

    Ports createSequence from instruments.ts.
    """
    note_dur = 1.0 / tempo
    overlap = 0.02
    total_dur = len(notes) * note_dur + overlap
    n = int(SAMPLE_RATE * total_dur)
    samples = [0.0] * n

    for idx, midi_note in enumerate(notes):
        freq = mtof(midi_note)
        start_t = idx * note_dur
        start_sample = int(start_t * SAMPLE_RATE)
        note_samples = int((note_dur + overlap) * SAMPLE_RATE)

        for i in range(note_samples):
            si = start_sample + i
            if si >= n:
                break
            t = i / SAMPLE_RATE
            # Envelope: quick attack, exponential release
            if t < note_dur * 0.1:
                env = t / (note_dur * 0.1) * 0.12
            else:
                env = 0.12 * math.exp(-(t - note_dur * 0.1) / (note_dur * 0.3))
            samples[si] += env * math.sin(2 * math.pi * freq * t)

    return samples


# ---------------------------------------------------------------------------
# Simple convolution reverb (impulse response)
# ---------------------------------------------------------------------------

def gen_impulse_response(duration=2.0, decay=2.0):
    """Generate a reverb impulse response (stereo).

    Ports createImpulseResponse from audio_engine.ts.
    """
    n = int(SAMPLE_RATE * duration)
    left = [0.0] * n
    right = [0.0] * n
    rng = random.Random(12345)
    for i in range(n):
        envelope = (1 - i / n) ** decay
        left[i] = (rng.random() * 2 - 1) * envelope
        right[i] = (rng.random() * 2 - 1) * envelope
    return left, right


def apply_reverb(dry_l, dry_r, ir_l, ir_r, wet=0.2):
    """Apply convolution reverb (simplified — uses overlap-add with truncation)."""
    n = len(dry_l)
    ir_len = min(len(ir_l), SAMPLE_RATE)  # Truncate IR to 1 second for speed
    out_l = list(dry_l)
    out_r = list(dry_r)

    # Simple FIR convolution (decimated for performance)
    step = 8  # Process every 8th IR sample for speed
    for i in range(0, n, 1):
        wet_l = 0.0
        wet_r = 0.0
        for j in range(0, min(ir_len, i + 1), step):
            wet_l += dry_l[i - j] * ir_l[j]
            wet_r += dry_r[i - j] * ir_r[j]
        wet_l *= step  # Compensate for decimation
        wet_r *= step
        out_l[i] = dry_l[i] * (1 - wet * 0.5) + wet_l * wet
        out_r[i] = dry_r[i] * (1 - wet * 0.5) + wet_r * wet

    return out_l, out_r


# ---------------------------------------------------------------------------
# Simple biquad lowpass filter
# ---------------------------------------------------------------------------
class LowpassFilter:
    """Simple 2nd-order lowpass filter (biquad)."""

    def __init__(self, cutoff=8000.0, q=0.707):
        self.cutoff = cutoff
        self.q = q
        self._x1 = self._x2 = 0.0
        self._y1 = self._y2 = 0.0
        self._update_coeffs()

    def _update_coeffs(self):
        w0 = 2 * math.pi * self.cutoff / SAMPLE_RATE
        alpha = math.sin(w0) / (2 * self.q)
        cos_w0 = math.cos(w0)
        b0 = (1 - cos_w0) / 2
        b1 = 1 - cos_w0
        b2 = (1 - cos_w0) / 2
        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha
        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0
        self.a1 = a1 / a0
        self.a2 = a2 / a0

    def set_cutoff(self, cutoff):
        self.cutoff = clamp(cutoff, 20, SAMPLE_RATE / 2 - 100)
        self._update_coeffs()

    def process(self, x):
        y = self.b0 * x + self.b1 * self._x1 + self.b2 * self._x2 - self.a1 * self._y1 - self.a2 * self._y2
        self._x2 = self._x1
        self._x1 = x
        self._y2 = self._y1
        self._y1 = y
        return y

    def process_block(self, samples):
        n = len(samples)
        out = [0.0] * n
        b0, b1, b2 = self.b0, self.b1, self.b2
        a1, a2 = self.a1, self.a2
        x1, x2 = self._x1, self._x2
        y1, y2 = self._y1, self._y2
        for i in range(n):
            x = samples[i]
            y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2 = x1
            x1 = x
            y2 = y1
            y1 = y
            out[i] = y
        self._x1, self._x2 = x1, x2
        self._y1, self._y2 = y1, y2
        return out


# ---------------------------------------------------------------------------
# Main audio renderer
# ---------------------------------------------------------------------------
class CosmicAudioRenderer:
    """Maps the Python simulator to audio output.

    Drives the Universe simulator, captures physics state each tick,
    and produces corresponding audio. The enhanced mode uses the full
    Composer engine with world musical scales, polyrhythmic beats,
    polyphonic melodic voices, harmonic progressions, and additive
    synthesis timbres. The basic mode uses the original TypeScript-style
    sonification mappings.
    """

    def __init__(self, seed=42, ticks_per_second=50.0, enhanced=True):
        self.universe = Universe(seed=seed, max_ticks=999999999)
        self.seed = seed
        self.ticks_per_second = ticks_per_second
        self.samples_per_tick = int(SAMPLE_RATE / ticks_per_second)
        self.enhanced = enhanced

        # State tracking
        self._last_epoch = ""
        self._last_particle_count = 0
        self._last_blip_tick = -100
        self._last_bell_tick = -100
        self._last_pulse_tick = -100
        self._last_sequence_tick = -100
        self._silence_counter = 0  # Track silence to prevent dead air

        # Filters
        self._lpf_l = LowpassFilter(8000, 0.7)
        self._lpf_r = LowpassFilter(8000, 0.7)

        # Reverb IR (precomputed once)
        self._ir_l, self._ir_r = gen_impulse_response(1.5, 2.2)

        # Pad state
        self._pad_remaining_samples = 0
        self._pad_l = []
        self._pad_r = []
        self._pad_offset = 0

        # RNG for instrument variations
        self._rng = random.Random(seed + 1)

        # Enhanced composition engine
        if enhanced:
            self._composer = Composer(seed=seed)

    def _epoch_index(self, name):
        """Get numeric index for epoch name."""
        try:
            return EPOCH_ORDER.index(name)
        except ValueError:
            return 0

    def _root_note(self, epoch_name):
        """Get MIDI root note for current epoch."""
        return EPOCH_ROOTS.get(epoch_name, 60)

    def _chord_notes(self, root):
        """Minor-7 chord from root."""
        return [root, root + 3, root + 7, root + 10]

    def render_chunk(self, num_ticks):
        """Render audio for num_ticks simulation steps.

        Returns interleaved 16-bit PCM bytes (stereo, 44100 Hz).
        """
        total_samples = num_ticks * self.samples_per_tick
        mix = MixBuffer(total_samples)

        for tick_i in range(num_ticks):
            self.universe.step()
            sample_offset = tick_i * self.samples_per_tick

            # Get physics state
            epoch = self.universe.current_epoch_name
            epoch_idx = self._epoch_index(epoch)
            root = self._root_note(epoch)
            temp = self.universe.quantum_field.temperature
            particles = len(self.universe.quantum_field.particles)
            atoms = len(self.universe.atomic_system.atoms) if self.universe.atomic_system else 0
            molecules = len(self.universe.chemical_system.molecules) if self.universe.chemical_system else 0
            cells = len(self.universe.biosphere.cells) if self.universe.biosphere else 0
            generation = self.universe.biosphere.generation if self.universe.biosphere else 0

            # --- Temperature -> filter cutoff ---
            log_t = math.log10(max(1, temp))
            cutoff = 200 + (log_t / 10) * 15800
            cutoff = clamp(cutoff, 200, 16000)
            self._lpf_l.set_cutoff(cutoff)
            self._lpf_r.set_cutoff(cutoff)

            if self.enhanced:
                # --- Enhanced composition ---
                comp_l, comp_r = self._composer.compose_tick(
                    epoch, epoch_idx, root, temp,
                    particles, atoms, molecules, cells, generation,
                    self.samples_per_tick,
                )
                for i in range(self.samples_per_tick):
                    si = sample_offset + i
                    if si < total_samples:
                        mix.left[si] += comp_l[i]
                        mix.right[si] += comp_r[i]

            # --- Original simulation sonification (always active) ---
            # Epoch transition: schedule ambient pad
            if epoch != self._last_epoch:
                self._last_epoch = epoch
                self._schedule_pad(root)

            if self._pad_remaining_samples <= 0:
                self._schedule_pad(root)

            pad_end = min(self.samples_per_tick, self._pad_remaining_samples)
            for i in range(pad_end):
                si = sample_offset + i
                pi = self._pad_offset + i
                if si < total_samples and pi < len(self._pad_l):
                    # Reduce pad level in enhanced mode (composer has its own pads)
                    pad_gain = 0.3 if self.enhanced else 1.0
                    mix.left[si] += self._pad_l[pi] * pad_gain
                    mix.right[si] += self._pad_r[pi] * pad_gain
            self._pad_offset += pad_end
            self._pad_remaining_samples -= pad_end

            # Epoch-specific simulation sounds
            if epoch_idx <= 4:
                self._sonify_quantum(mix, sample_offset, root, particles, tick_i)
            elif epoch_idx <= 7:
                self._sonify_atomic(mix, sample_offset, root, atoms, tick_i)
            elif epoch_idx <= 9:
                self._sonify_chemistry(mix, sample_offset, root, molecules, tick_i)
            else:
                self._sonify_biology(mix, sample_offset, root, cells, generation, tick_i)

            # --- Silence prevention ---
            # Check energy level and inject dark matter / quantum texture if too quiet
            if self.enhanced and tick_i % 10 == 0:
                energy = sum(abs(s) for s in mix.left[max(0, sample_offset - 100):sample_offset + 1]) / 100
                if energy < 0.001:
                    self._silence_counter += 1
                    if self._silence_counter > 5:
                        # "Dark matter" texture — sub-bass drone + quantum shimmer
                        self._inject_dark_matter_texture(mix, sample_offset, root)
                        self._silence_counter = 0
                else:
                    self._silence_counter = 0

            self._last_particle_count = particles

        # Apply lowpass filter
        mix.left = self._lpf_l.process_block(mix.left)
        mix.right = self._lpf_r.process_block(mix.right)

        return mix.to_pcm16()

    def _inject_dark_matter_texture(self, mix, offset, root):
        """Fill silence with dark matter / quantum entanglement texture.

        When the simulation enters sparse regions (void of space), this
        produces a subtle sub-bass drone with high-frequency quantum
        shimmer — representing dark matter's gravitational hum and
        quantum vacuum fluctuations.
        """
        n = self.samples_per_tick * 3
        # Sub-bass drone (dark matter gravitational hum)
        sub_freq = mtof(max(24, root - 36))  # Very low
        # High shimmer (quantum vacuum fluctuations)
        shimmer_freq = mtof(root + 48)  # Very high

        for i in range(min(n, mix.num_samples - offset)):
            t = i / SAMPLE_RATE
            # Sub-bass
            sub = 0.04 * math.sin(2 * math.pi * sub_freq * t)
            # Shimmer — two detuned high sines
            sh1 = 0.02 * math.sin(2 * math.pi * shimmer_freq * t)
            sh2 = 0.015 * math.sin(2 * math.pi * shimmer_freq * 1.003 * t)
            # Slow amplitude modulation (quantum entanglement pulsing)
            entangle = 0.5 + 0.5 * math.sin(2 * math.pi * 0.3 * t)
            si = offset + i
            if si < mix.num_samples:
                mix.left[si] += sub + (sh1 + sh2) * entangle * 0.5
                mix.right[si] += sub + (sh1 + sh2) * entangle * 0.5

    def _schedule_pad(self, root):
        """Generate a new ambient pad."""
        chord = self._chord_notes(root)
        sustain = 2.0 if self.enhanced else 5.0  # Shorter in enhanced (composer has its own pad)
        self._pad_l, self._pad_r = gen_pad(chord, sustain)
        self._pad_remaining_samples = len(self._pad_l)
        self._pad_offset = 0

    def _sonify_quantum(self, mix, offset, root, particles, tick_i):
        """Quantum epoch: sine blips for particle creation."""
        new_particles = particles - self._last_particle_count
        cooldown = int(self.ticks_per_second * 0.06)
        if new_particles > 0 and (tick_i - self._last_blip_tick) > cooldown:
            count = min(new_particles, 3)
            for _ in range(count):
                # Full pitch range: from low rumbles to high chirps
                octave_shift = self._rng.choice([-12, 0, 12, 24])
                midi = root + octave_shift + self._rng.randint(0, 23)
                midi = clamp(midi, 28, 108)  # ~40Hz to ~4186Hz
                freq = mtof(midi)
                duration = 0.04 + self._rng.random() * 0.06
                pan = self._rng.random() * 2 - 1
                samples, _ = gen_sine_blip(freq, duration, pan)
                mix.add_mono(samples, offset, pan, 1.0)
            self._last_blip_tick = tick_i

    def _sonify_atomic(self, mix, offset, root, atoms, tick_i):
        """Atomic epoch: harmonic stacking for atom formation."""
        cooldown = int(self.ticks_per_second * 0.15)
        if atoms > 0 and (tick_i - self._last_blip_tick) > cooldown:
            fundamental = mtof(root - 12)
            harmonic = (atoms % 8) + 1
            freq = fundamental * harmonic
            n = int(SAMPLE_RATE * 0.55)
            samples = [0.0] * n
            for i in range(n):
                t = i / SAMPLE_RATE
                amp = 0.12 * math.exp(-t / 0.15)
                s1 = math.sin(2 * math.pi * freq * (2.0 ** (-6 / 1200.0)) * t)
                s2 = math.sin(2 * math.pi * freq * (2.0 ** (6 / 1200.0)) * t)
                samples[i] = amp * (s1 + s2) * 0.5
            pan = self._rng.random() * 1.2 - 0.6
            mix.add_mono(samples, offset, pan, 1.0)
            self._last_blip_tick = tick_i

    def _sonify_chemistry(self, mix, offset, root, molecules, tick_i):
        """Chemistry epoch: FM bell tones for bond formation."""
        cooldown = int(self.ticks_per_second * 0.3)
        if molecules > 0 and (tick_i - self._last_bell_tick) > cooldown:
            chord = self._chord_notes(root)
            note_idx = molecules % len(chord)
            freq = mtof(chord[note_idx])
            samples = gen_bell_tone(freq, 1.0)
            pan = self._rng.random() * 1.0 - 0.5
            mix.add_mono(samples, offset, pan, 1.0)
            self._last_bell_tick = tick_i

    def _sonify_biology(self, mix, offset, root, cells, generation, tick_i):
        """Biology epoch: pulses for cell division, melody for DNA."""
        cooldown_pulse = int(self.ticks_per_second * 0.4)
        if cells > 0 and (tick_i - self._last_pulse_tick) > cooldown_pulse:
            freq = mtof(root - 24)
            samples = gen_pulse(freq, 0.12)
            mix.add_mono(samples, offset, 0.0, 1.0)
            self._last_pulse_tick = tick_i

        cooldown_seq = int(self.ticks_per_second * 2.0)
        if (tick_i - self._last_sequence_tick) > cooldown_seq:
            if self.universe.biosphere and self.universe.biosphere.cells:
                cell = self.universe.biosphere.cells[0]
                if hasattr(cell, 'dna') and cell.dna and hasattr(cell.dna, 'sequence'):
                    dna_seq = cell.dna.sequence[:8]
                    base_to_interval = {'A': 0, 'T': 3, 'G': 5, 'C': 7}
                    seq_notes = []
                    evolve_shift = (generation % 4) * 2
                    for base in dna_seq:
                        b = base if isinstance(base, str) else str(base)
                        interval = base_to_interval.get(b, 0)
                        seq_notes.append(root + interval + evolve_shift)
                    if seq_notes:
                        samples = gen_sequence(seq_notes, 8)
                        mix.add_mono(samples, offset, 0.0, 1.0)
                        self._last_sequence_tick = tick_i


# ---------------------------------------------------------------------------
# Output modes
# ---------------------------------------------------------------------------

def write_wav(renderer, duration_seconds, output_path, progress=True):
    """Render simulation audio to a WAV file."""
    chunk_seconds = 1.0
    ticks_per_chunk = int(renderer.ticks_per_second * chunk_seconds)
    total_chunks = int(duration_seconds / chunk_seconds)

    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(BITS_PER_SAMPLE // 8)
        wf.setframerate(SAMPLE_RATE)

        for chunk_i in range(total_chunks):
            pcm = renderer.render_chunk(ticks_per_chunk)
            wf.writeframes(pcm)
            if progress and (chunk_i + 1) % 10 == 0:
                elapsed = chunk_i + 1
                pct = elapsed / total_chunks * 100
                epoch = renderer.universe.current_epoch_name
                tick = renderer.universe.tick
                sys.stderr.write(
                    f"\r  [{pct:5.1f}%] {elapsed}/{total_chunks}s "
                    f"| tick {tick} | epoch: {epoch}"
                )
                sys.stderr.flush()
        if progress:
            sys.stderr.write("\n")


def write_mp3(renderer, duration_seconds, output_path, bitrate='192k', progress=True):
    """Render simulation audio to MP3 via ffmpeg."""
    chunk_seconds = 1.0
    ticks_per_chunk = int(renderer.ticks_per_second * chunk_seconds)
    total_chunks = int(duration_seconds / chunk_seconds)

    cmd = [
        'ffmpeg', '-y',
        '-f', 's16le',
        '-ar', str(SAMPLE_RATE),
        '-ac', str(CHANNELS),
        '-i', 'pipe:0',
        '-codec:a', 'libmp3lame',
        '-b:a', bitrate,
        '-id3v2_version', '3',
        '-metadata', 'title=In The Beginning — Cosmic Simulation',
        '-metadata', 'artist=In The Beginning Simulator',
        '-metadata', 'album=Cosmic Sonification',
        '-metadata', 'genre=Ambient',
        '-metadata', 'comment=Generated from physics simulation. Inspired by Hatnote.',
        output_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for chunk_i in range(total_chunks):
        pcm = renderer.render_chunk(ticks_per_chunk)
        try:
            proc.stdin.write(pcm)
        except BrokenPipeError:
            break
        if progress and (chunk_i + 1) % 10 == 0:
            elapsed = chunk_i + 1
            pct = elapsed / total_chunks * 100
            epoch = renderer.universe.current_epoch_name
            tick = renderer.universe.tick
            sys.stderr.write(
                f"\r  [{pct:5.1f}%] {elapsed}/{total_chunks}s "
                f"| tick {tick} | epoch: {epoch}"
            )
            sys.stderr.flush()

    proc.stdin.close()
    proc.wait()
    if progress:
        sys.stderr.write("\n")


def play_local(renderer, duration_seconds):
    """Play audio through local speakers via ffplay."""
    ticks_per_chunk = int(renderer.ticks_per_second * 0.5)
    total_chunks = int(duration_seconds * 2) if duration_seconds > 0 else None

    cmd = [
        'ffplay', '-nodisp', '-autoexit',
        '-f', 's16le',
        '-ar', str(SAMPLE_RATE),
        '-ac', str(CHANNELS),
        '-i', 'pipe:0'
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.stderr.write("Error: ffplay not found. Install ffmpeg.\n")
        sys.exit(1)

    chunk_i = 0
    try:
        while total_chunks is None or chunk_i < total_chunks:
            pcm = renderer.render_chunk(ticks_per_chunk)
            try:
                proc.stdin.write(pcm)
            except BrokenPipeError:
                break
            chunk_i += 1
            if chunk_i % 20 == 0:
                epoch = renderer.universe.current_epoch_name
                sys.stderr.write(f"\r  Playing... tick {renderer.universe.tick} | epoch: {epoch}  ")
                sys.stderr.flush()
    except KeyboardInterrupt:
        pass
    finally:
        proc.stdin.close()
        proc.wait()
        sys.stderr.write("\n")


def stream_raw(renderer, duration_seconds):
    """Stream raw PCM to stdout (pipe to any audio tool)."""
    ticks_per_chunk = int(renderer.ticks_per_second * 0.5)
    total_chunks = int(duration_seconds * 2) if duration_seconds > 0 else None

    chunk_i = 0
    try:
        while total_chunks is None or chunk_i < total_chunks:
            pcm = renderer.render_chunk(ticks_per_chunk)
            sys.stdout.buffer.write(pcm)
            chunk_i += 1
    except (BrokenPipeError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Icecast-compatible HTTP audio stream (internet radio)
# ---------------------------------------------------------------------------

def run_radio(renderer, port=8000, host='0.0.0.0', bitrate='128k'):
    """Run an Icecast-compatible internet radio stream.

    Serves an MP3 audio stream over HTTP with ICY metadata.
    Compatible with VLC, iTunes, Winamp, and any internet radio client.

    The stream runs forever — the simulation loops with a new seed when
    the universe reaches the Present epoch.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    sys.stderr.write(f"\n  In The Beginning Radio\n")
    sys.stderr.write(f"  ──────────────────────\n")
    sys.stderr.write(f"  Stream URL: http://localhost:{port}/stream\n")
    sys.stderr.write(f"  Playlist:   http://localhost:{port}/listen.m3u\n")
    sys.stderr.write(f"  Bitrate:    {bitrate}\n")
    sys.stderr.write(f"  Inspired by Hatnote\n")
    sys.stderr.write(f"\n  Waiting for listeners...\n\n")

    clients = []
    clients_lock = threading.Lock()

    def handle_client(conn, addr):
        """Handle an incoming HTTP connection."""
        try:
            request = conn.recv(4096).decode('utf-8', errors='ignore')
            first_line = request.split('\r\n')[0] if request else ''

            # Check for ICY metadata support
            icy_metadata = 'icy-metadata:1' in request.lower()

            if '/listen.m3u' in first_line:
                # Serve M3U playlist
                playlist = f"#EXTM3U\n#EXTINF:-1,In The Beginning Radio\nhttp://localhost:{port}/stream\n"
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: audio/x-mpegurl\r\n"
                    f"Content-Length: {len(playlist)}\r\n"
                    "\r\n"
                    + playlist
                )
                conn.sendall(response.encode())
                conn.close()
                return

            if '/stream' not in first_line and '/ ' not in first_line:
                conn.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
                conn.close()
                return

            # ICY/HTTP response headers for audio stream
            icy_metaint = 16000  # Metadata interval in bytes
            headers = (
                "ICY 200 OK\r\n"
                "Content-Type: audio/mpeg\r\n"
                "icy-name: In The Beginning Radio\r\n"
                "icy-description: Cosmic physics simulation sonification — from Big Bang to life\r\n"
                "icy-genre: Ambient\r\n"
                "icy-url: https://github.com/aiphenomenon/inthebeginning\r\n"
                f"icy-br: {bitrate.replace('k','')}\r\n"
                "icy-pub: 1\r\n"
            )
            if icy_metadata:
                headers += f"icy-metaint: {icy_metaint}\r\n"
            headers += "\r\n"

            conn.sendall(headers.encode())

            with clients_lock:
                clients.append({
                    'conn': conn,
                    'addr': addr,
                    'icy': icy_metadata,
                    'metaint': icy_metaint,
                    'bytes_sent': 0,
                })
            sys.stderr.write(f"  + Listener connected: {addr[0]}:{addr[1]}\n")

        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def accept_loop():
        while True:
            try:
                conn, addr = server.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except Exception:
                break

    accept_thread = threading.Thread(target=accept_loop, daemon=True)
    accept_thread.start()

    # Main audio generation + broadcast loop
    ticks_per_chunk = int(renderer.ticks_per_second * 0.5)

    # Encode PCM -> MP3 via ffmpeg pipe
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 's16le',
        '-ar', str(SAMPLE_RATE),
        '-ac', str(CHANNELS),
        '-i', 'pipe:0',
        '-codec:a', 'libmp3lame',
        '-b:a', bitrate,
        '-f', 'mp3',
        'pipe:1'
    ]
    encoder = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    def read_encoded():
        """Read encoded MP3 data and broadcast to all clients."""
        while True:
            mp3_data = encoder.stdout.read(4096)
            if not mp3_data:
                break

            with clients_lock:
                dead = []
                for client in clients:
                    try:
                        if client['icy']:
                            # Insert ICY metadata at intervals
                            remaining = mp3_data
                            while remaining:
                                until_meta = client['metaint'] - (client['bytes_sent'] % client['metaint'])
                                chunk = remaining[:until_meta]
                                client['conn'].sendall(chunk)
                                client['bytes_sent'] += len(chunk)
                                remaining = remaining[len(chunk):]

                                if client['bytes_sent'] % client['metaint'] == 0:
                                    # Send ICY metadata
                                    epoch = renderer.universe.current_epoch_name
                                    tick = renderer.universe.tick
                                    title = f"In The Beginning — {epoch} (tick {tick})"
                                    meta = f"StreamTitle='{title}';"
                                    meta_bytes = meta.encode('utf-8')
                                    meta_len = (len(meta_bytes) + 15) // 16
                                    padded = meta_bytes.ljust(meta_len * 16, b'\x00')
                                    client['conn'].sendall(bytes([meta_len]) + padded)
                        else:
                            client['conn'].sendall(mp3_data)
                            client['bytes_sent'] += len(mp3_data)
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        dead.append(client)

                for d in dead:
                    clients.remove(d)
                    sys.stderr.write(f"  - Listener disconnected: {d['addr'][0]}:{d['addr'][1]}\n")
                    try:
                        d['conn'].close()
                    except Exception:
                        pass

    broadcast_thread = threading.Thread(target=read_encoded, daemon=True)
    broadcast_thread.start()

    # Generate audio forever
    try:
        while True:
            pcm = renderer.render_chunk(ticks_per_chunk)
            try:
                encoder.stdin.write(pcm)
            except BrokenPipeError:
                break

            epoch = renderer.universe.current_epoch_name
            tick = renderer.universe.tick

            # Loop simulation when reaching Present
            if epoch == "Present" and tick > 300000:
                new_seed = renderer.seed + tick
                sys.stderr.write(f"\n  Universe complete. Restarting with seed {new_seed}...\n")
                renderer.universe = Universe(seed=new_seed, max_ticks=999999999)
                renderer.seed = new_seed
                renderer._last_epoch = ""
                renderer._last_particle_count = 0

            # Status update
            with clients_lock:
                n_clients = len(clients)
            if tick % 1000 == 0:
                sys.stderr.write(
                    f"\r  Radio: tick {tick:>7} | {epoch:<16} | "
                    f"{n_clients} listener{'s' if n_clients != 1 else ''}  "
                )
                sys.stderr.flush()
    except KeyboardInterrupt:
        sys.stderr.write("\n  Shutting down radio...\n")
    finally:
        encoder.stdin.close()
        encoder.wait()
        server.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="In The Beginning — Cosmic Physics Sonification",
        epilog="Inspired by Hatnote. Generates audio from Big Bang to life.",
    )
    parser.add_argument('--duration', type=int, default=600,
                        help='Duration in seconds (0 = infinite, default: 600)')
    parser.add_argument('--output', '-o', default='cosmic_simulation.mp3',
                        help='Output file path (default: cosmic_simulation.mp3)')
    parser.add_argument('--format', choices=['mp3', 'wav', 'raw'], default=None,
                        help='Output format (auto-detected from extension)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Simulation seed (default: 42)')
    parser.add_argument('--tps', type=float, default=50.0,
                        help='Simulation ticks per second of audio (default: 50)')
    parser.add_argument('--bitrate', default='192k',
                        help='MP3 bitrate (default: 192k)')
    parser.add_argument('--radio', action='store_true',
                        help='Run as internet radio stream')
    parser.add_argument('--port', type=int, default=8000,
                        help='Radio stream port (default: 8000)')
    parser.add_argument('--play', action='store_true',
                        help='Play through local speakers via ffplay')
    parser.add_argument('--basic', action='store_true',
                        help='Use basic sonification only (no composer engine)')

    args = parser.parse_args()

    # Auto-detect format from extension
    fmt = args.format
    if fmt is None:
        if args.output == '-':
            fmt = 'raw'
        elif args.output.endswith('.wav'):
            fmt = 'wav'
        else:
            fmt = 'mp3'

    enhanced = not args.basic
    renderer = CosmicAudioRenderer(seed=args.seed, ticks_per_second=args.tps,
                                   enhanced=enhanced)
    mode_str = "enhanced" if enhanced else "basic"

    if args.radio:
        run_radio(renderer, port=args.port, bitrate=args.bitrate)
    elif args.play:
        sys.stderr.write(f"  Playing cosmic simulation [{mode_str}] (seed={args.seed})...\n")
        play_local(renderer, args.duration)
    elif args.output == '-':
        stream_raw(renderer, args.duration)
    elif fmt == 'wav':
        sys.stderr.write(f"  Rendering {args.duration}s WAV [{mode_str}] to {args.output}...\n")
        write_wav(renderer, args.duration, args.output)
        size = os.path.getsize(args.output)
        sys.stderr.write(f"  Done: {args.output} ({size / 1024 / 1024:.1f} MB)\n")
    else:
        sys.stderr.write(f"  Rendering {args.duration}s MP3 [{mode_str}] to {args.output}...\n")
        write_mp3(renderer, args.duration, args.output, args.bitrate)
        size = os.path.getsize(args.output)
        sys.stderr.write(f"  Done: {args.output} ({size / 1024 / 1024:.1f} MB)\n")


if __name__ == '__main__':
    main()
