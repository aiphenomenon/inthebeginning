/**
 * Tests for MidiFilePlayer — MIDI playback via SynthEngine + Web Worker.
 *
 * Node.js test runner: node --test test/test_midi_player.js
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

// Mock SynthEngine for testing (no AudioContext in Node.js)
class MockSynthEngine {
  constructor() {
    this.ctx = null;
    this._mutation = { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' };
    this._voices = new Map();
    this._playedNotes = [];
  }
  init() { this.ctx = { currentTime: 0 }; }
  async resume() {}
  setMutation(m) { this._mutation = m; }
  setVolume() {}
  playNote(note, delay) { this._playedNotes.push({ note, delay }); return 0; }
  stopAll() { this._voices.clear(); this._playedNotes = []; }
  destroy() {}
}

// Provide mock SynthEngine
global.SynthEngine = MockSynthEngine;

const { MidiFilePlayer } = require('../js/midi-player.js');

describe('MidiFilePlayer constructor', () => {
  it('should create with a SynthEngine', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    assert.ok(player);
    assert.equal(player.synth, synth);
    assert.equal(player.isPlaying, false);
    player.destroy();
  });

  it('should start with empty notes', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    assert.equal(player._notes.length, 0);
    assert.equal(player._duration, 0);
    player.destroy();
  });

  it('should have default mutation', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    assert.equal(player._mutation.pitchShift, 0);
    assert.equal(player._mutation.tempoMult, 1.0);
    player.destroy();
  });
});

describe('MidiFilePlayer.setMutation', () => {
  it('should update mutation and pass to synth', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player.setMutation({ pitchShift: 12, tempoMult: 0.8, reverb: 0.6, filter: 'lowpass' });
    assert.equal(player._mutation.pitchShift, 12);
    assert.equal(synth._mutation.pitchShift, 12);
    player.destroy();
  });

  it('should handle null mutation', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player.setMutation(null);
    assert.equal(player._mutation.pitchShift, 0);
    player.destroy();
  });
});

describe('MidiFilePlayer.getCurrentTime', () => {
  it('should return 0 when not playing', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    assert.equal(player.getCurrentTime(), 0);
    player.destroy();
  });
});

describe('MidiFilePlayer.getDuration', () => {
  it('should return 0 when no MIDI loaded', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    assert.equal(player.getDuration(), 0);
    player.destroy();
  });
});

describe('MidiFilePlayer.getTrackInfo', () => {
  it('should return basic info when no MIDI loaded', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    const info = player.getTrackInfo();
    assert.equal(info.noteCount, 0);
    assert.equal(info.duration, 0);
    player.destroy();
  });

  it('should include custom trackInfo', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player.trackInfo = { name: 'Test', composer: 'Bach' };
    const info = player.getTrackInfo();
    assert.equal(info.name, 'Test');
    assert.equal(info.composer, 'Bach');
    player.destroy();
  });
});

describe('MidiFilePlayer.stop', () => {
  it('should reset state', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player._currentTime = 30;
    player._nextNote = 10;
    player.isPlaying = true;
    player.stop();
    assert.equal(player.isPlaying, false);
    assert.equal(player._currentTime, 0);
    assert.equal(player._nextNote, 0);
    player.destroy();
  });
});

describe('MidiFilePlayer.seek', () => {
  it('should clamp seek to 0 and duration', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player._duration = 60;
    player._notes = [{ t: 10 }, { t: 20 }, { t: 30 }, { t: 40 }, { t: 50 }];
    player.seek(-5);
    assert.equal(player._currentTime, 0);
    player.seek(100);
    assert.equal(player._currentTime, 60);
    player.destroy();
  });

  it('should find correct next note index after seek', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player._duration = 60;
    player._notes = [
      { t: 5 }, { t: 10 }, { t: 20 }, { t: 30 }, { t: 50 },
    ];
    player.seek(15);
    assert.equal(player._currentTime, 15);
    assert.equal(player._nextNote, 2); // t=20 is next
    player.destroy();
  });
});

describe('MidiFilePlayer.destroy', () => {
  it('should stop playback and clean up', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player.destroy();
    assert.equal(player.isPlaying, false);
    assert.equal(player._worker, null);
    assert.equal(player._pending.size, 0);
  });
});

describe('MidiFilePlayer callback setup', () => {
  it('should accept onNoteEvent callback', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    let called = false;
    player.onNoteEvent = () => { called = true; };
    assert.ok(player.onNoteEvent);
    player.destroy();
  });

  it('should accept onTrackEnd callback', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    let called = false;
    player.onTrackEnd = () => { called = true; };
    assert.ok(player.onTrackEnd);
    player.destroy();
  });

  it('should accept onTimeUpdate callback', () => {
    const synth = new MockSynthEngine();
    const player = new MidiFilePlayer(synth, { workerUrl: '/nonexistent' });
    player.onTimeUpdate = () => {};
    assert.ok(player.onTimeUpdate);
    player.destroy();
  });
});

describe('MIDI_MUTATIONS (imported from app.js context)', () => {
  it('should have 16 mutation presets', () => {
    // Load from the app module to test
    const { MIDI_MUTATIONS } = require('../js/app.js');
    assert.equal(MIDI_MUTATIONS.length, 16);
  });

  it('should have name, pitchShift, tempoMult, reverb, filter for each', () => {
    const { MIDI_MUTATIONS } = require('../js/app.js');
    for (const m of MIDI_MUTATIONS) {
      assert.ok(typeof m.name === 'string');
      assert.ok(typeof m.pitchShift === 'number');
      assert.ok(typeof m.tempoMult === 'number');
      assert.ok(typeof m.reverb === 'number');
      assert.ok(typeof m.filter === 'string');
    }
  });

  it('should have Original as first preset (no mutation)', () => {
    const { MIDI_MUTATIONS } = require('../js/app.js');
    assert.equal(MIDI_MUTATIONS[0].name, 'Original');
    assert.equal(MIDI_MUTATIONS[0].pitchShift, 0);
    assert.equal(MIDI_MUTATIONS[0].tempoMult, 1.0);
    assert.equal(MIDI_MUTATIONS[0].reverb, 0);
    assert.equal(MIDI_MUTATIONS[0].filter, 'none');
  });

  it('should have unique names for all presets', () => {
    const { MIDI_MUTATIONS } = require('../js/app.js');
    const names = MIDI_MUTATIONS.map(m => m.name);
    assert.equal(new Set(names).size, 16);
  });
});
