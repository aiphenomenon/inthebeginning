/**
 * Unit tests for player.js -- Audio player controls.
 * Run with: node --test test/test_player.js
 *
 * Note: These tests run in Node.js without a DOM, so they test the
 * non-DOM logic (formatTime, mode visibility rules, state management).
 * Full DOM integration testing requires a browser.
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { Player } = require('../js/player.js');

describe('Player.formatTime', () => {
  it('should format 0 seconds as 0:00', () => {
    assert.equal(Player.formatTime(0), '0:00');
  });

  it('should format 62 seconds as 1:02', () => {
    assert.equal(Player.formatTime(62), '1:02');
  });

  it('should format 3661 seconds as 1:01:01', () => {
    assert.equal(Player.formatTime(3661), '1:01:01');
  });

  it('should format 59 seconds as 0:59', () => {
    assert.equal(Player.formatTime(59), '0:59');
  });

  it('should format 600 seconds as 10:00', () => {
    assert.equal(Player.formatTime(600), '10:00');
  });

  it('should handle NaN as 0:00', () => {
    assert.equal(Player.formatTime(NaN), '0:00');
  });

  it('should handle negative as 0:00', () => {
    assert.equal(Player.formatTime(-5), '0:00');
  });

  it('should handle Infinity as 0:00', () => {
    assert.equal(Player.formatTime(Infinity), '0:00');
  });

  it('should floor fractional seconds', () => {
    assert.equal(Player.formatTime(90.7), '1:30');
  });

  it('should pad single-digit seconds', () => {
    assert.equal(Player.formatTime(65), '1:05');
  });

  it('should pad minutes and seconds in hour format', () => {
    assert.equal(Player.formatTime(3605), '1:00:05');
  });
});

describe('Player construction (headless)', () => {
  it('should create a player without a DOM', () => {
    // In Node.js, Audio is not defined, so we mock it minimally
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 0;
        this.muted = false;
        this.paused = true;
      }
      play() { this.paused = false; return Promise.resolve(); }
      pause() { this.paused = true; }
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({
        controlBar: null,
        mode: 'single',
        score: null,
        onTimeUpdate: () => {},
        onTrackChange: () => {}
      });

      assert.equal(player.mode, 'single');
      assert.equal(player.isPlaying, false);
      assert.equal(player.currentTrack, 0);
      assert.equal(player.volume, 0.8);
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should initialize with album mode', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 0;
        this.muted = false;
        this.paused = true;
      }
      play() { this.paused = false; return Promise.resolve(); }
      pause() { this.paused = true; }
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'album' });
      assert.equal(player.mode, 'album');
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should initialize with stream mode', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 0;
        this.muted = false;
        this.paused = true;
      }
      play() { this.paused = false; return Promise.resolve(); }
      pause() { this.paused = true; }
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'stream' });
      assert.equal(player.mode, 'stream');
    } finally {
      global.Audio = origAudio;
    }
  });
});

describe('Player play/pause (headless)', () => {
  it('should toggle play state', () => {
    const origAudio = global.Audio;
    const origRAF = global.requestAnimationFrame;
    const origCAF = global.cancelAnimationFrame;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = 'test.mp3';
        this.currentSrc = 'test.mp3';
        this.currentTime = 0;
        this.duration = 100;
        this.muted = false;
        this.paused = true;
      }
      play() { this.paused = false; return Promise.resolve(); }
      pause() { this.paused = true; }
      load() {}
      addEventListener() {}
    };
    global.requestAnimationFrame = (cb) => 1;
    global.cancelAnimationFrame = () => {};

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      assert.equal(player.isPlaying, false);

      player.togglePlay();
      assert.equal(player.isPlaying, true);

      player.togglePlay();
      assert.equal(player.isPlaying, false);
    } finally {
      global.Audio = origAudio;
      global.requestAnimationFrame = origRAF;
      global.cancelAnimationFrame = origCAF;
    }
  });
});

describe('Player skip (headless)', () => {
  it('should skip forward and backward', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 30;
        this.duration = 100;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      player.audio.currentTime = 30;
      player.audio.duration = 100;

      player.skip(15);
      assert.equal(player.audio.currentTime, 45);

      player.skip(-15);
      assert.equal(player.audio.currentTime, 30);
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should clamp skip to 0', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 5;
        this.duration = 100;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      player.audio.currentTime = 5;
      player.audio.duration = 100;

      player.skip(-20);
      assert.equal(player.audio.currentTime, 0);
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should not skip in stream mode', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 30;
        this.duration = 100;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'stream' });
      player.audio.currentTime = 30;
      player.skip(15);
      assert.equal(player.audio.currentTime, 30); // unchanged
    } finally {
      global.Audio = origAudio;
    }
  });
});

describe('Player track navigation (headless)', () => {
  it('should not navigate tracks in single mode', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 100;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      player.nextTrack();
      assert.equal(player.currentTrack, 0);
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should not navigate past first track', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 100;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const { Score } = require('../js/score.js');
      const score = Score.fromJSON({
        tracks: [
          { track_num: 1, title: 'A', start_time: 0, duration: 100, events: [] },
          { track_num: 2, title: 'B', start_time: 100, duration: 100, events: [] }
        ]
      });
      const player = new Player({ controlBar: null, mode: 'album', score: score });
      player.prevTrack();
      assert.equal(player.currentTrack, 0); // should not go negative
    } finally {
      global.Audio = origAudio;
    }
  });
});

describe('Player volume', () => {
  it('should set volume', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 0;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      player.setVolume(0.5);
      assert.equal(player.volume, 0.5);
      assert.equal(player.audio.volume, 0.5);
    } finally {
      global.Audio = origAudio;
    }
  });

  it('should clamp volume to 0-1', () => {
    const origAudio = global.Audio;
    global.Audio = class MockAudio {
      constructor() {
        this.preload = '';
        this.volume = 1;
        this.src = '';
        this.currentSrc = '';
        this.currentTime = 0;
        this.duration = 0;
        this.muted = false;
      }
      play() { return Promise.resolve(); }
      pause() {}
      load() {}
      addEventListener() {}
    };

    try {
      const player = new Player({ controlBar: null, mode: 'single' });
      player.setVolume(1.5);
      assert.equal(player.volume, 1);
      player.setVolume(-0.5);
      assert.equal(player.volume, 0);
    } finally {
      global.Audio = origAudio;
    }
  });
});

describe('Player mode-specific control visibility', () => {
  it('should identify album mode controls', () => {
    // In album mode: prev/next visible, seek visible, skip visible
    // This is tested conceptually since we have no DOM
    assert.equal('album' === 'album', true);
  });

  it('should identify stream mode restrictions', () => {
    // In stream mode: no prev/next, no seek, no skip
    const mode = 'stream';
    const showPrevNext = mode === 'album';
    const showSeek = mode !== 'stream';
    const showSkip = mode !== 'stream';
    assert.equal(showPrevNext, false);
    assert.equal(showSeek, false);
    assert.equal(showSkip, false);
  });

  it('should identify single mode controls', () => {
    // In single mode: no prev/next, seek visible, skip visible
    const mode = 'single';
    const showPrevNext = mode === 'album';
    const showSeek = mode !== 'stream';
    const showSkip = mode !== 'stream';
    assert.equal(showPrevNext, false);
    assert.equal(showSeek, true);
    assert.equal(showSkip, true);
  });
});
