# AST DSL Reactive Agent Pair -- Steering & Reuse Guide

> **Purpose**: Enable engineers to reuse the AST-reactive-agent-pair technique in any project, with any LLM-powered coding tool -- Claude Code, Claude.ai, Jules, Codex, SERA, or custom agents.

---

## Table of Contents

1. [Concept Overview](#1-concept-overview)
2. [How to Integrate](#2-how-to-integrate)
3. [The Reactive Protocol](#3-the-reactive-protocol)
4. [Language Support Matrix](#4-language-support-matrix)
5. [Prompt Templates](#5-prompt-templates)
6. [Performance Guidelines](#6-performance-guidelines)
7. [Example Workflows](#7-example-workflows)

---

## 1. Concept Overview

### The Problem

LLMs doing code intelligence face a fundamental constraint: context windows are finite, but codebases are not. Passing full source files into an LLM burns tokens at a rate that makes multi-file analysis impractical. A 10-file Python project can easily consume 40,000 tokens of raw source, leaving little room for reasoning.

### The Solution: AST DSL Reactive Agent Pair

Instead of passing raw source code, a **local analysis tool** parses source into structured AST representations and exchanges **CueSignals** with an LLM in a reactive loop. The LLM never sees raw source -- it works with compact, structured summaries that carry the same semantic information at a fraction of the token cost.

The architecture has two halves:

```
+------------------+       CueSignal         +------------------+
|                  | -----------------------> |                  |
|   LLM Agent      |   QUERY / REFINE /       |   AST Engine     |
|   (Claude, GPT,  |   TRANSFORM              |   (local tool,   |
|    any model)    | <----------------------- |    gVisor, etc.) |
|                  |   RESULT / SYNTHESIZE /   |                  |
+------------------+   COMPLETE               +------------------+
```

**Key insight**: The compact AST representation is **27x smaller** than the full JSON AST and carries equivalent structural information. In measured runs on this codebase:

| Representation | Size | Approx Tokens |
|---|---|---|
| Raw source (all .py files) | ~50 KB | ~12,500 |
| Full JSON AST | 16,443,157 bytes | ~4,110,000 |
| Compact AST | 602,783 bytes | ~150,000 |
| Symbol summary | 149,908 bytes | ~37,000 |
| Coverage map | 94,608 bytes | ~23,000 |

The compact format achieves this by encoding the AST as a single-line nested expression:

```
FunctionDef:add@29[args=['self', 'a', 'b'],decorators=0,is_async=False]{...children...}
```

versus the full JSON:

```json
{
  "type": "FunctionDef",
  "name": "add",
  "line": 29,
  "col": 4,
  "end_line": 32,
  "end_col": 21,
  "attrs": {
    "args": ["self", "a", "b"],
    "decorators": 0,
    "is_async": false
  },
  "children": [...]
}
```

### Core Data Structures

**ASTNode** -- Universal cross-language AST node:

```python
@dataclass
class ASTNode:
    node_type: str          # "FunctionDef", "ClassDef", "Import", etc.
    name: str = ""          # Symbol name
    children: list = []     # Child nodes
    attributes: dict = {}   # Language-specific metadata
    line: int = 0           # Source location
    col: int = 0
    end_line: int = 0
    end_col: int = 0
    source_text: str = ""   # Truncated source snippet (max 200 chars)
```

**ASTQuery** -- Structured request to the engine:

```python
@dataclass
class ASTQuery:
    action: str       # parse, find, symbols, dependencies, callers, metrics, transform, coverage_map
    target: str = ""  # File path or source string
    language: str = "python"
    filters: dict = {}
    depth: int = -1   # -1 = unlimited
```

**CueSignal** -- Message passed between agent and tool:

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

---

## 2. How to Integrate

### 2.1 Claude Code (gVisor Sandbox)

Claude Code runs inside a gVisor sandbox with full Python and subprocess access. This is the most powerful integration path.

#### Step 1: Copy the AST DSL module into your project

```bash
# Copy the ast_dsl/ directory into your project
cp -r ast_dsl/ /path/to/your/project/ast_dsl/
```

Required files:
- `ast_dsl/__init__.py` -- Package exports
- `ast_dsl/core.py` -- ASTEngine, ASTNode, ASTQuery, ASTResult
- `ast_dsl/reactive.py` -- ReactiveProtocol, CueSignal, AgentState
- `ast_dsl/python_ast.py` -- Deep Python analysis (scopes, control flow, dead code, test stubs)
- `ast_dsl/java_ast.py` -- Java regex + javac parser
- `ast_dsl/rust_ast.py` -- Rust regex + rustc parser
- `ast_dsl/perl_ast.py` -- Perl regex + B::Deparse parser
- `ast_dsl/php_ast.py` -- PHP regex + token_get_all parser
- `ast_dsl/c_ast.py` -- C pycparser + clang parser

#### Step 2: Install language-specific dependencies

```bash
# Python: built-in, no install needed
# JavaScript: install acorn
npm install acorn

# C/C++: install pycparser (optional, for C parsing)
pip install pycparser

# Go, Java, Rust, Perl, PHP: the parsers shell out to the
# language toolchain (go, javac, rustc, perl, php) when available,
# falling back to regex parsing when they are not installed.
```

#### Step 3: Use in Claude Code sessions

When Claude Code starts a session, include this in your project instructions or CLAUDE.md:

````markdown
## AST Analysis Tool

This project includes an AST DSL reactive agent pair in `ast_dsl/`.
Use it for code intelligence instead of reading full source files.

### Quick start:
```python
from ast_dsl import ReactiveProtocol
proto = ReactiveProtocol(session_id="my-session")

# Get all symbols in a file
result = proto.run_query("symbols", "/path/to/file.py")

# Get import dependencies
result = proto.run_query("dependencies", "/path/to/file.py")

# Find callers of a function
result = proto.run_query("callers", "/path/to/file.py",
                         filters={"name": "my_function"})

# Get complexity metrics
result = proto.run_query("metrics", "/path/to/file.py")

# Generate coverage map
result = proto.run_query("coverage_map", "/path/to/file.py")
```

Always use `result.payload` for the structured data.
Use compact representations when reporting: `result.to_compact()`
````

#### Step 4: Pre-generate AST captures for large codebases

For codebases too large to parse on-the-fly, pre-generate captures:

```python
#!/usr/bin/env python3
"""Pre-generate AST captures for a codebase."""
import json
import os
from ast_dsl.core import ASTEngine, ASTQuery

engine = ASTEngine()
base = "/path/to/your/project"

# Walk and collect Python files
py_files = []
for dirpath, dirnames, filenames in os.walk(base):
    dirnames[:] = [d for d in dirnames
                   if not d.startswith('.') and d != 'node_modules']
    for f in sorted(filenames):
        if f.endswith('.py'):
            py_files.append(os.path.join(dirpath, f))

# Generate symbol index
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

Then point Claude Code at the pre-generated files:

```markdown
Pre-generated AST data is in `ast_captures/`:
- `symbols.json` -- All symbol definitions across the codebase
- `coverage_map.json` -- Testable code paths
- `compact_ast.txt` -- Full compact AST (use for structural queries)
Read these instead of parsing source files directly when possible.
```

### 2.2 Claude.ai (Web Interface)

Claude.ai has no filesystem or subprocess access. The integration pattern relies on the **user pasting compact AST output** or the **system prompt describing the format**.

#### Option A: User-Generated Compact AST

Run the AST engine locally, paste the compact output into the conversation:

```bash
# Generate compact output locally
python3 -c "
from ast_dsl import ReactiveProtocol
proto = ReactiveProtocol()
result = proto.run_query('symbols', 'src/main.py')
import json
print(json.dumps(result.payload, indent=2))
"
```

Then paste the output into Claude.ai with a prompt like:

```
Here is the symbol table for my project. Using this structure,
identify which functions are candidates for refactoring:

[paste symbols.json output here]
```

#### Option B: System Prompt with Format Description

For Claude.ai Projects or custom system prompts, embed the compact AST format specification so the LLM can interpret AST data the user provides:

```
You understand the following compact AST format:

NodeType:name@line[attr1=val1,attr2=val2]{child1;child2}

Where:
- NodeType is the AST node type (FunctionDef, ClassDef, Import, etc.)
- name is the symbol name
- @line is the source line number
- [attrs] are comma-separated key=value metadata
- {children} are semicolon-separated child nodes in the same format

Example:
ClassDef:Calculator@5[bases=['object'],decorators=0]{FunctionDef:add@7[args=['self','a','b']];FunctionDef:divide@12[args=['self','a','b']]}

When the user provides AST data in this format, interpret it as
a code structure summary and use it to answer code intelligence
questions without requiring the full source code.

CueSignal protocol:
- QUERY: user asks you to analyze structure
- RESULT: you return analysis
- REFINE: user asks follow-up question
- TRANSFORM: user requests code change plan
- SYNTHESIZE: you combine multiple results
- COMPLETE: analysis is done

Track state across turns:
- Discovered symbols (accumulate across queries)
- Dependencies (import graph)
- Pending transforms (planned changes)
```

#### Option C: Upload Pre-Generated Files

If using Claude.ai with file upload:

1. Generate `symbols.json` and `compact_ast.txt` locally
2. Upload them to the conversation
3. Claude can reference them throughout the session

### 2.3 Jules (Anthropic Code Agent)

Jules is Anthropic's autonomous code agent that can run multi-step tasks. It has filesystem access within its workspace.

#### Integration Pattern

1. **Include `ast_dsl/` in the repository** -- Jules clones the repo and has access to the module.

2. **Add a `.jules` or project config** that tells Jules about the tool:

````markdown
# Jules Project Instructions

## Available Tools
This project includes `ast_dsl/` for AST-based code intelligence.

Before modifying code, run AST analysis:
```python
from ast_dsl import ReactiveProtocol
proto = ReactiveProtocol()

# Understand the file structure before editing
result = proto.run_query("symbols", "path/to/file.py")
# Check dependencies before refactoring
result = proto.run_query("dependencies", "path/to/file.py")
# Identify callers before renaming
result = proto.run_query("callers", "path/to/file.py",
                         filters={"name": "old_function_name"})
```

Use compact representations in your reasoning to conserve context.
````

3. **Multi-step workflow pattern for Jules**:

```
Task: Refactor the Calculator class

Step 1: Query symbols
  proto.run_query("symbols", "calculator.py")

Step 2: Query dependencies
  proto.run_query("dependencies", "calculator.py")

Step 3: Find all callers of the method being changed
  proto.run_query("callers", "calculator.py",
                  filters={"name": "add"})

Step 4: Plan the transformation
  [Jules reasons about the changes using compact AST data]

Step 5: Apply changes to source files
  [Jules edits the actual source code]

Step 6: Verify with another symbols query
  proto.run_query("symbols", "calculator.py")
```

### 2.4 Codex (OpenAI)

Codex uses a different tool-calling format. The AST DSL module works the same way, but the tool registration differs.

#### Tool Definition for Codex / OpenAI Function Calling

```json
{
  "type": "function",
  "function": {
    "name": "ast_query",
    "description": "Execute an AST query on source code. Returns structured analysis without requiring full source in context. Supported actions: parse, find, symbols, dependencies, callers, metrics, transform, coverage_map.",
    "parameters": {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["parse", "find", "symbols", "dependencies", "callers", "metrics", "transform", "coverage_map"],
          "description": "The analysis action to perform"
        },
        "target": {
          "type": "string",
          "description": "File path or source code string to analyze"
        },
        "language": {
          "type": "string",
          "enum": ["python", "javascript", "go", "c", "cpp", "java", "rust", "perl", "php"],
          "default": "python"
        },
        "filters": {
          "type": "object",
          "description": "Action-specific filters. For 'find': {node_type, name}. For 'callers': {name}. For 'transform': {transform, old_name, new_name}.",
          "properties": {
            "node_type": {"type": "string"},
            "name": {"type": "string"},
            "transform": {"type": "string"},
            "old_name": {"type": "string"},
            "new_name": {"type": "string"}
          }
        }
      },
      "required": ["action", "target"]
    }
  }
}
```

#### Tool Handler Implementation

```python
import json
from ast_dsl import ReactiveProtocol

# Persistent protocol instance across tool calls
_protocol = ReactiveProtocol(session_id="codex-session")

def handle_ast_query(action: str, target: str,
                     language: str = "python",
                     filters: dict = None) -> str:
    """Handler for the ast_query tool call."""
    result = _protocol.run_query(
        action=action,
        target=target,
        language=language,
        filters=filters or {},
    )
    # Return compact representation to minimize token usage
    return result.to_compact()
```

#### System Prompt Addon for Codex

```
You have access to an ast_query tool that analyzes source code structure.
Use it instead of reading full source files. The tool returns compact
AST representations that are 27x more token-efficient than raw source.

Workflow:
1. Use ast_query(action="symbols", target="file.py") to understand structure
2. Use ast_query(action="dependencies", target="file.py") for imports
3. Use ast_query(action="callers", target="file.py", filters={"name":"fn"})
   to find all call sites before making changes
4. Only read raw source for the specific lines you need to edit
```

### 2.5 SERA and Other Agents -- Generic Integration Pattern

For any LLM-powered coding agent with tool/function calling:

#### Step 1: Define the Tool Interface

Every agent framework has a way to register tools. The interface is always the same:

```
Tool Name: ast_query
Input:
  - action (string): parse | find | symbols | dependencies | callers | metrics | transform | coverage_map
  - target (string): file path
  - language (string, optional): python | javascript | go | c | cpp | java | rust | perl | php
  - filters (object, optional): action-specific parameters
Output:
  - Compact AST string or JSON result
```

#### Step 2: Implement the Handler

```python
from ast_dsl import ReactiveProtocol

class ASTToolHandler:
    def __init__(self):
        self.protocol = ReactiveProtocol()

    def __call__(self, action: str, target: str,
                 language: str = "python",
                 filters: dict = None) -> dict:
        result = self.protocol.run_query(
            action=action,
            target=target,
            language=language,
            filters=filters or {},
        )
        return {
            "compact": result.to_compact(),
            "state": self.protocol.state.to_compact(),
        }
```

#### Step 3: Add to Agent System Prompt

```
You have an ast_query tool for code intelligence. It parses source
files into structured AST summaries without requiring full source
in your context window.

Always prefer ast_query over reading raw files for:
- Understanding code structure (action="symbols")
- Finding imports and dependencies (action="dependencies")
- Locating function call sites (action="callers")
- Measuring complexity (action="metrics")
- Planning test coverage (action="coverage_map")

Only read raw source when you need to see exact implementation
details for a specific function.
```

---

## 3. The Reactive Protocol

### 3.1 CueTypes

The protocol defines six signal types that form a conversation between the LLM and the local tool:

| CueType | Direction | Purpose |
|---|---|---|
| `QUERY` | LLM -> Tool | Request analysis. Payload is an ASTQuery dict. |
| `RESULT` | Tool -> LLM | Return analysis results. Payload is an ASTResult dict. |
| `REFINE` | LLM -> Tool | Re-execute a previous query with modified parameters. Links to parent via `parent_id`. |
| `TRANSFORM` | LLM -> Tool | Request a code transformation (rename, extract). Payload includes transform filters. |
| `SYNTHESIZE` | Tool -> LLM | Combine accumulated state into a summary. Returns all discovered symbols, dependencies, and history. |
| `COMPLETE` | Either | Signal that the interaction is finished. Includes final state summary. |

### 3.2 Typical Cue Exchange

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

### 3.3 AgentState

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

This tells the LLM: session `a1b2c3d4`, turn 6, 30 symbols found, 6 dependencies found, ~62K tokens used so far.

### 3.4 Token Efficiency

The compact format achieves **27x compression** over full JSON AST:

| Format | This Codebase | Tokens (approx) |
|---|---|---|
| Full JSON AST | 16,443,157 bytes | ~4,110,000 |
| Compact AST | 602,783 bytes | ~150,000 |
| **Compression ratio** | **27.3x** | |

Even the compact AST is large for a context window. For iterative work, use targeted queries:

| Query Type | Typical Result Size | Tokens |
|---|---|---|
| `symbols` (one file) | 200-2,000 bytes | 50-500 |
| `dependencies` (one file) | 100-500 bytes | 25-125 |
| `callers` (one symbol) | 50-500 bytes | 12-125 |
| `metrics` (one file) | 100-200 bytes | 25-50 |
| `coverage_map` (one file) | 200-1,000 bytes | 50-250 |

**Rule of thumb**: A single targeted query costs ~100 tokens. Reading the raw source of the same file would cost ~3,000 tokens. That is a **30x saving per query**.

### 3.5 Sequence and Refinement Tracking

Every CueSignal carries a `sequence_id` (monotonically increasing) and an optional `parent_id`. This creates a tree of queries:

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

This lets the LLM (or a human reviewing the log) understand the reasoning chain.

---

## 4. Language Support Matrix

| Language | Parser | AST Depth | Fallback | Symbol Extraction | Dependency Extraction | Notes |
|---|---|---|---|---|---|---|
| **Python** | Built-in `ast` module | Full AST | N/A | Full (functions, classes, async) | Full (import, from-import) | Includes scope analysis, control flow, dead code detection, test stub generation |
| **JavaScript** | Acorn (npm) | Full AST | N/A | Full | Full | Requires `npm install acorn`; invoked via subprocess |
| **Go** | `go/ast` package | Full AST | N/A | Full | Full | Requires Go toolchain; invoked via `go` CLI |
| **Java** | Regex-based | Declarations only | `javac -Xprint` | Classes, interfaces, enums, records, methods | Package, import (including static) | Regex parser does not handle nested classes perfectly |
| **Rust** | Regex-based | Declarations only | `rustc -Z unpretty=ast-tree` | Structs, enums, traits, impl blocks, functions (sync and async) | use, mod | Regex handles generics and visibility; rustc fallback requires nightly |
| **C** | pycparser (pip) | Full AST | N/A | Functions, structs, unions, enums, typedefs | N/A (C has no module system) | Requires `pip install pycparser` |
| **C++** | clang `-ast-dump` | Full AST | N/A | Full | Includes | Requires clang installed; parses `-ast-dump` output |
| **Perl** | Regex-based | Declarations only | `perl -MO=Deparse` | Packages, subs, variables (my/our/local), method calls | use, require | Detects variable scoping and arrow-notation method calls |
| **PHP** | Regex-based | Declarations only | `php` + `token_get_all` | Namespaces, classes, interfaces, traits, enums, functions | use (with aliases) | Token-based fallback provides more accurate results; detects return types |

### Parser Detail: Python (`ast_dsl/python_ast.py`)

Python gets the deepest analysis because the `ast` module provides a full, typed AST. The `PythonASTAnalyzer` class provides:

- **Scope analysis** (`analyze_scopes`): Identifies variable reads and writes per function scope. Useful for understanding side effects and data flow.
- **Control flow extraction** (`extract_control_flow`): Builds control flow graph edges -- branches (if), loops (for, while), returns, raises, try/except blocks.
- **Dead code detection** (`find_dead_code`): Finds statements after return or raise that can never execute.
- **Test stub generation** (`generate_test_stubs`): Auto-generates unittest class and method stubs for every public function and class method.

### Parser Detail: Java (`ast_dsl/java_ast.py`)

The Java parser uses regex patterns to extract:
- Package declarations
- Import statements (including `static` imports)
- Class, interface, enum, and record declarations with extends/implements
- Method declarations with return types and parameter counts

When `javac` is available, it falls back to `javac -Xprint` for more accurate parsing.

### Parser Detail: Rust (`ast_dsl/rust_ast.py`)

The Rust parser uses regex patterns to extract:
- `use` declarations
- `mod` declarations
- Struct, enum, trait declarations with visibility
- Impl blocks (including trait implementations)
- Function declarations with async, visibility, return type, and parameter count

When `rustc` nightly is available, it can use `-Z unpretty=ast-tree` for the full AST.

### Parser Detail: C/C++ (`ast_dsl/c_ast.py`)

Two parsing strategies:
- **C**: Uses `pycparser` (pure Python C parser) for full AST access.
- **C++**: Uses `clang -ast-dump -fsyntax-only` and parses the indented text output into universal AST nodes.

### Parser Detail: Perl (`ast_dsl/perl_ast.py`)

Regex-based extraction of:
- `use` and `require` declarations (with arguments)
- `package` declarations
- `sub` declarations (with prototypes)
- Arrow-notation method calls (`->method()`)
- Variable declarations with scope (`my`, `our`, `local`)

Falls back to `perl -MO=Deparse` for deeper analysis when Perl is available.

### Parser Detail: PHP (`ast_dsl/php_ast.py`)

Regex-based extraction of:
- Namespace declarations
- `use` declarations (with aliases)
- Class, interface, trait, and enum declarations (with modifiers, extends, implements)
- Function declarations (with parameter counts and return types)

Falls back to PHP's `token_get_all()` function for token-level accuracy.

### Adding a New Language

To add support for a new language, create a module following this pattern:

```python
"""<Language> AST introspection."""
import re
from ast_dsl.core import ASTNode

def parse_<lang>_source(source: str,
                        filename: str = "<string>") -> ASTNode:
    """Parse <language> source into universal AST."""
    root = ASTNode(node_type="<RootType>", name=filename)

    # 1. Extract imports / dependencies
    for m in re.finditer(r"<import_pattern>", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="ImportDecl",
            name=m.group(1),
            line=line,
        ))

    # 2. Extract type declarations (classes, structs, etc.)
    for m in re.finditer(r"<type_pattern>", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="TypeDecl",
            name=m.group(1),
            line=line,
        ))

    # 3. Extract function declarations
    for m in re.finditer(r"<function_pattern>", source):
        line = source[:m.start()].count("\n") + 1
        root.children.append(ASTNode(
            node_type="FunctionDecl",
            name=m.group(1),
            line=line,
        ))

    return root

def find_<lang>_symbols(source: str) -> list:
    """Extract all symbols."""
    root = parse_<lang>_source(source)
    symbols = []
    for node in root.walk():
        if node.node_type.endswith("Decl") and node.name:
            symbols.append({
                "type": node.node_type,
                "name": node.name,
                "line": node.line,
            })
    return symbols

def to_compact(node: ASTNode) -> str:
    """Compact representation."""
    return node.to_compact()
```

Then register the parser in `core.py` by adding the language to the `Language` enum and registering the parse function in `ASTEngine._parsers`.

---

## 5. Prompt Templates

### 5.1 Claude Code -- Project Instructions (CLAUDE.md)

Copy this block into your `CLAUDE.md` or project instructions:

````markdown
## AST-Reactive Code Intelligence

This project uses the AST DSL reactive agent pair for token-efficient
code analysis. The module is in `ast_dsl/`.

### Usage Rules
1. ALWAYS use AST queries before reading raw source files
2. Use compact representations in reasoning to conserve context
3. Track discovered symbols across queries -- do not re-query
4. Use SYNTHESIZE to get accumulated state when planning multi-file changes

### Quick Reference

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

### Deep Python Analysis

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
````

### 5.2 Claude.ai -- System Prompt

Use this as a system prompt in Claude.ai Projects:

```
You are a code intelligence assistant that understands compact AST notation.

## Compact AST Format
Nodes are encoded as: NodeType:name@line[key=val,...]{child1;child2;...}

Examples:
  Module{Import:os@1;Import:sys@2;ClassDef:App@4[bases=['object']]{FunctionDef:run@5[args=['self']]}}
  FunctionDef:process@10[args=['data','config'],is_async=True]{If@12{Return@13};Return@15}

## Your Capabilities
When the user provides AST data in this format, you can:
1. Identify function signatures, class hierarchies, and module structure
2. Trace call graphs and dependency chains
3. Find potential dead code (statements after return/raise)
4. Suggest refactoring opportunities (long functions, deep nesting)
5. Plan test coverage based on branch complexity
6. Identify missing error handling

## Token Efficiency Protocol
- Work from compact AST data, not raw source
- When you need more detail, ask the user to query a specific symbol
- Accumulate findings across conversation turns
- Synthesize conclusions from structural data

## CueSignal Interaction
If the user is running a reactive protocol session, they may provide:
- cue:query#N -- they are asking you to analyze
- cue:result#N -- they are showing you tool output
- cue:refine#N<-#M -- follow-up to a previous query

Respond with your analysis and suggest next queries if needed.
```

### 5.3 Jules -- Task Instructions

```markdown
## Task: [Describe the task]

### Available Tooling
The `ast_dsl/` module provides AST-based code intelligence.
Use it to understand code structure before making changes.

### Mandatory Pre-Analysis Steps
Before editing any file, run these in order:

1. `proto.run_query("symbols", "<file>")` -- understand what is in the file
2. `proto.run_query("dependencies", "<file>")` -- understand what it imports
3. `proto.run_query("callers", "<file>", filters={"name": "<symbol>"})` -- find call sites

### Post-Change Verification
After editing, re-run:
1. `proto.run_query("symbols", "<file>")` -- verify the structure is correct
2. `proto.run_query("metrics", "<file>")` -- verify complexity did not increase
```

### 5.4 Codex -- System Message

```
You have an ast_query function for code analysis.

Usage:
  ast_query(action="symbols", target="file.py")
  ast_query(action="dependencies", target="file.py")
  ast_query(action="callers", target="file.py", filters={"name": "fn"})
  ast_query(action="metrics", target="file.py")
  ast_query(action="coverage_map", target="file.py")
  ast_query(action="find", target="file.py", filters={"node_type": "ClassDef"})
  ast_query(action="transform", target="file.py",
            filters={"transform": "rename", "old_name": "a", "new_name": "b"})

Results use compact AST format:
  NodeType:name@line[attrs]{children}

Always query structure before reading raw source.
Each query costs ~100 tokens vs ~3000 tokens for raw source.
```

### 5.5 SERA / Generic Agent

```
## Tool: ast_query

Analyzes source code structure. Returns compact AST representations
that are 27x more efficient than raw source.

### Actions
| Action | Purpose | Filters |
|--------|---------|---------|
| symbols | List all function/class definitions | none |
| dependencies | List all imports | none |
| callers | Find call sites of a function | name: string |
| metrics | Compute complexity metrics | none |
| coverage_map | Map testable code paths | none |
| find | Search for AST nodes | node_type, name |
| parse | Full AST parse | none |
| transform | Plan code transformation | transform, old_name, new_name |

### Compact Format
NodeType:name@line[key=val]{child1;child2}

### Protocol
1. Query structure first, read source only when necessary
2. Accumulate findings -- do not re-query symbols you already found
3. Use metrics to validate changes did not increase complexity
```

---

## 6. Performance Guidelines

### 6.1 When to Use Full vs Compact AST

| Scenario | Recommended Approach | Rationale |
|---|---|---|
| Understanding file structure | `symbols` query | Returns only declarations, minimal tokens |
| Tracing imports | `dependencies` query | Returns only import statements |
| Finding call sites | `callers` query | Returns only matching call nodes |
| Refactoring planning | `transform` query | Returns modified AST without source |
| Deep structural analysis | `parse` query (compact) | Full AST but in compact format |
| Debugging a specific function | Raw source (targeted lines) | Need exact implementation, but read only the relevant lines |
| Initial codebase scan | Pre-generated `symbols.json` | One-time cost, reusable across sessions |
| Multi-file dependency graph | `dependencies` per file | ~100 tokens per file vs ~3000 for raw source |

### 6.2 Token Budgets

Given a 200K-token context window, here is a budget plan:

```
System prompt + instructions:     2,000 tokens
AST query results (10 queries):   1,000 tokens
Reasoning and planning:          10,000 tokens
Code generation / edits:         10,000 tokens
Safety margin:                    5,000 tokens
                                 --------
Total per task:                  28,000 tokens

Remaining for conversation:     172,000 tokens
```

Compare with raw-source approach:

```
System prompt:                    2,000 tokens
Reading 5 source files:          15,000 tokens  (vs 500 with AST)
Reasoning:                       10,000 tokens
Code generation:                 10,000 tokens
                                 --------
Total per task:                  37,000 tokens   (32% more)
```

The AST approach saves ~25% of the budget on code understanding, which compounds with multi-file analysis. For a 20-file refactoring task:

```
AST approach: 20 files x 100 tokens = 2,000 tokens for understanding
Raw approach: 20 files x 3,000 tokens = 60,000 tokens for understanding
Savings: 58,000 tokens (97% reduction in understanding cost)
```

### 6.3 Caching Strategies

The ASTEngine implements file-level caching keyed on `(filepath, mtime)`:

```python
def _get_python_ast(self, filepath: str) -> ast.AST:
    mtime = os.path.getmtime(filepath)
    cache_key = (filepath, mtime)
    if cache_key in self._cache:
        return self._cache[cache_key]
    # ... parse and cache
```

**Best practices:**

1. **Reuse the protocol instance** across queries in a session. The `ReactiveProtocol` object maintains an `ASTEngine` with a warm cache.

2. **Pre-generate for CI/CD**: Run `generate_ast_captures.py` in CI to produce `symbols.json` and `compact_ast.txt`. Commit these or store as artifacts.

3. **Incremental updates**: For large codebases, only re-parse files whose `mtime` has changed. The cache handles this automatically within a session.

4. **Memory limits**: The full AST for this codebase (26 Python files) uses ~1.6 MB peak memory. For very large codebases (1000+ files), process files in batches.

### 6.4 Performance Metrics

Every query returns `PerformanceMetrics`:

```python
@dataclass
class PerformanceMetrics:
    wall_time_ms: float        # Wall clock time
    cpu_user_ms: float         # User CPU time
    cpu_system_ms: float       # System CPU time
    peak_memory_kb: int        # Peak memory usage
    current_memory_kb: int     # Current memory usage
    disk_read_bytes: int       # Disk reads
    disk_write_bytes: int      # Disk writes
    prompt_tokens_approx: int  # Estimated prompt tokens (source size / 4)
    result_tokens_approx: int  # Estimated result tokens (result size / 4)
```

Use these to monitor and optimize:

```python
result = proto.run_query("symbols", "big_file.py")
metrics = result.payload.get("metrics", {})

if metrics.get("wall_time_ms", 0) > 5000:
    print("Warning: slow parse, consider pre-generating")

if metrics.get("peak_memory_kb", 0) > 100000:
    print("Warning: high memory, consider depth-limited parse")
```

### 6.5 Choosing Depth

The `ASTQuery.depth` parameter controls how deep the AST is traversed (-1 means unlimited). For large files, limiting depth can significantly reduce output size:

| Depth | What You Get | Typical Tokens |
|---|---|---|
| 0 | Root node only (module name) | 10 |
| 1 | Top-level declarations (classes, functions, imports) | 50-200 |
| 2 | Class members, function bodies (first level) | 200-1,000 |
| -1 (unlimited) | Full AST including all expressions | 500-50,000 |

For most code intelligence tasks, depth 1-2 is sufficient. Use unlimited depth only when you need expression-level analysis (e.g., dead code detection, control flow).

---

## 7. Example Workflows

### 7.1 Code Refactoring via AST

**Goal**: Rename a function across the codebase and update all callers.

```python
from ast_dsl import ReactiveProtocol
import os

proto = ReactiveProtocol(session_id="refactor-rename")

project_dir = "/path/to/project"
py_files = []
for root, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(root, f))

# Step 1: Find all files that define the target function
target_function = "process_data"
defining_files = []
for filepath in py_files:
    result = proto.run_query("symbols", filepath)
    if result.payload.get("success"):
        for sym in result.payload.get("data", []):
            if sym.get("name") == target_function:
                defining_files.append(filepath)

print(f"Found '{target_function}' defined in: {defining_files}")

# Step 2: Find all files that call the target function
calling_files = []
for filepath in py_files:
    result = proto.run_query("callers", filepath,
                             filters={"name": target_function})
    if result.payload.get("success"):
        callers = result.payload.get("data", [])
        if callers:
            calling_files.append((filepath, callers))

print(f"Found {len(calling_files)} files with call sites")

# Step 3: Preview the transformation
for filepath in defining_files:
    result = proto.run_query("transform", filepath,
        filters={
            "transform": "rename",
            "old_name": target_function,
            "new_name": "transform_data",
        })
    print(f"Transform preview: {result.to_compact()}")

# Step 4: The LLM can now apply the actual source changes
# using the call site locations from Step 2
for filepath, callers in calling_files:
    for caller in callers:
        print(f"  {filepath}:{caller['line']} -- rename call site")
```

### 7.2 Finding Dead Code

**Goal**: Identify unreachable code across the project.

```python
from ast_dsl.python_ast import PythonASTAnalyzer

analyzer = PythonASTAnalyzer()

dead_code_report = []
for filepath in py_files:
    with open(filepath) as f:
        source = f.read()

    dead = analyzer.find_dead_code(source)
    if dead:
        for item in dead:
            dead_code_report.append({
                "file": filepath,
                "line": item["line"],
                "type": item["type"],
                "after": item["after"],
            })

print(f"Found {len(dead_code_report)} dead code segments:")
for item in dead_code_report:
    print(f"  {item['file']}:{item['line']} "
          f"-- {item['type']} after {item['after']}")
```

**Prompt for LLM** (paste the output):

```
Here are dead code segments found by AST analysis:

[paste dead_code_report]

For each:
1. Is this genuinely dead code or a false positive?
2. If dead, should it be removed or is it intentional (e.g., debug code)?
3. Generate a patch to remove confirmed dead code.
```

### 7.3 Generating Test Coverage

**Goal**: Identify untested code paths and generate test stubs.

```python
from ast_dsl import ReactiveProtocol
from ast_dsl.python_ast import PythonASTAnalyzer

proto = ReactiveProtocol(session_id="test-coverage")
analyzer = PythonASTAnalyzer()

# Step 1: Get the coverage map
result = proto.run_query("coverage_map", "src/calculator.py")
coverage = result.payload.get("data", [])

print("Testable functions:")
for item in coverage:
    print(f"  {item['function']}() "
          f"at line {item['line']} "
          f"-- {item['branches']} branches, "
          f"args: {item['args']}")

# Step 2: Generate test stubs
with open("src/calculator.py") as f:
    source = f.read()

stubs = analyzer.generate_test_stubs(source, "calculator")
print("\nGenerated test stubs:")
print(stubs)

# Step 3: Use scope analysis to understand what each function touches
scopes = analyzer.analyze_scopes(source)
for func_name, scope in scopes.items():
    if func_name == "global":
        continue
    print(f"\n{func_name}():")
    print(f"  Reads: {scope['reads']}")
    print(f"  Writes: {scope['writes']}")
```

**Prompt for LLM**:

```
Given this coverage map and scope analysis:

Coverage:
[paste coverage map]

Scopes:
[paste scope analysis]

Generate comprehensive pytest test cases that:
1. Cover all branches (if/else paths)
2. Test edge cases based on argument types
3. Verify side effects identified in scope writes
4. Include proper assertions, not just smoke tests
```

### 7.4 Dependency Analysis

**Goal**: Build a dependency graph and find circular imports.

```python
from ast_dsl import ReactiveProtocol
import os

proto = ReactiveProtocol(session_id="dep-analysis")

# Step 1: Collect all dependencies
dep_graph = {}
for filepath in py_files:
    result = proto.run_query("dependencies", filepath)
    if result.payload.get("success"):
        deps = result.payload.get("data", [])
        relpath = os.path.relpath(filepath, project_dir)
        dep_graph[relpath] = [d["module"] for d in deps]

# Step 2: Detect circular dependencies
def find_cycles(graph, node, visited=None, path=None):
    if visited is None:
        visited = set()
    if path is None:
        path = []
    visited.add(node)
    path.append(node)
    for dep in graph.get(node, []):
        if dep in path:
            cycle_start = path.index(dep)
            return path[cycle_start:] + [dep]
        if dep not in visited and dep in graph:
            cycle = find_cycles(graph, dep, visited, path[:])
            if cycle:
                return cycle
    return None

for module in dep_graph:
    cycle = find_cycles(dep_graph, module)
    if cycle:
        print(f"Circular dependency: {' -> '.join(cycle)}")

# Step 3: Find leaf modules (no internal dependencies)
internal_modules = set(dep_graph.keys())
for module, deps in dep_graph.items():
    internal_deps = [d for d in deps
                     if any(d.startswith(m.replace('/', '.').replace('.py', ''))
                            for m in internal_modules)]
    if not internal_deps:
        print(f"Leaf module (no internal deps): {module}")

# Step 4: Synthesize findings
from ast_dsl.reactive import CueSignal, CueType
cue = CueSignal(cue_type=CueType.SYNTHESIZE, sequence_id=999)
summary = proto.process_cue(cue)
print(f"\nSession summary: {summary.to_compact()}")
```

### 7.5 Cross-File Symbol Resolution

**Goal**: Find where a symbol is defined, used, and referenced across the entire project.

```python
from ast_dsl import ReactiveProtocol

proto = ReactiveProtocol(session_id="symbol-resolution")

target_symbol = "ASTEngine"

# Step 1: Find all definitions
definitions = []
for filepath in py_files:
    result = proto.run_query("symbols", filepath)
    if result.payload.get("success"):
        for sym in result.payload.get("data", []):
            if sym.get("name") == target_symbol:
                definitions.append({
                    "file": filepath,
                    "line": sym["line"],
                    "type": sym["type"],
                })

print(f"'{target_symbol}' is defined in:")
for d in definitions:
    print(f"  {d['file']}:{d['line']} ({d['type']})")

# Step 2: Find all imports of the symbol
importers = []
for filepath in py_files:
    result = proto.run_query("dependencies", filepath)
    if result.payload.get("success"):
        for dep in result.payload.get("data", []):
            names = dep.get("names", [])
            if target_symbol in names:
                importers.append({
                    "file": filepath,
                    "line": dep["line"],
                    "from_module": dep["module"],
                })

print(f"\n'{target_symbol}' is imported in:")
for imp in importers:
    print(f"  {imp['file']}:{imp['line']} "
          f"(from {imp['from_module']})")

# Step 3: Find all call sites / usages
usages = []
for filepath in py_files:
    result = proto.run_query("callers", filepath,
                             filters={"name": target_symbol})
    if result.payload.get("success"):
        for caller in result.payload.get("data", []):
            usages.append({
                "file": filepath,
                "line": caller["line"],
                "source": caller.get("source", ""),
            })

print(f"\n'{target_symbol}' is called/used in:")
for u in usages:
    print(f"  {u['file']}:{u['line']} -- {u['source'][:60]}")

# Summary
print(f"\nResolution summary for '{target_symbol}':")
print(f"  Definitions: {len(definitions)}")
print(f"  Importers: {len(importers)}")
print(f"  Call sites: {len(usages)}")
```

### 7.6 Combining Everything -- Full Audit Workflow

This is a complete audit workflow that an LLM agent can follow:

```python
#!/usr/bin/env python3
"""Full codebase audit using AST reactive protocol."""
import json
import os
from ast_dsl import ReactiveProtocol
from ast_dsl.python_ast import PythonASTAnalyzer
from ast_dsl.reactive import CueSignal, CueType

proto = ReactiveProtocol(session_id="full-audit")
analyzer = PythonASTAnalyzer()
project_dir = "/path/to/project"

# Collect files
py_files = []
for root_dir, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs
               if not d.startswith('.') and d != 'node_modules']
    for f in sorted(files):
        if f.endswith('.py') and not f.startswith('__'):
            py_files.append(os.path.join(root_dir, f))

audit = {
    "files_analyzed": len(py_files),
    "symbols": {},
    "dependencies": {},
    "metrics": {},
    "dead_code": [],
    "high_complexity": [],
    "coverage_gaps": [],
}

for filepath in py_files:
    relpath = os.path.relpath(filepath, project_dir)

    # Symbols
    result = proto.run_query("symbols", filepath)
    if result.payload.get("success"):
        audit["symbols"][relpath] = result.payload.get("data", [])

    # Dependencies
    result = proto.run_query("dependencies", filepath)
    if result.payload.get("success"):
        audit["dependencies"][relpath] = result.payload.get("data", [])

    # Metrics
    result = proto.run_query("metrics", filepath)
    if result.payload.get("success"):
        m = result.payload.get("data", {})
        audit["metrics"][relpath] = m
        if m.get("cyclomatic_complexity", 0) > 10:
            audit["high_complexity"].append({
                "file": relpath,
                "complexity": m["cyclomatic_complexity"],
            })

    # Dead code
    with open(filepath) as f:
        source = f.read()
    dead = analyzer.find_dead_code(source)
    for item in dead:
        audit["dead_code"].append({
            "file": relpath,
            "line": item["line"],
            "type": item["type"],
            "after": item["after"],
        })

    # Coverage gaps
    result = proto.run_query("coverage_map", filepath)
    if result.payload.get("success"):
        for path_item in result.payload.get("data", []):
            if path_item.get("branches", 0) > 3:
                audit["coverage_gaps"].append({
                    "file": relpath,
                    "function": path_item["function"],
                    "branches": path_item["branches"],
                })

# Synthesize
cue = CueSignal(cue_type=CueType.SYNTHESIZE, sequence_id=9999)
summary = proto.process_cue(cue)

audit["session"] = summary.payload.get("state", {})

# Write report
with open("audit_report.json", "w") as f:
    json.dump(audit, f, indent=2)

print(f"Audit complete: {len(py_files)} files analyzed")
print(f"  Symbols found: {sum(len(v) for v in audit['symbols'].values())}")
print(f"  Dead code segments: {len(audit['dead_code'])}")
print(f"  High complexity files: {len(audit['high_complexity'])}")
print(f"  Coverage gaps: {len(audit['coverage_gaps'])}")
print(f"  Total tokens used: {audit['session'].get('total_tokens', 0)}")
```

**Then hand the `audit_report.json` to the LLM with this prompt:**

```
Here is a codebase audit generated by AST analysis.
Review the report and provide:

1. Top 5 refactoring priorities (by impact)
2. Dead code that should be removed
3. Functions that need test coverage (sorted by branch count)
4. Circular dependency warnings
5. A concrete action plan with file:line references
```

---

## Appendix A: Compact AST Grammar

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

Example parse:

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

## Appendix B: ASTQuery Action Reference

| Action | Input | Output | Use Case |
|---|---|---|---|
| `parse` | file path or source string | Full ASTNode tree | Structural analysis |
| `find` | file + filters `{node_type, name}` | List of matching ASTNodes | Searching for specific constructs |
| `symbols` | file path | List of `{type, name, line, attributes}` dicts | Understanding file API |
| `dependencies` | file path | List of `{type, module, line, names}` dicts | Import analysis |
| `callers` | file + filters `{name}` | List of `{line, col, source}` dicts | Impact analysis before refactoring |
| `metrics` | file path | Dict `{total_nodes, functions, classes, imports, max_depth, cyclomatic_complexity}` | Complexity analysis |
| `transform` | file + filters `{transform, old_name, new_name}` | Modified ASTNode tree | Refactoring preview |
| `coverage_map` | file path | List of `{function, line, branches, args, testable}` dicts | Test planning |

## Appendix C: Session Log Format

Each session produces a JSON log (see `ast_captures/session_log.json` for a real example):

```json
{
  "session": {
    "session_id": "demo-session",
    "turn": 6,
    "history_len": 12,
    "context_keys": [],
    "symbols_found": 30,
    "deps_found": 6,
    "pending_transforms": 0,
    "total_tokens": 62017
  },
  "history": [
    {
      "cue_type": "query",
      "payload": {"action": "parse", "target": "...", ...},
      "sequence_id": 1,
      "parent_id": 0,
      "timestamp": 1772330975.24,
      "context_tokens_approx": 0
    },
    {
      "cue_type": "result",
      "payload": {"success": true, "ast_node_count": 2245, ...},
      "sequence_id": 2,
      "parent_id": 1,
      "timestamp": 1772330976.34,
      "context_tokens_approx": 60303
    }
  ]
}
```

Use this log for:
- Debugging agent behavior
- Measuring token efficiency across sessions
- Replaying analysis sessions
- Auditing what the agent analyzed before making changes

## Appendix D: PythonASTAnalyzer Deep Analysis Reference

The `PythonASTAnalyzer` class in `ast_dsl/python_ast.py` provides four advanced analysis methods beyond what the core engine offers:

### `analyze_scopes(source) -> dict`

Returns a dictionary mapping scope names to their variable reads and writes:

```python
{
    "global": {"reads": ["os", "sys"], "writes": ["app"]},
    "Calculator.__init__": {"reads": [], "writes": ["self"]},
    "Calculator.add": {"reads": ["a", "b", "self"], "writes": ["result"]}
}
```

### `extract_control_flow(source) -> list`

Returns a list of control flow edges:

```python
[
    {"func": "divide", "type": "branch", "line": 14, "true_line": 15, "false_line": None},
    {"func": "helper", "type": "loop", "line": 20, "body_line": 21},
    {"func": "helper", "type": "return", "line": 23},
    {"func": "process", "type": "try", "line": 30, "handlers": 2}
]
```

### `find_dead_code(source) -> list`

Returns statements that appear after return or raise:

```python
[
    {"line": 46, "type": "Assign", "after": "Return"},
    {"line": 52, "type": "Expr", "after": "Raise"}
]
```

### `generate_test_stubs(source, module_name) -> str`

Returns a complete unittest file as a string:

```python
"""Auto-generated test stubs for calculator."""
import unittest
from calculator import *

class TestCalculator(unittest.TestCase):
    def test_add(self):
        # TODO: test add(a, b)
        pass

    def test_divide(self):
        # TODO: test divide(a, b)
        pass

if __name__ == "__main__":
    unittest.main()
```
