# Python AST Introspection Guide

## Overview

Python has the richest built-in AST support of any language via the `ast` module. This gives us full, typed access to every syntactic element without any external dependencies.

## Runtime Requirements

- **Python 3.8+** (for `end_lineno`, `end_col_offset`)
- **No external dependencies** - `ast` is part of stdlib

## Architecture

```
Source Code -> ast.parse() -> ast.AST tree -> Universal ASTNode tree
```

### Core Module: `ast_dsl/python_ast.py`

```python
import ast

class PythonASTAnalyzer:
    def analyze_scopes(self, source: str) -> dict:
        """Analyze variable scopes - reads vs writes per function."""
        tree = ast.parse(source)
        # Uses ast.NodeVisitor to track Name nodes in Store/Load context

    def extract_control_flow(self, source: str) -> list:
        """Extract control flow graph edges."""
        # Visits If, For, While, Return, Raise, Try nodes

    def find_dead_code(self, source: str) -> list:
        """Find unreachable code after return/raise statements."""

    def generate_test_stubs(self, source: str, module_name: str) -> str:
        """Auto-generate unittest stubs for all functions/methods."""
```

## Capabilities

| Feature | Support | Method |
|---------|---------|--------|
| Full AST parsing | Native | `ast.parse()` |
| Symbol extraction | Native | Walk for FunctionDef/ClassDef |
| Import analysis | Native | Walk for Import/ImportFrom |
| Scope analysis | Native | NodeVisitor tracking Name contexts |
| Control flow | Native | Visit branch/loop/return nodes |
| Dead code detection | Native | Check statements after Return/Raise |
| Test stub generation | Native | Visit functions, generate unittest |
| Code metrics | Native | Count nodes, branches, depth |
| Source mapping | Native | `lineno`, `col_offset`, `end_lineno` |
| Rename transform | Programmatic | Walk and replace names |

## Universal AST Node Mapping

| Python AST | Universal ASTNode |
|-----------|-------------------|
| `ast.Module` | `Module` |
| `ast.FunctionDef` | `FunctionDef` with `args`, `decorators` attrs |
| `ast.AsyncFunctionDef` | `AsyncFunctionDef` with `is_async=True` |
| `ast.ClassDef` | `ClassDef` with `bases`, `decorators` attrs |
| `ast.Import` | `Import` with module name |
| `ast.ImportFrom` | `ImportFrom` with `names` attr |
| `ast.If/While/For` | Branch/loop nodes for complexity |
| `ast.Return/Raise` | Control flow terminators |
| `ast.Name` | `Name` with variable identifier |
| `ast.Call` | `Call` with function name |

## Query Examples

### Parse a File
```python
from ast_dsl.core import ASTEngine, ASTQuery

engine = ASTEngine()
result = engine.execute(ASTQuery(
    action="parse",
    target="my_module.py",
    language="python",
))
# result.data is an ASTNode tree
# result.metrics has wall_time_ms, peak_memory_kb
```

### Find All Symbols
```python
result = engine.execute(ASTQuery(
    action="symbols",
    target="my_module.py",
))
# result.data = [{"type": "ClassDef", "name": "MyClass", "line": 10}, ...]
```

### Analyze Scopes
```python
from ast_dsl.python_ast import PythonASTAnalyzer

analyzer = PythonASTAnalyzer()
scopes = analyzer.analyze_scopes(source_code)
# {"global": {"reads": [...], "writes": [...]},
#  "my_function": {"reads": ["x", "y"], "writes": ["result"]}}
```

### Extract Control Flow
```python
edges = analyzer.extract_control_flow(source_code)
# [{"func": "process", "type": "branch", "line": 15,
#   "true_line": 16, "false_line": 20}, ...]
```

### Generate Coverage Map
```python
result = engine.execute(ASTQuery(
    action="coverage_map",
    target="my_module.py",
))
# [{"function": "add", "line": 10, "branches": 0, "args": ["a", "b"]}, ...]
```

## Compact Representation

Full AST for a 200-line Python file: ~50KB JSON
Compact AST for the same file: ~2KB text (27x reduction)

Format: `NodeType:name@line[attrs]{child1;child2;...}`

Example:
```
Module@0{FunctionDef:add@10[args=['a','b']]{Return@11};ClassDef:Calc@15[bases=['Base']]{FunctionDef:run@16}}
```

## Performance Characteristics

| Operation | Time | Memory |
|-----------|------|--------|
| Parse 200-line file | ~5ms | ~100KB |
| Parse 1000-line file | ~20ms | ~500KB |
| Full symbol extraction | ~8ms | ~150KB |
| Scope analysis | ~10ms | ~200KB |
| Control flow extraction | ~6ms | ~100KB |

## Integration with Reactive Protocol

```python
from ast_dsl.reactive import ReactiveProtocol

protocol = ReactiveProtocol(session_id="my-session")

# Step 1: Parse
result = protocol.run_query("parse", "my_file.py")

# Step 2: Find specific symbols
result = protocol.run_query("symbols", "my_file.py")

# Step 3: Analyze dependencies
result = protocol.run_query("dependencies", "my_file.py")

# Step 4: Get compact session summary
synth = protocol.process_cue(CueSignal(cue_type=CueType.SYNTHESIZE))
```
