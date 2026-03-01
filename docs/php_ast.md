# PHP AST Introspection Guide

## Overview

PHP AST parsing uses a **regex-based parser** for symbol extraction, with optional enhancement via PHP's `token_get_all()` function for deeper tokenization.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- **Enhanced**: PHP 7.4+ for `token_get_all()` (optional)

## Architecture

```
PHP Source -> Regex parser       -> Universal ASTNode (fast)
PHP Source -> php token_get_all  -> Token stream -> AST (enhanced)
```

### Core Module: `ast_dsl/php_ast.py`

```python
def parse_php_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="PHPFile", name=filename)
    # Detects: namespace, use, class/interface/trait/enum,
    #          functions with params and return types

def parse_php_with_tokenizer(filepath: str) -> ASTNode:
    """Use PHP's token_get_all for token-level analysis."""
```

## Capabilities

| Feature | Regex Parser | token_get_all |
|---------|-------------|---------------|
| Namespace declarations | Yes | Yes |
| Use declarations (with alias) | Yes | Yes |
| Class declarations | Yes | Yes |
| Interface declarations | Yes | Yes |
| Trait declarations | Yes | Yes |
| Enum declarations | Yes | Yes |
| Function declarations | Yes | Yes |
| Abstract/final modifiers | Yes | Yes |
| Extends/implements | Yes | Yes |
| Return types | Yes | Yes |
| Nullable types (`?Type`) | Yes | Yes |
| Union types (`Type\|Type`) | Yes | Yes |
| Properties | Partial | Yes |

## Universal AST Node Mapping

| PHP Construct | Universal ASTNode |
|--------------|-------------------|
| `namespace App\Models;` | `NamespaceDecl` |
| `use App\Foo as Bar;` | `UseDecl` with `alias` |
| `abstract class Foo` | `ClassDecl` with `modifier=abstract` |
| `interface Bar` | `InterfaceDecl` |
| `trait Baz` | `TraitDecl` |
| `enum Qux` | `EnumDecl` |
| `function add(int $a): int` | `FunctionDecl` with `params`, `return_type` |

## Usage Examples

```python
from ast_dsl.php_ast import parse_php_source, find_php_symbols

source = '''<?php
namespace App\\Services;

use App\\Models\\User;

class UserService {
    public function findById(int $id): ?User {
        return User::find($id);
    }
}
'''

symbols = find_php_symbols(source)
# [{"type": "NamespaceDecl", "name": "App\\Services", "line": 2},
#  {"type": "UseDecl", "name": "App\\Models\\User", "line": 4},
#  {"type": "ClassDecl", "name": "UserService", "line": 6},
#  {"type": "FunctionDecl", "name": "findById", "line": 7}]
```

## Performance Characteristics

| Operation | Regex Parser | token_get_all |
|-----------|-------------|---------------|
| Parse 500-line file | ~2ms | ~50ms |
| Symbol extraction | ~3ms | ~50ms |
