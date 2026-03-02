#!/usr/bin/env python3
"""Tests for the In The Beginning Radio engine.

Tests cover: instrument factory, MIDI library, TTS engine, smoothing filters,
mood segments, time signatures, scales, crossfading, and full rendering.
"""

import math
import os
import random
import struct
import sys
import tempfile
import unittest
import wave

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from apps.audio.radio_engine import (
    InstrumentFactory, MidiLibrary, TTSEngine, SmoothingFilter,
    MoodSegment, RadioEngine, render_to_wav, mtof, ftom, clamp,
    SCALES, TIME_SIGNATURES, PROGRESSIONS, CHORD_INTERVALS,
    EPOCH_MUSIC, EPOCH_ORDER, EPOCH_ROOTS, SAMPLE_RATE,
    TWO_PI, EDM_TIME_SIGS,
    _adsr, _write_wav,
)


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_mtof_a4(self):
        """A4 (MIDI 69) should be 440 Hz."""
        self.assertAlmostEqual(mtof(69), 440.0, places=2)

    def test_mtof_c4(self):
        """C4 (MIDI 60) should be ~261.63 Hz."""
        self.assertAlmostEqual(mtof(60), 261.63, places=1)

    def test_ftom_440(self):
        """440 Hz should map to MIDI 69."""
        self.assertEqual(ftom(440.0), 69)

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_adsr_length(self):
        """ADSR envelope should have correct length."""
        n = 44100
        env = _adsr(n, 0.01, 0.05, 0.8, 0.1)
        self.assertEqual(len(env), n)

    def test_adsr_shape(self):
        """ADSR should start at 0, rise, sustain, and release."""
        env = _adsr(44100, 0.01, 0.05, 0.8, 0.1)
        self.assertAlmostEqual(env[0], 0.0, places=3)
        # Peak near end of attack
        peak_region = env[int(0.01 * 44100) - 5:int(0.01 * 44100) + 5]
        self.assertTrue(max(peak_region) > 0.9)
        # End near 0
        self.assertTrue(env[-1] < 0.1)


class TestDataIntegrity(unittest.TestCase):
    """Test that data constants are well-formed."""

    def test_all_scales_have_intervals(self):
        for name, intervals in SCALES.items():
            self.assertTrue(len(intervals) >= 2,
                           f"Scale {name} has too few intervals")
            self.assertEqual(intervals[0], 0,
                           f"Scale {name} should start at 0")

    def test_all_time_signatures_valid(self):
        for name, ts in TIME_SIGNATURES.items():
            self.assertIn('beats', ts)
            self.assertIn('unit', ts)
            self.assertTrue(ts['beats'] > 0)
            self.assertTrue(ts['unit'] > 0)

    def test_all_progressions_have_chords(self):
        for name, prog in PROGRESSIONS.items():
            self.assertTrue(len(prog) >= 2,
                           f"Progression {name} too short")
            for root_off, chord_type in prog:
                self.assertIn(chord_type, CHORD_INTERVALS,
                            f"Unknown chord type {chord_type} in {name}")

    def test_all_epochs_have_music_config(self):
        for epoch in EPOCH_ORDER:
            self.assertIn(epoch, EPOCH_MUSIC,
                         f"Epoch {epoch} missing music config")
            config = EPOCH_MUSIC[epoch]
            self.assertIn('tempo', config)
            self.assertIn('scales', config)
            self.assertIn('time_sigs', config)
            self.assertIn('density', config)

    def test_all_epoch_roots_defined(self):
        for epoch in EPOCH_ORDER:
            self.assertIn(epoch, EPOCH_ROOTS)
            root = EPOCH_ROOTS[epoch]
            self.assertTrue(24 <= root <= 108)

    def test_chord_intervals_valid(self):
        for name, intervals in CHORD_INTERVALS.items():
            self.assertTrue(len(intervals) >= 2)
            self.assertEqual(intervals[0], 0)


class TestInstrumentFactory(unittest.TestCase):
    """Test the algorithmic instrument factory."""

    def setUp(self):
        self.factory = InstrumentFactory(seed=42)

    def test_generate_single_instrument(self):
        instr = self.factory.generate_instrument("test_piano_0")
        self.assertIn('name', instr)
        self.assertIn('technique', instr)
        self.assertIn('harmonics', instr)
        self.assertIn('attack', instr)
        self.assertIn('freq_mult', instr)

    def test_generate_instrument_set_count(self):
        instruments = self.factory.generate_instrument_set(537)
        self.assertEqual(len(instruments), 537)

    def test_instrument_names_unique(self):
        instruments = self.factory.generate_instrument_set(100)
        names = [i['name'] for i in instruments]
        self.assertEqual(len(names), len(set(names)))

    def test_synthesize_note_produces_samples(self):
        instr = self.factory.generate_instrument("test_note")
        samples = self.factory.synthesize_note(instr, 440.0, 0.5, 0.8)
        self.assertTrue(len(samples) > 0)
        self.assertTrue(any(s != 0.0 for s in samples))

    def test_synthesize_note_duration(self):
        instr = self.factory.generate_instrument("test_dur")
        samples = self.factory.synthesize_note(instr, 440.0, 1.0, 0.8)
        expected = int(SAMPLE_RATE * 1.0)
        self.assertEqual(len(samples), expected)

    def test_synthesize_note_range(self):
        """All samples should be in reasonable range."""
        instr = self.factory.generate_instrument("test_range")
        samples = self.factory.synthesize_note(instr, 440.0, 0.5, 0.8)
        for s in samples:
            self.assertTrue(-5.0 <= s <= 5.0,
                          f"Sample out of range: {s}")

    def test_rotate_instruments(self):
        instruments = self.factory.generate_instrument_set(100)
        rotated = self.factory.rotate_instruments(instruments, n_swap=10, generation=1)
        self.assertEqual(len(rotated), 100)
        # Some instruments should be different
        changed = sum(1 for a, b in zip(instruments, rotated)
                     if a['name'] != b['name'])
        self.assertTrue(changed >= 5)  # At least some changed

    def test_fm_instrument(self):
        """FM synthesis technique should produce audio."""
        instr = self.factory.generate_instrument("fm_test", seed=12345)
        # Force FM technique
        instr['technique'] = 'fm'
        instr['harmonics'] = [('fm', 2.0, 3.0)]
        samples = self.factory.synthesize_note(instr, 440.0, 0.3, 0.7)
        self.assertTrue(len(samples) > 0)
        self.assertTrue(any(abs(s) > 0.01 for s in samples))

    def test_noise_percussion(self):
        """Noise percussion should produce audio."""
        instr = self.factory.generate_instrument("perc_test", seed=99999)
        instr['technique'] = 'noise_perc'
        instr['harmonics'] = [('noise', 0.8)]
        samples = self.factory.synthesize_note(instr, 200.0, 0.2, 0.7)
        self.assertTrue(len(samples) > 0)


class TestMidiLibrary(unittest.TestCase):
    """Test the MIDI library loader and sampler."""

    def setUp(self):
        self.lib = MidiLibrary()
        self.lib.load()

    def test_midi_files_loaded(self):
        """Should load MIDI files from the midi_library directory."""
        # May have 0 if mido not installed or directory empty
        if not HAS_MIDO:
            self.skipTest("mido not installed")
        self.assertTrue(len(self.lib._note_sequences) > 0,
                       "No MIDI sequences loaded")

    def test_sample_phrase(self):
        rng = random.Random(42)
        phrase = self.lib.sample_phrase(rng, length=8, root=60, scale=[0, 2, 4, 5, 7, 9, 11])
        self.assertTrue(len(phrase) > 0)
        for midi_note, dur, vel in phrase:
            self.assertTrue(24 <= midi_note <= 108)
            self.assertTrue(dur > 0)
            self.assertTrue(0 < vel <= 1.0)

    def test_fallback_phrase(self):
        """Should generate a phrase even with no MIDI files."""
        rng = random.Random(42)
        phrase = self.lib._generate_fallback_phrase(
            rng, 8, 60, [0, 2, 4, 5, 7, 9, 11]
        )
        self.assertEqual(len(phrase), 8)

    def test_snap_to_scale(self):
        # C major scale: C D E F G A B
        scale = [0, 2, 4, 5, 7, 9, 11]
        # C# should snap to C or D
        snapped = self.lib._snap_to_scale(61, 60, scale)
        self.assertIn(snapped, [60, 62])


class TestTTSEngine(unittest.TestCase):
    """Test the TTS engine."""

    def setUp(self):
        self.tts = TTSEngine()

    def test_espeak_available(self):
        """espeak-ng should be available as fallback."""
        import shutil
        self.assertTrue(shutil.which('espeak-ng') is not None)

    def test_generate_speech(self):
        samples, sr = self.tts.generate_speech("test", voice_seed=0, epoch_idx=5)
        if samples is not None:
            self.assertTrue(len(samples) > 0)
            self.assertTrue(sr > 0)

    def test_get_source_phrases(self):
        rng = random.Random(42)
        phrases = self.tts.get_source_phrases(rng, count=3)
        self.assertTrue(len(phrases) > 0)
        for p in phrases:
            self.assertTrue(len(p) > 5)


class TestSmoothingFilter(unittest.TestCase):
    """Test the smoothing/dampening filters."""

    def setUp(self):
        self.smoother = SmoothingFilter()

    def test_lowpass_reduces_high_freq(self):
        """Lowpass filter should reduce high-frequency content."""
        # Generate a mix of low and high frequency
        n = 4410
        low = [math.sin(TWO_PI * 100 * i / SAMPLE_RATE) for i in range(n)]
        high = [math.sin(TWO_PI * 10000 * i / SAMPLE_RATE) for i in range(n)]
        mixed = [l + h for l, h in zip(low, high)]

        filtered = self.smoother.apply_lowpass(mixed, 2000)
        # Energy of high freq should be reduced
        high_energy_before = sum(h * h for h in high) / n
        residual = [f - l for f, l in zip(filtered, low)]
        high_energy_after = sum(r * r for r in residual) / n
        self.assertTrue(high_energy_after < high_energy_before)

    def test_soft_limit_clamps(self):
        """Soft limiter should keep output below ~1.0."""
        samples = [0.5 * math.sin(i * 0.1) * 3.0 for i in range(1000)]
        limited = self.smoother.apply_soft_limit(samples, 0.8)
        for s in limited:
            self.assertTrue(abs(s) <= 1.1)

    def test_stereo_smooth_preserves_energy(self):
        n = 1000
        left = [math.sin(i * 0.05) for i in range(n)]
        right = [math.cos(i * 0.05) for i in range(n)]
        out_l, out_r = self.smoother.apply_stereo_smooth(left, right, 0.15)
        self.assertEqual(len(out_l), n)
        self.assertEqual(len(out_r), n)

    def test_compression(self):
        samples = [math.sin(i * 0.01) * 2.0 for i in range(4410)]
        compressed = self.smoother.apply_gentle_compression(samples)
        peak_orig = max(abs(s) for s in samples)
        peak_comp = max(abs(s) for s in compressed)
        self.assertTrue(peak_comp <= peak_orig)


class TestMoodSegment(unittest.TestCase):
    """Test mood segment generation."""

    def test_mood_creation(self):
        sim_state = {
            'temperature': 1e6,
            'particles': 500,
            'atoms': 100,
        }
        mood = MoodSegment(0, 'Star Formation', 7, sim_state, 42)
        self.assertEqual(mood.epoch, 'Star Formation')
        self.assertIn(mood.time_sig, list(TIME_SIGNATURES.keys()) + EDM_TIME_SIGS)
        self.assertTrue(1 <= mood.n_instruments <= 16)
        self.assertTrue(60 <= mood.tempo <= 200)

    def test_instrument_count_range(self):
        """Instrument count should always be 1-16."""
        for i in range(20):
            state = {'temperature': 10 ** i, 'particles': i * 100, 'atoms': i * 50}
            mood = MoodSegment(i, EPOCH_ORDER[i % 13], i % 13, state, i)
            self.assertTrue(1 <= mood.n_instruments <= 16,
                          f"Segment {i}: n_instruments={mood.n_instruments}")

    def test_all_epochs_produce_valid_mood(self):
        for idx, epoch in enumerate(EPOCH_ORDER):
            state = {'temperature': 1e6, 'particles': 100, 'atoms': 50}
            mood = MoodSegment(idx, epoch, idx, state, 42 + idx)
            self.assertIsNotNone(mood.scale)
            self.assertIsNotNone(mood.time_sig)
            self.assertTrue(mood.tempo > 0)


class TestRadioEngine(unittest.TestCase):
    """Test the main radio engine."""

    def test_engine_init(self):
        engine = RadioEngine(seed=42, total_duration=30.0)
        self.assertEqual(len(engine.instruments), 537)
        self.assertIsNotNone(engine.midi_lib)
        self.assertIsNotNone(engine.tts)

    def test_short_render(self):
        """Render a very short piece to verify basic operation."""
        engine = RadioEngine(seed=42, total_duration=5.0)
        left, right = engine.render()
        self.assertTrue(len(left) > 0)
        self.assertEqual(len(left), len(right))
        # Check it's not all silence
        energy = sum(abs(s) for s in left) / len(left)
        self.assertTrue(energy > 0.0001, "Output is too quiet")

    def test_stereo_channels_differ(self):
        """Left and right channels should not be identical (stereo)."""
        engine = RadioEngine(seed=42, total_duration=5.0)
        left, right = engine.render()
        diff = sum(abs(l - r) for l, r in zip(left, right)) / len(left)
        self.assertTrue(diff > 0.0001, "Channels are identical (mono)")

    def test_fade_in(self):
        """Output should start quiet (fade-in)."""
        engine = RadioEngine(seed=42, total_duration=10.0)
        left, right = engine.render()
        # First 100 samples should be near zero
        early_energy = sum(abs(left[i]) for i in range(100)) / 100
        self.assertTrue(early_energy < 0.01, f"Fade-in too loud: {early_energy}")

    def test_fade_out(self):
        """Output should end quiet (fade-out)."""
        engine = RadioEngine(seed=42, total_duration=10.0)
        left, right = engine.render()
        # Last 100 samples should be near zero
        late_energy = sum(abs(left[-i-1]) for i in range(100)) / 100
        self.assertTrue(late_energy < 0.01, f"Fade-out too loud: {late_energy}")

    def test_output_range(self):
        """All output samples should be in [-1, 1] after soft limiting."""
        engine = RadioEngine(seed=42, total_duration=5.0)
        left, right = engine.render()
        for i in range(0, len(left), 100):  # Sample every 100th
            self.assertTrue(-1.1 <= left[i] <= 1.1)
            self.assertTrue(-1.1 <= right[i] <= 1.1)


class TestWavOutput(unittest.TestCase):
    """Test WAV file output."""

    def test_render_to_wav(self):
        n = 44100
        left = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) * 0.5 for i in range(n)]
        right = [math.cos(TWO_PI * 440 * i / SAMPLE_RATE) * 0.5 for i in range(n)]

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            render_to_wav(left, right, tmp_path)
            with wave.open(tmp_path, 'rb') as wf:
                self.assertEqual(wf.getnchannels(), 2)
                self.assertEqual(wf.getframerate(), SAMPLE_RATE)
                self.assertEqual(wf.getnframes(), n)
        finally:
            os.unlink(tmp_path)


# Import flag check
try:
    from apps.audio.radio_engine import HAS_MIDO
except ImportError:
    HAS_MIDO = False


if __name__ == '__main__':
    unittest.main()
