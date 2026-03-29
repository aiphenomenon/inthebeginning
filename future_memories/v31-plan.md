# V31 Plan — Web Game & Visualizer Bug Fixes + Approach C Hybrid Audio

## Date: 2026-03-29

## Overview

Systematic bug hunting and fixing across the web game (inthebeginning-bounce) and
visualizer, plus beginning Approach C hybrid audio enhancements (WASM for sample-level
synthesis, JS for scheduling/structure, Web Audio for effects).

## Context

- User's prior session (PDF pages 448-453) analyzed three approaches to close the gap
  between Python radio engine and browser audio. User chose **Approach C: Hybrid**.
- Deploy versions: v5 (game+visualizer), v6 (game only), v7 (world music), v8 (WASM synth)
- Latest deploy is v8 with 4 sound modes: MP3, MIDI, Synth, WASM
- Visualizer exists in v5 but was dropped from v6+

## Phase 1: Testing Infrastructure (Playwright + Local Server)
- Install Playwright, Chromium, and dependencies
- Set up local HTTP server to serve deploy/v5/ and deploy/v8/
- Create automated test scripts that exercise all modes
- Screenshot every mode combination

## Phase 2: Bug Discovery
- Test all 3 display modes × 3-4 sound modes
- Test keyboard controls in each mode
- Test mode switching mid-playback
- Test track navigation (prev/next)
- Test mutation switching in MIDI mode
- Test 2D/3D toggle
- Test responsive layout
- Test the visualizer (deploy/v5/visualizer/)
- Document all bugs found

## Phase 3: Bug Fixes
- Fix each discovered bug
- Ensure fixes propagate to all deploy versions (v5, v6, v7, v8)
- Run tests after each fix

## Phase 4: Approach C Enhancements (if time permits)
- Enhance WASM synth: vibrato, FM synthesis, note coloring
- Enhance JS music generator: rondo patterns, consonance engine, scale expansion
- Wire Web Audio DSP chain: reverb, filters, compression

## Phase 5: Verification
- Re-run all Playwright tests
- Screenshot all modes post-fix
- Update session log and release history
