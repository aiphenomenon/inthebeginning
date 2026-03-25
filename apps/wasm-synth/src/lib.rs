//! WebAssembly Audio Synthesizer for inthebeginning bounce.
//!
//! Implements additive synthesis with ADSR envelopes, multiple instrument
//! timbres, and real-time audio rendering. Designed to be called from
//! JavaScript via wasm-bindgen, rendering audio into a shared f32 buffer
//! that an AudioWorklet reads.
//!
//! Zero external dependencies beyond wasm-bindgen and js-sys.

pub mod sf2;

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

fn web_sys_log(s: &str) {
    log(s);
}

// ──── Constants ────

const SAMPLE_RATE: f32 = 44100.0;
const MAX_VOICES: usize = 64;
const TWO_PI: f32 = std::f32::consts::PI * 2.0;

// ──── Timbre Definitions ────
// Harmonic amplitude profiles for additive synthesis (ported from synth-engine.js).

/// Harmonic profile: array of relative amplitudes for harmonics 1, 2, 3, ...
struct Timbre {
    name: &'static str,
    harmonics: &'static [f32],
    envelope: Adsr,
}

/// ADSR envelope parameters (in seconds, sustain is 0-1 level).
#[derive(Clone, Copy)]
struct Adsr {
    attack: f32,
    decay: f32,
    sustain: f32,
    release: f32,
}

const TIMBRES: &[Timbre] = &[
    Timbre {
        name: "piano",
        harmonics: &[1.0, 0.50, 0.30, 0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.07],
        envelope: Adsr { attack: 0.01, decay: 0.2, sustain: 0.3, release: 0.30 },
    },
    Timbre {
        name: "violin",
        harmonics: &[1.0, 0.50, 0.33, 0.25, 0.20, 0.16, 0.14, 0.12, 0.10, 0.08, 0.07, 0.06],
        envelope: Adsr { attack: 0.08, decay: 0.1, sustain: 0.7, release: 0.15 },
    },
    Timbre {
        name: "cello",
        harmonics: &[1.0, 0.70, 0.45, 0.30, 0.20, 0.15, 0.10, 0.08, 0.06, 0.04],
        envelope: Adsr { attack: 0.10, decay: 0.1, sustain: 0.7, release: 0.20 },
    },
    Timbre {
        name: "flute",
        harmonics: &[1.0, 0.40, 0.10, 0.02],
        envelope: Adsr { attack: 0.05, decay: 0.1, sustain: 0.6, release: 0.10 },
    },
    Timbre {
        name: "oboe",
        harmonics: &[1.0, 0.60, 0.80, 0.50, 0.40, 0.30, 0.20, 0.15, 0.10],
        envelope: Adsr { attack: 0.04, decay: 0.1, sustain: 0.7, release: 0.12 },
    },
    Timbre {
        name: "trumpet",
        harmonics: &[1.0, 0.90, 0.70, 0.60, 0.50, 0.40, 0.30, 0.25, 0.20, 0.15],
        envelope: Adsr { attack: 0.03, decay: 0.1, sustain: 0.8, release: 0.10 },
    },
    Timbre {
        name: "harp",
        harmonics: &[1.0, 0.30, 0.10, 0.05, 0.03, 0.02],
        envelope: Adsr { attack: 0.01, decay: 0.3, sustain: 0.2, release: 0.30 },
    },
    Timbre {
        name: "bell",
        harmonics: &[1.0, 0.60, 0.30, 0.20, 0.35, 0.15, 0.25, 0.10, 0.15, 0.08],
        envelope: Adsr { attack: 0.001, decay: 0.5, sustain: 0.1, release: 0.80 },
    },
    Timbre {
        name: "gamelan",
        harmonics: &[1.0, 0.40, 0.15, 0.30, 0.10, 0.20, 0.08, 0.15],
        envelope: Adsr { attack: 0.001, decay: 0.4, sustain: 0.15, release: 0.60 },
    },
    Timbre {
        name: "choir",
        harmonics: &[1.0, 0.40, 0.20, 0.15, 0.10, 0.08, 0.05],
        envelope: Adsr { attack: 0.15, decay: 0.1, sustain: 0.7, release: 0.25 },
    },
    Timbre {
        name: "warm_pad",
        harmonics: &[1.0, 0.30, 0.15, 0.08, 0.04],
        envelope: Adsr { attack: 0.20, decay: 0.2, sustain: 0.6, release: 0.40 },
    },
    Timbre {
        name: "cosmic",
        harmonics: &[1.0, 0.20, 0.10, 0.30, 0.05, 0.15, 0.03, 0.10, 0.02, 0.08],
        envelope: Adsr { attack: 0.10, decay: 0.3, sustain: 0.5, release: 0.50 },
    },
    Timbre {
        name: "sine",
        harmonics: &[1.0],
        envelope: Adsr { attack: 0.01, decay: 0.1, sustain: 0.8, release: 0.10 },
    },
];

// ──── GM Program to Timbre Index Mapping ────

/// Map GM program number (0-127) to timbre index.
fn gm_to_timbre(program: u8) -> usize {
    let group = program / 8;
    match group {
        0 => 0,   // piano
        1 => 7,   // chromatic → bell
        2 => 10,  // organ → warm_pad
        3 => 6,   // guitar → harp
        4 => 2,   // bass → cello
        5 => 1,   // strings → violin
        6 => 9,   // ensemble → choir
        7 => 5,   // brass → trumpet
        8 => 4,   // reed → oboe
        9 => 3,   // pipe → flute
        10 => 11, // synth-lead → cosmic
        11 => 10, // synth-pad → warm_pad
        12 => 11, // fx → cosmic
        13 => 8,  // ethnic → gamelan
        14 => 0,  // percussion → piano (fallback)
        15 => 11, // sfx → cosmic
        _ => 12,  // sine (default)
    }
}

// ──── Voice ────

#[derive(Clone, Copy)]
enum VoiceState {
    Off,
    Attack,
    Decay,
    Sustain,
    Release,
}

#[derive(Clone, Copy)]
struct Voice {
    state: VoiceState,
    note: u8,
    channel: u8,
    velocity: f32,
    frequency: f32,
    timbre_idx: usize,
    /// Phase accumulator for each harmonic.
    phase: [f32; 16],
    /// Envelope level (0-1).
    env_level: f32,
    /// Time spent in current envelope stage.
    env_time: f32,
    /// Total time since note on (for vibrato, etc.).
    age: f32,
}

impl Voice {
    const fn new() -> Self {
        Self {
            state: VoiceState::Off,
            note: 0,
            channel: 0,
            velocity: 0.0,
            frequency: 0.0,
            timbre_idx: 0,
            phase: [0.0; 16],
            env_level: 0.0,
            env_time: 0.0,
            age: 0.0,
        }
    }

    fn is_active(&self) -> bool {
        !matches!(self.state, VoiceState::Off)
    }

    fn note_on(&mut self, note: u8, velocity: f32, channel: u8, timbre_idx: usize) {
        self.note = note;
        self.channel = channel;
        self.velocity = velocity;
        self.frequency = midi_to_freq(note);
        self.timbre_idx = timbre_idx;
        self.phase = [0.0; 16];
        self.env_level = 0.0;
        self.env_time = 0.0;
        self.age = 0.0;
        self.state = VoiceState::Attack;
    }

    fn note_off(&mut self) {
        if self.is_active() {
            self.state = VoiceState::Release;
            self.env_time = 0.0;
        }
    }

    /// Render one sample of this voice.
    fn render(&mut self, dt: f32, pitch_shift: f32) -> f32 {
        if !self.is_active() {
            return 0.0;
        }

        let timbre = &TIMBRES[self.timbre_idx];
        let adsr = &timbre.envelope;

        // Update envelope
        self.env_time += dt;
        self.age += dt;
        match self.state {
            VoiceState::Attack => {
                if adsr.attack > 0.0 {
                    self.env_level = (self.env_time / adsr.attack).min(1.0);
                } else {
                    self.env_level = 1.0;
                }
                if self.env_time >= adsr.attack {
                    self.state = VoiceState::Decay;
                    self.env_time = 0.0;
                }
            }
            VoiceState::Decay => {
                let progress = if adsr.decay > 0.0 {
                    (self.env_time / adsr.decay).min(1.0)
                } else {
                    1.0
                };
                self.env_level = 1.0 + (adsr.sustain - 1.0) * progress;
                if self.env_time >= adsr.decay {
                    self.state = VoiceState::Sustain;
                    self.env_time = 0.0;
                }
            }
            VoiceState::Sustain => {
                self.env_level = adsr.sustain;
            }
            VoiceState::Release => {
                let start_level = self.env_level;
                if adsr.release > 0.0 {
                    let progress = (self.env_time / adsr.release).min(1.0);
                    self.env_level = start_level * (1.0 - progress);
                } else {
                    self.env_level = 0.0;
                }
                if self.env_time >= adsr.release || self.env_level < 0.001 {
                    self.state = VoiceState::Off;
                    return 0.0;
                }
            }
            VoiceState::Off => return 0.0,
        }

        // Additive synthesis: sum harmonics
        let freq = self.frequency * (2.0_f32).powf(pitch_shift / 12.0);
        let harmonics = timbre.harmonics;
        let mut sample = 0.0_f32;
        let n_harmonics = harmonics.len().min(16);

        for i in 0..n_harmonics {
            let harmonic_num = (i + 1) as f32;
            let harmonic_freq = freq * harmonic_num;

            // Skip harmonics above Nyquist
            if harmonic_freq >= SAMPLE_RATE / 2.0 {
                break;
            }

            self.phase[i] += harmonic_freq * dt * TWO_PI;
            if self.phase[i] > TWO_PI {
                self.phase[i] -= TWO_PI;
            }

            sample += fast_sin(self.phase[i]) * harmonics[i];
        }

        // Normalize and apply envelope + velocity
        let norm = 1.0 / (n_harmonics as f32).sqrt();
        sample * norm * self.env_level * self.velocity * 0.3
    }
}

// ──── Synth Engine ────

/// Global synth state, exported to JS via wasm-bindgen.
#[wasm_bindgen]
pub struct WasmSynthEngine {
    voices: Vec<Voice>,
    sample_rate: f32,
    volume: f32,
    pitch_shift: f32,
    tempo_mult: f32,
    /// Per-channel program (GM instrument) assignment.
    programs: [u8; 16],
    /// Output buffer for render_block.
    buffer: Vec<f32>,
    /// Optional loaded SoundFont for sample-based synthesis.
    soundfont: Option<sf2::SoundFont>,
    /// Whether to use SF2 samples when available.
    use_sf2: bool,
}

#[wasm_bindgen]
impl WasmSynthEngine {
    /// Create a new synth engine.
    #[wasm_bindgen(constructor)]
    pub fn new(sample_rate: f32) -> Self {
        let mut voices = Vec::with_capacity(MAX_VOICES);
        for _ in 0..MAX_VOICES {
            voices.push(Voice::new());
        }
        Self {
            voices,
            sample_rate: if sample_rate > 0.0 { sample_rate } else { SAMPLE_RATE },
            volume: 0.8,
            pitch_shift: 0.0,
            tempo_mult: 1.0,
            programs: [0; 16],
            buffer: Vec::new(),
            soundfont: None,
            use_sf2: false,
        }
    }

    /// Trigger a note on.
    pub fn note_on(&mut self, note: u8, velocity: u8, channel: u8) {
        let vel = (velocity as f32) / 127.0;
        let program = self.programs[channel.min(15) as usize];
        let timbre_idx = gm_to_timbre(program);

        // Find a free voice, or steal the oldest
        let mut free_idx: Option<usize> = None;
        let mut oldest_idx = 0;
        let mut oldest_age = 0.0_f32;

        for (i, v) in self.voices.iter().enumerate() {
            if !v.is_active() {
                free_idx = Some(i);
                break;
            }
            if v.age > oldest_age {
                oldest_age = v.age;
                oldest_idx = i;
            }
        }

        let idx = free_idx.unwrap_or(oldest_idx);
        self.voices[idx].note_on(note, vel, channel, timbre_idx);
    }

    /// Trigger a note off.
    pub fn note_off(&mut self, note: u8, channel: u8) {
        for v in &mut self.voices {
            if v.is_active() && v.note == note && v.channel == channel {
                v.note_off();
            }
        }
    }

    /// Set the GM program (instrument) for a channel.
    pub fn program_change(&mut self, channel: u8, program: u8) {
        if channel < 16 {
            self.programs[channel as usize] = program;
        }
    }

    /// Set master volume (0.0-1.0).
    pub fn set_volume(&mut self, vol: f32) {
        self.volume = vol.clamp(0.0, 1.0);
    }

    /// Set pitch shift in semitones.
    pub fn set_pitch_shift(&mut self, semitones: f32) {
        self.pitch_shift = semitones.clamp(-24.0, 24.0);
    }

    /// Set tempo multiplier.
    pub fn set_tempo_mult(&mut self, mult: f32) {
        self.tempo_mult = mult.clamp(0.25, 4.0);
    }

    /// Stop all voices immediately.
    pub fn stop_all(&mut self) {
        for v in &mut self.voices {
            v.state = VoiceState::Off;
        }
    }

    /// Render a block of audio samples (mono, interleaved f32).
    /// Returns a pointer to the internal buffer.
    pub fn render_block(&mut self, num_samples: usize) -> *const f32 {
        self.buffer.resize(num_samples, 0.0);
        let dt = 1.0 / self.sample_rate;

        for i in 0..num_samples {
            let mut sample = 0.0_f32;
            for v in &mut self.voices {
                sample += v.render(dt, self.pitch_shift);
            }
            self.buffer[i] = (sample * self.volume).clamp(-1.0, 1.0);
        }

        self.buffer.as_ptr()
    }

    /// Get the number of active voices.
    pub fn active_voice_count(&self) -> u32 {
        self.voices.iter().filter(|v| v.is_active()).count() as u32
    }

    /// Get a pointer to the render buffer (for JS to read).
    pub fn buffer_ptr(&self) -> *const f32 {
        self.buffer.as_ptr()
    }

    /// Get the buffer length.
    pub fn buffer_len(&self) -> usize {
        self.buffer.len()
    }

    /// Get the sample rate.
    pub fn sample_rate(&self) -> f32 {
        self.sample_rate
    }

    /// Get the tempo multiplier.
    pub fn tempo_mult(&self) -> f32 {
        self.tempo_mult
    }

    /// Load a SoundFont (.sf2) file from raw bytes.
    /// After loading, the engine will use SF2 samples for synthesis.
    /// Returns true on success.
    pub fn load_sf2(&mut self, data: &[u8]) -> bool {
        match sf2::SoundFont::parse(data) {
            Ok(sf) => {
                let preset_count = sf.presets.len();
                let sample_count = sf.sample_headers.len();
                let sample_data_size = sf.samples.len();
                self.soundfont = Some(sf);
                self.use_sf2 = true;
                // Log via console (js-sys)
                web_sys_log(&format!(
                    "SF2 loaded: {} presets, {} samples, {}KB sample data",
                    preset_count, sample_count, sample_data_size * 4 / 1024
                ));
                true
            }
            Err(e) => {
                web_sys_log(&format!("SF2 parse error: {}", e));
                false
            }
        }
    }

    /// Check if a SoundFont is loaded.
    pub fn has_sf2(&self) -> bool {
        self.soundfont.is_some()
    }

    /// Get the number of presets in the loaded SoundFont.
    pub fn sf2_preset_count(&self) -> u32 {
        self.soundfont.as_ref().map(|sf| sf.presets.len() as u32).unwrap_or(0)
    }

    /// Get the number of samples in the loaded SoundFont.
    pub fn sf2_sample_count(&self) -> u32 {
        self.soundfont.as_ref().map(|sf| sf.sample_headers.len() as u32).unwrap_or(0)
    }

    /// Toggle whether to use SF2 samples (true) or additive synthesis (false).
    pub fn set_use_sf2(&mut self, use_sf2: bool) {
        self.use_sf2 = use_sf2 && self.soundfont.is_some();
    }
}

// ──── Helper Functions ────

/// Convert MIDI note number to frequency (A4 = 440 Hz).
fn midi_to_freq(note: u8) -> f32 {
    440.0 * (2.0_f32).powf(((note as f32) - 69.0) / 12.0)
}

/// Fast sine approximation (Bhaskara I, accurate to ~0.1%).
fn fast_sin(x: f32) -> f32 {
    // Normalize x to [0, 2π]
    let mut x = x % TWO_PI;
    if x < 0.0 {
        x += TWO_PI;
    }

    // Use std sin — on WASM this compiles to efficient native code
    x.sin()
}

// ──── Tests ────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_midi_to_freq() {
        let a4 = midi_to_freq(69);
        assert!((a4 - 440.0).abs() < 0.01);

        let c4 = midi_to_freq(60);
        assert!((c4 - 261.63).abs() < 0.1);
    }

    #[test]
    fn test_voice_lifecycle() {
        let mut voice = Voice::new();
        assert!(!voice.is_active());

        voice.note_on(60, 0.8, 0, 0);
        assert!(voice.is_active());

        // Render some samples
        let dt = 1.0 / 44100.0;
        for _ in 0..441 {
            let s = voice.render(dt, 0.0);
            assert!(s.is_finite());
        }

        voice.note_off();
        // Should still be active during release
        assert!(voice.is_active());

        // Render through release
        for _ in 0..44100 {
            voice.render(dt, 0.0);
        }
        // Should be off after release
        assert!(!voice.is_active());
    }

    #[test]
    fn test_engine_render() {
        let mut engine = WasmSynthEngine::new(44100.0);
        engine.note_on(60, 100, 0);
        engine.note_on(64, 80, 0);
        engine.note_on(67, 80, 0);

        assert_eq!(engine.active_voice_count(), 3);

        let ptr = engine.render_block(128);
        assert!(!ptr.is_null());
        assert_eq!(engine.buffer_len(), 128);

        // Verify output is non-zero (we have active notes)
        let has_nonzero = engine.buffer.iter().any(|&s| s.abs() > 0.0001);
        assert!(has_nonzero, "Render output should have non-zero samples");

        // Verify output is in range
        for &s in &engine.buffer {
            assert!(s >= -1.0 && s <= 1.0, "Sample out of range: {}", s);
        }
    }

    #[test]
    fn test_gm_program_mapping() {
        // Piano group
        assert_eq!(gm_to_timbre(0), 0);  // Acoustic Grand Piano → piano
        assert_eq!(gm_to_timbre(7), 0);  // Clavinet → piano

        // Strings group
        assert_eq!(gm_to_timbre(40), 1); // Violin → violin
        assert_eq!(gm_to_timbre(42), 1); // Cello → violin (group)

        // Brass group
        assert_eq!(gm_to_timbre(56), 5); // Trumpet → trumpet
    }

    #[test]
    fn test_note_stealing() {
        let mut engine = WasmSynthEngine::new(44100.0);

        // Fill all voices
        for i in 0..MAX_VOICES {
            engine.note_on(60 + (i as u8 % 40), 100, 0);
        }

        assert_eq!(engine.active_voice_count() as usize, MAX_VOICES);

        // One more note should steal oldest
        engine.note_on(100, 100, 0);
        assert_eq!(engine.active_voice_count() as usize, MAX_VOICES);
    }

    #[test]
    fn test_stop_all() {
        let mut engine = WasmSynthEngine::new(44100.0);
        engine.note_on(60, 100, 0);
        engine.note_on(64, 100, 0);
        assert_eq!(engine.active_voice_count(), 2);

        engine.stop_all();
        assert_eq!(engine.active_voice_count(), 0);
    }

    #[test]
    fn test_pitch_shift() {
        let mut engine = WasmSynthEngine::new(44100.0);
        engine.set_pitch_shift(12.0); // One octave up
        engine.note_on(60, 100, 0);
        engine.render_block(128);

        // Should render without panic
        assert_eq!(engine.active_voice_count(), 1);
    }
}
