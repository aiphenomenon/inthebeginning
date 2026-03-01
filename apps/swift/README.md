# In The Beginning -- Swift iOS/iPadOS/tvOS App

A cosmic evolution simulator built with SwiftUI, Metal rendering, and
AVAudioEngine audio synthesis. Simulates the universe from the Big Bang
through the emergence of life with real-time 3D visualization and sound.

## Prerequisites

- Xcode 15 or later
- macOS 14 (Sonoma) or later for development
- Deployment targets: iOS 17 / macOS 14 / tvOS 17
- Swift 5.9+

## Project Structure

```
swift/
  InTheBeginning/
    App.swift              # App entry point (@main)
    Simulator/
      Constants.swift      # Physical constants and epoch definitions
      QuantumField.swift   # Quantum field simulation
      AtomicSystem.swift   # Atomic nucleosynthesis
      ChemicalSystem.swift # Chemical bonding
      Biosphere.swift      # Biological emergence
      Environment.swift    # Environmental conditions
      Universe.swift       # Top-level simulation orchestrator
    Renderer/
      MetalRenderer.swift  # Metal GPU rendering pipeline
      Shaders.metal        # Metal shading language shaders
    Audio/
      AudioEngine.swift    # AVAudioEngine-based sound synthesis
    Views/
      SimulationView.swift     # Main simulation display
      EpochTimelineView.swift  # Epoch progression timeline
      SettingsView.swift       # Configuration UI
  Info.plist
  Package.swift            # Swift Package Manager manifest
```

## Build

### Xcode

Open the project in Xcode, select a target device or simulator, and build
with Cmd+B.

### Command Line

```sh
xcodebuild -scheme InTheBeginning -destination 'platform=iOS Simulator,name=iPhone 15 Pro' build
```

For macOS:

```sh
xcodebuild -scheme InTheBeginning -destination 'platform=macOS' build
```

### Swift Package Manager (simulator library only)

```sh
swift build
```

This builds the `InTheBeginningSimulator` library target. The full app with
Metal and Audio requires Xcode.

## Architecture

- **Simulator layer**: Pure Swift, no UI dependencies. Available as a
  standalone SPM library (`InTheBeginningSimulator`).
- **Renderer**: Metal-based GPU rendering with custom WGSL-style shaders.
- **Audio**: AVAudioEngine for real-time sound synthesis driven by simulation
  parameters.
- **UI**: SwiftUI views for simulation display, epoch timeline, and settings.

## Notes

- The `Package.swift` defines two targets: the simulator library and the
  full app executable.
- Metal shaders are processed as package resources.
- The simulator library can be imported independently into other Swift projects.
