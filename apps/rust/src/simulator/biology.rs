//! Biological systems simulation.
//!
//! Models DNA replication, mutation, protein synthesis, lifeforms with traits,
//! natural selection, and population dynamics. Emerges from the chemical
//! substrate once nucleotides and amino acids are available.

use rand::Rng;
use std::collections::HashMap;

use super::constants::*;
use super::chemistry::ChemicalSystem;

// ---------------------------------------------------------------------------
// DNA / Genome
// ---------------------------------------------------------------------------

/// A strand of DNA represented as a sequence of nucleotide bases.
#[derive(Debug, Clone)]
pub struct Genome {
    pub bases: Vec<char>,
    pub methylation: Vec<bool>,
    pub generation: u64,
}

impl Genome {
    /// Create a random genome of the given length.
    pub fn random(length: usize) -> Self {
        let mut rng = rand::thread_rng();
        let bases: Vec<char> = (0..length)
            .map(|_| NUCLEOTIDE_BASES[rng.gen_range(0..4)])
            .collect();
        let methylation = vec![false; length];
        Self {
            bases,
            methylation,
            generation: 0,
        }
    }

    /// Transcribe DNA to RNA (T -> U).
    pub fn transcribe(&self) -> Vec<char> {
        self.bases
            .iter()
            .map(|&b| if b == 'T' { 'U' } else { b })
            .collect()
    }

    /// Translate RNA into a protein (sequence of amino acid names).
    pub fn translate(&self) -> Vec<&'static str> {
        let rna = self.transcribe();
        let mut protein = Vec::new();
        let mut i = 0;

        // Scan for start codon AUG
        while i + 2 < rna.len() {
            let codon: String = rna[i..i + 3].iter().collect();
            if codon == "AUG" {
                break;
            }
            i += 1;
        }

        // Translate codons
        while i + 2 < rna.len() {
            let codon: String = rna[i..i + 3].iter().collect();
            match codon_to_amino_acid(&codon) {
                Some("STOP") => break,
                Some(aa) => protein.push(aa),
                None => {}
            }
            i += 3;
        }

        protein
    }

    /// Mutate the genome with a given mutation rate per base.
    pub fn mutate(&mut self, mutation_rate: f64) {
        let mut rng = rand::thread_rng();
        for i in 0..self.bases.len() {
            // Methylated bases have reduced mutation rate
            let effective_rate = if self.methylation[i] {
                mutation_rate * 0.1
            } else {
                mutation_rate
            };

            if rng.gen::<f64>() < effective_rate {
                // Point mutation
                let new_base = NUCLEOTIDE_BASES[rng.gen_range(0..4)];
                self.bases[i] = new_base;
            }
        }

        // Epigenetic changes: methylation / demethylation
        for i in 0..self.methylation.len() {
            if !self.methylation[i] && rng.gen::<f64>() < METHYLATION_PROBABILITY {
                self.methylation[i] = true;
            } else if self.methylation[i] && rng.gen::<f64>() < DEMETHYLATION_PROBABILITY {
                self.methylation[i] = false;
            }
        }
    }

    /// Replicate with possible errors.
    pub fn replicate(&self, error_rate: f64) -> Self {
        let mut child = self.clone();
        child.generation = self.generation + 1;
        child.mutate(error_rate);
        child
    }

    /// Count occurrences of each base.
    pub fn base_composition(&self) -> HashMap<char, usize> {
        let mut counts = HashMap::new();
        for &b in &self.bases {
            *counts.entry(b).or_insert(0) += 1;
        }
        counts
    }

    /// GC content as a fraction.
    pub fn gc_content(&self) -> f64 {
        let gc = self.bases.iter().filter(|&&b| b == 'G' || b == 'C').count();
        gc as f64 / self.bases.len().max(1) as f64
    }

    /// Fraction of methylated bases.
    pub fn methylation_level(&self) -> f64 {
        let m = self.methylation.iter().filter(|&&x| x).count();
        m as f64 / self.methylation.len().max(1) as f64
    }

    pub fn len(&self) -> usize {
        self.bases.len()
    }
}

// ---------------------------------------------------------------------------
// Trait / Phenotype
// ---------------------------------------------------------------------------

/// A phenotypic trait derived from the genome.
#[derive(Debug, Clone)]
pub struct Trait {
    pub name: String,
    pub value: f64,
}

/// Decode traits from a genome. Uses simple hashing of subsequences.
pub fn decode_traits(genome: &Genome) -> Vec<Trait> {
    let mut traits = Vec::new();
    let len = genome.len();
    if len < 12 {
        return traits;
    }

    // Heat resistance: encoded by first 12 bases
    let heat_val: f64 = genome.bases[..12]
        .iter()
        .enumerate()
        .map(|(i, &b)| {
            let v = match b {
                'A' => 0.0,
                'T' => 1.0,
                'G' => 2.0,
                'C' => 3.0,
                _ => 0.0,
            };
            v / 4.0_f64.powi(i as i32 + 1)
        })
        .sum();
    traits.push(Trait {
        name: "heat_resistance".to_string(),
        value: heat_val.min(1.0),
    });

    // Metabolic efficiency: next 12 bases
    if len >= 24 {
        let met_val: f64 = genome.bases[12..24]
            .iter()
            .enumerate()
            .map(|(i, &b)| {
                let v = match b {
                    'A' => 0.0,
                    'T' => 1.0,
                    'G' => 2.0,
                    'C' => 3.0,
                    _ => 0.0,
                };
                v / 4.0_f64.powi(i as i32 + 1)
            })
            .sum();
        traits.push(Trait {
            name: "metabolic_efficiency".to_string(),
            value: met_val.min(1.0),
        });
    }

    // Reproduction rate: next 12 bases
    if len >= 36 {
        let rep_val: f64 = genome.bases[24..36]
            .iter()
            .enumerate()
            .map(|(i, &b)| {
                let v = match b {
                    'A' => 0.0,
                    'T' => 1.0,
                    'G' => 2.0,
                    'C' => 3.0,
                    _ => 0.0,
                };
                v / 4.0_f64.powi(i as i32 + 1)
            })
            .sum();
        traits.push(Trait {
            name: "reproduction_rate".to_string(),
            value: rep_val.min(1.0),
        });
    }

    traits
}

// ---------------------------------------------------------------------------
// Lifeform
// ---------------------------------------------------------------------------

/// A single lifeform with a genome and fitness.
#[derive(Debug, Clone)]
pub struct Lifeform {
    pub genome: Genome,
    pub traits: Vec<Trait>,
    pub fitness: f64,
    pub energy: f64,
    pub age: u64,
    pub alive: bool,
    pub species_id: u64,
}

static SPECIES_COUNTER: std::sync::atomic::AtomicU64 =
    std::sync::atomic::AtomicU64::new(0);

fn next_species_id() -> u64 {
    SPECIES_COUNTER.fetch_add(1, std::sync::atomic::Ordering::Relaxed) + 1
}

impl Lifeform {
    /// Create a new lifeform with a random genome.
    pub fn new(genome_length: usize) -> Self {
        let genome = Genome::random(genome_length);
        let traits = decode_traits(&genome);
        Self {
            genome,
            traits,
            fitness: 0.5,
            energy: 100.0,
            age: 0,
            alive: true,
            species_id: next_species_id(),
        }
    }

    /// Create a lifeform from an existing genome.
    pub fn from_genome(genome: Genome) -> Self {
        let traits = decode_traits(&genome);
        Self {
            genome,
            traits,
            fitness: 0.5,
            energy: 100.0,
            age: 0,
            alive: true,
            species_id: next_species_id(),
        }
    }

    /// Get a trait value by name, defaulting to 0.5.
    pub fn trait_value(&self, name: &str) -> f64 {
        self.traits
            .iter()
            .find(|t| t.name == name)
            .map(|t| t.value)
            .unwrap_or(0.5)
    }

    /// Evaluate fitness against environmental pressures.
    pub fn evaluate_fitness(&mut self, temperature: f64, resources: f64) {
        let heat_res = self.trait_value("heat_resistance");
        let metabolism = self.trait_value("metabolic_efficiency");

        // Temperature fitness: penalty for extreme temps
        let optimal_temp = 288.0 + heat_res * 100.0; // 288K - 388K range
        let temp_diff = (temperature - optimal_temp).abs();
        let temp_fitness = (-temp_diff / 200.0).exp();

        // Resource fitness
        let resource_fitness = (resources * metabolism).min(1.0);

        self.fitness = (temp_fitness * 0.5 + resource_fitness * 0.5).max(0.0).min(1.0);
    }

    /// Age and consume energy. Returns false if the lifeform dies.
    pub fn tick(&mut self) -> bool {
        if !self.alive {
            return false;
        }

        self.age += 1;
        let metabolism = self.trait_value("metabolic_efficiency");
        let energy_cost = 1.0 + (1.0 - metabolism) * 2.0;
        self.energy -= energy_cost;

        if self.energy <= 0.0 || self.fitness < 0.01 {
            self.alive = false;
            return false;
        }

        true
    }

    /// Reproduce with mutation.
    pub fn reproduce(&self, mutation_rate: f64) -> Option<Lifeform> {
        if !self.alive || self.energy < 50.0 {
            return None;
        }

        let child_genome = self.genome.replicate(mutation_rate);
        let mut child = Lifeform::from_genome(child_genome);
        child.energy = self.energy * 0.4;
        Some(child)
    }

    /// Protein the genome encodes.
    pub fn protein(&self) -> Vec<&'static str> {
        self.genome.translate()
    }
}

// ---------------------------------------------------------------------------
// BiologicalSystem
// ---------------------------------------------------------------------------

/// Manages a population of lifeforms with selection.
pub struct BiologicalSystem {
    pub population: Vec<Lifeform>,
    pub generation: u64,
    pub total_born: u64,
    pub total_died: u64,
    pub total_mutations: u64,
    pub max_population: usize,
    pub base_mutation_rate: f64,
}

impl BiologicalSystem {
    pub fn new() -> Self {
        Self {
            population: Vec::new(),
            generation: 0,
            total_born: 0,
            total_died: 0,
            total_mutations: 0,
            max_population: 200,
            base_mutation_rate: 0.001,
        }
    }

    /// Seed the population with initial lifeforms from available chemistry.
    pub fn abiogenesis(&mut self, chem: &ChemicalSystem) -> usize {
        let available_nucleotides = chem.nucleotide_count;
        let available_amino_acids = chem.amino_acid_count;

        if available_nucleotides < 10 || available_amino_acids < 5 {
            return 0;
        }

        let mut rng = rand::thread_rng();
        // Probability scales with available precursors
        let prob = (available_nucleotides as f64 * available_amino_acids as f64) / 1e6;
        if rng.gen::<f64>() > prob && !self.population.is_empty() {
            return 0;
        }

        // Create a few primitive lifeforms
        let count = rng.gen_range(1..=3).min(5 - self.population.len().min(4));
        let mut created = 0;
        for _ in 0..count {
            if self.population.len() >= self.max_population {
                break;
            }
            let genome_len = rng.gen_range(30..90);
            let lf = Lifeform::new(genome_len);
            self.population.push(lf);
            self.total_born += 1;
            created += 1;
        }
        created
    }

    /// Run one generation: evaluate fitness, select, reproduce, cull.
    pub fn tick(&mut self, temperature: f64, resources: f64, radiation: f64) {
        if self.population.is_empty() {
            return;
        }

        self.generation += 1;

        // Mutation rate increases with radiation
        let mutation_rate = self.base_mutation_rate + radiation * UV_MUTATION_RATE;

        // Evaluate fitness and age
        for lf in &mut self.population {
            lf.evaluate_fitness(temperature, resources);
            lf.tick();
            // Feed: energy proportional to fitness and resources
            if lf.alive {
                lf.energy += lf.fitness * resources * 5.0;
            }
        }

        // Reproduction
        let mut offspring = Vec::new();
        let mut rng = rand::thread_rng();
        for lf in &mut self.population {
            if !lf.alive {
                continue;
            }
            let rep_rate = lf.trait_value("reproduction_rate");
            if rng.gen::<f64>() < rep_rate * lf.fitness * 0.3 {
                if let Some(mut child) = lf.reproduce(mutation_rate) {
                    lf.energy -= 30.0;
                    child.evaluate_fitness(temperature, resources);
                    offspring.push(child);
                    self.total_born += 1;
                    self.total_mutations += 1;
                }
            }
        }
        self.population.extend(offspring);

        // Remove dead
        let before = self.population.len();
        self.population.retain(|lf| lf.alive);
        self.total_died += (before - self.population.len()) as u64;

        // Population cap: keep the fittest
        if self.population.len() > self.max_population {
            self.population
                .sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap());
            let died = self.population.len() - self.max_population;
            self.population.truncate(self.max_population);
            self.total_died += died as u64;
        }
    }

    /// Average fitness of the population.
    pub fn average_fitness(&self) -> f64 {
        if self.population.is_empty() {
            return 0.0;
        }
        let sum: f64 = self.population.iter().map(|lf| lf.fitness).sum();
        sum / self.population.len() as f64
    }

    /// Average genome length.
    pub fn average_genome_length(&self) -> f64 {
        if self.population.is_empty() {
            return 0.0;
        }
        let sum: f64 = self.population.iter().map(|lf| lf.genome.len() as f64).sum();
        sum / self.population.len() as f64
    }

    /// Number of unique species.
    pub fn species_count(&self) -> usize {
        let ids: std::collections::HashSet<u64> =
            self.population.iter().map(|lf| lf.species_id).collect();
        ids.len()
    }

    pub fn to_compact(&self) -> String {
        format!(
            "BIO[pop={} gen={} born={} died={} mut={} fit={:.3} glen={:.0} spp={}]",
            self.population.len(),
            self.generation,
            self.total_born,
            self.total_died,
            self.total_mutations,
            self.average_fitness(),
            self.average_genome_length(),
            self.species_count(),
        )
    }
}
