# Algorithm Port Tracking

Cross-reference for algorithms ported between languages. When updating
an algorithm in one language, check this table and propagate changes.

## Python → JavaScript Ports

| Algorithm | Python Source | JS Port | Version | Status |
|-----------|-------------|---------|---------|--------|
| MIDI fragment sampling | radio_engine.py:1294 `sample_bars_seeded` | hifi-generator.js `_sampleMidiBars` | V48 | Done |
| Loop friendliness scoring | radio_engine.py:1250 `_assess_loop_friendliness` | hifi-generator.js `_assessLoopFriendliness` | V48 | Done |
| Harmonic consonance | radio_engine.py:2471 `_build_chord_from_note` | hifi-generator.js `_buildChordFromNote` | V48 | Done |
| Rondo structure | radio_engine.py:2556 `_build_rondo_sections` | hifi-generator.js `_buildRondo` | V48 | Done |
| Mood segments | radio_engine.py:2004 `MoodSegment` | hifi-generator.js `_buildMoodSegment` | V48 | Done |
| Segment planning | radio_engine.py:2125 `_plan_segments` | hifi-generator.js `_planSegments` | V48 | Done |
| Epoch music mapping | radio_engine.py:328 `EPOCH_MUSIC` | hifi-generator.js `EPOCH_MUSIC` | V48 | Done |
| Scale definitions (24+) | radio_engine.py:125 `SCALES` | hifi-generator.js `HIFI_SCALES` | V48 | Done |
| Chord intervals | radio_engine.py:196 `CHORD_INTERVALS` | hifi-generator.js `CHORD_INTERVALS` | V48 | Done |
| Diatonic chord quality | radio_engine.py:234 `DIATONIC_CHORD_QUALITY` | hifi-generator.js `DIATONIC_CHORD_QUALITY` | V48 | Done |
| Scale snap | radio_engine.py (in sample_bars_seeded) | hifi-generator.js `_snapToScale` | V48 | Done |
| MIDI parsing | synth-worker.js (existing) | hifi-generator.js `_parseMidiNotes` | V48 | Done |
| Additive synthesis | radio_engine.py:424 `_synth_note_np` | synth-engine.js `playNote` | Pre-V48 | Done |
| Scale definitions (44) | composer.py:125 | music-generator.js | Pre-V48 | Done |
| Instrument names (clean) | radio_engine.py instrument naming | music-sync.js `cleanInstrumentName` | V47 | Done |

## External Dependencies

| Component | Source | License | Port Type | Notes |
|-----------|--------|---------|-----------|-------|
| SpessaSynth | spessasynth_lib v4.2.9 | Apache-2.0 | npm package (full) | SoundFont synthesizer |
| FluidR3_GM.sf2 | Debian fluid-soundfont-gm | MIT | Binary asset | 142MB GM SoundFont |
| FluidSynth (reference) | github.com/FluidSynth/fluidsynth | LGPL-2.1 | Reference only | SpessaSynth reimplements the synthesis |

## Future Ports Needed

| Algorithm | From | To | Priority |
|-----------|------|----|----------|
| Instrument rotation (14-seg) | radio_engine.py:2448 | hifi-generator.js | Medium |
| Anti-artifact processing | radio_engine.py:3288-3365 | hifi-generator.js | Medium |
| FluidSynth rendering | radio_engine.py:1404 | SpessaSynth (done via library) | Done |
| Segment morph transitions | radio_engine.py (6s cosine) | hifi-generator.js | Medium |
