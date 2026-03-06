# AGENTS.md — Multi-Agent Coordination for In The Beginning

This document defines the coordination protocol for AI agents and agent swarms
working on this repository. It applies to Claude Code, Claude Agent SDK,
OpenAI Codex, Google Jules, Devin, and any similar agentic coding tool.

All agents -- primary and subagents alike -- must follow every protocol in this
file. Subagents must also follow the AST-passing protocol by default, backing off
to full-source reads only when AST data is insufficient for the task at hand.

---

## Agent Architecture

### AST-Passing for Context Efficiency

Traditional agent workflows pass entire source files through the context window.
This project implements an **AST-passing protocol** that dramatically reduces
token usage:

```
┌──────────────┐      compact AST       ┌──────────────┐
│  Agent (LLM) │ ◄──────────────────── │  AST Engine  │
│              │ ────────────────────► │  (ast_dsl/)  │
│  Reasons on  │     ASTQuery           │  Parses all  │
│  structure   │                        │  15 languages│
└──────────────┘                        └──────────────┘
       │                                       ▲
       │  Targeted edits                       │
       ▼                                       │
┌──────────────┐                        ┌──────────────┐
│  Source Files │ ──────────────────── │   File I/O   │
│  (15 langs)  │                        │              │
└──────────────┘                        └──────────────┘
```

**Protocol**:
1. Agent sends an `ASTQuery` (action + target + filters + depth limit)
2. AST Engine returns an `ASTResult` with compact data + performance metrics
3. Agent reasons on the compact AST (typically 5-10x fewer tokens than source)
4. Agent emits targeted edits (line ranges, not full file rewrites)
5. After edits, agent re-queries to verify structural correctness

### CueSignal Protocol

The AST-passing architecture uses a **CueSignal** reactive protocol for
structured communication between the agent (LLM) and the local AST engine.
Every exchange is a typed signal that carries a payload and tracking metadata.

**CueSignal data structure:**

```python
@dataclass
class CueSignal:
    cue_type: CueType       # QUERY, RESULT, REFINE, TRANSFORM, SYNTHESIZE, COMPLETE
    payload: Any = None      # ASTQuery dict or ASTResult dict
    sequence_id: int = 0     # Monotonic sequence number
    parent_id: int = 0       # Links refinements to parent queries
    timestamp: float = ...
    context_tokens_approx: int = 0
```

**CueTypes and their direction:**

| CueType | Direction | Purpose |
|---|---|---|
| `QUERY` | LLM -> Tool | Request analysis. Payload is an ASTQuery dict. |
| `RESULT` | Tool -> LLM | Return analysis results. Payload is an ASTResult dict. |
| `REFINE` | LLM -> Tool | Re-execute a previous query with modified parameters. Links to parent via `parent_id`. |
| `TRANSFORM` | LLM -> Tool | Request a code transformation (rename, extract). Payload includes transform filters. |
| `SYNTHESIZE` | Tool -> LLM | Combine accumulated state into a summary. Returns all discovered symbols, dependencies, and history. |
| `COMPLETE` | Either | Signal that the interaction is finished. Includes final state summary. |

**Typical cue exchange:**

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

**Sequence and refinement tracking:** Every CueSignal carries a `sequence_id`
(monotonically increasing) and an optional `parent_id`, creating a tree of queries:

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

### AgentState

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

Compact state representation: `s:a1b2c3d4 t:6 sym:30 dep:6 tok:62017`

This tells the agent: session `a1b2c3d4`, turn 6, 30 symbols found,
6 dependencies found, ~62K tokens used so far.

### Compact AST Grammar

The compact AST format encodes AST nodes as single-line nested expressions.
This is the formal grammar (see also `docs/steering.md` Appendix A):

```
node      := type (':' name)? ('@' line)? attrs? children?
type      := [A-Za-z]+
name      := [^\[@{};]+
line      := [0-9]+
attrs     := '[' attr (',' attr)* ']'
attr      := key '=' value
key       := [A-Za-z_]+
value     := [^\],]+
children  := '{' node (';' node)* '}'
```

**Example parse:**

```
Input:  ClassDef:Calculator@5[bases=['object'],decorators=0]{FunctionDef:add@7[args=['self','a','b']];FunctionDef:divide@12[args=['self','a','b']]}

Parsed:
  type = ClassDef
  name = Calculator
  line = 5
  attrs = {bases: ['object'], decorators: 0}
  children = [
    {type: FunctionDef, name: add, line: 7, attrs: {args: ['self','a','b']}},
    {type: FunctionDef, name: divide, line: 12, attrs: {args: ['self','a','b']}}
  ]
```

### Token Budget Per Query

| Query Type     | Typical Tokens | Use Case                          |
|----------------|---------------|-----------------------------------|
| `symbols`      | 50-200        | Quick file overview               |
| `find`         | 100-500       | Locate specific definitions       |
| `dependencies` | 30-100        | Understand imports                |
| `metrics`      | 20-50         | Complexity assessment             |
| `coverage_map` | 100-300       | Test generation planning          |
| `parse` depth=2| 200-1000      | Moderate structural detail        |
| `parse` full   | 1000-5000     | Complete AST (use sparingly)      |

### Token Efficiency Data

The compact AST format achieves **27x compression** over full JSON AST for
this codebase:

| Format | Size | Approx Tokens |
|---|---|---|
| Raw source (all .py files) | ~50 KB | ~12,500 |
| Full JSON AST | 16,443,157 bytes | ~4,110,000 |
| Compact AST | 602,783 bytes | ~150,000 |
| Symbol summary | 149,908 bytes | ~37,000 |
| Coverage map | 94,608 bytes | ~23,000 |

Per-language compaction ratios (source tokens / AST tokens):

| Language   | Compaction Ratio | Notes |
|------------|----------------:|-------|
| Rust (wasm) | 14.3x | Highest -- FFI bindings and `#[wasm_bindgen]` compress aggressively |
| PHP | 10.1x | Verbose syntax collapses to compact signatures |
| Rust | 9.8x | Rich type system, lifetime annotations compress well |
| Swift | 5.2x--5.3x | Access control and property wrappers strip cleanly |
| Perl | 3.3x | `sub` declarations reduce to clean function references |
| Kotlin | 3.0x | Data classes and sealed hierarchies compress moderately |
| Java | 2.8x | High method count retains many AST nodes |
| TypeScript | 2.3x | Already compact; type annotations are structurally significant |

**Rule of thumb**: A single targeted query costs ~100 tokens. Reading the raw
source of the same file costs ~3,000 tokens. That is a **30x saving per query**.

For a 200K-token context window, the AST approach saves ~25% of the budget on
code understanding versus raw source, which compounds with multi-file analysis.
For a 20-file refactoring task: AST costs ~2,000 tokens for understanding versus
~60,000 tokens for raw source (97% reduction).

See `docs/ast_passing_efficiency.md` for the full methodology and per-language
breakdown.

### Pre-Generated AST Captures

The `ast_captures/` directory contains pre-computed AST snapshots that should be
loaded at the **start of every agent session** alongside any source code reads:

- `symbols.json` — All symbol definitions across the codebase
- `coverage_map.json` — Testable code paths for all Python files
- `compact_ast.txt` — Full compact AST representation

**Session startup protocol**:
1. Read `ast_captures/symbols.json` to get a global symbol map
2. Read `ast_captures/compact_ast.txt` for structural overview
3. Dispatch both ASTs + relevant source code to subagents for parallel processing
4. Use AST data to reason about code structure before reading raw source

**AST history in git**: The `ast_captures/` directory is versioned in git. The diff
history of these files is useful for reasoning about how the program structure has
changed over time — symbol additions/removals, complexity trends, and coverage gaps.
Agents can use `git log -- ast_captures/` to understand code fluctuation.

**Regeneration**: AST captures should be regenerated at the **end of each work
session** to keep them current:

```python
from ast_dsl.core import ASTEngine, ASTQuery
import json, os

engine = ASTEngine()
base = "/path/to/project"
# ... regenerate symbols.json, coverage_map.json, compact_ast.txt
```

---

## Agent Roles in a Swarm

When multiple agents work concurrently on this repository:

### Orchestrator Agent
- Maintains the global task queue
- Assigns files/modules to worker agents
- Merges results and resolves conflicts
- Runs the full test suite after each batch of changes

### Language Specialist Agents
- Each assigned to one or more language implementations
- Uses AST queries to understand current state
- Implements changes, tests, and documentation for their language
- Reports back symbol diffs for cross-language consistency checks

### Test Agent
- Runs after every batch of changes
- Executes the full CI test matrix locally
- Reports failures with AST-level context (which function, which branch)
- Uses `coverage_map` to identify untested code paths

### Documentation Agent
- Generates and updates doc comments across all languages
- Maintains README.md, CLAUDE.md, and AGENTS.md
- Cross-references the docs/ directory for consistency

---

## Coordination Protocol

### File Locking Convention

Agents should claim files before editing by checking git status. If a file has
unstaged changes, another agent may be working on it. Prefer:
1. Work on separate files in parallel
2. If you must edit the same file, coordinate through the orchestrator
3. Always pull before push

### Commit Conventions

Each agent commit should:
- Describe which language/module was changed
- Reference the AST query that motivated the change (if applicable)
- Include test results in the commit message body

Format:
```
<type>(<scope>): <description>

[optional body with AST context and test results]
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `ci`, `build`
Scopes: `python`, `nodejs`, `go`, `rust`, `c`, `cpp`, `java`, `perl`, `php`,
        `typescript`, `kotlin`, `swift`, `wasm`, `screensaver`, `ast`, `ci`

### Cross-Language Consistency Checks

After modifying the physics engine in any language, verify consistency:

1. Run `python ast_dsl/introspect.py` to generate symbol maps for all languages
2. Compare function signatures across implementations
3. Ensure epoch boundaries, constants, and particle types match
4. Run tests in all languages that have them

---

## Documentation Reference

The `docs/` directory contains comprehensive project documentation that **ALL
agents must review** before making substantive changes. These documents are the
authoritative reference for architecture, build procedures, and project direction.

### Required Reading

| Document | Purpose |
|---|---|
| `docs/steering.md` | AST DSL reactive agent pair -- full steering and reuse guide, CueSignal protocol, prompt templates, example workflows |
| `docs/walkthrough.md` | End-to-end walkthrough of the project structure and physics simulation |
| `docs/apps_overview.md` | Comprehensive overview of all 15 application implementations with build/run/test commands |
| `docs/build_guide.md` | Build instructions for every language and platform |
| `docs/ast_passing_efficiency.md` | Token efficiency metrics, per-language compaction ratios, methodology |
| `docs/ast_introspection.md` | How to use the AST introspection module for cross-language analysis |
| `docs/ios_app_store_guide.md` | End-to-end guide for building, testing, and publishing the Swift iOS app |
| `docs/android_play_store_guide.md` | End-to-end guide for building, testing, and publishing the Kotlin Android app |
| `docs/roadmap.md` | Planned features including containerization, platform targets, and metacognitive steering |

### Per-Language AST Documentation

| Document | Coverage |
|---|---|
| `docs/python_ast.md` | Python AST parser -- scope analysis, control flow, dead code, test stubs |
| `docs/go_ast.md` | Go AST parser -- `go/ast` package integration |
| `docs/nodejs_ast.md` | JavaScript/Node.js AST parser -- Acorn integration |
| `docs/cpp_ast.md` | C++ AST parser -- clang `-ast-dump` integration |
| `docs/java_ast.md` | Java AST parser -- regex + `javac -Xprint` fallback |
| `docs/rust_ast.md` | Rust AST parser -- regex + `rustc` nightly fallback |
| `docs/perl_ast.md` | Perl AST parser -- regex + `B::Deparse` fallback |
| `docs/php_ast.md` | PHP AST parser -- regex + `token_get_all` fallback |
| `docs/wasm_ast.md` | WebAssembly (WAT) AST parser -- S-expression parsing |
| `docs/typescript_ast.md` | TypeScript AST parser -- regex + `tsc` fallback |
| `docs/swift_ast.md` | Swift AST parser -- regex + `swiftc -dump-ast` fallback |
| `docs/kotlin_ast.md` | Kotlin AST parser -- regex + `kotlinc` fallback |

### Accuracy Requirement

At each conversation turn, review all markdown in the repo for accuracy and
update as needed. If any documentation is inconsistent with the current codebase
state, update the documentation to reflect reality. Session logs in
`session_logs/` are exempt from rewriting (see Session Logging Protocol below).

---

## Session Logging Protocol

Agents must generate session and transcript logs in `session_logs/` at each
conversation turn. These logs provide an audit trail of agent actions, AST
passing statistics, and test results.

### Log Format

Each session log is a markdown file named with the session identifier and date:
`session_logs/<version-or-id>-session.md`

Each log entry must include:

1. **Session metadata**: session ID, branch, date, input method
2. **Conversation turns**: numbered, with user request summary and agent actions
3. **AST passing stats**: queries executed, tokens consumed, compaction ratios
4. **Test results**: which test suites were run, pass/fail counts
5. **Commits made**: commit hashes and messages

### Size and Retention Rules

- **Truncation**: Log entries exceeding 1,000 lines must be truncated with a
  `truncated: true` field and a summary of the omitted content.
- **Sensitive information**: Scrub any sensitive data with
  `[REDACTED: <reason>]` (e.g., `[REDACTED: API key]`, `[REDACTED: file path
  containing username]`).
- **Rolling window**: Maintain a rolling window of the 3 most recent session
  logs. Archive older logs by moving them to `session_logs/archive/`.
- **Append-only**: Never rewrite or modify old session log entries. New
  information is appended as new conversation turns. If a correction is needed,
  add a new turn noting the correction rather than editing the original.
- **Input quality caveat**: Session logs and future memories may contain typos,
  autocomplete artifacts, speech-to-text errors, and exploratory/ambiguous
  language from the user. Preserve quoted user input as-is (except for
  redacting sensitive information).

---

## Future Memories Protocol

The `future_memories/` directory holds verbose plan files written **before and
during** implementation. They serve as durable restoration context if a session
is interrupted, times out, or must be resumed by a different agent.

### Iterative Plan Commits

**Before mutating any source code**, agents must:

1. Write a plan file to `future_memories/v{VERSION}-plan.md` with the full
   intended work, architectural decisions, and user context.
2. **Commit and push** the plan file before proceeding with code changes.
3. Update the plan file and commit again at significant milestones.
4. Multiple plan commits per conversation turn is expected and encouraged.

### Archival

- Raw plan files remain in the working tree while in-progress.
- After version completion, archive into `future_memories/archive.tar.gz`.
- The archive is **rebuilt** (not appended) to contain full history. The old
  archive is replaced in-place -- no orphan files in git history.
- Same strategy for `session_logs/archive.tar.gz`.

### Content

Future memories are intentionally verbose. They may include speculative notes,
alternative approaches, and reasoning chains. Scrub sensitive information with
`[REDACTED: <reason>]` markers.

---

## CI Flake Detection and Repair

At each conversation turn, if GitHub CI is accessible:

1. Check for flaked builds from the previous version using `gh run list`.
2. Fix flakes if possible (flaky tests, transient failures).
3. Add TODOs for unfixable flakes and notify the user.
4. Update steering if new CI patterns are discovered.

### AMD64 Build Verification

When feasible, verify AMD64 builds from CI:

1. Download or build locally for AMD64 (Go, Rust, C, C++).
2. Run basic smoke tests.
3. If broken, add TODOs and notify the user.
4. Best-effort -- do not block the session.

---

## Markdown Consistency Check

At each conversation turn, agents must analyze all markdown files in the
repository for accuracy against the current codebase. This includes:

1. **File references**: Verify that paths mentioned in documentation actually
   exist in the repository.
2. **Command accuracy**: Verify that build, test, and run commands are correct
   for the current state of each application.
3. **Symbol references**: Verify that function names, class names, and API
   references in documentation match the actual source code.
4. **Cross-document consistency**: Verify that the same information is presented
   consistently across CLAUDE.md, AGENTS.md, README.md, and files in `docs/`.

**Exemptions**: Session logs in `session_logs/` are exempt from rewriting.
They are historical records and must remain as-is (see Session Logging Protocol).

---

## Test Coverage Enforcement

Agents must ensure full test coverage at each conversation turn. This means:

### At Every Turn

1. **Run all available test suites** for any language that was modified.
2. **Run the Python reference tests** (`python -m pytest tests/ -v --tb=short`)
   after every edit, regardless of which language was changed, to verify the
   reference implementation remains stable.
3. **Use `coverage_map` queries** to identify untested code paths in modified
   files:
   ```python
   from ast_dsl import ReactiveProtocol
   proto = ReactiveProtocol()
   result = proto.run_query("coverage_map", "path/to/modified_file.py")
   ```
4. **Generate test stubs** for any new public functions that lack tests:
   ```python
   from ast_dsl.python_ast import PythonASTAnalyzer
   analyzer = PythonASTAnalyzer()
   stubs = analyzer.generate_test_stubs(source, "module_name")
   ```
5. **Report coverage gaps** in the session log with function names, branch
   counts, and file locations.

### Coverage Standards

- Every public function must have at least one test.
- Tests must be deterministic (use fixed random seeds).
- Tests must be fast (< 5s per test suite per language).
- Tests must not require network access.
- Tests must not depend on each other or on filesystem state outside the test
  directory.

---

## Self-Cueing / gVisor Enforcement

### gVisor Steering Hooks

When running inside a gVisor sandbox (as Claude Code does), the sandbox
environment emits steering reminders at tool-call boundaries. These are
intentional hooks that reinforce the protocols in this file and in CLAUDE.md.

**IMPORTANT**: `FAIL` markers in gVisor hooks are **intentional steering
signals** -- they are not bugs or errors. Do not delete, suppress, or work
around them. They exist to trigger the agent's attention and ensure protocol
compliance.

### Central Time Timestamps

All agent responses should include a **Central Time (US)** datetime stamp in the
format `[YYYY-MM-DD HH:MM CT]` at key progress points (render starts/finishes,
commits, pushes, milestone completions). Use `TZ='America/Chicago' date` to generate.

### Start-of-Turn Protocol (MANDATORY)

**BEFORE doing any work** at the start of every conversation turn, agents MUST:

1. **Update/create the session log**: Append a new turn entry to
   `session_logs/v{VERSION}-session.md` describing what was requested.
2. **Update the future memories plan**: If a plan file exists in `future_memories/`,
   append a milestone note. If starting new work, create a new plan file.
3. **Update RELEASE_HISTORY.md**: Add or append to the current version entry with
   the turn's intended work.

This prevents the failure mode where an agent dives into the main task and forgets
housekeeping. The `PostToolUse` hook in `.claude/settings.json` emits a lightweight
start-of-turn reminder on the first Bash call to reinforce this protocol.

### Steering Checklist Per Turn (During/After Work)

At every conversation turn, every agent (primary or subagent) must verify the
following items:

1. **AST-first**: Did I use AST queries before reading raw source files?
2. **Tests passing**: Did I run tests after my changes and confirm they pass?
3. **No new dependencies**: Did I avoid adding external packages?
4. **No network surface**: Did I avoid adding network listeners or outbound
   connections to simulator binaries?
5. **Documentation updated**: Did I update doc comments and markdown if my
   changes affect public APIs?
6. **Session logged**: Did I record my actions in the session log?
7. **Release history updated**: Did I update `RELEASE_HISTORY.md` with changes
   made this turn, agent activity, and files created/modified?
8. **Markdown consistency**: Did I review all markdown files for accuracy with
   the current codebase?

### Reflection Principle (Triple Cross-Check)

New steering information must be maintained in **ALL THREE** locations:

1. **`CLAUDE.md`** — agent steering for Claude Code
2. **`AGENTS.md`** — multi-agent coordination protocol
3. **`.claude/steering-check.sh`** — gVisor self-cueing hook script

If a new protocol or constraint is added to any one of these three, it must be
propagated to the other two. Specific items that must appear in all three:

- **Central Time timestamps**: `[YYYY-MM-DD HH:MM CT]` in agent responses
- **Start-of-turn protocol**: session log + future memories + release history BEFORE work
- Session log generation per conversation turn
- Release history (`RELEASE_HISTORY.md`) update per conversation turn
- Markdown consistency review per conversation turn
- Test coverage enforcement per conversation turn
- AST introspection on changed files
- AST-guided code generation (bug prevention)
- Cross-language consistency for physics changes
- Commit format rules
- Future memories: iterative plan commits before code mutation
- Future memories: early-stage orchestration (plan committed BEFORE code changes)
- CI flake detection and repair
- AMD64 build verification (best-effort)
- Audio engine quality gate (when modifying radio_engine.py)
- Audio engine v12 is the current version: v8 synthesis (_synth_colored_note_np)
  + v9 expanded instruments (15 families) + v10 MIDI library + v11 gain staging
  + multiprocessing parallel render + tempo clamped 1.1x-1.7x

This triple cross-check principle prevents drift between human-readable
documentation and machine-enforced hooks.

---

## Network Surface Clarification

### Core Simulators: Zero Network Surface

All 15 simulator implementations have **no network surface**:
- No HTTP servers in the core simulator binaries
- No outbound network calls
- No telemetry or analytics
- No dynamic code loading from external sources
- No file system access outside the project directory
- Input is limited to CLI arguments and environment variables

### Intentional Localhost Web Servers

Two components are intentional localhost-only web servers for end-user
consumption. They are **not** violations of the zero-network-surface rule:

1. **Go SSE Server** (`apps/go/cmd/server/`): A Server-Sent Events server that
   streams simulation state to web browsers. Binds to `localhost` only. No
   external dependencies. Built as a separate binary from the Go simulator CLI.

2. **PHP HTTP Server** (`apps/php/server.php`): A snapshot server that serves
   simulation state via HTTP. Binds to `localhost` only. No Composer
   dependencies.

These servers:
- Bind to `localhost` only (never `0.0.0.0` or external interfaces)
- Have no external dependencies beyond their language's standard library
- Are separate entry points from the core simulator binaries
- Are intended for local development and demonstration use

### Rules for Agents

- Do **not** add HTTP clients, socket listeners, or any form of network I/O to
  simulator binaries.
- Do **not** modify the Go SSE server or PHP HTTP server to bind to non-localhost
  addresses.
- Do **not** add telemetry, analytics, or phone-home behavior to any component.
- Tests must **not** require network access.

---

## Cross-Compilation

All compiled applications must be buildable for multiple OS/architecture targets.
The release workflow (`.github/workflows/release.yml`) defines the full build
matrix.

### Build Matrix

**Go** (CLI + SSE server):

| OS | Architecture |
|---|---|
| Linux | amd64, arm64 |
| macOS | amd64, arm64 |
| Windows | amd64 |

**Rust** (CLI):

| Target Triple | OS | Notes |
|---|---|---|
| `x86_64-unknown-linux-gnu` | Linux amd64 | Standard glibc |
| `x86_64-unknown-linux-musl` | Linux amd64 | Static musl libc |
| `aarch64-unknown-linux-gnu` | Linux arm64 | Cross-compiled |
| `x86_64-apple-darwin` | macOS amd64 | |
| `aarch64-apple-darwin` | macOS arm64 | Apple Silicon |
| `x86_64-pc-windows-msvc` | Windows amd64 | |

**C** (CLI): Linux amd64 (static build via `make static`)

**C++** (CLI): Linux amd64 (CMake Release build)

**Java**: Universal JAR (platform-independent)

**Node.js**: Tarball (platform-independent, requires Node.js runtime)

**TypeScript**: Tarball with compiled JavaScript (platform-independent)

### Rules for Agents

- When modifying compiled applications (Go, Rust, C, C++), verify that the code
  compiles for the primary target (the development host) at minimum.
- Do not introduce platform-specific code without guarding it behind build
  constraints or `#ifdef` blocks.
- Do not add build dependencies that are unavailable in the CI matrix runners
  (Ubuntu latest, macOS latest, Windows latest).
- Reference `.github/workflows/release.yml` for the definitive target list.

---

## AST-Guided Code Generation (Bug Prevention)

All agents MUST use AST introspection as a proactive quality gate when generating or
modifying code. This prevents common bug classes before they occur.

### Pre-Write Protocol

1. **Query symbols** of the target file before editing (prevents naming collisions,
   duplicate definitions).
2. **Query dependencies** to verify import targets exist (prevents broken imports).
3. **Query callers** before renaming or moving functions (prevents broken call sites).

### Post-Write Protocol

1. **Re-parse the modified file** to verify syntactic validity.
2. **Run coverage_map** to identify untested branches created by the edit.
3. **Cross-check interfaces** — verify exported function signatures match call sites.

### Bug Classes Prevented

| Bug Class | AST Query | Prevention |
|---|---|---|
| Broken imports | `dependencies` | Verify targets exist |
| Type mismatches | `symbols` + `callers` | Cross-check signatures |
| Dead code | `coverage_map` | Detect unreachable branches |
| Duplicate definitions | `symbols` | Detect naming collisions |
| Missing coverage | `coverage_map` | Generate stubs for untested paths |
| Circular dependencies | `dependencies` | Check import graph |
| Stale references | `callers` | Find all call sites before renaming |

### Agent Workflow Integration

```
1. QUERY symbols of target file
2. QUERY dependencies of target file
3. [Generate/edit code]
4. QUERY parse of modified file (verify syntax)
5. QUERY coverage_map of modified file (identify untested paths)
6. [Write tests for any untested paths]
7. [Run test suite]
```

---

## Principles for All Agents

### 1. Minimize Dependencies
- No new external packages without explicit human approval
- If a feature needs a library, implement it inline
- The goal is zero-dependency simulators that build with only the language toolchain

### 2. Zero Network Surface
- Simulator binaries must not open sockets, make HTTP requests, or listen on ports
- The Go SSE server (`apps/go/cmd/server/`) and PHP HTTP server
  (`apps/php/server.php`) are the only intentional network-facing components,
  and they bind to localhost only
- Tests must not require network access
- No telemetry, analytics, or phone-home behavior

### 3. Security First
- No command injection vectors (all input is numeric CLI args)
- No file system access outside the project directory
- No dynamic code evaluation (no `eval()`, no `exec()`, no `System.loadLibrary()`)
- No deserialization of untrusted data
- Memory-safe patterns preferred (bounds checking, no raw pointers in C where avoidable)

### 4. Test Everything
- Every public function must have at least one test
- Tests must be deterministic (use fixed random seeds)
- Tests must be fast (< 5s per test suite per language)
- Run tests across the entire solution at each commit

### 5. Document Everything
- All public APIs must have language-appropriate doc comments
- PHPDoc for PHP, JSDoc for JS/TS, Javadoc for Java, KDoc for Kotlin,
  Swift Markup for Swift, godoc for Go, `///` for Rust, Doxygen for C/C++,
  POD for Perl
- README.md in each app directory must list build, run, and test commands

### 6. AST-First Development
- Before reading a full file, query its symbols
- Before writing tests, query the coverage map
- Before refactoring, query the dependency graph
- After editing, verify with a targeted AST parse

### 7. Review the Roadmap
- Review `docs/roadmap.md` for planned features before proposing new work
- Align contributions with the near-term and medium-term roadmap items
- Flag any conflicts between requested changes and the roadmap

### 8. Subagent Protocol Compliance
- Subagents must also follow the AST-passing protocol by default
- Subagents may back off to full-source reads only when AST data is
  insufficient for the specific task (e.g., line-level edits, debugging
  with stack traces, files under 50 lines)
- Subagents must report their AST query counts and token usage to the
  orchestrator or primary agent

---

## Quick Reference: Running All Tests

```bash
#!/bin/bash
set -e

echo "=== Python ==="
python -m pytest tests/ -v --tb=short

echo "=== Node.js ==="
node --test apps/nodejs/test/test_simulator.js

echo "=== Go ==="
cd apps/go && go test ./... && cd ../..

echo "=== Rust ==="
cd apps/rust && cargo test && cd ../..

echo "=== C ==="
cd apps/c && make test && cd ../..

echo "=== C++ ==="
cd apps/cpp && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc) && ctest --output-on-failure && cd ../../..

echo "=== Java ==="
cd apps/java && mkdir -p build/classes && javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java && java -cp build/classes com.inthebeginning.simulator.SimulatorApp 2>&1 | head -5 && cd ../..

echo "=== Perl ==="
prove -v apps/perl/t/

echo "=== PHP ==="
cd apps/php && php tests/run_tests.php && cd ../..

echo "=== TypeScript ==="
cd apps/typescript && npm test && cd ../..

echo "=== All tests passed ==="
```
