# V23 Plan: Cosmic Runner V8 Album + Three-Mode Player

**Created**: 2026-03-21 17:26 CT (22:26 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe

## Overview

User wants to create a new version of Cosmic Runner that:
1. Merges two favorite MP3s (`cosmic_radio_v8.mp3` and `cosmic_radio_v18_v8-42.mp3`) into a 12-track album
2. Splits at natural silence boundaries into 3-6 minute tracks
3. Names tracks with nature words symbolizing universe evolution (different from current album names)
4. Has JSON note metadata for synchronized visualization
5. Supports three modes of operation:
   - **Music Player**: standalone audio player only
   - **Game Mode**: side-scroller game with subdued cells covering background + stars
   - **Grid Mode**: 64x64 cell grid visualization only (cells synchronized to music)
6. Easy to copy to GitHub Pages repository

## Source MP3 Strategy

### cosmic_radio_v8.mp3 (30 min)
- Generated with `RadioEngineV8(seed=42, total_duration=1800)`
- V8 engine: orchestral layering (~75% multi-instrument, ~25% solo)
- Anti-hiss filtering, subsonic removal, note quantization
- 70% simple time signatures
- Commit: 88a543d

### cosmic_radio_v18_v8-42.mp3 (30 min)
- Generated with `RadioEngineV15_V8Tempo(seed=42, total_duration=1800)` from generate_v18_mp3s.py
- V15 synthesis (pure-Python V8 synthesis via factory.synthesize_colored_note)
- V8 tempo range (1.5x-2.5x)
- Commit: 13b5b1c

### Strategy: Re-render with NoteLog
Since we need JSON note metadata, we must RE-RENDER both engines with NoteLog enabled,
then split the rendered audio into 12 tracks at low-energy boundaries.

## 12 Track Names (Nature + Universe Evolution)

1. **Ember** — Big Bang ignition
2. **Torrent** — Rapid expansion
3. **Quartz** — First matter crystallization
4. **Tide** — Cosmic flow/waves
5. **Root** — Stellar nucleosynthesis foundations
6. **Glacier** — Dark age cooling
7. **Bloom** — First stars ignite
8. **Dusk** — Dark energy emergence
9. **Coral** — Complex structure formation
10. **Moss** — Life's beginnings
11. **Thunder** — Energetic cosmic events
12. **Horizon** — Looking forward

## Cosmic Runner Three Modes

### Mode 1: Music Player (standalone)
- Album track list, play/pause, skip, seek, volume
- No game elements, no canvas
- Clean UI focused on music

### Mode 2: Game Mode
- Side-scroller with Aki character
- Subdued 64x64 cells covering entire background
- Stars parallax
- Obstacles, jumping, blasting
- Music plays, cells react to notes

### Mode 3: Grid Mode
- Full 64x64 grid visualization
- Cells at full opacity, synchronized to music
- No game elements
- Just music + visual grid

### Mode Switching
- Tab/button bar to switch between modes
- State preserves (music continues when switching)
- Keyboard shortcut: 1/2/3 to switch modes

## File Structure

```
apps/cosmic-runner-v2/
  index.html
  css/
    styles.css
  js/
    app.js          # Main controller, mode switching
    background.js   # Grid + starfield rendering
    game.js         # Game engine
    runner.js       # Aki character
    obstacles.js    # Obstacle system
    music-sync.js   # Note data loading/sync
    player.js       # Audio player
  audio/
    album_notes.json
    01-Ember.mp3
    01-Ember_notes.json
    ...
    12-Horizon.mp3
    12-Horizon_notes.json
  dist/
    index.html      # Bundled single-file version
```

## Implementation Steps

1. Create album generation script (`apps/audio/generate_v8_album.py`)
2. Re-render V8 and V18-V8 engines with NoteLog
3. Split into 12 tracks at silence boundaries
4. Generate per-track MP3 + JSON note files
5. Build new Cosmic Runner with three-mode architecture
6. Test all modes
7. Update docs
