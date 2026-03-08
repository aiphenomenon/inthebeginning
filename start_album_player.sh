#!/usr/bin/env bash
# Start the album player with 64x64 grid visualizer
# Usage: ./start_album_player.sh [port]
#
# Launches the Go SSE server and serves the visualizer from apps/visualizer/.
# The visualizer connects to the SSE note events stream for real-time
# audio-reactive visualization on a 64x64 grid.

set -euo pipefail

PORT="${1:-8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GO_SERVER_DIR="${SCRIPT_DIR}/apps/go"
AUDIO_OUTPUT_DIR="${SCRIPT_DIR}/apps/audio/output"
VISUALIZER_DIR="${SCRIPT_DIR}/apps/visualizer"

# Colors for terminal output.
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║    ${CYAN}IN THE BEGINNING${NC}${BOLD} — Album Player + Visualizer  ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Go is available.
if ! command -v go &>/dev/null; then
    echo -e "${RED}Error: Go toolchain not found. Please install Go 1.21+.${NC}"
    exit 1
fi

# Build the server if needed.
echo -e "${YELLOW}Building Go SSE server...${NC}"
cd "${GO_SERVER_DIR}"
go build -o "${GO_SERVER_DIR}/server" ./cmd/server/
echo -e "${GREEN}Build complete.${NC}"
echo ""

# List available album tracks (MP3 files).
echo -e "${BOLD}Album Track Listing:${NC}"
echo -e "${BOLD}────────────────────${NC}"
TRACK_NUM=0
if [ -d "${AUDIO_OUTPUT_DIR}" ]; then
    while IFS= read -r mp3file; do
        if [ -n "${mp3file}" ]; then
            TRACK_NUM=$((TRACK_NUM + 1))
            basename="${mp3file##*/}"
            # Get file size in human-readable format.
            if command -v du &>/dev/null; then
                size=$(du -h "${mp3file}" 2>/dev/null | cut -f1)
            else
                size="?"
            fi
            echo -e "  ${CYAN}${TRACK_NUM}.${NC} ${basename} (${size})"
        fi
    done < <(find "${AUDIO_OUTPUT_DIR}" -name '*.mp3' -type f 2>/dev/null | sort)
fi

if [ "${TRACK_NUM}" -eq 0 ]; then
    echo -e "  ${YELLOW}No tracks found.${NC}"
    echo -e "  Generate audio first: python apps/audio/radio_engine.py"
fi
echo ""

# Check for visualizer directory.
if [ -d "${VISUALIZER_DIR}" ]; then
    echo -e "${GREEN}Visualizer found at ${VISUALIZER_DIR}${NC}"
else
    echo -e "${YELLOW}Visualizer directory not found at ${VISUALIZER_DIR}.${NC}"
    echo -e "  The server will still work — visual player at http://localhost:${PORT}/"
fi
echo ""

# Check for note event JSON files.
NOTES_COUNT=0
if [ -d "${AUDIO_OUTPUT_DIR}" ]; then
    NOTES_COUNT=$(find "${AUDIO_OUTPUT_DIR}" -name '*notes*.json' 2>/dev/null | wc -l)
fi
if [ "${NOTES_COUNT}" -gt 0 ]; then
    echo -e "${GREEN}Found ${NOTES_COUNT} note event file(s) for visualization.${NC}"
else
    echo -e "${YELLOW}No note event JSON files found.${NC}"
    echo -e "  Note events stream from /events/notes will need a notes JSON file."
fi
echo ""

# Print URLs.
echo -e "${BOLD}Server URLs:${NC}"
echo -e "  ${CYAN}Visual Player:${NC}    http://localhost:${PORT}/"
echo -e "  ${CYAN}SSE Events:${NC}       http://localhost:${PORT}/events"
echo -e "  ${CYAN}Note Events:${NC}      http://localhost:${PORT}/events/notes"
echo -e "  ${CYAN}Audio Stream:${NC}     http://localhost:${PORT}/stream/audio"
echo -e "  ${CYAN}JSON Snapshot:${NC}    http://localhost:${PORT}/api/snapshot"
echo ""
echo -e "${BOLD}Visualizer:${NC}"
if [ -d "${VISUALIZER_DIR}" ]; then
    echo -e "  ${CYAN}Open:${NC} ${VISUALIZER_DIR}/index.html"
    echo -e "  (Connect to SSE at http://localhost:${PORT}/events/notes)"
fi
echo ""
echo -e "${BOLD}Playback options:${NC}"
echo -e "  ${CYAN}Speed 2x:${NC}  http://localhost:${PORT}/events/notes?speed=2.0"
echo -e "  ${CYAN}Speed 0.5x:${NC} http://localhost:${PORT}/events/notes?speed=0.5"
echo -e "  ${CYAN}Custom file:${NC} http://localhost:${PORT}/events/notes?file=path/to/notes.json"
echo ""

# Try to open in default browser (non-blocking, best-effort).
open_browser() {
    local url="$1"
    if command -v xdg-open &>/dev/null; then
        xdg-open "${url}" 2>/dev/null &
    elif command -v open &>/dev/null; then
        open "${url}" 2>/dev/null &
    elif command -v start &>/dev/null; then
        start "${url}" 2>/dev/null &
    fi
}

# Open the visualizer or main player.
if [ -d "${VISUALIZER_DIR}" ] && [ -f "${VISUALIZER_DIR}/index.html" ]; then
    open_browser "http://localhost:${PORT}/"
else
    open_browser "http://localhost:${PORT}/"
fi

echo -e "${GREEN}Starting server on port ${PORT}...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop.${NC}"
echo ""

# Start the server with audio directory configured.
exec "${GO_SERVER_DIR}/server" -port "${PORT}" -audio-dir "${AUDIO_OUTPUT_DIR}"
