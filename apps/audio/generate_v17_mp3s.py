#!/usr/bin/env python3
"""Generate two 30-minute MP3s for V17 comparison:
1. V15 with original V8 tempo clamping (1.5x-2.5x)
2. V15 with V15's own tempo clamping (1.1x-1.7x)

Both use V15's pure-Python V8 synthesis (no numpy).
"""
import sys
import os
import hashlib
import time
import wave

sys.path.insert(0, os.path.dirname(__file__))

from radio_engine import RadioEngineV15, wav_to_mp3, SAMPLE_RATE


class RadioEngineV15_V8Tempo(RadioEngineV15):
    """V15 synthesis with V8's original 1.5x-2.5x tempo range."""

    def _compute_tempo_multiplier(self, sim_state):
        """Original V8 tempo: 1.5x-2.5x range (no density awareness)."""
        if not sim_state:
            return 2.0
        state_str = repr(sorted(sim_state.items()))
        h = hashlib.sha256(state_str.encode()).hexdigest()[:8]
        return 1.5 + 1.0 * (int(h, 16) / 0xFFFFFFFF)


def render_mp3(engine, wav_path, mp3_path):
    """Render streaming WAV then convert to MP3."""
    print(f"  Rendering WAV: {wav_path}")
    t0 = time.time()
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        total_written = engine.render_streaming(wf)
    t1 = time.time()
    print(f"  WAV done in {t1-t0:.1f}s ({total_written/SAMPLE_RATE:.1f}s audio)")

    print(f"  Encoding MP3: {mp3_path}")
    wav_to_mp3(wav_path, mp3_path)
    t2 = time.time()
    print(f"  MP3 done in {t2-t1:.1f}s")

    os.remove(wav_path)
    sz = os.path.getsize(mp3_path)
    print(f"  Size: {sz:,} bytes")
    return sz


def main():
    base = os.path.dirname(__file__)

    # 1. V15 with V8 tempo (1.5x-2.5x)
    print("=== Generating V17 MP3 #1: V15 synthesis + V8 tempo (1.5x-2.5x) ===")
    eng1 = RadioEngineV15_V8Tempo(seed=42, total_duration=1800.0)
    wav1 = os.path.join(base, "cosmic_radio_v17_v8tempo.wav")
    mp3_1 = os.path.join(base, "cosmic_radio_v17_v8tempo.mp3")
    sz1 = render_mp3(eng1, wav1, mp3_1)

    # 2. V15 with its own tempo (1.1x-1.7x)
    print("\n=== Generating V17 MP3 #2: V15 synthesis + V15 tempo (1.1x-1.7x) ===")
    eng2 = RadioEngineV15(seed=42, total_duration=1800.0)
    wav2 = os.path.join(base, "cosmic_radio_v17_v15tempo.wav")
    mp3_2 = os.path.join(base, "cosmic_radio_v17_v15tempo.mp3")
    sz2 = render_mp3(eng2, wav2, mp3_2)

    print(f"\nDone! MP3 sizes: V8tempo={sz1:,}  V15tempo={sz2:,}")


if __name__ == "__main__":
    main()
