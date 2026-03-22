/**
 * Unit tests for score.js -- Score JSON loader and event lookup.
 * Run with: node --test test/test_score.js
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { Score, ScoreTrack } = require('../js/score.js');

const SAMPLE_SCORE = {
  version: '1.0',
  mode: 'album',
  sample_rate: 44100,
  duration: 500.0,
  color_shift_interval: 600,
  tracks: [
    {
      track_num: 1,
      title: 'Genesis',
      start_time: 0.0,
      duration: 250.0,
      audio_file: 'genesis.mp3',
      events: [
        { t: 0.5, dur: 1.2, note: 64, inst: 'violin', vel: 0.8, bend: 0.0, ch: 3 },
        { t: 0.5, dur: 0.8, note: 52, inst: 'piano', vel: 0.6, bend: 0.0, ch: 7 },
        { t: 2.0, dur: 0.5, note: 72, inst: 'flute', vel: 0.9, bend: 0.1, ch: 5 },
        { t: 100.0, dur: 2.0, note: 48, inst: 'cello', vel: 0.7, bend: 0.0, ch: 2 }
      ]
    },
    {
      track_num: 2,
      title: 'Expansion',
      start_time: 250.0,
      duration: 250.0,
      audio_file: 'expansion.mp3',
      events: [
        { t: 1.0, dur: 1.5, note: 60, inst: 'piano', vel: 0.5, bend: 0.0, ch: 7 },
        { t: 3.0, dur: 0.3, note: 80, inst: 'trumpet', vel: 1.0, bend: 0.0, ch: 10 }
      ]
    }
  ],
  instruments: ['violin', 'piano', 'flute', 'cello', 'trumpet'],
  instrument_families: {
    violin: 'strings',
    piano: 'keys',
    flute: 'winds',
    cello: 'strings',
    trumpet: 'winds'
  }
};

describe('Score.fromJSON', () => {
  it('should parse a valid score JSON', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    assert.equal(score.version, '1.0');
    assert.equal(score.mode, 'album');
    assert.equal(score.duration, 500.0);
    assert.equal(score.colorShiftInterval, 600);
    assert.equal(score.tracks.length, 2);
    assert.equal(score.instruments.length, 5);
  });

  it('should parse track details', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const track1 = score.tracks[0];
    assert.equal(track1.trackNum, 1);
    assert.equal(track1.title, 'Genesis');
    assert.equal(track1.startTime, 0.0);
    assert.equal(track1.duration, 250.0);
    assert.equal(track1.audioFile, 'genesis.mp3');
    assert.equal(track1.events.length, 4);
  });

  it('should parse event details', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const ev = score.tracks[0].events[0];
    assert.equal(ev.t, 0.5);
    assert.equal(ev.dur, 1.2);
    assert.equal(ev.note, 64);
    assert.equal(ev.inst, 'violin');
    assert.equal(ev.vel, 0.8);
    assert.equal(ev.bend, 0.0);
    assert.equal(ev.ch, 3);
  });

  it('should handle empty JSON gracefully', () => {
    const score = Score.fromJSON({});
    assert.equal(score.tracks.length, 0);
    assert.equal(score.duration, 0);
    assert.equal(score.instruments.length, 0);
  });

  it('should handle null gracefully', () => {
    const score = Score.fromJSON(null);
    assert.equal(score.tracks.length, 0);
  });

  it('should build a sorted event index', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // All events across both tracks should be sorted by absolute time
    assert.ok(score.allEvents.length > 0);
    for (let i = 1; i < score.allEvents.length; i++) {
      assert.ok(score.allEvents[i].absTime >= score.allEvents[i - 1].absTime,
        `Events not sorted at index ${i}`);
    }
  });

  it('should compute absolute times from track start + event t', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // Track 2 starts at 250.0, first event at t=1.0 -> absTime=251.0
    const track2Events = score.allEvents.filter(e => e.trackIndex === 1);
    assert.ok(track2Events.length >= 1);
    assert.equal(track2Events[0].absTime, 251.0);
  });
});

describe('Score.getActiveEvents', () => {
  it('should find events active at a given time', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // At t=0.8, violin (0.5-1.7) and piano (0.5-1.3) should be active
    const events = score.getActiveEvents(0.8);
    assert.equal(events.length, 2);
    const instruments = events.map(e => e.inst).sort();
    assert.deepEqual(instruments, ['piano', 'violin']);
  });

  it('should not return events before their start', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const events = score.getActiveEvents(0.0);
    assert.equal(events.length, 0);
  });

  it('should not return events after their end', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // Violin event: t=0.5, dur=1.2 -> ends at 1.7
    const events = score.getActiveEvents(1.8);
    // Only flute (2.0-2.5) not yet, piano ended at 1.3
    assert.equal(events.length, 0);
  });

  it('should find events in later tracks', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // Track 2 piano: absTime=251.0, dur=1.5 -> active at 251.5
    const events = score.getActiveEvents(251.5);
    assert.ok(events.length >= 1);
    assert.ok(events.some(e => e.inst === 'piano'));
  });

  it('should return empty for time beyond all events', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const events = score.getActiveEvents(999.0);
    assert.equal(events.length, 0);
  });

  it('should return empty for empty score', () => {
    const score = Score.fromJSON({});
    const events = score.getActiveEvents(1.0);
    assert.equal(events.length, 0);
  });

  it('should include bend information', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    // Flute at t=2.0 has bend=0.1
    const events = score.getActiveEvents(2.1);
    const flute = events.find(e => e.inst === 'flute');
    assert.ok(flute, 'Flute should be active at t=2.1');
    assert.equal(flute.bend, 0.1);
  });
});

describe('Score.getTrackAtTime', () => {
  it('should return track 1 for time in first track', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const track = score.getTrackAtTime(100.0);
    assert.ok(track);
    assert.equal(track.trackNum, 1);
  });

  it('should return track 2 for time in second track', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const track = score.getTrackAtTime(300.0);
    assert.ok(track);
    assert.equal(track.trackNum, 2);
  });

  it('should return last track for time past all tracks', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    const track = score.getTrackAtTime(600.0);
    assert.ok(track);
    assert.equal(track.trackNum, 2);
  });

  it('should return null for empty score', () => {
    const score = Score.fromJSON({});
    const track = score.getTrackAtTime(1.0);
    assert.equal(track, null);
  });
});

describe('Score.getTrackIndexAtTime', () => {
  it('should return 0 for time in first track', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    assert.equal(score.getTrackIndexAtTime(10.0), 0);
  });

  it('should return 1 for time in second track', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    assert.equal(score.getTrackIndexAtTime(260.0), 1);
  });

  it('should return -1 for empty score', () => {
    const score = Score.fromJSON({});
    assert.equal(score.getTrackIndexAtTime(1.0), -1);
  });
});

describe('Score.getTrackStartTime', () => {
  it('should return start time for valid index', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    assert.equal(score.getTrackStartTime(0), 0.0);
    assert.equal(score.getTrackStartTime(1), 250.0);
  });

  it('should return 0 for invalid index', () => {
    const score = Score.fromJSON(SAMPLE_SCORE);
    assert.equal(score.getTrackStartTime(-1), 0);
    assert.equal(score.getTrackStartTime(99), 0);
  });
});

describe('ScoreTrack.fromJSON', () => {
  it('should provide defaults for missing fields', () => {
    const track = ScoreTrack.fromJSON({}, 0);
    assert.equal(track.trackNum, 1);
    assert.equal(track.title, 'Track 1');
    assert.equal(track.startTime, 0);
    assert.equal(track.duration, 0);
    assert.equal(track.audioFile, '');
    assert.equal(track.events.length, 0);
  });

  it('should provide defaults for event fields', () => {
    const track = ScoreTrack.fromJSON({
      events: [{ t: 1.0 }]
    }, 0);
    assert.equal(track.events[0].dur, 0);
    assert.equal(track.events[0].note, 60);
    assert.equal(track.events[0].inst, 'piano');
    assert.equal(track.events[0].vel, 0.5);
    assert.equal(track.events[0].bend, 0);
    assert.equal(track.events[0].ch, 0);
  });
});

// --- V3 compressed format tests ---

const SAMPLE_COMPRESSED_V3_ALBUM = {
  format: 'compressed_v3',
  version: '3.0',
  total_duration: 720.0,
  sample_rate: 44100,
  color_shift_interval: 300,
  instruments: ['piano', 'violin', 'cello'],
  instrument_families: { piano: 'keys', violin: 'strings', cello: 'strings' },
  tracks: [
    {
      track_num: 1,
      title: 'Singularity',
      start_time: 0.0,
      duration: 360.0,
      audio_file: 'singularity.mp3',
      file: 'singularity_notes.json'
    },
    {
      track_num: 2,
      title: 'Nucleosynthesis',
      start_time: 360.0,
      duration: 360.0,
      audio_file: 'nucleosynthesis.mp3',
      file: 'nucleosynthesis_notes.json'
    }
  ]
};

const SAMPLE_COMPRESSED_V3_SINGLE = {
  title: 'Compressed Track',
  version: '3.0',
  legend: {
    instruments: {
      '0': 'piano',
      '1': 'violin',
      '2': 'flute'
    }
  },
  events: [
    // [t, dur, note, inst_index, vel, ch]
    [0.5, 1.0, 60, 0, 0.8, 1],
    [1.0, 0.5, 67, 1, 0.6, 2],
    [2.0, 1.5, 72, 2, 0.9, 5],
    [5.0, 2.0, 48, 0, 0.7, 1]
  ]
};

describe('V3 compressed album format', () => {
  it('should parse compressed album metadata', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    assert.equal(score.version, '3.0');
    assert.equal(score.colorShiftInterval, 300);
    assert.equal(score.instruments.length, 3);
    assert.deepEqual(score.instrumentFamilies, {
      piano: 'keys', violin: 'strings', cello: 'strings'
    });
  });

  it('should set mode to album', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    assert.equal(score.mode, 'album');
  });

  it('should create tracks with noteFile property', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    assert.equal(score.tracks.length, 2);
    assert.equal(score.tracks[0].noteFile, 'singularity_notes.json');
    assert.equal(score.tracks[1].noteFile, 'nucleosynthesis_notes.json');
    assert.equal(score.tracks[0].title, 'Singularity');
    assert.equal(score.tracks[0].audioFile, 'singularity.mp3');
    assert.equal(score.tracks[0].startTime, 0.0);
    assert.equal(score.tracks[1].startTime, 360.0);
    assert.equal(score.tracks[1].duration, 360.0);
  });

  it('should handle total_duration', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    assert.equal(score.duration, 720.0);
  });

  it('should have empty events initially (lazy loading)', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    assert.equal(score.tracks[0].events.length, 0);
    assert.equal(score.tracks[1].events.length, 0);
    assert.equal(score.allEvents.length, 0);
  });
});

describe('V3 single-track compressed format', () => {
  it('should parse compressed events with legend', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_SINGLE);
    assert.equal(score.tracks.length, 1);
    assert.equal(score.tracks[0].events.length, 4);
    assert.equal(score.tracks[0].title, 'Compressed Track');
  });

  it('should expand instrument indices to names', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_SINGLE);
    const events = score.tracks[0].events;
    assert.equal(events[0].inst, 'piano');
    assert.equal(events[1].inst, 'violin');
    assert.equal(events[2].inst, 'flute');
    assert.equal(events[3].inst, 'piano');
  });

  it('should calculate duration from last event', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_SINGLE);
    // Last event: t=5.0, dur=2.0 -> duration = 7.0
    assert.equal(score.tracks[0].duration, 7.0);
    assert.equal(score.duration, 7.0);
  });

  it('should set mode to single', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_SINGLE);
    assert.equal(score.mode, 'single');
  });

  it('should make getActiveEvents work with expanded events', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_SINGLE);
    // At t=0.8: piano (0.5-1.5) active
    const at08 = score.getActiveEvents(0.8);
    assert.equal(at08.length, 1);
    assert.equal(at08[0].inst, 'piano');
    assert.equal(at08[0].note, 60);

    // At t=1.0: piano (0.5-1.5) and violin (1.0-1.5) both active
    // Binary search finds absTime <= 1.0, violin starts exactly at 1.0
    const at10 = score.getActiveEvents(1.01);
    const insts = at10.map(e => e.inst).sort();
    assert.deepEqual(insts, ['piano', 'violin']);

    // At t=5.5: only last piano (5.0-7.0)
    const at55 = score.getActiveEvents(5.5);
    assert.equal(at55.length, 1);
    assert.equal(at55[0].inst, 'piano');
    assert.equal(at55[0].note, 48);
  });
});

describe('Score._buildEventIndexForTrack', () => {
  it('should build index with local times (startTime = 0)', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    // Simulate loading events into track 1 (startTime=360)
    score.tracks[1].events = [
      { t: 1.0, dur: 0.5, note: 60, inst: 'piano', vel: 0.8, bend: 0, ch: 1 },
      { t: 3.0, dur: 1.0, note: 72, inst: 'violin', vel: 0.6, bend: 0, ch: 2 }
    ];
    score._buildEventIndexForTrack(1);

    // Events should use local times (t values directly), not absolute
    assert.equal(score.allEvents.length, 2);
    assert.equal(score.allEvents[0].absTime, 1.0);
    assert.equal(score.allEvents[0].endTime, 1.5);
    assert.equal(score.allEvents[1].absTime, 3.0);
    assert.equal(score.allEvents[1].endTime, 4.0);
    assert.equal(score.allEvents[0].trackIndex, 1);
  });

  it('should make getActiveEvents work with local times after per-track build', () => {
    const score = Score.fromJSON(SAMPLE_COMPRESSED_V3_ALBUM);
    score.tracks[0].events = [
      { t: 0.5, dur: 1.0, note: 64, inst: 'cello', vel: 0.9, bend: 0, ch: 3 },
      { t: 2.0, dur: 0.8, note: 55, inst: 'violin', vel: 0.7, bend: 0.1, ch: 4 }
    ];
    score._buildEventIndexForTrack(0);

    // Query at local time 0.8 should find cello (0.5-1.5)
    const events = score.getActiveEvents(0.8);
    assert.equal(events.length, 1);
    assert.equal(events[0].inst, 'cello');
    assert.equal(events[0].bend, 0);

    // Query at local time 2.3 should find violin (2.0-2.8)
    const events2 = score.getActiveEvents(2.3);
    assert.equal(events2.length, 1);
    assert.equal(events2[0].inst, 'violin');
    assert.equal(events2[0].bend, 0.1);

    // Query at local time 5.0 should find nothing
    const events3 = score.getActiveEvents(5.0);
    assert.equal(events3.length, 0);
  });
});
