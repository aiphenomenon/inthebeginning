#!/usr/bin/env python3
"""V17 Full Comparison: Render with 1800s segment plan, compare first 160s.

Renders V8 and V15 variants using total_duration=1800.0 (matching the original
MP3 segment plan) via render_streaming(), but captures only the first ~160s
of audio — before any TTS injection at ~162s.

This gives a true apples-to-apples comparison of the TONAL quality against
the original V8 MP3, using the correct segment plan and streaming path.

Five variants:
  1. Repo V8 MP3 (first 160s decoded via ffmpeg)
  2. V8 streaming, numpy ON, 1800s plan
  3. V8 streaming, numpy OFF, 1800s plan
  4. V15 (bugfixed) streaming, V8 tempo, numpy ON, 1800s plan
  5. V15 (bugfixed) streaming, V8 tempo, numpy OFF, 1800s plan

Usage:
    python apps/audio/compare_v8_v15_full.py
"""

import hashlib
import math
import os
import struct
import sys
import tempfile
import time as _time
import wave

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

import apps.audio.radio_engine as mod
from apps.audio.radio_engine import RadioEngineV8, RadioEngineV15, SAMPLE_RATE

# How many seconds of pure music to compare (before TTS at ~162s)
COMPARE_SECONDS = 160.0
COMPARE_SAMPLES = int(COMPARE_SECONDS * SAMPLE_RATE)


class _EarlyStopError(Exception):
    """Raised to abort streaming after capturing enough audio."""
    pass


class _CapturingWavFile:
    """Fake WAV file that captures PCM frames and stops early.

    Implements just enough of the wave.Wave_write interface for
    render_streaming to work: setnchannels, setsampwidth, setframerate,
    writeframes.
    """

    def __init__(self, max_frames):
        self._max_frames = max_frames
        self._data = bytearray()
        self._frames_written = 0

    def setnchannels(self, n):
        """Set number of channels (ignored, always 2)."""
        pass

    def setsampwidth(self, w):
        """Set sample width (ignored, always 2)."""
        pass

    def setframerate(self, r):
        """Set frame rate (ignored, always SAMPLE_RATE)."""
        pass

    def writeframes(self, data):
        """Capture frame data, stop when we have enough."""
        n_new_frames = len(data) // 4  # 2 channels * 2 bytes
        self._data.extend(data)
        self._frames_written += n_new_frames
        if self._frames_written >= self._max_frames:
            raise _EarlyStopError("Captured enough audio")

    def get_samples(self):
        """Return (left, right) float lists from captured data."""
        left, right = [], []
        n = len(self._data) // 4
        for i in range(n):
            off = i * 4
            if off + 4 > len(self._data):
                break
            l = struct.unpack_from('<h', self._data, off)[0] / 32767.0
            r = struct.unpack_from('<h', self._data, off + 2)[0] / 32767.0
            left.append(l)
            right.append(r)
        return left, right


def render_streaming_capture(engine_class, seed, force_numpy, tempo_override=None):
    """Render with 1800s plan via streaming, capture first COMPARE_SECONDS.

    Uses a fake WAV writer that aborts early once enough audio is captured,
    so we don't render all 1800s — just enough for the first segment.

    Returns (left, right) float lists, truncated to COMPARE_SAMPLES.
    """
    saved = mod.HAS_NUMPY
    mod.HAS_NUMPY = force_numpy

    try:
        engine = engine_class(seed=seed, total_duration=1800.0)

        if tempo_override == 'v8':
            def v8_tempo(sim_state):
                """V8's tempo: 1.5 + 1.0 * hash."""
                if not sim_state:
                    return 2.0
                s = repr(sorted(sim_state.items()))
                h = hashlib.sha256(s.encode()).hexdigest()[:8]
                return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)
            engine._compute_tempo_multiplier = v8_tempo

        # Use capturing WAV that stops after enough frames
        # Request a bit more than COMPARE_SAMPLES to ensure we have enough
        cap = _CapturingWavFile(COMPARE_SAMPLES + SAMPLE_RATE)

        try:
            engine.render_streaming(cap)
        except _EarlyStopError:
            pass  # Expected — we got enough audio

        left, right = cap.get_samples()
        return left[:COMPARE_SAMPLES], right[:COMPARE_SAMPLES]
    finally:
        mod.HAS_NUMPY = saved


def _read_wav(path):
    """Read WAV -> (left, right) float lists."""
    with wave.open(path, 'rb') as wf:
        n = wf.getnframes()
        data = wf.readframes(n)
    left, right = [], []
    for i in range(n):
        off = i * 4
        l = struct.unpack_from('<h', data, off)[0] / 32767.0
        r = struct.unpack_from('<h', data, off + 2)[0] / 32767.0
        left.append(l)
        right.append(r)
    return left, right


def decode_mp3_first_n(mp3_path, n_samples):
    """Decode MP3 and return first n_samples of (left, right)."""
    import subprocess
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        wav_path = tmp.name
    try:
        dur = n_samples / SAMPLE_RATE + 1  # +1s margin
        subprocess.run(
            ['ffmpeg', '-y', '-i', mp3_path, '-t', str(dur),
             '-ar', str(SAMPLE_RATE), '-ac', '2', '-sample_fmt', 's16',
             wav_path],
            capture_output=True, timeout=120
        )
        left, right = _read_wav(wav_path)
        return left[:n_samples], right[:n_samples]
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def pcm_md5(left, right):
    """MD5 of interleaved PCM16."""
    h = hashlib.md5()
    for i in range(min(len(left), len(right))):
        lv = int(max(-1.0, min(1.0, left[i])) * 32767)
        rv = int(max(-1.0, min(1.0, right[i])) * 32767)
        h.update(struct.pack('<hh', lv, rv))
    return h.hexdigest()


def compare_pair(la, ra, lb, rb, label_a, label_b):
    """Compare two audio buffers and print results."""
    n = min(len(la), len(lb), len(ra), len(rb))
    max_d = 0.0
    rms_sum = 0.0
    n_diff = 0
    n_pcm_diff = 0
    for i in range(n):
        dl = abs(la[i] - lb[i])
        dr = abs(ra[i] - rb[i])
        d = max(dl, dr)
        max_d = max(max_d, d)
        rms_sum += dl*dl + dr*dr
        if d > 0:
            n_diff += 1
        pa = int(max(-1.0, min(1.0, la[i])) * 32767)
        pb = int(max(-1.0, min(1.0, lb[i])) * 32767)
        qa = int(max(-1.0, min(1.0, ra[i])) * 32767)
        qb = int(max(-1.0, min(1.0, rb[i])) * 32767)
        if pa != pb or qa != qb:
            n_pcm_diff += 1

    rms = math.sqrt(rms_sum / max(n * 2, 1))
    md5a = pcm_md5(la[:n], ra[:n])
    md5b = pcm_md5(lb[:n], rb[:n])
    identical = (md5a == md5b)
    pct = 100 * n_diff / max(n, 1)

    verdict = "IDENTICAL" if identical else "DIFFERENT"
    print(f"\n  {label_a} vs {label_b}:")
    print(f"    {verdict}  |  Samples: {n:,}  |  Max diff: {max_d:.8f}  "
          f"|  RMS: {rms:.8f}")
    print(f"    Float differ: {n_diff:,} ({pct:.1f}%)  "
          f"|  PCM16 differ: {n_pcm_diff:,} ({100*n_pcm_diff/max(n,1):.1f}%)")
    print(f"    MD5 A: {md5a}")
    print(f"    MD5 B: {md5b}")
    return identical, max_d, rms


def main():
    """Run full 1800s-plan comparison with first 160s of audio."""
    print("=" * 70)
    print("V17 Full Comparison: 1800s plan, first 160s of audio")
    print(f"Comparing {COMPARE_SECONDS}s ({COMPARE_SAMPLES:,} samples)")
    print(f"numpy available: {mod.HAS_NUMPY}, version: ", end='')
    try:
        import numpy
        print(numpy.__version__)
    except ImportError:
        print("N/A")
    print("=" * 70)

    renders = {}

    # 1. Decode repo V8 MP3
    v8_mp3 = os.path.join(PROJECT_ROOT, 'apps', 'audio', 'cosmic_radio_v8.mp3')
    print(f"\n[1/5] Decoding repo V8 MP3 (first {COMPARE_SECONDS}s)...")
    renders['repo_v8'] = decode_mp3_first_n(v8_mp3, COMPARE_SAMPLES)
    print(f"  -> {len(renders['repo_v8'][0]):,} samples")

    # 2. V8 streaming, numpy ON
    print(f"\n[2/5] Rendering V8 streaming (numpy ON, 1800s plan)...")
    t0 = _time.time()
    renders['v8_numpy'] = render_streaming_capture(
        RadioEngineV8, 42, force_numpy=True)
    print(f"  -> {len(renders['v8_numpy'][0]):,} samples in {_time.time()-t0:.1f}s")

    # 3. V8 streaming, numpy OFF
    print(f"\n[3/5] Rendering V8 streaming (numpy OFF, 1800s plan)...")
    t0 = _time.time()
    renders['v8_pure'] = render_streaming_capture(
        RadioEngineV8, 42, force_numpy=False)
    print(f"  -> {len(renders['v8_pure'][0]):,} samples in {_time.time()-t0:.1f}s")

    # 4. V15 bugfixed, V8 tempo, numpy ON
    print(f"\n[4/5] Rendering V15-bugfixed streaming (V8 tempo, numpy ON)...")
    t0 = _time.time()
    renders['v15_numpy'] = render_streaming_capture(
        RadioEngineV15, 42, force_numpy=True, tempo_override='v8')
    print(f"  -> {len(renders['v15_numpy'][0]):,} samples in {_time.time()-t0:.1f}s")

    # 5. V15 bugfixed, V8 tempo, numpy OFF
    print(f"\n[5/5] Rendering V15-bugfixed streaming (V8 tempo, numpy OFF)...")
    t0 = _time.time()
    renders['v15_pure'] = render_streaming_capture(
        RadioEngineV15, 42, force_numpy=False, tempo_override='v8')
    print(f"  -> {len(renders['v15_pure'][0]):,} samples in {_time.time()-t0:.1f}s")

    # Cross-compare all 5
    print("\n" + "=" * 70)
    print("COMPARISONS vs REPO V8 MP3")
    print("=" * 70)

    results = {}
    for key, label in [('v8_numpy', 'V8+numpy'),
                        ('v8_pure', 'V8+pure'),
                        ('v15_numpy', 'V15-fix+V8tempo+numpy'),
                        ('v15_pure', 'V15-fix+V8tempo+pure')]:
        la, ra = renders['repo_v8']
        lb, rb = renders[key]
        ident, maxd, rms = compare_pair(la, ra, lb, rb, 'Repo V8 MP3', label)
        results[key] = (ident, maxd, rms)

    print("\n" + "=" * 70)
    print("CROSS-COMPARISONS (new renders only)")
    print("=" * 70)

    compare_pair(*renders['v8_numpy'], *renders['v8_pure'],
                 'V8+numpy', 'V8+pure')
    compare_pair(*renders['v8_pure'], *renders['v15_pure'],
                 'V8+pure', 'V15-fix+V8tempo+pure')
    compare_pair(*renders['v8_numpy'], *renders['v15_numpy'],
                 'V8+numpy', 'V15-fix+V8tempo+numpy')

    # Determine which new render is closest to the repo MP3
    print("\n" + "=" * 70)
    print("VERDICT: Which synthesis path produced the repo V8 MP3?")
    print("=" * 70)

    closest = min(results.items(), key=lambda x: x[1][2])  # lowest RMS
    print(f"\n  Closest match (lowest RMS): {closest[0]} "
          f"(RMS diff: {closest[1][2]:.8f})")

    numpy_rms = results['v8_numpy'][2]
    pure_rms = results['v8_pure'][2]
    if numpy_rms < pure_rms:
        print(f"\n  CONCLUSION: The repo V8 MP3 was LIKELY rendered WITH numpy.")
        print(f"    numpy RMS: {numpy_rms:.8f} vs pure RMS: {pure_rms:.8f}")
    elif pure_rms < numpy_rms:
        print(f"\n  CONCLUSION: The repo V8 MP3 was LIKELY rendered WITHOUT numpy.")
        print(f"    pure RMS: {pure_rms:.8f} vs numpy RMS: {numpy_rms:.8f}")
    else:
        print(f"\n  INCONCLUSIVE: Both paths equally close to repo MP3.")

    # Note about MP3 lossy encoding
    print(f"\n  NOTE: All comparisons include MP3 lossy encoding artifacts")
    print(f"  from the repo V8 MP3. A perfect match is impossible due to")
    print(f"  WAV->MP3->WAV round-trip loss. Lower RMS = closer match.")

    print(f"\n  V8+pure vs V15-fix+V8tempo+pure should be IDENTICAL")
    print(f"  (confirming the bug fix works at 1800s plan scale)")


if __name__ == '__main__':
    main()
