# In The Beginning -- macOS Screensaver

A macOS screensaver bundle (`.saver`) that displays the cosmic evolution
simulation. Built with Swift using the ScreenSaver framework.

## Prerequisites

- macOS with Xcode Command Line Tools installed
- `swiftc` (included with Xcode or Command Line Tools)
- Target: macOS 12.0 or later

## Project Structure

```
screensaver-macos/
  InTheBeginning/
    InTheBeginningView.swift       # ScreenSaverView subclass (entry point)
    Info.plist                     # Bundle metadata
    Simulator/
      Constants.swift              # Physical constants and epoch definitions
      QuantumField.swift           # Quantum field simulation
      AtomicSystem.swift           # Atomic nucleosynthesis
      ChemicalSystem.swift         # Chemical bonding
      Biosphere.swift              # Biological emergence
      Environment.swift            # Environmental conditions
      Universe.swift               # Simulation orchestrator
    Renderer/
      MetalRenderer.swift          # Metal GPU rendering
      Shaders.metal                # Metal shaders
  InTheBeginning.xcodeproj/        # Xcode project (alternative build)
  Makefile
```

## Build

Using Make (no Xcode project required):

```sh
make
```

Using Xcode:

```sh
xcodebuild -project InTheBeginning.xcodeproj -scheme InTheBeginning build
```

The build produces an `InTheBeginning.saver` bundle in the project directory.

## Install

```sh
make install
```

This copies `InTheBeginning.saver` to `~/Library/Screen Savers/`.

Alternatively, double-click the `.saver` file in Finder to install it, then
select "In The Beginning" in System Settings > Screen Saver.

## Uninstall

Remove the screensaver bundle:

```sh
rm -rf ~/Library/Screen\ Savers/InTheBeginning.saver
```

## Clean

```sh
make clean
```

## Syntax Check

Compile-only check without linking:

```sh
make test
```

## Notes

- The Makefile builds with `swiftc` directly, linking against the ScreenSaver
  and AppKit frameworks.
- The target architecture is `x86_64-apple-macos12.0` by default. Modify the
  `-target` flag in the Makefile for arm64.
- The `.saver` bundle is a standard macOS bundle with `Contents/MacOS/` and
  `Contents/Info.plist`.
