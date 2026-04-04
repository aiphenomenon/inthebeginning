# V45 Plan: Testing Infrastructure + GM Verification + WORKLOG Expansion

## Date: 2026-04-04

## Context

V44 established work tracking scaffolding. V45 builds the real testing
infrastructure: PulseAudio virtual audio sink for real audio capture,
Playwright browser E2E tests with spectral analysis, targeted test execution
strategy, GM instrument verification, WASM verification, and WORKLOG expansion
to cover all 22+ apps.

## Key Findings

- **GM mapping already complete**: synth-engine.js has GM_PROGRAM_TO_SAMPLE
  (128 programs -> 60 MP3 samples with pitch shifting)
- **WASM binary exists** (40KB) in apps/inthebeginning-bounce/ and deploy v8-v11
- **WASM quality gap**: Only 13 additive timbres vs JS's 60 real MP3 samples
- **apps/cosmic-runner-v5/ is STALE** — latest code is apps/inthebeginning-bounce/
  which matches deploy/v11/ exactly (verified via checksums)
- **No audio system installed** — PulseAudio available via apt
- **Existing Playwright test** (tests/test_web_game.mjs, 543 lines) uses raw
  playwright API, not @playwright/test

## Deliverables

### Testing Infrastructure
1. PulseAudio virtual audio sink (tools/audio-sink.sh)
2. Playwright E2E test suite using @playwright/test:
   - tests/e2e/playwright.config.mjs
   - tests/e2e/fixtures.mjs (server, audio capture, spectral analysis)
   - tests/e2e/game.spec.mjs (full game flow coverage)
   - tests/e2e/audio.spec.mjs (audio verification per sound mode)
   - tests/e2e/wasm.spec.mjs (WASM load + synthesis verification)
3. Pytest integration: conftest.py, pytest.ini, test_e2e_browser.py
4. Targeted test execution: tools/quick-test.sh

### GM + WASM Verification
- Verify GM instruments work in MIDI mode via E2E audio tests
- Verify WASM binary loads and produces audio
- Document WASM quality gap (13 timbres vs 60 samples)
- Enqueue WASM parity with Python music generation as future work

### WORKLOG Expansion
- Add sections for all 22+ apps
- Enqueue discovered bugs from E2E testing
- Enqueue WASM-to-Python music parity work item

### Documentation
- Visual test report with screenshots (pass/fail evidence)
- CLAUDE.md updated with test tier documentation
- CI workflow updated with E2E test job

## Source Code Note

apps/cosmic-runner-v5/ is a stale sync copy. The canonical game source is:
- Source: apps/inthebeginning-bounce/ (latest)
- Deploy: deploy/v11/inthebeginning-bounce/ (matches source)
- Test against deploy/v11/ (has correct shared asset relative paths)
