# Node.js / JavaScript AST Introspection Guide

## Overview

JavaScript AST parsing uses the **Acorn** parser, which provides a complete ESTree-compatible AST for modern JavaScript (ES2024+). The module outputs the universal AST format for cross-language compatibility.

## Runtime Requirements

- **Node.js 16+**
- **Acorn** (`npm install acorn`)

## Architecture

```
Source Code -> acorn.parse() -> ESTree AST -> Universal ASTNode JSON
```

### Core Module: `ast_dsl/node_ast.js`

```javascript
const acorn = require("acorn");

function parseToUniversalAST(source, filename) {
  const tree = acorn.parse(source, {
    ecmaVersion: "latest",
    sourceType: "module",
    locations: true,
  });
  return convertNode(tree, source);
}

function findSymbols(source) { /* ... */ }
function findDependencies(source) { /* ... */ }
function toCompact(node, depth) { /* ... */ }
```

## Capabilities

| Feature | Support | Method |
|---------|---------|--------|
| Full AST parsing | Via Acorn | `acorn.parse()` |
| ES modules | Yes | `sourceType: "module"` |
| CommonJS | Yes | Detects `require()` calls |
| Symbol extraction | Yes | Walk for declarations |
| Import/require analysis | Yes | ImportDeclaration + CallExpression |
| Source mapping | Yes | Acorn locations |
| Compact output | Yes | Custom serializer |

## Universal AST Node Mapping

| ESTree Node | Universal ASTNode |
|------------|-------------------|
| `Program` | `Program` |
| `FunctionDeclaration` | `FunctionDeclaration` with `param_count` |
| `ClassDeclaration` | `ClassDeclaration` with `extends` |
| `VariableDeclaration` | `VariableDeclaration` with `kind` |
| `MethodDefinition` | `MethodDefinition` |
| `ImportDeclaration` | `ImportDeclaration` with module path |
| `CallExpression` | `CallExpression` |

## CLI Usage

```bash
# Parse a file
node ast_dsl/node_ast.js parse my_file.js

# Extract symbols
node ast_dsl/node_ast.js symbols my_file.js

# Get dependencies
node ast_dsl/node_ast.js dependencies my_file.js

# Compact output
node ast_dsl/node_ast.js compact my_file.js
```

Output is JSON with `success`, `data`, and `metrics` fields.

## Integration with Python Driver

The Node.js module is invoked from Python via subprocess:

```python
import subprocess, json

result = subprocess.run(
    ["node", "ast_dsl/node_ast.js", "symbols", "app.js"],
    capture_output=True, text=True,
)
data = json.loads(result.stdout)
```

## Performance Characteristics

| Operation | Time | Memory |
|-----------|------|--------|
| Parse 500-line file | ~10ms | ~2MB heap |
| Symbol extraction | ~12ms | ~2MB heap |
| Dependency analysis | ~8ms | ~2MB heap |

## Compact Representation

Format matches the universal compact format:
```
Program@1{FunctionDeclaration:handleRequest@5[param_count=2]{...};ClassDeclaration:Server@20[extends=Base]{...}}
```
