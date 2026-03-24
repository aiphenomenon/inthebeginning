# V28 Plan — Game Overhaul: Bug Fixes, Rich Synth, Remove Visualizer

**Created**: 2026-03-23 20:02 CT (01:02 UTC)
**Branch**: claude/resume-v9-document-v8-6yhAe
**Scope**: Major bug fix + feature enhancement session for the web game

## User Context

User provided extensive speech-to-text feedback after testing the game. Key themes:
1. Many bugs in current V5 game (branding, modals, playback, 2-player, 3D mode)
2. Synth generator music is too sparse — needs richer audio engine
3. Visualizer is redundant — remove it, focus on game
4. This becomes V6 deploy (new deploy/v6/ directory)
5. No player lives / game over from lives — game ends after 12 album tracks
6. Infinite play for album repeat, MIDI shuffle, synth generator
7. ~5 hour task estimated by user

## Bug Fixes Required

### Critical Bugs
1. **Branding**: "COSMIC RUNNER" → "inthebeginning bounce" (no spaces in "inthebeginning")
2. **Theme overlay**: Not opening from home screen buttons
3. **Accessibility overlay**: Not opening from home screen buttons
4. **MIDI playback**: Playhead starts mid-track, doesn't auto-play on start
5. **Synth playback**: Doesn't auto-play in grid mode
6. **Pause**: Only pauses gameplay, not music — should pause both
7. **Player pinned right**: Jumping to far right pins player to edge
8. **Two-player vanishing**: Players disappear after appearing (state accumulation)
9. **Two-player controls**: WASD should be P1, right-side keys for P2
10. **3D mode**: Not activating at level 7+ in MIDI/Synth modes
11. **3D obstacles**: Piling up at bottom instead of flying past player
12. **Note info**: Not showing in grid/player modes when accessibility checked
13. **Track list modal**: Shows empty rounded rectangle in synth/grid mode
14. **Modal close**: Can't click outside track list modal to close it
15. **Audio crunchiness**: Audio artifacts after extended playback

### Feature Additions
1. **Rich synth engine**: Port Python audio patterns to JavaScript
2. **Infinite play**: Album repeat, MIDI infinite shuffle, synth infinite
3. **Game completion**: End screen after 12 album tracks (non-infinite mode)
4. **Theme visual impact**: Theme colors should affect game visuals more
5. **Better P1/P2 control documentation**: Clear key mapping display

### Architecture Changes
1. **Remove visualizer**: Delete deploy/v5/visualizer/ equivalent from v6
2. **Create v6 deploy**: New deploy/v6/inthebeginning-bounce/
3. **Update all docs**: CLAUDE.md, README, deploy docs, etc.

## Implementation Order

### Phase 1: Quick Bug Fixes (branding, modals, overlays)
- Fix title text in index.html
- Fix theme/accessibility overlay event binding
- Fix modal close-on-click-outside
- Fix empty track list in synth/grid mode
- Fix pause to also pause/resume music

### Phase 2: Playback Fixes (MIDI, synth, auto-play)
- Fix MIDI playhead starting at beginning
- Fix auto-play on game start for MIDI/synth
- Fix audio context resume issues

### Phase 3: Game Mechanics Fixes
- Fix player right-side pinning
- Fix two-player mode vanishing
- Fix P1/P2 key bindings (P1=arrows/WASD, P2=numpad/IJKL)
- Fix 3D mode activation across all sound modes
- Fix 3D obstacle cleanup (fly past, don't pile up)
- Fix note info display

### Phase 4: Rich Synth Engine
- Enhance music-generator.js with richer patterns
- Add more complex harmony, rhythm, and texture
- Port key patterns from Python audio engine

### Phase 5: Infinite Play + Game Completion
- Implement album track repeat in infinite mode
- Ensure MIDI infinite shuffle works correctly
- Add game completion screen after track 12
- Level progression in MIDI/synth modes

### Phase 6: Theme Enhancement + Polish
- Make theme colors affect more game elements
- Audio artifact cleanup
- General polish

### Phase 7: Deploy + Documentation
- Create deploy/v6/ directory structure
- Remove visualizer
- Update all documentation
- Run tests
- Final commit and push

## Completion Status [2026-03-23 20:31 CT (01:31 UTC)]

### Completed
- **Phase 1-3**: All bug fixes applied to v5 source, copied to v6
- **Phase 4**: Synth generator enriched (12 epochs, 9 audio layers)
- **Phase 5**: Infinite play + game completion implemented
- **Phase 6**: Theme-aware ground rendering
- **Phase 7**: V6 deployed, visualizer removed, docs updated, tests written

### Test Results
- **766 passed, 2 skipped** — full test suite, no regressions
- **151 passed** — deploy tests (v5 + v6 assets, paths, flows)

### Remaining Items (for future sessions)
- Audio crunchiness investigation (may need Web Audio buffer management)
- Two-player vanishing deep root cause (try/catch safety added, needs browser testing)
- Player pinned-right edge case (NaN protection added, needs gameplay testing)
- Modal close-on-click-outside (may need overlay click handler)

## Key Files

- deploy/v5/inthebeginning-bounce/index.html — HTML structure
- deploy/v5/inthebeginning-bounce/js/app.js — Main controller (1181 lines)
- deploy/v5/inthebeginning-bounce/js/game.js — Game engine (538 lines)
- deploy/v5/inthebeginning-bounce/js/player.js — Audio player (568 lines)
- deploy/v5/inthebeginning-bounce/js/runner.js — Runner physics (252 lines)
- deploy/v5/inthebeginning-bounce/js/obstacles.js — Obstacles (383 lines)
- deploy/v5/inthebeginning-bounce/js/renderer3d.js — 3D renderer (401 lines)
- deploy/v5/inthebeginning-bounce/js/music-generator.js — Synth music (806 lines)
- deploy/v5/inthebeginning-bounce/js/synth-engine.js — Audio engine (905 lines)
- deploy/v5/inthebeginning-bounce/js/midi-player.js — MIDI playback (647 lines)
- deploy/v5/inthebeginning-bounce/js/music-sync.js — Music sync (439 lines)
- deploy/v5/inthebeginning-bounce/js/config.js — Config (85 lines)
- deploy/v5/inthebeginning-bounce/css/styles.css — Styles
