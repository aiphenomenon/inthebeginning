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
- [x] Agents complete (all 5 delivered)
- [x] Governor merge + reconciliation (ea94c48)
- [x] Engine code verified (pytest: 295+62 pass)
- [x] Streaming agent (Agent 6) complete (e77d535)
- [x] 30-min MP3 render complete (v21_random_759274.mp3)
- [ ] Album render in progress (seed 779275, 17 tracks)
- [ ] Test suite (Agent 8) — radio engine tests running
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

### 11:00 CT — All 5 agents completed, merged (ea94c48)
- 26 files changed, 5660 insertions
- Major deliverables: docs audit, music_algorithm.md, steering updates,
  album engine + vocoder + note logging, JS visualizer

### 11:02 CT — Push-after-commit steering update (bd38526)
- Added to CLAUDE.md item 11, AGENTS.md item 10, steering-check.sh item 17

### 11:10 CT — Context window compressed, session resumed
- 295 core tests pass (4.18s), 62 music engine tests pass (21.47s)
- 30-min MP3 complete: v21_random_759274.mp3 (41MB, 1800s, 192kbps)
- Session log + RELEASE_HISTORY updated (1ecd18c)

### 11:25 CT — Album duration bug fix
- Each mood was [42,84,126,168,210]s → fixed to 42s quantum
- Also fixed randint(lo,hi) edge case when lo > hi
- Commits: 69a5749, 580ad04

### 11:27 CT — Album render started (seed 779275)
- 17 tracks, 4746s target, sequential rendering
- Vocoder bookends generating

### 11:30 CT — Streaming infrastructure complete (e77d535)
- Go SSE: /events/notes + /stream/audio endpoints
- Bash scripts: start_radio.sh, start_album_player.sh
- Go server builds OK

### 11:37 CT — Album Track 1 "Bright Signal" complete (f94254b)
- 2.8 min, 3.9MB, 361 notes, Epochs: Earth, Inflation, Planck, Quark
- Render: 270s for 168s audio = 1.6x realtime

### 11:48 CT — Album Track 2 "Stellar Filament" complete (0239f3c)
- 3.5 min, 4.8MB, 822 notes, Epochs: Earth, Hadron, Present, Solar System
- Render: 484s for 210s audio = 2.3x realtime (CPU contention from test processes)

### 11:48-ongoing — Track 3 rendering
- 4.9 min audio, 7 moods, Epochs: Electroweak, Inflation, Planck, Present, Star Formation
- 3 CPU-intensive processes competing: album render + 2 radio engine test runs (240 tests)
- Test suite runs (2,143+ pass across 10 languages, audio tests still running)
- Estimated album completion: ~1:00-1:30 PM CT based on current render rate

### Timing constraints (UPDATED 12:05 CT from user screenshot)
- Session started: 10:24 CT
- **Session budget**: 18% used, resets ~1:01 PM CT (58 min from 12:03 CT)
- **Weekly budget**: 3% used (plenty of headroom)
- After session reset at ~1:01 PM CT, we get a fresh session allowance
- Album render is a background OS process — continues regardless of LLM budget
- **Critical**: Commit and push each track as it completes (failsafe)
- All tracks 1-3 already committed and pushed
- Track 4 rendering now (294s audio, started ~12:04 CT)

### Failsafe: If session budget exhausted before album finishes
1. Album render continues as background process (PID 1182)
2. All completed tracks are committed and pushed
3. Future memory plan describes what remains
4. After session reset (~1:01 PM CT), resume by:
   a. Check `ls apps/audio/output/album/*.mp3` for completed tracks
   b. `git add` and commit any uncommitted tracks
   c. Check if render process still alive: `ps -p 1182`
   d. If render complete, finalize session log and version cut
   e. If render still running, continue monitoring

### Album render process details
- PID: 1182 (python3 AlbumEngine) — **TERMINATED** (session/container reset)
- Seed: 779275
- Tracks: 17 total, **3 completed** (tracks 1-3 committed and pushed)
- Output dir: apps/audio/output/album/
- Note logs: per-track *_notes.json + album_notes.json (after all done)
- Also running: 2 pytest processes (radio engine tests, PID 48408 + 52199) — **TERMINATED**

### 12:30 CT — Turn 2 (session resumed after context compression)
- Album render background process terminated — only 3/17 tracks completed
- Test processes also terminated
- All prior work committed and pushed (latest: e718533)
- Added Session Budget Management facility to triple-check steering:
  - CLAUDE.md: new section with screenshot analysis protocol, pause thresholds, crash resilience
  - AGENTS.md: steering checklist item 15 + triple cross-check entry
  - steering-check.sh: FAIL-CUE item 25
- Committed and pushed (2735add)

### 14:44 CT — Turn 3 (session resumed after context compression)
- Tracks 1-11 had completed, tracks 10-11 uncommitted (MCP code-sign crash)
- Committed tracks 10-11 (a75c3fe) and pushed
- Restarted parallel render for tracks 12-17 (PID 4967)
- 15:25 CT: All 17 tracks complete, auto-committed and pushed
- 15:30 CT: Generated album_notes.json (904KB, 8626 events), committed (976981c)

### Album — COMPLETE
- **"In The Beginning Phase 0"** — 19 tracks, 79.4 min, 110MB
- All tracks committed and pushed to `claude/resume-v9-document-v8-6yhAe`
- Seed: 779275, deterministically reproducible

### Remaining work
- [x] Album render complete (all 17 tracks + bookends)
- [x] Album notes JSON generated
- [ ] Re-run radio engine tests
- [ ] Final session log and JSON transcript update
- [ ] Version cut and push
