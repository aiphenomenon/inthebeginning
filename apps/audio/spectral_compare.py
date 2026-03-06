#!/usr/bin/env python3
"""Spectral analysis comparison between v8 and v12 cosmic_radio MP3 files.

Decodes MP3 -> PCM via ffmpeg, then computes spectral metrics using only stdlib.
"""

import subprocess
import struct
import math
import sys
import os

# ── Config ──────────────────────────────────────────────────────────────────
V8_PATH = os.path.join(os.path.dirname(__file__), "cosmic_radio_v8.mp3")
V12_PATH = os.path.join(os.path.dirname(__file__), "cosmic_radio_v12.mp3")
SAMPLE_RATE = 44100
NUM_CHANNELS = 2  # will be mixed to mono
BITCRUSHER_FREQ_THRESHOLD = 8000  # Hz


def decode_mp3_to_pcm(path):
    """Decode MP3 to raw 16-bit signed LE mono PCM using ffmpeg."""
    cmd = [
        "ffmpeg", "-i", path,
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-v", "error", "-"
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        print(f"ffmpeg error for {path}: {proc.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    raw = proc.stdout
    n_samples = len(raw) // 2
    samples = struct.unpack(f"<{n_samples}h", raw)
    # Normalize to [-1.0, 1.0]
    return [s / 32768.0 for s in samples]


def rms(samples):
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def peak(samples):
    if not samples:
        return 0.0
    return max(abs(s) for s in samples)


def zero_crossing_rate(samples):
    if len(samples) < 2:
        return 0.0
    crossings = sum(
        1 for i in range(1, len(samples))
        if (samples[i] >= 0) != (samples[i - 1] >= 0)
    )
    return crossings / len(samples)


def crest_factor(samples):
    r = rms(samples)
    if r == 0:
        return 0.0
    return peak(samples) / r


def dft_magnitude(samples, n_fft):
    """Compute magnitude spectrum using DFT (real input).

    Only computes the first n_fft//2+1 bins (positive frequencies).
    Uses a Hann window.
    """
    N = min(len(samples), n_fft)
    # Apply Hann window
    windowed = [
        samples[i] * (0.5 - 0.5 * math.cos(2 * math.pi * i / (N - 1)))
        for i in range(N)
    ]
    # Pad to n_fft if needed
    if len(windowed) < n_fft:
        windowed.extend([0.0] * (n_fft - len(windowed)))

    n_bins = n_fft // 2 + 1
    magnitudes = []
    for k in range(n_bins):
        real = 0.0
        imag = 0.0
        for n in range(n_fft):
            angle = 2 * math.pi * k * n / n_fft
            real += windowed[n] * math.cos(angle)
            imag -= windowed[n] * math.sin(angle)
        magnitudes.append(math.sqrt(real * real + imag * imag))
    return magnitudes


def spectral_centroid_from_magnitudes(magnitudes, sample_rate, n_fft):
    """Compute spectral centroid in Hz from magnitude spectrum."""
    freq_per_bin = sample_rate / n_fft
    total_energy = sum(magnitudes)
    if total_energy == 0:
        return 0.0
    weighted = sum(magnitudes[k] * (k * freq_per_bin) for k in range(len(magnitudes)))
    return weighted / total_energy


def high_freq_energy_ratio(magnitudes, sample_rate, n_fft, threshold_hz):
    """Ratio of energy above threshold_hz to total energy."""
    freq_per_bin = sample_rate / n_fft
    threshold_bin = int(threshold_hz / freq_per_bin)
    total = sum(m * m for m in magnitudes)
    if total == 0:
        return 0.0
    high = sum(m * m for m in magnitudes[threshold_bin:])
    return high / total


def analyze_chunk_spectral(samples, n_fft=2048):
    """Compute spectral metrics for a chunk of audio."""
    mags = dft_magnitude(samples, n_fft)
    sc = spectral_centroid_from_magnitudes(mags, SAMPLE_RATE, n_fft)
    hf_ratio = high_freq_energy_ratio(mags, SAMPLE_RATE, n_fft, BITCRUSHER_FREQ_THRESHOLD)
    return sc, hf_ratio


def analyze_full(samples, label, window_sec=5.0):
    """Compute all metrics for a full audio track."""
    window_samples = int(window_sec * SAMPLE_RATE)
    n_windows = len(samples) // window_samples
    duration = len(samples) / SAMPLE_RATE

    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"  Duration: {duration:.1f}s  |  Samples: {len(samples):,}")
    print(f"{'=' * 70}")

    # Global metrics
    global_rms = rms(samples)
    global_peak = peak(samples)
    global_zcr = zero_crossing_rate(samples)
    global_crest = crest_factor(samples)

    # For spectral analysis, use a smaller DFT on sampled windows to keep runtime sane
    # We'll analyze the first 2048 samples of each window
    n_fft = 2048

    window_metrics = []
    for i in range(n_windows):
        start = i * window_samples
        end = start + window_samples
        chunk = samples[start:end]
        w_rms = rms(chunk)
        w_peak = peak(chunk)
        w_zcr = zero_crossing_rate(chunk)
        w_crest = crest_factor(chunk)
        # Spectral on first n_fft samples of chunk
        sc, hf = analyze_chunk_spectral(chunk[:n_fft], n_fft)
        window_metrics.append({
            "window": i,
            "time_start": i * window_sec,
            "time_end": (i + 1) * window_sec,
            "rms": w_rms,
            "peak": w_peak,
            "zcr": w_zcr,
            "crest": w_crest,
            "spectral_centroid": sc,
            "hf_energy_ratio": hf,
        })

    # Global spectral (use middle of track, 2048 samples)
    mid = len(samples) // 2
    global_sc, global_hf = analyze_chunk_spectral(samples[mid:mid + n_fft], n_fft)

    result = {
        "label": label,
        "duration": duration,
        "global_rms": global_rms,
        "global_peak": global_peak,
        "global_zcr": global_zcr,
        "global_crest": global_crest,
        "global_spectral_centroid": global_sc,
        "global_hf_energy_ratio": global_hf,
        "windows": window_metrics,
    }
    return result


def print_comparison(r8, r12):
    """Print a side-by-side comparison table."""
    print("\n")
    print("=" * 78)
    print("  SPECTRAL COMPARISON: v8 vs v12 (seed-42)")
    print("=" * 78)

    def row(label, v8_val, v12_val, fmt=".6f", unit="", higher_is_harsher=True):
        v8s = f"{v8_val:{fmt}}{unit}"
        v12s = f"{v12_val:{fmt}}{unit}"
        if v12_val == 0 and v8_val == 0:
            delta = "same"
        elif v8_val == 0:
            delta = "+inf%"
        else:
            pct = (v12_val - v8_val) / abs(v8_val) * 100
            sign = "+" if pct >= 0 else ""
            delta = f"{sign}{pct:.1f}%"
            if higher_is_harsher and pct > 5:
                delta += " <<"
            elif not higher_is_harsher and pct < -5:
                delta += " <<"
        print(f"  {label:<30s}  {v8s:>14s}  {v12s:>14s}  {delta:>10s}")

    print(f"\n  {'Metric':<30s}  {'v8':>14s}  {'v12':>14s}  {'Delta':>10s}")
    print(f"  {'-' * 30}  {'-' * 14}  {'-' * 14}  {'-' * 10}")

    row("RMS Level", r8["global_rms"], r12["global_rms"], ".6f", "", True)
    row("Peak Level", r8["global_peak"], r12["global_peak"], ".6f", "", True)
    row("Crest Factor (peak/RMS)", r8["global_crest"], r12["global_crest"], ".3f", "", True)
    row("Zero-Crossing Rate", r8["global_zcr"], r12["global_zcr"], ".6f", "", True)
    row("Spectral Centroid (Hz)", r8["global_spectral_centroid"], r12["global_spectral_centroid"], ".1f", " Hz", True)
    row("HF Energy Ratio (>8kHz)", r8["global_hf_energy_ratio"], r12["global_hf_energy_ratio"], ".6f", "", True)

    # Window-by-window comparison
    n_windows = min(len(r8["windows"]), len(r12["windows"]), 10)
    # Pick windows spread across the track
    if n_windows >= 10:
        indices = [0, 1, 2, n_windows // 4, n_windows // 3, n_windows // 2,
                   2 * n_windows // 3, 3 * n_windows // 4, n_windows - 2, n_windows - 1]
    else:
        indices = list(range(n_windows))
    # Deduplicate and sort
    indices = sorted(set(i for i in indices if i < len(r8["windows"]) and i < len(r12["windows"])))

    print(f"\n\n  TIME-WINDOW ANALYSIS (5-second windows)")
    print(f"  {'Window':<12s}  {'Metric':<22s}  {'v8':>12s}  {'v12':>12s}  {'Delta':>10s}")
    print(f"  {'-' * 12}  {'-' * 22}  {'-' * 12}  {'-' * 12}  {'-' * 10}")

    for idx in indices:
        w8 = r8["windows"][idx]
        w12 = r12["windows"][idx]
        time_label = f"{w8['time_start']:.0f}-{w8['time_end']:.0f}s"

        for metric, mkey, fmt, harsher in [
            ("RMS", "rms", ".6f", True),
            ("Peak", "peak", ".6f", True),
            ("Crest Factor", "crest", ".3f", True),
            ("Zero-Cross Rate", "zcr", ".6f", True),
            ("Spec. Centroid", "spectral_centroid", ".1f", True),
            ("HF Energy Ratio", "hf_energy_ratio", ".6f", True),
        ]:
            v8v = w8[mkey]
            v12v = w12[mkey]
            if v8v == 0 and v12v == 0:
                delta = "same"
            elif v8v == 0:
                delta = "+inf%"
            else:
                pct = (v12v - v8v) / abs(v8v) * 100
                sign = "+" if pct >= 0 else ""
                delta = f"{sign}{pct:.1f}%"
                if harsher and pct > 10:
                    delta += " !!"
            print(f"  {time_label:<12s}  {metric:<22s}  {v8v:>12{fmt}}  {v12v:>12{fmt}}  {delta:>10s}")
        print(f"  {'-' * 12}  {'-' * 22}  {'-' * 12}  {'-' * 12}  {'-' * 10}")

    # Summary
    print(f"\n\n  SUMMARY OF HARSHNESS INDICATORS")
    print(f"  {'=' * 60}")

    # Compute average differences across all windows
    all_w8 = r8["windows"]
    all_w12 = r12["windows"]
    n = min(len(all_w8), len(all_w12))

    metrics_to_avg = [
        ("Avg RMS difference", "rms"),
        ("Avg Zero-Crossing Rate diff", "zcr"),
        ("Avg Spectral Centroid diff", "spectral_centroid"),
        ("Avg HF Energy Ratio diff", "hf_energy_ratio"),
        ("Avg Crest Factor diff", "crest"),
    ]

    for label, key in metrics_to_avg:
        diffs = []
        for i in range(n):
            v8v = all_w8[i][key]
            v12v = all_w12[i][key]
            if v8v != 0:
                diffs.append((v12v - v8v) / abs(v8v) * 100)
        if diffs:
            avg_diff = sum(diffs) / len(diffs)
            max_diff = max(diffs)
            sign = "+" if avg_diff >= 0 else ""
            msign = "+" if max_diff >= 0 else ""
            print(f"  {label:<35s}  avg: {sign}{avg_diff:.1f}%   max: {msign}{max_diff:.1f}%")

    # Find the spikiest windows in v12 (highest crest factor difference)
    crest_diffs = []
    for i in range(n):
        if all_w8[i]["crest"] != 0:
            d = (all_w12[i]["crest"] - all_w8[i]["crest"]) / all_w8[i]["crest"] * 100
            crest_diffs.append((i, d, all_w8[i]["time_start"], all_w8[i]["time_end"]))

    crest_diffs.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  TOP 5 SPIKIEST WINDOWS (v12 vs v8 crest factor increase):")
    for rank, (idx, diff, t_start, t_end) in enumerate(crest_diffs[:5], 1):
        print(f"    {rank}. Window {idx} ({t_start:.0f}-{t_end:.0f}s): +{diff:.1f}% crest factor")

    # Find highest HF energy windows
    hf_diffs = []
    for i in range(n):
        if all_w8[i]["hf_energy_ratio"] != 0:
            d = (all_w12[i]["hf_energy_ratio"] - all_w8[i]["hf_energy_ratio"]) / all_w8[i]["hf_energy_ratio"] * 100
            hf_diffs.append((i, d, all_w8[i]["time_start"], all_w8[i]["time_end"]))

    hf_diffs.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  TOP 5 HARSHEST WINDOWS (v12 vs v8 high-freq energy increase):")
    for rank, (idx, diff, t_start, t_end) in enumerate(hf_diffs[:5], 1):
        sign = "+" if diff >= 0 else ""
        print(f"    {rank}. Window {idx} ({t_start:.0f}-{t_end:.0f}s): {sign}{diff:.1f}% HF energy")

    print()


def main():
    print("Decoding v8 MP3...")
    v8_samples = decode_mp3_to_pcm(V8_PATH)
    print(f"  -> {len(v8_samples):,} samples ({len(v8_samples) / SAMPLE_RATE:.1f}s)")

    print("Decoding v12 MP3...")
    v12_samples = decode_mp3_to_pcm(V12_PATH)
    print(f"  -> {len(v12_samples):,} samples ({len(v12_samples) / SAMPLE_RATE:.1f}s)")

    print("\nAnalyzing v8...")
    r8 = analyze_full(v8_samples, "v8 (cosmic_radio_v8.mp3 - the good one)")

    print("\nAnalyzing v12...")
    r12 = analyze_full(v12_samples, "v12 (cosmic_radio_v12.mp3 - too much bitcrusher)")

    print_comparison(r8, r12)


if __name__ == "__main__":
    main()
