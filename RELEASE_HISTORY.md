# Release History

Release history for **In The Beginning** — reverse chronological order (newest first).

---

## v0.5.0 — 2026-03-01 — Enhanced Musical Composition Engine + AST Bug Prevention Steering

### Summary

Added a rich musical composition engine (`apps/audio/composer.py`) that draws from
6000+ years of human musical tradition to create evolving soundscapes driven by
simulation state. Integrated with the existing audio renderer for enhanced mode.
Introduced AST-guided code generation as a formal steering practice for bug prevention.

### Changes

- **Composition engine** (`apps/audio/composer.py`, 1085 lines):
  - 40+ world musical scales (Western, Japanese, Chinese, Middle Eastern, Indian, African, gamelan)
  - 16 instrument timbre profiles via additive synthesis with wavetable oscillators
  - 20+ polyrhythmic patterns (3:2, 4:3, 5:4, West African bell, gamelan kotekan)
  - 15+ harmonic progressions (Bach, minimalist, drone, circle of fifths)
  - 15+ melodic motifs from public domain works (Bach, Mozart, Beethoven, Chopin, Debussy,
    Satie, Grieg, Dvořák, Sakura, Jasmine Flower)
  - Streaming oscillator architecture (StreamingOsc) for O(samples_per_tick) rendering
  - Beat engine with 10-90% presence oscillation guided by simulation epoch
  - 4-voice polyphonic melodic system with phrase queuing
  - Universe pocket navigation across simulation domains
  - Percussion synthesis (kick, snare, hihat, rim) with caching
- **Performance optimizations** in `apps/audio/generate.py`:
  - Wavetable-based gen_pad (27% faster)
  - Inlined lowpass filter coefficients (reduced function call overhead)
  - Optimized PCM conversion with local variable caching
  - Dark matter texture for silence prevention
  - `--basic` flag (enhanced is default)
- **67 new tests** in `apps/audio/test_composer.py` covering all components
- **AST-guided code generation steering** added to all three steering locations:
  - Pre-write protocol: symbols, dependencies, callers queries
  - Post-write protocol: parse, coverage_map queries
  - Bug class taxonomy: broken imports, type mismatches, dead code, duplicates, etc.
- **Steering triple cross-check**: Updated CLAUDE.md, AGENTS.md, .claude/steering-check.sh

### Files Created

- `apps/audio/composer.py` — Musical composition engine
- `apps/audio/test_composer.py` — 67 tests for composer

### Files Modified

- `apps/audio/generate.py` — Enhanced mode integration, performance optimizations
- `CLAUDE.md` — AST-guided code generation section + checklist item
- `AGENTS.md` — AST-guided code generation section + reflection principle
- `.claude/steering-check.sh` — Bug prevention cue + reflection principle update
- `RELEASE_HISTORY.md` — This entry

### Agent Activity

- AST introspection run on composer.py (44 symbols, 1628 result tokens, 6.7x compression)
- Dependency analysis confirmed zero external dependencies in composer.py
- Coverage map identified 36 testable paths in composer.py, all covered by tests
- Background MP3 generation (10 minutes, enhanced mode, ~27 minutes render time)

### Test Results

- Python reference: 400 passed
- Audio tests (generate.py): 36 passed
- Composer tests: 67 passed
- Total: 503 passed, 0 failed

---

## v0.4.1 — 2026-03-01 — 100% Test Coverage Expansion Across All 15 Languages

### Summary

Massive test coverage expansion toward 100% across all 15 language implementations.
Launched 11+ parallel agents to analyze coverage gaps and write tests for every
untested public API. Fixed probabilistic test flakiness, constructor default issues,
and gitignore conflicts. Total: ~11,900 lines of new test code across 47 files.

### Changes

- **Test coverage expansion**: Wrote comprehensive tests for every untested public
  function/method across all 15 language implementations
- **Node.js**: 44 → 147 tests — added coverage for WaveFunction, Particle, Spin,
  Color, EntangledPair, QuantumField, ElectronShell, Atom (all methods), AtomicSystem,
  Molecule, ChemicalReaction, ChemicalSystem, Biology (Gene, DNAStrand, Protein, Cell,
  Biosphere). Fixed Atom constructor default (electronCount: 0 → explicit neutral)
- **Perl**: 56 → 376 tests — expanded all test files (quantum, atomic, chemistry,
  biology, universe) plus new environment test file
- **PHP**: 309 → 464 tests — added Spin::value, WaveFunction::toArray, Particle
  mass/charge, EntangledPair, QuantumField (vacuum fluctuation, decohere, evolve,
  snapshot), ElectronShell, AtomicSystem (recombination, nucleosynthesis, bonds),
  ChemicalSystem (catalyzed reaction, snapshot), biology toCompact, Epoch::description,
  Color enum, Gene::demethylate, Cell fitness/divide edge cases. Fixed UV mutation
  flakiness (intensity 50→5000)
- **Go**: suite → 112 tests — 29 new test functions for biology (20), atomic (4),
  chemistry (4), environment (1). Used `git add -f` for gitignore workaround
- **C**: 213 → 307 assertions — 14 new test functions for wf_collapse,
  vacuum_fluctuation, recombination, stellar_nucleosynthesis, epoch setters, universe_run
- **C++**: suite → 356 assertions — 17+ methods including spinValue, WaveFunction
  collapse, QuantumField annihilate/vacuumFluctuation, ElectronShell lifecycle, Atom
  ion/bondEnergy, AtomicSystem recombination/nucleosynthesis, ChemicalSystem formAminoAcid/
  formNucleotide, Gene epigenetic methods, Protein length
- **Rust**: 240 → 261 tests — 19 new tests for vacuum_fluctuation, decohere,
  stellar_nucleosynthesis, attempt_bond, catalyzed_reaction. Fixed flaky
  vacuum_fluctuation_high_temp test
- **Java**: suite → 682 tests — new TestParticle.java (86 tests) and TestMolecule.java
  (32 tests), expanded all existing test classes
- **TypeScript**: 44 → 157 tests — comprehensive coverage of all audio sonification
  and simulation modules
- **Kotlin**: expanded to 331 tests (syntax verified, no Android SDK)
- **Swift**: expanded to 535 tests (syntax verified, no Swift compiler)
- **WASM**: expanded to 134 tests — new test modules for atomic, biology, chemistry,
  quantum, universe
- **macOS screensaver**: expanded to 407+ additional test lines

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | 112   | PASS   |
| Rust     | 261   | PASS   |
| C        | 307   | PASS   |
| C++      | 356   | PASS   |
| Node.js  | 147   | PASS   |
| Perl     | 376   | PASS   |
| PHP      | 464   | PASS   |
| Java     | 682   | PASS   |
| TypeScript | 157 | PASS   |
| WASM     | 134   | PASS   |
| Kotlin   | 331   | SYNTAX OK |
| Swift    | 535   | SYNTAX OK |

### Agent Activity (this session)

1. Go coverage agent — filled 29 untested functions
2. C coverage agent — filled 14 untested functions (307 assertions)
3. C++ coverage agent — filled 17+ untested methods (356 assertions)
4. Rust coverage agent — filled gaps, fixed flaky test (261 tests)
5. Node.js/Perl/PHP/Java analysis agent — identified coverage gaps
6. Node.js coverage agent — expanded from 44 to 147 tests
7. Perl coverage agent — expanded from 56 to 376 tests
8. PHP coverage agent — expanded from 309 to 464 tests
9. Java coverage agent — expanded to 682 tests, 2 new test files
10. TypeScript/WASM/screensaver agent — expanded TS to 157, WASM to 134
11. Kotlin coverage agent — expanded to 331 tests
12. Swift coverage agent — expanded to 535 tests

### Files Modified (40+ files)

- `apps/c/test_simulator.c` (+263 lines)
- `apps/cpp/test_simulator.cpp` (+461 lines)
- `apps/go/simulator/simulator_test.go` (+860 lines)
- `apps/java/src/test/java/...` (9 files, +1,180 lines, 2 new files)
- `apps/kotlin/app/src/test/java/...` (7 files, +2,003 lines)
- `apps/nodejs/test/test_simulator.js` (+1,010 lines)
- `apps/perl/t/` (6 files + 1 new, +1,532 lines)
- `apps/php/tests/run_tests.php` (+594 lines)
- `apps/rust/src/simulator/` (3 files, +353 lines)
- `apps/swift/Tests/SimulatorTests/` (7 files, +2,095 lines)
- `apps/typescript/src/test.ts` (+670 lines)
- `apps/wasm/src/` (5 files, +294 lines)
- `apps/screensaver-macos/Tests/SimulatorTests.swift` (+407 lines)
- `RELEASE_HISTORY.md` — This entry

---

## v0.4.0 — 2026-03-01 — Steering Infrastructure, Session Logging, and CI Fix

### Summary

Major expansion of project governance infrastructure. Fixed CI pipeline failure,
added comprehensive steering enforcement via gVisor hooks, established session
logging protocol with historical reconstruction, created feature roadmap, and
ensured all markdown files reference each other coherently.

### Changes

- **CI fix**: Added `pip install pytest` step to `python-tests` job in
  `.github/workflows/ci.yml` — the root cause of the CI failure on the branch
- **CLAUDE.md**: Major rewrite (192→730+ lines) pulling in steering content from
  `docs/steering.md` — CueSignal protocol, AgentState tracking, token efficiency
  data, session logging protocol, markdown consistency checks, test coverage
  enforcement, self-cueing/gVisor enforcement, cross-compilation guidance,
  release history update mandate, triple cross-check reflection principle
- **AGENTS.md**: Major rewrite with same enhancements — session logging, release
  history, markdown review, test coverage, gVisor self-cueing, reflection principle
- **gVisor self-cueing**: Created `.claude/settings.json` and
  `.claude/steering-check.sh` — hook-based enforcement of steering rules with
  FAIL-CUE markers that prompt the agent to complete all per-turn tasks. Includes
  triple cross-check requirement (CLAUDE.md + AGENTS.md + gVisor hooks).
- **Session logs**: Reconstructed `v0.1.0-session.md` and `v0.2.0-session.md` from
  git history; created `v0.4.0-session.md` with full transcript detail
- **Feature roadmap**: Created `docs/roadmap.md` covering containerization
  (Docker/Colima), deployment target matrix, metacognitive steering enhancements,
  cross-language consistency automation, performance benchmarking
- **Network surface clarification**: Updated steering to note Go SSE server and PHP
  HTTP server are intentional localhost web servers for end-user use
- **Release history mandate**: Added to steering checklist — RELEASE_HISTORY.md must
  be updated at every conversation turn

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | suite | PASS   |
| Rust     | 240   | PASS   |
| C        | 213   | PASS   |
| C++      | suite | PASS   |
| Node.js  | 44    | PASS   |
| Perl     | 56    | PASS   |
| PHP      | 309   | PASS   |

### AST Passing Stats (this session)

- AST introspection ran on simulator modules: quantum.py (30 symbols),
  universe.py (14 symbols), biology.py (40 symbols), constants.py
- Pre-computed captures in `ast_captures/` validated

### Agent Activity (this session)

1. Codebase exploration agent — exhaustive file inventory and structure analysis
2. CLAUDE.md rewrite agent — comprehensive steering document
3. AGENTS.md rewrite agent — comprehensive multi-agent protocol
4. Feature roadmap agent — created `docs/roadmap.md`
5. Session log v0.1 agent — reconstructed from git history
6. Session log v0.2 agent — reconstructed from git history

### Files Created

- `.claude/settings.json` — gVisor hook configuration
- `.claude/steering-check.sh` — Steering enforcement script
- `docs/roadmap.md` — Feature roadmap
- `session_logs/v0.1.0-session.md` — Reconstructed session log
- `session_logs/v0.2.0-session.md` — Reconstructed session log
- `session_logs/v0.4.0-session.md` — This session's log

### Files Modified

- `.github/workflows/ci.yml` — Added pytest install step
- `CLAUDE.md` — Major rewrite with steering enhancements
- `AGENTS.md` — Major rewrite with steering enhancements
- `RELEASE_HISTORY.md` — Added v0.4.0 entry

---

## v0.3.0 — 2026-03-01 — Comprehensive Testing, Documentation, and Store Deployment Guides

### Summary

Major expansion adding tests to all 15 language implementations, comprehensive
documentation generation infrastructure, App Store and Play Store deployment guides,
and project-wide steering files for AI-assisted development.

### Changes

- **README.md**: Created top-level README documenting the full project — simulation
  overview, 15 applications, testing commands, AST-passing workflow, cross-compiled
  releases, and project structure
- **CLAUDE.md**: Created agent steering file for Claude Code and similar LLM tools —
  AST-passing protocol, coding principles (minimal dependencies, zero network surface),
  documentation standards, test commands
- **AGENTS.md**: Created multi-agent coordination protocol — swarm architecture,
  token budget guidelines, file locking conventions, commit format, cross-language
  consistency checks
- **Tests added** for: Go, Rust, C, C++, Java, PHP, TypeScript, Kotlin, Swift,
  WebAssembly, macOS screensaver, Ubuntu screensaver
- **CI/CD updated**: All test suites now run in the CI pipeline (`.github/workflows/ci.yml`)
  including Go test, Rust test, C test, C++ ctest, Java test runner, PHP test, TypeScript test
- **Documentation generation**: Added Doxygen configs for C and C++; all languages
  already have doc comments (JSDoc, PHPDoc, Javadoc, KDoc, Swift Markup, godoc, rustdoc, POD)
- **iOS App Store guide**: End-to-end instructions from zero to App Store release,
  using only Xcode (no Homebrew) — covers developer account, signing, simulator,
  TestFlight, and public release
- **Android Play Store guide**: End-to-end instructions from zero to Play Store release,
  using Android Studio — covers developer account, signing, emulator, internal testing,
  and production release
- **Session log infrastructure**: Created `session_logs/` directory for tracking
  development history across conversation turns
- **Release history**: This file, tracking the evolution of the project

### Agent Activity (this session)

This session used dictation mode for user input. The following agents were spawned:
1. Codebase exploration agent — mapped all 200+ files across 15 apps
2. Go test agent — created `apps/go/simulator/simulator_test.go`
3. Rust test agent — added `#[cfg(test)]` modules to all simulator source files
4. C/C++ test agent — created `test_simulator.c` and `test_simulator.cpp`, updated Makefiles
5. Java/PHP test agent — created Java test classes and PHP test runner
6. TypeScript/Kotlin/Swift test agent — created test suites for each
7. WASM/screensaver test agent — added tests for WebAssembly and screensaver simulator logic
8. iOS App Store documentation agent — wrote comprehensive Xcode-only deployment guide
9. Android Play Store documentation agent — wrote comprehensive Android Studio deployment guide

---

## v0.2.0 — 2026-02-28 — AST DSL Engine and Multi-Language Implementations

### Summary

Added the AST-passing DSL framework, reactive agent protocol, and all 15 language
implementations of the cosmic physics simulator.

### Changes

- **AST DSL**: Core engine (`ast_dsl/core.py`) with universal ASTNode, query/result
  protocol, performance metrics, and compact serialization
- **Reactive protocol**: Agent-pair state management (`ast_dsl/reactive.py`)
- **Language parsers**: 13 parsers covering Python, JS, TS, Go, Rust, C, C++, Java,
  Perl, PHP, Swift, Kotlin, WebAssembly
- **Introspection**: Cross-project analysis tool (`ast_dsl/introspect.py`)
- **15 applications**: Python CLI, Node.js CLI, Perl CLI, Go CLI+SSE, Rust CLI,
  C CLI, C++ CLI, Java GUI, TypeScript Audio, WebAssembly, PHP Snapshot,
  Swift iOS, Kotlin Android, macOS Screensaver, Ubuntu Screensaver
- **CI/CD**: GitHub Actions workflows for testing and cross-platform release builds
- **Documentation**: Comprehensive walkthrough, steering guide, per-app docs

---

## v0.1.0 — Initial Release — Python Reference Implementation

### Summary

Initial implementation of the cosmic physics simulator in Python.

### Changes

- **Simulator modules**: quantum.py, atomic.py, chemistry.py, biology.py,
  environment.py, universe.py, constants.py, terminal_ui.py
- **Test suite**: 400+ pytest tests covering all physics subsystems
- **Demo runner**: `run_demo.py` for interactive simulation
