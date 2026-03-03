# In The Beginning -- Perl CLI

A cosmic evolution simulator written in Perl. Simulates the universe from the
Big Bang through the emergence of life.

## Prerequisites

- Perl 5.20 or later
- No CPAN dependencies (uses only core modules: `Time::HiRes`, `Test::More`,
  `FindBin`, `POSIX`)
- `prove` (part of `Test::Harness`, included with Perl core)

## Project Structure

```
perl/
  simulate.pl              # Entry point
  lib/
    Constants.pm           # Physical constants and epoch definitions
    Quantum.pm             # Quantum field simulation
    Atomic.pm              # Atomic nucleosynthesis
    Chemistry.pm           # Chemical bonding and molecules
    Biology.pm             # Biological emergence
    Environment.pm         # Environmental conditions
    Universe.pm            # Top-level simulation orchestrator
  t/
    01_constants.t         # Constants tests
    02_quantum.t           # Quantum field tests
    03_atomic.t            # Atomic system tests
    04_chemistry.t         # Chemistry tests
    05_biology.t           # Biology tests
    06_universe.t          # Universe integration tests
    07_environment.t       # Environment tests
```

## Run

```sh
perl simulate.pl
```

## Testing

Run the full test suite (376 tests across 7 test files):

```sh
prove -v t/
```

Run a single test file:

```sh
perl t/01_constants.t
```

## Notes

- All modules are in the `lib/` directory, loaded via `FindBin` and `use lib`.
- No installation step required; run directly from the source directory.
- The simulator prints epoch-by-epoch progress with temperature, scale factor,
  and cumulative statistics.
