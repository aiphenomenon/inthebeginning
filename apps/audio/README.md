# Audio Composition Engine — In The Beginning Radio

A cosmic simulation music station that generates continuously evolving music
driven by physics simulation state. The engine transforms epoch transitions,
temperature changes, and particle interactions into musical compositions.

## Features (v7)

- **Radio Engine** (`radio_engine.py`): Standalone 30-minute music generator
  - 500+ algorithmically synthesized instruments with runtime rotation
  - Mood segments at multiples of 42 seconds (42, 84, 126, 168, 210s)
  - 2-4 instruments per mood forming a small band ensemble
  - 7 rondo structures (ABACA, ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA)
  - 6 arpeggio forms (block, ascending, descending, alberti, broken, pendulum)
  - Tempo multiplier 1.5x-2.5x for natural pacing
  - Hartmann consonance enforcement on all chord voicings
  - Anti-click processing: micro-fades, DC offset removal, cosine crossfades
  - MIDI sampling from 249 public domain classical works (1600-1900)
  - FluidSynth integration with FluidR3_GM.sf2 soundfont
  - TTS voice injection using Silero or espeak-ng

- **Composition Engine** (`composer.py`): Streaming per-tick renderer
  - 40+ world musical scales (Western, Japanese, Chinese, Middle Eastern, Indian)
  - 16 instrument timbres via additive synthesis with wavetable oscillators
  - 4-voice polyphonic melodic system
  - Beat engine with epoch-driven presence

- **Music Engine** (`music_engine.py`): Bar-based structured renderer
  - Multi-track mixing (melody, harmony, bass, pad, drums, accent)
  - 40 synthetic instrument samples
  - Proper time signatures and chord progressions

## Quick Start

```bash
# Generate 30-minute cosmic radio MP3 (v7)
python apps/audio/radio_engine.py --output cosmic_radio_v7.mp3 --duration 1800

# Generate with custom seed
python apps/audio/radio_engine.py --output radio.mp3 --seed 123

# Generate simulation-driven audio (structured engine)
python apps/audio/generate.py --duration 600 --output cosmic.mp3 --engine structured
```

## Dependencies

All synthesis is stdlib-only Python. Optional dependencies for enhanced features:

| Dependency | Purpose | Required? |
|-----------|---------|-----------|
| ffmpeg | WAV → MP3 conversion | Yes (for MP3 output) |
| mido | MIDI file parsing | Optional (enables classical MIDI sampling) |
| fluidsynth + FluidR3_GM.sf2 | High-quality instrument rendering | Optional |
| numpy | ~10x faster rendering | Optional |
| torch + torchaudio | Silero TTS voice synthesis | Optional |
| espeak-ng | Fallback TTS | Optional |

## Testing

```bash
# Run all audio tests
python -m pytest apps/audio/ -v

# Run just radio engine tests (fast, no MIDI loading)
python -m pytest apps/audio/test_radio_engine.py -v -k "not TestRadioEngine"

# Run all tests including full render tests (slow, loads 249 MIDI files)
python -m pytest apps/audio/test_radio_engine.py -v
```

## File Structure

```
apps/audio/
  radio_engine.py       Radio engine v7 (standalone music generator)
  composer.py           Streaming composition engine (per-tick)
  music_engine.py       Bar-based structured music engine
  generate.py           Audio renderer and output pipeline
  sample_gen.py         40-instrument sample generator
  test_radio_engine.py  Radio engine tests (81 tests)
  test_composer.py      Composer tests (67 tests)
  test_music_engine.py  Music engine tests (62 tests)
  test_audio.py         Audio renderer tests (36 tests)
  midi_library/         249 public domain classical MIDI files
  samples/              40 synthetic instrument samples (MP3)
```

## Attribution

MIDI files sourced from public domain compositions (1600-1900) by Bach, Beethoven,
Mozart, Chopin, Brahms, and others. See `midi_library/ATTRIBUTION.md` for details.
