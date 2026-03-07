# In The Beginning -- Simulation Applications Overview

## Project Summary

"In The Beginning" is a multi-language physics simulator that models the
universe from the Big Bang through the emergence of DNA-based life. The
simulation spans 13 cosmic epochs -- from the Planck era (tick 1) to the
Present (tick 300,000) -- and is implemented across 16 applications in 12
programming languages, targeting terminals, browsers, desktops, and mobile
devices.

Every application implements the same core simulation engine, built around 5
physics subsystems orchestrated by a Universe class. The subsystems activate
progressively as the simulated universe cools and evolves, producing particles,
atoms, molecules, cells, and eventually self-replicating DNA-based life.

---

## Shared Simulation Architecture

### The 13 Cosmic Epochs

Every application implements the same timeline, defined by simulation ticks:

| #  | Epoch            | Start Tick | Temperature         | Description                                       |
|----|------------------|------------|---------------------|---------------------------------------------------|
| 1  | Planck           | 1          | 10^10 K (sim)       | All forces unified, quantum gravity regime         |
| 2  | Inflation        | 10         | ~10^9 K             | Exponential expansion, quantum fluctuations seed structure |
| 3  | Electroweak      | 100        | ~10^8 K             | Electromagnetic and weak forces separate           |
| 4  | Quark            | 1,000      | ~10^6 K             | Quark-gluon plasma, free quarks and gluons         |
| 5  | Hadron           | 5,000      | ~10^6 K             | Quarks confined into protons and neutrons           |
| 6  | Nucleosynthesis  | 10,000     | ~10^4 K             | Light nuclei form: H, He, Li                      |
| 7  | Recombination    | 50,000     | ~3,000 K            | Atoms form, universe becomes transparent (CMB)     |
| 8  | Star Formation   | 100,000    | ~2.725 K (CMB)      | First stars ignite, heavier elements forged         |
| 9  | Solar System     | 200,000    | ~2.725 K            | Our solar system coalesces from stellar debris     |
| 10 | Earth            | 210,000    | ~288 K              | Earth forms, oceans appear, volcanic activity      |
| 11 | Life             | 250,000    | ~288 K              | First self-replicating molecules emerge            |
| 12 | DNA Era          | 280,000    | ~288 K              | DNA-based life, epigenetics, genetic code          |
| 13 | Present          | 300,000    | ~288 K              | Complex multicellular life, intelligence           |

The epoch timeline is logarithmic in physical time but linear in simulation
ticks. Each application uses the same tick-based boundaries, ensuring identical
epoch transitions regardless of implementation language.

### The 5 Physics Subsystems

Each application implements these subsystems as modules, classes, or structs
depending on the language idioms:

**1. QuantumField**

Manages quantum-scale physics from the Planck epoch through hadron formation.
Models particle creation via vacuum fluctuations, pair production and
annihilation, quantum wave functions (amplitude, phase, Born rule collapse),
entangled pairs (EPR), quark confinement into hadrons (protons and neutrons),
and decoherence. Particles include up quarks, down quarks, electrons,
positrons, neutrinos, photons, gluons, W/Z bosons, protons, and neutrons.
Each particle carries position, momentum, spin, and color charge.

**2. AtomicSystem**

Models atomic physics from the recombination epoch onward. Handles electron
shell filling (Aufbau principle with 7 shells), ionization and electron
capture, nucleosynthesis (primordial and stellar), the triple-alpha process
(3 He -> C), and chemical bonding potential (covalent, ionic, polar covalent).
Implements a partial periodic table (H through Ca plus Fe, 21 elements) with
electronegativity values for bond-type determination.

**3. ChemicalSystem**

Handles molecular formation from the Earth epoch onward. Forms water (H2O),
methane (CH4), ammonia (NH3), amino acids (20 types from the standard genetic
code), and nucleotides (A, T, G, C with sugar-phosphate backbone). Chemical
reactions are driven by activation energy, temperature, and catalyst presence.
Tracks molecule census, reaction counts, and organic molecule classification.

**4. Biosphere**

Simulates biological evolution from the Life epoch onward (when the
Environment reports habitable conditions). Models DNA strands with genes and
epigenetic marks (methylation, histone acetylation), RNA transcription (T->U),
protein translation via codon table (64 codons -> 20 amino acids + STOP),
protein folding, cell metabolism (enzyme-dependent energy extraction), cell
division with semi-conservative DNA replication, point mutations driven by
UV intensity and cosmic ray flux, natural selection (top 50% reproduce),
and population dynamics with a cap of 100 cells. Fitness is computed from
functional protein count, energy reserves, and GC content optimality.

**5. Environment**

Tracks the physical context that affects all other subsystems. Models
temperature evolution (logarithmic cooling from 10^10 K to ~288 K),
UV intensity (modulated by day/night cycle), cosmic ray flux, atmospheric
density (grows with planet formation, shields from radiation), water
availability, day/night cycles (100-tick period), seasonal variations
(1000-tick period), and random environmental events (volcanic eruptions,
asteroid impacts, solar flares, ice ages). Reports habitability based on
temperature (200-400 K), water availability (>0.1), and radiation dose
below the damage threshold.

**Universe (Orchestrator)**

The Universe class ties everything together. It initializes the quantum field
at Planck temperature, seeds the early universe with 30 up quarks, 20 down
quarks, 40 electrons, and 5 photons, then steps through all 300,000 ticks.
At each step it updates the environment, evolves the quantum field, triggers
hadron formation, runs nucleosynthesis, performs recombination, drives stellar
nucleosynthesis, activates chemistry when Earth forms, and starts the
biosphere when conditions become habitable. It records state snapshots,
epoch transitions, and simulation metrics (wall time, CPU time, peak memory).

---

## Application Matrix

| App                | Directory                  | Language       | Execution Mode                          |
|--------------------|----------------------------|----------------|-----------------------------------------|
| Python CLI         | `simulator/`               | Python 3.11    | Terminal ANSI UI                        |
| Node.js CLI        | `apps/nodejs/`             | JavaScript ES modules | Terminal ANSI UI                 |
| Perl CLI           | `apps/perl/`               | Perl 5         | Terminal ANSI UI                        |
| Go CLI + SSE       | `apps/go/`                 | Go 1.22        | Terminal CLI + HTTP SSE streaming       |
| Rust CLI           | `apps/rust/`               | Rust           | Terminal CLI                            |
| C CLI              | `apps/c/`                  | C11            | Terminal CLI                            |
| C++ CLI            | `apps/cpp/`                | C++20          | Terminal CLI                            |
| Java GUI           | `apps/java/`               | Java 21        | Swing GUI with terminal/visual/audio    |
| TypeScript Audio   | `apps/typescript/`         | TypeScript     | Browser Web Audio API sonification      |
| WebAssembly        | `apps/wasm/`               | Rust -> WASM   | Browser WebGPU particle rendering       |
| PHP Snapshot       | `apps/php/`                | PHP 8.4        | HTTP auto-refresh snapshot server       |
| Swift iOS          | `apps/swift/`              | Swift          | SwiftUI + Metal rendering               |
| Kotlin Android     | `apps/kotlin/`             | Kotlin         | Jetpack Compose + OpenGL ES             |
| macOS Screensaver  | `apps/screensaver-macos/`  | Swift          | ScreenSaverView + Metal                 |
| Ubuntu Screensaver | `apps/screensaver-ubuntu/` | C              | X11 + OpenGL                            |

---

## Per-Application Details

### 1. Python CLI (Reference Implementation)

**Description:** The reference implementation of the simulation engine. All
other ports mirror its behavior. Runs the full simulation from the Big Bang
to the Present epoch with an ANSI-colored terminal UI featuring Unicode
box-drawing characters, progress bars, sparkline charts, and a final report
with performance metrics.

**Build command:**
```
python run_demo.py
```

**Run command:**
```
python run_demo.py
```

**Key features:**
- Reference implementation that defines the canonical simulation behavior
- ANSI terminal UI with box-drawing characters and 256-color support
- AST DSL reactive agent demo (parses its own source code at startup)
- Performance metrics: wall time, CPU user/system time, peak memory (via tracemalloc)
- Configurable seed, max ticks, and step size
- State snapshots recorded every 1% of simulation progress
- Sparkline charts for temperature and population history in final report
- 400 tests across 9 test files covering all subsystems

**File structure:**
```
simulator/
  __init__.py
  constants.py        # Physical constants, epoch timeline, biology parameters
  quantum.py          # QuantumField, Particle, WaveFunction, EntangledPair
  atomic.py           # AtomicSystem, Atom, ElectronShell, periodic table
  chemistry.py        # ChemicalSystem, Molecule, ChemicalReaction
  biology.py          # Biosphere, Cell, DNAStrand, Gene, Protein, epigenetics
  environment.py      # Environment, EnvironmentalEvent
  terminal_ui.py      # ANSI rendering: box(), progress_bar(), sparkline()
run_demo.py           # Entry point
tests/                # 9 test files, ~3200 lines
```

---

### 2. Node.js CLI

**Description:** A JavaScript ES modules port that runs the same simulation
with a rich ANSI terminal output. Features epoch-colored progress bars,
formatted temperature display (GK/MK/kK/K), and a comprehensive final report
with element and molecule breakdowns.

**Build command:**
```
cd apps/nodejs && npm install  # (no dependencies to install)
```

**Run command:**
```
cd apps/nodejs && node index.js
# or: node index.js --step 100 --max 300000 --interval 5000
```

**Key features:**
- ES module architecture with `"type": "module"` in package.json
- CLI argument parsing: `--step`, `--max`, `--interval`, `--help`
- Epoch-colored output with per-epoch ANSI color mapping
- Temperature auto-formatting (GK, MK, kK, K units)
- Progress bars with Unicode block characters
- DNA sequence display in biological epochs
- Habitability indicator with UV and cosmic ray readings
- 194 tests using `node:test` built-in test runner

**File structure:**
```
apps/nodejs/
  index.js             # CLI entry point with ANSI formatting
  constants.js         # Physical constants, epoch definitions
  quantum.js           # QuantumField, particles, wave functions
  atomic.js            # AtomicSystem, Atom, electron shells
  chemistry.js         # ChemicalSystem, molecular formation
  biology.js           # Biosphere, cells, DNA, epigenetics
  environment.js       # Environment, events, habitability
  universe.js          # Universe orchestrator
  package.json         # ES module config
  test/
    test_simulator.js  # 194 tests using node:test
```

---

### 3. Perl CLI

**Description:** A Perl 5 implementation using object-oriented modules in
`lib/`. Runs the simulation with epoch-by-epoch terminal output showing
temperature, scale factor, and cumulative statistics for particles, atoms,
molecules, and lifeforms.

**Build command:**
```
# No build step required
```

**Run command:**
```
cd apps/perl && perl simulate.pl
```

**Key features:**
- Object-oriented Perl modules using `bless` and package namespaces
- Callback-based epoch reporting via `on_epoch_complete` subroutine
- Time::HiRes for precise elapsed-time measurement
- Configurable ticks per epoch
- 376 tests using Test::More across 7 test files

**File structure:**
```
apps/perl/
  simulate.pl          # Entry point
  lib/
    Universe.pm        # Orchestrator
    Quantum.pm         # Quantum field simulation
    Atomic.pm          # Atomic physics
    Chemistry.pm       # Molecular chemistry
    Biology.pm         # Biological systems
    Environment.pm     # Environmental modeling
    Constants.pm       # Physical constants
  t/
    01_constants.t     # Constants tests
    02_quantum.t       # Quantum tests
    03_atomic.t        # Atomic tests
    04_chemistry.t     # Chemistry tests
    05_biology.t       # Biology tests
    06_universe.t      # Universe integration tests
```

---

### 4. Go CLI + SSE Server

**Description:** A dual-mode Go application. The CLI (`cmd/simulator/`)
runs the simulation with ASCII-art banners and formatted terminal output.
The SSE server (`cmd/server/`) runs the simulation on the backend and
streams real-time JSON snapshots to a browser dashboard via Server-Sent
Events, with an embedded web frontend.

**Build command:**
```
cd apps/go && go build ./cmd/simulator/
cd apps/go && go build ./cmd/server/
```

**Run command (CLI):**
```
cd apps/go && ./simulator
```

**Run command (SSE server):**
```
cd apps/go && ./server --port 8080
# Then open http://localhost:8080 in a browser
```

**Key features:**
- Two separate entry points: `cmd/simulator/` (CLI) and `cmd/server/` (SSE)
- Cross-compiled to 5 platforms: linux-amd64, linux-arm64, darwin-amd64,
  darwin-arm64, windows-amd64
- SSE server with broker pattern for multiple simultaneous browser viewers
- JSON snapshot API at `/api/snapshot`
- Embedded web frontend using `go:embed` (HTML, CSS, JS)
- Per-viewer seed selection via query parameter
- Epoch-specific ASCII art symbols in progress bars
- Real-time browser dashboard with connection status, epoch progress,
  particle/atom/molecule/cell counts, and animated star background
- Rate-limited broadcast (50ms minimum interval)

**File structure:**
```
apps/go/
  go.mod                   # Go 1.22 module
  cmd/
    simulator/main.go      # CLI entry point with ASCII banners
    server/
      main.go              # SSE HTTP server with broker pattern
      web/
        index.html         # Browser dashboard
        style.css          # Dashboard styles
        app.js             # EventSource consumer, DOM updates
  simulator/
    constants.go           # Physical constants, epochs
    quantum.go             # QuantumField
    atomic.go              # AtomicSystem
    chemistry.go           # ChemicalSystem
    biology.go             # Biosphere
    environment.go         # Environment
    universe.go            # Universe orchestrator
  web/                     # Alternate web assets directory
  builds/                  # Pre-built binaries for 5 platforms
```

---

### 5. Rust CLI

**Description:** A native Rust implementation with release-optimized binary
(LTO, single codegen unit, stripped). Displays epoch banners, inline progress
bars with carriage-return updates, and a comprehensive final summary with
species, oxygen levels, and habitability status.

**Build command:**
```
cd apps/rust && cargo build --release
```

**Run command:**
```
cd apps/rust && cargo run --release
# or: ./target/release/inthebeginning-rust
```

**Key features:**
- Release binary approximately 464 KB (with LTO, strip, and single codegen unit)
- Inline progress bar with carriage-return (\r) for live terminal updates
- Optional SDL2+OpenGL GUI via `--features gui` (requires sdl2 and gl crates)
- Epoch banners with box-drawing characters
- Scientific notation formatting for temperatures and energies
- Species count and atmospheric oxygen percentage tracking
- Dual callback system: `on_epoch` for banners, `on_tick` for progress

**File structure:**
```
apps/rust/
  Cargo.toml               # Edition 2021, release profile optimized
  Cargo.lock
  src/
    main.rs                # CLI entry point, display helpers
    simulator/
      mod.rs               # Module declarations
      constants.rs         # Physical constants
      quantum.rs           # QuantumField
      atomic.rs            # AtomicSystem
      chemistry.rs         # ChemicalSystem
      biology.rs           # Biosphere
      environment.rs       # Environment
      universe.rs          # Universe orchestrator
```

---

### 6. C CLI

**Description:** A C11 implementation with epoch-specific ASCII art for each
cosmic era (singularity, exponential expansion, quark-gluon plasma, etc.).
Supports both dynamic and static linking, with verbose output showing quantum
field state, atomic census, chemistry, biosphere statistics, and environmental
conditions at each epoch transition.

**Build command:**
```
cd apps/c && make
```

**Run command:**
```
cd apps/c && ./build/simulator
# Options: -v (verbose), -s NUM (seed), -h (help)
```

**Key features:**
- C11 standard with `-Wall -Wextra -O2` warnings
- Static linking option: `make static` produces a fully self-contained binary
- Epoch-specific ASCII art (singularity, exponential expansion, quark-gluon
  plasma, hadron confinement, nucleosynthesis, CMB, stellar ignition, solar
  system formation, volcanic Earth, hydrothermal vents, DNA replication,
  complex life)
- Variable step size per epoch (1 tick in Planck, up to 5000 in Recombination)
- Automatic epoch boundary alignment
- Full event log with tick and epoch association
- Atmosphere composition summary

**File structure:**
```
apps/c/
  Makefile                 # Targets: all, static, clean
  simulator/
    main.c                 # CLI entry point, ASCII art, report printers
    constants.h            # Physical constants, epoch enum
    quantum.c / quantum.h  # QuantumField
    atomic.c / atomic.h    # AtomicSystem
    chemistry.c / chemistry.h  # ChemicalSystem
    biology.c / biology.h  # Biosphere
    environment.c / environment.h  # Environment
    universe.c / universe.h  # Universe orchestrator
  build/                   # Build output directory
```

---

### 7. C++ CLI

**Description:** A modern C++20 implementation using CMake. Features
ANSI-colored epoch headers with per-epoch color coding, a tabular summary
of all 13 epochs at completion, and support for running individual epochs
via the `--epoch N` flag. Optionally builds a GUI target with SDL2+OpenGL.

**Build command:**
```
cd apps/cpp && cmake -B build && cmake --build build
```

**Run command:**
```
cd apps/cpp && ./build/inthebeginning
# Options: --epoch N, --verbose/-v, --no-color, --help/-h
```

**Key features:**
- C++20 standard with `-Wall -Wextra -Wpedantic -O2`
- CMake build system with `CMAKE_EXPORT_COMPILE_COMMANDS` for IDE integration
- Optional GUI build: `cmake -B build -DBUILD_GUI=ON` (requires SDL2 + OpenGL)
- Per-epoch ANSI color coding (13 distinct colors)
- Tabular epoch summary at simulation completion
- Single-epoch execution mode (`--epoch N` runs epochs 1 through N)
- `--no-color` flag for piping output to files
- Callback-based simulation with `universe.simulate()` accepting a lambda

**File structure:**
```
apps/cpp/
  CMakeLists.txt           # C++20, CLI + optional GUI targets
  simulator/
    main.cpp               # CLI entry point, display functions
    constants.hpp          # Physical constants
    quantum.cpp / quantum.hpp    # QuantumField
    atomic.cpp / atomic.hpp      # AtomicSystem
    chemistry.cpp / chemistry.hpp  # ChemicalSystem
    biology.cpp / biology.hpp    # Biosphere
    environment.cpp / environment.hpp  # Environment
    universe.cpp / universe.hpp  # Universe orchestrator
  build/                   # CMake build output
```

---

### 8. Java GUI

**Description:** A Java 21 Swing application with a Gradle build system.
Runs the simulation with ANSI-colored terminal output showing per-epoch
physics data including particle breakdowns, element census, molecule counts,
biological species census, and environmental conditions. Distributed as a
fat JAR for single-file execution.

**Build command:**
```
cd apps/java && gradle fatJar
```

**Run command:**
```
cd apps/java && java -jar build/libs/java-all.jar
# or: gradle run
# Optional: pass a seed as first argument
```

**Key features:**
- Java 21 toolchain with Gradle build
- Fat JAR distribution (single executable JAR with no external dependencies)
- ANSI-colored terminal output with epoch-specific colors (13 color codes)
- Per-epoch detailed physics summary: temperature, scale factor, total energy,
  particle breakdown, element census, molecule counts, environment state
- Biological system reporting: species census, DNA replications, extinctions,
  fitness tracking, max evolutionary generation
- Environmental state: surface temperature, ocean coverage, atmospheric
  composition, liquid water detection, complex life support
- Full event log with chronological simulation events
- JVM args: `-Xmx512m` memory limit
- Configurable random seed via command-line argument

**File structure:**
```
apps/java/
  build.gradle             # Java 21, application plugin, fatJar task
  src/main/java/com/inthebeginning/simulator/
    SimulatorApp.java      # Entry point, display functions
    Constants.java         # Physical constants, epoch definitions
    QuantumField.java      # Quantum field, particles
    Particle.java          # Particle data class
    ParticleType.java      # Particle type enum
    Atom.java              # Atom with electron shells
    AtomicSystem.java      # Atomic system
    Molecule.java          # Molecule data class
    ChemicalSystem.java    # Chemical reactions
    BiologicalSystem.java  # Biology, DNA, evolution
    Environment.java       # Environmental modeling
    Universe.java          # Universe orchestrator
  build/                   # Gradle build output
```

---

### 9. TypeScript Audio (Browser Sonification)

**Description:** A TypeScript application that sonifies the cosmic simulation
through the Web Audio API. Each epoch maps to a musical key root (cycling
through C, D, E, F#, G#, Bb), temperature controls a global lowpass filter
cutoff, particle count modulates reverb wet/dry mix, and different epoch
categories trigger distinct instrument voices: sine blips for quantum epochs,
harmonic stacking for atomic, FM bell tones for chemistry, and rhythmic pulse
sequences for biology. Renders a fullscreen spectrogram canvas.

**Build command:**
```
cd apps/typescript && npm install && npm run build:all
```

**Run command (browser):**
```
cd apps/typescript && npx serve public
# Then open http://localhost:3000 in a browser
```

**Run command (CLI):**
```
cd apps/typescript && npm run build && npm start
```

**Key features:**
- Dual build targets: Node.js CLI (`tsconfig.json`) and browser
  (`tsconfig.browser.json`)
- Web Audio API sonification with epoch-to-key mapping (13 MIDI root notes)
- Instrument voices: sine blips, bell tones, pulses, pads, melodic sequences
- Fullscreen spectrogram canvas visualization via AnalyserNode FFT
- Volume and tempo controls in browser UI
- Mute button, click-to-start overlay (Web Audio autoplay policy compliance)
- HUD overlay showing epoch name, tick progress, temperature, particle count
- Import map for ES module resolution in browser
- TypeScript 5.4+, strict mode

**File structure:**
```
apps/typescript/
  package.json             # Dual build scripts, TypeScript 5.4
  tsconfig.json            # Node.js target
  tsconfig.browser.json    # Browser target
  src/
    index.ts               # CLI entry point
    constants.ts           # Physical constants
    simulator.ts           # Simulation engine
    audio_engine.ts        # Web Audio sonification engine
    instruments.ts         # Tone generators (sine, bell, pulse, pad)
    browser_main.ts        # Browser entry point
  public/
    index.html             # Browser UI with spectrogram canvas
    style.css              # Dark theme styles
  dist/                    # Node.js build output
  dist-browser/            # Browser build output
```

---

### 10. WebAssembly (WebGPU Particle Rendering)

**Description:** A Rust-to-WebAssembly application that renders the cosmic
simulation as a fullscreen particle visualization using WebGPU. Particles,
atoms, molecules, and cells are drawn as instanced billboard quads with
circular fragment masking and epoch-derived color palettes. The simulation
runs in the browser with WGSL shaders for GPU-accelerated rendering.

**Build command:**
```
cd apps/wasm && ./build.sh
# or: wasm-pack build --target web --out-dir pkg
```

**Run command:**
```
cd apps/wasm && python3 -m http.server 8080
# Then open http://localhost:8080 in a WebGPU-capable browser (Chrome 113+)
```

**Key features:**
- Rust compiled to WebAssembly via wasm-bindgen and wasm-pack
- WebGPU rendering pipeline with WGSL particle shaders
- Instanced billboard quads with circular fragment masking
- Epoch-based background color gradients
- Fullscreen canvas with dark monospace HUD overlay
- Epoch name, description, progress bar, and stats display
- Size-optimized WASM (`opt-level = "s"`, LTO enabled)
- Dependencies: wgpu 28.0, wasm-bindgen, web-sys, bytemuck

**File structure:**
```
apps/wasm/
  Cargo.toml               # cdylib crate, WebGPU dependencies
  Cargo.lock
  build.sh                 # wasm-pack build script
  index.html               # Fullscreen canvas, HUD overlay, ES module import
  src/
    lib.rs                 # WASM entry point
    constants.rs           # Physical constants
    quantum.rs             # QuantumField
    atomic.rs              # AtomicSystem
    chemistry.rs           # ChemicalSystem
    biology.rs             # Biosphere
    environment.rs         # Environment
    universe.rs            # Universe orchestrator
    renderer.rs            # WebGPU renderer (Uniforms, InstanceData, pipeline)
    shaders/
      particle.wgsl        # Vertex/fragment shaders for particle rendering
```

---

### 11. PHP Snapshot Server

**Description:** A PHP 8.4 application with two modes. The CLI script
(`simulate.php`) runs the simulation and prints epoch-by-epoch results.
The HTTP server (`server.php`) runs on PHP's built-in web server and serves
an HTML snapshot page that auto-refreshes every 10 seconds, plus a JSON
API endpoint for programmatic access.

**Build command:**
```
# No build step required
```

**Run command (CLI):**
```
cd apps/php && php simulate.php
```

**Run command (HTTP server):**
```
cd apps/php && php -S localhost:8080 server.php
# Then open http://localhost:8080
```

**Key features:**
- PHP 8.4 with strict types and named arguments
- Built-in PHP development server (no Apache/nginx required)
- HTML snapshot with `<meta http-equiv="refresh" content="10">` auto-refresh
- JSON API endpoint at `/api/state` with CORS headers
- Simulation reset endpoint at `/api/reset`
- CSS-styled card layout with progress bar
- Server-side rendering via PHP templates
- Simulation state persisted across requests via static class properties

**File structure:**
```
apps/php/
  server.php               # HTTP router, SimulationServer class
  simulate.php             # CLI entry point
  simulator/
    Universe.php           # Universe orchestrator
    Constants.php          # Physical constants
    Quantum.php            # QuantumField
    Atomic.php             # AtomicSystem
    Chemistry.php          # ChemicalSystem
    Biology.php            # Biosphere
    Environment.php        # Environment
  templates/
    snapshot.php           # HTML template with epoch data cards
  public/
    style.css              # Card layout styles
```

---

### 12. Swift iOS App

**Description:** A SwiftUI application with Metal GPU rendering targeting
iOS 17, iPadOS, and tvOS. Renders simulation entities (particles, atoms,
molecules, cells) as instanced point sprites with epoch-based color palettes.
Includes an epoch timeline view, settings panel, and audio engine for
sonification.

**Build command:**
```
cd apps/swift && swift build
# or: xcodebuild (with Xcode project)
```

**Run command:**
```
# Run via Xcode on iOS Simulator or physical device
# or: swift run InTheBeginning
```

**Key features:**
- SwiftUI app lifecycle with `@main` attribute
- Metal rendering pipeline with custom shaders (Shaders.metal)
- Instanced point sprites with per-entity position, color, size, and category
- Projection and model-view matrix uniforms
- Epoch-based color palette
- Epoch timeline view, settings view, and simulation view
- AVAudioEngine-based audio sonification
- Swift Package Manager (Package.swift) with library + executable targets
- Platforms: iOS 17, macOS 14, tvOS 17
- Dark color scheme preferred

**File structure:**
```
apps/swift/
  Package.swift            # SPM: InTheBeginningSimulator library + app target
  Info.plist
  InTheBeginning/
    App.swift              # @main SwiftUI app entry point
    Views/
      SimulationView.swift     # Main simulation display
      EpochTimelineView.swift  # Epoch progress timeline
      SettingsView.swift       # Configuration panel
    Renderer/
      MetalRenderer.swift  # Metal GPU rendering pipeline
      Shaders.metal        # Vertex/fragment shaders
    Audio/
      AudioEngine.swift    # AVAudioEngine sonification
    Simulator/
      Constants.swift      # Physical constants
      QuantumField.swift   # Quantum physics
      AtomicSystem.swift   # Atomic physics
      ChemicalSystem.swift # Chemistry
      Biosphere.swift      # Biology
      Environment.swift    # Environmental modeling
      Universe.swift       # Orchestrator
```

---

### 13. Kotlin Android App

**Description:** An Android application built with Jetpack Compose and
Material You (Material 3 with dynamic colors). Features an OpenGL ES 2.0
renderer for particle visualization with pinch-to-zoom and pan gestures,
a settings screen for seed and speed configuration, and a ViewModel-based
architecture for lifecycle-aware simulation management.

**Build command:**
```
cd apps/kotlin && ./gradlew assembleRelease
```

**Run command:**
```
# Install via: adb install app/build/outputs/apk/release/app-release.apk
# or: ./gradlew installDebug
```

**Key features:**
- Jetpack Compose UI with Material 3 (Material You dynamic colors)
- OpenGL ES 2.0 renderer for particle/atom/molecule/cell visualization
- Pinch-to-zoom and pan gesture support
- ViewModel architecture with StateFlow for reactive UI updates
- Coroutine-based simulation loop on `Dispatchers.Default` (UI stays responsive)
- Play/pause/reset controls with speed slider (10-2000 ticks per step)
- Settings screen with seed, speed, and visualization style configuration
- Edge-to-edge display with dark theme
- ProGuard/R8 minification and resource shrinking in release builds
- Min SDK 26, Target SDK 34
- Compose BOM 2024.02.00 for coordinated library versions

**File structure:**
```
apps/kotlin/
  build.gradle.kts             # Root build config
  settings.gradle.kts
  gradle.properties
  app/
    build.gradle.kts           # Android plugin, Compose, OpenGL ES
    src/main/
      AndroidManifest.xml
      java/com/inthebeginning/
        MainActivity.kt       # ComponentActivity, SimulationViewModel
        simulator/
          Constants.kt         # Physical constants
          QuantumField.kt      # Quantum physics
          AtomicSystem.kt      # Atomic physics
          ChemicalSystem.kt    # Chemistry
          Biosphere.kt         # Biology
          Environment.kt       # Environmental modeling
          Universe.kt          # Orchestrator with StateFlow
        renderer/
          SimulationRenderer.kt  # OpenGL ES 2.0 GLSurfaceView.Renderer
        ui/
          SimulationScreen.kt  # Main Compose UI with Canvas + gestures
          SettingsScreen.kt    # Configuration screen
          theme/
            Color.kt           # Material You color definitions
            Theme.kt           # Dark/light theme setup
      res/
        values/
          strings.xml
          themes.xml
```

---

### 14. macOS Screensaver

**Description:** A macOS screensaver bundle (`.saver`) that renders the
cosmic simulation using Metal (with a Core Graphics fallback). Subclasses
`ScreenSaverView` and advances the simulation by a fixed number of ticks
per frame at 30 fps. Each activation starts from the Big Bang with a random
seed. Displays a HUD overlay with epoch name, description, tick count,
temperature, and entity counts.

**Build command:**
```
cd apps/screensaver-macos && make
```

**Run command:**
```
make install
# Then select "InTheBeginning" in System Preferences > Screen Saver
```

**Key features:**
- `ScreenSaverView` subclass with 30 fps animation
- Metal rendering (preferred) with Core Graphics fallback
- Epoch-based background glow using radial CGGradient (13 color schemes)
- Entity rendering as glowing ellipses with position/size/color mapping
- HUD overlay with epoch name, description, stats (drawn via NSAttributedString)
- Random seed on each screensaver activation
- No Xcode project required -- builds with `swiftc` and Make
- Targets macOS 12.0+ (x86_64, can be modified for arm64)
- Frameworks: ScreenSaver, AppKit, Metal, MetalKit

**File structure:**
```
apps/screensaver-macos/
  Makefile                     # swiftc build, install to ~/Library/Screen Savers/
  InTheBeginning.xcodeproj/    # Optional Xcode project
    project.pbxproj
  InTheBeginning/
    InTheBeginningView.swift   # ScreenSaverView subclass, Metal + CG rendering
    Info.plist                 # Bundle metadata
    Renderer/
      MetalRenderer.swift      # Metal pipeline, point sprite instances
      Shaders.metal            # Metal vertex/fragment shaders
    Simulator/
      Constants.swift
      QuantumField.swift
      AtomicSystem.swift
      ChemicalSystem.swift
      Environment.swift
      Biosphere.swift
      Universe.swift
```

---

### 15. Ubuntu Screensaver

**Description:** A standalone X11/OpenGL screensaver for Linux that can run
as a fullscreen application, an XScreenSaver module (with `-root`), or in
windowed mode (with `-window` for testing). Renders particles as colored
points with epoch-specific color schemes using immediate-mode OpenGL. Includes
a `.desktop` file for XScreenSaver/GNOME integration.

**Build command:**
```
cd apps/screensaver-ubuntu && make
```

**Run command:**
```
cd apps/screensaver-ubuntu && ./inthebeginning-screensaver
# Flags: -root (XScreenSaver mode), -window (windowed test mode)
```

**Install command:**
```
sudo make install
# Installs to /usr/local/libexec/xscreensaver/ and registers .desktop file
```

**Key features:**
- C11 with X11, OpenGL, and GLX
- Three run modes: standalone fullscreen, XScreenSaver hack (`-root`),
  windowed testing (`-window`)
- 14 epoch-specific RGB color schemes
- 30 fps target with POSIX nanosleep timing
- Up to 2048 simultaneously rendered particles
- `.desktop` file for XScreenSaver and GNOME screensaver integration
- Install/uninstall Make targets
- Handles X11 `Atom` typedef conflict by `#define`/`#undef` around X11 headers
- Links against: libX11, libGL, libGLX, libm

**File structure:**
```
apps/screensaver-ubuntu/
  Makefile                          # Build, install, uninstall targets
  inthebeginning-screensaver.c      # X11/OpenGL rendering, main loop
  inthebeginning.desktop            # XScreenSaver/GNOME registration
  simulator/
    constants.h                     # Physical constants
    universe.c / universe.h         # Simplified simulation for screensaver
```

---

### 16. Audio Composition Engine

**Description:** A Python-based audio composition engine that sonifies the cosmic
simulation into structured, multi-track music. Features a bar-oriented architecture
with real time signatures, 537+ synthesized instruments, MIDI library sampling from
1,771 public domain classical works by 120+ composers, FluidSynth integration with
128 General MIDI instruments, and world musical scales spanning Western classical,
Asian, Middle Eastern, Indian, and African traditions. V20 engine adds volume
normalization to -1dB peak, lookahead limiter for spike prevention, and 10-20%
solo instrument moods for variety.

**Build command:**
```
# No build step required
```

**Run command:**
```
cd apps/audio && python generate.py
```

**Key features:**
- Bar-based multi-track music with real time signatures (4/4, 3/4, 6/8, 7/8, 5/4)
- 537+ synthesized instruments (strings, winds, bells, percussion, pads, world instruments)
- 1,771 public domain MIDI files from 120+ classical composers (pre-1900)
- FluidSynth integration with FluidR3_GM.sf2 (128 General MIDI instruments)
- Multi-TTS voice injection: espeak-ng, flite, festival, pico2wave
- V20 engine: master normalization (-1dB peak), lookahead limiter, solo moods
- World musical scales (30+ scales from 6 traditions)
- Additive synthesis timbres with FFT-guided waveform shaping
- Polyrhythmic patterns (3:2, 4:3, 5:4, West African, gamelan)
- No external dependencies -- pure Python stdlib (math, random, struct)
- Optional: FluidSynth, mido (MIDI parsing), numpy, ffmpeg (MP3 output)

**File structure:**
```
apps/audio/
  composer.py            # Musical composition engine with world traditions
  music_engine.py        # Bar-oriented multi-track structured music engine
  generate.py            # Audio generation entry point
  sample_gen.py          # Instrument sample generation
  test_audio.py          # Audio engine tests
  test_composer.py       # Composer tests
  test_music_engine.py   # Music engine tests
  samples/               # 45+ instrument samples (MP3)
  midi_library/          # 1,771 classical MIDI files from 120+ composers
```

---

## Build Quick Reference

| App                | Build Command                                          | Run Command                                     | Output                          |
|--------------------|--------------------------------------------------------|-------------------------------------------------|---------------------------------|
| Python CLI         | (none)                                                 | `python run_demo.py`                            | Terminal output                 |
| Node.js CLI        | (none)                                                 | `cd apps/nodejs && node index.js`               | Terminal output                 |
| Perl CLI           | (none)                                                 | `cd apps/perl && perl simulate.pl`              | Terminal output                 |
| Go CLI             | `cd apps/go && go build ./cmd/simulator/`              | `./simulator`                                   | Terminal output                 |
| Go SSE Server      | `cd apps/go && go build ./cmd/server/`                 | `./server --port 8080`                          | HTTP on port 8080               |
| Rust CLI           | `cd apps/rust && cargo build --release`                | `./target/release/inthebeginning-rust`          | Terminal output                 |
| C CLI              | `cd apps/c && make`                                    | `./build/simulator`                             | Terminal output                 |
| C CLI (static)     | `cd apps/c && make static`                             | `./build/simulator-static`                      | Terminal output                 |
| C++ CLI            | `cd apps/cpp && cmake -B build && cmake --build build` | `./build/inthebeginning`                        | Terminal output                 |
| Java GUI           | `cd apps/java && gradle fatJar`                        | `java -jar build/libs/java-all.jar`             | Terminal output                 |
| TypeScript Audio   | `cd apps/typescript && npm run build:all`               | Open `public/index.html` via HTTP server        | Browser audio + spectrogram     |
| WebAssembly        | `cd apps/wasm && ./build.sh`                           | Serve directory, open in WebGPU browser         | Browser particle visualization  |
| PHP Snapshot       | (none)                                                 | `cd apps/php && php -S localhost:8080 server.php` | HTTP on port 8080              |
| Swift iOS          | `cd apps/swift && swift build`                         | Run via Xcode on device/simulator               | iOS/iPadOS/tvOS app             |
| Kotlin Android     | `cd apps/kotlin && ./gradlew assembleRelease`          | Install APK via adb                             | Android app                     |
| macOS Screensaver  | `cd apps/screensaver-macos && make`                    | `make install`, select in System Preferences    | .saver bundle                   |
| Ubuntu Screensaver | `cd apps/screensaver-ubuntu && make`                   | `./inthebeginning-screensaver`                  | X11/OpenGL fullscreen           |
