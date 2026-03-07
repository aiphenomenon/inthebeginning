#!/usr/bin/env python3
"""Generate five 30-minute MP3s for V18 comparison suite:

1. V8-style seed=42: V15 synthesis + V8 tempo (1.5x-2.5x) — faithful V8 reproduction
2. V8-style random:  V15 synthesis + V8 tempo, random seed
3. V18 seed=42:      V15 synthesis + clean mixing + 1.1x-1.45x tempo
4. V18 random:       V15 synthesis + clean mixing + 1.1x-1.45x tempo, random seed
5. V18 Orchestra:    Expanded 15-family palette + character preservation, random seed

All use V15's pure-Python V8 synthesis (factory.synthesize_colored_note).
"""
import sys
import os
import hashlib
import time
import wave
import random

sys.path.insert(0, os.path.dirname(__file__))

from radio_engine import (
    RadioEngineV15, RadioEngineV18, RadioEngineV18Orchestra,
    wav_to_mp3, SAMPLE_RATE,
)


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
    random_seed = random.randint(100000, 999999)
    print(f"Random seed for this run: {random_seed}")

    # Determine which MP3s to generate based on CLI args
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['all']

    renders = []

    if 'all' in targets or '1' in targets or 'v8-42' in targets:
        renders.append(('v8-42', 42, RadioEngineV15_V8Tempo,
                       "V8-style seed=42 (V15 synth + V8 tempo 1.5x-2.5x)"))

    if 'all' in targets or '2' in targets or 'v8-random' in targets:
        renders.append(('v8-random', random_seed, RadioEngineV15_V8Tempo,
                       f"V8-style random seed={random_seed} (V15 synth + V8 tempo)"))

    if 'all' in targets or '3' in targets or 'v18-42' in targets:
        renders.append(('v18-42', 42, RadioEngineV18,
                       "V18 seed=42 (clean mixing + 1.1x-1.45x tempo)"))

    if 'all' in targets or '4' in targets or 'v18-random' in targets:
        renders.append(('v18-random', random_seed, RadioEngineV18,
                       f"V18 random seed={random_seed} (clean mixing + 1.1x-1.45x tempo)"))

    if 'all' in targets or '5' in targets or 'v18o' in targets:
        renders.append(('v18o', random_seed, RadioEngineV18Orchestra,
                       f"V18 Orchestra seed={random_seed} (expanded palette + character)"))

    for tag, seed, engine_cls, desc in renders:
        print(f"\n=== Generating MP3: {desc} ===")
        engine = engine_cls(seed=seed, total_duration=1800.0)
        wav_path = os.path.join(base, f"cosmic_radio_v18_{tag}.wav")
        mp3_path = os.path.join(base, f"cosmic_radio_v18_{tag}.mp3")
        render_mp3(engine, wav_path, mp3_path)

    print(f"\nDone! Generated {len(renders)} MP3(s).")


if __name__ == "__main__":
    main()
