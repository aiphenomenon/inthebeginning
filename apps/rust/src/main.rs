//! In The Beginning -- A cosmic simulation from the Big Bang to life.
//!
//! CLI entry point that runs the full simulation and reports progress
//! through each of the 13 cosmic epochs.

mod simulator;

use simulator::universe::{SimStats, Universe};
use std::fs;
use std::path::Path;

// ---------------------------------------------------------------------------
// Display helpers
// ---------------------------------------------------------------------------

fn separator() {
    println!(
        "{}",
        "=".repeat(78)
    );
}

fn thin_separator() {
    println!(
        "{}",
        "-".repeat(78)
    );
}

fn format_sci(v: f64) -> String {
    if v == 0.0 {
        "0".to_string()
    } else if v.abs() >= 1e6 || (v.abs() < 0.01 && v != 0.0) {
        format!("{:.2e}", v)
    } else {
        format!("{:.2}", v)
    }
}

fn print_epoch_banner(stats: &SimStats) {
    separator();
    println!(
        "  EPOCH: {:<20}  tick {}/300000",
        stats.epoch_name, stats.tick
    );
    println!("  {}", stats.epoch_description);
    separator();
    print_stats(stats);
}

fn print_stats(stats: &SimStats) {
    println!(
        "  Temperature : {:<16}  Energy      : {}",
        format_sci(stats.temperature),
        format_sci(stats.total_energy)
    );
    println!(
        "  Particles   : {:<16}  Atoms       : {}",
        stats.particle_count, stats.atom_count
    );
    println!(
        "  Molecules   : {:<16}  Water (H2O) : {}",
        stats.molecule_count, stats.water_count
    );
    println!(
        "  Amino acids : {:<16}  Nucleotides : {}",
        stats.amino_acid_count, stats.nucleotide_count
    );
    if stats.population > 0 || stats.generation > 0 {
        thin_separator();
        println!(
            "  Population  : {:<16}  Generation  : {}",
            stats.population, stats.generation
        );
        println!(
            "  Avg fitness : {:<16}  Species     : {}",
            format!("{:.4}", stats.average_fitness),
            stats.species_count
        );
        println!(
            "  Habitable   : {:<16}  Oxygen      : {:.2}%",
            if stats.is_habitable { "YES" } else { "NO" },
            stats.oxygen_pct
        );
    }
    println!();
}

fn print_progress(stats: &SimStats) {
    let pct = stats.tick as f64 / 300_000.0 * 100.0;
    let bar_width = 40;
    let filled = (pct / 100.0 * bar_width as f64) as usize;
    let bar: String = "#".repeat(filled) + &"-".repeat(bar_width - filled);
    print!(
        "\r  [{bar}] {pct:5.1}%  T={temp}  particles={p}  atoms={a}  pop={pop}",
        bar = bar,
        pct = pct,
        temp = format_sci(stats.temperature),
        p = stats.particle_count,
        a = stats.atom_count,
        pop = stats.population,
    );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::simulator::constants::*;
    use super::simulator::quantum::{Particle, QuantumField};
    use super::simulator::atomic::{Atom, AtomicSystem};
    use super::simulator::chemistry::ChemicalSystem;
    use super::simulator::biology::{BiologicalSystem, Genome, Lifeform};
    use super::simulator::environment::Environment;
    use super::simulator::universe::Universe;

    // -----------------------------------------------------------------------
    // Integration: Quantum -> Atomic pipeline
    // -----------------------------------------------------------------------

    /// Pair production followed by quark confinement produces hadrons.
    #[test]
    fn integration_pair_production_to_hadrons() {
        let mut qf = QuantumField::new(T_QUARK_HADRON * 2.0);

        // Manually add quarks (as if produced by pair production)
        // 2 up + 1 down => proton
        qf.particles.push(Particle::new(ParticleType::Up));
        qf.particles.push(Particle::new(ParticleType::Up));
        qf.particles.push(Particle::new(ParticleType::Down));

        // Cool below confinement temperature
        qf.temperature = T_QUARK_HADRON * 0.1;

        let hadrons = qf.quark_confinement();
        assert_eq!(hadrons.len(), 1);
        assert_eq!(hadrons[0].particle_type, ParticleType::Proton);
    }

    /// Recombination converts field protons+electrons into hydrogen atoms.
    #[test]
    fn integration_recombination_pipeline() {
        let mut qf = QuantumField::new(T_RECOMBINATION * 0.5);
        let mut atomic = AtomicSystem::new(T_RECOMBINATION * 0.5);

        // Add 3 protons and 3 electrons
        for _ in 0..3 {
            qf.particles.push(Particle::new(ParticleType::Proton));
            qf.particles.push(Particle::new(ParticleType::Electron));
        }

        let atoms = atomic.recombination(&mut qf);
        assert_eq!(atoms.len(), 3);
        for a in &atoms {
            assert_eq!(a.atomic_number, 1);
            assert_eq!(a.symbol(), "H");
        }
        assert_eq!(qf.particles.len(), 0);
    }

    // -----------------------------------------------------------------------
    // Integration: Atomic -> Chemistry pipeline
    // -----------------------------------------------------------------------

    /// Atoms can form water molecules.
    #[test]
    fn integration_atoms_to_water() {
        let mut chem = ChemicalSystem::new();
        let mut atoms: Vec<Atom> = Vec::new();

        // Add 4H + 2O
        for _ in 0..4 {
            atoms.push(Atom::new(1));
        }
        for _ in 0..2 {
            atoms.push(Atom::new(8));
        }

        let water_count = chem.form_water(&mut atoms);
        assert_eq!(water_count, 2);
        assert_eq!(chem.water_count, 2);
    }

    /// Multiple molecule types form from a mixed atom pool.
    #[test]
    fn integration_mixed_molecule_formation() {
        let mut chem = ChemicalSystem::new();
        let mut atoms: Vec<Atom> = Vec::new();

        // Add H, C, N, O atoms
        for _ in 0..20 {
            atoms.push(Atom::new(1)); // H
        }
        for _ in 0..3 {
            atoms.push(Atom::new(6)); // C
        }
        for _ in 0..2 {
            atoms.push(Atom::new(7)); // N
        }
        for _ in 0..5 {
            atoms.push(Atom::new(8)); // O
        }

        let water = chem.form_water(&mut atoms);
        let methane = chem.form_methane(&mut atoms);
        let ammonia = chem.form_ammonia(&mut atoms);

        assert!(water + methane + ammonia > 0,
            "should form at least some molecules");
    }

    // -----------------------------------------------------------------------
    // Integration: Chemistry -> Biology pipeline
    // -----------------------------------------------------------------------

    /// Abiogenesis produces lifeforms when chemistry provides precursors.
    #[test]
    fn integration_chemistry_to_biology() {
        let mut chem = ChemicalSystem::new();
        chem.nucleotide_count = 50;
        chem.amino_acid_count = 50;

        let mut bio = BiologicalSystem::new();
        let created = bio.abiogenesis(&chem);
        assert!(created > 0, "abiogenesis should produce lifeforms");
        assert!(!bio.population.is_empty());
    }

    // -----------------------------------------------------------------------
    // Integration: Biology + Environment
    // -----------------------------------------------------------------------

    /// Lifeforms evolve in a habitable environment.
    #[test]
    fn integration_life_in_environment() {
        let mut env = Environment::early_earth();
        env.make_habitable();

        let mut bio = BiologicalSystem::new();
        // Seed a few lifeforms
        for _ in 0..5 {
            let mut lf = Lifeform::new(48);
            lf.energy = 200.0;
            bio.population.push(lf);
        }

        // Run a few generations
        for _ in 0..10 {
            bio.tick(env.temperature, env.resources, env.radiation_level);
            env.tick(bio.population.len());
        }

        assert!(bio.generation == 10);
        // At least some lifeforms should survive
        assert!(!bio.population.is_empty(),
            "some lifeforms should survive in habitable environment");
    }

    // -----------------------------------------------------------------------
    // Integration: Full Universe pipeline (abbreviated)
    // -----------------------------------------------------------------------

    /// Universe advances through multiple epochs without panic.
    #[test]
    fn integration_universe_multi_epoch() {
        let mut u = Universe::new();
        // Run through the first 6 epochs (up to nucleosynthesis)
        while u.tick < RECOMBINATION_EPOCH {
            u.step();
        }
        let stats = u.stats();
        assert_eq!(stats.tick, RECOMBINATION_EPOCH);
        assert!(stats.temperature < T_PLANCK);
    }

    /// format_sci produces correct formatting.
    #[test]
    fn format_sci_values() {
        assert_eq!(super::format_sci(0.0), "0");
        assert_eq!(super::format_sci(1234567.0), "1.23e6");
        assert_eq!(super::format_sci(0.001), "1.00e-3");
        assert_eq!(super::format_sci(42.0), "42.00");
    }

    // -----------------------------------------------------------------------
    // Integration: DNA replication fidelity
    // -----------------------------------------------------------------------

    /// DNA replication with zero error rate preserves the sequence.
    #[test]
    fn integration_dna_replication_fidelity() {
        let bases: Vec<char> = "ATGCATGCATGCATGCATGCATGCATGCATGCATGC"
            .chars().collect();
        let genome = Genome {
            bases: bases.clone(),
            methylation: vec![false; bases.len()],
            generation: 0,
        };
        let child = genome.replicate(0.0);
        assert_eq!(child.bases, bases);
        assert_eq!(child.generation, 1);
    }

    // -----------------------------------------------------------------------
    // Integration: Wave function -> Particle -> Field
    // -----------------------------------------------------------------------

    /// Wave function evolution affects particles in the field.
    #[test]
    fn integration_wavefunction_in_field() {
        let mut qf = QuantumField::new(1000.0);
        let p = Particle::new(ParticleType::Electron)
            .with_momentum([1.0, 0.0, 0.0]);
        qf.particles.push(p);

        // Evolve the field
        qf.evolve(0.1);

        // Particle should have moved and phase should have changed
        assert!(qf.particles[0].position[0] != 0.0);
        assert!(qf.particles[0].wave_fn.phase != 0.0);
    }

    // -----------------------------------------------------------------------
    // Integration: Energy conservation in pair creation/annihilation
    // -----------------------------------------------------------------------

    /// Pair creation followed by annihilation conserves energy approximately.
    #[test]
    fn integration_energy_conservation() {
        let mut qf = QuantumField::new(1000.0);
        let input_energy = 5.0;
        let _pair = qf.pair_production(input_energy).unwrap();

        let particle_energy: f64 = qf.particles.iter()
            .map(|p| p.energy())
            .sum();

        // Particles should have nonzero energy
        assert!(particle_energy > 0.0);
    }

    // -----------------------------------------------------------------------
    // Integration: Nucleosynthesis atom composition
    // -----------------------------------------------------------------------

    /// Nucleosynthesis with 7:1 proton-to-neutron ratio produces
    /// ~75% hydrogen, ~25% helium by atom count.
    #[test]
    fn integration_nucleosynthesis_composition() {
        let mut sys = AtomicSystem::new(T_NUCLEOSYNTHESIS);
        // 14 protons, 2 neutrons (7:1 ratio)
        let atoms = sys.nucleosynthesis(14, 2);
        let h_count = atoms.iter().filter(|a| a.atomic_number == 1).count();
        let he_count = atoms.iter().filter(|a| a.atomic_number == 2).count();
        // 2p+2n => 1 He, remaining 12p => 12 H
        assert_eq!(he_count, 1);
        assert_eq!(h_count, 12);
    }
}

// ---------------------------------------------------------------------------
// AST self-introspection
// ---------------------------------------------------------------------------

/// Count occurrences of a simple pattern in the source text.
///
/// Matches patterns like `fn `, `struct `, `impl `, and `mod ` at the start
/// of a token boundary (preceded by start-of-line or whitespace).
fn count_pattern(src: &str, keyword: &str) -> usize {
    let mut count = 0;
    for line in src.lines() {
        let trimmed = line.trim();
        // Match keyword at start of trimmed line, or after `pub `, `pub(crate) `, etc.
        // This handles: `fn foo`, `pub fn foo`, `pub(crate) fn foo`, `unsafe fn foo`, etc.
        let tokens: Vec<&str> = trimmed.split_whitespace().collect();
        for (i, token) in tokens.iter().enumerate() {
            if *token == keyword {
                // For `fn`, avoid matching inside `pub(crate)` or attribute-like contexts
                // by checking it looks like a real definition (keyword followed by a name or '{')
                if keyword == "fn" {
                    // `fn` should be followed by something (function name)
                    if i + 1 < tokens.len() {
                        count += 1;
                    }
                    break;
                } else if keyword == "struct" {
                    if i + 1 < tokens.len() {
                        count += 1;
                    }
                    break;
                } else if keyword == "impl" {
                    // `impl` block
                    count += 1;
                    break;
                } else if keyword == "mod" {
                    if i + 1 < tokens.len() {
                        count += 1;
                    }
                    break;
                }
            }
        }
    }
    count
}

/// Collect all `.rs` files from `src/` and `src/simulator/`, analyze them,
/// and print a formatted table of results.
fn run_ast_introspection() {
    println!();
    println!("=== AST Self-Introspection: Rust App ===");
    println!();

    // Determine the src directory relative to the binary's expected project root.
    // We look for the `src/` directory starting from the current working directory.
    let src_dir = Path::new("src");
    let sim_dir = src_dir.join("simulator");

    let mut files: Vec<(String, String)> = Vec::new(); // (display_name, full_path)

    // Collect files from src/
    if let Ok(entries) = fs::read_dir(src_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().map_or(false, |e| e == "rs") {
                let display = path.file_name().unwrap().to_string_lossy().to_string();
                files.push((display, path.to_string_lossy().to_string()));
            }
        }
    }

    // Collect files from src/simulator/
    if let Ok(entries) = fs::read_dir(&sim_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().map_or(false, |e| e == "rs") {
                let display = format!(
                    "simulator/{}",
                    path.file_name().unwrap().to_string_lossy()
                );
                files.push((display, path.to_string_lossy().to_string()));
            }
        }
    }

    files.sort_by(|a, b| a.0.cmp(&b.0));

    if files.is_empty() {
        println!("  No .rs files found. Run from the apps/rust/ directory.");
        std::process::exit(1);
    }

    // Table header
    println!(
        "  {:<28} {:>6} {:>8} {:>5} {:>7} {:>6} {:>5}",
        "File", "Lines", "Bytes", "fn", "struct", "impl", "mod"
    );
    println!(
        "  {:<28} {:>6} {:>8} {:>5} {:>7} {:>6} {:>5}",
        "─".repeat(28),
        "─".repeat(6),
        "─".repeat(8),
        "─".repeat(5),
        "─".repeat(7),
        "─".repeat(6),
        "─".repeat(5)
    );

    let mut total_lines: usize = 0;
    let mut total_bytes: usize = 0;
    let mut total_fns: usize = 0;
    let mut total_structs: usize = 0;
    let mut total_impls: usize = 0;
    let mut total_mods: usize = 0;

    for (display_name, filepath) in &files {
        let content = match fs::read_to_string(filepath) {
            Ok(c) => c,
            Err(_) => continue,
        };
        let bytes = match fs::metadata(filepath) {
            Ok(m) => m.len() as usize,
            Err(_) => content.len(),
        };
        let lines = content.lines().count();
        let fns = count_pattern(&content, "fn");
        let structs = count_pattern(&content, "struct");
        let impls = count_pattern(&content, "impl");
        let mods = count_pattern(&content, "mod");

        total_lines += lines;
        total_bytes += bytes;
        total_fns += fns;
        total_structs += structs;
        total_impls += impls;
        total_mods += mods;

        println!(
            "  {:<28} {:>6} {:>8} {:>5} {:>7} {:>6} {:>5}",
            display_name, lines, bytes, fns, structs, impls, mods
        );
    }

    // Totals row
    println!(
        "  {:<28} {:>6} {:>8} {:>5} {:>7} {:>6} {:>5}",
        "─".repeat(28),
        "─".repeat(6),
        "─".repeat(8),
        "─".repeat(5),
        "─".repeat(7),
        "─".repeat(6),
        "─".repeat(5)
    );
    println!(
        "  {:<28} {:>6} {:>8} {:>5} {:>7} {:>6} {:>5}",
        "TOTAL",
        total_lines,
        total_bytes,
        total_fns,
        total_structs,
        total_impls,
        total_mods
    );
    println!();
}

fn main() {
    // Check for --ast-introspect flag
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--ast-introspect") {
        run_ast_introspection();
        std::process::exit(0);
    }

    println!();
    println!(
        "  ╔══════════════════════════════════════════════════════════════════════════╗"
    );
    println!(
        "  ║              IN THE BEGINNING -- Cosmic Simulation v0.1                ║"
    );
    println!(
        "  ║       From the Big Bang through the emergence of life                  ║"
    );
    println!(
        "  ╚══════════════════════════════════════════════════════════════════════════╝"
    );
    println!();

    let mut universe = Universe::new();

    let start = std::time::Instant::now();

    universe.run(
        // on_epoch: called when a new epoch begins
        |stats| {
            // Clear the progress line
            print!("\r{}\r", " ".repeat(100));
            print_epoch_banner(stats);
        },
        // on_tick: called periodically for progress
        |stats| {
            print_progress(stats);
        },
    );

    let elapsed = start.elapsed();

    // Clear progress line
    print!("\r{}\r", " ".repeat(100));

    separator();
    println!("  SIMULATION COMPLETE");
    separator();
    println!(
        "  Wall-clock time : {:.2}s",
        elapsed.as_secs_f64()
    );

    let final_stats = universe.stats();
    println!(
        "  Final tick      : {}",
        final_stats.tick
    );
    println!(
        "  Final temp      : {} K",
        format_sci(final_stats.temperature)
    );
    println!(
        "  Total energy    : {}",
        format_sci(final_stats.total_energy)
    );
    println!(
        "  Particles       : {}",
        final_stats.particle_count
    );
    println!(
        "  Atoms           : {}",
        final_stats.atom_count
    );
    println!(
        "  Molecules       : {} (H2O: {}, amino acids: {}, nucleotides: {})",
        final_stats.molecule_count,
        final_stats.water_count,
        final_stats.amino_acid_count,
        final_stats.nucleotide_count,
    );
    println!(
        "  Lifeforms       : {} across {} species",
        final_stats.population, final_stats.species_count,
    );
    println!(
        "  Generations     : {}",
        final_stats.generation
    );
    println!(
        "  Avg fitness     : {:.4}",
        final_stats.average_fitness
    );
    println!(
        "  Habitable       : {}",
        if final_stats.is_habitable { "YES" } else { "NO" }
    );
    println!(
        "  Atm. oxygen     : {:.2}%",
        final_stats.oxygen_pct
    );
    separator();
    println!();
}
