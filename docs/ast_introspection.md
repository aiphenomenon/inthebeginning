# AST Self-Introspection Module

## Overview

The AST self-introspection module (`ast_dsl/introspect.py`) provides a universal
interface for any application to parse and analyze its own source code. It
supports all 13 languages in the AST DSL framework and produces compact,
token-efficient representations suitable for LLM consumption.

The module serves two purposes:

1. **Runtime self-analysis** -- Each application can introspect its own source
   at startup (or on demand) to generate metrics about its codebase structure.

2. **Cross-project analysis** -- The `introspect_all_apps()` function walks the
   entire project tree, parsing every application directory and producing
   aggregate reports.

---

## How It Works

### Parsing Pipeline

```
Source File  -->  Language Detection  -->  AST Parser  -->  ASTNode Tree
                 (by file extension)     (per-language)
                                                              |
                                                              v
                                          Compact AST  <--  Node Walking
                                          (token-efficient    (count functions,
                                           string format)      classes, imports)
```

1. **File discovery**: The module walks the application directory, filtering by
   file extension (e.g., `.py`, `.rs`, `.go`, `.java`).

2. **Parser selection**: Each language maps to a dedicated parser function via
   the `_PARSER_REGISTRY`. Parsers are lazy-loaded on first use.

3. **AST construction**: The parser produces a tree of `ASTNode` objects with
   universal fields: `node_type`, `name`, `children`, `attributes`, `line`.

4. **Metrics extraction**: `_count_node_types()` walks the tree and tallies
   functions, classes/structs/interfaces/traits, and imports.

5. **Compaction**: `ASTNode.to_compact()` serializes the tree into a minimal
   string format (`Type:Name@Line[attrs]{children}`) designed to maximize
   information density per token.

6. **Token estimation**: Source and AST token counts are approximated as
   `len(text) // 4`, consistent with typical LLM tokenizer ratios.

### Supported Languages and Extensions

| Language     | Parser Module          | File Extensions              |
|-------------|------------------------|------------------------------|
| Python       | `python_ast.py`        | `.py`                        |
| JavaScript   | `node_ast.js`          | `.js`, `.mjs`                |
| TypeScript   | `typescript_ast.py`    | `.ts`, `.tsx`                |
| Go           | `go_ast.go`            | `.go`                        |
| C            | `c_ast.py`             | `.c`, `.h`                   |
| C++          | `c_ast.py` (shared)    | `.cpp`, `.hpp`, `.cc`, `.hh` |
| Java         | `java_ast.py`          | `.java`                      |
| Rust         | `rust_ast.py`          | `.rs`                        |
| Perl         | `perl_ast.py`          | `.pl`, `.pm`                 |
| PHP          | `php_ast.py`           | `.php`                       |
| Swift        | `swift_ast.py`         | `.swift`                     |
| Kotlin       | `kotlin_ast.py`        | `.kt`, `.kts`                |
| WebAssembly  | `wasm_ast.py`          | `.wat`, `.wast`              |

### Per-Language Compaction Ratios

Compaction ratio = source tokens / AST tokens. Higher values indicate the
compact AST is more space-efficient relative to the original source.

| Language     | Source Tokens | AST Tokens | Compaction Ratio |
|-------------|--------------|------------|------------------|
| Kotlin       | 41,180       | 13,745     | 3.0x             |
| Java         | 26,611       | 9,424      | 2.8x             |
| TypeScript   | 27,791       | 11,899     | 2.3x             |
| Perl         | 20,076       | 6,056      | 3.3x             |
| PHP          | 22,138       | 2,138      | 10.4x            |
| Rust         | 25,845       | 2,570      | 10.1x            |
| Swift        | 38,549       | 7,124      | 5.4x             |
| WASM (Rust)  | 24,291       | 1,642      | 14.8x            |
| macOS Saver  | 25,147       | 4,752      | 5.3x             |

---

## Usage

### Programmatic API

```python
from ast_dsl.introspect import introspect_app

# Introspect a single application
report = introspect_app("/path/to/app/src", language="python")
print(report.summary())

# Access individual file results
for f in report.files:
    print(f"{f.filepath}: {f.ast_nodes} nodes, {f.compaction_ratio:.1f}x compaction")

# Export as JSON
print(report.to_json())
```

### Introspect All Applications

```python
from ast_dsl.introspect import introspect_all_apps

reports = introspect_all_apps("/path/to/project/root")
for name, report in sorted(reports.items()):
    print(f"{name}: {report.total_lines:,} lines, "
          f"{report.total_ast_nodes} nodes, "
          f"{report.avg_compaction_ratio:.1f}x compaction")
```

### CLI Integration via `--ast-introspect`

Each application supports a `--ast-introspect` flag that triggers self-analysis
on startup. The flag causes the app to:

1. Parse all of its own source files using the appropriate AST parser.
2. Print a summary report (file count, lines, AST nodes, compaction ratio).
3. Optionally write a JSON report to `ast_captures/<app>_introspection.json`.

Example usage:

```bash
# Python reference implementation
python run_demo.py --ast-introspect

# Rust CLI
cargo run --release -- --ast-introspect

# Node.js CLI
node apps/nodejs/index.js --ast-introspect

# Go SSE server
go run ./cmd/... --ast-introspect
```

---

## Data Structures

### FileIntrospection

Per-file result containing:

- `filepath`, `language`, `lines`, `bytes`
- `ast_nodes`, `functions`, `classes`, `imports`
- `compact_ast` -- the minimal string representation
- `source_tokens_approx`, `ast_tokens_approx`
- `compaction_ratio` -- derived property (source / AST tokens)

### IntrospectionReport

Aggregate report for an application directory:

- `app_name`, `language`, `root_path`
- `files` -- list of `FileIntrospection` objects
- Totals: `total_lines`, `total_bytes`, `total_ast_nodes`, etc.
- `avg_compaction_ratio` -- aggregate compaction across all files
- `summary()` -- human-readable text report
- `to_json()` -- full JSON serialization
