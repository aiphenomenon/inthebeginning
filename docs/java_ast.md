# Java AST Introspection Guide

## Overview

Java AST parsing uses a dual approach: a fast **regex-based parser** for quick symbol extraction, and **javac -Xprint** for compilation-verified analysis.

## Runtime Requirements

- **Primary**: No dependencies (regex-based)
- **Enhanced**: JDK 11+ for `javac -Xprint`

## Architecture

```
Java Source -> Regex parser    -> Universal ASTNode (fast, no JDK needed)
Java Source -> javac -Xprint   -> Detailed AST (requires JDK)
```

### Core Module: `ast_dsl/java_ast.py`

```python
def parse_java_source(source: str, filename: str = "<string>") -> ASTNode:
    """Regex-based parser for quick symbol extraction."""
    root = ASTNode(node_type="CompilationUnit", name=filename)
    # Detects: package, imports, classes, interfaces, enums,
    #          records, methods with params and return types

def parse_java_with_javac(filepath: str) -> ASTNode:
    """Enhanced parsing using javac -Xprint."""
    result = subprocess.run(
        ["javac", "-Xprint", filepath], ...
    )
```

## Capabilities

| Feature | Regex Parser | javac |
|---------|-------------|-------|
| Package declaration | Yes | Yes |
| Import declarations | Yes (incl. static) | Yes |
| Class declarations | Yes | Yes |
| Interface declarations | Yes | Yes |
| Enum declarations | Yes | Yes |
| Method declarations | Yes (with params) | Yes |
| Extends/implements | Yes | Yes |
| Return types | Yes | Yes |
| Annotations | Partial | Yes |
| Generics | Partial | Yes |

## Universal AST Node Mapping

| Java Construct | Universal ASTNode |
|---------------|-------------------|
| `package ...;` | `PackageDecl` |
| `import ...;` | `ImportDecl` with `static` attr |
| `class Foo` | `ClassDecl` with `extends`, `implements` |
| `interface Bar` | `InterfaceDecl` |
| `enum Baz` | `EnumDecl` |
| `record Qux` | `RecordDecl` |
| `void method(...)` | `MethodDecl` with `return_type`, `params` |

## Usage Examples

```python
from ast_dsl.java_ast import parse_java_source, find_java_symbols

source = '''
package com.example;
import java.util.List;

public class Calculator {
    public int add(int a, int b) { return a + b; }
}
'''

root = parse_java_source(source)
symbols = find_java_symbols(source)
# [{"type": "PackageDecl", "name": "com.example", "line": 1},
#  {"type": "ImportDecl", "name": "java.util.List", "line": 2},
#  {"type": "ClassDecl", "name": "Calculator", "line": 4},
#  {"type": "MethodDecl", "name": "add", "line": 5}]
```

## Performance Characteristics

| Operation | Regex Parser | javac |
|-----------|-------------|-------|
| Parse 500-line file | ~2ms | ~500ms |
| Symbol extraction | ~3ms | ~500ms |

The regex parser is 250x faster but less precise for complex generics and nested classes.
