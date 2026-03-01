# Kotlin AST Introspection Guide

## Overview

Kotlin AST parsing uses a **regex-based parser** for fast symbol extraction from Kotlin source files, supporting modern Kotlin features including data classes, sealed hierarchies, coroutines, and extension functions.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- **Enhanced**: `kotlinc -script` for deeper analysis (optional)

## Architecture

```
Kotlin Source -> Regex parser -> Universal ASTNode (fast)
```

### Core Module: `ast_dsl/kotlin_ast.py`

```python
def parse_kotlin_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="KotlinFile", name=filename)
    # Detects: package, imports, typealias, annotations, classes,
    #          objects, interfaces, companion objects, constructors,
    #          functions, properties (val/var)
```

## Capabilities

| Feature | Support | Notes |
|---------|---------|-------|
| `package` declarations | Yes | |
| `import` declarations | Yes | Including wildcard imports |
| `typealias` declarations | Yes | With aliased type |
| Annotations | Yes | `@Serializable`, `@JvmStatic`, etc. |
| `class` declarations | Yes | data, sealed, abstract, open, inner, inline, enum, annotation |
| `object` declarations | Yes | Including companion objects |
| `interface` declarations | Yes | Including sealed interfaces |
| `fun` declarations | Yes | suspend, inline, operator, infix, extension functions, generics |
| `constructor` declarations | Yes | Primary and secondary, visibility |
| Property declarations | Yes | val/var, const, lateinit, delegated, lazy |
| Access control | Yes | public, private, internal, protected |
| Receiver types | Yes | Extension function receivers |

## Universal AST Node Mapping

| Kotlin Construct | Universal ASTNode |
|-----------------|-------------------|
| `package com.example` | `PackageDecl` |
| `import kotlinx.coroutines.*` | `ImportDecl` |
| `typealias Handler = (Event) -> Unit` | `TypeAliasDecl` with `aliased_type` |
| `@Serializable` | `AnnotationDecl` |
| `data class User(val name: String)` | `ClassDecl` with `data=true` |
| `sealed class Result<T>` | `ClassDecl` with `sealed=true`, `generic_params` |
| `object Singleton` | `ObjectDecl` |
| `companion object Factory` | `ObjectDecl` with `companion=true` |
| `interface Repository<T>` | `InterfaceDecl` with `generic_params` |
| `suspend fun fetch(): Result` | `FunDecl` with `suspend=true`, `return_type` |
| `fun String.capitalize(): String` | `FunDecl` with `receiver_type=String` |
| `val count: Int by lazy { 0 }` | `PropertyDecl` with `kind=val`, `lazy=true` |
| `lateinit var adapter: Adapter` | `PropertyDecl` with `lateinit=true` |

## Usage Examples

```python
from ast_dsl.kotlin_ast import parse_kotlin_source, find_kotlin_symbols

source = '''
package com.inthebeginning.simulator

import kotlinx.coroutines.flow.Flow

sealed class SimulationState {
    object Idle : SimulationState()
    data class Running(val tick: Int, val epoch: String) : SimulationState()
    data class Complete(val summary: Summary) : SimulationState()
}

interface SimulationEngine {
    suspend fun step(): SimulationState
    fun reset()
}

class Universe(
    private val seed: Long = 42L
) : SimulationEngine {
    private val rng = Random(seed)
    override suspend fun step(): SimulationState { ... }
    override fun reset() { ... }
}

fun SimulationState.isTerminal(): Boolean =
    this is SimulationState.Complete
'''

symbols = find_kotlin_symbols(source)
# [{"type": "PackageDecl", "name": "com.inthebeginning.simulator", "line": 1},
#  {"type": "ImportDecl", "name": "kotlinx.coroutines.flow.Flow", "line": 3},
#  {"type": "ClassDecl", "name": "SimulationState", "line": 5},
#  {"type": "ObjectDecl", "name": "Idle", "line": 6},
#  {"type": "ClassDecl", "name": "Running", "line": 7},
#  {"type": "ClassDecl", "name": "Complete", "line": 8},
#  {"type": "InterfaceDecl", "name": "SimulationEngine", "line": 11},
#  {"type": "FunDecl", "name": "step", "line": 12},
#  {"type": "FunDecl", "name": "reset", "line": 13},
#  {"type": "ClassDecl", "name": "Universe", "line": 16},
#  {"type": "FunDecl", "name": "isTerminal", "line": 23}]
```

## Performance Characteristics

| Operation | Regex Parser |
|-----------|-------------|
| Parse 500-line file | ~3ms |
| Symbol extraction | ~4ms |
