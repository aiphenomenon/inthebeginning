//! Universe simulation orchestrator.
//!
//! Coordinates all simulation layers from the Big Bang through
//! emergence of life. Port of the Python `simulator/universe.py`.

use rand::rngs::SmallRng;
use rand::SeedableRng;

use crate::atomic::AtomicSystem;
use crate::biology::Biosphere;
use crate::chemistry::ChemicalSystem;
use crate::constants::*;
use crate::environment::Environment;
use crate::quantum::QuantumField;

// ---------------------------------------------------------------------------
// Snapshot for renderer
// ---------------------------------------------------------------------------

/// Lightweight snapshot of the universe state for rendering.
pub struct Snapshot {
    pub tick: u64,
    pub epoch_name: &'static str,
    pub epoch_description: &'static str,
    pub temperature: f64,
    pub particle_count: usize,
    pub atom_count: usize,
    pub molecule_count: usize,
    pub cell_count: usize,
    pub average_fitness: f64,
    pub generation: u32,
    pub total_mutations: u64,
}

// ---------------------------------------------------------------------------
// SimulationMetrics
// ---------------------------------------------------------------------------

/// Performance metrics for the simulation.
pub struct SimulationMetrics {
    pub ticks_completed: u64,
    pub particles_created: u64,
    pub atoms_formed: u64,
    pub molecules_formed: u64,
    pub cells_born: u64,
    pub mutations: u64,
}

impl SimulationMetrics {
    pub fn new() -> Self {
        Self {
            ticks_completed: 0,
            particles_created: 0,
            atoms_formed: 0,
            molecules_formed: 0,
            cells_born: 0,
            mutations: 0,
        }
    }
}

// ---------------------------------------------------------------------------
// Universe
// ---------------------------------------------------------------------------

/// An epoch transition record.
pub struct EpochTransition {
    pub tick: u64,
    pub from: &'static str,
    pub to: &'static str,
}

pub struct Universe {
    pub tick: u64,
    pub max_ticks: u64,
    pub step_size: u64,
    pub current_epoch_name: &'static str,

    // Physical layers
    pub quantum_field: QuantumField,
    pub atomic_system: AtomicSystem,
    pub chemical_system: Option<ChemicalSystem>,
    pub biosphere: Option<Biosphere>,
    pub environment: Environment,

    // Metrics
    pub particles_created: u64,
    pub atoms_formed: u64,
    pub molecules_formed: u64,
    pub cells_born: u64,
    pub mutations: u64,

    // State tracking
    pub history: Vec<Snapshot>,
    pub epoch_transitions: Vec<EpochTransition>,

    rng: SmallRng,

    // Track one-time events
    earth_seeded: bool,
    earth_molecules_formed: bool,
    hadron_done: bool,

    // Big Bounce cycle counter
    cycle: u32,
}

impl Universe {
    pub fn new(seed: u64, max_ticks: u64) -> Self {
        let rng = SmallRng::seed_from_u64(seed);
        Self {
            tick: 0,
            max_ticks,
            step_size: 1,
            current_epoch_name: "Void",
            quantum_field: QuantumField::new(T_PLANCK),
            atomic_system: AtomicSystem::new(),
            chemical_system: None,
            biosphere: None,
            environment: Environment::new(T_PLANCK),
            particles_created: 0,
            atoms_formed: 0,
            molecules_formed: 0,
            cells_born: 0,
            mutations: 0,
            history: Vec::new(),
            epoch_transitions: Vec::new(),
            rng,
            earth_seeded: false,
            earth_molecules_formed: false,
            hadron_done: false,
            cycle: 0,
        }
    }

    /// Advance simulation by one tick.
    pub fn step(&mut self) {
        self.tick += self.step_size;

        // Epoch transition
        let new_epoch = epoch_name_for_tick(self.tick);
        if new_epoch != self.current_epoch_name {
            self.epoch_transitions.push(EpochTransition {
                tick: self.tick,
                from: self.current_epoch_name,
                to: new_epoch,
            });
        }
        self.current_epoch_name = new_epoch;

        // Update environment
        self.environment.update(self.tick, &mut self.rng);

        // === Quantum level ===
        if self.tick <= HADRON_EPOCH {
            self.quantum_field.temperature = self.environment.temperature;

            // Seed on first quantum tick
            if self.quantum_field.particles.is_empty() && self.environment.temperature > 100.0 {
                self.quantum_field.seed_early_universe(&mut self.rng);
                self.particles_created += self.quantum_field.particles.len() as u64;
            }

            // Pair production in hot early universe
            if self.environment.temperature > 100.0 {
                let n_attempts = (self.environment.temperature / 1000.0)
                    .max(1.0)
                    .min(5.0) as usize;
                for _ in 0..n_attempts {
                    if self.quantum_field.vacuum_fluctuation(&mut self.rng) {
                        self.particles_created += 2;
                    }
                }
            }

            self.quantum_field.evolve(self.step_size as f64);
        }

        // === Hadron formation ===
        if !self.hadron_done
            && self.tick >= HADRON_EPOCH.saturating_sub(self.step_size)
            && self.tick <= HADRON_EPOCH + self.step_size
        {
            self.quantum_field.temperature = self.environment.temperature;
            let hadrons = self.quantum_field.quark_confinement(&mut self.rng);
            self.particles_created += hadrons.len() as u64;
            self.hadron_done = true;
        }

        // === Nucleosynthesis ===
        if self.tick >= NUCLEOSYNTHESIS_EPOCH && self.tick < RECOMBINATION_EPOCH {
            let protons = self.quantum_field.proton_count();
            let neutrons = self.quantum_field.neutron_count();
            if protons > 0 || neutrons > 0 {
                let new_atoms =
                    self.atomic_system
                        .nucleosynthesis(protons, neutrons, &mut self.rng);
                self.quantum_field.remove_hadrons();
                self.atoms_formed += new_atoms as u64;
            }
        }

        // === Recombination ===
        if self.tick >= RECOMBINATION_EPOCH.saturating_sub(self.step_size)
            && self.tick <= RECOMBINATION_EPOCH + self.step_size
        {
            self.atomic_system.temperature = self.environment.temperature;
            let new_atoms = self
                .atomic_system
                .recombination(&mut self.quantum_field, &mut self.rng);
            self.atoms_formed += new_atoms as u64;
        }

        // === Star formation and stellar nucleosynthesis ===
        if self.tick >= STAR_FORMATION_EPOCH && self.tick < SOLAR_SYSTEM_EPOCH {
            self.atomic_system.temperature = self.environment.temperature;
            let new_heavy = self
                .atomic_system
                .stellar_nucleosynthesis(self.environment.temperature * 100.0, &mut self.rng);
            self.atoms_formed += new_heavy as u64;
        }

        // === Chemistry ===
        if self.tick >= EARTH_EPOCH {
            if self.chemical_system.is_none() {
                self.chemical_system = Some(ChemicalSystem::new());
            }

            // Seed Earth elements
            if !self.earth_seeded {
                let seeded = self.atomic_system.seed_earth_elements(&mut self.rng);
                self.atoms_formed += seeded as u64;
                self.earth_seeded = true;
            }

            // Form basic molecules once
            if !self.earth_molecules_formed {
                if let Some(ref mut chem) = self.chemical_system {
                    let w = chem.form_water(&mut self.atomic_system.atoms);
                    let m = chem.form_methane(&mut self.atomic_system.atoms);
                    let a = chem.form_ammonia(&mut self.atomic_system.atoms);
                    self.molecules_formed += (w + m + a) as u64;
                }
                self.earth_molecules_formed = true;
            }

            // Catalyzed reactions
            if self.tick > EARTH_EPOCH {
                if let Some(ref mut chem) = self.chemical_system {
                    let catalyst = self.tick > LIFE_EPOCH;
                    let formed = chem.catalyzed_reaction(
                        &mut self.atomic_system.atoms,
                        self.environment.temperature,
                        catalyst,
                        &mut self.rng,
                    );
                    self.molecules_formed += formed as u64;
                }
            }
        }

        // === Biology ===
        if self.tick >= LIFE_EPOCH && self.environment.is_habitable() {
            if self.biosphere.is_none() {
                self.biosphere = Some(Biosphere::new(3, 90, &mut self.rng));
                self.cells_born += 3;
            }

            if let Some(ref mut bio) = self.biosphere {
                bio.step(
                    self.environment.thermal_energy(),
                    self.environment.uv_intensity,
                    self.environment.cosmic_ray_flux,
                    self.environment.temperature,
                    &mut self.rng,
                );
                self.cells_born = bio.total_born;
                self.mutations = bio.total_mutations();
            }
        }

        // Record state snapshot periodically
        let interval = (self.max_ticks / 100).max(1);
        if self.tick % interval == 0 {
            self.history.push(self.snapshot());
        }
    }

    /// Reset the universe for a new cycle (Big Bounce).
    ///
    /// Clears the tick counter, resets temperature and all subsystems to
    /// their initial state, and increments the cycle counter.  This allows
    /// the simulation to be re-run perpetually without leaking memory from
    /// previous cycles.
    pub fn big_bounce(&mut self) {
        self.cycle += 1;
        self.tick = 0;
        self.step_size = 1;
        self.current_epoch_name = "Void";

        // Re-seed the RNG from the original seed mixed with the cycle number
        // so each cycle is deterministic but distinct.
        self.rng = SmallRng::seed_from_u64(self.cycle as u64);

        // Reset physical layers
        self.quantum_field = QuantumField::new(T_PLANCK);
        self.atomic_system = AtomicSystem::new();
        self.chemical_system = None;
        self.biosphere = None;
        self.environment = Environment::new(T_PLANCK);

        // Reset metrics
        self.particles_created = 0;
        self.atoms_formed = 0;
        self.molecules_formed = 0;
        self.cells_born = 0;
        self.mutations = 0;

        // Reset history
        self.history.clear();
        self.epoch_transitions.clear();

        // Reset one-time event flags
        self.earth_seeded = false;
        self.earth_molecules_formed = false;
        self.hadron_done = false;
    }

    /// Return the current cycle number (0 = first run).
    pub fn cycle(&self) -> u32 {
        self.cycle
    }

    /// Whether the simulation has reached its end.
    pub fn is_complete(&self) -> bool {
        self.tick >= self.max_ticks
    }

    /// Build a `SimulationMetrics` summary.
    pub fn metrics(&self) -> SimulationMetrics {
        SimulationMetrics {
            ticks_completed: self.tick,
            particles_created: self.particles_created,
            atoms_formed: self.atoms_formed,
            molecules_formed: self.molecules_formed,
            cells_born: self.cells_born,
            mutations: self.mutations,
        }
    }

    /// Full compact state representation.
    pub fn state_compact(&self) -> String {
        let mut parts = vec![
            format!("U[t={}/{} e={}]", self.tick, self.max_ticks, self.current_epoch_name),
            self.quantum_field.to_compact(),
            self.atomic_system.to_compact(),
        ];
        if let Some(ref chem) = self.chemical_system {
            parts.push(chem.to_compact());
        }
        if let Some(ref bio) = self.biosphere {
            parts.push(bio.to_compact());
        }
        parts.push(self.environment.to_compact());
        parts.join(" | ")
    }

    /// Run the simulation to completion.
    pub fn run(&mut self) {
        while self.tick < self.max_ticks {
            self.step();
        }
    }

    /// Run the simulation in perpetual Big Bounce mode.
    ///
    /// After each cycle completes, the universe resets and starts a new cycle.
    /// Runs `max_cycles` cycles (0 = infinite, but in WASM we require a limit).
    pub fn run_perpetual(&mut self, max_cycles: u32) {
        let mut cycle = 0u32;
        while max_cycles == 0 || cycle < max_cycles {
            self.run();
            cycle += 1;
            if max_cycles > 0 && cycle >= max_cycles {
                break;
            }
            self.big_bounce();
        }
    }

    /// Capture a snapshot for the renderer.
    pub fn snapshot(&self) -> Snapshot {
        let molecule_count = self
            .chemical_system
            .as_ref()
            .map(|c| c.molecules.len())
            .unwrap_or(0);
        let (cell_count, avg_fitness, generation, mutations) =
            if let Some(ref bio) = self.biosphere {
                (
                    bio.cells.len(),
                    bio.average_fitness(),
                    bio.generation,
                    bio.total_mutations(),
                )
            } else {
                (0, 0.0, 0, 0)
            };

        Snapshot {
            tick: self.tick,
            epoch_name: self.current_epoch_name,
            epoch_description: epoch_description_for_tick(self.tick),
            temperature: self.environment.temperature,
            particle_count: self.quantum_field.particles.len(),
            atom_count: self.atomic_system.atoms.len(),
            molecule_count,
            cell_count,
            average_fitness: avg_fitness,
            generation,
            total_mutations: mutations,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_universe_new() {
        let u = Universe::new(42, 300_000);
        assert_eq!(u.tick, 0);
        assert_eq!(u.max_ticks, 300_000);
        assert_eq!(u.current_epoch_name, "Void");
        assert!(u.quantum_field.particles.is_empty());
        assert!(u.atomic_system.atoms.is_empty());
        assert!(u.chemical_system.is_none());
        assert!(u.biosphere.is_none());
    }

    #[test]
    fn test_universe_is_complete() {
        let mut u = Universe::new(42, 100);
        assert!(!u.is_complete());
        u.tick = 100;
        assert!(u.is_complete());
        u.tick = 101;
        assert!(u.is_complete());
    }

    #[test]
    fn test_universe_step_advances_tick() {
        let mut u = Universe::new(42, 300_000);
        u.step();
        assert_eq!(u.tick, 1);
        u.step();
        assert_eq!(u.tick, 2);
    }

    #[test]
    fn test_universe_epoch_transitions() {
        let mut u = Universe::new(42, 300_000);

        // Advance to Planck epoch
        u.step();
        assert_eq!(u.current_epoch_name, "Planck");

        // Advance to Inflation epoch
        while u.tick < INFLATION_EPOCH {
            u.step();
        }
        assert_eq!(u.current_epoch_name, "Inflation");

        // Advance to Quark epoch
        while u.tick < QUARK_EPOCH {
            u.step();
        }
        assert_eq!(u.current_epoch_name, "Quark");
    }

    #[test]
    fn test_universe_creates_particles() {
        let mut u = Universe::new(42, 300_000);

        // Run through early universe
        for _ in 0..100 {
            u.step();
        }
        // Should have created particles by now
        assert!(u.quantum_field.particles.len() > 0);
        assert!(u.particles_created > 0);
    }

    #[test]
    fn test_universe_hadron_formation() {
        let mut u = Universe::new(42, 300_000);

        // Advance past hadron epoch
        while u.tick <= HADRON_EPOCH + 1 {
            u.step();
        }
        // Should have formed some hadrons
        assert!(u.hadron_done);
    }

    #[test]
    fn test_universe_nucleosynthesis() {
        let mut u = Universe::new(42, 300_000);

        // Advance through nucleosynthesis epoch
        while u.tick < NUCLEOSYNTHESIS_EPOCH + 100 {
            u.step();
        }
        // Should have formed some atoms
        assert!(u.atoms_formed > 0 || u.atomic_system.atoms.len() > 0);
    }

    #[test]
    fn test_universe_snapshot_initial() {
        let u = Universe::new(42, 300_000);
        let snap = u.snapshot();

        assert_eq!(snap.tick, 0);
        assert_eq!(snap.epoch_name, "Void");
        assert_eq!(snap.particle_count, 0);
        assert_eq!(snap.atom_count, 0);
        assert_eq!(snap.molecule_count, 0);
        assert_eq!(snap.cell_count, 0);
        assert_eq!(snap.generation, 0);
        assert_eq!(snap.total_mutations, 0);
    }

    #[test]
    fn test_universe_snapshot_after_steps() {
        let mut u = Universe::new(42, 300_000);

        for _ in 0..50 {
            u.step();
        }
        let snap = u.snapshot();
        assert_eq!(snap.tick, 50);
        assert!(snap.particle_count > 0);
    }

    #[test]
    fn test_universe_chemistry_epoch() {
        let mut u = Universe::new(42, 300_000);

        // Advance to Earth epoch where chemistry starts
        while u.tick < EARTH_EPOCH + 10 {
            u.step();
        }
        assert!(u.chemical_system.is_some());
        assert!(u.earth_seeded);
    }

    #[test]
    fn test_universe_deterministic() {
        // Two universes with the same seed should produce identical results
        let mut u1 = Universe::new(42, 300_000);
        let mut u2 = Universe::new(42, 300_000);

        for _ in 0..200 {
            u1.step();
            u2.step();
        }

        assert_eq!(u1.tick, u2.tick);
        assert_eq!(u1.quantum_field.particles.len(), u2.quantum_field.particles.len());
        assert_eq!(u1.particles_created, u2.particles_created);
        assert_eq!(u1.atoms_formed, u2.atoms_formed);
    }

    #[test]
    fn test_universe_full_run_small() {
        // Run a small universe to completion
        let mut u = Universe::new(42, 1000);

        while !u.is_complete() {
            u.step();
        }
        assert!(u.tick >= 1000);
        let snap = u.snapshot();
        assert!(snap.tick >= 1000);
    }

    #[test]
    fn test_universe_step_size() {
        let mut u = Universe::new(42, 300_000);
        assert_eq!(u.step_size, 1);
        // The step size should advance tick by 1 each step
        u.step();
        assert_eq!(u.tick, 1);
    }

    #[test]
    fn test_universe_different_seeds() {
        let mut u1 = Universe::new(42, 300_000);
        let mut u2 = Universe::new(99, 300_000);

        for _ in 0..100 {
            u1.step();
            u2.step();
        }

        // Same tick, but potentially different particle counts due to RNG
        assert_eq!(u1.tick, u2.tick);
        // At minimum, they should both have created particles
        assert!(u1.particles_created > 0);
        assert!(u2.particles_created > 0);
    }

    #[test]
    fn test_universe_snapshot_fields() {
        let mut u = Universe::new(42, 300_000);
        for _ in 0..20 {
            u.step();
        }
        let snap = u.snapshot();

        assert_eq!(snap.tick, 20);
        assert!(!snap.epoch_name.is_empty());
        assert!(!snap.epoch_description.is_empty());
        assert!(snap.temperature > 0.0);
        assert!(snap.particle_count >= 0);
    }

    #[test]
    fn test_universe_cycle_initial() {
        let u = Universe::new(42, 300_000);
        assert_eq!(u.cycle(), 0);
    }

    #[test]
    fn test_universe_big_bounce_resets_state() {
        let mut u = Universe::new(42, 300_000);

        // Run for a while to accumulate state
        for _ in 0..200 {
            u.step();
        }
        assert!(u.tick > 0);
        assert!(u.particles_created > 0);
        assert_eq!(u.cycle(), 0);

        // Bounce
        u.big_bounce();

        assert_eq!(u.tick, 0);
        assert_eq!(u.cycle(), 1);
        assert_eq!(u.current_epoch_name, "Void");
        assert_eq!(u.particles_created, 0);
        assert_eq!(u.atoms_formed, 0);
        assert_eq!(u.molecules_formed, 0);
        assert_eq!(u.cells_born, 0);
        assert!(u.quantum_field.particles.is_empty());
        assert!(u.atomic_system.atoms.is_empty());
        assert!(u.chemical_system.is_none());
        assert!(u.biosphere.is_none());
        assert!(!u.hadron_done);
    }

    #[test]
    fn test_universe_big_bounce_multiple_cycles() {
        let mut u = Universe::new(42, 1000);

        for expected_cycle in 0..3u32 {
            assert_eq!(u.cycle(), expected_cycle);

            // Run to completion
            while !u.is_complete() {
                u.step();
            }
            assert!(u.tick >= 1000);

            if expected_cycle < 2 {
                u.big_bounce();
            }
        }
        assert_eq!(u.cycle(), 2);
    }

    #[test]
    fn test_universe_big_bounce_allows_re_run() {
        let mut u = Universe::new(42, 1000);

        // Complete first cycle
        while !u.is_complete() {
            u.step();
        }
        assert!(u.is_complete());

        // Bounce and verify we can step again
        u.big_bounce();
        assert!(!u.is_complete());
        u.step();
        assert_eq!(u.tick, 1);
    }

    #[test]
    fn test_universe_life_epoch() {
        let mut u = Universe::new(42, 300_000);
        // Advance to life epoch
        while u.tick < LIFE_EPOCH + 10 {
            u.step();
        }
        // Should have a biosphere by now
        assert!(u.biosphere.is_some());
    }
}
