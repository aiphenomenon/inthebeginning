# In The Beginning -- TypeScript CLI + Audio

A cosmic evolution simulator written in TypeScript, with both a terminal CLI
and a browser-based audio sonification app. Simulates the universe from the
Big Bang through the emergence of life, with sound synthesis driven by
simulation state.

## Prerequisites

- Node.js 20 or later
- npm (for dependency installation and build scripts)

## Project Structure

```
typescript/
  src/
    index.ts               # CLI entry point
    constants.ts           # Physical constants and epoch definitions
    simulator.ts           # Core simulation engine
    audio_engine.ts        # Web Audio API sound synthesis
    instruments.ts         # Instrument definitions for sonification
    browser_main.ts        # Browser app entry point
  dist/                    # Compiled CLI output (ES modules)
  dist-browser/            # Compiled browser output
  public/
    index.html             # Browser UI
    style.css              # Browser styles
  tsconfig.json            # CLI TypeScript config
  tsconfig.browser.json    # Browser TypeScript config
  package.json
```

## Install Dependencies

```sh
npm install
```

## Build

Build the CLI:

```sh
npm run build
```

Build the browser audio app:

```sh
npm run build:browser
```

Build both:

```sh
npm run build:all
```

## Run

### CLI

```sh
node dist/index.js
```

Or using npm:

```sh
npm start
```

### Browser Audio App

1. Build the browser target: `npm run build:browser`
2. Open `public/index.html` in a browser.

The browser app uses the Web Audio API to sonify simulation state, mapping
physical parameters (temperature, particle counts, chemical complexity) to
audio synthesis parameters.

## Development

Watch mode for CLI:

```sh
npm run dev
```

Watch mode for browser:

```sh
npm run dev:browser
```

## Dependencies

- `typescript` ^5.4 (dev)
- `@types/node` ^20.0.0 (dev)

## Notes

- ES modules throughout (`"type": "module"`).
- The CLI has no runtime dependencies beyond Node.js.
- The browser build targets ES modules for direct `<script type="module">` use.
- TypeScript strict mode is enabled.
