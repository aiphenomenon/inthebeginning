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
                .sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap_or(std::cmp::Ordering::Equal));
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

#[cfg(test)]
mod tests {
    use super::*;

    /// Helper: create a deterministic genome with known bases.
    fn make_genome(bases: &[char]) -> Genome {
        Genome {
            bases: bases.to_vec(),
            methylation: vec![false; bases.len()],
            generation: 0,
        }
    }

    // -----------------------------------------------------------------------
    // Genome
    // -----------------------------------------------------------------------

    /// Genome::random produces the requested length.
    #[test]
    fn genome_random_length() {
        let g = Genome::random(100);
        assert_eq!(g.len(), 100);
        assert_eq!(g.methylation.len(), 100);
        assert_eq!(g.generation, 0);
    }

    /// All bases in a random genome are valid nucleotides.
    #[test]
    fn genome_random_valid_bases() {
        let g = Genome::random(200);
        for &b in &g.bases {
            assert!(
                b == 'A' || b == 'T' || b == 'G' || b == 'C',
                "invalid base: {}", b
            );
        }
    }

    /// Transcription replaces T with U, leaves others unchanged.
    #[test]
    fn genome_transcribe() {
        let g = make_genome(&['A', 'T', 'G', 'C', 'T', 'A']);
        let rna = g.transcribe();
        assert_eq!(rna, vec!['A', 'U', 'G', 'C', 'U', 'A']);
    }

    /// Translation of AUG-UUU-UAA produces [Met, Phe].
    #[test]
    fn genome_translate_simple() {
        // DNA: ATG TTT TAA => RNA: AUG UUU UAA
        let g = make_genome(&['A', 'T', 'G', 'T', 'T', 'T', 'T', 'A', 'A']);
        let protein = g.translate();
        assert_eq!(protein, vec!["Met", "Phe"]);
    }

    /// Translation without a start codon yields an empty protein.
    #[test]
    fn genome_translate_no_start() {
        let g = make_genome(&['T', 'T', 'T', 'T', 'T', 'T']); // UUU UUU
        let protein = g.translate();
        assert!(protein.is_empty());
    }

    /// Translation stops at a stop codon.
    #[test]
    fn genome_translate_stops() {
        // DNA: ATG TTT TAA GGG => RNA: AUG UUU UAA GGG
        let dna: Vec<char> = "ATGTTTTAAGGG".chars().collect();
        let g = make_genome(&dna);
        let protein = g.translate();
        // Should produce [Met, Phe], then stop at UAA
        assert_eq!(protein, vec!["Met", "Phe"]);
    }

    /// Replication increments the generation.
    #[test]
    fn genome_replicate_increments_generation() {
        let g = make_genome(&['A', 'T', 'G', 'C']);
        let child = g.replicate(0.0); // zero error rate
        assert_eq!(child.generation, 1);
    }

    /// Replication with zero error rate produces an identical copy.
    #[test]
    fn genome_replicate_zero_error() {
        let g = make_genome(&['A', 'T', 'G', 'C', 'A', 'T']);
        let child = g.replicate(0.0);
        assert_eq!(child.bases, g.bases);
    }

    /// Base composition counts each base correctly.
    #[test]
    fn genome_base_composition() {
        let g = make_genome(&['A', 'A', 'T', 'G', 'G', 'C']);
        let comp = g.base_composition();
        assert_eq!(*comp.get(&'A').unwrap(), 2);
        assert_eq!(*comp.get(&'T').unwrap(), 1);
        assert_eq!(*comp.get(&'G').unwrap(), 2);
        assert_eq!(*comp.get(&'C').unwrap(), 1);
    }

    /// GC content is computed correctly.
    #[test]
    fn genome_gc_content() {
        let g = make_genome(&['G', 'C', 'G', 'C', 'A', 'T']); // 4 GC out of 6
        let gc = g.gc_content();
        assert!((gc - 4.0 / 6.0).abs() < 1e-10);
    }

    /// GC content of all-AT genome is 0.
    #[test]
    fn genome_gc_content_zero() {
        let g = make_genome(&['A', 'T', 'A', 'T']);
        assert_eq!(g.gc_content(), 0.0);
    }

    /// GC content of all-GC genome is 1.
    #[test]
    fn genome_gc_content_one() {
        let g = make_genome(&['G', 'C', 'G', 'C']);
        assert_eq!(g.gc_content(), 1.0);
    }

    /// Methylation level is 0 when no bases are methylated.
    #[test]
    fn genome_methylation_level_zero() {
        let g = make_genome(&['A', 'T', 'G', 'C']);
        assert_eq!(g.methylation_level(), 0.0);
    }

    /// Methylation level reflects the fraction of methylated bases.
    #[test]
    fn genome_methylation_level_fraction() {
        let mut g = make_genome(&['A', 'T', 'G', 'C']);
        g.methylation[0] = true;
        g.methylation[2] = true;
        assert!((g.methylation_level() - 0.5).abs() < 1e-10);
    }

    /// Methylated bases have a reduced effective mutation rate.
    #[test]
    fn genome_methylated_bases_reduce_mutation() {
        // We test this indirectly: with very high mutation rate,
        // an all-methylated genome should mutate less than an unmethylated one.
        // With mutation_rate = 1.0, effective rate for methylated = 0.1
        let original = vec!['A'; 1000];
        let mut g_unmethylated = make_genome(&original);
        let mut g_methylated = make_genome(&original);
        g_methylated.methylation = vec![true; 1000];

        // Mutate both with rate 1.0
        g_unmethylated.mutate(1.0);
        g_methylated.mutate(1.0);

        let unmeth_changes = g_unmethylated.bases.iter()
            .zip(original.iter())
            .filter(|(a, b)| a != b)
            .count();
        let meth_changes = g_methylated.bases.iter()
            .zip(original.iter())
            .filter(|(a, b)| a != b)
            .count();

        // Methylated should have fewer mutations
        assert!(meth_changes < unmeth_changes,
            "methylated changes ({}) should be less than unmethylated ({})",
            meth_changes, unmeth_changes);
    }

    // -----------------------------------------------------------------------
    // decode_traits
    // -----------------------------------------------------------------------

    /// Short genomes (< 12 bases) produce no traits.
    #[test]
    fn decode_traits_short_genome() {
        let g = make_genome(&['A'; 11]);
        let traits = decode_traits(&g);
        assert!(traits.is_empty());
    }

    /// A 12-base genome produces exactly 1 trait (heat_resistance).
    #[test]
    fn decode_traits_one_trait() {
        let g = make_genome(&['A'; 12]);
        let traits = decode_traits(&g);
        assert_eq!(traits.len(), 1);
        assert_eq!(traits[0].name, "heat_resistance");
    }

    /// A 24-base genome produces 2 traits.
    #[test]
    fn decode_traits_two_traits() {
        let g = make_genome(&['A'; 24]);
        let traits = decode_traits(&g);
        assert_eq!(traits.len(), 2);
        assert_eq!(traits[1].name, "metabolic_efficiency");
    }

    /// A 36+ base genome produces 3 traits.
    #[test]
    fn decode_traits_three_traits() {
        let g = make_genome(&['G'; 36]);
        let traits = decode_traits(&g);
        assert_eq!(traits.len(), 3);
        assert_eq!(traits[2].name, "reproduction_rate");
    }

    /// Trait values are bounded in [0, 1].
    #[test]
    fn decode_traits_bounded() {
        let g = Genome::random(48);
        let traits = decode_traits(&g);
        for t in &traits {
            assert!(t.value >= 0.0 && t.value <= 1.0,
                "trait {} = {} out of range", t.name, t.value);
        }
    }

    // -----------------------------------------------------------------------
    // Lifeform
    // -----------------------------------------------------------------------

    /// New lifeform has expected initial state.
    #[test]
    fn lifeform_new_initial_state() {
        let lf = Lifeform::new(36);
        assert_eq!(lf.genome.len(), 36);
        assert_eq!(lf.fitness, 0.5);
        assert_eq!(lf.energy, 100.0);
        assert_eq!(lf.age, 0);
        assert!(lf.alive);
    }

    /// Lifeform from genome preserves the genome.
    #[test]
    fn lifeform_from_genome() {
        let g = make_genome(&['A', 'T', 'G', 'C', 'A', 'T', 'G', 'C',
                              'A', 'T', 'G', 'C', 'A', 'T', 'G', 'C',
                              'A', 'T', 'G', 'C', 'A', 'T', 'G', 'C',
                              'A', 'T', 'G', 'C', 'A', 'T', 'G', 'C',
                              'A', 'T', 'G', 'C']);
        let lf = Lifeform::from_genome(g.clone());
        assert_eq!(lf.genome.bases, g.bases);
        assert_eq!(lf.traits.len(), 3); // 36 bases => 3 traits
    }

    /// trait_value returns the trait or default 0.5.
    #[test]
    fn lifeform_trait_value() {
        let lf = Lifeform::new(36);
        // Should have heat_resistance trait
        let hr = lf.trait_value("heat_resistance");
        assert!(hr >= 0.0 && hr <= 1.0);
        // Nonexistent trait defaults to 0.5
        let unknown = lf.trait_value("nonexistent");
        assert_eq!(unknown, 0.5);
    }

    /// Fitness evaluation produces values in [0, 1].
    #[test]
    fn lifeform_evaluate_fitness_bounded() {
        let mut lf = Lifeform::new(36);
        lf.evaluate_fitness(288.0, 1.0);
        assert!(lf.fitness >= 0.0 && lf.fitness <= 1.0);
    }

    /// Fitness is higher near optimal temperature.
    #[test]
    fn lifeform_fitness_optimal_temp() {
        let mut lf1 = Lifeform::new(36);
        let mut lf2 = lf1.clone();

        lf1.evaluate_fitness(300.0, 1.0);  // near optimal
        lf2.evaluate_fitness(1000.0, 1.0); // far from optimal

        assert!(lf1.fitness > lf2.fitness,
            "near-optimal fitness {} should exceed far-from-optimal {}",
            lf1.fitness, lf2.fitness);
    }

    /// Tick ages the lifeform and consumes energy.
    #[test]
    fn lifeform_tick_ages() {
        let mut lf = Lifeform::new(36);
        let initial_energy = lf.energy;
        let alive = lf.tick();
        assert!(alive);
        assert_eq!(lf.age, 1);
        assert!(lf.energy < initial_energy);
    }

    /// Lifeform dies when energy reaches zero.
    #[test]
    fn lifeform_dies_no_energy() {
        let mut lf = Lifeform::new(36);
        lf.energy = 0.5; // very low
        let alive = lf.tick();
        assert!(!alive);
        assert!(!lf.alive);
    }

    /// Dead lifeform stays dead on tick.
    #[test]
    fn lifeform_dead_stays_dead() {
        let mut lf = Lifeform::new(36);
        lf.alive = false;
        assert!(!lf.tick());
    }

    /// Reproduce succeeds when alive and has enough energy.
    #[test]
    fn lifeform_reproduce_success() {
        let lf = Lifeform::new(36);
        // energy = 100 >= 50
        let child = lf.reproduce(0.0);
        assert!(child.is_some());
        let child = child.unwrap();
        assert!(child.alive);
        assert_eq!(child.energy, 100.0 * 0.4);
    }

    /// Reproduce fails when energy is too low.
    #[test]
    fn lifeform_reproduce_insufficient_energy() {
        let mut lf = Lifeform::new(36);
        lf.energy = 30.0;
        assert!(lf.reproduce(0.0).is_none());
    }

    /// Reproduce fails when dead.
    #[test]
    fn lifeform_reproduce_dead() {
        let mut lf = Lifeform::new(36);
        lf.alive = false;
        assert!(lf.reproduce(0.0).is_none());
    }

    /// Protein returns a vector of amino acid names.
    #[test]
    fn lifeform_protein() {
        let g = make_genome(&"ATGTTTTAA".chars().collect::<Vec<_>>());
        let lf = Lifeform::from_genome(g);
        let protein = lf.protein();
        assert_eq!(protein, vec!["Met", "Phe"]);
    }

    // -----------------------------------------------------------------------
    // BiologicalSystem
    // -----------------------------------------------------------------------

    /// New BiologicalSystem is empty.
    #[test]
    fn biological_system_new_empty() {
        let bs = BiologicalSystem::new();
        assert_eq!(bs.population.len(), 0);
        assert_eq!(bs.generation, 0);
        assert_eq!(bs.max_population, 200);
    }

    /// Abiogenesis fails with insufficient precursors.
    #[test]
    fn abiogenesis_insufficient_precursors() {
        let mut bs = BiologicalSystem::new();
        let chem = ChemicalSystem::new(); // no nucleotides or amino acids
        let created = bs.abiogenesis(&chem);
        assert_eq!(created, 0);
    }

    /// Abiogenesis creates lifeforms when precursors are available.
    #[test]
    fn abiogenesis_with_precursors() {
        let mut bs = BiologicalSystem::new();
        let mut chem = ChemicalSystem::new();
        chem.nucleotide_count = 100;
        chem.amino_acid_count = 100;

        let created = bs.abiogenesis(&chem);
        assert!(created > 0);
        assert!(!bs.population.is_empty());
        assert_eq!(bs.total_born, created as u64);
    }

    /// Average fitness of empty population is 0.
    #[test]
    fn average_fitness_empty() {
        let bs = BiologicalSystem::new();
        assert_eq!(bs.average_fitness(), 0.0);
    }

    /// Average genome length of empty population is 0.
    #[test]
    fn average_genome_length_empty() {
        let bs = BiologicalSystem::new();
        assert_eq!(bs.average_genome_length(), 0.0);
    }

    /// Species count returns unique species IDs.
    #[test]
    fn species_count_unique() {
        let mut bs = BiologicalSystem::new();
        bs.population.push(Lifeform::new(36));
        bs.population.push(Lifeform::new(36));
        // Each Lifeform::new gets a unique species_id
        assert_eq!(bs.species_count(), 2);
    }

    /// Tick with empty population is a no-op.
    #[test]
    fn tick_empty_population() {
        let mut bs = BiologicalSystem::new();
        bs.tick(288.0, 1.0, 0.0);
        assert_eq!(bs.generation, 0); // no increment
    }

    /// Tick increments generation when population is present.
    #[test]
    fn tick_increments_generation() {
        let mut bs = BiologicalSystem::new();
        bs.population.push(Lifeform::new(36));
        bs.tick(288.0, 1.0, 0.0);
        assert_eq!(bs.generation, 1);
    }

    /// Population is capped at max_population.
    #[test]
    fn population_cap() {
        let mut bs = BiologicalSystem::new();
        bs.max_population = 5;
        for _ in 0..10 {
            let mut lf = Lifeform::new(36);
            lf.energy = 200.0;
            bs.population.push(lf);
        }
        bs.tick(288.0, 1.0, 0.0);
        assert!(bs.population.len() <= 5);
    }

    /// Compact representation includes population stats.
    #[test]
    fn biological_system_compact() {
        let mut bs = BiologicalSystem::new();
        bs.population.push(Lifeform::new(36));
        let compact = bs.to_compact();
        assert!(compact.starts_with("BIO["));
        assert!(compact.contains("pop=1"));
    }
}
