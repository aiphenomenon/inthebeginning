# In The Beginning -- 64x64 Grid Visualizer

A pure JavaScript web application that visualizes music playback on a 64x64 grid
of embossed cells. Each cell represents a pitch/instrument intersection, lighting
up with instrument-family-colored HSL when notes are active.

## Usage

Open `index.html` in any modern browser. No build step, no npm, no server required.

### Loading a Score

1. Click **Load Score** (top right) or drag-and-drop a `.json` score file onto the grid.
2. Press play to start playback.

### URL Parameters

You can also configure the visualizer via URL parameters:

```
index.html?mode=album&score=scores/my_score.json&audio=my_album.mp3
index.html?mode=single&score=scores/render.json&audio=render.mp3
index.html?mode=stream&stream=http://localhost:8080/events
```

| Parameter | Description |
|-----------|-------------|
| `mode`    | `album`, `single`, or `stream` |
| `score`   | URL to a score JSON file |
| `audio`   | URL to an audio file (MP3, WAV, OGG) |
| `stream`  | SSE endpoint URL (stream mode only) |

## Three Modes

### Album Mode (`mode=album`)

Full album playback with multiple tracks. Track list sidebar (collapsible on mobile).
Auto-advances to next track. All controls visible: play/pause, skip +/-15s,
previous/next track, seek bar, volume, fullscreen.

### Single Mode (`mode=single`)

Single continuous audio file (e.g., a 30-minute render). No previous/next track
buttons. Seek bar, skip, play/pause, and volume all active.

### Stream Mode (`mode=stream`)

Infinite radio stream via Server-Sent Events. Play/pause only -- no seek, no skip.
Note data arrives in real-time from the SSE endpoint. Color transitions happen
automatically.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| Left Arrow | Skip back 15 seconds |
| Right Arrow | Skip forward 15 seconds |
| Up Arrow | Volume up |
| Down Arrow | Volume down |
| F | Toggle fullscreen |

## Grid Design

- **64x64 cells** (4096 total)
- **Y-axis (rows)**: Pitch -- MIDI notes 24-87 (C1 to Eb6, ~5 octaves). Row 0 = highest.
- **X-axis (columns)**: Instrument channels (up to 64 concurrent instruments).
- **Color hue**: Instrument family -- strings (red), keys (blue), winds (green),
  percussion (yellow), world (purple), synth (cyan), voice (white).
- **Saturation**: 60-100% based on velocity (louder = more saturated).
- **Brightness**: 30-90% based on velocity (louder = brighter).
- **Bent notes**: Pulsing glow animation.
- **Color shift**: Every 10 minutes, hues rotate by 30-60 degrees with a smooth
  5-second CSS transition.
- **Inactive cells**: Dark embossed (#1a1a1a) with inset box-shadow.

## JSON Score Format

Score files describe note events with timing information:

```json
{
  "version": "1.0",
  "mode": "album",
  "sample_rate": 44100,
  "duration": 4746.0,
  "color_shift_interval": 600,
  "tracks": [
    {
      "track_num": 1,
      "title": "Track Name",
      "start_time": 0.0,
      "duration": 252.0,
      "audio_file": "path/to/track.mp3",
      "events": [
        {
          "t": 0.5,
          "dur": 1.2,
          "note": 64,
          "inst": "violin",
          "vel": 0.8,
          "bend": 0.0,
          "ch": 3
        }
      ]
    }
  ],
  "instruments": ["violin", "piano", "flute"],
  "instrument_families": {
    "violin": "strings",
    "piano": "keys",
    "flute": "winds"
  }
}
```

### Event Fields

| Field | Type | Description |
|-------|------|-------------|
| `t` | float | Time offset from track start (seconds) |
| `dur` | float | Note duration (seconds) |
| `note` | int | MIDI note number (24-87 mapped to grid) |
| `inst` | string | Instrument name |
| `vel` | float | Velocity 0.0-1.0 (affects brightness/saturation) |
| `bend` | float | Pitch bend amount (non-zero triggers glow animation) |
| `ch` | int | Channel/column assignment (0-63) |

### SSE Stream Format

For stream mode, the SSE endpoint sends `notes` events:

```
event: notes
data: {"t":123.4,"events":[{"note":64,"inst":"violin","vel":0.8,"dur":0.5}]}
```

## Generating Scores

Score JSON files can be generated from the audio composition engine:

```bash
python apps/audio/radio_engine.py --score-output scores/my_score.json
```

## Browser Compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires: ES6, CSS Grid, Fullscreen API, requestAnimationFrame, EventSource (for
stream mode).

## Running Tests

```bash
cd apps/visualizer
node --test test/test_grid.js test/test_score.js test/test_player.js
```

## File Structure

```
apps/visualizer/
  index.html          Main entry point
  css/
    visualizer.css    Grid, controls, and responsive styling
  js/
    grid.js           Grid engine: note-to-cell mapping, colors, hue rotation
    player.js         Audio playback, UI controls, keyboard shortcuts
    stream.js         SSE client for infinite radio mode
    score.js          Score JSON loader and binary-search event lookup
    app.js            Main application: mode detection, initialization
  test/
    test_grid.js      Grid mapping and color tests (88 assertions)
    test_player.js    Player control and state tests
    test_score.js     Score parsing and event lookup tests
  scores/             Directory for score JSON files
  version.json        Version metadata
  README.md           This file
```

## Architecture

Pure JavaScript -- no frameworks, no npm dependencies, no build tools. The entire
application is five JS files loaded via script tags, one CSS file, and one HTML file.

Audio playback uses the native HTML5 `<audio>` element. Grid updates run via
`requestAnimationFrame` at ~30fps, diffing previous state to minimize DOM mutations.
Binary search through sorted events finds active notes at the current playback time.
