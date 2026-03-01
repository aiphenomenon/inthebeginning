//! Universe orchestrator.
//!
//! Manages the 13 cosmic epochs from the Planck era through the emergence
//! of complex life. Coordinates quantum fields, atomic systems, chemistry,
//! environment, and biology across the cosmic timeline.

use rand::Rng;

use super::constants::*;
use super::quantum::QuantumField;
use super::atomic::{Atom, AtomicSystem};
use super::chemistry::ChemicalSystem;
use super::biology::BiologicalSystem;
use super::environment::Environment;

// ---------------------------------------------------------------------------
// Epoch tracking
// ---------------------------------------------------------------------------

/// Which epoch are we currently in?
pub fn current_epoch(tick: u64) -> &'static EpochInfo {
    let mut current = &EPOCHS[0];
    for epoch in EPOCHS {
        if tick >= epoch.start_tick {
            current = epoch;
        }
    }
    current
}

/// Index of the current epoch (0..12).
pub fn epoch_index(tick: u64) -> usize {
    let mut idx = 0;
    for (i, epoch) in EPOCHS.iter().enumerate() {
        if tick >= epoch.start_tick {
            idx = i;
        }
    }
    idx
}

/// Compute the target temperature for a given tick via log-interpolation
/// between known epoch temperatures.
fn target_temperature(tick: u64) -> f64 {
    // (tick, temperature) anchors
    let anchors: &[(u64, f64)] = &[
        (PLANCK_EPOCH,            T_PLANCK),         // 1e10
        (INFLATION_EPOCH,         1e9),
        (ELECTROWEAK_EPOCH,       T_ELECTROWEAK),    // 1e8
        (QUARK_EPOCH,             T_QUARK_HADRON),   // 1e6
        (HADRON_EPOCH,            1e5),
        (NUCLEOSYNTHESIS_EPOCH,   T_NUCLEOSYNTHESIS),// 1e4
        (RECOMBINATION_EPOCH,     T_RECOMBINATION),  // 3000
        (STAR_FORMATION_EPOCH,    1000.0),
        (SOLAR_SYSTEM_EPOCH,      500.0),
        (EARTH_EPOCH,             400.0),
        (LIFE_EPOCH,              T_EARTH_SURFACE),  // 288
        (DNA_EPOCH,               T_EARTH_SURFACE),
        (PRESENT_EPOCH,           T_EARTH_SURFACE),
    ];

    if tick <= anchors[0].0 {
        return anchors[0].1;
    }
    if tick >= anchors[anchors.len() - 1].0 {
        return anchors[anchors.len() - 1].1;
    }

    // Find the bounding anchors and log-interpolate
    for i in 0..anchors.len() - 1 {
        let (t0, temp0) = anchors[i];
        let (t1, temp1) = anchors[i + 1];
        if tick >= t0 && tick < t1 {
            let frac = (tick - t0) as f64 / (t1 - t0) as f64;
            let log_t0 = temp0.max(1.0).ln();
            let log_t1 = temp1.max(1.0).ln();
            return (log_t0 + frac * (log_t1 - log_t0)).exp();
        }
    }

    T_EARTH_SURFACE
}

// ---------------------------------------------------------------------------
// SimStats -- snapshot of universe state
// ---------------------------------------------------------------------------

/// Statistics snapshot for display.
#[derive(Debug, Clone)]
pub struct SimStats {
    pub tick: u64,
    pub epoch_name: String,
    pub epoch_description: String,
    pub temperature: f64,
    pub total_energy: f64,
    pub particle_count: usize,
    pub atom_count: usize,
    pub molecule_count: usize,
    pub water_count: u64,
    pub amino_acid_count: u64,
    pub nucleotide_count: u64,
    pub population: usize,
    pub generation: u64,
    pub average_fitness: f64,
    pub species_count: usize,
    pub is_habitable: bool,
    pub oxygen_pct: f64,
}

// ---------------------------------------------------------------------------
// Universe
// ---------------------------------------------------------------------------

/// The Universe: orchestrates all subsystems.
pub struct Universe {
    pub tick: u64,
    pub quantum_field: QuantumField,
    pub atomic_system: AtomicSystem,
    pub chemical_system: ChemicalSystem,
    pub biological_system: BiologicalSystem,
    pub environment: Environment,
    pub scale_factor: f64,
    pub last_epoch_index: usize,
    nucleosynthesis_done: bool,
    recombination_done: bool,
    earth_initialized: bool,
    stellar_seeded: bool,
    solar_seeded: bool,
}

impl Universe {
    /// Create a new Universe at the Big Bang (tick 0).
    pub fn new() -> Self {
        Self {
            tick: 0,
            quantum_field: QuantumField::new(T_PLANCK),
            atomic_system: AtomicSystem::new(T_PLANCK),
            chemical_system: ChemicalSystem::new(),
            biological_system: BiologicalSystem::new(),
            environment: Environment::interstellar(),
            scale_factor: 1.0,
            last_epoch_index: 0,
            nucleosynthesis_done: false,
            recombination_done: false,
            earth_initialized: false,
            stellar_seeded: false,
            solar_seeded: false,
        }
    }

    /// Advance the universe by one tick. Returns true if a new epoch began.
    pub fn step(&mut self) -> bool {
        self.tick += 1;
        let ei = epoch_index(self.tick);
        let new_epoch = ei != self.last_epoch_index;
        self.last_epoch_index = ei;

        // Enforce the cosmic cooling curve
        let t_target = target_temperature(self.tick);
        self.quantum_field.temperature = t_target;
        self.atomic_system.temperature = t_target;

        match ei {
            0 => self.step_planck(),
            1 => self.step_inflation(),
            2 => self.step_electroweak(),
            3 => self.step_quark(),
            4 => self.step_hadron(),
            5 => self.step_nucleosynthesis(),
            6 => self.step_recombination(),
            7 => self.step_star_formation(),
            8 => self.step_solar_system(),
            9 => self.step_earth(),
            10 => self.step_life(),
            11 => self.step_dna(),
            12 => self.step_present(),
            _ => {}
        }

        new_epoch
    }

    // --- Epoch step functions ---

    fn step_planck(&mut self) {
        // Quantum fluctuations at the Planck scale
        self.quantum_field.vacuum_fluctuation();
        self.quantum_field.evolve(0.001);
    }

    fn step_inflation(&mut self) {
        // Exponential expansion, copious pair production
        let mut rng = rand::thread_rng();
        self.scale_factor *= 1.0 + rng.gen::<f64>() * 0.1;

        // Massive pair production during reheating
        for _ in 0..3 {
            let energy = self.quantum_field.temperature * K_B * rng.gen::<f64>() * 10.0;
            self.quantum_field.pair_production(energy);
        }
        self.quantum_field.vacuum_fluctuation();
        self.quantum_field.evolve(0.01);
    }

    fn step_electroweak(&mut self) {
        // Electroweak symmetry breaking
        let mut rng = rand::thread_rng();
        if rng.gen::<f64>() < 0.5 {
            let energy = self.quantum_field.temperature * K_B * rng.gen::<f64>() * 5.0;
            self.quantum_field.pair_production(energy);
        }
        self.quantum_field.vacuum_fluctuation();
        self.quantum_field.evolve(0.01);
    }

    fn step_quark(&mut self) {
        // Quark-gluon plasma
        let mut rng = rand::thread_rng();
        if rng.gen::<f64>() < 0.3 {
            let energy = self.quantum_field.temperature * K_B * rng.gen::<f64>() * 3.0;
            self.quantum_field.pair_production(energy);
        }
        self.quantum_field.evolve(0.01);
    }

    fn step_hadron(&mut self) {
        // Quark confinement into hadrons
        self.quantum_field.quark_confinement();
        self.quantum_field.evolve(0.01);
    }

    fn step_nucleosynthesis(&mut self) {
        // Big Bang nucleosynthesis: form light nuclei (H, He, Li)
        // This is a one-time bulk event at the start of the epoch.
        if !self.nucleosynthesis_done {
            self.nucleosynthesis_done = true;

            // Count protons and neutrons in the quantum field
            let counts = self.quantum_field.particle_count();
            let protons = *counts.get(&ParticleType::Proton).unwrap_or(&0) as u32;
            let neutrons = *counts.get(&ParticleType::Neutron).unwrap_or(&0) as u32;

            // BBN ratio: ~7:1 proton:neutron by this point
            // Use all available neutrons, pair them with protons
            if protons > 0 && neutrons > 0 {
                let n_use = neutrons;
                let p_use = protons.min(n_use * 7); // roughly 7:1 ratio remaining
                self.atomic_system.nucleosynthesis(p_use, n_use);
            }

            // Also add some extra hydrogen from remaining protons
            let remaining_p = protons.saturating_sub(neutrons * 7);
            if remaining_p > 0 {
                self.atomic_system.nucleosynthesis(remaining_p, 0);
            }
        }

        self.quantum_field.evolve(0.01);
    }

    fn step_recombination(&mut self) {
        // Atoms form as electrons bind to nuclei. Universe becomes transparent.
        // At T < 3000K, electrons combine with protons to form neutral H.
        // We model this as a one-time conversion at the start of the epoch
        // plus continued recombination of any remaining field particles.
        if !self.recombination_done {
            self.recombination_done = true;
            // Force recombination of field protons + electrons into H atoms
            self.atomic_system.temperature = T_RECOMBINATION;
            self.atomic_system.recombination(&mut self.quantum_field);
        }
    }

    fn step_star_formation(&mut self) {
        // Stellar nucleosynthesis: forge heavier elements in stellar cores
        self.atomic_system.stellar_nucleosynthesis(T_STELLAR_CORE);

        // At the start of this epoch, seed heavier elements from supernovae.
        // Real stellar populations process vast amounts of H/He into C,N,O,Fe
        // over hundreds of millions of years. We represent this as a batch.
        if !self.stellar_seeded {
            self.stellar_seeded = true;
            let mut rng = rand::thread_rng();
            // Supernova debris: C, N, O, P, S, Fe plus lots of H
            let seed_elements: &[(u32, u32, usize)] = &[
                // (atomic_number, mass_number, count)
                (1,  1,   200),  // Hydrogen
                (6,  12,  60),   // Carbon
                (7,  14,  40),   // Nitrogen
                (8,  16,  80),   // Oxygen
                (15, 31,  15),   // Phosphorus
                (16, 32,  10),   // Sulfur
                (26, 56,  5),    // Iron
            ];
            for &(z, mn, count) in seed_elements {
                for _ in 0..count {
                    let atom = Atom::new(z)
                        .with_mass_number(mn)
                        .with_position([
                            rng.gen::<f64>() * 20.0 - 10.0,
                            rng.gen::<f64>() * 20.0 - 10.0,
                            rng.gen::<f64>() * 20.0 - 10.0,
                        ]);
                    self.atomic_system.atoms.push(atom);
                }
            }
        }

        // Form simple molecules in cooler regions (limit to preserve atoms)
        if self.chemical_system.water_count < 50 {
            self.chemical_system.form_water(&mut self.atomic_system.atoms);
        }
        if self.chemical_system.molecules.len() < 100 {
            self.chemical_system.form_methane(&mut self.atomic_system.atoms);
            self.chemical_system.form_ammonia(&mut self.atomic_system.atoms);
        }
    }

    fn step_solar_system(&mut self) {
        // Solar system coalesces from stellar debris
        if !self.solar_seeded {
            self.solar_seeded = true;
            let mut rng = rand::thread_rng();
            // Additional material accreted into the solar nebula
            let seed_elements: &[(u32, u32, usize)] = &[
                (1,  1,   100),  // Hydrogen
                (6,  12,  30),   // Carbon
                (7,  14,  20),   // Nitrogen
                (8,  16,  50),   // Oxygen
                (15, 31,  10),   // Phosphorus
                (16, 32,  5),    // Sulfur
            ];
            for &(z, mn, count) in seed_elements {
                for _ in 0..count {
                    let atom = Atom::new(z)
                        .with_mass_number(mn)
                        .with_position([
                            rng.gen::<f64>() * 10.0 - 5.0,
                            rng.gen::<f64>() * 10.0 - 5.0,
                            rng.gen::<f64>() * 10.0 - 5.0,
                        ]);
                    self.atomic_system.atoms.push(atom);
                }
            }
        }

        self.atomic_system.stellar_nucleosynthesis(T_STELLAR_CORE);
        if self.chemical_system.water_count < 80 {
            self.chemical_system.form_water(&mut self.atomic_system.atoms);
        }
        if self.chemical_system.molecules.len() < 120 {
            self.chemical_system.form_methane(&mut self.atomic_system.atoms);
            self.chemical_system.form_ammonia(&mut self.atomic_system.atoms);
        }
    }

    fn step_earth(&mut self) {
        // Earth forms, oceans appear, environment initializes
        if !self.earth_initialized {
            self.earth_initialized = true;
            self.environment = Environment::early_earth();

            // Seed Earth's crust and ocean with CHONPS atoms for prebiotic chemistry.
            // In reality, Earth's inventory of these elements comes from the accretion
            // disk and late heavy bombardment by comets and asteroids.
            let mut rng = rand::thread_rng();
            let earth_elements: &[(u32, u32, usize)] = &[
                (1,  1,   1500), // Hydrogen (from water, organics)
                (6,  12,  600),  // Carbon
                (7,  14,  400),  // Nitrogen
                (8,  16,  800),  // Oxygen
                (15, 31,  60),   // Phosphorus
                (16, 32,  50),   // Sulfur
            ];
            for &(z, mn, count) in earth_elements {
                for _ in 0..count {
                    let atom = Atom::new(z)
                        .with_mass_number(mn)
                        .with_position([
                            rng.gen::<f64>() * 6.0 - 3.0,
                            rng.gen::<f64>() * 6.0 - 3.0,
                            rng.gen::<f64>() * 6.0 - 3.0,
                        ]);
                    self.atomic_system.atoms.push(atom);
                }
            }
        }

        // Cool toward habitable
        let target = T_EARTH_SURFACE;
        self.environment.temperature +=
            (target - self.environment.temperature) * 0.01;
        self.environment.ocean_coverage =
            (self.environment.ocean_coverage + 0.001).min(0.7);
        self.environment.land_coverage = 1.0 - self.environment.ocean_coverage;

        // Chemistry in the ocean and hydrothermal vents.
        // Catalyzed reactions form amino acids and nucleotides from raw atoms.
        // We do NOT greedily form water here, preserving atoms for prebiotic chemistry.
        self.chemical_system.catalyzed_reaction(
            &mut self.atomic_system.atoms,
            self.environment.temperature,
            self.environment.volcanism > 0.5,
        );
    }

    fn step_life(&mut self) {
        // Abiogenesis: first self-replicating molecules
        if !self.environment.is_habitable() {
            self.environment.make_habitable();
        }
        self.environment.tick(self.biological_system.population.len());

        // Prebiotic chemistry: form amino acids and nucleotides.
        // Clay minerals and hydrothermal vents catalyze these reactions.
        // Multiple reaction attempts per tick represent the vast number of
        // concurrent reaction sites in Earth's early oceans and
        // hydrothermal vents.
        for _ in 0..10 {
            self.chemical_system.catalyzed_reaction(
                &mut self.atomic_system.atoms,
                self.environment.temperature,
                true, // clay minerals catalyse
            );
        }

        // Try abiogenesis
        self.biological_system.abiogenesis(&self.chemical_system);

        // Evolve life
        self.biological_system.tick(
            self.environment.temperature,
            self.environment.resources,
            self.environment.radiation_level,
        );
    }

    fn step_dna(&mut self) {
        // DNA-based life, more complex evolution
        self.environment.tick(self.biological_system.population.len());

        for _ in 0..3 {
            self.chemical_system.catalyzed_reaction(
                &mut self.atomic_system.atoms,
                self.environment.temperature,
                true,
            );
        }

        self.biological_system.abiogenesis(&self.chemical_system);
        self.biological_system.tick(
            self.environment.temperature,
            self.environment.resources,
            self.environment.radiation_level,
        );
    }

    fn step_present(&mut self) {
        // Complex life, intelligence
        self.environment.tick(self.biological_system.population.len());

        self.biological_system.tick(
            self.environment.temperature,
            self.environment.resources,
            self.environment.radiation_level,
        );
    }

    /// Snapshot of the current state.
    pub fn stats(&self) -> SimStats {
        let epoch = current_epoch(self.tick);
        SimStats {
            tick: self.tick,
            epoch_name: epoch.name.to_string(),
            epoch_description: epoch.description.to_string(),
            temperature: self.quantum_field.temperature,
            total_energy: self.quantum_field.total_energy(),
            particle_count: self.quantum_field.particles.len(),
            atom_count: self.atomic_system.atoms.len(),
            molecule_count: self.chemical_system.molecules.len(),
            water_count: self.chemical_system.water_count,
            amino_acid_count: self.chemical_system.amino_acid_count,
            nucleotide_count: self.chemical_system.nucleotide_count,
            population: self.biological_system.population.len(),
            generation: self.biological_system.generation,
            average_fitness: self.biological_system.average_fitness(),
            species_count: self.biological_system.species_count(),
            is_habitable: self.environment.is_habitable(),
            oxygen_pct: self.environment.atmosphere.oxygen * 100.0,
        }
    }

    /// Run the full simulation from Big Bang to Present.
    /// Calls `on_epoch` whenever a new epoch starts,
    /// and `on_tick` periodically for progress.
    pub fn run<F, G>(&mut self, mut on_epoch: F, mut on_tick: G)
    where
        F: FnMut(&SimStats),
        G: FnMut(&SimStats),
    {
        // Report initial state
        on_epoch(&self.stats());

        let report_interval = 5000;
        while self.tick < PRESENT_EPOCH {
            let new_epoch = self.step();
            if new_epoch {
                on_epoch(&self.stats());
            } else if self.tick % report_interval == 0 {
                on_tick(&self.stats());
            }
        }

        // Final report
        on_epoch(&self.stats());
    }
}
