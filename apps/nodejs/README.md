# In The Beginning -- Node.js CLI

A cosmic evolution simulator written in JavaScript for Node.js. Simulates the
universe from the Big Bang through the emergence of life.

## Prerequisites

- Node.js 20 or later

## Project Structure

```
nodejs/
  index.js                 # Entry point
  constants.js             # Physical constants and epoch definitions
  quantum.js               # Quantum field simulation
  atomic.js                # Atomic nucleosynthesis
  chemistry.js             # Chemical bonding and molecules
  biology.js               # Biological emergence
  environment.js           # Environmental conditions
  universe.js              # Top-level simulation orchestrator
  test/
    test_simulator.js      # Test suite (node:test runner)
  package.json
```

## Run

```sh
node index.js
```

Or using npm:

```sh
npm start
```

## Testing

Uses the built-in Node.js test runner (`node:test`):

```sh
node --test test/test_simulator.js
```

The test suite contains 44 tests covering constants, quantum fields, atomic
systems, chemistry, biology, environment, and universe orchestration.

## Notes

- ES modules (`"type": "module"` in package.json).
- No external dependencies; uses only the Node.js standard library.
- The package declares a `bin` entry (`inthebeginning`) for optional global install.
- MIT licensed.
