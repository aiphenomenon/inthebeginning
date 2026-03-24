# V29 Plan — V7 Deploy: Full Python Music Port + Bug Fixes

**Created**: 2026-03-23 21:07 CT (02:07 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Scope**: Port Python composer.py music generation to JavaScript, fix V6 bugs, create V7 deploy

## User Context

User asked to:
1. Fix all previously identified issues (V28 remaining items)
2. Fully port Python music generation code to JavaScript for robust synthetic music
3. Make deploy folder easy to copy to GitHub Pages
4. This becomes V7

## What Python Has That JavaScript Lacks

### Scales (30+ in Python → 11 in JS)
- Missing: Japanese (hirajoshi, in_sen, iwato, yo, miyako_bushi)
- Missing: Chinese (gong, shang, jue, zhi, yu)
- Missing: Middle Eastern (hijaz, bayati, rast, saba, nahawand) — bayati/rast have quarter-tones
- Missing: Indian ragas (bhairav, yaman, malkauns, bhairavi, todi)
- Missing: African (equi_pent, mbira, kora)
- Missing: Ancient (drone, tetrachord, slendro, pelog)
- Missing: Western modes (locrian, harmonic_minor, melodic_minor, blues, etc.)

### Harmonic Progressions (15 in Python → 0 in JS)
- I_V_vi_IV, I_IV_V, i_VII_VI_V, circle_of_fifths, bach_cmaj
- glass_1, glass_2, riley_rainbow (minimalist)
- tanpura, didgeridoo, bagpipe (drone)
- parallel_4ths, parallel_5ths (East Asian)
- aeolian_drift, phrygian_pulse, lydian_float (modal)

### Rhythmic Patterns (20+ in Python → random in JS)
- West African bell (gahu, agbadza, ewe_bell)
- Polyrhythmic (3:2, 4:3, 5:4, 5:3, 7:4)
- Gamelan interlocking (kotekan)
- Minimalist phasing (Steve Reich)
- Indian tala (teen_taal, jhaptaal)
- Sparse/ambient patterns

### Melodic Motifs (30+ in Python → 0 in JS)
- Bach (prelude, cello suite), Mozart (nachtmusik, turca)
- Beethoven (elise, 5th, moonlight), Chopin, Debussy, Satie, Grieg, Dvořák
- Traditional (sakura, jasmine, raga patterns, African call-response, mbira)
- Pentatonic (rise, fall, wave)

### Humanization
- Python adds timing jitter; JS is perfectly metronomic

### Time Signatures
- Python has 11 types (4/4, 3/4, 6/8, 5/4, 7/8, etc.); JS has none

### Epoch-to-Music Mapping
- Python maps each epoch to specific scale families, rhythm families,
  progression styles, and motif pools; JS uses hardcoded per-epoch data

## Bug Fixes (V28 Remaining Items)

1. Modal close-on-click-outside (track list, help, etc.)
2. Audio crunchiness after extended playback (Web Audio buffer management)
3. Two-player vanishing (deep root cause)
4. Player pinned to right edge

## Implementation Plan

### Phase 1: Port Python data tables to JavaScript music-generator.js
- All 44 scales from SCALES dict
- All 15 progressions from PROGRESSIONS dict
- All 20+ rhythm patterns from RHYTHM_PATTERNS dict
- All 30+ motifs from MOTIFS dict
- Epoch-to-scale, epoch-to-rhythm, epoch-to-progression, epoch-to-motif mappings
- Time signature system

### Phase 2: Enhance generation algorithms
- Replace random chord layer with progression-based chord changes
- Replace random percussion with structured rhythm patterns
- Replace random-walk melody with motif-based phrases
- Add humanization (timing jitter ±10ms)
- Add time signature grouping

### Phase 3: Fix V6 bugs
- Click-outside-to-close for modals
- Audio context management for crunchiness
- Two-player state management
- Player position edge case

### Phase 4: Create deploy/v7
- Copy from v6, apply all changes
- Ensure shared asset paths work
- .nojekyll
- README

### Phase 5: Test and commit

## Key Files
- deploy/v6/inthebeginning-bounce/js/music-generator.js (primary target)
- deploy/v6/inthebeginning-bounce/js/app.js (bug fixes)
- deploy/v6/inthebeginning-bounce/js/synth-engine.js (may need updates)
- apps/audio/composer.py (source of truth for music data)
