# WebAssembly (WAT) AST Introspection Guide

## Overview

WebAssembly AST parsing uses a **regex-based parser** that processes WAT (WebAssembly Text Format) S-expressions into universal AST nodes for symbol extraction.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- WAT source only — binary `.wasm` is not supported (convert with `wasm2wat` first)

## Architecture

```
WAT Source -> Regex S-expression parser -> Universal ASTNode (fast)
```

### Core Module: `ast_dsl/wasm_ast.py`

```python
def parse_wasm_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="WasmModule", name=filename)
    # Detects: type, import, func, export, memory, table, global,
    #          data segments, elem segments, start function
```

## Capabilities

| Feature | Support | Notes |
|---------|---------|-------|
| `(type ...)` | Yes | Named type declarations |
| `(import ...)` | Yes | Module + name + kind |
| `(func ...)` | Yes | With param/result signatures |
| `(export ...)` | Yes | With export name + kind |
| `(memory ...)` | Yes | Initial pages, skips imports |
| `(table ...)` | Yes | Size + element type |
| `(global ...)` | Yes | Type + mutability |
| `(data ...)` | Yes | Data segment detection |
| `(elem ...)` | Yes | Element segment detection |
| `(start ...)` | Yes | Start function reference |
| Inline expressions | No | Only top-level declarations |

## Universal AST Node Mapping

| WAT Construct | Universal ASTNode |
|---------------|-------------------|
| `(type $name ...)` | `TypeDecl` |
| `(import "mod" "name" (func ...))` | `ImportDecl` with `import_module`, `import_name`, `kind` |
| `(func $name ...)` | `FuncDecl` with `param_count`, `result_type` |
| `(export "name" (func ...))` | `ExportDecl` with `export_name`, `kind` |
| `(memory $name N)` | `MemoryDecl` with `initial_pages` |
| `(table $name N funcref)` | `TableDecl` with `initial_size`, `element_type` |
| `(global $name (mut i32) ...)` | `GlobalDecl` with `value_type`, `mutable` |
| `(data ...)` | `DataSegment` |
| `(elem ...)` | `ElemSegment` |
| `(start $name)` | `StartDecl` |

## Usage Examples

```python
from ast_dsl.wasm_ast import parse_wasm_source, find_wasm_symbols

source = '''
(module
  (type $sig (func (param i32 i32) (result i32)))
  (import "env" "log" (func $log (param i32)))
  (func $add (param i32) (param i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add))
  (memory 1)
  (global $counter (mut i32) (i32.const 0))
)
'''

symbols = find_wasm_symbols(source)
# [{"type": "TypeDecl", "name": "sig", "line": 2},
#  {"type": "ImportDecl", "name": "env.log", "line": 3},
#  {"type": "FuncDecl", "name": "add", "line": 4},
#  {"type": "ExportDecl", "name": "add", "line": 7},
#  {"type": "GlobalDecl", "name": "counter", "line": 9}]
```

## Performance Characteristics

| Operation | Regex Parser |
|-----------|-------------|
| Parse 500-line WAT file | ~3ms |
| Symbol extraction | ~4ms |
