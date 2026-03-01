# TypeScript AST Introspection Guide

## Overview

TypeScript AST parsing uses a **regex-based parser** for fast symbol extraction from TypeScript source files without requiring `tsc` or external dependencies.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- **Enhanced**: `tsc --ast` for deeper analysis (optional)

## Architecture

```
TypeScript Source -> Regex parser -> Universal ASTNode (fast)
```

### Core Module: `ast_dsl/typescript_ast.py`

```python
def parse_typescript_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="TSModule", name=filename)
    # Detects: decorators, imports, exports, interfaces, type aliases,
    #          enums, classes, functions, variables, methods, namespaces
```

## Capabilities

| Feature | Support | Notes |
|---------|---------|-------|
| `import` declarations | Yes | Named, default, namespace imports |
| `export` declarations | Yes | Default and named exports |
| `interface` declarations | Yes | With generics and `extends` |
| `type` aliases | Yes | With generic parameters |
| `enum` declarations | Yes | Including `const enum` |
| `class` declarations | Yes | Abstract, extends, implements, generics |
| `function` declarations | Yes | Async, generics, return types |
| Variable declarations | Yes | `const`, `let`, `var` with type annotations |
| Method declarations | Yes | Visibility, static, abstract, async |
| Decorator declarations | Yes | `@decorator` syntax |
| `namespace` declarations | Yes | |
| Type-level constructs | Partial | Mapped/conditional types not parsed |

## Universal AST Node Mapping

| TypeScript Construct | Universal ASTNode |
|---------------------|-------------------|
| `import { X } from "y"` | `ImportDecl` with `names` attribute |
| `export function foo()` | `ExportDecl` |
| `interface Foo<T> extends Bar` | `InterfaceDecl` with `generic_params`, `extends` |
| `type Foo<T> = ...` | `TypeAliasDecl` with `generic_params` |
| `enum Direction` | `EnumDecl` |
| `abstract class Foo<T> extends Bar implements Baz` | `ClassDecl` with `abstract`, `generic_params`, `extends`, `implements` |
| `async function foo(x: T): R` | `FunctionDecl` with `async`, `param_count`, `return_type` |
| `const x: Type = ...` | `VarDecl` with `kind`, `type_annotation` |
| `private async method()` | `MethodDecl` with `visibility`, `async` |
| `@decorator` | `DecoratorDecl` |
| `namespace Foo` | `NamespaceDecl` |

## Usage Examples

```python
from ast_dsl.typescript_ast import parse_typescript_source, find_typescript_symbols

source = '''
import { Observable } from "rxjs";

export interface EventEmitter<T> extends Disposable {
    emit(event: T): void;
    on(handler: (event: T) => void): void;
}

export type Result<T, E> = Success<T> | Failure<E>;

export class EventBus<T> implements EventEmitter<T> {
    private handlers: Array<(event: T) => void> = [];

    async emit(event: T): Promise<void> {
        for (const handler of this.handlers) {
            await handler(event);
        }
    }
}
'''

symbols = find_typescript_symbols(source)
# [{"type": "ImportDecl", "name": "rxjs", "line": 1},
#  {"type": "ExportDecl", "name": "EventEmitter", "line": 3},
#  {"type": "InterfaceDecl", "name": "EventEmitter", "line": 3},
#  {"type": "ExportDecl", "name": "Result", "line": 8},
#  {"type": "TypeAliasDecl", "name": "Result", "line": 8},
#  {"type": "ExportDecl", "name": "EventBus", "line": 10},
#  {"type": "ClassDecl", "name": "EventBus", "line": 10},
#  {"type": "MethodDecl", "name": "emit", "line": 13}]
```

## Performance Characteristics

| Operation | Regex Parser |
|-----------|-------------|
| Parse 500-line file | ~2ms |
| Symbol extraction | ~3ms |
