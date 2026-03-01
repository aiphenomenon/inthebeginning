# AGENTS.md — Multi-Agent Coordination for In The Beginning

This document defines the coordination protocol for AI agents and agent swarms
working on this repository. It applies to Claude Code, Claude Agent SDK,
OpenAI Codex, Google Jules, Devin, and any similar agentic coding tool.

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

### Agent Roles in a Swarm

When multiple agents work concurrently on this repository:

#### Orchestrator Agent
- Maintains the global task queue
- Assigns files/modules to worker agents
- Merges results and resolves conflicts
- Runs the full test suite after each batch of changes

#### Language Specialist Agents
- Each assigned to one or more language implementations
- Uses AST queries to understand current state
- Implements changes, tests, and documentation for their language
- Reports back symbol diffs for cross-language consistency checks

#### Test Agent
- Runs after every batch of changes
- Executes the full CI test matrix locally
- Reports failures with AST-level context (which function, which branch)
- Uses `coverage_map` to identify untested code paths

#### Documentation Agent
- Generates and updates doc comments across all languages
- Maintains README.md, CLAUDE.md, and AGENTS.md
- Cross-references the docs/ directory for consistency

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

## Principles for All Agents

### 1. Minimize Dependencies
- No new external packages without explicit human approval
- If a feature needs a library, implement it inline
- The goal is zero-dependency simulators that build with only the language toolchain

### 2. Zero Network Surface
- Simulator binaries must not open sockets, make HTTP requests, or listen on ports
- The only exception is the Go SSE server (`apps/go/cmd/server/`), which is a
  separate binary from the simulator
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
