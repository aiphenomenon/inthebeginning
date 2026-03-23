# Feature Roadmap — In The Beginning

This document describes planned future features and enhancements for the
"In The Beginning" cosmic physics simulator project.

## Current State (V21)

- 16 applications across 12 programming languages (including Audio Radio Engine)
- AST-passing architecture for AI-assisted development
- Comprehensive test suites across all languages (~490 Python tests, plus per-language tests)
- CI/CD with cross-platform releases
- Session logging and steering infrastructure
- Audio Radio Engine v7-v20 with 537+ instruments, 1,771 MIDI files from 120+ composers
- Audio composition engine with bar-oriented multi-track architecture
- Golden output tests, cross-language parity tests, screen capture tests
- Integration tests for Go SSE and PHP snapshot servers

## Near-Term Roadmap

### Containerization (Docker/Colima)

- Docker Engine-based build and execution for non-graphical applications
- On macOS Apple Silicon: use Colima (without Homebrew requirement) as the
  container runtime
- Avoid Docker Desktop entirely
- Containers for: Go, Rust, C, C++, Java, Node.js, Perl, PHP, TypeScript, Python
- Bare-metal remains required for graphical apps:
  - Swift iOS (SwiftUI + Metal)
  - Kotlin Android (Compose)
  - macOS Screensaver (Metal)
  - Ubuntu Screensaver (X11 + OpenGL)
  - WASM (WebGPU)
- Justification: graphics engines require OS-level access that VMs/containers
  cannot provide performantly

### Deployment Target Matrix

The full set of deployment targets:

| Target | Architecture | Notes |
|--------|-------------|-------|
| VMs on macOS Apple Silicon | ARM64 Ubuntu/Debian via Parallels | Primary dev environment |
| Apple Silicon macOS hosts | ARM64 bare metal | Required for graphical apps |
| Bare metal Linux | AMD64 | Production servers |
| AMD64 containers on bare metal AMD64 | AMD64 | Standard container deployment |
| AMD64 (Intel) with Nvidia GPU | AMD64 + CUDA | GPU-accelerated simulation |
| Raspberry Pi (various models) | ARM32/ARM64 | Limited virtualization/container capability; Docker Compose tested |

Note: Raspberry Pi may not realistically handle heavy virtualization, but
lightweight Docker Compose works for the non-graphical simulator applications.

### Enhanced Metacognitive Steering

- Additional metacognitive principles for agent coordination (forthcoming)
- Advanced AST-passing optimizations for larger context utilization
- Potential investigation of "Ralph Wiggum" patterns (selected pieces, not full
  adoption)
- Goal: maximize agent working memory utilization for bigger tasks with
  rock-solid correctness

### Audio Engine: Multicore Rendering (TODO)

The radio engine's streaming renderer is single-threaded pure Python. On a 16-core
machine, each 30-minute render uses 1 core and takes ~16 minutes. Potential speedup:

- **Parallel segment rendering**: Each mood segment (15-18 per composition) is
  largely independent. Render segments in parallel using `multiprocessing.Pool`
  with 12-14 workers, then stitch WAV chunks with crossfade at boundaries.
- **Estimated speedup**: 8-12x on 16 cores (16 min -> ~2 min per render)
- **Complexity**: Moderate (~100-150 lines). Main challenge is crossfade/morph
  regions at segment boundaries, which need samples from adjacent segments.
- **Approach**: Render each segment to a temp WAV with extra overlap (morph
  duration), then stitch with crossfade in a final serial pass.
- **Risk**: Python GIL prevents threading gains; must use multiprocessing.
  Shared state (instrument pool, MIDI library) would need to be serialized
  or shared via `multiprocessing.Manager`.

## Medium-Term Roadmap

### Cross-Language Physics Consistency Automation

- Automated CI step to verify that physics constants, epoch boundaries, and
  particle types match across all 16 implementations
- AST-based comparison tool that extracts constants and enum values from each
  language implementation and diffs them against the Python reference

### Performance Benchmarking

- Cross-language performance comparison framework
- Simulation output regression testing to ensure all implementations produce
  identical results for a given seed
- GPU acceleration benchmarks (Metal, OpenGL, WebGPU)

### Expanded Platform Support

- ARM64 Linux containers
- Windows ARM64
- FreeBSD builds for C/Rust
- Raspberry Pi optimized builds

### Web Audio: Coloring/Imprinting/Bending Library (Future)

The Python radio_engine implements a library of ~538 sound coloring, imprinting,
and bending effects that transform instrument tones into unique textures. These
include:

- **Coloring**: Harmonic overtone shaping, formant shifting, spectral tilt
- **Imprinting**: Transient injection, resonance seeding, envelope sculpting
- **Bending**: Pitch micro-modulation, glissando, portamento curves

The Python implementation includes clamping mechanisms to keep effects within
comfortable human hearing ranges (avoiding harsh frequencies, extreme amplitudes,
or disorienting pitch shifts).

**Current web state**: The Visualizer and Cosmic Runner apps have 16 mutation
presets (pitchShift, tempoMult, reverb, filter) which provide a subset of this
capability. The full ~538 effect library is a future enhancement.

**Implementation considerations for web**:
- Web Audio API's AudioParam scheduling can reproduce most effects
- Clamping is critical — the Python clamping logic must be ported faithfully
- Effects should be applied post-instrument (after sample or additive synthesis)
- Performance: each effect adds AudioNode overhead; budget for ~4-6 simultaneous
  effects per voice maximum in real-time browser playback
- Consider Web Audio Worklet for custom DSP effects that aren't achievable
  with built-in nodes

**Prerequisites**:
- Sample-based instrument playback (DONE — SampleBank in synth-engine.js)
- GM program-to-instrument mapping (DONE — GM_PROGRAM_TO_SAMPLE)
- Regular Claude Code CLI access for comprehensive SoundFont curation

## Long-Term Vision

### Multi-Simulation Modes

- Real-time visualization server (extending the existing Go SSE server)
- Distributed simulation across multiple nodes
- Educational mode with step-by-step explanations of each cosmic epoch

### Community

- Contributor guidelines
- Plugin architecture for custom physics modules
- Localization for educational deployment
