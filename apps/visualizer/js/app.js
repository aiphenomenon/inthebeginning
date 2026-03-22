/**
 * Main Application for In The Beginning Visualizer.
 *
 * Detects mode (album, single, stream), initializes grid, player, and score.
 * Orchestrates the animation loop and color transitions.
 */

/**
 * VisualizerApp is the main application controller.
 */
class VisualizerApp {
  /**
   * Create and initialize the visualizer application.
   */
  constructor() {
    /** @type {Grid|null} */
    this.grid = null;

    /** @type {Player|null} */
    this.player = null;

    /** @type {Score|null} */
    this.score = null;

    /** @type {StreamClient|null} */
    this.streamClient = null;

    /** @type {string} */
    this.mode = 'single';

    /** @type {number} Last color shift time */
    this._lastColorShift = 0;

    /** @type {number} Color shift interval in seconds */
    this._colorShiftInterval = 600;

    /** @type {number} Hue rotation per shift in degrees */
    this._hueRotationPerShift = 45;

    /** @type {HTMLElement|null} */
    this._trackListEl = null;

    /** @type {HTMLElement|null} */
    this._statusEl = null;

    /** @type {HTMLElement|null} */
    this._fileInputEl = null;
  }

  /**
   * Initialize the application after DOM is ready.
   */
  init() {
    const gridContainer = document.getElementById('grid-container');
    const controlBar = document.getElementById('control-bar');
    this._trackListEl = document.getElementById('track-list');
    this._statusEl = document.getElementById('status-message');
    this._fileInputEl = document.getElementById('score-file-input');

    // Create grid
    this.grid = new Grid(gridContainer);

    // Detect mode from URL params
    const params = new URLSearchParams(window.location.search);
    this.mode = params.get('mode') || 'album';
    const scoreUrl = params.get('score') || '';
    const streamUrl = params.get('stream') || '';
    const audioUrl = params.get('audio') || '';

    /** @type {string} Base URL for note JSON files */
    this._notesBaseUrl = '';

    /** @type {string} Base URL for MP3 audio files */
    this._audioBaseUrl = '';

    // Create player
    this.player = new Player({
      controlBar: controlBar,
      mode: this.mode,
      score: null,
      onTimeUpdate: (time) => this._onTimeUpdate(time),
      onTrackChange: (idx) => this._onTrackChange(idx)
    });

    // Set up file input handler
    if (this._fileInputEl) {
      this._fileInputEl.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          this._loadScoreFile(file);
        }
      });
    }

    // Set up drag and drop on grid
    if (gridContainer) {
      gridContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        gridContainer.classList.add('drag-over');
      });
      gridContainer.addEventListener('dragleave', () => {
        gridContainer.classList.remove('drag-over');
      });
      gridContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        gridContainer.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.json')) {
          this._loadScoreFile(file);
        }
      });
    }

    // Load score if URL provided, otherwise auto-load V8 Sessions
    if (scoreUrl) {
      this._loadScoreFromUrl(scoreUrl);
    } else if (!streamUrl) {
      this._autoLoadV8Sessions();
    }

    // Load audio if URL provided
    if (audioUrl) {
      this.player.loadAudio(audioUrl);
    }

    // Start stream if in stream mode
    if (this.mode === 'stream' && streamUrl) {
      this._startStream(streamUrl);
    }

    if (!scoreUrl && !streamUrl && !audioUrl) {
      this._setStatus('Loading V8 Sessions...');
    }
  }

  /**
   * Auto-load the V8 Sessions album from sibling directories.
   * Tries multiple relative paths to find the album_notes.json and MP3s.
   * Works on GitHub Pages without a Python server.
   * @private
   */
  async _autoLoadV8Sessions() {
    // Possible locations for album_notes.json (relative to visualizer/)
    const notePaths = [
      '../cosmic-runner-v3/audio/',
      '../cosmic-runner-v2/audio/',
    ];
    // Possible locations for MP3 files
    const audioPaths = [
      '../cosmic-runner-v2/audio/',
      '../cosmic-runner-v3/audio/',
    ];

    let albumJson = null;
    let notesBase = '';

    for (const base of notePaths) {
      try {
        const resp = await fetch(base + 'album_notes.json');
        if (resp.ok) {
          albumJson = await resp.json();
          notesBase = base;
          break;
        }
      } catch (e) {
        // Try next path
      }
    }

    if (!albumJson) {
      this._setStatus('Drop a score JSON or use ?score=URL to load.');
      return;
    }

    // Determine audio base URL
    let audioBase = '';
    if (albumJson.tracks && albumJson.tracks.length > 0) {
      const testFile = albumJson.tracks[0].audio_file;
      for (const base of audioPaths) {
        try {
          const resp = await fetch(base + testFile, { method: 'HEAD' });
          if (resp.ok) {
            audioBase = base;
            break;
          }
        } catch (e) {
          // Try next path
        }
      }
    }
    if (!audioBase) audioBase = notesBase;

    this._notesBaseUrl = notesBase;
    this._audioBaseUrl = audioBase;
    this._applyScore(albumJson);
    this._setStatus('In The Beginning Phase 0 \u2014 V8 Sessions');
  }

  /**
   * Load a score JSON file from a File object.
   * @param {File} file
   * @private
   */
  _loadScoreFile(file) {
    this._setStatus('Loading score...');
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target.result);
        this._applyScore(json);
        this._setStatus(`Loaded: ${file.name}`);
      } catch (err) {
        this._setStatus(`Error loading score: ${err.message}`);
      }
    };
    reader.readAsText(file);
  }

  /**
   * Load a score JSON file from a URL.
   * @param {string} url
   * @private
   */
  _loadScoreFromUrl(url) {
    this._setStatus('Loading score from URL...');
    fetch(url)
      .then(r => r.json())
      .then(json => {
        this._applyScore(json);
        this._setStatus('Score loaded.');
      })
      .catch(err => {
        this._setStatus(`Error loading score: ${err.message}`);
      });
  }

  /**
   * Apply a parsed score JSON to the application.
   * @param {Object} json
   * @private
   */
  _applyScore(json) {
    this.score = Score.fromJSON(json);
    this.mode = this.score.mode || this.mode;
    this._colorShiftInterval = this.score.colorShiftInterval || 600;

    // Configure grid
    if (this.score.instrumentFamilies) {
      this.grid.setInstrumentFamilies(this.score.instrumentFamilies);
    }
    if (this.score.instruments && this.score.instruments.length > 0) {
      this.grid.preassignColumns(this.score.instruments);
    }

    // Update player
    this.player.score = this.score;
    this.player.mode = this.mode;
    this.player._updateModeVisibility();

    // Load first track audio if album mode
    if (this.mode === 'album' && this.score.tracks.length > 0) {
      const firstTrack = this.score.tracks[0];
      const audioUrl = this._resolveAudioUrl(firstTrack.audioFile);
      if (audioUrl) {
        this.player.loadAudio(audioUrl);
      }
      // Load first track's note events if V3 compressed (lazy loading)
      if (firstTrack.noteFile) {
        this._loadTrackNotes(0);
      }
      this._buildTrackList();
    }

    // Update track title
    if (this.score.tracks.length > 0 && this.player.ui.trackTitle) {
      const t = this.score.tracks[0];
      this.player.ui.trackTitle.textContent = `${t.trackNum}. ${t.title}`;
    }
  }

  /**
   * Resolve audio URL, applying the audio base path.
   * @param {string} audioFile - Audio file name.
   * @returns {string} Full URL.
   * @private
   */
  _resolveAudioUrl(audioFile) {
    if (!audioFile) return '';
    if (audioFile.startsWith('http') || audioFile.startsWith('/')) return audioFile;
    return (this._audioBaseUrl || '') + audioFile;
  }

  /**
   * Load V3 compressed note events for a track.
   * @param {number} trackIndex - Track index (0-based).
   * @returns {Promise<void>}
   * @private
   */
  async _loadTrackNotes(trackIndex) {
    if (!this.score || trackIndex < 0 || trackIndex >= this.score.tracks.length) return;
    const track = this.score.tracks[trackIndex];
    if (!track.noteFile) return;
    if (track.events && track.events.length > 0) return; // already loaded

    const url = (this._notesBaseUrl || '') + track.noteFile;
    const loaded = await this.score.loadTrackEvents(trackIndex, url);
    if (loaded) {
      // Rebuild instruments from loaded events
      const instruments = new Set();
      for (const ev of track.events) {
        instruments.add(ev.inst);
      }
      for (const inst of instruments) {
        this.grid.getColumn(inst); // assign columns
      }
    }
  }

  /**
   * Build the track list sidebar for album mode.
   * @private
   */
  _buildTrackList() {
    if (!this._trackListEl || !this.score) return;

    this._trackListEl.innerHTML = '';
    this._trackListEl.style.display = this.mode === 'album' ? 'block' : 'none';

    for (let i = 0; i < this.score.tracks.length; i++) {
      const track = this.score.tracks[i];
      const item = document.createElement('div');
      item.className = 'track-item';
      if (i === 0) item.classList.add('active');
      item.textContent = `${track.trackNum}. ${track.title}`;
      item.dataset.index = i;
      item.addEventListener('click', () => {
        this._switchToTrack(i);
      });
      this._trackListEl.appendChild(item);
    }
  }

  /**
   * Switch to a specific track, loading notes and audio.
   * @param {number} index - Track index (0-based).
   * @private
   */
  async _switchToTrack(index) {
    if (!this.score || index < 0 || index >= this.score.tracks.length) return;
    const track = this.score.tracks[index];

    this.player.currentTrack = index;
    this._highlightTrack(index);
    this.grid.clearGrid();
    this.grid.resetColumns();

    // Load track audio
    const audioUrl = this._resolveAudioUrl(track.audioFile);
    if (audioUrl) {
      this.player.audio.src = audioUrl;
      if (this.player.ui.trackTitle) {
        this.player.ui.trackTitle.textContent = `${track.trackNum}. ${track.title}`;
      }
      if (this.player.isPlaying) {
        this.player.audio.play().catch(() => {});
      }
    }

    // Load V3 compressed notes if needed
    await this._loadTrackNotes(index);

    // If track already has events loaded, rebuild the index for local time
    if (track.events && track.events.length > 0 && track.noteFile) {
      this.score._buildEventIndexForTrack(index);
    }
  }

  /**
   * Highlight the current track in the track list.
   * @param {number} index
   * @private
   */
  _highlightTrack(index) {
    if (!this._trackListEl) return;
    const items = this._trackListEl.querySelectorAll('.track-item');
    items.forEach((item, i) => {
      item.classList.toggle('active', i === index);
    });
  }

  /**
   * Handle time updates from the player.
   * For V3 compressed format, events are per-track with local times,
   * so we use audio.currentTime directly (which is local to the track).
   * For legacy format, events use absolute times from the score.
   * @param {number} time - Current playback time in seconds.
   * @private
   */
  _onTimeUpdate(time) {
    if (!this.score) return;

    // For V3 compressed album format, events are per-track (local time)
    // The audio.currentTime IS the local track time, so use getActiveEvents
    // which searches allEvents by absolute time. For V3, each track's events
    // have startTime=0 effectively since they're loaded individually.
    const events = this.score.getActiveEvents(time);
    this.grid.updateGrid(events);

    // Color shift check
    const shiftIndex = Math.floor(time / this._colorShiftInterval);
    if (shiftIndex > this._lastColorShift) {
      this._lastColorShift = shiftIndex;
      const rotation = 30 + Math.random() * 30; // 30-60 degrees
      this.grid.rotateHue(rotation);
    }

    // Update player accent color
    const dominantHue = this.grid.getDominantHue();
    this.player.updateAccentColor(dominantHue);
  }

  /**
   * Handle track changes from the player (auto-advance on track end).
   * @param {number} index - New track index.
   * @private
   */
  _onTrackChange(index) {
    this._switchToTrack(index);
  }

  /**
   * Start the SSE stream for radio mode.
   * @param {string} url - SSE endpoint URL.
   * @private
   */
  _startStream(url) {
    this.streamClient = new StreamClient({
      url: url,
      onNotes: (events) => {
        this.grid.updateGrid(events);
        const dominantHue = this.grid.getDominantHue();
        this.player.updateAccentColor(dominantHue);
      },
      onConnect: () => {
        this._setStatus('Connected to stream.');
      },
      onDisconnect: () => {
        this._setStatus('Stream disconnected. Reconnecting...');
      },
      onError: (err) => {
        this._setStatus(`Stream error: ${err.message}`);
      }
    });
    this.streamClient.connect();
  }

  /**
   * Set the status message.
   * @param {string} msg
   * @private
   */
  _setStatus(msg) {
    if (this._statusEl) {
      this._statusEl.textContent = msg;
    }
  }
}

// Initialize on DOM ready
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    const app = new VisualizerApp();
    app.init();
    window.__visualizerApp = app;
  });
}

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { VisualizerApp };
}
