# Swift AST Introspection Guide

## Overview

Swift AST parsing uses a **regex-based parser** for fast symbol extraction from Swift source files, supporting modern Swift features including actors, async/await, and property wrappers.

## Runtime Requirements

- **Primary**: No dependencies (regex-based, runs in Python)
- **Enhanced**: `swiftc -dump-ast` for deeper analysis (optional, requires Xcode)

## Architecture

```
Swift Source -> Regex parser -> Universal ASTNode (fast)
```

### Core Module: `ast_dsl/swift_ast.py`

```python
def parse_swift_source(source: str, filename: str = "<string>") -> ASTNode:
    root = ASTNode(node_type="SwiftModule", name=filename)
    # Detects: imports, structs, classes, enums, protocols, extensions,
    #          actors, functions, initializers, properties, typealiases,
    #          attributes (@propertyWrapper, @main, etc.)
```

## Capabilities

| Feature | Support | Notes |
|---------|---------|-------|
| `import` declarations | Yes | Module imports |
| `struct` declarations | Yes | Generics, conformances, final |
| `class` declarations | Yes | Generics, conformances, final, visibility |
| `enum` declarations | Yes | Generics, conformances |
| `protocol` declarations | Yes | Conformances (protocol inheritance) |
| `extension` declarations | Yes | Conformances |
| `actor` declarations | Yes | Generics, conformances |
| `func` declarations | Yes | Visibility, static, mutating, async, throws, generics, return type |
| `init` declarations | Yes | Failable (`init?`), convenience, visibility |
| Property declarations | Yes | `var`/`let`, computed properties, static |
| `typealias` declarations | Yes | With aliased type |
| Attribute annotations | Yes | `@propertyWrapper`, `@main`, `@Published`, etc. |
| Access control | Yes | open, public, internal, fileprivate, private |

## Universal AST Node Mapping

| Swift Construct | Universal ASTNode |
|----------------|-------------------|
| `import Foundation` | `ImportDecl` |
| `struct Point<T>: Equatable` | `StructDecl` with `generic_params`, `conformances` |
| `final class ViewModel: ObservableObject` | `ClassDecl` with `final`, `conformances` |
| `enum State: String, CaseIterable` | `EnumDecl` with `conformances` |
| `protocol Drawable: AnyObject` | `ProtocolDecl` with `conformances` |
| `extension Array: CustomStringConvertible` | `ExtensionDecl` with `conformances` |
| `actor NetworkManager` | `ActorDecl` |
| `public func fetch() async throws -> Data` | `FuncDecl` with `visibility`, `async`, `throws`, `return_type` |
| `convenience init?(data: Data)` | `InitDecl` with `failable`, `param_count` |
| `@Published var count: Int` | `PropertyDecl` with `kind=var` |
| `typealias Callback = (Result) -> Void` | `TypeAliasDecl` with `type` |
| `@propertyWrapper` | `AttributeDecl` |

## Usage Examples

```python
from ast_dsl.swift_ast import parse_swift_source, find_swift_symbols

source = '''
import SwiftUI

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

actor DataStore {
    private var cache: [String: Data] = [:]

    func fetch(key: String) async throws -> Data {
        if let cached = cache[key] { return cached }
        let data = try await URLSession.shared.data(from: url).0
        cache[key] = data
        return data
    }
}

protocol Renderable: AnyObject {
    func render() -> some View
}
'''

symbols = find_swift_symbols(source)
# [{"type": "ImportDecl", "name": "SwiftUI", "line": 1},
#  {"type": "AttributeDecl", "name": "main", "line": 3},
#  {"type": "StructDecl", "name": "MyApp", "line": 4},
#  {"type": "ActorDecl", "name": "DataStore", "line": 12},
#  {"type": "FuncDecl", "name": "fetch", "line": 15},
#  {"type": "ProtocolDecl", "name": "Renderable", "line": 23}]
```

## Performance Characteristics

| Operation | Regex Parser |
|-----------|-------------|
| Parse 500-line file | ~2ms |
| Symbol extraction | ~3ms |
