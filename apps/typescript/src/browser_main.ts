/**
 * Browser entry point for the In The Beginning cosmic sonification app.
 *
 * Sets up:
 *   - Canvas-based spectrogram visualisation (AnalyserNode FFT data)
 *   - Universe simulation stepping
 *   - AudioEngine sonification
 *   - User controls (volume, tempo, mute)
 *   - Click-to-start overlay (required by browser autoplay policy)
 *   - Epoch transition visual effects
 */

import { Universe, type SimulationSnapshot } from "./simulator.js";
import { AudioEngine } from "./audio_engine.js";
import { EPOCHS } from "./constants.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SIM_STEP_SIZE = 100;
const SIM_MAX_TICKS = 300_000;
const STEPS_PER_FRAME = 2;            // simulation steps per animation frame
const BAR_COUNT = 128;                  // number of spectrogram bars

// Epoch colour palette (CSS colours)
const EPOCH_COLORS: Record<string, string> = {
    "Planck":          "#ff4444",
    "Inflation":       "#ff6633",
    "Electroweak":     "#cc44ff",
    "Quark":           "#aa33ee",
    "Hadron":          "#ffcc00",
    "Nucleosynthesis": "#ffaa00",
    "Recombination":   "#44ddff",
    "Star Formation":  "#3388ff",
    "Solar System":    "#5566ff",
    "Earth":           "#33cc66",
    "Life":            "#22ee88",
    "DNA Era":         "#00ffaa",
    "Present":         "#ffffff",
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let canvas: HTMLCanvasElement;
let ctx2d: CanvasRenderingContext2D;
let universe: Universe;
let audio: AudioEngine;
let running = false;
let animId = 0;
let lastEpoch = "";

// UI elements (grabbed in setup)
let epochBar: HTMLElement;
let epochLabel: HTMLElement;
let tickLabel: HTMLElement;
let tempLabel: HTMLElement;
let particleLabel: HTMLElement;

// ---------------------------------------------------------------------------
// Spectrogram drawing
// ---------------------------------------------------------------------------

function drawSpectrogram(): void {
    const width = canvas.width;
    const height = canvas.height;
    const analyser = audio.analyser;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    // Fade existing content (trail effect)
    ctx2d.fillStyle = "rgba(0, 0, 8, 0.15)";
    ctx2d.fillRect(0, 0, width, height);

    const barWidth = width / BAR_COUNT;
    const step = Math.floor(bufferLength / BAR_COUNT);

    const snap = universe.snapshot();
    const epochColor = EPOCH_COLORS[snap.epoch] ?? "#ffffff";

    for (let i = 0; i < BAR_COUNT; i++) {
        // Average a bin range
        let sum = 0;
        for (let j = 0; j < step; j++) {
            sum += dataArray[i * step + j];
        }
        const avg = sum / step;
        const barHeight = (avg / 255) * height * 0.85;

        const x = i * barWidth;
        const y = height - barHeight;

        // Gradient per bar
        const gradient = ctx2d.createLinearGradient(x, height, x, y);
        gradient.addColorStop(0, epochColor);
        gradient.addColorStop(0.6, adjustAlpha(epochColor, 0.5));
        gradient.addColorStop(1, "transparent");

        ctx2d.fillStyle = gradient;
        ctx2d.fillRect(x, y, barWidth - 1, barHeight);
    }
}

function adjustAlpha(hex: string, alpha: number): string {
    // Convert #rrggbb to rgba
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

// ---------------------------------------------------------------------------
// Epoch transition effect
// ---------------------------------------------------------------------------

function flashEpochTransition(epochName: string): void {
    const color = EPOCH_COLORS[epochName] ?? "#ffffff";
    // Brief white flash on canvas
    ctx2d.fillStyle = adjustAlpha(color, 0.3);
    ctx2d.fillRect(0, 0, canvas.width, canvas.height);

    // Update epoch indicator bar
    epochBar.style.background = `linear-gradient(90deg, ${color}, transparent)`;
    epochLabel.textContent = epochName.toUpperCase();
}

// ---------------------------------------------------------------------------
// HUD update
// ---------------------------------------------------------------------------

function updateHUD(snap: SimulationSnapshot): void {
    const pct = ((snap.tick / SIM_MAX_TICKS) * 100).toFixed(1);
    tickLabel.textContent = `Tick ${snap.tick.toLocaleString()} / ${SIM_MAX_TICKS.toLocaleString()} (${pct}%)`;
    tempLabel.textContent = formatTemp(snap.temperature);

    let detail = `Particles: ${snap.particles}`;
    if (snap.atoms > 0) detail += ` | Atoms: ${snap.atoms}`;
    if (snap.molecules > 0) detail += ` | Molecules: ${snap.molecules}`;
    if (snap.cells > 0) detail += ` | Cells: ${snap.cells}`;
    particleLabel.textContent = detail;
}

function formatTemp(t: number): string {
    if (t >= 1e9) return `${(t / 1e9).toFixed(1)} GK`;
    if (t >= 1e6) return `${(t / 1e6).toFixed(1)} MK`;
    if (t >= 1e3) return `${(t / 1e3).toFixed(1)} kK`;
    return `${t.toFixed(1)} K`;
}

// ---------------------------------------------------------------------------
// Animation loop
// ---------------------------------------------------------------------------

function loop(): void {
    if (!running) return;

    // Advance simulation
    for (let i = 0; i < STEPS_PER_FRAME; i++) {
        if (universe.tick < SIM_MAX_TICKS) {
            universe.step();
        }
    }

    const snap = universe.snapshot();

    // Epoch transition detection
    if (snap.epoch !== lastEpoch) {
        lastEpoch = snap.epoch;
        flashEpochTransition(snap.epoch);
    }

    // Sonify
    audio.sonifySnapshot(snap);

    // Draw
    drawSpectrogram();
    updateHUD(snap);

    // Continue or finish
    if (universe.tick < SIM_MAX_TICKS) {
        animId = requestAnimationFrame(loop);
    } else {
        running = false;
        epochLabel.textContent = "SIMULATION COMPLETE";
    }
}

// ---------------------------------------------------------------------------
// Setup & start
// ---------------------------------------------------------------------------

function resizeCanvas(): void {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

function setup(): void {
    // Grab DOM elements
    canvas = document.getElementById("spectrogram") as HTMLCanvasElement;
    ctx2d = canvas.getContext("2d")!;
    epochBar = document.getElementById("epoch-bar")!;
    epochLabel = document.getElementById("epoch-label")!;
    tickLabel = document.getElementById("tick-label")!;
    tempLabel = document.getElementById("temp-label")!;
    particleLabel = document.getElementById("particle-label")!;

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Create simulation and audio engine
    universe = new Universe(42, SIM_MAX_TICKS, SIM_STEP_SIZE);
    audio = new AudioEngine();

    // --- Controls ---
    const volumeSlider = document.getElementById("volume") as HTMLInputElement;
    const tempoSlider = document.getElementById("tempo") as HTMLInputElement;
    const muteBtn = document.getElementById("mute-btn") as HTMLButtonElement;

    volumeSlider.addEventListener("input", () => {
        audio.setVolume(parseFloat(volumeSlider.value));
    });

    tempoSlider.addEventListener("input", () => {
        audio.setTempoScale(parseFloat(tempoSlider.value));
    });

    let muted = false;
    muteBtn.addEventListener("click", () => {
        muted = !muted;
        audio.setMuted(muted);
        muteBtn.textContent = muted ? "Unmute" : "Mute";
    });

    // --- Click-to-start overlay ---
    const overlay = document.getElementById("overlay")!;
    overlay.addEventListener("click", async () => {
        audio.init();
        await audio.resume();
        overlay.classList.add("hidden");
        running = true;
        lastEpoch = "";
        animId = requestAnimationFrame(loop);
    });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

if (typeof window !== "undefined") {
    window.addEventListener("DOMContentLoaded", setup);
}
