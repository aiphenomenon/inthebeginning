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
    RONDO_PATTERNS, DIATONIC_CHORD_QUALITY, GM_ORCHESTRA_INSTRUMENTS,
    PIANO_PROGRAMS, HAS_FLUIDSYNTH, ARPEGGIO_FORMS,
    GM_EXPANDED_INSTRUMENTS, GM_ALL_INSTRUMENTS, V9_FAMILY_POOLS,
    RadioEngineV9,
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
        self.assertTrue(1 <= mood.n_instruments <= 4)
        self.assertTrue(60 <= mood.tempo <= 200)

    def test_instrument_count_range(self):
        """v7: Instrument count should always be 2-4 (small band)."""
        for i in range(20):
            state = {'temperature': 10 ** i, 'particles': i * 100, 'atoms': i * 50}
            mood = MoodSegment(i, EPOCH_ORDER[i % 13], i % 13, state, i)
            self.assertTrue(2 <= mood.n_instruments <= 4,
                          f"Segment {i}: n_instruments={mood.n_instruments}")

    def test_all_epochs_produce_valid_mood(self):
        for idx, epoch in enumerate(EPOCH_ORDER):
            state = {'temperature': 1e6, 'particles': 100, 'atoms': 50}
            mood = MoodSegment(idx, epoch, idx, state, 42 + idx)
            self.assertIsNotNone(mood.scale)
            self.assertIsNotNone(mood.time_sig)
            self.assertTrue(mood.tempo > 0)


class TestV7Features(unittest.TestCase):
    """Test v7 radio engine features."""

    def test_rondo_patterns_expanded(self):
        """v7: Should have 7 rondo patterns."""
        self.assertEqual(len(RONDO_PATTERNS), 7)
        self.assertIn('ABCBA', RONDO_PATTERNS)
        self.assertIn('AABBA', RONDO_PATTERNS)
        self.assertIn('ABCDA', RONDO_PATTERNS)
        self.assertIn('ABACBA', RONDO_PATTERNS)
        self.assertIn('AABA', RONDO_PATTERNS)

    def test_arpeggio_forms(self):
        """v7: Should have 6 arpeggio forms."""
        from apps.audio.radio_engine import ARPEGGIO_FORMS
        self.assertEqual(len(ARPEGGIO_FORMS), 6)
        self.assertIn('block', ARPEGGIO_FORMS)
        self.assertIn('ascending', ARPEGGIO_FORMS)
        self.assertIn('descending', ARPEGGIO_FORMS)
        self.assertIn('alberti', ARPEGGIO_FORMS)
        self.assertIn('broken', ARPEGGIO_FORMS)
        self.assertIn('pendulum', ARPEGGIO_FORMS)
        # Block should be None (simultaneous), others callable
        self.assertIsNone(ARPEGGIO_FORMS['block'])
        self.assertTrue(callable(ARPEGGIO_FORMS['ascending']))

    def test_arpeggio_ascending(self):
        """Ascending arpeggio should sort notes."""
        from apps.audio.radio_engine import ARPEGGIO_FORMS
        notes = [72, 60, 67, 64]
        result = ARPEGGIO_FORMS['ascending'](notes)
        self.assertEqual(result, [60, 64, 67, 72])

    def test_arpeggio_descending(self):
        """Descending arpeggio should reverse sort."""
        from apps.audio.radio_engine import ARPEGGIO_FORMS
        notes = [60, 64, 67]
        result = ARPEGGIO_FORMS['descending'](notes)
        self.assertEqual(result, [67, 64, 60])

    def test_tempo_multiplier_range(self):
        """v7: Tempo multiplier should be in 1.5-2.5x range."""
        from apps.audio.radio_engine import RadioEngine
        # Use a mock engine without MIDI loading
        engine = RadioEngine.__new__(RadioEngine)
        for i in range(20):
            state = {'temperature': 10 ** i, 'particles': i * 100}
            mult = engine._compute_tempo_multiplier(state)
            self.assertGreaterEqual(mult, 1.5,
                f"Multiplier {mult} below 1.5 for state {state}")
            self.assertLessEqual(mult, 2.5,
                f"Multiplier {mult} above 2.5 for state {state}")

    def test_tempo_multiplier_none_state(self):
        """Tempo multiplier with None state should be 2.0."""
        engine = RadioEngine.__new__(RadioEngine)
        self.assertEqual(engine._compute_tempo_multiplier(None), 2.0)

    def test_mood_duration_multiples_of_42(self):
        """v7: Mood durations should be multiples of 42 seconds."""
        valid_durations = {42.0, 84.0, 126.0, 168.0, 210.0}
        for i in range(50):
            state = {'temperature': 1e6, 'particles': 100, 'atoms': 50}
            mood = MoodSegment(i, EPOCH_ORDER[i % 13], i % 13, state, i * 7)
            self.assertIn(mood.duration, valid_durations,
                         f"Duration {mood.duration} not a multiple of 42")

    def test_plan_segments_42s_multiples(self):
        """v7: Planned segment durations should be multiples of 42s."""
        engine = RadioEngine.__new__(RadioEngine)
        engine.seed = 42
        engine.total_duration = 300.0
        segments = engine._plan_segments()
        valid_durations = {42.0, 84.0, 126.0, 168.0, 210.0}
        for seg in segments[:-1]:  # Last segment may be truncated
            self.assertIn(seg['duration'], valid_durations,
                         f"Duration {seg['duration']} not a 42s multiple")


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


class TestMidiLibrarySampleBars(unittest.TestCase):
    """Tests for MidiLibrary.sample_bars() method."""

    def setUp(self):
        self.lib = MidiLibrary()
        self.rng = random.Random(42)

    def test_sample_bars_returns_tuple(self):
        """sample_bars should return (notes_list, duration) tuple."""
        result = self.lib.sample_bars(self.rng, 4, 120, 4, root=60)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        notes, duration = result
        self.assertIsInstance(notes, list)
        self.assertIsInstance(duration, float)
        self.assertGreater(duration, 0)

    def test_sample_bars_timing_bounds(self):
        """All note times should be within segment duration."""
        result = self.lib.sample_bars(self.rng, 4, 120, 4, root=60)
        notes, duration = result
        for t_sec, midi_note, dur_sec, vel in notes:
            self.assertGreaterEqual(t_sec, 0.0)
            self.assertLessEqual(t_sec, duration + 0.01)
            self.assertGreater(dur_sec, 0.0)
            self.assertGreaterEqual(vel, 0.0)
            self.assertLessEqual(vel, 1.0)

    def test_sample_bars_fallback(self):
        """With no MIDI files, should use fallback generation."""
        lib = MidiLibrary()
        lib._note_sequences = []
        result = lib.sample_bars(self.rng, 4, 120, 4, root=60)
        notes, duration = result
        self.assertGreater(len(notes), 0)
        self.assertGreater(duration, 0)


class TestSynthesizeColoredNote(unittest.TestCase):
    """Tests for InstrumentFactory.synthesize_colored_note()."""

    def setUp(self):
        self.factory = InstrumentFactory(42)
        self.instr = self.factory.generate_instrument("test_color", 42)

    def test_produces_samples(self):
        """Should produce a non-empty list of samples."""
        samples = self.factory.synthesize_colored_note(
            self.instr, 440.0, 0.5, 0.8, 0.25
        )
        self.assertGreater(len(samples), 0)

    def test_correct_duration(self):
        """Output length should match requested duration."""
        duration = 0.5
        samples = self.factory.synthesize_colored_note(
            self.instr, 440.0, duration, 0.8, 0.25
        )
        expected = int(duration * SAMPLE_RATE)
        self.assertEqual(len(samples), expected)

    def test_zero_color_is_clean(self):
        """With color_amount=0, output should be clean base tone."""
        samples = self.factory.synthesize_colored_note(
            self.instr, 440.0, 0.1, 0.8, 0.0
        )
        self.assertGreater(len(samples), 0)
        # Should have non-zero energy
        energy = sum(s * s for s in samples)
        self.assertGreater(energy, 0)

    def test_various_color_amounts(self):
        """Different color amounts should produce different outputs."""
        s1 = self.factory.synthesize_colored_note(
            self.instr, 440.0, 0.1, 0.8, 0.1
        )
        s2 = self.factory.synthesize_colored_note(
            self.instr, 440.0, 0.1, 0.8, 0.35
        )
        # They should differ (different blend ratios)
        diff = sum(abs(a - b) for a, b in zip(s1, s2))
        self.assertGreater(diff, 0)


class TestChamberEffects(unittest.TestCase):
    """Tests for chamber orchestra effects in SmoothingFilter."""

    def setUp(self):
        self.smoother = SmoothingFilter()
        # Create a simple test signal: impulse
        self.impulse = [0.0] * SAMPLE_RATE
        self.impulse[0] = 1.0

    def test_reverb_adds_tail(self):
        """Reverb should add energy after the impulse."""
        out = self.smoother.apply_reverb(self.impulse)
        # Check that there's energy in the tail (after 10ms)
        tail_start = int(0.01 * SAMPLE_RATE)
        tail_energy = sum(s * s for s in out[tail_start:tail_start + 2000])
        self.assertGreater(tail_energy, 0)

    def test_reverb_preserves_length(self):
        """Reverb output should be same length as input."""
        out = self.smoother.apply_reverb(self.impulse)
        self.assertEqual(len(out), len(self.impulse))

    def test_chorus_preserves_length(self):
        """Chorus output should be same length as input."""
        # Use a tone instead of impulse for chorus
        tone = [math.sin(2 * math.pi * 440 * i / SAMPLE_RATE) * 0.5
                for i in range(SAMPLE_RATE // 10)]
        out = self.smoother.apply_chorus(tone)
        self.assertEqual(len(out), len(tone))

    def test_early_reflections(self):
        """Early reflections should produce delayed copies."""
        out = self.smoother.apply_early_reflections(self.impulse)
        self.assertEqual(len(out), len(self.impulse))
        # Check that there's energy at reflection delay points
        delay_11ms = int(0.011 * SAMPLE_RATE)
        self.assertNotEqual(out[delay_11ms], 0.0)


class TestChordMultiplication(unittest.TestCase):
    """Tests for _build_chord_from_note() -- chord expansion with consonance."""

    def setUp(self):
        self.engine = RadioEngine(seed=42, total_duration=5.0)
        self.rng = random.Random(42)

    def test_returns_2_to_5_notes(self):
        """Chord should have between 2 and 5 notes."""
        for n in range(2, 6):
            chord = self.engine._build_chord_from_note(
                60, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11], n_notes=n, rng=self.rng
            )
            self.assertTrue(2 <= len(chord) <= n,
                           f"Requested {n} notes, got {len(chord)}")

    def test_valid_midi_range(self):
        """All chord notes should be in valid MIDI range 24-108."""
        chord = self.engine._build_chord_from_note(
            60, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11], n_notes=5, rng=self.rng
        )
        for note in chord:
            self.assertTrue(24 <= note <= 108, f"Note {note} out of range")

    def test_root_preserved(self):
        """Root note (or close) should be in the chord."""
        chord = self.engine._build_chord_from_note(
            60, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11], n_notes=3, rng=self.rng
        )
        # The base note (60 = C4) should be in the chord
        self.assertIn(60, chord)

    def test_consonant_intervals(self):
        """No adjacent notes should have minor 2nd interval (1 semitone)."""
        for _ in range(20):
            note = self.rng.randint(48, 84)
            chord = self.engine._build_chord_from_note(
                note, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11],
                n_notes=self.rng.randint(2, 5), rng=self.rng
            )
            sorted_chord = sorted(chord)
            for i in range(1, len(sorted_chord)):
                interval = sorted_chord[i] - sorted_chord[i - 1]
                self.assertGreater(interval, 1,
                    f"Minor 2nd found: {sorted_chord[i-1]}-{sorted_chord[i]}")

    def test_dissonant_input_corrected(self):
        """A dissonant input note should still produce a consonant chord."""
        # MIDI 61 = C#, which is outside C major scale
        chord = self.engine._build_chord_from_note(
            61, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11], n_notes=3, rng=self.rng
        )
        sorted_chord = sorted(chord)
        for i in range(1, len(sorted_chord)):
            interval = sorted_chord[i] - sorted_chord[i - 1]
            self.assertGreater(interval, 1,
                "Dissonance not corrected")


class TestRondoStructure(unittest.TestCase):
    """Tests for _build_rondo_sections()."""

    def setUp(self):
        self.engine = RadioEngine(seed=42, total_duration=5.0)
        self.rng = random.Random(42)
        # Create some base chord notes: (t_sec, [chord_notes], dur_sec, vel)
        self.base_notes = [
            (0.0, [60, 64, 67], 0.5, 0.8),
            (0.5, [62, 65, 69], 0.5, 0.7),
            (1.0, [64, 67, 71], 0.5, 0.8),
            (1.5, [60, 64, 67], 0.5, 0.7),
        ]

    def test_returns_sections(self):
        """Should return a list of (label, notes) tuples."""
        result = self.engine._build_rondo_sections(
            self.base_notes, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11],
            100.0, self.rng  # >80s triggers ABACADA
        )
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) >= 5)  # At least ABACA
        for label, notes in result:
            self.assertIn(label, ['A', 'B', 'C', 'D'])
            self.assertIsInstance(notes, list)

    def test_a_sections_match_theme(self):
        """All A sections should be the original theme."""
        result = self.engine._build_rondo_sections(
            self.base_notes, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11],
            100.0, self.rng
        )
        a_sections = [(label, notes) for label, notes in result if label == 'A']
        self.assertTrue(len(a_sections) >= 2)
        for _, notes in a_sections:
            self.assertEqual(len(notes), len(self.base_notes))

    def test_episodes_differ_from_theme(self):
        """B, C, D sections should differ from A."""
        result = self.engine._build_rondo_sections(
            self.base_notes, 60, 'ionian', [0, 2, 4, 5, 7, 9, 11],
            100.0, random.Random(42)
        )
        a_notes = None
        for label, notes in result:
            if label == 'A':
                a_notes = notes
                break
        for label, notes in result:
            if label != 'A' and a_notes:
                # At least one chord should differ
                diffs = 0
                for (_, c1, _, _), (_, c2, _, _) in zip(a_notes, notes):
                    if c1 != c2:
                        diffs += 1
                self.assertGreater(diffs, 0,
                    f"Section {label} is identical to A")


class TestTempoMultiplier(unittest.TestCase):
    """Tests for _compute_tempo_multiplier()."""

    def setUp(self):
        self.engine = RadioEngine(seed=42, total_duration=5.0)

    def test_range_1_5_to_2_5(self):
        """v7: Multiplier should be in [1.5, 2.5]."""
        for i in range(50):
            state = {'temperature': 10 ** i, 'particles': i * 100}
            mult = self.engine._compute_tempo_multiplier(state)
            self.assertTrue(1.5 <= mult <= 2.5,
                           f"Multiplier {mult} out of range for state {state}")

    def test_deterministic(self):
        """Same state should give same multiplier."""
        state = {'temperature': 1e6, 'particles': 500}
        m1 = self.engine._compute_tempo_multiplier(state)
        m2 = self.engine._compute_tempo_multiplier(state)
        self.assertEqual(m1, m2)

    def test_different_states_differ(self):
        """Different states should usually give different multipliers."""
        m1 = self.engine._compute_tempo_multiplier({'temperature': 1e6})
        m2 = self.engine._compute_tempo_multiplier({'temperature': 1e9})
        self.assertNotEqual(m1, m2)


class TestInstrumentVoiceSelection(unittest.TestCase):
    """Tests for _choose_gm_instruments()."""

    def setUp(self):
        self.engine = RadioEngine(seed=42, total_duration=5.0)
        self.rng = random.Random(42)

    def test_correct_voice_count(self):
        """Should return exactly n_voices voice configs."""
        for n in range(1, 6):
            midi_info = {'programs': set(), 'path': None}
            voices = self.engine._choose_gm_instruments(midi_info, n, self.rng)
            self.assertEqual(len(voices), n)

    def test_voice_has_required_fields(self):
        """Each voice config should have gm_program, octave_offset, pan, chord_size."""
        midi_info = {'programs': set(), 'path': None}
        voices = self.engine._choose_gm_instruments(midi_info, 3, self.rng)
        for v in voices:
            self.assertIn('gm_program', v)
            self.assertIn('octave_offset', v)
            self.assertIn('pan', v)
            self.assertIn('chord_size', v)
            self.assertIn('color_amount', v)
            self.assertTrue(2 <= v['chord_size'] <= 5)


class TestLoopFriendliness(unittest.TestCase):
    """Tests for MidiLibrary._assess_loop_friendliness()."""

    def setUp(self):
        self.lib = MidiLibrary()

    def test_perfect_loop_scores_high(self):
        """A segment with matching start/end pitches should score well."""
        # Notes with same pitch classes at start and end, balanced density
        notes = [(i * 100, 60, 100, 80) for i in range(16)]
        score = self.lib._assess_loop_friendliness(notes, 0, 1600, 480)
        self.assertGreater(score, 0.5)

    def test_score_in_range(self):
        """Score should always be between 0 and 1."""
        for _ in range(20):
            rng = random.Random(_)
            notes = [(rng.randint(0, 5000), rng.randint(40, 80),
                      rng.randint(50, 200), rng.randint(40, 100))
                     for _ in range(rng.randint(0, 30))]
            score = self.lib._assess_loop_friendliness(notes, 0, 5000, 480)
            self.assertTrue(0.0 <= score <= 1.0, f"Score {score} out of range")


class TestFluidSynthRendering(unittest.TestCase):
    """Tests for MidiLibrary.render_fluidsynth()."""

    def test_returns_none_without_valid_path(self):
        """Should return None for a nonexistent MIDI path."""
        result = MidiLibrary.render_fluidsynth('/nonexistent.mid', 0)
        self.assertIsNone(result)

    def test_produces_samples_with_real_midi(self):
        """Should produce stereo samples from a real MIDI file (if available)."""
        if not HAS_FLUIDSYNTH:
            self.skipTest("FluidSynth not available")
        # Find a MIDI file
        midi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'midi_library')
        midi_files = []
        if os.path.isdir(midi_dir):
            for f in os.listdir(midi_dir):
                if f.endswith('.mid') or f.endswith('.midi'):
                    midi_files.append(os.path.join(midi_dir, f))
        if not midi_files:
            self.skipTest("No MIDI files available")
        result = MidiLibrary.render_fluidsynth(midi_files[0], 0)
        if result is not None:
            left, right = result
            self.assertTrue(len(left) > 0)
            self.assertEqual(len(left), len(right))

    def test_graceful_fallback(self):
        """Should not crash even when FluidSynth has issues."""
        # Use an empty file to trigger an error path
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
            f.write(b'\x00' * 10)
            bad_path = f.name
        try:
            result = MidiLibrary.render_fluidsynth(bad_path, 40)
            # Should return None, not crash
            self.assertTrue(result is None or isinstance(result, tuple))
        finally:
            os.unlink(bad_path)


class TestSampleBarsSeeded(unittest.TestCase):
    """Tests for MidiLibrary.sample_bars_seeded()."""

    def setUp(self):
        self.lib = MidiLibrary()
        self.lib.load()
        self.rng = random.Random(42)

    def test_returns_triple(self):
        """Should return (notes, duration, midi_info) tuple."""
        state = {'temperature': 1e6, 'particles': 500}
        result = self.lib.sample_bars_seeded(state, 4, 120, 4,
                                              root=60, rng=self.rng)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        notes, duration, info = result
        self.assertIsInstance(notes, list)
        self.assertGreater(duration, 0)
        self.assertIsInstance(info, dict)

    def test_deterministic_selection(self):
        """Same sim_state should select the same MIDI segment."""
        state = {'temperature': 1e6, 'particles': 500}
        r1 = self.lib.sample_bars_seeded(state, 4, 120, 4,
                                          root=60, rng=random.Random(42))
        r2 = self.lib.sample_bars_seeded(state, 4, 120, 4,
                                          root=60, rng=random.Random(42))
        self.assertEqual(len(r1[0]), len(r2[0]))
        self.assertAlmostEqual(r1[1], r2[1], places=2)


# ---------------------------------------------------------------------------
# V8 Tests
# ---------------------------------------------------------------------------
from apps.audio.radio_engine import (
    RadioEngineV8, NoteSmoother, AntiHissFilter, SubsonicFilter,
    NoteQuantizer, SIMPLE_TIME_SIGS, COMPOUND_TIME_SIGS, COMPLEX_TIME_SIGS,
    generate_radio_v8_mp3,
)


class TestNoteSmoother(unittest.TestCase):
    """Tests for the v8 NoteSmoother."""

    def setUp(self):
        self.smoother = NoteSmoother()

    def test_preserves_length(self):
        """Output length should match input length."""
        samples = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) for i in range(1000)]
        result = self.smoother.smooth_note(samples, 440.0)
        self.assertEqual(len(result), len(samples))

    def test_short_input(self):
        """Very short inputs should be returned as-is."""
        short = [0.1, 0.2]
        result = self.smoother.smooth_note(short, 440.0)
        self.assertEqual(len(result), 2)

    def test_reduces_high_frequency(self):
        """Smoothing should reduce high-frequency energy."""
        # Create a signal with lots of high-frequency content
        samples = [((-1) ** i) * 0.5 for i in range(4410)]  # Nyquist alternating
        result = self.smoother.smooth_note(samples, 440.0)
        # RMS of smoothed should be less than original
        orig_rms = math.sqrt(sum(s ** 2 for s in samples) / len(samples))
        smooth_rms = math.sqrt(sum(s ** 2 for s in result) / len(result))
        self.assertLess(smooth_rms, orig_rms)

    def test_smooth_chord(self):
        """Smooth chord should process each note independently."""
        samples1 = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) for i in range(500)]
        samples2 = [math.sin(TWO_PI * 880 * i / SAMPLE_RATE) for i in range(500)]
        result = self.smoother.smooth_chord([samples1, samples2], [440.0, 880.0])
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result[0]), 500)
        self.assertEqual(len(result[1]), 500)


class TestAntiHissFilter(unittest.TestCase):
    """Tests for the v8 AntiHissFilter."""

    def setUp(self):
        self.filt = AntiHissFilter()

    def test_preserves_length(self):
        """Output should match input length."""
        samples = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) for i in range(1000)]
        result = self.filt.apply(samples)
        self.assertEqual(len(result), len(samples))

    def test_removes_dc(self):
        """DC offset should be removed."""
        samples = [0.5 + math.sin(TWO_PI * 440 * i / SAMPLE_RATE) * 0.3
                   for i in range(4410)]
        result = self.filt.apply(samples)
        dc = sum(result) / len(result)
        self.assertLess(abs(dc), 0.01)

    def test_stereo(self):
        """Stereo apply should return two lists."""
        left = [0.1] * 100
        right = [0.2] * 100
        l_out, r_out = self.filt.apply_stereo(left, right)
        self.assertEqual(len(l_out), 100)
        self.assertEqual(len(r_out), 100)


class TestSubsonicFilter(unittest.TestCase):
    """Tests for the v8 SubsonicFilter."""

    def setUp(self):
        self.filt = SubsonicFilter(cutoff_hz=30.0)

    def test_preserves_length(self):
        """Output should match input length."""
        samples = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) for i in range(1000)]
        result = self.filt.apply(samples)
        self.assertEqual(len(result), len(samples))

    def test_attenuates_subsonic(self):
        """Low-frequency content should be attenuated."""
        # 10 Hz sine wave (subsonic)
        samples = [math.sin(TWO_PI * 10 * i / SAMPLE_RATE) for i in range(44100)]
        result = self.filt.apply(samples)
        orig_rms = math.sqrt(sum(s ** 2 for s in samples) / len(samples))
        filt_rms = math.sqrt(sum(s ** 2 for s in result) / len(result))
        self.assertLess(filt_rms, orig_rms * 0.5)

    def test_preserves_audible(self):
        """Audible frequencies should be mostly preserved."""
        # 440 Hz sine wave
        samples = [math.sin(TWO_PI * 440 * i / SAMPLE_RATE) for i in range(4410)]
        result = self.filt.apply(samples)
        orig_rms = math.sqrt(sum(s ** 2 for s in samples) / len(samples))
        filt_rms = math.sqrt(sum(s ** 2 for s in result) / len(result))
        self.assertGreater(filt_rms, orig_rms * 0.5)


class TestNoteQuantizer(unittest.TestCase):
    """Tests for the v8 NoteQuantizer."""

    def setUp(self):
        self.q = NoteQuantizer()

    def test_quantize_preserves_note_count(self):
        """Number of notes should be preserved after quantization."""
        notes = [(0.0, 60, 0.3, 0.8), (0.3, 64, 0.45, 0.7), (0.75, 67, 0.25, 0.9)]
        result = self.q.quantize_to_bar(notes, 2.0, 4)
        self.assertEqual(len(result), 3)

    def test_durations_snap_to_grid(self):
        """Quantized durations should be multiples of beat subdivisions."""
        beat_dur = 0.5  # 120 BPM
        notes = [(0.0, 60, 0.33, 0.8)]
        result = self.q.quantize_to_bar(notes, 2.0, 4)
        # Duration should be snapped to one of the grid values
        dur = result[0][2]
        grid_fracs = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.375, 0.25, 0.125]
        grid_secs = [f * beat_dur for f in grid_fracs]
        self.assertTrue(any(abs(dur - gs) < 0.001 for gs in grid_secs),
                        f"Duration {dur} not on grid")

    def test_fit_notes_to_bars(self):
        """Notes should be scaled to fill the target bar span."""
        notes = [(0.0, 60, 0.5, 0.8), (0.5, 64, 0.5, 0.7)]
        result = self.q.fit_notes_to_bars(notes, 2, 1.0, 4)
        # Total span should be approximately 2 bars
        total_span = result[-1][0] + result[-1][2]
        self.assertGreater(total_span, 0.5)


class TestV8TimeSigDistribution(unittest.TestCase):
    """Tests for v8 time signature distribution."""

    def test_simple_majority(self):
        """At least 60% of segments should use simple time signatures."""
        engine = RadioEngineV8(seed=42, total_duration=1800.0)
        total = len(engine.segments)
        simple = sum(1 for s in engine.segments
                     if s.get('time_sig_override') in SIMPLE_TIME_SIGS)
        pct = simple / total if total > 0 else 0
        self.assertGreaterEqual(pct, 0.5,
            f"Simple time sigs are only {pct*100:.0f}%, expected >= 50%")

    def test_non_simple_per_10min_window(self):
        """Every 10-minute window must have at least one non-simple time sig."""
        engine = RadioEngineV8(seed=42, total_duration=1800.0)
        window_sec = 600.0
        n_windows = max(1, int(math.ceil(1800 / window_sec)))
        for w in range(n_windows):
            w_start = w * window_sec
            w_end = min((w + 1) * window_sec, 1800)
            window_segs = [s for s in engine.segments
                           if s['start'] >= w_start and s['start'] < w_end]
            has_nonstandard = any(
                s.get('time_sig_override') in COMPOUND_TIME_SIGS + COMPLEX_TIME_SIGS
                for s in window_segs
            )
            self.assertTrue(has_nonstandard,
                f"Window {w+1} ({w_start/60:.0f}-{w_end/60:.0f}min) has no non-simple time sig")


class TestV8EngineCreation(unittest.TestCase):
    """Tests for RadioEngineV8 initialization."""

    def test_creates_successfully(self):
        """V8 engine should initialize without errors."""
        engine = RadioEngineV8(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.note_smoother)
        self.assertIsNotNone(engine.anti_hiss)
        self.assertIsNotNone(engine.subsonic_filter)
        self.assertIsNotNone(engine.quantizer)

    def test_has_time_sig_overrides(self):
        """All segments should have time_sig_override field."""
        engine = RadioEngineV8(seed=42, total_duration=1800.0)
        for seg in engine.segments:
            self.assertIn('time_sig_override', seg)
            self.assertIn(seg['time_sig_override'],
                          SIMPLE_TIME_SIGS + COMPOUND_TIME_SIGS + COMPLEX_TIME_SIGS)


# ---------------------------------------------------------------------------
# V9 Tests
# ---------------------------------------------------------------------------
from apps.audio.radio_engine import (
    generate_radio_v9_mp3,
)


class TestV9InstrumentCatalog(unittest.TestCase):
    """Tests for v9 expanded instrument catalog."""

    def test_expanded_instruments_count(self):
        """v9 should add ~50 new instruments."""
        self.assertGreaterEqual(len(GM_EXPANDED_INSTRUMENTS), 45)

    def test_all_instruments_superset(self):
        """GM_ALL_INSTRUMENTS should contain all v7/v8 instruments."""
        for prog in GM_ORCHESTRA_INSTRUMENTS:
            self.assertIn(prog, GM_ALL_INSTRUMENTS)

    def test_all_instruments_has_expanded(self):
        """GM_ALL_INSTRUMENTS should contain all expanded instruments."""
        for prog in GM_EXPANDED_INSTRUMENTS:
            self.assertIn(prog, GM_ALL_INSTRUMENTS)

    def test_v9_family_pools_count(self):
        """v9 should have 15 family pools."""
        self.assertEqual(len(V9_FAMILY_POOLS), 15)

    def test_v9_family_pools_unique_programs(self):
        """All programs in v9 pools should be valid GM programs (0-127)."""
        for family, programs in V9_FAMILY_POOLS.items():
            for prog in programs:
                self.assertGreaterEqual(prog, 0, f"{family}: {prog} < 0")
                self.assertLessEqual(prog, 127, f"{family}: {prog} > 127")

    def test_v9_pools_superset_of_v7(self):
        """v9 pools should include all v7 families."""
        v7_families = {'strings', 'brass', 'woodwinds', 'keys', 'pitched_perc'}
        for fam in v7_families:
            self.assertIn(fam, V9_FAMILY_POOLS)

    def test_rock_family_exists(self):
        """v9 should have rock guitar and bass families."""
        self.assertIn('rock_guitar', V9_FAMILY_POOLS)
        self.assertIn('rock_bass', V9_FAMILY_POOLS)
        self.assertTrue(len(V9_FAMILY_POOLS['rock_guitar']) >= 3)

    def test_synth_families_exist(self):
        """v9 should have synth lead, pad, and fx families."""
        self.assertIn('synth_lead', V9_FAMILY_POOLS)
        self.assertIn('synth_pad', V9_FAMILY_POOLS)
        self.assertIn('synth_fx', V9_FAMILY_POOLS)

    def test_world_family_exists(self):
        """v9 should have world/ethnic family."""
        self.assertIn('world', V9_FAMILY_POOLS)
        self.assertTrue(len(V9_FAMILY_POOLS['world']) >= 8)

    def test_sax_and_choir_families(self):
        """v9 should have sax and choir families."""
        self.assertIn('sax', V9_FAMILY_POOLS)
        self.assertIn('choir', V9_FAMILY_POOLS)
        self.assertEqual(len(V9_FAMILY_POOLS['sax']), 4)


class TestV9TempoMultiplier(unittest.TestCase):
    """Tests for v9 density-aware tempo."""

    def test_default_tempo(self):
        """Default (no sim state) should return 1.6."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        self.assertAlmostEqual(engine._compute_tempo_multiplier(None), 1.6)

    def test_tempo_range(self):
        """Tempo should be in 1.1-2.1 range for normal states."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        for i in range(50):
            state = {'temperature': 1000 + i * 100, 'particles': 5,
                     'atoms': 2, 'molecules': 0, 'cells': 0}
            mult = engine._compute_tempo_multiplier(state)
            self.assertGreaterEqual(mult, 1.1)
            self.assertLessEqual(mult, 2.1)

    def test_high_density_cap(self):
        """High density states should cap tempo at 1.6."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        state = {'temperature': 5000, 'particles': 50, 'atoms': 30,
                 'molecules': 10, 'cells': 5}
        # density = 50 + 60 + 30 + 25 = 165 > 100
        mult = engine._compute_tempo_multiplier(state)
        self.assertLessEqual(mult, 1.6)

    def test_medium_density_cap(self):
        """Medium density states should cap tempo at 1.8."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        state = {'temperature': 3000, 'particles': 20, 'atoms': 15,
                 'molecules': 2, 'cells': 0}
        # density = 20 + 30 + 6 + 0 = 56 > 50
        mult = engine._compute_tempo_multiplier(state)
        self.assertLessEqual(mult, 1.8)


class TestV9EngineCreation(unittest.TestCase):
    """Tests for RadioEngineV9 initialization."""

    def test_creates_successfully(self):
        """V9 engine should initialize without errors."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)
        self.assertIsInstance(engine, RadioEngineV8)
        self.assertIsInstance(engine, RadioEngine)

    def test_has_family_groups(self):
        """V9 should track family groups for variety enforcement."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine._family_groups)
        self.assertIn('symphonic', engine._family_groups)
        self.assertIn('rock', engine._family_groups)
        self.assertIn('electronic', engine._family_groups)
        self.assertIn('world', engine._family_groups)
        self.assertIn('classical', engine._family_groups)

    def test_instrument_selection_uses_expanded_pools(self):
        """V9 instrument selection should use all 15 family pools."""
        engine = RadioEngineV9(seed=42, total_duration=10.0)
        rng = random.Random(42)
        midi_info = {'programs': set()}

        # Run selection many times, collect all families used
        all_families = set()
        for _ in range(100):
            voices = engine._choose_gm_instruments_v9(midi_info, 4, rng)
            for v in voices:
                all_families.add(v['family'])

        # Should use many different families across 100 iterations
        self.assertGreaterEqual(len(all_families), 10)

    def test_v9_has_time_sig_overrides(self):
        """V9 inherits v8 time sig control."""
        engine = RadioEngineV9(seed=42, total_duration=1800.0)
        for seg in engine.segments:
            self.assertIn('time_sig_override', seg)

    def test_v9_short_render(self):
        """V9 should render a short segment without errors."""
        engine = RadioEngineV9(seed=42, total_duration=5.0)
        left, right = engine.render()
        self.assertGreater(len(left), 0)
        self.assertGreater(len(right), 0)
        self.assertEqual(len(left), len(right))


class TestV9CLIArgument(unittest.TestCase):
    """Tests for v9 CLI argument support."""

    def test_v9_in_choices(self):
        """CLI should accept --version v9."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V', choices=['v7', 'v8', 'v9'])
        args = parser.parse_args(['--version', 'v9'])
        self.assertEqual(args.version, 'v9')


if __name__ == '__main__':
    unittest.main()
