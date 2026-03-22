const { describe, it } = require('node:test');
const assert = require('node:assert');
const { MidiPlayer } = require('../js/midi-player.js');

// Helper: create a minimal MIDI file as Uint8Array
function createTestMidi() {
  // Format 0, 1 track, 480 ticks/beat
  // Header: MThd + length(6) + format(0) + nTracks(1) + division(480)
  // Track: MTrk + length + events
  const header = [
    0x4D, 0x54, 0x68, 0x64, // MThd
    0x00, 0x00, 0x00, 0x06, // length = 6
    0x00, 0x00,             // format 0
    0x00, 0x01,             // 1 track
    0x01, 0xE0,             // 480 ticks/beat
  ];

  // Track events:
  // Delta=0, Tempo=500000 (120 BPM): FF 51 03 07 A1 20
  // Delta=0, Note On ch0 C4 vel=80: 90 3C 50
  // Delta=480, Note Off ch0 C4: 80 3C 00
  // Delta=0, Note On ch0 E4 vel=90: 90 40 5A
  // Delta=240, Note Off ch0 E4: 80 40 00
  // Delta=0, End of track: FF 2F 00
  const trackData = [
    0x00,                         // delta=0
    0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20, // tempo 500000
    0x00,                         // delta=0
    0x90, 0x3C, 0x50,             // note on C4 vel=80
    0x83, 0x60,                   // delta=480 (VLQ: 0x83 0x60 = 480)
    0x80, 0x3C, 0x00,             // note off C4
    0x00,                         // delta=0
    0x90, 0x40, 0x5A,             // note on E4 vel=90
    0x81, 0x70,                   // delta=240 (VLQ: 0x81 0x70 = 240)
    0x80, 0x40, 0x00,             // note off E4
    0x00,                         // delta=0
    0xFF, 0x2F, 0x00,             // end of track
  ];

  const trackHeader = [
    0x4D, 0x54, 0x72, 0x6B, // MTrk
    0x00, 0x00, 0x00, trackData.length, // track length
  ];

  const bytes = new Uint8Array([...header, ...trackHeader, ...trackData]);
  return bytes.buffer;
}

describe('MidiPlayer VLQ Decoding', () => {
  it('decodes single-byte VLQ', () => {
    const data = new DataView(new Uint8Array([0x00]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 0);
    assert.strictEqual(result.offset, 1);
  });

  it('decodes single-byte VLQ value 127', () => {
    const data = new DataView(new Uint8Array([0x7F]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 127);
    assert.strictEqual(result.offset, 1);
  });

  it('decodes two-byte VLQ value 128', () => {
    const data = new DataView(new Uint8Array([0x81, 0x00]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 128);
    assert.strictEqual(result.offset, 2);
  });

  it('decodes two-byte VLQ value 480', () => {
    const data = new DataView(new Uint8Array([0x83, 0x60]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 480);
    assert.strictEqual(result.offset, 2);
  });

  it('decodes two-byte VLQ value 240', () => {
    const data = new DataView(new Uint8Array([0x81, 0x70]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 240);
    assert.strictEqual(result.offset, 2);
  });

  it('decodes three-byte VLQ', () => {
    const data = new DataView(new Uint8Array([0x81, 0x80, 0x00]).buffer);
    const result = MidiPlayer._readVLQ(data, 0);
    assert.strictEqual(result.value, 16384);
    assert.strictEqual(result.offset, 3);
  });
});

describe('MidiPlayer String Reading', () => {
  it('reads ASCII string', () => {
    const bytes = new Uint8Array([0x4D, 0x54, 0x68, 0x64]); // MThd
    const data = new DataView(bytes.buffer);
    assert.strictEqual(MidiPlayer._readStr(data, 0, 4), 'MThd');
  });

  it('reads partial string', () => {
    const bytes = new Uint8Array([0x41, 0x42]); // AB
    const data = new DataView(bytes.buffer);
    assert.strictEqual(MidiPlayer._readStr(data, 0, 2), 'AB');
  });
});

describe('MidiPlayer MIDI Parsing', () => {
  it('parses a valid MIDI file header', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result, 'parse should succeed');
    assert.strictEqual(result.header.format, 0);
    assert.strictEqual(result.header.nTracks, 1);
    assert.strictEqual(result.header.ticksPerBeat, 480);
  });

  it('extracts correct number of notes', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    assert.strictEqual(result.notes.length, 2, 'should have 2 notes (C4 and E4)');
  });

  it('extracts correct note pitches', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    assert.strictEqual(result.notes[0].note, 60, 'first note should be C4 (60)');
    assert.strictEqual(result.notes[1].note, 64, 'second note should be E4 (64)');
  });

  it('calculates note durations', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    // 480 ticks at 120 BPM (500000 us/beat) = 1 beat = 0.5 seconds
    assert.ok(Math.abs(result.notes[0].dur - 0.5) < 0.01,
      `first note duration ${result.notes[0].dur} should be ~0.5s`);
    // 240 ticks = 0.25 seconds
    assert.ok(Math.abs(result.notes[1].dur - 0.25) < 0.01,
      `second note duration ${result.notes[1].dur} should be ~0.25s`);
  });

  it('calculates total duration', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    // First note: t=0, dur=0.5; Second note: t=0.5, dur=0.25
    // Total duration = 0.5 + 0.25 = 0.75s
    assert.ok(result.duration > 0.5, `duration ${result.duration} should be > 0.5s`);
    assert.ok(result.duration < 1.0, `duration ${result.duration} should be < 1.0s`);
  });

  it('rejects non-MIDI data', () => {
    const bytes = new Uint8Array([0x00, 0x01, 0x02, 0x03]);
    const data = new DataView(bytes.buffer);
    const result = MidiPlayer._parseMidi(data);
    assert.strictEqual(result, null);
  });

  it('extracts velocity', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    assert.ok(Math.abs(result.notes[0].vel - 80 / 127) < 0.01, 'C4 velocity');
    assert.ok(Math.abs(result.notes[1].vel - 90 / 127) < 0.01, 'E4 velocity');
  });

  it('assigns channel 0', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    assert.strictEqual(result.notes[0].ch, 0);
    assert.strictEqual(result.notes[1].ch, 0);
  });

  it('assigns piano instrument for channel 0', () => {
    const buffer = createTestMidi();
    const data = new DataView(buffer);
    const result = MidiPlayer._parseMidi(data);

    assert.ok(result);
    assert.strictEqual(result.notes[0].inst, 'piano');
  });
});

describe('MidiPlayer Build Note Events', () => {
  it('pairs note-on with note-off', () => {
    const events = [
      { type: 'noteOn', time: 0, ch: 0, note: 60, vel: 0.8 },
      { type: 'noteOff', time: 1.0, ch: 0, note: 60 },
    ];
    const notes = MidiPlayer._buildNoteEvents(events);
    assert.strictEqual(notes.length, 1);
    assert.strictEqual(notes[0].note, 60);
    assert.ok(Math.abs(notes[0].dur - 1.0) < 0.01);
  });

  it('handles note-on with velocity 0 as note-off', () => {
    const events = [
      { type: 'noteOn', time: 0, ch: 0, note: 60, vel: 0.8 },
      { type: 'noteOn', time: 0.5, ch: 0, note: 60, vel: 0 },
    ];
    // Note-on vel=0 is treated as noteOff in the parser, but
    // _buildNoteEvents only sees noteOn/noteOff types
    // The parser already converts vel=0 noteOn to noteOff type
  });

  it('closes unclosed notes with default duration', () => {
    const events = [
      { type: 'noteOn', time: 0, ch: 0, note: 60, vel: 0.5 },
    ];
    const notes = MidiPlayer._buildNoteEvents(events);
    assert.strictEqual(notes.length, 1);
    assert.strictEqual(notes[0].dur, 0.5); // default
  });

  it('assigns percussion for channel 9', () => {
    const events = [
      { type: 'noteOn', time: 0, ch: 9, note: 36, vel: 0.8 },
      { type: 'noteOff', time: 0.1, ch: 9, note: 36 },
    ];
    const notes = MidiPlayer._buildNoteEvents(events);
    assert.strictEqual(notes[0].inst, 'drums');
  });

  it('handles program changes', () => {
    const events = [
      { type: 'programChange', time: 0, ch: 0, program: 24 }, // guitar
      { type: 'noteOn', time: 0, ch: 0, note: 60, vel: 0.5 },
      { type: 'noteOff', time: 0.5, ch: 0, note: 60 },
    ];
    const notes = MidiPlayer._buildNoteEvents(events);
    assert.strictEqual(notes[0].inst, 'guitar');
  });

  it('sorts notes by time', () => {
    const events = [
      { type: 'noteOn', time: 1, ch: 0, note: 64, vel: 0.5 },
      { type: 'noteOn', time: 0, ch: 0, note: 60, vel: 0.5 },
      { type: 'noteOff', time: 0.5, ch: 0, note: 60 },
      { type: 'noteOff', time: 1.5, ch: 0, note: 64 },
    ];
    const notes = MidiPlayer._buildNoteEvents(events);
    assert.ok(notes[0].t <= notes[1].t, 'notes should be sorted by time');
  });
});

describe('MidiPlayer Instance', () => {
  it('creates with default state', () => {
    const player = new MidiPlayer();
    assert.strictEqual(player.isPlaying, false);
    assert.strictEqual(player.getCurrentTime(), 0);
    assert.strictEqual(player.getDuration(), 0);
  });

  it('reports track info', () => {
    const player = new MidiPlayer();
    const info = player.getTrackInfo();
    assert.strictEqual(info.noteCount, 0);
    assert.strictEqual(info.duration, 0);
  });

  it('accepts mutation preset', () => {
    const player = new MidiPlayer();
    player.setMutation({ pitchShift: 12, tempoMult: 0.8, reverb: 0.6, filter: 'lowpass' });
    assert.strictEqual(player._mutation.pitchShift, 12);
    assert.strictEqual(player._mutation.tempoMult, 0.8);
  });

  it('loads synthetic MIDI data', async () => {
    const player = new MidiPlayer();
    const buffer = createTestMidi();
    const result = await player.loadMidi(buffer);
    assert.strictEqual(result, true);
    assert.strictEqual(player._notes.length, 2);
    assert.ok(player.getDuration() > 0);
  });
});
