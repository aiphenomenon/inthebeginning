//! Chemistry simulation -- molecular assembly and reactions.
//!
//! Models formation of molecules from atoms: water, amino acids,
//! nucleotides, and other biomolecules essential for life.
//! Chemical reactions are driven by energy, catalysis, and concentration.

use rand::Rng;
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};

use super::atomic::{Atom, AtomicSystem};
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
