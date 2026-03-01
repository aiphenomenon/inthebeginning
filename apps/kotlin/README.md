# In The Beginning -- Kotlin Android App

A cosmic evolution simulator for Android, built with Jetpack Compose,
Material You (Material 3), and OpenGL ES rendering. Simulates the universe
from the Big Bang through the emergence of life.

## Prerequisites

- Android Studio (Hedgehog or later recommended)
- Android SDK with API level 34 (compileSdk 34)
- JDK 17
- Gradle (uses project-level build scripts, no wrapper included)

## Project Structure

```
kotlin/
  app/
    src/main/
      AndroidManifest.xml
      java/com/inthebeginning/
        MainActivity.kt              # Activity entry point
        simulator/
          Constants.kt               # Physical constants and epochs
          QuantumField.kt            # Quantum field simulation
          AtomicSystem.kt            # Atomic nucleosynthesis
          ChemicalSystem.kt          # Chemical bonding
          Biosphere.kt               # Biological emergence
          Environment.kt             # Environmental conditions
          Universe.kt                # Simulation orchestrator
        renderer/
          SimulationRenderer.kt      # OpenGL ES rendering
        ui/
          SimulationScreen.kt        # Main simulation Compose screen
          SettingsScreen.kt          # Settings Compose screen
          theme/
            Color.kt                 # Color definitions
            Theme.kt                 # Material 3 theme
      res/
        values/
          strings.xml
          themes.xml
    build.gradle.kts                 # App-level build config
  build.gradle.kts                   # Project-level build config
  settings.gradle.kts
  gradle.properties
```

## Build

Debug APK:

```sh
./gradlew assembleDebug
```

Release APK (requires signing configuration):

```sh
./gradlew assembleRelease
```

The debug APK is produced at `app/build/outputs/apk/debug/app-debug.apk`.

## Run

Install and launch on a connected device or emulator:

```sh
./gradlew installDebug
```

Or open the project in Android Studio and run from the IDE.

## Key Dependencies

- Jetpack Compose (BOM 2024.02.00) -- declarative UI
- Material 3 -- Material You design system
- AndroidX Lifecycle -- state management
- Kotlin Coroutines -- asynchronous simulation
- OpenGL ES -- GPU particle rendering (Android framework, no extra library)

## Configuration

- `minSdk`: 26 (Android 8.0)
- `targetSdk`: 34 (Android 14)
- `compileSdk`: 34
- Kotlin JVM target: 17
- Compose compiler extension: 1.5.8

## Notes

- The debug build appends `.debug` to the application ID.
- Release builds enable R8 minification and resource shrinking.
- The renderer uses Android's built-in OpenGL ES classes (`android.opengl.*`).
- The project name is `InTheBeginning` (see `settings.gradle.kts`).
