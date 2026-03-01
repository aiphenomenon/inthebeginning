# AST Reactive Agent Pair: Steering Guide for Reuse

## Purpose

This document enables engineers to adopt the **AST reactive agent pair** technique in their projects using Claude Code, Claude.ai, Jules, Codex, SERA, or similar AI coding tools.

The core idea: instead of feeding full source code to an LLM, use a **local AST analysis tool** that exchanges **structured CueSignals** with the LLM. This reduces context window usage by **27x** while providing richer code intelligence.

## Quick Start

### For Claude Code (gVisor sandbox)

Claude Code runs inside gVisor with full access to Python, Node.js, Go, Java, Rust, Perl, and PHP runtimes.

**Step 1**: Copy the `ast_dsl/` directory into your project.

**Step 2**: Use the reactive protocol in your workflow:

```python
from ast_dsl.reactive import ReactiveProtocol

protocol = ReactiveProtocol(session_id="my-session")

# Analyze a file
result = protocol.run_query("symbols", "src/main.py")
# result.payload contains structured symbol data

# The LLM reads this compact result, decides next action
result = protocol.run_query("dependencies", "src/main.py")

# Synthesize everything learned
result = protocol.process_cue(CueSignal(cue_type=CueType.SYNTHESIZE))
```

**Step 3**: Use compact representations to minimize context:

```python
# Full JSON: ~50KB per file
result.to_dict()

# Compact text: ~2KB per file (27x smaller)
result.to_compact()
```

### For Claude.ai (Web Interface)

Add this to your system prompt or paste as context:

```
You have access to an AST analysis tool. When analyzing code:

1. Request parsing: {"action": "parse", "target": "filename.py"}
2. The tool returns compact AST: NodeType:name@line[attrs]{children}
3. Request symbols: {"action": "symbols", "target": "filename.py"}
4. Request dependencies: {"action": "dependencies", "target": "filename.py"}
5. Request metrics: {"action": "metrics", "target": "filename.py"}

Compact AST format example:
Module@0{FunctionDef:add@10[args=['a','b']]{Return@11};ClassDef:Calc@15}

Use this to understand code structure without needing full source.
```

### For Jules (Anthropic Code Agent)

Jules can invoke the AST tool as a subprocess:

```bash
# In your CLAUDE.md or project config:
python3 -c "
from ast_dsl.core import ASTEngine, ASTQuery
import json, sys
engine = ASTEngine()
result = engine.execute(ASTQuery(action=sys.argv[1], target=sys.argv[2]))
print(json.dumps(result.to_dict(), default=str))
" symbols src/main.py
```

### For Codex (OpenAI)

Adapt the tool calling format:

```json
{
  "type": "function",
  "function": {
    "name": "ast_analyze",
    "description": "Analyze source code AST",
    "parameters": {
      "type": "object",
      "properties": {
        "action": {"type": "string", "enum": ["parse", "symbols", "dependencies", "metrics", "coverage_map"]},
        "target": {"type": "string", "description": "File path"},
        "language": {"type": "string", "default": "python"}
      }
    }
  }
}
```

### For SERA and Other Agents

The generic integration pattern:

1. **Install**: Copy `ast_dsl/` into the project
2. **Invoke**: Call via subprocess or Python import
3. **Parse result**: JSON with `success`, `data`, `metrics` fields
4. **Use compact**: Call `.to_compact()` to minimize token usage
5. **Iterate**: Use the reactive protocol for multi-step analysis

## The Reactive Protocol

### CueTypes

| CueType | Direction | Purpose |
|---------|-----------|---------|
| `QUERY` | LLM → Tool | Request analysis |
| `RESULT` | Tool → LLM | Return structured data |
| `REFINE` | LLM → Tool | Modify previous query |
| `TRANSFORM` | LLM → Tool | Request code transformation |
| `SYNTHESIZE` | LLM → Tool | Summarize accumulated state |
| `COMPLETE` | Either | Signal end of interaction |

### AgentState

The protocol tracks shared state:

```python
@dataclass
class AgentState:
    session_id: str       # Unique session identifier
    turn: int             # Interaction count
    history: list         # All cue signals exchanged
    discovered_symbols: list   # Accumulated symbol definitions
    discovered_deps: list      # Accumulated dependencies
    pending_transforms: list   # Requested but unapplied transforms
    total_tokens_used: int     # Token budget tracking
```

### Token Efficiency

| Data Type | Full JSON | Compact | Reduction |
|-----------|-----------|---------|-----------|
| Single file AST | ~50KB | ~2KB | 25x |
| Project AST (10 files) | ~500KB | ~20KB | 25x |
| Symbol list | ~15KB | ~1KB | 15x |
| Session state | ~5KB | ~200B | 25x |

## Language Support Matrix

| Language | Parser | AST Quality | Dependencies |
|----------|--------|-------------|-------------|
| Python | `ast` module | Full (native) | None |
| JavaScript | Acorn | Full | `npm install acorn` |
| Go | `go/ast` | Full (native) | None |
| C | pycparser | Full | `pip install pycparser` |
| C++ | clang | Full | `clang` binary |
| Java | Regex + javac | Good (heuristic) | JDK (optional) |
| Rust | Regex + rustc | Good (heuristic) | rustc (optional) |
| Perl | Regex + B::Deparse | Good (heuristic) | perl (optional) |
| PHP | Regex + token_get_all | Good (heuristic) | PHP (optional) |

## Prompt Templates

### Code Refactoring

```
Using the AST tool, analyze {file} for refactoring opportunities:

1. Parse the file to get structure
2. Find all symbols to understand the API surface
3. Get dependencies to understand coupling
4. Compute metrics to identify complexity hotspots
5. Generate coverage map to ensure tests exist

Based on the AST analysis, suggest specific refactorings
with file:line references.
```

### Dead Code Detection

```
Using the AST tool, find dead code in {directory}:

1. For each .py file, extract all symbol definitions
2. For each .py file, extract all call sites
3. Cross-reference: symbols defined but never called are dead
4. Exception: exported symbols (__all__), test functions

Report dead code with file:line references.
```

### Dependency Analysis

```
Using the AST tool, analyze the dependency graph of {project}:

1. For each module, extract import statements
2. Build a dependency graph (module → dependencies)
3. Identify circular dependencies
4. Identify modules with high fan-in (many dependents)
5. Identify modules with high fan-out (many dependencies)

Suggest architectural improvements based on coupling analysis.
```

### Test Coverage Generation

```
Using the AST tool, generate tests for uncovered code in {file}:

1. Get the coverage map (testable functions with branch counts)
2. For each untested function, analyze:
   - Input parameters and types
   - Branch conditions
   - Return values
   - Side effects
3. Generate test cases that cover all branches
4. Use the compact AST to verify test completeness
```

## Performance Guidelines

### When to Use Full vs Compact AST

| Scenario | Use Full | Use Compact |
|----------|----------|-------------|
| Initial code understanding | | X |
| Specific symbol lookup | X | |
| Cross-file analysis | | X |
| Refactoring planning | | X |
| Code generation | X | |
| Review/audit | | X |

### Token Budget Strategy

For a 200K token context window:

1. **Reserve 50K** for conversation history
2. **Reserve 50K** for LLM reasoning
3. **Use 100K** for code context

With compact AST (27x reduction):
- Can analyze **~50 files** per session (vs ~2 with full source)
- Can hold entire small project structure in context

### Caching Strategy

```python
engine = ASTEngine()
# Cache is keyed by (filepath, mtime)
# First parse: ~5ms
result1 = engine.parse_file("module.py")
# Cached parse: <0.1ms
result2 = engine.parse_file("module.py")
```

## Example Workflow: Cross-File Rename

```python
protocol = ReactiveProtocol()

# Step 1: Find the symbol
result = protocol.run_query("symbols", "src/utils.py",
                           filters={"name": "old_name"})

# Step 2: Find all callers across the project
for py_file in glob("src/**/*.py"):
    result = protocol.run_query("callers", py_file,
                               filters={"name": "old_name"})

# Step 3: Apply transform
for py_file in files_with_calls:
    protocol.run_query("transform", py_file,
                      filters={"transform": "rename",
                               "old_name": "old_name",
                               "new_name": "new_name"})

# Step 4: Verify
result = protocol.process_cue(CueSignal(cue_type=CueType.SYNTHESIZE))
```

## Extending to New Languages

To add a new language:

1. Create `ast_dsl/newlang_ast.py`
2. Implement `parse_newlang_source(source) -> ASTNode`
3. Implement `find_newlang_symbols(source) -> list`
4. Implement `to_compact(node) -> str`
5. Register the parser in `ASTEngine._parsers`

The universal `ASTNode` format ensures cross-language compatibility.
