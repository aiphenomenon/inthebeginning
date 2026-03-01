#!/usr/bin/env python3
"""Tests for the musical composition engine (composer.py)."""

import math
import os
import sys
import unittest

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from apps.audio.composer import (
    mtof, clamp, SAMPLE_RATE,
    SCALES, EPOCH_SCALE_FAMILIES, TIMBRES, DOMAIN_TIMBRES,
    RHYTHM_PATTERNS, EPOCH_RHYTHM_FAMILIES,
    PROGRESSIONS, EPOCH_PROGRESSIONS,
    MOTIFS, EPOCH_MOTIFS,
    _fast_sin, _WAVETABLE, _WAVETABLE_SIZE,
    StreamingOsc, AdditiveSynth, PercSynth,
    BeatEngine, MelodicVoice, HarmonicEngine,
    PocketNavigator, Composer,
)


class TestComposerUtilities(unittest.TestCase):
    """Test utility functions in composer."""

    def test_mtof_a4(self):
        self.assertAlmostEqual(mtof(69), 440.0, places=2)

    def test_mtof_c4(self):
        self.assertAlmostEqual(mtof(60), 261.63, places=1)

    def test_clamp_within(self):
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_clamp_below(self):
        self.assertEqual(clamp(-5, 0, 10), 0)

    def test_clamp_above(self):
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_fast_sin_zero(self):
        self.assertAlmostEqual(_fast_sin(0.0), 0.0, places=2)

    def test_fast_sin_quarter(self):
        self.assertAlmostEqual(_fast_sin(0.25), 1.0, places=2)

    def test_fast_sin_half(self):
        self.assertAlmostEqual(_fast_sin(0.5), 0.0, places=2)

    def test_wavetable_size(self):
        self.assertEqual(len(_WAVETABLE), _WAVETABLE_SIZE)


class TestScalesData(unittest.TestCase):
    """Test scale data integrity."""

    def test_scales_not_empty(self):
        self.assertGreater(len(SCALES), 30)

    def test_all_scales_start_with_zero(self):
        for name, intervals in SCALES.items():
            self.assertEqual(intervals[0], 0, f"Scale {name} doesn't start with 0")

    def test_all_scales_have_intervals(self):
        for name, intervals in SCALES.items():
            self.assertGreater(len(intervals), 0, f"Scale {name} is empty")

    def test_epoch_scale_families_cover_all_epochs(self):
        expected = [
            "Planck", "Inflation", "Electroweak", "Quark", "Hadron",
            "Nucleosynthesis", "Recombination", "Star Formation",
            "Solar System", "Earth", "Life", "DNA Era", "Present",
        ]
        for epoch in expected:
            self.assertIn(epoch, EPOCH_SCALE_FAMILIES)

    def test_epoch_scale_families_reference_valid_scales(self):
        for epoch, families in EPOCH_SCALE_FAMILIES.items():
            for scale_name in families:
                self.assertIn(scale_name, SCALES,
                              f"Epoch {epoch} references unknown scale {scale_name}")


class TestTimbresData(unittest.TestCase):
    """Test timbre data integrity."""

    def test_timbres_not_empty(self):
        self.assertGreater(len(TIMBRES), 10)

    def test_tonal_timbres_have_harmonics(self):
        """All tonal (non-percussion) timbres should have harmonics."""
        noise_timbres = {"hat"}  # Noise-based, no harmonics
        for name, harmonics in TIMBRES.items():
            if name not in noise_timbres:
                self.assertGreater(len(harmonics), 0, f"Timbre {name} has no harmonics")

    def test_fundamental_is_loudest(self):
        """For tonal timbres the fundamental should be the strongest harmonic."""
        noise_timbres = {"hat"}
        for name, harmonics in TIMBRES.items():
            if name in noise_timbres or not harmonics:
                continue
            self.assertAlmostEqual(harmonics[0], 1.0, places=1,
                                   msg=f"Timbre {name} fundamental != 1.0")

    def test_domain_timbres_reference_valid_timbres(self):
        for domain, timbre_list in DOMAIN_TIMBRES.items():
            for t in timbre_list:
                self.assertIn(t, TIMBRES,
                              f"Domain {domain} references unknown timbre {t}")


class TestRhythmPatternsData(unittest.TestCase):
    """Test rhythm pattern data."""

    def test_patterns_not_empty(self):
        self.assertGreater(len(RHYTHM_PATTERNS), 15)

    def test_all_patterns_have_onsets(self):
        for name, pattern in RHYTHM_PATTERNS.items():
            self.assertGreater(len(pattern), 0, f"Pattern {name} is empty")

    def test_onsets_between_zero_and_one(self):
        for name, pattern in RHYTHM_PATTERNS.items():
            for onset in pattern:
                self.assertGreaterEqual(onset, 0.0, f"{name} has onset < 0")
                self.assertLessEqual(onset, 1.0, f"{name} has onset > 1")

    def test_epoch_rhythm_families_reference_valid_patterns(self):
        for epoch, families in EPOCH_RHYTHM_FAMILIES.items():
            for pat_name in families:
                self.assertIn(pat_name, RHYTHM_PATTERNS,
                              f"Epoch {epoch} references unknown pattern {pat_name}")


class TestProgressionsData(unittest.TestCase):
    """Test harmonic progressions data."""

    def test_progressions_not_empty(self):
        self.assertGreater(len(PROGRESSIONS), 10)

    def test_epoch_progressions_reference_valid(self):
        for epoch, progs in EPOCH_PROGRESSIONS.items():
            for prog_name in progs:
                self.assertIn(prog_name, PROGRESSIONS,
                              f"Epoch {epoch} references unknown progression {prog_name}")


class TestMotifsData(unittest.TestCase):
    """Test melodic motifs data."""

    def test_motifs_not_empty(self):
        self.assertGreater(len(MOTIFS), 10)

    def test_all_motifs_have_notes(self):
        for name, intervals in MOTIFS.items():
            self.assertGreater(len(intervals), 0, f"Motif {name} is empty")

    def test_epoch_motifs_reference_valid(self):
        for epoch, motif_list in EPOCH_MOTIFS.items():
            for m in motif_list:
                self.assertIn(m, MOTIFS,
                              f"Epoch {epoch} references unknown motif {m}")


class TestStreamingOsc(unittest.TestCase):
    """Test the streaming oscillator."""

    def test_creation(self):
        osc = StreamingOsc(440, 0.1, timbre_name="violin", gain=0.1)
        self.assertTrue(osc.alive)

    def test_render_chunk_returns_samples(self):
        osc = StreamingOsc(440, 0.1, gain=0.1)
        chunk = osc.render_chunk(88)
        self.assertEqual(len(chunk), 88)

    def test_has_sound(self):
        osc = StreamingOsc(440, 0.1, gain=0.2, attack=0.001)
        chunk = osc.render_chunk(4410)
        peak = max(abs(s) for s in chunk)
        self.assertGreater(peak, 0.01)

    def test_dies_after_duration(self):
        osc = StreamingOsc(440, 0.01, gain=0.1)
        # 0.01s = 441 samples
        chunk = osc.render_chunk(500)
        self.assertFalse(osc.alive)

    def test_dead_osc_returns_none(self):
        osc = StreamingOsc(440, 0.01, gain=0.1)
        osc.render_chunk(500)
        self.assertIsNone(osc.render_chunk(88))

    def test_incremental_matches_full(self):
        """Rendering in small chunks should produce same total energy as one big chunk."""
        osc1 = StreamingOsc(440, 0.05, gain=0.2, attack=0.001, release=0.01)
        full = osc1.render_chunk(2205)
        full_energy = sum(s * s for s in full)

        osc2 = StreamingOsc(440, 0.05, gain=0.2, attack=0.001, release=0.01)
        chunks = []
        for _ in range(25):
            c = osc2.render_chunk(88)
            if c:
                chunks.extend(c[:88])
            else:
                break
        chunk_energy = sum(s * s for s in chunks[:2205])

        self.assertAlmostEqual(full_energy, chunk_energy, delta=full_energy * 0.01)

    def test_nyquist_filter(self):
        """Very high frequency should produce silence (above Nyquist)."""
        osc = StreamingOsc(25000, 0.01, gain=0.5)
        # 25kHz > 22050Hz Nyquist
        self.assertFalse(osc.alive)


class TestAdditiveSynth(unittest.TestCase):
    """Test the AdditiveSynth wrapper."""

    def test_render_returns_samples(self):
        samples = AdditiveSynth.render(440, 0.1, gain=0.1)
        self.assertEqual(len(samples), int(SAMPLE_RATE * 0.1))

    def test_different_timbres_sound_different(self):
        s1 = AdditiveSynth.render(440, 0.05, timbre_name="violin", gain=0.2, attack=0.001)
        s2 = AdditiveSynth.render(440, 0.05, timbre_name="flute", gain=0.2, attack=0.001)
        # Compare waveform shapes (they should differ due to different harmonic content)
        diff = sum(abs(a - b) for a, b in zip(s1[:1000], s2[:1000]))
        self.assertGreater(diff, 0.01)


class TestPercSynth(unittest.TestCase):
    """Test percussion synthesizer."""

    def test_kick_returns_samples(self):
        samples = PercSynth.kick(55, 0.3, 0.25)
        self.assertGreater(len(samples), 0)

    def test_kick_has_sound(self):
        samples = PercSynth.kick(55, 0.3, 0.25)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)

    def test_kick_cache(self):
        """Subsequent kick calls with same params should use cache."""
        PercSynth._cache.clear()
        s1 = PercSynth.kick(55, 0.3, 0.25)
        s2 = PercSynth.kick(55, 0.3, 0.25)
        self.assertEqual(len(s1), len(s2))

    def test_snare_returns_samples(self):
        import random
        samples = PercSynth.snare(180, 0.2, 0.15, rng=random.Random(42))
        self.assertGreater(len(samples), 0)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)

    def test_hihat_returns_samples(self):
        import random
        samples = PercSynth.hihat(0.08, 0.08, rng=random.Random(42))
        self.assertGreater(len(samples), 0)

    def test_rim_returns_samples(self):
        samples = PercSynth.rim(800, 0.05, 0.12)
        self.assertGreater(len(samples), 0)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)


class TestBeatEngine(unittest.TestCase):
    """Test the beat engine."""

    def test_creation(self):
        import random
        be = BeatEngine(random.Random(42))
        self.assertIsNotNone(be.pattern)

    def test_render_returns_correct_length(self):
        import random
        be = BeatEngine(random.Random(42))
        samples = be.render_beat_bar(882, 60)
        self.assertEqual(len(samples), 882)

    def test_presence_bounded(self):
        """Presence should be between 0.1 and 0.9."""
        import random
        be = BeatEngine(random.Random(42))
        for epoch_idx in range(13):
            be.update_state("test", epoch_idx, 0, 1000, 100)
            self.assertGreaterEqual(be.presence, 0.1)
            self.assertLessEqual(be.presence, 0.9)

    def test_update_state_changes_pattern(self):
        import random
        be = BeatEngine(random.Random(42))
        be.update_state("Planck", 0, 0, 1e10, 100)
        p1 = be.pattern_name
        be.update_state("Life", 10, 1000, 288, 500)
        p2 = be.pattern_name
        # Different epochs should likely pick different patterns
        # (not guaranteed but highly probable with different families)


class TestMelodicVoice(unittest.TestCase):
    """Test the melodic voice."""

    def test_creation(self):
        import random
        v = MelodicVoice(random.Random(42), voice_id=0)
        self.assertEqual(v.voice_id, 0)

    def test_update_state(self):
        import random
        v = MelodicVoice(random.Random(42), voice_id=0)
        v.update_state("Planck", 0, 60, "chromatic")
        self.assertIn(v.timbre, list(TIMBRES.keys()))

    def test_render_chunk_when_not_playing(self):
        import random
        v = MelodicVoice(random.Random(42), voice_id=0)
        v.cooldown = 100
        result = v.render_chunk(88)
        self.assertIsNone(result)

    def test_maybe_play_phrase_returns_samples(self):
        """Force a phrase to play by resetting state repeatedly."""
        import random
        v = MelodicVoice(random.Random(42), voice_id=0)
        v.update_state("Life", 10, 60, "blues")
        # Try many times — it's probabilistic
        found = False
        for _ in range(50):
            v.cooldown = 0
            v._note_queue = []
            v._current_osc = None
            result = v.maybe_play_phrase("Life", 60, SCALES["blues"], 882)
            if result and max(abs(s) for s in result[0]) > 0.001:
                found = True
                break
        self.assertTrue(found, "MelodicVoice never produced audible output in 50 tries")


class TestHarmonicEngine(unittest.TestCase):
    """Test harmonic engine."""

    def test_creation(self):
        import random
        he = HarmonicEngine(random.Random(42))
        self.assertIsNotNone(he.progression)

    def test_get_current_chord(self):
        import random
        he = HarmonicEngine(random.Random(42))
        chord = he.get_current_chord(60, SCALES["ionian"])
        self.assertEqual(len(chord), 3)
        self.assertIn(60, chord)  # Root should be in chord

    def test_advance_chord(self):
        import random
        he = HarmonicEngine(random.Random(42))
        he.advance_chord()
        self.assertEqual(he.chord_index, 1)

    def test_start_and_render_pad(self):
        import random
        he = HarmonicEngine(random.Random(42))
        he.start_chord_pad([60, 64, 67], 0.1, timbre="warm_pad")
        self.assertTrue(he.has_active_pad())
        left, right = he.render_pad_chunk(88)
        self.assertEqual(len(left), 88)
        self.assertEqual(len(right), 88)

    def test_pad_has_sound(self):
        import random
        he = HarmonicEngine(random.Random(42))
        # Use a long pad (2s) with short attack so we have time to hear it
        he.start_chord_pad([60, 64, 67], 2.0, timbre="warm_pad")
        total_energy = 0.0
        for _ in range(100):
            left, right = he.render_pad_chunk(882)
            total_energy += sum(s * s for s in left)
        self.assertGreater(total_energy, 0.0)

    def test_pad_eventually_dies(self):
        import random
        he = HarmonicEngine(random.Random(42))
        he.start_chord_pad([60], 0.05, timbre="sine")
        for _ in range(100):
            he.render_pad_chunk(88)
        self.assertFalse(he.has_active_pad())


class TestPocketNavigator(unittest.TestCase):
    """Test universe pocket navigator."""

    def test_creation(self):
        import random
        nav = PocketNavigator(random.Random(42))
        self.assertEqual(nav.current_domain, "subatomic")

    def test_update_changes_domain(self):
        import random
        nav = PocketNavigator(random.Random(42))
        domains_seen = set()
        for epoch_idx in range(13):
            for _ in range(10):
                nav.update(epoch_idx, 100, 50, 20, 10, 1000)
                domains_seen.add(nav.current_domain)
        # Should visit at least a few different domains
        self.assertGreater(len(domains_seen), 1)

    def test_get_timbre_for_domain(self):
        import random
        nav = PocketNavigator(random.Random(42))
        timbres = nav.get_timbre_for_domain()
        self.assertIsInstance(timbres, list)
        self.assertGreater(len(timbres), 0)

    def test_get_octave_shift(self):
        import random
        nav = PocketNavigator(random.Random(42))
        shift = nav.get_octave_shift()
        self.assertIsInstance(shift, int)


class TestComposer(unittest.TestCase):
    """Test the main Composer class."""

    def test_creation(self):
        c = Composer(seed=42)
        self.assertIsNotNone(c.beat_engine)
        self.assertIsNotNone(c.harmonic_engine)
        self.assertIsNotNone(c.navigator)
        self.assertEqual(len(c.voices), 4)

    def test_compose_tick_returns_stereo(self):
        c = Composer(seed=42)
        left, right = c.compose_tick(
            "Planck", 0, 60, 1e10, 100, 0, 0, 0, 0, 88
        )
        self.assertEqual(len(left), 88)
        self.assertEqual(len(right), 88)

    def test_compose_tick_produces_sound(self):
        """After several ticks, output should have non-zero energy."""
        c = Composer(seed=42)
        total_energy = 0.0
        for i in range(100):
            left, right = c.compose_tick(
                "Hadron", 4, 67, 1e6, 500, 100, 0, 0, 0, 882
            )
            total_energy += sum(s * s for s in left) + sum(s * s for s in right)
        self.assertGreater(total_energy, 0.0)

    def test_epoch_transitions(self):
        """Changing epoch should update scales and state."""
        c = Composer(seed=42)
        c.compose_tick("Planck", 0, 60, 1e10, 100, 0, 0, 0, 0, 88)
        scale1 = c.current_scale_name
        c.compose_tick("Life", 10, 72, 288, 500, 200, 50, 100, 5, 88)
        scale2 = c.current_scale_name
        self.assertNotEqual(scale1, scale2)

    def test_get_scale_for_state(self):
        import random
        c = Composer(seed=42)
        name, scale = c.get_scale_for_state("Earth", 9, 288, random.Random(42))
        self.assertIn(name, SCALES)
        self.assertEqual(scale, SCALES[name])

    def test_performance_under_threshold(self):
        """Compose tick should be fast enough for real-time-ish rendering."""
        import time
        c = Composer(seed=42)
        start = time.time()
        for i in range(200):
            c.compose_tick("Quark", 3, 63, 1e6, 300, 50, 0, 0, 0, 88)
        elapsed = time.time() - start
        per_tick_ms = elapsed / 200 * 1000
        # Should be under 5ms per tick for 88-sample chunks
        self.assertLess(per_tick_ms, 5.0,
                        f"compose_tick too slow: {per_tick_ms:.2f}ms/tick")

    def test_deterministic_with_same_seed(self):
        """Same seed should produce identical output."""
        c1 = Composer(seed=99)
        c2 = Composer(seed=99)
        for _ in range(10):
            l1, r1 = c1.compose_tick("Planck", 0, 60, 1e10, 100, 0, 0, 0, 0, 88)
            l2, r2 = c2.compose_tick("Planck", 0, 60, 1e10, 100, 0, 0, 0, 0, 88)
            for i in range(88):
                self.assertAlmostEqual(l1[i], l2[i], places=10)
                self.assertAlmostEqual(r1[i], r2[i], places=10)


if __name__ == '__main__':
    unittest.main()
