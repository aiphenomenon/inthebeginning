/**
 * Complete physics engine - faithful port of the Python simulator.
 *
 * Contains: QuantumField, Particle, ParticleType, AtomicSystem, Atom,
 * ChemicalSystem, Molecule, Biosphere, Cell, DNAStrand, Environment,
 * and Universe orchestrator.
 *
 * All in one file for simplicity (the TypeScript app focuses on audio).
 */

import {
    C, HBAR, K_B, PI, T_PLANCK, T_QUARK_HADRON, T_CMB, T_EARTH_SURFACE,
    T_RECOMBINATION, M_UP_QUARK, M_DOWN_QUARK, M_ELECTRON, M_PROTON,
    M_NEUTRON, M_PHOTON, M_NEUTRINO,
    ELECTRON_SHELLS, BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC,
    NUCLEOTIDE_BASES, AMINO_ACIDS, CODON_TABLE,
    METHYLATION_PROBABILITY, DEMETHYLATION_PROBABILITY,
    HISTONE_ACETYLATION_PROB, HISTONE_DEACETYLATION_PROB,
    UV_MUTATION_RATE, COSMIC_RAY_MUTATION_RATE, RADIATION_DAMAGE_THRESHOLD,
    PLANCK_EPOCH, INFLATION_EPOCH, ELECTROWEAK_EPOCH, QUARK_EPOCH,
    HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH, RECOMBINATION_EPOCH,
    STAR_FORMATION_EPOCH, SOLAR_SYSTEM_EPOCH, EARTH_EPOCH,
    LIFE_EPOCH, DNA_EPOCH, PRESENT_EPOCH, EPOCHS, ELEMENTS,
} from "./constants.js";

// ============================================================================
// Seeded random number generator (xorshift128+)
// ============================================================================

export class RNG {
    private s0: number;
    private s1: number;

    constructor(seed: number) {
        // Initialize from seed using splitmix32
        let s = seed | 0;
        s = (s + 0x9e3779b9) | 0;
        let t = s ^ (s >>> 16); t = Math.imul(t, 0x21f0aaad);
        t = t ^ (t >>> 15); t = Math.imul(t, 0x735a2d97);
        this.s0 = (t ^ (t >>> 15)) >>> 0;
        s = (s + 0x9e3779b9) | 0;
        t = s ^ (s >>> 16); t = Math.imul(t, 0x21f0aaad);
        t = t ^ (t >>> 15); t = Math.imul(t, 0x735a2d97);
        this.s1 = (t ^ (t >>> 15)) >>> 0;
        if (this.s0 === 0 && this.s1 === 0) this.s1 = 1;
    }

    /** Returns a random float in [0, 1). */
    random(): number {
        let s1 = this.s0;
        const s0 = this.s1;
        this.s0 = s0;
        s1 ^= s1 << 23;
        s1 ^= s1 >>> 17;
        s1 ^= s0;
        s1 ^= s0 >>> 26;
        this.s1 = s1;
        return ((this.s0 + this.s1) >>> 0) / 4294967296;
    }

    /** Gaussian using Box-Muller. */
    gauss(mean: number = 0, stddev: number = 1): number {
        const u1 = this.random() || 1e-10;
        const u2 = this.random();
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * PI * u2);
        return mean + z * stddev;
    }

    /** Exponential variate with given rate (lambda). */
    expovariate(lambda: number): number {
        return -Math.log(1 - this.random() + 1e-20) / lambda;
    }

    /** Choose a random element from an array. */
    choice<T>(arr: T[]): T {
        return arr[Math.floor(this.random() * arr.length)];
    }

    /** Random integer in [min, max] inclusive. */
    randint(min: number, max: number): number {
        return min + Math.floor(this.random() * (max - min + 1));
    }

    /** Random float in [min, max). */
    uniform(min: number, max: number): number {
        return min + this.random() * (max - min);
    }
}

// Module-level RNG instance, reset by Universe constructor
let rng = new RNG(42);

// ============================================================================
// Particle types and quantum physics
// ============================================================================

export enum ParticleType {
    UP = "up",
    DOWN = "down",
    ELECTRON = "electron",
    POSITRON = "positron",
    NEUTRINO = "neutrino",
    PHOTON = "photon",
    GLUON = "gluon",
    W_BOSON = "W",
    Z_BOSON = "Z",
    PROTON = "proton",
    NEUTRON = "neutron",
}

export enum Spin {
    UP = 0.5,
    DOWN = -0.5,
}

export enum Color {
    RED = "r",
    GREEN = "g",
    BLUE = "b",
    ANTI_RED = "ar",
    ANTI_GREEN = "ag",
    ANTI_BLUE = "ab",
}

const PARTICLE_MASSES: Record<string, number> = {
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

const PARTICLE_CHARGES: Record<string, number> = {
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

export class WaveFunction {
    amplitude: number;
    phase: number;
    coherent: boolean;

    constructor(amplitude = 1.0, phase = 0.0, coherent = true) {
        this.amplitude = amplitude;
        this.phase = phase;
        this.coherent = coherent;
    }

    get probability(): number {
        return this.amplitude * this.amplitude;
    }

    evolve(dt: number, energy: number): void {
        if (this.coherent) {
            this.phase += energy * dt / HBAR;
            this.phase %= 2 * PI;
        }
    }

    collapse(): boolean {
        const result = rng.random() < this.probability;
        this.amplitude = result ? 1.0 : 0.0;
        this.coherent = false;
        return result;
    }
}

let particleIdCounter = 0;

export class Particle {
    particleType: ParticleType;
    position: number[];
    momentum: number[];
    spin: Spin;
    color: Color | null;
    waveFn: WaveFunction;
    entangledWith: number | null;
    particleId: number;

    constructor(
        particleType: ParticleType,
        position?: number[],
        momentum?: number[],
        spin?: Spin,
        color?: Color | null,
    ) {
        this.particleType = particleType;
        this.position = position ?? [0, 0, 0];
        this.momentum = momentum ?? [0, 0, 0];
        this.spin = spin ?? Spin.UP;
        this.color = color ?? null;
        this.waveFn = new WaveFunction();
        this.entangledWith = null;
        this.particleId = ++particleIdCounter;
    }

    get mass(): number {
        return PARTICLE_MASSES[this.particleType] ?? 0;
    }

    get charge(): number {
        return PARTICLE_CHARGES[this.particleType] ?? 0;
    }

    get energy(): number {
        const p2 = this.momentum[0] ** 2 + this.momentum[1] ** 2 + this.momentum[2] ** 2;
        return Math.sqrt(p2 * C * C + (this.mass * C * C) ** 2);
    }
}

// ============================================================================
// Quantum Field
// ============================================================================

export class QuantumField {
    temperature: number;
    particles: Particle[];
    vacuumEnergy: number;
    totalCreated: number;
    totalAnnihilated: number;

    constructor(temperature: number = T_PLANCK) {
        this.temperature = temperature;
        this.particles = [];
        this.vacuumEnergy = 0;
        this.totalCreated = 0;
        this.totalAnnihilated = 0;
    }

    pairProduction(energy: number): [Particle, Particle] | null {
        if (energy < 2 * M_ELECTRON * C * C) return null;

        let pType: ParticleType;
        let apType: ParticleType;

        if (energy >= 2 * M_PROTON * C * C && rng.random() < 0.1) {
            pType = ParticleType.UP;
            apType = ParticleType.DOWN;
        } else {
            pType = ParticleType.ELECTRON;
            apType = ParticleType.POSITRON;
        }

        const direction = [rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)];
        const norm = Math.sqrt(direction[0] ** 2 + direction[1] ** 2 + direction[2] ** 2) || 1;
        const pMomentum = energy / (2 * C);

        const particle = new Particle(
            pType,
            [0, 0, 0],
            [direction[0] / norm * pMomentum, direction[1] / norm * pMomentum, direction[2] / norm * pMomentum],
            Spin.UP,
        );
        const antiparticle = new Particle(
            apType,
            [0, 0, 0],
            [-direction[0] / norm * pMomentum, -direction[1] / norm * pMomentum, -direction[2] / norm * pMomentum],
            Spin.DOWN,
        );

        particle.entangledWith = antiparticle.particleId;
        antiparticle.entangledWith = particle.particleId;

        this.particles.push(particle, antiparticle);
        this.totalCreated += 2;

        return [particle, antiparticle];
    }

    annihilate(p1: Particle, p2: Particle): number {
        const energy = p1.energy + p2.energy;
        this.particles = this.particles.filter(p => p !== p1 && p !== p2);
        this.totalAnnihilated += 2;
        this.vacuumEnergy += energy * 0.01;

        const photon1 = new Particle(ParticleType.PHOTON, [0, 0, 0], [energy / (2 * C), 0, 0]);
        const photon2 = new Particle(ParticleType.PHOTON, [0, 0, 0], [-energy / (2 * C), 0, 0]);
        this.particles.push(photon1, photon2);
        return energy;
    }

    quarkConfinement(): Particle[] {
        if (this.temperature > T_QUARK_HADRON) return [];

        const hadrons: Particle[] = [];
        const ups = this.particles.filter(p => p.particleType === ParticleType.UP);
        const downs = this.particles.filter(p => p.particleType === ParticleType.DOWN);

        // Form protons (uud)
        while (ups.length >= 2 && downs.length >= 1) {
            const u1 = ups.pop()!;
            const u2 = ups.pop()!;
            const d1 = downs.pop()!;

            u1.color = Color.RED;
            u2.color = Color.GREEN;
            d1.color = Color.BLUE;

            const proton = new Particle(
                ParticleType.PROTON,
                [...u1.position],
                [
                    u1.momentum[0] + u2.momentum[0] + d1.momentum[0],
                    u1.momentum[1] + u2.momentum[1] + d1.momentum[1],
                    u1.momentum[2] + u2.momentum[2] + d1.momentum[2],
                ],
            );

            this.particles = this.particles.filter(p => p !== u1 && p !== u2 && p !== d1);
            this.particles.push(proton);
            hadrons.push(proton);
        }

        // Form neutrons (udd)
        while (ups.length >= 1 && downs.length >= 2) {
            const u1 = ups.pop()!;
            const d1 = downs.pop()!;
            const d2 = downs.pop()!;

            u1.color = Color.RED;
            d1.color = Color.GREEN;
            d2.color = Color.BLUE;

            const neutron = new Particle(
                ParticleType.NEUTRON,
                [...u1.position],
                [
                    u1.momentum[0] + d1.momentum[0] + d2.momentum[0],
                    u1.momentum[1] + d1.momentum[1] + d2.momentum[1],
                    u1.momentum[2] + d1.momentum[2] + d2.momentum[2],
                ],
            );

            this.particles = this.particles.filter(p => p !== u1 && p !== d1 && p !== d2);
            this.particles.push(neutron);
            hadrons.push(neutron);
        }

        return hadrons;
    }

    vacuumFluctuation(): [Particle, Particle] | null {
        const prob = Math.min(0.5, this.temperature / T_PLANCK);
        if (rng.random() < prob) {
            const energy = rng.expovariate(1.0 / (this.temperature * 0.001));
            return this.pairProduction(energy);
        }
        return null;
    }

    evolve(dt: number = 1.0): void {
        for (const p of this.particles) {
            if (p.mass > 0) {
                for (let i = 0; i < 3; i++) {
                    p.position[i] += p.momentum[i] / p.mass * dt;
                }
            } else {
                const pMag = Math.sqrt(p.momentum[0] ** 2 + p.momentum[1] ** 2 + p.momentum[2] ** 2) || 1;
                for (let i = 0; i < 3; i++) {
                    p.position[i] += p.momentum[i] / pMag * C * dt;
                }
            }
            p.waveFn.evolve(dt, p.energy);
        }
    }

    particleCount(): Record<string, number> {
        const counts: Record<string, number> = {};
        for (const p of this.particles) {
            counts[p.particleType] = (counts[p.particleType] || 0) + 1;
        }
        return counts;
    }

    totalEnergy(): number {
        let total = this.vacuumEnergy;
        for (const p of this.particles) total += p.energy;
        return total;
    }
}

// ============================================================================
// Atomic Physics
// ============================================================================

let atomIdCounter = 0;

export class Atom {
    atomicNumber: number;
    massNumber: number;
    electronCount: number;
    position: number[];
    velocity: number[];
    bonds: number[];
    atomId: number;
    ionizationEnergy: number;
    shells: { n: number; maxElectrons: number; electrons: number }[];

    constructor(atomicNumber: number, massNumber?: number, position?: number[]) {
        this.atomicNumber = atomicNumber;
        this.massNumber = massNumber ?? (atomicNumber === 1 ? 1 : atomicNumber * 2);
        this.electronCount = atomicNumber; // neutral
        this.position = position ?? [0, 0, 0];
        this.velocity = [0, 0, 0];
        this.bonds = [];
        this.atomId = ++atomIdCounter;
        this.ionizationEnergy = 0;
        this.shells = [];
        this._buildShells();
        this._computeIonizationEnergy();
    }

    private _buildShells(): void {
        this.shells = [];
        let remaining = this.electronCount;
        for (let i = 0; i < ELECTRON_SHELLS.length; i++) {
            if (remaining <= 0) break;
            const maxE = ELECTRON_SHELLS[i];
            const electrons = Math.min(remaining, maxE);
            this.shells.push({ n: i + 1, maxElectrons: maxE, electrons });
            remaining -= electrons;
        }
    }

    private _computeIonizationEnergy(): void {
        if (this.shells.length === 0 || this.shells[this.shells.length - 1].electrons === 0) {
            this.ionizationEnergy = 0;
            return;
        }
        const n = this.shells[this.shells.length - 1].n;
        const innerElectrons = this.shells.slice(0, -1).reduce((s, sh) => s + sh.electrons, 0);
        const zEff = this.atomicNumber - innerElectrons;
        this.ionizationEnergy = 13.6 * zEff * zEff / (n * n);
    }

    get symbol(): string {
        const elem = ELEMENTS[this.atomicNumber];
        return elem ? elem[0] : `E${this.atomicNumber}`;
    }

    get electronegativity(): number {
        const elem = ELEMENTS[this.atomicNumber];
        return elem ? elem[4] : 1.0;
    }

    get charge(): number {
        return this.atomicNumber - this.electronCount;
    }

    get valenceElectrons(): number {
        if (this.shells.length === 0) return 0;
        return this.shells[this.shells.length - 1].electrons;
    }

    get isNobleGas(): boolean {
        if (this.shells.length === 0) return false;
        const last = this.shells[this.shells.length - 1];
        return last.electrons >= last.maxElectrons;
    }

    canBondWith(other: Atom): boolean {
        if (this.isNobleGas || other.isNobleGas) return false;
        if (this.bonds.length >= 4 || other.bonds.length >= 4) return false;
        return true;
    }

    bondType(other: Atom): string {
        const diff = Math.abs(this.electronegativity - other.electronegativity);
        if (diff > 1.7) return "ionic";
        if (diff > 0.4) return "polar_covalent";
        return "covalent";
    }

    bondEnergy(other: Atom): number {
        const btype = this.bondType(other);
        if (btype === "ionic") return BOND_ENERGY_IONIC;
        if (btype === "polar_covalent") return (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2;
        return BOND_ENERGY_COVALENT;
    }

    distanceTo(other: Atom): number {
        return Math.sqrt(
            (this.position[0] - other.position[0]) ** 2 +
            (this.position[1] - other.position[1]) ** 2 +
            (this.position[2] - other.position[2]) ** 2
        );
    }
}

// ============================================================================
// Atomic System
// ============================================================================

export class AtomicSystem {
    atoms: Atom[];
    temperature: number;
    bondsFormed: number;
    bondsBroken: number;

    constructor(temperature: number = T_RECOMBINATION) {
        this.atoms = [];
        this.temperature = temperature;
        this.bondsFormed = 0;
        this.bondsBroken = 0;
    }

    recombination(field: QuantumField): Atom[] {
        if (this.temperature > T_RECOMBINATION) return [];

        const newAtoms: Atom[] = [];
        const protons = field.particles.filter(p => p.particleType === ParticleType.PROTON);
        const electrons = field.particles.filter(p => p.particleType === ParticleType.ELECTRON);

        for (const proton of protons) {
            if (electrons.length === 0) break;
            electrons.pop();
            const atom = new Atom(1, 1, [...proton.position]);
            newAtoms.push(atom);
            this.atoms.push(atom);
            field.particles = field.particles.filter(p => p !== proton);
        }

        // Remove used electrons
        const usedCount = newAtoms.length;
        const electronSet = new Set(field.particles.filter(p => p.particleType === ParticleType.ELECTRON));
        let removed = 0;
        field.particles = field.particles.filter(p => {
            if (p.particleType === ParticleType.ELECTRON && removed < usedCount) {
                removed++;
                return false;
            }
            return true;
        });

        return newAtoms;
    }

    nucleosynthesis(protons: number, neutrons: number): Atom[] {
        const newAtoms: Atom[] = [];

        // He-4: 2p + 2n
        while (protons >= 2 && neutrons >= 2) {
            const he = new Atom(2, 4, [rng.gauss(0, 10), rng.gauss(0, 10), rng.gauss(0, 10)]);
            newAtoms.push(he);
            this.atoms.push(he);
            protons -= 2;
            neutrons -= 2;
        }

        // Remaining protons -> H
        for (let i = 0; i < protons; i++) {
            const h = new Atom(1, 1, [rng.gauss(0, 10), rng.gauss(0, 10), rng.gauss(0, 10)]);
            newAtoms.push(h);
            this.atoms.push(h);
        }

        return newAtoms;
    }

    stellarNucleosynthesis(temperature: number): Atom[] {
        const newAtoms: Atom[] = [];
        if (temperature < 1e3) return newAtoms;

        let heliums = this.atoms.filter(a => a.atomicNumber === 2);

        // Triple-alpha: 3 He -> C
        while (heliums.length >= 3 && rng.random() < 0.01) {
            for (let i = 0; i < 3; i++) {
                const he = heliums.pop()!;
                this.atoms = this.atoms.filter(a => a !== he);
            }
            const carbon = new Atom(6, 12, [rng.gauss(0, 5), rng.gauss(0, 5), rng.gauss(0, 5)]);
            newAtoms.push(carbon);
            this.atoms.push(carbon);
        }

        // C + He -> O
        let carbons = this.atoms.filter(a => a.atomicNumber === 6);
        heliums = this.atoms.filter(a => a.atomicNumber === 2);
        while (carbons.length > 0 && heliums.length > 0 && rng.random() < 0.02) {
            const c = carbons.pop()!;
            const he = heliums.pop()!;
            this.atoms = this.atoms.filter(a => a !== c && a !== he);
            const oxygen = new Atom(8, 16, [...c.position]);
            newAtoms.push(oxygen);
            this.atoms.push(oxygen);
        }

        // O + He -> N (simplified chain)
        const oxygens = this.atoms.filter(a => a.atomicNumber === 8);
        heliums = this.atoms.filter(a => a.atomicNumber === 2);
        if (oxygens.length > 0 && heliums.length > 0 && rng.random() < 0.005) {
            const o = oxygens[0];
            const he = heliums[0];
            this.atoms = this.atoms.filter(a => a !== o && a !== he);
            const nitrogen = new Atom(7, 14, [...o.position]);
            newAtoms.push(nitrogen);
            this.atoms.push(nitrogen);
        }

        return newAtoms;
    }

    elementCounts(): Record<string, number> {
        const counts: Record<string, number> = {};
        for (const a of this.atoms) {
            counts[a.symbol] = (counts[a.symbol] || 0) + 1;
        }
        return counts;
    }
}

// ============================================================================
// Chemistry
// ============================================================================

let moleculeIdCounter = 0;

export class Molecule {
    atoms: Atom[];
    name: string;
    formula: string;
    moleculeId: number;
    energy: number;
    position: number[];
    isOrganic: boolean;
    functionalGroups: string[];

    constructor(atoms: Atom[], name: string = "", position?: number[]) {
        this.atoms = atoms;
        this.name = name;
        this.formula = "";
        this.moleculeId = ++moleculeIdCounter;
        this.energy = 0;
        this.position = position ?? [0, 0, 0];
        this.isOrganic = false;
        this.functionalGroups = [];
        this._computeFormula();
    }

    private _computeFormula(): void {
        const counts: Record<string, number> = {};
        for (const atom of this.atoms) {
            counts[atom.symbol] = (counts[atom.symbol] || 0) + 1;
        }
        const parts: string[] = [];
        for (const sym of ["C", "H"]) {
            if (counts[sym]) {
                parts.push(counts[sym] > 1 ? `${sym}${counts[sym]}` : sym);
                delete counts[sym];
            }
        }
        for (const sym of Object.keys(counts).sort()) {
            parts.push(counts[sym] > 1 ? `${sym}${counts[sym]}` : sym);
        }
        this.formula = parts.join("");
        const hasC = this.atoms.some(a => a.atomicNumber === 6);
        const hasH = this.atoms.some(a => a.atomicNumber === 1);
        this.isOrganic = hasC && hasH;
    }

    get molecularWeight(): number {
        return this.atoms.reduce((s, a) => s + a.massNumber, 0);
    }
}

export class ChemicalSystem {
    atomic: AtomicSystem;
    molecules: Molecule[];
    reactionsOccurred: number;
    waterCount: number;
    aminoAcidCount: number;
    nucleotideCount: number;

    constructor(atomicSystem: AtomicSystem) {
        this.atomic = atomicSystem;
        this.molecules = [];
        this.reactionsOccurred = 0;
        this.waterCount = 0;
        this.aminoAcidCount = 0;
        this.nucleotideCount = 0;
    }

    formWater(): Molecule[] {
        const waters: Molecule[] = [];
        const hydrogens = this.atomic.atoms.filter(a => a.atomicNumber === 1 && a.bonds.length === 0);
        const oxygens = this.atomic.atoms.filter(a => a.atomicNumber === 8 && a.bonds.length < 2);

        while (hydrogens.length >= 2 && oxygens.length > 0) {
            const h1 = hydrogens.pop()!;
            const h2 = hydrogens.pop()!;
            const o = oxygens.pop()!;
            const water = new Molecule([h1, h2, o], "water", [...o.position]);
            waters.push(water);
            this.molecules.push(water);
            this.waterCount++;
            h1.bonds.push(o.atomId);
            h2.bonds.push(o.atomId);
            o.bonds.push(h1.atomId, h2.atomId);
        }
        return waters;
    }

    formMethane(): Molecule[] {
        const methanes: Molecule[] = [];
        const carbons = this.atomic.atoms.filter(a => a.atomicNumber === 6 && a.bonds.length === 0);
        const hydrogens = this.atomic.atoms.filter(a => a.atomicNumber === 1 && a.bonds.length === 0);

        while (carbons.length > 0 && hydrogens.length >= 4) {
            const c = carbons.pop()!;
            const hs = [hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!];
            const methane = new Molecule([c, ...hs], "methane", [...c.position]);
            methanes.push(methane);
            this.molecules.push(methane);
            for (const h of hs) {
                c.bonds.push(h.atomId);
                h.bonds.push(c.atomId);
            }
        }
        return methanes;
    }

    formAmmonia(): Molecule[] {
        const ammonias: Molecule[] = [];
        const nitrogens = this.atomic.atoms.filter(a => a.atomicNumber === 7 && a.bonds.length === 0);
        const hydrogens = this.atomic.atoms.filter(a => a.atomicNumber === 1 && a.bonds.length === 0);

        while (nitrogens.length > 0 && hydrogens.length >= 3) {
            const n = nitrogens.pop()!;
            const hs = [hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!];
            const ammonia = new Molecule([n, ...hs], "ammonia", [...n.position]);
            ammonias.push(ammonia);
            this.molecules.push(ammonia);
            for (const h of hs) {
                n.bonds.push(h.atomId);
                h.bonds.push(n.atomId);
            }
        }
        return ammonias;
    }

    formAminoAcid(aaType: string = "Gly"): Molecule | null {
        const carbons = this.atomic.atoms.filter(a => a.atomicNumber === 6 && a.bonds.length === 0);
        const hydrogens = this.atomic.atoms.filter(a => a.atomicNumber === 1 && a.bonds.length === 0);
        const oxygens = this.atomic.atoms.filter(a => a.atomicNumber === 8 && a.bonds.length < 2);
        const nitrogens = this.atomic.atoms.filter(a => a.atomicNumber === 7 && a.bonds.length === 0);

        if (carbons.length < 2 || hydrogens.length < 5 || oxygens.length < 2 || nitrogens.length < 1) {
            return null;
        }

        const atoms = [
            carbons.pop()!, carbons.pop()!,
            hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!, hydrogens.pop()!,
            oxygens.pop()!, oxygens.pop()!,
            nitrogens.pop()!,
        ];

        const aa = new Molecule(atoms, aaType, [...atoms[0].position]);
        aa.isOrganic = true;
        aa.functionalGroups = ["amino", "carboxyl"];
        this.molecules.push(aa);
        this.aminoAcidCount++;

        for (let i = 1; i < atoms.length; i++) {
            atoms[0].bonds.push(atoms[i].atomId);
            atoms[i].bonds.push(atoms[0].atomId);
        }
        return aa;
    }

    formNucleotide(base: string = "A"): Molecule | null {
        const carbons = this.atomic.atoms.filter(a => a.atomicNumber === 6 && a.bonds.length === 0);
        const hydrogens = this.atomic.atoms.filter(a => a.atomicNumber === 1 && a.bonds.length === 0);
        const oxygens = this.atomic.atoms.filter(a => a.atomicNumber === 8 && a.bonds.length < 2);
        const nitrogens = this.atomic.atoms.filter(a => a.atomicNumber === 7 && a.bonds.length === 0);

        if (carbons.length < 5 || hydrogens.length < 8 || oxygens.length < 4 || nitrogens.length < 2) {
            return null;
        }

        const atoms: Atom[] = [];
        for (let i = 0; i < 5; i++) atoms.push(carbons.pop()!);
        for (let i = 0; i < 8; i++) atoms.push(hydrogens.pop()!);
        for (let i = 0; i < 4; i++) atoms.push(oxygens.pop()!);
        for (let i = 0; i < 2; i++) atoms.push(nitrogens.pop()!);

        const nuc = new Molecule(atoms, `nucleotide-${base}`, [...atoms[0].position]);
        nuc.isOrganic = true;
        nuc.functionalGroups = ["sugar", "phosphate", "base"];
        this.molecules.push(nuc);
        this.nucleotideCount++;

        for (let i = 1; i < atoms.length; i++) {
            atoms[0].bonds.push(atoms[i].atomId);
            atoms[i].bonds.push(atoms[0].atomId);
        }
        return nuc;
    }

    catalyzedReaction(temperature: number, catalystPresent: boolean = false): number {
        let formed = 0;
        const eaFactor = catalystPresent ? 0.3 : 1.0;
        const thermal = K_B * temperature;

        if (thermal > 0 && this.atomic.atoms.length > 10) {
            const aaProb = Math.exp(-5.0 * eaFactor / (thermal + 1e-20));
            if (rng.random() < aaProb) {
                const aaType = rng.choice(AMINO_ACIDS);
                if (this.formAminoAcid(aaType)) {
                    formed++;
                    this.reactionsOccurred++;
                }
            }
        }

        if (thermal > 0 && this.atomic.atoms.length > 19) {
            const nucProb = Math.exp(-8.0 * eaFactor / (thermal + 1e-20));
            if (rng.random() < nucProb) {
                const base = rng.choice(["A", "T", "G", "C"]);
                if (this.formNucleotide(base)) {
                    formed++;
                    this.reactionsOccurred++;
                }
            }
        }

        return formed;
    }

    moleculeCensus(): Record<string, number> {
        const counts: Record<string, number> = {};
        for (const m of this.molecules) {
            const key = m.name || m.formula;
            counts[key] = (counts[key] || 0) + 1;
        }
        return counts;
    }
}

// ============================================================================
// Biology
// ============================================================================

export class Gene {
    name: string;
    sequence: string[];
    startPos: number;
    endPos: number;
    expressionLevel: number;
    epigeneticMarks: { position: number; markType: string; active: boolean; generationAdded: number }[];
    essential: boolean;

    constructor(name: string, sequence: string[], startPos: number, endPos: number, essential: boolean = false) {
        this.name = name;
        this.sequence = sequence;
        this.startPos = startPos;
        this.endPos = endPos;
        this.expressionLevel = 1.0;
        this.epigeneticMarks = [];
        this.essential = essential;
    }

    get length(): number {
        return this.sequence.length;
    }

    get isSilenced(): boolean {
        const methylCount = this.epigeneticMarks.filter(m => m.markType === "methylation" && m.active).length;
        return methylCount > this.length * 0.3;
    }

    methylate(position: number, generation: number = 0): void {
        if (position >= 0 && position < this.length) {
            this.epigeneticMarks.push({ position, markType: "methylation", active: true, generationAdded: generation });
            this._updateExpression();
        }
    }

    demethylate(position: number): void {
        this.epigeneticMarks = this.epigeneticMarks.filter(
            m => !(m.position === position && m.markType === "methylation")
        );
        this._updateExpression();
    }

    acetylate(position: number, generation: number = 0): void {
        this.epigeneticMarks.push({ position, markType: "acetylation", active: true, generationAdded: generation });
        this._updateExpression();
    }

    _updateExpression(): void {
        const methyl = this.epigeneticMarks.filter(m => m.markType === "methylation" && m.active).length;
        const acetyl = this.epigeneticMarks.filter(m => m.markType === "acetylation" && m.active).length;
        const suppression = Math.min(1.0, methyl / Math.max(1, this.length) * 3);
        const activation = Math.min(1.0, acetyl / Math.max(1, this.length) * 5);
        this.expressionLevel = Math.max(0.0, Math.min(1.0, 1.0 - suppression + activation));
    }

    transcribe(): string[] {
        if (this.isSilenced) return [];
        return this.sequence.map(b => b === "T" ? "U" : b);
    }

    mutate(rate: number = 0.001): number {
        let mutations = 0;
        for (let i = 0; i < this.length; i++) {
            if (rng.random() < rate) {
                const old = this.sequence[i];
                const choices = NUCLEOTIDE_BASES.filter(b => b !== old);
                this.sequence[i] = rng.choice(choices);
                mutations++;
            }
        }
        return mutations;
    }
}

export class DNAStrand {
    sequence: string[];
    genes: Gene[];
    generation: number;
    mutationCount: number;

    static COMPLEMENT: Record<string, string> = { A: "T", T: "A", G: "C", C: "G" };

    constructor(sequence: string[], genes: Gene[] = [], generation: number = 0) {
        this.sequence = sequence;
        this.genes = genes;
        this.generation = generation;
        this.mutationCount = 0;
    }

    get length(): number {
        return this.sequence.length;
    }

    get gcContent(): number {
        if (this.sequence.length === 0) return 0;
        const gc = this.sequence.filter(b => b === "G" || b === "C").length;
        return gc / this.sequence.length;
    }

    static randomStrand(length: number, numGenes: number = 3): DNAStrand {
        const sequence = Array.from({ length }, () => rng.choice(NUCLEOTIDE_BASES));
        const strand = new DNAStrand(sequence);

        const geneLen = Math.floor(length / (numGenes + 1));
        for (let i = 0; i < numGenes; i++) {
            const start = i * geneLen + rng.randint(0, Math.floor(geneLen / 4));
            let end = start + Math.floor(geneLen / 2);
            if (end > length) end = length;

            const gene = new Gene(
                `gene_${i}`,
                sequence.slice(start, end),
                start,
                end,
                i === 0, // first gene is essential
            );
            strand.genes.push(gene);
        }
        return strand;
    }

    replicate(): DNAStrand {
        const newSequence = [...this.sequence];
        const newGenes: Gene[] = [];

        for (const gene of this.genes) {
            const newGene = new Gene(
                gene.name,
                [...gene.sequence],
                gene.startPos,
                gene.endPos,
                gene.essential,
            );
            newGene.epigeneticMarks = gene.epigeneticMarks
                .filter(() => rng.random() < 0.7)
                .map(m => ({
                    position: m.position,
                    markType: m.markType,
                    active: m.active && rng.random() < 0.8,
                    generationAdded: m.generationAdded,
                }));
            newGene._updateExpression();
            newGenes.push(newGene);
        }

        return new DNAStrand(newSequence, newGenes, this.generation + 1);
    }

    applyMutations(uvIntensity: number = 0, cosmicRayFlux: number = 0): number {
        let totalMutations = 0;
        const rate = UV_MUTATION_RATE * uvIntensity + COSMIC_RAY_MUTATION_RATE * cosmicRayFlux;

        for (const gene of this.genes) {
            totalMutations += gene.mutate(rate);
        }

        for (let i = 0; i < this.length; i++) {
            if (rng.random() < rate) {
                const old = this.sequence[i];
                const choices = NUCLEOTIDE_BASES.filter(b => b !== old);
                this.sequence[i] = rng.choice(choices);
                totalMutations++;
            }
        }

        this.mutationCount += totalMutations;
        return totalMutations;
    }

    applyEpigeneticChanges(temperature: number, generation: number = 0): void {
        for (const gene of this.genes) {
            if (rng.random() < METHYLATION_PROBABILITY) {
                gene.methylate(rng.randint(0, Math.max(0, gene.length - 1)), generation);
            }
            if (rng.random() < DEMETHYLATION_PROBABILITY) {
                const methyls = gene.epigeneticMarks.filter(m => m.markType === "methylation");
                if (methyls.length > 0) {
                    const mark = rng.choice(methyls);
                    gene.demethylate(mark.position);
                }
            }
            const thermalFactor = Math.min(2.0, temperature / 300.0);
            if (rng.random() < HISTONE_ACETYLATION_PROB * thermalFactor) {
                gene.acetylate(rng.randint(0, Math.max(0, gene.length - 1)), generation);
            }
            if (rng.random() < HISTONE_DEACETYLATION_PROB) {
                const acetyls = gene.epigeneticMarks.filter(m => m.markType === "acetylation");
                if (acetyls.length > 0) {
                    const mark = rng.choice(acetyls);
                    mark.active = false;
                    gene._updateExpression();
                }
            }
        }
    }
}

function translateMRNA(mrna: string[]): string[] {
    const protein: string[] = [];
    let i = 0;
    let started = false;

    while (i + 2 < mrna.length) {
        const codon = mrna[i] + mrna[i + 1] + mrna[i + 2];
        const aa = CODON_TABLE[codon];

        if (aa === "Met" && !started) {
            started = true;
            protein.push(aa);
        } else if (started) {
            if (aa === "STOP") break;
            if (aa) protein.push(aa);
        }
        i += 3;
    }
    return protein;
}

export class Protein {
    aminoAcids: string[];
    name: string;
    func: string;
    folded: boolean;
    active: boolean;

    constructor(aminoAcids: string[], name: string = "", func: string = "") {
        this.aminoAcids = aminoAcids;
        this.name = name;
        this.func = func;
        this.folded = false;
        this.active = true;
    }

    get length(): number {
        return this.aminoAcids.length;
    }

    fold(): boolean {
        if (this.length < 3) {
            this.folded = false;
            return false;
        }
        const foldProb = Math.min(0.9, 0.5 + 0.1 * Math.log(this.length + 1));
        this.folded = rng.random() < foldProb;
        return this.folded;
    }
}

let cellIdCounter = 0;

export class Cell {
    dna: DNAStrand;
    proteins: Protein[];
    fitness: number;
    alive: boolean;
    generation: number;
    energy: number;
    cellId: number;

    constructor(dna?: DNAStrand, generation: number = 0, energy: number = 100) {
        this.dna = dna ?? DNAStrand.randomStrand(100);
        this.proteins = [];
        this.fitness = 1.0;
        this.alive = true;
        this.generation = generation;
        this.energy = energy;
        this.cellId = ++cellIdCounter;
    }

    transcribeAndTranslate(): Protein[] {
        const newProteins: Protein[] = [];
        for (const gene of this.dna.genes) {
            if (gene.expressionLevel < 0.1) continue;
            const mrna = gene.transcribe();
            if (mrna.length === 0) continue;
            const aaSeq = translateMRNA(mrna);
            if (aaSeq.length === 0) continue;
            if (rng.random() > gene.expressionLevel) continue;

            const protein = new Protein(
                aaSeq,
                `protein_${gene.name}`,
                rng.choice(["enzyme", "structural", "signaling"]),
            );
            protein.fold();
            newProteins.push(protein);
            this.proteins.push(protein);
        }
        return newProteins;
    }

    metabolize(environmentEnergy: number = 10.0): void {
        const enzymeCount = this.proteins.filter(p => p.func === "enzyme" && p.folded && p.active).length;
        const efficiency = 0.3 + 0.15 * enzymeCount;
        this.energy += environmentEnergy * efficiency;
        this.energy -= 3.0;
        this.energy = Math.min(this.energy, 200);
        if (this.energy <= 0) this.alive = false;
    }

    divide(): Cell | null {
        if (!this.alive || this.energy < 50) return null;

        const newDNA = this.dna.replicate();
        this.energy /= 2;

        const daughter = new Cell(newDNA, this.generation + 1, this.energy);
        daughter.transcribeAndTranslate();
        return daughter;
    }

    computeFitness(): number {
        if (!this.alive) {
            this.fitness = 0;
            return 0;
        }

        const essentialActive = this.dna.genes
            .filter(g => g.essential)
            .every(g => !g.isSilenced);

        if (!essentialActive) {
            this.fitness = 0.1;
            return 0.1;
        }

        const functionalProteins = this.proteins.filter(p => p.folded && p.active).length;
        const proteinFitness = Math.min(1.0, functionalProteins / Math.max(1, this.dna.genes.length));
        const energyFitness = Math.min(1.0, this.energy / 100.0);
        const gcFitness = 1.0 - Math.abs(this.dna.gcContent - 0.5) * 2;

        this.fitness = proteinFitness * 0.4 + energyFitness * 0.3 + gcFitness * 0.3;
        return this.fitness;
    }
}

export class Biosphere {
    cells: Cell[];
    generation: number;
    totalBorn: number;
    totalDied: number;
    dnaLength: number;

    constructor(initialCells: number = 5, dnaLength: number = 90) {
        this.cells = [];
        this.generation = 0;
        this.totalBorn = 0;
        this.totalDied = 0;
        this.dnaLength = dnaLength;

        for (let i = 0; i < initialCells; i++) {
            const cell = new Cell(DNAStrand.randomStrand(dnaLength, 3));
            cell.transcribeAndTranslate();
            this.cells.push(cell);
            this.totalBorn++;
        }
    }

    step(environmentEnergy: number = 10, uvIntensity: number = 0, cosmicRayFlux: number = 0, temperature: number = 300): void {
        this.generation++;

        for (const cell of this.cells) cell.metabolize(environmentEnergy);

        for (const cell of this.cells) {
            if (cell.alive) {
                cell.dna.applyMutations(uvIntensity, cosmicRayFlux);
                cell.dna.applyEpigeneticChanges(temperature, this.generation);
            }
        }

        for (const cell of this.cells) {
            if (cell.alive) cell.transcribeAndTranslate();
        }

        for (const cell of this.cells) cell.computeFitness();

        // Selection and reproduction
        const aliveCells = this.cells.filter(c => c.alive);
        if (aliveCells.length > 0) {
            aliveCells.sort((a, b) => b.fitness - a.fitness);
            const cutoff = Math.max(1, Math.floor(aliveCells.length / 2));
            const newCells: Cell[] = [];
            for (const cell of aliveCells.slice(0, cutoff)) {
                const daughter = cell.divide();
                if (daughter) {
                    newCells.push(daughter);
                    this.totalBorn++;
                }
            }
            this.cells.push(...newCells);
        }

        // Remove dead
        const dead = this.cells.filter(c => !c.alive);
        this.totalDied += dead.length;
        this.cells = this.cells.filter(c => c.alive);

        // Population cap
        if (this.cells.length > 100) {
            this.cells.sort((a, b) => b.fitness - a.fitness);
            this.totalDied += this.cells.length - 100;
            this.cells = this.cells.slice(0, 100);
        }
    }

    averageFitness(): number {
        if (this.cells.length === 0) return 0;
        return this.cells.reduce((s, c) => s + c.fitness, 0) / this.cells.length;
    }

    totalMutations(): number {
        return this.cells.reduce((s, c) => s + c.dna.mutationCount, 0);
    }
}

// ============================================================================
// Environment
// ============================================================================

export interface EnvironmentalEvent {
    eventType: string;
    intensity: number;
    duration: number;
    tickOccurred: number;
}

export class Environment {
    temperature: number;
    uvIntensity: number;
    cosmicRayFlux: number;
    stellarWind: number;
    atmosphericDensity: number;
    waterAvailability: number;
    dayNightCycle: number;
    season: number;
    events: EnvironmentalEvent[];
    tick: number;

    constructor(initialTemperature: number = T_PLANCK) {
        this.temperature = initialTemperature;
        this.uvIntensity = 0;
        this.cosmicRayFlux = 0;
        this.stellarWind = 0;
        this.atmosphericDensity = 0;
        this.waterAvailability = 0;
        this.dayNightCycle = 0;
        this.season = 0;
        this.events = [];
        this.tick = 0;
    }

    update(epoch: number): void {
        this.tick++;

        // Temperature evolution
        if (epoch < 1000) {
            this.temperature = T_PLANCK * Math.exp(-epoch / 200);
        } else if (epoch < 50000) {
            this.temperature = Math.max(T_CMB, T_PLANCK * Math.exp(-epoch / 200));
        } else if (epoch < 200000) {
            this.temperature = T_CMB + rng.gauss(0, 0.5);
        } else {
            this.temperature = T_EARTH_SURFACE + rng.gauss(0, 5);
            this.dayNightCycle = (this.tick % 100) / 100.0;
            const tempMod = 10 * Math.sin(this.dayNightCycle * 2 * PI);
            this.temperature += tempMod;
            this.season = (this.tick % 1000) / 1000.0;
            const seasonMod = 15 * Math.sin(this.season * 2 * PI);
            this.temperature += seasonMod;
        }

        // UV intensity
        if (epoch > 100000) {
            const baseUV = 1.0;
            if (this.dayNightCycle > 0.25 && this.dayNightCycle < 0.75) {
                this.uvIntensity = baseUV * Math.sin((this.dayNightCycle - 0.25) * 2 * PI);
            } else {
                this.uvIntensity = 0;
            }
        } else {
            this.uvIntensity = 0;
        }

        // Cosmic ray flux
        if (epoch > 10000) {
            this.cosmicRayFlux = 0.1 + rng.expovariate(10.0);
        } else {
            this.cosmicRayFlux = 1.0;
        }

        // Atmospheric density
        if (epoch > 210000) {
            this.atmosphericDensity = Math.min(1.0, (epoch - 210000) / 50000);
            this.uvIntensity *= (1 - this.atmosphericDensity * 0.7);
            this.cosmicRayFlux *= (1 - this.atmosphericDensity * 0.5);
        }

        // Water
        if (epoch > 220000) {
            this.waterAvailability = Math.min(1.0, (epoch - 220000) / 30000);
        }

        // Random events
        this._generateEvents(epoch);
        this._processEvents();
    }

    private _generateEvents(epoch: number): void {
        if (epoch > 210000 && rng.random() < 0.005) {
            this.events.push({ eventType: "volcanic", intensity: rng.uniform(0.5, 3.0), duration: rng.randint(10, 100), tickOccurred: this.tick });
        }
        if (rng.random() < 0.0001) {
            this.events.push({ eventType: "asteroid", intensity: rng.uniform(1.0, 10.0), duration: rng.randint(50, 500), tickOccurred: this.tick });
        }
        if (epoch > 100000 && rng.random() < 0.01) {
            this.events.push({ eventType: "solar_flare", intensity: rng.uniform(0.1, 2.0), duration: rng.randint(5, 20), tickOccurred: this.tick });
        }
        if (epoch > 250000 && rng.random() < 0.001) {
            this.events.push({ eventType: "ice_age", intensity: rng.uniform(0.5, 1.5), duration: rng.randint(500, 2000), tickOccurred: this.tick });
        }
    }

    private _processEvents(): void {
        const active: EnvironmentalEvent[] = [];
        for (const event of this.events) {
            const elapsed = this.tick - event.tickOccurred;
            if (elapsed < event.duration) {
                active.push(event);
                this._applyEvent(event);
            }
        }
        this.events = active;
    }

    private _applyEvent(event: EnvironmentalEvent): void {
        switch (event.eventType) {
            case "volcanic":
                this.temperature += event.intensity * 2;
                this.atmosphericDensity = Math.min(1, this.atmosphericDensity + 0.01);
                this.uvIntensity *= 0.9;
                break;
            case "asteroid":
                this.temperature -= event.intensity * 5;
                this.cosmicRayFlux += event.intensity;
                this.uvIntensity *= 0.5;
                break;
            case "solar_flare":
                this.uvIntensity += event.intensity;
                this.cosmicRayFlux += event.intensity * 0.5;
                break;
            case "ice_age":
                this.temperature -= event.intensity * 20;
                this.waterAvailability *= 0.8;
                break;
        }
    }

    getRadiationDose(): number {
        return this.uvIntensity + this.cosmicRayFlux + this.stellarWind;
    }

    isHabitable(): boolean {
        return this.temperature > 200 && this.temperature < 400
            && this.waterAvailability > 0.1
            && this.getRadiationDose() < RADIATION_DAMAGE_THRESHOLD;
    }

    thermalEnergy(): number {
        if (this.temperature < 100 || this.temperature > 500) return 0.1;
        return Math.max(0.1, this.temperature * 0.1);
    }
}

// ============================================================================
// Universe Orchestrator
// ============================================================================

export interface SimulationSnapshot {
    tick: number;
    epoch: string;
    epochDescription: string;
    temperature: number;
    particles: number;
    atoms: number;
    molecules: number;
    cells: number;
    fitness: number;
    mutations: number;
    generation: number;
    particleCounts: Record<string, number>;
    elementCounts: Record<string, number>;
    moleculeCounts: Record<string, number>;
    dnaSequences: string[];
    isHabitable: boolean;
    uvIntensity: number;
    cosmicRayFlux: number;
}

export class Universe {
    tick: number;
    maxTicks: number;
    stepSize: number;
    currentEpochName: string;

    quantumField: QuantumField;
    atomicSystem: AtomicSystem;
    chemicalSystem: ChemicalSystem | null;
    biosphere: Biosphere | null;
    environment: Environment;

    particlesCreated: number;
    atomsFormed: number;
    moleculesFormed: number;
    cellsBorn: number;
    mutationCount: number;

    private seed: number;

    constructor(seed: number = 42, maxTicks: number = PRESENT_EPOCH, stepSize: number = 1) {
        this.seed = seed;
        rng = new RNG(seed);
        particleIdCounter = 0;
        atomIdCounter = 0;
        moleculeIdCounter = 0;
        cellIdCounter = 0;

        this.tick = 0;
        this.maxTicks = maxTicks;
        this.stepSize = stepSize;
        this.currentEpochName = "Void";

        this.quantumField = new QuantumField(T_PLANCK);
        this.atomicSystem = new AtomicSystem();
        this.chemicalSystem = null;
        this.biosphere = null;
        this.environment = new Environment(T_PLANCK);

        this.particlesCreated = 0;
        this.atomsFormed = 0;
        this.moleculesFormed = 0;
        this.cellsBorn = 0;
        this.mutationCount = 0;
    }

    private _getEpochName(): string {
        let name = "Void";
        for (const epoch of EPOCHS) {
            if (this.tick >= epoch.startTick) name = epoch.name;
        }
        return name;
    }

    private _getEpochDescription(): string {
        let desc = "";
        for (const epoch of EPOCHS) {
            if (this.tick >= epoch.startTick) desc = epoch.description;
        }
        return desc;
    }

    private _seedEarlyUniverse(): void {
        // Quarks
        for (let i = 0; i < 30; i++) {
            this.quantumField.particles.push(new Particle(
                ParticleType.UP,
                [rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)],
                [rng.gauss(0, 5), rng.gauss(0, 5), rng.gauss(0, 5)],
                rng.choice([Spin.UP, Spin.DOWN]),
                rng.choice([Color.RED, Color.GREEN, Color.BLUE]),
            ));
        }
        for (let i = 0; i < 20; i++) {
            this.quantumField.particles.push(new Particle(
                ParticleType.DOWN,
                [rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)],
                [rng.gauss(0, 5), rng.gauss(0, 5), rng.gauss(0, 5)],
                rng.choice([Spin.UP, Spin.DOWN]),
                rng.choice([Color.RED, Color.GREEN, Color.BLUE]),
            ));
        }
        for (let i = 0; i < 40; i++) {
            this.quantumField.particles.push(new Particle(
                ParticleType.ELECTRON,
                [rng.gauss(0, 2), rng.gauss(0, 2), rng.gauss(0, 2)],
                [rng.gauss(0, 3), rng.gauss(0, 3), rng.gauss(0, 3)],
            ));
        }
        for (let i = 0; i < 5; i++) {
            this.quantumField.particles.push(new Particle(
                ParticleType.PHOTON,
                [0, 0, 0],
                [rng.gauss(0, 10), rng.gauss(0, 10), rng.gauss(0, 10)],
            ));
        }
        this.particlesCreated += this.quantumField.particles.length;
    }

    step(): void {
        this.tick += this.stepSize;

        // Check epoch transition
        const newEpoch = this._getEpochName();
        if (newEpoch !== this.currentEpochName) {
            this.currentEpochName = newEpoch;
        }

        // Update environment
        this.environment.update(this.tick);

        // === Quantum level ===
        if (this.tick <= HADRON_EPOCH) {
            this.quantumField.temperature = this.environment.temperature;

            if (this.quantumField.particles.length === 0 && this.environment.temperature > 100) {
                this._seedEarlyUniverse();
            }

            if (this.environment.temperature > 100) {
                const nAttempts = Math.min(5, Math.max(1, Math.floor(this.environment.temperature / 1000)));
                for (let i = 0; i < nAttempts; i++) {
                    const result = this.quantumField.vacuumFluctuation();
                    if (result) this.particlesCreated += 2;
                }
            }

            this.quantumField.evolve(this.stepSize);
        }

        // === Hadron formation ===
        if (HADRON_EPOCH - this.stepSize < this.tick && this.tick <= HADRON_EPOCH + this.stepSize) {
            this.quantumField.temperature = this.environment.temperature;
            const hadrons = this.quantumField.quarkConfinement();
            if (hadrons.length > 0) this.particlesCreated += hadrons.length;
        }

        // === Nucleosynthesis ===
        if (this.tick >= NUCLEOSYNTHESIS_EPOCH && this.tick < RECOMBINATION_EPOCH) {
            const protons = this.quantumField.particles.filter(p => p.particleType === ParticleType.PROTON).length;
            const neutrons = this.quantumField.particles.filter(p => p.particleType === ParticleType.NEUTRON).length;

            if (protons > 0 || neutrons > 0) {
                const newAtoms = this.atomicSystem.nucleosynthesis(protons, neutrons);
                // Remove used particles
                this.quantumField.particles = this.quantumField.particles.filter(
                    p => p.particleType !== ParticleType.PROTON && p.particleType !== ParticleType.NEUTRON
                );
                this.atomsFormed += newAtoms.length;
            }
        }

        // === Recombination ===
        if (RECOMBINATION_EPOCH - this.stepSize < this.tick && this.tick <= RECOMBINATION_EPOCH + this.stepSize) {
            this.atomicSystem.temperature = this.environment.temperature;
            const newAtoms = this.atomicSystem.recombination(this.quantumField);
            this.atomsFormed += newAtoms.length;
        }

        // === Star formation ===
        if (this.tick >= STAR_FORMATION_EPOCH && this.tick < SOLAR_SYSTEM_EPOCH) {
            this.atomicSystem.temperature = this.environment.temperature;
            const newHeavy = this.atomicSystem.stellarNucleosynthesis(this.environment.temperature * 100);
            this.atomsFormed += newHeavy.length;
        }

        // === Chemistry ===
        if (this.tick >= EARTH_EPOCH) {
            if (this.chemicalSystem === null) {
                this.chemicalSystem = new ChemicalSystem(this.atomicSystem);
            }

            if (EARTH_EPOCH - this.stepSize < this.tick && this.tick <= EARTH_EPOCH + this.stepSize) {
                // Seed elements
                const elementsToSeed: [number, number][] = [
                    [1, 40], [2, 10], [6, 15], [7, 10], [8, 15], [15, 3],
                ];
                for (const [z, count] of elementsToSeed) {
                    for (let i = 0; i < count; i++) {
                        const a = new Atom(z, undefined, [rng.gauss(0, 5), rng.gauss(0, 5), rng.gauss(0, 5)]);
                        this.atomicSystem.atoms.push(a);
                        this.atomsFormed++;
                    }
                }

                // Form basic molecules
                const waters = this.chemicalSystem.formWater();
                const methanes = this.chemicalSystem.formMethane();
                const ammonias = this.chemicalSystem.formAmmonia();
                this.moleculesFormed += waters.length + methanes.length + ammonias.length;
            }

            if (this.tick > EARTH_EPOCH) {
                const formed = this.chemicalSystem.catalyzedReaction(
                    this.environment.temperature,
                    this.tick > LIFE_EPOCH,
                );
                this.moleculesFormed += formed;
            }
        }

        // === Biology ===
        if (this.tick >= LIFE_EPOCH && this.environment.isHabitable()) {
            if (this.biosphere === null) {
                this.biosphere = new Biosphere(3, 90);
                this.cellsBorn += 3;
            }

            this.biosphere.step(
                this.environment.thermalEnergy(),
                this.environment.uvIntensity,
                this.environment.cosmicRayFlux,
                this.environment.temperature,
            );

            this.cellsBorn = this.biosphere.totalBorn;
            this.mutationCount = this.biosphere.totalMutations();
        }
    }

    snapshot(): SimulationSnapshot {
        const dnaSequences: string[] = [];
        if (this.biosphere) {
            for (const cell of this.biosphere.cells.slice(0, 3)) {
                dnaSequences.push(cell.dna.sequence.slice(0, 30).join(""));
            }
        }

        return {
            tick: this.tick,
            epoch: this.currentEpochName,
            epochDescription: this._getEpochDescription(),
            temperature: this.environment.temperature,
            particles: this.quantumField.particles.length,
            atoms: this.atomicSystem.atoms.length,
            molecules: this.chemicalSystem ? this.chemicalSystem.molecules.length : 0,
            cells: this.biosphere ? this.biosphere.cells.length : 0,
            fitness: this.biosphere ? this.biosphere.averageFitness() : 0,
            mutations: this.mutationCount,
            generation: this.biosphere ? this.biosphere.generation : 0,
            particleCounts: this.quantumField.particleCount(),
            elementCounts: this.atomicSystem.elementCounts(),
            moleculeCounts: this.chemicalSystem ? this.chemicalSystem.moleculeCensus() : {},
            dnaSequences,
            isHabitable: this.environment.isHabitable(),
            uvIntensity: this.environment.uvIntensity,
            cosmicRayFlux: this.environment.cosmicRayFlux,
        };
    }

    /** Reset and restart with a new seed. */
    restart(newSeed?: number): void {
        const seed = newSeed ?? (this.seed + 1);
        rng = new RNG(seed);
        particleIdCounter = 0;
        atomIdCounter = 0;
        moleculeIdCounter = 0;
        cellIdCounter = 0;

        this.seed = seed;
        this.tick = 0;
        this.currentEpochName = "Void";
        this.quantumField = new QuantumField(T_PLANCK);
        this.atomicSystem = new AtomicSystem();
        this.chemicalSystem = null;
        this.biosphere = null;
        this.environment = new Environment(T_PLANCK);
        this.particlesCreated = 0;
        this.atomsFormed = 0;
        this.moleculesFormed = 0;
        this.cellsBorn = 0;
        this.mutationCount = 0;
    }
}
