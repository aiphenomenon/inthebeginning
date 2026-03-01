//! Physical constants and simulation parameters.
//!
//! All values are in simulation units (SU) scaled for computational tractability.
//! Real-world proportions are maintained where possible.
//! Ported from the Python `simulator/constants.py`.

use std::f64::consts::PI as PI_F64;

// === Fundamental Constants (simulation-scaled) ===
pub const C: f64 = 1.0;
pub const HBAR: f64 = 0.01;
pub const K_B: f64 = 0.001;
pub const G: f64 = 1e-6;
pub const ALPHA: f64 = 1.0 / 137.0;
pub const E_CHARGE: f64 = 0.1;
pub const PI: f64 = PI_F64;

// === Particle masses (SU, proportional to real) ===
pub const M_ELECTRON: f64 = 1.0;
pub const M_UP_QUARK: f64 = 4.4;
pub const M_DOWN_QUARK: f64 = 9.4;
pub const M_PROTON: f64 = 1836.0;
pub const M_NEUTRON: f64 = 1839.0;
pub const M_PHOTON: f64 = 0.0;
pub const M_NEUTRINO: f64 = 1e-6;
pub const M_W_BOSON: f64 = 157_000.0;
pub const M_Z_BOSON: f64 = 178_000.0;
pub const M_HIGGS: f64 = 245_000.0;

// === Force coupling strengths (dimensionless) ===
pub const STRONG_COUPLING: f64 = 1.0;
pub const EM_COUPLING: f64 = ALPHA;
pub const WEAK_COUPLING: f64 = 1e-6;
pub const GRAVITY_COUPLING: f64 = 1e-38;

// === Nuclear parameters ===
pub const NUCLEAR_RADIUS: f64 = 0.01;
pub const BINDING_ENERGY_DEUTERIUM: f64 = 2.22;
pub const BINDING_ENERGY_HELIUM4: f64 = 28.3;
pub const BINDING_ENERGY_CARBON12: f64 = 92.16;
pub const BINDING_ENERGY_IRON56: f64 = 492.26;

// === Cosmic timeline (simulation ticks) ===
pub const PLANCK_EPOCH: u64 = 1;
pub const INFLATION_EPOCH: u64 = 10;
pub const ELECTROWEAK_EPOCH: u64 = 100;
pub const QUARK_EPOCH: u64 = 1_000;
pub const HADRON_EPOCH: u64 = 5_000;
pub const NUCLEOSYNTHESIS_EPOCH: u64 = 10_000;
pub const RECOMBINATION_EPOCH: u64 = 50_000;
pub const STAR_FORMATION_EPOCH: u64 = 100_000;
pub const SOLAR_SYSTEM_EPOCH: u64 = 200_000;
pub const EARTH_EPOCH: u64 = 210_000;
pub const LIFE_EPOCH: u64 = 250_000;
pub const DNA_EPOCH: u64 = 280_000;
pub const PRESENT_EPOCH: u64 = 300_000;

// === Temperature scale (simulation Kelvin) ===
pub const T_PLANCK: f64 = 1e10;
pub const T_ELECTROWEAK: f64 = 1e8;
pub const T_QUARK_HADRON: f64 = 1e6;
pub const T_NUCLEOSYNTHESIS: f64 = 1e4;
pub const T_RECOMBINATION: f64 = 3_000.0;
pub const T_CMB: f64 = 2.725;
pub const T_STELLAR_CORE: f64 = 1.5e4;
pub const T_EARTH_SURFACE: f64 = 288.0;

// === Chemistry parameters ===
pub const ELECTRON_SHELLS: [u32; 7] = [2, 8, 18, 32, 32, 18, 8];
pub const BOND_ENERGY_COVALENT: f64 = 3.5;
pub const BOND_ENERGY_IONIC: f64 = 5.0;
pub const BOND_ENERGY_HYDROGEN: f64 = 0.2;
pub const BOND_ENERGY_VAN_DER_WAALS: f64 = 0.01;

// === Biology parameters ===
pub const METHYLATION_PROBABILITY: f64 = 0.03;
pub const DEMETHYLATION_PROBABILITY: f64 = 0.01;
pub const HISTONE_ACETYLATION_PROB: f64 = 0.02;
pub const HISTONE_DEACETYLATION_PROB: f64 = 0.015;
pub const CHROMATIN_REMODEL_ENERGY: f64 = 1.5;
pub const UV_MUTATION_RATE: f64 = 1e-4;
pub const COSMIC_RAY_MUTATION_RATE: f64 = 1e-6;
pub const THERMAL_FLUCTUATION: f64 = 0.01;
pub const RADIATION_DAMAGE_THRESHOLD: f64 = 10.0;

// === Epoch information for display ===
#[derive(Debug, Clone)]
pub struct EpochInfo {
    pub name: &'static str,
    pub start_tick: u64,
    pub description: &'static str,
}

pub const EPOCHS: &[EpochInfo] = &[
    EpochInfo {
        name: "Planck",
        start_tick: PLANCK_EPOCH,
        description: "All forces unified, T~10^32K",
    },
    EpochInfo {
        name: "Inflation",
        start_tick: INFLATION_EPOCH,
        description: "Exponential expansion, quantum fluctuations seed structure",
    },
    EpochInfo {
        name: "Electroweak",
        start_tick: ELECTROWEAK_EPOCH,
        description: "Electromagnetic and weak forces separate",
    },
    EpochInfo {
        name: "Quark",
        start_tick: QUARK_EPOCH,
        description: "Quark-gluon plasma, free quarks",
    },
    EpochInfo {
        name: "Hadron",
        start_tick: HADRON_EPOCH,
        description: "Quarks confined into protons and neutrons",
    },
    EpochInfo {
        name: "Nucleosynthesis",
        start_tick: NUCLEOSYNTHESIS_EPOCH,
        description: "Light nuclei form: H, He, Li",
    },
    EpochInfo {
        name: "Recombination",
        start_tick: RECOMBINATION_EPOCH,
        description: "Atoms form, universe becomes transparent",
    },
    EpochInfo {
        name: "Star Formation",
        start_tick: STAR_FORMATION_EPOCH,
        description: "First stars ignite, heavier elements forged",
    },
    EpochInfo {
        name: "Solar System",
        start_tick: SOLAR_SYSTEM_EPOCH,
        description: "Our solar system coalesces from stellar debris",
    },
    EpochInfo {
        name: "Earth",
        start_tick: EARTH_EPOCH,
        description: "Earth forms, oceans appear",
    },
    EpochInfo {
        name: "Life",
        start_tick: LIFE_EPOCH,
        description: "First self-replicating molecules",
    },
    EpochInfo {
        name: "DNA Era",
        start_tick: DNA_EPOCH,
        description: "DNA-based life, epigenetics emerge",
    },
    EpochInfo {
        name: "Present",
        start_tick: PRESENT_EPOCH,
        description: "Complex life, intelligence",
    },
];

/// Get the epoch name for a given tick.
pub fn epoch_name_for_tick(tick: u64) -> &'static str {
    let mut name = "Void";
    for epoch in EPOCHS {
        if tick >= epoch.start_tick {
            name = epoch.name;
        }
    }
    name
}

/// Get the epoch description for a given tick.
pub fn epoch_description_for_tick(tick: u64) -> &'static str {
    let mut desc = "Before time itself";
    for epoch in EPOCHS {
        if tick >= epoch.start_tick {
            desc = epoch.description;
        }
    }
    desc
}

/// Background color (r, g, b) for a given epoch, used by the renderer.
/// Colors shift: hot white -> orange -> blue -> dark blue -> green-tinged -> earth tones
pub fn epoch_background_color(tick: u64) -> [f32; 3] {
    let t = tick as f32;
    let max = PRESENT_EPOCH as f32;
    let frac = (t / max).clamp(0.0, 1.0);

    if tick < INFLATION_EPOCH {
        // Hot white
        [1.0, 1.0, 1.0]
    } else if tick < QUARK_EPOCH {
        // Hot white -> bright orange
        let f = (t - INFLATION_EPOCH as f32) / (QUARK_EPOCH as f32 - INFLATION_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [1.0, 1.0 - f * 0.3, 1.0 - f * 0.7]
    } else if tick < HADRON_EPOCH {
        // Bright orange -> dark orange/red
        let f = (t - QUARK_EPOCH as f32) / (HADRON_EPOCH as f32 - QUARK_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [1.0 - f * 0.3, 0.7 - f * 0.3, 0.3 - f * 0.2]
    } else if tick < RECOMBINATION_EPOCH {
        // Dark orange -> deep blue (recombination = transparency)
        let f = (t - HADRON_EPOCH as f32) / (RECOMBINATION_EPOCH as f32 - HADRON_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [0.7 - f * 0.65, 0.4 - f * 0.3, 0.1 + f * 0.5]
    } else if tick < STAR_FORMATION_EPOCH {
        // Deep blue -> dark blue (dark ages)
        let f = (t - RECOMBINATION_EPOCH as f32)
            / (STAR_FORMATION_EPOCH as f32 - RECOMBINATION_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [0.05 - f * 0.03, 0.1 - f * 0.05, 0.6 - f * 0.35]
    } else if tick < EARTH_EPOCH {
        // Dark blue -> slightly lighter blue (stars appear)
        let f =
            (t - STAR_FORMATION_EPOCH as f32) / (EARTH_EPOCH as f32 - STAR_FORMATION_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [0.02 + f * 0.03, 0.05 + f * 0.05, 0.25 + f * 0.1]
    } else if tick < LIFE_EPOCH {
        // Dark blue -> green-tinged (Earth forming, oceans)
        let f = (t - EARTH_EPOCH as f32) / (LIFE_EPOCH as f32 - EARTH_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [0.05, 0.1 + f * 0.12, 0.35 - f * 0.1]
    } else {
        // Green-tinged -> earth tones (life to present)
        let f = (t - LIFE_EPOCH as f32) / (PRESENT_EPOCH as f32 - LIFE_EPOCH as f32);
        let f = f.clamp(0.0, 1.0);
        [0.05 + f * 0.1, 0.22 + f * 0.08, 0.25 - f * 0.1]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fundamental_constants() {
        assert_eq!(C, 1.0);
        assert_eq!(HBAR, 0.01);
        assert_eq!(K_B, 0.001);
        assert!((ALPHA - 1.0 / 137.0).abs() < 1e-10);
    }

    #[test]
    fn test_particle_masses_ordering() {
        // Electron is lightest massive particle
        assert!(M_ELECTRON < M_UP_QUARK);
        assert!(M_UP_QUARK < M_DOWN_QUARK);
        assert!(M_DOWN_QUARK < M_PROTON);
        assert!(M_PROTON < M_NEUTRON);
        assert_eq!(M_PHOTON, 0.0);
        // Proton mass should be approximately 1836 electron masses
        assert_eq!(M_PROTON, 1836.0);
    }

    #[test]
    fn test_force_coupling_hierarchy() {
        // Strong > EM > Weak > Gravity
        assert!(STRONG_COUPLING > EM_COUPLING);
        assert!(EM_COUPLING > WEAK_COUPLING);
        assert!(WEAK_COUPLING > GRAVITY_COUPLING);
    }

    #[test]
    fn test_epoch_ordering() {
        assert!(PLANCK_EPOCH < INFLATION_EPOCH);
        assert!(INFLATION_EPOCH < ELECTROWEAK_EPOCH);
        assert!(ELECTROWEAK_EPOCH < QUARK_EPOCH);
        assert!(QUARK_EPOCH < HADRON_EPOCH);
        assert!(HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
        assert!(NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
        assert!(RECOMBINATION_EPOCH < STAR_FORMATION_EPOCH);
        assert!(STAR_FORMATION_EPOCH < SOLAR_SYSTEM_EPOCH);
        assert!(SOLAR_SYSTEM_EPOCH < EARTH_EPOCH);
        assert!(EARTH_EPOCH < LIFE_EPOCH);
        assert!(LIFE_EPOCH < DNA_EPOCH);
        assert!(DNA_EPOCH < PRESENT_EPOCH);
    }

    #[test]
    fn test_temperature_ordering() {
        // Universe cools over time
        assert!(T_PLANCK > T_ELECTROWEAK);
        assert!(T_ELECTROWEAK > T_QUARK_HADRON);
        assert!(T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
        assert!(T_NUCLEOSYNTHESIS > T_RECOMBINATION);
        assert!(T_RECOMBINATION > T_CMB);
    }

    #[test]
    fn test_electron_shells() {
        assert_eq!(ELECTRON_SHELLS[0], 2);  // 1s
        assert_eq!(ELECTRON_SHELLS[1], 8);  // 2s2p
        assert_eq!(ELECTRON_SHELLS.len(), 7);
    }

    #[test]
    fn test_epoch_name_for_tick() {
        assert_eq!(epoch_name_for_tick(0), "Void");
        assert_eq!(epoch_name_for_tick(1), "Planck");
        assert_eq!(epoch_name_for_tick(5), "Planck");
        assert_eq!(epoch_name_for_tick(10), "Inflation");
        assert_eq!(epoch_name_for_tick(100), "Electroweak");
        assert_eq!(epoch_name_for_tick(1000), "Quark");
        assert_eq!(epoch_name_for_tick(5000), "Hadron");
        assert_eq!(epoch_name_for_tick(10_000), "Nucleosynthesis");
        assert_eq!(epoch_name_for_tick(50_000), "Recombination");
        assert_eq!(epoch_name_for_tick(100_000), "Star Formation");
        assert_eq!(epoch_name_for_tick(200_000), "Solar System");
        assert_eq!(epoch_name_for_tick(210_000), "Earth");
        assert_eq!(epoch_name_for_tick(250_000), "Life");
        assert_eq!(epoch_name_for_tick(280_000), "DNA Era");
        assert_eq!(epoch_name_for_tick(300_000), "Present");
    }

    #[test]
    fn test_epoch_description_for_tick() {
        let desc = epoch_description_for_tick(0);
        assert_eq!(desc, "Before time itself");

        let desc = epoch_description_for_tick(PLANCK_EPOCH);
        assert!(desc.contains("unified"));

        let desc = epoch_description_for_tick(LIFE_EPOCH);
        assert!(desc.contains("self-replicating"));
    }

    #[test]
    fn test_epoch_background_color_early() {
        let color = epoch_background_color(0);
        // Before inflation: hot white
        assert_eq!(color, [1.0, 1.0, 1.0]);
    }

    #[test]
    fn test_epoch_background_color_ranges() {
        // Colors should always be in valid range [0, 1]
        let test_ticks = [0, 5, 50, 500, 3000, 7000, 25000, 75000, 150000, 205000, 230000, 290000];
        for &tick in &test_ticks {
            let color = epoch_background_color(tick);
            for &c in &color {
                assert!(c >= 0.0, "Color component negative at tick {}: {:?}", tick, color);
                assert!(c <= 1.0, "Color component > 1 at tick {}: {:?}", tick, color);
            }
        }
    }

    #[test]
    fn test_epochs_array_completeness() {
        assert_eq!(EPOCHS.len(), 13);
        // First epoch should be Planck
        assert_eq!(EPOCHS[0].name, "Planck");
        // Last epoch should be Present
        assert_eq!(EPOCHS[EPOCHS.len() - 1].name, "Present");
    }

    #[test]
    fn test_binding_energies_ordering() {
        // Heavier nuclei should have higher binding energy
        assert!(BINDING_ENERGY_DEUTERIUM < BINDING_ENERGY_HELIUM4);
        assert!(BINDING_ENERGY_HELIUM4 < BINDING_ENERGY_CARBON12);
        assert!(BINDING_ENERGY_CARBON12 < BINDING_ENERGY_IRON56);
    }

    #[test]
    fn test_biology_probabilities_valid() {
        assert!(METHYLATION_PROBABILITY > 0.0 && METHYLATION_PROBABILITY < 1.0);
        assert!(DEMETHYLATION_PROBABILITY > 0.0 && DEMETHYLATION_PROBABILITY < 1.0);
        assert!(HISTONE_ACETYLATION_PROB > 0.0 && HISTONE_ACETYLATION_PROB < 1.0);
        assert!(HISTONE_DEACETYLATION_PROB > 0.0 && HISTONE_DEACETYLATION_PROB < 1.0);
        assert!(UV_MUTATION_RATE > 0.0 && UV_MUTATION_RATE < 1.0);
        assert!(COSMIC_RAY_MUTATION_RATE > 0.0 && COSMIC_RAY_MUTATION_RATE < 1.0);
    }

    #[test]
    fn test_bond_energies_ordering() {
        // Van der Waals < hydrogen bond < covalent < ionic
        assert!(BOND_ENERGY_VAN_DER_WAALS < BOND_ENERGY_HYDROGEN);
        assert!(BOND_ENERGY_HYDROGEN < BOND_ENERGY_COVALENT);
        assert!(BOND_ENERGY_COVALENT < BOND_ENERGY_IONIC);
    }
}
