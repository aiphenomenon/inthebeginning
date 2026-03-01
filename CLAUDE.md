# CLAUDE.md — Agent Steering for In The Beginning

This file provides steering instructions for Claude Code, Claude Agent SDK agents,
and similar LLM-based coding assistants working on this repository.

## Project Overview

**In The Beginning** is a multi-language cosmic physics simulator that models the
universe from the Big Bang through the emergence of life. It implements the same
simulation across 15 different programming languages and execution modes.

The Python implementation in `simulator/` is the reference. All other implementations
in `apps/` replicate its physics engine.

## AST-Passing Workflow

This project uses an **AST-passing architecture** to minimize context window usage
when AI agents work on the codebase. Instead of passing raw source files back and
forth, agents exchange compact AST representations.

### How It Works

1. **Parse phase**: The `ast_dsl/` module parses source files into a universal
   `ASTNode` tree. Each language has a dedicated parser (e.g., `python_ast.py`,
   `go_ast.go`, `node_ast.js`).

2. **Compact representation**: `ASTNode.to_compact()` produces a minimal string
   representation (e.g., `FunctionDef:evolve@49[args=self,dt]{...}`) that conveys
   structure, names, and locations without full source text.

3. **Query interface**: `ASTEngine.execute(ASTQuery)` supports actions:
   - `parse` — full AST of a file
   - `find` — search by node type or name
   - `symbols` — extract all definitions
   - `dependencies` — extract imports
   - `callers` — find call sites
   - `metrics` — cyclomatic complexity, node counts
   - `coverage_map` — identify testable paths
   - `transform` — rename, extract, inline

4. **Performance tracking**: Every query returns `PerformanceMetrics` with wall time,
   CPU time, memory usage, and approximate token counts so agents can budget context.

5. **Agent loop**: An agent requests a compact AST of a file, reasons about it,
   requests targeted sub-trees or transformations, and emits edits — never needing
   the full file in context unless writing new code.

### Token Budget Guidelines

- Prefer `to_compact()` over `to_dict()` for initial exploration (5-10x smaller).
- Use `depth` parameter on queries to limit tree depth.
- Request `symbols` before `parse` to decide which files need full analysis.
- Use `coverage_map` to target test generation without parsing entire files.

## Coding Principles

### Minimal External Dependencies

All applications must minimize external dependencies:
- **Python**: stdlib only (no pip packages for the simulator)
- **Node.js**: zero npm dependencies for the simulator (devDependencies for tests OK)
- **Go**: stdlib only
- **Rust**: only `rand` crate
- **C/C++**: stdlib and POSIX only
- **Java**: JDK standard library only
- **Perl**: core modules only
- **PHP**: no Composer dependencies
- **TypeScript**: only `typescript` as devDependency
- **Swift**: Foundation/SwiftUI/Metal only
- **Kotlin**: AndroidX and Jetpack Compose (platform standard)

### Security — Zero Network Surface

The simulator applications have **no network surface**:
- No HTTP servers in the core simulator (the Go SSE server is a separate binary)
- No outbound network calls
- No telemetry or analytics
- No dynamic code loading from external sources
- No file system access outside the project directory
- Input is limited to CLI arguments and environment variables

If adding new features, do not introduce network listeners or outbound connections
to the simulator binaries. The Go SSE server (`cmd/server/`) is the only intentional
network-facing component.

### Code Quality Standards

- Every module must have corresponding tests.
- Tests must be runnable without network access.
- All public APIs must have documentation comments in the language's standard format:
  - Python: docstrings (Google style)
  - JavaScript/TypeScript: JSDoc (`/** ... */`)
  - Go: godoc comments
  - Rust: `///` doc comments
  - C/C++: Doxygen (`/** ... */`)
  - Java: Javadoc (`/** ... */`)
  - Perl: POD (`=head1`, `=cut`)
  - PHP: PHPDoc (`/** ... */`)
  - Swift: `///` doc comments (Swift Markup)
  - Kotlin: KDoc (`/** ... */`)

## Test Execution

Run the full test suite:

```bash
# Python (reference)
python -m pytest tests/ -v

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
cd apps/java && javac -d build/test-classes -cp build/classes src/test/java/com/inthebeginning/simulator/*.java && java -cp build/classes:build/test-classes org.junit.runner.JUnitCore com.inthebeginning.simulator.AllTests

# Perl
prove -v apps/perl/t/

# PHP
cd apps/php && php tests/run_tests.php

# TypeScript
cd apps/typescript && npm test

# Kotlin (unit tests, no Android device required)
cd apps/kotlin && ./gradlew test

# Swift (unit tests)
cd apps/swift && swift test
```

## CI/CD

Tests are run on every push and PR via `.github/workflows/ci.yml`. The release
workflow (`.github/workflows/release.yml`) cross-compiles binaries for Go, Rust,
C, and C++ across Linux/macOS/Windows when a version tag is pushed.

Ensure all tests pass before committing. The CI pipeline is the source of truth.

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
  wasm/              WebAssembly (Rust→wasm-bindgen)
  screensaver-macos/ macOS screensaver (Swift + Metal)
  screensaver-ubuntu/ Ubuntu screensaver (C + X11)
ast_dsl/             AST parsing and transformation engine
ast_captures/        Pre-computed AST snapshots for reference
tests/               Python test suite
docs/                Architecture documentation
.github/workflows/   CI/CD pipelines
```

## For Agentic Tools (Jules, Codex, Devin, etc.)

When working on this repository with an automated agent:

1. **Start with AST introspection**: Run `python -c "from ast_dsl.core import ASTEngine; e = ASTEngine(); print(e.find_symbols('simulator/quantum.py').to_compact())"` to get a symbol map before reading files.

2. **Run tests after every change**: `python -m pytest tests/ -v --tb=short` is fast (~2s). Run it after every edit.

3. **Cross-language consistency**: Changes to the physics engine in one language should be reflected in all languages. Use the AST DSL to compare symbols across implementations.

4. **No new dependencies**: Do not add external packages. If a feature requires a library, implement it from scratch or skip it.

5. **No network code**: Do not add HTTP clients, socket listeners, or any form of network I/O to simulator binaries.

6. **Test isolation**: Tests must not depend on each other, on network access, or on filesystem state outside the test directory.
