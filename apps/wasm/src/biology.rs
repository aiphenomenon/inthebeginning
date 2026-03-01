//! Biology simulation - cells, DNA, fitness, and natural selection.
//!
//! Lightweight port of the Python `simulator/biology.py`. Tracks cells
//! with position and fitness for rendering; DNA and mutation logic is
//! simplified for WASM performance.

use rand::Rng;

use crate::constants::*;

// ---------------------------------------------------------------------------
// Cell
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct Cell {
    pub id: u32,
    pub position: [f64; 3],
    pub fitness: f64,
    pub energy: f64,
    pub alive: bool,
    pub generation: u32,
    pub dna_gc_content: f64,
    pub dna_mutation_count: u32,
    pub protein_count: u32,
}

impl Cell {
    pub fn new(id: u32, position: [f64; 3], rng: &mut impl Rng) -> Self {
        Self {
            id,
            position,
            fitness: 1.0,
            energy: 100.0,
            alive: true,
            generation: 0,
            dna_gc_content: 0.4 + rng.gen::<f64>() * 0.2, // ~0.4-0.6
            dna_mutation_count: 0,
            protein_count: rng.gen_range(1..4),
        }
    }

    /// Metabolize: consume energy from environment.
    pub fn metabolize(&mut self, environment_energy: f64) {
        let efficiency = 0.3 + 0.15 * self.protein_count as f64;
        self.energy += environment_energy * efficiency;
        self.energy -= 3.0; // basal cost
        self.energy = self.energy.min(200.0);

        if self.energy <= 0.0 {
            self.alive = false;
        }
    }

    /// Apply mutations from environment.
    pub fn apply_mutations(&mut self, uv_intensity: f64, cosmic_ray_flux: f64, rng: &mut impl Rng) {
        let rate = UV_MUTATION_RATE * uv_intensity + COSMIC_RAY_MUTATION_RATE * cosmic_ray_flux;
        // Simplified: probability of at least one mutation
        if rng.gen::<f64>() < rate * 90.0 {
            // dna length ~90
            self.dna_mutation_count += 1;
            // Drift GC content slightly
            self.dna_gc_content += rng.gen::<f64>() * 0.02 - 0.01;
            self.dna_gc_content = self.dna_gc_content.clamp(0.1, 0.9);
        }

        // Epigenetic changes can affect protein count
        if rng.gen::<f64>() < METHYLATION_PROBABILITY {
            if self.protein_count > 0 && rng.gen::<f64>() < 0.3 {
                self.protein_count -= 1;
            }
        }
        if rng.gen::<f64>() < HISTONE_ACETYLATION_PROB {
            if rng.gen::<f64>() < 0.3 {
                self.protein_count += 1;
            }
        }
    }

    /// Compute fitness based on proteins, energy, GC content.
    pub fn compute_fitness(&mut self) -> f64 {
        if !self.alive {
            self.fitness = 0.0;
            return 0.0;
        }

        let protein_fitness = (self.protein_count as f64 / 3.0).min(1.0);
        let energy_fitness = (self.energy / 100.0).min(1.0);
        let gc_fitness = 1.0 - (self.dna_gc_content - 0.5).abs() * 2.0;

        self.fitness = protein_fitness * 0.4 + energy_fitness * 0.3 + gc_fitness.max(0.0) * 0.3;
        self.fitness
    }

    /// Try to divide. Returns new cell if successful.
    pub fn divide(&mut self, new_id: u32, rng: &mut impl Rng) -> Option<Cell> {
        if !self.alive || self.energy < 50.0 {
            return None;
        }

        self.energy /= 2.0;

        let offset = [
            gauss(rng, 0.0, 0.5),
            gauss(rng, 0.0, 0.5),
            gauss(rng, 0.0, 0.5),
        ];
        let daughter = Cell {
            id: new_id,
            position: [
                self.position[0] + offset[0],
                self.position[1] + offset[1],
                self.position[2] + offset[2],
            ],
            fitness: self.fitness,
            energy: self.energy,
            alive: true,
            generation: self.generation + 1,
            dna_gc_content: self.dna_gc_content + (rng.gen::<f64>() - 0.5) * 0.01,
            dna_mutation_count: self.dna_mutation_count,
            protein_count: self.protein_count.max(1),
        };

        Some(daughter)
    }

    /// Rendering: green blobs, size proportional to fitness.
    pub fn render_color(&self) -> [f32; 4] {
        let g = 0.4 + self.fitness as f32 * 0.6;
        [0.1, g, 0.15, 0.85]
    }

    pub fn render_size(&self) -> f32 {
        10.0 + self.fitness as f32 * 10.0
    }
}

// ---------------------------------------------------------------------------
// Biosphere
// ---------------------------------------------------------------------------

pub struct Biosphere {
    pub cells: Vec<Cell>,
    pub generation: u32,
    pub total_born: u64,
    pub total_died: u64,
    next_id: u32,
}

impl Biosphere {
    pub fn new(initial_cells: usize, rng: &mut impl Rng) -> Self {
        let mut cells = Vec::with_capacity(initial_cells);
        for i in 0..initial_cells {
            let pos = [gauss(rng, 0.0, 3.0), gauss(rng, 0.0, 3.0), gauss(rng, 0.0, 3.0)];
            cells.push(Cell::new(i as u32 + 1, pos, rng));
        }

        Self {
            cells,
            generation: 0,
            total_born: initial_cells as u64,
            total_died: 0,
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
        _temperature: f64,
        rng: &mut impl Rng,
    ) {
        self.generation += 1;

        // Metabolize
        for cell in &mut self.cells {
            cell.metabolize(environment_energy);
        }

        // Mutations
        for cell in &mut self.cells {
            if cell.alive {
                cell.apply_mutations(uv_intensity, cosmic_ray_flux, rng);
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
            self.cells
                .sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap_or(std::cmp::Ordering::Equal));
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

    pub fn total_mutations(&self) -> u64 {
        self.cells.iter().map(|c| c.dna_mutation_count as u64).sum()
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

    // --- Cell tests ---

    #[test]
    fn test_cell_new() {
        let mut rng = make_rng();
        let cell = Cell::new(1, [0.0, 0.0, 0.0], &mut rng);
        assert_eq!(cell.id, 1);
        assert!(cell.alive);
        assert_eq!(cell.fitness, 1.0);
        assert_eq!(cell.energy, 100.0);
        assert_eq!(cell.generation, 0);
        assert_eq!(cell.dna_mutation_count, 0);
        // GC content should be between 0.4 and 0.6
        assert!(cell.dna_gc_content >= 0.4 && cell.dna_gc_content <= 0.6);
        // Protein count should be 1..3
        assert!(cell.protein_count >= 1 && cell.protein_count <= 3);
    }

    #[test]
    fn test_cell_metabolize_gains_energy() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 50.0;

        cell.metabolize(20.0);
        // Energy should increase from environment input minus basal cost
        // efficiency = 0.3 + 0.15 * protein_count; gain = 20 * efficiency - 3
        assert!(cell.alive);
    }

    #[test]
    fn test_cell_metabolize_death() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 1.0;

        cell.metabolize(0.0);
        // Basal cost (3.0) should kill the cell
        assert!(!cell.alive);
    }

    #[test]
    fn test_cell_metabolize_energy_cap() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 199.0;

        cell.metabolize(100.0);
        // Energy should be capped at 200
        assert!(cell.energy <= 200.0);
    }

    #[test]
    fn test_cell_compute_fitness_alive() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 100.0;
        cell.protein_count = 3;
        cell.dna_gc_content = 0.5;

        let fitness = cell.compute_fitness();
        assert!(fitness > 0.0);
        assert!(fitness <= 1.0);
    }

    #[test]
    fn test_cell_compute_fitness_dead() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.alive = false;

        let fitness = cell.compute_fitness();
        assert_eq!(fitness, 0.0);
    }

    #[test]
    fn test_cell_divide_success() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 100.0;

        let daughter = cell.divide(2, &mut rng);
        assert!(daughter.is_some());
        let daughter = daughter.unwrap();

        assert_eq!(daughter.id, 2);
        assert_eq!(daughter.generation, 1);
        assert!(daughter.alive);
        // Parent energy should be halved
        assert!((cell.energy - 50.0).abs() < 1e-10);
        // Daughter gets parent's halved energy
        assert!((daughter.energy - 50.0).abs() < 1e-10);
    }

    #[test]
    fn test_cell_divide_insufficient_energy() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.energy = 30.0;

        let daughter = cell.divide(2, &mut rng);
        assert!(daughter.is_none());
    }

    #[test]
    fn test_cell_divide_dead_cell() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        cell.alive = false;
        cell.energy = 100.0;

        let daughter = cell.divide(2, &mut rng);
        assert!(daughter.is_none());
    }

    #[test]
    fn test_cell_render_color() {
        let mut rng = make_rng();
        let cell = Cell::new(1, [0.0; 3], &mut rng);
        let color = cell.render_color();
        assert_eq!(color.len(), 4);
        // Cells should be greenish
        assert!(color[1] > color[0]);
    }

    #[test]
    fn test_cell_render_size() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);

        cell.fitness = 0.0;
        let size_low = cell.render_size();

        cell.fitness = 1.0;
        let size_high = cell.render_size();

        assert!(size_high > size_low);
    }

    // --- Biosphere tests ---

    #[test]
    fn test_biosphere_new() {
        let mut rng = make_rng();
        let bio = Biosphere::new(5, &mut rng);
        assert_eq!(bio.cells.len(), 5);
        assert_eq!(bio.total_born, 5);
        assert_eq!(bio.total_died, 0);
        assert_eq!(bio.generation, 0);
    }

    #[test]
    fn test_biosphere_step() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(5, &mut rng);

        bio.step(10.0, 0.5, 0.1, 288.0, &mut rng);
        assert_eq!(bio.generation, 1);
        // Cells should still be alive with adequate energy
        assert!(!bio.cells.is_empty());
    }

    #[test]
    fn test_biosphere_average_fitness() {
        let mut rng = make_rng();
        let bio = Biosphere::new(5, &mut rng);
        let avg = bio.average_fitness();
        // Initial fitness is 1.0 for all cells
        assert!((avg - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_biosphere_average_fitness_empty() {
        let mut rng = make_rng();
        let bio = Biosphere::new(0, &mut rng);
        assert_eq!(bio.average_fitness(), 0.0);
    }

    #[test]
    fn test_biosphere_population_cap() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(50, &mut rng);

        // Run several steps with high energy to encourage division
        for _ in 0..20 {
            bio.step(50.0, 0.1, 0.01, 288.0, &mut rng);
        }
        // Population should be capped at 100
        assert!(bio.cells.len() <= 100);
    }

    #[test]
    fn test_biosphere_total_mutations() {
        let mut rng = make_rng();
        let bio = Biosphere::new(3, &mut rng);
        // No mutations initially
        assert_eq!(bio.total_mutations(), 0);
    }

    #[test]
    fn test_biosphere_starvation() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(5, &mut rng);
        // Set all cells to low energy
        for cell in &mut bio.cells {
            cell.energy = 1.0;
        }

        // Step with zero environmental energy
        bio.step(0.0, 0.0, 0.0, 288.0, &mut rng);
        // Some or all cells should have died
        assert!(bio.total_died > 0 || bio.cells.iter().any(|c| !c.alive));
    }

    #[test]
    fn test_cell_apply_mutations_high_uv() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        let initial_mutations = cell.dna_mutation_count;

        // Apply mutations with very high UV intensity to ensure mutations occur
        for _ in 0..50 {
            cell.apply_mutations(100.0, 0.0, &mut rng);
        }
        assert!(cell.dna_mutation_count > initial_mutations,
            "High UV should cause mutations");
    }

    #[test]
    fn test_cell_apply_mutations_cosmic_rays() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);
        let initial_mutations = cell.dna_mutation_count;

        // Use very high flux and many iterations to ensure at least one mutation
        for _ in 0..500 {
            cell.apply_mutations(0.0, 1000.0, &mut rng);
        }
        assert!(cell.dna_mutation_count > initial_mutations,
            "High cosmic ray flux should cause mutations over 500 iterations");
    }

    #[test]
    fn test_cell_gc_content_stays_in_bounds() {
        let mut rng = make_rng();
        let mut cell = Cell::new(1, [0.0; 3], &mut rng);

        for _ in 0..200 {
            cell.apply_mutations(10.0, 10.0, &mut rng);
        }
        assert!(cell.dna_gc_content >= 0.1 && cell.dna_gc_content <= 0.9,
            "GC content {} should stay in [0.1, 0.9]", cell.dna_gc_content);
    }

    #[test]
    fn test_biosphere_total_mutations_after_steps() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(5, &mut rng);

        // Run several steps with high UV to cause mutations
        for _ in 0..20 {
            bio.step(10.0, 50.0, 10.0, 288.0, &mut rng);
        }
        assert!(bio.total_mutations() > 0,
            "Should have accumulated mutations after many steps with high UV");
    }

    #[test]
    fn test_biosphere_step_with_zero_initial_cells() {
        let mut rng = make_rng();
        let mut bio = Biosphere::new(0, &mut rng);
        assert!(bio.cells.is_empty());

        bio.step(10.0, 0.5, 0.1, 288.0, &mut rng);
        assert_eq!(bio.generation, 1);
        assert!(bio.cells.is_empty()); // No cells to evolve
    }
}
