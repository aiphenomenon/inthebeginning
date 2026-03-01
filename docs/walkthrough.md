# AST-Driven Reality Simulator: Complete Walkthrough

## Overview

This project demonstrates a novel approach to AI-assisted code intelligence: a **reactive agent pair** where a local AST analysis tool and an LLM pass structured state back and forth via **CueSignals**. This paradigm is then exercised by building a **physics reality simulator** that models the universe from the Big Bang through the emergence of life.

The project includes:
- **AST DSL Engine**: Multi-language AST introspection (Python, JS, Go, C/C++, Java, Rust, Perl, PHP)
- **Reactive Protocol**: Structured state-passing between LLM and local tool
- **Reality Simulator**: Physics from quantum fields to DNA epigenetics
- **352 tests** at **93% code coverage**
- **Performance metrics** for all operations

## Architecture

### The Reactive Agent Pair

```
┌─────────────────┐    CueSignal(QUERY)     ┌──────────────────┐
│                 │ ────────────────────────> │                  │
│   LLM Agent     │                          │   AST Tool       │
│   (Claude)      │ <─────────────────────── │   (Local)        │
│                 │    CueSignal(RESULT)      │                  │
│                 │                          │  - Parse ASTs     │
│  Decides what   │    CueSignal(REFINE)     │  - Find symbols  │
│  to analyze     │ ────────────────────────>│  - Analyze deps   │
│  next based on  │                          │  - Code metrics   │
│  prior results  │ <─────────────────────── │  - Transform      │
│                 │    CueSignal(RESULT)      │  - Coverage map  │
│                 │                          │                  │
│                 │    CueSignal(SYNTHESIZE)  │                  │
│                 │ ────────────────────────>│                  │
│                 │ <─────────────────────── │  Accumulated     │
│                 │    CueSignal(RESULT)      │  state summary   │
└─────────────────┘                          └──────────────────┘
```

Key insight: The LLM never needs the full source code in context. It works with **compact AST summaries** that are 27x smaller than the full AST representation.

### Self-Prompting Flow

The reactive protocol creates a self-cuing loop:

1. LLM sends QUERY cue → Tool parses code → Returns structured result
2. LLM examines result → Sends REFINE cue with adjusted filters
3. LLM requests TRANSFORM → Tool applies AST transformation
4. LLM sends SYNTHESIZE → Tool summarizes all accumulated state
5. Either side signals COMPLETE

Each CueSignal carries:
- `cue_type`: The action type
- `payload`: Query parameters or result data
- `sequence_id`: For ordering
- `parent_id`: For tracking refinement chains
- `context_tokens_approx`: Token budget tracking

## Project Structure

```
inthebeginning/
├── ast_dsl/                    # AST DSL Engine
│   ├── __init__.py             # Package exports
│   ├── core.py                 # ASTEngine, ASTNode, ASTQuery, ASTResult
│   ├── reactive.py             # ReactiveProtocol, AgentState, CueSignal
│   ├── python_ast.py           # Deep Python analysis
│   ├── node_ast.js             # JavaScript/Node.js AST (Acorn)
│   ├── go_ast.go               # Go AST (go/ast stdlib)
│   ├── c_ast.py                # C/C++ AST (pycparser + clang)
│   ├── java_ast.py             # Java AST (regex + javac)
│   ├── rust_ast.py             # Rust AST (regex + rustc)
│   ├── perl_ast.py             # Perl AST (regex + B::Deparse)
│   └── php_ast.py              # PHP AST (regex + token_get_all)
├── simulator/                  # Reality Simulator
│   ├── constants.py            # Physical constants (scaled for simulation)
│   ├── quantum.py              # Quantum fields, particles, wave functions
│   ├── atomic.py               # Atoms, electron shells, nucleosynthesis
│   ├── chemistry.py            # Molecules, amino acids, nucleotides
│   ├── biology.py              # DNA, RNA, proteins, epigenetics, cells
│   ├── environment.py          # Temperature, radiation, geological events
│   ├── universe.py             # Big Bang → Present orchestrator
│   └── terminal_ui.py          # Unicode/ANSI terminal rendering
├── tests/                      # 352 tests, 93% coverage
├── ast_captures/               # Generated AST data
│   ├── full_ast.json           # 16.4 MB complete AST
│   ├── compact_ast.txt         # 603 KB compact representation
│   ├── symbols.json            # All symbol definitions
│   ├── coverage_map.json       # Testable code paths
│   ├── session_log.json        # Reactive protocol session
│   └── simulation_results.json # Simulation output
├── docs/                       # Per-language documentation
├── run_demo.py                 # Main entry point
└── generate_ast_captures.py    # AST capture generator
```

## Worked Example: AST Demo Session

The demo (`run_demo.py`) executes a 6-step self-cuing sequence:

### Cue 1: Parse quantum.py

```
[Cue 1] Parsing simulator/quantum.py...
  Nodes: 2245
  Time: 1062.5ms
  Memory: 1596KB
```

The engine parses 330 lines of quantum physics code into 2,245 AST nodes. This is a one-time cost; results are cached.

### Cue 2: Find Symbols

```
[Cue 2] Finding symbols in quantum.py...
  Found 30 symbols:
    ClassDef             ParticleType                   line 22
    ClassDef             Spin                           line 40
    ClassDef             Color                          line 45
    ClassDef             WaveFunction                   line 80
    FunctionDef          probability                    line 87
    FunctionDef          evolve                         line 91
    ...
```

30 symbols extracted: 7 classes and 23 functions. The LLM now knows the module structure without reading the source.

### Cue 3: Dependencies

```
[Cue 3] Extracting dependencies...
  Found 6 imports:
    Import          math
    Import          random
    ImportFrom      dataclasses
    ImportFrom      enum
    ImportFrom      typing
    ImportFrom      simulator.constants
```

### Cue 4: Code Metrics

```
[Cue 4] Computing code metrics...
  Total AST nodes:        2245
  Functions:              23
  Classes:                7
  Imports:                6
  Max depth:              13
  Cyclomatic complexity:   23
```

### Cue 5: Coverage Map

```
[Cue 5] Generating coverage map...
  Testable functions: 23
    probability               line   87 branches=0
    evolve                    line   91 branches=1
    collapse                  line   97 branches=0
    ...
```

### Cue 6: Synthesize

```
[Cue 6] Synthesizing session state...
  Session: demo-session
  Turns: 6
  Symbols found: 30
  Dependencies found: 6
  Total tokens: 62,017
```

The session consumed approximately 62K tokens across 6 turns — a fraction of what full source reading would require.

## Reality Simulator: Big Bang to Life

### Simulation Timeline

| Epoch | Tick | Temperature | Key Events |
|-------|------|-------------|------------|
| Planck | 1 | 10^10 K | All forces unified |
| Quark | 1,000 | ~10^8 K | Free quarks, gluon plasma |
| Hadron | 5,000 | ~10^6 K | Quarks confined into protons/neutrons |
| Nucleosynthesis | 10,000 | ~10^4 K | H, He, Li nuclei form |
| Recombination | 50,000 | ~3,000 K | Atoms form, universe transparent |
| Star Formation | 100,000 | ~2.7 K | First stars, heavier elements |
| Solar System | 200,000 | ~2.7 K | Solar system coalesces |
| Earth | 210,000 | ~288 K | Oceans, atmosphere |
| Life | 250,000 | ~288 K | Self-replicating molecules |
| DNA Era | 280,000 | ~288 K | DNA-based life, epigenetics |
| Present | 300,000 | ~288 K | Complex life |

### Simulation Results

```
Performance:
  Wall Time:     0.428s
  CPU User:      0.400s
  CPU System:    0.000s
  Peak Memory:   611 KB
  Ticks:         300,000

Creation:
  Particles:     110
  Atoms:         201
  Molecules:     39
  Cells Born:    498
  Mutations:     0

Final Biosphere:
  Population:    100
  Avg Fitness:   0.7245
  Generations:   51
  GC Content:    0.5111
```

### Physics Layers

#### Quantum Level (`simulator/quantum.py`)

```python
@dataclass
class WaveFunction:
    amplitude: float = 1.0
    phase: float = 0.0
    coherent: bool = True

    @property
    def probability(self) -> float:
        """Born rule: |ψ|²"""
        return self.amplitude ** 2

    def collapse(self) -> bool:
        """Measurement: collapse to eigenstate."""
        result = random.random() < self.probability
        self.amplitude = 1.0 if result else 0.0
        self.coherent = False
        return result
```

Models: Wave functions, particles (quarks, leptons, bosons), entangled pairs, quantum fields with pair production/annihilation, quark confinement.

#### Atomic Level (`simulator/atomic.py`)

```python
@dataclass
class Atom:
    atomic_number: int
    shells: list  # Electron shells built via Aufbau principle

    @property
    def valence_electrons(self) -> int:
        return self.shells[-1].electrons

    def bond_type(self, other: "Atom") -> str:
        diff = abs(self.electronegativity - other.electronegativity)
        if diff > 1.7: return "ionic"
        elif diff > 0.4: return "polar_covalent"
        else: return "covalent"
```

Models: Electron shells, ionization, chemical bonding, nucleosynthesis (primordial + stellar), periodic table.

#### Biology Level (`simulator/biology.py`)

```python
@dataclass
class Gene:
    sequence: list  # ATGC bases
    epigenetic_marks: list  # Methylation, acetylation

    @property
    def is_silenced(self) -> bool:
        methyl_count = sum(1 for m in self.epigenetic_marks
                          if m.mark_type == "methylation" and m.active)
        return methyl_count > self.length * 0.3

    def transcribe(self) -> list:
        """DNA → mRNA (T → U)"""
        if self.is_silenced: return []
        return ["U" if b == "T" else b for b in self.sequence]
```

Models: DNA strands, gene expression, epigenetic modification (methylation, histone acetylation), mRNA transcription, protein translation via codon table, protein folding, cell metabolism and division, population dynamics with selection.

## Performance Metrics

### AST Analysis Performance

| Module | AST Nodes | Functions | Classes | Complexity |
|--------|-----------|-----------|---------|------------|
| quantum.py | 2,245 | 23 | 7 | 23 |
| biology.py | 3,127 | 34 | 6 | 53 |
| atomic.py | 2,420 | 31 | 3 | 42 |
| terminal_ui.py | 2,538 | 13 | 0 | 26 |
| universe.py | 2,362 | 11 | 3 | 40 |
| chemistry.py | 2,218 | 17 | 3 | 25 |
| environment.py | 1,163 | 10 | 2 | 20 |
| constants.py | 439 | 0 | 0 | 1 |
| **TOTAL** | **16,512** | **139** | **24** | **230** |

### Token Budget Analysis

| Representation | Size | Approx Tokens | Ratio |
|---------------|------|---------------|-------|
| Full AST JSON | 16.4 MB | ~4,100,000 | 1.0x |
| Compact AST | 603 KB | ~150,000 | **27x reduction** |
| Symbols JSON | 150 KB | ~37,500 | 109x reduction |
| Coverage Map | 95 KB | ~23,750 | 173x reduction |

The compact representation fits entirely within Claude's context window (~200K tokens), while the full AST would require ~20 context windows.

### Simulation Performance

| Metric | Value |
|--------|-------|
| Wall time | 0.428s |
| CPU user time | 0.400s |
| CPU system time | 0.000s |
| Peak memory | 611 KB |
| Ticks simulated | 300,000 |
| Epoch transitions | 10 |

### Test Suite

| Metric | Value |
|--------|-------|
| Total tests | 352 |
| Passed | 352 |
| Failed | 0 |
| Line coverage | 93% |
| Execution time | 3.85s |

## Code Quality Metrics

All code is pure Python with minimal dependencies:
- **stdlib only** for the simulator
- **pycparser** for C AST (optional)
- **acorn** for JS AST (optional, Node.js)
- **pytest + pytest-cov** for testing
