#!/usr/bin/env node

/**
 * In The Beginning - Cosmic Evolution Simulator (Node.js)
 *
 * CLI entry point that runs the full simulation from the Big Bang
 * through the emergence of complex life, with formatted terminal output.
 */

import { Universe, EPOCHS } from './universe.js';
import { PRESENT_EPOCH } from './constants.js';

// ─── Terminal formatting helpers ─────────────────────────────────────────────

const BOLD    = "\x1b[1m";
const DIM     = "\x1b[2m";
const RESET   = "\x1b[0m";
const RED     = "\x1b[31m";
const GREEN   = "\x1b[32m";
const YELLOW  = "\x1b[33m";
const BLUE    = "\x1b[34m";
const MAGENTA = "\x1b[35m";
const CYAN    = "\x1b[36m";
const WHITE   = "\x1b[37m";

const EPOCH_COLORS = {
    "Planck":          RED,
    "Inflation":       RED,
    "Electroweak":     MAGENTA,
    "Quark":           MAGENTA,
    "Hadron":          YELLOW,
    "Nucleosynthesis": YELLOW,
    "Recombination":   CYAN,
    "Star Formation":  BLUE,
    "Solar System":    BLUE,
    "Earth":           GREEN,
    "Life":            GREEN,
    "DNA Era":         GREEN,
    "Present":         WHITE,
};

function formatTemp(t) {
    if (t >= 1e9)  return `${(t / 1e9).toFixed(1)} GK`;
    if (t >= 1e6)  return `${(t / 1e6).toFixed(1)} MK`;
    if (t >= 1e3)  return `${(t / 1e3).toFixed(1)} kK`;
    return `${t.toFixed(1)} K`;
}

function formatNumber(n) {
    if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(1)}k`;
    return String(n);
}

function progressBar(fraction, width = 30) {
    const filled = Math.round(fraction * width);
    const empty = width - filled;
    const bar = "█".repeat(filled) + "░".repeat(empty);
    return `[${bar}]`;
}

function formatCounts(counts) {
    return Object.entries(counts)
        .sort(([, a], [, b]) => b - a)
        .map(([k, v]) => `${k}:${v}`)
        .join(" ");
}


// ─── AST Self-Introspection ──────────────────────────────────────────────────

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function runAstIntrospection() {
    console.log(`\n${BOLD}${CYAN}=== AST Self-Introspection: Node.js App ===${RESET}\n`);

    const files = readdirSync(__dirname)
        .filter(f => f.endsWith('.js') && !f.startsWith('.'))
        .sort();

    let totalLines = 0;
    let totalBytes = 0;
    let totalFunctions = 0;
    let totalClasses = 0;
    let totalExports = 0;

    console.log(`  ${'File'.padEnd(28)} ${'Lines'.padStart(6)} ${'Bytes'.padStart(8)} ${'Funcs'.padStart(6)} ${'Classes'.padStart(8)} ${'Exports'.padStart(8)}`);
    console.log(`  ${'─'.repeat(28)} ${'─'.repeat(6)} ${'─'.repeat(8)} ${'─'.repeat(6)} ${'─'.repeat(8)} ${'─'.repeat(8)}`);

    for (const file of files) {
        const fpath = join(__dirname, file);
        const src = readFileSync(fpath, 'utf-8');
        const lines = src.split('\n').length;
        const bytes = statSync(fpath).size;

        // Simple regex-based analysis
        const funcMatches = src.match(/(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:\([^)]*\)|[^=])\s*=>|(?:get|set)\s+\w+\s*\()/g) || [];
        const classMatches = src.match(/class\s+\w+/g) || [];
        const exportMatches = src.match(/export\s+(?:class|function|const|let|default)/g) || [];

        totalLines += lines;
        totalBytes += bytes;
        totalFunctions += funcMatches.length;
        totalClasses += classMatches.length;
        totalExports += exportMatches.length;

        console.log(`  ${file.padEnd(28)} ${String(lines).padStart(6)} ${String(bytes).padStart(8)} ${String(funcMatches.length).padStart(6)} ${String(classMatches.length).padStart(8)} ${String(exportMatches.length).padStart(8)}`);
    }

    console.log(`  ${'─'.repeat(28)} ${'─'.repeat(6)} ${'─'.repeat(8)} ${'─'.repeat(6)} ${'─'.repeat(8)} ${'─'.repeat(8)}`);
    console.log(`  ${'TOTAL'.padEnd(28)} ${String(totalLines).padStart(6)} ${String(totalBytes).padStart(8)} ${String(totalFunctions).padStart(6)} ${String(totalClasses).padStart(8)} ${String(totalExports).padStart(8)}`);
    console.log();
}


// ─── Main simulation ────────────────────────────────────────────────────────

function printBanner() {
    console.log();
    console.log(`${BOLD}${CYAN}  ╔══════════════════════════════════════════════════════════╗${RESET}`);
    console.log(`${BOLD}${CYAN}  ║                                                          ║${RESET}`);
    console.log(`${BOLD}${CYAN}  ║          ${WHITE}I N   T H E   B E G I N N I N G${CYAN}                ║${RESET}`);
    console.log(`${BOLD}${CYAN}  ║          ${DIM}Cosmic Evolution Simulator${RESET}${BOLD}${CYAN}                   ║${RESET}`);
    console.log(`${BOLD}${CYAN}  ║          ${DIM}Node.js Edition${RESET}${BOLD}${CYAN}                              ║${RESET}`);
    console.log(`${BOLD}${CYAN}  ║                                                          ║${RESET}`);
    console.log(`${BOLD}${CYAN}  ╚══════════════════════════════════════════════════════════╝${RESET}`);
    console.log();
}

function printEpochTransition(epochName, description) {
    const color = EPOCH_COLORS[epochName] || WHITE;
    console.log();
    console.log(`${BOLD}${color}  ── ${epochName.toUpperCase()} EPOCH ─────────────────────────────────────────${RESET}`);
    console.log(`${DIM}     ${description}${RESET}`);
    console.log();
}

function printSnapshot(snap, elapsed) {
    const color = EPOCH_COLORS[snap.epoch] || WHITE;
    const pct = snap.tick / PRESENT_EPOCH;
    const bar = progressBar(pct, 40);

    let line = `  ${DIM}t=${String(snap.tick).padStart(6)}${RESET}`;
    line += ` ${color}${bar}${RESET}`;
    line += ` ${DIM}${(pct * 100).toFixed(1)}%${RESET}`;

    console.log(line);

    // Temperature
    console.log(`${DIM}           Temp: ${RESET}${formatTemp(snap.temperature)}`);

    // Particle counts
    if (snap.particles > 0) {
        const pc = formatCounts(snap.particleCounts);
        console.log(`${DIM}      Particles: ${RESET}${formatNumber(snap.particles)} ${DIM}(${pc})${RESET}`);
    }

    // Atoms
    if (snap.atoms > 0) {
        const ec = formatCounts(snap.elementCounts);
        console.log(`${DIM}          Atoms: ${RESET}${formatNumber(snap.atoms)} ${DIM}(${ec})${RESET}`);
    }

    // Molecules
    if (snap.molecules > 0) {
        const mc = formatCounts(snap.moleculeCounts);
        console.log(`${DIM}      Molecules: ${RESET}${formatNumber(snap.molecules)} ${DIM}(${mc})${RESET}`);
    }

    // Biology
    if (snap.cells > 0) {
        console.log(`${DIM}          Cells: ${RESET}${snap.cells} ${DIM}gen=${snap.generation} fit=${snap.fitness.toFixed(3)} mut=${snap.mutations}${RESET}`);
    }

    // Habitability
    if (snap.isHabitable) {
        console.log(`${DIM}     Habitable: ${RESET}${GREEN}YES${RESET} ${DIM}UV=${snap.uvIntensity.toFixed(3)} CR=${snap.cosmicRayFlux.toFixed(3)}${RESET}`);
    }

    // DNA sequences
    if (snap.dnaSequences.length > 0) {
        console.log(`${DIM}            DNA: ${RESET}${CYAN}${snap.dnaSequences[0]}...${RESET}`);
    }

    console.log();
}

function printFinalReport(universe, elapsedMs) {
    const snap = universe.snapshot();
    console.log();
    console.log(`${BOLD}${WHITE}  ══════════════════════════════════════════════════════════${RESET}`);
    console.log(`${BOLD}${WHITE}   SIMULATION COMPLETE${RESET}`);
    console.log(`${BOLD}${WHITE}  ══════════════════════════════════════════════════════════${RESET}`);
    console.log();
    console.log(`${DIM}   Runtime:          ${RESET}${(elapsedMs / 1000).toFixed(2)}s`);
    console.log(`${DIM}   Total ticks:      ${RESET}${formatNumber(universe.tick)}`);
    console.log(`${DIM}   Final epoch:      ${RESET}${snap.epoch}`);
    console.log(`${DIM}   Temperature:      ${RESET}${formatTemp(snap.temperature)}`);
    console.log();
    console.log(`${BOLD}   Cumulative Statistics:${RESET}`);
    console.log(`${DIM}   Particles created: ${RESET}${formatNumber(universe.particlesCreated)}`);
    console.log(`${DIM}   Atoms formed:      ${RESET}${formatNumber(universe.atomsFormed)}`);
    console.log(`${DIM}   Molecules formed:  ${RESET}${formatNumber(universe.moleculesFormed)}`);
    console.log(`${DIM}   Cells born:        ${RESET}${formatNumber(universe.cellsBorn)}`);
    console.log(`${DIM}   Mutations:         ${RESET}${formatNumber(universe.mutationCount)}`);

    if (snap.atoms > 0) {
        console.log();
        console.log(`${BOLD}   Final Element Counts:${RESET}`);
        for (const [elem, count] of Object.entries(snap.elementCounts).sort(([, a], [, b]) => b - a)) {
            const bar = "█".repeat(Math.min(30, Math.round(count / Math.max(1, snap.atoms) * 30)));
            console.log(`${DIM}     ${elem.padEnd(4)}${RESET}${GREEN}${bar}${RESET} ${count}`);
        }
    }

    if (snap.molecules > 0) {
        console.log();
        console.log(`${BOLD}   Final Molecule Counts:${RESET}`);
        for (const [mol, count] of Object.entries(snap.moleculeCounts).sort(([, a], [, b]) => b - a)) {
            console.log(`${DIM}     ${mol.padEnd(16)}${RESET}${count}`);
        }
    }

    if (snap.cells > 0) {
        console.log();
        console.log(`${BOLD}   Biosphere:${RESET}`);
        console.log(`${DIM}     Population:      ${RESET}${snap.cells}`);
        console.log(`${DIM}     Generations:     ${RESET}${snap.generation}`);
        console.log(`${DIM}     Avg fitness:     ${RESET}${snap.fitness.toFixed(4)}`);
        console.log(`${DIM}     Total mutations: ${RESET}${snap.mutations}`);
        if (snap.dnaSequences.length > 0) {
            console.log(`${DIM}     Sample DNA:      ${RESET}${CYAN}${snap.dnaSequences[0]}...${RESET}`);
        }
    }

    console.log();
    console.log(`${DIM}  From quantum foam to conscious observers -- the universe persists.${RESET}`);
    console.log();
}


function main() {
    printBanner();

    // Parse CLI args
    const args = process.argv.slice(2);
    let stepSize = 100;  // Default step size for speed
    let maxTicks = PRESENT_EPOCH;
    let reportInterval = 5000;

    for (let i = 0; i < args.length; i++) {
        if ((args[i] === "--step" || args[i] === "-s") && args[i + 1]) {
            stepSize = parseInt(args[++i], 10);
        } else if ((args[i] === "--max" || args[i] === "-m") && args[i + 1]) {
            maxTicks = parseInt(args[++i], 10);
        } else if ((args[i] === "--interval" || args[i] === "-i") && args[i + 1]) {
            reportInterval = parseInt(args[++i], 10);
        } else if (args[i] === "--ast-introspect") {
            runAstIntrospection();
            process.exit(0);
        } else if (args[i] === "--help" || args[i] === "-h") {
            console.log("Usage: node index.js [options]");
            console.log();
            console.log("Options:");
            console.log("  -s, --step <n>      Simulation step size (default: 100)");
            console.log("  -m, --max <n>       Max ticks (default: 300000)");
            console.log("  -i, --interval <n>  Report every N ticks (default: 5000)");
            console.log("  --ast-introspect    Show AST self-introspection of source files");
            console.log("  -h, --help          Show this help");
            console.log();
            process.exit(0);
        }
    }

    console.log(`${DIM}  Step size: ${stepSize} | Max ticks: ${formatNumber(maxTicks)} | Report interval: ${formatNumber(reportInterval)}${RESET}`);
    console.log();

    const universe = new Universe(maxTicks, stepSize);
    let lastEpoch = "Void";
    let lastReportTick = 0;

    const startTime = performance.now();

    while (universe.tick < maxTicks) {
        const epochChanged = universe.step();

        // Print epoch transition
        if (epochChanged && universe.currentEpochName !== lastEpoch) {
            lastEpoch = universe.currentEpochName;
            printEpochTransition(
                universe.currentEpochName,
                universe._getEpochDescription(),
            );
        }

        // Periodic snapshot
        if (universe.tick - lastReportTick >= reportInterval) {
            lastReportTick = universe.tick;
            const snap = universe.snapshot();
            const elapsed = performance.now() - startTime;
            printSnapshot(snap, elapsed);
        }
    }

    const totalMs = performance.now() - startTime;
    printFinalReport(universe, totalMs);
}

main();
