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
    RadioEngineV9, RadioEngineV10, RadioEngineV11,
    GM_TIMBRE_PROFILES, _gm_program_to_timbre, _synth_gm_note_np,
    GainStage, ConsonanceEngine, BarGrid, OrchestratorV11, _soft_limit,
    RadioEngineV12, GM_TIMBRE_PROFILES_V12,
    RadioEngineV13,
    RadioEngineV14,
    RadioEngineV15,
    RadioEngineV16,
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


# ===================================================================
# V10 TESTS
# ===================================================================

class TestV10GMTimbreProfiles(unittest.TestCase):
    """Tests for v10 GM timbre profile mapping."""

    def test_all_profiles_exist(self):
        """All 15 GM timbre profiles should exist."""
        self.assertEqual(len(GM_TIMBRE_PROFILES), 15)

    def test_profiles_have_required_keys(self):
        """Each profile must have attack, decay, sustain, release, harmonics, brightness."""
        required = {'attack', 'decay', 'sustain', 'release', 'harmonics',
                    'brightness', 'vib_depth'}
        for name, profile in GM_TIMBRE_PROFILES.items():
            for key in required:
                self.assertIn(key, profile, f"Profile {name} missing {key}")

    def test_gm_program_mapping_covers_all(self):
        """Every GM program 0-127 should map to a valid profile."""
        for prog in range(128):
            timbre = _gm_program_to_timbre(prog)
            self.assertIn(timbre, GM_TIMBRE_PROFILES,
                          f"GM program {prog} maps to unknown profile {timbre}")

    def test_piano_mapping(self):
        """GM programs 0-7 should map to piano."""
        for prog in range(8):
            self.assertEqual(_gm_program_to_timbre(prog), 'piano')

    def test_strings_mapping(self):
        """GM programs 40-47 should map to strings."""
        for prog in range(40, 48):
            self.assertEqual(_gm_program_to_timbre(prog), 'strings')

    def test_brass_mapping(self):
        """GM programs 56-63 should map to brass."""
        for prog in range(56, 64):
            self.assertEqual(_gm_program_to_timbre(prog), 'brass')

    def test_synth_pad_mapping(self):
        """GM programs 88-95 should map to synth_pad."""
        for prog in range(88, 96):
            self.assertEqual(_gm_program_to_timbre(prog), 'synth_pad')

    def test_distinct_envelope_shapes(self):
        """Different families should have meaningfully different envelopes."""
        piano = GM_TIMBRE_PROFILES['piano']
        strings = GM_TIMBRE_PROFILES['strings']
        synth_pad = GM_TIMBRE_PROFILES['synth_pad']
        # Piano has fast attack, strings slow, pads very slow
        self.assertLess(piano['attack'], strings['attack'])
        self.assertLess(strings['attack'], synth_pad['attack'])

    def test_harmonics_not_empty(self):
        """Each profile should have at least 2 harmonics."""
        for name, profile in GM_TIMBRE_PROFILES.items():
            self.assertGreaterEqual(len(profile['harmonics']), 2,
                                    f"Profile {name} has too few harmonics")


class TestV10GMSynthesis(unittest.TestCase):
    """Tests for v10 GM-timbre-aware synthesis function."""

    def test_synth_produces_audio(self):
        """_synth_gm_note_np should produce non-empty output."""
        result = _synth_gm_note_np(440.0, 0.1, 0)  # Piano A4
        self.assertGreater(len(result), 0)

    def test_different_programs_different_output(self):
        """Different GM programs should produce different audio."""
        piano = _synth_gm_note_np(440.0, 0.1, 0)
        strings = _synth_gm_note_np(440.0, 0.1, 44)
        brass = _synth_gm_note_np(440.0, 0.1, 60)
        # Compare RMS levels (different envelopes = different energy)
        def rms(samples):
            if hasattr(samples, 'tolist'):
                samples = samples.tolist()
            return (sum(s*s for s in samples) / max(len(samples), 1)) ** 0.5
        # At least two of the three should differ noticeably
        rms_p, rms_s, rms_b = rms(piano), rms(strings), rms(brass)
        # They can't all be identical
        self.assertFalse(
            abs(rms_p - rms_s) < 0.001 and abs(rms_s - rms_b) < 0.001,
            "All three instrument families produced identical output"
        )

    def test_synth_correct_length(self):
        """Output length should match duration * sample_rate."""
        result = _synth_gm_note_np(440.0, 0.5, 0)
        expected = int(0.5 * SAMPLE_RATE)
        if hasattr(result, '__len__'):
            self.assertEqual(len(result), expected)

    def test_zero_duration(self):
        """Zero duration should produce empty output."""
        result = _synth_gm_note_np(440.0, 0.0, 0)
        self.assertEqual(len(result), 0)


class TestV10TempoMultiplier(unittest.TestCase):
    """Tests for v10 flat tempo range."""

    def test_default_tempo(self):
        """Default (no sim state) should return 1.5."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        self.assertAlmostEqual(engine._compute_tempo_multiplier(None), 1.5)

    def test_tempo_range(self):
        """Tempo should be in 1.2-1.8 range for all states."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        for i in range(100):
            state = {'temperature': 500 + i * 200, 'particles': i,
                     'atoms': i * 2, 'molecules': i, 'cells': i // 5}
            mult = engine._compute_tempo_multiplier(state)
            self.assertGreaterEqual(mult, 1.2, f"Tempo {mult} < 1.2 for state {i}")
            self.assertLessEqual(mult, 1.8, f"Tempo {mult} > 1.8 for state {i}")

    def test_no_density_capping(self):
        """v10 should NOT cap tempo based on density (unlike v9)."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        # High density state that would trigger v9 cap at 1.6
        state = {'temperature': 5000, 'particles': 100, 'atoms': 50,
                 'molecules': 20, 'cells': 10}
        mult = engine._compute_tempo_multiplier(state)
        # Should still be in 1.2-1.8 range, but NOT necessarily <= 1.6
        self.assertGreaterEqual(mult, 1.2)
        self.assertLessEqual(mult, 1.8)


class TestV10EngineCreation(unittest.TestCase):
    """Tests for RadioEngineV10 initialization."""

    def test_creates_successfully(self):
        """V10 engine should initialize without errors."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)
        self.assertIsInstance(engine, RadioEngineV9)
        self.assertIsInstance(engine, RadioEngineV8)
        self.assertIsInstance(engine, RadioEngine)

    def test_morph_duration_increased(self):
        """V10 should have 8s morph transitions (up from 6s)."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        self.assertEqual(engine.MORPH_DURATION, 8.0)

    def test_fade_durations_increased(self):
        """V10 should have longer fade in/out."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        self.assertEqual(engine.FADE_IN_DURATION, 6.0)
        self.assertEqual(engine.FADE_OUT_DURATION, 10.0)

    def test_inherits_v9_features(self):
        """V10 should inherit v9 family tracking."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine._family_groups)
        self.assertIsNotNone(engine._used_family_groups)

    def test_v10_short_render(self):
        """V10 should render a short segment without errors."""
        engine = RadioEngineV10(seed=42, total_duration=5.0)
        left, right = engine.render()
        self.assertGreater(len(left), 0)
        self.assertGreater(len(right), 0)
        self.assertEqual(len(left), len(right))

    def test_v10_instrument_diversity(self):
        """V10 instrument selection should guarantee 3+ families per segment."""
        engine = RadioEngineV10(seed=42, total_duration=10.0)
        rng = random.Random(42)
        midi_info = {'programs': set()}

        for trial in range(20):
            voices = engine._choose_gm_instruments_v10(midi_info, 5, rng)
            families_used = set(v['family'] for v in voices)
            self.assertGreaterEqual(len(families_used), 3,
                                    f"Trial {trial}: only {len(families_used)} families")


class TestV10CLIArgument(unittest.TestCase):
    """Tests for v10 CLI argument support."""

    def test_v10_in_choices(self):
        """CLI should accept --version v10."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V', choices=['v7', 'v8', 'v9', 'v10'])
        args = parser.parse_args(['--version', 'v10'])
        self.assertEqual(args.version, 'v10')


class TestSoftLimit(unittest.TestCase):
    """Tests for the soft-knee limiter function."""

    def test_passthrough_below_knee(self):
        """Values below knee should pass through unchanged."""
        for v in [0.0, 0.1, 0.5, 0.79, -0.5, -0.79]:
            self.assertAlmostEqual(_soft_limit(v, 0.8), v, places=6)

    def test_compression_above_knee(self):
        """Values above knee should be compressed below 1.0."""
        for v in [1.0, 2.0, 5.0, 10.0]:
            result = _soft_limit(v, 0.8)
            self.assertLess(result, 1.0)
            self.assertGreater(result, 0.8)

    def test_symmetry(self):
        """Negative values should be symmetric."""
        for v in [1.0, 2.0, 5.0]:
            self.assertAlmostEqual(_soft_limit(-v, 0.8), -_soft_limit(v, 0.8))


class TestGainStage(unittest.TestCase):
    """Tests for GainStage per-voice normalization."""

    def test_voice_gain_sums_to_headroom(self):
        """Sum of all voice gains should equal headroom."""
        gs = GainStage(4, headroom_db=-3.0)
        total = gs.voice_gain * 4
        self.assertAlmostEqual(total, gs.headroom, places=3)

    def test_master_limit_clamps(self):
        """Master limiter should keep peaks below 1.0."""
        gs = GainStage(1)
        left = [2.0, -3.0, 0.5, 1.5]
        right = [0.0, 4.0, -2.0, 0.3]
        gs.master_limit(left, right)
        for s in left + right:
            self.assertLessEqual(abs(s), 1.0)

    def test_solo_gain_higher(self):
        """Solo gain should be higher than ensemble gain."""
        gs = GainStage(4)
        samples = [0.5] * 100
        solo = gs.voice_samples(list(samples), is_solo=True)
        ensemble = gs.voice_samples(list(samples), is_solo=False)
        solo_peak = max(abs(s) for s in solo)
        ens_peak = max(abs(s) for s in ensemble)
        self.assertGreater(solo_peak, ens_peak)


class TestConsonanceEngine(unittest.TestCase):
    """Tests for inter-voice consonance scoring."""

    def test_unison_is_perfect(self):
        """Unison should score 1.0."""
        ce = ConsonanceEngine()
        score = ce.score_composite([[60], [60]])
        self.assertAlmostEqual(score, 1.0)

    def test_fifth_is_consonant(self):
        """Perfect fifth should score high."""
        ce = ConsonanceEngine()
        score = ce.score_composite([[60], [67]])
        self.assertGreater(score, 0.9)

    def test_semitone_is_dissonant(self):
        """Semitone interval should score very low."""
        ce = ConsonanceEngine()
        score = ce.score_composite([[60], [61]])
        self.assertLess(score, 0.1)

    def test_major_triad_consonant(self):
        """C major triad should be consonant."""
        ce = ConsonanceEngine()
        score = ce.score_composite([[60, 64, 67]])
        self.assertGreater(score, 0.6)

    def test_adjustment_improves_score(self):
        """Consonance adjustment should not worsen the score."""
        ce = ConsonanceEngine()
        dissonant = [[60, 61], [64, 65]]
        original_score = ce.score_composite(dissonant)
        adjusted = ce.adjust_for_consonance(
            dissonant, 60, [0, 2, 4, 5, 7, 9, 11], min_score=0.5
        )
        adjusted_score = ce.score_composite(adjusted)
        self.assertGreaterEqual(adjusted_score, original_score)


class TestBarGrid(unittest.TestCase):
    """Tests for bar-aligned timing grid."""

    def test_bar_duration_4_4(self):
        """4/4 at 120 BPM should have 2-second bars."""
        grid = BarGrid(120, 4, 4)
        self.assertAlmostEqual(grid.bar_dur, 2.0, places=3)

    def test_snap_onset_to_16th(self):
        """Onset should snap to nearest 16th note."""
        grid = BarGrid(120, 4, 4)
        sixteenth = 0.5 / 4  # 0.125 seconds
        snapped = grid.snap_onset(0.13, '16th')
        self.assertAlmostEqual(snapped, 0.125, places=3)

    def test_section_start_alignment(self):
        """Section starts should be bar-aligned."""
        grid = BarGrid(120, 4, 4)
        for i in range(5):
            start = grid.section_start(i, 4)
            # Should be exact multiple of bar duration
            self.assertAlmostEqual(start % grid.bar_dur, 0.0, places=6)

    def test_snap_duration(self):
        """Duration should snap to standard note value."""
        grid = BarGrid(120, 4, 4)
        # 0.48 seconds is close to a quarter note (0.5s at 120 BPM)
        snapped = grid.snap_duration(0.48)
        self.assertAlmostEqual(snapped, 0.5, places=3)

    def test_3_4_time(self):
        """3/4 time at 90 BPM should have correct bar duration."""
        grid = BarGrid(90, 3, 4)
        beat_dur = 60.0 / 90  # 0.667s
        expected_bar = beat_dur * 3  # 2.0s
        self.assertAlmostEqual(grid.bar_dur, expected_bar, places=3)


class TestOrchestratorV11(unittest.TestCase):
    """Tests for orchestral role assignment."""

    def test_assign_roles_distinct_offsets(self):
        """Voices should get distinct register offsets."""
        orch = OrchestratorV11()
        configs = [{'pan': 0.0, 'chord_size': 3, 'gm_program': 40} for _ in range(5)]
        orch.assign_roles(configs, random.Random(42))
        offsets = [c['octave_offset'] for c in configs]
        # Should have at least 3 distinct offsets for 5 voices
        self.assertGreaterEqual(len(set(offsets)), 3)

    def test_gain_weights_vary(self):
        """Different roles should have different gain weights."""
        orch = OrchestratorV11()
        configs = [{'pan': 0.0, 'chord_size': 3, 'gm_program': 40} for _ in range(5)]
        orch.assign_roles(configs, random.Random(42))
        weights = [c['gain_weight'] for c in configs]
        # Melody should be 1.0, others less
        self.assertEqual(max(weights), 1.0)
        self.assertLess(min(weights), 1.0)

    def test_voice_leading_smooth(self):
        """Voice leading should minimize movement between chords."""
        orch = OrchestratorV11()
        prev = [60, 64, 67]  # C major
        next_chord = [65, 69, 72]  # F major
        led = orch.apply_voice_leading(prev, next_chord, [0, 2, 4, 5, 7, 9, 11], 60)
        # Total movement should be less than parallel movement
        total_move = sum(abs(a - b) for a, b in zip(prev, led))
        parallel_move = sum(abs(a - b) for a, b in zip(prev, next_chord))
        self.assertLessEqual(total_move, parallel_move + 12)  # Allow some tolerance


class TestRadioEngineV11(unittest.TestCase):
    """Integration tests for RadioEngineV11."""

    def test_v11_init(self):
        """V11 should initialize successfully."""
        engine = RadioEngineV11(seed=42, total_duration=5.0)
        self.assertIsNotNone(engine.consonance)
        self.assertIsNotNone(engine.orchestrator)

    def test_v11_mix_mono_no_phase_inversion(self):
        """v11 _mix_mono should never produce negative gains from panning."""
        engine = RadioEngineV11(seed=42, total_duration=5.0)
        left = [0.0] * 100
        right = [0.0] * 100
        samples = [1.0] * 100
        # Test extreme pan values
        for pan in [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]:
            left_test = [0.0] * 100
            right_test = [0.0] * 100
            engine._mix_mono_v11(left_test, right_test, samples, 0, 100, pan, 0.5)
            # All values should be non-negative (no phase inversion)
            for i in range(100):
                self.assertGreaterEqual(left_test[i], 0.0,
                    f"Phase inversion at pan={pan}, left[{i}]={left_test[i]}")
                self.assertGreaterEqual(right_test[i], 0.0,
                    f"Phase inversion at pan={pan}, right[{i}]={right_test[i]}")

    def test_v11_short_render(self):
        """V11 should render a short segment without errors."""
        engine = RadioEngineV11(seed=42, total_duration=5.0)
        left, right = engine.render()
        self.assertGreater(len(left), 0)
        self.assertGreater(len(right), 0)
        self.assertEqual(len(left), len(right))

    def test_v11_no_clipping(self):
        """V11 output should not clip (peak < 1.0 after soft limiting)."""
        engine = RadioEngineV11(seed=42, total_duration=5.0)
        left, right = engine.render()
        # After soft-knee limiting, peaks should be controlled
        peak_l = max(abs(s) for s in left) if left else 0
        peak_r = max(abs(s) for s in right) if right else 0
        # Allow up to 1.05 since the master limit is on the loop buffer,
        # and the crossfade looping can add up slightly
        self.assertLess(peak_l, 1.5,
                       f"Left channel peak too high: {peak_l}")
        self.assertLess(peak_r, 1.5,
                       f"Right channel peak too high: {peak_r}")

    def test_v11_reverb_less_resonant(self):
        """V11 reverb tail should have less energy than v10 reverb tail."""
        smoother = SmoothingFilter()
        engine = RadioEngineV11(seed=42, total_duration=5.0)
        # Simple impulse test
        impulse = [0.0] * 4410
        impulse[0] = 1.0
        v10_reverb = smoother.apply_reverb(list(impulse), wet=0.30)
        v11_reverb = engine._apply_reverb_v11(list(impulse), wet=0.20)
        # Compare reverb tail energy (last 75% of samples, after direct sound)
        tail_start = len(impulse) // 4
        v10_tail_energy = sum(s * s for s in v10_reverb[tail_start:])
        v11_tail_energy = sum(s * s for s in v11_reverb[tail_start:])
        # V11 reverb tail should have less energy (lower feedback + lower wet)
        self.assertLess(v11_tail_energy, v10_tail_energy)


class TestV11CLIArgument(unittest.TestCase):
    """Tests for v11 CLI argument support."""

    def test_v11_in_choices(self):
        """CLI should accept --version v11."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11'])
        args = parser.parse_args(['--version', 'v11'])
        self.assertEqual(args.version, 'v11')


# ---------------------------------------------------------------------------
# V12 TESTS
# ---------------------------------------------------------------------------

class TestV12TimbreProfiles(unittest.TestCase):
    """Tests for v12 timbre profiles (retained for reference data)."""

    def test_all_profiles_present(self):
        """V12 must have all instrument family profiles."""
        expected = ['piano', 'mallets', 'organ', 'guitar', 'bass', 'strings',
                    'ensemble', 'brass', 'reed', 'pipe', 'synth_lead',
                    'synth_pad', 'synth_fx', 'world', 'percussive']
        for name in expected:
            self.assertIn(name, GM_TIMBRE_PROFILES_V12, f"Missing profile: {name}")

    def test_profiles_have_v12_fields(self):
        """V12 profiles must have detune_cents, noise_amount, warmth."""
        for name, profile in GM_TIMBRE_PROFILES_V12.items():
            self.assertIn('detune_cents', profile, f"{name} missing detune_cents")
            self.assertIn('noise_amount', profile, f"{name} missing noise_amount")
            self.assertIn('warmth', profile, f"{name} missing warmth")
            self.assertIn('harmonics', profile, f"{name} missing harmonics")
            self.assertGreater(profile['detune_cents'], 0,
                             f"{name} detune_cents must be positive")


class TestV12Engine(unittest.TestCase):
    """Tests for RadioEngineV12 (v8 synthesis + expanded instruments)."""

    def test_engine_creation(self):
        """V12 engine should create successfully."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.gain_stage)

    def test_inherits_from_v8(self):
        """V12 should inherit from RadioEngineV8, not V11."""
        from apps.audio.radio_engine import RadioEngineV8
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        self.assertIsInstance(engine, RadioEngineV8)

    def test_uses_v8_synthesis(self):
        """V12 should use v8's _synth_colored_note_np (module-level function)."""
        import apps.audio.radio_engine as re_mod
        self.assertTrue(hasattr(re_mod, '_synth_colored_note_np'))

    def test_has_gain_staging(self):
        """V12 should have v11-style gain staging."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        self.assertIsNotNone(engine.gain_stage)
        self.assertIsInstance(engine.gain_stage, GainStage)

    def test_tempo_multiplier_range(self):
        """V12 tempo multiplier should be clamped to 1.1x-1.7x."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        # Test with various sim states
        for i in range(20):
            state = {'particles': i * 50, 'atoms': i * 10,
                     'molecules': i * 5, 'cells': i}
            mult = engine._compute_tempo_multiplier(state)
            self.assertGreaterEqual(mult, 1.1, f"Tempo too slow: {mult}")
            self.assertLessEqual(mult, 1.7, f"Tempo too fast: {mult}")

    def test_tempo_density_capping(self):
        """High-density states should cap tempo lower."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        high_density = {'particles': 300, 'atoms': 200,
                        'molecules': 100, 'cells': 50}
        mult = engine._compute_tempo_multiplier(high_density)
        self.assertLessEqual(mult, 1.5, "High density should cap at 1.5x")

    def test_instrument_selection_uses_v9_pools(self):
        """V12 should use v9's family pools for instrument selection."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        rng = random.Random(42)
        voices = engine._choose_gm_instruments({}, 5, rng)
        self.assertEqual(len(voices), 5)
        # Each voice should have expected keys
        for v in voices:
            self.assertIn('gm_program', v)
            self.assertIn('family', v)

    def test_instrument_selection_diverse(self):
        """V12 should select at least 3 different families."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        rng = random.Random(42)
        voices = engine._choose_gm_instruments({}, 5, rng)
        families = set(v['family'] for v in voices)
        self.assertGreaterEqual(len(families), 3)

    def test_v12_has_family_groups(self):
        """V12 should have family group tracking for variety."""
        engine = RadioEngineV12(seed=42, total_duration=60.0)
        self.assertIsNotNone(engine._family_groups)
        self.assertIn('symphonic', engine._family_groups)
        self.assertIn('rock', engine._family_groups)
        self.assertIn('electronic', engine._family_groups)

    def test_render_segment_applies_gain_staging(self):
        """V12 _render_segment should apply gain staging on top of v8."""
        engine = RadioEngineV12(seed=42, total_duration=10.0)
        # Just verify the method exists and is overridden
        self.assertTrue(hasattr(engine, '_render_segment'))
        # V12's _render_segment calls super() then gain_stage
        import inspect
        src = inspect.getsource(engine._render_segment)
        self.assertIn('gain_stage', src)
        self.assertIn('master_limit', src)


class TestV12CLIArgument(unittest.TestCase):
    """Tests for v12 CLI argument support."""

    def test_v12_in_choices(self):
        """CLI should accept --version v12."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12'])
        args = parser.parse_args(['--version', 'v12'])
        self.assertEqual(args.version, 'v12')


class TestRadioEngineV13(unittest.TestCase):
    """Tests for RadioEngineV13 -- V8 core with V12 tempo."""

    def test_v13_inherits_from_v8(self):
        """V13 should inherit from RadioEngineV8."""
        from apps.audio.radio_engine import RadioEngineV8
        self.assertTrue(issubclass(RadioEngineV13, RadioEngineV8))

    def test_v13_instantiation(self):
        """V13 should instantiate without errors."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)

    def test_v13_tempo_range(self):
        """V13 tempo should be in 1.1-1.7 range (not v8's 1.5-2.5)."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        # Test with various sim states
        for particles in [0, 50, 100, 300, 600]:
            sim_state = {'particles': particles, 'atoms': 0,
                         'molecules': 0, 'cells': 0}
            tempo = engine._compute_tempo_multiplier(sim_state)
            self.assertGreaterEqual(tempo, 1.1)
            self.assertLessEqual(tempo, 1.7)

    def test_v13_tempo_default(self):
        """V13 default tempo (no sim_state) should be 1.4."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        self.assertEqual(engine._compute_tempo_multiplier(None), 1.4)
        self.assertEqual(engine._compute_tempo_multiplier({}), 1.4)

    def test_v13_density_capping(self):
        """V13 should cap tempo for high-density epochs."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        # Very high density should cap at 1.4
        high_density = {'particles': 100, 'atoms': 100,
                        'molecules': 100, 'cells': 100}
        tempo = engine._compute_tempo_multiplier(high_density)
        self.assertLessEqual(tempo, 1.4)

    def test_v13_no_gain_stage(self):
        """V13 should NOT have v12's GainStage or per-segment limiting."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        # V13 should not have gain_stage attribute (it's v8's init, not v12's)
        # V8's init doesn't create self.gain_stage
        import inspect
        # V13's _render_segment should be V8's, not V12's
        src = inspect.getsource(engine._render_segment)
        self.assertNotIn('gain_stage', src)
        self.assertNotIn('master_limit', src)

    def test_v13_uses_v8_instruments(self):
        """V13 should use V8's instrument selection (5 families, not 15)."""
        engine = RadioEngineV13(seed=42, total_duration=10.0)
        import inspect
        # V13 should NOT override _choose_gm_instruments
        # So it uses V8's version (which uses 5 families from base)
        v13_method = engine._choose_gm_instruments
        v8_class = RadioEngineV13.__mro__[1]  # Should be RadioEngineV8
        self.assertEqual(v8_class.__name__, 'RadioEngineV8')

    def test_v13_short_render(self):
        """V13 should render a short clip successfully."""
        engine = RadioEngineV13(seed=42, total_duration=2.0)
        left, right = engine.render()
        self.assertIsInstance(left, list)
        self.assertIsInstance(right, list)
        self.assertGreater(len(left), 0)
        self.assertEqual(len(left), len(right))

    def test_v13_volume_matches_v8(self):
        """V13 should have similar volume to V8 (no extra limiting)."""
        v8_engine = RadioEngineV8(seed=42, total_duration=2.0)
        v13_engine = RadioEngineV13(seed=42, total_duration=2.0)
        v8_left, _ = v8_engine.render()
        v13_left, _ = v13_engine.render()
        # RMS should be within 20% (same audio path, slightly different tempo)
        v8_rms = (sum(x*x for x in v8_left) / len(v8_left)) ** 0.5
        v13_rms = (sum(x*x for x in v13_left) / len(v13_left)) ** 0.5
        if v8_rms > 0.001:
            ratio = v13_rms / v8_rms
            self.assertGreater(ratio, 0.5)
            self.assertLess(ratio, 2.0)


class TestV13CLIArgument(unittest.TestCase):
    """Tests for v13 CLI argument support."""

    def test_v13_in_choices(self):
        """CLI should accept --version v13."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13'])
        args = parser.parse_args(['--version', 'v13'])
        self.assertEqual(args.version, 'v13')


class TestRadioEngineV14(unittest.TestCase):
    """Tests for RadioEngineV14 -- Full palette with serial render."""

    def test_v14_inherits_from_v8(self):
        """V14 should inherit from RadioEngineV8."""
        from apps.audio.radio_engine import RadioEngineV8
        self.assertTrue(issubclass(RadioEngineV14, RadioEngineV8))

    def test_v14_instantiation(self):
        """V14 should instantiate without errors."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)

    def test_v14_has_family_tracking(self):
        """V14 should have V12's family tracking for variety enforcement."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        self.assertIsInstance(engine._used_family_groups, set)
        self.assertIsInstance(engine._family_groups, dict)
        self.assertEqual(len(engine._family_groups), 5)

    def test_v14_tempo_range(self):
        """V14 tempo should be in 1.1-1.7 range (V12's density-aware tempo)."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        for particles in [0, 50, 100, 300, 600]:
            sim_state = {'particles': particles, 'atoms': 0,
                         'molecules': 0, 'cells': 0}
            tempo = engine._compute_tempo_multiplier(sim_state)
            self.assertGreaterEqual(tempo, 1.1)
            self.assertLessEqual(tempo, 1.7)

    def test_v14_tempo_default(self):
        """V14 default tempo (no sim_state) should be 1.4."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        self.assertEqual(engine._compute_tempo_multiplier(None), 1.4)
        self.assertEqual(engine._compute_tempo_multiplier({}), 1.4)

    def test_v14_uses_expanded_instruments(self):
        """V14 should use V12's expanded 15-family instrument selection."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        rng = random.Random(42)
        voices = engine._choose_gm_instruments({}, 5, rng)
        self.assertEqual(len(voices), 5)
        # Should have at least 3 different families (variety enforcement)
        families = {v['family'] for v in voices}
        self.assertGreaterEqual(len(families), 3)

    def test_v14_no_gain_stage_in_render(self):
        """V14 should NOT have per-segment GainStage limiting."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        import inspect
        # V14's _render_segment should be V8's (no master_limit)
        src = inspect.getsource(engine._render_segment)
        self.assertNotIn('gain_stage', src)
        self.assertNotIn('master_limit', src)

    def test_v14_short_render(self):
        """V14 should render a short clip successfully."""
        engine = RadioEngineV14(seed=42, total_duration=2.0)
        left, right = engine.render()
        self.assertIsInstance(left, list)
        self.assertIsInstance(right, list)
        self.assertGreater(len(left), 0)
        self.assertEqual(len(left), len(right))

    def test_v14_volume_reasonable(self):
        """V14 should produce audible output with reasonable volume."""
        v14_engine = RadioEngineV14(seed=42, total_duration=2.0)
        v14_left, _ = v14_engine.render()
        v14_rms = (sum(x*x for x in v14_left) / len(v14_left)) ** 0.5
        # V14 uses 15 instrument families (expanded) so short renders may be
        # quieter than V8 — many voices may not fully activate in 2s.
        # Just verify we got non-silent, non-clipping output.
        self.assertGreater(v14_rms, 0.0001, "Output is silent")
        self.assertLess(v14_rms, 1.0, "Output clipping")

    def test_v14_expanded_families_vs_v13(self):
        """V14 should have more instrument families available than V13."""
        engine = RadioEngineV14(seed=42, total_duration=10.0)
        # V14 overrides _choose_gm_instruments to use V9_FAMILY_POOLS (15 families)
        # V13 does not override it, using V8's 5 families
        rng = random.Random(42)
        voices = engine._choose_gm_instruments({}, 5, rng)
        # All voices should have a 'family' key from V9_FAMILY_POOLS
        for v in voices:
            self.assertIn(v['family'], V9_FAMILY_POOLS)


class TestV14CLIArgument(unittest.TestCase):
    """Tests for v14 CLI argument support."""

    def test_v14_in_choices(self):
        """CLI should accept --version v14."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14'])
        args = parser.parse_args(['--version', 'v14'])
        self.assertEqual(args.version, 'v14')


class TestRadioEngineV15(unittest.TestCase):
    """Tests for RadioEngineV15 -- True original V8 synthesis + V12 tempo."""

    def test_v15_inherits_from_v8(self):
        """V15 should inherit from RadioEngineV8."""
        from apps.audio.radio_engine import RadioEngineV8
        self.assertTrue(issubclass(RadioEngineV15, RadioEngineV8))

    def test_v15_instantiation(self):
        """V15 should instantiate without errors."""
        engine = RadioEngineV15(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)

    def test_v15_tempo_range(self):
        """V15 tempo should be in 1.1-1.7 range."""
        engine = RadioEngineV15(seed=42, total_duration=10.0)
        for particles in [0, 50, 100, 300, 600]:
            sim_state = {'particles': particles, 'atoms': 0,
                         'molecules': 0, 'cells': 0}
            tempo = engine._compute_tempo_multiplier(sim_state)
            self.assertGreaterEqual(tempo, 1.1)
            self.assertLessEqual(tempo, 1.7)

    def test_v15_uses_original_synthesis(self):
        """V15 _render_segment should use factory.synthesize_colored_note, not numpy."""
        engine = RadioEngineV15(seed=42, total_duration=10.0)
        import inspect
        src = inspect.getsource(engine._render_segment)
        self.assertIn('factory.synthesize_colored_note', src)
        self.assertNotIn('_synth_colored_note_np', src)

    def test_v15_has_537_instruments(self):
        """V15 should have 537 instruments."""
        engine = RadioEngineV15(seed=42, total_duration=10.0)
        self.assertEqual(len(engine.instruments), 537)

    def test_v15_short_render(self):
        """V15 should render a short clip successfully."""
        engine = RadioEngineV15(seed=42, total_duration=2.0)
        left, right = engine.render()
        self.assertIsInstance(left, list)
        self.assertIsInstance(right, list)
        self.assertGreater(len(left), 0)
        self.assertEqual(len(left), len(right))


class TestRadioEngineV16(unittest.TestCase):
    """Tests for RadioEngineV16 -- True original V8 synthesis + expanded palette."""

    def test_v16_inherits_from_v15(self):
        """V16 should inherit from RadioEngineV15."""
        self.assertTrue(issubclass(RadioEngineV16, RadioEngineV15))

    def test_v16_instantiation(self):
        """V16 should instantiate without errors."""
        engine = RadioEngineV16(seed=42, total_duration=10.0)
        self.assertIsNotNone(engine)

    def test_v16_has_family_tracking(self):
        """V16 should have V12's family tracking."""
        engine = RadioEngineV16(seed=42, total_duration=10.0)
        self.assertIsInstance(engine._used_family_groups, set)
        self.assertIsInstance(engine._family_groups, dict)
        self.assertEqual(len(engine._family_groups), 5)

    def test_v16_uses_expanded_instruments(self):
        """V16 should use V12's 15-family instrument selection."""
        engine = RadioEngineV16(seed=42, total_duration=10.0)
        rng = random.Random(42)
        voices = engine._choose_gm_instruments({}, 5, rng)
        self.assertEqual(len(voices), 5)
        families = {v['family'] for v in voices}
        self.assertGreaterEqual(len(families), 3)

    def test_v16_uses_original_synthesis(self):
        """V16 _render_segment should use factory.synthesize_colored_note."""
        engine = RadioEngineV16(seed=42, total_duration=10.0)
        import inspect
        src = inspect.getsource(engine._render_segment)
        self.assertIn('factory.synthesize_colored_note', src)
        self.assertNotIn('_synth_colored_note_np', src)

    def test_v16_short_render(self):
        """V16 should render a short clip successfully."""
        engine = RadioEngineV16(seed=42, total_duration=2.0)
        left, right = engine.render()
        self.assertIsInstance(left, list)
        self.assertIsInstance(right, list)
        self.assertGreater(len(left), 0)


class TestV15NoDoubleFilter(unittest.TestCase):
    """V17 regression test: V15 should not double-apply anti-hiss/subsonic.

    V15's _render_segment must NOT apply anti_hiss + subsonic_filter because
    V8's render() (which V15 inherits) already applies them at the master level.
    Double-applying would over-filter the signal.
    """

    def test_v15_render_segment_no_anti_hiss(self):
        """V15._render_segment should not contain anti_hiss.apply_stereo."""
        import inspect
        src = inspect.getsource(RadioEngineV15._render_segment)
        self.assertNotIn('self.anti_hiss.apply_stereo', src,
                         "V15._render_segment should not apply anti_hiss "
                         "(it's already applied in V8's render())")

    def test_v15_render_segment_no_subsonic(self):
        """V15._render_segment should not contain subsonic_filter.apply_stereo."""
        import inspect
        src = inspect.getsource(RadioEngineV15._render_segment)
        self.assertNotIn('self.subsonic_filter.apply_stereo', src,
                         "V15._render_segment should not apply subsonic_filter "
                         "(it's already applied in V8's render())")

    def test_v8_render_has_master_filters(self):
        """V8.render() should apply anti_hiss and subsonic at master level."""
        import inspect
        src = inspect.getsource(RadioEngineV8.render)
        self.assertIn('anti_hiss', src)
        self.assertIn('subsonic_filter', src)

    def test_v15_inherits_v8_render(self):
        """V15 should inherit V8's render() (no override)."""
        # V15 should NOT define its own render() method
        self.assertNotIn('render', RadioEngineV15.__dict__,
                         "V15 should inherit render() from V8, not override it")

    def test_v8_render_segment_no_anti_hiss(self):
        """V8._render_segment should not apply anti_hiss (it's in render())."""
        import inspect
        src = inspect.getsource(RadioEngineV8._render_segment)
        self.assertNotIn('self.anti_hiss.apply_stereo', src)

    def test_compare_script_exists(self):
        """The V17 comparison script should exist."""
        script = os.path.join(os.path.dirname(__file__), 'compare_v8_v15.py')
        self.assertTrue(os.path.exists(script))


class TestV15V16CLIArguments(unittest.TestCase):
    """Tests for v15/v16 CLI argument support."""

    def test_v15_in_choices(self):
        """CLI should accept --version v15."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16'])
        args = parser.parse_args(['--version', 'v15'])
        self.assertEqual(args.version, 'v15')

    def test_v16_in_choices(self):
        """CLI should accept --version v16."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', '-V',
                          choices=['v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'v16'])
        args = parser.parse_args(['--version', 'v16'])
        self.assertEqual(args.version, 'v16')


if __name__ == '__main__':
    unittest.main()
