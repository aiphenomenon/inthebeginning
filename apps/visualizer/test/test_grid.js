/**
 * Unit tests for grid.js -- Grid engine.
 * Run with: node --test test/test_grid.js
 */

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { Grid, FAMILY_HUES, GRID_SIZE, MIDI_LOW, MIDI_HIGH } = require('../js/grid.js');

describe('Grid Constants', () => {
  it('should have grid size of 64', () => {
    assert.equal(GRID_SIZE, 64);
  });

  it('should have MIDI range 24-87', () => {
    assert.equal(MIDI_LOW, 24);
    assert.equal(MIDI_HIGH, 87);
  });

  it('should have family hues defined', () => {
    assert.equal(FAMILY_HUES.strings, 0);
    assert.equal(FAMILY_HUES.keys, 220);
    assert.equal(FAMILY_HUES.winds, 120);
    assert.equal(FAMILY_HUES.percussion, 50);
    assert.equal(FAMILY_HUES.world, 280);
    assert.equal(FAMILY_HUES.synth, 180);
    assert.equal(FAMILY_HUES.voice, 0);
  });
});

describe('Grid.noteToRow', () => {
  it('should map MIDI 87 (highest) to row 0', () => {
    assert.equal(Grid.noteToRow(87), 0);
  });

  it('should map MIDI 24 (lowest) to row 63', () => {
    assert.equal(Grid.noteToRow(24), 63);
  });

  it('should map MIDI 60 (middle C) to row 27', () => {
    assert.equal(Grid.noteToRow(60), 27);
  });

  it('should clamp notes above 87 to row 0', () => {
    assert.equal(Grid.noteToRow(100), 0);
    assert.equal(Grid.noteToRow(127), 0);
  });

  it('should clamp notes below 24 to row 63', () => {
    assert.equal(Grid.noteToRow(0), 63);
    assert.equal(Grid.noteToRow(10), 63);
  });

  it('should handle boundary notes correctly', () => {
    assert.equal(Grid.noteToRow(85), 2);
    assert.equal(Grid.noteToRow(25), 62);
  });
});

describe('Grid.rowToNote', () => {
  it('should convert row 0 back to MIDI 87', () => {
    assert.equal(Grid.rowToNote(0), 87);
  });

  it('should convert row 63 back to MIDI 24', () => {
    assert.equal(Grid.rowToNote(63), 24);
  });

  it('should be inverse of noteToRow within range', () => {
    for (let note = MIDI_LOW; note <= MIDI_HIGH; note++) {
      const row = Grid.noteToRow(note);
      assert.equal(Grid.rowToNote(row), note);
    }
  });
});

describe('Grid.cellIndex', () => {
  it('should calculate index for row 0, col 0 as 0', () => {
    assert.equal(Grid.cellIndex(0, 0), 0);
  });

  it('should calculate index for row 0, col 63 as 63', () => {
    assert.equal(Grid.cellIndex(0, 63), 63);
  });

  it('should calculate index for row 1, col 0 as 64', () => {
    assert.equal(Grid.cellIndex(1, 0), 64);
  });

  it('should calculate index for row 63, col 63 as 4095', () => {
    assert.equal(Grid.cellIndex(63, 63), 4095);
  });
});

describe('Grid instrument column assignment', () => {
  it('should assign sequential columns to instruments', () => {
    const grid = new Grid(null);
    assert.equal(grid.getColumn('violin'), 0);
    assert.equal(grid.getColumn('piano'), 1);
    assert.equal(grid.getColumn('flute'), 2);
  });

  it('should return same column for same instrument', () => {
    const grid = new Grid(null);
    const col1 = grid.getColumn('violin');
    const col2 = grid.getColumn('violin');
    assert.equal(col1, col2);
  });

  it('should be case-insensitive', () => {
    const grid = new Grid(null);
    const col1 = grid.getColumn('Violin');
    const col2 = grid.getColumn('violin');
    assert.equal(col1, col2);
  });

  it('should wrap around at 64 columns', () => {
    const grid = new Grid(null);
    for (let i = 0; i < 64; i++) {
      grid.getColumn(`instrument_${i}`);
    }
    const col65 = grid.getColumn('instrument_64');
    assert.equal(col65, 0); // wraps
  });

  it('should preassign columns from instrument list', () => {
    const grid = new Grid(null);
    grid.preassignColumns(['cello', 'violin', 'piano']);
    assert.equal(grid.getColumn('cello'), 0);
    assert.equal(grid.getColumn('violin'), 1);
    assert.equal(grid.getColumn('piano'), 2);
  });

  it('should reset columns', () => {
    const grid = new Grid(null);
    grid.getColumn('violin');
    grid.resetColumns();
    assert.equal(grid.getColumn('piano'), 0);
  });
});

describe('Grid instrument family detection', () => {
  it('should use explicit family map', () => {
    const grid = new Grid(null);
    grid.setInstrumentFamilies({ violin: 'strings', piano: 'keys' });
    assert.equal(grid.getFamily('violin'), 'strings');
    assert.equal(grid.getFamily('piano'), 'keys');
  });

  it('should use heuristic matching when no explicit map', () => {
    const grid = new Grid(null);
    assert.equal(grid.getFamily('violin'), 'strings');
    assert.equal(grid.getFamily('piano'), 'keys');
    assert.equal(grid.getFamily('flute'), 'winds');
    assert.equal(grid.getFamily('drums'), 'percussion');
    assert.equal(grid.getFamily('sitar'), 'world');
    assert.equal(grid.getFamily('synthesizer'), 'synth');
    assert.equal(grid.getFamily('choir'), 'voice');
  });

  it('should default to synth for unknown instruments', () => {
    const grid = new Grid(null);
    assert.equal(grid.getFamily('unknown_thing'), 'synth');
  });
});

describe('Grid color calculation', () => {
  it('should return correct hue for strings (red)', () => {
    const grid = new Grid(null);
    const color = grid.calculateColor('violin', 0.8);
    assert.equal(color.hue, FAMILY_HUES.strings); // 0
  });

  it('should return correct hue for keys (blue)', () => {
    const grid = new Grid(null);
    const color = grid.calculateColor('piano', 0.8);
    assert.equal(color.hue, FAMILY_HUES.keys); // 220
  });

  it('should map velocity to saturation (60-100%)', () => {
    const grid = new Grid(null);
    const colorLow = grid.calculateColor('violin', 0.0);
    const colorHigh = grid.calculateColor('violin', 1.0);
    assert.equal(colorLow.sat, 60);
    assert.equal(colorHigh.sat, 100);
  });

  it('should map velocity to lightness (30-90%)', () => {
    const grid = new Grid(null);
    const colorLow = grid.calculateColor('violin', 0.0);
    const colorHigh = grid.calculateColor('violin', 1.0);
    assert.equal(colorLow.light, 30);
    assert.equal(colorHigh.light, 90);
  });

  it('should give voice low saturation (white)', () => {
    const grid = new Grid(null);
    const color = grid.calculateColor('choir', 0.8);
    assert.equal(color.sat, 10);
    assert.ok(color.isVoice);
  });

  it('should apply hue offset rotation', () => {
    const grid = new Grid(null);
    grid.setHueOffset(90);
    const color = grid.calculateColor('violin', 0.5);
    assert.equal(color.hue, 90); // 0 + 90
  });

  it('should wrap hue past 360', () => {
    const grid = new Grid(null);
    grid.setHueOffset(300);
    const color = grid.calculateColor('piano', 0.5);
    assert.equal(color.hue, (220 + 300) % 360); // 160
  });
});

describe('Grid hue rotation', () => {
  it('should rotate hue offset', () => {
    const grid = new Grid(null);
    assert.equal(grid.hueOffset, 0);
    grid.rotateHue(45);
    assert.equal(grid.hueOffset, 45);
    grid.rotateHue(45);
    assert.equal(grid.hueOffset, 90);
  });

  it('should wrap hue offset past 360', () => {
    const grid = new Grid(null);
    grid.rotateHue(350);
    grid.rotateHue(20);
    assert.equal(grid.hueOffset, 10); // (350+20) % 360
  });
});

describe('Grid updateGrid (headless)', () => {
  it('should track active cells', () => {
    const grid = new Grid(null);
    grid.preassignColumns(['violin', 'piano']);

    const events = [
      { note: 60, inst: 'violin', vel: 0.8, ch: 0 },
      { note: 72, inst: 'piano', vel: 0.6, ch: 1 }
    ];
    grid.updateGrid(events);

    assert.equal(grid.activeCells.size, 2);
  });

  it('should clear grid', () => {
    const grid = new Grid(null);
    grid.updateGrid([{ note: 60, inst: 'violin', vel: 0.8, ch: 0 }]);
    assert.equal(grid.activeCells.size, 1);

    grid.clearGrid();
    assert.equal(grid.activeCells.size, 0);
    assert.equal(grid.cellColors.size, 0);
  });

  it('should compute dominant hue', () => {
    const grid = new Grid(null);
    grid.setInstrumentFamilies({ violin: 'strings' });
    grid.updateGrid([{ note: 60, inst: 'violin', vel: 0.8, ch: 0 }]);
    const hue = grid.getDominantHue();
    // Strings hue is 0 (red)
    assert.ok(hue >= 0 && hue < 360);
  });

  it('should return default hue when no active cells', () => {
    const grid = new Grid(null);
    assert.equal(grid.getDominantHue(), 200);
  });
});
