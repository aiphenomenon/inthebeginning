//! Chemistry simulation -- molecular assembly and reactions.
//!
//! Models formation of molecules from atoms: water, amino acids,
//! nucleotides, and other biomolecules essential for life.
//! Chemical reactions are driven by energy, catalysis, and concentration.

use rand::Rng;
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};

use super::atomic::Atom;
use super::constants::*;

static MOLECULE_ID_COUNTER: AtomicU64 = AtomicU64::new(0);

fn next_molecule_id() -> u64 {
    MOLECULE_ID_COUNTER.fetch_add(1, Ordering::Relaxed) + 1
}

// ---------------------------------------------------------------------------
// Molecule
// ---------------------------------------------------------------------------

/// A molecule: a collection of bonded atoms.
#[derive(Debug, Clone)]
pub struct Molecule {
    /// Atom IDs that form this molecule
    pub atom_ids: Vec<u64>,
    pub name: String,
    pub formula: String,
    pub molecule_id: u64,
    pub energy: f64,
    pub position: [f64; 3],
    pub is_organic: bool,
    pub functional_groups: Vec<String>,
    pub molecular_weight: f64,
}

impl Molecule {
    pub fn new(name: &str, atom_ids: Vec<u64>, position: [f64; 3], mw: f64) -> Self {
        Self {
            atom_ids,
            name: name.to_string(),
            formula: String::new(),
            molecule_id: next_molecule_id(),
            energy: 0.0,
            position,
            is_organic: false,
            functional_groups: Vec::new(),
            molecular_weight: mw,
        }
    }

    pub fn with_formula(mut self, formula: &str) -> Self {
        self.formula = formula.to_string();
        self
    }

    pub fn with_organic(mut self, organic: bool) -> Self {
        self.is_organic = organic;
        self
    }

    pub fn with_functional_groups(mut self, groups: Vec<&str>) -> Self {
        self.functional_groups = groups.into_iter().map(String::from).collect();
        self
    }

    pub fn atom_count(&self) -> usize {
        self.atom_ids.len()
    }
}

// ---------------------------------------------------------------------------
// ChemicalSystem
// ---------------------------------------------------------------------------

/// Manages molecular assembly and chemical reactions.
pub struct ChemicalSystem {
    pub molecules: Vec<Molecule>,
    pub reactions_occurred: u64,
    pub water_count: u64,
    pub amino_acid_count: u64,
    pub nucleotide_count: u64,
}

impl ChemicalSystem {
    pub fn new() -> Self {
        Self {
            molecules: Vec::new(),
            reactions_occurred: 0,
            water_count: 0,
            amino_acid_count: 0,
            nucleotide_count: 0,
        }
    }

    /// Form water molecules: 2H + O -> H2O.
    /// Returns the number of water molecules formed.
    pub fn form_water(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut count = 0;

        loop {
            // Find two unbonded H and one O with fewer than 2 bonds
            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .collect();
            let o_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 8 && a.bonds.len() < 2);

            if h_indices.len() < 2 || o_idx.is_none() {
                break;
            }

            let oi = o_idx.unwrap();
            let h1i = h_indices[0];
            let h2i = h_indices[1];

            let pos = atoms[oi].position;
            let o_id = atoms[oi].atom_id;
            let h1_id = atoms[h1i].atom_id;
            let h2_id = atoms[h2i].atom_id;

            // Form bonds
            atoms[h1i].bonds.push(o_id);
            atoms[h2i].bonds.push(o_id);
            atoms[oi].bonds.push(h1_id);
            atoms[oi].bonds.push(h2_id);

            let water = Molecule::new("water", vec![h1_id, h2_id, o_id], pos, 18.0)
                .with_formula("H2O");
            self.molecules.push(water);
            self.water_count += 1;
            count += 1;
        }

        count
    }

    /// Form methane: C + 4H -> CH4.
    pub fn form_methane(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut count = 0;

        loop {
            let c_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 6 && a.bonds.is_empty());
            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .collect();

            if c_idx.is_none() || h_indices.len() < 4 {
                break;
            }

            let ci = c_idx.unwrap();
            let his: Vec<usize> = h_indices[..4].to_vec();

            let pos = atoms[ci].position;
            let c_id = atoms[ci].atom_id;
            let mut atom_ids = vec![c_id];

            for &hi in &his {
                let h_id = atoms[hi].atom_id;
                atoms[hi].bonds.push(c_id);
                atoms[ci].bonds.push(h_id);
                atom_ids.push(h_id);
            }

            let methane = Molecule::new("methane", atom_ids, pos, 16.0)
                .with_formula("CH4");
            self.molecules.push(methane);
            count += 1;
        }

        count
    }

    /// Form ammonia: N + 3H -> NH3.
    pub fn form_ammonia(&mut self, atoms: &mut Vec<Atom>) -> usize {
        let mut count = 0;

        loop {
            let n_idx = atoms
                .iter()
                .position(|a| a.atomic_number == 7 && a.bonds.is_empty());
            let h_indices: Vec<usize> = atoms
                .iter()
                .enumerate()
                .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
                .map(|(i, _)| i)
                .collect();

            if n_idx.is_none() || h_indices.len() < 3 {
                break;
            }

            let ni = n_idx.unwrap();
            let his: Vec<usize> = h_indices[..3].to_vec();

            let pos = atoms[ni].position;
            let n_id = atoms[ni].atom_id;
            let mut atom_ids = vec![n_id];

            for &hi in &his {
                let h_id = atoms[hi].atom_id;
                atoms[hi].bonds.push(n_id);
                atoms[ni].bonds.push(h_id);
                atom_ids.push(h_id);
            }

            let ammonia = Molecule::new("ammonia", atom_ids, pos, 17.0)
                .with_formula("NH3");
            self.molecules.push(ammonia);
            count += 1;
        }

        count
    }

    /// Form an amino acid from available atoms.
    /// Simplified: requires 2C + 5H + 2O + 1N minimum (glycine).
    pub fn form_amino_acid(&mut self, atoms: &mut Vec<Atom>, aa_type: &str) -> bool {
        let carbons: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 6 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();
        let hydrogens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();
        let oxygens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 8 && a.bonds.len() < 2)
            .map(|(i, _)| i)
            .collect();
        let nitrogens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 7 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();

        if carbons.len() < 2 || hydrogens.len() < 5 || oxygens.len() < 2 || nitrogens.is_empty() {
            return false;
        }

        let pos = atoms[carbons[0]].position;
        let anchor_id = atoms[carbons[0]].atom_id;

        // Collect atom IDs and form bonds
        let mut atom_ids = Vec::new();
        let all_indices: Vec<usize> = carbons[..2]
            .iter()
            .chain(hydrogens[..5].iter())
            .chain(oxygens[..2].iter())
            .chain(nitrogens[..1].iter())
            .copied()
            .collect();

        for &idx in &all_indices {
            let aid = atoms[idx].atom_id;
            atom_ids.push(aid);
            if aid != anchor_id {
                atoms[idx].bonds.push(anchor_id);
                atoms[carbons[0]].bonds.push(aid);
            }
        }

        let aa = Molecule::new(aa_type, atom_ids, pos, 75.0)
            .with_organic(true)
            .with_functional_groups(vec!["amino", "carboxyl"]);
        self.molecules.push(aa);
        self.amino_acid_count += 1;
        true
    }

    /// Form a nucleotide (sugar + phosphate + base).
    /// Simplified: requires C5 + H8 + O4 + N2 minimum.
    pub fn form_nucleotide(&mut self, atoms: &mut Vec<Atom>, base: &str) -> bool {
        let carbons: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 6 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();
        let hydrogens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 1 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();
        let oxygens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 8 && a.bonds.len() < 2)
            .map(|(i, _)| i)
            .collect();
        let nitrogens: Vec<usize> = atoms
            .iter()
            .enumerate()
            .filter(|(_, a)| a.atomic_number == 7 && a.bonds.is_empty())
            .map(|(i, _)| i)
            .collect();

        if carbons.len() < 5 || hydrogens.len() < 8 || oxygens.len() < 4 || nitrogens.len() < 2 {
            return false;
        }

        let pos = atoms[carbons[0]].position;
        let anchor_id = atoms[carbons[0]].atom_id;

        let mut atom_ids = Vec::new();
        let all_indices: Vec<usize> = carbons[..5]
            .iter()
            .chain(hydrogens[..8].iter())
            .chain(oxygens[..4].iter())
            .chain(nitrogens[..2].iter())
            .copied()
            .collect();

        for &idx in &all_indices {
            let aid = atoms[idx].atom_id;
            atom_ids.push(aid);
            if aid != anchor_id {
                atoms[idx].bonds.push(anchor_id);
                atoms[carbons[0]].bonds.push(aid);
            }
        }

        let name = format!("nucleotide-{}", base);
        let nuc = Molecule::new(&name, atom_ids, pos, 330.0)
            .with_organic(true)
            .with_functional_groups(vec!["sugar", "phosphate", "base"]);
        self.molecules.push(nuc);
        self.nucleotide_count += 1;
        true
    }

    /// Run catalyzed reactions to form complex molecules.
    pub fn catalyzed_reaction(
        &mut self,
        atoms: &mut Vec<Atom>,
        temperature: f64,
        catalyst_present: bool,
    ) -> u64 {
        let mut formed: u64 = 0;
        let ea_factor = if catalyst_present { 0.3 } else { 1.0 };
        let thermal = K_B * temperature;
        let mut rng = rand::thread_rng();

        // Try to form amino acids
        if thermal > 0.0 && atoms.len() > 10 {
            let aa_prob = (-5.0 * ea_factor / (thermal + 1e-20)).exp();
            if rng.gen::<f64>() < aa_prob {
                let idx = rng.gen_range(0..AMINO_ACIDS.len());
                let aa_type = AMINO_ACIDS[idx];
                if self.form_amino_acid(atoms, aa_type) {
                    formed += 1;
                    self.reactions_occurred += 1;
                }
            }
        }

        // Try to form nucleotides
        if thermal > 0.0 && atoms.len() > 19 {
            let nuc_prob = (-8.0 * ea_factor / (thermal + 1e-20)).exp();
            if rng.gen::<f64>() < nuc_prob {
                let bases = ['A', 'T', 'G', 'C'];
                let base = bases[rng.gen_range(0..4)];
                if self.form_nucleotide(atoms, &base.to_string()) {
                    formed += 1;
                    self.reactions_occurred += 1;
                }
            }
        }

        formed
    }

    /// Count molecules by type.
    pub fn molecule_census(&self) -> HashMap<String, usize> {
        let mut counts = HashMap::new();
        for m in &self.molecules {
            let key = if m.name.is_empty() {
                m.formula.clone()
            } else {
                m.name.clone()
            };
            *counts.entry(key).or_insert(0) += 1;
        }
        counts
    }

    pub fn to_compact(&self) -> String {
        let counts = self.molecule_census();
        let mut parts: Vec<String> = counts
            .iter()
            .map(|(k, v)| format!("{}:{}", k, v))
            .collect();
        parts.sort();
        format!(
            "CS[mol={} H2O={} aa={} nuc={} rxn={} {}]",
            self.molecules.len(),
            self.water_count,
            self.amino_acid_count,
            self.nucleotide_count,
            self.reactions_occurred,
            parts.join(",")
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Helper: create a set of unbonded atoms of the given elements.
    fn make_atoms(elements: &[(u32, usize)]) -> Vec<Atom> {
        let mut atoms = Vec::new();
        for &(z, count) in elements {
            for _ in 0..count {
                atoms.push(Atom::new(z));
            }
        }
        atoms
    }

    // -----------------------------------------------------------------------
    // Molecule
    // -----------------------------------------------------------------------

    /// New molecule has correct name and atom count.
    #[test]
    fn molecule_new() {
        let mol = Molecule::new("water", vec![1, 2, 3], [0.0; 3], 18.0);
        assert_eq!(mol.name, "water");
        assert_eq!(mol.atom_count(), 3);
        assert_eq!(mol.molecular_weight, 18.0);
    }

    /// Builder methods chain correctly.
    #[test]
    fn molecule_builder() {
        let mol = Molecule::new("test", vec![1], [0.0; 3], 10.0)
            .with_formula("X2")
            .with_organic(true)
            .with_functional_groups(vec!["amino", "carboxyl"]);
        assert_eq!(mol.formula, "X2");
        assert!(mol.is_organic);
        assert_eq!(mol.functional_groups.len(), 2);
    }

    /// Molecule IDs are unique.
    #[test]
    fn molecule_ids_unique() {
        let m1 = Molecule::new("a", vec![1], [0.0; 3], 1.0);
        let m2 = Molecule::new("b", vec![2], [0.0; 3], 2.0);
        assert_ne!(m1.molecule_id, m2.molecule_id);
    }

    // -----------------------------------------------------------------------
    // ChemicalSystem
    // -----------------------------------------------------------------------

    /// New ChemicalSystem is empty.
    #[test]
    fn chemical_system_new_empty() {
        let cs = ChemicalSystem::new();
        assert_eq!(cs.molecules.len(), 0);
        assert_eq!(cs.water_count, 0);
        assert_eq!(cs.amino_acid_count, 0);
        assert_eq!(cs.nucleotide_count, 0);
        assert_eq!(cs.reactions_occurred, 0);
    }

    /// form_water creates water from 2H + O.
    #[test]
    fn form_water_basic() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 4), (8, 2)]); // 4H + 2O => 2 H2O
        let count = cs.form_water(&mut atoms);
        assert_eq!(count, 2);
        assert_eq!(cs.water_count, 2);
        assert_eq!(cs.molecules.len(), 2);
        assert_eq!(cs.molecules[0].name, "water");
        assert_eq!(cs.molecules[0].formula, "H2O");
    }

    /// form_water returns 0 when insufficient atoms.
    #[test]
    fn form_water_insufficient_hydrogen() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 1), (8, 1)]); // only 1H
        let count = cs.form_water(&mut atoms);
        assert_eq!(count, 0);
    }

    /// form_water returns 0 when no oxygen available.
    #[test]
    fn form_water_no_oxygen() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 10)]);
        let count = cs.form_water(&mut atoms);
        assert_eq!(count, 0);
    }

    /// form_water does not consume bonded hydrogen atoms.
    #[test]
    fn form_water_skips_bonded_atoms() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 2), (8, 1)]);
        // Bond one hydrogen
        atoms[0].bonds.push(999);
        let count = cs.form_water(&mut atoms);
        // Only 1 unbonded H available, need 2
        assert_eq!(count, 0);
    }

    /// form_methane creates CH4 from C + 4H.
    #[test]
    fn form_methane_basic() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 1), (1, 4)]); // C + 4H
        let count = cs.form_methane(&mut atoms);
        assert_eq!(count, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert_eq!(cs.molecules[0].formula, "CH4");
    }

    /// form_methane needs at least 4 unbonded hydrogens.
    #[test]
    fn form_methane_insufficient_hydrogen() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 1), (1, 3)]); // only 3H
        let count = cs.form_methane(&mut atoms);
        assert_eq!(count, 0);
    }

    /// form_ammonia creates NH3 from N + 3H.
    #[test]
    fn form_ammonia_basic() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(7, 1), (1, 3)]); // N + 3H
        let count = cs.form_ammonia(&mut atoms);
        assert_eq!(count, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert_eq!(cs.molecules[0].formula, "NH3");
    }

    /// form_ammonia returns 0 when insufficient atoms.
    #[test]
    fn form_ammonia_insufficient() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(7, 1), (1, 2)]); // only 2H
        let count = cs.form_ammonia(&mut atoms);
        assert_eq!(count, 0);
    }

    /// form_amino_acid needs 2C + 5H + 2O + 1N minimum.
    #[test]
    fn form_amino_acid_success() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 2), (1, 5), (8, 2), (7, 1)]);
        let result = cs.form_amino_acid(&mut atoms, "Gly");
        assert!(result);
        assert_eq!(cs.amino_acid_count, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert!(cs.molecules[0].is_organic);
        assert!(cs.molecules[0].functional_groups.contains(&"amino".to_string()));
    }

    /// form_amino_acid fails with insufficient carbons.
    #[test]
    fn form_amino_acid_insufficient_carbon() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 1), (1, 5), (8, 2), (7, 1)]);
        let result = cs.form_amino_acid(&mut atoms, "Gly");
        assert!(!result);
        assert_eq!(cs.amino_acid_count, 0);
    }

    /// form_nucleotide needs 5C + 8H + 4O + 2N minimum.
    #[test]
    fn form_nucleotide_success() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 5), (1, 8), (8, 4), (7, 2)]);
        let result = cs.form_nucleotide(&mut atoms, "A");
        assert!(result);
        assert_eq!(cs.nucleotide_count, 1);
        assert_eq!(cs.molecules.len(), 1);
        assert!(cs.molecules[0].name.contains("nucleotide"));
        assert!(cs.molecules[0].is_organic);
    }

    /// form_nucleotide fails with insufficient nitrogen.
    #[test]
    fn form_nucleotide_insufficient_nitrogen() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 5), (1, 8), (8, 4), (7, 1)]); // only 1 N
        let result = cs.form_nucleotide(&mut atoms, "A");
        assert!(!result);
    }

    /// molecule_census counts molecules by type.
    #[test]
    fn molecule_census_counts() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 4), (8, 2)]);
        cs.form_water(&mut atoms);
        let census = cs.molecule_census();
        assert_eq!(*census.get("water").unwrap(), 2);
    }

    /// Compact representation includes molecule counts.
    #[test]
    fn chemical_system_compact() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 2), (8, 1)]);
        cs.form_water(&mut atoms);
        let compact = cs.to_compact();
        assert!(compact.starts_with("CS["));
        assert!(compact.contains("H2O=1"));
    }

    /// Multiple molecule types can coexist.
    #[test]
    fn multiple_molecule_types() {
        let mut cs = ChemicalSystem::new();
        // 2H + O for water, C + 4H for methane, N + 3H for ammonia
        let mut atoms = make_atoms(&[(1, 9), (8, 1), (6, 1), (7, 1)]);
        let water = cs.form_water(&mut atoms);
        let methane = cs.form_methane(&mut atoms);
        let ammonia = cs.form_ammonia(&mut atoms);
        assert_eq!(water, 1);
        assert_eq!(methane, 1);
        assert_eq!(ammonia, 1);
        assert_eq!(cs.molecules.len(), 3);
    }

    // -----------------------------------------------------------------------
    // ChemicalSystem::catalyzed_reaction
    // -----------------------------------------------------------------------

    /// Catalyzed reaction with insufficient atoms produces nothing.
    #[test]
    fn catalyzed_reaction_insufficient_atoms() {
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(1, 2)]); // only 2 hydrogen, not enough for anything
        let formed = cs.catalyzed_reaction(&mut atoms, 300.0, true);
        assert_eq!(formed, 0);
    }

    /// Catalyzed reaction with zero temperature produces nothing.
    #[test]
    fn catalyzed_reaction_zero_temp() {
        let mut cs = ChemicalSystem::new();
        // Plenty of atoms for amino acid (2C + 5H + 2O + 1N)
        let mut atoms = make_atoms(&[(6, 10), (1, 50), (8, 10), (7, 10)]);
        let formed = cs.catalyzed_reaction(&mut atoms, 0.0, true);
        // thermal = K_B * 0 = 0, so condition thermal > 0 fails
        assert_eq!(formed, 0);
    }

    /// Catalyzed reaction with catalyst can form amino acids or nucleotides.
    #[test]
    fn catalyzed_reaction_with_catalyst_produces_molecules() {
        // With a catalyst, the activation energy factor is 0.3 (lower barrier).
        // At high temperature, exp(-5 * 0.3 / (K_B * T)) approaches 1.
        // We need lots of atoms (>10 for amino acid, >19 for nucleotide).
        let mut total_formed = 0u64;
        for _ in 0..100 {
            let mut cs = ChemicalSystem::new();
            // Provide plentiful CHON atoms
            let mut atoms = make_atoms(&[(6, 20), (1, 80), (8, 20), (7, 20)]);
            let formed = cs.catalyzed_reaction(&mut atoms, 1e6, true);
            total_formed += formed;
            if total_formed > 0 {
                break;
            }
        }
        assert!(total_formed > 0,
            "catalyzed reaction with catalyst at high temp should eventually produce molecules");
    }

    /// Catalyzed reaction without catalyst has a higher activation barrier.
    #[test]
    fn catalyzed_reaction_without_catalyst() {
        // Without catalyst, ea_factor = 1.0 (full barrier).
        // At moderate temperature the probability is lower.
        let mut cs = ChemicalSystem::new();
        let mut atoms = make_atoms(&[(6, 20), (1, 80), (8, 20), (7, 20)]);
        // At very high temperature, even without catalyst, reactions should occur.
        let mut total_formed = 0u64;
        for _ in 0..100 {
            let formed = cs.catalyzed_reaction(&mut atoms, 1e8, false);
            total_formed += formed;
            if total_formed > 0 {
                break;
            }
        }
        // At extreme temperature, reactions should eventually happen
        assert!(total_formed > 0,
            "catalyzed reaction without catalyst at extreme temp should produce molecules");
    }

    /// Catalyzed reaction increments reactions_occurred.
    #[test]
    fn catalyzed_reaction_increments_counter() {
        let mut total_reactions = 0u64;
        for _ in 0..200 {
            let mut cs = ChemicalSystem::new();
            let mut atoms = make_atoms(&[(6, 20), (1, 80), (8, 20), (7, 20)]);
            cs.catalyzed_reaction(&mut atoms, 1e6, true);
            total_reactions += cs.reactions_occurred;
            if total_reactions > 0 {
                break;
            }
        }
        assert!(total_reactions > 0,
            "catalyzed reaction should increment reactions_occurred");
    }
}
