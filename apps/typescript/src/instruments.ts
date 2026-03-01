/**
 * Web Audio API instrument voices for cosmic sonification.
 *
 * Each function creates a self-contained sound using native Web Audio nodes.
 * No external samples are needed -- everything is generated from oscillators,
 * gain envelopes, and filters.
 */

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

/** MIDI note to frequency. */
function mtof(note: number): number {
    return 440 * Math.pow(2, (note - 69) / 12);
}

/** Clamp a value between min and max. */
function clamp(v: number, lo: number, hi: number): number {
    return v < lo ? lo : v > hi ? hi : v;
}

// ---------------------------------------------------------------------------
// createSineBlip  --  quantum particle creation
// ---------------------------------------------------------------------------

/**
 * A short sine-wave "blip" -- the sound of a particle popping into existence.
 *
 * @param ctx      AudioContext
 * @param freq     Fundamental frequency in Hz
 * @param duration Blip duration in seconds (default 0.08)
 * @param pan      Stereo pan position -1..1 (default 0)
 * @param dest     Destination node (defaults to ctx.destination)
 */
export function createSineBlip(
    ctx: AudioContext,
    freq: number,
    duration: number = 0.08,
    pan: number = 0,
    dest?: AudioNode,
): void {
    const now = ctx.currentTime;
    const out = dest ?? ctx.destination;

    const osc = ctx.createOscillator();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(freq * 2.5, now + duration);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.25, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);

    const panner = ctx.createStereoPanner();
    panner.pan.setValueAtTime(clamp(pan, -1, 1), now);

    osc.connect(gain).connect(panner).connect(out);
    osc.start(now);
    osc.stop(now + duration + 0.01);
}

// ---------------------------------------------------------------------------
// createBellTone  --  molecular bond formation (FM synthesis)
// ---------------------------------------------------------------------------

/**
 * FM-synthesis bell -- rings when a molecular bond forms.
 *
 * Carrier : sine at `freq`
 * Modulator : sine at `freq * 1.4` (inharmonic ratio for bell timbre)
 *
 * @param ctx   AudioContext
 * @param freq  Fundamental frequency in Hz
 * @param decay Decay time in seconds (default 1.2)
 * @param dest  Destination node
 */
export function createBellTone(
    ctx: AudioContext,
    freq: number,
    decay: number = 1.2,
    dest?: AudioNode,
): void {
    const now = ctx.currentTime;
    const out = dest ?? ctx.destination;

    // Modulator
    const mod = ctx.createOscillator();
    mod.type = "sine";
    mod.frequency.setValueAtTime(freq * 1.4, now);

    const modGain = ctx.createGain();
    modGain.gain.setValueAtTime(freq * 0.6, now);
    modGain.gain.exponentialRampToValueAtTime(0.01, now + decay);

    mod.connect(modGain);

    // Carrier
    const carrier = ctx.createOscillator();
    carrier.type = "sine";
    carrier.frequency.setValueAtTime(freq, now);
    modGain.connect(carrier.frequency);

    const env = ctx.createGain();
    env.gain.setValueAtTime(0.20, now);
    env.gain.exponentialRampToValueAtTime(0.001, now + decay);

    carrier.connect(env).connect(out);

    mod.start(now);
    carrier.start(now);
    mod.stop(now + decay + 0.05);
    carrier.stop(now + decay + 0.05);
}

// ---------------------------------------------------------------------------
// createPulse  --  cell division
// ---------------------------------------------------------------------------

/**
 * A single low "pulse" representing cell division.
 *
 * Uses a square wave with a short envelope for a percussive thud.
 *
 * @param ctx   AudioContext
 * @param freq  Frequency in Hz (typically 40-120)
 * @param width Pulse width in seconds (default 0.15)
 * @param dest  Destination node
 */
export function createPulse(
    ctx: AudioContext,
    freq: number,
    width: number = 0.15,
    dest?: AudioNode,
): void {
    const now = ctx.currentTime;
    const out = dest ?? ctx.destination;

    const osc = ctx.createOscillator();
    osc.type = "square";
    osc.frequency.setValueAtTime(freq, now);
    osc.frequency.exponentialRampToValueAtTime(freq * 0.5, now + width);

    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.18, now);
    gain.gain.linearRampToValueAtTime(0.18, now + width * 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, now + width);

    // Low-pass to soften the square wave
    const lpf = ctx.createBiquadFilter();
    lpf.type = "lowpass";
    lpf.frequency.setValueAtTime(freq * 4, now);
    lpf.Q.setValueAtTime(1.0, now);

    osc.connect(lpf).connect(gain).connect(out);
    osc.start(now);
    osc.stop(now + width + 0.02);
}

// ---------------------------------------------------------------------------
// createPad  --  epoch ambient drone
// ---------------------------------------------------------------------------

/**
 * Layered oscillator pad that provides an ambient tonal bed for each epoch.
 *
 * Multiple detuned oscillators fade in and sustain, then fade out.
 *
 * @param ctx     AudioContext
 * @param notes   Array of MIDI note numbers forming the chord
 * @param sustain Duration in seconds (default 4.0)
 * @param dest    Destination node
 * @returns       The master GainNode so the caller can fade / kill it
 */
export function createPad(
    ctx: AudioContext,
    notes: number[],
    sustain: number = 4.0,
    dest?: AudioNode,
): GainNode {
    const now = ctx.currentTime;
    const out = dest ?? ctx.destination;
    const fadeIn = 0.6;
    const fadeOut = 1.2;
    const total = fadeIn + sustain + fadeOut;

    const master = ctx.createGain();
    master.gain.setValueAtTime(0.001, now);
    master.gain.linearRampToValueAtTime(0.10 / Math.max(1, notes.length), now + fadeIn);
    master.gain.setValueAtTime(0.10 / Math.max(1, notes.length), now + fadeIn + sustain);
    master.gain.exponentialRampToValueAtTime(0.001, now + total);
    master.connect(out);

    for (const note of notes) {
        const freq = mtof(note);
        // Two oscillators per note: one slightly sharp, one slightly flat
        for (const detuneCents of [-8, 8]) {
            const osc = ctx.createOscillator();
            osc.type = "sine";
            osc.frequency.setValueAtTime(freq, now);
            osc.detune.setValueAtTime(detuneCents, now);
            osc.connect(master);
            osc.start(now);
            osc.stop(now + total + 0.1);
        }
        // Add a triangle an octave above for shimmer
        const shimmer = ctx.createOscillator();
        shimmer.type = "triangle";
        shimmer.frequency.setValueAtTime(freq * 2, now);
        shimmer.connect(master);
        shimmer.start(now);
        shimmer.stop(now + total + 0.1);
    }

    return master;
}

// ---------------------------------------------------------------------------
// createSequence  --  DNA transcription melody
// ---------------------------------------------------------------------------

/**
 * Plays an ascending / descending melodic sequence mapped from DNA bases.
 *
 * Each note is a short sine tone. The sequence auto-schedules all notes
 * ahead of time using Web Audio's precise timing.
 *
 * @param ctx   AudioContext
 * @param notes Array of MIDI note numbers
 * @param tempo Notes per second (default 8)
 * @param dest  Destination node
 */
export function createSequence(
    ctx: AudioContext,
    notes: number[],
    tempo: number = 8,
    dest?: AudioNode,
): void {
    const now = ctx.currentTime;
    const out = dest ?? ctx.destination;
    const noteDur = 1 / tempo;
    const overlap = 0.02;

    for (let i = 0; i < notes.length; i++) {
        const t = now + i * noteDur;
        const freq = mtof(notes[i]);

        const osc = ctx.createOscillator();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, t);

        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.001, t);
        gain.gain.linearRampToValueAtTime(0.12, t + noteDur * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.001, t + noteDur + overlap);

        osc.connect(gain).connect(out);
        osc.start(t);
        osc.stop(t + noteDur + overlap + 0.01);
    }
}

// ---------------------------------------------------------------------------
// Exported utility
// ---------------------------------------------------------------------------

export { mtof, clamp };
