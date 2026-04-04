#!/usr/bin/env bash
# tools/audio-sink.sh — PulseAudio virtual audio sink for E2E testing.
#
# Creates a virtual audio sink whose monitor source captures all audio
# output from the browser. This is NOT a true null sink — the monitor
# provides real PCM data for spectral analysis and silence detection.
#
# Usage:
#   bash tools/audio-sink.sh --start   # Start PulseAudio + virtual sink
#   bash tools/audio-sink.sh --stop    # Tear down sink + kill daemon
#   bash tools/audio-sink.sh --status  # Check if sink is running
#   bash tools/audio-sink.sh --capture <seconds> <outfile>  # Capture PCM
#
# After --start, browsers will route audio to the virtual sink.
# Capture with: parec --device=test_sink.monitor --format=float32le \
#               --rate=44100 --channels=1

set -euo pipefail

SINK_NAME="test_sink"
SINK_DESC="InTheBeginning Test Sink"

start_sink() {
    # Kill any existing PulseAudio first for clean state
    pulseaudio --kill 2>/dev/null || true
    sleep 0.5

    # Start PulseAudio with the null-sink loaded inline.
    # Loading via --load avoids the "Module initialization failed" error
    # that occurs when loading module-null-sink via pactl on systems
    # without D-Bus (containers, CI environments).
    echo "[audio-sink] Starting PulseAudio daemon with virtual sink..."
    pulseaudio --start --exit-idle-time=-1 \
        --load="module-null-sink sink_name=$SINK_NAME rate=44100 channels=2 format=s16le" \
        2>/dev/null || true
    sleep 1

    # Set as default sink so browsers use it
    pactl set-default-sink "$SINK_NAME" 2>/dev/null || true

    # Verify monitor source exists
    if pactl list sources short 2>/dev/null | grep -q "${SINK_NAME}.monitor"; then
        echo "[audio-sink] Monitor source '${SINK_NAME}.monitor' ready."
        echo "[audio-sink] Capture with: parec --device=${SINK_NAME}.monitor --format=float32le --rate=44100 --channels=1"
    else
        echo "[audio-sink] ERROR: Monitor source not found!" >&2
        exit 1
    fi

    echo "[audio-sink] Virtual audio sink started successfully."
}

stop_sink() {
    echo "[audio-sink] Stopping virtual audio sink..."

    # Unload our sink module
    if pactl list sinks short 2>/dev/null | grep -q "$SINK_NAME"; then
        MODULE_ID=$(pactl list modules short 2>/dev/null | grep "module-null-sink.*$SINK_NAME" | awk '{print $1}')
        if [ -n "$MODULE_ID" ]; then
            pactl unload-module "$MODULE_ID" 2>/dev/null || true
        fi
    fi

    # Kill PulseAudio daemon
    pulseaudio --kill 2>/dev/null || true
    echo "[audio-sink] Stopped."
}

status_sink() {
    if pulseaudio --check 2>/dev/null; then
        echo "[audio-sink] PulseAudio is running."
        if pactl list sinks short 2>/dev/null | grep -q "$SINK_NAME"; then
            echo "[audio-sink] Virtual sink '$SINK_NAME' is loaded."
            echo "[audio-sink] Monitor source: ${SINK_NAME}.monitor"
            pactl list sinks short 2>/dev/null | grep "$SINK_NAME"
        else
            echo "[audio-sink] Virtual sink NOT loaded."
        fi
    else
        echo "[audio-sink] PulseAudio is NOT running."
    fi
}

capture_audio() {
    local duration="${1:-3}"
    local outfile="${2:-/tmp/audio_capture.wav}"

    echo "[audio-sink] Capturing ${duration}s of audio to ${outfile}..."
    # Use parecord with WAV output for reliable capture.
    # Start recording, wait for duration + 0.5s buffer, then kill.
    parecord --device="${SINK_NAME}.monitor" \
        --file-format=wav \
        "$outfile" &
    local rec_pid=$!
    sleep "$duration"
    kill "$rec_pid" 2>/dev/null || true
    wait "$rec_pid" 2>/dev/null || true

    if [ -f "$outfile" ]; then
        local size
        size=$(stat -c%s "$outfile" 2>/dev/null || echo 0)
        echo "[audio-sink] Captured WAV file (${size} bytes)."
    else
        echo "[audio-sink] ERROR: No capture file created." >&2
    fi
}

case "${1:-}" in
    --start)   start_sink ;;
    --stop)    stop_sink ;;
    --status)  status_sink ;;
    --capture) capture_audio "${2:-3}" "${3:-/tmp/audio_capture.pcm}" ;;
    *)
        echo "Usage: $0 {--start|--stop|--status|--capture <seconds> <outfile>}"
        exit 1
        ;;
esac
