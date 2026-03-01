/**
 * Chemistry simulation - molecular assembly and reactions.
 *
 * Models formation of molecules from atoms: water, amino acids,
 * nucleotides, and other biomolecules essential for life.
 * Chemical reactions are driven by energy, catalysis, and concentration.
 */

import {
    K_B, BOND_ENERGY_COVALENT, BOND_ENERGY_HYDROGEN,
    BOND_ENERGY_VAN_DER_WAALS, AMINO_ACIDS,
} from './constants.js';

import { Atom, AtomicSystem } from './atomic.js';


// === Molecule ===

let moleculeIdCounter = 0;

export class Molecule {
    /** A molecule: a collection of bonded atoms. */
    constructor({
        atoms = [],
        name = "",
        formula = "",
        energy = 0.0,
        position = [0.0, 0.0, 0.0],
        isOrganic = false,
        functionalGroups = [],
    } = {}) {
        this.atoms = atoms;
        this.name = name;
        this.formula = formula;
        this.energy = energy;
        this.position = [...position];
        this.isOrganic = isOrganic;
        this.functionalGroups = [...functionalGroups];

        moleculeIdCounter++;
        this.moleculeId = moleculeIdCounter;

        if (!this.formula && this.atoms.length > 0) {
            this._computeFormula();
        }
    }

    _computeFormula() {
        const counts = {};
        for (const atom of this.atoms) {
            const sym = atom.symbol;
            counts[sym] = (counts[sym] || 0) + 1;
        }

        // Standard chemistry ordering: C, H, then alphabetical
        const parts = [];
        for (const sym of ["C", "H"]) {
            if (sym in counts) {
                const n = counts[sym];
                delete counts[sym];
                parts.push(n > 1 ? `${sym}${n}` : sym);
            }
        }
        for (const sym of Object.keys(counts).sort()) {
            const n = counts[sym];
            parts.push(n > 1 ? `${sym}${n}` : sym);
        }
        this.formula = parts.join("");

        // Check if organic
        const hasC = this.atoms.some(a => a.atomicNumber === 6);
        const hasH = this.atoms.some(a => a.atomicNumber === 1);
        this.isOrganic = hasC && hasH;
    }

    get molecularWeight() {
        return this.atoms.reduce((sum, a) => sum + a.massNumber, 0);
    }

    get atomCount() {
        return this.atoms.length;
    }

    toCompact() {
        return `${this.name || this.formula}(mw=${this.molecularWeight})`;
    }
}

/** Reset molecule ID counter (useful for tests). */
export function resetMoleculeIdCounter() {
    moleculeIdCounter = 0;
}


// === ChemicalReaction ===

export class ChemicalReaction {
    /** A chemical reaction with reactants, products, and energy. */
    constructor(reactants, products, activationEnergy = 1.0, deltaH = 0.0, name = "") {
        this.reactants = reactants;
        this.products = products;
        this.activationEnergy = activationEnergy;
        this.deltaH = deltaH;  // Negative = exothermic
        this.name = name;
    }

    /** Check if reaction can proceed at given temperature. */
    canProceed(temperature) {
        const thermalEnergy = K_B * temperature;
        if (thermalEnergy <= 0) return false;
        const rate = Math.exp(-this.activationEnergy / thermalEnergy);
        return Math.random() < rate;
    }

    toCompact() {
        const r = this.reactants.join("+");
        const p = this.products.join("+");
        return `${r}->${p}(Ea=${this.activationEnergy.toFixed(1)},dH=${this.deltaH.toFixed(1)})`;
    }
}


// === ChemicalSystem ===

export class ChemicalSystem {
    /** Manages molecular assembly and chemical reactions. */
    constructor(atomicSystem) {
        this.atomic = atomicSystem;
        this.molecules = [];
        this.reactionsOccurred = 0;
        this.waterCount = 0;
        this.aminoAcidCount = 0;
        this.nucleotideCount = 0;
    }

    /** Form water molecules: 2H + O -> H2O */
    formWater() {
        const waters = [];
        const hydrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 1 && a.bonds.length === 0
        );
        const oxygens = this.atomic.atoms.filter(
            a => a.atomicNumber === 8 && a.bonds.length < 2
        );

        while (hydrogens.length >= 2 && oxygens.length > 0) {
            const h1 = hydrogens.pop();
            const h2 = hydrogens.pop();
            const o = oxygens.pop();

            const water = new Molecule({
                atoms: [h1, h2, o],
                name: "water",
                position: [...o.position],
            });
            waters.push(water);
            this.molecules.push(water);
            this.waterCount++;

            // Form bonds
            h1.bonds.push(o.atomId);
            h2.bonds.push(o.atomId);
            o.bonds.push(h1.atomId, h2.atomId);
        }

        return waters;
    }

    /** Form methane: C + 4H -> CH4 */
    formMethane() {
        const methanes = [];
        const carbons = this.atomic.atoms.filter(
            a => a.atomicNumber === 6 && a.bonds.length === 0
        );
        const hydrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 1 && a.bonds.length === 0
        );

        while (carbons.length > 0 && hydrogens.length >= 4) {
            const c = carbons.pop();
            const hs = [];
            for (let i = 0; i < 4; i++) hs.push(hydrogens.pop());

            const methane = new Molecule({
                atoms: [c, ...hs],
                name: "methane",
                position: [...c.position],
            });
            methanes.push(methane);
            this.molecules.push(methane);

            for (const h of hs) {
                c.bonds.push(h.atomId);
                h.bonds.push(c.atomId);
            }
        }

        return methanes;
    }

    /** Form ammonia: N + 3H -> NH3 */
    formAmmonia() {
        const ammonias = [];
        const nitrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 7 && a.bonds.length === 0
        );
        const hydrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 1 && a.bonds.length === 0
        );

        while (nitrogens.length > 0 && hydrogens.length >= 3) {
            const n = nitrogens.pop();
            const hs = [];
            for (let i = 0; i < 3; i++) hs.push(hydrogens.pop());

            const ammonia = new Molecule({
                atoms: [n, ...hs],
                name: "ammonia",
                position: [...n.position],
            });
            ammonias.push(ammonia);
            this.molecules.push(ammonia);

            for (const h of hs) {
                n.bonds.push(h.atomId);
                h.bonds.push(n.atomId);
            }
        }

        return ammonias;
    }

    /**
     * Form an amino acid from available atoms.
     * Amino acids need: C, H, O, N (and sometimes S).
     * Simplified: requires 2C + 5H + 2O + 1N minimum (glycine).
     */
    formAminoAcid(aaType = "Gly") {
        const carbons = this.atomic.atoms.filter(
            a => a.atomicNumber === 6 && a.bonds.length === 0
        );
        const hydrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 1 && a.bonds.length === 0
        );
        const oxygens = this.atomic.atoms.filter(
            a => a.atomicNumber === 8 && a.bonds.length < 2
        );
        const nitrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 7 && a.bonds.length === 0
        );

        if (carbons.length < 2 || hydrogens.length < 5) return null;
        if (oxygens.length < 2 || nitrogens.length < 1) return null;

        const atoms = [];
        for (let i = 0; i < 2; i++) atoms.push(carbons.pop());
        for (let i = 0; i < 5; i++) atoms.push(hydrogens.pop());
        for (let i = 0; i < 2; i++) atoms.push(oxygens.pop());
        atoms.push(nitrogens.pop());

        const aa = new Molecule({
            atoms: atoms,
            name: aaType,
            position: [...atoms[0].position],
            isOrganic: true,
            functionalGroups: ["amino", "carboxyl"],
        });
        this.molecules.push(aa);
        this.aminoAcidCount++;

        // Form internal bonds
        for (let i = 1; i < atoms.length; i++) {
            atoms[0].bonds.push(atoms[i].atomId);
            atoms[i].bonds.push(atoms[0].atomId);
        }

        return aa;
    }

    /**
     * Form a nucleotide (sugar + phosphate + base).
     * Simplified: requires C5 + H10 + O7 + N2 + P minimum.
     * We use available atoms to approximate.
     */
    formNucleotide(base = "A") {
        const carbons = this.atomic.atoms.filter(
            a => a.atomicNumber === 6 && a.bonds.length === 0
        );
        const hydrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 1 && a.bonds.length === 0
        );
        const oxygens = this.atomic.atoms.filter(
            a => a.atomicNumber === 8 && a.bonds.length < 2
        );
        const nitrogens = this.atomic.atoms.filter(
            a => a.atomicNumber === 7 && a.bonds.length === 0
        );

        // Simplified requirements
        if (carbons.length < 5 || hydrogens.length < 8) return null;
        if (oxygens.length < 4 || nitrogens.length < 2) return null;

        const atoms = [];
        for (let i = 0; i < 5; i++) atoms.push(carbons.pop());
        for (let i = 0; i < 8; i++) atoms.push(hydrogens.pop());
        for (let i = 0; i < 4; i++) atoms.push(oxygens.pop());
        for (let i = 0; i < 2; i++) atoms.push(nitrogens.pop());

        const nuc = new Molecule({
            atoms: atoms,
            name: `nucleotide-${base}`,
            position: [...atoms[0].position],
            isOrganic: true,
            functionalGroups: ["sugar", "phosphate", "base"],
        });
        this.molecules.push(nuc);
        this.nucleotideCount++;

        for (let i = 1; i < atoms.length; i++) {
            atoms[0].bonds.push(atoms[i].atomId);
            atoms[i].bonds.push(atoms[0].atomId);
        }

        return nuc;
    }

    /** Run catalyzed reactions to form complex molecules. */
    catalyzedReaction(temperature, catalystPresent = false) {
        let formed = 0;
        const eaFactor = catalystPresent ? 0.3 : 1.0;
        const thermal = K_B * temperature;

        // Try to form amino acids
        if (thermal > 0 && this.atomic.atoms.length > 10) {
            const aaProb = Math.exp(-5.0 * eaFactor / (thermal + 1e-20));
            if (Math.random() < aaProb) {
                const aaType = AMINO_ACIDS[Math.floor(Math.random() * AMINO_ACIDS.length)];
                if (this.formAminoAcid(aaType)) {
                    formed++;
                    this.reactionsOccurred++;
                }
            }
        }

        // Try to form nucleotides
        if (thermal > 0 && this.atomic.atoms.length > 19) {
            const nucProb = Math.exp(-8.0 * eaFactor / (thermal + 1e-20));
            if (Math.random() < nucProb) {
                const bases = ["A", "T", "G", "C"];
                const base = bases[Math.floor(Math.random() * bases.length)];
                if (this.formNucleotide(base)) {
                    formed++;
                    this.reactionsOccurred++;
                }
            }
        }

        return formed;
    }

    /** Count molecules by type. */
    moleculeCensus() {
        const counts = {};
        for (const m of this.molecules) {
            const key = m.name || m.formula;
            counts[key] = (counts[key] || 0) + 1;
        }
        return counts;
    }

    toCompact() {
        const counts = this.moleculeCensus();
        const countStr = Object.entries(counts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([k, v]) => `${k}:${v}`)
            .join(",");
        return (
            `CS[mol=${this.molecules.length} `
            + `H2O=${this.waterCount} `
            + `aa=${this.aminoAcidCount} `
            + `nuc=${this.nucleotideCount} `
            + `rxn=${this.reactionsOccurred} ${countStr}]`
        );
    }
}
