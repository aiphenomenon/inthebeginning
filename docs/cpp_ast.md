# C/C++ AST Introspection Guide

## Overview

C/C++ AST parsing uses a dual approach: **pycparser** for pure C code and **clang** for C++ code. Both produce the universal AST format for cross-language compatibility.

## Runtime Requirements

- **C path**: `pycparser` Python package (`pip install pycparser`)
- **C++ path**: `clang` compiler (typically pre-installed)
- **Fallback**: Regex-based symbol extraction (no dependencies)

## Architecture

```
C Source  -> pycparser.CParser() -> pycparser AST -> Universal ASTNode
C++ Source -> clang -ast-dump    -> Clang AST text -> Universal ASTNode
```

### Core Module: `ast_dsl/c_ast.py`

```python
import pycparser

def parse_c_source(source: str, filename: str = "<string>") -> ASTNode:
    parser = pycparser.CParser()
    tree = parser.parse(source, filename=filename)
    return _convert_pycparser_node(tree)

def parse_cpp_with_clang(source: str, filename: str = "<string>") -> ASTNode:
    result = subprocess.run(
        ["clang", "-Xclang", "-ast-dump", "-fsyntax-only", filename],
        capture_output=True, text=True,
    )
    return _parse_clang_dump(result.stdout)
```

## Capabilities

| Feature | C (pycparser) | C++ (clang) |
|---------|--------------|-------------|
| Full AST parsing | Yes | Yes |
| Function declarations | Yes | Yes |
| Struct/Union/Enum | Yes | Yes |
| Typedef | Yes | Yes |
| Templates | No | Yes |
| Namespaces | No | Yes |
| Classes | No | Yes |
| Source mapping | Line/col | Line/col |
| Preprocessor | Partial | Full |

## Universal AST Node Mapping

### C (pycparser)
| pycparser Node | Universal ASTNode |
|---------------|-------------------|
| `FileAST` | `FileAST` |
| `FuncDecl` | `FuncDecl` with `param_count` |
| `FuncDef` | `FuncDef` |
| `Decl` | `Decl` with `quals`, `storage` |
| `Struct` | `Struct` |
| `Union` | `Union` |
| `Enum` | `Enum` |
| `Typedef` | `Typedef` |

### C++ (clang)
| Clang Node | Universal ASTNode |
|-----------|-------------------|
| `TranslationUnitDecl` | `TranslationUnit` |
| `FunctionDecl` | `FunctionDecl` |
| `CXXRecordDecl` | `CXXRecordDecl` (class/struct) |
| `NamespaceDecl` | `NamespaceDecl` |
| `CXXMethodDecl` | `CXXMethodDecl` |

## Usage Examples

### Parse C Source
```python
from ast_dsl.c_ast import parse_c_source, find_c_symbols

source = '''
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
'''

root = parse_c_source(source)
symbols = find_c_symbols(source)
# [{"type": "FuncDecl", "name": "factorial", "line": 2}]
```

### Parse C++ with Clang
```python
from ast_dsl.c_ast import parse_cpp_with_clang

root = parse_cpp_with_clang(source, "my_class.cpp")
```

## Limitations

- pycparser requires preprocessed C code (no `#include` resolution)
- For C++ templates, clang is required
- Macro expansions are not tracked in the AST

## Performance Characteristics

| Operation | C (pycparser) | C++ (clang) |
|-----------|--------------|-------------|
| Parse 200-line file | ~10ms | ~100ms |
| Parse 1000-line file | ~50ms | ~500ms |
| Symbol extraction | ~5ms | ~50ms |

Note: clang is slower due to subprocess overhead but provides much richer AST information.
