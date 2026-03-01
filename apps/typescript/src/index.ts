#!/usr/bin/env node

/**
 * In The Beginning - Cosmic Evolution Simulator (TypeScript)
 *
 * CLI entry point that runs the full simulation from the Big Bang
 * through the emergence of complex life, with formatted terminal output.
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

import {
    Universe,
    type SimulationSnapshot,
} from "./simulator.js";

import {
    PRESENT_EPOCH,
    EPOCHS,
    type EpochInfo,
} from "./constants.js";

// -- Terminal formatting helpers -----------------------------------------------

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

const EPOCH_COLORS: Record<string, string> = {
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

function formatTemp(t: number): string {
    if (t >= 1e9)  return `${(t / 1e9).toFixed(1)} GK`;
    if (t >= 1e6)  return `${(t / 1e6).toFixed(1)} MK`;
    if (t >= 1e3)  return `${(t / 1e3).toFixed(1)} kK`;
    return `${t.toFixed(1)} K`;
}

function formatNumber(n: number): string {
    if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(1)}k`;
    return String(n);
}

function progressBar(fraction: number, width: number = 40): string {
    const filled = Math.round(fraction * width);
    const empty = width - filled;
    return "[" + "\u2588".repeat(filled) + "\u2591".repeat(empty) + "]";
}

function formatCounts(counts: Record<string, number>): string {
    return Object.entries(counts)
        .sort(([, a], [, b]) => b - a)
        .map(([k, v]) => `${k}:${v}`)
        .join(" ");
}

// -- Output routines ----------------------------------------------------------

function printBanner(): void {
    console.log();
    console.log(`${BOLD}${CYAN}  \u2554${"═".repeat(58)}\u2557${RESET}`);
    console.log(`${BOLD}${CYAN}  \u2551${" ".repeat(58)}\u2551${RESET}`);
    console.log(`${BOLD}${CYAN}  \u2551          ${WHITE}I N   T H E   B E G I N N I N G${CYAN}                \u2551${RESET}`);
    console.log(`${BOLD}${CYAN}  \u2551          ${DIM}Cosmic Evolution Simulator${RESET}${BOLD}${CYAN}                   \u2551${RESET}`);
    console.log(`${BOLD}${CYAN}  \u2551          ${DIM}TypeScript Edition${RESET}${BOLD}${CYAN}                           \u2551${RESET}`);
    console.log(`${BOLD}${CYAN}  \u2551${" ".repeat(58)}\u2551${RESET}`);
    console.log(`${BOLD}${CYAN}  \u255A${"═".repeat(58)}\u255D${RESET}`);
    console.log();
}

function printEpochTransition(epochName: string, description: string): void {
    const color = EPOCH_COLORS[epochName] || WHITE;
    console.log();
    console.log(`${BOLD}${color}  \u2500\u2500 ${epochName.toUpperCase()} EPOCH ${"\u2500".repeat(Math.max(2, 50 - epochName.length))}${RESET}`);
    console.log(`${DIM}     ${description}${RESET}`);
    console.log();
}

function printSnapshot(snap: SimulationSnapshot): void {
    const color = EPOCH_COLORS[snap.epoch] || WHITE;
    const pct = snap.tick / PRESENT_EPOCH;
    const bar = progressBar(pct);

    let line = `  ${DIM}t=${String(snap.tick).padStart(6)}${RESET}`;
    line += ` ${color}${bar}${RESET}`;
    line += ` ${DIM}${(pct * 100).toFixed(1)}%${RESET}`;
    console.log(line);

    // Temperature
    console.log(`${DIM}           Temp: ${RESET}${formatTemp(snap.temperature)}`);

    // Particles
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

    // DNA
    if (snap.dnaSequences.length > 0) {
        console.log(`${DIM}            DNA: ${RESET}${CYAN}${snap.dnaSequences[0]}...${RESET}`);
    }

    console.log();
}

function printFinalReport(universe: Universe, elapsedMs: number): void {
    const snap = universe.snapshot();
    console.log();
    console.log(`${BOLD}${WHITE}  ${"═".repeat(58)}${RESET}`);
    console.log(`${BOLD}${WHITE}   SIMULATION COMPLETE${RESET}`);
    console.log(`${BOLD}${WHITE}  ${"═".repeat(58)}${RESET}`);
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
        const entries = Object.entries(snap.elementCounts).sort(([, a], [, b]) => b - a);
        for (const [elem, count] of entries) {
            const barWidth = Math.min(30, Math.round(count / Math.max(1, snap.atoms) * 30));
            const bar = "\u2588".repeat(barWidth);
            console.log(`${DIM}     ${elem.padEnd(4)}${RESET}${GREEN}${bar}${RESET} ${count}`);
        }
    }

    if (snap.molecules > 0) {
        console.log();
        console.log(`${BOLD}   Final Molecule Counts:${RESET}`);
        const entries = Object.entries(snap.moleculeCounts).sort(([, a], [, b]) => b - a);
        for (const [mol, count] of entries) {
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

// -- AST Self-Introspection ---------------------------------------------------

function runAstIntrospection(): void {
    console.log(`\n${BOLD}${CYAN}=== AST Self-Introspection: TypeScript App ===${RESET}\n`);

    const srcDir = dirname(fileURLToPath(import.meta.url));
    // Read .ts source files from the source directory (one level up from dist/)
    const tsSrcDir = srcDir.replace(/[/\\]dist$/, "/src");
    let scanDir = tsSrcDir;
    try {
        readdirSync(scanDir);
    } catch {
        scanDir = srcDir;
    }

    const files = readdirSync(scanDir)
        .filter(f => f.endsWith(".ts") || f.endsWith(".js"))
        .sort();

    let totalLines = 0;
    let totalBytes = 0;
    let totalFunctions = 0;
    let totalClasses = 0;
    let totalInterfaces = 0;
    let totalTypes = 0;

    console.log(`  ${"File".padEnd(28)} ${"Lines".padStart(6)} ${"Bytes".padStart(8)} ${"Funcs".padStart(6)} ${"Classes".padStart(8)} ${"Ifaces".padStart(7)} ${"Types".padStart(6)}`);
    console.log(`  ${"─".repeat(28)} ${"─".repeat(6)} ${"─".repeat(8)} ${"─".repeat(6)} ${"─".repeat(8)} ${"─".repeat(7)} ${"─".repeat(6)}`);

    for (const file of files) {
        const fpath = join(scanDir, file);
        const src = readFileSync(fpath, "utf-8");
        const lines = src.split("\n").length;
        const bytes = statSync(fpath).size;

        const funcMatches = src.match(/(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:\([^)]*\)|[^=])\s*=>)/g) || [];
        const classMatches = src.match(/class\s+\w+/g) || [];
        const ifaceMatches = src.match(/interface\s+\w+/g) || [];
        const typeMatches = src.match(/type\s+\w+\s*[<=]/g) || [];

        totalLines += lines;
        totalBytes += bytes;
        totalFunctions += funcMatches.length;
        totalClasses += classMatches.length;
        totalInterfaces += ifaceMatches.length;
        totalTypes += typeMatches.length;

        console.log(`  ${file.padEnd(28)} ${String(lines).padStart(6)} ${String(bytes).padStart(8)} ${String(funcMatches.length).padStart(6)} ${String(classMatches.length).padStart(8)} ${String(ifaceMatches.length).padStart(7)} ${String(typeMatches.length).padStart(6)}`);
    }

    console.log(`  ${"─".repeat(28)} ${"─".repeat(6)} ${"─".repeat(8)} ${"─".repeat(6)} ${"─".repeat(8)} ${"─".repeat(7)} ${"─".repeat(6)}`);
    console.log(`  ${"TOTAL".padEnd(28)} ${String(totalLines).padStart(6)} ${String(totalBytes).padStart(8)} ${String(totalFunctions).padStart(6)} ${String(totalClasses).padStart(8)} ${String(totalInterfaces).padStart(7)} ${String(totalTypes).padStart(6)}`);
    console.log();
}

// -- Main ---------------------------------------------------------------------

function parseArgs(): { stepSize: number; maxTicks: number; reportInterval: number; seed: number } {
    const args = process.argv.slice(2);
    let stepSize = 100;
    let maxTicks = PRESENT_EPOCH;
    let reportInterval = 5000;
    let seed = 42;

    for (let i = 0; i < args.length; i++) {
        if ((args[i] === "--step" || args[i] === "-s") && args[i + 1]) {
            stepSize = parseInt(args[++i], 10);
        } else if ((args[i] === "--max" || args[i] === "-m") && args[i + 1]) {
            maxTicks = parseInt(args[++i], 10);
        } else if ((args[i] === "--interval" || args[i] === "-i") && args[i + 1]) {
            reportInterval = parseInt(args[++i], 10);
        } else if ((args[i] === "--seed") && args[i + 1]) {
            seed = parseInt(args[++i], 10);
        } else if (args[i] === "--ast-introspect") {
            runAstIntrospection();
            process.exit(0);
        } else if (args[i] === "--help" || args[i] === "-h") {
            console.log("Usage: node dist/index.js [options]");
            console.log();
            console.log("Options:");
            console.log("  -s, --step <n>      Simulation step size (default: 100)");
            console.log("  -m, --max <n>       Max ticks (default: 300000)");
            console.log("  -i, --interval <n>  Report every N ticks (default: 5000)");
            console.log("  --seed <n>          Random seed (default: 42)");
            console.log("  --ast-introspect    Show AST self-introspection of source files");
            console.log("  -h, --help          Show this help");
            console.log();
            process.exit(0);
        }
    }

    return { stepSize, maxTicks, reportInterval, seed };
}

function main(): void {
    printBanner();

    const { stepSize, maxTicks, reportInterval, seed } = parseArgs();

    console.log(`${DIM}  Seed: ${seed} | Step size: ${stepSize} | Max ticks: ${formatNumber(maxTicks)} | Report interval: ${formatNumber(reportInterval)}${RESET}`);
    console.log();

    const universe = new Universe(seed, maxTicks, stepSize);
    let lastEpoch = "Void";
    let lastReportTick = 0;

    const startTime = performance.now();

    while (universe.tick < maxTicks) {
        universe.step();

        // Detect epoch transition
        if (universe.currentEpochName !== lastEpoch) {
            lastEpoch = universe.currentEpochName;
            // Find description from EPOCHS
            const epochInfo = EPOCHS.find((e: EpochInfo) => e.name === lastEpoch);
            const desc = epochInfo ? epochInfo.description : "";
            printEpochTransition(lastEpoch, desc);
        }

        // Periodic snapshot
        if (universe.tick - lastReportTick >= reportInterval) {
            lastReportTick = universe.tick;
            const snap = universe.snapshot();
            printSnapshot(snap);
        }
    }

    const totalMs = performance.now() - startTime;
    printFinalReport(universe, totalMs);
}

main();
