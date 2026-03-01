//! Universe simulation orchestrator.
//!
//! Coordinates all simulation layers from the Big Bang through
//! emergence of life. Port of the Python `simulator/universe.py`.

use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};

use crate::atomic::AtomicSystem;
use crate::biology::Biosphere;
use crate::chemistry::ChemicalSystem;
use crate::constants::*;
use crate::environment::Environment;
use crate::quantum::{ParticleType, QuantumField};

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
// Universe
// ---------------------------------------------------------------------------

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

    rng: SmallRng,

    // Track one-time events
    earth_seeded: bool,
    earth_molecules_formed: bool,
    hadron_done: bool,
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
            rng,
            earth_seeded: false,
            earth_molecules_formed: false,
            hadron_done: false,
        }
    }

    /// Advance simulation by one tick.
    pub fn step(&mut self) {
        self.tick += self.step_size;

        // Epoch transition
        let new_epoch = epoch_name_for_tick(self.tick);
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
                self.biosphere = Some(Biosphere::new(3, &mut self.rng));
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
            }
        }
    }

    /// Whether the simulation has reached its end.
    pub fn is_complete(&self) -> bool {
        self.tick >= self.max_ticks
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
