# CLAUDE.md -- Project Steering

This file is the single source of truth for Claude Code CLI steering in this
repository. For multi-agent/AST protocol details, see `AGENTS.md`. For the
Web/iOS (gVisor) hook-based flow, see `docs/web-ios-flow.md`. For outstanding
work items, see `WORKLOG.md`.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Coding Principles](#coding-principles)
3. [CLI Hooks](#cli-hooks)
4. [Test Execution](#test-execution)
5. [Session Logging Protocol](#session-logging-protocol)
6. [Future Memories Protocol](#future-memories-protocol)
7. [Documentation Reference](#documentation-reference)
8. [Cross-Compilation](#cross-compilation)
9. [CI/CD](#cicd)
10. [File Structure](#file-structure)
11. [GitHub Pages Deployment](#github-pages-deployment)
12. [Web Application Modes](#web-application-modes)
13. [For Agentic Tools](#for-agentic-tools)

---

## Project Overview

**In The Beginning** is a multi-language cosmic physics simulator that models the
universe from the Big Bang through the emergence of life. It implements the same
simulation across 16 different applications and execution modes.

The Python implementation in `simulator/` is the reference. All other implementations
in `apps/` replicate its physics engine.

The project includes an **AST-passing architecture** (`ast_dsl/`) for AI-assisted
development -- see `AGENTS.md` for the full protocol specification.

---

## Coding Principles

### Minimal External Dependencies

All applications must minimize external dependencies:

| Language | Rule |
|----------|------|
| Python | stdlib only (no pip packages for the simulator) |
| Node.js | zero npm deps for simulator (devDependencies for tests OK) |
| Go | stdlib only |
| Rust | only `rand` crate |
| C/C++ | stdlib and POSIX only |
| Java | JDK standard library only |
| Perl | core modules only |
| PHP | no Composer dependencies |
| TypeScript | only `typescript` as devDependency |
| Swift | Foundation/SwiftUI/Metal only |
| Kotlin | AndroidX and Jetpack Compose (platform standard) |

Write everything from scratch using the language's native capabilities. If a feature
would normally require an external library, implement it from scratch or skip it.

### Zero Network Surface

The simulator applications have **no network surface**:
- No HTTP servers in the core simulator
- No outbound network calls, telemetry, or dynamic code loading
- Input is limited to CLI arguments and environment variables

**Intentional localhost servers**: The Go SSE server (`apps/go/cmd/server/`) and the
PHP snapshot server (`apps/php/`) are intentional localhost-only web servers for
end-user consumption. They are the only network-facing components.

### Code Quality Standards

- Every module must have corresponding tests
- Tests must be runnable without network access
- All public APIs must have doc comments in the language's standard format:
  Python (docstrings), JS/TS (JSDoc), Go (godoc), Rust (`///`), C/C++ (Doxygen),
  Java (Javadoc), Perl (POD), PHP (PHPDoc), Swift (`///` Markup), Kotlin (KDoc)

### Cross-Language Consistency

When a physics engine change is made in the Python reference, propagate the change
to all other language implementations. Use `tests/test_cross_language_parity.py` to
verify epoch transitions match.

---

## CLI Hooks

Claude Code CLI hooks in `.claude/settings.json` enforce key engineering practices
automatically. The hooks are in `.claude/hooks/` and fire at specific lifecycle
points. These complement the steering in this file — both the hooks and CLAUDE.md
should agree on what's expected.

### Hook Summary

| Hook | Event | What It Does | Blocking? |
|------|-------|-------------|-----------|
| `lint-on-write.sh` | PostToolUse (Edit/Write) | Python `py_compile`, JSON validation, JS `node --check` | No (feedback) |
| `pre-commit-plan-check.sh` | PreToolUse (Bash git commit) | Blocks commit if code changed but no future_memories plan exists | **Yes** (exit 2) |
| `post-bash-test-nudge.sh` | PostToolUse (Bash) | After build commands, reminds to run corresponding test suite | No (nudge) |
| `stop-check.sh` | Stop | Blocks stop if uncommitted changes, unpushed commits, or missing session log | **Yes** (exit 2) |
| `session-start.sh` | SessionStart | Injects branch, plan, session log, and dirty-tree status | No (context) |

### Hook-Enforced Practices

These practices are enforced by hooks **and** expected by this steering file:

1. **Lint every write**: Python files must pass `py_compile`, JSON files must be
   valid. Fix syntax errors immediately — the hook output shows the error.

2. **Plan before code commits**: A `future_memories/v{VERSION}-plan.md` must exist
   before committing source code changes. Doc-only commits (session logs, markdown)
   are exempt. Write the plan, commit it, then start coding.

3. **Commit before stopping**: The Stop hook blocks if there are uncommitted or
   unpushed changes. Always commit logical units of work and push to remote before
   ending a conversation turn.

4. **Session log every turn**: The Stop hook checks for a session log in
   `session_logs/`. Generate one before the conversation ends.

5. **Test after building**: After build commands (cargo build, go build, make,
   npm run build), run the corresponding test suite. The hook reminds; follow through.

### Commit and Push Cadence

- Commit at every significant milestone, not just end of turn
- Push future_memories plans and large commits immediately
- Push code changes at intervals of roughly every 15-20 minutes
- The Stop hook enforces that nothing is left uncommitted or unpushed at turn end

---

## Test Execution

### Per-Language Commands

```bash
# Python (reference) — fast (~2s), run after every edit
python -m pytest tests/ -v --tb=short

# Node.js
node --test apps/nodejs/test/test_simulator.js

# Go
cd apps/go && go test ./...

# Rust
cd apps/rust && cargo test

# C
cd apps/c && make test

# C++
cd apps/cpp && mkdir -p build && cd build && cmake .. && make && ctest

# Java
cd apps/java && javac -d build/test-classes -cp build/classes \
  src/test/java/com/inthebeginning/simulator/*.java && \
  java -cp build/classes:build/test-classes \
  org.junit.runner.JUnitCore com.inthebeginning.simulator.AllTests

# Perl
prove -v apps/perl/t/

# PHP
cd apps/php && php tests/run_tests.php

# TypeScript
cd apps/typescript && npm test

# Kotlin (unit tests, no Android device required)
cd apps/kotlin && ./gradlew test

# Swift (requires Swift 5.9+ toolchain)
cd apps/swift && swift test

# Audio composition engine
python -m pytest apps/audio/ -v
```

### Integration & Golden Tests

```bash
# Golden output tests (build + run all CLI apps, compare to snapshots)
python -m pytest tests/test_golden_outputs.py -v

# Cross-language parity
python -m pytest tests/test_cross_language_parity.py -v

# Server smoke tests (Go SSE + PHP)
python -m pytest tests/test_server_smoke.py -v

# Visualizer golden tests
python -m pytest tests/test_visualizer_golden.py -v

# Audio golden tests
python -m pytest tests/test_audio_golden.py -v

# Deploy asset validation
python -m pytest tests/test_deploy_assets.py tests/test_deploy_app_flows.py -v

# Screen capture tests
python -m pytest tests/test_screen_capture.py -v

# Regenerate golden snapshots (after changing simulator output)
python tools/capture_golden.py
```

### Test Coverage

- Run the Python reference suite after every edit
- Run language-specific tests for any language where code was modified
- Use `coverage_map` AST queries to identify untested code paths (see `AGENTS.md`)
- When physics engine changes are made, verify cross-language parity

---

## Session Logging Protocol

Session logs provide continuity between agent sessions and an audit trail of work.

### File Naming

- Session log: `session_logs/v{VERSION}-session.md`
- Journal (active): `session_logs/v{VERSION}-journal.json`
- Journal (finalized): `session_logs/v{VERSION}-journal.json.tar.gz`

### Content Requirements

Each session log entry must include:
- What was requested, what was done, outcome
- Test results (pass/fail summary)
- Files created, modified, or deleted
- Timestamps in dual format: `YYYY-MM-DD HH:MM CT (HH:MM UTC)`
- Reference to the finalized journal tar.gz

### Turn-by-Turn Journal Protocol

Every conversation turn is logged to a rolling journal file that captures the
full conversation text and all tool calls verbatim.

#### Per-Turn Write

After every assistant response, write/update `session_logs/v{VER}-journal.json`
with the current turn appended. This happens before any other end-of-turn work.
The journal file must always reflect the latest completed turn.

Contents per turn:
- `user_input.raw`: Verbatim user text (security-redacted only)
- `user_input.proofread`: Typo/grammar-corrected version
- `assistant_text`: Full verbatim assistant response text as shown on screen —
  includes markdown tables, reasoning, status updates, etc. Never use bracketed
  summaries like `[did X]`. No length cap.
- `tool_calls[]`: Every tool invocation with verbatim parameters and output.
  Include process/reasoning commands verbatim (git status, git log, git diff
  --stat, ls, validation runs, etc.). Exclude raw patch content from `git diff`
  that only shows code changes already captured in the repo — the diff stat
  (file list + line counts) is sufficient for those.
- `files_modified`, `files_read`: File access log for the turn

#### Truncation

Per tool call result: if output exceeds **500 lines or 60,000 characters**,
keep the first **100 lines or 12,000 characters** (whichever limit hits first).
Append a truncation marker with original size and brief description of remaining
content. This applies uniformly to all tools (Bash, Read, Agent, Grep, etc.).
Within Agent subagent results, individual command outputs follow the same rule.

#### Redaction

Replace API keys, tokens, passwords, and non-project emails with
`<REDACTED:type>`. Do not redact system paths, git SHAs, filenames, or
project structure.

#### Cuts and Version Bumps

A cut occurs at each solution milestone (logical completion of a version).
Each cut bumps the solution version number (v37 -> v38). On cut:

1. Populate the journal's `cut` field with version, commit SHAs, and summary
2. The finalized `v{VER}-journal.json` stays **prettified and uncompressed**
   (human-readable on GitHub)
3. Compress **all** prior uncompressed journals:
   `for f in session_logs/v*-journal.json (excluding v{VER}):`
   `tar czf $f.tar.gz $f && rm $f`
4. Update each compressed journal's session log link to point to `.tar.gz`
5. Write `v{VER}-session.md` referencing `v{VER}-journal.json` (uncompressed)
6. Update `RELEASE_HISTORY.md` with the version entry
7. Commit and push

At any point in time, only the **latest** cut's journal is uncompressed.
All prior cuts are compressed to `.tar.gz`. This keeps the most recent
journal browsable on GitHub while saving space for older ones.

#### Schema

Defined in `session_logs/journal_schema.json` (format version 2.0).
Historical files under `transcript_schema.json` (v1) are unchanged.

### Rolling Window & Append-Only

- Keep the 3 most recent session logs as raw markdown files
- Compress older logs into `session_logs/archive.tar.gz`
- Session logs are append-only per turn -- do not rewrite historical entries

---

## Work Tracking

`WORKLOG.md` is the master list of outstanding work items, organized by facet:
Cosmic Runner (game bugs, audio/instruments), Testing Infrastructure,
Architecture, Steering/Hooks, Simulator, Deploy.

### Protocol

- Check `WORKLOG.md` at session start to understand current priorities
- Update `WORKLOG.md` when items are completed or new items discovered
- Mark items with status: Open, In Progress, Done, Blocked
- Reference WORKLOG items in commit messages where applicable

### Local-First Testing

Run tests locally before pushing to avoid burning GitHub CI minutes:

```bash
# Python reference (fast, ~2s) — run after every edit
python3 -m pytest tests/ -v --tb=short

# Note data completeness (fast, <1s)
python3 -m pytest tests/test_note_data_completeness.py -v

# Deploy asset validation
python3 -m pytest tests/test_deploy_assets.py tests/test_deploy_app_flows.py -v
```

Only push when local tests pass. The CI pipeline is the final gate, not the
first line of defense.

---

## Future Memories Protocol

The `future_memories/` directory contains plan files written before and during
implementation. They serve as restoration context if a session is interrupted.

### Workflow

1. Before starting significant work, write a plan to `future_memories/v{VERSION}-plan.md`
2. Commit and push the plan file before proceeding with code changes
3. Update the plan file at significant milestones
4. After a version ships, archive the plan into `future_memories/archive.tar.gz`

### Release History

Update `RELEASE_HISTORY.md` with a version entry documenting changes made during
each work session.

---

## Documentation Reference

### Key Documents

| File | Description |
|------|-------------|
| `docs/steering.md` | AST reactive protocol -- full CueSignal specification |
| `docs/walkthrough.md` | Architecture walkthrough -- simulator structure, physics |
| `docs/apps_overview.md` | Overview of all 16 application implementations |
| `docs/build_guide.md` | Cross-platform build instructions |
| `docs/ast_passing_efficiency.md` | Token efficiency metrics and benchmarks |
| `docs/ast_introspection.md` | AST self-introspection module guide |
| `docs/roadmap.md` | Feature roadmap and planned work |
| `docs/music_algorithm.md` | Radio engine: physics simulation to music |
| `docs/ios_app_store_guide.md` | iOS App Store publishing guide |
| `docs/android_play_store_guide.md` | Google Play publishing guide |
| `docs/web-ios-flow.md` | Claude Code Web/iOS hook-based flow (gVisor) |

### Per-Language AST Documentation

`docs/python_ast.md`, `docs/go_ast.md`, `docs/nodejs_ast.md`, `docs/java_ast.md`,
`docs/rust_ast.md`, `docs/cpp_ast.md`, `docs/perl_ast.md`, `docs/php_ast.md`,
`docs/wasm_ast.md`, `docs/typescript_ast.md`, `docs/swift_ast.md`, `docs/kotlin_ast.md`

---

## Cross-Compilation

Compilable programs (Go, Rust, C, C++) must be buildable for multiple targets.
See `.github/workflows/release.yml` for the full cross-compilation matrix.

### Per-Language Build Commands

- **Go**: `GOOS=<os> GOARCH=<arch> go build -o <output> ./cmd/simulator/`
- **Rust**: `cargo build --release --target <target-triple>`
- **C/C++**: Platform-specific Makefiles / CMake with appropriate toolchain files

### Swift on Linux

The Swift simulator library (`apps/swift/InTheBeginning/Simulator/*.swift`) uses only
`Foundation` and `Observation` -- both available on Linux via swift-corelibs (Swift 5.9+).

**Linux-compatible** (7 files): `Constants.swift`, `QuantumField.swift`,
`AtomicSystem.swift`, `ChemicalSystem.swift`, `Biosphere.swift`, `Environment.swift`,
`Universe.swift`

**Apple-only** (6 files): `App.swift`, `SimulationView.swift`,
`EpochTimelineView.swift`, `SettingsView.swift`, `MetalRenderer.swift`,
`AudioEngine.swift` -- require SwiftUI, MetalKit, or AVFoundation.

On macOS: use `xcodebuild` or `swift build` via Xcode CLI tools (no Homebrew).

---

## CI/CD

Tests run on every push and PR via `.github/workflows/ci.yml`. The release workflow
(`.github/workflows/release.yml`) cross-compiles binaries for Go, Rust, C, and C++
across Linux/macOS/Windows when a version tag is pushed.

Ensure all tests pass before committing. The CI pipeline is the source of truth.

---

## File Structure

```
simulator/           Python reference implementation
apps/
  nodejs/            Node.js CLI
  go/                Go CLI + SSE server
  rust/              Rust CLI
  c/                 C CLI
  cpp/               C++ CLI
  java/              Java GUI (Swing)
  perl/              Perl CLI
  php/               PHP snapshot server
  typescript/        TypeScript audio sonification
  kotlin/            Kotlin Android (Jetpack Compose)
  swift/             Swift iOS (SwiftUI + Metal)
  wasm/              WebAssembly (Rust -> wasm-bindgen)
  screensaver-macos/ macOS screensaver (Swift + Metal)
  screensaver-ubuntu/ Ubuntu screensaver (C + X11)
  audio/             Audio composition engine (Python)
  cosmic-runner-v5/  V5 game source (development copy)
deploy/
  shared/            Shared assets for GitHub Pages
    audio/
      tracks/        12 album MP3s + note event JSONs
      midi/          1,771 MIDI files (120 composers) + catalog
      instruments/   60 instrument sample MP3s
      metadata/v1/   Album + MIDI catalog metadata
      interstitials/ Radio station ID MP3
  v5/                V5 deploy-ready apps (game + visualizer)
  v6/                V6 deploy-ready app (game only)
ast_dsl/             AST parsing and transformation engine
ast_captures/        Pre-computed AST snapshots for reference
tests/               Python test suite
docs/                Architecture documentation
session_logs/        Per-turn session and transcript logs
future_memories/     Verbose plan files for session restoration
.github/workflows/   CI/CD pipelines
.claude/             Claude Code settings and CLI hooks
  hooks/             Hook scripts (lint, plan check, stop check, etc.)
```

---

## GitHub Pages Deployment

The `deploy/` directory is structured for **zero-build-step deployment** to GitHub
Pages. Simple filesystem copies followed by `git add`, `git commit`, `git push` --
no build scripts, no bundlers.

### Repository Layout

```
<gh-pages-root>/
  shared/                              Shared assets (one copy, all versions use it)
    audio/
      tracks/                          12 album MP3s + per-track notes JSON files
      metadata/v1/                     album.json + midi_catalog.json
      interstitials/                   "In The Beginning Radio" station ID MP3
      midi/                            MIDI files organized by composer (Bach/, ...)
      instruments/                     60 instrument sample MP3s
  v5/
    inthebeginning-bounce/             Game (vanilla JS, no bundler)
    visualizer/                        Visualizer (5 modes)
  v6/
    inthebeginning-bounce/             Game (v6, no visualizer)
```

### Asset Manifest

| Category | Location | Count | Size |
|----------|----------|-------|------|
| Album MP3s | shared/audio/tracks/ | 12 | ~84MB |
| Note events | shared/audio/tracks/ | 12 | ~1.2MB |
| MIDI files | shared/audio/midi/ | 1,771 | ~25MB |
| Instruments | shared/audio/instruments/ | 60 | ~2.5MB |
| Game JS | v5/inthebeginning-bounce/js/ | 16 | ~200KB |
| Visualizer JS | v5/visualizer/js/ | 9 | ~100KB |

**Total deploy size**: ~200MB (dominated by album MP3s)

### Shared Folder Strategy

All version folders reference `../../shared/audio/` via relative paths -- adding a
new version does not duplicate the ~110MB of shared audio assets.

JS apps try local paths first (`audio/`), then shared paths (`../../shared/audio/`),
so they work both standalone and deployed.

`midi_catalog.json` is placed in `shared/audio/midi/` alongside the MIDI files so
JavaScript base URL derivation produces correct paths for loading individual files.

When to update shared assets:
- New album tracks or re-renders: update `shared/audio/tracks/`
- New MIDI files: update `shared/audio/midi/` + regenerate catalog
- New instrument samples: update `shared/audio/instruments/`
- Schema changes: create `shared/audio/metadata/v2/` (never modify v1)

### Copy-and-Push Workflow

```bash
cp -r deploy/shared/ /path/to/gh-pages-repo/shared/
cp -r deploy/v5/ /path/to/gh-pages-repo/v5/
cd /path/to/gh-pages-repo && git add . && git commit -m "deploy v5" && git push
```

### MP3 ID3 Tag Standard

| Tag | Value |
|-----|-------|
| Title (TIT2) | Track name (e.g., "Ember") |
| Artist (TPE1) | A. Johan Bizzle |
| Album (TALB) | inthebeginning |
| Track (TRCK) | N/12 |
| Year (TDRC) | 2026 |
| Genre (TCON) | Electronic |
| Copyright (TCOP) | Copyright 2026 aiphenomenon |
| License (TXXX:LICENSE) | CC BY-SA 4.0 |

### MIDI Catalog Metadata

`midi_catalog.json` contains composer name/era, source collection, license, file
count and size for each MIDI file. Displayed in the MIDI info panel in both game
and visualizer.

---

## Web Application Modes

### Cosmic Runner (inthebeginning-bounce)

Three display modes and three sound modes:

#### Display Modes

| Mode | Description |
|------|-------------|
| **Game** | Runner/dodge game. 2D at early levels, transitions to 3D at track 7. LEFT/RIGHT moves runner. Scoring: 3 pts jump-over, 1 pt hit. |
| **Player** | Music player. Full-screen visualization with album art colors. No game scoring. |
| **Grid** | 64x64 color grid synchronized to music. 2D and 3D views. |

#### Sound Modes

| Mode | Description |
|------|-------------|
| **MP3 (Album)** | 12-track album via HTML5 Audio. Interstitial every 4 tracks. |
| **MIDI Library** | Random shuffle from 1,800+ classical MIDIs. In-browser synthesis. 16 mutation presets. |
| **Synth Generator** | Procedural music generation. Style sliders for speed, arpeggio, chord density, note bending. |

#### Game Engine Design

- **Terrain is traversable**: Runners physically go up/down hills. Ground Y at
  runner's X determines foot position. Terrain from layered sine waves.
- **Lane-based spawning**: Obstacles in discrete lanes (3-7 per level). Jitter
  prevents robotic feel.
- **Auto 2D to 3D at track 7**: Manual toggle sets `_user3DOverride`.
- **Progressive difficulty**: Terrain complexity, lane count, and spawn rate
  increase with level. Multi-obstacle spawns start at level 3.
- **Valley depth clamping**: Prevents stuck-in-valley situations.

#### Progressive Difficulty

| Level | Terrain | Lanes | Notes |
|-------|---------|-------|-------|
| 0 | Nearly flat | 3 | Gentle intro |
| 1-3 | Rolling hills | 3 | Pronounced hills at 2-3 |
| 4-5 | Dramatic terrain | 4 | Deeper valleys |
| 6-7 | 3D transition | 4-5 | Auto-switch to 3D |
| 8+ | Full 3D | 5-7 | Rich terrain, fast spawns |

### Visualizer

Standalone music visualization with five modes: Album, MIDI, Synth, Stream (SSE),
Single (drag-and-drop). Same music engine as the game.

### Music Engine Principles

- **Album mode**: 12-track, 60-minute release. Notes JSON drives visualization.
- **MIDI mode**: In-browser Web Audio synthesis. 16 mutation presets. C2-C7 range.
- **Synth mode**: Procedural via MusicGenerator. Same pipeline as MIDI/MP3.
- **Interstitials**: "In The Beginning Radio" station ID every 4 tracks.

### Architecture Evolution Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03 | Traversable terrain in 2D | Runners physically go up/down hills |
| 2026-03 | Lane-based obstacle spawning | Strategic dodging, natural progression |
| 2026-03 | Auto 2D to 3D at track 7 | First 6 tracks teach mechanics in 2D |
| 2026-03 | Valley depth clamping | Prevent stuck-in-valley |
| 2026-03 | Shared assets in deploy/shared/ | One copy of MP3s/MIDIs for all versions |

---

## For Agentic Tools

When working on this repository with any automated agent (Jules, Codex, Devin, etc.):

1. **Run tests after every change**: `python -m pytest tests/ -v --tb=short` (~2s)
2. **Cross-language consistency**: Physics changes must be reflected in all languages
3. **No new dependencies**: Implement from scratch or skip
4. **No network code**: No HTTP/socket/telemetry in simulator binaries
5. **Test isolation**: No inter-test deps, no network, no external filesystem state
6. **Review roadmap**: Check `docs/roadmap.md` before proposing new features
7. **Session logging**: Generate logs in `session_logs/` per the protocol above
8. **AST-first development**: See `AGENTS.md` for the AST-passing protocol
9. **Markdown consistency**: Periodically verify all markdown files are accurate
   and consistent with actual code/config state. Apply factual corrections only
   — don't rewrite steering intent during cleanup. Session logs are append-only
   (never modified). Use `markdown_sweep_tracker.json` to track sweep progress.
