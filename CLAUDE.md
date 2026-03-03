# CLAUDE.md -- Agent Steering for In The Beginning

This file provides steering instructions for Claude Code, Claude Agent SDK agents,
and similar LLM-based coding assistants working on this repository.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [AST-Passing Workflow](#ast-passing-workflow)
3. [Coding Principles](#coding-principles)
4. [Documentation Reference](#documentation-reference)
5. [Test Execution](#test-execution)
6. [Test Coverage Enforcement](#test-coverage-enforcement)
7. [Session Logging Protocol](#session-logging-protocol)
8. [Markdown Consistency Check](#markdown-consistency-check)
9. [Self-Cueing and gVisor Enforcement](#self-cueing-and-gvisor-enforcement)
10. [Cross-Compilation](#cross-compilation)
11. [CI/CD](#cicd)
12. [File Structure](#file-structure)
13. [For Agentic Tools](#for-agentic-tools-jules-codex-devin-etc)

---

## Project Overview

**In The Beginning** is a multi-language cosmic physics simulator that models the
universe from the Big Bang through the emergence of life. It implements the same
simulation across 16 different applications and execution modes.

The Python implementation in `simulator/` is the reference. All other implementations
in `apps/` replicate its physics engine.

---

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
   - `parse` -- full AST of a file
   - `find` -- search by node type or name
   - `symbols` -- extract all definitions
   - `dependencies` -- extract imports
   - `callers` -- find call sites
   - `metrics` -- cyclomatic complexity, node counts
   - `coverage_map` -- identify testable paths
   - `transform` -- rename, extract, inline

4. **Performance tracking**: Every query returns `PerformanceMetrics` with wall time,
   CPU time, memory usage, and approximate token counts so agents can budget context.

5. **Agent loop**: An agent requests a compact AST of a file, reasons about it,
   requests targeted sub-trees or transformations, and emits edits -- never needing
   the full file in context unless writing new code.

### The CueSignal Reactive Protocol

The AST-passing workflow is built on a **reactive protocol** in which the LLM agent
and the local AST engine exchange structured **CueSignal** messages. Six signal types
form the conversation:

| CueType | Direction | Purpose |
|---|---|---|
| `QUERY` | LLM -> Tool | Request analysis. Payload is an ASTQuery dict. |
| `RESULT` | Tool -> LLM | Return analysis results. Payload is an ASTResult dict. |
| `REFINE` | LLM -> Tool | Re-execute a previous query with modified parameters. Links to parent via `parent_id`. |
| `TRANSFORM` | LLM -> Tool | Request a code transformation (rename, extract). Payload includes transform filters. |
| `SYNTHESIZE` | Tool -> LLM | Combine accumulated state into a summary. Returns all discovered symbols, dependencies, and history. |
| `COMPLETE` | Either | Signal that the interaction is finished. Includes final state summary. |

#### Typical Cue Exchange

```
Turn 1: LLM sends QUERY(action="symbols", target="app.py")
Turn 2: Tool returns RESULT(symbols=[...], metrics={...})
Turn 3: LLM sends REFINE(action="callers", target="app.py",
                          filters={"name": "process_data"})
         parent_id points to Turn 1's sequence_id
Turn 4: Tool returns RESULT(callers=[...])
Turn 5: LLM sends TRANSFORM(target="app.py",
                             filters={"transform": "rename",
                                      "old_name": "process_data",
                                      "new_name": "transform_data"})
Turn 6: Tool returns RESULT(transformed_ast=...)
Turn 7: LLM sends SYNTHESIZE
Turn 8: Tool returns RESULT(all_symbols=..., all_deps=..., history=...)
Turn 9: LLM sends COMPLETE
```

#### AgentState Tracking

State persists across the entire session and accumulates:

```python
@dataclass
class AgentState:
    session_id: str              # Unique session identifier
    turn: int                    # Current turn number
    history: list                # Full cue exchange history
    context: dict                # Arbitrary context data
    discovered_symbols: list     # Symbols found across all queries
    discovered_deps: list        # Dependencies found across all queries
    pending_transforms: list     # Transformations requested but not applied
    total_tokens_used: int       # Running token count
```

The compact representation of state:

```
s:a1b2c3d4 t:6 sym:30 dep:6 tok:62017
```

This tells the agent: session `a1b2c3d4`, turn 6, 30 symbols found, 6 dependencies
found, ~62K tokens used so far.

#### Sequence and Refinement Tracking

Every CueSignal carries a `sequence_id` (monotonically increasing) and an optional
`parent_id`. This creates a tree of queries:

```
#1 QUERY(symbols, app.py)
  #2 RESULT(...)
  #3 REFINE(callers, app.py, name="foo")  parent_id=1
    #4 RESULT(...)
  #5 REFINE(callers, app.py, name="bar")  parent_id=1
    #6 RESULT(...)
#7 QUERY(symbols, utils.py)
  #8 RESULT(...)
#9 SYNTHESIZE
  #10 RESULT(summary)
```

This lets the agent (or a human reviewing the log) understand the reasoning chain.

### Token Efficiency

The compact AST format achieves **27x compression** over full JSON AST:

| Representation | Size | Approx Tokens |
|---|---|---|
| Raw source (all .py files) | ~50 KB | ~12,500 |
| Full JSON AST | 16,443,157 bytes | ~4,110,000 |
| Compact AST | 602,783 bytes | ~150,000 |
| Symbol summary | 149,908 bytes | ~37,000 |
| Coverage map | 94,608 bytes | ~23,000 |

For targeted queries the savings are even greater:

| Query Type | Typical Result Size | Tokens |
|---|---|---|
| `symbols` (one file) | 200-2,000 bytes | 50-500 |
| `dependencies` (one file) | 100-500 bytes | 25-125 |
| `callers` (one symbol) | 50-500 bytes | 12-125 |
| `metrics` (one file) | 100-200 bytes | 25-50 |
| `coverage_map` (one file) | 200-1,000 bytes | 50-250 |

**Rule of thumb**: A single targeted query costs ~100 tokens. Reading the raw source
of the same file would cost ~3,000 tokens. That is a **30x saving per query**.

### Token Budget Guidelines

- Prefer `to_compact()` over `to_dict()` for initial exploration (5-10x smaller).
- Use `depth` parameter on queries to limit tree depth.
- Request `symbols` before `parse` to decide which files need full analysis.
- Use `coverage_map` to target test generation without parsing entire files.
- Use depth 1-2 for most code intelligence tasks; unlimited depth only for
  expression-level analysis (dead code detection, control flow).

### Usage Rules

1. **ALWAYS use AST queries before reading raw source files.** Do not read a source
   file until you have queried its symbols and understand its structure.
2. **Use compact representations** in reasoning to conserve context.
3. **Track discovered symbols** across queries -- do not re-query symbols you have
   already found. The `AgentState.discovered_symbols` list accumulates automatically.
4. **Use SYNTHESIZE** to get accumulated state when planning multi-file changes.

### Quick Code Reference: ReactiveProtocol

```python
from ast_dsl import ReactiveProtocol

proto = ReactiveProtocol(session_id="current-task")

# Understand a file's structure
result = proto.run_query("symbols", "path/to/file.py")
print(result.to_compact())

# Find dependencies
result = proto.run_query("dependencies", "path/to/file.py")

# Find all callers of a function
result = proto.run_query("callers", "path/to/file.py",
                         filters={"name": "function_name"})

# Compute complexity metrics
result = proto.run_query("metrics", "path/to/file.py")

# Map testable code paths
result = proto.run_query("coverage_map", "path/to/file.py")

# Plan a rename transformation
result = proto.run_query("transform", "path/to/file.py",
    filters={"transform": "rename",
             "old_name": "old", "new_name": "new"})

# Synthesize accumulated findings
from ast_dsl.reactive import CueSignal, CueType
cue = CueSignal(cue_type=CueType.SYNTHESIZE, sequence_id=99)
summary = proto.process_cue(cue)
```

### Deep Python Analysis (PythonASTAnalyzer)

Python gets the deepest analysis because the built-in `ast` module provides a full,
typed AST. The `PythonASTAnalyzer` class (in `ast_dsl/python_ast.py`) provides:

- **Scope analysis** (`analyze_scopes`): Identifies variable reads and writes per
  function scope. Useful for understanding side effects and data flow.
- **Control flow extraction** (`extract_control_flow`): Builds control flow graph
  edges -- branches (if), loops (for, while), returns, raises, try/except blocks.
- **Dead code detection** (`find_dead_code`): Finds statements after return or raise
  that can never execute.
- **Test stub generation** (`generate_test_stubs`): Auto-generates unittest class and
  method stubs for every public function and class method.

```python
from ast_dsl.python_ast import PythonASTAnalyzer

analyzer = PythonASTAnalyzer()

# Scope analysis (variable reads/writes per function)
scopes = analyzer.analyze_scopes(source_code)

# Control flow graph edges
cfg = analyzer.extract_control_flow(source_code)

# Dead code detection
dead = analyzer.find_dead_code(source_code)

# Auto-generate test stubs
stubs = analyzer.generate_test_stubs(source_code, "module_name")
```

### Pre-Generated AST Captures

The `ast_captures/` directory contains pre-computed AST snapshots for reference. These
files allow agents to skip on-the-fly parsing for common queries:

- `symbols.json` -- All symbol definitions across the codebase
- `coverage_map.json` -- Testable code paths
- `compact_ast.txt` -- Full compact AST (use for structural queries)

**Session startup**: At the start of each session, read `ast_captures/symbols.json`
and `ast_captures/compact_ast.txt` to get a global overview of the codebase structure.
Dispatch these ASTs alongside relevant source code to subagents for parallel
processing. This enables faster reasoning about code structure.

**AST history in git**: The `ast_captures/` directory is versioned in git. Use
`git log -- ast_captures/` to reason about program fluctuation over time -- symbol
additions/removals, complexity trends, and coverage gap history.

**Regeneration**: AST captures must be regenerated at the **end of each work session**
to keep them current for the next agent session.

Read these instead of parsing source files directly when possible. To regenerate:

```python
from ast_dsl.core import ASTEngine, ASTQuery
import json, os

engine = ASTEngine()
base = "/path/to/project"

py_files = []
for dirpath, dirnames, filenames in os.walk(base):
    dirnames[:] = [d for d in dirnames
                   if not d.startswith('.') and d != 'node_modules']
    for f in sorted(filenames):
        if f.endswith('.py'):
            py_files.append(os.path.join(dirpath, f))

symbols = {}
for filepath in py_files:
    relpath = os.path.relpath(filepath, base)
    result = engine.execute(ASTQuery(
        action="symbols", target=filepath, language="python"
    ))
    if result.success and isinstance(result.data, list):
        symbols[relpath] = result.data

with open(os.path.join(base, "ast_captures", "symbols.json"), "w") as f:
    json.dump(symbols, f, indent=2)
```

### AST-Guided Code Generation (Bug Prevention)

When generating new code or modifying existing code, use AST introspection to prevent
common bug classes **before they occur**. This is a proactive quality gate, not a
post-hoc check.

#### Pre-Write Checks

Before writing or editing a file:

1. **Query symbols** of the target file to understand existing structure:
   ```python
   result = proto.run_query("symbols", "path/to/file.py")
   ```
   This prevents: duplicate definitions, naming collisions, incorrect import paths.

2. **Query dependencies** to verify import targets exist:
   ```python
   result = proto.run_query("dependencies", "path/to/file.py")
   ```
   This prevents: broken imports, circular dependencies, missing modules.

3. **Query callers** before renaming or moving a function:
   ```python
   result = proto.run_query("callers", "path/to/file.py",
                            filters={"name": "function_name"})
   ```
   This prevents: broken call sites, signature mismatches, orphaned references.

#### Post-Write Checks

After writing or editing a file:

1. **Re-parse the modified file** to verify syntactic validity:
   ```python
   result = proto.run_query("parse", "path/to/modified_file.py")
   assert result.success, f"Parse error: {result.error}"
   ```

2. **Run coverage_map** on the modified file to identify untested branches:
   ```python
   result = proto.run_query("coverage_map", "path/to/modified_file.py")
   ```

3. **Cross-check interfaces** — if the file exports functions/classes used by other
   files, verify the signatures still match by querying callers.

#### Bug Classes Prevented by AST Analysis

| Bug Class | AST Query | Prevention |
|---|---|---|
| Broken imports | `dependencies` | Verify import targets exist before writing |
| Type mismatches | `symbols` + `callers` | Cross-check function signatures with call sites |
| Dead code | `coverage_map` | Identify unreachable branches after edits |
| Duplicate definitions | `symbols` | Detect naming collisions before writing |
| Missing test coverage | `coverage_map` | Generate stubs for untested paths |
| Circular dependencies | `dependencies` (multi-file) | Check import graph for cycles |
| Stale references | `callers` | Find all call sites before renaming/removing |

#### Example: AST-Guided Bug Prevention in Practice

During the audio composition engine development, AST analysis caught:
- `abs()` called on a list slice instead of a generator expression (`sum(abs(list_slice))`)
- The `_inject_dark_matter_texture` method referenced `mix.left` as a list but tried
  to use `abs()` on the slice — AST symbol analysis confirmed `mix.left` is `list[float]`
- Dependency analysis confirmed `composer.py` imports only `math` and `random` (stdlib),
  maintaining the zero-dependency principle

---

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

### Pure Code Philosophy

Write everything from scratch using the language or framework's native capabilities.
If a feature would normally require an external library, implement it from scratch or
skip it. This keeps the project self-contained, auditable, and free of supply-chain
risk.

### Security -- Zero Network Surface

The simulator applications have **no network surface**:
- No HTTP servers in the core simulator
- No outbound network calls
- No telemetry or analytics
- No dynamic code loading from external sources
- No file system access outside the project directory
- Input is limited to CLI arguments and environment variables

If adding new features, do not introduce network listeners or outbound connections
to the simulator binaries.

**Intentional localhost servers**: The Go SSE server (`apps/go/cmd/server/`) and the
PHP snapshot server (`apps/php/`) are intentional localhost-only web servers designed
for end-user consumption. They bind to `localhost` only and have no external service
dependencies. These are the only network-facing components in the project.

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

---

## Documentation Reference

The `docs/` directory contains comprehensive project documentation. **Review ALL files
in `docs/` at each conversation turn** to ensure familiarity with the full architecture.

### Key Documents

| File | Description |
|---|---|
| `docs/steering.md` | AST reactive protocol -- full CueSignal specification, integration patterns for Claude Code / Jules / Codex / SERA, prompt templates, performance guidelines, and example workflows |
| `docs/walkthrough.md` | Architecture walkthrough -- how the simulator is structured, physics modules, epoch progression |
| `docs/apps_overview.md` | Overview of all 16 application implementations with language-specific notes |
| `docs/build_guide.md` | Cross-platform build instructions for all languages and targets |
| `docs/ast_passing_efficiency.md` | Token efficiency metrics and benchmarks for the AST-passing approach |
| `docs/ast_introspection.md` | Guide to using AST introspection for code intelligence |
| `docs/roadmap.md` | Feature roadmap -- planned features and future state |
| `docs/ios_app_store_guide.md` | Guide for publishing the Swift iOS app to the App Store |
| `docs/android_play_store_guide.md` | Guide for publishing the Kotlin Android app to Google Play |

### Per-Language AST Documentation

| File | Language |
|---|---|
| `docs/python_ast.md` | Python AST parser details |
| `docs/go_ast.md` | Go AST parser details |
| `docs/nodejs_ast.md` | Node.js (JavaScript) AST parser details |
| `docs/java_ast.md` | Java AST parser details |
| `docs/rust_ast.md` | Rust AST parser details |
| `docs/cpp_ast.md` | C++ AST parser details |
| `docs/perl_ast.md` | Perl AST parser details |
| `docs/php_ast.md` | PHP AST parser details |
| `docs/wasm_ast.md` | WebAssembly (WAT) AST parser details |
| `docs/typescript_ast.md` | TypeScript AST parser details |
| `docs/swift_ast.md` | Swift AST parser details |
| `docs/kotlin_ast.md` | Kotlin AST parser details |

---

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

# Audio composition engine
python -m pytest apps/audio/ -v
```

---

## Test Coverage Enforcement

At each conversation turn, ensure full test coverage across all languages:

1. **Run the Python reference test suite**: `python -m pytest tests/ -v --tb=short`
   This is fast (~2s) and should be run after every edit.

2. **Run language-specific tests** for any language where code was modified, using the
   commands listed in the [Test Execution](#test-execution) section above.

3. **Add new tests** when new code is added or when coverage gaps are identified.

4. **Use `coverage_map` AST queries** to identify untested code paths:

   ```python
   from ast_dsl import ReactiveProtocol
   proto = ReactiveProtocol()
   result = proto.run_query("coverage_map", "path/to/file.py")
   # Examine result.payload for functions lacking test coverage
   ```

5. **Use `generate_test_stubs`** from `PythonASTAnalyzer` to auto-generate test
   scaffolding for new Python modules:

   ```python
   from ast_dsl.python_ast import PythonASTAnalyzer
   analyzer = PythonASTAnalyzer()
   stubs = analyzer.generate_test_stubs(source_code, "module_name")
   ```

6. **Cross-language test parity**: When a physics engine change is made in the Python
   reference, ensure corresponding tests exist in all other language implementations.

---

## Session Logging Protocol

At each conversation turn, generate a session and transcript log in `session_logs/`.

### File Naming

- Session log: `session_logs/v{VERSION}-session.md`
- Optional JSON companion: `session_logs/v{VERSION}-session.json`

Where `{VERSION}` is the current version or session identifier.

### Content Requirements

Each session log must include:

- **Conversation turn details**: What was requested, what was done, outcome
- **Agent spawning**: If subagents were spawned, record their identifiers and tasks
- **AST passing stats**: Number of AST queries, total tokens used, compression ratios
- **Test results**: Full pass/fail summary for all test suites run during the turn
- **File changes**: List of files created, modified, or deleted

### Transcript Detail

Include detailed transcript entries for each action taken. However, **truncate entries
exceeding 1,000 lines** with a note:

```
[TRUNCATED: Original entry was {N} lines. Showing first 1000 lines.]
```

For the JSON companion file, add a `truncated` boolean field for entries that were
truncated:

```json
{
  "turn": 3,
  "action": "run_tests",
  "output_lines": 1000,
  "truncated": true,
  "truncated_from": 2847
}
```

### Sensitive Information

Scrub highly sensitive information from session logs, leaving markers:

```
[REDACTED: API key]
[REDACTED: filesystem credential]
[REDACTED: personal information]
```

### Rolling Window

- Keep the **3 most recent** session logs as raw markdown files.
- Compress older session logs into a tarball: `session_logs/archive.tar.gz`

### Append-Only Rule

Session logs are **append-only** per conversation turn. Do not rewrite old session logs
during the markdown review step or any other automated process. They are historical
records generated once per conversation turn.

---

## Markdown Consistency Check

At each conversation turn, analyze **ALL markdown files** in the repository to ensure
they are accurate and in harmony with the current codebase:

### Files to Check

- `CLAUDE.md` (this file)
- `AGENTS.md`
- `README.md`
- `docs/*.md` (all documentation files)
- `apps/*/README.md` (per-app README files)

### What to Look For

- **Stale references**: File paths, function names, or module names that no longer
  exist in the codebase.
- **Outdated instructions**: Build commands, test commands, or workflows that have
  changed.
- **Inconsistencies**: Contradictions between different markdown files or between
  markdown and the actual code.
- **Missing documentation**: New modules, features, or apps that are not documented.

### What to Fix

Fix any stale references, outdated instructions, or inconsistencies found. Update
documentation to match the current state of the codebase.

### Exception

Files in `session_logs/` are historical records and should **NOT** be rewritten. They
are generated once per conversation turn and preserved as-is.

---

## Self-Cueing and gVisor Enforcement

The gVisor sandbox environment (Claude Code's execution context) has self-cueing
mechanisms to enforce steering compliance.

### Hook Reminders

Hooks in `.claude/settings.json` emit reminder signals (as "FAIL" test markers with
explicit guidance) to ensure all steering rules are followed at each turn. **These
FAIL markers in gVisor hooks are intentional reminders -- do NOT delete them.** They
exist to prompt the agent to complete all required steering tasks.

### Steering Checklist (Per Conversation Turn)

At every conversation turn, complete the following checklist:

1. **Run AST introspection** on changed files
   ```bash
   python -c "from ast_dsl.core import ASTEngine; e = ASTEngine(); print(e.find_symbols('<file>').to_compact())"
   ```

2. **Run the full Python test suite**
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

3. **Update session log** in `session_logs/` with turn details, AST stats, and test
   results

4. **Review markdown files** for accuracy (see
   [Markdown Consistency Check](#markdown-consistency-check))

5. **Update RELEASE_HISTORY.md** with a version entry documenting changes made this
   turn, agent activity, and files created/modified

6. **Ensure cross-language consistency** for any physics engine changes -- if the
   Python reference was modified, propagate changes to all other implementations

7. **Commit with proper format** -- descriptive commit messages, no unrelated changes

8. **AST-guided code generation** -- before editing files, run `symbols` and
   `dependencies` queries; after editing, run `parse` and `coverage_map` queries
   (see [AST-Guided Code Generation](#ast-guided-code-generation-bug-prevention))

### Reflection Principle (Triple Cross-Check)

When new steering information is added anywhere in the repository, ensure it is
reflected in **ALL THREE** locations:

1. **`CLAUDE.md`** — agent steering for Claude Code
2. **`AGENTS.md`** — multi-agent coordination protocol
3. **`.claude/steering-check.sh`** — gVisor self-cueing hook script

This maintains a single source of truth through triple redundancy. If a policy is
added to any one of these three, it must be propagated to the other two. Specific
items that must appear in all three:

- Session log generation per conversation turn
- Release history (`RELEASE_HISTORY.md`) update per conversation turn
- Markdown consistency review per conversation turn
- Test coverage enforcement per conversation turn
- AST introspection on changed files
- AST-guided code generation (bug prevention)
- Cross-language consistency for physics changes
- Commit format rules

---

## Cross-Compilation

Compilable programs (Go, Rust, C, C++) must be buildable for multiple targets.

### Supported Targets

See `.github/workflows/release.yml` for the full cross-compilation matrix. The release
workflow cross-compiles binaries across:

- **Operating systems**: Linux, macOS, Windows
- **Architectures**: amd64, arm64 (where supported)

### Per-Language Build Commands

- **Go**: `GOOS=<os> GOARCH=<arch> go build -o <output> ./cmd/simulator/`
- **Rust**: `cargo build --release --target <target-triple>`
- **C/C++**: Platform-specific Makefiles / CMake with appropriate toolchain files

### Verification

At each conversation turn, verify that compilable programs build successfully for
available toolchains. At minimum, ensure the native platform builds succeed:

```bash
# Go
cd apps/go && go build ./...

# Rust
cd apps/rust && cargo build

# C
cd apps/c && make

# C++
cd apps/cpp && mkdir -p build && cd build && cmake .. && make
```

---

## CI/CD

Tests are run on every push and PR via `.github/workflows/ci.yml`. The release
workflow (`.github/workflows/release.yml`) cross-compiles binaries for Go, Rust,
C, and C++ across Linux/macOS/Windows when a version tag is pushed.

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
ast_dsl/             AST parsing and transformation engine
ast_captures/        Pre-computed AST snapshots for reference
tests/               Python test suite
docs/                Architecture documentation
session_logs/        Per-turn session and transcript logs
.github/workflows/   CI/CD pipelines
.claude/             gVisor hook scripts and settings
```

---

## For Agentic Tools (Jules, Codex, Devin, etc.)

When working on this repository with an automated agent:

1. **Start with AST introspection**: Run `python -c "from ast_dsl.core import ASTEngine; e = ASTEngine(); print(e.find_symbols('simulator/quantum.py').to_compact())"` to get a symbol map before reading files.

2. **Run tests after every change**: `python -m pytest tests/ -v --tb=short` is fast (~2s). Run it after every edit.

3. **Cross-language consistency**: Changes to the physics engine in one language should be reflected in all languages. Use the AST DSL to compare symbols across implementations.

4. **No new dependencies**: Do not add external packages. If a feature requires a library, implement it from scratch or skip it.

5. **No network code**: Do not add HTTP clients, socket listeners, or any form of network I/O to simulator binaries.

6. **Test isolation**: Tests must not depend on each other, on network access, or on filesystem state outside the test directory.

7. **Review the feature roadmap**: Check `docs/roadmap.md` for planned features and future state before proposing new features. Align work with the roadmap where possible.

8. **Follow the AST-passing protocol**: Subagents should also follow the AST-passing protocol when possible. Use `ReactiveProtocol` instances to query code structure before reading raw source. This applies to all agents, including spawned subagents.

9. **Session logging**: Generate a session log in `session_logs/` for each conversation turn, following the [Session Logging Protocol](#session-logging-protocol).

10. **Markdown review**: At each turn, verify that all markdown files are consistent with the codebase, following the [Markdown Consistency Check](#markdown-consistency-check).
