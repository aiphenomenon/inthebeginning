# In The Beginning -- Cross-Platform Build Guide

A comprehensive guide for building and running the "In The Beginning" multi-language
physics simulator across all supported platforms and language implementations.

---

## Prerequisites

Each language implementation has its own requirements. Install only what you need
for the implementations you plan to build.

| Language   | Toolchain Required                                           |
|------------|--------------------------------------------------------------|
| Python     | Python 3.11+, pip                                            |
| Node.js    | Node.js 22+ (built-in test runner)                           |
| Perl       | Perl 5.20+, `prove` (ships with Perl)                       |
| Go         | Go 1.22+                                                     |
| Rust       | Rust stable toolchain (rustup, cargo)                        |
| C          | GCC or Clang, make, libc math (`-lm`)                       |
| C++        | GCC or Clang (C++20), CMake 3.16+, make                     |
| Java       | JDK 21+ (Temurin recommended)                                |
| TypeScript | Node.js 20+, npm                                            |
| PHP        | PHP 8.0+ (CLI with built-in server)                          |
| WASM       | Rust toolchain + wasm-pack                                   |
| Swift      | Xcode 15+ (macOS only)                                       |
| Kotlin     | Android Studio or Android SDK with Gradle                    |
| macOS Screensaver | Xcode (macOS only)                                    |
| Ubuntu Screensaver | GCC, libx11-dev, libgl1-mesa-dev, libglu1-mesa-dev  |

---

## Quick Start (All Platforms)

Clone the repository and pick any implementation to run:

```bash
git clone <repo-url> inthebeginning
cd inthebeginning
```

The fastest way to see the simulator in action:

```bash
# Python (no compilation step)
python run_demo.py

# Node.js (no compilation step)
node apps/nodejs/index.js

# Perl (no compilation step)
perl apps/perl/simulate.pl
```

For compiled languages, see the dedicated sections below.

---

## Python

Python is the reference implementation with the most comprehensive test suite.

**Run the demo:**

```bash
python run_demo.py
```

**Run all tests (400 tests):**

```bash
python -m pytest tests/ -v
```

---

## Node.js

Uses the Node.js built-in test runner (requires Node.js 22+).

**Run the CLI simulator:**

```bash
node apps/nodejs/index.js
```

**Run tests (194 tests):**

```bash
node --test apps/nodejs/test/test_simulator.js
```

---

## Perl

**Run the CLI simulator:**

```bash
perl apps/perl/simulate.pl
```

**Run tests (376 tests):**

```bash
prove -v apps/perl/t/
```

---

## Go

The Go implementation produces two binaries: a CLI simulator and an SSE
(Server-Sent Events) server.

**Build the CLI:**

```bash
cd apps/go && go build -o simulator ./cmd/simulator/
```

**Build the SSE server:**

```bash
cd apps/go && go build -o server ./cmd/server/
```

**Run vet checks:**

```bash
cd apps/go && go vet ./...
```

### Cross-Compilation

Go supports cross-compilation natively. Set `GOOS` and `GOARCH` before building:

```bash
# Linux (x86_64)
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o inthebeginning-go-linux-amd64 ./cmd/simulator/

# Linux (ARM64)
GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o inthebeginning-go-linux-arm64 ./cmd/simulator/

# macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -ldflags="-s -w" -o inthebeginning-go-darwin-amd64 ./cmd/simulator/

# macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -o inthebeginning-go-darwin-arm64 ./cmd/simulator/

# Windows (x86_64)
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o inthebeginning-go-windows-amd64.exe ./cmd/simulator/
```

### Supported Targets

| GOOS    | GOARCH | Description           |
|---------|--------|-----------------------|
| linux   | amd64  | Linux x86_64          |
| linux   | arm64  | Linux ARM64           |
| darwin  | amd64  | macOS Intel           |
| darwin  | arm64  | macOS Apple Silicon   |
| windows | amd64  | Windows x86_64        |

---

## Rust

**Build (release mode):**

```bash
cd apps/rust && cargo build --release
```

**Binary location:**

```
apps/rust/target/release/inthebeginning-rust
```

**Run:**

```bash
cd apps/rust && ./target/release/inthebeginning-rust
```

### Cross-Compilation

Rust cross-compilation requires adding the appropriate target via `rustup` and,
for some targets, a cross-linker.

```bash
# Add a target
rustup target add aarch64-unknown-linux-gnu

# Build for that target
cargo build --release --target aarch64-unknown-linux-gnu
```

The release workflow builds for the following targets:

| Target                        | Platform               | Notes                    |
|-------------------------------|------------------------|--------------------------|
| x86_64-unknown-linux-gnu      | Linux x86_64 (glibc)   |                          |
| x86_64-unknown-linux-musl     | Linux x86_64 (musl)    | Requires `musl-tools`    |
| aarch64-unknown-linux-gnu     | Linux ARM64            | Requires cross-linker    |
| x86_64-apple-darwin           | macOS Intel            | Build on macOS           |
| aarch64-apple-darwin          | macOS Apple Silicon    | Build on macOS           |
| x86_64-pc-windows-msvc        | Windows x86_64         | Build on Windows         |

---

## C

**Standard build:**

```bash
cd apps/c && make
```

**Static build:**

```bash
cd apps/c && make static
```

**Binary location:**

```
apps/c/build/simulator         # standard build
apps/c/build/simulator-static  # static build
```

**Run:**

```bash
cd apps/c && ./build/simulator
```

**Clean:**

```bash
cd apps/c && make clean
```

---

## C++

Requires CMake 3.16+ and a C++20-capable compiler.

**Build:**

```bash
cd apps/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

**Binary location:**

```
apps/cpp/build/inthebeginning
```

**Run:**

```bash
cd apps/cpp/build && ./inthebeginning
```

---

## Java

Requires JDK 21 or later.

**Build:**

```bash
cd apps/java
mkdir -p build/classes
javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java
jar cfe build/inthebeginning.jar com.inthebeginning.simulator.SimulatorApp -C build/classes .
```

**Run:**

```bash
java -jar apps/java/build/inthebeginning.jar
```

---

## TypeScript

**Install dependencies and build:**

```bash
cd apps/typescript
npm install
npm run build
```

**Run the CLI:**

```bash
node dist/index.js
```

**Build for browser:**

```bash
npm run build:browser
```

**Development (watch mode):**

```bash
npm run dev            # CLI watch
npm run dev:browser    # Browser watch
```

---

## PHP

PHP ships with a built-in web server. No compilation or dependency installation
is required.

**Start the server:**

```bash
php -S localhost:8080 apps/php/server.php
```

Then open `http://localhost:8080` in a browser.

---

## WebAssembly (WASM)

Requires the Rust toolchain and wasm-pack.

**Install wasm-pack:**

```bash
curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
```

**Build:**

```bash
cd apps/wasm && wasm-pack build --target web
```

The output is placed in `apps/wasm/pkg/` and can be loaded from the included
`index.html` or any web application.

---

## Swift (iOS / iPadOS / tvOS)

Requires macOS with Xcode 15 or later.

**Build for iOS Simulator:**

```bash
cd apps/swift
xcodebuild build \
  -scheme InTheBeginning \
  -destination 'platform=iOS Simulator,name=iPhone 15'
```

The project can also be opened directly in Xcode:

```bash
open apps/swift/InTheBeginning.xcodeproj
```

---

## Kotlin (Android)

Requires Android Studio or the Android SDK with Gradle.

**Build a debug APK:**

```bash
cd apps/kotlin && ./gradlew assembleDebug
```

The APK is placed in `apps/kotlin/app/build/outputs/apk/debug/`.

To build in Android Studio, open the `apps/kotlin` directory as a project.

---

## macOS Screensaver

Requires macOS with Xcode.

**Build:**

```bash
cd apps/screensaver-macos
xcodebuild build -scheme InTheBeginning
```

The build produces an `InTheBeginning.saver` bundle that can be installed by
double-clicking it or copying it to `~/Library/Screen Savers/`.

---

## Ubuntu Screensaver

Requires X11 and OpenGL development libraries.

**Install dependencies (Debian/Ubuntu):**

```bash
sudo apt-get install libx11-dev libgl1-mesa-dev libglu1-mesa-dev
```

**Build:**

```bash
cd apps/screensaver-ubuntu && make
```

**Install (to xscreensaver):**

```bash
cd apps/screensaver-ubuntu && sudo make install
```

**Uninstall:**

```bash
cd apps/screensaver-ubuntu && sudo make uninstall
```

---

## Audio Composition Engine

The audio engine is pure Python (stdlib only) with no required external dependencies.

**Run the generator:**

```bash
cd apps/audio && python generate.py
```

**Run tests:**

```bash
python -m pytest apps/audio/ -v
```

**Optional dependencies for enhanced output:**

| Dependency | Purpose | Install |
|------------|---------|---------|
| FluidSynth | MIDI rendering with SoundFont samples | `apt install fluidsynth` or `brew install fluid-synth` |
| mido | MIDI file parsing for classical library sampling | `pip install mido` |
| ffmpeg | MP3 encoding from WAV output | `apt install ffmpeg` or `brew install ffmpeg` |

These are optional -- the engine generates WAV output using only the Python standard
library (`math`, `random`, `struct`). FluidSynth, mido, and ffmpeg extend output
capabilities but are not required.

---

## CI/CD

Continuous integration is handled by GitHub Actions with two workflows.

### CI Workflow (`.github/workflows/ci.yml`)

Runs on:
- Push to `main` branch
- Push to `claude/*` branches
- Pull requests targeting `main`

The CI pipeline builds and tests every language implementation:

| Job              | What it does                          |
|------------------|---------------------------------------|
| python-tests     | Runs the full pytest suite            |
| go-build         | Builds CLI + SSE server, runs vet     |
| rust-build       | Builds release binary                 |
| c-build          | Builds with make                      |
| cpp-build        | Builds with CMake                     |
| java-build       | Compiles and packages JAR             |
| nodejs-test      | Runs built-in test runner + CLI       |
| typescript-build | Builds CLI and browser bundles        |
| perl-test        | Runs prove test harness               |

### Release Workflow (`.github/workflows/release.yml`)

Triggered by pushing a tag matching `v*` (e.g., `v1.0.0`).

Matrix builds produce platform-specific binaries:

- **Go**: 5 platform targets (linux/amd64, linux/arm64, darwin/amd64, darwin/arm64, windows/amd64) -- builds both CLI and SSE server for each
- **Rust**: 6 targets (linux-amd64, linux-amd64-musl, linux-arm64, darwin-amd64, darwin-arm64, windows-amd64)
- **C**: Static binary for linux-amd64
- **C++**: Release binary for linux-amd64
- **Java**: Portable JAR
- **Node.js**: Packaged tarball
- **TypeScript**: Packaged tarball with CLI and browser builds

All artifacts are collected and published as a GitHub Release with auto-generated
release notes.

---

## Release

To create a new release:

1. Ensure all CI checks pass on `main`.
2. Tag the commit:

   ```bash
   git tag v1.0.0
   git push --tags
   ```

3. The release workflow will automatically:
   - Build binaries for all platforms and languages
   - Create a GitHub Release with the tag name
   - Attach all compiled artifacts to the release
   - Generate release notes from commit history

Tag names must follow semantic versioning prefixed with `v` (e.g., `v1.0.0`,
`v1.2.3-beta.1`).
