#!/bin/bash
# Build the "In The Beginning" WASM app using wasm-pack.
# Output goes to ./pkg/ which index.html loads via ES module import.
set -euo pipefail

cd "$(dirname "$0")"

echo "Building inthebeginning-wasm ..."
wasm-pack build --target web --out-dir pkg

echo ""
echo "Build complete.  Serve this directory with any static HTTP server, e.g.:"
echo "  python3 -m http.server 8080"
echo "Then open http://localhost:8080/ in a WebGPU-capable browser."
