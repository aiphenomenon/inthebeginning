# Perl AST Introspection Guide

## Overview

Perl AST parsing uses a **regex-based parser** for symbol extraction, with optional enhancement via `perl -MO=Deparse` for deeper analysis.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- **Enhanced**: Perl 5.10+ for `B::Deparse` (typically pre-installed)

## Architecture

```
Perl Source -> Regex parser     -> Universal ASTNode (fast)
Perl Source -> perl -MO=Deparse -> Deparsed output (enhanced)
```

### Core Module: `ast_dsl/perl_ast.py`

```python
def parse_perl_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="PerlScript", name=filename)
    # Detects: use/require, package, sub, method calls,
    #          variable declarations (my, our, local)
```

## Capabilities

| Feature | Support | Notes |
|---------|---------|-------|
| `use`/`require` | Yes | With arguments |
| `package` declarations | Yes | |
| `sub` declarations | Yes | With prototypes |
| Method calls (`->`) | Yes | Arrow notation |
| Variable declarations | Yes | my, our, local |
| Regular expressions | No | Too context-dependent |
| Moose/Moo attributes | Partial | `has` keyword |

## Universal AST Node Mapping

| Perl Construct | Universal ASTNode |
|---------------|-------------------|
| `use Module;` | `UseDecl` |
| `require Module;` | `RequireDecl` |
| `package Foo;` | `PackageDecl` |
| `sub name { }` | `SubDecl` with `prototype` |
| `->method()` | `MethodCall` |
| `my $var` | `VarDecl` with `scope=my` |
| `our @array` | `VarDecl` with `scope=our` |

## Usage Examples

```python
from ast_dsl.perl_ast import parse_perl_source, find_perl_symbols

source = '''
package Calculator;
use strict;
use Moose;

has 'value' => (is => 'rw', isa => 'Num');

sub add {
    my ($self, $a, $b) = @_;
    return $a + $b;
}

1;
'''

symbols = find_perl_symbols(source)
# [{"type": "PackageDecl", "name": "Calculator", "line": 1},
#  {"type": "UseDecl", "name": "strict", "line": 2},
#  {"type": "UseDecl", "name": "Moose", "line": 3},
#  {"type": "SubDecl", "name": "add", "line": 7}]
```

## Performance Characteristics

| Operation | Regex Parser | B::Deparse |
|-----------|-------------|-----------|
| Parse 500-line file | ~2ms | ~100ms |
| Symbol extraction | ~3ms | ~100ms |
