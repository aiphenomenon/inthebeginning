# Cosmic Runner — In The Beginning

An 8-bit side-scroller music game set in the cosmic universe of
*In The Beginning Phase 0*. Play as **Aki**, a cosmic entity that
runs, jumps, and blasts through obstacles while the album plays.

## Features

- Auto-running endless runner with jump mechanics
- Unkillable — Aki blasts through obstacles in particle explosions
- Music-synced 64x64 grid visualization as a muted background
- Character morphs through 6 cosmic forms as music epochs change
- Foreground obstacles with high contrast against the subdued background
- Full album player with track navigation, seek, and volume controls
- Responsive design (desktop, tablet, phone)

## Two Versions

### 1. Multi-File JS Version (Development)

The source code in this directory. Serve with any static file server:

```bash
# From the project root
cd apps/cosmic-runner
python3 -m http.server 8000
# Open http://localhost:8000
```

### 2. Bundled Single-File Version (GitHub Pages)

A single `dist/index.html` with all JS and CSS inlined.
Only external dependencies are the MP3 audio files.

```bash
# Build the bundled version
python3 build.py
# Output: dist/index.html (73 KB)
```

## Deployment to GitHub Pages

### Setup

1. **Build the bundled file:**
   ```bash
   cd apps/cosmic-runner
   python3 build.py
   ```

2. **Copy files to your GitHub Pages repo:**
   ```
   your-github-pages-repo/
     cosmic-runner/
       index.html          (from dist/index.html)
       audio/
         album_notes.json  (from apps/audio/output/album/)
         *.mp3             (from apps/audio/output/album/)
   ```

3. **Or via GitHub UI (mobile-friendly):**
   - Go to your GitHub Pages repo in a browser
   - Create a new directory `cosmic-runner/`
   - Upload `dist/index.html` as `index.html`
   - Create `cosmic-runner/audio/` subdirectory
   - Upload `album_notes.json` and all album MP3s there
   - Commit to the `main` (or `gh-pages`) branch

4. **Access at:**
   ```
   https://yourusername.github.io/your-repo/cosmic-runner/
   ```

### Copy Commands (Terminal)

If you prefer terminal commands to copy from this repo to your
GitHub Pages repo:

```bash
# Set these to your paths
PAGES_REPO="/path/to/your-github-pages-repo"
GAME_DIR="$PAGES_REPO/cosmic-runner"

# Create directory and copy bundled HTML
mkdir -p "$GAME_DIR/audio"
cp apps/cosmic-runner/dist/index.html "$GAME_DIR/index.html"

# Copy album audio files
cp apps/audio/output/album/album_notes.json "$GAME_DIR/audio/"
cp apps/audio/output/album/*.mp3 "$GAME_DIR/audio/"
cp apps/audio/output/album/*_notes.json "$GAME_DIR/audio/"

# Commit and push
cd "$PAGES_REPO"
git add cosmic-runner/
git commit -m "Add Cosmic Runner game"
git push
```

### Note on File Sizes

The album MP3s total ~111 MB. GitHub repos have a 100 MB per-file
limit and 1 GB total repo size recommendation. Individual MP3 files
are 4-10 MB each, well under the per-file limit.

If your Pages repo approaches the size limit, consider hosting
audio files on a CDN or external storage and updating the
`audio/album_notes.json` paths accordingly.

Git LFS is not required for these file sizes.

## Controls

| Input | Action |
|-------|--------|
| SPACE / TAP / CLICK | Jump |
| P / ESC | Pause / Resume |
| Track title (click) | Open track list |
| Music bar | Play/pause, seek, volume, prev/next |

## Architecture

```
index.html          Entry point
css/game.css        All styles
js/
  background.js     Muted 64x64 grid + parallax starfield
  runner.js         Aki character (physics, morphing, rendering)
  obstacles.js      Obstacle generation and collision
  music-sync.js     Score JSON loading and time-based event lookup
  game.js           Game engine (loop, state, canvas rendering)
  player.js         Audio player with HTML5 Audio API
  app.js            Top-level controller (screens, input, sync)
build.py            Bundle script (-> dist/index.html)
```

## How Music Sync Works

1. `album_notes.json` describes all tracks with timing data
2. Per-track `*_notes.json` files contain individual note events
3. During gameplay, note events are fed to the background grid
4. Music intensity (note density + velocity) affects game speed
5. Epoch transitions (time-based within each track) trigger
   character morphing to different cosmic forms

## No External Dependencies

- Pure JavaScript (no npm, no build tools except the bundler)
- HTML5 Canvas for rendering
- HTML5 Audio API for playback
- Zero external libraries
