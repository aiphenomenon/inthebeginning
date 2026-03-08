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

- [ ] Phase 0 committed
- [ ] Wave 1 agents launched (1-3)
- [ ] Wave 2 agents launched (4-5)
- [ ] Engine code merged
- [ ] Album rendered
- [ ] Visualizer built
- [ ] All tests pass
- [ ] V21 released and pushed
