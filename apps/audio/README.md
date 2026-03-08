# Audio Composition Engine — In The Beginning Radio

A cosmic simulation music station that generates continuously evolving music
driven by physics simulation state. The engine transforms epoch transitions,
temperature changes, and particle interactions into musical compositions.

## Engine Versions

### v20 (Latest) — Volume-Normalized Orchestra

- Master normalization to -1dB peak with lookahead limiter for spike prevention
- 10-20% solo instrument moods for variety
- Inherits all V18 Orchestra features (expanded instruments, consonance engine)
- All prior version features preserved

### v18 / v18o — Orchestra Engine

- Expanded instrument roster, consonance engine
- V18o variant: orchestral layering with full instrument diversity

### v15/v16 — Refined Layering

- Improved multi-track layering and morph transitions
- Enhanced instrument family balancing

### v10 — GM-Timbre-Aware Synthesis

- **Tempo**: 1.2x-1.8x (flat range, moderate pace)
- **GM timbre profiles**: 15 distinct synthesis profiles per instrument family
  (piano, strings, brass, reed, pipe, synth, world, etc.) — each with unique
  attack, decay, harmonics, and brightness
- **Orchestral layering**: 85% simultaneous (4-6 voices), 15% solo
- **Min 3 family groups** per segment for true section diversity
- **8s morph transitions** between moods (smooth crossfades)
- **Wider register**: -24 to +24 semitone spread
- **1,771 MIDI files** from 120+ composers (Renaissance through Late Romantic)
- **60 instrument samples**
- All v9/v8/v7 features preserved

### v9 — Expanded Instruments + Density-Aware Tempo

- ~50 new GM instruments across 15 family pools
- Density-aware tempo 1.1x-2.1x (capped during busy epochs)
- Family variety enforcement

### v8 — Orchestral Layering

- 75% simultaneous multi-instrument sections
- Anti-hiss filtering, subsonic removal, note smoothing
- 70% simple time signatures with compound/complex guarantees

### v7 (Classic)

- 500+ synthesized instruments, 2-4 per mood
- 7 rondo structures, 6 arpeggio forms
- Harmonic consonance enforcement
- MIDI sampling, TTS voice injection

## Quick Start

```bash
# Generate 30-minute cosmic radio MP3 (v20 — recommended)
python apps/audio/radio_engine.py -V v20 --output cosmic_radio_v20.mp3 --duration 1800

# Generate with specific seed
python apps/audio/radio_engine.py -V v20 --output radio.mp3 --seed 42

# v7 classic style
python apps/audio/radio_engine.py --output cosmic_radio_v7.mp3 --duration 1800
```

## Dependencies

All synthesis is stdlib-only Python. Optional dependencies for enhanced features:

| Dependency | Purpose | Required? |
|-----------|---------|-----------|
| ffmpeg | WAV -> MP3 conversion | Yes (for MP3 output) |
| mido | MIDI file parsing | Optional (enables 1,771-file classical MIDI sampling) |
| fluidsynth + FluidR3_GM.sf2 | High-quality instrument rendering | Optional |
| numpy | ~7-10x faster rendering | Optional |
| torch + torchaudio | Silero TTS voice synthesis | Optional |
| espeak-ng | Fallback TTS | Optional |

## Testing

```bash
# Run all audio tests
python -m pytest apps/audio/ -v

# Run specific test files
python -m pytest apps/audio/test_radio_engine.py -v
python -m pytest apps/audio/test_composer.py -v
python -m pytest apps/audio/test_music_engine.py -v
python -m pytest apps/audio/test_audio.py -v
```

## File Structure

```
apps/audio/
  radio_engine.py       Radio engine v7-v20 (standalone music generator)
  composer.py           Streaming composition engine (per-tick)
  music_engine.py       Bar-based structured music engine
  generate.py           Audio renderer and output pipeline
  sample_gen.py         Instrument sample generator
  test_radio_engine.py  Radio engine tests (240 tests)
  test_composer.py      Composer tests (67 tests)
  test_music_engine.py  Music engine tests (62 tests)
  test_audio.py         Audio renderer tests (36 tests)
  midi_library/         1,771 public domain classical MIDI files from 120+ composers
  samples/              60 synthetic instrument samples (MP3)
```

## Attribution

MIDI files sourced from public domain compositions (~1400-1920) spanning 120+
composers from the Renaissance through Late Romantic era. Sources include
narcisse-dev/classical_ancient_midifiles, MAESTRO dataset, ASAP dataset, and MusicNet.
See `midi_library/ATTRIBUTION.md` for full details and licensing.
