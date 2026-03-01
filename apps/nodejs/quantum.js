/**
 * Quantum and subatomic physics simulation.
 *
 * Models quantum fields, particles, wave functions, superposition,
 * entanglement (simplified), and the quark-hadron transition.
 * Quantum effects influence atomic-level phenomena through
 * measurement/decoherence events.
 */

import {
    HBAR, C, M_UP_QUARK, M_DOWN_QUARK, M_ELECTRON, M_PROTON,
    M_NEUTRON, M_PHOTON, M_NEUTRINO, STRONG_COUPLING, EM_COUPLING,
    WEAK_COUPLING, ALPHA, E_CHARGE, PI, T_PLANCK, T_ELECTROWEAK,
    T_QUARK_HADRON, NUCLEAR_RADIUS,
} from './constants.js';


// === Enums ===

export const ParticleType = Object.freeze({
    // Quarks
    UP: "up",
    DOWN: "down",
    // Leptons
    ELECTRON: "electron",
    POSITRON: "positron",
    NEUTRINO: "neutrino",
    // Gauge bosons
    PHOTON: "photon",
    GLUON: "gluon",
    W_BOSON: "W",
    Z_BOSON: "Z",
    // Composite
    PROTON: "proton",
    NEUTRON: "neutron",
});

export const Spin = Object.freeze({
    UP: 0.5,
    DOWN: -0.5,
});

export const Color = Object.freeze({
    RED: "r",
    GREEN: "g",
    BLUE: "b",
    ANTI_RED: "ar",
    ANTI_GREEN: "ag",
    ANTI_BLUE: "ab",
});


// === Lookup tables ===

const PARTICLE_MASSES = {
    [ParticleType.UP]: M_UP_QUARK,
    [ParticleType.DOWN]: M_DOWN_QUARK,
    [ParticleType.ELECTRON]: M_ELECTRON,
    [ParticleType.POSITRON]: M_ELECTRON,
    [ParticleType.NEUTRINO]: M_NEUTRINO,
    [ParticleType.PHOTON]: M_PHOTON,
    [ParticleType.GLUON]: M_PHOTON,
    [ParticleType.PROTON]: M_PROTON,
    [ParticleType.NEUTRON]: M_NEUTRON,
};

const PARTICLE_CHARGES = {
    [ParticleType.UP]: 2.0 / 3.0,
    [ParticleType.DOWN]: -1.0 / 3.0,
    [ParticleType.ELECTRON]: -1.0,
    [ParticleType.POSITRON]: 1.0,
    [ParticleType.NEUTRINO]: 0.0,
    [ParticleType.PHOTON]: 0.0,
    [ParticleType.GLUON]: 0.0,
    [ParticleType.PROTON]: 1.0,
    [ParticleType.NEUTRON]: 0.0,
};


// === Helper: random gaussian ===

function gaussRandom(mean = 0, stddev = 1) {
    // Box-Muller transform
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2.0 * Math.log(u1 || 1e-20)) * Math.cos(2.0 * PI * u2);
    return mean + stddev * z;
}

function expoVariate(lambda) {
    // Exponential distribution
    return -Math.log(Math.random() || 1e-20) / lambda;
}


// === WaveFunction ===

export class WaveFunction {
    /**
     * Simplified quantum wave function with amplitude and phase.
     */
    constructor(amplitude = 1.0, phase = 0.0, coherent = true) {
        this.amplitude = amplitude;
        this.phase = phase;
        this.coherent = coherent;
    }

    /** Born rule: |psi|^2 */
    get probability() {
        return this.amplitude ** 2;
    }

    /** Time evolution: phase rotation by E*dt/hbar. */
    evolve(dt, energy) {
        if (this.coherent) {
            this.phase += energy * dt / HBAR;
            this.phase %= (2 * PI);
        }
    }

    /** Measurement: collapse to eigenstate. Returns true if 'detected'. */
    collapse() {
        const result = Math.random() < this.probability;
        this.amplitude = result ? 1.0 : 0.0;
        this.coherent = false;
        return result;
    }

    /** Superposition of two states. */
    superpose(other) {
        const phaseDiff = this.phase - other.phase;
        const combinedAmp = Math.sqrt(
            this.amplitude ** 2 + other.amplitude ** 2
            + 2 * this.amplitude * other.amplitude * Math.cos(phaseDiff)
        );
        const combinedPhase = (this.phase + other.phase) / 2;
        return new WaveFunction(
            Math.min(combinedAmp, 1.0),
            combinedPhase,
            true,
        );
    }

    toCompact() {
        return `\u03C8(${this.amplitude.toFixed(3)}\u2220${this.phase.toFixed(2)})`;
    }
}


// === Particle ===

let particleIdCounter = 0;

export class Particle {
    /**
     * A quantum particle with position, momentum, and quantum numbers.
     */
    constructor({
        particleType,
        position = [0.0, 0.0, 0.0],
        momentum = [0.0, 0.0, 0.0],
        spin = Spin.UP,
        color = null,
        waveFn = null,
        entangledWith = null,
    } = {}) {
        this.particleType = particleType;
        this.position = [...position];
        this.momentum = [...momentum];
        this.spin = spin;
        this.color = color;
        this.waveFn = waveFn || new WaveFunction();
        this.entangledWith = entangledWith;
        particleIdCounter++;
        this.particleId = particleIdCounter;
    }

    get mass() {
        return PARTICLE_MASSES[this.particleType] ?? 0.0;
    }

    get charge() {
        return PARTICLE_CHARGES[this.particleType] ?? 0.0;
    }

    /** E = sqrt(p^2*c^2 + m^2*c^4) */
    get energy() {
        const p2 = this.momentum.reduce((s, p) => s + p ** 2, 0);
        return Math.sqrt(p2 * C ** 2 + (this.mass * C ** 2) ** 2);
    }

    /** de Broglie wavelength: lambda = h / p */
    get wavelength() {
        const p = Math.sqrt(this.momentum.reduce((s, v) => s + v ** 2, 0));
        if (p < 1e-20) return Infinity;
        return 2 * PI * HBAR / p;
    }

    toCompact() {
        return (
            `${this.particleType}`
            + `[${this.position[0].toFixed(1)},${this.position[1].toFixed(1)},`
            + `${this.position[2].toFixed(1)}]`
            + `s=${this.spin}`
        );
    }
}

/** Reset particle ID counter (useful for tests). */
export function resetParticleIdCounter() {
    particleIdCounter = 0;
}


// === EntangledPair ===

export class EntangledPair {
    /** A pair of entangled particles (EPR pair). */
    constructor(particleA, particleB, bellState = "phi+") {
        this.particleA = particleA;
        this.particleB = particleB;
        this.bellState = bellState;
    }

    /** Measure particle A, instantly determining B. */
    measureA() {
        if (Math.random() < 0.5) {
            this.particleA.spin = Spin.UP;
            this.particleB.spin = Spin.DOWN;
        } else {
            this.particleA.spin = Spin.DOWN;
            this.particleB.spin = Spin.UP;
        }
        this.particleA.waveFn.coherent = false;
        this.particleB.waveFn.coherent = false;
        return this.particleA.spin;
    }
}


// === QuantumField ===

export class QuantumField {
    /** Represents a quantum field that can create and annihilate particles. */
    constructor(temperature = T_PLANCK) {
        this.temperature = temperature;
        this.particles = [];
        this.entangledPairs = [];
        this.vacuumEnergy = 0.0;
        this.totalCreated = 0;
        this.totalAnnihilated = 0;
    }

    /**
     * Create particle-antiparticle pair from vacuum energy.
     * Requires E >= 2mc^2 for the lightest possible pair.
     */
    pairProduction(energy) {
        if (energy < 2 * M_ELECTRON * C ** 2) {
            return null;
        }

        let pType, apType;
        // Determine what we can produce
        if (energy >= 2 * M_PROTON * C ** 2 && Math.random() < 0.1) {
            // Quark-antiquark pair (simplified as proton-like)
            pType = ParticleType.UP;
            apType = ParticleType.DOWN;
        } else {
            pType = ParticleType.ELECTRON;
            apType = ParticleType.POSITRON;
        }

        const direction = [gaussRandom(), gaussRandom(), gaussRandom()];
        const norm = Math.sqrt(direction.reduce((s, d) => s + d ** 2, 0)) || 1.0;
        const pMomentum = energy / (2 * C);

        const particle = new Particle({
            particleType: pType,
            momentum: direction.map(d => d / norm * pMomentum),
            spin: Spin.UP,
        });
        const antiparticle = new Particle({
            particleType: apType,
            momentum: direction.map(d => -d / norm * pMomentum),
            spin: Spin.DOWN,
        });

        // They're entangled
        particle.entangledWith = antiparticle.particleId;
        antiparticle.entangledWith = particle.particleId;

        this.particles.push(particle, antiparticle);
        this.entangledPairs.push(new EntangledPair(particle, antiparticle));
        this.totalCreated += 2;

        return [particle, antiparticle];
    }

    /** Annihilate particle-antiparticle pair, returning energy. */
    annihilate(p1, p2) {
        const energy = p1.energy + p2.energy;
        let idx = this.particles.indexOf(p1);
        if (idx !== -1) this.particles.splice(idx, 1);
        idx = this.particles.indexOf(p2);
        if (idx !== -1) this.particles.splice(idx, 1);
        this.totalAnnihilated += 2;
        this.vacuumEnergy += energy * 0.01;

        // Create photons from annihilation
        const photon1 = new Particle({
            particleType: ParticleType.PHOTON,
            momentum: [energy / (2 * C), 0, 0],
        });
        const photon2 = new Particle({
            particleType: ParticleType.PHOTON,
            momentum: [-energy / (2 * C), 0, 0],
        });
        this.particles.push(photon1, photon2);
        return energy;
    }

    /** Combine quarks into hadrons when temperature drops enough. */
    quarkConfinement() {
        if (this.temperature > T_QUARK_HADRON) {
            return [];
        }

        const hadrons = [];
        const ups = this.particles.filter(p => p.particleType === ParticleType.UP);
        const downs = this.particles.filter(p => p.particleType === ParticleType.DOWN);

        // Form protons (uud)
        while (ups.length >= 2 && downs.length >= 1) {
            const u1 = ups.pop();
            const u2 = ups.pop();
            const d1 = downs.pop();

            // Assign colors for color neutrality
            u1.color = Color.RED;
            u2.color = Color.GREEN;
            d1.color = Color.BLUE;

            const proton = new Particle({
                particleType: ParticleType.PROTON,
                position: [...u1.position],
                momentum: [
                    u1.momentum[0] + u2.momentum[0] + d1.momentum[0],
                    u1.momentum[1] + u2.momentum[1] + d1.momentum[1],
                    u1.momentum[2] + u2.momentum[2] + d1.momentum[2],
                ],
            });

            for (const q of [u1, u2, d1]) {
                const idx = this.particles.indexOf(q);
                if (idx !== -1) this.particles.splice(idx, 1);
            }
            this.particles.push(proton);
            hadrons.push(proton);
        }

        // Form neutrons (udd)
        while (ups.length >= 1 && downs.length >= 2) {
            const u1 = ups.pop();
            const d1 = downs.pop();
            const d2 = downs.pop();

            u1.color = Color.RED;
            d1.color = Color.GREEN;
            d2.color = Color.BLUE;

            const neutron = new Particle({
                particleType: ParticleType.NEUTRON,
                position: [...u1.position],
                momentum: [
                    u1.momentum[0] + d1.momentum[0] + d2.momentum[0],
                    u1.momentum[1] + d1.momentum[1] + d2.momentum[1],
                    u1.momentum[2] + d1.momentum[2] + d2.momentum[2],
                ],
            });

            for (const q of [u1, d1, d2]) {
                const idx = this.particles.indexOf(q);
                if (idx !== -1) this.particles.splice(idx, 1);
            }
            this.particles.push(neutron);
            hadrons.push(neutron);
        }

        return hadrons;
    }

    /** Spontaneous virtual particle pair from vacuum energy. */
    vacuumFluctuation() {
        const prob = Math.min(0.5, this.temperature / T_PLANCK);
        if (Math.random() < prob) {
            const energy = expoVariate(1.0 / (this.temperature * 0.001));
            return this.pairProduction(energy);
        }
        return null;
    }

    /** Environmental decoherence of a particle's wave function. */
    decohere(particle, environmentCoupling = 0.1) {
        if (particle.waveFn.coherent) {
            const decoherenceRate = environmentCoupling * this.temperature;
            if (Math.random() < decoherenceRate) {
                particle.waveFn.collapse();
            }
        }
    }

    /** Cool the field (universe expansion). */
    cool(factor = 0.999) {
        this.temperature *= factor;
    }

    /** Evolve all particles by one time step. */
    evolve(dt = 1.0) {
        for (const p of this.particles) {
            if (p.mass > 0) {
                for (let i = 0; i < 3; i++) {
                    p.position[i] += p.momentum[i] / p.mass * dt;
                }
            } else {
                // Massless particles move at c
                const pMag = Math.sqrt(p.momentum.reduce((s, x) => s + x ** 2, 0)) || 1.0;
                for (let i = 0; i < 3; i++) {
                    p.position[i] += p.momentum[i] / pMag * C * dt;
                }
            }

            // Evolve wave function
            p.waveFn.evolve(dt, p.energy);
        }
    }

    /** Count particles by type. */
    particleCount() {
        const counts = {};
        for (const p of this.particles) {
            const key = p.particleType;
            counts[key] = (counts[key] || 0) + 1;
        }
        return counts;
    }

    /** Total energy in the field. */
    totalEnergy() {
        let sum = 0;
        for (const p of this.particles) {
            sum += p.energy;
        }
        return sum + this.vacuumEnergy;
    }

    /** Compact state representation. */
    toCompact() {
        const counts = this.particleCount();
        const countStr = Object.entries(counts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([k, v]) => `${k}:${v}`)
            .join(",");
        return (
            `QF[T=${this.temperature.toExponential(1)} `
            + `E=${this.totalEnergy().toExponential(1)} `
            + `n=${this.particles.length} ${countStr}]`
        );
    }
}

// Re-export helpers for universe seeding
export { gaussRandom, expoVariate };
