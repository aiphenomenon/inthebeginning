# V19 Future Memories — Test Infrastructure Overhaul

## Session Context
- **Date**: 2026-03-07 13:25 CT (19:25 UTC)
- **Branch**: claude/resume-v9-document-v8-6yhAe
- **Session window**: ~2.5 hours remaining (ends ~15:55 CT)
- **Timer**: Background self-cueing at 15:45 CT (warning) and 15:55 CT (final)

## What We're Building

Comprehensive test infrastructure overhaul across all 16 apps. The project has
4,500+ unit tests but zero golden output tests, zero cross-language parity tests,
zero server smoke tests, and zero audio fingerprint tests.

## Plan (11 Phases)

### Phase 1: Golden Output Test Framework (tests/test_golden_outputs.py)
- Pytest-based framework that captures CLI stdout and compares to golden snapshots
- Supports all CLI apps: Python, Node.js, Go, Rust, C, C++, Perl, PHP, Java, TypeScript
- Uses deterministic seed (42) for reproducible output
- Tolerant comparison (ignores timestamps, memory addresses)

### Phase 2: Golden Snapshot Capture Tool (tools/capture_golden.py)
- Script to regenerate golden snapshots for all apps
- Stores in tests/golden_snapshots/<lang>/output.txt
- Detects available toolchains automatically

### Phase 3: Capture Initial Golden Snapshots
- Run all available CLI apps with --seed=42
- Store baseline outputs

### Phase 4: Cross-Language Parity Tests (tests/test_cross_language_parity.py)
- Parse simulation output from multiple languages
- Compare epoch transitions, particle counts, final state
- Tolerance-based comparison for floating-point values

### Phase 5: Server Smoke Tests (tests/test_server_smoke.py)
- Go SSE server: start, HTTP GET, verify SSE stream, kill
- PHP snapshot server: start, HTTP GET, verify JSON response, kill

### Phase 6: Audio Engine Golden Tests (tests/test_audio_golden.py)
- Verify WAV generation produces consistent output
- Duration/sample-rate validation
- Spectral fingerprint comparison (basic)

### Phase 7: CI Integration (.github/workflows/golden.yml)
- Workflow that runs golden tests on push
- Matrix: available languages only
- Artifact upload for golden snapshots

### Phase 8: Full Test Suite Run + Fix Failures
- Run all existing tests + new golden tests
- Fix any failures

### Phase 9: Documentation Updates
- Update CLAUDE.md test execution section
- Update docs/apps_overview.md
- Add tests/README.md

### Phase 10: AST Captures Regeneration
- Regenerate ast_captures/ at end of session

### Phase 11: Final Commit & Push

## Key Constraints
- No Swift toolchain available (skip Swift tests)
- No external dependencies (stdlib only)
- MP3 audio (never MP4)
- Deterministic seeds for reproducibility
- All tests must work offline

## User Notes
- User will check back occasionally
- Version is v19 (not v9 — branch name is legacy)
- User noted Silero domains for future TTS work (not this session)
