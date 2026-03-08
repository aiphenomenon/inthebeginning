#!/usr/bin/env bash
# Start the In The Beginning infinite radio stream
# Usage: ./start_radio.sh [port]
#
# Launches the Go SSE server with audio streaming enabled.
# The server provides:
#   - /events       SSE simulation events (visual player)
#   - /events/notes SSE note events from audio engine
#   - /stream/audio MP3 audio stream (compatible with VLC, mpv, browsers)
#   - /api/snapshot JSON snapshot of current simulation state

set -euo pipefail

PORT="${1:-8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GO_SERVER_DIR="${SCRIPT_DIR}/apps/go"
AUDIO_OUTPUT_DIR="${SCRIPT_DIR}/apps/audio/output"

# Colors for terminal output.
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     ${CYAN}IN THE BEGINNING${NC}${BOLD} — Infinite Radio Stream    ║${NC}"
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

# Check for available MP3 files.
MP3_COUNT=0
if [ -d "${AUDIO_OUTPUT_DIR}" ]; then
    MP3_COUNT=$(find "${AUDIO_OUTPUT_DIR}" -name '*.mp3' 2>/dev/null | wc -l)
fi

if [ "${MP3_COUNT}" -gt 0 ]; then
    echo -e "${GREEN}Found ${MP3_COUNT} MP3 file(s) in audio output directory.${NC}"
    echo -e "  Audio files available for streaming via /stream/audio"
else
    echo -e "${YELLOW}No MP3 files found in ${AUDIO_OUTPUT_DIR}.${NC}"
    echo -e "  Generate audio first: python apps/audio/radio_engine.py"
    echo -e "  The simulation SSE stream will still work without audio."
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
echo -e "${BOLD}Stream with external players:${NC}"
echo -e "  ${CYAN}VLC:${NC}   vlc http://localhost:${PORT}/stream/audio"
echo -e "  ${CYAN}mpv:${NC}   mpv http://localhost:${PORT}/stream/audio"
echo -e "  ${CYAN}curl:${NC}  curl -s http://localhost:${PORT}/stream/audio > output.mp3"
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

# Open the visual player in the browser.
open_browser "http://localhost:${PORT}/"

echo -e "${GREEN}Starting server on port ${PORT}...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop.${NC}"
echo ""

# Start the server with audio directory configured.
exec "${GO_SERVER_DIR}/server" -port "${PORT}" -audio-dir "${AUDIO_OUTPUT_DIR}"
