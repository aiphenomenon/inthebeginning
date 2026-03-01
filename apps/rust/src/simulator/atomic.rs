//! Atomic physics simulation.
//!
//! Models atoms with electron shells, ionization, chemical bonding potential,
//! and the periodic table. Atoms emerge from the quantum/nuclear level
//! when temperature drops below the recombination threshold.

use rand::Rng;
use std::sync::atomic::{AtomicU64, Ordering};

use super::constants::*;
use super::quantum::{Particle, QuantumField};

static ATOM_ID_COUNTER: AtomicU64 = AtomicU64::new(0);

fn next_atom_id() -> u64 {
    ATOM_ID_COUNTER.fetch_add(1, Ordering::Relaxed) + 1
}

// ---------------------------------------------------------------------------
// ElectronShell
// ---------------------------------------------------------------------------

/// An electron shell with quantum numbers.
#[derive(Debug, Clone)]
pub struct ElectronShell {
    /// Principal quantum number
    pub n: u32,
    /// Maximum electrons (from ELECTRON_SHELLS table)
    pub max_electrons: u32,
    /// Current electron count
    pub electrons: u32,
}

impl ElectronShell {
    pub fn full(&self) -> bool {
        self.electrons >= self.max_electrons
    }

    pub fn empty(&self) -> bool {
        self.electrons == 0
    }

    pub fn add_electron(&mut self) -> bool {
        if !self.full() {
            self.electrons += 1;
            true
        } else {
            false
        }
    }

    pub fn remove_electron(&mut self) -> bool {
        if !self.empty() {
            self.electrons -= 1;
            true
        } else {
            false
        }
    }
}

// ---------------------------------------------------------------------------
// Atom
// ---------------------------------------------------------------------------

/// An atom with protons, neutrons, and electron shells.
#[derive(Debug, Clone)]
pub struct Atom {
    /// Number of protons
    pub atomic_number: u32,
    /// Protons + neutrons
    pub mass_number: u32,
    pub electron_count: u32,
    pub position: [f64; 3],
    pub velocity: [f64; 3],
    pub shells: Vec<ElectronShell>,
    /// IDs of bonded atoms
    pub bonds: Vec<u64>,
    pub atom_id: u64,
    pub ionization_energy: f64,
}

impl Atom {
    pub fn new(atomic_number: u32) -> Self {
        let mut atom = Self {
            atomic_number,
            mass_number: if atomic_number == 1 { 1 } else { atomic_number * 2 },
            electron_count: atomic_number,
            position: [0.0; 3],
            velocity: [0.0; 3],
            shells: Vec::new(),
            bonds: Vec::new(),
            atom_id: next_atom_id(),
            ionization_energy: 0.0,
        };
        atom.build_shells();
        atom.compute_ionization_energy();
        atom
    }

    pub fn with_mass_number(mut self, mn: u32) -> Self {
        self.mass_number = mn;
        self
    }

    pub fn with_position(mut self, pos: [f64; 3]) -> Self {
        self.position = pos;
        self
    }

    pub fn with_velocity(mut self, vel: [f64; 3]) -> Self {
        self.velocity = vel;
        self
    }

    fn build_shells(&mut self) {
        self.shells.clear();
        let mut remaining = self.electron_count as i32;
        for (i, &max_e) in ELECTRON_SHELLS.iter().enumerate() {
            if remaining <= 0 {
                break;
            }
            let electrons = (remaining as u32).min(max_e);
            self.shells.push(ElectronShell {
                n: (i + 1) as u32,
                max_electrons: max_e,
                electrons,
            });
            remaining -= electrons as i32;
        }
    }

    fn compute_ionization_energy(&mut self) {
        if self.shells.is_empty() || self.shells.last().unwrap().empty() {
            self.ionization_energy = 0.0;
            return;
        }
        let n = self.shells.last().unwrap().n as f64;
        let inner_electrons: u32 = if self.shells.len() > 1 {
            self.shells[..self.shells.len() - 1]
                .iter()
                .map(|s| s.electrons)
                .sum()
        } else {
            0
        };
        let z_eff = self.atomic_number as f64 - inner_electrons as f64;
        self.ionization_energy = 13.6 * z_eff * z_eff / (n * n);
    }

    pub fn symbol(&self) -> &'static str {
        element_data(self.atomic_number)
            .map(|(sym, _, _, _, _)| sym)
            .unwrap_or("??")
    }

    pub fn name(&self) -> &'static str {
        element_data(self.atomic_number)
            .map(|(_, name, _, _, _)| name)
            .unwrap_or("Unknown")
    }

    pub fn electronegativity(&self) -> f64 {
        element_data(self.atomic_number)
            .map(|(_, _, _, _, en)| en)
            .unwrap_or(1.0)
    }

    pub fn charge(&self) -> i32 {
        self.atomic_number as i32 - self.electron_count as i32
    }

    pub fn valence_electrons(&self) -> u32 {
        self.shells.last().map(|s| s.electrons).unwrap_or(0)
    }

    pub fn needs_electrons(&self) -> u32 {
        self.shells
            .last()
            .map(|s| s.max_electrons - s.electrons)
            .unwrap_or(0)
    }

    pub fn is_noble_gas(&self) -> bool {
        self.shells.last().map(|s| s.full()).unwrap_or(false)
    }

    pub fn is_ion(&self) -> bool {
        self.charge() != 0
    }

    pub fn ionize(&mut self) -> bool {
        if self.electron_count > 0 {
            self.electron_count -= 1;
            self.build_shells();
            self.compute_ionization_energy();
            true
        } else {
            false
        }
    }

    pub fn capture_electron(&mut self) {
        self.electron_count += 1;
        self.build_shells();
        self.compute_ionization_energy();
    }

    pub fn can_bond_with(&self, other: &Atom) -> bool {
        if self.is_noble_gas() || other.is_noble_gas() {
            return false;
        }
        if self.bonds.len() >= 4 || other.bonds.len() >= 4 {
            return false;
        }
        true
    }

    pub fn bond_type(&self, other: &Atom) -> &'static str {
        let diff = (self.electronegativity() - other.electronegativity()).abs();
        if diff > 1.7 {
            "ionic"
        } else if diff > 0.4 {
            "polar_covalent"
        } else {
            "covalent"
        }
    }

    pub fn bond_energy(&self, other: &Atom) -> f64 {
        match self.bond_type(other) {
            "ionic" => BOND_ENERGY_IONIC,
            "polar_covalent" => (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2.0,
            _ => BOND_ENERGY_COVALENT,
        }
    }

    pub fn distance_to(&self, other: &Atom) -> f64 {
        self.position
            .iter()
            .zip(other.position.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f64>()
            .sqrt()
    }

    /// Render color based on element.
    pub fn render_color(&self) -> [f32; 4] {
        match self.atomic_number {
            1 => [0.9, 0.9, 0.9, 1.0],   // H  white
            2 => [0.8, 1.0, 1.0, 0.7],    // He pale cyan
            6 => [0.2, 0.2, 0.2, 1.0],    // C  dark gray
            7 => [0.2, 0.2, 0.9, 1.0],    // N  blue
            8 => [0.9, 0.2, 0.2, 1.0],    // O  red
            15 => [1.0, 0.5, 0.0, 1.0],   // P  orange
            26 => [0.6, 0.4, 0.2, 1.0],   // Fe brown
            _ => [0.5, 0.8, 0.5, 1.0],    // default green
        }
    }
}

// ---------------------------------------------------------------------------
// AtomicSystem
// ---------------------------------------------------------------------------

/// Collection of atoms with interactions.
pub struct AtomicSystem {
    pub atoms: Vec<Atom>,
    pub temperature: f64,
    pub free_electrons: Vec<Particle>,
    pub bonds_formed: u64,
    pub bonds_broken: u64,
}

impl AtomicSystem {
    pub fn new(temperature: f64) -> Self {
        Self {
            atoms: Vec::new(),
            temperature,
            free_electrons: Vec::new(),
            bonds_formed: 0,
            bonds_broken: 0,
        }
    }

    /// Capture free electrons into ions when T < T_recombination.
    pub fn recombination(&mut self, field: &mut QuantumField) -> Vec<Atom> {
        if self.temperature > T_RECOMBINATION {
            return Vec::new();
        }

        let mut new_atoms = Vec::new();

        // Find protons and electrons in the quantum field
        let proton_indices: Vec<usize> = field
            .particles
            .iter()
            .enumerate()
            .filter(|(_, p)| p.particle_type == ParticleType::Proton)
            .map(|(i, _)| i)
            .collect();

        let mut electron_indices: Vec<usize> = field
            .particles
            .iter()
            .enumerate()
            .filter(|(_, p)| p.particle_type == ParticleType::Electron)
            .map(|(i, _)| i)
            .collect();

        let mut to_remove = Vec::new();

        for &pi in &proton_indices {
            if let Some(ei) = electron_indices.pop() {
                let pos = field.particles[pi].position;
                let vel = field.particles[pi].momentum;
                let atom = Atom::new(1)
                    .with_mass_number(1)
                    .with_position(pos)
                    .with_velocity(vel);
                new_atoms.push(atom.clone());
                self.atoms.push(atom);

                to_remove.push(pi);
                to_remove.push(ei);
            }
        }

        // Remove used particles (sort descending)
        to_remove.sort_unstable();
        to_remove.dedup();
        for idx in to_remove.into_iter().rev() {
            if idx < field.particles.len() {
                field.particles.remove(idx);
            }
        }

        new_atoms
    }

    /// Form heavier elements through nuclear fusion.
    pub fn nucleosynthesis(&mut self, protons: u32, neutrons: u32) -> Vec<Atom> {
        let mut new_atoms = Vec::new();
        let mut p = protons;
        let mut n = neutrons;
        let mut rng = rand::thread_rng();

        // Helium-4: 2 protons + 2 neutrons
        while p >= 2 && n >= 2 {
            let he = Atom::new(2)
                .with_mass_number(4)
                .with_position([
                    rng.gen::<f64>() * 20.0 - 10.0,
                    rng.gen::<f64>() * 20.0 - 10.0,
                    rng.gen::<f64>() * 20.0 - 10.0,
                ]);
            new_atoms.push(he.clone());
            self.atoms.push(he);
            p -= 2;
            n -= 2;
        }

        // Remaining protons become hydrogen
        for _ in 0..p {
            let h = Atom::new(1)
                .with_mass_number(1)
                .with_position([
                    rng.gen::<f64>() * 20.0 - 10.0,
                    rng.gen::<f64>() * 20.0 - 10.0,
                    rng.gen::<f64>() * 20.0 - 10.0,
                ]);
            new_atoms.push(h.clone());
            self.atoms.push(h);
        }

        new_atoms
    }

    /// Form heavier elements in stellar cores.
    pub fn stellar_nucleosynthesis(&mut self, temperature: f64) -> Vec<Atom> {
        let mut new_atoms = Vec::new();
        let mut rng = rand::thread_rng();

        if temperature < 1e3 {
            return new_atoms;
        }

        // Triple-alpha process: 3 He -> C
        let he_indices: Vec<usize> = self
            .atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 2)
            .map(|(i, _)| i)
            .collect();

        if he_indices.len() >= 3 && rng.gen::<f64>() < 0.01 {
            let mut to_remove: Vec<usize> = he_indices[..3].to_vec();
            to_remove.sort_unstable();
            for idx in to_remove.into_iter().rev() {
                self.atoms.remove(idx);
            }
            let carbon = Atom::new(6)
                .with_mass_number(12)
                .with_position([
                    rng.gen::<f64>() * 10.0 - 5.0,
                    rng.gen::<f64>() * 10.0 - 5.0,
                    rng.gen::<f64>() * 10.0 - 5.0,
                ]);
            new_atoms.push(carbon.clone());
            self.atoms.push(carbon);
        }

        // C + He -> O
        let c_idx = self.atoms.iter().position(|a| a.atomic_number == 6);
        let he_idx = self.atoms.iter().position(|a| a.atomic_number == 2);
        if let (Some(ci), Some(hi)) = (c_idx, he_idx) {
            if rng.gen::<f64>() < 0.02 {
                let pos = self.atoms[ci].position;
                let (first, second) = if ci > hi { (ci, hi) } else { (hi, ci) };
                self.atoms.remove(first);
                self.atoms.remove(second);
                let oxygen = Atom::new(8).with_mass_number(16).with_position(pos);
                new_atoms.push(oxygen.clone());
                self.atoms.push(oxygen);
            }
        }

        // O + He -> N (simplified chain)
        let o_idx = self.atoms.iter().position(|a| a.atomic_number == 8);
        let he_idx = self.atoms.iter().position(|a| a.atomic_number == 2);
        if let (Some(oi), Some(hi)) = (o_idx, he_idx) {
            if rng.gen::<f64>() < 0.005 {
                let pos = self.atoms[oi].position;
                let (first, second) = if oi > hi { (oi, hi) } else { (hi, oi) };
                self.atoms.remove(first);
                self.atoms.remove(second);
                let nitrogen = Atom::new(7).with_mass_number(14).with_position(pos);
                new_atoms.push(nitrogen.clone());
                self.atoms.push(nitrogen);
            }
        }

        new_atoms
    }

    /// Try to form a chemical bond between two atoms.
    pub fn attempt_bond(&mut self, idx_a: usize, idx_b: usize) -> bool {
        let (a, b) = if idx_a < idx_b {
            let (left, right) = self.atoms.split_at_mut(idx_b);
            (&mut left[idx_a], &mut right[0])
        } else {
            let (left, right) = self.atoms.split_at_mut(idx_a);
            (&mut right[0], &mut left[idx_b])
        };

        if !a.can_bond_with(b) {
            return false;
        }

        let dist = a.distance_to(b);
        let bond_dist = 2.0;

        if dist > bond_dist * 3.0 {
            return false;
        }

        let energy_barrier = a.bond_energy(b);
        let thermal_energy = K_B * self.temperature;
        let prob = if thermal_energy > 0.0 {
            (-energy_barrier / thermal_energy).exp()
        } else if dist < bond_dist {
            1.0
        } else {
            0.0
        };

        let mut rng = rand::thread_rng();
        if rng.gen::<f64>() < prob {
            let aid = a.atom_id;
            let bid = b.atom_id;
            a.bonds.push(bid);
            b.bonds.push(aid);
            self.bonds_formed += 1;
            true
        } else {
            false
        }
    }

    /// Count atoms by element.
    pub fn element_counts(&self) -> std::collections::HashMap<&'static str, usize> {
        let mut counts = std::collections::HashMap::new();
        for a in &self.atoms {
            *counts.entry(a.symbol()).or_insert(0) += 1;
        }
        counts
    }

    pub fn to_compact(&self) -> String {
        let counts = self.element_counts();
        let mut parts: Vec<String> = counts
            .iter()
            .map(|(k, v)| format!("{}:{}", k, v))
            .collect();
        parts.sort();
        format!(
            "AS[T={:.1e} n={} bonds={} {}]",
            self.temperature,
            self.atoms.len(),
            self.bonds_formed,
            parts.join(",")
        )
    }
}
