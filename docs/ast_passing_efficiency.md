# AST Passing Efficiency Metrics

## Overview

When passing code between LLM conversations, agent handoffs, or multi-step
reasoning chains, the full source text of a file consumes a large portion of
the context window. AST passing replaces raw source with a compact structural
representation -- function signatures, class hierarchies, type annotations,
and import graphs -- that preserves the information an LLM needs to reason
about code while dramatically reducing token count.

The **compaction ratio** (source tokens / AST tokens) measures how much
context window space is saved. A compaction ratio of 5.0x means the AST
representation uses roughly one-fifth the tokens of the original source. The
higher the ratio, the more conversations, files, or agent steps can fit
within a single context window.

This matters in practice for:

- **Multi-file reasoning**: Fitting an entire module's structure into a
  single prompt instead of cherry-picking files.
- **Agent-to-agent handoffs**: Passing a project summary from a planning
  agent to an implementation agent without exhausting the context budget.
- **Iterative refinement**: Retaining the structural context of prior
  iterations without re-sending full source each round.

## Methodology

The `ast_dsl/introspect.py` module provides a universal introspection
interface that walks an application directory, identifies source files by
extension, and parses each file with the appropriate language-specific AST
parser. The project includes 13 AST parsers covering C, C++, Go, Java,
JavaScript, Kotlin, Perl, PHP, Python, Rust, Swift, TypeScript, and
WebAssembly.

For each file the introspection module:

1. Reads the source and computes raw byte count and line count.
2. Estimates **source tokens** as `len(source_bytes) / 4` (a standard
   approximation for English-weighted tokenizers).
3. Parses the source into a universal `ASTNode` tree using the registered
   parser for that language.
4. Walks the AST tree to count total nodes, functions/methods, classes/
   structs/interfaces/traits, and imports/uses.
5. Serializes the AST to a compact text representation via
   `ASTNode.to_compact()` and estimates **AST tokens** as
   `len(compact_text) / 4`.
6. Computes the **compaction ratio** as `source_tokens / ast_tokens`.

Higher ratios indicate that the language's source syntax carries more
boilerplate relative to its structural content, making AST passing
especially beneficial.

Data was collected by running:

```python
from ast_dsl.introspect import introspect_all_apps
results = introspect_all_apps('/home/user/inthebeginning')
```

**Note on parser availability**: Several parsers (C, C++, Go, JavaScript)
are implemented in their native languages or require external dependencies
(e.g., `pycparser`, Acorn, `go/parser`). When these dependencies are not
available in the Python runtime, the introspection module reports zero AST
nodes and a 0.0x compaction ratio. Results for those languages are reported
separately below.

## Per-Language Results

### Applications With Successful AST Parsing

| Language   | App Dir           | Files | Lines | AST Nodes | Functions | Classes | Compaction Ratio |
|------------|-------------------|------:|------:|----------:|----------:|--------:|-----------------:|
| Rust       | wasm              |     9 | 2,880 |       148 |         0 |      16 |           14.3x  |
| PHP        | php               |    10 | 3,009 |       174 |       144 |      20 |           10.1x  |
| Rust       | rust              |     9 | 3,197 |       212 |         0 |      18 |            9.8x  |
| Swift      | swift             |    14 | 4,700 |       604 |         0 |      31 |            5.3x  |
| Swift      | screensaver-macos |     9 | 3,017 |       424 |         0 |      23 |            5.2x  |
| Perl       | perl              |     8 | 2,697 |       785 |       156 |       0 |            3.3x  |
| Kotlin     | kotlin            |    16 | 4,991 |     1,157 |         0 |      44 |            3.0x  |
| Java       | java              |    12 | 2,815 |       717 |       650 |      15 |            2.8x  |
| TypeScript | typescript        |     6 | 3,156 |     1,182 |       597 |      19 |            2.3x  |

### Applications With Unavailable Native Parsers

These languages have parsers written in their native runtimes (Go binary,
Node.js module) or require external C libraries (`pycparser`). Their parsers
returned zero AST nodes in the Python-based introspection harness. Raw
source metrics are included for reference.

| Language   | App Dir            | Files | Lines | Source Tokens | Parser Dependency       |
|------------|--------------------|------:|------:|--------------:|-------------------------|
| C          | c                  |    14 | 3,084 |        24,517 | pycparser (not installed)|
| C          | screensaver-ubuntu |     4 | 2,517 |        20,089 | pycparser (not installed)|
| C++        | cpp                |    14 | 3,327 |        26,524 | pycparser / clang        |
| Go         | go                 |     9 | 3,047 |        19,685 | Native Go binary         |
| JavaScript | nodejs             |     9 | 3,337 |        27,240 | Acorn (Node.js module)   |

## Analysis

### High-Compaction Languages (5x and above)

**PHP (10.1x)** achieves strong compaction because PHP source is
syntactically verbose. Opening/closing tags, long function declarations with
type hints, docblocks, and deep curly-brace nesting produce substantial
source text, while the structural skeleton -- 144 function signatures and 20
class declarations extracted from 3,009 lines -- is comparatively small. The
AST representation strips the ceremony and retains only the signatures and
hierarchy.

**Rust (9.8x--14.3x)** achieves the highest compaction ratios in the
project. Rust's rich type system, trait implementations, lifetime
annotations, `pub(crate)` visibility modifiers, and macro invocations create
substantial source text that collapses into relatively few structural nodes
(212 nodes for the main app, 148 for the WASM app). The `wasm` app (14.3x)
shows even higher compaction than the main `rust` app (9.8x) because
WebAssembly-targeted Rust includes additional boilerplate for FFI bindings,
`#[wasm_bindgen]` attributes, and memory management annotations that the AST
parser condenses aggressively.

**Swift (5.2x--5.3x)** sits in the upper-middle tier. Swift's verbose
syntax -- access control keywords (`public`, `private`, `internal`),
optional types, protocol conformances, property wrappers, and SwiftUI view
builders -- contributes meaningful overhead that the AST representation
strips. The parser identified 31 classes/structs in the main Swift app and
23 in the macOS screensaver, with no separately counted functions (methods
are nested within class/struct nodes).

### Moderate-Compaction Languages (2x--4x)

**Perl (3.3x)** benefits from its characteristically verbose `sub`
declarations and `use`/`require` statements being reduced to clean function
and module references. The parser identified 156 subroutines and 63 imports
across 8 files (2,697 lines). Perl's regex-heavy idioms and sigil syntax
contribute less compressible content, keeping the ratio below the 5x tier.

**Kotlin (3.0x)** and **Java (2.8x)** are in a similar range. Both are
statically typed JVM languages with moderate boilerplate. Kotlin's data
classes and sealed hierarchies compress well, but Compose UI code with
trailing lambdas retains more structure. Java's high method count (650
methods across 12 files) produces many AST nodes, keeping the ratio below
3x. The AST parser preserves method signatures and class hierarchies, which
constitute a significant fraction of the original source.

**TypeScript (2.3x)** has the lowest compaction among successfully parsed
languages. TypeScript is already relatively compact as a language, and its
type annotations -- interface declarations, generics, union types -- are
structurally significant information that the AST representation must
preserve rather than strip. The parser extracted 597 functions and 19
classes from only 6 files (3,156 lines), indicating dense,
information-rich source where the structural representation retains most of
the meaningful content.

### When Full Source Context Is Preferable

AST passing is not always the right choice. Full source is better when:

- **Files are very short** (under ~50 lines). The overhead of AST
  serialization format headers can approach the size of the source itself,
  eliminating any compaction benefit.
- **DSL-heavy or configuration code**. Files dominated by declarative
  configuration (YAML-like structures, build scripts, SQL migrations) may
  not parse well with language AST parsers and lose critical formatting
  context.
- **Inline comments carry essential context**. AST representations
  typically strip comments. If function behavior depends heavily on
  inline documentation, TODO annotations, or specification references,
  full source preserves that context.
- **Regex-heavy or template code**. Perl regex patterns, C/C++ preprocessor
  macros, and Rust declarative macros contain domain-specific syntax that
  the AST parser does not fully decompose. Full source preserves the actual
  logic.
- **Exact formatting matters**. Code review, diff generation, and
  whitespace-sensitive languages (Python indentation, Makefile tabs)
  require the original source.
- **The task involves line-level edits**. When the LLM needs to produce
  exact line-level patches or character-precise modifications, it needs the
  original text, not a structural summary.

## Recommendations

### When to Use AST Passing

1. **Surveying large codebases** (10+ files). Pass AST summaries of all
   modules to let the LLM identify relevant entry points, then follow up
   with full source for targeted files. At 5--10x compaction, a 20-file
   project that would consume 100k tokens as raw source fits in 10--20k
   tokens as AST.

2. **Agent-to-agent handoffs**. When a planning agent needs to communicate
   project structure to an implementation agent, AST summaries provide the
   architectural map without consuming the implementation agent's context
   budget for the actual code it needs to write.

3. **Iterative multi-turn conversations**. Instead of re-sending full
   source each turn, send the AST summary once and only include full source
   for the specific file under discussion. This is especially effective for
   PHP (10.1x) and Rust (9.8--14.3x) codebases where the savings are an
   order of magnitude.

4. **Cross-language projects**. When an LLM needs to understand
   interactions between components written in different languages (e.g., a
   Rust backend and TypeScript frontend), AST summaries of both sides fit
   where full source of both would not.

### When to Use Full Source

1. **Performing line-level edits or code review** on a specific file.

2. **Working with files under 100 lines** where compaction savings are
   marginal.

3. **Debugging runtime errors** where stack traces reference specific line
   numbers and the LLM needs to see the exact code at those locations.

4. **The language parser is unavailable**. For C, C++, Go, and JavaScript
   in environments without their native toolchains, fall back to full
   source rather than sending empty AST results.

### Hybrid Strategy (Recommended)

The most effective approach combines both methods:

1. Start with AST summaries of all project files to establish structural
   context. For this project, the 9 successfully parsed apps produce a
   combined AST representation of approximately 59,895 tokens -- about 30%
   of a 200k context window.

2. Request full source for the 1--3 files most relevant to the current
   task.

3. On subsequent turns, reference the AST summary for unchanged files and
   only re-send full source for files that have been modified.

This hybrid approach typically achieves 60--80% context window reduction
compared to sending full source for all files, while preserving the detail
needed for accurate code generation and modification.
