/**
 * Atomic physics simulation.
 *
 * Models atoms with electron shells, ionization, chemical bonding potential,
 * and the periodic table. Atoms emerge from the quantum/nuclear level
 * when temperature drops below recombination threshold.
 */

import {
    ELECTRON_SHELLS, BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC,
    BOND_ENERGY_HYDROGEN, T_RECOMBINATION, E_CHARGE, HBAR,
    M_ELECTRON, ALPHA, C, K_B,
} from './constants.js';

import { Particle, ParticleType, QuantumField, gaussRandom } from './quantum.js';


// Periodic table data: [symbol, name, group, period, electronegativity]
export const ELEMENTS = {
    1:  ["H",  "Hydrogen",    1,  1, 2.20],
    2:  ["He", "Helium",      18, 1, 0.0],
    3:  ["Li", "Lithium",     1,  2, 0.98],
    4:  ["Be", "Beryllium",   2,  2, 1.57],
    5:  ["B",  "Boron",       13, 2, 2.04],
    6:  ["C",  "Carbon",      14, 2, 2.55],
    7:  ["N",  "Nitrogen",    15, 2, 3.04],
    8:  ["O",  "Oxygen",      16, 2, 3.44],
    9:  ["F",  "Fluorine",    17, 2, 3.98],
    10: ["Ne", "Neon",        18, 2, 0.0],
    11: ["Na", "Sodium",      1,  3, 0.93],
    12: ["Mg", "Magnesium",   2,  3, 1.31],
    13: ["Al", "Aluminum",    13, 3, 1.61],
    14: ["Si", "Silicon",     14, 3, 1.90],
    15: ["P",  "Phosphorus",  15, 3, 2.19],
    16: ["S",  "Sulfur",      16, 3, 2.58],
    17: ["Cl", "Chlorine",    17, 3, 3.16],
    18: ["Ar", "Argon",       18, 3, 0.0],
    19: ["K",  "Potassium",   1,  4, 0.82],
    20: ["Ca", "Calcium",     2,  4, 1.00],
    26: ["Fe", "Iron",        8,  4, 1.83],
};


// === ElectronShell ===

export class ElectronShell {
    /** An electron shell with quantum numbers. */
    constructor(n, maxElectrons, electrons = 0) {
        this.n = n;                     // Principal quantum number
        this.maxElectrons = maxElectrons; // 2n^2
        this.electrons = electrons;     // Current electron count
    }

    get full() {
        return this.electrons >= this.maxElectrons;
    }

    get empty() {
        return this.electrons === 0;
    }

    /** Add an electron if shell not full. */
    addElectron() {
        if (!this.full) {
            this.electrons++;
            return true;
        }
        return false;
    }

    /** Remove an electron if shell not empty. */
    removeElectron() {
        if (!this.empty) {
            this.electrons--;
            return true;
        }
        return false;
    }
}


// === Atom ===

let atomIdCounter = 0;

export class Atom {
    /**
     * An atom with protons, neutrons, and electron shells.
     */
    constructor({
        atomicNumber,
        massNumber = 0,
        electronCount = 0,
        position = [0.0, 0.0, 0.0],
        velocity = [0.0, 0.0, 0.0],
        shells = null,
        bonds = null,
    } = {}) {
        this.atomicNumber = atomicNumber;
        this.position = [...position];
        this.velocity = [...velocity];
        this.bonds = bonds ? [...bonds] : [];

        atomIdCounter++;
        this.atomId = atomIdCounter;

        // Mass number defaults
        if (massNumber === 0) {
            this.massNumber = atomicNumber * 2;
            if (atomicNumber === 1) this.massNumber = 1;
        } else {
            this.massNumber = massNumber;
        }

        // Electron count defaults to neutral atom
        this.electronCount = electronCount || atomicNumber;

        // Build shells
        this.shells = [];
        if (shells) {
            this.shells = shells;
        } else {
            this._buildShells();
        }

        this.ionizationEnergy = 0.0;
        this._computeIonizationEnergy();
    }

    _buildShells() {
        this.shells = [];
        let remaining = this.electronCount;
        for (let i = 0; i < ELECTRON_SHELLS.length; i++) {
            if (remaining <= 0) break;
            const maxE = ELECTRON_SHELLS[i];
            const shell = new ElectronShell(
                i + 1,
                maxE,
                Math.min(remaining, maxE),
            );
            this.shells.push(shell);
            remaining -= shell.electrons;
        }
    }

    _computeIonizationEnergy() {
        if (this.shells.length === 0 || this.shells[this.shells.length - 1].empty) {
            this.ionizationEnergy = 0.0;
            return;
        }
        const n = this.shells[this.shells.length - 1].n;
        let innerElectrons = 0;
        for (let i = 0; i < this.shells.length - 1; i++) {
            innerElectrons += this.shells[i].electrons;
        }
        const zEff = this.atomicNumber - innerElectrons;
        // Hydrogen-like approximation: E = 13.6 * Z_eff^2 / n^2
        this.ionizationEnergy = 13.6 * zEff ** 2 / n ** 2;
    }

    get symbol() {
        const elem = ELEMENTS[this.atomicNumber];
        return elem ? elem[0] : `E${this.atomicNumber}`;
    }

    get name() {
        const elem = ELEMENTS[this.atomicNumber];
        return elem ? elem[1] : `Element-${this.atomicNumber}`;
    }

    get electronegativity() {
        const elem = ELEMENTS[this.atomicNumber];
        return elem ? elem[4] : 1.0;
    }

    get charge() {
        return this.atomicNumber - this.electronCount;
    }

    get valenceElectrons() {
        if (this.shells.length === 0) return 0;
        return this.shells[this.shells.length - 1].electrons;
    }

    get needsElectrons() {
        if (this.shells.length === 0) return 0;
        const shell = this.shells[this.shells.length - 1];
        return shell.maxElectrons - shell.electrons;
    }

    get isNobleGas() {
        if (this.shells.length === 0) return false;
        return this.shells[this.shells.length - 1].full;
    }

    get isIon() {
        return this.charge !== 0;
    }

    /** Remove outermost electron. */
    ionize() {
        if (this.electronCount > 0) {
            this.electronCount--;
            this._buildShells();
            this._computeIonizationEnergy();
            return true;
        }
        return false;
    }

    /** Capture a free electron. */
    captureElectron() {
        this.electronCount++;
        this._buildShells();
        this._computeIonizationEnergy();
        return true;
    }

    /** Check if bonding is possible. */
    canBondWith(other) {
        if (this.isNobleGas || other.isNobleGas) return false;
        if (this.bonds.length >= 4 || other.bonds.length >= 4) return false;
        return true;
    }

    /** Determine bond type based on electronegativity difference. */
    bondType(other) {
        const diff = Math.abs(this.electronegativity - other.electronegativity);
        if (diff > 1.7) return "ionic";
        if (diff > 0.4) return "polar_covalent";
        return "covalent";
    }

    /** Calculate bond energy. */
    bondEnergy(other) {
        const btype = this.bondType(other);
        if (btype === "ionic") return BOND_ENERGY_IONIC;
        if (btype === "polar_covalent") return (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2;
        return BOND_ENERGY_COVALENT;
    }

    /** Euclidean distance to another atom. */
    distanceTo(other) {
        let sum = 0;
        for (let i = 0; i < 3; i++) {
            sum += (this.position[i] - other.position[i]) ** 2;
        }
        return Math.sqrt(sum);
    }

    toCompact() {
        let chargeStr = "";
        if (this.charge > 0) chargeStr = `+${this.charge}`;
        else if (this.charge < 0) chargeStr = `${this.charge}`;
        const shellsStr = this.shells.map(s => s.electrons).join(".");
        return `${this.symbol}${this.massNumber}${chargeStr}[${shellsStr}]b${this.bonds.length}`;
    }
}

/** Reset atom ID counter (useful for tests). */
export function resetAtomIdCounter() {
    atomIdCounter = 0;
}


// === AtomicSystem ===

export class AtomicSystem {
    /** Collection of atoms with interactions. */
    constructor(temperature = T_RECOMBINATION) {
        this.atoms = [];
        this.temperature = temperature;
        this.freeElectrons = [];
        this.bondsFormed = 0;
        this.bondsBroken = 0;
    }

    /** Capture free electrons into ions when T < T_recombination. */
    recombination(field) {
        if (this.temperature > T_RECOMBINATION) {
            return [];
        }

        const newAtoms = [];
        const protons = field.particles.filter(
            p => p.particleType === ParticleType.PROTON
        );
        const electrons = field.particles.filter(
            p => p.particleType === ParticleType.ELECTRON
        );

        for (const proton of protons) {
            if (electrons.length === 0) break;
            const electron = electrons.pop();

            const atom = new Atom({
                atomicNumber: 1,
                massNumber: 1,
                position: [...proton.position],
                velocity: [...proton.momentum],
            });
            newAtoms.push(atom);
            this.atoms.push(atom);

            let idx = field.particles.indexOf(proton);
            if (idx !== -1) field.particles.splice(idx, 1);
            idx = field.particles.indexOf(electron);
            if (idx !== -1) field.particles.splice(idx, 1);
        }

        return newAtoms;
    }

    /**
     * Form heavier elements through nuclear fusion.
     * Simplified: combines protons and neutrons into nuclei.
     */
    nucleosynthesis(protons = 0, neutrons = 0) {
        const newAtoms = [];

        // Helium-4: 2 protons + 2 neutrons
        while (protons >= 2 && neutrons >= 2) {
            const he = new Atom({
                atomicNumber: 2,
                massNumber: 4,
                position: [gaussRandom(0, 10), gaussRandom(0, 10), gaussRandom(0, 10)],
            });
            newAtoms.push(he);
            this.atoms.push(he);
            protons -= 2;
            neutrons -= 2;
        }

        // Remaining protons become hydrogen
        for (let i = 0; i < protons; i++) {
            const h = new Atom({
                atomicNumber: 1,
                massNumber: 1,
                position: [gaussRandom(0, 10), gaussRandom(0, 10), gaussRandom(0, 10)],
            });
            newAtoms.push(h);
            this.atoms.push(h);
        }

        return newAtoms;
    }

    /**
     * Form heavier elements in stellar cores.
     * Carbon (6), Nitrogen (7), Oxygen (8), and up to Iron (26).
     */
    stellarNucleosynthesis(temperature) {
        const newAtoms = [];

        if (temperature < 1e3) return newAtoms;

        let heliums = this.atoms.filter(a => a.atomicNumber === 2);

        // Triple-alpha process: 3 He -> C
        while (heliums.length >= 3 && Math.random() < 0.01) {
            for (let i = 0; i < 3; i++) {
                const he = heliums.pop();
                const idx = this.atoms.indexOf(he);
                if (idx !== -1) this.atoms.splice(idx, 1);
            }

            const carbon = new Atom({
                atomicNumber: 6,
                massNumber: 12,
                position: [gaussRandom(0, 5), gaussRandom(0, 5), gaussRandom(0, 5)],
            });
            newAtoms.push(carbon);
            this.atoms.push(carbon);
        }

        // C + He -> O
        let carbons = this.atoms.filter(a => a.atomicNumber === 6);
        heliums = this.atoms.filter(a => a.atomicNumber === 2);
        while (carbons.length > 0 && heliums.length > 0 && Math.random() < 0.02) {
            const c = carbons.pop();
            const he = heliums.pop();
            let idx = this.atoms.indexOf(c);
            if (idx !== -1) this.atoms.splice(idx, 1);
            idx = this.atoms.indexOf(he);
            if (idx !== -1) this.atoms.splice(idx, 1);

            const oxygen = new Atom({
                atomicNumber: 8,
                massNumber: 16,
                position: [...c.position],
            });
            newAtoms.push(oxygen);
            this.atoms.push(oxygen);
        }

        // O + He -> N (simplified chain for variety)
        const oxygens = this.atoms.filter(a => a.atomicNumber === 8);
        heliums = this.atoms.filter(a => a.atomicNumber === 2);
        if (oxygens.length > 0 && heliums.length > 0 && Math.random() < 0.005) {
            const o = oxygens[0];
            const he = heliums[0];
            let idx = this.atoms.indexOf(o);
            if (idx !== -1) this.atoms.splice(idx, 1);
            idx = this.atoms.indexOf(he);
            if (idx !== -1) this.atoms.splice(idx, 1);

            const nitrogen = new Atom({
                atomicNumber: 7,
                massNumber: 14,
                position: [...o.position],
            });
            newAtoms.push(nitrogen);
            this.atoms.push(nitrogen);
        }

        return newAtoms;
    }

    /** Try to form a chemical bond between two atoms. */
    attemptBond(a1, a2) {
        if (!a1.canBondWith(a2)) return false;

        const dist = a1.distanceTo(a2);
        const bondDist = 2.0;

        if (dist > bondDist * 3) return false;

        const energyBarrier = a1.bondEnergy(a2);
        const thermalEnergy = K_B * this.temperature;
        let prob;
        if (thermalEnergy > 0) {
            prob = Math.exp(-energyBarrier / thermalEnergy);
        } else {
            prob = dist < bondDist ? 1.0 : 0.0;
        }

        if (Math.random() < prob) {
            a1.bonds.push(a2.atomId);
            a2.bonds.push(a1.atomId);
            this.bondsFormed++;
            return true;
        }
        return false;
    }

    /** Break a bond due to thermal energy. */
    breakBond(a1, a2) {
        if (!a1.bonds.includes(a2.atomId)) return false;

        const energyBarrier = a1.bondEnergy(a2);
        const thermalEnergy = K_B * this.temperature;

        if (thermalEnergy > energyBarrier * 0.5) {
            const prob = Math.exp(-energyBarrier / (thermalEnergy + 1e-20));
            if (Math.random() < prob) {
                a1.bonds = a1.bonds.filter(id => id !== a2.atomId);
                a2.bonds = a2.bonds.filter(id => id !== a1.atomId);
                this.bondsBroken++;
                return true;
            }
        }
        return false;
    }

    /** Cool the atomic system. */
    cool(factor = 0.999) {
        this.temperature *= factor;
    }

    /** Count atoms by element. */
    elementCounts() {
        const counts = {};
        for (const a of this.atoms) {
            const sym = a.symbol;
            counts[sym] = (counts[sym] || 0) + 1;
        }
        return counts;
    }

    toCompact() {
        const counts = this.elementCounts();
        const countStr = Object.entries(counts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([k, v]) => `${k}:${v}`)
            .join(",");
        return (
            `AS[T=${this.temperature.toExponential(1)} n=${this.atoms.length} `
            + `bonds=${this.bondsFormed} ${countStr}]`
        );
    }
}
