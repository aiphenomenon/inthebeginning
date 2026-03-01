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

#[cfg(test)]
mod tests {
    use super::*;

    // -----------------------------------------------------------------------
    // ElectronShell
    // -----------------------------------------------------------------------

    /// A new shell with 0 electrons is empty.
    #[test]
    fn shell_empty() {
        let shell = ElectronShell { n: 1, max_electrons: 2, electrons: 0 };
        assert!(shell.empty());
        assert!(!shell.full());
    }

    /// A full shell rejects additional electrons.
    #[test]
    fn shell_full_rejects_add() {
        let mut shell = ElectronShell { n: 1, max_electrons: 2, electrons: 2 };
        assert!(shell.full());
        assert!(!shell.add_electron());
    }

    /// Adding an electron increments the count.
    #[test]
    fn shell_add_electron() {
        let mut shell = ElectronShell { n: 1, max_electrons: 2, electrons: 0 };
        assert!(shell.add_electron());
        assert_eq!(shell.electrons, 1);
    }

    /// Removing an electron decrements the count.
    #[test]
    fn shell_remove_electron() {
        let mut shell = ElectronShell { n: 1, max_electrons: 2, electrons: 1 };
        assert!(shell.remove_electron());
        assert_eq!(shell.electrons, 0);
    }

    /// Cannot remove from an empty shell.
    #[test]
    fn shell_remove_from_empty_fails() {
        let mut shell = ElectronShell { n: 1, max_electrons: 2, electrons: 0 };
        assert!(!shell.remove_electron());
    }

    // -----------------------------------------------------------------------
    // Atom
    // -----------------------------------------------------------------------

    /// Hydrogen has atomic number 1 and mass number 1.
    #[test]
    fn hydrogen_atom() {
        let h = Atom::new(1);
        assert_eq!(h.atomic_number, 1);
        assert_eq!(h.mass_number, 1); // special case for H
        assert_eq!(h.electron_count, 1);
        assert_eq!(h.symbol(), "H");
        assert_eq!(h.name(), "Hydrogen");
    }

    /// Carbon has atomic number 6, default mass number 12.
    #[test]
    fn carbon_atom() {
        let c = Atom::new(6);
        assert_eq!(c.atomic_number, 6);
        assert_eq!(c.mass_number, 12); // 6*2
        assert_eq!(c.symbol(), "C");
        assert_eq!(c.name(), "Carbon");
    }

    /// Builder methods: with_mass_number, with_position, with_velocity.
    #[test]
    fn atom_builder() {
        let a = Atom::new(8)
            .with_mass_number(16)
            .with_position([1.0, 2.0, 3.0])
            .with_velocity([0.1, 0.2, 0.3]);
        assert_eq!(a.mass_number, 16);
        assert_eq!(a.position, [1.0, 2.0, 3.0]);
        assert_eq!(a.velocity, [0.1, 0.2, 0.3]);
    }

    /// Atom IDs are unique.
    #[test]
    fn atom_ids_unique() {
        let a1 = Atom::new(1);
        let a2 = Atom::new(1);
        assert_ne!(a1.atom_id, a2.atom_id);
    }

    /// Hydrogen has one shell with 1 electron, max 2.
    #[test]
    fn hydrogen_shells() {
        let h = Atom::new(1);
        assert_eq!(h.shells.len(), 1);
        assert_eq!(h.shells[0].n, 1);
        assert_eq!(h.shells[0].max_electrons, 2);
        assert_eq!(h.shells[0].electrons, 1);
    }

    /// Helium has one full shell.
    #[test]
    fn helium_is_noble_gas() {
        let he = Atom::new(2);
        assert!(he.is_noble_gas());
        assert_eq!(he.valence_electrons(), 2);
        assert_eq!(he.needs_electrons(), 0);
    }

    /// Carbon needs 4 electrons to fill its outer shell.
    #[test]
    fn carbon_needs_electrons() {
        let c = Atom::new(6);
        // Shell 1: 2 electrons (full)
        // Shell 2: 4 electrons out of 8
        assert_eq!(c.valence_electrons(), 4);
        assert_eq!(c.needs_electrons(), 4);
    }

    /// Neutral atom has zero charge.
    #[test]
    fn neutral_atom_charge() {
        let a = Atom::new(8);
        assert_eq!(a.charge(), 0);
        assert!(!a.is_ion());
    }

    /// Ionized atom has positive charge.
    #[test]
    fn ionize_creates_cation() {
        let mut a = Atom::new(11); // Sodium
        assert!(a.ionize());
        assert_eq!(a.charge(), 1);
        assert!(a.is_ion());
    }

    /// Cannot ionize past zero electrons.
    #[test]
    fn ionize_hydrogen_once() {
        let mut h = Atom::new(1);
        assert!(h.ionize());    // Remove the 1 electron
        assert!(!h.ionize());   // No electrons left
        assert_eq!(h.electron_count, 0);
    }

    /// Capture electron makes ion neutral.
    #[test]
    fn capture_electron_neutralizes() {
        let mut a = Atom::new(1);
        a.ionize();
        assert_eq!(a.charge(), 1);
        a.capture_electron();
        assert_eq!(a.charge(), 0);
    }

    /// Electronegativity for known elements.
    #[test]
    fn electronegativity_values() {
        let f = Atom::new(9);
        assert!((f.electronegativity() - 3.98).abs() < 1e-10);
        let na = Atom::new(11);
        assert!((na.electronegativity() - 0.93).abs() < 1e-10);
    }

    /// Noble gases cannot bond.
    #[test]
    fn noble_gas_cannot_bond() {
        let he = Atom::new(2);
        let h = Atom::new(1);
        assert!(!he.can_bond_with(&h));
        assert!(!h.can_bond_with(&he));
    }

    /// Atoms with fewer than 4 bonds can bond.
    #[test]
    fn can_bond_when_under_limit() {
        let h1 = Atom::new(1);
        let h2 = Atom::new(1);
        assert!(h1.can_bond_with(&h2));
    }

    /// Atoms with 4 bonds cannot bond further.
    #[test]
    fn cannot_bond_at_limit() {
        let mut c = Atom::new(6);
        c.bonds = vec![100, 101, 102, 103]; // 4 bonds
        let h = Atom::new(1);
        assert!(!c.can_bond_with(&h));
    }

    /// Bond type depends on electronegativity difference.
    #[test]
    fn bond_type_classification() {
        let na = Atom::new(11); // EN = 0.93
        let cl = Atom::new(17); // EN = 3.16
        // diff = 2.23 > 1.7 => ionic
        assert_eq!(na.bond_type(&cl), "ionic");

        let c = Atom::new(6);   // EN = 2.55
        let o = Atom::new(8);   // EN = 3.44
        // diff = 0.89, in (0.4, 1.7] => polar covalent
        assert_eq!(c.bond_type(&o), "polar_covalent");

        let c1 = Atom::new(6);
        let c2 = Atom::new(6);
        // diff = 0 < 0.4 => covalent
        assert_eq!(c1.bond_type(&c2), "covalent");
    }

    /// Bond energy reflects bond type.
    #[test]
    fn bond_energy_values() {
        let na = Atom::new(11);
        let cl = Atom::new(17);
        assert_eq!(na.bond_energy(&cl), BOND_ENERGY_IONIC);

        let c = Atom::new(6);
        let c2 = Atom::new(6);
        assert_eq!(c.bond_energy(&c2), BOND_ENERGY_COVALENT);
    }

    /// Distance between atoms at the same position is zero.
    #[test]
    fn distance_same_position() {
        let a = Atom::new(1).with_position([1.0, 2.0, 3.0]);
        let b = Atom::new(1).with_position([1.0, 2.0, 3.0]);
        assert!((a.distance_to(&b)).abs() < 1e-10);
    }

    /// Distance is computed as Euclidean norm.
    #[test]
    fn distance_euclidean() {
        let a = Atom::new(1).with_position([0.0, 0.0, 0.0]);
        let b = Atom::new(1).with_position([3.0, 4.0, 0.0]);
        assert!((a.distance_to(&b) - 5.0).abs() < 1e-10);
    }

    /// Ionization energy is positive for non-empty shells.
    #[test]
    fn ionization_energy_positive() {
        let h = Atom::new(1);
        assert!(h.ionization_energy > 0.0);
    }

    /// Ionization energy follows 13.6 * Z_eff^2 / n^2 formula.
    #[test]
    fn ionization_energy_hydrogen() {
        let h = Atom::new(1);
        // Z_eff = 1 (no inner electrons), n = 1
        let expected = 13.6 * 1.0 * 1.0 / (1.0 * 1.0);
        assert!((h.ionization_energy - expected).abs() < 1e-10);
    }

    /// Render color returns valid RGBA for various elements.
    #[test]
    fn render_color_valid() {
        let elements = [1, 2, 6, 7, 8, 15, 26, 14];
        for z in &elements {
            let a = Atom::new(*z);
            let c = a.render_color();
            for val in &c {
                assert!(*val >= 0.0 && *val <= 1.0, "element {} has out-of-range color", z);
            }
        }
    }

    /// Unknown element symbol returns "??".
    #[test]
    fn unknown_element_symbol() {
        let a = Atom::new(99);
        assert_eq!(a.symbol(), "??");
        assert_eq!(a.name(), "Unknown");
    }

    // -----------------------------------------------------------------------
    // AtomicSystem
    // -----------------------------------------------------------------------

    /// New AtomicSystem is empty.
    #[test]
    fn atomic_system_new_empty() {
        let sys = AtomicSystem::new(1000.0);
        assert_eq!(sys.atoms.len(), 0);
        assert_eq!(sys.bonds_formed, 0);
    }

    /// Nucleosynthesis forms helium from protons and neutrons.
    #[test]
    fn nucleosynthesis_forms_helium() {
        let mut sys = AtomicSystem::new(T_NUCLEOSYNTHESIS);
        let atoms = sys.nucleosynthesis(4, 4);
        // 4p + 4n => 2 He-4
        let he_count = atoms.iter().filter(|a| a.atomic_number == 2).count();
        assert_eq!(he_count, 2);
    }

    /// Nucleosynthesis with no neutrons produces only hydrogen.
    #[test]
    fn nucleosynthesis_protons_only() {
        let mut sys = AtomicSystem::new(T_NUCLEOSYNTHESIS);
        let atoms = sys.nucleosynthesis(5, 0);
        // 5 protons, 0 neutrons => 5 hydrogen atoms
        assert_eq!(atoms.len(), 5);
        for a in &atoms {
            assert_eq!(a.atomic_number, 1);
        }
    }

    /// Nucleosynthesis: remaining protons become hydrogen.
    #[test]
    fn nucleosynthesis_remainder_hydrogen() {
        let mut sys = AtomicSystem::new(T_NUCLEOSYNTHESIS);
        let atoms = sys.nucleosynthesis(5, 2);
        // 2p+2n => 1 He, remaining 3p => 3 H
        let he_count = atoms.iter().filter(|a| a.atomic_number == 2).count();
        let h_count = atoms.iter().filter(|a| a.atomic_number == 1).count();
        assert_eq!(he_count, 1);
        assert_eq!(h_count, 3);
    }

    /// Element counts reflect the atomic composition.
    #[test]
    fn element_counts_correct() {
        let mut sys = AtomicSystem::new(1000.0);
        sys.atoms.push(Atom::new(1));
        sys.atoms.push(Atom::new(1));
        sys.atoms.push(Atom::new(6));
        let counts = sys.element_counts();
        assert_eq!(*counts.get("H").unwrap(), 2);
        assert_eq!(*counts.get("C").unwrap(), 1);
    }

    /// Compact representation includes temperature and atom count.
    #[test]
    fn atomic_system_compact() {
        let mut sys = AtomicSystem::new(1000.0);
        sys.atoms.push(Atom::new(1));
        let compact = sys.to_compact();
        assert!(compact.starts_with("AS["));
        assert!(compact.contains("n=1"));
    }

    /// Recombination at high temperature does nothing.
    #[test]
    fn recombination_high_temp_no_effect() {
        let mut sys = AtomicSystem::new(T_RECOMBINATION * 2.0);
        let mut field = QuantumField::new(T_RECOMBINATION * 2.0);
        field.particles.push(Particle::new(ParticleType::Proton));
        field.particles.push(Particle::new(ParticleType::Electron));

        let atoms = sys.recombination(&mut field);
        assert!(atoms.is_empty());
        assert_eq!(field.particles.len(), 2); // unchanged
    }

    /// Recombination below threshold converts protons+electrons to hydrogen.
    #[test]
    fn recombination_forms_hydrogen() {
        let mut sys = AtomicSystem::new(T_RECOMBINATION * 0.5);
        let mut field = QuantumField::new(T_RECOMBINATION * 0.5);
        field.particles.push(Particle::new(ParticleType::Proton));
        field.particles.push(Particle::new(ParticleType::Electron));

        let atoms = sys.recombination(&mut field);
        assert_eq!(atoms.len(), 1);
        assert_eq!(atoms[0].atomic_number, 1);
        assert_eq!(field.particles.len(), 0); // consumed
    }

    // -----------------------------------------------------------------------
    // AtomicSystem::stellar_nucleosynthesis
    // -----------------------------------------------------------------------

    /// Stellar nucleosynthesis at low temperature does nothing.
    #[test]
    fn stellar_nucleosynthesis_low_temp_no_effect() {
        let mut sys = AtomicSystem::new(500.0);
        // Add some helium
        for _ in 0..6 {
            sys.atoms.push(Atom::new(2).with_mass_number(4));
        }
        let new_atoms = sys.stellar_nucleosynthesis(500.0); // below 1e3 threshold
        assert!(new_atoms.is_empty());
    }

    /// Stellar nucleosynthesis requires at least 3 He for triple-alpha.
    #[test]
    fn stellar_nucleosynthesis_insufficient_helium() {
        let mut sys = AtomicSystem::new(T_STELLAR_CORE);
        // Only 2 helium -- not enough for triple alpha (needs 3)
        sys.atoms.push(Atom::new(2).with_mass_number(4));
        sys.atoms.push(Atom::new(2).with_mass_number(4));

        // The triple-alpha also has a random chance (0.01), so even with 3 He
        // it might not fire. With only 2 He it should never produce carbon.
        let new_atoms = sys.stellar_nucleosynthesis(T_STELLAR_CORE);
        let carbon_count = new_atoms.iter().filter(|a| a.atomic_number == 6).count();
        assert_eq!(carbon_count, 0, "2 He should not produce carbon");
    }

    /// Stellar nucleosynthesis can produce carbon from 3+ helium (probabilistic).
    #[test]
    fn stellar_nucleosynthesis_triple_alpha_possible() {
        // Since triple-alpha has a 1% chance per call, run many iterations.
        let mut carbon_ever_produced = false;
        for _ in 0..500 {
            let mut sys = AtomicSystem::new(T_STELLAR_CORE);
            for _ in 0..6 {
                sys.atoms.push(Atom::new(2).with_mass_number(4));
            }
            let new_atoms = sys.stellar_nucleosynthesis(T_STELLAR_CORE);
            if new_atoms.iter().any(|a| a.atomic_number == 6) {
                carbon_ever_produced = true;
                break;
            }
        }
        assert!(carbon_ever_produced,
            "triple-alpha should eventually produce carbon from 6 He over many tries");
    }

    // -----------------------------------------------------------------------
    // AtomicSystem::attempt_bond
    // -----------------------------------------------------------------------

    /// attempt_bond fails when atoms cannot bond (e.g., noble gas).
    #[test]
    fn attempt_bond_noble_gas_fails() {
        let mut sys = AtomicSystem::new(300.0);
        sys.atoms.push(Atom::new(2)); // Helium (noble gas)
        sys.atoms.push(Atom::new(1)); // Hydrogen
        let result = sys.attempt_bond(0, 1);
        assert!(!result, "noble gas should not bond");
        assert_eq!(sys.bonds_formed, 0);
    }

    /// attempt_bond fails when atoms are too far apart.
    #[test]
    fn attempt_bond_too_far_apart() {
        let mut sys = AtomicSystem::new(300.0);
        sys.atoms.push(Atom::new(1).with_position([0.0, 0.0, 0.0]));
        sys.atoms.push(Atom::new(1).with_position([100.0, 0.0, 0.0])); // very far
        let result = sys.attempt_bond(0, 1);
        assert!(!result, "atoms too far apart should not bond");
    }

    /// attempt_bond can succeed for close non-noble-gas atoms.
    #[test]
    fn attempt_bond_close_atoms() {
        // With high temperature, the exponential probability exp(-E/kT) approaches 1.
        let mut bonded = false;
        for _ in 0..200 {
            let mut sys = AtomicSystem::new(1e10); // very high temperature
            sys.atoms.push(Atom::new(1).with_position([0.0, 0.0, 0.0]));
            sys.atoms.push(Atom::new(1).with_position([0.1, 0.0, 0.0])); // very close
            if sys.attempt_bond(0, 1) {
                bonded = true;
                assert_eq!(sys.bonds_formed, 1);
                // Both atoms should reference each other
                assert!(!sys.atoms[0].bonds.is_empty());
                assert!(!sys.atoms[1].bonds.is_empty());
                break;
            }
        }
        assert!(bonded, "close atoms at high temperature should eventually bond");
    }

    /// attempt_bond with idx_a > idx_b works correctly (index order handling).
    #[test]
    fn attempt_bond_reversed_indices() {
        let mut bonded = false;
        for _ in 0..200 {
            let mut sys = AtomicSystem::new(1e10);
            sys.atoms.push(Atom::new(1).with_position([0.0, 0.0, 0.0]));
            sys.atoms.push(Atom::new(1).with_position([0.1, 0.0, 0.0]));
            // Pass indices in reverse order (1, 0 instead of 0, 1)
            if sys.attempt_bond(1, 0) {
                bonded = true;
                assert_eq!(sys.bonds_formed, 1);
                break;
            }
        }
        assert!(bonded, "attempt_bond should work with reversed index order");
    }

    /// attempt_bond fails when atoms already have 4 bonds.
    #[test]
    fn attempt_bond_at_bond_limit() {
        let mut sys = AtomicSystem::new(1e10);
        let mut c = Atom::new(6); // Carbon
        c.bonds = vec![100, 101, 102, 103]; // already 4 bonds
        sys.atoms.push(c);
        sys.atoms.push(Atom::new(1).with_position([0.1, 0.0, 0.0]));
        let result = sys.attempt_bond(0, 1);
        assert!(!result, "atom with 4 bonds should not form more");
    }
}
