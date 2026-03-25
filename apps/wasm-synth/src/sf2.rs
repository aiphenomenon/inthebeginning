//! SoundFont 2 (.sf2) parser for WebAssembly synthesis.
//!
//! Parses the SF2 RIFF structure to extract:
//! - Sample data (16-bit PCM → f32)
//! - Preset and instrument definitions
//! - Generator parameters (root key, loop points, envelope, etc.)
//!
//! This is a minimal parser targeting the most commonly used SF2 features.
//! It does NOT implement all SF2 spec features (e.g., modulators are ignored).
//!
//! Reference: SoundFont 2.04 Technical Specification
//! http://www.synthfont.com/sfspec24.pdf

/// A parsed SoundFont file.
pub struct SoundFont {
    /// All sample data as f32 (-1.0 to 1.0).
    pub samples: Vec<f32>,
    /// Sample headers (name, start, end, loop, sample rate, root key).
    pub sample_headers: Vec<SampleHeader>,
    /// Instruments (name, zone list).
    pub instruments: Vec<Instrument>,
    /// Presets (name, bank, preset number, zone list).
    pub presets: Vec<Preset>,
}

/// A single sample's metadata.
#[derive(Clone, Debug)]
pub struct SampleHeader {
    pub name: String,
    pub start: u32,
    pub end: u32,
    pub loop_start: u32,
    pub loop_end: u32,
    pub sample_rate: u32,
    pub original_pitch: u8,
    pub pitch_correction: i8,
    pub sample_type: u16,
}

/// A preset (e.g., "Grand Piano", bank 0, preset 0).
#[derive(Clone, Debug)]
pub struct Preset {
    pub name: String,
    pub preset_num: u16,
    pub bank: u16,
    pub zones: Vec<Zone>,
}

/// An instrument (used by presets via zones).
#[derive(Clone, Debug)]
pub struct Instrument {
    pub name: String,
    pub zones: Vec<Zone>,
}

/// A zone maps key/velocity ranges to generators and a sample.
#[derive(Clone, Debug, Default)]
pub struct Zone {
    /// Key range (low, high). Default: 0-127.
    pub key_range: (u8, u8),
    /// Velocity range (low, high). Default: 0-127.
    pub vel_range: (u8, u8),
    /// Sample index (for instrument zones) or instrument index (for preset zones).
    pub sample_or_inst_idx: Option<u16>,
    /// Root key override (-1 = use sample header).
    pub root_key: i8,
    /// Fine tuning in cents.
    pub fine_tune: i16,
    /// Coarse tuning in semitones.
    pub coarse_tune: i16,
    /// Volume attenuation in centibels (0 = max volume).
    pub attenuation: u16,
    /// Sample loop mode: 0=no loop, 1=loop, 3=loop+release.
    pub loop_mode: u16,
    /// Envelope: delay, attack, hold, decay, sustain, release (in timecents).
    pub vol_env: VolEnvelope,
    /// Scale tuning (100 = standard, 0 = no pitch tracking).
    pub scale_tuning: u16,
    /// Exclusive class (0 = none).
    pub exclusive_class: u16,
}

/// Volume envelope parameters (in SF2 timecent units).
/// -12000 timecents = 0 seconds, 0 timecents = 1 second.
#[derive(Clone, Debug)]
pub struct VolEnvelope {
    pub delay: i16,
    pub attack: i16,
    pub hold: i16,
    pub decay: i16,
    pub sustain: i16, // in centibels (0=max, 1440=silence)
    pub release: i16,
}

impl Default for VolEnvelope {
    fn default() -> Self {
        Self {
            delay: -12000,
            attack: -12000,
            hold: -12000,
            decay: -12000,
            sustain: 0,
            release: -12000,
        }
    }
}

// ──── SF2 Generator Opcodes ────

const GEN_START_ADDRS_OFFSET: u16 = 0;
const GEN_END_ADDRS_OFFSET: u16 = 1;
const GEN_STARTLOOP_ADDRS_OFFSET: u16 = 2;
const GEN_ENDLOOP_ADDRS_OFFSET: u16 = 3;
const GEN_START_ADDRS_COARSE_OFFSET: u16 = 4;
const GEN_END_ADDRS_COARSE_OFFSET: u16 = 12;
const GEN_STARTLOOP_ADDRS_COARSE_OFFSET: u16 = 45;
const GEN_ENDLOOP_ADDRS_COARSE_OFFSET: u16 = 50;
const GEN_INITIAL_ATTENUATION: u16 = 48;
const GEN_PAN: u16 = 17;
const GEN_VOL_ENV_DELAY: u16 = 33;
const GEN_VOL_ENV_ATTACK: u16 = 34;
const GEN_VOL_ENV_HOLD: u16 = 35;
const GEN_VOL_ENV_DECAY: u16 = 36;
const GEN_VOL_ENV_SUSTAIN: u16 = 37;
const GEN_VOL_ENV_RELEASE: u16 = 38;
const GEN_KEY_RANGE: u16 = 43;
const GEN_VEL_RANGE: u16 = 44;
const GEN_INSTRUMENT: u16 = 41;
const GEN_SAMPLE_ID: u16 = 53;
const GEN_SAMPLE_MODES: u16 = 54;
const GEN_SCALE_TUNING: u16 = 56;
const GEN_EXCLUSIVE_CLASS: u16 = 57;
const GEN_OVERRIDING_ROOT_KEY: u16 = 58;
const GEN_FINE_TUNE: u16 = 52;
const GEN_COARSE_TUNE: u16 = 51;

// ──── Parsing ────

impl SoundFont {
    /// Parse an SF2 file from a byte slice.
    pub fn parse(data: &[u8]) -> Result<Self, String> {
        if data.len() < 12 {
            return Err("File too small for RIFF header".into());
        }

        // Verify RIFF header
        if &data[0..4] != b"RIFF" {
            return Err("Not a RIFF file".into());
        }
        if &data[8..12] != b"sfbk" {
            return Err("Not a SoundFont file (expected 'sfbk')".into());
        }

        let mut samples = Vec::new();
        let mut sample_headers = Vec::new();
        let mut instruments = Vec::new();
        let mut presets = Vec::new();

        // Temporary pdta data
        let mut phdr_data: &[u8] = &[];
        let mut pbag_data: &[u8] = &[];
        let mut pgen_data: &[u8] = &[];
        let mut inst_data: &[u8] = &[];
        let mut ibag_data: &[u8] = &[];
        let mut igen_data: &[u8] = &[];
        let mut shdr_data: &[u8] = &[];

        // Walk top-level LIST chunks
        let mut pos = 12;
        while pos + 8 <= data.len() {
            let chunk_id = &data[pos..pos + 4];
            let chunk_size = read_u32_le(data, pos + 4) as usize;
            let chunk_end = (pos + 8 + chunk_size).min(data.len());

            if chunk_id == b"LIST" && pos + 12 <= data.len() {
                let list_type = &data[pos + 8..pos + 12];

                if list_type == b"sdta" {
                    // Sample data
                    let mut sub_pos = pos + 12;
                    while sub_pos + 8 <= chunk_end {
                        let sub_id = &data[sub_pos..sub_pos + 4];
                        let sub_size = read_u32_le(data, sub_pos + 4) as usize;
                        if sub_id == b"smpl" && sub_pos + 8 + sub_size <= data.len() {
                            // 16-bit PCM samples
                            let sample_data = &data[sub_pos + 8..sub_pos + 8 + sub_size];
                            samples = pcm16_to_f32(sample_data);
                        }
                        sub_pos += 8 + sub_size;
                        if sub_size % 2 != 0 {
                            sub_pos += 1; // RIFF padding
                        }
                    }
                } else if list_type == b"pdta" {
                    // Preset data
                    let mut sub_pos = pos + 12;
                    while sub_pos + 8 <= chunk_end {
                        let sub_id = &data[sub_pos..sub_pos + 4];
                        let sub_size = read_u32_le(data, sub_pos + 4) as usize;
                        let sub_data_end = (sub_pos + 8 + sub_size).min(data.len());
                        let sub_data = &data[sub_pos + 8..sub_data_end];

                        match sub_id {
                            b"phdr" => phdr_data = sub_data,
                            b"pbag" => pbag_data = sub_data,
                            b"pgen" => pgen_data = sub_data,
                            b"inst" => inst_data = sub_data,
                            b"ibag" => ibag_data = sub_data,
                            b"igen" => igen_data = sub_data,
                            b"shdr" => shdr_data = sub_data,
                            _ => {} // pmod, imod ignored
                        }

                        sub_pos += 8 + sub_size;
                        if sub_size % 2 != 0 {
                            sub_pos += 1;
                        }
                    }
                }
            }

            pos += 8 + chunk_size;
            if chunk_size % 2 != 0 {
                pos += 1;
            }
        }

        // Parse sample headers (46 bytes each)
        sample_headers = parse_sample_headers(shdr_data);

        // Parse instruments
        instruments = parse_instruments(inst_data, ibag_data, igen_data);

        // Parse presets
        presets = parse_presets(phdr_data, pbag_data, pgen_data);

        Ok(SoundFont {
            samples,
            sample_headers,
            instruments,
            presets,
        })
    }

    /// Find the best zone for a given preset number, bank, key, and velocity.
    /// Returns (sample_header, zone_generators) or None.
    pub fn find_zone(&self, bank: u16, preset: u16, key: u8, vel: u8)
        -> Option<(&SampleHeader, Zone)>
    {
        // Find the preset
        let prs = self.presets.iter().find(|p| p.bank == bank && p.preset_num == preset)?;

        // Find matching preset zone
        for pzone in &prs.zones {
            if key < pzone.key_range.0 || key > pzone.key_range.1 {
                continue;
            }
            if vel < pzone.vel_range.0 || vel > pzone.vel_range.1 {
                continue;
            }

            let inst_idx = pzone.sample_or_inst_idx? as usize;
            if inst_idx >= self.instruments.len() {
                continue;
            }

            let inst = &self.instruments[inst_idx];

            // Find matching instrument zone
            for izone in &inst.zones {
                if key < izone.key_range.0 || key > izone.key_range.1 {
                    continue;
                }
                if vel < izone.vel_range.0 || vel > izone.vel_range.1 {
                    continue;
                }

                let sample_idx = match izone.sample_or_inst_idx {
                    Some(idx) if (idx as usize) < self.sample_headers.len() => idx as usize,
                    _ => continue,
                };

                // Merge preset and instrument zone parameters
                let mut merged = izone.clone();
                merged.attenuation = merged.attenuation.saturating_add(pzone.attenuation);
                merged.fine_tune += pzone.fine_tune;
                merged.coarse_tune += pzone.coarse_tune;

                return Some((&self.sample_headers[sample_idx], merged));
            }
        }

        None
    }

    /// Get the sample data for a sample header as f32 slice.
    pub fn get_sample_data(&self, header: &SampleHeader) -> &[f32] {
        let start = header.start as usize;
        let end = header.end as usize;
        if end <= start || end > self.samples.len() {
            return &[];
        }
        &self.samples[start..end]
    }
}

// ──── Helper Functions ────

fn read_u16_le(data: &[u8], offset: usize) -> u16 {
    if offset + 2 > data.len() { return 0; }
    u16::from_le_bytes([data[offset], data[offset + 1]])
}

fn read_u32_le(data: &[u8], offset: usize) -> u32 {
    if offset + 4 > data.len() { return 0; }
    u32::from_le_bytes([data[offset], data[offset + 1], data[offset + 2], data[offset + 3]])
}

fn read_i16_le(data: &[u8], offset: usize) -> i16 {
    read_u16_le(data, offset) as i16
}

fn read_i8(data: &[u8], offset: usize) -> i8 {
    if offset >= data.len() { return 0; }
    data[offset] as i8
}

fn read_string(data: &[u8], offset: usize, max_len: usize) -> String {
    let end = (offset + max_len).min(data.len());
    if offset >= end { return String::new(); }
    let slice = &data[offset..end];
    let nul = slice.iter().position(|&b| b == 0).unwrap_or(slice.len());
    String::from_utf8_lossy(&slice[..nul]).to_string()
}

/// Convert 16-bit PCM samples to f32 (-1.0 to 1.0).
fn pcm16_to_f32(data: &[u8]) -> Vec<f32> {
    let num_samples = data.len() / 2;
    let mut out = Vec::with_capacity(num_samples);
    for i in 0..num_samples {
        let sample = i16::from_le_bytes([data[i * 2], data[i * 2 + 1]]);
        out.push(sample as f32 / 32768.0);
    }
    out
}

/// Parse shdr (sample header) records. Each record is 46 bytes.
fn parse_sample_headers(data: &[u8]) -> Vec<SampleHeader> {
    let record_size = 46;
    let count = data.len() / record_size;
    let mut headers = Vec::with_capacity(count);

    for i in 0..count {
        let base = i * record_size;
        if base + record_size > data.len() { break; }

        let name = read_string(data, base, 20);
        // Skip terminal record (name = "EOS")
        if name == "EOS" { break; }

        headers.push(SampleHeader {
            name,
            start: read_u32_le(data, base + 20),
            end: read_u32_le(data, base + 24),
            loop_start: read_u32_le(data, base + 28),
            loop_end: read_u32_le(data, base + 32),
            sample_rate: read_u32_le(data, base + 36),
            original_pitch: data.get(base + 40).copied().unwrap_or(60),
            pitch_correction: read_i8(data, base + 41),
            sample_type: read_u16_le(data, base + 44),
        });
    }

    headers
}

/// Parse instrument records and their zones.
fn parse_instruments(inst_data: &[u8], ibag_data: &[u8], igen_data: &[u8]) -> Vec<Instrument> {
    let inst_size = 22; // 20 name + 2 bag index
    let inst_count = inst_data.len() / inst_size;
    let mut instruments = Vec::new();

    for i in 0..inst_count.saturating_sub(1) { // Last is terminal
        let base = i * inst_size;
        let name = read_string(inst_data, base, 20);
        let bag_start = read_u16_le(inst_data, base + 20) as usize;
        let bag_end = read_u16_le(inst_data, (i + 1) * inst_size + 20) as usize;

        let zones = parse_zones(ibag_data, igen_data, bag_start, bag_end, false);
        instruments.push(Instrument { name, zones });
    }

    instruments
}

/// Parse preset records and their zones.
fn parse_presets(phdr_data: &[u8], pbag_data: &[u8], pgen_data: &[u8]) -> Vec<Preset> {
    let phdr_size = 38; // 20 name + 2 preset + 2 bank + 2 bag + 4 library + 4 genre + 4 morphology
    let phdr_count = phdr_data.len() / phdr_size;
    let mut presets = Vec::new();

    for i in 0..phdr_count.saturating_sub(1) { // Last is terminal
        let base = i * phdr_size;
        let name = read_string(phdr_data, base, 20);
        let preset_num = read_u16_le(phdr_data, base + 20);
        let bank = read_u16_le(phdr_data, base + 22);
        let bag_start = read_u16_le(phdr_data, base + 24) as usize;
        let bag_end = read_u16_le(phdr_data, (i + 1) * phdr_size + 24) as usize;

        let zones = parse_zones(pbag_data, pgen_data, bag_start, bag_end, true);
        presets.push(Preset { name, preset_num, bank, zones });
    }

    presets
}

/// Parse zones from bag and gen data.
fn parse_zones(
    bag_data: &[u8],
    gen_data: &[u8],
    bag_start: usize,
    bag_end: usize,
    is_preset: bool,
) -> Vec<Zone> {
    let bag_size = 4; // 2 gen_idx + 2 mod_idx
    let gen_size = 4; // 2 opcode + 2 amount
    let mut zones = Vec::new();

    for b in bag_start..bag_end {
        let bag_offset = b * bag_size;
        if bag_offset + bag_size > bag_data.len() { break; }

        let gen_start = read_u16_le(bag_data, bag_offset) as usize;
        let gen_end = if (b + 1) * bag_size + 2 <= bag_data.len() {
            read_u16_le(bag_data, (b + 1) * bag_size) as usize
        } else {
            gen_data.len() / gen_size
        };

        let mut zone = Zone {
            key_range: (0, 127),
            vel_range: (0, 127),
            scale_tuning: 100,
            root_key: -1,
            ..Default::default()
        };

        for g in gen_start..gen_end {
            let gen_offset = g * gen_size;
            if gen_offset + gen_size > gen_data.len() { break; }

            let opcode = read_u16_le(gen_data, gen_offset);
            let amount = read_u16_le(gen_data, gen_offset + 2);
            let amount_i16 = amount as i16;
            let lo = (amount & 0xFF) as u8;
            let hi = ((amount >> 8) & 0xFF) as u8;

            match opcode {
                GEN_KEY_RANGE => zone.key_range = (lo, hi),
                GEN_VEL_RANGE => zone.vel_range = (lo, hi),
                GEN_INSTRUMENT if is_preset => zone.sample_or_inst_idx = Some(amount),
                GEN_SAMPLE_ID if !is_preset => zone.sample_or_inst_idx = Some(amount),
                GEN_OVERRIDING_ROOT_KEY => zone.root_key = amount_i16 as i8,
                GEN_FINE_TUNE => zone.fine_tune = amount_i16,
                GEN_COARSE_TUNE => zone.coarse_tune = amount_i16,
                GEN_INITIAL_ATTENUATION => zone.attenuation = amount,
                GEN_SAMPLE_MODES => zone.loop_mode = amount,
                GEN_SCALE_TUNING => zone.scale_tuning = amount,
                GEN_EXCLUSIVE_CLASS => zone.exclusive_class = amount,
                GEN_VOL_ENV_DELAY => zone.vol_env.delay = amount_i16,
                GEN_VOL_ENV_ATTACK => zone.vol_env.attack = amount_i16,
                GEN_VOL_ENV_HOLD => zone.vol_env.hold = amount_i16,
                GEN_VOL_ENV_DECAY => zone.vol_env.decay = amount_i16,
                GEN_VOL_ENV_SUSTAIN => zone.vol_env.sustain = amount_i16,
                GEN_VOL_ENV_RELEASE => zone.vol_env.release = amount_i16,
                _ => {} // Ignore other generators
            }
        }

        zones.push(zone);
    }

    zones
}

// ──── Tests ────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pcm16_to_f32() {
        // Silence
        let silence = pcm16_to_f32(&[0, 0, 0, 0]);
        assert_eq!(silence.len(), 2);
        assert_eq!(silence[0], 0.0);

        // Max positive
        let max_pos = pcm16_to_f32(&[0xFF, 0x7F]);
        assert!((max_pos[0] - 0.99997).abs() < 0.001);

        // Max negative
        let max_neg = pcm16_to_f32(&[0x00, 0x80]);
        assert_eq!(max_neg[0], -1.0);
    }

    #[test]
    fn test_read_string() {
        let data = b"Hello\0World\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0";
        assert_eq!(read_string(data, 0, 20), "Hello");
        assert_eq!(read_string(data, 6, 20), "World");
    }

    #[test]
    fn test_empty_sf2() {
        // Build a minimal valid RIFF/sfbk header with empty lists
        let mut data = Vec::new();
        data.extend_from_slice(b"RIFF");
        let size_pos = data.len();
        data.extend_from_slice(&[0, 0, 0, 0]); // placeholder size
        data.extend_from_slice(b"sfbk");

        // INFO LIST (minimal)
        data.extend_from_slice(b"LIST");
        data.extend_from_slice(&12u32.to_le_bytes()); // size
        data.extend_from_slice(b"INFO");
        data.extend_from_slice(b"ifil");
        data.extend_from_slice(&4u32.to_le_bytes());
        data.extend_from_slice(&2u16.to_le_bytes()); // major
        data.extend_from_slice(&4u16.to_le_bytes()); // minor

        // sdta LIST (empty samples)
        data.extend_from_slice(b"LIST");
        data.extend_from_slice(&4u32.to_le_bytes());
        data.extend_from_slice(b"sdta");

        // pdta LIST (empty)
        data.extend_from_slice(b"LIST");
        data.extend_from_slice(&4u32.to_le_bytes());
        data.extend_from_slice(b"pdta");

        // Fix RIFF size
        let total = (data.len() - 8) as u32;
        data[size_pos..size_pos + 4].copy_from_slice(&total.to_le_bytes());

        let sf2 = SoundFont::parse(&data).unwrap();
        assert!(sf2.samples.is_empty());
        assert!(sf2.sample_headers.is_empty());
        assert!(sf2.presets.is_empty());
        assert!(sf2.instruments.is_empty());
    }

    #[test]
    fn test_invalid_file() {
        assert!(SoundFont::parse(b"NOT A SOUNDFONT").is_err());
        assert!(SoundFont::parse(b"RIFF\0\0\0\0WAVE").is_err());
        assert!(SoundFont::parse(b"tiny").is_err());
    }
}
