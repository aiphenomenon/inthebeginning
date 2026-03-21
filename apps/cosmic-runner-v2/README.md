# Cosmic Runner V2 — V8 Sessions

A three-mode cosmic music experience built on the V8 Sessions album.

## Modes

| Mode | Key | Description |
|------|-----|-------------|
| **Music Player** | `1` | Standalone audio player with ambient background grid |
| **Game** | `2` | Side-scroller game with Aki, subdued cells, parallax stars |
| **Grid** | `3` | Full 64x64 cell grid visualization synced to music |

Switch between modes at any time with the `1`/`2`/`3` keys or the tab buttons
in the HUD. Music playback continues seamlessly when switching.

## V8 Sessions Album

12 tracks split from two favorite 30-minute renders:

| # | Name | Source |
|---|------|--------|
| 1 | Ember | V8 orchestral |
| 2 | Torrent | V8 orchestral |
| 3 | Quartz | V8 orchestral |
| 4 | Tide | V8 orchestral |
| 5 | Root | V8 orchestral |
| 6 | Glacier | V8 orchestral |
| 7 | Bloom | V18-V8 tempo |
| 8 | Dusk | V18-V8 tempo |
| 9 | Coral | V18-V8 tempo |
| 10 | Moss | V18-V8 tempo |
| 11 | Thunder | V18-V8 tempo |
| 12 | Horizon | V18-V8 tempo |

Each track includes JSON note metadata for synchronized visualization.

## Controls

- **Space / Tap**: Jump (game mode) or start
- **1 / 2 / 3**: Switch modes (player / game / grid)
- **P / Escape**: Pause
- **Click track title**: Show track list

## Building

```bash
# Bundle into single HTML file
python build.py
# Output: dist/index.html

# Generate the album (requires audio engine)
python ../../apps/audio/generate_v8_album.py
```

## Deployment to GitHub Pages

1. Copy `dist/index.html` to your Pages repo
2. Copy `audio/` folder (all MP3s + `album_notes.json`) alongside it
3. Push and deploy

## Architecture

```
index.html          Entry point
css/styles.css      All styles (no preprocessor)
js/
  app.js            Main controller, mode switching
  background.js     64x64 grid + starfield renderer
  game.js           Game engine (mode-aware)
  runner.js         Aki character (shapes, physics)
  obstacles.js      Obstacle generation and rendering
  music-sync.js     Note data loading, time sync, note info
  player.js         HTML5 Audio playback
audio/              Album MP3s + JSON note files
dist/index.html     Bundled single-file version
build.py            Build script for bundling
```

## Dependencies

None. Pure HTML5 Canvas + JavaScript + CSS. No frameworks, no npm packages.
