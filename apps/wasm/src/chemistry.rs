//! Chemistry simulation - molecular assembly and reactions.
//!
//! Models formation of water, methane, ammonia, amino acids, and
//! nucleotides from atoms. Port of the Python `simulator/chemistry.py`.

use rand::Rng;

use crate::atomic::Atom;
use crate::constants::*;

// ---------------------------------------------------------------------------
// Molecule
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct Molecule {
    pub id: u32,
    pub name: String,
    pub formula: String,
    pub atom_ids: Vec<u32>,
    pub atom_positions: Vec<[f64; 3]>,
    pub atom_atomic_numbers: Vec<u32>,
    /// Bond list: pairs of indices into the atom_ids/positions arrays.
    pub bonds: Vec<(usize, usize)>,
    pub position: [f64; 3],
    pub is_organic: bool,
}

impl Molecule {
    pub fn render_color(&self) -> [f32; 4] {
        if self.is_organic {
            [0.2, 0.9, 0.3, 0.9] // green for organic
        } else if self.name == "water" {
            [0.3, 0.5, 1.0, 0.8] // blue for water
        } else {
            [0.7, 0.7, 0.7, 0.8] // gray default
        }
    }
}

// ---------------------------------------------------------------------------
// Chemical system
// ---------------------------------------------------------------------------

pub struct ChemicalSystem {
    pub molecules: Vec<Molecule>,
    pub water_count: usize,
    pub amino_acid_count: usize,
    pub nucleotide_count: usize,
    pub reactions_occurred: u64,
    next_id: u32,
}

impl ChemicalSystem {
    pub fn new() -> Self {
        Self {
            molecules: Vec::new(),
            water_count: 0,
            amino_acid_count: 0,
            nucleotide_count: 0,
            reactions_occurred: 0,
            next_id: 1,
        }
    }

    fn alloc_id(&mut self) -> u32 {
        let id = self.next_id;
        self.next_id = self.next_id.wrapping_add(1);
        id
    }

    /// Form water molecules: 2H + O -> H2O.
    pub fn form_water(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut formed = 0;

        loop {
            // Find unbonded H
            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .take(2)
                .collect();

            if h_indices.len() < 2 {
                break;
            }

            // Find unbonded O
            let o_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 8 && a.bonds.len() < 2);

            if o_idx.is_none() {
                break;
            }
            let o_idx = o_idx.unwrap();

            let h1_id = atoms[h_indices[0]].id;
            let h2_id = atoms[h_indices[1]].id;
            let o_id = atoms[o_idx].id;
            let pos = atoms[o_idx].position;

            // Record bonds
            atoms[h_indices[0]].bonds.push(o_id);
            atoms[h_indices[1]].bonds.push(o_id);
            atoms[o_idx].bonds.push(h1_id);
            atoms[o_idx].bonds.push(h2_id);

            let mol_id = self.alloc_id();
            self.molecules.push(Molecule {
                id: mol_id,
                name: "water".to_string(),
                formula: "H2O".to_string(),
                atom_ids: vec![h1_id, h2_id, o_id],
                atom_positions: vec![
                    atoms[h_indices[0]].position,
                    atoms[h_indices[1]].position,
                    pos,
                ],
                atom_atomic_numbers: vec![1, 1, 8],
                bonds: vec![(0, 2), (1, 2)],
                position: pos,
                is_organic: false,
            });

            self.water_count += 1;
            formed += 1;
        }

        formed
    }

    /// Form methane: C + 4H -> CH4.
    pub fn form_methane(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut formed = 0;

        loop {
            let c_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 6 && a.bonds.is_empty());
            if c_idx.is_none() {
                break;
            }
            let c_idx = c_idx.unwrap();

            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .take(4)
                .collect();
            if h_indices.len() < 4 {
                break;
            }

            let c_id = atoms[c_idx].id;
            let c_pos = atoms[c_idx].position;

            let mut atom_ids = vec![c_id];
            let mut atom_positions = vec![c_pos];
            let mut atom_zs = vec![6u32];
            let mut bonds = Vec::new();

            for (bond_i, &hi) in h_indices.iter().enumerate() {
                let h_id = atoms[hi].id;
                atoms[hi].bonds.push(c_id);
                atoms[c_idx].bonds.push(h_id);
                atom_ids.push(h_id);
                atom_positions.push(atoms[hi].position);
                atom_zs.push(1);
                bonds.push((0, bond_i + 1));
            }

            let mol_id = self.alloc_id();
            self.molecules.push(Molecule {
                id: mol_id,
                name: "methane".to_string(),
                formula: "CH4".to_string(),
                atom_ids,
                atom_positions,
                atom_atomic_numbers: atom_zs,
                bonds,
                position: c_pos,
                is_organic: true,
            });
            formed += 1;
        }

        formed
    }

    /// Form ammonia: N + 3H -> NH3.
    pub fn form_ammonia(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut formed = 0;

        loop {
            let n_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 7 && a.bonds.is_empty());
            if n_idx.is_none() {
                break;
            }
            let n_idx = n_idx.unwrap();

            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .take(3)
                .collect();
            if h_indices.len() < 3 {
                break;
            }

            let n_id = atoms[n_idx].id;
            let n_pos = atoms[n_idx].position;

            let mut atom_ids = vec![n_id];
            let mut atom_positions = vec![n_pos];
            let mut atom_zs = vec![7u32];
            let mut bonds = Vec::new();

            for (bond_i, &hi) in h_indices.iter().enumerate() {
                let h_id = atoms[hi].id;
                atoms[hi].bonds.push(n_id);
                atoms[n_idx].bonds.push(h_id);
                atom_ids.push(h_id);
                atom_positions.push(atoms[hi].position);
                atom_zs.push(1);
                bonds.push((0, bond_i + 1));
            }

            let mol_id = self.alloc_id();
            self.molecules.push(Molecule {
                id: mol_id,
                name: "ammonia".to_string(),
                formula: "NH3".to_string(),
                atom_ids,
                atom_positions,
                atom_atomic_numbers: atom_zs,
                bonds,
                position: n_pos,
                is_organic: false,
            });
            formed += 1;
        }

        formed
    }

    /// Try forming an amino acid from available atoms.
    /// Requires 2C + 5H + 2O + 1N minimum.
    pub fn form_amino_acid(&mut self, atoms: &mut Vec<Atom>, name: &str) -> bool {
        let c_count = atoms.iter().filter(|a| a.atomic_number == 6 && a.bonds.is_empty()).count();
        let h_count = atoms.iter().filter(|a| a.atomic_number == 1 && a.bonds.is_empty()).count();
        let o_count = atoms.iter().filter(|a| a.atomic_number == 8 && a.bonds.len() < 2).count();
        let n_count = atoms.iter().filter(|a| a.atomic_number == 7 && a.bonds.is_empty()).count();

        if c_count < 2 || h_count < 5 || o_count < 2 || n_count < 1 {
            return false;
        }

        let mut collected_ids = Vec::new();
        let mut collected_pos = Vec::new();
        let mut collected_zs = Vec::new();

        // Collect 2 C
        let needed: &[(u32, usize)] = &[(6, 2), (1, 5), (8, 2), (7, 1)];
        for &(z, count) in needed {
            let mut found = 0;
            for a in atoms.iter() {
                if found >= count {
                    break;
                }
                if a.atomic_number == z && a.bonds.is_empty() && !collected_ids.contains(&a.id) {
                    collected_ids.push(a.id);
                    collected_pos.push(a.position);
                    collected_zs.push(z);
                    found += 1;
                }
            }
        }

        // Mark atoms as bonded (simplified: bond to first atom)
        let first_id = collected_ids[0];
        for a in atoms.iter_mut() {
            if collected_ids.contains(&a.id) && a.id != first_id {
                a.bonds.push(first_id);
            }
            if a.id == first_id {
                for &cid in &collected_ids[1..] {
                    a.bonds.push(cid);
                }
            }
        }

        let center = collected_pos[0];
        let mut bonds = Vec::new();
        for i in 1..collected_ids.len() {
            bonds.push((0, i));
        }

        let mol_id = self.alloc_id();
        self.molecules.push(Molecule {
            id: mol_id,
            name: name.to_string(),
            formula: format!("C2H5NO2({})", name),
            atom_ids: collected_ids,
            atom_positions: collected_pos,
            atom_atomic_numbers: collected_zs,
            bonds,
            position: center,
            is_organic: true,
        });
        self.amino_acid_count += 1;
        self.reactions_occurred += 1;
        true
    }

    /// Try forming a nucleotide from available atoms.
    pub fn form_nucleotide(&mut self, atoms: &mut Vec<Atom>, base: &str) -> bool {
        let c_count = atoms.iter().filter(|a| a.atomic_number == 6 && a.bonds.is_empty()).count();
        let h_count = atoms.iter().filter(|a| a.atomic_number == 1 && a.bonds.is_empty()).count();
        let o_count = atoms.iter().filter(|a| a.atomic_number == 8 && a.bonds.len() < 2).count();
        let n_count = atoms.iter().filter(|a| a.atomic_number == 7 && a.bonds.is_empty()).count();

        if c_count < 5 || h_count < 8 || o_count < 4 || n_count < 2 {
            return false;
        }

        let mut collected_ids = Vec::new();
        let mut collected_pos = Vec::new();
        let mut collected_zs = Vec::new();

        let needed: &[(u32, usize)] = &[(6, 5), (1, 8), (8, 4), (7, 2)];
        for &(z, count) in needed {
            let mut found = 0;
            for a in atoms.iter() {
                if found >= count {
                    break;
                }
                if a.atomic_number == z && a.bonds.is_empty() && !collected_ids.contains(&a.id) {
                    collected_ids.push(a.id);
                    collected_pos.push(a.position);
                    collected_zs.push(z);
                    found += 1;
                }
            }
        }

        let first_id = collected_ids[0];
        for a in atoms.iter_mut() {
            if collected_ids.contains(&a.id) && a.id != first_id {
                a.bonds.push(first_id);
            }
            if a.id == first_id {
                for &cid in &collected_ids[1..] {
                    a.bonds.push(cid);
                }
            }
        }

        let center = collected_pos[0];
        let mut bonds = Vec::new();
        for i in 1..collected_ids.len() {
            bonds.push((0, i));
        }

        let mol_id = self.alloc_id();
        self.molecules.push(Molecule {
            id: mol_id,
            name: format!("nucleotide-{}", base),
            formula: format!("C5H8N2O4({})", base),
            atom_ids: collected_ids,
            atom_positions: collected_pos,
            atom_atomic_numbers: collected_zs,
            bonds,
            position: center,
            is_organic: true,
        });
        self.nucleotide_count += 1;
        self.reactions_occurred += 1;
        true
    }

    /// Catalyzed reactions: form complex molecules.
    pub fn catalyzed_reaction(
        &mut self,
        atoms: &mut Vec<Atom>,
        temperature: f64,
        catalyst_present: bool,
        rng: &mut impl Rng,
    ) -> usize {
        let mut formed = 0;
        let ea_factor = if catalyst_present { 0.3 } else { 1.0 };
        let thermal = K_B * temperature;

        // Try amino acids
        if thermal > 0.0 && atoms.len() > 10 {
            let aa_prob = (-5.0 * ea_factor / (thermal + 1e-20)).exp();
            if rng.gen::<f64>() < aa_prob {
                let aa_names = [
                    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
                    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
                    "Thr", "Trp", "Tyr", "Val",
                ];
                let name = aa_names[rng.gen_range(0..aa_names.len())];
                if self.form_amino_acid(atoms, name) {
                    formed += 1;
                }
            }
        }

        // Try nucleotides
        if thermal > 0.0 && atoms.len() > 19 {
            let nuc_prob = (-8.0 * ea_factor / (thermal + 1e-20)).exp();
            if rng.gen::<f64>() < nuc_prob {
                let bases = ["A", "T", "G", "C"];
                let base = bases[rng.gen_range(0..4)];
                if self.form_nucleotide(atoms, base) {
                    formed += 1;
                }
            }
        }

        formed
    }

    /// Count molecules by name.
    pub fn molecule_census(&self) -> Vec<(String, usize)> {
        use std::collections::HashMap;
        let mut map: HashMap<String, usize> = HashMap::new();
        for mol in &self.molecules {
            *map.entry(mol.name.clone()).or_insert(0) += 1;
        }
        let mut v: Vec<_> = map.into_iter().collect();
        v.sort_by_key(|(name, _)| name.clone());
        v
    }

    pub fn to_compact(&self) -> String {
        let census = self.molecule_census();
        let census_str: String = census
            .iter()
            .map(|(name, count)| format!("{}:{}", name, count))
            .collect::<Vec<_>>()
            .join(",");
        format!(
            "Chem[n={} rx={} {}]",
            self.molecules.len(),
            self.reactions_occurred,
            census_str,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::atomic::Atom;

    fn make_atoms(elements: &[(u32, usize)]) -> Vec<Atom> {
        let mut atoms = Vec::new();
        let mut next_id = 1u32;
        for &(z, count) in elements {
            for _ in 0..count {
                atoms.push(Atom::new(next_id, z, [0.0, 0.0, 0.0]));
                next_id += 1;
            }
        }
        atoms
    }

    // --- Molecule tests ---

    #[test]
    fn test_molecule_render_color_water() {
        let mol = Molecule {
            id: 1,
            name: "water".to_string(),
            formula: "H2O".to_string(),
            atom_ids: vec![1, 2, 3],
            atom_positions: vec![[0.0; 3]; 3],
            atom_atomic_numbers: vec![1, 1, 8],
            bonds: vec![(0, 2), (1, 2)],
            position: [0.0; 3],
            is_organic: false,
        };
        let color = mol.render_color();
        // Water should be blue
        assert!(color[2] > color[0], "Water should be more blue than red");
    }

    #[test]
    fn test_molecule_render_color_organic() {
        let mol = Molecule {
            id: 1,
            name: "methane".to_string(),
            formula: "CH4".to_string(),
            atom_ids: vec![],
            atom_positions: vec![],
            atom_atomic_numbers: vec![],
            bonds: vec![],
            position: [0.0; 3],
            is_organic: true,
        };
        let color = mol.render_color();
        // Organic should be green
        assert!(color[1] > color[0], "Organic should be more green than red");
    }

    // --- ChemicalSystem tests ---

    #[test]
    fn test_chemical_system_new() {
        let cs = ChemicalSystem::new();
        assert!(cs.molecules.is_empty());
        assert_eq!(cs.water_count, 0);
        assert_eq!(cs.amino_acid_count, 0);
        assert_eq!(cs.nucleotide_count, 0);
        assert_eq!(cs.reactions_occurred, 0);
    }

    #[test]
    fn test_form_water() {
        let mut cs = ChemicalSystem::new();
        // 2 H + 1 O -> H2O
        let mut atoms = make_atoms(&[(1, 4), (8, 2)]);
        let formed = cs.form_water(&mut atoms);
        assert_eq!(formed, 2);
        assert_eq!(cs.water_count, 2);
        assert_eq!(cs.molecules.len(), 2);
        assert_eq!(cs.molecules[0].name, "water");
        assert_eq!(cs.molecules[0].formula, "H2O");
        assert!(!cs.molecules[0].is_organic);
    }

    #[test]
    fn test_form_water_insufficient() {
        let mut cs = ChemicalSystem::new();
        // 1 H + 1 O: not enough hydrogen
        let mut atoms = make_atoms(&[(1, 1), (8, 1)]);
        let formed = cs.form_water(&mut atoms);
        assert_eq!(formed, 0);
    }

    #[test]
    fn test_form_methane() {
        let mut cs = ChemicalSystem::new();
        // 1 C + 4 H -> CH4
        let mut atoms = make_atoms(&[(6, 1), (1, 4)]);
        let formed = cs.form_methane(&mut atoms);
        assert_eq!(formed, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert_eq!(cs.molecules[0].name, "methane");
        assert_eq!(cs.molecules[0].formula, "CH4");
        assert!(cs.molecules[0].is_organic);
    }

    #[test]
    fn test_form_methane_insufficient() {
        let mut cs = ChemicalSystem::new();
        // 1 C + 3 H: not enough hydrogen
        let mut atoms = make_atoms(&[(6, 1), (1, 3)]);
        let formed = cs.form_methane(&mut atoms);
        assert_eq!(formed, 0);
    }

    #[test]
    fn test_form_ammonia() {
        let mut cs = ChemicalSystem::new();
        // 1 N + 3 H -> NH3
        let mut atoms = make_atoms(&[(7, 1), (1, 3)]);
        let formed = cs.form_ammonia(&mut atoms);
        assert_eq!(formed, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert_eq!(cs.molecules[0].name, "ammonia");
        assert_eq!(cs.molecules[0].formula, "NH3");
    }

    #[test]
    fn test_form_amino_acid() {
        let mut cs = ChemicalSystem::new();
        // Needs: 2C + 5H + 2O + 1N
        let mut atoms = make_atoms(&[(6, 2), (1, 5), (8, 2), (7, 1)]);
        let result = cs.form_amino_acid(&mut atoms, "Gly");
        assert!(result);
        assert_eq!(cs.amino_acid_count, 1);
        assert_eq!(cs.reactions_occurred, 1);
        assert!(cs.molecules[0].is_organic);
    }

    #[test]
    fn test_form_amino_acid_insufficient() {
        let mut cs = ChemicalSystem::new();
        // Missing nitrogen
        let mut atoms = make_atoms(&[(6, 2), (1, 5), (8, 2)]);
        let result = cs.form_amino_acid(&mut atoms, "Gly");
        assert!(!result);
        assert_eq!(cs.amino_acid_count, 0);
    }

    #[test]
    fn test_form_nucleotide() {
        let mut cs = ChemicalSystem::new();
        // Needs: 5C + 8H + 4O + 2N
        let mut atoms = make_atoms(&[(6, 5), (1, 8), (8, 4), (7, 2)]);
        let result = cs.form_nucleotide(&mut atoms, "A");
        assert!(result);
        assert_eq!(cs.nucleotide_count, 1);
        assert_eq!(cs.reactions_occurred, 1);
        assert!(cs.molecules[0].is_organic);
        assert!(cs.molecules[0].name.contains("nucleotide"));
    }

    #[test]
    fn test_form_nucleotide_insufficient() {
        let mut cs = ChemicalSystem::new();
        // Not enough atoms
        let mut atoms = make_atoms(&[(6, 3), (1, 4), (8, 2), (7, 1)]);
        let result = cs.form_nucleotide(&mut atoms, "G");
        assert!(!result);
        assert_eq!(cs.nucleotide_count, 0);
    }

    #[test]
    fn test_multiple_molecule_formation() {
        let mut cs = ChemicalSystem::new();
        // Enough for 2 water + 1 methane
        let mut atoms = make_atoms(&[(1, 8), (8, 2), (6, 1)]);
        let water_formed = cs.form_water(&mut atoms);
        let methane_formed = cs.form_methane(&mut atoms);
        assert_eq!(water_formed, 2);
        assert_eq!(methane_formed, 1);
        assert_eq!(cs.molecules.len(), 3);
    }

    #[test]
    fn test_molecule_render_color_default() {
        let mol = Molecule {
            id: 1,
            name: "salt".to_string(),
            formula: "NaCl".to_string(),
            atom_ids: vec![1, 2],
            atom_positions: vec![[0.0; 3]; 2],
            atom_atomic_numbers: vec![11, 17],
            bonds: vec![(0, 1)],
            position: [0.0; 3],
            is_organic: false,
        };
        let color = mol.render_color();
        assert_eq!(color.len(), 4);
        // Default color: gray-ish
        assert!(color[3] > 0.0, "Alpha should be positive");
    }

    #[test]
    fn test_catalyzed_reaction_with_atoms() {
        use rand::rngs::SmallRng;
        use rand::SeedableRng;

        let mut rng = SmallRng::seed_from_u64(42);
        let mut cs = ChemicalSystem::new();
        // Add plenty of atoms for amino acid and nucleotide formation
        // Needs: 2C + 5H + 2O + 1N for amino acid
        let mut atoms = make_atoms(&[(6, 20), (1, 40), (8, 20), (7, 10)]);
        let mut total = 0;
        for _ in 0..200 {
            total += cs.catalyzed_reaction(&mut atoms, 5000.0, true, &mut rng);
        }
        assert!(total > 0, "Catalyzed reaction should produce at least 1 product over 200 tries");
    }

    #[test]
    fn test_catalyzed_reaction_low_temp() {
        use rand::rngs::SmallRng;
        use rand::SeedableRng;

        let mut rng = SmallRng::seed_from_u64(42);
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 10), (1, 20), (8, 10), (7, 5)]);
        // At very low temperature, thermal energy K_B * T is tiny so exp(-X/tiny) -> 0
        let formed = cs.catalyzed_reaction(&mut atoms, 0.0001, false, &mut rng);
        assert_eq!(formed, 0, "No products should form at near-zero temperature");
    }

    #[test]
    fn test_form_ammonia_insufficient() {
        let mut cs = ChemicalSystem::new();
        // 1 N + 2 H: not enough hydrogen
        let mut atoms = make_atoms(&[(7, 1), (1, 2)]);
        let formed = cs.form_ammonia(&mut atoms);
        assert_eq!(formed, 0);
    }
}
