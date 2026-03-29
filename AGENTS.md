# AGENTS.md -- Multi-Agent Coordination Protocol

This file defines the AST-passing protocol, agent roles, and coordination rules
for multi-agent work on this repository. For engineering rules, test commands,
session logging, and deployment details, see `CLAUDE.md`.

---

## Table of Contents

1. [AST-Passing Architecture](#ast-passing-architecture)
2. [CueSignal Reactive Protocol](#cuesignal-reactive-protocol)
3. [Token Efficiency](#token-efficiency)
4. [Pre-Generated AST Captures](#pre-generated-ast-captures)
5. [AST-Guided Code Generation](#ast-guided-code-generation)
6. [Agent Roles](#agent-roles)
7. [Coordination Protocol](#coordination-protocol)
8. [Commit Conventions](#commit-conventions)

---

## AST-Passing Architecture

This project uses an AST-passing architecture to minimize context window usage.
Instead of passing raw source files, agents exchange compact AST representations.

### How It Works

1. **Parse**: `ast_dsl/` parses source files into a universal `ASTNode` tree.
   Each language has a dedicated parser (e.g., `python_ast.py`, `go_ast.go`).

2. **Compact representation**: `ASTNode.to_compact()` produces minimal strings
   like `FunctionDef:evolve@49[args=self,dt]{...}` -- structure without source text.

3. **Query interface**: `ASTEngine.execute(ASTQuery)` supports:
   - `parse` -- full AST of a file
   - `find` -- search by node type or name
   - `symbols` -- extract all definitions
   - `dependencies` -- extract imports
   - `callers` -- find call sites
   - `metrics` -- cyclomatic complexity, node counts
   - `coverage_map` -- identify testable paths
   - `transform` -- rename, extract, inline

4. **Performance tracking**: Every query returns `PerformanceMetrics` with wall
   time, CPU time, memory, and approximate token counts.

### Quick Code Reference

```python
from ast_dsl import ReactiveProtocol

proto = ReactiveProtocol(session_id="current-task")
result = proto.run_query("symbols", "path/to/file.py")
print(result.to_compact())

# Dependencies, callers, metrics, coverage
result = proto.run_query("dependencies", "path/to/file.py")
result = proto.run_query("callers", "path/to/file.py",
                         filters={"name": "function_name"})
result = proto.run_query("metrics", "path/to/file.py")
result = proto.run_query("coverage_map", "path/to/file.py")
```

### Deep Python Analysis (PythonASTAnalyzer)

```python
from ast_dsl.python_ast import PythonASTAnalyzer
analyzer = PythonASTAnalyzer()

scopes = analyzer.analyze_scopes(source_code)       # Variable reads/writes
cfg = analyzer.extract_control_flow(source_code)     # Control flow graph
dead = analyzer.find_dead_code(source_code)          # Unreachable statements
stubs = analyzer.generate_test_stubs(source_code, "module_name")  # Test scaffolding
```

---

## CueSignal Reactive Protocol

The AST-passing workflow uses a reactive protocol where agent and AST engine
exchange structured CueSignal messages.

### Signal Types

| CueType | Direction | Purpose |
|---------|-----------|---------|
| `QUERY` | Agent -> Engine | Request analysis (payload: ASTQuery) |
| `RESULT` | Engine -> Agent | Return results (payload: ASTResult) |
| `REFINE` | Agent -> Engine | Re-execute with modified params (links via `parent_id`) |
| `TRANSFORM` | Agent -> Engine | Request code transformation |
| `SYNTHESIZE` | Engine -> Agent | Combine accumulated state into summary |
| `COMPLETE` | Either | Signal interaction complete |

### Typical Exchange

```
#1 QUERY(symbols, app.py)
  #2 RESULT(...)
  #3 REFINE(callers, name="process_data")  parent_id=1
    #4 RESULT(...)
#5 TRANSFORM(rename, old="process_data", new="transform_data")
  #6 RESULT(transformed_ast=...)
#7 SYNTHESIZE
  #8 RESULT(all_symbols, all_deps, history)
#9 COMPLETE
```

### AgentState Tracking

State persists across the session:

```python
@dataclass
class AgentState:
    session_id: str
    turn: int
    history: list
    context: dict
    discovered_symbols: list
    discovered_deps: list
    pending_transforms: list
    total_tokens_used: int
```

Compact representation: `s:a1b2c3d4 t:6 sym:30 dep:6 tok:62017`

---

## Token Efficiency

The compact AST format achieves **27x compression** over full JSON AST:

| Representation | Size | Approx Tokens |
|----------------|------|---------------|
| Raw source (all .py files) | ~50 KB | ~12,500 |
| Full JSON AST | 16,443,157 B | ~4,110,000 |
| Compact AST | 602,783 B | ~150,000 |
| Symbol summary | 149,908 B | ~37,000 |

Per-query costs:

| Query Type | Typical Size | Tokens |
|------------|-------------|--------|
| `symbols` (one file) | 200-2,000 B | 50-500 |
| `dependencies` (one file) | 100-500 B | 25-125 |
| `callers` (one symbol) | 50-500 B | 12-125 |
| `metrics` (one file) | 100-200 B | 25-50 |
| `coverage_map` (one file) | 200-1,000 B | 50-250 |

**Rule of thumb**: A targeted query costs ~100 tokens vs ~3,000 for the raw file.

### Budget Guidelines

- Prefer `to_compact()` over `to_dict()` (5-10x smaller)
- Use `depth` parameter to limit tree depth
- Request `symbols` before `parse` to decide what needs full analysis
- Use `coverage_map` to target test generation without parsing entire files

---

## Pre-Generated AST Captures

`ast_captures/` contains pre-computed snapshots:
- `symbols.json` -- all symbol definitions
- `coverage_map.json` -- testable code paths
- `compact_ast.txt` -- full compact AST

Read these at session start for a global codebase overview. Regenerate at end of
session to keep current. Versioned in git -- use `git log -- ast_captures/` to
track program evolution.

### Regeneration

```python
from ast_dsl.core import ASTEngine, ASTQuery
import json, os

engine = ASTEngine()
base = "/path/to/project"
py_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(base)
            for f in sorted(fn) if f.endswith('.py')
            if not any(d.startswith('.') or d == 'node_modules' for d in dp.split('/'))]

symbols = {}
for fp in py_files:
    result = engine.execute(ASTQuery(action="symbols", target=fp, language="python"))
    if result.success and isinstance(result.data, list):
        symbols[os.path.relpath(fp, base)] = result.data

with open(os.path.join(base, "ast_captures", "symbols.json"), "w") as f:
    json.dump(symbols, f, indent=2)
```

---

## AST-Guided Code Generation

Use AST introspection to prevent bugs before they occur.

### Before Editing

1. **Query symbols** -- prevents duplicate definitions, naming collisions
2. **Query dependencies** -- prevents broken imports, circular deps
3. **Query callers** (before rename/move) -- prevents broken call sites

### After Editing

1. **Re-parse** -- verify syntactic validity
2. **Run coverage_map** -- identify untested branches
3. **Cross-check interfaces** -- verify signatures match callers

### Bug Classes Prevented

| Bug Class | Query | Prevention |
|-----------|-------|------------|
| Broken imports | `dependencies` | Verify targets exist |
| Type mismatches | `symbols` + `callers` | Cross-check signatures |
| Dead code | `coverage_map` | Find unreachable branches |
| Duplicate definitions | `symbols` | Detect collisions |
| Missing coverage | `coverage_map` | Generate stubs for gaps |
| Circular dependencies | `dependencies` (multi-file) | Check import graph |
| Stale references | `callers` | Find all call sites before rename |

---

## Agent Roles

### Orchestrator Agent
- Maintains task queue, assigns files to specialists, merges results
- Runs full test suite after batch changes

### Language Specialist Agents
- Assigned per-language; uses AST queries to understand structure
- Implements changes following the dependency and coding rules in `CLAUDE.md`

### Test Agent
- Runs after batch changes; executes CI matrix
- Reports failures with AST context (symbols, callers of failing code)

### Documentation Agent
- Generates doc comments in language-appropriate format
- Maintains README and docs consistency

---

## Coordination Protocol

### File Locking

- Check `git status` before modifying shared files
- Prefer separate files over concurrent edits to the same file
- Coordinate through the orchestrator for multi-file changes

### Cross-Language Consistency

When physics engine changes are made:
1. Run `python ast_dsl/introspect.py` to compare function signatures
2. Verify physical constants match across implementations
3. Run `tests/test_cross_language_parity.py` to verify epoch transitions

---

## Commit Conventions

Format: `<type>(<scope>): <description>`

**Types**: feat, fix, test, docs, refactor, ci, build

**Scopes**: python, nodejs, go, rust, c, cpp, java, perl, php, typescript,
kotlin, swift, wasm, screensaver, ast, ci, audio, deploy
