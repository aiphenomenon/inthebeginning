# V21 Plan — "In The Beginning Phase 0"

**Created**: 2026-03-08 10:31 CT (15:31 UTC)
**Status**: IN PROGRESS
**Branch**: claude/resume-v9-document-v8-6yhAe

## Objectives

1. **Documentation audit**: Cross-reference all markdown against actual source code, fix gaps
2. **JSON transcript logging**: New steering rule — companion `.json` alongside `.md` session logs
3. **Music algorithm doc**: `docs/music_algorithm.md` — accessible description of radio engine
4. **Steering triple-check**: Update CLAUDE.md, AGENTS.md, steering-check.sh with JSON rules
5. **Album generation**: "In The Beginning Phase 0" — full CD-length album (79 min, 16-18 tracks)
6. **Vocoder pitch projection**: Musical note superimposition on TTS (50% of spoken segments)
7. **Note event logging**: JSON visualization data exported during renders
8. **JavaScript visualizer**: 64×64 grid player with three modes (album, 30-min, stream)
9. **Streaming enhancements**: Go SSE server note events, bash scripts, audio-only URL
10. **New 30-min MP3**: V20 engine, random seed
11. **Version cut**: V21

## Agent Architecture

- Agent 1: Documentation Audit (worktree)
- Agent 2: Steering & JSON Transcript System (worktree)
- Agent 3: Music Algorithm Documentation (worktree)
- Agent 4: Album Engine + Vocoder + Note Logging (worktree)
- Agent 5: JavaScript Visualizer (worktree)
- Agent 6: Streaming Infrastructure (worktree)
- Agent 7: MP3 Renders (album + 30-min)
- Agent 8: Test Suite
- Governor: Main agent coordination

## Timer Protocol

- Start: 10:24 CT
- Pause: 12:44 CT (2h20m)
- Resume: 12:59 CT
- Checkpoint commits every ~20 minutes
- Future memory updated at each checkpoint

## Album Specification

- Album: "In The Beginning Phase 0"
- Artist: "aiphenomenon (A. Johan Bizzle)"
- Target: 79 min 6 sec (113 moods × 42s = 4746s)
- Tracks: 16-18 (each 3-7 moods)
- Genre: Psychedelic Rock (ID3 genre 67)
- License: CC BY-SA 4.0
- Vocoder bookends: "In the beginning" spoken with MIDI pitch projection
- Source code readings: ~7 across album (once per ~10 min)
- Each mood: random universe epoch
- ID3v2.3 metadata on all tracks

## Key Decisions

- System paths OK in JSON logs (not sensitive)
- Redact only: security tokens, personal user info
- JSON truncation: ≤500 lines verbatim, >500 → first 100 + summary
- Player controls colorized to match grid color scheme
- Truly random seeds for all MP3s
- Per-track JSON score files (not embedded — too large for album)

## Milestones

- [x] Phase 0 committed (10:32 CT)
- [x] Wave 1 agents launched — all 5 agents (1-5) running in parallel (10:34 CT)
- [ ] Agents complete — awaiting results
- [ ] Governor merge + reconciliation
- [ ] Engine code verified (pytest)
- [ ] Streaming agent (Agent 6) launched
- [ ] MP3 renders (Agent 7): 30-min + album
- [ ] Test suite (Agent 8)
- [ ] All tests pass
- [ ] V21 released and pushed

## Progress Log

### 10:32 CT — Phase 0 committed and pushed
- Created future memory plan, session log, JSON transcript
- Commit 00d4a88

### 10:34 CT — Wave 1 launched (5 agents in parallel worktrees)
- Agent 1 (add6878a): Documentation audit
- Agent 2 (ad510742): Steering & JSON transcript
- Agent 3 (a8cdd66a): Music algorithm doc
- Agent 4 (a9dec08d): Album engine + vocoder + note logging
- Agent 5 (ab0f8fae): JavaScript 64×64 grid visualizer

### 11:16 CT — All agents active, large writes in progress
- Agent 1: 379 output lines, actively auditing docs
- Agent 2: 202 lines, large CLAUDE.md/AGENTS.md write
- Agent 3: 110 lines, writing music_algorithm.md
- Agent 4: 233 lines, building album engine code
- Agent 5: 63 lines, creating visualizer app files
- Random seed for 30-min MP3: 759274

### 11:30 CT — 30-min MP3 render started (seed 759274)
- V20 engine, background process, ~15-20 min to complete
- Memory usage: ~5GB (streaming render), 15GB free

### 11:42 CT — All agents still active in large write operations
- Agent 1: 533 lines, in large write (near completion)
- Agent 2: 202 lines, sustained large write
- Agent 3: 110 lines, sustained large write
- Agent 4: 292 lines, actively generating album engine code
- Agent 5: 85 lines, creating multi-file JS app
- MP3 render: actively running (99% CPU)
- Checkpoint commit 4a9853b pushed
