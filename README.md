# In The Beginning

A multi-language cosmic physics simulator that models the universe from the Big Bang
through the emergence of DNA-based life — implemented across 16 applications in
13 programming languages.

The project also demonstrates an **AST-passing workflow** for AI-assisted development,
where compact Abstract Syntax Tree representations are exchanged between an LLM agent
and a local analysis engine to minimize context window usage.

## Quick Start

```bash
# Run the Python reference implementation
python run_demo.py

# Run in any language
cd apps/go    && go run ./cmd/simulator/
cd apps/rust  && cargo run --release
cd apps/c     && make && ./build/simulator
cd apps/cpp   && mkdir -p build && cd build && cmake .. && make && ./inthebeginning
cd apps/nodejs && node index.js
cd apps/java  && mkdir -p build/classes && javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java && java -cp build/classes com.inthebeginning.simulator.SimulatorApp
cd apps/perl  && perl simulate.pl
cd apps/php   && php simulate.php
cd apps/typescript && npm install && npm run build && node dist/index.js
```

## The Simulation

The simulator models 13 cosmic epochs across 300,000 simulation ticks:

| Epoch | Tick | Temperature | Key Events |
|-------|------|-------------|------------|
| Planck | 1 | 10^10 K | All forces unified |
| Inflation | 10 | ~10^9 K | Exponential expansion, quantum fluctuations |
| Electroweak | 100 | 10^8 K | EM and weak forces separate |
| Quark | 1,000 | ~10^6 K | Quark-gluon plasma |
| Hadron | 5,000 | 10^6 K | Quarks confined into protons/neutrons |
| Nucleosynthesis | 10,000 | 10^4 K | Light nuclei form (H, He, Li) |
| Recombination | 50,000 | 3,000 K | Atoms form, universe becomes transparent |
| Star Formation | 100,000 | — | First stars, heavier elements forged |
| Solar System | 200,000 | — | Our solar system coalesces |
| Earth | 210,000 | ~288 K | Oceans appear, chemistry begins |
| Life | 250,000 | ~288 K | First self-replicating molecules |
| DNA Era | 280,000 | ~288 K | DNA-based life, epigenetics |
| Present | 300,000 | 288 K | Complex life, intelligence |

### Physics Subsystems

```
Universe (Orchestrator)
├── QuantumField     — Particles, wave functions, pair production, quark confinement
├── AtomicSystem     — Nucleosynthesis, electron shells, periodic table (H–Fe)
├── ChemicalSystem   — Molecular bonds, water, amino acids, nucleotides
├── Biosphere        — DNA/RNA, transcription, translation, mutation, selection
└── Environment      — Temperature, UV, cosmic rays, volcanic events, habitability
```

## Applications

| # | Application | Language | Directory | Execution Mode |
|---|-------------|----------|-----------|----------------|
| 1 | Python CLI | Python 3.11 | `simulator/` | Reference implementation |
| 2 | Node.js CLI | JavaScript | `apps/nodejs/` | Terminal with ANSI colors |
| 3 | Perl CLI | Perl 5 | `apps/perl/` | Terminal output |
| 4 | Go CLI + SSE | Go 1.22 | `apps/go/` | Terminal + web SSE server |
| 5 | Rust CLI | Rust | `apps/rust/` | High-performance terminal |
| 6 | C CLI | C11 | `apps/c/` | Minimal footprint |
| 7 | C++ CLI | C++20 | `apps/cpp/` | Object-oriented terminal |
| 8 | Java GUI | Java 21 | `apps/java/` | Swing GUI with live chart |
| 9 | TypeScript Audio | TypeScript | `apps/typescript/` | Web Audio sonification |
| 10 | WebAssembly | Rust→WASM | `apps/wasm/` | Browser WebGPU particles |
| 11 | PHP Snapshot | PHP 8.x | `apps/php/` | HTML snapshot server |
| 12 | Swift iOS | Swift | `apps/swift/` | SwiftUI + Metal rendering |
| 13 | Kotlin Android | Kotlin | `apps/kotlin/` | Jetpack Compose + OpenGL |
| 14 | macOS Screensaver | Swift | `apps/screensaver-macos/` | Metal particles |
| 15 | Ubuntu Screensaver | C | `apps/screensaver-ubuntu/` | X11 + OpenGL |
| 16 | Audio Radio Engine | Python | `apps/audio/` | WAV/MP3 composition engine |

## Testing

Every language implementation has tests. Run the full suite:

```bash
# Python (reference — ~490 tests)
python -m pytest tests/ -v

# Node.js
node --test apps/nodejs/test/test_simulator.js

# Go
cd apps/go && go test ./...

# Rust
cd apps/rust && cargo test

# C
cd apps/c && make test

# C++
cd apps/cpp && mkdir -p build && cd build && cmake .. && make && ctest --output-on-failure

# Java
cd apps/java && mkdir -p build/classes build/test-classes && \
  javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java && \
  javac -d build/test-classes -cp build/classes src/test/java/com/inthebeginning/simulator/*.java && \
  java -cp build/classes:build/test-classes com.inthebeginning.simulator.AllTests

# Perl
prove -v apps/perl/t/

# PHP
cd apps/php && php tests/run_tests.php

# TypeScript
cd apps/typescript && npm test

# Audio composition engine
python -m pytest apps/audio/ -v

# Integration tests: golden outputs, cross-language parity, servers, visualizers
python -m pytest tests/test_golden_outputs.py -v          # Build & run all CLI apps
python -m pytest tests/test_cross_language_parity.py -v   # Epoch parity across languages
python -m pytest tests/test_server_smoke.py -v            # Go SSE + PHP server smoke
python -m pytest tests/test_visualizer_golden.py -v       # Ubuntu screensaver, WASM, Java GUI
python -m pytest tests/test_audio_golden.py -v            # Audio pipeline verification

# Regenerate golden snapshots (after changing simulator output)
python tools/capture_golden.py
```

## AST-Passing Workflow

Traditional AI coding workflows pass entire source files through the LLM context
window. This project implements an AST-passing protocol that reduces token usage
by 5-27x:

```
┌──────────────┐     ASTQuery (action, target, filters)     ┌──────────────┐
│              │ ──────────────────────────────────────────► │              │
│  LLM Agent   │                                             │  AST Engine  │
│  (reasons on │ ◄────────────────────────────────────────── │  (ast_dsl/)  │
│   structure) │   ASTResult (compact AST + performance)     │              │
└──────────────┘                                             └──────────────┘
```

### Example

Instead of reading a 381-line Python file, an agent can query:

```python
from ast_dsl.core import ASTEngine, ASTQuery

engine = ASTEngine()
result = engine.execute(ASTQuery(action="symbols", target="simulator/quantum.py"))
print(result.to_compact())
# ok=True nodes=42 mem=12kb cpu=1.2ms results=[FunctionDef:pair_production@201|...]
```

This returns ~200 tokens instead of ~1,500, letting the agent reason about structure
and make targeted edits without ever loading the full file.

### Supported Languages

The AST engine (`ast_dsl/`) has parsers for all 13 languages in the project:
Python, JavaScript, TypeScript, Go, Rust, C, C++, Java, Perl, PHP, Swift, Kotlin,
and WebAssembly (WAT).

## Documentation Generation

Each language uses its standard documentation tooling:

| Language | Tool | Command |
|----------|------|---------|
| Python | pydoc / Sphinx | `python -m pydoc simulator.quantum` |
| JavaScript | JSDoc | `npx jsdoc apps/nodejs/*.js -d docs/jsdoc` |
| TypeScript | TypeDoc | `cd apps/typescript && npx typedoc src/` |
| Go | godoc | `cd apps/go && go doc ./simulator/` |
| Rust | rustdoc | `cd apps/rust && cargo doc --open` |
| C/C++ | Doxygen | `cd apps/c && doxygen Doxyfile` |
| Java | Javadoc | `cd apps/java && javadoc -d docs -sourcepath src/main/java com.inthebeginning.simulator` |
| Perl | perldoc / POD | `perldoc apps/perl/lib/Quantum.pm` |
| PHP | phpDocumentor | `cd apps/php && phpdoc run -d simulator/ -t docs/` |
| Swift | DocC / swift-doc | Xcode: Product → Build Documentation |
| Kotlin | Dokka | `cd apps/kotlin && ./gradlew dokkaHtml` |

## Cross-Compiled Releases

When a version tag (`v*`) is pushed, GitHub Actions cross-compiles binaries:

| Language | Platforms |
|----------|-----------|
| Go | linux/amd64, linux/arm64, darwin/amd64, darwin/arm64, windows/amd64 |
| Rust | linux-gnu, linux-musl, darwin/amd64, darwin/arm64, windows/amd64 |
| C | linux/amd64 (static) |
| C++ | linux/amd64 |
| Java | Platform-independent JAR |
| Node.js | Tarball (requires Node.js runtime) |
| TypeScript | Tarball (compiled JS + browser bundle) |

See [Releases](../../releases) for pre-built binaries.

## CI/CD

All tests run on every push and pull request via GitHub Actions:

- **Python**: pytest with coverage
- **Go**: build + vet + test
- **Rust**: build + test
- **C**: make + test
- **C++**: cmake + make + ctest
- **Java**: javac + test runner
- **Node.js**: node --test
- **TypeScript**: build + test
- **Perl**: prove

The release workflow builds and uploads cross-compiled binaries on version tags.

## Design Principles

1. **Minimal dependencies** — Simulators use only the language's standard library
   (Rust's `rand` crate is the sole exception)
2. **Zero network surface** — No HTTP clients, no socket listeners, no telemetry
   in simulator binaries
3. **Security first** — No eval/exec, no deserialization of untrusted data, no
   command injection vectors
4. **Test everything** — Every public function has tests; tests use fixed random
   seeds for determinism
5. **AST-first development** — Query structure before reading files; use compact
   representations to minimize token usage

## Project Structure

```
├── README.md              This file
├── CLAUDE.md              Agent steering for Claude Code
├── AGENTS.md              Multi-agent coordination protocol
├── LICENSE                Project license
├── run_demo.py            Main demo entry point
├── simulator/             Python reference implementation
│   ├── constants.py       Physical constants
│   ├── quantum.py         Quantum field simulation
│   ├── atomic.py          Atomic system
│   ├── chemistry.py       Molecular chemistry
│   ├── biology.py         DNA, cells, evolution
│   ├── environment.py     Environmental context
│   ├── universe.py        Orchestrator
│   └── terminal_ui.py     ANSI terminal rendering
├── ast_dsl/               AST parsing and transformation engine
│   ├── core.py            Universal AST engine
│   ├── reactive.py        Agent-pair protocol
│   ├── introspect.py      Cross-project introspection
│   └── *_ast.py           Per-language parsers (13 languages)
├── tests/                 Python test suite (~490 tests)
├── apps/                  Multi-language implementations
│   ├── nodejs/            Node.js CLI
│   ├── go/                Go CLI + SSE server
│   ├── rust/              Rust CLI
│   ├── c/                 C CLI
│   ├── cpp/               C++ CLI
│   ├── java/              Java Swing GUI
│   ├── perl/              Perl CLI
│   ├── php/               PHP snapshot server
│   ├── typescript/        TypeScript audio sonification
│   ├── wasm/              WebAssembly (Rust → WASM)
│   ├── kotlin/            Kotlin Android
│   ├── swift/             Swift iOS
│   ├── screensaver-macos/ macOS screensaver
│   ├── screensaver-ubuntu/ Ubuntu screensaver
│   └── audio/             Audio composition engine
├── docs/                  Architecture documentation
│   ├── walkthrough.md     Complete architecture guide
│   ├── steering.md        AST integration guide
│   ├── apps_overview.md   Per-app documentation
│   ├── build_guide.md     Build instructions
│   └── ...                Per-language AST docs
└── .github/workflows/     CI/CD pipelines
    ├── ci.yml             Test pipeline
    └── release.yml        Cross-compile release pipeline
```

## License

See [LICENSE](LICENSE) for details.
