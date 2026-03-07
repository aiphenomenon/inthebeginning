#!/usr/bin/env python3
"""V17 Comparison Script: V8 vs V15 Bit-Identity Investigation.

Empirically determines which synthesis path (numpy vs pure Python) produced the
original V8 MP3 in the repo, then tests whether V15 with V8's tempo formula
produces identical audio.

The test renders multiple variants and compares their PCM audio data (ignoring
MP3 metadata) against the existing MP3 files in the repo.

Variants rendered:
  1. V8 with numpy enabled (if available)
  2. V8 with numpy disabled (forced pure Python)
  3. V15 with its own tempo (density-aware 1.1-1.7x)
  4. V15 with V8's tempo formula (hash-based 1.5-2.5x)
  5. V15 with V8's tempo + anti-hiss/subsonic removed from _render_segment
     (to test if the double-filter application is the remaining difference)

For each variant, a WAV file is produced and its audio content compared at the
PCM sample level against all other variants and against the existing repo MP3s.

Usage:
    python apps/audio/compare_v8_v15.py [--duration SECONDS] [--seed SEED]

For matching against existing 30-min MP3s, use --duration 1800 (very slow).
For quick structural comparison, use --duration 30 (default).
"""

import argparse
import hashlib
import math
import os
import struct
import sys
import tempfile
import time as _time
import wave

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from apps.audio.radio_engine import (
    RadioEngineV8, RadioEngineV15, SAMPLE_RATE
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_numpy():
    """Return (has_numpy, numpy_module_or_None)."""
    try:
        import numpy
        return True, numpy
    except ImportError:
        return False, None


def _force_numpy(enable):
    """Context-manager-style: override HAS_NUMPY in radio_engine module."""
    import apps.audio.radio_engine as mod
    original = mod.HAS_NUMPY
    mod.HAS_NUMPY = enable
    return original


def _restore_numpy(original):
    """Restore HAS_NUMPY to its original value."""
    import apps.audio.radio_engine as mod
    mod.HAS_NUMPY = original


def render_clip(engine_class, seed, duration, force_numpy_flag=None,
                tempo_override=None, remove_segment_filters=False):
    """Render a clip and return (left, right) as lists of floats.

    Args:
        engine_class: RadioEngineV8 or RadioEngineV15
        seed: Random seed
        duration: Duration in seconds
        force_numpy_flag: If True/False, override HAS_NUMPY. None = use default.
        tempo_override: If 'v8', monkey-patch to use V8's tempo formula.
        remove_segment_filters: If True, remove anti-hiss/subsonic from
            _render_segment (to test the double-filter hypothesis).

    Returns:
        (left, right) sample lists
    """
    saved_numpy = None
    if force_numpy_flag is not None:
        saved_numpy = _force_numpy(force_numpy_flag)

    try:
        engine = engine_class(seed=seed, total_duration=duration)

        if tempo_override == 'v8':
            def patched_tempo(sim_state):
                """V8's tempo: 1.5 + 1.0 * hash (range 1.5-2.5x)."""
                if not sim_state:
                    return 2.0
                state_str = repr(sorted(sim_state.items()))
                h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
                return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)
            engine._compute_tempo_multiplier = patched_tempo

        if remove_segment_filters:
            original_render_seg = engine._render_segment

            def patched_render_segment(mood, kits, n_samples, sim_state):
                """Call original then undo the per-segment anti-hiss/subsonic."""
                # V15's _render_segment applies anti_hiss + subsonic at the end.
                # We want to remove that to test if the double-filter is the diff.
                # Strategy: call original, then reverse-apply the filters.
                # Actually, simpler: just call V8's _render_segment via super.
                left, right = original_render_seg(mood, kits, n_samples, sim_state)
                return left, right

            # Instead of the above, let's directly use V8's _render_segment
            # by binding it to this V15 instance
            engine._render_segment = lambda mood, kits, n_samples, sim_state: \
                RadioEngineV8._render_segment(engine, mood, kits, n_samples, sim_state)

        # Use render() for short clips, streaming for long ones
        if duration > 660:
            # Use streaming path (matches how the 30-min MP3s were generated)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            try:
                with wave.open(wav_path, 'wb') as wf:
                    wf.setnchannels(2)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    engine.render_streaming(wf)
                # Read back the WAV to get sample data
                left, right = _read_wav_samples(wav_path)
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        else:
            left, right = engine.render()

        return left, right

    finally:
        if saved_numpy is not None:
            _restore_numpy(saved_numpy)


def _read_wav_samples(wav_path):
    """Read a WAV file and return (left, right) as lists of floats in [-1, 1]."""
    with wave.open(wav_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)

    left = []
    right = []
    for i in range(n_frames):
        offset = i * n_channels * 2
        l_val = struct.unpack_from('<h', data, offset)[0] / 32767.0
        r_val = struct.unpack_from('<h', data, offset + 2)[0] / 32767.0
        left.append(l_val)
        right.append(r_val)

    return left, right


def _read_mp3_pcm(mp3_path):
    """Read an MP3 file and return (left, right) as lists of floats.

    Uses ffmpeg/avconv to decode MP3 to WAV, then reads the WAV.
    Returns None if ffmpeg is not available.
    """
    import subprocess
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        wav_path = tmp.name
    try:
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', mp3_path, '-ar', str(SAMPLE_RATE),
             '-ac', '2', '-sample_fmt', 's16', wav_path],
            capture_output=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  ffmpeg failed: {result.stderr.decode()[:200]}")
            return None
        return _read_wav_samples(wav_path)
    except FileNotFoundError:
        print("  ffmpeg not available — cannot decode MP3 for comparison")
        return None
    except Exception as e:
        print(f"  Error decoding MP3: {e}")
        return None
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def compute_stats(left_a, right_a, left_b, right_b):
    """Compute comparison statistics between two stereo audio buffers."""
    min_len = min(len(left_a), len(left_b), len(right_a), len(right_b))
    if min_len == 0:
        return {'error': 'Empty buffers'}

    la, ra = left_a[:min_len], right_a[:min_len]
    lb, rb = left_b[:min_len], right_b[:min_len]

    # Float-level comparison
    max_diff_l = max_diff_r = 0.0
    sum_sq_l = sum_sq_r = 0.0
    n_diff_l = n_diff_r = 0
    n_pcm_diff = 0

    for i in range(min_len):
        dl = abs(la[i] - lb[i])
        dr = abs(ra[i] - rb[i])
        if dl > 0:
            n_diff_l += 1
        if dr > 0:
            n_diff_r += 1
        max_diff_l = max(max_diff_l, dl)
        max_diff_r = max(max_diff_r, dr)
        sum_sq_l += dl * dl
        sum_sq_r += dr * dr
        # PCM16 comparison
        pcm_al = int(max(-1.0, min(1.0, la[i])) * 32767)
        pcm_ar = int(max(-1.0, min(1.0, ra[i])) * 32767)
        pcm_bl = int(max(-1.0, min(1.0, lb[i])) * 32767)
        pcm_br = int(max(-1.0, min(1.0, rb[i])) * 32767)
        if pcm_al != pcm_bl:
            n_pcm_diff += 1
        if pcm_ar != pcm_br:
            n_pcm_diff += 1

    rms_l = math.sqrt(sum_sq_l / min_len) if min_len > 0 else 0.0
    rms_r = math.sqrt(sum_sq_r / min_len) if min_len > 0 else 0.0

    # MD5 of PCM data
    def pcm_md5(left_ch, right_ch):
        """MD5 of interleaved PCM16 data."""
        h = hashlib.md5()
        for i in range(min(len(left_ch), len(right_ch))):
            lv = int(max(-1.0, min(1.0, left_ch[i])) * 32767)
            rv = int(max(-1.0, min(1.0, right_ch[i])) * 32767)
            h.update(struct.pack('<hh', lv, rv))
        return h.hexdigest()

    md5_a = pcm_md5(la, ra)
    md5_b = pcm_md5(lb, rb)

    return {
        'samples': min_len,
        'bit_identical': (md5_a == md5_b),
        'md5_a': md5_a,
        'md5_b': md5_b,
        'left_max_diff': max_diff_l,
        'right_max_diff': max_diff_r,
        'left_rms_diff': rms_l,
        'right_rms_diff': rms_r,
        'left_samples_differ': n_diff_l,
        'right_samples_differ': n_diff_r,
        'pcm16_samples_differ': n_pcm_diff,
        'pcm16_total_samples': min_len * 2,
        'length_a': len(left_a),
        'length_b': len(left_b),
    }


def format_report(stats, label_a, label_b):
    """Format comparison stats as a readable report section."""
    lines = []
    lines.append(f"### {label_a} vs {label_b}")
    lines.append("")

    if 'error' in stats:
        lines.append(f"**Error**: {stats['error']}")
        return '\n'.join(lines)

    verdict = "YES" if stats['bit_identical'] else "NO"
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Samples compared | {stats['samples']:,} |")
    lines.append(f"| Length A / B | {stats['length_a']:,} / {stats['length_b']:,} |")
    lines.append(f"| **Bit-identical (PCM16)** | **{verdict}** |")
    lines.append(f"| MD5 A | `{stats['md5_a']}` |")
    lines.append(f"| MD5 B | `{stats['md5_b']}` |")
    lines.append(f"| Left max sample diff | {stats['left_max_diff']:.10f} |")
    lines.append(f"| Right max sample diff | {stats['right_max_diff']:.10f} |")
    lines.append(f"| Left RMS diff | {stats['left_rms_diff']:.10f} |")
    lines.append(f"| Right RMS diff | {stats['right_rms_diff']:.10f} |")
    pct_l = 100 * stats['left_samples_differ'] / max(stats['samples'], 1)
    pct_r = 100 * stats['right_samples_differ'] / max(stats['samples'], 1)
    pct_pcm = 100 * stats['pcm16_samples_differ'] / max(stats['pcm16_total_samples'], 1)
    lines.append(f"| Left float differ | {stats['left_samples_differ']:,} ({pct_l:.1f}%) |")
    lines.append(f"| Right float differ | {stats['right_samples_differ']:,} ({pct_r:.1f}%) |")
    lines.append(f"| PCM16 differ | {stats['pcm16_samples_differ']:,} ({pct_pcm:.1f}%) |")
    lines.append("")
    return '\n'.join(lines)


def main():
    """Run the V8 vs V15 comparison suite."""
    parser = argparse.ArgumentParser(
        description='V17: Compare V8 and V15 radio engine output')
    parser.add_argument('--duration', type=float, default=30.0,
                        help='Clip duration in seconds (default: 30)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')
    parser.add_argument('--output', type=str,
                        default=os.path.join(PROJECT_ROOT,
                                             'docs', 'v8_v15_results.md'),
                        help='Output markdown file path')
    parser.add_argument('--compare-mp3', action='store_true',
                        help='Also compare against existing MP3 files in repo')
    args = parser.parse_args()

    duration = args.duration
    seed = args.seed
    has_numpy, np_mod = _check_numpy()

    print("=" * 70)
    print("V17 Comparison: V8 vs V15 Bit-Identity Investigation")
    print("=" * 70)
    print(f"Duration: {duration}s | Seed: {seed} | numpy: {has_numpy}")
    if has_numpy:
        print(f"numpy version: {np_mod.__version__}")
    print()

    renders = {}
    reports = []

    # --- Render all variants ---

    if has_numpy:
        print(f"[1/5] V8 with numpy ON (seed={seed}, {duration}s)...")
        t0 = _time.time()
        renders['v8_numpy'] = render_clip(RadioEngineV8, seed, duration,
                                          force_numpy_flag=True)
        print(f"  -> {len(renders['v8_numpy'][0]):,} samples "
              f"({_time.time()-t0:.1f}s)")

    print(f"[2/5] V8 with numpy OFF (seed={seed}, {duration}s)...")
    t0 = _time.time()
    renders['v8_pure'] = render_clip(RadioEngineV8, seed, duration,
                                     force_numpy_flag=False)
    print(f"  -> {len(renders['v8_pure'][0]):,} samples ({_time.time()-t0:.1f}s)")

    print(f"[3/5] V15 with own tempo (seed={seed}, {duration}s)...")
    t0 = _time.time()
    renders['v15_own'] = render_clip(RadioEngineV15, seed, duration,
                                     force_numpy_flag=False)
    print(f"  -> {len(renders['v15_own'][0]):,} samples ({_time.time()-t0:.1f}s)")

    print(f"[4/5] V15 with V8 tempo (seed={seed}, {duration}s)...")
    t0 = _time.time()
    renders['v15_v8tempo'] = render_clip(RadioEngineV15, seed, duration,
                                          force_numpy_flag=False,
                                          tempo_override='v8')
    print(f"  -> {len(renders['v15_v8tempo'][0]):,} samples "
          f"({_time.time()-t0:.1f}s)")

    print(f"[5/5] V15 with V8 tempo + V8's _render_segment "
          f"(seed={seed}, {duration}s)...")
    t0 = _time.time()
    renders['v15_v8full'] = render_clip(RadioEngineV15, seed, duration,
                                         force_numpy_flag=False,
                                         tempo_override='v8',
                                         remove_segment_filters=True)
    print(f"  -> {len(renders['v15_v8full'][0]):,} samples "
          f"({_time.time()-t0:.1f}s)")

    if has_numpy:
        print(f"[bonus] V15 with V8 tempo + numpy ON (seed={seed}, {duration}s)...")
        t0 = _time.time()
        renders['v15_v8tempo_numpy'] = render_clip(
            RadioEngineV15, seed, duration,
            force_numpy_flag=True, tempo_override='v8')
        print(f"  -> {len(renders['v15_v8tempo_numpy'][0]):,} samples "
              f"({_time.time()-t0:.1f}s)")

    # --- Compare existing MP3s ---
    mp3_data = {}
    if args.compare_mp3:
        v8_mp3 = os.path.join(PROJECT_ROOT, 'apps', 'audio',
                               'cosmic_radio_v8.mp3')
        v15_mp3 = os.path.join(PROJECT_ROOT, 'apps', 'audio',
                                'cosmic_radio_v15.mp3')
        for label, path in [('repo_v8_mp3', v8_mp3),
                            ('repo_v15_mp3', v15_mp3)]:
            if os.path.exists(path):
                print(f"[mp3] Decoding {os.path.basename(path)}...")
                result = _read_mp3_pcm(path)
                if result is not None:
                    mp3_data[label] = result
                    print(f"  -> {len(result[0]):,} samples")

    # --- Compute all comparisons ---
    print()
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print()

    comparison_pairs = []

    # Core comparisons
    if has_numpy:
        comparison_pairs.append(('v8_numpy', 'v8_pure',
                                 'V8+numpy', 'V8 pure Python'))
    comparison_pairs.append(('v8_pure', 'v15_own',
                             'V8 pure', 'V15 (own tempo)'))
    comparison_pairs.append(('v8_pure', 'v15_v8tempo',
                             'V8 pure', 'V15+V8tempo'))
    comparison_pairs.append(('v8_pure', 'v15_v8full',
                             'V8 pure', 'V15+V8tempo+V8render'))
    if has_numpy:
        comparison_pairs.append(('v8_numpy', 'v15_v8tempo_numpy',
                                 'V8+numpy', 'V15+V8tempo+numpy'))

    # MP3 comparisons (only if we have decoded MP3s and matching-length renders)
    for mp3_label, mp3_samples in mp3_data.items():
        for render_label in renders:
            if abs(len(renders[render_label][0]) - len(mp3_samples[0])) < SAMPLE_RATE:
                comparison_pairs.append(
                    (render_label, mp3_label,
                     render_label.replace('_', ' '),
                     mp3_label.replace('_', ' ')))

    all_data = {**renders, **mp3_data}

    for key_a, key_b, label_a, label_b in comparison_pairs:
        if key_a not in all_data or key_b not in all_data:
            continue
        la, ra = all_data[key_a]
        lb, rb = all_data[key_b]
        stats = compute_stats(la, ra, lb, rb)
        report = format_report(stats, label_a, label_b)
        reports.append((label_a, label_b, stats, report))
        print(report)

    # --- Summary ---
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    for label_a, label_b, stats, _ in reports:
        if 'error' in stats:
            continue
        verdict = "IDENTICAL" if stats['bit_identical'] else "DIFFERENT"
        max_d = max(stats['left_max_diff'], stats['right_max_diff'])
        print(f"  {label_a} vs {label_b}: {verdict}"
              f"  (max diff: {max_d:.8f})")

    print()

    # Key findings
    key_test = None
    for la, lb, st, _ in reports:
        if 'V8 pure' in la and 'V15+V8tempo+V8render' in lb:
            key_test = st
            break

    if key_test:
        if key_test['bit_identical']:
            print("KEY FINDING: With V8's tempo AND V8's _render_segment,")
            print("V15 produces BIT-IDENTICAL output to V8 (pure Python).")
            print("The claim holds when ALL code paths are matched.")
        else:
            print("KEY FINDING: Even with V8's tempo and V8's _render_segment,")
            print("differences remain. Something else diverges.")

    # Check if numpy vs pure Python matters
    if has_numpy:
        numpy_test = None
        for la, lb, st, _ in reports:
            if 'V8+numpy' in la and 'V8 pure Python' in lb:
                numpy_test = st
                break
        if numpy_test:
            print()
            if numpy_test['bit_identical']:
                print("NUMPY FINDING: numpy and pure Python produce IDENTICAL output.")
            else:
                print(f"NUMPY FINDING: numpy and pure Python produce DIFFERENT output.")
                print(f"  Max diff: {max(numpy_test['left_max_diff'], numpy_test['right_max_diff']):.8f}")

    print()
    print(f"numpy available: {has_numpy}")

    # Write output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write("# V17: V8 vs V15 Comparison Results\n\n")
            f.write(f"**Generated by**: `compare_v8_v15.py`\n")
            f.write(f"**Date**: {_time.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Duration**: {duration}s | **Seed**: {seed} "
                    f"| **numpy**: {has_numpy}\n\n")
            f.write("## Test Variants\n\n")
            f.write("| Variant | Engine | numpy | Tempo | Filters |\n")
            f.write("|---------|--------|-------|-------|----------|\n")
            if has_numpy:
                f.write("| V8+numpy | V8 | ON | V8 (1.5-2.5x) "
                        "| master only |\n")
            f.write("| V8 pure | V8 | OFF | V8 (1.5-2.5x) "
                    "| master only |\n")
            f.write("| V15 own | V15 | OFF | V15 (1.1-1.7x) "
                    "| segment+master |\n")
            f.write("| V15+V8tempo | V15 | OFF | V8 (1.5-2.5x) "
                    "| segment+master |\n")
            f.write("| V15+V8full | V15 | OFF | V8 (1.5-2.5x) "
                    "| master only |\n")
            if has_numpy:
                f.write("| V15+V8tempo+numpy | V15 | ON | V8 (1.5-2.5x) "
                        "| segment+master |\n")
            f.write("\n## Comparisons\n\n")
            for _, _, _, report in reports:
                f.write(report + "\n")
        print(f"Report written to: {args.output}")

    # Exit code: 0 if the key test passes
    if key_test and key_test['bit_identical']:
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())
