/**
 * SpessaSynth Bridge — connects SpessaSynth SoundFont synthesizer
 * to the inthebeginning bounce game interfaces.
 *
 * SpessaSynth provides true FluidSynth-equivalent SoundFont synthesis
 * via AudioWorklet, rendering instrument samples from a GM SoundFont
 * (FluidR3_GM.sf2, 142MB) for album-quality audio output.
 *
 * Usage:
 *   const bridge = new SpessaBridge();
 *   await bridge.init('../../shared/audio/soundfonts/FluidR3_GM.sf2');
 *   bridge.programChange(0, 40);  // violin on channel 0
 *   bridge.noteOn(0, 60, 100);    // middle C, velocity 100
 *   bridge.noteOff(0, 60);
 *
 * @license Apache-2.0 (SpessaSynth by Spessasus)
 */

class SpessaBridge {
  constructor() {
    /** @type {Object|null} SpessaSynth WorkletSynthesizer instance. */
    this._synth = null;

    /** @type {AudioContext|null} */
    this._ctx = null;

    /** @type {boolean} Whether the synth is initialized and ready. */
    this.ready = false;

    /** @type {boolean} Whether SoundFont is loaded. */
    this.sf2Loaded = false;

    /** @type {string} Status message for UI display. */
    this.status = 'Not initialized';

    /** @type {number} SoundFont file size in bytes (for progress). */
    this._sf2Size = 0;

    /** @type {Function|null} Progress callback: (loaded, total) => void. */
    this.onProgress = null;

    /** @type {GainNode|null} Master gain for volume control. */
    this._masterGain = null;
  }

  /**
   * Initialize the synthesizer and load a SoundFont.
   *
   * Throws a descriptive Error if the SoundFont is missing, truncated, or
   * is an LFS pointer file (a known GitHub Pages LFS serving issue). Callers
   * should surface the error to the user rather than swallow it.
   *
   * @param {string} sf2Url - URL to the .sf2 SoundFont file.
   * @returns {Promise<boolean>} True if initialization succeeded.
   * @throws {Error} If the SF2 cannot be loaded or is invalid.
   */
  async init(sf2Url) {
    this.status = 'Loading SoundFont...';

    // Fetch SF2 with progress tracking — may throw for network errors
    // or return null if the server responded non-OK.
    const sf2Buffer = await this._fetchWithProgress(sf2Url);
    if (!sf2Buffer) {
      this.status = 'SoundFont download failed';
      throw new Error(`SoundFont fetch failed: ${sf2Url} (non-OK response)`);
    }

    // Validate the buffer: a real .sf2 begins with the 4-byte RIFF magic.
    // LFS pointer files begin with "version https://..." (first 4 bytes
    // "vers"), which produces SpessaSynth's cryptic "Expected riff got vers"
    // error. Detect that explicitly and surface a useful message.
    SpessaBridge._validateSoundFontBuffer(sf2Buffer, sf2Url);

    this.status = 'Initializing synthesizer...';

    // Create AudioContext
    this._ctx = new (window.AudioContext || window.webkitAudioContext)();

    // Load the AudioWorklet processor
    await this._ctx.audioWorklet.addModule('js/spessasynth_processor.min.js');

    // Create the WorkletSynthesizer from the bundled SpessaSynth
    const { WorkletSynthesizer } = window.SpessaSynth;
    this._synth = new WorkletSynthesizer(this._ctx);

    // Load the SoundFont — SpessaSynth may throw if the buffer is malformed
    // beyond the RIFF header check above.
    await this._synth.soundBankManager.addSoundBank(sf2Buffer, 'gm');
    await this._synth.isReady;

    // Connect synth output to destination through a gain node
    this._masterGain = this._ctx.createGain();
    this._masterGain.gain.value = 0.8;
    this._masterGain.connect(this._ctx.destination);
    this._synth.connect(this._masterGain);

    this.ready = true;
    this.sf2Loaded = true;
    this.status = 'Ready';
    console.log(`SpessaBridge: SoundFont loaded (${Math.round(sf2Buffer.byteLength / 1048576)} MB), synthesizer ready`);
    return true;
  }

  /**
   * Validate a downloaded SoundFont buffer. Throws with a specific,
   * actionable error message if the buffer is too small or missing the
   * RIFF magic header.
   * @param {ArrayBuffer} buffer
   * @param {string} url - Original URL, for the error message.
   */
  static _validateSoundFontBuffer(buffer, url) {
    const MIN_SF2_BYTES = 1000000; // Real soundfonts are always > 1 MB

    if (!buffer || buffer.byteLength < 4) {
      throw new Error(
        `SoundFont too small or empty: ${buffer ? buffer.byteLength : 0} bytes from ${url}. ` +
        `Expected a multi-megabyte .sf2 file.`
      );
    }

    // Check RIFF magic (first 4 bytes = "RIFF")
    const header = new Uint8Array(buffer, 0, 4);
    const magic = String.fromCharCode(header[0], header[1], header[2], header[3]);

    if (magic === 'vers') {
      // This is almost certainly an LFS pointer file.
      const pointerText = new TextDecoder().decode(
        new Uint8Array(buffer, 0, Math.min(200, buffer.byteLength))
      );
      throw new Error(
        `SoundFont at ${url} is a Git LFS pointer file, not the actual .sf2 binary. ` +
        `GitHub Pages is serving the pointer text instead of resolving it through LFS. ` +
        `Fix: enable Git LFS on the Pages repo and ensure LFS objects are pushed, ` +
        `or commit the .sf2 outside of LFS. Pointer content: ${pointerText.substring(0, 120)}...`
      );
    }

    if (magic !== 'RIFF') {
      throw new Error(
        `SoundFont at ${url} has invalid magic bytes: expected "RIFF" but got "${magic}". ` +
        `The file may be corrupted or the server returned HTML/JSON instead of the binary.`
      );
    }

    if (buffer.byteLength < MIN_SF2_BYTES) {
      throw new Error(
        `SoundFont at ${url} is suspiciously small: ${buffer.byteLength} bytes ` +
        `(expected > ${MIN_SF2_BYTES}). The server may be returning a truncated or ` +
        `placeholder file.`
      );
    }
  }

  /**
   * Fetch a file with progress tracking. Returns the ArrayBuffer on success,
   * or null if the response was not OK. Network errors propagate to the caller.
   * @param {string} url
   * @returns {Promise<ArrayBuffer|null>}
   */
  async _fetchWithProgress(url) {
    const resp = await fetch(url);
    if (!resp.ok) {
      console.warn(`SpessaBridge: fetch ${url} returned HTTP ${resp.status}`);
      return null;
    }

    const total = parseInt(resp.headers.get('content-length') || '0', 10);
    this._sf2Size = total;

    if (!resp.body || !total) {
      // No streaming — just get the buffer
      return resp.arrayBuffer();
    }

    // Stream with progress
    const reader = resp.body.getReader();
    const chunks = [];
    let loaded = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      loaded += value.length;
      if (this.onProgress) {
        this.onProgress(loaded, total);
      }
      this.status = `Loading SoundFont: ${Math.round(loaded / 1048576)}/${Math.round(total / 1048576)} MB`;
    }

    // Combine chunks into single ArrayBuffer
    const combined = new Uint8Array(loaded);
    let offset = 0;
    for (const chunk of chunks) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }
    return combined.buffer;
  }

  /**
   * Resume the AudioContext (required after user gesture).
   */
  async resume() {
    if (this._ctx && this._ctx.state === 'suspended') {
      await this._ctx.resume();
    }
  }

  /**
   * Send a note-on event.
   * @param {number} channel - MIDI channel (0-15).
   * @param {number} note - MIDI note number (0-127).
   * @param {number} velocity - Note velocity (0-127).
   */
  noteOn(channel, note, velocity) {
    if (!this._synth || !this.ready) return;
    this._synth.noteOn(channel, note, velocity);
  }

  /**
   * Send a note-off event.
   * @param {number} channel - MIDI channel (0-15).
   * @param {number} note - MIDI note number (0-127).
   */
  noteOff(channel, note) {
    if (!this._synth || !this.ready) return;
    this._synth.noteOff(channel, note);
  }

  /**
   * Change the instrument (GM program) on a channel.
   * @param {number} channel - MIDI channel (0-15).
   * @param {number} program - GM program number (0-127).
   */
  programChange(channel, program) {
    if (!this._synth || !this.ready) return;
    this._synth.programChange(channel, program);
  }

  /**
   * Set channel volume.
   * @param {number} channel - MIDI channel (0-15).
   * @param {number} volume - Volume (0-127).
   */
  setChannelVolume(channel, volume) {
    if (!this._synth || !this.ready) return;
    this._synth.controllerChange(channel, 7, volume); // CC7 = volume
  }

  /**
   * Set master volume.
   * @param {number} vol - Volume (0-1).
   */
  setVolume(vol) {
    if (this._synth && this.ready) {
      this._synth.setMainVolume(Math.round(vol * 127));
    }
  }

  /**
   * Send pitch bend.
   * @param {number} channel - MIDI channel (0-15).
   * @param {number} value - Pitch bend value (0-16383, center=8192).
   */
  pitchBend(channel, value) {
    if (!this._synth || !this.ready) return;
    // SpessaSynth uses MSB/LSB format
    const msb = (value >> 7) & 0x7f;
    const lsb = value & 0x7f;
    this._synth.pitchWheel(channel, msb, lsb);
  }

  /**
   * Stop all notes on all channels.
   */
  allNotesOff() {
    if (!this._synth || !this.ready) return;
    for (let ch = 0; ch < 16; ch++) {
      this._synth.controllerChange(ch, 123, 0); // CC123 = all notes off
    }
  }

  /**
   * Get the AudioContext (for sharing with other audio components).
   * @returns {AudioContext|null}
   */
  getAudioContext() {
    return this._ctx;
  }

  /**
   * Clean up resources.
   */
  destroy() {
    if (this._synth) {
      this.allNotesOff();
      this._synth = null;
    }
    this.ready = false;
    this.sf2Loaded = false;
    this.status = 'Destroyed';
  }
}
