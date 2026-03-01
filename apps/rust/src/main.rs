//! In The Beginning -- A cosmic simulation from the Big Bang to life.
//!
//! CLI entry point that runs the full simulation and reports progress
//! through each of the 13 cosmic epochs.

mod simulator;

use simulator::universe::{SimStats, Universe};

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

fn main() {
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
