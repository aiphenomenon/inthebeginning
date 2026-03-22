# In The Beginning -- 64x64 Grid Visualizer V3

A pure JavaScript web application that visualizes music playback on a 64x64 grid
of embossed cells. Each cell represents a pitch/instrument intersection, lighting
up with instrument-family-colored HSL when notes are active.

**V3 features**: In-browser MIDI synthesizer with 16+ instrument timbres, Web Worker
concurrent parsing, 16 mutation presets, full MIDI library access (1,854 classical
pieces), pitch bend visualization, and GitHub Pages deployment.

## Usage

Open `index.html` in any modern browser. No build step, no npm, no server required.

### Loading Content

1. **Album mode**: Auto-loads V8 Sessions album (12 MP3 tracks) if found in sibling directories.
2. **MIDI Synth mode**: Click the MIDI Synth tab to switch. Loads and synthesizes MIDI files
   in real-time using Web Audio API additive synthesis.
3. **Drag-and-drop**: Drop a `.json` score file or `.mid` MIDI file directly onto the grid.
4. **File input**: Click **Load Score** to browse for a JSON or MIDI file.

### URL Parameters

```
index.html?mode=album&score=scores/my_score.json&audio=my_album.mp3
index.html?mode=single&score=scores/render.json&audio=render.mp3
index.html?mode=midi
index.html?mode=stream&stream=http://localhost:8080/events
```

| Parameter | Description |
|-----------|-------------|
| `mode`    | `album`, `single`, `midi`, or `stream` |
| `score`   | URL to a score JSON file |
| `audio`   | URL to an audio file (MP3, WAV, OGG) |
| `stream`  | SSE endpoint URL (stream mode only) |

## Four Modes

### Album Mode (`mode=album`)

Full album playback with multiple tracks. Track list sidebar (collapsible on mobile).
Auto-advances to next track. All controls visible: play/pause, skip +/-15s,
previous/next track, seek bar, volume, fullscreen.

### Single Mode (`mode=single`)

Continuous audio file playback. Like album mode but no track list or prev/next.

### MIDI Synth Mode (`mode=midi`)

**New in V3.** In-browser MIDI synthesis using Web Audio API:

- **Additive synthesis**: 16+ instrument timbres ported from the Python composer.py
  (violin, cello, flute, oboe, trumpet, piano, bell, gamelan, choir, etc.)
- **Web Worker parsing**: MIDI files are parsed in a background Web Worker thread
  for non-blocking performance
- **16 mutation presets**: Original, Celestial, Subterranean, Crystal, Nebula,
  Quantum, Solar Wind, Deep Space, Pulsar, Cosmic Ray, Dark Matter, Supernova,
  Event Horizon, Starlight, Graviton, Photon
- **MIDI library access**: 1,854 classical MIDI files from 120+ public domain composers
- **Infinite shuffle**: Enable to continuously play random MIDIs
- **Pitch bend visualization**: Notes with pitch bend show pulsing glow animation
- **Composer provenance**: Shows composer name, piece title, and active mutation
- **ADSR envelopes**: Per-instrument attack/decay/sustain/release curves
- **Percussion synthesis**: Kick, snare, hi-hat synthesized from scratch
- **Vibrato/tremolo**: Automatic vibrato on sustained notes

### Stream Mode (`mode=stream`)

Server-Sent Events for infinite radio visualization. Play/pause only (no seek).

## Synthesizer Architecture

The synthesizer is a direct port of the Python `AdditiveSynth` from `apps/audio/composer.py`:

```
MIDI File (.mid) → Web Worker (synth-worker.js) → Parsed Note Events
                                                        ↓
Grid Visualization ← Note Events ← SynthEngine (synth-engine.js) → AudioContext
```

### Instrument Timbres (Additive Synthesis)

Each instrument is defined by a harmonic profile — amplitudes of overtones relative
to the fundamental frequency:

| Instrument | Harmonics | Character |
|------------|-----------|-----------|
| Violin     | 12        | Rich, sustained bow |
| Cello      | 10        | Deep, warm strings |
| Flute      | 4         | Pure, few harmonics |
| Oboe       | 9         | Nasal, reedy |
| Clarinet   | 10        | Odd harmonics dominant |
| Trumpet    | 10        | Bright, brassy |
| Piano      | 10        | Percussive, rich decay |
| Bell       | 10        | Metallic, inharmonic overtones |
| Gamelan    | 8         | Javanese metallic shimmer |
| Choir (Ah) | 7         | Warm vocal formant |
| Throat Sing| 10        | Enhanced 6th/10th overtones |
| Cosmic     | 10        | Alien, otherworldly |

### Color Mapping

Grid cells are colored by instrument family:

| Family     | Hue    | Color   |
|------------|--------|---------|
| Strings    | 0°     | Red     |
| Keys       | 220°   | Blue    |
| Winds      | 120°   | Green   |
| Percussion | 50°    | Yellow  |
| World      | 280°   | Purple  |
| Synth      | 180°   | Cyan    |
| Voice      | 0° (low sat) | White |
| Brass      | 30°    | Orange  |

Saturation scales with velocity (60-100%). Lightness scales with velocity (30-90%).
Colors shift every 2 minutes in MIDI mode (every 10 minutes in album mode).

## GitHub Pages Deployment

### Build

```bash
python build.py                    # Full build (MP3s + MIDI)
python build.py --no-midi          # MP3 only (smaller)
python build.py --no-mp3           # Synth only (smallest)
python build.py --no-mp3 --no-midi # Just the visualizer shell
```

### Deploy

1. Copy the contents of `dist/` to your GitHub Pages repository
2. Push to the `gh-pages` branch (or configure Pages to serve from `main/docs`)
3. Open `https://yourusername.github.io/your-repo/`

### Deployment Options

| Option | Size | Features |
|--------|------|----------|
| Full (MP3 + MIDI) | ~115 MB | Album playback + MIDI synthesis + full library |
| MP3 only | ~90 MB | Album playback only |
| MIDI only | ~25 MB | MIDI synthesis + full classical library |
| Synth only | ~50 KB | Pure synthesizer (drag-and-drop MIDI files) |

## Tests

```bash
cd apps/visualizer
node --test test/test_grid.js test/test_score.js test/test_player.js \
  test/test_synth_engine.js test/test_midi_player.js
```

152 tests covering: grid mapping, score parsing, player controls, synth engine
timbres/envelopes/colors, MIDI player state management, and mutation presets.

## File Structure

```
apps/visualizer/
├── index.html              Main page (4 modes: album, single, midi, stream)
├── version.json            Version identifier
├── build.py                GitHub Pages build script
├── css/
│   └── visualizer.css      Styles (responsive, MIDI controls, bend animation)
├── js/
│   ├── grid.js             64x64 grid engine (pitch/instrument mapping, colors)
│   ├── score.js            Score JSON parser (V3 compressed + legacy formats)
│   ├── synth-engine.js     Additive synthesizer (16+ timbres, ADSR, percussion)
│   ├── synth-worker.js     Web Worker for MIDI parsing (non-blocking)
│   ├── midi-player.js      MIDI playback via SynthEngine + Worker
│   ├── player.js           HTML5 Audio player (album/single modes)
│   ├── stream.js           SSE client for radio mode
│   └── app.js              Application controller (mode management, catalog)
├── test/
│   ├── test_grid.js        Grid mapping tests (88 assertions)
│   ├── test_score.js       Score parsing tests
│   ├── test_player.js      Player control tests
│   ├── test_synth_engine.js Synth engine tests (timbres, envelopes, colors)
│   └── test_midi_player.js  MIDI player tests (state, mutations)
└── scores/                 Example score JSON files
```

## Dependencies

- **Zero external dependencies**. Pure ES6 JavaScript + Web Audio API.
- Browser requirements: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Web Worker support (graceful fallback to main thread if unavailable)
