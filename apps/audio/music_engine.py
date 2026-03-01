#!/usr/bin/env python3
"""
Structured music engine for cosmic simulation sonification.

This replaces the original composer with a bar-oriented, multi-track
architecture that produces structured, harmonic music with proper time
signatures, clean transitions, and real instrument samples.

Architecture:
    Universe state -> MusicDirector -> [Track, Track, Track, ...]
                                            |
                                            v
                                       MixBus -> PCM output

Key improvements over the original composer:
    - Bar-based structure: Music organized into bars with real time signatures
      (4/4, 3/4, 6/8, 7/8, 5/4, etc.) rather than random note triggers
    - Multi-track mixing: Separate instrument tracks (melody, harmony, bass,
      percussion, pad) that blend with proper gain staging
    - Sample-based instruments: Loads WAV/MP3 samples and pitch-shifts them
      for realistic timbres
    - Phrase repetition: Musical phrases repeat and develop, not random chaos
    - Frequency filtering: Highpass (>80Hz) and lowpass (<8kHz) to remove
      harsh noise and sub-rumble
    - Clean transitions: Crossfade between time signatures over 2-4 bars
    - Spectral safety: Limits output to 80Hz-8kHz human-comfortable range

No external dependencies — pure Python stdlib + optional numpy.
"""

import math
import os
import random
import struct
import wave

# Optional numpy for vectorized rendering
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SAMPLE_RATE = 44100
TWO_PI = 2 * math.pi
INV_SR = 1.0 / SAMPLE_RATE

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def mtof(note):
    """MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def ftom(freq):
    """Frequency to MIDI note number."""
    if freq <= 0:
        return 0
    return 69 + 12 * math.log2(freq / 440.0)

def clamp(v, lo, hi):
    """Clamp value to range."""
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# TIME SIGNATURES
# ---------------------------------------------------------------------------

class TimeSignature:
    """Represents a musical time signature with beat grouping.

    Attributes:
        numerator: Beats per bar (e.g. 4 in 4/4)
        denominator: Beat unit (e.g. 4 means quarter note)
        beat_groups: How beats are grouped (e.g. [2,2] for 4/4, [3,2,2] for 7/8)
        name: Human-readable name
    """

    def __init__(self, numerator, denominator, beat_groups=None, name=None):
        self.numerator = numerator
        self.denominator = denominator
        self.beat_groups = beat_groups or self._default_groups()
        self.name = name or f"{numerator}/{denominator}"

    def _default_groups(self):
        """Default beat groupings."""
        if self.numerator <= 4:
            return [self.numerator]
        # Common groupings for odd meters
        n = self.numerator
        if n == 5:
            return [3, 2]
        if n == 7:
            return [2, 2, 3]
        if n == 9:
            return [3, 3, 3]
        if n == 11:
            return [3, 3, 3, 2]
        if n == 13:
            return [3, 3, 3, 2, 2]
        return [n]

    def bar_duration(self, bpm):
        """Duration of one bar in seconds at given BPM."""
        beat_duration = 60.0 / bpm  # Duration of one beat unit
        # Adjust for denominator (8th note = half a quarter note beat)
        quarter_per_beat = 4.0 / self.denominator
        return self.numerator * beat_duration * quarter_per_beat

    def bar_samples(self, bpm):
        """Number of samples in one bar."""
        return int(self.bar_duration(bpm) * SAMPLE_RATE)

    def beat_positions(self, bpm):
        """Absolute positions of each beat within a bar (in samples).

        Returns list of (sample_position, is_downbeat, group_idx).
        """
        positions = []
        beat_dur = 60.0 / bpm * (4.0 / self.denominator) * SAMPLE_RATE
        pos = 0.0
        beat = 0
        for g_idx, group_size in enumerate(self.beat_groups):
            for b in range(group_size):
                is_down = (beat == 0) or (b == 0)
                positions.append((int(pos), is_down, g_idx))
                pos += beat_dur
                beat += 1
        return positions

    def strong_beats(self, bpm):
        """Return sample positions of strong (downbeat/group-start) beats."""
        return [p for p, is_down, _ in self.beat_positions(bpm) if is_down]


# Pre-defined time signatures for different musical eras
TIME_SIGNATURES = {
    # Standard Western
    "4/4":   TimeSignature(4, 4, [2, 2], "Common time"),
    "3/4":   TimeSignature(3, 4, [3], "Waltz"),
    "2/4":   TimeSignature(2, 4, [2], "March"),
    "6/8":   TimeSignature(6, 8, [3, 3], "Compound duple"),
    "9/8":   TimeSignature(9, 8, [3, 3, 3], "Compound triple"),
    "12/8":  TimeSignature(12, 8, [3, 3, 3, 3], "Compound quadruple"),
    # Complex / odd
    "5/4":   TimeSignature(5, 4, [3, 2], "Five-four"),
    "7/8":   TimeSignature(7, 8, [2, 2, 3], "Aksak (Balkan)"),
    "7/4":   TimeSignature(7, 4, [4, 3], "Seven-four"),
    "11/8":  TimeSignature(11, 8, [3, 3, 3, 2], "Eleven-eight"),
    # Additive
    "3+3+2/8": TimeSignature(8, 8, [3, 3, 2], "Tresillo"),
    "2+2+3/8": TimeSignature(7, 8, [2, 2, 3], "Additive seven"),
}

# Map epochs to preferred time signatures (more structure over time)
EPOCH_TIME_SIGS = {
    "Planck":          ["3/4"],
    "Inflation":       ["3/4", "4/4"],
    "Electroweak":     ["4/4", "6/8"],
    "Quark":           ["6/8", "3/4"],
    "Hadron":          ["4/4", "3/4"],
    "Nucleosynthesis": ["4/4", "6/8", "3/4"],
    "Recombination":   ["4/4", "3/4", "6/8"],
    "Star Formation":  ["4/4", "6/8", "5/4"],
    "Solar System":    ["4/4", "3/4", "9/8"],
    "Earth":           ["4/4", "6/8", "7/8"],
    "Life":            ["4/4", "3/4", "12/8"],
    "DNA Era":         ["4/4", "5/4", "7/8", "3+3+2/8"],
    "Present":         ["4/4", "3/4", "6/8", "5/4", "7/8"],
}


# ---------------------------------------------------------------------------
# SCALES AND CHORD SYSTEM
# ---------------------------------------------------------------------------

# Core scales (reduced from the full set for cleaner harmony)
SCALES = {
    "major":          [0, 2, 4, 5, 7, 9, 11],
    "natural_minor":  [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "dorian":         [0, 2, 3, 5, 7, 9, 10],
    "mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "lydian":         [0, 2, 4, 6, 7, 9, 11],
    "phrygian":       [0, 1, 3, 5, 7, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues":          [0, 3, 5, 6, 7, 10],
    "whole_tone":     [0, 2, 4, 6, 8, 10],
    "hirajoshi":      [0, 2, 3, 7, 8],
    "hijaz":          [0, 1, 4, 5, 7, 8, 11],
    "bhairav":        [0, 1, 4, 5, 7, 8, 11],
    "gamelan_pelog":  [0, 1, 3, 7, 8],
}

# Chord types as intervals from root
CHORD_TYPES = {
    "major":   [0, 4, 7],
    "minor":   [0, 3, 7],
    "dim":     [0, 3, 6],
    "aug":     [0, 4, 8],
    "maj7":    [0, 4, 7, 11],
    "min7":    [0, 3, 7, 10],
    "dom7":    [0, 4, 7, 10],
    "sus2":    [0, 2, 7],
    "sus4":    [0, 5, 7],
}

# Chord progressions — each entry is (degree, chord_type)
PROGRESSIONS = {
    "I-V-vi-IV":       [(0, "major"), (4, "major"), (5, "minor"), (3, "major")],
    "I-IV-V":          [(0, "major"), (3, "major"), (4, "major")],
    "i-VII-VI-V":      [(0, "minor"), (6, "major"), (5, "major"), (4, "major")],
    "I-vi-IV-V":       [(0, "major"), (5, "minor"), (3, "major"), (4, "major")],
    "vi-IV-I-V":       [(5, "minor"), (3, "major"), (0, "major"), (4, "major")],
    "I-V-vi-iii-IV":   [(0, "major"), (4, "major"), (5, "minor"), (2, "minor"), (3, "major")],
    "i-iv-v":          [(0, "minor"), (3, "minor"), (4, "minor")],
    "I-IV":            [(0, "major"), (3, "major")],
    "drone":           [(0, "sus2")],
    "min-drift":       [(0, "minor"), (5, "minor"), (3, "major")],
}

# Map epochs to preferred progressions and scales
EPOCH_MUSIC_STYLE = {
    "Planck":          {"scales": ["whole_tone"], "progs": ["drone"], "tempo_range": (40, 55)},
    "Inflation":       {"scales": ["pentatonic_major"], "progs": ["drone", "I-IV"], "tempo_range": (45, 60)},
    "Electroweak":     {"scales": ["phrygian", "hirajoshi"], "progs": ["i-iv-v", "drone"], "tempo_range": (50, 65)},
    "Quark":           {"scales": ["pentatonic_minor", "dorian"], "progs": ["i-iv-v", "min-drift"], "tempo_range": (55, 72)},
    "Hadron":          {"scales": ["dorian", "mixolydian"], "progs": ["I-IV-V", "I-IV"], "tempo_range": (60, 80)},
    "Nucleosynthesis": {"scales": ["major", "dorian"], "progs": ["I-IV-V", "I-V-vi-IV"], "tempo_range": (65, 85)},
    "Recombination":   {"scales": ["major", "lydian"], "progs": ["I-V-vi-IV", "I-vi-IV-V"], "tempo_range": (70, 90)},
    "Star Formation":  {"scales": ["lydian", "hijaz"], "progs": ["I-V-vi-IV", "vi-IV-I-V"], "tempo_range": (75, 95)},
    "Solar System":    {"scales": ["major", "harmonic_minor"], "progs": ["I-V-vi-IV", "I-V-vi-iii-IV"], "tempo_range": (80, 100)},
    "Earth":           {"scales": ["major", "natural_minor", "blues"], "progs": ["I-V-vi-IV", "i-VII-VI-V"], "tempo_range": (85, 110)},
    "Life":            {"scales": ["pentatonic_major", "blues", "dorian"], "progs": ["I-V-vi-IV", "I-IV-V"], "tempo_range": (90, 120)},
    "DNA Era":         {"scales": ["major", "dorian", "gamelan_pelog"], "progs": ["I-V-vi-IV", "vi-IV-I-V"], "tempo_range": (95, 130)},
    "Present":         {"scales": ["major", "dorian", "pentatonic_major", "lydian"], "progs": ["I-V-vi-IV", "I-vi-IV-V", "vi-IV-I-V"], "tempo_range": (85, 135)},
}


# ---------------------------------------------------------------------------
# SAMPLE LOADER
# ---------------------------------------------------------------------------

class SampleBank:
    """Loads and caches instrument samples, providing pitch-shifted playback.

    Loads WAV or MP3 samples from the samples/ directory. Each sample is
    recorded at C4 (MIDI 60). To play other notes, the sample is resampled
    (pitch-shifted) by changing playback rate.
    """

    def __init__(self, samples_dir=None, preload=True):
        if samples_dir is None:
            samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples')
        self.samples_dir = samples_dir
        self._cache = {}  # name -> (float_samples, original_freq)
        self._pitch_cache = {}  # (name, midi_note) -> float_samples
        if preload:
            self._preload_all()

    def _preload_all(self):
        """Preload all samples at startup to avoid ffmpeg latency during rendering."""
        if not os.path.isdir(self.samples_dir):
            return
        for fname in os.listdir(self.samples_dir):
            if fname.endswith('.mp3') or fname.endswith('.wav'):
                name = fname.rsplit('.', 1)[0]
                self.load(name)

    def load(self, name):
        """Load a sample by name. Returns float samples or None."""
        if name in self._cache:
            return self._cache[name]

        # Try WAV first, then MP3 (decode via subprocess)
        wav_path = os.path.join(self.samples_dir, f"{name}.wav")
        mp3_path = os.path.join(self.samples_dir, f"{name}.mp3")

        samples = None
        if os.path.exists(wav_path):
            samples = self._load_wav(wav_path)
        elif os.path.exists(mp3_path):
            samples = self._load_mp3(mp3_path)

        if samples is not None:
            self._cache[name] = (samples, 261.63)  # C4 base
            return self._cache[name]
        return None

    def _load_wav(self, path):
        """Load WAV file as float samples."""
        try:
            with wave.open(path, 'rb') as wf:
                n_frames = wf.getnframes()
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                data = wf.readframes(n_frames)

                if sample_width == 2:
                    fmt = f'<{n_frames * n_channels}h'
                    raw = struct.unpack(fmt, data)
                elif sample_width == 1:
                    raw = [(b - 128) * 256 for b in data]
                else:
                    return None

                # Convert to mono float
                if n_channels > 1:
                    mono = []
                    for i in range(0, len(raw), n_channels):
                        mono.append(sum(raw[i:i+n_channels]) / n_channels / 32768.0)
                    return mono
                return [s / 32768.0 for s in raw]
        except Exception:
            return None

    def _load_mp3(self, path):
        """Load MP3 by decoding to raw PCM via ffmpeg."""
        import subprocess
        try:
            result = subprocess.run([
                'ffmpeg', '-i', path,
                '-f', 's16le', '-ac', '1', '-ar', str(SAMPLE_RATE),
                'pipe:1'
            ], capture_output=True, timeout=10)
            if result.returncode != 0:
                return None
            data = result.stdout
            n = len(data) // 2
            raw = struct.unpack(f'<{n}h', data)
            return [s / 32768.0 for s in raw]
        except Exception:
            return None

    def get_pitched(self, name, midi_note, duration_samples=None):
        """Get a sample pitched to the given MIDI note.

        Uses numpy-accelerated linear interpolation resampling when available.
        """
        cache_key = (name, midi_note, duration_samples)
        if cache_key in self._pitch_cache:
            return self._pitch_cache[cache_key]

        loaded = self.load(name)
        if loaded is None:
            return None

        base_samples, base_freq = loaded
        target_freq = mtof(midi_note)
        ratio = target_freq / base_freq  # Playback speed ratio

        if abs(ratio - 1.0) < 0.001:
            result = list(base_samples)
        elif HAS_NUMPY:
            # Vectorized resampling with numpy
            src = np.asarray(base_samples, dtype=np.float64)
            src_len = len(src)
            if duration_samples is None:
                out_len = int(src_len / ratio)
            else:
                out_len = duration_samples
            indices = np.arange(out_len, dtype=np.float64) * ratio
            valid = indices < (src_len - 1)
            idx = np.clip(indices.astype(np.int64), 0, src_len - 2)
            frac = indices - idx
            out = np.where(valid,
                           src[idx] * (1 - frac) + src[np.minimum(idx + 1, src_len - 1)] * frac,
                           0.0)
            result = out.tolist()
        else:
            # Python fallback
            src_len = len(base_samples)
            if duration_samples is None:
                out_len = int(src_len / ratio)
            else:
                out_len = duration_samples
            result = [0.0] * out_len
            for i in range(out_len):
                src_pos = i * ratio
                idx = int(src_pos)
                frac = src_pos - idx
                if idx + 1 < src_len:
                    result[i] = base_samples[idx] * (1 - frac) + base_samples[idx + 1] * frac
                elif idx < src_len:
                    result[i] = base_samples[idx] * (1 - frac)

        # Trim or pad to duration
        if duration_samples is not None:
            if len(result) > duration_samples:
                result = result[:duration_samples]
            elif len(result) < duration_samples:
                result.extend([0.0] * (duration_samples - len(result)))

        # Cache a limited number of results
        if len(self._pitch_cache) < 512:
            self._pitch_cache[cache_key] = result
        return result


# Global sample bank (lazy-loaded)
_sample_bank = None

def get_sample_bank():
    """Get or create the global sample bank."""
    global _sample_bank
    if _sample_bank is None:
        _sample_bank = SampleBank()
    return _sample_bank


# ---------------------------------------------------------------------------
# INSTRUMENT TRACK
# ---------------------------------------------------------------------------

class Track:
    """A single instrument track that renders bars of music.

    Each track represents one instrument voice (e.g., piano melody,
    bass line, string pad, percussion). Tracks are mixed together
    by the MixBus.

    Attributes:
        name: Track identifier
        instrument: Sample name from SampleBank
        gain: Track volume (0.0 to 1.0)
        pan: Stereo position (-1.0 left to 1.0 right)
        active: Whether this track is currently playing
    """

    def __init__(self, name, instrument, gain=0.15, pan=0.0):
        self.name = name
        self.instrument = instrument
        self.gain = gain
        self.pan = pan
        self.active = True
        self._buffer = None  # Pre-rendered bar buffer
        self._buffer_pos = 0
        self._crossfade_in = 0  # Samples of crossfade remaining
        self._crossfade_total = 0

    def render_bar(self, notes, bar_samples, time_sig, bpm, rng):
        """Render one bar of music for this track.

        Args:
            notes: List of (beat_position, midi_note, duration_beats) or None
            bar_samples: Total samples in this bar
            time_sig: TimeSignature object
            bpm: Current tempo

        Returns:
            Float sample list (mono).
        """
        if notes is None or not self.active:
            return [0.0] * bar_samples

        bank = get_sample_bank()
        if HAS_NUMPY:
            out = np.zeros(bar_samples, dtype=np.float64)
        else:
            out = [0.0] * bar_samples
        beat_dur_samples = int(60.0 / bpm * (4.0 / time_sig.denominator) * SAMPLE_RATE)

        for beat_pos, midi, dur_beats in notes:
            start = int(beat_pos * beat_dur_samples)
            if start >= bar_samples:
                continue
            note_samples = int(dur_beats * beat_dur_samples)
            note_samples = min(note_samples, bar_samples - start)

            # Get pitched sample
            pitched = bank.get_pitched(self.instrument, midi, note_samples)
            if pitched is None:
                pitched = self._synth_fallback(midi, note_samples)

            # Apply per-note envelope (prevent clicks) and mix
            fade = min(int(0.005 * SAMPLE_RATE), note_samples // 4)
            count = min(len(pitched), note_samples, bar_samples - start)

            if HAS_NUMPY and count > 0:
                arr = np.asarray(pitched[:count], dtype=np.float64)
                # Vectorized fade in/out
                if fade > 0 and count > fade:
                    arr[:fade] *= np.linspace(0, 1, fade)
                    fade_out_start = max(0, count - fade)
                    arr[fade_out_start:count] *= np.linspace(1, 0, count - fade_out_start)
                out[start:start + count] += arr * self.gain
            else:
                for i in range(count):
                    s = pitched[i]
                    if i < fade:
                        s *= i / max(fade, 1)
                    if i > note_samples - fade:
                        s *= (note_samples - i) / max(fade, 1)
                    if start + i < bar_samples:
                        out[start + i] += s * self.gain

        if HAS_NUMPY:
            return out.tolist()
        return out

    def _synth_fallback(self, midi, num_samples):
        """Simple sine fallback when sample is not available."""
        freq = mtof(midi)
        out = [0.0] * num_samples
        phase_inc = freq * INV_SR
        phase = 0.0
        for i in range(num_samples):
            t = i * INV_SR
            env = 1.0
            if t < 0.01:
                env = t / 0.01
            if i > num_samples - int(0.02 * SAMPLE_RATE):
                remaining = num_samples - i
                env = remaining / max(int(0.02 * SAMPLE_RATE), 1)
            out[i] = math.sin(TWO_PI * phase) * env * 0.3
            phase += phase_inc
        return out


# ---------------------------------------------------------------------------
# PHRASE GENERATOR
# ---------------------------------------------------------------------------

class PhraseGenerator:
    """Generates musical phrases (note sequences) for a bar.

    Creates melodic lines, bass lines, chord voicings, and drum patterns
    based on the current musical state (key, scale, chord, time signature).
    """

    # Classic melodic motifs (intervals from chord root, in scale degrees)
    MELODY_PATTERNS = [
        # Ascending patterns
        [0, 1, 2, 3, 4],
        [0, 2, 4, 2, 0],
        [0, 0, 4, 4, 5, 5, 4],  # Twinkle-like
        [0, 4, 3, 2, 1, 0],     # Descending scale
        # Arpeggiated
        [0, 2, 4, 2],
        [0, 2, 4, 6, 4, 2],
        [4, 2, 0, 2, 4],
        # Stepwise
        [0, 1, 0, -1, 0],
        [0, 1, 2, 1, 0, -1, 0],
        # Leap then step
        [0, 4, 3, 2],
        [0, -3, -2, -1, 0],
        # Repetitive (good for rhythm)
        [0, 0, 2, 2, 4, 4, 2],
        [0, 2, 0, 2, 4, 2, 0],
    ]

    # Bass patterns (scale degree movements)
    BASS_PATTERNS = [
        [0],                    # Root only
        [0, 0, 4, 4],          # Root-fifth
        [0, 4, 0, 4],          # Alternating
        [0, 2, 4, 2],          # Walking bass
        [0, 0, 0, 4],          # Root with fifth approach
        [0, -1, 0, 4],         # Chromatic approach
    ]

    # Drum patterns (hit_type, beat_position_fraction)
    # hit_type: 0=kick, 1=snare, 2=hihat, 3=tom
    DRUM_PATTERNS_44 = [
        # Basic rock
        [(0, 0.0), (2, 0.0), (2, 0.5), (1, 1.0), (2, 1.0), (2, 1.5),
         (0, 2.0), (2, 2.0), (2, 2.5), (1, 3.0), (2, 3.0), (2, 3.5)],
        # Four on the floor
        [(0, 0.0), (2, 0.5), (0, 1.0), (2, 1.5), (0, 2.0), (2, 2.5), (0, 3.0), (2, 3.5)],
        # Sparse
        [(0, 0.0), (1, 2.0)],
        # Bossa nova
        [(0, 0.0), (2, 0.5), (2, 1.0), (0, 1.5), (2, 2.0), (2, 2.5), (0, 3.0), (2, 3.5)],
    ]

    DRUM_PATTERNS_34 = [
        # Waltz: bass on 1, hihat on 2 and 3
        [(0, 0.0), (2, 1.0), (2, 2.0)],
        # With snare
        [(0, 0.0), (1, 1.0), (2, 2.0)],
    ]

    DRUM_PATTERNS_68 = [
        # 6/8 feel
        [(0, 0.0), (2, 1.0), (2, 2.0), (1, 3.0), (2, 4.0), (2, 5.0)],
    ]

    def __init__(self, rng):
        self.rng = rng
        self._last_melody_pattern = -1
        self._melody_transposition = 0
        self._phrase_count = 0

    def generate_melody(self, root, scale, chord_notes, time_sig, bars_in_phrase=2):
        """Generate a melodic phrase spanning multiple bars.

        Returns list of bars, each bar being list of (beat_pos, midi, dur).
        """
        # Pick a pattern, preferring different from last
        pattern_idx = self.rng.randint(0, len(self.MELODY_PATTERNS) - 1)
        if pattern_idx == self._last_melody_pattern and len(self.MELODY_PATTERNS) > 1:
            pattern_idx = (pattern_idx + 1) % len(self.MELODY_PATTERNS)
        self._last_melody_pattern = pattern_idx
        pattern = self.MELODY_PATTERNS[pattern_idx]

        bars = []
        for bar_i in range(bars_in_phrase):
            notes = []
            beats_per_bar = time_sig.numerator
            beats_available = beats_per_bar

            # Scale the pattern to fill the bar
            step_dur = max(0.5, beats_available / max(len(pattern), 1))
            # Add some rhythmic variation
            if self.rng.random() < 0.3:
                step_dur *= 0.5  # Double time

            pos = 0.0
            for p_idx, degree in enumerate(pattern):
                if pos >= beats_available:
                    break
                # Convert scale degree to MIDI note
                midi = self._degree_to_midi(degree, root, scale)
                # Octave: melody should be in comfortable range (C4-C6)
                midi = clamp(midi, 60, 84)
                dur = min(step_dur, beats_available - pos)
                # Slight variation in second bar
                if bar_i > 0 and self.rng.random() < 0.2:
                    midi += self.rng.choice([-2, -1, 1, 2])
                    midi = clamp(midi, 60, 84)
                notes.append((pos, midi, dur))
                pos += step_dur

            bars.append(notes)

        self._phrase_count += 1
        return bars

    def generate_bass(self, root, scale, chord_degree, time_sig):
        """Generate a bass line for one bar.

        Returns list of (beat_pos, midi, dur).
        """
        pattern = self.rng.choice(self.BASS_PATTERNS)
        notes = []
        beats = time_sig.numerator
        step = max(1.0, beats / max(len(pattern), 1))

        for p_idx, degree in enumerate(pattern):
            pos = p_idx * step
            if pos >= beats:
                break
            midi = self._degree_to_midi(degree + chord_degree, root, scale)
            # Bass in low octave (C2-C3)
            while midi > 48:
                midi -= 12
            while midi < 36:
                midi += 12
            dur = min(step, beats - pos)
            notes.append((pos, midi, dur * 0.9))  # Slight gap between notes

        return notes

    def generate_chord_voicing(self, root, scale, chord_degree, chord_type, time_sig):
        """Generate chord notes for a pad/harmony track.

        Returns list of (beat_pos, midi, dur) — chord sustained for full bar.
        """
        intervals = CHORD_TYPES.get(chord_type, [0, 4, 7])
        chord_root = root + chord_degree
        notes = []
        dur = float(time_sig.numerator)

        for interval in intervals:
            midi = chord_root + interval
            # Voicing: spread across C3-C5 range
            while midi < 48:
                midi += 12
            while midi > 72:
                midi -= 12
            notes.append((0.0, midi, dur))

        return notes

    def generate_drums(self, time_sig, intensity=0.5):
        """Generate a drum pattern for one bar.

        Returns list of (beat_pos, drum_type, velocity).
        drum_type: 'kick', 'snare', 'hihat_closed', 'hihat_open', 'tom'
        """
        # Select pattern based on time signature
        if time_sig.numerator == 3 and time_sig.denominator == 4:
            patterns = self.DRUM_PATTERNS_34
        elif time_sig.numerator == 6 and time_sig.denominator == 8:
            patterns = self.DRUM_PATTERNS_68
        else:
            patterns = self.DRUM_PATTERNS_44

        raw = self.rng.choice(patterns)
        result = []
        type_map = {0: "kick_drum", 1: "snare_drum", 2: "hi_hat_closed", 3: "tom"}

        for hit_type, pos in raw:
            if self.rng.random() > intensity and hit_type != 0:
                continue  # Skip non-kick hits based on intensity
            drum = type_map.get(hit_type, "hi_hat_closed")
            velocity = 0.5 + self.rng.random() * 0.5
            # Downbeat is louder
            if pos == 0.0:
                velocity = min(1.0, velocity * 1.2)
            result.append((pos, drum, velocity))

        return result

    def _degree_to_midi(self, degree, root, scale):
        """Convert a scale degree to MIDI note number."""
        if not scale:
            scale = [0, 2, 4, 5, 7, 9, 11]
        octave = 0
        d = int(round(degree))
        while d < 0:
            d += len(scale)
            octave -= 1
        while d >= len(scale):
            d -= len(scale)
            octave += 1
        return root + scale[d] + octave * 12


# ---------------------------------------------------------------------------
# DRUM TRACK (special handling — uses sample bank for percussion)
# ---------------------------------------------------------------------------

class DrumTrack:
    """Specialized track for percussion rendering.

    Unlike melodic tracks, drums use hit patterns rather than pitched notes.
    Each drum type maps to a specific sample.
    """

    def __init__(self, gain=0.12, pan=0.0):
        self.gain = gain
        self.pan = pan
        self.active = True

    def render_bar(self, hits, bar_samples, time_sig, bpm):
        """Render drum hits for one bar.

        Args:
            hits: List of (beat_pos, drum_name, velocity)
            bar_samples: Total samples in this bar
            time_sig: TimeSignature
            bpm: Current tempo

        Returns:
            Float sample list (mono).
        """
        if not hits or not self.active:
            return [0.0] * bar_samples

        bank = get_sample_bank()
        out = [0.0] * bar_samples
        beat_dur_samples = int(60.0 / bpm * (4.0 / time_sig.denominator) * SAMPLE_RATE)

        for beat_pos, drum_name, velocity in hits:
            start = int(beat_pos * beat_dur_samples)
            if start >= bar_samples:
                continue

            # Get drum sample (no pitch shifting — use as-is)
            loaded = bank.load(drum_name)
            if loaded:
                samples, _ = loaded
            else:
                continue

            # Mix in with velocity scaling
            v = velocity * self.gain
            for i in range(min(len(samples), bar_samples - start)):
                out[start + i] += samples[i] * v

        return out


# ---------------------------------------------------------------------------
# BIQUAD FILTERS (highpass + lowpass for frequency safety)
# ---------------------------------------------------------------------------

class BiquadFilter:
    """Second-order biquad filter for frequency shaping.

    Supports lowpass and highpass modes.
    """

    def __init__(self, cutoff, q=0.707, filter_type='lowpass'):
        self.cutoff = cutoff
        self.q = q
        self.filter_type = filter_type
        self._x1 = self._x2 = 0.0
        self._y1 = self._y2 = 0.0
        self._compute_coeffs()

    def _compute_coeffs(self):
        """Compute filter coefficients."""
        w0 = TWO_PI * self.cutoff / SAMPLE_RATE
        alpha = math.sin(w0) / (2 * self.q)
        cos_w0 = math.cos(w0)

        if self.filter_type == 'lowpass':
            b0 = (1 - cos_w0) / 2
            b1 = 1 - cos_w0
            b2 = (1 - cos_w0) / 2
        elif self.filter_type == 'highpass':
            b0 = (1 + cos_w0) / 2
            b1 = -(1 + cos_w0)
            b2 = (1 + cos_w0) / 2
        else:
            b0 = b1 = b2 = 0

        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha

        self.b0 = b0 / a0
        self.b1 = b1 / a0
        self.b2 = b2 / a0
        self.a1 = a1 / a0
        self.a2 = a2 / a0

    def process_block(self, samples):
        """Process a block of samples. Accepts list or numpy array."""
        if HAS_NUMPY:
            arr = np.asarray(samples, dtype=np.float64) if not isinstance(samples, np.ndarray) else samples
        else:
            arr = samples
        n = len(arr)
        out = [0.0] * n
        b0, b1, b2 = self.b0, self.b1, self.b2
        a1, a2 = self.a1, self.a2
        x1, x2 = self._x1, self._x2
        y1, y2 = self._y1, self._y2
        for i in range(n):
            x = float(arr[i])
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
# MIX BUS
# ---------------------------------------------------------------------------

class MixBus:
    """Mixes multiple tracks into stereo output with filtering.

    Applies:
    - Per-track gain and panning
    - Master highpass (removes sub-bass rumble below 80Hz)
    - Master lowpass (removes harsh frequencies above 8kHz)
    - Soft limiter (prevents clipping)
    """

    def __init__(self):
        self.master_gain = 0.85
        # Frequency safety filters
        self._hpf_l = BiquadFilter(80.0, 0.707, 'highpass')
        self._hpf_r = BiquadFilter(80.0, 0.707, 'highpass')
        self._lpf_l = BiquadFilter(8000.0, 0.707, 'lowpass')
        self._lpf_r = BiquadFilter(8000.0, 0.707, 'lowpass')

    def set_lowpass(self, cutoff):
        """Adjust lowpass cutoff (e.g. based on epoch temperature)."""
        cutoff = clamp(cutoff, 1000, 12000)
        self._lpf_l = BiquadFilter(cutoff, 0.707, 'lowpass')
        self._lpf_r = BiquadFilter(cutoff, 0.707, 'lowpass')

    def mix_tracks(self, track_buffers, num_samples):
        """Mix track buffers into stereo output.

        Args:
            track_buffers: List of (mono_samples, gain, pan) tuples
            num_samples: Output buffer size

        Returns:
            (left, right) float sample lists.
        """
        if HAS_NUMPY:
            return self._mix_tracks_numpy(track_buffers, num_samples)

        left = [0.0] * num_samples
        right = [0.0] * num_samples

        for mono, gain, pan in track_buffers:
            if mono is None:
                continue
            l_gain = gain * math.cos((pan + 1) * math.pi / 4)
            r_gain = gain * math.sin((pan + 1) * math.pi / 4)
            count = min(len(mono), num_samples)
            for i in range(count):
                left[i] += mono[i] * l_gain
                right[i] += mono[i] * r_gain

        left = self._hpf_l.process_block(left)
        right = self._hpf_r.process_block(right)
        left = self._lpf_l.process_block(left)
        right = self._lpf_r.process_block(right)

        for i in range(num_samples):
            left[i] = math.tanh(left[i] * self.master_gain)
            right[i] = math.tanh(right[i] * self.master_gain)

        return left, right

    def _mix_tracks_numpy(self, track_buffers, num_samples):
        """Numpy-vectorized mixing for speed."""
        left = np.zeros(num_samples, dtype=np.float64)
        right = np.zeros(num_samples, dtype=np.float64)

        for mono, gain, pan in track_buffers:
            if mono is None:
                continue
            l_gain = gain * math.cos((pan + 1) * math.pi / 4)
            r_gain = gain * math.sin((pan + 1) * math.pi / 4)
            arr = np.asarray(mono[:num_samples], dtype=np.float64)
            count = len(arr)
            left[:count] += arr * l_gain
            right[:count] += arr * r_gain

        # Apply filters (still sample-by-sample but fast enough for per-tick)
        left = self._hpf_l.process_block(left)
        right = self._hpf_r.process_block(right)
        left = self._lpf_l.process_block(left)
        right = self._lpf_r.process_block(right)

        # Vectorized soft limiter
        if isinstance(left, np.ndarray):
            left = np.tanh(left * self.master_gain)
            right = np.tanh(right * self.master_gain)
        else:
            left = np.tanh(np.asarray(left) * self.master_gain)
            right = np.tanh(np.asarray(right) * self.master_gain)

        return left.tolist(), right.tolist()


# ---------------------------------------------------------------------------
# SECTION MANAGER
# ---------------------------------------------------------------------------

class Section:
    """A musical section (e.g. verse, chorus, bridge) with consistent style.

    Sections last 4-16 bars and maintain consistent:
    - Time signature
    - Tempo
    - Scale
    - Chord progression
    - Instrument selection
    """

    def __init__(self, time_sig, bpm, root, scale_name, progression_name,
                 instruments, duration_bars=8):
        self.time_sig = time_sig
        self.bpm = bpm
        self.root = root
        self.scale_name = scale_name
        self.scale = SCALES.get(scale_name, SCALES["major"])
        self.progression_name = progression_name
        self.progression = PROGRESSIONS.get(progression_name, PROGRESSIONS["I-V-vi-IV"])
        self.instruments = instruments
        self.duration_bars = duration_bars
        self.current_bar = 0

    def get_chord_for_bar(self):
        """Get the current chord (degree, type) for the current bar.

        Chords cycle through the progression every N bars.
        """
        bars_per_chord = max(1, self.duration_bars // len(self.progression))
        chord_idx = (self.current_bar // bars_per_chord) % len(self.progression)
        return self.progression[chord_idx]


# ---------------------------------------------------------------------------
# MUSIC DIRECTOR (top-level orchestrator)
# ---------------------------------------------------------------------------

class MusicDirector:
    """Orchestrates the entire music generation pipeline.

    The MusicDirector:
    1. Receives simulation state each tick
    2. Manages musical sections (time sig, key, instruments)
    3. Delegates phrase generation to PhraseGenerator
    4. Manages multiple instrument Tracks
    5. Mixes output through the MixBus

    This replaces both the old Composer and parts of CosmicAudioRenderer.
    """

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.seed = seed

        # Sub-systems
        self.phrase_gen = PhraseGenerator(random.Random(seed + 100))
        self.mix_bus = MixBus()

        # Tracks
        self.melody_track = Track("melody", "piano", gain=0.55, pan=0.15)
        self.harmony_track = Track("harmony", "string_ensemble", gain=0.35, pan=-0.25)
        self.bass_track = Track("bass", "acoustic_bass", gain=0.50, pan=0.0)
        self.pad_track = Track("pad", "warm_pad", gain=0.30, pan=0.0)
        self.drum_track = DrumTrack(gain=0.40, pan=0.0)
        self.accent_track = Track("accent", "harp", gain=0.20, pan=0.35)

        # Current section
        self.current_section = None
        self._section_bar = 0
        self._bars_rendered = 0
        self._last_epoch = ""
        self._last_epoch_idx = -1

        # Pre-rendered bar buffers (each track has a queue of bars)
        self._bar_queues = {
            "melody": [],
            "harmony": [],
            "bass": [],
            "pad": [],
            "drums": [],
            "accent": [],
        }
        self._bar_position = 0  # Current position within current bar buffer
        self._current_bar_len = 0

        # Transition state
        self._transition_samples = 0
        self._transition_total = 0

        # Instrument pools per epoch era
        self._instrument_pools = {
            "early": {
                "melody": ["singing_bowl", "glass_pad", "celesta"],
                "harmony": ["cosmic_drone", "warm_pad"],
                "bass": ["synth_bass"],
                "pad": ["cosmic_drone", "glass_pad"],
                "accent": ["tubular_bell", "glockenspiel"],
            },
            "middle": {
                "melody": ["piano", "flute", "clarinet", "vibraphone"],
                "harmony": ["string_ensemble", "warm_pad", "choir_pad"],
                "bass": ["acoustic_bass", "electric_bass"],
                "pad": ["string_ensemble", "warm_pad"],
                "accent": ["harp", "kalimba", "celesta"],
            },
            "late": {
                "melody": ["piano", "violin", "flute", "oboe", "trumpet"],
                "harmony": ["string_ensemble", "choir_pad"],
                "bass": ["acoustic_bass", "electric_bass", "synth_bass"],
                "pad": ["string_ensemble", "choir_pad", "warm_pad"],
                "accent": ["harp", "pizzicato", "glockenspiel", "kalimba"],
            },
            "world": {
                "melody": ["sitar", "koto", "shakuhachi", "kalimba"],
                "harmony": ["gamelan_gong", "singing_bowl"],
                "bass": ["didgeridoo", "acoustic_bass"],
                "pad": ["cosmic_drone", "singing_bowl"],
                "accent": ["gamelan_gong", "kalimba", "koto"],
            },
        }

    def _get_era(self, epoch_idx):
        """Map epoch index to era for instrument selection."""
        if epoch_idx <= 3:
            return "early"
        if epoch_idx <= 7:
            return "middle"
        return "late"

    def _create_section(self, epoch, epoch_idx, temperature):
        """Create a new musical section based on simulation state."""
        style = EPOCH_MUSIC_STYLE.get(epoch, EPOCH_MUSIC_STYLE["Present"])

        # Pick time signature
        ts_options = EPOCH_TIME_SIGS.get(epoch, ["4/4"])
        ts_name = self.rng.choice(ts_options)
        time_sig = TIME_SIGNATURES[ts_name]

        # Pick tempo from range
        lo, hi = style["tempo_range"]
        bpm = lo + (hi - lo) * self.rng.random()
        bpm = int(bpm)

        # Pick scale and root
        scale_name = self.rng.choice(style["scales"])
        root = 48 + self.rng.randint(0, 11)  # C3 to B3

        # Pick progression
        prog_name = self.rng.choice(style["progs"])

        # Pick instruments from era pool
        era = self._get_era(epoch_idx)
        # Occasionally mix in world instruments
        if self.rng.random() < 0.15:
            era = "world"
        pool = self._instrument_pools.get(era, self._instrument_pools["middle"])
        instruments = {k: self.rng.choice(v) for k, v in pool.items()}

        # Section length: 4-16 bars
        duration = self.rng.choice([4, 4, 8, 8, 8, 12, 16])

        section = Section(
            time_sig=time_sig,
            bpm=bpm,
            root=root,
            scale_name=scale_name,
            progression_name=prog_name,
            instruments=instruments,
            duration_bars=duration,
        )
        return section

    def _render_next_bar(self):
        """Pre-render the next bar for all tracks."""
        if self.current_section is None:
            return

        sec = self.current_section
        ts = sec.time_sig
        bpm = sec.bpm
        bar_samples = ts.bar_samples(bpm)

        # Get current chord
        chord_degree, chord_type = sec.get_chord_for_bar()

        # Assign instruments
        self.melody_track.instrument = sec.instruments.get("melody", "piano")
        self.harmony_track.instrument = sec.instruments.get("harmony", "string_ensemble")
        self.bass_track.instrument = sec.instruments.get("bass", "acoustic_bass")
        self.pad_track.instrument = sec.instruments.get("pad", "warm_pad")
        self.accent_track.instrument = sec.instruments.get("accent", "harp")

        # Generate phrases
        # Melody: generate 2-bar phrase, use appropriate bar
        if sec.current_bar % 2 == 0:
            chord_notes = [sec.root + i for i in CHORD_TYPES.get(chord_type, [0, 4, 7])]
            self._current_melody_phrase = self.phrase_gen.generate_melody(
                sec.root, sec.scale, chord_notes, ts, bars_in_phrase=2
            )
        bar_in_phrase = sec.current_bar % 2
        melody_notes = self._current_melody_phrase[bar_in_phrase] if hasattr(self, '_current_melody_phrase') and bar_in_phrase < len(self._current_melody_phrase) else []

        bass_notes = self.phrase_gen.generate_bass(sec.root, sec.scale, chord_degree, ts)
        chord_notes = self.phrase_gen.generate_chord_voicing(sec.root, sec.scale, chord_degree, chord_type, ts)
        drum_hits = self.phrase_gen.generate_drums(ts, intensity=clamp(sec.current_bar / sec.duration_bars, 0.3, 0.8))

        # Accent: play on first beat occasionally
        accent_notes = []
        if self.rng.random() < 0.3:
            accent_midi = sec.root + self.rng.choice([0, 4, 7]) + 12
            accent_notes = [(0.0, accent_midi, 1.0)]

        # Render each track
        self._bar_queues["melody"].append(
            self.melody_track.render_bar(melody_notes, bar_samples, ts, bpm, self.rng))
        self._bar_queues["harmony"].append(
            self.harmony_track.render_bar(chord_notes, bar_samples, ts, bpm, self.rng))
        self._bar_queues["bass"].append(
            self.bass_track.render_bar(bass_notes, bar_samples, ts, bpm, self.rng))
        self._bar_queues["pad"].append(
            self.pad_track.render_bar(chord_notes, bar_samples, ts, bpm, self.rng))
        self._bar_queues["drums"].append(
            self.drum_track.render_bar(drum_hits, bar_samples, ts, bpm))
        self._bar_queues["accent"].append(
            self.accent_track.render_bar(accent_notes, bar_samples, ts, bpm, self.rng))

        self._current_bar_len = bar_samples
        sec.current_bar += 1
        self._bars_rendered += 1

    def compose_tick(self, epoch, epoch_idx, temperature, particles, atoms,
                     molecules, cells, generation, samples_per_tick):
        """Generate audio samples for one simulation tick.

        Returns (left_samples, right_samples) float lists.
        """
        # Check if we need a new section
        if (self.current_section is None or
            self.current_section.current_bar >= self.current_section.duration_bars or
            epoch != self._last_epoch):

            self._last_epoch = epoch
            self._last_epoch_idx = epoch_idx
            self.current_section = self._create_section(epoch, epoch_idx, temperature)
            self._section_bar = 0

            # Adjust lowpass based on epoch (brighter in later epochs)
            lp_cutoff = 3000 + epoch_idx * 500
            self.mix_bus.set_lowpass(clamp(lp_cutoff, 3000, 10000))

        # Ensure we have enough pre-rendered bars
        while not self._bar_queues["melody"] or self._bar_position >= self._current_bar_len:
            self._bar_position = 0
            # Consume current bar
            for key in self._bar_queues:
                if self._bar_queues[key]:
                    self._bar_queues[key].pop(0)
            self._render_next_bar()

        # Extract samples_per_tick from pre-rendered bars
        track_buffers = []
        for track_name, track_obj in [
            ("melody", self.melody_track),
            ("harmony", self.harmony_track),
            ("bass", self.bass_track),
            ("pad", self.pad_track),
            ("accent", self.accent_track),
        ]:
            queue = self._bar_queues[track_name]
            if queue:
                bar = queue[0]
                start = self._bar_position
                end = min(start + samples_per_tick, len(bar))
                chunk = bar[start:end]
                # Pad if needed
                if len(chunk) < samples_per_tick:
                    chunk = list(chunk) + [0.0] * (samples_per_tick - len(chunk))
                track_buffers.append((chunk, track_obj.gain, track_obj.pan))
            else:
                track_buffers.append((None, 0, 0))

        # Drums
        drum_queue = self._bar_queues["drums"]
        if drum_queue:
            bar = drum_queue[0]
            start = self._bar_position
            end = min(start + samples_per_tick, len(bar))
            chunk = bar[start:end]
            if len(chunk) < samples_per_tick:
                chunk = list(chunk) + [0.0] * (samples_per_tick - len(chunk))
            track_buffers.append((chunk, self.drum_track.gain, self.drum_track.pan))

        self._bar_position += samples_per_tick

        # Mix all tracks through the bus
        left, right = self.mix_bus.mix_tracks(track_buffers, samples_per_tick)
        return left, right
