# In The Beginning -- Java Simulator

A cosmic evolution simulator written in Java. Simulates the universe from the
Big Bang through the emergence of life. Pure JDK, no external dependencies.

## Prerequisites

- Java 21 (Temurin / Eclipse Adoptium recommended)
- Optional: Gradle (wrapper not included; use system Gradle or manual javac)

## Project Structure

```
java/
  src/main/java/com/inthebeginning/simulator/
    SimulatorApp.java      # Entry point
    Constants.java         # Physical constants and epoch definitions
    QuantumField.java      # Quantum field simulation
    Particle.java          # Particle representation
    ParticleType.java      # Particle type enum
    Atom.java              # Atom model with electron shells
    AtomicSystem.java      # Atomic nucleosynthesis
    Molecule.java          # Molecule representation
    ChemicalSystem.java    # Chemical bonding
    BiologicalSystem.java  # Biological emergence
    Environment.java       # Environmental conditions
    Universe.java          # Top-level simulation orchestrator
  build.gradle             # Gradle build configuration
  build/
    inthebeginning.jar     # Executable JAR
```

## Build (javac)

```sh
mkdir -p build/classes
javac -d build/classes src/main/java/com/inthebeginning/simulator/*.java
jar cfe build/inthebeginning.jar com.inthebeginning.simulator.SimulatorApp -C build/classes .
```

## Build (Gradle)

```sh
gradle build
gradle fatJar    # Produces build/libs/java-all.jar
```

## Run

From JAR:

```sh
java -jar build/inthebeginning.jar
```

From compiled classes:

```sh
java -cp build/classes com.inthebeginning.simulator.SimulatorApp
```

With Gradle:

```sh
gradle run
```

## Notes

- No external dependencies; uses only the Java standard library.
- The Gradle build configures `-Xmx512m` for the `run` task.
- The main class is `com.inthebeginning.simulator.SimulatorApp`.
- Java 21 features (records, pattern matching) may be used in the source.
