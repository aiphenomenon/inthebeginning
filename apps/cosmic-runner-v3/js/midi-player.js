/**
 * Web Audio API MIDI Player for Cosmic Runner V3.
 *
 * Parses Standard MIDI Files (SMF Format 0 and 1) in the browser
 * and synthesizes audio using Web Audio API oscillators + envelopes.
 * Emits real-time note events for grid visualization synchronization.
 *
 * No external dependencies — pure Web Audio API.
 */

class MidiPlayer {
  constructor() {
    /** @type {AudioContext|null} */
    this.ctx = null;
    /** @type {boolean} */
    this.isPlaying = false;
    /** @type {number} Current playback time in seconds. */
    this._currentTime = 0;
    /** @type {number} Start timestamp from AudioContext. */
    this._startCtxTime = 0;
    /** @type {number} Duration in seconds. */
    this._duration = 0;
    /** @type {Array} Parsed note events sorted by time. */
    this._notes = [];
    /** @type {number} Next note index to schedule. */
    this._nextNote = 0;
    /** @type {number} RAF ID for scheduling loop. */
    this._rafId = 0;
    /** @type {Map<number, OscillatorNode>} Active oscillators by note key. */
    this._activeOscs = new Map();
    /** @type {GainNode|null} Master gain. */
    this._masterGain = null;
    /** @type {ConvolverNode|null} Reverb node. */
    this._reverbNode = null;
    /** @type {GainNode|null} Reverb send gain. */
    this._reverbGain = null;
    /** @type {BiquadFilterNode|null} Master filter. */
    this._filterNode = null;
    /** @type {Object} Current mutation preset. */
    this._mutation = { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' };
    /** @type {Object} Parsed MIDI header info. */
    this._header = null;
    /** @type {Function|null} Callback for note events (for grid). */
    this.onNoteEvent = null;
    /** @type {Function|null} Callback when track ends. */
    this.onTrackEnd = null;
    /** @type {Object|null} Track metadata from catalog. */
    this.trackInfo = null;
    /** @type {number} Interval for emitting note events. */
    this._emitInterval = 0;
  }

  /**
   * Parse a Standard MIDI File from an ArrayBuffer.
   * @param {ArrayBuffer} buffer - Raw MIDI file bytes.
   * @returns {Promise<boolean>} True if parsing succeeded.
   */
  async loadMidi(buffer) {
    this.stop();

    try {
      const data = new DataView(buffer);
      const parsed = MidiPlayer._parseMidi(data);
      if (!parsed) return false;

      this._header = parsed.header;
      this._notes = parsed.notes;
      this._duration = parsed.duration;
      this._nextNote = 0;
      this._currentTime = 0;
      return true;
    } catch (e) {
      console.warn('MIDI parse error:', e);
      return false;
    }
  }

  /** Start or resume playback. */
  play() {
    if (this.isPlaying) return;
    if (!this._notes.length) return;

    this._ensureContext();
    this.isPlaying = true;
    this._startCtxTime = this.ctx.currentTime - this._currentTime;
    this._scheduleLoop();
    this._startEmitLoop();
  }

  /** Pause playback. */
  pause() {
    this.isPlaying = false;
    this._currentTime = this.getCurrentTime();
    this._stopAllNotes();
    if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = 0; }
    if (this._emitInterval) { clearInterval(this._emitInterval); this._emitInterval = 0; }
  }

  /** Stop playback and reset to beginning. */
  stop() {
    this.isPlaying = false;
    this._currentTime = 0;
    this._nextNote = 0;
    this._stopAllNotes();
    if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = 0; }
    if (this._emitInterval) { clearInterval(this._emitInterval); this._emitInterval = 0; }
  }

  /** @returns {number} Current playback time in seconds. */
  getCurrentTime() {
    if (!this.isPlaying || !this.ctx) return this._currentTime;
    return this.ctx.currentTime - this._startCtxTime;
  }

  /** @returns {number} Total duration in seconds. */
  getDuration() { return this._duration; }

  /**
   * Apply a mutation preset.
   * @param {Object} mutation - { pitchShift, tempoMult, reverb, filter }
   */
  setMutation(mutation) {
    this._mutation = mutation || { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' };
    if (this._reverbGain && this.ctx) {
      this._reverbGain.gain.setValueAtTime(this._mutation.reverb || 0, this.ctx.currentTime);
    }
    if (this._filterNode && this.ctx) {
      this._applyFilter();
    }
  }

  /**
   * Get metadata about the loaded track.
   * @returns {Object} Track info.
   */
  getTrackInfo() {
    return {
      noteCount: this._notes.length,
      duration: this._duration,
      channels: [...new Set(this._notes.map(n => n.ch))].length,
      ...(this.trackInfo || {}),
    };
  }

  // ──── Audio Graph Setup ────

  _ensureContext() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Master gain
    this._masterGain = this.ctx.createGain();
    this._masterGain.gain.value = 0.3;

    // Filter
    this._filterNode = this.ctx.createBiquadFilter();
    this._filterNode.type = 'allpass';
    this._filterNode.frequency.value = 2000;
    this._applyFilter();

    // Reverb (simple algorithmic impulse)
    this._reverbNode = this.ctx.createConvolver();
    this._reverbNode.buffer = this._createImpulseResponse(2, 2);
    this._reverbGain = this.ctx.createGain();
    this._reverbGain.gain.value = this._mutation.reverb || 0;

    // Routing: source -> filter -> masterGain -> destination
    //                  -> reverbGain -> reverb -> masterGain
    this._filterNode.connect(this._masterGain);
    this._filterNode.connect(this._reverbGain);
    this._reverbGain.connect(this._reverbNode);
    this._reverbNode.connect(this._masterGain);
    this._masterGain.connect(this.ctx.destination);
  }

  _applyFilter() {
    if (!this._filterNode) return;
    const f = this._mutation.filter || 'none';
    switch (f) {
      case 'lowpass':
        this._filterNode.type = 'lowpass';
        this._filterNode.frequency.value = 1200;
        this._filterNode.Q.value = 1;
        break;
      case 'highpass':
        this._filterNode.type = 'highpass';
        this._filterNode.frequency.value = 400;
        this._filterNode.Q.value = 1;
        break;
      case 'bandpass':
        this._filterNode.type = 'bandpass';
        this._filterNode.frequency.value = 800;
        this._filterNode.Q.value = 2;
        break;
      default:
        this._filterNode.type = 'allpass';
        break;
    }
  }

  /**
   * Generate a simple reverb impulse response.
   * @param {number} duration - Seconds.
   * @param {number} decay - Decay factor.
   * @returns {AudioBuffer}
   */
  _createImpulseResponse(duration, decay) {
    const rate = this.ctx.sampleRate;
    const length = rate * duration;
    const impulse = this.ctx.createBuffer(2, length, rate);
    for (let ch = 0; ch < 2; ch++) {
      const data = impulse.getChannelData(ch);
      for (let i = 0; i < length; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
      }
    }
    return impulse;
  }

  // ──── Note Scheduling ────

  _scheduleLoop() {
    if (!this.isPlaying) return;

    const now = this.getCurrentTime();
    const lookAhead = 0.15; // seconds to look ahead for scheduling
    const tempoMult = this._mutation.tempoMult || 1.0;

    while (this._nextNote < this._notes.length) {
      const note = this._notes[this._nextNote];
      const noteTime = note.t / tempoMult;

      if (noteTime > now + lookAhead) break;

      if (noteTime >= now - 0.05) {
        this._playNote(note, noteTime - now);
      }
      this._nextNote++;
    }

    // Check if track ended
    if (this._nextNote >= this._notes.length && now >= this._duration / tempoMult) {
      this.isPlaying = false;
      if (this.onTrackEnd) this.onTrackEnd();
      return;
    }

    this._rafId = requestAnimationFrame(() => this._scheduleLoop());
  }

  /**
   * Play a single note using an oscillator.
   * @param {Object} note - { t, dur, note, vel, ch }
   * @param {number} delay - Seconds from now.
   */
  _playNote(note, delay) {
    if (!this.ctx || delay < 0) delay = 0;

    const time = this.ctx.currentTime + delay;
    const pitchShift = this._mutation.pitchShift || 0;
    const midiNote = note.note + pitchShift;
    const freq = 440 * Math.pow(2, (midiNote - 69) / 12);
    const tempoMult = this._mutation.tempoMult || 1.0;
    const dur = Math.max(0.05, (note.dur || 0.2) / tempoMult);
    const vel = Math.max(0.01, Math.min(1, note.vel || 0.5));

    // Choose waveform based on channel
    let waveform = 'triangle';
    if (note.ch === 9) {
      // Percussion channel — use noise-like approach
      this._playPercussion(time, vel, dur);
      return;
    } else if (note.ch < 4) {
      waveform = 'sine';
    } else if (note.ch < 8) {
      waveform = 'triangle';
    } else {
      waveform = 'sawtooth';
    }

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = waveform;
      osc.frequency.setValueAtTime(freq, time);

      // ADSR envelope
      const attack = 0.02;
      const release = Math.min(0.15, dur * 0.3);
      gain.gain.setValueAtTime(0, time);
      gain.gain.linearRampToValueAtTime(vel * 0.15, time + attack);
      gain.gain.setValueAtTime(vel * 0.15, time + dur - release);
      gain.gain.linearRampToValueAtTime(0, time + dur);

      osc.connect(gain);
      gain.connect(this._filterNode);

      osc.start(time);
      osc.stop(time + dur + 0.01);

      // Track active oscillator
      const key = midiNote * 100 + note.ch;
      this._activeOscs.set(key, osc);
      osc.onended = () => this._activeOscs.delete(key);
    } catch (e) {
      // Silently handle oscillator creation failures
    }
  }

  /**
   * Simple percussion via filtered noise burst.
   * @param {number} time - AudioContext time.
   * @param {number} vel - Velocity 0-1.
   * @param {number} dur - Duration seconds.
   */
  _playPercussion(time, vel, dur) {
    try {
      const bufferSize = Math.floor(this.ctx.sampleRate * Math.min(dur, 0.3));
      const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / bufferSize, 3);
      }

      const source = this.ctx.createBufferSource();
      source.buffer = buffer;

      const gain = this.ctx.createGain();
      gain.gain.setValueAtTime(vel * 0.1, time);
      gain.gain.linearRampToValueAtTime(0, time + Math.min(dur, 0.3));

      const filter = this.ctx.createBiquadFilter();
      filter.type = 'highpass';
      filter.frequency.value = 200;

      source.connect(filter);
      filter.connect(gain);
      gain.connect(this._filterNode);

      source.start(time);
    } catch (e) {
      // Silently handle
    }
  }

  _stopAllNotes() {
    for (const [key, osc] of this._activeOscs) {
      try { osc.stop(); } catch (e) { /* already stopped */ }
    }
    this._activeOscs.clear();
  }

  // ──── Note Event Emission (for grid visualization) ────

  _startEmitLoop() {
    if (this._emitInterval) clearInterval(this._emitInterval);
    this._emitInterval = setInterval(() => {
      if (!this.isPlaying || !this.onNoteEvent) return;

      const now = this.getCurrentTime();
      const tempoMult = this._mutation.tempoMult || 1.0;
      const pitchShift = this._mutation.pitchShift || 0;
      const activeEvents = [];

      for (const note of this._notes) {
        const t = note.t / tempoMult;
        const dur = (note.dur || 0.2) / tempoMult;
        if (t > now + 0.05) break;
        if (t + dur > now && t <= now) {
          activeEvents.push({
            t: t,
            dur: dur,
            note: note.note + pitchShift,
            inst: note.inst || 'piano',
            vel: note.vel || 0.5,
            ch: note.ch || 0,
          });
        }
      }

      this.onNoteEvent(activeEvents);
    }, 50); // 20 Hz update rate
  }

  // ──── MIDI Parser ────

  /**
   * Parse a Standard MIDI File.
   * @param {DataView} data - MIDI file data.
   * @returns {Object|null} { header, notes, duration }
   */
  static _parseMidi(data) {
    let offset = 0;

    // Read header chunk
    const headerTag = MidiPlayer._readStr(data, offset, 4);
    if (headerTag !== 'MThd') return null;
    offset += 4;

    const headerLen = data.getUint32(offset);
    offset += 4;

    const format = data.getUint16(offset);
    offset += 2;
    const nTracks = data.getUint16(offset);
    offset += 2;
    const ticksPerBeat = data.getUint16(offset);
    offset += 2;
    offset += headerLen - 6; // skip any extra header bytes

    const header = { format, nTracks, ticksPerBeat };

    // Parse all tracks
    const allEvents = [];
    for (let t = 0; t < nTracks; t++) {
      const trackTag = MidiPlayer._readStr(data, offset, 4);
      if (trackTag !== 'MTrk') {
        // Try to skip unknown chunks
        if (offset + 8 <= data.byteLength) {
          offset += 4;
          const chunkLen = data.getUint32(offset);
          offset += 4 + chunkLen;
          continue;
        }
        break;
      }
      offset += 4;
      const trackLen = data.getUint32(offset);
      offset += 4;
      const trackEnd = offset + trackLen;

      const events = MidiPlayer._parseTrack(data, offset, trackEnd, ticksPerBeat);
      allEvents.push(...events);
      offset = trackEnd;
    }

    // Sort by time, then convert to note events
    allEvents.sort((a, b) => a.time - b.time);

    // Build note events (pair note-on with note-off)
    const notes = MidiPlayer._buildNoteEvents(allEvents);
    const duration = notes.length > 0 ?
      Math.max(...notes.map(n => n.t + (n.dur || 0.2))) : 0;

    return { header, notes, duration };
  }

  /**
   * Parse a single MIDI track.
   * @param {DataView} data
   * @param {number} start - Byte offset of track data.
   * @param {number} end - Byte offset of track end.
   * @param {number} ticksPerBeat
   * @returns {Array} Raw events with tick-based timing.
   */
  static _parseTrack(data, start, end, ticksPerBeat) {
    const events = [];
    let offset = start;
    let totalTicks = 0;
    let tempo = 500000; // microseconds per beat (120 BPM default)
    let totalTime = 0; // seconds
    let lastTempo = tempo;
    let lastTempoTick = 0;
    let lastTempoTime = 0;
    let runningStatus = 0;

    while (offset < end) {
      // Read delta time (VLQ)
      const vlq = MidiPlayer._readVLQ(data, offset);
      offset = vlq.offset;
      totalTicks += vlq.value;

      // Convert ticks to time using current tempo
      totalTime = lastTempoTime + ((totalTicks - lastTempoTick) / ticksPerBeat) * (tempo / 1000000);

      if (offset >= end) break;

      // Read status byte
      let status = data.getUint8(offset);

      // Handle running status
      if (status < 0x80) {
        status = runningStatus;
      } else {
        offset++;
        if (status < 0xF0) {
          runningStatus = status;
        }
      }

      const type = status & 0xF0;
      const ch = status & 0x0F;

      if (type === 0x90) {
        // Note On
        const note = data.getUint8(offset++);
        const vel = data.getUint8(offset++);
        events.push({
          type: vel > 0 ? 'noteOn' : 'noteOff',
          time: totalTime, ch, note,
          vel: vel / 127,
        });
      } else if (type === 0x80) {
        // Note Off
        const note = data.getUint8(offset++);
        offset++; // velocity (ignored)
        events.push({ type: 'noteOff', time: totalTime, ch, note });
      } else if (type === 0xA0) {
        // Aftertouch
        offset += 2;
      } else if (type === 0xB0) {
        // Control Change
        offset += 2;
      } else if (type === 0xC0) {
        // Program Change
        const program = data.getUint8(offset++);
        events.push({ type: 'programChange', time: totalTime, ch, program });
      } else if (type === 0xD0) {
        // Channel Pressure
        offset++;
      } else if (type === 0xE0) {
        // Pitch Bend
        offset += 2;
      } else if (status === 0xFF) {
        // Meta Event
        const metaType = data.getUint8(offset++);
        const metaVLQ = MidiPlayer._readVLQ(data, offset);
        offset = metaVLQ.offset;
        const metaLen = metaVLQ.value;

        if (metaType === 0x51 && metaLen === 3) {
          // Tempo change
          tempo = (data.getUint8(offset) << 16) |
                  (data.getUint8(offset + 1) << 8) |
                  data.getUint8(offset + 2);
          lastTempoTick = totalTicks;
          lastTempoTime = totalTime;
          lastTempo = tempo;
        } else if (metaType === 0x03) {
          // Track name
          let name = '';
          for (let i = 0; i < metaLen && offset + i < end; i++) {
            name += String.fromCharCode(data.getUint8(offset + i));
          }
          events.push({ type: 'trackName', time: totalTime, name });
        } else if (metaType === 0x2F) {
          // End of track
          offset += metaLen;
          break;
        }

        offset += metaLen;
      } else if (status === 0xF0 || status === 0xF7) {
        // SysEx
        const sysVLQ = MidiPlayer._readVLQ(data, offset);
        offset = sysVLQ.offset + sysVLQ.value;
      } else {
        // Unknown — skip
        offset++;
      }
    }

    return events;
  }

  /**
   * Build paired note events from raw note-on/note-off events.
   * @param {Array} rawEvents
   * @returns {Array} Note events with duration: [{ t, dur, note, vel, ch, inst }]
   */
  static _buildNoteEvents(rawEvents) {
    const notes = [];
    const openNotes = new Map(); // key -> { t, vel, ch }
    const programMap = new Map(); // ch -> program name

    // GM instrument families
    const GM_FAMILIES = [
      'piano', 'piano', 'piano', 'piano', 'piano', 'piano', 'piano', 'piano',
      'chromatic', 'chromatic', 'chromatic', 'chromatic', 'chromatic', 'chromatic', 'chromatic', 'chromatic',
      'organ', 'organ', 'organ', 'organ', 'organ', 'organ', 'organ', 'organ',
      'guitar', 'guitar', 'guitar', 'guitar', 'guitar', 'guitar', 'guitar', 'guitar',
      'bass', 'bass', 'bass', 'bass', 'bass', 'bass', 'bass', 'bass',
      'strings', 'strings', 'strings', 'strings', 'strings', 'strings', 'strings', 'strings',
      'ensemble', 'ensemble', 'ensemble', 'ensemble', 'ensemble', 'ensemble', 'ensemble', 'ensemble',
      'brass', 'brass', 'brass', 'brass', 'brass', 'brass', 'brass', 'brass',
      'reed', 'reed', 'reed', 'reed', 'reed', 'reed', 'reed', 'reed',
      'pipe', 'pipe', 'pipe', 'pipe', 'pipe', 'pipe', 'pipe', 'pipe',
      'synth-lead', 'synth-lead', 'synth-lead', 'synth-lead', 'synth-lead', 'synth-lead', 'synth-lead', 'synth-lead',
      'synth-pad', 'synth-pad', 'synth-pad', 'synth-pad', 'synth-pad', 'synth-pad', 'synth-pad', 'synth-pad',
      'fx', 'fx', 'fx', 'fx', 'fx', 'fx', 'fx', 'fx',
      'ethnic', 'ethnic', 'ethnic', 'ethnic', 'ethnic', 'ethnic', 'ethnic', 'ethnic',
      'percussion', 'percussion', 'percussion', 'percussion', 'percussion', 'percussion', 'percussion', 'percussion',
      'sfx', 'sfx', 'sfx', 'sfx', 'sfx', 'sfx', 'sfx', 'sfx',
    ];

    for (const ev of rawEvents) {
      if (ev.type === 'programChange') {
        programMap.set(ev.ch, GM_FAMILIES[ev.program] || 'piano');
      } else if (ev.type === 'noteOn') {
        const key = ev.ch * 128 + ev.note;
        openNotes.set(key, { t: ev.time, vel: ev.vel, ch: ev.ch, note: ev.note });
      } else if (ev.type === 'noteOff') {
        const key = ev.ch * 128 + ev.note;
        const open = openNotes.get(key);
        if (open) {
          const dur = Math.max(0.02, ev.time - open.t);
          const inst = ev.ch === 9 ? 'drums' : (programMap.get(ev.ch) || 'piano');
          notes.push({
            t: open.t,
            dur: dur,
            note: open.note,
            vel: open.vel,
            ch: open.ch,
            inst: inst,
          });
          openNotes.delete(key);
        }
      }
    }

    // Close any remaining open notes with a default duration
    for (const [key, open] of openNotes) {
      const inst = open.ch === 9 ? 'drums' : (programMap.get(open.ch) || 'piano');
      notes.push({
        t: open.t, dur: 0.5, note: open.note,
        vel: open.vel, ch: open.ch, inst: inst,
      });
    }

    notes.sort((a, b) => a.t - b.t);
    return notes;
  }

  // ──── Binary Helpers ────

  /**
   * Read a variable-length quantity.
   * @param {DataView} data
   * @param {number} offset
   * @returns {{ value: number, offset: number }}
   */
  static _readVLQ(data, offset) {
    let value = 0;
    let byte;
    do {
      if (offset >= data.byteLength) return { value, offset };
      byte = data.getUint8(offset++);
      value = (value << 7) | (byte & 0x7F);
    } while (byte & 0x80);
    return { value, offset };
  }

  /**
   * Read ASCII string from DataView.
   * @param {DataView} data
   * @param {number} offset
   * @param {number} length
   * @returns {string}
   */
  static _readStr(data, offset, length) {
    let s = '';
    for (let i = 0; i < length && offset + i < data.byteLength; i++) {
      s += String.fromCharCode(data.getUint8(offset + i));
    }
    return s;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MidiPlayer };
}
