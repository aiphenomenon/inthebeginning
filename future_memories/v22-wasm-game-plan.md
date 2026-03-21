# V22 Plan — Unified WASM Music Player + Side-Scroller Game

## Created: 2026-03-21 CT

## Context

User requested (via speech-to-text on iPhone) a unified WebAssembly application that
bundles everything into a single deployable package for GitHub Pages:

1. The existing 64x64 grid visualizer
2. The album music (MP3s from "In The Beginning Phase 0")
3. A new 8-bit side-scroller game mode

The game is a fun, casual, unkillable side-scroller where an ASCII creature runs and
jumps to the music. The character morphs at each musical epoch/mood transition.

## Architecture Plan

See detailed plan below.

## Status

- [ ] Phase 1: Core infrastructure
- [ ] Phase 2: Game engine
- [ ] Phase 3: WASM bundling
- [ ] Phase 4: Testing
- [ ] Phase 5: Polish and deploy
