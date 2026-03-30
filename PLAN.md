> **HISTORICAL PLAN (V22 era)** — This plan predates the current state.
> See `RELEASE_HISTORY.md` for what was actually implemented.
> See `future_memories/` for current plans.

# V22 Implementation Plan — Unified WASM Music + Visualizer + Side-Scroller

## Overview

Build a **single self-contained WebAssembly application** deployable to GitHub Pages
that bundles:
- The album music player (all 19 MP3 tracks, ~110MB)
- The 64x64 note event grid visualizer
- A new 8-bit side-scroller game mode
- Full-screen support (desktop, laptop, best-effort tablet/phone)

No server required. Everything compiled/bundled into static assets.

---

## Prior V21 Items (Already Complete)

Per session logs, all 9 V21 objectives were completed in the previous round:
1. Documentation audit — done (8 files)
2. JSON transcript logging — done (steering updated)
3. Music algorithm doc — done (docs/music_algorithm.md)
4. Steering triple-check — done (CLAUDE.md, AGENTS.md, steering-check.sh)
5. Album generation — done (19 tracks, 79.4 min, 110MB)
6. Vocoder → plain TTS — done (simplified)
7. Note event logging — done (8,626 events)
8. JavaScript visualizer — done (apps/visualizer/)
9. Streaming infrastructure — done (Go SSE, bash scripts)

No outstanding items from V21 to carry forward.

---

## Phase 1: Unified Web App Shell (`apps/wasm-player/`)

**Goal**: Create a new `apps/wasm-player/` directory that serves as the unified app.

### 1.1 Project Structure
```
apps/wasm-player/
├── index.html              # Single entry point
├── css/
│   └── style.css           # Unified styles (visualizer + game + player)
├── js/
│   ├── app.js              # Main app controller (mode switching)
│   ├── audio-player.js     # MP3 playback (Web Audio API + HTML5 Audio)
│   ├── visualizer.js       # 64x64 grid (ported from apps/visualizer/)
│   ├── game-engine.js      # Side-scroller game engine
│   ├── game-renderer.js    # 8-bit canvas renderer for the game
│   ├── game-sprites.js     # ASCII creature sprite definitions per epoch
│   ├── score.js            # Note event score loader (ported)
│   └── fullscreen.js       # Fullscreen API wrapper
├── assets/
│   ├── album/              # All 19 MP3 files (copied from audio output)
│   ├── scores/             # Note event JSON files
│   └── sprites/            # Optional: sprite sheet PNGs (or generated in JS)
├── build.sh                # Bundle script (creates dist/)
├── dist/                   # Final deployable output
└── test/
    └── test_game.js        # Game engine unit tests
```

### 1.2 Entry Point (index.html)
- Single HTML file with three mode buttons: **Listen** | **Visualize** | **Play Game**
- Small game controller icon (🎮 or pixel-art joystick) in the corner that toggles
  game mode
- Responsive layout: works on desktop (1920x1080+), laptop, tablet, phone
- Meta viewport for mobile scaling

### 1.3 Audio Player (audio-player.js)
- Port the existing Player class from `apps/visualizer/js/player.js`
- Uses HTML5 Audio for MP3 decoding (widely supported, no WASM audio decoder needed)
- Track list, play/pause, seek, volume, track navigation
- **Music continues playing across all modes** — switching to game mode doesn't
  interrupt playback
- Web Audio API `AnalyserNode` for real-time frequency data (feeds both visualizer
  and game)

### 1.4 Visualizer (visualizer.js)
- Port the existing 64x64 grid from `apps/visualizer/js/grid.js`
- Driven by note event scores (JSON) synced to audio playback time
- Color mapping matches existing instrument-to-color scheme

---

## Phase 2: Side-Scroller Game Engine

**Goal**: 8-bit style casual side-scroller, music-reactive, unkillable character.

### 2.1 Game Design Principles
- **No death mechanics**: Character cannot die, fall off screen, get crushed, or get
  stuck. Obstacles are just fun things to jump over.
- **Auto-scroll**: World scrolls left at a slow/medium pace (~60-80px/sec)
- **Player controls**:
  - **Jump**: Tap/click/spacebar — character does an arc jump
  - **Move left/right**: Arrow keys / touch drag — character can move horizontally
    within the visible window bounds
  - **Cannot exceed window bounds** — character is clamped to visible area
- **Music-reactive**:
  - Scroll speed subtly varies with music tempo/energy
  - Background colors shift with the current mood/epoch
  - Obstacles are themed to the current epoch (e.g., quantum particles in early
    epochs, DNA strands in biology epoch, stars in stellar epoch)
- **Character morphing**: At each mood/epoch transition, the ASCII creature morphs
  into a different form. ~8-10 distinct character sprites, one per cosmic epoch.

### 2.2 Game Engine (game-engine.js)
```
GameEngine:
  - gameState: { x, y, vx, vy, jumping, characterForm }
  - obstacles: Array<{ x, y, width, height, type }>
  - scrollSpeed: number (modulated by music energy)
  - update(dt): physics step (gravity, collision, bounds clamping)
  - spawnObstacle(): procedural obstacle generation
  - onEpochChange(epoch): morph character, change obstacle theme
```

**Physics**:
- Simple 2D platformer: gravity pulls down, ground plane at bottom
- Jump: apply upward velocity, gravity brings back down
- Horizontal movement: left/right with friction, clamped to window
- No pits, no ceilings, no kill zones — ground is always there

**Obstacle generation**:
- Procedural: spawn obstacles off-screen right, scroll left
- Spacing ensures player always has time to react (minimum gap)
- Obstacles are decorative — collision just bumps the character, doesn't kill
- Maybe: character does a little bounce/stumble animation on collision

### 2.3 Sprite System (game-sprites.js)
- Each epoch gets a distinct ASCII art character (rendered to canvas):
  - **Quantum Epoch**: Tiny vibrating particle `·∘○`
  - **Inflation**: Expanding blob `◉`
  - **Quark**: Triangle `▲`
  - **Hadron**: Circle cluster `⚛`
  - **Nuclear**: Star `✦`
  - **Atomic**: Shell rings `◎`
  - **Stellar**: Sparkle `✧`
  - **Galactic**: Spiral `🌀` (or ASCII spiral)
  - **Chemical**: Molecule `⌬`
  - **Biology**: Cell/creature `☘`
- Each sprite is an 8x8 or 16x16 pixel grid drawn on canvas
- Morph transition: quick dissolve/reassemble animation (~0.5s)

### 2.4 Game Renderer (game-renderer.js)
- Canvas 2D rendering (no WebGL needed for 8-bit style)
- Pixel-art aesthetic: nearest-neighbor scaling, limited color palette
- Background layers (parallax):
  - Layer 0: Solid color (epoch-themed)
  - Layer 1: Stars/particles (slow scroll)
  - Layer 2: Terrain/obstacles (main scroll speed)
  - Layer 3: Foreground detail (fast scroll)
- Ground: simple platform line at ~80% of canvas height
- Obstacles: 8-bit styled blocks/shapes themed per epoch
- HUD: minimal — current epoch name, track name (semi-transparent overlay)

### 2.5 Input Handling
- **Keyboard**: Space/Up = jump, Left/Right = move
- **Touch**: Tap anywhere = jump, drag left/right = move
- **Gamepad**: (stretch goal) basic gamepad API support
- All input systems coexist — keyboard + touch simultaneously OK

---

## Phase 3: Mode Integration

**Goal**: Seamless mode switching with persistent audio.

### 3.1 App Controller (app.js)
- Three modes: `listen`, `visualize`, `game`
- Mode switch via UI buttons or keyboard shortcut (G for game, V for visualize)
- Audio playback is **shared across all modes** — never interrupted
- When in game mode:
  - Visualizer grid becomes a small picture-in-picture overlay (corner of screen),
    or is hidden entirely (user preference)
  - Game canvas fills the main area
  - Audio frequency data drives both game energy and obstacle pacing
- When in visualize mode:
  - Grid fills the main area
  - Game is paused/hidden
- When in listen mode:
  - Album art / track list fills the main area
  - Both game and visualizer are hidden

### 3.2 Game Icon
- A small pixelated game controller icon (CSS/SVG, ~24x24px)
- Positioned in the bottom-right or top-right corner of the visualizer
- Tap/click toggles game mode on/off
- Subtle glow animation to indicate it's interactive

### 3.3 Fullscreen Support
- Fullscreen API (`document.documentElement.requestFullscreen()`)
- Works on desktop browsers (Chrome, Firefox, Safari, Edge)
- Works on iPad/tablet Safari with some limitations (no true fullscreen, but
  hides address bar via `minimal-ui` viewport or scroll trick)
- On iPhone: no Fullscreen API support — use `standalone` web app manifest
  to allow "Add to Home Screen" which gives full-screen-like experience
- Fullscreen button in the control bar
- ESC or swipe to exit fullscreen

---

## Phase 4: Static Bundling (No Server Required)

**Goal**: Everything as static files, deployable to GitHub Pages.

### 4.1 Asset Bundling Strategy
- **MP3 files**: Kept as-is (browser decodes natively), ~110MB total
- **Note event JSONs**: Kept as-is, ~1MB total
- **JavaScript**: Concatenated/minified into a single `bundle.js` (no npm,
  no webpack — just a simple shell script that `cat`s files together)
- **CSS**: Single `style.css`
- **HTML**: Single `index.html`
- Total bundle: ~112MB (dominated by MP3 audio)

### 4.2 Why Not Actual WASM?
The user said "WebAssembly" but the actual requirements (audio playback, canvas
rendering, touch input) are best served by plain JavaScript:
- MP3 decoding: Browser's native Audio API (WASM can't do this better)
- Canvas rendering: 2D context API (native JS, no WASM advantage for 8-bit)
- Input handling: DOM events (must be JS)
- The existing WASM app (`apps/wasm/`) is a Rust→WASM cosmic *simulator* — different
  purpose

**However**, to honor the user's "WASM" intent, we can:
- Option A: Keep it as pure JS (simpler, smaller, faster to build) but package it
  as a "web application" deployable to GitHub Pages — which is what the user actually
  wants functionally
- Option B: Compile the game physics engine to WASM (Rust) and call it from JS —
  technically WASM but adds complexity for minimal benefit in an 8-bit game

**Recommendation: Option A** — pure JS web app, static files, GitHub Pages ready.
The user's core request is "no server, self-contained, point someone to a URL."
That's a static web app, not necessarily WASM. We should clarify this with the user.

### 4.3 Build Script (build.sh)
```bash
#!/bin/bash
# Bundle all assets into dist/ for deployment
mkdir -p dist/assets/album dist/assets/scores
cp index.html dist/
cat js/*.js > dist/bundle.js  # or keep separate for cacheability
cp css/style.css dist/
cp assets/album/*.mp3 dist/assets/album/
cp assets/scores/*.json dist/assets/scores/
echo "Bundle complete: $(du -sh dist/)"
```

### 4.4 GitHub Pages Deployment
- `dist/` directory is the deployable artifact
- Can be deployed via `gh-pages` branch or GitHub Actions
- Add a `.nojekyll` file to prevent Jekyll processing
- Large MP3 files: GitHub Pages has a 1GB repo limit — 110MB of MP3s is fine
- Alternative: Use Git LFS for the MP3 files to keep repo size manageable

---

## Phase 5: Testing

### 5.1 Game Engine Tests (test/test_game.js)
- Physics: gravity, jump arc, bounds clamping
- Obstacle generation: spacing, scroll behavior
- Character morphing: epoch transitions
- Input: keyboard and touch event simulation
- No-death guarantee: verify character can never reach an invalid state

### 5.2 Integration Tests
- Audio playback continues across mode switches
- Fullscreen toggle works
- Score loading and sync
- Asset loading (all MP3s, all JSONs accessible)

### 5.3 Visual Golden Tests
- Screenshot comparison of game rendering at each epoch
- Visualizer grid matches existing golden outputs

---

## Phase 6: Documentation & Steering Updates

- Update `docs/roadmap.md` with WASM player entry
- Update `docs/apps_overview.md` with new app
- Update `RELEASE_HISTORY.md` with V22 entry
- Update `CLAUDE.md` if new test commands needed
- Session log and JSON transcript

---

## Execution Order

1. **Phase 1.1-1.2**: Create directory structure and HTML shell
2. **Phase 1.3-1.4**: Port audio player and visualizer from existing code
3. **Phase 2.1-2.5**: Build the side-scroller game engine
4. **Phase 3.1-3.3**: Integrate modes, add game icon, fullscreen
5. **Phase 4.1-4.3**: Build script, asset copying
6. **Phase 5**: Tests
7. **Phase 6**: Documentation

Estimated file count: ~15 new files, ~5 modified files.

---

## Open Questions for User

1. **WASM vs static JS**: The functional requirement (no server, GitHub Pages, music +
   game in browser) is best served by a static JavaScript web app. True WASM
   compilation would add complexity without benefit for this use case. Is plain JS
   acceptable, or do you specifically want Rust→WASM compilation?

2. **Asset hosting**: 110MB of MP3s in a GitHub repo is feasible but large. Options:
   - (a) Commit MP3s directly (simplest, ~110MB added to repo)
   - (b) Git LFS for MP3s (keeps repo small, LFS serves on Pages)
   - (c) Separate asset hosting (CDN) — but this reintroduces a server dependency
   Recommendation: (a) for simplicity since GitHub Pages supports it.

3. **Collision behavior**: When the character hits an obstacle, should it:
   - (a) Bounce/stumble (brief animation) then continue — slight penalty feel
   - (b) Pass through with a visual effect (sparkle/flash) — purely decorative
   - (c) Push the obstacle away — character is unstoppable force
   Recommendation: (b) — pass through with visual effect, keeping it chill.

4. **Visualizer in game mode**: Should the 64x64 grid be:
   - (a) Hidden during game mode
   - (b) Small picture-in-picture overlay
   - (c) Integrated as the game background (grid behind the platformer)
   Recommendation: (c) — grid as the game background would look spectacular.
