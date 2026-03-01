package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"inthebeginning/go-sse/simulator"
)

// sseEvent is a JSON event sent over the SSE stream.
type sseEvent struct {
	Type          string       `json:"type"`
	Epoch         string       `json:"epoch,omitempty"`
	EpochIndex    int          `json:"epoch_index,omitempty"`
	Tick          int          `json:"tick,omitempty"`
	Temperature   float64      `json:"temperature,omitempty"`
	Particles     int          `json:"particles,omitempty"`
	Atoms         int          `json:"atoms,omitempty"`
	Molecules     int          `json:"molecules,omitempty"`
	Cells         int          `json:"cells,omitempty"`
	TotalEpochs   int          `json:"total_epochs,omitempty"`
	ParticlePos   [][3]float64 `json:"particle_pos,omitempty"`
	ParticleTypes []string     `json:"particle_types,omitempty"`
	ElapsedMs     int64        `json:"elapsed_ms,omitempty"`
}

// broker manages SSE client connections and event broadcasting.
type broker struct {
	mu      sync.Mutex
	clients map[chan sseEvent]struct{}
}

func newBroker() *broker {
	return &broker{
		clients: make(map[chan sseEvent]struct{}),
	}
}

func (b *broker) subscribe() chan sseEvent {
	ch := make(chan sseEvent, 64)
	b.mu.Lock()
	b.clients[ch] = struct{}{}
	b.mu.Unlock()
	return ch
}

func (b *broker) unsubscribe(ch chan sseEvent) {
	b.mu.Lock()
	delete(b.clients, ch)
	b.mu.Unlock()
	close(ch)
}

func (b *broker) broadcast(ev sseEvent) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for ch := range b.clients {
		select {
		case ch <- ev:
		default:
			// drop if client is too slow
		}
	}
}

// history stores recent events so late-connecting clients can catch up.
type history struct {
	mu     sync.Mutex
	events []sseEvent
}

func newHistory() *history {
	return &history{
		events: make([]sseEvent, 0, 512),
	}
}

func (h *history) add(ev sseEvent) {
	h.mu.Lock()
	h.events = append(h.events, ev)
	h.mu.Unlock()
}

func (h *history) snapshot() []sseEvent {
	h.mu.Lock()
	defer h.mu.Unlock()
	out := make([]sseEvent, len(h.events))
	copy(out, h.events)
	return out
}

func main() {
	port := flag.Int("port", 8080, "HTTP server port")
	seed := flag.Int64("seed", 0, "Simulation seed (0 = time-based)")
	flag.Parse()

	if *seed == 0 {
		*seed = time.Now().UnixNano()
	}

	b := newBroker()
	hist := newHistory()

	// Determine path to web/ directory relative to this binary or working directory.
	webDir := findWebDir()

	log.Printf("Starting simulation with seed %d", *seed)
	log.Printf("Serving web UI from %s", webDir)
	log.Printf("Listening on http://localhost:%d", *port)

	// Run simulation in background goroutine.
	go runSimulation(*seed, b, hist)

	// SSE endpoint.
	http.HandleFunc("/api/events", func(w http.ResponseWriter, r *http.Request) {
		handleSSE(w, r, b, hist)
	})

	// Static file server for the web frontend.
	fs := http.FileServer(http.Dir(webDir))
	http.Handle("/", fs)

	addr := fmt.Sprintf(":%d", *port)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// findWebDir locates the web/ directory by checking common locations.
func findWebDir() string {
	// Try relative to working directory.
	candidates := []string{
		"web",
		"../../web",
		filepath.Join(filepath.Dir(os.Args[0]), "..", "..", "web"),
	}

	// Also try relative to the executable location.
	if exe, err := os.Executable(); err == nil {
		candidates = append(candidates, filepath.Join(filepath.Dir(exe), "..", "..", "web"))
	}

	for _, dir := range candidates {
		if info, err := os.Stat(dir); err == nil && info.IsDir() {
			abs, _ := filepath.Abs(dir)
			return abs
		}
	}

	// Fallback.
	return "web"
}

// runSimulation creates a Universe and runs it, broadcasting events via the broker.
func runSimulation(seed int64, b *broker, hist *history) {
	universe := simulator.NewUniverse(seed)
	startTime := time.Now()

	// Track current epoch for epoch_start events.
	var lastEpochIndex int = -1

	// OnTick: send a tick event for each simulation step.
	// To avoid flooding clients, we throttle to roughly every 5ms of wall-clock time
	// and always send the first tick of a new epoch.
	var lastSend time.Time
	const minInterval = 5 * time.Millisecond

	universe.OnTick = func(epochName string, epochIndex int, tick int) {
		// Send epoch_start when we enter a new epoch.
		if epochIndex != lastEpochIndex {
			lastEpochIndex = epochIndex
			ev := sseEvent{
				Type:       "epoch_start",
				Epoch:      epochName,
				EpochIndex: epochIndex,
			}
			b.broadcast(ev)
			hist.add(ev)
		}

		now := time.Now()
		if now.Sub(lastSend) < minInterval {
			return
		}
		lastSend = now

		snap := universe.TakeSnapshot(epochName, epochIndex, true)
		ev := sseEvent{
			Type:          "tick",
			Epoch:         snap.Epoch,
			EpochIndex:    snap.EpochIndex,
			Tick:          snap.Tick,
			Temperature:   snap.Temperature,
			Particles:     snap.Particles,
			Atoms:         snap.Atoms,
			Molecules:     snap.Molecules,
			Cells:         snap.Cells,
			TotalEpochs:   snap.TotalEpochs,
			ParticlePos:   snap.ParticlePos,
			ParticleTypes: snap.ParticleTypes,
		}
		b.broadcast(ev)
		hist.add(ev)
	}

	// OnEpochComplete is still used for logging.
	universe.OnEpochComplete = func(result simulator.EpochResult) {
		log.Printf("Epoch complete: %s (particles=%d atoms=%d molecules=%d cells=%d)",
			result.EpochName, result.ParticleCount, result.AtomCount,
			result.MoleculeCount, result.CellCount)
	}

	universe.Run()

	elapsed := time.Since(startTime)
	log.Printf("Simulation complete in %v", elapsed)

	ev := sseEvent{
		Type:      "complete",
		ElapsedMs: elapsed.Milliseconds(),
	}
	b.broadcast(ev)
	hist.add(ev)
}

// handleSSE handles an SSE connection: replays history, then streams live events.
func handleSSE(w http.ResponseWriter, r *http.Request, b *broker, hist *history) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Subscribe to live events.
	ch := b.subscribe()
	defer b.unsubscribe(ch)

	// Replay history so late-joining clients see past state.
	for _, ev := range hist.snapshot() {
		data, err := json.Marshal(ev)
		if err != nil {
			continue
		}
		fmt.Fprintf(w, "data: %s\n\n", data)
	}
	flusher.Flush()

	// Stream live events until client disconnects.
	ctx := r.Context()
	for {
		select {
		case <-ctx.Done():
			return
		case ev, ok := <-ch:
			if !ok {
				return
			}
			data, err := json.Marshal(ev)
			if err != nil {
				continue
			}
			fmt.Fprintf(w, "data: %s\n\n", data)
			flusher.Flush()
		}
	}
}
