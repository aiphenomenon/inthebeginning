# V47 Plan: WASM Overhaul + Playhead Testing + Mobile WORKLOG

## Date: 2026-04-05

## Context
Making WASM mode truly work with Python-quality audio. Hybrid approach:
MusicGenerator composes notes (44 scales, 12 epochs, 25 rhythms), JS
SampleBank plays them with 60 real MP3 instrument samples. Grid/gameplay
visualization driven by note events — same pipeline as Synth mode.

## Deliverables
1. Bug #6: WASM HUD fix (empty track info, 0:00 time)
2. Bug #7: Clean raw instrument names in note info display
3. #10: GM instruments in WASM (wire program_change bridge)
4. #13: WASM music parity (hybrid JS+WASM with real samples)
5. T4: Playhead seeking tests across all modes
6. Mobile/tablet viewport tests (iPhone 16, iPad)
7. New WORKLOG items (Firefox/WebKit, 2P touch, 3D movement, etc.)
8. Deploy v12 with verified paths

## Architecture: Hybrid JS+WASM
MusicGenerator (composition) → note events → SynthEngine/SampleBank
(60 MP3 instruments) + Grid/Game (visualization). WASM mode uses
this same pipeline. WASM AudioWorklet for additive synthesis layer.
