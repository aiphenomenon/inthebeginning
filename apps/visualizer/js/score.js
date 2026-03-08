/**
 * Score JSON loader and time-based event lookup.
 *
 * Loads score JSON files describing note events with timing information.
 * Provides efficient binary search for finding active notes at any given time.
 */

/**
 * Represents a loaded score with tracks and events.
 */
class Score {
  /**
   * Create a Score instance.
   */
  constructor() {
    /** @type {string} */
    this.version = '1.0';

    /** @type {string} */
    this.mode = 'album';

    /** @type {number} */
    this.sampleRate = 44100;

    /** @type {number} Total duration in seconds */
    this.duration = 0;

    /** @type {number} Color shift interval in seconds */
    this.colorShiftInterval = 600;

    /** @type {Array<ScoreTrack>} */
    this.tracks = [];

    /** @type {string[]} */
    this.instruments = [];

    /** @type {Object<string, string>} instrument -> family */
    this.instrumentFamilies = {};

    /** @type {Array<ScoreEvent>} All events sorted by time */
    this.allEvents = [];
  }

  /**
   * Parse a JSON score object.
   * @param {Object} json - Parsed JSON score data.
   * @returns {Score} The populated Score instance.
   */
  static fromJSON(json) {
    const score = new Score();

    if (!json || typeof json !== 'object') {
      return score;
    }

    score.version = json.version || '1.0';
    score.mode = json.mode || 'album';
    score.sampleRate = json.sample_rate || 44100;
    score.duration = json.duration || 0;
    score.colorShiftInterval = json.color_shift_interval || 600;
    score.instruments = json.instruments || [];
    score.instrumentFamilies = json.instrument_families || {};

    if (Array.isArray(json.tracks)) {
      score.tracks = json.tracks.map((t, idx) => ScoreTrack.fromJSON(t, idx));
    }

    // Build flat sorted event list with absolute times
    score._buildEventIndex();

    return score;
  }

  /**
   * Build a flat, sorted index of all events across all tracks.
   * Events store absolute times (track start_time + event t).
   * @private
   */
  _buildEventIndex() {
    this.allEvents = [];
    for (const track of this.tracks) {
      for (const ev of track.events) {
        this.allEvents.push({
          absTime: track.startTime + ev.t,
          endTime: track.startTime + ev.t + ev.dur,
          note: ev.note,
          inst: ev.inst,
          vel: ev.vel,
          bend: ev.bend || 0,
          ch: ev.ch,
          trackIndex: track.trackNum - 1
        });
      }
    }
    // Sort by absolute start time
    this.allEvents.sort((a, b) => a.absTime - b.absTime);
  }

  /**
   * Find all events active at a given time using binary search.
   * An event is active if absTime <= time < endTime.
   * @param {number} time - Current playback time in seconds.
   * @returns {Array<{note: number, inst: string, vel: number, bend: number, ch: number}>}
   */
  getActiveEvents(time) {
    const active = [];

    if (this.allEvents.length === 0) return active;

    // Binary search for the first event that could be active.
    // We need events where absTime <= time, so find the rightmost event
    // with absTime <= time, then scan backwards and forwards.
    let lo = 0;
    let hi = this.allEvents.length - 1;

    // Find insertion point for time
    while (lo <= hi) {
      const mid = (lo + hi) >>> 1;
      if (this.allEvents[mid].absTime <= time) {
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    // lo is now the first event with absTime > time
    // Check events from 0 to lo-1 that might still be active (endTime > time)

    // Optimization: only look back a reasonable window. Most notes are < 30s.
    const scanStart = Math.max(0, lo - this.allEvents.length); // scan all for correctness
    for (let i = 0; i < lo; i++) {
      const ev = this.allEvents[i];
      if (ev.endTime > time) {
        active.push({
          note: ev.note,
          inst: ev.inst,
          vel: ev.vel,
          bend: ev.bend,
          ch: ev.ch
        });
      }
    }

    return active;
  }

  /**
   * Get the track that contains a given time.
   * @param {number} time - Current time in seconds.
   * @returns {ScoreTrack|null} The track, or null if no track contains this time.
   */
  getTrackAtTime(time) {
    for (const track of this.tracks) {
      if (time >= track.startTime && time < track.startTime + track.duration) {
        return track;
      }
    }
    // If past all tracks, return last track
    if (this.tracks.length > 0 && time >= this.tracks[this.tracks.length - 1].startTime) {
      return this.tracks[this.tracks.length - 1];
    }
    return null;
  }

  /**
   * Get the track index at a given time.
   * @param {number} time - Current time in seconds.
   * @returns {number} Track index (0-based), or -1.
   */
  getTrackIndexAtTime(time) {
    const track = this.getTrackAtTime(time);
    return track ? track.trackNum - 1 : -1;
  }

  /**
   * Get the start time of a track by index.
   * @param {number} index - Track index (0-based).
   * @returns {number} Start time in seconds.
   */
  getTrackStartTime(index) {
    if (index >= 0 && index < this.tracks.length) {
      return this.tracks[index].startTime;
    }
    return 0;
  }
}

/**
 * Represents a single track within a score.
 */
class ScoreTrack {
  constructor() {
    /** @type {number} 1-based track number */
    this.trackNum = 1;

    /** @type {string} */
    this.title = '';

    /** @type {number} Start time in seconds (absolute) */
    this.startTime = 0;

    /** @type {number} Duration in seconds */
    this.duration = 0;

    /** @type {string} Audio file name */
    this.audioFile = '';

    /** @type {Array<{t: number, dur: number, note: number, inst: string, vel: number, bend: number, ch: number}>} */
    this.events = [];
  }

  /**
   * Parse a track from JSON.
   * @param {Object} json - Track JSON object.
   * @param {number} index - Track index (0-based).
   * @returns {ScoreTrack}
   */
  static fromJSON(json, index) {
    const track = new ScoreTrack();
    track.trackNum = json.track_num || (index + 1);
    track.title = json.title || `Track ${track.trackNum}`;
    track.startTime = json.start_time || 0;
    track.duration = json.duration || 0;
    track.audioFile = json.audio_file || '';
    track.events = (json.events || []).map(e => ({
      t: e.t || 0,
      dur: e.dur || 0,
      note: e.note || 60,
      inst: e.inst || 'piano',
      vel: e.vel !== undefined ? e.vel : 0.5,
      bend: e.bend || 0,
      ch: e.ch !== undefined ? e.ch : 0
    }));
    return track;
  }
}

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Score, ScoreTrack };
}
