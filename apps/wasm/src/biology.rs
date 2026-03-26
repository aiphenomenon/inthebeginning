//! Biology simulation - DNA, RNA, proteins, and epigenetics.
//!
//! Models:
//! - DNA strand assembly from nucleotides
//! - RNA transcription
//! - Protein translation via codon table
//! - Epigenetic modifications (methylation, histone acetylation)
//! - Cell division with mutation
//! - Natural selection pressure
//!
//! Full-fidelity port of the Python `simulator/biology.py`.

use rand::Rng;

use crate::constants::*;

// ---------------------------------------------------------------------------
// Epigenetic mark
// ---------------------------------------------------------------------------

/// An epigenetic modification at a specific genomic position.
#[derive(Debug, Clone)]
pub struct EpigeneticMark {
    pub position: usize,
    pub mark_type: MarkType,
    pub active: bool,
    pub generation_added: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MarkType {
    Methylation,
    Acetylation,
    Phosphorylation,
}

impl EpigeneticMark {
    pub fn to_compact(&self) -> String {
        let m = match self.mark_type {
            MarkType::Methylation => 'M',
            MarkType::Acetylation => 'A',
            MarkType::Phosphorylation => 'P',
        };
        let state = if self.active { '+' } else { '-' };
        format!("{}{}{}", m, self.position, state)
    }
}

// ---------------------------------------------------------------------------
// Gene
// ---------------------------------------------------------------------------

/// A gene: a segment of DNA that encodes a protein.
#[derive(Debug, Clone)]
pub struct Gene {
    pub name: String,
    pub sequence: Vec<String>,
    pub start_pos: usize,
    pub end_pos: usize,
    pub expression_level: f64,
    pub epigenetic_marks: Vec<EpigeneticMark>,
    pub essential: bool,
}

impl Gene {
    pub fn length(&self) -> usize {
        self.sequence.len()
    }

    /// Gene is silenced if heavily methylated.
    pub fn is_silenced(&self) -> bool {
        let methyl_count = self
            .epigenetic_marks
            .iter()
            .filter(|m| m.mark_type == MarkType::Methylation && m.active)
            .count();
        methyl_count > (self.length() as f64 * 0.3) as usize
    }

    /// Add methylation mark.
    pub fn methylate(&mut self, position: usize, generation: u32) {
        if position < self.length() {
            self.epigenetic_marks.push(EpigeneticMark {
                position,
                mark_type: MarkType::Methylation,
                active: true,
                generation_added: generation,
            });
            self.update_expression();
        }
    }

    /// Remove methylation mark.
    pub fn demethylate(&mut self, position: usize) {
        self.epigenetic_marks.retain(|m| {
            !(m.position == position && m.mark_type == MarkType::Methylation)
        });
        self.update_expression();
    }

    /// Add histone acetylation (increases expression).
    pub fn acetylate(&mut self, position: usize, generation: u32) {
        self.epigenetic_marks.push(EpigeneticMark {
            position,
            mark_type: MarkType::Acetylation,
            active: true,
            generation_added: generation,
        });
        self.update_expression();
    }

    fn update_expression(&mut self) {
        let methyl = self
            .epigenetic_marks
            .iter()
            .filter(|m| m.mark_type == MarkType::Methylation && m.active)
            .count();
        let acetyl = self
            .epigenetic_marks
            .iter()
            .filter(|m| m.mark_type == MarkType::Acetylation && m.active)
            .count();
        let len = self.length().max(1) as f64;
        let suppression = (methyl as f64 / len * 3.0).min(1.0);
        let activation = (acetyl as f64 / len * 5.0).min(1.0);
        self.expression_level = (1.0 - suppression + activation).clamp(0.0, 1.0);
    }

    /// Transcribe DNA to mRNA (T -> U).
    pub fn transcribe(&self) -> Vec<String> {
        if self.is_silenced() {
            return Vec::new();
        }
        self.sequence
            .iter()
            .map(|base| {
                if base == "T" {
                    "U".to_string()
                } else {
                    base.clone()
                }
            })
            .collect()
    }

    /// Apply random point mutations. Returns mutation count.
    pub fn mutate(&mut self, rate: f64, rng: &mut impl Rng) -> usize {
        let mut mutations = 0;
        for i in 0..self.length() {
            if rng.gen::<f64>() < rate {
                let old = &self.sequence[i];
                let choices: Vec<&str> = NUCLEOTIDE_BASES
                    .iter()
                    .copied()
                    .filter(|b| *b != old.as_str())
                    .collect();
                self.sequence[i] = choices[rng.gen_range(0..choices.len())].to_string();
                mutations += 1;
            }
        }
        mutations
    }

    pub fn to_compact(&self) -> String {
        let seq: String = self.sequence.iter().take(20).cloned().collect::<Vec<_>>().join("");
        let suffix = if self.length() > 20 {
            format!("...({})", self.length())
        } else {
            String::new()
        };
        let marks: String = self
            .epigenetic_marks
            .iter()
            .take(5)
            .map(|m| m.to_compact())
            .collect::<Vec<_>>()
            .join("");
        format!(
            "G:{}[{}{}]e={:.2}{{{}}}",
            self.name, seq, suffix, self.expression_level, marks
        )
    }
}

// ---------------------------------------------------------------------------
// DNA strand
// ---------------------------------------------------------------------------

/// A double-stranded DNA molecule.
#[derive(Debug, Clone)]
pub struct DNAStrand {
    pub sequence: Vec<String>,
    pub genes: Vec<Gene>,
    pub generation: u32,
    pub mutation_count: u32,
}

impl DNAStrand {
    pub fn length(&self) -> usize {
        self.sequence.len()
    }

    pub fn complementary_strand(&self) -> Vec<String> {
        self.sequence
            .iter()
            .map(|b| {
                match b.as_str() {
                    "A" => "T",
                    "T" => "A",
                    "G" => "C",
                    "C" => "G",
                    _ => "N",
                }
                .to_string()
            })
            .collect()
    }

    pub fn gc_content(&self) -> f64 {
        if self.sequence.is_empty() {
            return 0.0;
        }
        let gc = self
            .sequence
            .iter()
            .filter(|b| b.as_str() == "G" || b.as_str() == "C")
            .count();
        gc as f64 / self.sequence.len() as f64
    }

    /// Generate a random DNA strand with genes.
    pub fn random_strand(length: usize, num_genes: usize, rng: &mut impl Rng) -> Self {
        let sequence: Vec<String> = (0..length)
            .map(|_| NUCLEOTIDE_BASES[rng.gen_range(0..4)].to_string())
            .collect();

        let mut genes = Vec::new();
        let gene_len = length / (num_genes + 1);
        for i in 0..num_genes {
            let start = i * gene_len + rng.gen_range(0..gene_len.max(1) / 4 + 1);
            let end = (start + gene_len / 2).min(length);
            let gene_seq: Vec<String> = sequence[start..end].to_vec();
            genes.push(Gene {
                name: format!("gene_{}", i),
                sequence: gene_seq,
                start_pos: start,
                end_pos: end,
                expression_level: 1.0,
                epigenetic_marks: Vec::new(),
                essential: i == 0,
            });
        }

        DNAStrand {
            sequence,
            genes,
            generation: 0,
            mutation_count: 0,
        }
    }

    /// Semi-conservative replication with possible errors.
    pub fn replicate(&self, rng: &mut impl Rng) -> DNAStrand {
        let new_sequence = self.sequence.clone();
        let new_genes: Vec<Gene> = self
            .genes
            .iter()
            .map(|gene| {
                let new_marks: Vec<EpigeneticMark> = gene
                    .epigenetic_marks
                    .iter()
                    .filter_map(|m| {
                        if rng.gen::<f64>() < 0.7 {
                            Some(EpigeneticMark {
                                position: m.position,
                                mark_type: m.mark_type,
                                active: m.active && rng.gen::<f64>() < 0.8,
                                generation_added: m.generation_added,
                            })
                        } else {
                            None
                        }
                    })
                    .collect();
                let mut new_gene = Gene {
                    name: gene.name.clone(),
                    sequence: gene.sequence.clone(),
                    start_pos: gene.start_pos,
                    end_pos: gene.end_pos,
                    expression_level: gene.expression_level,
                    epigenetic_marks: new_marks,
                    essential: gene.essential,
                };
                new_gene.update_expression();
                new_gene
            })
            .collect();

        DNAStrand {
            sequence: new_sequence,
            genes: new_genes,
            generation: self.generation + 1,
            mutation_count: 0,
        }
    }

    /// Apply environmental mutations.
    pub fn apply_mutations(
        &mut self,
        uv_intensity: f64,
        cosmic_ray_flux: f64,
        rng: &mut impl Rng,
    ) -> u32 {
        let mut total_mutations = 0u32;
        let rate = UV_MUTATION_RATE * uv_intensity + COSMIC_RAY_MUTATION_RATE * cosmic_ray_flux;

        for gene in &mut self.genes {
            total_mutations += gene.mutate(rate, rng) as u32;
        }

        // Also mutate non-genic regions
        for i in 0..self.length() {
            if rng.gen::<f64>() < rate {
                let old = &self.sequence[i];
                let choices: Vec<&str> = NUCLEOTIDE_BASES
                    .iter()
                    .copied()
                    .filter(|b| *b != old.as_str())
                    .collect();
                self.sequence[i] = choices[rng.gen_range(0..choices.len())].to_string();
                total_mutations += 1;
            }
        }

        self.mutation_count += total_mutations;
        total_mutations
    }

    /// Environmental epigenetic modifications.
    pub fn apply_epigenetic_changes(
        &mut self,
        temperature: f64,
        generation: u32,
        rng: &mut impl Rng,
    ) {
        for gene in &mut self.genes {
            // Methylation
            if rng.gen::<f64>() < METHYLATION_PROBABILITY {
                let pos = rng.gen_range(0..gene.length().max(1));
                gene.methylate(pos, generation);
            }

            // Demethylation
            if rng.gen::<f64>() < DEMETHYLATION_PROBABILITY {
                let methyls: Vec<usize> = gene
                    .epigenetic_marks
                    .iter()
                    .filter(|m| m.mark_type == MarkType::Methylation)
                    .map(|m| m.position)
                    .collect();
                if !methyls.is_empty() {
                    let pos = methyls[rng.gen_range(0..methyls.len())];
                    gene.demethylate(pos);
                }
            }

            // Histone acetylation (temperature-dependent)
            let thermal_factor = (temperature / 300.0).min(2.0);
            if rng.gen::<f64>() < HISTONE_ACETYLATION_PROB * thermal_factor {
                let pos = rng.gen_range(0..gene.length().max(1));
                gene.acetylate(pos, generation);
            }

            // Histone deacetylation
            if rng.gen::<f64>() < HISTONE_DEACETYLATION_PROB {
                let acetyls: Vec<usize> = gene
                    .epigenetic_marks
                    .iter()
                    .enumerate()
                    .filter(|(_, m)| m.mark_type == MarkType::Acetylation)
                    .map(|(i, _)| i)
                    .collect();
                if !acetyls.is_empty() {
                    let idx = acetyls[rng.gen_range(0..acetyls.len())];
                    gene.epigenetic_marks[idx].active = false;
                    gene.update_expression();
                }
            }
        }
    }

    pub fn to_compact(&self) -> String {
        let seq: String = self.sequence.iter().take(30).cloned().collect::<Vec<_>>().join("");
        let suffix = if self.length() > 30 {
            format!("...({})", self.length())
        } else {
            String::new()
        };
        let genes: String = self
            .genes
            .iter()
            .take(5)
            .map(|g| g.to_compact())
            .collect::<Vec<_>>()
            .join("|");
        format!(
            "DNA[gen={} mut={} gc={:.2} {}{}]{{{}}}",
            self.generation,
            self.mutation_count,
            self.gc_content(),
            seq,
            suffix,
            genes,
        )
    }
}

// ---------------------------------------------------------------------------
// mRNA translation
// ---------------------------------------------------------------------------

/// Translate mRNA to protein (amino acid sequence).
pub fn translate_mrna(mrna: &[String]) -> Vec<&'static str> {
    let mut protein = Vec::new();
    let mut i = 0;
    let mut started = false;

    while i + 2 < mrna.len() {
        let codon = format!("{}{}{}", mrna[i], mrna[i + 1], mrna[i + 2]);
        if let Some(aa) = codon_to_amino_acid(&codon) {
            if aa == "Met" && !started {
                started = true;
                protein.push(aa);
            } else if started {
                if aa == "STOP" {
                    break;
                }
                protein.push(aa);
            }
        }
        i += 3;
    }

    protein
}

// ---------------------------------------------------------------------------
// Protein
// ---------------------------------------------------------------------------

/// A protein: a chain of amino acids.
#[derive(Debug, Clone)]
pub struct Protein {
    pub amino_acids: Vec<&'static str>,
    pub name: String,
    pub function: ProteinFunction,
    pub folded: bool,
    pub active: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProteinFunction {
    Enzyme,
    Structural,
    Signaling,
}

impl Protein {
    pub fn length(&self) -> usize {
        self.amino_acids.len()
    }

    /// Simplified protein folding - probability based on length.
    pub fn fold(&mut self, rng: &mut impl Rng) -> bool {
        if self.length() < 3 {
            self.folded = false;
            return false;
        }
        let fold_prob = (0.5 + 0.1 * (self.length() as f64 + 1.0).ln()).min(0.9);
        self.folded = rng.gen::<f64>() < fold_prob;
        self.folded
    }

    pub fn to_compact(&self) -> String {
        let seq: String = self
            .amino_acids
            .iter()
            .take(10)
            .copied()
            .collect::<Vec<_>>()
            .join("-");
        let suffix = if self.length() > 10 {
            format!("...({})", self.length())
        } else {
            String::new()
        };
        format!(
            "P:{}[{}{}]f={}",
            self.name,
            seq,
            suffix,
            if self.folded { "Y" } else { "N" },
        )
    }
}

// ---------------------------------------------------------------------------
// Cell
// ---------------------------------------------------------------------------

/// A cell with DNA, RNA, and proteins.
#[derive(Debug, Clone)]
pub struct Cell {
    pub id: u32,
    pub dna: DNAStrand,
    pub proteins: Vec<Protein>,
    pub fitness: f64,
    pub energy: f64,
    pub alive: bool,
    pub generation: u32,
    pub position: [f64; 3],
}

impl Cell {
    pub fn new(id: u32, position: [f64; 3], dna_length: usize, rng: &mut impl Rng) -> Self {
        let dna = DNAStrand::random_strand(dna_length, 3, rng);
        let mut cell = Self {
            id,
            dna,
            proteins: Vec::new(),
            fitness: 1.0,
            energy: 100.0,
            alive: true,
            generation: 0,
            position,
        };
        cell.transcribe_and_translate(rng);
        cell
    }

    /// Central dogma: DNA -> mRNA -> Protein.
    pub fn transcribe_and_translate(&mut self, rng: &mut impl Rng) -> Vec<Protein> {
        let mut new_proteins = Vec::new();
        for gene in &self.dna.genes {
            if gene.expression_level < 0.1 {
                continue;
            }

            let mrna = gene.transcribe();
            if mrna.is_empty() {
                continue;
            }

            let aa_seq = translate_mrna(&mrna);
            if aa_seq.is_empty() {
                continue;
            }

            if rng.gen::<f64>() > gene.expression_level {
                continue;
            }

            let func = match rng.gen_range(0..3) {
                0 => ProteinFunction::Enzyme,
                1 => ProteinFunction::Structural,
                _ => ProteinFunction::Signaling,
            };

            let mut protein = Protein {
                amino_acids: aa_seq,
                name: format!("protein_{}", gene.name),
                function: func,
                folded: false,
                active: true,
            };
            protein.fold(rng);
            new_proteins.push(protein.clone());
            self.proteins.push(protein);
        }
        new_proteins
    }

    /// Basic metabolism: consume energy, produce waste.
    pub fn metabolize(&mut self, environment_energy: f64) {
        let enzyme_count = self
            .proteins
            .iter()
            .filter(|p| p.function == ProteinFunction::Enzyme && p.folded && p.active)
            .count();
        let efficiency = 0.3 + 0.15 * enzyme_count as f64;
        self.energy += environment_energy * efficiency;
        self.energy -= 3.0;
        self.energy = self.energy.min(200.0);

        if self.energy <= 0.0 {
            self.alive = false;
        }
    }

    /// Cell division with DNA replication and possible mutation.
    pub fn divide(&mut self, new_id: u32, rng: &mut impl Rng) -> Option<Cell> {
        if !self.alive || self.energy < 50.0 {
            return None;
        }

        let new_dna = self.dna.replicate(rng);
        self.energy /= 2.0;

        let offset = [
            gauss(rng, 0.0, 0.5),
            gauss(rng, 0.0, 0.5),
            gauss(rng, 0.0, 0.5),
        ];

        let mut daughter = Cell {
            id: new_id,
            dna: new_dna,
            proteins: Vec::new(),
            fitness: self.fitness,
            energy: self.energy,
            alive: true,
            generation: self.generation + 1,
            position: [
                self.position[0] + offset[0],
                self.position[1] + offset[1],
                self.position[2] + offset[2],
            ],
        };
        daughter.transcribe_and_translate(rng);

        Some(daughter)
    }

    /// Compute cell fitness based on functional proteins and DNA integrity.
    pub fn compute_fitness(&mut self) -> f64 {
        if !self.alive {
            self.fitness = 0.0;
            return 0.0;
        }

        // Essential genes must be active
        let essential_active = self
            .dna
            .genes
            .iter()
            .filter(|g| g.essential)
            .all(|g| !g.is_silenced());
        if !essential_active {
            self.fitness = 0.1;
            return 0.1;
        }

        // Fitness from proteins
        let functional_proteins = self
            .proteins
            .iter()
            .filter(|p| p.folded && p.active)
            .count();
        let protein_fitness =
            (functional_proteins as f64 / self.dna.genes.len().max(1) as f64).min(1.0);

        // Fitness from energy
        let energy_fitness = (self.energy / 100.0).min(1.0);

        // GC content near 0.5 is optimal
        let gc_fitness = 1.0 - (self.dna.gc_content() - 0.5).abs() * 2.0;

        self.fitness = protein_fitness * 0.4 + energy_fitness * 0.3 + gc_fitness.max(0.0) * 0.3;
        self.fitness
    }

    /// Rendering: green blobs, size proportional to fitness.
    pub fn render_color(&self) -> [f32; 4] {
        let g = 0.4 + self.fitness as f32 * 0.6;
        [0.1, g, 0.15, 0.85]
    }

    pub fn render_size(&self) -> f32 {
        10.0 + self.fitness as f32 * 10.0
    }

    pub fn to_compact(&self) -> String {
        let state = if self.alive { "alive" } else { "dead" };
        format!(
            "Cell#{}[gen={} fit={:.2} E={:.0} prot={} {}]",
            self.id,
            self.generation,
            self.fitness,
            self.energy,
            self.proteins.len(),
            state,
        )
    }
}

// ---------------------------------------------------------------------------
// Biosphere
// ---------------------------------------------------------------------------

/// Collection of cells with population dynamics.
pub struct Biosphere {
    pub cells: Vec<Cell>,
    pub generation: u32,
    pub total_born: u64,
    pub total_died: u64,
    pub dna_length: usize,
    next_id: u32,
}

impl Biosphere {
    pub fn new(initial_cells: usize, dna_length: usize, rng: &mut impl Rng) -> Self {
        let mut cells = Vec::with_capacity(initial_cells);
        for i in 0..initial_cells {
            let pos = [
                gauss(rng, 0.0, 3.0),
                gauss(rng, 0.0, 3.0),
                gauss(rng, 0.0, 3.0),
            ];
            cells.push(Cell::new(i as u32 + 1, pos, dna_length, rng));
        }

        Self {
            cells,
            generation: 0,
            total_born: initial_cells as u64,
            total_died: 0,
            dna_length,
            next_id: initial_cells as u32 + 1,
        }
    }

    fn alloc_id(&mut self) -> u32 {
        let id = self.next_id;
        self.next_id = self.next_id.wrapping_add(1);
        id
    }

    /// One generation step.
    pub fn step(
        &mut self,
        environment_energy: f64,
        uv_intensity: f64,
        cosmic_ray_flux: f64,
        temperature: f64,
        rng: &mut impl Rng,
    ) {
        self.generation += 1;

        // Metabolize
        for cell in &mut self.cells {
            cell.metabolize(environment_energy);
        }

        // Apply mutations
        for cell in &mut self.cells {
            if cell.alive {
                cell.dna.apply_mutations(uv_intensity, cosmic_ray_flux, rng);
                cell.dna
                    .apply_epigenetic_changes(temperature, self.generation, rng);
            }
        }

        // Transcribe/translate (clear old proteins to prevent unbounded growth)
        for cell in &mut self.cells {
            if cell.alive {
                cell.proteins.clear();
                cell.transcribe_and_translate(rng);
            }
        }

        // Compute fitness
        for cell in &mut self.cells {
            cell.compute_fitness();
        }

        // Selection and reproduction: top 50% reproduce
        let mut alive: Vec<usize> = self
            .cells
            .iter()
            .enumerate()
            .filter(|(_, c)| c.alive)
            .map(|(i, _)| i)
            .collect();
        alive.sort_by(|&a, &b| {
            self.cells[b]
                .fitness
                .partial_cmp(&self.cells[a].fitness)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let cutoff = (alive.len() / 2).max(1);
        let mut new_cells = Vec::new();
        for &idx in alive.iter().take(cutoff) {
            let new_id = self.alloc_id();
            if let Some(daughter) = self.cells[idx].divide(new_id, rng) {
                new_cells.push(daughter);
                self.total_born += 1;
            }
        }
        self.cells.extend(new_cells);

        // Remove dead
        let dead_count = self.cells.iter().filter(|c| !c.alive).count();
        self.total_died += dead_count as u64;
        self.cells.retain(|c| c.alive);

        // Population cap
        if self.cells.len() > 100 {
            self.cells.sort_by(|a, b| {
                b.fitness
                    .partial_cmp(&a.fitness)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            let overflow = self.cells.len() - 100;
            self.total_died += overflow as u64;
            self.cells.truncate(100);
        }
    }

    pub fn average_fitness(&self) -> f64 {
        if self.cells.is_empty() {
            return 0.0;
        }
        self.cells.iter().map(|c| c.fitness).sum::<f64>() / self.cells.len() as f64
    }

    pub fn average_gc_content(&self) -> f64 {
        if self.cells.is_empty() {
            return 0.0;
        }
        self.cells.iter().map(|c| c.dna.gc_content()).sum::<f64>() / self.cells.len() as f64
    }

    pub fn total_mutations(&self) -> u64 {
        self.cells
            .iter()
            .map(|c| c.dna.mutation_count as u64)
            .sum()
    }

    pub fn to_compact(&self) -> String {
        format!(
            "Bio[gen={} pop={} fit={:.3} gc={:.2} born={} died={} mut={}]",
            self.generation,
            self.cells.len(),
            self.average_fitness(),
            self.average_gc_content(),
            self.total_born,
            self.total_died,
            self.total_mutations(),
        )
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn gauss(rng: &mut impl Rng, mean: f64, std: f64) -> f64 {
    let u1: f64 = rng.gen::<f64>().max(1e-15);
    let u2: f64 = rng.gen::<f64>();
    mean + std * (-2.0 * u1.ln()).sqrt() * (2.0 * crate::constants::PI * u2).cos()
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::SmallRng;
    use rand::SeedableRng;

    fn make_rng() -> SmallRng {
        SmallRng::seed_from_u64(42)
    }

    // --- Gene tests ---

    #[test]
    fn test_gene_transcribe() {
        let gene = Gene {
            name: "test".to_string(),
            sequence: vec!["A", "T", "G", "C"]
                .into_iter()
                .map(String::from)
                .collect(),
            start_pos: 0,
            end_pos: 4,
            expression_level: 1.0,
            epigenetic_marks: Vec::new(),
            essential: false,
        };
        let mrna = gene.transcribe();
        assert_eq!(mrna, vec!["A", "U", "G", "C"]);
    }

    #[test]
    fn test_gene_silenced_by_methylation() {
        let mut gene = Gene {
            name: "test".to_string(),
            sequence: vec!["A"; 10].into_iter().map(String::from).collect(),
            start_pos: 0,
            end_pos: 10,
            expression_level: 1.0,
            epigenetic_marks: Vec::new(),
            essential: false,
        };
        assert!(!gene.is_silenced());

        // Add > 30% methylation marks
        for i in 0..4 {
            gene.methylate(i, 0);
        }
        assert!(gene.is_silenced());
        assert!(gene.transcribe().is_empty());
    }

    #[test]
    fn test_gene_acetylation_increases_expression() {
        let mut gene = Gene {
            name: "test".to_string(),
            sequence: vec!["A"; 10].into_iter().map(String::from).collect(),
            start_pos: 0,
            end_pos: 10,
            expression_level: 1.0,
            epigenetic_marks: Vec::new(),
            essential: false,
        };
        // Suppress with methylation first
        for i in 0..3 {
            gene.methylate(i, 0);
        }
        let suppressed = gene.expression_level;
        // Acetylation should increase expression
        gene.acetylate(0, 0);
        gene.acetylate(1, 0);
        assert!(gene.expression_level >= suppressed);
    }

    // --- DNAStrand tests ---

    #[test]
    fn test_dna_random_strand() {
        let mut rng = make_rng();
        let dna = DNAStrand::random_strand(90, 3, &mut rng);
        assert_eq!(dna.length(), 90);
        assert_eq!(dna.genes.len(), 3);
        assert!(dna.genes[0].essential);
        assert!(!dna.genes[1].essential);
    }

    #[test]
    fn test_dna_gc_content() {
        let dna = DNAStrand {
            sequence: vec!["G", "C", "A", "T"]
                .into_iter()
                .map(String::from)
                .collect(),
            genes: Vec::new(),
            generation: 0,
            mutation_count: 0,
        };
        assert!((dna.gc_content() - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_dna_replicate() {
        let mut rng = make_rng();
        let dna = DNAStrand::random_strand(90, 3, &mut rng);
        let daughter = dna.replicate(&mut rng);
        assert_eq!(daughter.generation, 1);
        assert_eq!(daughter.sequence.len(), dna.sequence.len());
        assert_eq!(daughter.genes.len(), dna.genes.len());
    }

    // --- translate_mrna tests ---

    #[test]
    fn test_translate_mrna_basic() {
        // AUG (Met) + UUU (Phe) + UAA (STOP)
        let mrna: Vec<String> = vec!["A", "U", "G", "U", "U", "U", "U", "A", "A"]
            .into_iter()
            .map(String::from)
            .collect();
        let protein = translate_mrna(&mrna);
        assert_eq!(protein, vec!["Met", "Phe"]);
    }

    #[test]
    fn test_translate_mrna_no_start() {
        let mrna: Vec<String> = vec!["U", "U", "U", "U", "A", "A"]
            .into_iter()
            .map(String::from)
            .collect();
        let protein = translate_mrna(&mrna);
        assert!(protein.is_empty());
    }

    // --- Protein tests ---

    #[test]
    fn test_protein_fold() {
        let mut rng = make_rng();
        let mut protein = Protein {
            amino_acids: vec!["Met", "Phe", "Ala", "Gly", "Val"],
            name: "test".to_string(),
            function: ProteinFunction::Enzyme,
            folded: false,
            active: true,
        };
        // Run many times; with length 5, folding should succeed sometimes
        let mut folded_once = false;
        for _ in 0..20 {
            protein.folded = false;
            if protein.fold(&mut rng) {
                folded_once = true;
            }
        }
        assert!(folded_once);
    }

    #[test]
    fn test_protein_too_short_to_fold() {
        let mut rng = make_rng();
        let mut protein = Protein {
            amino_acids: vec!["Met", "Phe"],
            name: "short".to_string(),
            function: ProteinFunction::Structural,
            folded: false,
            active: true,
        };
        assert!(!protein.fold(&mut rng));
    }

    // --- Cell tests ---

    #[test]
    fn test_cell_new() {
        let mut rng = make_rng();
        let cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        assert_eq!(cell.id, 1);
        assert!(cell.alive);
        assert_eq!(cell.energy, 100.0);
        assert_eq!(cell.generation, 0);
        assert_eq!(cell.dna.genes.len(), 3);
    }

    #[test]
    fn test_cell_metabolize() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        cell.energy = 50.0;
        cell.metabolize(20.0);
        assert!(cell.alive);
    }

    #[test]
    fn test_cell_metabolize_death() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        cell.energy = 1.0;
        cell.metabolize(0.0);
        assert!(!cell.alive);
    }

    #[test]
    fn test_cell_divide() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        cell.energy = 100.0;
        let daughter = cell.divide(2, &mut rng);
        assert!(daughter.is_some());
        let daughter = daughter.unwrap();
        assert_eq!(daughter.id, 2);
        assert_eq!(daughter.generation, 1);
        assert!((cell.energy - 50.0).abs() < 1e-10);
    }

    #[test]
    fn test_cell_divide_insufficient_energy() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        cell.energy = 30.0;
        assert!(cell.divide(2, &mut rng).is_none());
    }

    #[test]
    fn test_cell_compute_fitness() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], 90, &mut rng);
        let fitness = cell.compute_fitness();
        assert!(fitness > 0.0 && fitness <= 1.0);
    }

    // --- Biosphere tests ---

    #[test]
    fn test_biosphere_new() {
        let mut rng = make_rng();
        let bio = Biosphere::new(5, 90, &mut rng);
        assert_eq!(bio.cells.len(), 5);
        assert_eq!(bio.total_born, 5);
        assert_eq!(bio.total_died, 0);
        assert_eq!(bio.generation, 0);
    }

    #[test]
    fn test_biosphere_step() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(5, 90, &mut rng);
        bio.step(10.0, 0.5, 0.1, 288.0, &mut rng);
        assert_eq!(bio.generation, 1);
        assert!(!bio.cells.is_empty());
    }

    #[test]
    fn test_biosphere_population_cap() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(50, 90, &mut rng);
        for _ in 0..20 {
            bio.step(50.0, 0.1, 0.01, 288.0, &mut rng);
        }
        assert!(bio.cells.len() <= 100);
    }

    #[test]
    fn test_biosphere_average_fitness() {
        let mut rng = make_rng();
        let bio = Biosphere::new(5, 90, &mut rng);
        let avg = bio.average_fitness();
        assert!(avg > 0.0);
    }

    #[test]
    fn test_biosphere_average_gc_content() {
        let mut rng = make_rng();
        let bio = Biosphere::new(5, 90, &mut rng);
        let gc = bio.average_gc_content();
        assert!(gc > 0.0 && gc < 1.0);
    }

    #[test]
    fn test_biosphere_to_compact() {
        let mut rng = make_rng();
        let bio = Biosphere::new(3, 90, &mut rng);
        let s = bio.to_compact();
        assert!(s.contains("Bio["));
        assert!(s.contains("pop=3"));
    }

    #[test]
    fn test_biosphere_starvation() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(5, 90, &mut rng);
        for cell in &mut bio.cells {
            cell.energy = 1.0;
        }
        bio.step(0.0, 0.0, 0.0, 288.0, &mut rng);
        assert!(bio.total_died > 0 || bio.cells.iter().any(|c| !c.alive));
    }
}
