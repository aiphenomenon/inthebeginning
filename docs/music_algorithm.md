# Music Algorithm -- In The Beginning Radio

How the radio engine turns a physics simulation into a 30-minute musical journey.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Instrument System](#instrument-system)
4. [Mood Segments](#mood-segments)
5. [MIDI Sampling](#midi-sampling)
6. [Synthesis](#synthesis)
7. [Mixing and Spatialization](#mixing-and-spatialization)
8. [Orchestration](#orchestration)
9. [Voice Narration](#voice-narration)
10. [Volume and Mastering](#volume-and-mastering)
11. [Solo Moods](#solo-moods)

---

## Overview

In The Beginning Radio is a generative music engine that produces continuously
evolving audio driven by a cosmic physics simulation. The simulation models the
universe from the Big Bang through the emergence of life -- 13 epochs spanning
from the Planck era to the Present day -- and the engine translates each epoch's
physical state (temperature, particle counts, atomic density, molecular complexity)
into musical parameters.

The engine can produce:

- **30-minute cosmic radio broadcasts** -- the standard format, a single MP3
  file that evolves through all 13 simulation epochs
- **Album-length renders** -- any duration, from a few minutes to hours
- **Infinite streaming** -- segment-by-segment rendering that writes directly
  to disk, keeping memory usage bounded regardless of duration

The creative vision: map the universe's story into sound. The sparse, alien Planck
era uses drone scales and slow tempos. As matter forms during nucleosynthesis, the
music warms into Dorian and Mixolydian modes. By the time stars ignite, bright
Lydian melodies emerge. Life's arrival brings blues and pentatonic grooves.
Throughout, classical MIDI phrases from 26 composers (Bach, Beethoven, Mozart,
Chopin, and others) are woven into the texture -- transposed, re-scaled, and
adapted to each epoch's harmonic character.

Everything is synthesized from scratch. No audio samples are loaded at runtime.
The entire engine runs on Python's standard library plus optional numpy for speed.

---

## Architecture

The engine is built as a class hierarchy where each version inherits from a
previous one, adding fixes and features while preserving the core synthesis
pipeline.

### Version Lineage

```
RadioEngine (V7) -- the foundation
  |
  +-- RadioEngineV8 -- orchestral layering, anti-hiss, bar quantization
       |
       +-- RadioEngineV9 -- 50+ new instruments, 15 family pools
       |    |
       |    +-- RadioEngineV10 -- GM timbre profiles, 4-6 voices
       |         |
       |         +-- RadioEngineV11 -- consonance engine, voice leading, gain staging
       |
       +-- RadioEngineV12 -- V8 synthesis + expanded catalog + multiprocessing
       |
       +-- RadioEngineV15 -- authentic V8 synthesis (pure Python), V12 tempo
            |
            +-- RadioEngineV18 -- clean mixing, quality gating, soft-knee limiter
                 |
                 +-- RadioEngineV18Orchestra -- 15 family pools, variety enforcement
                      |
                      +-- RadioEngineV20 -- master normalization, solo moods (CURRENT)
```

### What Each Version Added

**V7** (RadioEngine): The foundation. 537 synthesized instruments, mood segments
at 42-second boundaries, 7 rondo structures (ABACA, ABACADA, ABCBA, etc.),
6 arpeggio forms, MIDI phrase sampling, TTS voice injection, Schroeder reverb,
6-second morph transitions between moods.

**V8**: Simultaneous multi-instrument orchestral sections (75% of the time,
multiple instruments play together like an orchestra section). Anti-hiss spectral
filtering. Subsonic frequency removal (30 Hz highpass). Note duration quantization
to fit bar structures. Guaranteed compound/complex time signatures in every
10-minute window.

**V9**: Expanded the instrument catalog from 5 to 15 family pools, adding rock
guitars, synthesizers, world instruments, saxophones, and mallets. Density-aware
tempo (1.1x-2.1x) that slows down when the simulation gets busy.

**V10**: GM (General MIDI) timbre-aware synthesis -- each instrument family gets
a distinct volume shape, brightness, and harmonic character instead of a generic
organ-like tone. 4-6 voices per segment. 8-second morph transitions.

**V11**: The "audio quality overhaul." Inter-voice consonance scoring to prevent
random clashing between instruments. Voice leading for smooth chord transitions.
Proper gain staging with separated pan and volume controls. Reduced reverb
resonance. Pre-reverb highpass at 150 Hz. Orchestral role assignment (melody,
harmony, foundation, bass, color).

**V15**: Returns to V8's authentic pure-Python synthesis path (which had a warmer
sound than the numpy-accelerated version), combined with V12's density-aware tempo.

**V18**: Clean mixing fixes inherited from V11 -- separated pan and gain, quality
gating (noise instruments excluded from melodic roles), soft-knee limiter on the
loop buffer, 5ms anti-click fades. Tempo tightened to 1.1x-1.45x.

**V18 Orchestra**: Expands V18 from 5 to 15 instrument family pools. Enforces
variety -- tracks which families have been used and biases toward under-represented
ones past the halfway point. Higher instrument coloring (0.35-0.55) to preserve
each instrument's identity (so a xylophone sounds like a xylophone, not a
generic tone).

**V20** (current): Master normalization to -1 dB peak. Lookahead limiter for
transient control. Fixed gain staging (removed a double-attenuation bug). Solo
moods (15% chance) where a single instrument plays the melody alone. Multi-engine
TTS support (Silero, espeak-ng, flite, festival, pico2wave). Streaming render
pipeline for memory-safe long renders.

---

## Instrument System

### Generating 537 Instruments

The `InstrumentFactory` generates 537 unique instruments by combining **10
synthesis techniques** with **51 timbral families** and seeded randomization.

**Synthesis techniques** (each shapes how sound is produced):

| Technique | Character |
|---|---|
| `additive` | Stacks pure tones (harmonics) at different loudnesses |
| `fm` | One wave shape modulates another, creating metallic or bell-like tones |
| `plucked` | Harmonics decay rapidly like a guitar string |
| `bowed` | Sustained harmonics with subtle variation, like a violin |
| `blown` | Odd-numbered harmonics dominate, like a clarinet or flute |
| `struck` | Slightly out-of-tune harmonics, like a bell or gong |
| `pad` | Soft, sustained washes of sound |
| `bass` | Emphasis on low harmonics |
| `bell` | Inharmonic (not perfectly tuned) overtones for metallic shimmer |
| `noise_perc` | Pitched noise burst with a tonal center, like a snare or shaker |

**Timbral families** (51 named templates that influence harmonic profile and
volume shape): piano, organ, harpsichord, celesta, marimba, violin, viola, cello,
bass, harp, guitar, flute, oboe, clarinet, bassoon, piccolo, trumpet, horn,
trombone, tuba, bell, glockenspiel, vibraphone, xylophone, chimes, kick, snare,
hihat, tom, cymbal, shaker, sitar, koto, kalimba, erhu, shamisen, banjo,
shakuhachi, didgeridoo, bagpipe, accordion, and various synth/pad variants.

Each instrument is generated by picking a technique, feeding it through a
seeded random number generator, and producing:

- A **harmonic profile**: which overtones are present and how loud each is
- A **volume shape** (ADSR): how the note starts (attack), drops to its
  sustained level (decay), holds (sustain), and fades out (release)
- **Vibrato** settings: how fast and how deep the pitch wobbles (only 15% of
  instruments get noticeable vibrato; the rest are nearly straight-toned)
- **Noise level**: a small amount of breath or scratchiness
- **Distortion**: optional harmonic saturation (20% of instruments)
- A **musical role**: melody, harmony, bass, or rhythm (assigned by technique)

### Volume Shape (ADSR)

Every note follows a four-stage volume curve:

1. **Attack**: the note ramps up from silence (0.001s for a percussive strike to
   0.8s for a slow pad swell)
2. **Decay**: the initial burst settles down to the sustained level
3. **Sustain**: the note holds at a steady volume (between 20% and 95% of peak)
4. **Release**: after the note ends, it fades to silence (0.05s to 2s)

These four parameters give each instrument its feel -- a piano has fast attack,
quick decay, moderate sustain; a pad has slow attack, minimal decay, high sustain.

### Instrument Rotation

Every 14 mood segments, the engine swaps out 50 synthetic instruments for fresh
ones with different seeds. This keeps the sound evolving over long renders and
prevents the listener from hearing the same timbres loop. Only synthesized
instruments are rotated -- sample-based instruments (from FluidSynth) are kept.

### 15 Instrument Family Pools

For orchestral selection, instruments are organized into 15 General MIDI family
pools:

| Family | Instruments |
|---|---|
| Strings | Violin, Viola, Cello, Contrabass, Tremolo Strings, Pizzicato, Harp |
| Brass | Trumpet, Trombone, Tuba, French Horn, Brass Section |
| Woodwinds | Oboe, English Horn, Bassoon, Clarinet, Piccolo, Flute, Recorder, Pan Flute |
| Keys | Pianos, Organs, Harpsichord, Celesta |
| Pitched Perc | Vibraphone, Tubular Bells, Harp |
| Rock Guitar | Jazz Guitar, Muted, Overdriven, Distortion |
| Rock Bass | Electric Bass (Finger, Pick), Slap Bass |
| Synth Lead | Square, Sawtooth, Calliope |
| Synth Pad | New Age, Polysynth, Choir, Bowed, Halo, Sweep |
| Synth FX | Rain, Soundtrack, Crystal, Atmosphere, Brightness, Echoes, Sci-Fi |
| World | Sitar, Banjo, Shamisen, Koto, Kalimba, Bagpipe, Fiddle, Shanai |
| Sax | Soprano, Alto, Tenor, Baritone |
| Choir | Choir Aahs, Voice Oohs, Synth Voice |
| Symphonic Ext | Timpani, String Ensemble 2, Orchestra Hit, Muted Trumpet |
| Mallets | Glockenspiel, Music Box, Xylophone, Dulcimer, Steel Drums |

The engine groups these into 5 macro-groups (symphonic, keys/percussion, world/
ethnic, electronic, classical) and enforces variety: past the halfway point of a
render, the engine biases instrument selection toward under-represented groups so
the full orchestral palette is heard across the piece.

---

## Mood Segments

### The 42-Second Building Block

Music is generated in **mood segments** -- discrete blocks of musical character.
Each segment has a duration that is a multiple of 42 seconds: 42, 84, 126, 168,
or 210 seconds. The 42-second quantum was chosen for mood development -- long
enough for a musical idea to develop, short enough for variety.

### How Simulation Drives Music

Each mood segment reads the simulation's current state and derives its musical
parameters:

**Root note**: Each epoch has a base MIDI note (Planck = C3, Inflation = D3,
up to Present = C5). The simulation's particle count shifts this up or down by
up to 6 semitones, sampling from "different regions of space."

**Scale**: Each epoch has a palette of scales drawn from world music traditions:

| Epoch | Scales | Character |
|---|---|---|
| Planck | chromatic, drone, whole tone | Alien, formless |
| Inflation | pentatonic major, drone, whole tone | Expanding, hollow |
| Electroweak | Phrygian, Hirajoshi, Hijaz | Tense, mysterious |
| Quark | Hirajoshi, In-sen, Bhairav | Dense, mystical |
| Hadron | pentatonic minor, Yo, Aeolian | Dark, primal |
| Nucleosynthesis | Dorian, Mixolydian, Rast | Warming, earthy |
| Recombination | pentatonic major, Gong, Yaman | Brightening |
| Star Formation | Lydian, Hijaz, harmonic minor | Radiant, dramatic |
| Solar System | Ionian, harmonic minor, Gong | Majestic |
| Earth | Aeolian, Miyako-bushi, Nahawand | Grounded, complex |
| Life | blues, pentatonic minor, Malkauns | Rhythmic, vital |
| DNA Era | melodic minor, Bhairavi, Dorian | Intricate |
| Present | Ionian, Dorian, pentatonic major, Lydian | Triumphant, varied |

The engine includes 30 scales from Western, Japanese, Chinese, Middle Eastern,
and Indian traditions, organized into 5 families: bright, dark, mystical, earthy,
and cosmic.

**Tempo**: Derived from the epoch's temperature range. Early hot epochs get
slower tempos (50-70 BPM for Planck); later epochs get faster (100-140 BPM for
Present). The simulation temperature maps logarithmically onto this range. V20
applies a density-aware tempo multiplier of 1.1x-1.45x, capping during busy
epochs to prevent cacophony.

**Time signature**: Each epoch favors certain meters. Planck prefers 3/4 and 3/2
(waltz-like, floating). Present allows everything including 5/4, 7/8, and
additive meters like 3+3+2/8. The engine uses 17 time signatures drawn from
classical and world music, enforcing that 70% are simple meters with
compound/complex meters guaranteed in every 10-minute window.

**Density** (how many instruments): Early sparse epochs (density 0.1 for Planck)
use fewer instruments. Dense late epochs (0.95 for Present) use more. The engine
picks 2-4 instruments per segment, modulated by a sine function of the segment
index for organic variation.

### Morph Transitions

When one mood ends and the next begins, there is no hard cut. Instead, the
engine applies a **6-8 second crossfade morph** (V20 uses 8 seconds) using a
cosine curve. The outgoing segment fades down while the incoming segment fades
up, creating a smooth blend. Voice narration is injected during these morph
windows (see [Voice Narration](#voice-narration)).

### Scale Families

Scales are grouped into families for harmonic compatibility:

- **Bright**: Ionian, Lydian, Mixolydian, pentatonic major, Yaman
- **Dark**: Aeolian, Phrygian, harmonic minor, Hijaz, Bhairav
- **Mystical**: whole tone, Hirajoshi, In-sen, Malkauns
- **Earthy**: Dorian, pentatonic minor, blues, Yo, Gong
- **Cosmic**: chromatic, drone, Iwato, Miyako-bushi

---

## MIDI Sampling

### The Classical Library

The engine includes 744 MIDI files from 26 public-domain composers spanning
the Renaissance through the Late Romantic era (~1400-1920). Sources include
works by Bach, Beethoven, Mozart, Chopin, Brahms, Debussy, Tchaikovsky,
Vivaldi, Handel, Schubert, and others.

These MIDI files are not played back directly. Instead, the engine:

1. **Extracts note sequences** from each file -- pitch, timing, duration,
   and velocity for every note across all tracks
2. **Samples multi-bar phrases** from random positions within the composition
3. **Transposes** the phrase to the current mood's root note by calculating the
   phrase's center pitch and shifting all notes to match
4. **Snaps notes to the current scale** -- each note is moved to the nearest
   pitch class in the active scale (e.g., a G# from a Bach piece might become
   a G natural if the current scale is Dorian)
5. **Quantizes timing** to the bar grid -- note onsets snap to 16th-note
   positions, durations snap to standard note values (whole, half, quarter,
   eighth, sixteenth)

### Loop Friendliness

When selecting a phrase from a MIDI file, the engine scores how well the segment
would loop by checking three qualities:

- **Pitch class overlap** at boundaries: do the notes at the start and end of
  the phrase share pitch classes? (weight: 40%)
- **Note density balance**: is the note count similar in the first and second
  halves? (weight: 30%)
- **Clean endings**: do notes end near the segment boundary rather than being
  cut mid-sustain? (weight: 30%)

The engine tries up to 3 starting positions in each MIDI file and picks the one
with the best loop score.

### FluidSynth Rendering

When FluidSynth is available with the FluidR3_GM SoundFont, the engine can
render MIDI phrases through a full General MIDI synthesizer. For the primary
voice in the first A-section of a rondo, the engine creates a temporary MIDI
file with the target instrument, renders it through FluidSynth at 44.1 kHz, and
mixes the resulting stereo audio into the segment. This gives one voice per
segment a realistic sampled sound alongside the other synthesized voices.

### Fallback Generation

When no MIDI files are available (or the `mido` library is not installed), the
engine generates phrases algorithmically by walking through the current scale
in random steps, choosing note durations from standard values (quarter, eighth,
half notes), and adding occasional octave jumps for interest.

---

## Synthesis

### Building Sound from Wave Shapes

All sound in the engine is built from basic wave shapes -- primarily sine waves
at different pitches stacked on top of each other. This is **additive synthesis**:
the fundamental pitch plays loudest, and integer multiples of that pitch
(harmonics/overtones) are layered on top at decreasing volumes.

A pure sine wave sounds like a tuning fork. Adding the 2nd harmonic (twice the
pitch, half the volume) warms it up. Adding odd harmonics (3rd, 5th, 7th) makes
it hollow like a clarinet. Adding many harmonics with random amplitudes makes it
bright like a violin. Each instrument's harmonic profile defines its tone color.

The core synthesis function (`_synth_note_np`) works like this:

1. Generate a time array at 44,100 samples per second
2. Calculate the ADSR volume shape
3. Add vibrato: a slow pitch wobble (4-6 Hz) that fades in after a delay, giving
   the note a human quality
4. For each harmonic, compute a sine wave at that multiple of the fundamental
   pitch, scaled by the harmonic's amplitude
5. Sum all harmonics together
6. Optionally add noise (breath, scratch) and distortion (soft clipping via tanh)
7. Multiply by the volume shape and note velocity

### Colored Notes

The engine's signature sound comes from **colored notes** -- a blend of two
layers:

- **Base layer** (75% by default): a clean, piano-like tone built from 8
  harmonics with a gentle 1/h^1.2 rolloff. This gives every note a smooth,
  musical foundation.
- **Color layer** (25% by default): the instrument's own harmonic profile,
  vibrato, and character, but with noise and distortion suppressed for
  cleanliness.

The blend ratio (`color_amount`) varies by engine version. V18 Orchestra uses
0.35-0.55 to let instruments retain more identity. Solo moods use 0.35-0.55
as well, since a single exposed instrument needs its character to carry the
music.

### FM Synthesis

For instruments with the `fm` technique, the engine uses frequency modulation:
one sine wave (the modulator) controls the pitch of another (the carrier). The
modulator's depth decays over time (multiplied by e^(-3t)), creating a
characteristic "plinking" or metallic attack that settles into a pure tone.

The modulator-to-carrier ratio is chosen from musically useful values: 1:1
(warm), 1.5:1, 2:1 (octave), 3:1 (bright), 7:1 or 14:1 (metallic/bell-like).

---

## Mixing and Spatialization

### Stereo Placement

Each voice in a segment is assigned a pan position in the stereo field.
Positions are drawn from a pool: -0.6, -0.2, 0.2, 0.6 (left to right), giving
a natural spread without extreme hard-panning.

The V18/V20 engine uses **equal-power panning** (cosine/sine pan law): as a
voice moves from left to right, its total perceived loudness stays constant.
The left gain is `cos((pan+1) * pi/4)` and the right gain is
`sin((pan+1) * pi/4)`.

### Reverb

The engine implements a **Schroeder reverb** -- a classic algorithmic reverb
built from:

1. **4 comb filters** at delays of 30, 37, 41, and 44 milliseconds. Each comb
   filter feeds its output back into its input at reduced volume (feedback
   gains: 0.62, 0.60, 0.58, 0.55 in V11+; higher in earlier versions), creating
   a decaying echo trail.
2. **2 allpass filters** at 5ms and 1.7ms that diffuse the echoes without
   adding color, smearing the distinct repeats into a smooth wash.

The reverb is mixed at 20-30% wet (V11+ uses 20%) with the original signal.

V11+ applies a **pre-reverb highpass** at 150 Hz to prevent low-pitch content
from turning into muddy rumble in the reverb tail.

### Early Reflections

Before the main reverb, the engine adds **early reflections** -- 5 delayed
copies of the signal at 11, 17, 23, 31, and 41 milliseconds with decreasing
amplitudes (0.20 down to 0.05 in V11+). These simulate the first bounces off
nearby walls and give the sound a sense of being in a small room or chamber.

### Chorus

An optional **chorus effect** creates the illusion of multiple performers by
adding a slightly delayed copy of the signal with a slowly wobbling delay time.
The base delay is 20ms, modulated by +/-3ms at 0.7 Hz. The chorus copy is mixed
at 30% with the original at 70%.

### Stereo Cross-Feed

A gentle stereo smoothing pass bleeds 10-15% of each channel into the other,
creating a more natural, less "headphone-y" stereo image.

### Soft-Knee Limiting

After all effects, the engine applies a **soft-knee limiter** to prevent
clipping. Below the knee threshold (0.85 in V20), the signal passes unchanged.
Above it, excess amplitude is compressed via tanh saturation, creating a smooth
ceiling rather than a hard clip.

---

## Orchestration

### Role Assignment

The `OrchestratorV11` assigns each voice in a segment to a complementary role,
preventing instruments from competing for the same frequency range:

| Role | Register Shift | Loudness | Rhythmic Character |
|---|---|---|---|
| Foundation | -12 semitones (one octave down) | 80% | Sustained, long tones |
| Harmony Low | No shift | 55% | Chordal patterns |
| Harmony Mid | No shift | 50% | Chordal patterns |
| Melody | +12 semitones (one octave up) | 100% | Melodic lines |
| Color | +12 semitones | 30% | Textural, decorative |
| Bass Deep | -24 semitones (two octaves down) | 70% | Sustained, anchoring |

For small ensembles (2-4 voices, the norm in V20), the engine picks a focused
subset: foundation + harmony + melody for trios, adding a second harmony voice
for quartets.

### Consonance Scoring

The `ConsonanceEngine` prevents dissonance between voices by scoring all
notes sounding simultaneously against a table of interval pleasantness:

| Interval | Score | Character |
|---|---|---|
| Unison | 1.0 | Perfect |
| Perfect 5th | 0.95 | Strong, open |
| Perfect 4th | 0.8 | Stable |
| Major 3rd | 0.75 | Sweet |
| Minor 3rd | 0.7 | Warm |
| Major 6th | 0.75 | Pleasant |
| Minor 6th | 0.7 | Gentle |
| Major 2nd | 0.3 | Mild tension |
| Minor 7th | 0.3 | Jazzy tension |
| Major 7th | 0.2 | Sharp tension |
| Tritone | 0.15 | Strong tension |
| Minor 2nd | 0.05 | Harsh |

If the composite consonance score falls below 0.55, the engine iteratively
adjusts the most dissonant voice by trying nearby notes (+/-1 or 2 semitones,
snapped to the current scale) up to 5 times until the score improves.

### Voice Leading

When chords change, the engine minimizes the distance each voice moves. Instead
of all voices jumping to new positions in parallel, each voice slides to the
nearest available note in the new chord. If the jump would be larger than an
octave, the engine octave-transposes the target note to bring it closer. This
creates smooth, connected harmonic motion.

### Chord Building

Single MIDI notes are expanded into 2-4 note chords using diatonic harmony.
The engine looks up the chord quality for each scale degree (major, minor,
diminished, augmented) and builds the chord from scale tones. Consonance
checking ensures the result sounds pleasant.

The engine includes 11 chord progressions (I-V-vi-IV, circle of fifths, Bach
C major, Romantic, Debussy-style, and others) and 7 rondo structures (ABACA,
ABACADA, ABCBA, AABBA, ABCDA, ABACBA, AABA) that organize how chord sections
are arranged within a mood segment.

---

## Voice Narration

### Multi-Engine TTS

The engine injects spoken word segments during mood transitions, using a
cascade of text-to-speech engines:

1. **Silero** (preferred): A neural TTS model (Apache 2.0 license) with 118
   English speaker voices. Produces natural-sounding speech. Requires PyTorch.
2. **espeak-ng** (primary fallback): An open-source speech synthesizer with 7
   English voice variants (US, British RP, Scottish, Welsh, Caribbean). Speed
   and pitch adjust based on the current simulation epoch.
3. **flite** (secondary fallback): Carnegie Mellon's lightweight synthesizer
   with 5 voice variants.
4. **festival** (tertiary fallback): University of Edinburgh's system, using
   the `text2wave` command.
5. **pico2wave** (last resort): SVOX's compact synthesizer with US and British
   English.

The engine tries each in order, falling back gracefully if one is unavailable.
Voice selection is influenced by the epoch index, so early cosmic epochs might
get a different speaker than later biological epochs.

### What Gets Spoken

The engine generates speech from two sources:

- **Source code readings**: Random lines from the project's Python source files
  (simulator, audio engine, AST parser) are extracted, cleaned of syntax
  characters, and spoken aloud. This creates an otherworldly effect of the
  universe "reading its own source code."
- **Cosmic phrases**: Fallback phrases like "the universe expands from a
  singularity" and "quantum fluctuations give rise to matter."

### Injection Timing

TTS is injected once per 10-minute window, during a morph transition between
mood segments. The speech is mixed into the crossfade region at moderate volume,
so it sits on top of the blending music without fighting for attention.

### Safety

All text is sanitized before passing to TTS: shell metacharacters are stripped,
control characters are removed, and text is truncated to 500 characters. Even
though subprocess calls use list arguments (no `shell=True`), this provides
defense-in-depth against injection.

---

## Volume and Mastering

### The V20 Mastering Chain

V20 applies a three-stage mastering chain to the final output:

1. **Per-segment soft-knee limiting** (knee = 0.85): Applied to each mood
   segment's loop buffer after effects processing. Catches segment-level peaks
   without affecting the global dynamics.

2. **Master normalization** (target = -1 dB): After all segments are rendered
   and stitched together, the engine scans both channels for the absolute peak
   amplitude and scales the entire signal so that peak reaches -1 dB (0.891 on
   a 0-to-1 scale). This ensures consistent loudness across different seeds
   and durations.

3. **Lookahead limiter** (threshold = 0.92): A second pass catches transient
   spikes that the normalization might have created. The limiter looks 5ms
   ahead to anticipate peaks, instantly reduces gain when a spike is detected,
   and smoothly releases gain over 50ms. This prevents the pops and static
   bursts that earlier versions suffered from.

### RMS Compensation

V11 introduced per-voice RMS normalization: each voice's amplitude is measured
and scaled so that quiet instruments are brought up and loud ones are brought
down before mixing. Combined with the gain-weight system from orchestral role
assignment (melody at 100%, foundation at 80%, color at 30%), this ensures
a balanced ensemble.

### Gain Staging Fix

V18 and earlier had a bug where voice gain was attenuated twice -- once as
`0.25 / n_voices` and again with a `0.25` mix multiplier, producing a combined
-30 dB attenuation that made the output very quiet. V20 fixes this: voice gain
is `0.35 / n_voices` with a 1.0 mix multiplier, giving proper headroom without
the double penalty.

### The Streaming Render Pipeline

For memory-safe rendering of long pieces, V20 uses a streaming pipeline:

1. **Segment-by-segment rendering**: Each mood segment is synthesized, morphed,
   and written to a rolling buffer. When enough audio has accumulated past the
   morph overlap region, it is flushed to a WAV file on disk and the buffer
   memory is reclaimed.

2. **ffmpeg normalization**: After the raw WAV is complete, ffmpeg applies
   dynamic audio normalization (`dynaudnorm`) and a limiter (`alimiter`) as
   a final loudness pass.

3. **MP3 encoding**: ffmpeg converts the normalized WAV to 192 kbps MP3 at
   44.1 kHz using the LAME encoder.

This pipeline avoids holding a full 30-minute stereo buffer in memory (~2.5 GB
at 44.1 kHz, 64-bit float), enabling renders within memory-constrained
container environments.

---

## Solo Moods

### The Intimate Reset

With a 15% chance per segment, V20 renders a **solo mood**: a single instrument
plays the MIDI-sampled melody directly, without chord building, arpeggios, or
harmonic embellishment. The instrument is randomly chosen (with noise instruments
excluded) and plays with:

- A centered-ish stereo position (pan between -0.3 and 0.3)
- Moderate instrument coloring (0.35-0.55 blend)
- Higher gain (0.55, since it is playing alone)
- Gentle reverb (the same Schroeder reverb at default mix)
- A comfortable pitch range (C2 to C7)

The solo mood gives the listener's ear a reset after dense multi-voice sections.
It creates exposed, intimate moments where a single instrument's character
can be heard clearly -- a flute wandering through a Lydian phrase, or a cello
tracing a fragment of Bach in harmonic minor.

After the solo section, the next mood segment returns to full ensemble playing,
and the contrast makes the return feel richer.
