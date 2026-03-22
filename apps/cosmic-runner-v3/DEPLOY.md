# Cosmic Runner V3 — GitHub Pages Deployment Guide

## Overview

Cosmic Runner V3 is a self-contained web application that can be deployed to any
GitHub Pages repository (or any static file host). It includes:

- **12-track V8 Sessions album** (MP3 + synchronized note visualization)
- **1,854 classical MIDI files** from 120 composers (optional, for MIDI mode)
- **Three modes**: Music Player, Game, and Grid Visualizer
- **Infinite mode**: Endless shuffled playback (both MP3 and MIDI)

No server required. Everything runs in the browser.

---

## Quick Start

### 1. Build the deployment bundle

```bash
cd apps/cosmic-runner-v3

# HTML-only bundle (MP3 album, no MIDIs)
python3 build.py

# Full bundle with MIDI library (~25MB additional)
python3 build.py --with-midi

# Full bundle with asset verification
python3 build.py --full
```

### 2. Copy to your GitHub Pages repo

```bash
# Set your paths
PAGES_REPO="/path/to/your-github-pages-repo"
APP_DIR="$PAGES_REPO/cosmic-runner"

# Copy the built bundle
mkdir -p "$APP_DIR"
cp -r dist/* "$APP_DIR/"

# Add .nojekyll to prevent Jekyll processing
touch "$PAGES_REPO/.nojekyll"

# Commit and push
cd "$PAGES_REPO"
git add -A
git commit -m "Deploy Cosmic Runner V3"
git push
```

### 3. Access your app

```
https://yourusername.github.io/your-repo/cosmic-runner/
```

---

## Directory Structure in Your Pages Repo

```
your-github-pages-repo/
  .nojekyll                     # Required: prevents Jekyll processing
  cosmic-runner/
    index.html                  # Bundled app (all JS/CSS inlined, ~120KB)
    audio/
      album_notes.json          # Album index (track metadata)
      midi_catalog.json         # MIDI library index (if --with-midi)
      V8_Sessions-aiphenomenon-01-Ember.mp3
      V8_Sessions-aiphenomenon-01-Ember_notes_v3.json
      ... (12 tracks × 2 files = 24 files)
    midi/                       # Optional (if --with-midi)
      ATTRIBUTION.md            # Source/license info for all MIDIs
      midi_catalog.json         # MIDI index (duplicate for direct access)
      Bach/
        bwv846_prelude.mid
        ...
      Beethoven/
        ...
      ... (120 composer directories, 1,854 MIDI files)
```

---

## Deployment Without build.py

If you prefer not to use the build script, you can copy files directly:

```bash
PAGES_REPO="/path/to/your-github-pages-repo"
APP_DIR="$PAGES_REPO/cosmic-runner"
V3_DIR="apps/cosmic-runner-v3"

# Copy the multi-file version (not bundled)
mkdir -p "$APP_DIR/js" "$APP_DIR/css" "$APP_DIR/audio"
cp "$V3_DIR/index.html" "$APP_DIR/"
cp "$V3_DIR/css/"*.css "$APP_DIR/css/"
cp "$V3_DIR/js/"*.js "$APP_DIR/js/"
cp "$V3_DIR/audio/"*.mp3 "$APP_DIR/audio/"
cp "$V3_DIR/audio/"*.json "$APP_DIR/audio/"

# Optional: MIDI library
mkdir -p "$APP_DIR/midi"
cp -r apps/audio/midi_library/* "$APP_DIR/midi/"

touch "$PAGES_REPO/.nojekyll"
```

---

## GitHub Pages Setup

### Option A: Dedicated Pages repo (recommended)

1. Create a new GitHub repo (e.g., `yourusername/my-games`)
2. Go to **Settings → Pages**
3. Set **Source**: Deploy from a branch
4. Set **Branch**: `main`, folder: `/ (root)`
5. Copy files and push

### Option B: User site (yourusername.github.io)

1. Create repo named `yourusername.github.io`
2. Copy files into `cosmic-runner/` subdirectory
3. Push to `main`
4. Access at `https://yourusername.github.io/cosmic-runner/`

### Option C: Project site with gh-pages branch

1. In your existing repo, create a `gh-pages` branch
2. Copy files and push to that branch
3. Enable Pages from the `gh-pages` branch in Settings

---

## File Size Summary

| Component | Size | Files | Required? |
|-----------|------|-------|-----------|
| index.html (bundled) | ~120 KB | 1 | Yes |
| Album MP3s | ~110 MB | 12 | Yes (for MP3 mode) |
| Album JSON notes | ~2 MB | 13 | Yes (for visualization) |
| MIDI library | ~25 MB | 1,854 | No (for MIDI mode) |
| MIDI catalog JSON | ~500 KB | 1 | No (for MIDI mode) |
| **Total (MP3 only)** | **~112 MB** | **26** | |
| **Total (with MIDI)** | **~137 MB** | **1,881** | |

GitHub Pages has a 1GB repository size recommendation and a 100MB per-file limit.
All files are well within these limits.

---

## MIDI Mode

When deployed with `--with-midi`, the app loads `audio/midi_catalog.json` on startup.
If the catalog loads successfully, a MIDI toggle appears in the player controls.

In MIDI mode:
- The browser's Web Audio API synthesizes MIDI files in real-time
- No server needed — everything runs client-side
- 16 mutation presets alter pitch, tempo, reverb, and filtering
- The 64×64 grid visualizes MIDI note events in real-time
- Infinite mode shuffles through 1,854 classical pieces endlessly

MIDI files are served as static files from the `midi/` directory.

---

## Provenance and Licensing

All 1,854 MIDI files represent public domain compositions (composers died before
1925). The MIDI sequences come from these sources:

| Source | License | Files |
|--------|---------|-------|
| ADL Piano MIDI | CC-BY 4.0 | 947 |
| narcisse-dev | Public domain sequences | ~400 |
| MAESTRO (Google Magenta) | CC BY-NC-SA 4.0 | ~50 |
| ASAP Dataset | CC BY-NC-SA 4.0 | ~20 |
| Nottingham Music Database | Public domain | 80 |
| Algorithmic (synthetic) | Public domain | ~30 |

Full attribution details are in `midi/ATTRIBUTION.md`.

The V8 Sessions album tracks are original compositions by aiphenomenon
(A. Johan Bizzle), generated by the In The Beginning radio engine.

---

## Troubleshooting

### Audio doesn't play
- Check browser console for CORS errors
- Ensure MP3 files are in the `audio/` directory relative to `index.html`
- Some browsers require user interaction before playing audio

### MIDI mode not available
- Ensure `midi_catalog.json` is in the `audio/` directory
- Check browser console for fetch errors
- Web Audio API requires a secure context (HTTPS or localhost)

### Grid doesn't light up
- Ensure the `*_notes_v3.json` files are present in `audio/`
- Check that `album_notes.json` references the correct filenames

### GitHub Pages shows 404
- Add a `.nojekyll` file to the repo root
- Wait a few minutes after pushing (Pages can take up to 10 minutes to deploy)
- Check that the branch and folder are correctly set in Settings → Pages

---

## Updating

To update the deployed app:

1. Make changes in the source `apps/cosmic-runner-v3/` directory
2. Rebuild: `python3 build.py --full`
3. Copy `dist/` contents to your Pages repo
4. Commit and push

The album MP3s rarely change, so you can skip copying them if only the code changed.
Just copy `dist/index.html` and any new JSON files.
