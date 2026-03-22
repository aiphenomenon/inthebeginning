/**
 * Tests for SynthEngine — additive synthesis port from Python composer.py.
 *
 * Node.js test runner: node --test test/test_synth_engine.js
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { SynthEngine, TIMBRES, ENVELOPES, FAMILY_HUES, GM_TO_TIMBRE, GM_TO_FAMILY, mtof } = require('../js/synth-engine.js');

describe('mtof (MIDI-to-frequency conversion)', () => {
  it('should convert A4 (MIDI 69) to 440 Hz', () => {
    assert.equal(mtof(69), 440);
  });

  it('should convert C4 (MIDI 60) to ~261.63 Hz', () => {
    assert.ok(Math.abs(mtof(60) - 261.626) < 0.01);
  });

  it('should convert A3 (MIDI 57) to 220 Hz', () => {
    assert.ok(Math.abs(mtof(57) - 220) < 0.01);
  });

  it('should convert A5 (MIDI 81) to 880 Hz', () => {
    assert.ok(Math.abs(mtof(81) - 880) < 0.01);
  });

  it('should handle edge values', () => {
    assert.ok(mtof(0) > 0);
    assert.ok(mtof(127) > 0);
    assert.ok(mtof(127) > mtof(0));
  });
});

describe('TIMBRES', () => {
  it('should have at least 16 instrument timbres', () => {
    assert.ok(Object.keys(TIMBRES).length >= 16);
  });

  it('should have all expected instrument names', () => {
    const expected = ['violin', 'cello', 'harp', 'flute', 'oboe', 'clarinet',
      'horn', 'trumpet', 'piano', 'bell', 'gamelan', 'tibetan_bowl',
      'choir_ah', 'choir_oo', 'throat_sing', 'warm_pad', 'cosmic', 'sine'];
    for (const name of expected) {
      assert.ok(TIMBRES[name] !== undefined, `Missing timbre: ${name}`);
    }
  });

  it('should have fundamental amplitude of 1.0 for all timbres', () => {
    for (const [name, harmonics] of Object.entries(TIMBRES)) {
      if (harmonics.length > 0) {
        assert.equal(harmonics[0], 1.0, `${name} fundamental should be 1.0`);
      }
    }
  });

  it('should have decreasing or variable harmonic amplitudes', () => {
    for (const [name, harmonics] of Object.entries(TIMBRES)) {
      for (const amp of harmonics) {
        assert.ok(amp >= 0 && amp <= 1.0, `${name}: amplitude ${amp} out of range`);
      }
    }
  });
});

describe('ENVELOPES', () => {
  it('should have an envelope for each timbre', () => {
    for (const name of Object.keys(TIMBRES)) {
      assert.ok(ENVELOPES[name] !== undefined, `Missing envelope: ${name}`);
    }
  });

  it('should have valid ADSR parameters', () => {
    for (const [name, env] of Object.entries(ENVELOPES)) {
      assert.ok(env.a >= 0 && env.a <= 2, `${name}: attack ${env.a} out of range`);
      assert.ok(env.d >= 0 && env.d <= 2, `${name}: decay ${env.d} out of range`);
      assert.ok(env.s >= 0 && env.s <= 1, `${name}: sustain ${env.s} out of range`);
      assert.ok(env.r >= 0 && env.r <= 2, `${name}: release ${env.r} out of range`);
    }
  });
});

describe('FAMILY_HUES', () => {
  it('should have all 10 families', () => {
    const expected = ['strings', 'keys', 'winds', 'percussion', 'world', 'synth', 'voice', 'brass', 'organ', 'bass'];
    for (const f of expected) {
      assert.ok(FAMILY_HUES[f] !== undefined, `Missing family: ${f}`);
    }
  });

  it('should have hue values in 0-360 range', () => {
    for (const [name, hue] of Object.entries(FAMILY_HUES)) {
      assert.ok(hue >= 0 && hue <= 360, `${name}: hue ${hue} out of range`);
    }
  });
});

describe('GM_TO_TIMBRE mapping', () => {
  it('should map all GM groups', () => {
    const groups = ['piano', 'chromatic', 'organ', 'guitar', 'bass', 'strings',
      'ensemble', 'brass', 'reed', 'pipe', 'synth-lead', 'synth-pad',
      'fx', 'ethnic', 'percussion', 'sfx'];
    for (const g of groups) {
      assert.ok(GM_TO_TIMBRE.hasOwnProperty(g), `Missing GM group: ${g}`);
    }
  });

  it('should map percussion to null (synthesized separately)', () => {
    assert.equal(GM_TO_TIMBRE['percussion'], null);
  });

  it('should map piano to piano timbre', () => {
    assert.equal(GM_TO_TIMBRE['piano'], 'piano');
  });

  it('should map strings to violin timbre', () => {
    assert.equal(GM_TO_TIMBRE['strings'], 'violin');
  });
});

describe('GM_TO_FAMILY mapping', () => {
  it('should map all GM groups to families', () => {
    for (const group of Object.keys(GM_TO_TIMBRE)) {
      assert.ok(GM_TO_FAMILY[group] !== undefined, `Missing family for: ${group}`);
    }
  });

  it('should map to valid family names', () => {
    for (const [group, family] of Object.entries(GM_TO_FAMILY)) {
      assert.ok(FAMILY_HUES[family] !== undefined,
        `${group} -> ${family}: not a valid family`);
    }
  });
});

describe('SynthEngine.getColor', () => {
  it('should return hue, saturation, lightness for an instrument', () => {
    const c = SynthEngine.getColor('piano', 0.8, 0);
    assert.ok(typeof c.hue === 'number');
    assert.ok(typeof c.sat === 'number');
    assert.ok(typeof c.light === 'number');
    assert.ok(typeof c.isVoice === 'boolean');
  });

  it('should apply hue offset', () => {
    const c1 = SynthEngine.getColor('piano', 0.8, 0);
    const c2 = SynthEngine.getColor('piano', 0.8, 60);
    assert.notEqual(c1.hue, c2.hue);
  });

  it('should handle voice instruments with low saturation', () => {
    const c = SynthEngine.getColor('ensemble', 0.8, 0);
    assert.equal(c.isVoice, true);
    assert.equal(c.sat, 10);
  });

  it('should scale saturation with velocity', () => {
    const cLow = SynthEngine.getColor('strings', 0.1, 0);
    const cHigh = SynthEngine.getColor('strings', 1.0, 0);
    assert.ok(cHigh.sat > cLow.sat);
    assert.ok(cHigh.light > cLow.light);
  });
});

describe('SynthEngine.getTimbre', () => {
  it('should return the timbre name for known GM groups', () => {
    assert.equal(SynthEngine.getTimbre('piano'), 'piano');
    assert.equal(SynthEngine.getTimbre('strings'), 'violin');
    assert.equal(SynthEngine.getTimbre('brass'), 'trumpet');
  });

  it('should return the input for unknown names', () => {
    assert.equal(SynthEngine.getTimbre('theremin'), 'theremin');
  });
});

describe('SynthEngine constructor', () => {
  it('should initialize with null AudioContext', () => {
    const engine = new SynthEngine();
    assert.equal(engine.ctx, null);
  });

  it('should have default mutation preset', () => {
    const engine = new SynthEngine();
    assert.deepEqual(engine._mutation, { pitchShift: 0, tempoMult: 1.0, reverb: 0, filter: 'none' });
  });

  it('should have vibrato enabled by default', () => {
    const engine = new SynthEngine();
    assert.equal(engine.vibratoEnabled, true);
  });

  it('should have 128 max voices', () => {
    const engine = new SynthEngine();
    assert.equal(engine.maxVoices, 128);
  });

  it('should have empty voices map', () => {
    const engine = new SynthEngine();
    assert.equal(engine._voices.size, 0);
  });
});

describe('SynthEngine.setMutation', () => {
  it('should accept mutation presets', () => {
    const engine = new SynthEngine();
    engine.setMutation({ pitchShift: 5, tempoMult: 0.8, reverb: 0.5, filter: 'lowpass' });
    assert.equal(engine._mutation.pitchShift, 5);
    assert.equal(engine._mutation.tempoMult, 0.8);
  });

  it('should handle null mutation (reset to defaults)', () => {
    const engine = new SynthEngine();
    engine.setMutation(null);
    assert.equal(engine._mutation.pitchShift, 0);
    assert.equal(engine._mutation.tempoMult, 1.0);
  });
});
