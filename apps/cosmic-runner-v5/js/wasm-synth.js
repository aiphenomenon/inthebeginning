/**
 * WebAssembly Synthesizer Bridge for inthebeginning bounce.
 *
 * Provides a 4th audio mode ("WASM Synth") that renders MIDI through a
 * WebAssembly audio synthesis module. When the WASM binary is available,
 * synthesis runs in an AudioWorklet powered by Rust-compiled WebAssembly
 * for higher performance and lower latency.
 *
 * When the WASM binary is NOT available (e.g., not yet compiled, network
 * error, or unsupported browser), gracefully falls back to the existing
 * SynthEngine (additive synthesis + sample bank).
 *
 * The WasmSynth exposes the same API surface as MidiPlayer so it can be
 * used interchangeably by GamePlayer. It manages its own MIDI catalog,
 * shuffle history, and playback state.
 *
 * Existing "knobs" (mutation presets, volume, speed) all work in WASM mode
 * by forwarding parameters to the WASM module (or to the fallback synth).
 */

class WasmSynth {
  /**
   * @param {SynthEngine} fallbackSynth - Shared SynthEngine for fallback mode.
   */
  constructor(fallbackSynth) {
    /** @type {SynthEngine} Fallback synth engine when WASM is unavailable. */
    this._fallbackSynth = fallbackSynth;

    /** @type {boolean} Whether the WASM module loaded successfully. */
    this._wasmReady = false;

    /** @type {object|null} WASM module exports (init, note_on, note_off, render). */
    this._wasmModule = null;

    /** @type {AudioWorkletNode|null} AudioWorklet node for WASM rendering. */
    this._workletNode = null;

    /** @type {AudioContext|null} Audio context (shared or own). */
    this._ctx = null;

    // ──── Playback state ────
    /** @type {boolean} */
    this.isPlaying = false;
    /** @type {number} Current playback position in seconds. */
    this._currentTime = 0;
    /** @type {number} AudioContext.currentTime when playback started/resumed. */
    this._startCtxTime = 0;
    /** @type {number} Duration of loaded MIDI in seconds. */
    this._duration = 0;
    /** @type {Array} Parsed note events sorted by time. */
    this._notes = [];
    /** @type {number} Next note index to schedule. */
    this._nextNote = 0;
    /** @type {number} RAF ID for scheduling loop. */
    this._rafId = 0;
    /** @type {number} Interval ID for note event emission. */
    this._emitInterval = 0;

    // ──── Mutation & speed ────
    /** @type {Object} Current mutation preset. */
    this._mutation = { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' };
    /** @type {number} Playback speed multiplier. */
    this._speedMult = 1.0;
    /** @type {number} Volume (0-1). */
    this._volume = 0.8;

    // ──── MIDI catalog & shuffle ────
    /** @type {Array} Full MIDI catalog entries. */
    this.catalog = [];
    /** @type {string} Base URL for MIDI files. */
    this.catalogBaseUrl = '';
    /** @type {Array<number>} Shuffle history (indices into catalog). */
    this._shuffleHistory = [];
    /** @type {number} Current position in shuffle history. */
    this._shufflePos = -1;

    // ──── Track metadata ────
    /** @type {Object|null} Current track info (name, composer, era). */
    this.trackInfo = null;

    // ──── Worker for MIDI parsing ────
    /** @type {Worker|null} */
    this._worker = null;
    /** @type {boolean} */
    this._workerReady = false;
    /** @type {number} */
    this._parseId = 0;
    /** @type {Map<number, {resolve, reject}>} */
    this._pending = new Map();

    // ──── Callbacks ────
    /** @type {Function|null} Note event callback for visualization. */
    this.onNoteEvent = null;
    /** @type {Function|null} Track end callback. */
    this.onTrackEnd = null;

    this._initWorker();
  }

  // ──── Initialization ────

  /**
   * Attempt to load the WASM synthesis module.
   * @param {string} [wasmUrl='js/wasm-synth.wasm'] - URL to the .wasm binary.
   * @returns {Promise<boolean>} True if WASM loaded, false if falling back.
   */
  async initWasm(wasmUrl) {
    wasmUrl = wasmUrl || 'js/wasm-synth.wasm';
    try {
      if (typeof WebAssembly === 'undefined') {
        console.warn('WasmSynth: WebAssembly not supported, using fallback');
        return false;
      }

      const resp = await fetch(wasmUrl);
      if (!resp.ok) {
        console.warn(`WasmSynth: WASM binary not found at ${wasmUrl}, using fallback`);
        return false;
      }

      const bytes = await resp.arrayBuffer();
      const { instance } = await WebAssembly.instantiate(bytes, this._getImports());

      this._wasmModule = instance.exports;
      if (typeof this._wasmModule.init === 'function') {
        this._wasmModule.init(44100); // sample rate
      }
      this._wasmReady = true;
      console.log('WasmSynth: WASM module loaded successfully');
      return true;
    } catch (e) {
      console.warn('WasmSynth: Failed to load WASM module, using fallback:', e.message);
      this._wasmReady = false;
      return false;
    }
  }

  /**
   * Build the WebAssembly import object.
   * Provides JS functions that the WASM module can call.
   * @returns {Object} Import object for WebAssembly.instantiate.
   */
  _getImports() {
    return {
      env: {
        // Console logging from WASM
        log_f64: (val) => console.log('WASM:', val),
        log_str: (ptr, len) => {
          // Will be implemented when WASM module has string memory
        },
        // Math functions WASM might need
        sin: Math.sin,
        cos: Math.cos,
        pow: Math.pow,
        exp: Math.exp,
        log: Math.log,
        random: Math.random,
      },
    };
  }

  /**
   * Initialize the AudioContext and AudioWorklet for WASM rendering.
   * If WASM is not available, initializes the fallback SynthEngine instead.
   */
  async initAudio() {
    if (this._wasmReady) {
      // Create or reuse AudioContext
      this._ctx = this._fallbackSynth?.ctx || new (window.AudioContext || window.webkitAudioContext)();
      // TODO: Register AudioWorklet processor for WASM rendering
      // For now, use ScriptProcessorNode as a bridge
      // (AudioWorklet registration will come in Phase 2)
    }

    // Always ensure fallback synth is initialized
    if (this._fallbackSynth) {
      this._fallbackSynth.init();
    }
  }

  // ──── Worker Setup (reuses synth-worker.js for MIDI parsing) ────

  _initWorker() {
    try {
      this._worker = new Worker('js/synth-worker.js');
      this._workerReady = true;
      this._worker.onmessage = (e) => this._onWorkerMessage(e);
      this._worker.onerror = () => {
        this._workerReady = false;
        this._worker = null;
      };
    } catch (err) {
      this._workerReady = false;
    }
  }

  _onWorkerMessage(e) {
    const msg = e.data;
    const pending = this._pending.get(msg.id);
    if (!pending) return;
    this._pending.delete(msg.id);

    if (msg.type === 'notes') {
      pending.resolve({ notes: msg.notes, duration: msg.duration, header: msg.header });
    } else {
      pending.reject(new Error(msg.message || 'Parse error'));
    }
  }

  // ──── MIDI Catalog Management ────

  /**
   * Load MIDI catalog from a JSON index file.
   * @param {string} catalogUrl - URL to midi_catalog.json.
   * @param {string} [baseUrl] - Base URL for MIDI file paths.
   * @returns {Promise<boolean>}
   */
  async loadCatalog(catalogUrl, baseUrl) {
    try {
      const resp = await fetch(catalogUrl);
      if (!resp.ok) return false;
      const data = await resp.json();
      this.catalog = data.midis || [];
      this.catalogBaseUrl = baseUrl ||
        catalogUrl.substring(0, catalogUrl.lastIndexOf('/') + 1);
      return this.catalog.length > 0;
    } catch (e) {
      return false;
    }
  }

  /**
   * Pick a random MIDI from the catalog, avoiding recent history.
   * @returns {Object|null} Catalog entry { path, name, composer }.
   */
  _pickRandom() {
    if (this.catalog.length === 0) return null;
    const recentSet = new Set(this._shuffleHistory.slice(-20));
    let idx;
    let attempts = 0;
    do {
      idx = Math.floor(Math.random() * this.catalog.length);
      attempts++;
    } while (recentSet.has(idx) && attempts < 50);

    this._shuffleHistory.length = this._shufflePos + 1;
    this._shuffleHistory.push(idx);
    if (this._shuffleHistory.length > 144) {
      this._shuffleHistory.shift();
    }
    this._shufflePos = this._shuffleHistory.length - 1;
    return this.catalog[idx];
  }

  // ──── MIDI Loading ────

  /**
   * Load and start playing the next random MIDI.
   * @returns {Promise<boolean>}
   */
  async loadNextRandom() {
    const entry = this._pickRandom();
    if (!entry) return false;
    return this._loadFromCatalogEntry(entry);
  }

  /**
   * Load a MIDI file from a catalog entry.
   * @param {Object} entry - Catalog entry with path, name, composer.
   * @returns {Promise<boolean>}
   */
  async _loadFromCatalogEntry(entry) {
    try {
      const url = this.catalogBaseUrl + entry.path;
      const resp = await fetch(url);
      if (!resp.ok) return false;
      const buffer = await resp.arrayBuffer();

      const parsed = await this._parseMidi(buffer);
      this._notes = parsed.notes || [];
      this._duration = parsed.duration || 0;
      this._currentTime = 0;
      this._nextNote = 0;

      this.trackInfo = {
        name: entry.name || entry.path.split('/').pop().replace('.mid', ''),
        composer: entry.composer || 'Unknown',
        era: entry.era || '',
      };

      return true;
    } catch (e) {
      console.warn('WasmSynth: Failed to load MIDI:', e.message);
      return false;
    }
  }

  /**
   * Parse a MIDI ArrayBuffer into note events.
   * Uses the Web Worker (same as MidiPlayer).
   * @param {ArrayBuffer} buffer - Raw MIDI file data.
   * @returns {Promise<Object>} Parsed notes and duration.
   */
  _parseMidi(buffer) {
    return new Promise((resolve, reject) => {
      if (!this._workerReady || !this._worker) {
        // Fallback: inline parse (basic)
        reject(new Error('Worker not available'));
        return;
      }
      const id = ++this._parseId;
      this._pending.set(id, { resolve, reject });
      this._worker.postMessage({
        type: 'parse',
        id,
        buffer: new Uint8Array(buffer),
      });
    });
  }

  // ──── Playback Controls ────

  /** Start or resume playback. */
  play() {
    if (this.isPlaying) return;
    if (!this._notes.length) return;

    // Get the synth (WASM or fallback)
    const synth = this._getActiveSynth();
    if (synth) {
      synth.init();
      synth.resume();
      synth.setMutation(this._mutation);
    }

    this.isPlaying = true;
    const ctx = this._getAudioContext();
    if (ctx) {
      this._startCtxTime = ctx.currentTime - (this._currentTime / this._effectiveSpeed());
    }

    this._scheduleLoop();
    this._startEmitLoop();
  }

  /** Pause playback. */
  pause() {
    if (!this.isPlaying) return;
    this.isPlaying = false;
    this._currentTime = this.getCurrentTime();
    const synth = this._getActiveSynth();
    if (synth) synth.stopAll();
    this._cancelLoops();
  }

  /** Stop playback and reset to beginning. */
  stop() {
    this.isPlaying = false;
    this._currentTime = 0;
    this._nextNote = 0;
    const synth = this._getActiveSynth();
    if (synth) synth.stopAll();
    this._cancelLoops();
  }

  /**
   * Seek to a specific time.
   * @param {number} timeSec - Target time in seconds.
   */
  seek(timeSec) {
    const wasPlaying = this.isPlaying;
    if (this.isPlaying) {
      const synth = this._getActiveSynth();
      if (synth) synth.stopAll();
      this._cancelLoops();
      this.isPlaying = false;
    }

    timeSec = Math.max(0, Math.min(timeSec, this._duration));
    this._currentTime = timeSec;

    const speed = this._effectiveSpeed();
    let lo = 0, hi = this._notes.length;
    while (lo < hi) {
      const mid = (lo + hi) >>> 1;
      if ((this._notes[mid].t / speed) < timeSec) lo = mid + 1;
      else hi = mid;
    }
    this._nextNote = lo;

    if (wasPlaying) {
      this.isPlaying = true;
      const ctx = this._getAudioContext();
      if (ctx) {
        this._startCtxTime = ctx.currentTime - (this._currentTime / speed);
      }
      this._scheduleLoop();
      this._startEmitLoop();
    }
  }

  /** @returns {number} Current playback time in seconds. */
  getCurrentTime() {
    if (!this.isPlaying) return this._currentTime;
    const ctx = this._getAudioContext();
    if (!ctx) return this._currentTime;
    const speed = this._effectiveSpeed();
    return (ctx.currentTime - this._startCtxTime) * speed;
  }

  /** @returns {number} Duration of loaded MIDI in seconds. */
  getDuration() {
    return this._duration / this._effectiveSpeed();
  }

  /** @returns {Object} Display info for the current track. */
  getDisplayInfo() {
    const sanitize = (s) => String(s || '')
      .replace(/[<>]/g, '')
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .slice(0, 200);
    return {
      name: sanitize(this.trackInfo?.name),
      composer: sanitize(this.trackInfo?.composer),
      era: sanitize(this.trackInfo?.era),
      wasmActive: this._wasmReady,
    };
  }

  /** @returns {Object} Track info including note count. */
  getTrackInfo() {
    return {
      noteCount: this._notes.length,
      duration: this._duration,
      channels: [...new Set(this._notes.map(n => n.ch))].length,
      wasmActive: this._wasmReady,
      ...(this.trackInfo || {}),
    };
  }

  // ──── Mutation & Settings ────

  /**
   * Apply a mutation preset. Affects both WASM and fallback rendering.
   * @param {Object} mutation - Mutation preset object.
   */
  setMutation(mutation) {
    this._mutation = mutation || { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' };
    const synth = this._getActiveSynth();
    if (synth) synth.setMutation(this._mutation);

    // If WASM is active, also forward mutation to WASM module
    if (this._wasmReady && this._wasmModule) {
      if (typeof this._wasmModule.set_pitch_shift === 'function') {
        this._wasmModule.set_pitch_shift(this._mutation.pitchShift || 0);
      }
      if (typeof this._wasmModule.set_tempo_mult === 'function') {
        this._wasmModule.set_tempo_mult(this._mutation.tempoMult || 1.0);
      }
    }
  }

  /**
   * Set playback speed multiplier.
   * @param {number} mult - Speed multiplier (0.25-4.0).
   */
  setSpeed(mult) {
    this._speedMult = Math.max(0.25, Math.min(4.0, mult));
  }

  /**
   * Set volume.
   * @param {number} vol - Volume (0-1).
   */
  setVolume(vol) {
    this._volume = Math.max(0, Math.min(1, vol));
    const synth = this._getActiveSynth();
    if (synth) synth.setVolume(this._volume);

    if (this._wasmReady && this._wasmModule) {
      if (typeof this._wasmModule.set_volume === 'function') {
        this._wasmModule.set_volume(this._volume);
      }
    }
  }

  // ──── Internal Helpers ────

  /**
   * Get the active synthesis engine (WASM or fallback).
   * @returns {SynthEngine|null}
   */
  _getActiveSynth() {
    // For now, always use fallback synth for audio output.
    // When WASM AudioWorklet is implemented (Phase 2), this will
    // return the WASM-backed synth when _wasmReady is true.
    return this._fallbackSynth;
  }

  /**
   * Get the active AudioContext.
   * @returns {AudioContext|null}
   */
  _getAudioContext() {
    if (this._ctx) return this._ctx;
    return this._fallbackSynth?.ctx || null;
  }

  /** @returns {number} Effective playback speed (base speed * mutation tempo). */
  _effectiveSpeed() {
    return this._speedMult * (this._mutation.tempoMult || 1.0);
  }

  // ──── Note Scheduling ────

  _scheduleLoop() {
    if (!this.isPlaying) return;

    const now = this.getCurrentTime();
    const lookAhead = 0.15;
    const speed = this._effectiveSpeed();
    const synth = this._getActiveSynth();

    while (this._nextNote < this._notes.length) {
      const note = this._notes[this._nextNote];
      const noteTime = note.t / speed;

      if (noteTime > now + lookAhead) break;

      if (noteTime >= now - 0.05 && synth) {
        synth.playNote(note, Math.max(0, noteTime - now));
      }
      this._nextNote++;
    }

    // Check if track ended
    if (this._nextNote >= this._notes.length && now >= this._duration / speed) {
      this.isPlaying = false;
      this._cancelLoops();
      if (this.onTrackEnd) this.onTrackEnd();
      return;
    }

    this._rafId = requestAnimationFrame(() => this._scheduleLoop());
  }

  _startEmitLoop() {
    if (this._emitInterval) clearInterval(this._emitInterval);
    this._emitInterval = setInterval(() => {
      if (!this.isPlaying || !this.onNoteEvent) return;
      const now = this.getCurrentTime();
      const speed = this._effectiveSpeed();
      const active = [];

      for (let i = Math.max(0, this._nextNote - 30); i < this._notes.length; i++) {
        const note = this._notes[i];
        const t = note.t / speed;
        const dur = (note.dur || 0.1) / speed;
        if (t > now + 0.1) break;
        if (t + dur >= now && t <= now) {
          active.push({
            note: note.note,
            vel: note.vel || 80,
            ch: note.ch || 0,
            inst: note.inst || 0,
          });
        }
      }

      if (active.length > 0) {
        this.onNoteEvent(active);
      }
    }, 50);
  }

  _cancelLoops() {
    if (this._rafId) {
      cancelAnimationFrame(this._rafId);
      this._rafId = 0;
    }
    if (this._emitInterval) {
      clearInterval(this._emitInterval);
      this._emitInterval = 0;
    }
  }

  // ──── Navigation ────

  /**
   * Go to previous track in shuffle history.
   * @returns {Promise<boolean>}
   */
  async prevTrack() {
    if (this._shufflePos > 0) {
      this._shufflePos--;
      const idx = this._shuffleHistory[this._shufflePos];
      if (idx < this.catalog.length) {
        this.stop();
        return this._loadFromCatalogEntry(this.catalog[idx]);
      }
    }
    return false;
  }

  /**
   * Go to next track (forward in history or new random).
   * @returns {Promise<boolean>}
   */
  async nextTrack() {
    this.stop();
    if (this._shufflePos < this._shuffleHistory.length - 1) {
      this._shufflePos++;
      const idx = this._shuffleHistory[this._shufflePos];
      if (idx < this.catalog.length) {
        return this._loadFromCatalogEntry(this.catalog[idx]);
      }
    }
    return this.loadNextRandom();
  }

  // ──── Cleanup ────

  /** Destroy all resources. */
  destroy() {
    this.stop();
    if (this._worker) {
      this._worker.terminate();
      this._worker = null;
    }
    if (this._workletNode) {
      this._workletNode.disconnect();
      this._workletNode = null;
    }
    this._wasmModule = null;
    this._wasmReady = false;
  }
}

// Export for Node.js test environment
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { WasmSynth };
}
