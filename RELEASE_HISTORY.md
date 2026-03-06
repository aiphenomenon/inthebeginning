# Release History

Release history for **In The Beginning** — reverse chronological order (newest first).

---

## v0.12.0 — 2026-03-06 — Radio Engine v12: Natural Instrument Character Overhaul

### Summary

Radio engine v12 returns to v8's natural instrument sound while keeping v11's mixing
improvements. The primary goal is warm, acoustic-forward timbre with natural harmonic
detuning and noise/breath layers for organic texture. A frequency ceiling at C6
(1047 Hz) prevents ear-piercing highs, and a master lowpass at 7kHz tames brightness.

### Changes

- **Radio Engine v12** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV12` class returning to natural instrument character
  - Natural harmonic detuning for organic, less-synthetic sound
  - Noise and breath layers added to synthesis for realism
  - Frequency ceiling at C6 (1047 Hz) prevents ear-piercing high notes
  - Acoustic instrument family bias: 70% acoustic, 30% synth instrument selection
  - Reduced melody register offset (+7 semitones instead of +12)
  - Master lowpass filter at 7kHz for warmth
  - Every ensemble guaranteed a bass/foundation instrument
  - Longer note durations for legato character
  - Retains all v11 mixing improvements (per-voice RMS normalization, soft-knee
    limiting, consonance enforcement, bar-aligned rendering, orchestral roles)
  - CT timestamps in all script output
  - CLI `--version v12` support

---

## v0.11.0 — 2026-03-06 — Radio Engine v11: Comprehensive Audio Quality Overhaul

### Summary

Radio engine v11 addresses 19 audio quality issues identified through deep code
review. The primary fix resolves the "radio static at full volume" effect caused by
pan parameter overflow in `_mix_mono` which produced phase-inverted channels. V11
introduces per-voice RMS normalization, master bus soft-knee limiting, inter-voice
consonance enforcement, bar-aligned rendering, and orchestral role assignment.

### Changes

- **Radio Engine v11** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV11` class extending `RadioEngineV10`
  - `GainStage`: Per-voice RMS normalization + master bus soft-knee limiting
  - `ConsonanceEngine`: Inter-voice consonance scoring (Helmholtz model) with
    iterative adjustment to ensure composite harmony exceeds 0.55 threshold
  - `BarGrid`: Absolute time grid ensuring note onsets and rondo sections align
    to 16th-note metric positions
  - `OrchestratorV11`: Orchestral role assignment (foundation, harmony_low,
    harmony_mid, melody, color) with distinct register offsets and gain weights
  - `_soft_limit()`: Soft-knee limiter replacing `math.tanh` in streaming renderer
  - `_mix_mono_v11()`: Separated pan [-1,1] and gain parameters (fixes phase inversion)
  - `_apply_reverb_v11()`: Reduced comb feedback (0.55-0.65), pre-reverb 150Hz highpass
  - `_apply_early_reflections_v11()`: Reduced amplitudes (0.05-0.20)
  - Compression applied AFTER reverb (fixes pumping effect)
  - Minimum MIDI note raised to 36/C2 (prevents subsonic fundamentals)
  - Anti-click fades increased to 5ms (from 2ms)
  - Crossfade duration extended to 4-6s (from 2-4s)
  - Voice leading: smooth chord transitions (min-movement algorithm)
  - CLI `--version v11` support
  - `generate_radio_v11_mp3()` helper function
- **Tests** (`apps/audio/test_radio_engine.py`):
  - 25 new tests across 7 test classes for V11 components
  - Phase inversion verification test
  - Consonance scoring and adjustment tests
  - Bar grid alignment tests

### Agent Activity (Turn 1 — Implementation)
- Session: claude/resume-v9-document-v8-6yhAe
- Agent: Claude Opus 4.6
- Files created: 1 (session log)
- Files modified: 3 (radio_engine.py, test_radio_engine.py, RELEASE_HISTORY.md)

### Agent Activity (Turn 2 — MP3 Generation + Steering Fix)
- Generated 30-minute V11 MP3s: `cosmic_radio_v11.mp3` (seed 42) +
  `cosmic_radio_v11_random.mp3` (random seed)
- Diagnosed and fixed steering self-cue gap: start-of-turn housekeeping was being
  skipped because no pre-work reminder existed
- Added Start-of-Turn Protocol to CLAUDE.md, AGENTS.md, `.claude/steering-check.sh`
- PostToolUse hook now emits lightweight reminder on first Bash call per turn
- Files modified: `.claude/steering-check.sh`, `CLAUDE.md`, `AGENTS.md`,
  `session_logs/v0.11.0-session.md`, `future_memories/v11-plan.md`,
  `RELEASE_HISTORY.md`
- Files created: `apps/audio/cosmic_radio_v11.mp3`,
  `apps/audio/cosmic_radio_v11_random.mp3`

---

## v0.10.0 — 2026-03-06 — Radio Engine v10: GM-Timbre-Aware Synthesis + Expanded Library

### Summary

Radio engine v10 with GM-timbre-aware synthesis: each of the 15 GM instrument families
now gets a distinct ADSR envelope, harmonic structure, and brightness profile instead
of the generic additive synthesis that made everything sound organ-y. Features tempo
range narrowed to 1.2x-1.8x, 85% orchestral simultaneous layering with 4-6 voices
per segment, 8-second morph transitions between moods, and minimum 3 family groups
per segment.

The MIDI library was tripled from 249 to 744 files spanning 26 composers across 500
years of Western music (Renaissance through Late Romantic). 20 new instrument samples
added (60 total). espeak-ng TTS installed for spoken word announcements.

### Changes

- **Radio Engine v10** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV10` class extending `RadioEngineV9`
  - `GM_TIMBRE_PROFILES`: 15 GM timbre profiles with distinct attack, decay, sustain,
    release, harmonic ratios, brightness, and vibrato per instrument family (piano,
    mallets, organ, guitar, bass, strings, ensemble, brass, reed, pipe, synth_lead,
    synth_pad, synth_fx, world, percussive)
  - `_gm_program_to_timbre()`: Maps any GM program 0-127 to its timbre profile
  - `_synth_gm_note_np()`: New synthesis function using family-specific parameters
    instead of generic 8-harmonic additive base
  - Tempo range 1.2x-1.8x flat (no density-dependent capping)
  - 85% simultaneous orchestral layering (up from 75% in v8/v9)
  - 4-6 voices per segment (up from 2-4) with minimum 3 family groups
  - Register spread widened to -24/+24 semitones
  - 8s morph transitions (up from 6s), 6s fade-in, 10s fade-out
  - 3-5s crossfade between loop iterations (up from 2-4s)
  - CLI: `--version v10` flag
  - `generate_radio_v10_mp3()` convenience function
  - All v9/v8 features preserved (expanded instruments, family variety, time signature
    control, anti-hiss, subsonic removal, note smoothing, note quantization, rondo
    structures, arpeggio forms, harmonic consonance (Helmholtz/Hartmann), MIDI sampling)
- **23 new v10 tests** in `test_radio_engine.py`:
  - GM timbre profiles: count, required keys, program mapping coverage
  - Piano/strings/brass/synth_pad mapping tests
  - Distinct envelope shapes verification
  - GM synthesis: audio production, different-programs-different-output
  - Tempo range 1.2-1.8x, no density capping
  - Engine creation, morph duration, fade durations
  - Instrument diversity (3+ families per segment)
  - Short render integration test
  - CLI v10 argument acceptance
- **MIDI library expanded** (249 → 744 files, 14 → 26 composers):
  - Added from narcisse-dev/classical_ancient_midifiles: Bach (+45), Beethoven (+45),
    Chopin (+30), Corelli (55, new), Haydn (+55), Hummel (24, new), Joplin (47, new),
    Mozart (+45), Scarlatti (55, new)
  - Added Renaissance composers: Josquin (45), DuFay (19), Ockeghem (23), Isaac (5),
    Obrecht (7), Busnoys (10), Brumel (3), Compère (10), Mouton (10)
  - Synthetic Handel (10), Haydn (12), Mendelssohn (8), Tchaikovsky (15) via mido
- **20 new instrument samples** (40 → 60):
  - Saxophones: alto, tenor, soprano
  - Guitars: acoustic, electric clean, overdriven
  - Keyboards: pipe organ, marimba, xylophone, steel drums
  - Brass: muted trumpet, tuba, English horn, piccolo
  - World: banjo, shamisen, bagpipe
  - Synth: sawtooth lead, square lead, synth strings
- **gVisor steering updates** (`.claude/steering-check.sh`):
  - Added future memories early-stage orchestration cue (#14)
  - Added audio engine quality gate cue (#15)
- **30-minute cosmic radio v10 MP3s**:
  - `cosmic_radio_v10.mp3`: Seed 42, 1800 seconds
  - `cosmic_radio_v10_random.mp3`: Random seed, 1800 seconds

### Agent Activity

- Agent: Claude Opus 4.6 via Claude Code CLI
- Session: claude/resume-v9-document-v8-6yhAe
- Subagents spawned: 1 (codebase exploration)
- External repos cloned: narcisse-dev/classical_ancient_midifiles (4,723 MIDI files)
- espeak-ng installed for TTS
- Test results: 141 radio engine tests (23 new v10), 400 Python reference tests pass
- MP3 render time: ~595s per 30-min piece (numpy-accelerated)

### Files Created

- `future_memories/v0.10.0-plan.md`
- `apps/audio/cosmic_radio_v10.mp3`
- `apps/audio/cosmic_radio_v10_random.mp3`
- `session_logs/v0.10.0-session.md`
- 20 new instrument samples in `apps/audio/samples/`
- 495 new MIDI files across 12 new composer directories
- MIDI library: Corelli/, Hummel/, Joplin/, Scarlatti/, Josquin/, DuFay/, Ockeghem/,
  Isaac/, Obrecht/, Busnoys/, Brumel/, Compère/, Mouton/

### Files Modified

- `apps/audio/radio_engine.py` — v10 engine class, GM timbre profiles, CLI update
- `apps/audio/test_radio_engine.py` — 23 new v10 tests
- `apps/audio/midi_library/ATTRIBUTION.md` — expanded attribution
- `.claude/steering-check.sh` — two new steering cues
- `RELEASE_HISTORY.md` — this entry

---

## v0.9.0 — 2026-03-06 — Radio Engine v9: Expanded Instruments + Density-Aware Tempo

### Summary

Radio engine v9 with ~50 new GM instruments across 15 family pools (up from 5),
density-aware tempo multiplier (1.1x-2.1x range with caps during busy simulation
epochs), and family variety enforcement ensuring symphonic, rock, electronic, and
world instrument groups all appear across a 30-minute piece.

Also introduces the **future memories** protocol for durable session restoration,
CI flake detection steering, and AMD64 build verification guidance.

### Changes

- **Radio Engine v9** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV9` class extending `RadioEngineV8` with expanded instrument palette
  - `GM_EXPANDED_INSTRUMENTS`: ~50 new GM instruments across rock, electronic, synth FX,
    world/ethnic, symphonic, sax, choir, and mallet families
  - `GM_ALL_INSTRUMENTS`: combined v7/v8 + v9 instrument catalog
  - `V9_FAMILY_POOLS`: 15 instrument family pools (strings, brass, woodwinds, keys,
    pitched_perc, rock_guitar, rock_bass, synth_lead, synth_pad, synth_fx, world,
    sax, choir, symphonic_ext, mallets)
  - Density-aware tempo: `_compute_tempo_multiplier` returns 1.1x-2.1x, capped at
    1.6x for high-density epochs (>100 density score) and 1.8x for medium density
  - Family variety enforcement: tracks used family groups across render, biases toward
    under-represented groups past the halfway point
  - CLI: `--version v9` flag (v7 remains default)
  - `generate_radio_v9_mp3()` convenience function
  - All v8 features preserved (orchestral layering, anti-hiss, subsonic removal,
    note smoothing, time signature control, note quantization)
- **19 new v9 tests** in `test_radio_engine.py`:
  - Instrument catalog validation (count, superset, GM range)
  - 15 family pools verification
  - Rock, synth, world, sax, choir family existence
  - Density-aware tempo range, high/medium density caps
  - V9 engine creation, family group tracking, expanded pool coverage
  - Short render integration test
  - CLI v9 argument acceptance
- **Future memories protocol** (`future_memories/`):
  - New directory for verbose plan files committed before code mutation
  - `future_memories/README.md` explaining the protocol
  - `future_memories/v0.9.0-plan.md` documenting the full implementation plan
- **Steering updates** (CLAUDE.md, AGENTS.md, .claude/steering-check.sh):
  - Future memories: iterative plan commits before code mutation
  - CI flake detection and repair protocol
  - AMD64 build verification (best-effort)
  - Input quality caveat for typos/speech-to-text/ambiguity
  - Archive strategy: single tar.gz rebuilt each time, no orphan files
- **30-minute cosmic radio v9 MP3s**:
  - `cosmic_radio_v9.mp3`: Seed 42, 1800 seconds
  - `cosmic_radio_v9_random.mp3`: Random seed, 1800 seconds

### Agent Activity

- Agent: Claude Opus 4.6 via Claude Code CLI
- Session: Resuming interrupted v9 implementation from previous session
- Subagents spawned: 2 (codebase exploration, radio engine structure analysis)
- Test results: 117/118 radio engine tests pass (1 pre-existing espeak-ng skip),
  400/400 Python reference tests pass
- AMD64 builds verified: Go, Rust, C, C++

### Files Created

- `future_memories/README.md`
- `future_memories/v0.9.0-plan.md`
- `cosmic_radio_v9.mp3`
- `cosmic_radio_v9_random.mp3`
- `session_logs/v0.9.0-session.md`

### Files Modified

- `apps/audio/radio_engine.py` — v9 engine class, expanded instruments, CLI
- `apps/audio/test_radio_engine.py` — 19 new v9 tests
- `AGENTS.md` — future memories, CI flakes, AMD64 builds steering
- `CLAUDE.md` — matching steering updates
- `.claude/steering-check.sh` — matching hook updates
- `RELEASE_HISTORY.md` — this entry

---

## v0.8.0 — 2026-03-04 — Radio Engine v8: Orchestral Layering + Numpy Acceleration

### Summary

Radio engine v8 with orchestral layering: simultaneous multi-instrument sections
(~75% of segments) with occasional solo passages (~25%) for variety, anti-hiss
spectral filtering (cascaded lowpass at 10kHz/14kHz), subsonic removal (2-pole
highpass at 30Hz), note texture smoothing, time signature control (70%+ simple
with guaranteed compound/complex per 10-minute window), note duration quantization
to bar structure, and numpy-accelerated synthesis achieving ~7x speedup.

### Changes

- **Radio Engine v8** (`apps/audio/radio_engine.py`):
  - New `RadioEngineV8` class extending `RadioEngine` with orchestral layering
  - Simultaneous multi-instrument orchestral sections (~75% of segments)
  - Solo instrument alternation (~25%) for variety and contrast
  - Consonant octave offsets between simultaneous voices (-12, 0, 0, 12, 24 semitones)
  - `NoteSmoother` class: post-synthesis buffer-level lowpass for smoother note textures
  - `AntiHissFilter` class: cascaded lowpass at 10kHz/14kHz for spectral cleanliness
  - `SubsonicFilter` class: 2-pole highpass at 30Hz removing subsonic rumble
  - `NoteQuantizer` class: duration quantization to fit bar structure (snap to beat grid)
  - Time signature rules: 70-80% simple (2/4, 3/4, 4/4), guaranteed compound/complex
    (6/8, 5/4, 7/8) in every 10-minute window per Wikipedia classification
  - CLI: `--version v8` flag (v7 remains default)
- **Numpy-accelerated synthesis** (`apps/audio/radio_engine.py`):
  - Vectorized ADSR envelope generation using numpy arrays
  - Vectorized harmonic synthesis (all harmonics computed in parallel)
  - Vectorized colored note generation replacing per-sample Python loops
  - ~7x speedup: 30-minute MP3 renders in ~6 minutes (was ~60 minutes)
  - Falls back gracefully to pure-Python when numpy unavailable
- **17 new v8 tests** in `test_radio_engine.py`:
  - `NoteSmoother` output validation
  - `AntiHissFilter` frequency response verification
  - `SubsonicFilter` low-frequency attenuation
  - `NoteQuantizer` beat grid snapping
  - `RadioEngineV8` instantiation and orchestral section generation
  - Time signature distribution validation (70%+ simple)
  - Compound/complex time signature guarantee per 10-minute window
  - All numpy acceleration paths tested
- **30-minute cosmic radio v8 MP3** (`cosmic_radio_v8.mp3`):
  - Seed 42, 1800 seconds, rendered with numpy acceleration
  - 73% simple time signatures (11/15 segments)

### Test Results

- Python reference: 400 passed
- Audio radio engine: 97 passed (80 v7 + 17 new v8)
- Audio composer: 67 passed
- Audio music engine: 62 passed
- Total quick tests: 626+

### Files Created

- `apps/audio/cosmic_radio_v8.mp3` — 30-minute cosmic radio v8 (~41 MB)

### Files Modified

- `apps/audio/radio_engine.py` — +1,200 lines: RadioEngineV8, NoteSmoother,
  AntiHissFilter, SubsonicFilter, NoteQuantizer, numpy acceleration
- `apps/audio/test_radio_engine.py` — +193 lines: 17 new v8 tests

### Agent Activity

- Session: `018qG8DYYWiDnmYdJZjN5GqX` (Claude Code native app)
- Branch: `claude/ast-physics-simulator-IWFs4`
- 3 commits: `348bf29`, `45791bd`, `88a543d`
- Note: Release notes and session log were not generated during the original session
  due to a UI bug in the Claude Code iOS app that caused the session to hang.
  This entry was reverse-engineered from git history on 2026-03-06.

---

## v0.7.0 — 2026-03-03 — Radio Engine v7 + Comprehensive Markdown Audit

### Summary

Radio engine v7 with improved musical quality: 1.5-2.5x tempo (down from 2-4x),
2-4 instrument small band ensembles (down from 6-16), mood segments at multiples
of 42 seconds, 7 rondo structures with 6 arpeggio forms, harmonic consonance (Helmholtz/Hartmann)
enforcement, anti-click processing, diverse instrument family selection, and
comprehensive 32-issue markdown audit fixing all stale references across the project.

### Changes

- **Radio Engine v7** (`apps/audio/radio_engine.py`):
  - Tempo multiplier: 1.5x-2.5x (was 2x-4x) for more natural pacing
  - Instruments per mood: 2-4 small band (was 6-16) for tighter ensemble
  - Mood duration: multiples of 42s (42, 84, 126, 168, 210s) for longer development
  - 7 rondo patterns: ABACA, ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA (was 2)
  - 6 arpeggio forms: block, ascending, descending, alberti, broken, pendulum
  - harmonic consonance (Helmholtz/Hartmann) enforcement: rejects tritones in bass, enforces consonant intervals
  - Anti-click processing: 2ms micro-fades on notes, DC offset removal, 2-4s cosine crossfades
  - Diverse instrument families: strings, brass, woodwinds, keys, pitched percussion
  - 8kHz gentle lowpass on all loop output for smoother sound
  - Fixed piano/non-piano alternation with weighted family selection
- **32-issue markdown audit** (HIGH/MEDIUM/LOW):
  - Fixed test counts: Node.js 44→194, Perl 56→376
  - Fixed Perl filename: `simulator.pl` → `simulate.pl`
  - Fixed C++ standard: C++17 → C++20
  - Added audio app to README, CLAUDE.md, docs/apps_overview.md, docs/build_guide.md
  - Added 4 missing AST doc entries to AGENTS.md (wasm, typescript, swift, kotlin)
  - Updated roadmap version from v0.4.0 to v0.7.0
  - Fixed temperature inconsistencies (Quark ~10^6 K, Inflation ~10^9 K)
  - Fixed PHP server bind address documentation
  - Aligned compaction ratios between ast_introspection.md and ast_passing_efficiency.md
  - Updated app count from 15 to 16
  - Fixed Swift build commands (xcodeproj → SPM)
  - Created apps/audio/README.md
- **8 new v7 tests** in `test_radio_engine.py`:
  - Rondo patterns expanded (7 patterns)
  - Arpeggio forms (6 forms, ascending/descending verified)
  - Tempo multiplier range (1.5-2.5x)
  - Mood duration at 42s multiples
  - Plan segments at 42s multiples
- **30-minute cosmic radio v7 MP3** (`cosmic_radio_v7.mp3`)

### Test Results

- Python reference: 400 passed
- Audio radio engine: 36 passed (quick) + 8 new v7 tests
- Audio composer: 67 passed
- Audio music engine: 62 passed
- Total quick tests: 573+

### Files Created

- `apps/audio/README.md` — Audio engine documentation
- `apps/audio/cosmic_radio_v7.mp3` — 30-minute cosmic radio v7

### Files Modified

- `apps/audio/radio_engine.py` — Radio engine v7 improvements
- `apps/audio/test_radio_engine.py` — 8 new v7 tests, updated assertions
- `README.md` — Audio app added, test counts updated, app count updated
- `CLAUDE.md` — Audio test command, app count, file structure
- `AGENTS.md` — 4 missing AST doc entries added
- `RELEASE_HISTORY.md` — This entry
- `docs/apps_overview.md` — Audio section, test counts, temperature fixes
- `docs/build_guide.md` — Audio section, C++20, simulate.pl, test counts
- `docs/roadmap.md` — Version updated to v0.7.0
- `docs/ast_introspection.md` — Compaction ratios aligned
- `docs/ast_passing_efficiency.md` — Compaction ratios aligned
- `apps/nodejs/README.md` — Test count 44→194
- `apps/perl/README.md` — Test count 56→376, added 07_environment.t
- `apps/php/server.php` — Bind address documentation
- `apps/php/README.md` — Bind address documentation
- `apps/swift/README.md` — Build commands updated to SPM

---

## v0.6.0 — 2026-03-01 — Structured Music Engine + 40 Instrument Samples + Spectral Safety

### Summary

Complete music engine rewrite with bar-based time signature system, multi-track
mixing, 40 synthetic instrument samples, and spectral frequency filtering.
Eliminates harsh high-frequency and low-frequency noise. Music now uses proper
time signatures (4/4, 3/4, 6/8, 5/4, 7/8, etc.) with real chord progressions,
melodic phrases, bass lines, and percussion patterns.

### Changes

- **New structured music engine** (`apps/audio/music_engine.py`, ~1200 lines):
  - `MusicDirector`: Top-level orchestrator managing sections, tracks, and phrases
  - `TimeSignature` system: 12 time signatures (4/4, 3/4, 6/8, 7/8, 5/4, etc.)
  - `PhraseGenerator`: Creates melodic lines, bass patterns, chord voicings, drum patterns
  - `Track` / `DrumTrack`: Separate instrument voices with gain/pan control
  - `MixBus`: Multi-track mixer with highpass (80Hz) + lowpass (8kHz) filtering
  - `Section`: Musical sections (4-16 bars) with consistent style
  - `SampleBank`: Sample-based instruments with numpy-accelerated pitch shifting
  - `BiquadFilter`: Highpass/lowpass for frequency safety
- **40 synthetic instrument samples** (`apps/audio/sample_gen.py` + `apps/audio/samples/`):
  - Piano, electric piano, harpsichord, celesta (4 keyboard)
  - Violin, viola, cello, harp, pizzicato (5 strings)
  - Flute, clarinet, oboe, bassoon (4 woodwinds)
  - French horn, trumpet, trombone (3 brass)
  - Tubular bell, glockenspiel, vibraphone, singing bowl (4 bells)
  - Kick, snare, hi-hat (closed/open), cymbal, tom (6 percussion)
  - Sitar, koto, kalimba, gamelan gong, shakuhachi, didgeridoo (6 world)
  - Warm pad, string ensemble, choir, glass pad, cosmic drone (5 pads)
  - Acoustic bass, synth bass, electric bass (3 bass)
  - All stored as MP3, ~1.5MB total
- **Spectral safety**:
  - Highpass filter at 80Hz removes sub-bass rumble
  - Lowpass filter at 3-10kHz (epoch-dependent) removes harsh highs
  - Soft limiter prevents clipping (output always in [-1, 1])
  - Verified: sub-bass 3%, no energy above 8kHz
- **Performance**: 9.8x realtime (10-min MP3 in ~70 seconds rendering)
  - Sample preloading eliminates ffmpeg subprocess overhead during render
  - Numpy-vectorized pitch shifting and mixing
- **62 new tests** for music engine (`apps/audio/test_music_engine.py`)
- **10-minute MP3** (`cosmic_simulation_v2.mp3`) with structured music

### Test Results

- Python reference: 400 passed
- Audio tests: 36 passed
- Composer tests: 67 passed
- Music engine tests: 62 passed
- **Total: 565 tests passing**

### Files Created

- `apps/audio/music_engine.py` — Structured music engine
- `apps/audio/sample_gen.py` — Instrument sample generator
- `apps/audio/test_music_engine.py` — 62 tests for music engine
- `apps/audio/samples/*.mp3` — 40 instrument samples
- `cosmic_simulation_v2.mp3` — New 10-minute MP3

### Files Modified

- `apps/audio/generate.py` — Integrated new music engine via `--engine` flag

### Additional Changes (Turn 2)

- **AST parser documentation** for 4 new parsers:
  - `docs/wasm_ast.md`, `docs/typescript_ast.md`, `docs/swift_ast.md`, `docs/kotlin_ast.md`
- **AST self-introspection** added to all 14 simulation apps:
  - CLI apps: `--ast-introspect` flag (C, C++, Rust, Java, PHP, TypeScript, Ubuntu screensaver)
  - GUI/mobile apps: Utility classes (Swift iOS, Kotlin Android, macOS screensaver)
  - WASM: `introspect.rs` module with compile-time metrics
- **Updated CLAUDE.md** with new AST parser doc references
- **Test total**: 1219+ tests passing across all verified languages

---

## v0.5.1 — 2026-03-01 — Vectorized Mixing Pipeline + Parallel Encoding + AST Analysis

### Summary

Vectorized the audio mixing pipeline with numpy, achieving 5.2x rendering speedup.
Added pipelined MP3 encoding via background threading. Generated 10-minute enhanced
MP3 (13.7 MB, all epochs). Provided comprehensive AST utilization analysis.

### Changes

- **Vectorized mixing pipeline** in `apps/audio/generate.py`:
  - Composer output mixing: numpy slice assignment replaces per-sample Python loop
  - Pad mixing: vectorized array operations with numpy
  - Silence detection: `np.mean(np.abs(...))` replaces generator comprehension
  - Dark matter texture: fully vectorized with `np.sin`/`np.pi`
  - Atomic sonification: vectorized with `np.exp`/`np.sin`
- **Pipelined MP3 encoding**:
  - Background thread feeds PCM chunks to ffmpeg concurrently
  - `deque`-based queue with sentinel-based shutdown
  - Hides ffmpeg encoding latency behind audio rendering
- **Performance results**:
  - 500 ticks: 10.1s → 1.95s (5.2x improvement)
  - Projected 10-min render: ~30 min → ~19.5 min
  - Combined with numpy synthesis (previous commit): total ~7.3x vs initial
- **10-minute enhanced MP3** (`cosmic_simulation_enhanced.mp3`, 13.7 MB):
  - Traverses all epochs: Hadron → Present
  - 500 ticks/sec, seed 42, enhanced mode with world musical traditions
- **AST utilization analysis**: Comprehensive assessment of AST-passing infrastructure
  utilization, compression ratios, and recommendations for full adoption

### Test Results

- Python reference: 400 passed
- Audio tests: 36 passed
- Composer tests: 67 passed
- Total: 503 passed, 0 failed

### Agent Activity

- Explore agent: AST utilization research (13 parsers, 17.9 MB captures, session logs)
- Background render: 10-minute enhanced MP3 (~42 min render time, pre-numpy code)
- Profiling: cProfile of render_chunk identified simulation (75%) vs composer (24%) split

### Files Modified

- `apps/audio/generate.py` — Vectorized mixing, pipelined encoding, numpy atomic sonification
- `RELEASE_HISTORY.md` — This entry

### Files Created

- `cosmic_simulation_enhanced.mp3` — 10-minute enhanced cosmic simulation audio

---

## v0.5.0 — 2026-03-01 — Enhanced Musical Composition Engine + AST Bug Prevention Steering

### Summary

Added a rich musical composition engine (`apps/audio/composer.py`) that draws from
6000+ years of human musical tradition to create evolving soundscapes driven by
simulation state. Integrated with the existing audio renderer for enhanced mode.
Introduced AST-guided code generation as a formal steering practice for bug prevention.

### Changes

- **Composition engine** (`apps/audio/composer.py`, 1085 lines):
  - 40+ world musical scales (Western, Japanese, Chinese, Middle Eastern, Indian, African, gamelan)
  - 16 instrument timbre profiles via additive synthesis with wavetable oscillators
  - 20+ polyrhythmic patterns (3:2, 4:3, 5:4, West African bell, gamelan kotekan)
  - 15+ harmonic progressions (Bach, minimalist, drone, circle of fifths)
  - 15+ melodic motifs from public domain works (Bach, Mozart, Beethoven, Chopin, Debussy,
    Satie, Grieg, Dvořák, Sakura, Jasmine Flower)
  - Streaming oscillator architecture (StreamingOsc) for O(samples_per_tick) rendering
  - Beat engine with 10-90% presence oscillation guided by simulation epoch
  - 4-voice polyphonic melodic system with phrase queuing
  - Universe pocket navigation across simulation domains
  - Percussion synthesis (kick, snare, hihat, rim) with caching
- **Performance optimizations** in `apps/audio/generate.py`:
  - Wavetable-based gen_pad (27% faster)
  - Inlined lowpass filter coefficients (reduced function call overhead)
  - Optimized PCM conversion with local variable caching
  - Dark matter texture for silence prevention
  - `--basic` flag (enhanced is default)
- **67 new tests** in `apps/audio/test_composer.py` covering all components
- **AST-guided code generation steering** added to all three steering locations:
  - Pre-write protocol: symbols, dependencies, callers queries
  - Post-write protocol: parse, coverage_map queries
  - Bug class taxonomy: broken imports, type mismatches, dead code, duplicates, etc.
- **Steering triple cross-check**: Updated CLAUDE.md, AGENTS.md, .claude/steering-check.sh

### Files Created

- `apps/audio/composer.py` — Musical composition engine
- `apps/audio/test_composer.py` — 67 tests for composer

### Files Modified

- `apps/audio/generate.py` — Enhanced mode integration, performance optimizations
- `CLAUDE.md` — AST-guided code generation section + checklist item
- `AGENTS.md` — AST-guided code generation section + reflection principle
- `.claude/steering-check.sh` — Bug prevention cue + reflection principle update
- `RELEASE_HISTORY.md` — This entry

### Agent Activity

- AST introspection run on composer.py (44 symbols, 1628 result tokens, 6.7x compression)
- Dependency analysis confirmed zero external dependencies in composer.py
- Coverage map identified 36 testable paths in composer.py, all covered by tests
- Background MP3 generation (10 minutes, enhanced mode, ~27 minutes render time)

### Test Results

- Python reference: 400 passed
- Audio tests (generate.py): 36 passed
- Composer tests: 67 passed
- Total: 503 passed, 0 failed

---

## v0.4.1 — 2026-03-01 — 100% Test Coverage Expansion Across All 15 Languages

### Summary

Massive test coverage expansion toward 100% across all 15 language implementations.
Launched 11+ parallel agents to analyze coverage gaps and write tests for every
untested public API. Fixed probabilistic test flakiness, constructor default issues,
and gitignore conflicts. Total: ~11,900 lines of new test code across 47 files.

### Changes

- **Test coverage expansion**: Wrote comprehensive tests for every untested public
  function/method across all 15 language implementations
- **Node.js**: 44 → 147 tests — added coverage for WaveFunction, Particle, Spin,
  Color, EntangledPair, QuantumField, ElectronShell, Atom (all methods), AtomicSystem,
  Molecule, ChemicalReaction, ChemicalSystem, Biology (Gene, DNAStrand, Protein, Cell,
  Biosphere). Fixed Atom constructor default (electronCount: 0 → explicit neutral)
- **Perl**: 56 → 376 tests — expanded all test files (quantum, atomic, chemistry,
  biology, universe) plus new environment test file
- **PHP**: 309 → 464 tests — added Spin::value, WaveFunction::toArray, Particle
  mass/charge, EntangledPair, QuantumField (vacuum fluctuation, decohere, evolve,
  snapshot), ElectronShell, AtomicSystem (recombination, nucleosynthesis, bonds),
  ChemicalSystem (catalyzed reaction, snapshot), biology toCompact, Epoch::description,
  Color enum, Gene::demethylate, Cell fitness/divide edge cases. Fixed UV mutation
  flakiness (intensity 50→5000)
- **Go**: suite → 112 tests — 29 new test functions for biology (20), atomic (4),
  chemistry (4), environment (1). Used `git add -f` for gitignore workaround
- **C**: 213 → 307 assertions — 14 new test functions for wf_collapse,
  vacuum_fluctuation, recombination, stellar_nucleosynthesis, epoch setters, universe_run
- **C++**: suite → 356 assertions — 17+ methods including spinValue, WaveFunction
  collapse, QuantumField annihilate/vacuumFluctuation, ElectronShell lifecycle, Atom
  ion/bondEnergy, AtomicSystem recombination/nucleosynthesis, ChemicalSystem formAminoAcid/
  formNucleotide, Gene epigenetic methods, Protein length
- **Rust**: 240 → 261 tests — 19 new tests for vacuum_fluctuation, decohere,
  stellar_nucleosynthesis, attempt_bond, catalyzed_reaction. Fixed flaky
  vacuum_fluctuation_high_temp test
- **Java**: suite → 682 tests — new TestParticle.java (86 tests) and TestMolecule.java
  (32 tests), expanded all existing test classes
- **TypeScript**: 44 → 157 tests — comprehensive coverage of all audio sonification
  and simulation modules
- **Kotlin**: expanded to 331 tests (syntax verified, no Android SDK)
- **Swift**: expanded to 535 tests (syntax verified, no Swift compiler)
- **WASM**: expanded to 134 tests — new test modules for atomic, biology, chemistry,
  quantum, universe
- **macOS screensaver**: expanded to 407+ additional test lines

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | 112   | PASS   |
| Rust     | 261   | PASS   |
| C        | 307   | PASS   |
| C++      | 356   | PASS   |
| Node.js  | 147   | PASS   |
| Perl     | 376   | PASS   |
| PHP      | 464   | PASS   |
| Java     | 682   | PASS   |
| TypeScript | 157 | PASS   |
| WASM     | 134   | PASS   |
| Kotlin   | 331   | SYNTAX OK |
| Swift    | 535   | SYNTAX OK |

### Agent Activity (this session)

1. Go coverage agent — filled 29 untested functions
2. C coverage agent — filled 14 untested functions (307 assertions)
3. C++ coverage agent — filled 17+ untested methods (356 assertions)
4. Rust coverage agent — filled gaps, fixed flaky test (261 tests)
5. Node.js/Perl/PHP/Java analysis agent — identified coverage gaps
6. Node.js coverage agent — expanded from 44 to 147 tests
7. Perl coverage agent — expanded from 56 to 376 tests
8. PHP coverage agent — expanded from 309 to 464 tests
9. Java coverage agent — expanded to 682 tests, 2 new test files
10. TypeScript/WASM/screensaver agent — expanded TS to 157, WASM to 134
11. Kotlin coverage agent — expanded to 331 tests
12. Swift coverage agent — expanded to 535 tests

### Files Modified (40+ files)

- `apps/c/test_simulator.c` (+263 lines)
- `apps/cpp/test_simulator.cpp` (+461 lines)
- `apps/go/simulator/simulator_test.go` (+860 lines)
- `apps/java/src/test/java/...` (9 files, +1,180 lines, 2 new files)
- `apps/kotlin/app/src/test/java/...` (7 files, +2,003 lines)
- `apps/nodejs/test/test_simulator.js` (+1,010 lines)
- `apps/perl/t/` (6 files + 1 new, +1,532 lines)
- `apps/php/tests/run_tests.php` (+594 lines)
- `apps/rust/src/simulator/` (3 files, +353 lines)
- `apps/swift/Tests/SimulatorTests/` (7 files, +2,095 lines)
- `apps/typescript/src/test.ts` (+670 lines)
- `apps/wasm/src/` (5 files, +294 lines)
- `apps/screensaver-macos/Tests/SimulatorTests.swift` (+407 lines)
- `RELEASE_HISTORY.md` — This entry

---

## v0.4.0 — 2026-03-01 — Steering Infrastructure, Session Logging, and CI Fix

### Summary

Major expansion of project governance infrastructure. Fixed CI pipeline failure,
added comprehensive steering enforcement via gVisor hooks, established session
logging protocol with historical reconstruction, created feature roadmap, and
ensured all markdown files reference each other coherently.

### Changes

- **CI fix**: Added `pip install pytest` step to `python-tests` job in
  `.github/workflows/ci.yml` — the root cause of the CI failure on the branch
- **CLAUDE.md**: Major rewrite (192→730+ lines) pulling in steering content from
  `docs/steering.md` — CueSignal protocol, AgentState tracking, token efficiency
  data, session logging protocol, markdown consistency checks, test coverage
  enforcement, self-cueing/gVisor enforcement, cross-compilation guidance,
  release history update mandate, triple cross-check reflection principle
- **AGENTS.md**: Major rewrite with same enhancements — session logging, release
  history, markdown review, test coverage, gVisor self-cueing, reflection principle
- **gVisor self-cueing**: Created `.claude/settings.json` and
  `.claude/steering-check.sh` — hook-based enforcement of steering rules with
  FAIL-CUE markers that prompt the agent to complete all per-turn tasks. Includes
  triple cross-check requirement (CLAUDE.md + AGENTS.md + gVisor hooks).
- **Session logs**: Reconstructed `v0.1.0-session.md` and `v0.2.0-session.md` from
  git history; created `v0.4.0-session.md` with full transcript detail
- **Feature roadmap**: Created `docs/roadmap.md` covering containerization
  (Docker/Colima), deployment target matrix, metacognitive steering enhancements,
  cross-language consistency automation, performance benchmarking
- **Network surface clarification**: Updated steering to note Go SSE server and PHP
  HTTP server are intentional localhost web servers for end-user use
- **Release history mandate**: Added to steering checklist — RELEASE_HISTORY.md must
  be updated at every conversation turn

### Test Results (this session)

| Language | Tests | Result |
|----------|-------|--------|
| Python   | 400   | PASS   |
| Go       | suite | PASS   |
| Rust     | 240   | PASS   |
| C        | 213   | PASS   |
| C++      | suite | PASS   |
| Node.js  | 44    | PASS   |
| Perl     | 56    | PASS   |
| PHP      | 309   | PASS   |

### AST Passing Stats (this session)

- AST introspection ran on simulator modules: quantum.py (30 symbols),
  universe.py (14 symbols), biology.py (40 symbols), constants.py
- Pre-computed captures in `ast_captures/` validated

### Agent Activity (this session)

1. Codebase exploration agent — exhaustive file inventory and structure analysis
2. CLAUDE.md rewrite agent — comprehensive steering document
3. AGENTS.md rewrite agent — comprehensive multi-agent protocol
4. Feature roadmap agent — created `docs/roadmap.md`
5. Session log v0.1 agent — reconstructed from git history
6. Session log v0.2 agent — reconstructed from git history

### Files Created

- `.claude/settings.json` — gVisor hook configuration
- `.claude/steering-check.sh` — Steering enforcement script
- `docs/roadmap.md` — Feature roadmap
- `session_logs/v0.1.0-session.md` — Reconstructed session log
- `session_logs/v0.2.0-session.md` — Reconstructed session log
- `session_logs/v0.4.0-session.md` — This session's log

### Files Modified

- `.github/workflows/ci.yml` — Added pytest install step
- `CLAUDE.md` — Major rewrite with steering enhancements
- `AGENTS.md` — Major rewrite with steering enhancements
- `RELEASE_HISTORY.md` — Added v0.4.0 entry

---

## v0.3.0 — 2026-03-01 — Comprehensive Testing, Documentation, and Store Deployment Guides

### Summary

Major expansion adding tests to all 15 language implementations, comprehensive
documentation generation infrastructure, App Store and Play Store deployment guides,
and project-wide steering files for AI-assisted development.

### Changes

- **README.md**: Created top-level README documenting the full project — simulation
  overview, 15 applications, testing commands, AST-passing workflow, cross-compiled
  releases, and project structure
- **CLAUDE.md**: Created agent steering file for Claude Code and similar LLM tools —
  AST-passing protocol, coding principles (minimal dependencies, zero network surface),
  documentation standards, test commands
- **AGENTS.md**: Created multi-agent coordination protocol — swarm architecture,
  token budget guidelines, file locking conventions, commit format, cross-language
  consistency checks
- **Tests added** for: Go, Rust, C, C++, Java, PHP, TypeScript, Kotlin, Swift,
  WebAssembly, macOS screensaver, Ubuntu screensaver
- **CI/CD updated**: All test suites now run in the CI pipeline (`.github/workflows/ci.yml`)
  including Go test, Rust test, C test, C++ ctest, Java test runner, PHP test, TypeScript test
- **Documentation generation**: Added Doxygen configs for C and C++; all languages
  already have doc comments (JSDoc, PHPDoc, Javadoc, KDoc, Swift Markup, godoc, rustdoc, POD)
- **iOS App Store guide**: End-to-end instructions from zero to App Store release,
  using only Xcode (no Homebrew) — covers developer account, signing, simulator,
  TestFlight, and public release
- **Android Play Store guide**: End-to-end instructions from zero to Play Store release,
  using Android Studio — covers developer account, signing, emulator, internal testing,
  and production release
- **Session log infrastructure**: Created `session_logs/` directory for tracking
  development history across conversation turns
- **Release history**: This file, tracking the evolution of the project

### Agent Activity (this session)

This session used dictation mode for user input. The following agents were spawned:
1. Codebase exploration agent — mapped all 200+ files across 15 apps
2. Go test agent — created `apps/go/simulator/simulator_test.go`
3. Rust test agent — added `#[cfg(test)]` modules to all simulator source files
4. C/C++ test agent — created `test_simulator.c` and `test_simulator.cpp`, updated Makefiles
5. Java/PHP test agent — created Java test classes and PHP test runner
6. TypeScript/Kotlin/Swift test agent — created test suites for each
7. WASM/screensaver test agent — added tests for WebAssembly and screensaver simulator logic
8. iOS App Store documentation agent — wrote comprehensive Xcode-only deployment guide
9. Android Play Store documentation agent — wrote comprehensive Android Studio deployment guide

---

## v0.2.0 — 2026-02-28 — AST DSL Engine and Multi-Language Implementations

### Summary

Added the AST-passing DSL framework, reactive agent protocol, and all 15 language
implementations of the cosmic physics simulator.

### Changes

- **AST DSL**: Core engine (`ast_dsl/core.py`) with universal ASTNode, query/result
  protocol, performance metrics, and compact serialization
- **Reactive protocol**: Agent-pair state management (`ast_dsl/reactive.py`)
- **Language parsers**: 13 parsers covering Python, JS, TS, Go, Rust, C, C++, Java,
  Perl, PHP, Swift, Kotlin, WebAssembly
- **Introspection**: Cross-project analysis tool (`ast_dsl/introspect.py`)
- **15 applications**: Python CLI, Node.js CLI, Perl CLI, Go CLI+SSE, Rust CLI,
  C CLI, C++ CLI, Java GUI, TypeScript Audio, WebAssembly, PHP Snapshot,
  Swift iOS, Kotlin Android, macOS Screensaver, Ubuntu Screensaver
- **CI/CD**: GitHub Actions workflows for testing and cross-platform release builds
- **Documentation**: Comprehensive walkthrough, steering guide, per-app docs

---

## v0.1.0 — Initial Release — Python Reference Implementation

### Summary

Initial implementation of the cosmic physics simulator in Python.

### Changes

- **Simulator modules**: quantum.py, atomic.py, chemistry.py, biology.py,
  environment.py, universe.py, constants.py, terminal_ui.py
- **Test suite**: 400+ pytest tests covering all physics subsystems
- **Demo runner**: `run_demo.py` for interactive simulation
