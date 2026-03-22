# Cosmic Runner V3: V8 Sessions

The definitive version of Cosmic Runner — a music-synchronized interactive
experience combining an arcade runner game, 64x64 grid visualizer, and
standalone music player.

## Features

- **Three modes**: Music Player, Game (1-2 player), Grid Visualizer
- **V8 Sessions album**: 12 tracks synced with 64x64 cell grid visualization
- **MIDI mode**: 1,854 classical MIDI files from 120 composers played via
  Web Audio API with 16 mutation presets
- **Infinite shuffle**: Endless playback in both MP3 and MIDI modes
- **2-player cooperative**: WASD/Arrows with shared glow mechanic
- **Progressive 3D**: Rolling terrain that builds over 6 levels
- **8 themes + 34 star styles**: Cosmic, Ember, Neon, Midnight, and more
- **3 accessibility modes**: Minimal, Normal, Flashy
- **Provenance display**: Composer, piece, era, mutation shown during MIDI play
- **GitHub Pages ready**: Single-file bundle deployable anywhere

## Quick Start

```bash
# Serve locally
python3 -m http.server 8000
# Open http://localhost:8000

# Or use the radio server (infinite streaming)
node server/radio.js
# SSE at http://localhost:8088/stream/events
```

## Build for Deployment

```bash
# Bundle all JS/CSS into dist/index.html
python3 build.py

# Include MIDI library
python3 build.py --with-midi

# Full build with verification
python3 build.py --full
```

See [DEPLOY.md](DEPLOY.md) for GitHub Pages deployment instructions.

## Controls

| Input | Action |
|-------|--------|
| SPACE / UP | Jump (unlimited multi-jump) |
| DOWN | Fast drop |
| LEFT / RIGHT | Move horizontally |
| 1 / 2 / 3 | Switch mode (Player / Game / Grid) |
| P / ESC | Pause |
| + / - | Adjust speed |
| Mouse click | Jump (P2 in 2-player) |
| Mouse drag | Reposition character |

**2-Player**: P2 uses WASD or Numpad 8/4/6/5.

## MIDI Mode

Toggle MIDI Mode on the title screen. When enabled:
- Random classical MIDI files play via Web Audio API synthesis
- 16 mutation presets alter pitch, tempo, reverb, and filtering
- The 64x64 grid visualizes MIDI note events in real-time
- Provenance panel shows composer, piece name, and era

## File Structure

```
cosmic-runner-v3/
  index.html          Main entry point
  css/styles.css      All styling (responsive)
  js/
    config.js         Constants (colors, epochs, scoring, MIDI mutations)
    themes.js         8 themes + 34 star styles
    app.js            Main controller (modes, MIDI toggle, input)
    game.js           Game engine (physics, scoring, levels)
    player.js         HTML5 Audio player with Media Session API
    midi-player.js    Web Audio API MIDI parser + synthesizer
    music-sync.js     Note event loading, MIDI catalog, grid sync
    background.js     64x64 grid + starfield rendering
    renderer3d.js     Progressive 3D terrain
    runner.js         Player character (physics, rendering)
    obstacles.js      Emoji-based obstacle system
    characters.js     12 character types (cosmic epoch forms)
    blast-effect.js   Collision visual effects
  audio/
    album_notes.json  Album index
    midi_catalog.json MIDI library index (1,854 files)
    *.mp3             12 V8 Sessions tracks
    *_notes_v3.json   Per-track note events (compressed)
  server/radio.js     Infinite streaming radio (Node.js SSE)
  test/               Unit tests (Node.js native test runner)
  build.py            Static site bundler
  DEPLOY.md           GitHub Pages deployment guide
```

## Tests

```bash
# JS tests (111 tests)
node --test test/test_game.js test/test_radio.js test/test_midi_player.js

# Python integration tests (71 tests)
python -m pytest tests/test_cosmic_runner_v3.py -v

# MIDI catalog tests (24 tests)
python -m pytest tests/test_midi_catalog.py -v
```

## Album: V8 Sessions

| # | Track | Epoch | Duration |
|---|-------|-------|----------|
| 1 | Ember | Quantum Fluctuation | 4:12 |
| 2 | Torrent | Inflation | 4:54 |
| 3 | Quartz | Quark-Gluon Plasma | 6:18 |
| 4 | Tide | Nucleosynthesis | 4:58 |
| 5 | Root | Recombination | 4:50 |
| 6 | Glacier | Dark Ages | 4:48 |
| 7 | Bloom | First Stars | 4:12 |
| 8 | Dusk | Galaxy Formation | 4:54 |
| 9 | Coral | Solar Ignition | 6:18 |
| 10 | Moss | Hadean Earth | 4:58 |
| 11 | Thunder | Abiogenesis | 4:50 |
| 12 | Horizon | Emergence of Life | 4:48 |

Artist: aiphenomenon (A. Johan Bizzle)
