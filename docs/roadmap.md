# Feature Roadmap — In The Beginning

This document describes planned future features and enhancements for the
"In The Beginning" cosmic physics simulator project.

## Current State (v0.4.0)

- 15 language implementations of the cosmic physics simulator
- AST-passing architecture for AI-assisted development
- Comprehensive test suites across all languages
- CI/CD with cross-platform releases
- Session logging and steering infrastructure

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

## Medium-Term Roadmap

### Cross-Language Physics Consistency Automation

- Automated CI step to verify that physics constants, epoch boundaries, and
  particle types match across all 15 implementations
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

## Long-Term Vision

### Multi-Simulation Modes

- Real-time visualization server (extending the existing Go SSE server)
- Distributed simulation across multiple nodes
- Educational mode with step-by-step explanations of each cosmic epoch

### Community

- Contributor guidelines
- Plugin architecture for custom physics modules
- Localization for educational deployment
