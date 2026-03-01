# Release History

Release history for **In The Beginning** — reverse chronological order (newest first).

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
