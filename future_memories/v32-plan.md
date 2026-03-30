# V32 Plan — Comprehensive Game Bug Fixes + Feature Polish

## Date: 2026-03-29

## Overview

Massive bug fix and feature polish pass based on detailed user testing of V9.
Covers gameplay mechanics, audio integration, UI/UX, WASM fixes, and new features.

## Critical Bugs (P0)

1. **MP3 404s**: deploy/v9 has JSON note files but no MP3 tracks. Need to either
   include MP3s or ensure paths resolve to shared/ assets correctly.
2. **Grid mode starts game mode**: Selecting Grid on title screen doesn't honor it.
3. **Canvas negative radius error**: `arc()` called with negative radius causing
   green tinting, flickering, and Donnie Darko wormhole effect on emoji.
4. **WASM mode broken**: AudioWorklet import error (`__wbg_log` not a Function),
   DataView expects ArrayBuffer got Uint8Array.
5. **Pause+play synth noise**: Pressing pause then play in synth mode causes
   a flurry of noise.
6. **Mutation switching**: Jumping playhead, sometimes breaks playback entirely.

## Gameplay Fixes (P1)

7. Player movement speed: too fast in 2D, slightly fast in 3D.
8. 3D objects pause at bottom: should fly through, player jumps over them.
9. Jump scoring: only 3pts once per jump landing, not per object mid-air.
10. 2D/3D: respect user choice, auto-switch at level 7 but honor manual toggle.
11. Terrain tracking: runners should follow manifold edge, not bounce randomly.
12. 2-player controls: P1=WASD+Space, P2=arrows/numpad/vim. 1P=all keys.
13. Infinite mode: enforce 12-song limit when unchecked.

## UI/UX Fixes (P1)

14. HUD buttons swipeable on mobile (horizontal scroll).
15. 2D/3D buttons disabled in music player mode.
16. Correct HUD buttons per mode (no +/- in music, etc).
17. Double pause button icon.
18. Music player: no 2-player option on title screen.
19. Theme colors not applied (stars work, colors don't).
20. Music stops on refresh/restart.
21. Track name click: useful modal for all modes.
22. Controls Guide: correct per player count and mode.
23. +/- speed buttons work in MP3 mode.
24. Level transition animation (CSS repaint between levels).
25. Grid 3D: cube shapes for cells.
26. Title font: "inthebeginning" smaller, "bounce" bigger, space-themed.

## Audio Fixes (P1)

27. MIDI licensing display in music/grid mode.
28. MP3 sourcing info (which MIDIs were sampled for each section).
29. Synth speed < 1.3x: gaps/no notes. Fix minimum tempo.
30. MIDI soundbank: use with instrument selection panel.
31. Minimize window: keep MIDI playing (Web Audio vs HTML5 Audio).

## New Features (P2)

32. CREDITS screen: licenses, sources, attribution, repo link.
33. WASM fixes: AudioWorklet compat, DataView, Firefox support.

## Infrastructure

34. Reinstate apps/ as primary dev location, deploy/ as dist copy.
35. Ensure relative paths to shared/ assets work.
36. Linting for all languages in CI hooks.
37. Playwright regression testing for all fixes.
38. Visual report with before/after screenshots.
39. Follow all steering: future memories, session logs, release history.
40. GitHub Pages deployment instructions.

## Phase 2: Complete All Remaining Items (2026-03-30)

### Round 2 Fixes
1. 3D objects fly-through (not pause at bottom)
2. Jump scoring: 3pts once per jump landing, not per-object mid-air
3. Runner terrain manifold smoothing
4. Infinite mode enforcement for MIDI/synth (12-track limit when unchecked)
5. Double pause button icon investigation
6. Track name click → useful modal for all modes
7. Level transition animation (CSS)
8. Grid 3D cube shapes
9. Title font: split sizing + space-themed
10. MIDI licensing display
11. MP3 sourcing info (which MIDIs sampled)
12. MIDI soundbank instrument selection panel
13. Minimize window MIDI playback
14. Mutation playhead jumping fix
15. Arpeggio/runs in MIDI investigation
16. Controls Guide per player count
17. Accessibility settings edge cases
18. WASM Firefox fallback
19. Linting for all languages in hooks
20. Reinstate apps/ as primary dev location
