//! Atomic physics simulation.
//!
//! Models atoms with electron shells, nucleosynthesis, recombination,
//! and stellar nucleosynthesis of heavier elements. Port of the Python
//! `simulator/atomic.py`.

use rand::Rng;

use crate::constants::*;
use crate::quantum::QuantumField;

// ---------------------------------------------------------------------------
// Element data
// ---------------------------------------------------------------------------

/// (symbol, name, electronegativity)
pub struct ElementInfo {
    pub symbol: &'static str,
    pub name: &'static str,
    pub electronegativity: f64,
}

pub fn element_info(z: u32) -> ElementInfo {
    match z {
        1 => ElementInfo { symbol: "H", name: "Hydrogen", electronegativity: 2.20 },
        2 => ElementInfo { symbol: "He", name: "Helium", electronegativity: 0.0 },
        3 => ElementInfo { symbol: "Li", name: "Lithium", electronegativity: 0.98 },
        4 => ElementInfo { symbol: "Be", name: "Beryllium", electronegativity: 1.57 },
        5 => ElementInfo { symbol: "B", name: "Boron", electronegativity: 2.04 },
        6 => ElementInfo { symbol: "C", name: "Carbon", electronegativity: 2.55 },
        7 => ElementInfo { symbol: "N", name: "Nitrogen", electronegativity: 3.04 },
        8 => ElementInfo { symbol: "O", name: "Oxygen", electronegativity: 3.44 },
        9 => ElementInfo { symbol: "F", name: "Fluorine", electronegativity: 3.98 },
        10 => ElementInfo { symbol: "Ne", name: "Neon", electronegativity: 0.0 },
        14 => ElementInfo { symbol: "Si", name: "Silicon", electronegativity: 1.90 },
        15 => ElementInfo { symbol: "P", name: "Phosphorus", electronegativity: 2.19 },
        16 => ElementInfo { symbol: "S", name: "Sulfur", electronegativity: 2.58 },
        26 => ElementInfo { symbol: "Fe", name: "Iron", electronegativity: 1.83 },
        _ => ElementInfo {
            symbol: "?",
            name: "Unknown",
            electronegativity: 1.0,
        },
    }
}

/// Rendering color for atoms by atomic number.
/// H=white, He=yellow, C=dark gray, N=blue, O=red, Fe=brown
pub fn atom_render_color(z: u32) -> [f32; 4] {
    match z {
        1 => [0.95, 0.95, 0.95, 1.0],  // H  - white
        2 => [1.0, 1.0, 0.3, 1.0],     // He - yellow
        3 => [0.8, 0.5, 0.8, 1.0],     // Li - purple-ish
        6 => [0.35, 0.35, 0.35, 1.0],  // C  - dark gray
        7 => [0.2, 0.3, 1.0, 1.0],     // N  - blue
        8 => [1.0, 0.15, 0.15, 1.0],   // O  - red
        15 => [1.0, 0.5, 0.0, 1.0],    // P  - orange
        16 => [1.0, 1.0, 0.0, 1.0],    // S  - yellow
        26 => [0.55, 0.3, 0.1, 1.0],   // Fe - brown
        _ => [0.7, 0.7, 0.7, 1.0],     // default gray
    }
}

// ---------------------------------------------------------------------------
// Atom
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct Atom {
    pub id: u32,
    pub atomic_number: u32,
    pub mass_number: u32,
    pub electron_count: u32,
    pub position: [f64; 3],
    pub velocity: [f64; 3],
    pub bonds: Vec<u32>, // IDs of bonded atoms
}

impl Atom {
    pub fn new(id: u32, atomic_number: u32, position: [f64; 3]) -> Self {
        let mass_number = if atomic_number == 1 {
            1
        } else {
            atomic_number * 2
        };
        Self {
            id,
            atomic_number,
            mass_number,
            electron_count: atomic_number,
            position,
            velocity: [0.0; 3],
            bonds: Vec::new(),
        }
    }

    pub fn symbol(&self) -> &'static str {
        element_info(self.atomic_number).symbol
    }

    pub fn electronegativity(&self) -> f64 {
        element_info(self.atomic_number).electronegativity
    }

    /// Valence electrons (simplified).
    pub fn valence_electrons(&self) -> u32 {
        let mut remaining = self.electron_count;
        for &max_e in &ELECTRON_SHELLS {
            if remaining <= max_e {
                return remaining;
            }
            remaining -= max_e;
        }
        remaining
    }

    pub fn is_noble_gas(&self) -> bool {
        let mut remaining = self.electron_count;
        for &max_e in &ELECTRON_SHELLS {
            if remaining == 0 {
                return true; // all shells exactly filled
            }
            if remaining < max_e {
                return false;
            }
            remaining -= max_e;
        }
        remaining == 0
    }

    pub fn can_bond(&self) -> bool {
        !self.is_noble_gas() && self.bonds.len() < 4
    }

    pub fn render_size(&self) -> f32 {
        8.0 + (self.atomic_number as f32).sqrt() * 2.0
    }

    pub fn render_color(&self) -> [f32; 4] {
        atom_render_color(self.atomic_number)
    }
}

// ---------------------------------------------------------------------------
// Atomic system
// ---------------------------------------------------------------------------

pub struct AtomicSystem {
    pub atoms: Vec<Atom>,
    pub temperature: f64,
    pub bonds_formed: u64,
    next_id: u32,
}

impl AtomicSystem {
    pub fn new() -> Self {
        Self {
            atoms: Vec::new(),
            temperature: T_RECOMBINATION,
            bonds_formed: 0,
            next_id: 1,
        }
    }

    fn alloc_id(&mut self) -> u32 {
        let id = self.next_id;
        self.next_id = self.next_id.wrapping_add(1);
        id
    }

    /// Big Bang Nucleosynthesis: protons + neutrons -> He and H.
    pub fn nucleosynthesis(&mut self, mut protons: usize, mut neutrons: usize, rng: &mut impl Rng) -> usize {
        let mut created = 0;

        // Helium-4: 2p + 2n
        while protons >= 2 && neutrons >= 2 {
            let id = self.alloc_id();
            let pos = [gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0)];
            let mut atom = Atom::new(id, 2, pos);
            atom.mass_number = 4;
            self.atoms.push(atom);
            protons -= 2;
            neutrons -= 2;
            created += 1;
        }

        // Remaining protons -> hydrogen
        for _ in 0..protons {
            let id = self.alloc_id();
            let pos = [gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0)];
            self.atoms.push(Atom::new(id, 1, pos));
            created += 1;
        }

        created
    }

    /// Recombination: capture electrons as temperature drops.
    pub fn recombination(&mut self, field: &mut QuantumField, _rng: &mut impl Rng) -> usize {
        if self.temperature > T_RECOMBINATION {
            return 0;
        }

        let protons = field.proton_count();
        let electrons = field.particles.iter().filter(|p| p.particle_type == crate::quantum::ParticleType::Electron).count();
        let count = protons.min(electrons);

        if count == 0 {
            return 0;
        }

        // Get positions from protons
        let proton_positions: Vec<[f64; 3]> = field.particles.iter()
            .filter(|p| p.particle_type == crate::quantum::ParticleType::Proton)
            .take(count)
            .map(|p| p.position)
            .collect();

        // Remove consumed particles
        field.remove_for_recombination(count, count);

        let mut created = 0;
        for pos in proton_positions {
            let id = self.alloc_id();
            self.atoms.push(Atom::new(id, 1, pos));
            created += 1;
        }

        created
    }

    /// Stellar nucleosynthesis: He -> C, O, N, Fe in stellar cores.
    pub fn stellar_nucleosynthesis(&mut self, temperature: f64, rng: &mut impl Rng) -> usize {
        if temperature < 1e3 {
            return 0;
        }

        let mut created = 0;

        // Triple-alpha: 3 He -> C
        let he_count = self.atoms.iter().filter(|a| a.atomic_number == 2).count();
        if he_count >= 3 && rng.gen::<f64>() < 0.01 {
            // Remove 3 He atoms
            let mut removed = 0;
            self.atoms.retain(|a| {
                if removed < 3 && a.atomic_number == 2 {
                    removed += 1;
                    false
                } else {
                    true
                }
            });
            let id = self.alloc_id();
            let pos = [gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0)];
            let mut atom = Atom::new(id, 6, pos);
            atom.mass_number = 12;
            self.atoms.push(atom);
            created += 1;
        }

        // C + He -> O
        let c_count = self.atoms.iter().filter(|a| a.atomic_number == 6).count();
        let he_count = self.atoms.iter().filter(|a| a.atomic_number == 2).count();
        if c_count > 0 && he_count > 0 && rng.gen::<f64>() < 0.02 {
            // Find first C position
            let c_pos = self.atoms.iter().find(|a| a.atomic_number == 6).map(|a| a.position).unwrap_or([0.0; 3]);
            // Remove 1 C and 1 He
            let mut c_removed = false;
            let mut he_removed = false;
            self.atoms.retain(|a| {
                if !c_removed && a.atomic_number == 6 {
                    c_removed = true;
                    false
                } else if !he_removed && a.atomic_number == 2 {
                    he_removed = true;
                    false
                } else {
                    true
                }
            });
            let id = self.alloc_id();
            let mut atom = Atom::new(id, 8, c_pos);
            atom.mass_number = 16;
            self.atoms.push(atom);
            created += 1;
        }

        // O + He -> N (simplified chain for variety)
        let o_count = self.atoms.iter().filter(|a| a.atomic_number == 8).count();
        let he_count = self.atoms.iter().filter(|a| a.atomic_number == 2).count();
        if o_count > 0 && he_count > 0 && rng.gen::<f64>() < 0.005 {
            let o_pos = self.atoms.iter().find(|a| a.atomic_number == 8).map(|a| a.position).unwrap_or([0.0; 3]);
            let mut o_removed = false;
            let mut he_removed = false;
            self.atoms.retain(|a| {
                if !o_removed && a.atomic_number == 8 {
                    o_removed = true;
                    false
                } else if !he_removed && a.atomic_number == 2 {
                    he_removed = true;
                    false
                } else {
                    true
                }
            });
            let id = self.alloc_id();
            let mut atom = Atom::new(id, 7, o_pos);
            atom.mass_number = 14;
            self.atoms.push(atom);
            created += 1;
        }

        created
    }

    /// Seed extra elements at Earth epoch for chemistry.
    pub fn seed_earth_elements(&mut self, rng: &mut impl Rng) -> usize {
        let elements_to_seed: &[(u32, usize)] = &[
            (1, 40),  // Hydrogen
            (2, 10),  // Helium
            (6, 15),  // Carbon
            (7, 10),  // Nitrogen
            (8, 15),  // Oxygen
            (15, 3),  // Phosphorus
        ];
        let mut total = 0;
        for &(z, count) in elements_to_seed {
            for _ in 0..count {
                let id = self.alloc_id();
                let pos = [gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0)];
                let mut atom = Atom::new(id, z, pos);
                atom.mass_number = if z == 1 { 1 } else { z * 2 };
                self.atoms.push(atom);
                total += 1;
            }
        }
        total
    }

    /// Count atoms by element symbol.
    pub fn element_counts(&self) -> Vec<(&'static str, usize)> {
        use std::collections::HashMap;
        let mut map: HashMap<&str, usize> = HashMap::new();
        for a in &self.atoms {
            *map.entry(a.symbol()).or_insert(0) += 1;
        }
        let mut v: Vec<_> = map.into_iter().collect();
        v.sort_by_key(|(s, _)| *s);
        v
    }

    pub fn cool(&mut self, factor: f64) {
        self.temperature *= factor;
    }

    pub fn to_compact(&self) -> String {
        let counts = self.element_counts();
        let count_str: String = counts
            .iter()
            .map(|(s, c)| format!("{}:{}", s, c))
            .collect::<Vec<_>>()
            .join(",");
        format!(
            "Atoms[n={} T={:.1e} {}]",
            self.atoms.len(),
            self.temperature,
            count_str,
        )
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn gauss(rng: &mut impl Rng, mean: f64, std: f64) -> f64 {
    let u1: f64 = rng.gen::<f64>().max(1e-15);
    let u2: f64 = rng.gen::<f64>();
    mean + std * (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::SmallRng;
    use rand::SeedableRng;

    fn make_rng() -> SmallRng {
        SmallRng::seed_from_u64(42)
    }

    // --- ElementInfo tests ---

    #[test]
    fn test_element_info_hydrogen() {
        let info = element_info(1);
        assert_eq!(info.symbol, "H");
        assert_eq!(info.name, "Hydrogen");
        assert!((info.electronegativity - 2.20).abs() < 0.01);
    }

    #[test]
    fn test_element_info_helium() {
        let info = element_info(2);
        assert_eq!(info.symbol, "He");
        assert_eq!(info.name, "Helium");
        assert_eq!(info.electronegativity, 0.0); // Noble gas
    }

    #[test]
    fn test_element_info_carbon() {
        let info = element_info(6);
        assert_eq!(info.symbol, "C");
        assert_eq!(info.name, "Carbon");
        assert!((info.electronegativity - 2.55).abs() < 0.01);
    }

    #[test]
    fn test_element_info_unknown() {
        let info = element_info(99);
        assert_eq!(info.symbol, "?");
        assert_eq!(info.name, "Unknown");
    }

    // --- Atom tests ---

    #[test]
    fn test_atom_new_hydrogen() {
        let atom = Atom::new(1, 1, [0.0, 0.0, 0.0]);
        assert_eq!(atom.atomic_number, 1);
        assert_eq!(atom.mass_number, 1);
        assert_eq!(atom.electron_count, 1);
        assert_eq!(atom.symbol(), "H");
        assert!(atom.bonds.is_empty());
    }

    #[test]
    fn test_atom_new_helium() {
        let atom = Atom::new(1, 2, [0.0, 0.0, 0.0]);
        assert_eq!(atom.atomic_number, 2);
        assert_eq!(atom.mass_number, 4); // Non-hydrogen: z * 2
    }

    #[test]
    fn test_atom_valence_electrons_hydrogen() {
        let atom = Atom::new(1, 1, [0.0, 0.0, 0.0]);
        // H has 1 electron in first shell (max 2)
        assert_eq!(atom.valence_electrons(), 1);
    }

    #[test]
    fn test_atom_valence_electrons_helium() {
        let atom = Atom::new(1, 2, [0.0, 0.0, 0.0]);
        // He has 2 electrons filling first shell
        assert_eq!(atom.valence_electrons(), 2);
    }

    #[test]
    fn test_atom_valence_electrons_carbon() {
        let atom = Atom::new(1, 6, [0.0, 0.0, 0.0]);
        // C has 6 electrons: 2 in first shell, 4 in second
        assert_eq!(atom.valence_electrons(), 4);
    }

    #[test]
    fn test_atom_is_noble_gas_helium() {
        let atom = Atom::new(1, 2, [0.0, 0.0, 0.0]);
        // He fills first shell (2/2)
        assert!(atom.is_noble_gas());
    }

    #[test]
    fn test_atom_is_noble_gas_neon() {
        let atom = Atom::new(1, 10, [0.0, 0.0, 0.0]);
        // Ne fills first two shells (2+8=10)
        assert!(atom.is_noble_gas());
    }

    #[test]
    fn test_atom_is_not_noble_gas() {
        let atom = Atom::new(1, 6, [0.0, 0.0, 0.0]);
        assert!(!atom.is_noble_gas());
    }

    #[test]
    fn test_atom_can_bond() {
        let atom = Atom::new(1, 1, [0.0, 0.0, 0.0]);
        assert!(atom.can_bond());

        let noble = Atom::new(1, 2, [0.0, 0.0, 0.0]);
        assert!(!noble.can_bond());
    }

    #[test]
    fn test_atom_can_bond_limit() {
        let mut atom = Atom::new(1, 6, [0.0, 0.0, 0.0]);
        // Carbon can bond, but not more than 4
        assert!(atom.can_bond());
        atom.bonds = vec![1, 2, 3, 4];
        assert!(!atom.can_bond());
    }

    #[test]
    fn test_atom_render_color() {
        let color = atom_render_color(1);
        assert_eq!(color.len(), 4);
        // H should be white-ish
        assert!(color[0] > 0.9);

        let color_c = atom_render_color(6);
        // C should be dark gray
        assert!(color_c[0] < 0.5);
    }

    // --- AtomicSystem tests ---

    #[test]
    fn test_atomic_system_new() {
        let sys = AtomicSystem::new();
        assert!(sys.atoms.is_empty());
        assert_eq!(sys.temperature, T_RECOMBINATION);
        assert_eq!(sys.bonds_formed, 0);
    }

    #[test]
    fn test_nucleosynthesis_basic() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();

        // 4 protons + 4 neutrons -> 2 He-4 atoms
        let created = sys.nucleosynthesis(4, 4, &mut rng);
        assert_eq!(created, 2);
        assert_eq!(sys.atoms.len(), 2);
        assert!(sys.atoms.iter().all(|a| a.atomic_number == 2));
    }

    #[test]
    fn test_nucleosynthesis_mixed() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();

        // 5 protons + 2 neutrons -> 1 He-4 + 3 H
        let created = sys.nucleosynthesis(5, 2, &mut rng);
        assert_eq!(created, 4); // 1 He + 3 H
        let he_count = sys.atoms.iter().filter(|a| a.atomic_number == 2).count();
        let h_count = sys.atoms.iter().filter(|a| a.atomic_number == 1).count();
        assert_eq!(he_count, 1);
        assert_eq!(h_count, 3);
    }

    #[test]
    fn test_nucleosynthesis_only_protons() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();

        // 3 protons + 0 neutrons -> 3 H
        let created = sys.nucleosynthesis(3, 0, &mut rng);
        assert_eq!(created, 3);
        assert!(sys.atoms.iter().all(|a| a.atomic_number == 1));
    }

    #[test]
    fn test_seed_earth_elements() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();

        let total = sys.seed_earth_elements(&mut rng);
        // Expected: 40 H + 10 He + 15 C + 10 N + 15 O + 3 P = 93
        assert_eq!(total, 93);
        assert_eq!(sys.atoms.len(), 93);
    }

    #[test]
    fn test_element_counts() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();
        sys.seed_earth_elements(&mut rng);

        let counts = sys.element_counts();
        // Should contain H, He, C, N, O, P
        let h_count = counts.iter().find(|(s, _)| *s == "H").map(|(_, c)| *c).unwrap_or(0);
        assert_eq!(h_count, 40);

        let c_count = counts.iter().find(|(s, _)| *s == "C").map(|(_, c)| *c).unwrap_or(0);
        assert_eq!(c_count, 15);
    }

    #[test]
    fn test_atom_render_size() {
        let h = Atom::new(1, 1, [0.0; 3]);
        let fe = Atom::new(1, 26, [0.0; 3]);
        // Iron should be visually larger than hydrogen
        assert!(fe.render_size() > h.render_size());
    }

    #[test]
    fn test_stellar_nucleosynthesis_low_temp() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();
        for _ in 0..10 {
            let id = sys.alloc_id();
            sys.atoms.push(Atom::new(id, 2, [0.0; 3]));
        }
        let created = sys.stellar_nucleosynthesis(100.0, &mut rng);
        assert_eq!(created, 0, "No fusion below 1e3 temperature");
    }

    #[test]
    fn test_stellar_nucleosynthesis_creates_heavier_elements() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();
        // Add many He atoms and try many rounds to overcome 0.01 probability
        let mut carbon_formed = false;
        for _ in 0..500 {
            // Re-seed with He atoms to keep the pool fresh
            if sys.atoms.iter().filter(|a| a.atomic_number == 2).count() < 10 {
                for _ in 0..20 {
                    let id = sys.alloc_id();
                    let mut atom = Atom::new(id, 2, [0.0; 3]);
                    atom.mass_number = 4;
                    sys.atoms.push(atom);
                }
            }
            let _created = sys.stellar_nucleosynthesis(1e7, &mut rng);
            if sys.atoms.iter().any(|a| a.atomic_number == 6) {
                carbon_formed = true;
                break;
            }
        }
        assert!(carbon_formed, "Triple-alpha should eventually produce carbon");
    }

    #[test]
    fn test_recombination_above_threshold() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();
        sys.temperature = T_RECOMBINATION * 2.0; // Too hot
        let mut field = crate::quantum::QuantumField::new(1e6);
        field.particles.push(crate::quantum::Particle {
            id: 1,
            particle_type: crate::quantum::ParticleType::Proton,
            position: [0.0; 3],
            momentum: [0.0; 3],
            spin: crate::quantum::Spin::Up,
            color: None,
            wave_fn: crate::quantum::WaveFunction::new(),
            entangled_with: None,
        });
        let created = sys.recombination(&mut field, &mut rng);
        assert_eq!(created, 0, "No recombination above threshold temperature");
    }

    #[test]
    fn test_recombination_below_threshold() {
        let mut rng = make_rng();
        let mut sys = AtomicSystem::new();
        sys.temperature = T_RECOMBINATION * 0.5; // Cold enough

        let mut field = crate::quantum::QuantumField::new(1e3);
        // Add protons and electrons
        for i in 0..3u32 {
            field.particles.push(crate::quantum::Particle {
                id: i * 2 + 1,
                particle_type: crate::quantum::ParticleType::Proton,
                position: [0.0; 3],
                momentum: [0.0; 3],
                spin: crate::quantum::Spin::Up,
                color: None,
                wave_fn: crate::quantum::WaveFunction::new(),
                entangled_with: None,
            });
            field.particles.push(crate::quantum::Particle {
                id: i * 2 + 2,
                particle_type: crate::quantum::ParticleType::Electron,
                position: [0.0; 3],
                momentum: [0.0; 3],
                spin: crate::quantum::Spin::Up,
                color: None,
                wave_fn: crate::quantum::WaveFunction::new(),
                entangled_with: None,
            });
        }

        let created = sys.recombination(&mut field, &mut rng);
        assert_eq!(created, 3, "Should form 3 hydrogen atoms from 3 protons + 3 electrons");
        assert_eq!(sys.atoms.len(), 3);
        assert!(sys.atoms.iter().all(|a| a.atomic_number == 1));
    }
}
