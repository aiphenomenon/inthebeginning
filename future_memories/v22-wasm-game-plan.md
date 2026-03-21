# V22 Plan — Cosmic Runner: Music Player + Side-Scroller Game

## Created: 2026-03-21 13:19 CT (18:19 UTC)

## Context

User requested a unified web application combining:
1. The existing 64x64 grid visualizer (as muted background)
2. Album music playback (MP3s from "In The Beginning Phase 0")
3. A new 8-bit side-scroller game ("Cosmic Runner")

### User Requirements (Speech-to-Text, Preserved As-Is)
- JS + plain MP3s version that works as "basically an Ajax application"
- Also a bundled single-file HTML version for GitHub Pages deployment
- Grid visualization as subdued/muted background during gameplay
- Foreground objects with high contrast against the muted background
- Player character ("Aki") blasts through obstacles
- No git LFS unless absolutely necessary
- Include deployment instructions for GitHub Pages in markdown

### Architecture Decisions
- **No WASM compilation needed**: A 2D canvas side-scroller runs perfectly in JS.
  The "single file" goal is achieved by bundling all JS/CSS into one HTML file.
- **MP3s remain separate files**: 111MB of audio cannot be embedded in a single file.
  Both versions reference MP3s from a sibling `audio/` directory.
- **Single directory**: `apps/cosmic-runner/` holds both the source (multi-file JS)
  and a Python build script that produces `dist/index.html` (bundled version).

## Game Design

### Character: Aki
- Pixel-art cosmic entity rendered on canvas
- Morphs shape/color at musical epoch transitions
- Unkillable — blasts through obstacles instead of dying

### Mechanics
- Auto-running endless runner (left to right)
- Jump with spacebar / tap / click
- Obstacles: cosmic objects (asteroids, dark matter, crystals, DNA helixes)
- Score based on distance traveled + objects blasted
- Speed increases with music intensity

### Visual Layers (back to front)
1. Dark space background
2. Muted 64x64 grid (low opacity, subdued colors from album note events)
3. Parallax star field
4. Ground/platforms
5. Obstacles
6. Aki character
7. Particle effects (blast-through explosions)
8. UI overlay (score, track info)

## File Structure

```
apps/cosmic-runner/
  index.html              # Main HTML entry point
  css/game.css            # All styles
  js/
    game.js               # Game engine (canvas, loop, state)
    runner.js             # Aki character (physics, rendering, morphing)
    obstacles.js          # Obstacle generation and collision
    background.js         # Muted grid background + starfield
    music-sync.js         # Music analysis + epoch detection
    player.js             # Audio player UI
    app.js                # Main app controller
  build.py                # Bundle script -> dist/index.html
  dist/
    index.html            # Bundled single-file version
  README.md               # Deployment and usage guide
```

## Status

- [x] Phase 1: Directory structure and plan
- [ ] Phase 2: Game engine (canvas, character, obstacles, physics)
- [ ] Phase 3: Muted grid background with music sync
- [ ] Phase 4: Music player integration
- [ ] Phase 5: Bundled single-file build
- [ ] Phase 6: Testing, deployment docs, polish

## Deployment

### JS Version (Multi-File)
Serve `apps/cosmic-runner/` via any static file server.
Copy MP3s from `apps/audio/output/album/` to `apps/cosmic-runner/audio/`.

### Bundled Single-File Version
Run `python apps/cosmic-runner/build.py` to generate `dist/index.html`.
Copy `dist/index.html` + `audio/` folder to GitHub Pages repo.
The HTML file is self-contained (all JS/CSS inlined). Only MP3s are external.
