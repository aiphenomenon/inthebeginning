#!/usr/bin/env python3
"""Tests for the cosmic simulation audio renderer."""

import math
import os
import sys
import tempfile
import unittest
import wave

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from apps.audio.generate import (
    mtof, clamp, MixBuffer, LowpassFilter,
    gen_sine_blip, gen_bell_tone, gen_pulse, gen_pad, gen_sequence,
    gen_impulse_response, CosmicAudioRenderer,
    SAMPLE_RATE, EPOCH_ROOTS, EPOCH_ORDER,
)


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_mtof_a4(self):
        """MIDI note 69 = A4 = 440 Hz."""
        self.assertAlmostEqual(mtof(69), 440.0, places=2)

    def test_mtof_c4(self):
        """MIDI note 60 = C4 = ~261.63 Hz."""
        self.assertAlmostEqual(mtof(60), 261.63, places=1)

    def test_mtof_octave(self):
        """An octave up doubles frequency."""
        self.assertAlmostEqual(mtof(72) / mtof(60), 2.0, places=4)

    def test_clamp_within(self):
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_clamp_below(self):
        self.assertEqual(clamp(-5, 0, 10), 0)

    def test_clamp_above(self):
        self.assertEqual(clamp(15, 0, 10), 10)


class TestMixBuffer(unittest.TestCase):
    """Test the stereo mixing buffer."""

    def test_creation(self):
        buf = MixBuffer(1000)
        self.assertEqual(buf.num_samples, 1000)
        self.assertEqual(len(buf.left), 1000)
        self.assertEqual(len(buf.right), 1000)

    def test_add_mono(self):
        buf = MixBuffer(100)
        samples = [0.5] * 10
        buf.add_mono(samples, 0, pan=0.0, gain=1.0)
        # Center-panned mono should appear in both channels
        self.assertGreater(buf.left[0], 0)
        self.assertGreater(buf.right[0], 0)

    def test_add_mono_hard_left(self):
        buf = MixBuffer(100)
        samples = [1.0] * 10
        buf.add_mono(samples, 0, pan=-1.0, gain=1.0)
        self.assertGreater(buf.left[0], buf.right[0])

    def test_to_pcm16_length(self):
        buf = MixBuffer(100)
        pcm = buf.to_pcm16()
        # 100 samples * 2 channels * 2 bytes = 400 bytes
        self.assertEqual(len(pcm), 400)

    def test_to_pcm16_soft_limit(self):
        """Large values should be soft-limited (tanh)."""
        buf = MixBuffer(1)
        buf.left[0] = 100.0  # Way beyond 1.0
        pcm = buf.to_pcm16()
        import struct
        l_val = struct.unpack('<h', pcm[:2])[0]
        # Should be near MAX_AMPLITUDE due to tanh saturation
        self.assertGreater(abs(l_val), 30000)


class TestInstruments(unittest.TestCase):
    """Test instrument voice generators."""

    def test_sine_blip_returns_samples(self):
        samples, pan = gen_sine_blip(440, duration=0.08)
        self.assertGreater(len(samples), 0)
        self.assertAlmostEqual(pan, 0.0)

    def test_sine_blip_has_sound(self):
        samples, _ = gen_sine_blip(440, duration=0.08)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)

    def test_sine_blip_decays(self):
        samples, _ = gen_sine_blip(440, duration=0.1)
        # Last quarter should be quieter than first quarter
        n = len(samples)
        q1_peak = max(abs(s) for s in samples[:n // 4])
        q4_peak = max(abs(s) for s in samples[3 * n // 4:])
        self.assertGreater(q1_peak, q4_peak)

    def test_bell_tone_returns_samples(self):
        samples = gen_bell_tone(440, decay=0.5)
        self.assertGreater(len(samples), 0)

    def test_bell_tone_has_fm_character(self):
        """FM synthesis should produce complex harmonics."""
        samples = gen_bell_tone(440, decay=0.5)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)

    def test_pulse_returns_samples(self):
        samples = gen_pulse(80, width=0.15)
        self.assertGreater(len(samples), 0)

    def test_pulse_has_sound(self):
        samples = gen_pulse(80, width=0.15)
        peak = max(abs(s) for s in samples)
        self.assertGreater(peak, 0.01)

    def test_pad_returns_stereo(self):
        left, right = gen_pad([60, 63, 67, 70], sustain=1.0)
        self.assertEqual(len(left), len(right))
        self.assertGreater(len(left), 0)

    def test_pad_has_fade_in(self):
        """Pad should start quiet and fade in."""
        left, right = gen_pad([60], sustain=2.0)
        # First 100 samples should be very quiet
        early_peak = max(abs(s) for s in left[:100])
        # Mid section should be louder
        mid = len(left) // 2
        mid_peak = max(abs(s) for s in left[mid:mid + 1000])
        self.assertGreater(mid_peak, early_peak)

    def test_sequence_returns_samples(self):
        samples = gen_sequence([60, 64, 67, 72], tempo=8)
        self.assertGreater(len(samples), 0)

    def test_sequence_length_matches_tempo(self):
        notes = [60, 64, 67, 72]
        tempo = 8
        samples = gen_sequence(notes, tempo)
        expected_dur = len(notes) / tempo + 0.02  # plus overlap
        expected_samples = int(SAMPLE_RATE * expected_dur)
        self.assertAlmostEqual(len(samples), expected_samples, delta=10)


class TestImpulseResponse(unittest.TestCase):
    """Test reverb impulse response generator."""

    def test_returns_stereo(self):
        ir_l, ir_r = gen_impulse_response(1.0, 2.0)
        self.assertEqual(len(ir_l), len(ir_r))
        self.assertEqual(len(ir_l), SAMPLE_RATE)

    def test_decays(self):
        ir_l, _ = gen_impulse_response(1.0, 2.0)
        # Early samples should be louder than late samples (on average)
        early_energy = sum(s * s for s in ir_l[:1000]) / 1000
        late_energy = sum(s * s for s in ir_l[-1000:]) / 1000
        self.assertGreater(early_energy, late_energy)


class TestLowpassFilter(unittest.TestCase):
    """Test biquad lowpass filter."""

    def test_creation(self):
        lpf = LowpassFilter(1000, 0.707)
        self.assertEqual(lpf.cutoff, 1000)

    def test_passes_low_frequencies(self):
        """A 100 Hz sine should pass through a 1000 Hz lowpass."""
        lpf = LowpassFilter(1000, 0.707)
        # Generate 100 Hz sine
        samples = [math.sin(2 * math.pi * 100 * i / SAMPLE_RATE) for i in range(4410)]
        filtered = lpf.process_block(samples)
        # Output should have significant energy
        energy = sum(s * s for s in filtered[1000:]) / 3410  # skip transient
        self.assertGreater(energy, 0.1)

    def test_attenuates_high_frequencies(self):
        """A 10000 Hz sine should be attenuated by a 500 Hz lowpass."""
        lpf = LowpassFilter(500, 0.707)
        samples = [math.sin(2 * math.pi * 10000 * i / SAMPLE_RATE) for i in range(4410)]
        filtered = lpf.process_block(samples)
        in_energy = sum(s * s for s in samples) / len(samples)
        out_energy = sum(s * s for s in filtered[1000:]) / 3410
        self.assertGreater(in_energy, out_energy * 10)  # At least 10x attenuation

    def test_set_cutoff(self):
        lpf = LowpassFilter(1000, 0.707)
        lpf.set_cutoff(2000)
        self.assertEqual(lpf.cutoff, 2000)


class TestEpochMapping(unittest.TestCase):
    """Test epoch-to-music mappings."""

    def test_all_epochs_have_roots(self):
        for epoch in EPOCH_ORDER:
            self.assertIn(epoch, EPOCH_ROOTS)

    def test_root_notes_ascending(self):
        """Root notes should generally ascend through epochs."""
        roots = [EPOCH_ROOTS[e] for e in EPOCH_ORDER]
        self.assertEqual(roots[0], 60)   # C4
        self.assertEqual(roots[-1], 84)  # C6

    def test_epoch_count(self):
        self.assertEqual(len(EPOCH_ORDER), 13)
        self.assertEqual(len(EPOCH_ROOTS), 13)


class TestCosmicAudioRenderer(unittest.TestCase):
    """Test the main audio renderer."""

    def test_creation(self):
        renderer = CosmicAudioRenderer(seed=42, ticks_per_second=50)
        self.assertIsNotNone(renderer.universe)

    def test_render_chunk(self):
        renderer = CosmicAudioRenderer(seed=42, ticks_per_second=50)
        pcm = renderer.render_chunk(50)  # 1 second
        expected_bytes = 50 * int(SAMPLE_RATE / 50) * 4  # ticks * samples_per_tick * 2ch * 2bytes
        self.assertEqual(len(pcm), expected_bytes)

    def test_render_chunk_not_silent(self):
        """Rendered audio should not be all zeros."""
        renderer = CosmicAudioRenderer(seed=42, ticks_per_second=50)
        pcm = renderer.render_chunk(100)
        # Check that not all bytes are zero
        non_zero = sum(1 for b in pcm if b != 0)
        self.assertGreater(non_zero, 0)

    def test_epoch_progression(self):
        """After enough ticks the epoch should advance."""
        renderer = CosmicAudioRenderer(seed=42, ticks_per_second=500)
        renderer.render_chunk(200)  # 200 ticks
        epoch1 = renderer.universe.current_epoch_name
        renderer.render_chunk(5000)
        epoch2 = renderer.universe.current_epoch_name
        # Should have progressed
        idx1 = EPOCH_ORDER.index(epoch1)
        idx2 = EPOCH_ORDER.index(epoch2)
        self.assertGreater(idx2, idx1)

    def test_wav_output(self):
        """Write a short WAV file and verify it's valid."""
        renderer = CosmicAudioRenderer(seed=42, ticks_per_second=100)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmpfile = f.name
        try:
            from apps.audio.generate import write_wav
            write_wav(renderer, 2, tmpfile, progress=False)
            # Verify it's a valid WAV
            with wave.open(tmpfile, 'rb') as wf:
                self.assertEqual(wf.getnchannels(), 2)
                self.assertEqual(wf.getsampwidth(), 2)
                self.assertEqual(wf.getframerate(), SAMPLE_RATE)
                frames = wf.getnframes()
                self.assertGreater(frames, 0)
        finally:
            os.unlink(tmpfile)


if __name__ == '__main__':
    unittest.main()
