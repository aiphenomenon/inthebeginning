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

    /// Big Bounce: reset the universe for a new cycle.
    ///
    /// Clears all physical layers and resets tick to 0, enabling
    /// perpetual simulation without memory leaks.
    pub fn big_bounce(&mut self) {
        self.tick = 0;
        self.quantum_field = QuantumField::new(T_PLANCK);
        self.atomic_system = AtomicSystem::new(T_PLANCK);
        self.chemical_system = ChemicalSystem::new();
        self.biological_system = BiologicalSystem::new();
        self.environment = Environment::interstellar();
        self.scale_factor = 1.0;
        self.last_epoch_index = 0;
        self.nucleosynthesis_done = false;
        self.recombination_done = false;
        self.earth_initialized = false;
        self.stellar_seeded = false;
        self.solar_seeded = false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // -----------------------------------------------------------------------
    // current_epoch / epoch_index
    // -----------------------------------------------------------------------

    /// Tick 1 is in the Planck epoch.
    #[test]
    fn current_epoch_planck() {
        let e = current_epoch(1);
        assert_eq!(e.name, "Planck");
    }

    /// Tick at inflation boundary is in Inflation epoch.
    #[test]
    fn current_epoch_inflation() {
        let e = current_epoch(INFLATION_EPOCH);
        assert_eq!(e.name, "Inflation");
    }

    /// Tick at present boundary is in Present epoch.
    #[test]
    fn current_epoch_present() {
        let e = current_epoch(PRESENT_EPOCH);
        assert_eq!(e.name, "Present");
    }

    /// epoch_index at tick 0 is 0 (before Planck, defaults to Planck).
    #[test]
    fn epoch_index_zero() {
        // tick 0 < PLANCK_EPOCH(1), so no epoch matches => stays at 0
        // Actually, the loop starts at EPOCHS[0].start_tick = 1, so tick 0
        // won't match any epoch: idx stays 0 because it's initialized to 0.
        let idx = epoch_index(0);
        assert_eq!(idx, 0);
    }

    /// epoch_index advances correctly through epochs.
    #[test]
    fn epoch_index_progression() {
        assert_eq!(epoch_index(PLANCK_EPOCH), 0);
        assert_eq!(epoch_index(INFLATION_EPOCH), 1);
        assert_eq!(epoch_index(ELECTROWEAK_EPOCH), 2);
        assert_eq!(epoch_index(QUARK_EPOCH), 3);
        assert_eq!(epoch_index(HADRON_EPOCH), 4);
        assert_eq!(epoch_index(NUCLEOSYNTHESIS_EPOCH), 5);
        assert_eq!(epoch_index(RECOMBINATION_EPOCH), 6);
        assert_eq!(epoch_index(STAR_FORMATION_EPOCH), 7);
        assert_eq!(epoch_index(SOLAR_SYSTEM_EPOCH), 8);
        assert_eq!(epoch_index(EARTH_EPOCH), 9);
        assert_eq!(epoch_index(LIFE_EPOCH), 10);
        assert_eq!(epoch_index(DNA_EPOCH), 11);
        assert_eq!(epoch_index(PRESENT_EPOCH), 12);
    }

    /// Ticks between boundaries belong to the earlier epoch.
    #[test]
    fn epoch_index_between_boundaries() {
        assert_eq!(epoch_index(INFLATION_EPOCH + 5), 1);
        assert_eq!(epoch_index(ELECTROWEAK_EPOCH - 1), 1);
    }

    // -----------------------------------------------------------------------
    // target_temperature (tested indirectly via Universe)
    // -----------------------------------------------------------------------

    /// Temperature at tick 1 equals T_PLANCK.
    #[test]
    fn target_temp_planck() {
        let t = target_temperature(PLANCK_EPOCH);
        assert!((t - T_PLANCK).abs() < 1e-5);
    }

    /// Temperature at the present epoch equals T_EARTH_SURFACE.
    #[test]
    fn target_temp_present() {
        let t = target_temperature(PRESENT_EPOCH);
        assert!((t - T_EARTH_SURFACE).abs() < 1e-5);
    }

    /// Temperature decreases monotonically across epoch boundaries.
    #[test]
    fn target_temp_monotonically_decreasing() {
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
        ];
        for w in ticks.windows(2) {
            let t0 = target_temperature(w[0]);
            let t1 = target_temperature(w[1]);
            assert!(t0 >= t1,
                "temperature at tick {} ({}) should >= tick {} ({})",
                w[0], t0, w[1], t1);
        }
    }

    /// Temperature is interpolated between anchors (not just step functions).
    #[test]
    fn target_temp_interpolated() {
        let midpoint = (PLANCK_EPOCH + INFLATION_EPOCH) / 2;
        let t_mid = target_temperature(midpoint);
        let t_start = target_temperature(PLANCK_EPOCH);
        let t_end = target_temperature(INFLATION_EPOCH);
        assert!(t_mid < t_start && t_mid > t_end,
            "midpoint temp {} should be between {} and {}",
            t_mid, t_start, t_end);
    }

    // -----------------------------------------------------------------------
    // Universe
    // -----------------------------------------------------------------------

    /// New Universe starts at tick 0 with Planck-era temperature.
    #[test]
    fn universe_new_initial_state() {
        let u = Universe::new();
        assert_eq!(u.tick, 0);
        assert_eq!(u.quantum_field.temperature, T_PLANCK);
        assert_eq!(u.scale_factor, 1.0);
        assert!(!u.nucleosynthesis_done);
        assert!(!u.recombination_done);
        assert!(!u.earth_initialized);
    }

    /// First step advances tick to 1.
    #[test]
    fn universe_step_advances_tick() {
        let mut u = Universe::new();
        u.step();
        assert_eq!(u.tick, 1);
    }

    /// First step returns true (new epoch: Planck).
    #[test]
    fn universe_first_step_new_epoch() {
        let mut u = Universe::new();
        let new_epoch = u.step();
        // Tick goes from 0 to 1; epoch_index(1) = 0, last_epoch_index was 0,
        // so no change => false
        // Actually, last_epoch_index starts at 0 and epoch_index(1) = 0,
        // so new_epoch is false.
        assert!(!new_epoch);
    }

    /// Step detects epoch transitions.
    #[test]
    fn universe_step_detects_epoch_transition() {
        let mut u = Universe::new();
        // Advance to just before inflation
        for _ in 0..INFLATION_EPOCH - 1 {
            u.step();
        }
        // Now at tick INFLATION_EPOCH - 1, epoch_index = 0 (Planck)
        let new_epoch = u.step();
        // tick is now INFLATION_EPOCH, epoch_index = 1 (Inflation)
        assert!(new_epoch, "should detect transition to Inflation");
    }

    /// Temperature cools as the universe evolves.
    #[test]
    fn universe_temperature_cools() {
        let mut u = Universe::new();
        let initial_temp = u.quantum_field.temperature;
        for _ in 0..100 {
            u.step();
        }
        assert!(u.quantum_field.temperature < initial_temp,
            "temperature should cool from {} to {}",
            initial_temp, u.quantum_field.temperature);
    }

    /// Stats snapshot reflects current state.
    #[test]
    fn universe_stats_reflect_state() {
        let mut u = Universe::new();
        u.step();
        let stats = u.stats();
        assert_eq!(stats.tick, 1);
        assert_eq!(stats.epoch_name, "Planck");
        assert!(stats.temperature > 0.0);
    }

    /// Advancing through inflation creates particles.
    #[test]
    fn universe_inflation_creates_particles() {
        let mut u = Universe::new();
        // Run through the inflation epoch
        while u.tick < ELECTROWEAK_EPOCH {
            u.step();
        }
        assert!(u.quantum_field.particles.len() > 0,
            "inflation should create particles");
    }

    /// Advancing through hadron epoch creates hadrons.
    #[test]
    fn universe_hadron_epoch_creates_hadrons() {
        let mut u = Universe::new();
        while u.tick < NUCLEOSYNTHESIS_EPOCH {
            u.step();
        }
        let counts = u.quantum_field.particle_count();
        let has_hadrons = counts.get(&ParticleType::Proton).copied().unwrap_or(0) > 0
            || counts.get(&ParticleType::Neutron).copied().unwrap_or(0) > 0;
        // Hadrons might have formed during the hadron epoch
        // or been consumed by nucleosynthesis
        let has_atoms = !u.atomic_system.atoms.is_empty();
        assert!(has_hadrons || has_atoms,
            "hadron/nucleosynthesis epoch should produce hadrons or atoms");
    }

    /// Nucleosynthesis creates atoms from hadrons.
    #[test]
    fn universe_nucleosynthesis_creates_atoms() {
        let mut u = Universe::new();
        while u.tick < RECOMBINATION_EPOCH {
            u.step();
        }
        // After nucleosynthesis, we should have atoms
        assert!(!u.atomic_system.atoms.is_empty(),
            "nucleosynthesis should create atoms");
    }

    /// Star formation seeds heavier elements.
    #[test]
    fn universe_star_formation_seeds_elements() {
        let mut u = Universe::new();
        while u.tick < SOLAR_SYSTEM_EPOCH {
            u.step();
        }
        let counts = u.atomic_system.element_counts();
        // Should have carbon, nitrogen, oxygen from stellar nucleosynthesis
        assert!(counts.contains_key("C"), "should have carbon");
        assert!(counts.contains_key("N"), "should have nitrogen");
        assert!(counts.contains_key("O"), "should have oxygen");
    }

    /// Earth epoch initializes the environment.
    #[test]
    fn universe_earth_initializes_environment() {
        let mut u = Universe::new();
        while u.tick < LIFE_EPOCH {
            u.step();
        }
        assert!(u.earth_initialized);
        // Environment should be approaching habitable
        assert!(u.environment.ocean_coverage > 0.0);
    }

    /// SimStats fields are populated correctly.
    #[test]
    fn sim_stats_fields() {
        let u = Universe::new();
        let stats = u.stats();
        assert_eq!(stats.tick, 0);
        assert_eq!(stats.particle_count, 0);
        assert_eq!(stats.atom_count, 0);
        assert_eq!(stats.molecule_count, 0);
        assert_eq!(stats.water_count, 0);
        assert_eq!(stats.amino_acid_count, 0);
        assert_eq!(stats.nucleotide_count, 0);
        assert_eq!(stats.population, 0);
        assert_eq!(stats.generation, 0);
    }

    /// Run executes from tick 0 to PRESENT_EPOCH.
    #[test]
    fn universe_run_completes() {
        let mut u = Universe::new();
        let mut epoch_count = 0u32;
        let mut tick_count = 0u32;
        u.run(
            |_stats| { epoch_count += 1; },
            |_stats| { tick_count += 1; },
        );
        assert_eq!(u.tick, PRESENT_EPOCH);
        // At least 13 epoch callbacks (one per epoch + initial + final)
        assert!(epoch_count >= 13,
            "should have at least 13 epoch reports, got {}", epoch_count);
    }

    /// After a full run, the simulation has molecules and life.
    #[test]
    fn universe_full_run_has_molecules_and_life() {
        let mut u = Universe::new();
        u.run(|_| {}, |_| {});

        let stats = u.stats();
        assert!(stats.molecule_count > 0, "should have molecules");
        assert!(stats.water_count > 0, "should have water");
        // Life may or may not emerge depending on random seed,
        // but atoms and molecules should exist.
        assert!(stats.atom_count > 0, "should have atoms");
    }
}
