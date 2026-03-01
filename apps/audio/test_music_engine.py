#!/usr/bin/env python3
"""Tests for the structured music engine (music_engine.py)."""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from apps.audio.music_engine import (
    TimeSignature, TIME_SIGNATURES, EPOCH_TIME_SIGS,
    SCALES, CHORD_TYPES, PROGRESSIONS, EPOCH_MUSIC_STYLE,
    SampleBank, Track, DrumTrack, PhraseGenerator,
    BiquadFilter, MixBus, Section, MusicDirector,
    mtof, ftom, clamp,
)


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_mtof_a4(self):
        self.assertAlmostEqual(mtof(69), 440.0, places=1)

    def test_mtof_c4(self):
        self.assertAlmostEqual(mtof(60), 261.63, places=1)

    def test_mtof_octave(self):
        self.assertAlmostEqual(mtof(69 + 12), 880.0, places=1)

    def test_ftom_a4(self):
        self.assertAlmostEqual(ftom(440.0), 69, places=1)

    def test_ftom_roundtrip(self):
        for midi in [36, 48, 60, 72, 84, 96]:
            self.assertAlmostEqual(ftom(mtof(midi)), midi, places=5)

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)


class TestTimeSignature(unittest.TestCase):
    """Test time signature system."""

    def test_44_bar_duration(self):
        ts = TIME_SIGNATURES["4/4"]
        # At 120 BPM, 4 beats = 2 seconds
        self.assertAlmostEqual(ts.bar_duration(120), 2.0, places=2)

    def test_34_bar_duration(self):
        ts = TIME_SIGNATURES["3/4"]
        # At 120 BPM, 3 beats = 1.5 seconds
        self.assertAlmostEqual(ts.bar_duration(120), 1.5, places=2)

    def test_68_bar_duration(self):
        ts = TIME_SIGNATURES["6/8"]
        # 6 eighth notes at 120 BPM = 6 * 0.25s = 1.5s
        self.assertAlmostEqual(ts.bar_duration(120), 1.5, places=2)

    def test_78_bar_duration(self):
        ts = TIME_SIGNATURES["7/8"]
        # 7 eighth notes at 120 BPM = 7 * 0.25s = 1.75s
        self.assertAlmostEqual(ts.bar_duration(120), 1.75, places=2)

    def test_54_bar_duration(self):
        ts = TIME_SIGNATURES["5/4"]
        # 5 quarter notes at 120 BPM = 5 * 0.5s = 2.5s
        self.assertAlmostEqual(ts.bar_duration(120), 2.5, places=2)

    def test_bar_samples_positive(self):
        for name, ts in TIME_SIGNATURES.items():
            samples = ts.bar_samples(120)
            self.assertGreater(samples, 0, f"Time sig {name} should have positive samples")

    def test_beat_positions(self):
        ts = TIME_SIGNATURES["4/4"]
        positions = ts.beat_positions(120)
        self.assertEqual(len(positions), 4)
        # First beat should be downbeat at position 0
        self.assertEqual(positions[0][0], 0)
        self.assertTrue(positions[0][1])  # is_downbeat

    def test_strong_beats_44(self):
        ts = TIME_SIGNATURES["4/4"]
        strong = ts.strong_beats(120)
        self.assertGreater(len(strong), 0)
        self.assertEqual(strong[0], 0)

    def test_all_time_sigs_defined(self):
        expected = ["4/4", "3/4", "2/4", "6/8", "9/8", "12/8",
                    "5/4", "7/8", "7/4", "11/8", "3+3+2/8", "2+2+3/8"]
        for name in expected:
            self.assertIn(name, TIME_SIGNATURES)

    def test_epoch_time_sigs_valid(self):
        for epoch, sigs in EPOCH_TIME_SIGS.items():
            for sig_name in sigs:
                self.assertIn(sig_name, TIME_SIGNATURES,
                              f"Epoch {epoch} references undefined time sig {sig_name}")

    def test_beat_groups_sum(self):
        for name, ts in TIME_SIGNATURES.items():
            self.assertEqual(sum(ts.beat_groups), ts.numerator,
                             f"Time sig {name} beat groups don't sum to numerator")


class TestScalesAndChords(unittest.TestCase):
    """Test scale and chord definitions."""

    def test_all_scales_valid_intervals(self):
        for name, intervals in SCALES.items():
            self.assertGreater(len(intervals), 0, f"Scale {name} is empty")
            self.assertEqual(intervals[0], 0, f"Scale {name} doesn't start at 0")
            for i in intervals:
                self.assertGreaterEqual(i, 0, f"Scale {name} has negative interval")
                self.assertLess(i, 12, f"Scale {name} has interval >= 12")

    def test_all_chord_types_valid(self):
        for name, intervals in CHORD_TYPES.items():
            self.assertGreater(len(intervals), 0)
            self.assertEqual(intervals[0], 0, f"Chord {name} doesn't start at root")

    def test_all_progressions_reference_valid_chords(self):
        for name, prog in PROGRESSIONS.items():
            for degree, chord_type in prog:
                self.assertIn(chord_type, CHORD_TYPES,
                              f"Progression {name} references unknown chord type {chord_type}")

    def test_epoch_styles_defined(self):
        expected_epochs = [
            "Planck", "Inflation", "Electroweak", "Quark", "Hadron",
            "Nucleosynthesis", "Recombination", "Star Formation",
            "Solar System", "Earth", "Life", "DNA Era", "Present"
        ]
        for epoch in expected_epochs:
            self.assertIn(epoch, EPOCH_MUSIC_STYLE, f"Missing style for epoch {epoch}")

    def test_epoch_styles_reference_valid_scales(self):
        for epoch, style in EPOCH_MUSIC_STYLE.items():
            for scale in style["scales"]:
                self.assertIn(scale, SCALES,
                              f"Epoch {epoch} references undefined scale {scale}")

    def test_epoch_styles_reference_valid_progressions(self):
        for epoch, style in EPOCH_MUSIC_STYLE.items():
            for prog in style["progs"]:
                self.assertIn(prog, PROGRESSIONS,
                              f"Epoch {epoch} references undefined progression {prog}")

    def test_epoch_styles_have_tempo_range(self):
        for epoch, style in EPOCH_MUSIC_STYLE.items():
            lo, hi = style["tempo_range"]
            self.assertGreater(lo, 0)
            self.assertGreater(hi, lo)
            self.assertLess(hi, 300)


class TestSampleBank(unittest.TestCase):
    """Test sample loading and pitch shifting."""

    @classmethod
    def setUpClass(cls):
        cls.bank = SampleBank(preload=False)

    def test_load_piano(self):
        result = self.bank.load("piano")
        if result is not None:  # May not exist in CI
            samples, freq = result
            self.assertGreater(len(samples), 0)
            self.assertAlmostEqual(freq, 261.63, places=1)

    def test_get_pitched_returns_list(self):
        result = self.bank.load("piano")
        if result is None:
            self.skipTest("No samples available")
        pitched = self.bank.get_pitched("piano", 72, 44100)
        self.assertIsNotNone(pitched)
        self.assertEqual(len(pitched), 44100)

    def test_pitch_shift_higher(self):
        result = self.bank.load("piano")
        if result is None:
            self.skipTest("No samples available")
        base, _ = result
        # Higher pitch = shorter sample (when not fixed duration)
        pitched_high = self.bank.get_pitched("piano", 72)
        pitched_low = self.bank.get_pitched("piano", 48)
        if pitched_high and pitched_low:
            self.assertLess(len(pitched_high), len(pitched_low))

    def test_nonexistent_sample(self):
        result = self.bank.load("nonexistent_instrument_xyz")
        self.assertIsNone(result)


class TestTrack(unittest.TestCase):
    """Test instrument track rendering."""

    def test_track_creation(self):
        track = Track("test", "piano", gain=0.5, pan=0.0)
        self.assertEqual(track.name, "test")
        self.assertEqual(track.instrument, "piano")
        self.assertTrue(track.active)

    def test_render_empty_notes(self):
        track = Track("test", "piano")
        ts = TIME_SIGNATURES["4/4"]
        result = track.render_bar(None, 44100, ts, 120, None)
        self.assertEqual(len(result), 44100)
        self.assertTrue(all(s == 0.0 for s in result))

    def test_render_with_notes(self):
        track = Track("test", "piano")
        ts = TIME_SIGNATURES["4/4"]
        notes = [(0.0, 60, 1.0)]  # C4 for 1 beat
        result = track.render_bar(notes, 44100, ts, 120, None)
        self.assertEqual(len(result), 44100)
        # Should have some non-zero samples
        self.assertTrue(any(s != 0.0 for s in result))

    def test_inactive_track(self):
        track = Track("test", "piano")
        track.active = False
        ts = TIME_SIGNATURES["4/4"]
        notes = [(0.0, 60, 1.0)]
        result = track.render_bar(notes, 44100, ts, 120, None)
        self.assertTrue(all(s == 0.0 for s in result))


class TestDrumTrack(unittest.TestCase):
    """Test percussion track."""

    def test_drum_creation(self):
        drum = DrumTrack(gain=0.2)
        self.assertTrue(drum.active)

    def test_render_empty(self):
        drum = DrumTrack()
        ts = TIME_SIGNATURES["4/4"]
        result = drum.render_bar([], 44100, ts, 120)
        self.assertEqual(len(result), 44100)

    def test_render_with_hits(self):
        drum = DrumTrack()
        ts = TIME_SIGNATURES["4/4"]
        hits = [(0.0, "kick_drum", 0.8), (1.0, "snare_drum", 0.6)]
        result = drum.render_bar(hits, 44100, ts, 120)
        self.assertEqual(len(result), 44100)


class TestPhraseGenerator(unittest.TestCase):
    """Test phrase generation."""

    def setUp(self):
        import random
        self.gen = PhraseGenerator(random.Random(42))

    def test_generate_melody(self):
        scale = SCALES["major"]
        bars = self.gen.generate_melody(60, scale, [60, 64, 67], TIME_SIGNATURES["4/4"])
        self.assertEqual(len(bars), 2)  # 2-bar phrase
        for bar in bars:
            self.assertGreater(len(bar), 0)
            for pos, midi, dur in bar:
                self.assertGreaterEqual(pos, 0)
                self.assertGreaterEqual(midi, 36)
                self.assertLessEqual(midi, 96)
                self.assertGreater(dur, 0)

    def test_generate_bass(self):
        scale = SCALES["major"]
        notes = self.gen.generate_bass(60, scale, 0, TIME_SIGNATURES["4/4"])
        self.assertGreater(len(notes), 0)
        for pos, midi, dur in notes:
            self.assertLessEqual(midi, 60)  # Bass should be low

    def test_generate_chord_voicing(self):
        scale = SCALES["major"]
        notes = self.gen.generate_chord_voicing(60, scale, 0, "major", TIME_SIGNATURES["4/4"])
        self.assertEqual(len(notes), 3)  # Major triad
        for pos, midi, dur in notes:
            self.assertGreaterEqual(midi, 36)
            self.assertLessEqual(midi, 84)

    def test_generate_drums(self):
        hits = self.gen.generate_drums(TIME_SIGNATURES["4/4"], intensity=0.5)
        self.assertGreater(len(hits), 0)
        for pos, drum, vel in hits:
            self.assertGreaterEqual(pos, 0)
            self.assertGreater(vel, 0)

    def test_generate_drums_34(self):
        hits = self.gen.generate_drums(TIME_SIGNATURES["3/4"], intensity=0.5)
        self.assertGreater(len(hits), 0)


class TestBiquadFilter(unittest.TestCase):
    """Test frequency filters."""

    def test_lowpass_creation(self):
        f = BiquadFilter(4000, 0.707, 'lowpass')
        self.assertIsNotNone(f)

    def test_highpass_creation(self):
        f = BiquadFilter(80, 0.707, 'highpass')
        self.assertIsNotNone(f)

    def test_process_block(self):
        f = BiquadFilter(4000, 0.707, 'lowpass')
        samples = [math.sin(2 * math.pi * 1000 * i / 44100) for i in range(1000)]
        result = f.process_block(samples)
        self.assertEqual(len(result), 1000)

    def test_lowpass_attenuates_high(self):
        f = BiquadFilter(200, 0.707, 'lowpass')
        # Generate 10kHz tone
        samples = [math.sin(2 * math.pi * 10000 * i / 44100) for i in range(4410)]
        result = f.process_block(samples)
        # Output energy should be much less than input
        in_energy = sum(s * s for s in samples) / len(samples)
        out_energy = sum(s * s for s in result) / len(result)
        self.assertLess(out_energy, in_energy * 0.1)

    def test_highpass_attenuates_low(self):
        f = BiquadFilter(1000, 0.707, 'highpass')
        # Generate 50Hz tone
        samples = [math.sin(2 * math.pi * 50 * i / 44100) for i in range(44100)]
        result = f.process_block(samples)
        in_energy = sum(s * s for s in samples[-22050:]) / 22050
        out_energy = sum(s * s for s in result[-22050:]) / 22050
        self.assertLess(out_energy, in_energy * 0.1)


class TestMixBus(unittest.TestCase):
    """Test mixing bus."""

    def test_mix_empty(self):
        bus = MixBus()
        left, right = bus.mix_tracks([], 1000)
        self.assertEqual(len(left), 1000)
        self.assertEqual(len(right), 1000)

    def test_mix_single_track(self):
        bus = MixBus()
        mono = [0.5] * 1000
        left, right = bus.mix_tracks([(mono, 1.0, 0.0)], 1000)
        self.assertEqual(len(left), 1000)
        # Center pan should have equal L/R
        # (after filtering, values will be different but both non-zero)

    def test_mix_preserves_length(self):
        bus = MixBus()
        for n in [100, 882, 1000, 4410]:
            left, right = bus.mix_tracks([], n)
            self.assertEqual(len(left), n)
            self.assertEqual(len(right), n)

    def test_soft_limiter(self):
        bus = MixBus()
        # Very loud signal
        mono = [10.0] * 1000
        left, right = bus.mix_tracks([(mono, 1.0, 0.0)], 1000)
        for s in left:
            self.assertLessEqual(abs(s), 1.0)


class TestSection(unittest.TestCase):
    """Test musical sections."""

    def test_section_creation(self):
        sec = Section(
            TIME_SIGNATURES["4/4"], 120, 60, "major", "I-V-vi-IV",
            {"melody": "piano", "bass": "acoustic_bass"}, 8
        )
        self.assertEqual(sec.bpm, 120)
        self.assertEqual(sec.duration_bars, 8)

    def test_chord_cycling(self):
        sec = Section(
            TIME_SIGNATURES["4/4"], 120, 60, "major", "I-V-vi-IV",
            {}, 8
        )
        chords_seen = set()
        for bar in range(8):
            sec.current_bar = bar
            degree, ctype = sec.get_chord_for_bar()
            chords_seen.add((degree, ctype))
        self.assertGreater(len(chords_seen), 1)


class TestMusicDirector(unittest.TestCase):
    """Test the top-level music director."""

    def test_creation(self):
        director = MusicDirector(seed=42)
        self.assertIsNotNone(director)

    def test_compose_tick_returns_stereo(self):
        director = MusicDirector(seed=42)
        spt = int(44100 / 50)
        left, right = director.compose_tick(
            "Hadron", 4, 1e6, 50, 10, 0, 0, 0, spt
        )
        self.assertEqual(len(left), spt)
        self.assertEqual(len(right), spt)

    def test_compose_tick_not_silent(self):
        director = MusicDirector(seed=42)
        spt = int(44100 / 50)
        total_energy = 0.0
        for i in range(100):
            left, right = director.compose_tick(
                "Present", 12, 1e4, 50, 20, 10, 5, 3, spt
            )
            total_energy += sum(abs(s) for s in left[:100])
        self.assertGreater(total_energy, 0.0, "100 ticks produced silence")

    def test_epoch_transition(self):
        director = MusicDirector(seed=42)
        spt = int(44100 / 50)
        # Switch epochs — should not crash
        for epoch, idx in [("Planck", 0), ("Hadron", 4), ("Earth", 9), ("Present", 12)]:
            left, right = director.compose_tick(
                epoch, idx, 1e6, 50, 10, 5, 2, 0, spt
            )
            self.assertEqual(len(left), spt)

    def test_deterministic_with_seed(self):
        spt = int(44100 / 50)
        d1 = MusicDirector(seed=123)
        d2 = MusicDirector(seed=123)
        for i in range(10):
            l1, r1 = d1.compose_tick("Hadron", 4, 1e6, 50, 10, 0, 0, 0, spt)
            l2, r2 = d2.compose_tick("Hadron", 4, 1e6, 50, 10, 0, 0, 0, spt)
            self.assertEqual(l1[:10], l2[:10], f"Non-deterministic at tick {i}")

    def test_different_seeds_differ(self):
        spt = int(44100 / 50)
        d1 = MusicDirector(seed=1)
        d2 = MusicDirector(seed=999)
        l1_samples = []
        l2_samples = []
        for i in range(20):
            l1, _ = d1.compose_tick("Present", 12, 1e4, 50, 20, 10, 5, 3, spt)
            l2, _ = d2.compose_tick("Present", 12, 1e4, 50, 20, 10, 5, 3, spt)
            l1_samples.extend(l1[:10])
            l2_samples.extend(l2[:10])
        # With high probability, different seeds produce different output
        self.assertNotEqual(l1_samples, l2_samples)


class TestSampleGen(unittest.TestCase):
    """Test that sample generation works."""

    def test_sample_catalog_exists(self):
        from apps.audio.sample_gen import SAMPLE_CATALOG
        self.assertGreaterEqual(len(SAMPLE_CATALOG), 30)

    def test_all_generators_callable(self):
        from apps.audio.sample_gen import SAMPLE_CATALOG
        for name, fn in SAMPLE_CATALOG.items():
            self.assertTrue(callable(fn), f"{name} is not callable")

    def test_sample_files_exist(self):
        samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
        if not os.path.isdir(samples_dir):
            self.skipTest("Samples directory not found")
        files = [f for f in os.listdir(samples_dir) if f.endswith('.mp3')]
        self.assertGreaterEqual(len(files), 30, f"Only {len(files)} samples found")


class TestSpectralSafety(unittest.TestCase):
    """Test that output stays within safe frequency ranges."""

    def test_no_dc_offset(self):
        director = MusicDirector(seed=42)
        spt = int(44100 / 50)
        all_samples = []
        for i in range(50):
            left, _ = director.compose_tick("Present", 12, 1e4, 50, 20, 10, 5, 3, spt)
            all_samples.extend(left)
        if all_samples:
            mean = sum(all_samples) / len(all_samples)
            self.assertLess(abs(mean), 0.05, "DC offset detected")

    def test_output_in_range(self):
        director = MusicDirector(seed=42)
        spt = int(44100 / 50)
        for i in range(50):
            left, right = director.compose_tick("Present", 12, 1e4, 50, 20, 10, 5, 3, spt)
            for s in left:
                self.assertLessEqual(abs(s), 1.0, "Output exceeds [-1, 1]")
            for s in right:
                self.assertLessEqual(abs(s), 1.0, "Output exceeds [-1, 1]")


if __name__ == '__main__':
    unittest.main()
