/**
 * AudioEngine -- maps simulation snapshots to sound via the Web Audio API.
 *
 * The engine maintains persistent nodes (master gain, compressor, global
 * filter, analyser) and spawns transient instrument voices through the
 * helpers in instruments.ts whenever simulation events occur.
 *
 * Sonification design
 * -------------------
 *   Epoch index  ->  musical key  (C, D, E, F#, G#, Bb cycle)
 *   Temperature  ->  global lowpass filter cutoff
 *   Particle count -> reverb wet/dry mix (more particles = wetter)
 *
 *   Quantum epoch   (0-4)  : high sine blips, random panning
 *   Atomic epoch    (5-7)  : harmonic stacking / overtone series
 *   Chemistry epoch (8-9)  : FM bell tones on bond formation
 *   Biology epoch   (10-12): rhythmic pulses, DNA melody sequences
 */

import type { SimulationSnapshot } from "./simulator.js";
import {
    createSineBlip,
    createBellTone,
    createPulse,
    createPad,
    createSequence,
    mtof,
    clamp,
} from "./instruments.js";

// ---------------------------------------------------------------------------
// Epoch -> musical key root (MIDI note number, all in octave 4)
// Cycle: C  D  E  F#  G#  Bb  C  D  E  F#  G#  Bb  C
// ---------------------------------------------------------------------------
const EPOCH_ROOTS: number[] = [
    60, // 0  Planck       C4
    62, // 1  Inflation    D4
    64, // 2  Electroweak  E4
    66, // 3  Quark        F#4
    68, // 4  Hadron       G#4
    70, // 5  Nucleosyn    Bb4
    72, // 6  Recombination C5
    74, // 7  Star Form    D5
    76, // 8  Solar System E5
    78, // 9  Earth        F#5
    80, // 10 Life         G#5
    82, // 11 DNA Era      Bb5
    84, // 12 Present      C6
];

// Epoch names in order, matching EPOCHS from constants.ts
const EPOCH_NAMES: string[] = [
    "Planck", "Inflation", "Electroweak", "Quark", "Hadron",
    "Nucleosynthesis", "Recombination", "Star Formation",
    "Solar System", "Earth", "Life", "DNA Era", "Present",
];

// ---------------------------------------------------------------------------
// Convolver impulse response generator (simple algorithmic reverb)
// ---------------------------------------------------------------------------

function createImpulseResponse(
    ctx: AudioContext,
    duration: number = 2.0,
    decay: number = 2.0,
): AudioBuffer {
    const length = Math.floor(ctx.sampleRate * duration);
    const buffer = ctx.createBuffer(2, length, ctx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
        const data = buffer.getChannelData(ch);
        for (let i = 0; i < length; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
        }
    }
    return buffer;
}

// ---------------------------------------------------------------------------
// AudioEngine
// ---------------------------------------------------------------------------

export class AudioEngine {
    ctx!: AudioContext;
    masterGain!: GainNode;
    compressor!: DynamicsCompressorNode;
    globalFilter!: BiquadFilterNode;
    analyser!: AnalyserNode;
    convolver!: ConvolverNode;
    convolverGain!: GainNode;
    dryGain!: GainNode;

    private _initialized = false;
    private _lastEpochIndex = -1;
    private _lastParticleCount = 0;
    private _padNode: GainNode | null = null;
    private _padScheduledEnd = 0;
    private _lastBlipTime = 0;
    private _lastBellTime = 0;
    private _lastPulseTime = 0;
    private _lastSequenceTime = 0;
    private _muted = false;
    private _volume = 0.7;
    private _tempoScale = 1.0;

    // -----------------------------------------------------------------------
    // Lifecycle
    // -----------------------------------------------------------------------

    /**
     * Create AudioContext and the persistent signal chain:
     *   instruments -> globalFilter -> dry / wet split -> compressor -> masterGain -> destination
     */
    init(): void {
        if (this._initialized) return;

        this.ctx = new AudioContext();

        // Master gain (user volume control)
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.setValueAtTime(this._volume, this.ctx.currentTime);
        this.masterGain.connect(this.ctx.destination);

        // Compressor (keep peaks in check)
        this.compressor = this.ctx.createDynamicsCompressor();
        this.compressor.threshold.setValueAtTime(-24, this.ctx.currentTime);
        this.compressor.knee.setValueAtTime(12, this.ctx.currentTime);
        this.compressor.ratio.setValueAtTime(4, this.ctx.currentTime);
        this.compressor.attack.setValueAtTime(0.003, this.ctx.currentTime);
        this.compressor.release.setValueAtTime(0.25, this.ctx.currentTime);
        this.compressor.connect(this.masterGain);

        // Analyser (for spectrogram visualization)
        this.analyser = this.ctx.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.smoothingTimeConstant = 0.8;
        this.analyser.connect(this.compressor);

        // Dry path
        this.dryGain = this.ctx.createGain();
        this.dryGain.gain.setValueAtTime(0.8, this.ctx.currentTime);
        this.dryGain.connect(this.analyser);

        // Convolver reverb (wet path)
        this.convolver = this.ctx.createConvolver();
        this.convolver.buffer = createImpulseResponse(this.ctx, 2.5, 2.2);
        this.convolverGain = this.ctx.createGain();
        this.convolverGain.gain.setValueAtTime(0.2, this.ctx.currentTime);
        this.convolver.connect(this.convolverGain);
        this.convolverGain.connect(this.analyser);

        // Global lowpass filter (temperature mapping)
        this.globalFilter = this.ctx.createBiquadFilter();
        this.globalFilter.type = "lowpass";
        this.globalFilter.frequency.setValueAtTime(8000, this.ctx.currentTime);
        this.globalFilter.Q.setValueAtTime(0.7, this.ctx.currentTime);
        this.globalFilter.connect(this.dryGain);
        this.globalFilter.connect(this.convolver);

        this._initialized = true;
    }

    /** Resume the AudioContext (must be called from a user gesture). */
    async resume(): Promise<void> {
        if (this.ctx?.state === "suspended") {
            await this.ctx.resume();
        }
    }

    // -----------------------------------------------------------------------
    // Controls
    // -----------------------------------------------------------------------

    setVolume(v: number): void {
        this._volume = clamp(v, 0, 1);
        if (this._initialized) {
            this.masterGain.gain.setTargetAtTime(
                this._muted ? 0 : this._volume,
                this.ctx.currentTime,
                0.05,
            );
        }
    }

    setMuted(m: boolean): void {
        this._muted = m;
        if (this._initialized) {
            this.masterGain.gain.setTargetAtTime(
                m ? 0 : this._volume,
                this.ctx.currentTime,
                0.05,
            );
        }
    }

    setTempoScale(s: number): void {
        this._tempoScale = clamp(s, 0.25, 4.0);
    }

    get initialized(): boolean {
        return this._initialized;
    }

    // -----------------------------------------------------------------------
    // Epoch helpers
    // -----------------------------------------------------------------------

    private _epochIndex(name: string): number {
        const idx = EPOCH_NAMES.indexOf(name);
        return idx === -1 ? 0 : idx;
    }

    private _rootNote(epochIdx: number): number {
        return EPOCH_ROOTS[clamp(epochIdx, 0, EPOCH_ROOTS.length - 1)];
    }

    /** Build a minor-7 chord from the epoch root. */
    private _chordNotes(root: number): number[] {
        return [root, root + 3, root + 7, root + 10];
    }

    // -----------------------------------------------------------------------
    // Temperature -> filter cutoff
    // -----------------------------------------------------------------------

    private _mapTemperatureToFilter(temperature: number): void {
        // Map log(temperature) to filter cutoff: hotter = more open
        const logT = Math.log10(Math.max(1, temperature));
        // logT range roughly 0..10.  Map to 200..16000 Hz
        const cutoff = 200 + (logT / 10) * 15800;
        this.globalFilter.frequency.setTargetAtTime(
            clamp(cutoff, 200, 16000),
            this.ctx.currentTime,
            0.1,
        );
    }

    // -----------------------------------------------------------------------
    // Particle count -> reverb wet/dry
    // -----------------------------------------------------------------------

    private _mapParticlesToReverb(count: number): void {
        // More particles = wetter reverb
        const wet = clamp(count / 200, 0.05, 0.6);
        const dry = 1.0 - wet * 0.5;
        this.convolverGain.gain.setTargetAtTime(wet, this.ctx.currentTime, 0.2);
        this.dryGain.gain.setTargetAtTime(dry, this.ctx.currentTime, 0.2);
    }

    // -----------------------------------------------------------------------
    // Main sonification entry point
    // -----------------------------------------------------------------------

    /**
     * Map a simulation snapshot to sound events.
     * Called once per animation frame (or per simulation step in the browser).
     */
    sonifySnapshot(snap: SimulationSnapshot): void {
        if (!this._initialized || this._muted) return;

        const now = this.ctx.currentTime;
        const epochIdx = this._epochIndex(snap.epoch);
        const root = this._rootNote(epochIdx);

        // --- Global mappings ---
        this._mapTemperatureToFilter(snap.temperature);
        this._mapParticlesToReverb(snap.particles);

        // --- Epoch transition: re-create ambient pad ---
        if (epochIdx !== this._lastEpochIndex) {
            this._lastEpochIndex = epochIdx;
            this._schedulePad(epochIdx, root);
        }

        // Re-trigger pad if it has expired
        if (now > this._padScheduledEnd - 0.5) {
            this._schedulePad(epochIdx, root);
        }

        // --- Epoch-specific sonification ---
        if (epochIdx <= 4) {
            this._sonifyQuantum(snap, root, now);
        } else if (epochIdx <= 7) {
            this._sonifyAtomic(snap, root, now);
        } else if (epochIdx <= 9) {
            this._sonifyChemistry(snap, root, now);
        } else {
            this._sonifyBiology(snap, root, now);
        }

        this._lastParticleCount = snap.particles;
    }

    // -----------------------------------------------------------------------
    // Ambient pad scheduling
    // -----------------------------------------------------------------------

    private _schedulePad(epochIdx: number, root: number): void {
        const sustain = 5.0 / this._tempoScale;
        this._padNode = createPad(
            this.ctx,
            this._chordNotes(root),
            sustain,
            this.globalFilter,
        );
        this._padScheduledEnd = this.ctx.currentTime + sustain + 1.8;
    }

    // -----------------------------------------------------------------------
    // Quantum epoch  (indices 0-4)
    // -----------------------------------------------------------------------

    private _sonifyQuantum(
        snap: SimulationSnapshot,
        root: number,
        now: number,
    ): void {
        // Particle creation -> short sine blips
        const newParticles = snap.particles - this._lastParticleCount;
        if (newParticles > 0 && now - this._lastBlipTime > 0.06 / this._tempoScale) {
            const count = Math.min(newParticles, 5);
            for (let i = 0; i < count; i++) {
                const freq = mtof(root + 24 + Math.floor(Math.random() * 24));
                const pan = Math.random() * 2 - 1;
                createSineBlip(
                    this.ctx,
                    freq,
                    0.04 + Math.random() * 0.06,
                    pan,
                    this.globalFilter,
                );
            }
            this._lastBlipTime = now;
        }
    }

    // -----------------------------------------------------------------------
    // Atomic epoch  (indices 5-7)
    // -----------------------------------------------------------------------

    private _sonifyAtomic(
        snap: SimulationSnapshot,
        root: number,
        now: number,
    ): void {
        // Harmonic stacking -- overtone series.  Each new atom adds an
        // oscillator at the next harmonic of the root frequency.
        if (snap.atoms > 0 && now - this._lastBlipTime > 0.15 / this._tempoScale) {
            const fundamentalFreq = mtof(root - 12); // one octave below root
            const harmonicIndex = (snap.atoms % 8) + 1;
            const freq = fundamentalFreq * harmonicIndex;

            // Detuned oscillator pair
            const osc1 = this.ctx.createOscillator();
            const osc2 = this.ctx.createOscillator();
            osc1.type = "sine";
            osc2.type = "sine";
            osc1.frequency.setValueAtTime(freq, now);
            osc2.frequency.setValueAtTime(freq, now);
            osc1.detune.setValueAtTime(-6, now);
            osc2.detune.setValueAtTime(6, now);

            const gain = this.ctx.createGain();
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

            osc1.connect(gain);
            osc2.connect(gain);
            gain.connect(this.globalFilter);

            osc1.start(now);
            osc2.start(now);
            osc1.stop(now + 0.55);
            osc2.stop(now + 0.55);

            this._lastBlipTime = now;
        }
    }

    // -----------------------------------------------------------------------
    // Chemistry epoch  (indices 8-9)
    // -----------------------------------------------------------------------

    private _sonifyChemistry(
        snap: SimulationSnapshot,
        root: number,
        now: number,
    ): void {
        // Bond formation -> bell tones (FM synthesis)
        if (snap.molecules > 0 && now - this._lastBellTime > 0.3 / this._tempoScale) {
            // Walk through a chord progression based on molecule count
            const chordTones = this._chordNotes(root);
            const noteIdx = snap.molecules % chordTones.length;
            const freq = mtof(chordTones[noteIdx]);

            createBellTone(this.ctx, freq, 1.0, this.globalFilter);
            this._lastBellTime = now;
        }

        // Water molecule -> special bell with longer decay
        const waterCount = snap.moleculeCounts["H2O"] ?? 0;
        if (waterCount > 0 && now - this._lastBlipTime > 0.5 / this._tempoScale) {
            createBellTone(this.ctx, mtof(root + 12), 1.8, this.globalFilter);
            this._lastBlipTime = now;
        }
    }

    // -----------------------------------------------------------------------
    // Biology epoch  (indices 10-12)
    // -----------------------------------------------------------------------

    private _sonifyBiology(
        snap: SimulationSnapshot,
        root: number,
        now: number,
    ): void {
        // Cell division -> rhythmic pulses
        if (snap.cells > 0 && now - this._lastPulseTime > 0.4 / this._tempoScale) {
            const pulseFreq = mtof(root - 24); // two octaves below
            createPulse(
                this.ctx,
                pulseFreq,
                0.12 / this._tempoScale,
                this.globalFilter,
            );
            this._lastPulseTime = now;
        }

        // DNA transcription -> melodic sequence
        if (
            snap.dnaSequences.length > 0 &&
            now - this._lastSequenceTime > 2.0 / this._tempoScale
        ) {
            const dna = snap.dnaSequences[0];
            const baseToInterval: Record<string, number> = {
                A: 0, T: 3, G: 5, C: 7,
            };
            const seqNotes: number[] = [];
            const maxNotes = Math.min(dna.length, 8);
            for (let i = 0; i < maxNotes; i++) {
                const base = dna[i];
                const interval = baseToInterval[base] ?? 0;
                // Scale modulation: shift up with generation for evolution feel
                const evolveShift = Math.floor((snap.generation % 4) * 2);
                seqNotes.push(root + interval + evolveShift);
            }
            createSequence(
                this.ctx,
                seqNotes,
                8 * this._tempoScale,
                this.globalFilter,
            );
            this._lastSequenceTime = now;
        }
    }
}
