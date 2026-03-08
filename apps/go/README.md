# In The Beginning -- Go CLI + SSE Server

A cosmic evolution simulator written in Go, featuring both a terminal CLI and
an HTTP server with Server-Sent Events (SSE) streaming. Simulates the universe
from the Big Bang through the emergence of life.

## Prerequisites

- Go 1.22 or later
- No external dependencies (standard library only)

## Project Structure

```
go/
  cmd/
    simulator/
      main.go              # CLI entry point
    server/
      main.go              # HTTP SSE server entry point
      web/
        index.html         # Web UI
        app.js             # Client-side EventSource logic
        style.css          # Styles
  simulator/
    constants.go           # Physical constants and epoch definitions
    quantum.go             # Quantum field simulation
    atomic.go              # Atomic system formation
    chemistry.go           # Chemical bonding and molecules
    biology.go             # Biological emergence
    environment.go         # Environmental conditions
    universe.go            # Top-level simulation orchestrator
  web/
    index.html             # Alternate web UI assets
    app.js
    style.css
  go.mod
```

## Build

Build the CLI simulator:

```sh
go build -o simulator ./cmd/simulator/
```

Build the SSE server:

```sh
go build -o server ./cmd/server/
```

Build both:

```sh
go build ./cmd/...
```

## Cross-Compilation

```sh
GOOS=linux   GOARCH=amd64 go build -o simulator-linux-amd64   ./cmd/simulator/
GOOS=linux   GOARCH=arm64 go build -o simulator-linux-arm64   ./cmd/simulator/
GOOS=darwin  GOARCH=arm64 go build -o simulator-darwin-arm64  ./cmd/simulator/
GOOS=windows GOARCH=amd64 go build -o simulator-windows.exe   ./cmd/simulator/
```

## Run

### CLI Simulator

```sh
./simulator
```

Prints epoch-by-epoch simulation output to the terminal.

### SSE Server

```sh
./server
```

Open http://localhost:8080 in a browser. The server streams JSON snapshots
via EventSource, and the embedded web UI renders simulation state in real time.

## Testing

```sh
go test ./...
```

## Notes

- The module path is `inthebeginning/go-sse`.
- The SSE server embeds the web UI files from `cmd/server/web/`.
- Cross-compiled binaries are produced by the CI release workflow.
