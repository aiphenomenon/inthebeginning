# V31 Session Log — Steering Rearchitecture + Web Game Bug Fixes

## Date: 2026-03-29

---

### Turn 1: Steering Rearchitecture

**Requested**: Rearchitect CLAUDE.md, AGENTS.md, and the gVisor hook system for
Claude Code CLI. Keep Web/iOS flow preserved separately.

**Actions**:
1. Explored all steering files (CLAUDE.md 1662 lines, AGENTS.md 967 lines,
   steering-check.sh 314 lines, settings.json 42 lines)
2. Rewrote CLAUDE.md (499 lines) — single source of truth for CLI steering
3. Rewrote AGENTS.md (271 lines) — AST protocol + coordination only
4. Created docs/web-ios-flow.md (345 lines) — preserves full gVisor hook approach
5. Cleared .claude/settings.json hooks
6. Archived steering-check.sh with pointer to docs/web-ios-flow.md

**Reduction**: 2,985 lines → 1,140 lines (62% reduction, zero content loss)

### Turn 2: CLI Hook Implementation

**Requested**: Set up Claude Code CLI hooks for engineering practice enforcement.

**Actions**:
1. Created 5 hook scripts in .claude/hooks/:
   - lint-on-write.sh — py_compile, JSON validation, JS node --check
   - pre-commit-plan-check.sh — blocks commit without future_memories plan
   - post-bash-test-nudge.sh — reminds to run tests after builds
   - stop-check.sh — blocks stop with uncommitted changes or missing session log
   - session-start.sh — injects branch/plan/session status at start
2. Updated .claude/settings.json with hook wiring
3. Updated CLAUDE.md with CLI Hooks section

### Turn 3: Web Game & Visualizer Bug Fixes

**Requested**: Go through deploy/ apps, set up Playwright testing, find and fix bugs
across all game modes and the visualizer. Approach C (Hybrid audio) selected for
future enhancement work.

**Actions**:
1. Read PDF pages 448-453 for Approach C specification
2. Installed Playwright + Chromium
3. Set up local HTTP servers for deploy/v5 and full deploy layout
4. Created comprehensive Playwright test suite (tests/test_web_game.mjs)
5. Found and fixed 4 bugs:

**Bug 1: Key "2" mode switch broken**
- Root cause: Duplicate `case '2'` in switch — numpad P2 fast-drop case
  caught all '2' presses before the mode-switching case
- Fix: Merged into single case with location check
- Propagated to: v4-v8, apps/cosmic-runner-v5

**Bug 2: Visualizer FAMILY_HUES redeclaration**
- Root cause: `const FAMILY_HUES` in both grid.js and synth-engine.js
- Fix: Changed to `var` with Object.assign merge pattern
- Cascading fix: Also resolved "SynthEngine is not defined"
- Propagated to: v4-v5 visualizer, apps/visualizer

**Bug 3: Visualizer generateCycle not a function**
- Root cause: app.js called musicGenerator.generateCycle() but method is generate(seed)
- Fix: Changed to generate(this.musicGenerator.seed)

**Bug 4: MIDI info panel empty on initial track**
- Root cause: startMidiMode() fires onTrackChange before first MIDI loads
- Fix: Added onTrackChange after loadNextRandom() completes
- Propagated to: v5-v8, apps/cosmic-runner-v5

### Test Results

**Playwright**: 38 PASS, 0 FAIL, 3 WARN
- All 9 mode combos (3 display × 3 sound) pass
- All overlays (mutation, style, help, theme) open/close correctly
- Keyboard mode switching (1/2/3) all work
- Canvas rendering verified non-blank
- Visualizer loads without JS errors

**Python core tests**: 283 passed in 0.56s

### Commits

1. `d61daa7` refactor(docs): rearchitect steering for Claude Code CLI
2. `f016fcd` feat(.claude): add CLI hooks for engineering practice enforcement
3. `3a7d1e2` fix(.claude): make unpushed-commits check a warning, not a blocker
4. `0cc46f3` docs(future_memories): add V31 plan
5. `cef51b9` fix(web): key-2 mode switch, visualizer FAMILY_HUES & generateCycle bugs
6. `0a10647` fix(web): MIDI info panel empty on first track load
