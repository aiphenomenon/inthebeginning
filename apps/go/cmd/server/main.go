package main

import (
	"embed"
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"sync"
	"time"

	"inthebeginning/go-sse/simulator"
)

//go:embed web/*
var webAssets embed.FS

// snapshot is a JSON event sent over the SSE stream.
type snapshot struct {
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
	Events        []string     `json:"events,omitempty"`
	ParticlePos   [][3]float64 `json:"particle_pos,omitempty"`
	ParticleTypes []string     `json:"particle_types,omitempty"`
	ElapsedMs     int64        `json:"elapsed_ms,omitempty"`
}

// broker manages SSE client connections and event broadcasting.
type broker struct {
	mu      sync.Mutex
	clients map[chan snapshot]struct{}
}

func newBroker() *broker {
	return &broker{clients: make(map[chan snapshot]struct{})}
}

func (b *broker) subscribe() chan snapshot {
	ch := make(chan snapshot, 128)
	b.mu.Lock()
	b.clients[ch] = struct{}{}
	b.mu.Unlock()
	return ch
}

func (b *broker) unsubscribe(ch chan snapshot) {
	b.mu.Lock()
	delete(b.clients, ch)
	b.mu.Unlock()
	close(ch)
}

func (b *broker) broadcast(ev snapshot) {
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

// latestStore holds the most recent snapshot for the JSON API.
type latestStore struct {
	mu   sync.RWMutex
	snap *snapshot
}

func (ls *latestStore) set(s snapshot) {
	ls.mu.Lock()
	ls.snap = &s
	ls.mu.Unlock()
}

func (ls *latestStore) get() *snapshot {
	ls.mu.RLock()
	defer ls.mu.RUnlock()
	return ls.snap
}

// noteEvent represents a single musical note event from the audio engine.
type noteEvent struct {
	T    float64 `json:"t"`
	Dur  float64 `json:"dur"`
	Note int     `json:"note"`
	Inst string  `json:"inst"`
	Vel  float64 `json:"vel"`
	Bend float64 `json:"bend"`
	Ch   int     `json:"ch"`
}

func main() {
	port := flag.Int("port", 8080, "HTTP server port")
	seed := flag.Int64("seed", 0, "Simulation seed (0 = time-based)")
	audioDir := flag.String("audio-dir", "", "Directory containing MP3 files for /stream/audio")
	flag.Parse()

	if *seed == 0 {
		*seed = time.Now().UnixNano()
	}

	b := newBroker()
	latest := &latestStore{}

	log.Printf("Starting simulation with seed %d", *seed)
	log.Printf("Listening on http://localhost:%d", *port)

	// Serve the embedded web directory at /.
	webFS, err := fs.Sub(webAssets, "web")
	if err != nil {
		log.Fatalf("Failed to access embedded web assets: %v", err)
	}

	// SSE endpoint: each viewer gets their own goroutine streaming events.
	http.HandleFunc("/events", func(w http.ResponseWriter, r *http.Request) {
		// Support optional per-viewer seed via query param.
		viewerSeed := *seed
		if qs := r.URL.Query().Get("seed"); qs != "" {
			if s, err := strconv.ParseInt(qs, 10, 64); err == nil {
				viewerSeed = s
			}
		}
		handleSSE(w, r, viewerSeed, b, latest)
	})

	// JSON snapshot API: returns the latest simulation state.
	http.HandleFunc("/api/snapshot", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		s := latest.get()
		if s == nil {
			w.WriteHeader(http.StatusServiceUnavailable)
			fmt.Fprintf(w, `{"error":"no data yet"}`)
			return
		}
		json.NewEncoder(w).Encode(s)
	})

	// SSE endpoint for streaming note events from audio engine JSON files.
	http.HandleFunc("/events/notes", func(w http.ResponseWriter, r *http.Request) {
		handleNoteSSE(w, r)
	})

	// Audio stream endpoint: serves MP3 files with Range request support.
	http.HandleFunc("/stream/audio", func(w http.ResponseWriter, r *http.Request) {
		handleAudioStream(w, r, *audioDir)
	})

	// Static file server for the embedded web frontend.
	http.Handle("/", http.FileServer(http.FS(webFS)))

	// Start a shared simulation that broadcasts to all viewers.
	go runSimulation(*seed, b, latest)

	addr := fmt.Sprintf(":%d", *port)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// runSimulation creates a Universe and runs it, broadcasting snapshots to all
// connected SSE clients via the broker.
func runSimulation(seed int64, b *broker, latest *latestStore) {
	universe := simulator.NewUniverse(seed)
	startTime := time.Now()

	var lastEpochIndex int = -1
	var lastSend time.Time
	const minInterval = 50 * time.Millisecond

	universe.OnTick = func(epochName string, epochIndex int, tick int) {
		// Send epoch_start when we enter a new epoch.
		if epochIndex != lastEpochIndex {
			lastEpochIndex = epochIndex
			ev := snapshot{
				Type:       "epoch_start",
				Epoch:      epochName,
				EpochIndex: epochIndex,
			}
			b.broadcast(ev)
		}

		now := time.Now()
		if now.Sub(lastSend) < minInterval {
			return
		}
		lastSend = now

		snap := universe.TakeSnapshot(epochName, epochIndex, true)
		ev := snapshot{
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
		latest.set(ev)

		// Small sleep to yield to HTTP handlers and pace the simulation.
		time.Sleep(minInterval)
	}

	universe.OnEpochComplete = func(result simulator.EpochResult) {
		log.Printf("Epoch complete: %s (particles=%d atoms=%d molecules=%d cells=%d)",
			result.EpochName, result.ParticleCount, result.AtomCount,
			result.MoleculeCount, result.CellCount)
	}

	// Run in perpetual Big Bounce mode: when the universe completes,
	// derive a new seed and restart. This keeps the SSE stream alive
	// indefinitely with varying content.
	cycle := 0
	currentSeed := seed
	for {
		universe.Run()
		cycle++

		elapsed := time.Since(startTime)
		log.Printf("Cycle %d complete (seed=%d) in %v — Big Bounce!", cycle, currentSeed, elapsed)

		// Broadcast bounce event (not "complete" — we're continuing)
		ev := snapshot{
			Type:      "bounce",
			ElapsedMs: elapsed.Milliseconds(),
		}
		b.broadcast(ev)

		// Derive new seed from current state
		currentSeed = currentSeed*6364136223846793005 + 1442695040888963407 // LCG
		log.Printf("New universe seed: %d", currentSeed)

		// Reset for next cycle
		universe = simulator.NewUniverse(currentSeed)
		lastEpochIndex = -1

		// Re-attach callbacks
		universe.OnTick = func(epochName string, epochIndex int, tick int) {
			if epochIndex != lastEpochIndex {
				lastEpochIndex = epochIndex
				ev := snapshot{
					Type:       "epoch_start",
					Epoch:      epochName,
					EpochIndex: epochIndex,
				}
				b.broadcast(ev)
			}

			now := time.Now()
			if now.Sub(lastSend) < minInterval {
				return
			}
			lastSend = now

			snap := universe.TakeSnapshot(epochName, epochIndex, true)
			ev := snapshot{
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
			latest.set(ev)

			time.Sleep(minInterval)
		}

		universe.OnEpochComplete = func(result simulator.EpochResult) {
			log.Printf("Epoch complete: %s (particles=%d atoms=%d molecules=%d cells=%d)",
				result.EpochName, result.ParticleCount, result.AtomCount,
				result.MoleculeCount, result.CellCount)
		}

		// Brief pause between cycles for visual breathing room
		time.Sleep(2 * time.Second)
	}
}

// handleNoteSSE streams note events from a JSON file as SSE, pacing them
// according to each note's timestamp to simulate real-time playback.
func handleNoteSSE(w http.ResponseWriter, r *http.Request) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	// Determine which notes file to stream.
	notesFile := r.URL.Query().Get("file")
	if notesFile == "" {
		notesFile = "../../audio/output/album_notes.json"
	}

	// Parse playback speed multiplier (default 1.0).
	speed := 1.0
	if qs := r.URL.Query().Get("speed"); qs != "" {
		if s, err := strconv.ParseFloat(qs, 64); err == nil && s > 0 {
			speed = s
		}
	}

	// Read and parse the notes JSON file.
	data, err := os.ReadFile(notesFile)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to read notes file: %v", err), http.StatusNotFound)
		return
	}

	var notes []noteEvent
	if err := json.Unmarshal(data, &notes); err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse notes JSON: %v", err), http.StatusBadRequest)
		return
	}

	// Sort notes by time to ensure correct playback order.
	sort.Slice(notes, func(i, j int) bool {
		return notes[i].T < notes[j].T
	})

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Send metadata event first.
	meta := map[string]interface{}{
		"type":       "notes_start",
		"total":      len(notes),
		"speed":      speed,
		"source":     notesFile,
	}
	metaJSON, _ := json.Marshal(meta)
	fmt.Fprintf(w, "data: %s\n\n", metaJSON)
	flusher.Flush()

	ctx := r.Context()
	startTime := time.Now()
	var baseTime float64
	if len(notes) > 0 {
		baseTime = notes[0].T
	}

	for i, note := range notes {
		// Calculate when this note should be sent relative to stream start.
		noteOffset := (note.T - baseTime) / speed
		targetTime := startTime.Add(time.Duration(noteOffset * float64(time.Second)))

		// Wait until it is time to send this note.
		waitDur := time.Until(targetTime)
		if waitDur > 0 {
			select {
			case <-ctx.Done():
				return
			case <-time.After(waitDur):
			}
		}

		// Check for client disconnect.
		select {
		case <-ctx.Done():
			return
		default:
		}

		noteJSON, err := json.Marshal(note)
		if err != nil {
			continue
		}
		fmt.Fprintf(w, "id: %d\ndata: %s\n\n", i, noteJSON)
		flusher.Flush()
	}

	// Send completion event.
	complete := map[string]interface{}{
		"type":    "notes_complete",
		"total":   len(notes),
		"elapsed": time.Since(startTime).Seconds(),
	}
	completeJSON, _ := json.Marshal(complete)
	fmt.Fprintf(w, "data: %s\n\n", completeJSON)
	flusher.Flush()
}

// handleAudioStream serves MP3 files as a streaming audio endpoint with support
// for HTTP Range requests (seeking). Compatible with VLC, mpv, and browsers.
func handleAudioStream(w http.ResponseWriter, r *http.Request, defaultDir string) {
	// Determine which file to stream.
	requestedFile := r.URL.Query().Get("file")

	if requestedFile == "" {
		// If no file specified, look for the most recent MP3 in the audio output dir.
		searchDir := defaultDir
		if searchDir == "" {
			searchDir = "../../audio/output"
		}

		// Find the newest MP3 file in the directory.
		entries, err := os.ReadDir(searchDir)
		if err != nil {
			http.Error(w, fmt.Sprintf("Cannot read audio directory: %v", err), http.StatusNotFound)
			return
		}

		var newestMP3 string
		var newestTime time.Time
		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			if filepath.Ext(entry.Name()) != ".mp3" {
				continue
			}
			info, err := entry.Info()
			if err != nil {
				continue
			}
			if newestMP3 == "" || info.ModTime().After(newestTime) {
				newestMP3 = filepath.Join(searchDir, entry.Name())
				newestTime = info.ModTime()
			}
		}

		if newestMP3 == "" {
			http.Error(w, "No MP3 files found in audio output directory", http.StatusNotFound)
			return
		}
		requestedFile = newestMP3
	}

	// Open the file.
	f, err := os.Open(requestedFile)
	if err != nil {
		http.Error(w, fmt.Sprintf("Cannot open audio file: %v", err), http.StatusNotFound)
		return
	}
	defer f.Close()

	stat, err := f.Stat()
	if err != nil {
		http.Error(w, fmt.Sprintf("Cannot stat audio file: %v", err), http.StatusInternalServerError)
		return
	}

	// Set audio-appropriate headers.
	w.Header().Set("Content-Type", "audio/mpeg")
	w.Header().Set("Accept-Ranges", "bytes")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("X-Content-Type-Options", "nosniff")

	// Use http.ServeContent which handles Range requests automatically.
	http.ServeContent(w, r, filepath.Base(requestedFile), stat.ModTime(), f)
}

// handleSSE handles an individual SSE connection: subscribes to the broker,
// streams live events until the client disconnects.
func handleSSE(w http.ResponseWriter, r *http.Request, seed int64, b *broker, latest *latestStore) {
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming not supported", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	// Subscribe to the shared broadcast.
	ch := b.subscribe()
	defer b.unsubscribe(ch)

	// Send the latest known state immediately so the viewer is not blank.
	if s := latest.get(); s != nil {
		data, err := json.Marshal(s)
		if err == nil {
			fmt.Fprintf(w, "data: %s\n\n", data)
			flusher.Flush()
		}
	}

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
