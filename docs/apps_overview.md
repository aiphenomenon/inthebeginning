# In The Beginning: Simulation Applications Overview

## Summary

The "In The Beginning" project implements a cosmic evolution simulator across
14+ languages and platforms. Each application models the same physical timeline
-- from the Big Bang through the emergence of DNA-based life -- using a shared
architecture of 13 epochs and 5 physics subsystems. Every app also integrates
AST self-introspection, parsing its own source code at startup or via a CLI
flag.

---

## Application Matrix

| Language     | App Directory            | Type                         | Platform             | Build System       | Status      |
|-------------|--------------------------|------------------------------|----------------------|--------------------|-----------  |
| Python       | `simulator/`             | CLI (reference impl)         | Cross-platform       | `python run_demo.py`| Complete   |
| C            | `apps/c/`                | SDL2/OpenGL native           | Linux, macOS         | Make / CMake       | Complete    |
| C++          | `apps/cpp/`              | SDL2/OpenGL native           | Linux, macOS         | CMake              | Complete    |
| Rust         | `apps/rust/`             | CLI native, optional GUI     | Cross-platform       | Cargo (musl)       | Complete    |
| Go           | `apps/go/`               | CLI + SSE web server         | Cross-platform       | `go build`         | Complete    |
| Java         | `apps/java/`             | Swing GUI (4 modes)          | Cross-platform       | Gradle (fatJar)    | Complete    |
| Node.js      | `apps/nodejs/`           | CLI with colored terminal    | Cross-platform       | `node index.js`    | Complete    |
| TypeScript   | `apps/typescript/`       | CLI + Web Audio browser      | Cross-platform       | `tsc` / npm        | Complete    |
| Perl         | `apps/perl/`             | CLI terminal                 | Cross-platform       | `perl simulate.pl` | Complete    |
| PHP          | `apps/php/`              | HTTP snapshot server         | Cross-platform       | `php -S`           | Complete    |
| Swift        | `apps/swift/`            | iOS/iPadOS/tvOS (Metal)      | Apple platforms      | Xcode / SPM        | Complete    |
| Kotlin       | `apps/kotlin/`           | Android (Jetpack Compose)    | Android              | Gradle (AAB)       | Complete    |
| WebAssembly  | `apps/wasm/`             | WebGPU browser visualization | Web (modern browsers)| wasm-pack / Cargo  | Complete    |
| macOS Saver  | `apps/screensaver-macos/`| ScreenSaverView + Metal      | macOS (Apple Silicon)| swiftc / Make      | Complete    |
| Ubuntu Saver | `apps/screensaver-ubuntu/`| X11/OpenGL (XScreenSaver)   | Ubuntu 24.04         | Make               | Complete    |

---

## Architecture Diagram

```
 ┌────────────────────────────────────────────────────────────────────────────┐
 │                          IN THE BEGINNING                                  │
 │                    Cosmic Evolution Simulator                              │
 ├────────────────────────────────────────────────────────────────────────────┤
 │                                                                            │
 │  ┌──────────────────────┐         ┌──────────────────────────────────┐     │
 │  │   AST DSL Engine     │         │   Physics Simulation Engine      │     │
 │  │                      │         │                                  │     │
 │  │  13 Language Parsers │         │  5 Subsystems:                   │     │
 │  │  Reactive Protocol   │◄───────►│    QuantumField                  │     │
 │  │  Self-Introspection  │         │    AtomicSystem                  │     │
 │  │  Compact AST Output  │         │    ChemicalSystem                │     │
 │  │                      │         │    Biosphere                     │     │
 │  └──────────────────────┘         │    Environment                   │     │
 │                                   │                                  │     │
 │                                   │  Orchestrated by Universe        │     │
 │                                   └──────────────────────────────────┘     │
 │                                                                            │
 │  ┌─────────────────────────────────────────────────────────────────────┐   │
 │  │                    Application Layer (14+ targets)                   │   │
 │  │                                                                     │   │
 │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │   │
 │  │  │  CLI    │ │  Web    │ │  Native │ │ Desktop │ │ Mobile  │     │   │
 │  │  │         │ │         │ │  GUI    │ │ Savers  │ │         │     │   │
 │  │  │ Python  │ │ Go SSE  │ │ C/SDL2  │ │ macOS   │ │ Swift   │     │   │
 │  │  │ Node.js │ │ PHP     │ │ C++/SDL2│ │ Ubuntu  │ │  (iOS)  │     │   │
 │  │  │ Perl    │ │ TS/Web  │ │ Rust    │ │         │ │ Kotlin  │     │   │
 │  │  │ Rust    │ │  Audio  │ │ Java/   │ │         │ │(Android)│     │   │
 │  │  │         │ │ WASM/   │ │  Swing  │ │         │ │         │     │   │
 │  │  │         │ │  WebGPU │ │         │ │         │ │         │     │   │
 │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │   │
 │  └─────────────────────────────────────────────────────────────────────┘   │
 └────────────────────────────────────────────────────────────────────────────┘
```

---

## Common Simulation Structure

### The 13 Cosmic Epochs

Every application implements the same timeline, defined by simulation ticks:

| #  | Epoch            | Start Tick | Description                                  |
|----|------------------|-----------|----------------------------------------------|
| 1  | Planck           | 1         | All forces unified, T ~ 10^32 K              |
| 2  | Inflation        | 10        | Exponential expansion, quantum fluctuations   |
| 3  | Electroweak      | 100       | EM and weak forces separate                   |
| 4  | Quark            | 1,000     | Quark-gluon plasma, free quarks               |
| 5  | Hadron           | 5,000     | Quarks confined into protons and neutrons      |
| 6  | Nucleosynthesis  | 10,000    | Light nuclei form (H, He, Li)                |
| 7  | Recombination    | 50,000    | Atoms form, universe becomes transparent       |
| 8  | Star Formation   | 100,000   | First stars ignite, stellar nucleosynthesis    |
| 9  | Solar System     | 200,000   | Protoplanetary disks, planet formation         |
| 10 | Earth            | 210,000   | Terrestrial planet with atmosphere             |
| 11 | Life             | 250,000   | First self-replicating molecules               |
| 12 | DNA              | 280,000   | DNA-based life, genetic code, epigenetics      |
| 13 | Present          | 300,000   | Complex multicellular life                     |

### The 5 Physics Subsystems

Each app implements these subsystems as modules, classes, or structs depending
on the language:

1. **QuantumField** -- Manages particle creation and annihilation, quantum
   fluctuations, field interactions. Active from the Planck epoch onward.

2. **AtomicSystem** -- Models electron shell filling, atomic formation, isotope
   stability. Becomes active at the Recombination epoch.

3. **ChemicalSystem** -- Handles molecular bond formation (covalent, ionic,
   hydrogen, van der Waals), chemical reactions. Active from Star Formation.

4. **Biosphere** -- Simulates self-replicating molecules, DNA/RNA transcription,
   mutation, natural selection, epigenetics. Active from the Life epoch.

5. **Environment** -- Tracks temperature, pressure, radiation levels, and
   provides the physical context for all other subsystems.

These are orchestrated by a **Universe** module that manages the cosmic
timeline, epoch transitions, and inter-subsystem coupling.

---

## Per-Application Details

### Python (Reference Implementation)

- **Entry point**: `python run_demo.py`
- **Role**: Reference implementation; all other ports mirror its behavior
- **Features**: AST DSL demo, full simulation, terminal UI with ANSI colors
- **Files**: `simulator/` (7 modules + terminal_ui.py), `ast_dsl/` (13 parsers + core + reactive)

### C (SDL2/OpenGL Native)

- **Entry point**: `make && ./build/simulator`
- **Rendering**: SDL2 windowing + OpenGL 3.3+ core profile, instanced particles
- **Build targets**: Linux AMD64, Linux ARM64, macOS Apple Silicon
- **Static build**: `make static` produces a fully static binary
- **Files**: 14 source files (7 .c + 7 .h), shaders in `shaders/`

### C++ (SDL2/OpenGL Native)

- **Entry point**: `cmake -B build && cmake --build build`
- **Approach**: Modern C++20, RAII, smart pointers, templated physics layers
- **Build modes**: CLI-only (default) or GUI (`-DBUILD_GUI=ON`)
- **Files**: 14 source files, CMakeLists.txt, shaders in `shaders/`

### Rust (CLI + Optional GUI)

- **Entry point**: `cargo run --release`
- **Features**: `default` = CLI only; `gui` = SDL2 + OpenGL rendering
- **Cross-compilation**: `cargo build --target x86_64-unknown-linux-musl`
- **Cargo.toml config**: LTO enabled, single codegen unit, stripped binary
- **Files**: `src/main.rs`, `src/simulator/` (7 modules)

### Go (CLI + SSE Web Server)

- **Entry point**: `go run ./cmd/...`
- **SSE protocol**: JSON snapshots every tick, epoch transition events
- **Frontend**: `web/index.html` with EventSource consumer, live DOM updates
- **Features**: Multiple simultaneous viewers, seed selection via query param
- **Files**: `cmd/`, `server/`, `simulator/` (7 modules), `web/`

### Java (Swing GUI)

- **Entry point**: `gradle run` or `java -jar build/libs/inthebeginning.jar`
- **GUI modes** (tab-selectable):
  1. Terminal Mode -- ANSI-styled text stream
  2. Visual Mode -- Canvas particle rendering
  3. Audio Mode -- MIDI sonification of simulation state
  4. Ongoing Mode -- 10% CPU background, refreshes every 30s
- **Parameter tuning**: Seed, step size, max ticks, mutation rates
- **Capture**: Record simulation to JSON/CSV (max 10 min, 100 MB)
- **Files**: 12 Java files across `simulator/`, `ui/`, `audio/`

### Node.js (CLI Terminal)

- **Entry point**: `node index.js` or `npm start`
- **Rendering**: ANSI terminal UI with 256-color support
- **Features**: Matches Python reference output format
- **Test runner**: `npm test` (built-in Node.js test runner)
- **Files**: `index.js`, 7 simulator modules, `terminal_ui.js`

### TypeScript (CLI + Web Audio Browser)

- **Entry points**:
  - CLI: `npm run build && npm start`
  - Browser: `npm run build:browser` then open `index.html`
- **Sonification mapping**:
  - Quantum epoch: high-frequency sine tones, random panning
  - Atomic epoch: harmonic stacking as shells fill
  - Chemistry: chord progressions for molecular bonds
  - Biology: rhythmic patterns for cell division
- **Files**: `src/` (simulator + audio engine), dual tsconfig

### Perl (CLI Terminal)

- **Entry point**: `perl simulate.pl`
- **Rendering**: ANSI terminal output
- **Modules**: `lib/` with Universe.pm, Quantum.pm, Atomic.pm, etc.
- **Tests**: `t/` directory using Test::More
- **Files**: `simulate.pl`, 8 library modules

### PHP (HTTP Snapshot Server)

- **Entry point**: `php -S 0.0.0.0:8080 server.php`
- **Behavior**: Background simulation loop with usleep() (capped at 10% CPU)
- **HTML output**: Auto-refreshes every 30 seconds via `<meta http-equiv="refresh">`
- **API**: JSON endpoint alongside the HTML snapshot view
- **Files**: `server.php`, `simulate.php`, `simulator/` (7 classes), `templates/`, `public/`

### Swift (iOS/iPadOS/tvOS)

- **Build**: Xcode or `xcodebuild` CLI
- **Rendering**: Metal + SwiftUI
- **Platform adaptations**:
  - iPhone: portrait-optimized, swipe between epochs, haptic feedback
  - iPad: side-by-side parameter panel + visualization, Apple Pencil support
  - tvOS: ambient mode, Siri Remote control, focus-based UI
- **Audio**: AVAudioEngine-based sonification
- **Files**: 14 Swift files across `Simulator/`, `Views/`, `Renderer/`, `Audio/`

### Kotlin (Android)

- **Build**: `./gradlew assembleRelease`
- **UI**: Jetpack Compose + Material You (dynamic colors)
- **Platform adaptations**:
  - Phone: bottom sheet for settings, pinch-to-zoom
  - Tablet: split-pane layout
- **Features**: Home screen widget (current epoch), notification on life emergence
- **Files**: 16 Kotlin files across `simulator/`, `renderer/`, `ui/`

### WebAssembly (WebGPU Browser)

- **Build**: `wasm-pack build --target web`
- **Source language**: Rust compiled to WASM via wasm-bindgen
- **Rendering**: WebGPU pipeline with WGSL shaders
- **Visualization**: Instanced particles, orbital clouds, ball-and-stick molecules
- **Behavior**: Fullscreen, ~10 min per cycle, fade-out and restart with jittered seed
- **Files**: `src/` (9 Rust modules), `src/shaders/` (WGSL), `index.html`

### macOS Screensaver

- **Build**: `make` (uses `swiftc` directly, no Xcode project required)
- **Install**: `make install` copies `.saver` bundle to `~/Library/Screen Savers/`
- **Rendering**: Metal via ScreenSaverView subclass
- **Behavior**: Starts from Big Bang on each activation, random seed
- **Target**: macOS 12.0+ (Apple Silicon / Intel universal)
- **Files**: 9 Swift files, Info.plist, Makefile

### Ubuntu Screensaver

- **Build**: `make`
- **Install**: `make install` registers with XScreenSaver
- **Rendering**: X11 + OpenGL
- **Registration**: `.desktop` file for XScreenSaver/GNOME integration
- **Target**: Ubuntu 24.04 (X11)
- **Files**: `inthebeginning-screensaver.c`, shared `simulator/` (C), Makefile

---

## Build Instructions Quick Reference

| App             | Build Command                                           | Output                       |
|-----------------|--------------------------------------------------------|------------------------------|
| Python          | `python run_demo.py`                                    | Terminal output              |
| C               | `cd apps/c && make`                                     | `build/simulator`            |
| C (static)      | `cd apps/c && make static`                              | `build/simulator-static`     |
| C++             | `cd apps/cpp && cmake -B build && cmake --build build`  | `build/inthebeginning`       |
| Rust            | `cd apps/rust && cargo build --release`                 | `target/release/inthebeginning-rust` |
| Go              | `cd apps/go && go build ./cmd/...`                      | `inthebeginning-go`          |
| Java            | `cd apps/java && gradle fatJar`                         | `build/libs/*.jar`           |
| Node.js         | `cd apps/nodejs && node index.js`                       | Terminal output              |
| TypeScript      | `cd apps/typescript && npm run build && npm start`      | Terminal / browser           |
| Perl            | `cd apps/perl && perl simulate.pl`                      | Terminal output              |
| PHP             | `cd apps/php && php -S 0.0.0.0:8080 server.php`        | HTTP on port 8080            |
| Swift           | `cd apps/swift && xcodebuild`                           | .app bundle                  |
| Kotlin          | `cd apps/kotlin && ./gradlew assembleRelease`           | .apk / .aab                  |
| WebAssembly     | `cd apps/wasm && wasm-pack build --target web`          | `pkg/` WASM bundle           |
| macOS Saver     | `cd apps/screensaver-macos && make`                     | `.saver` bundle              |
| Ubuntu Saver    | `cd apps/screensaver-ubuntu && make`                    | `inthebeginning-screensaver` |

---

## Resource and Energy Guidelines

All applications follow these principles:

- **Battery-aware**: On mobile and laptop platforms, detect battery state and
  reduce simulation fidelity (lower particle count, fewer draw calls, throttled
  tick rate) when running on battery power.

- **CPU headroom**: Simulation thread capped at ~60% of a single core. Background
  apps coexist without lag.

- **Adaptive quality**: If frame time exceeds budget, automatically reduce particle
  count or skip visual detail. Never drop below minimum visual quality threshold.

- **Smooth UX**: Double-buffered rendering, frame pacing, graceful epoch
  transitions across all GUI targets.

- **Minimal permissions**: No camera, microphone, contacts, or location access.
  Only display and audio output are used.
