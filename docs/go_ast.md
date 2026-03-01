# Go AST Introspection Guide

## Overview

Go has excellent built-in AST support via the `go/ast`, `go/parser`, and `go/token` packages. The AST module compiles to a standalone binary for fast, native-speed parsing.

## Runtime Requirements

- **Go 1.18+**
- **No external dependencies** - uses stdlib only

## Architecture

```
Source Code -> parser.ParseFile() -> ast.File -> Universal ASTNode JSON
```

### Core Module: `ast_dsl/go_ast.go`

```go
import (
    "go/ast"
    "go/parser"
    "go/token"
)

func convertNode(fset *token.FileSet, node ast.Node, src []byte) *UniversalNode {
    // Recursively converts Go AST to universal format
}

func parseFile(filename string) (*UniversalNode, error) {
    fset := token.NewFileSet()
    file, err := parser.ParseFile(fset, filename, src, parser.ParseComments)
    return convertNode(fset, file, src), nil
}
```

## Capabilities

| Feature | Support | Method |
|---------|---------|--------|
| Full AST parsing | Native | `parser.ParseFile()` |
| Function declarations | Native | `ast.FuncDecl` |
| Type declarations | Native | `ast.TypeSpec` |
| Interface detection | Native | `ast.InterfaceType` |
| Import analysis | Native | `ast.ImportSpec` |
| Method receivers | Native | `FuncDecl.Recv` |
| Source mapping | Native | `token.FileSet` positions |
| Comments | Native | `parser.ParseComments` |

## Universal AST Node Mapping

| Go AST | Universal ASTNode |
|--------|-------------------|
| `ast.File` | `File` with package name |
| `ast.FuncDecl` | `FuncDecl` with `receiver`, `params` |
| `ast.GenDecl` | `GenDecl` with `tok` (var/const/type/import) |
| `ast.TypeSpec` | `TypeSpec` with type name |
| `ast.ValueSpec` | `ValueSpec` with variable names |
| `ast.ImportSpec` | `ImportSpec` with path |
| `ast.CallExpr` | `CallExpr` with function name |
| `ast.Ident` | `Ident` with identifier name |

## CLI Usage

```bash
# Build
go build -o go_ast ast_dsl/go_ast.go

# Parse a file
./go_ast parse my_file.go

# Extract symbols
./go_ast symbols my_file.go

# Compact output
./go_ast compact my_file.go
```

## Performance Characteristics

Go's parser is exceptionally fast:

| Operation | Time | Memory |
|-----------|------|--------|
| Parse 500-line file | ~1ms | ~500KB |
| Parse 5000-line file | ~5ms | ~2MB |
| Symbol extraction | ~2ms | ~600KB |

## Compact Representation

```
File:main@1{FuncDecl:handleRequest@10[params=3,receiver=true]{...};TypeSpec:Server@30{...}}
```

## Build and Integration

```bash
# Build the binary
cd ast_dsl && go build -o ../bin/go_ast go_ast.go

# Use from Python
import subprocess, json
result = subprocess.run(
    ["./bin/go_ast", "symbols", "main.go"],
    capture_output=True, text=True,
)
data = json.loads(result.stdout)
```
