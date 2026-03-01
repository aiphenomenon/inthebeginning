//! Physical constants and simulation parameters.
//!
//! All values are in simulation units (SU) scaled for computational tractability.
//! Real-world proportions are maintained where possible.

use std::f64::consts::PI as STD_PI;

// === Fundamental Constants (simulation-scaled) ===
pub const C: f64 = 1.0;                    // Speed of light (SU)
pub const HBAR: f64 = 0.01;                // Reduced Planck constant (SU)
pub const K_B: f64 = 0.001;                // Boltzmann constant (SU)
pub const G: f64 = 1e-6;                   // Gravitational constant (SU)
pub const ALPHA: f64 = 1.0 / 137.0;        // Fine structure constant
pub const E_CHARGE: f64 = 0.1;             // Elementary charge (SU)
pub const PI: f64 = STD_PI;

// === Particle masses (SU, proportional to real) ===
pub const M_ELECTRON: f64 = 1.0;
pub const M_UP_QUARK: f64 = 4.4;           // ~2.2 MeV / 0.511 MeV
pub const M_DOWN_QUARK: f64 = 9.4;         // ~4.7 MeV / 0.511 MeV
pub const M_PROTON: f64 = 1836.0;          // Real ratio to electron
pub const M_NEUTRON: f64 = 1839.0;
pub const M_PHOTON: f64 = 0.0;
pub const M_NEUTRINO: f64 = 1e-6;
pub const M_W_BOSON: f64 = 157000.0;
pub const M_Z_BOSON: f64 = 178000.0;
pub const M_HIGGS: f64 = 245000.0;

// === Force coupling strengths (dimensionless) ===
pub const STRONG_COUPLING: f64 = 1.0;
pub const EM_COUPLING: f64 = ALPHA;
pub const WEAK_COUPLING: f64 = 1e-6;
pub const GRAVITY_COUPLING: f64 = 1e-38;

// === Nuclear parameters ===
pub const NUCLEAR_RADIUS: f64 = 0.01;      // SU
pub const BINDING_ENERGY_DEUTERIUM: f64 = 2.22;    // MeV equivalent
pub const BINDING_ENERGY_HELIUM4: f64 = 28.3;
pub const BINDING_ENERGY_CARBON12: f64 = 92.16;
pub const BINDING_ENERGY_IRON56: f64 = 492.26;

// === Cosmic timeline (simulation ticks) ===
pub const PLANCK_EPOCH: u64 = 1;
pub const INFLATION_EPOCH: u64 = 10;
pub const ELECTROWEAK_EPOCH: u64 = 100;
pub const QUARK_EPOCH: u64 = 1000;
pub const HADRON_EPOCH: u64 = 5000;
pub const NUCLEOSYNTHESIS_EPOCH: u64 = 10000;
pub const RECOMBINATION_EPOCH: u64 = 50000;
pub const STAR_FORMATION_EPOCH: u64 = 100000;
pub const SOLAR_SYSTEM_EPOCH: u64 = 200000;
pub const EARTH_EPOCH: u64 = 210000;
pub const LIFE_EPOCH: u64 = 250000;
pub const DNA_EPOCH: u64 = 280000;
pub const PRESENT_EPOCH: u64 = 300000;

// === Temperature scale (simulation Kelvin) ===
pub const T_PLANCK: f64 = 1e10;
pub const T_ELECTROWEAK: f64 = 1e8;
pub const T_QUARK_HADRON: f64 = 1e6;
pub const T_NUCLEOSYNTHESIS: f64 = 1e4;
pub const T_RECOMBINATION: f64 = 3000.0;
pub const T_CMB: f64 = 2.725;
pub const T_STELLAR_CORE: f64 = 1.5e4;
pub const T_EARTH_SURFACE: f64 = 288.0;

// === Chemistry parameters ===
pub const ELECTRON_SHELLS: &[u32] = &[2, 8, 18, 32, 32, 18, 8];
pub const BOND_ENERGY_COVALENT: f64 = 3.5;     // eV equivalent
pub const BOND_ENERGY_IONIC: f64 = 5.0;
pub const BOND_ENERGY_HYDROGEN: f64 = 0.2;
pub const BOND_ENERGY_VAN_DER_WAALS: f64 = 0.01;

// === Biology parameters ===
pub const NUCLEOTIDE_BASES: &[char] = &['A', 'T', 'G', 'C'];
pub const RNA_BASES: &[char] = &['A', 'U', 'G', 'C'];

pub const AMINO_ACIDS: &[&str] = &[
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
];

/// Returns the amino acid (or "STOP") for a given RNA codon triplet.
pub fn codon_to_amino_acid(codon: &str) -> Option<&'static str> {
    match codon {
        "AUG" => Some("Met"),
        "UUU" | "UUC" => Some("Phe"),
        "UUA" | "UUG" | "CUU" | "CUC" | "CUA" | "CUG" => Some("Leu"),
        "AUU" | "AUC" | "AUA" => Some("Ile"),
        "GUU" | "GUC" | "GUA" | "GUG" => Some("Val"),
        "UCU" | "UCC" | "UCA" | "UCG" => Some("Ser"),
        "CCU" | "CCC" | "CCA" | "CCG" => Some("Pro"),
        "ACU" | "ACC" | "ACA" | "ACG" => Some("Thr"),
        "GCU" | "GCC" | "GCA" | "GCG" => Some("Ala"),
        "UAU" | "UAC" => Some("Tyr"),
        "CAU" | "CAC" => Some("His"),
        "CAA" | "CAG" => Some("Gln"),
        "AAU" | "AAC" => Some("Asn"),
        "AAA" | "AAG" => Some("Lys"),
        "GAU" | "GAC" => Some("Asp"),
        "GAA" | "GAG" => Some("Glu"),
        "UGU" | "UGC" => Some("Cys"),
        "UGG" => Some("Trp"),
        "CGU" | "CGC" | "CGA" | "CGG" => Some("Arg"),
        "AGU" | "AGC" => Some("Ser"),
        "AGA" | "AGG" => Some("Arg"),
        "GGU" | "GGC" | "GGA" | "GGG" => Some("Gly"),
        "UAA" | "UAG" | "UGA" => Some("STOP"),
        _ => None,
    }
}

// === Epigenetic parameters ===
pub const METHYLATION_PROBABILITY: f64 = 0.03;
pub const DEMETHYLATION_PROBABILITY: f64 = 0.01;
pub const HISTONE_ACETYLATION_PROB: f64 = 0.02;
pub const HISTONE_DEACETYLATION_PROB: f64 = 0.015;
pub const CHROMATIN_REMODEL_ENERGY: f64 = 1.5;

// === Environmental parameters ===
pub const UV_MUTATION_RATE: f64 = 1e-4;
pub const COSMIC_RAY_MUTATION_RATE: f64 = 1e-6;
pub const THERMAL_FLUCTUATION: f64 = 0.01;
pub const RADIATION_DAMAGE_THRESHOLD: f64 = 10.0;

// === Particle type enum ===
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ParticleType {
    // Quarks
    Up,
    Down,
    // Leptons
    Electron,
    Positron,
    Neutrino,
    // Gauge bosons
    Photon,
    Gluon,
    WBoson,
    ZBoson,
    // Composite
    Proton,
    Neutron,
}

impl ParticleType {
    pub fn label(self) -> &'static str {
        match self {
            Self::Up => "up",
            Self::Down => "down",
            Self::Electron => "electron",
            Self::Positron => "positron",
            Self::Neutrino => "neutrino",
            Self::Photon => "photon",
            Self::Gluon => "gluon",
            Self::WBoson => "W",
            Self::ZBoson => "Z",
            Self::Proton => "proton",
            Self::Neutron => "neutron",
        }
    }

    pub fn mass(self) -> f64 {
        match self {
            Self::Up => M_UP_QUARK,
            Self::Down => M_DOWN_QUARK,
            Self::Electron => M_ELECTRON,
            Self::Positron => M_ELECTRON,
            Self::Neutrino => M_NEUTRINO,
            Self::Photon => M_PHOTON,
            Self::Gluon => M_PHOTON,
            Self::WBoson => M_W_BOSON,
            Self::ZBoson => M_Z_BOSON,
            Self::Proton => M_PROTON,
            Self::Neutron => M_NEUTRON,
        }
    }

    pub fn charge(self) -> f64 {
        match self {
            Self::Up => 2.0 / 3.0,
            Self::Down => -1.0 / 3.0,
            Self::Electron => -1.0,
            Self::Positron => 1.0,
            Self::Neutrino => 0.0,
            Self::Photon => 0.0,
            Self::Gluon => 0.0,
            Self::WBoson => 1.0,
            Self::ZBoson => 0.0,
            Self::Proton => 1.0,
            Self::Neutron => 0.0,
        }
    }

    /// Returns an RGBA color for rendering this particle type.
    pub fn render_color(self) -> [f32; 4] {
        match self {
            Self::Up => [1.0, 0.3, 0.3, 1.0],        // red
            Self::Down => [0.3, 0.3, 1.0, 1.0],       // blue
            Self::Electron => [0.2, 0.8, 1.0, 1.0],   // cyan
            Self::Positron => [1.0, 0.8, 0.2, 1.0],   // yellow
            Self::Neutrino => [0.5, 0.5, 0.5, 0.3],   // faint gray
            Self::Photon => [1.0, 1.0, 0.8, 0.9],     // white-yellow
            Self::Gluon => [0.0, 1.0, 0.3, 0.7],      // bright green
            Self::WBoson => [0.8, 0.0, 1.0, 0.8],     // purple
            Self::ZBoson => [0.6, 0.0, 0.8, 0.8],     // dark purple
            Self::Proton => [1.0, 0.5, 0.0, 1.0],     // orange
            Self::Neutron => [0.6, 0.6, 0.6, 1.0],    // gray
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Spin {
    Up,
    Down,
}

impl Spin {
    pub fn value(self) -> f64 {
        match self {
            Self::Up => 0.5,
            Self::Down => -0.5,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Color {
    Red,
    Green,
    Blue,
    AntiRed,
    AntiGreen,
    AntiBlue,
}

/// Epoch info for the cosmic timeline.
#[derive(Debug, Clone)]
pub struct EpochInfo {
    pub name: &'static str,
    pub start_tick: u64,
    pub description: &'static str,
}

pub const EPOCHS: &[EpochInfo] = &[
    EpochInfo { name: "Planck", start_tick: PLANCK_EPOCH, description: "All forces unified, T~10^32K" },
    EpochInfo { name: "Inflation", start_tick: INFLATION_EPOCH, description: "Exponential expansion, quantum fluctuations seed structure" },
    EpochInfo { name: "Electroweak", start_tick: ELECTROWEAK_EPOCH, description: "Electromagnetic and weak forces separate" },
    EpochInfo { name: "Quark", start_tick: QUARK_EPOCH, description: "Quark-gluon plasma, free quarks" },
    EpochInfo { name: "Hadron", start_tick: HADRON_EPOCH, description: "Quarks confined into protons and neutrons" },
    EpochInfo { name: "Nucleosynthesis", start_tick: NUCLEOSYNTHESIS_EPOCH, description: "Light nuclei form: H, He, Li" },
    EpochInfo { name: "Recombination", start_tick: RECOMBINATION_EPOCH, description: "Atoms form, universe becomes transparent" },
    EpochInfo { name: "Star Formation", start_tick: STAR_FORMATION_EPOCH, description: "First stars ignite, heavier elements forged" },
    EpochInfo { name: "Solar System", start_tick: SOLAR_SYSTEM_EPOCH, description: "Our solar system coalesces from stellar debris" },
    EpochInfo { name: "Earth", start_tick: EARTH_EPOCH, description: "Earth forms, oceans appear" },
    EpochInfo { name: "Life", start_tick: LIFE_EPOCH, description: "First self-replicating molecules" },
    EpochInfo { name: "DNA Era", start_tick: DNA_EPOCH, description: "DNA-based life, epigenetics emerge" },
    EpochInfo { name: "Present", start_tick: PRESENT_EPOCH, description: "Complex life, intelligence" },
];

/// Element data: (symbol, name, group, period, electronegativity)
pub fn element_data(z: u32) -> Option<(&'static str, &'static str, u32, u32, f64)> {
    match z {
        1  => Some(("H",  "Hydrogen",   1, 1, 2.20)),
        2  => Some(("He", "Helium",    18, 1, 0.0)),
        3  => Some(("Li", "Lithium",    1, 2, 0.98)),
        4  => Some(("Be", "Beryllium",  2, 2, 1.57)),
        5  => Some(("B",  "Boron",     13, 2, 2.04)),
        6  => Some(("C",  "Carbon",    14, 2, 2.55)),
        7  => Some(("N",  "Nitrogen",  15, 2, 3.04)),
        8  => Some(("O",  "Oxygen",    16, 2, 3.44)),
        9  => Some(("F",  "Fluorine",  17, 2, 3.98)),
        10 => Some(("Ne", "Neon",      18, 2, 0.0)),
        11 => Some(("Na", "Sodium",     1, 3, 0.93)),
        12 => Some(("Mg", "Magnesium",  2, 3, 1.31)),
        13 => Some(("Al", "Aluminum",  13, 3, 1.61)),
        14 => Some(("Si", "Silicon",   14, 3, 1.90)),
        15 => Some(("P",  "Phosphorus",15, 3, 2.19)),
        16 => Some(("S",  "Sulfur",    16, 3, 2.58)),
        17 => Some(("Cl", "Chlorine",  17, 3, 3.16)),
        18 => Some(("Ar", "Argon",     18, 3, 0.0)),
        19 => Some(("K",  "Potassium",  1, 4, 0.82)),
        20 => Some(("Ca", "Calcium",    2, 4, 1.00)),
        26 => Some(("Fe", "Iron",       8, 4, 1.83)),
        _  => None,
    }
}
