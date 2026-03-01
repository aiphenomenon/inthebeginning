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

#[cfg(test)]
mod tests {
    use super::*;

    // -----------------------------------------------------------------------
    // Fundamental constants
    // -----------------------------------------------------------------------

    /// Speed of light should be 1.0 in simulation units.
    #[test]
    fn speed_of_light_is_unity() {
        assert_eq!(C, 1.0);
    }

    /// Fine-structure constant should be approximately 1/137.
    #[test]
    fn fine_structure_constant_value() {
        let expected = 1.0 / 137.0;
        assert!((ALPHA - expected).abs() < 1e-10);
    }

    /// EM coupling equals the fine-structure constant.
    #[test]
    fn em_coupling_equals_alpha() {
        assert_eq!(EM_COUPLING, ALPHA);
    }

    /// Force couplings are ordered: gravity < weak < EM < strong.
    #[test]
    fn force_coupling_ordering() {
        assert!(GRAVITY_COUPLING < WEAK_COUPLING);
        assert!(WEAK_COUPLING < EM_COUPLING);
        assert!(EM_COUPLING < STRONG_COUPLING);
    }

    // -----------------------------------------------------------------------
    // Particle masses
    // -----------------------------------------------------------------------

    /// Photon is massless.
    #[test]
    fn photon_is_massless() {
        assert_eq!(M_PHOTON, 0.0);
    }

    /// Neutrino mass is very small but nonzero.
    #[test]
    fn neutrino_mass_tiny() {
        assert!(M_NEUTRINO > 0.0);
        assert!(M_NEUTRINO < M_ELECTRON);
    }

    /// Proton and neutron masses are close but neutron is heavier.
    #[test]
    fn neutron_heavier_than_proton() {
        assert!(M_NEUTRON > M_PROTON);
    }

    /// Proton mass is approximately 1836 times the electron mass.
    #[test]
    fn proton_electron_mass_ratio() {
        assert_eq!(M_PROTON / M_ELECTRON, 1836.0);
    }

    /// Higgs boson is the heaviest particle.
    #[test]
    fn higgs_is_heaviest() {
        assert!(M_HIGGS > M_W_BOSON);
        assert!(M_HIGGS > M_Z_BOSON);
        assert!(M_HIGGS > M_PROTON);
    }

    // -----------------------------------------------------------------------
    // Binding energies
    // -----------------------------------------------------------------------

    /// Binding energies increase with nuclear size up to iron.
    #[test]
    fn binding_energy_ordering() {
        assert!(BINDING_ENERGY_DEUTERIUM < BINDING_ENERGY_HELIUM4);
        assert!(BINDING_ENERGY_HELIUM4 < BINDING_ENERGY_CARBON12);
        assert!(BINDING_ENERGY_CARBON12 < BINDING_ENERGY_IRON56);
    }

    // -----------------------------------------------------------------------
    // Cosmic timeline -- epoch ordering
    // -----------------------------------------------------------------------

    /// All epoch start ticks are strictly increasing.
    #[test]
    fn epoch_ticks_strictly_increasing() {
        let ticks = [
            PLANCK_EPOCH,
            INFLATION_EPOCH,
            ELECTROWEAK_EPOCH,
            QUARK_EPOCH,
            HADRON_EPOCH,
            NUCLEOSYNTHESIS_EPOCH,
            RECOMBINATION_EPOCH,
            STAR_FORMATION_EPOCH,
            SOLAR_SYSTEM_EPOCH,
            EARTH_EPOCH,
            LIFE_EPOCH,
            DNA_EPOCH,
            PRESENT_EPOCH,
        ];
        for w in ticks.windows(2) {
            assert!(w[0] < w[1], "epoch {} should precede {}", w[0], w[1]);
        }
    }

    /// The EPOCHS table has exactly 13 entries.
    #[test]
    fn epochs_table_count() {
        assert_eq!(EPOCHS.len(), 13);
    }

    /// EPOCHS table start ticks match the individual constants.
    #[test]
    fn epochs_table_matches_constants() {
        assert_eq!(EPOCHS[0].start_tick, PLANCK_EPOCH);
        assert_eq!(EPOCHS[5].start_tick, NUCLEOSYNTHESIS_EPOCH);
        assert_eq!(EPOCHS[12].start_tick, PRESENT_EPOCH);
    }

    /// The present epoch ends the simulation at tick 300,000.
    #[test]
    fn present_epoch_is_300k() {
        assert_eq!(PRESENT_EPOCH, 300_000);
    }

    // -----------------------------------------------------------------------
    // Temperature scale
    // -----------------------------------------------------------------------

    /// Temperatures decrease from the Planck era to CMB.
    #[test]
    fn temperature_scale_decreasing() {
        assert!(T_PLANCK > T_ELECTROWEAK);
        assert!(T_ELECTROWEAK > T_QUARK_HADRON);
        assert!(T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
        assert!(T_NUCLEOSYNTHESIS > T_RECOMBINATION);
        assert!(T_RECOMBINATION > T_CMB);
    }

    /// Earth surface temperature is reasonable (~288 K).
    #[test]
    fn earth_surface_temperature() {
        assert!((T_EARTH_SURFACE - 288.0).abs() < 1e-10);
    }

    /// CMB temperature is approximately 2.725 K.
    #[test]
    fn cmb_temperature() {
        assert!((T_CMB - 2.725).abs() < 1e-10);
    }

    // -----------------------------------------------------------------------
    // Chemistry parameters
    // -----------------------------------------------------------------------

    /// Electron shell capacities start with 2 and sum correctly.
    #[test]
    fn electron_shells_first_is_two() {
        assert_eq!(ELECTRON_SHELLS[0], 2);
    }

    /// Bond energies are ordered: van der Waals < hydrogen < covalent < ionic.
    #[test]
    fn bond_energy_ordering() {
        assert!(BOND_ENERGY_VAN_DER_WAALS < BOND_ENERGY_HYDROGEN);
        assert!(BOND_ENERGY_HYDROGEN < BOND_ENERGY_COVALENT);
        assert!(BOND_ENERGY_COVALENT < BOND_ENERGY_IONIC);
    }

    // -----------------------------------------------------------------------
    // Biology parameters
    // -----------------------------------------------------------------------

    /// DNA uses four nucleotide bases: A, T, G, C.
    #[test]
    fn nucleotide_bases_are_atgc() {
        assert_eq!(NUCLEOTIDE_BASES, &['A', 'T', 'G', 'C']);
    }

    /// RNA replaces T with U.
    #[test]
    fn rna_bases_are_augc() {
        assert_eq!(RNA_BASES, &['A', 'U', 'G', 'C']);
    }

    /// There are exactly 20 standard amino acids.
    #[test]
    fn twenty_amino_acids() {
        assert_eq!(AMINO_ACIDS.len(), 20);
    }

    // -----------------------------------------------------------------------
    // Codon table
    // -----------------------------------------------------------------------

    /// AUG is the start codon (methionine).
    #[test]
    fn aug_is_start_codon() {
        assert_eq!(codon_to_amino_acid("AUG"), Some("Met"));
    }

    /// Stop codons return "STOP".
    #[test]
    fn stop_codons() {
        assert_eq!(codon_to_amino_acid("UAA"), Some("STOP"));
        assert_eq!(codon_to_amino_acid("UAG"), Some("STOP"));
        assert_eq!(codon_to_amino_acid("UGA"), Some("STOP"));
    }

    /// Invalid codons return None.
    #[test]
    fn invalid_codon_returns_none() {
        assert_eq!(codon_to_amino_acid("XYZ"), None);
        assert_eq!(codon_to_amino_acid(""), None);
    }

    /// Known codon-to-amino-acid mappings.
    #[test]
    fn known_codon_mappings() {
        assert_eq!(codon_to_amino_acid("UUU"), Some("Phe"));
        assert_eq!(codon_to_amino_acid("UUC"), Some("Phe"));
        assert_eq!(codon_to_amino_acid("GGG"), Some("Gly"));
        assert_eq!(codon_to_amino_acid("UGG"), Some("Trp"));
    }

    /// Synonymous codons encode the same amino acid (degeneracy).
    #[test]
    fn codon_degeneracy() {
        // Leucine has 6 codons
        let leu_codons = ["UUA", "UUG", "CUU", "CUC", "CUA", "CUG"];
        for codon in &leu_codons {
            assert_eq!(codon_to_amino_acid(codon), Some("Leu"));
        }
    }

    // -----------------------------------------------------------------------
    // ParticleType
    // -----------------------------------------------------------------------

    /// Every ParticleType has a non-empty label.
    #[test]
    fn particle_type_labels_non_empty() {
        let types = [
            ParticleType::Up, ParticleType::Down, ParticleType::Electron,
            ParticleType::Positron, ParticleType::Neutrino, ParticleType::Photon,
            ParticleType::Gluon, ParticleType::WBoson, ParticleType::ZBoson,
            ParticleType::Proton, ParticleType::Neutron,
        ];
        for pt in &types {
            assert!(!pt.label().is_empty());
        }
    }

    /// Particle masses match the mass constants.
    #[test]
    fn particle_type_mass_matches_constants() {
        assert_eq!(ParticleType::Electron.mass(), M_ELECTRON);
        assert_eq!(ParticleType::Proton.mass(), M_PROTON);
        assert_eq!(ParticleType::Neutron.mass(), M_NEUTRON);
        assert_eq!(ParticleType::Photon.mass(), M_PHOTON);
    }

    /// Proton charge is +1, electron charge is -1, neutron is 0.
    #[test]
    fn particle_charges() {
        assert_eq!(ParticleType::Proton.charge(), 1.0);
        assert_eq!(ParticleType::Electron.charge(), -1.0);
        assert_eq!(ParticleType::Neutron.charge(), 0.0);
        assert_eq!(ParticleType::Photon.charge(), 0.0);
    }

    /// Up quark charge is +2/3, down quark charge is -1/3.
    #[test]
    fn quark_charges() {
        assert!((ParticleType::Up.charge() - 2.0 / 3.0).abs() < 1e-10);
        assert!((ParticleType::Down.charge() - (-1.0 / 3.0)).abs() < 1e-10);
    }

    /// Positron has opposite charge to electron.
    #[test]
    fn positron_charge() {
        assert_eq!(ParticleType::Positron.charge(), -ParticleType::Electron.charge());
    }

    /// All render colors have 4 components in [0, 1].
    #[test]
    fn render_colors_valid_range() {
        let types = [
            ParticleType::Up, ParticleType::Down, ParticleType::Electron,
            ParticleType::Positron, ParticleType::Neutrino, ParticleType::Photon,
            ParticleType::Gluon, ParticleType::WBoson, ParticleType::ZBoson,
            ParticleType::Proton, ParticleType::Neutron,
        ];
        for pt in &types {
            let c = pt.render_color();
            for val in &c {
                assert!(*val >= 0.0 && *val <= 1.0, "{:?} has out-of-range color", pt);
            }
        }
    }

    // -----------------------------------------------------------------------
    // Spin
    // -----------------------------------------------------------------------

    /// Spin up is +0.5, spin down is -0.5.
    #[test]
    fn spin_values() {
        assert_eq!(Spin::Up.value(), 0.5);
        assert_eq!(Spin::Down.value(), -0.5);
    }

    // -----------------------------------------------------------------------
    // Element data
    // -----------------------------------------------------------------------

    /// Hydrogen is element 1 with symbol "H".
    #[test]
    fn hydrogen_element_data() {
        let (sym, name, group, period, en) = element_data(1).unwrap();
        assert_eq!(sym, "H");
        assert_eq!(name, "Hydrogen");
        assert_eq!(group, 1);
        assert_eq!(period, 1);
        assert!((en - 2.20).abs() < 1e-10);
    }

    /// Iron is element 26.
    #[test]
    fn iron_element_data() {
        let (sym, name, _, _, _) = element_data(26).unwrap();
        assert_eq!(sym, "Fe");
        assert_eq!(name, "Iron");
    }

    /// Unknown elements return None.
    #[test]
    fn unknown_element_returns_none() {
        assert!(element_data(0).is_none());
        assert!(element_data(99).is_none());
    }

    /// Noble gases have electronegativity 0.
    #[test]
    fn noble_gas_electronegativity_zero() {
        let (_, _, _, _, en) = element_data(2).unwrap();  // He
        assert_eq!(en, 0.0);
        let (_, _, _, _, en) = element_data(10).unwrap(); // Ne
        assert_eq!(en, 0.0);
        let (_, _, _, _, en) = element_data(18).unwrap(); // Ar
        assert_eq!(en, 0.0);
    }

    // -----------------------------------------------------------------------
    // Epigenetic / environmental parameter sanity
    // -----------------------------------------------------------------------

    /// Methylation probability is greater than demethylation probability
    /// (methylation accumulates over time).
    #[test]
    fn methylation_accumulates() {
        assert!(METHYLATION_PROBABILITY > DEMETHYLATION_PROBABILITY);
    }

    /// UV mutation rate is higher than cosmic ray mutation rate.
    #[test]
    fn uv_mutation_rate_dominates() {
        assert!(UV_MUTATION_RATE > COSMIC_RAY_MUTATION_RATE);
    }
}
