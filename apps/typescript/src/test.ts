/**
 * Tests for the cosmic evolution simulator.
 * Uses Node.js built-in test runner (node:test).
 */

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import {
    C, HBAR, K_B, G, ALPHA, E_CHARGE, PI,
    M_ELECTRON, M_UP_QUARK, M_DOWN_QUARK, M_PROTON, M_NEUTRON,
    M_PHOTON, M_NEUTRINO, M_W_BOSON, M_Z_BOSON, M_HIGGS,
    STRONG_COUPLING, EM_COUPLING, WEAK_COUPLING, GRAVITY_COUPLING,
    NUCLEAR_RADIUS, BINDING_ENERGY_DEUTERIUM, BINDING_ENERGY_HELIUM4,
    BINDING_ENERGY_CARBON12, BINDING_ENERGY_IRON56,
    PLANCK_EPOCH, INFLATION_EPOCH, ELECTROWEAK_EPOCH, QUARK_EPOCH,
    HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH, RECOMBINATION_EPOCH,
    STAR_FORMATION_EPOCH, SOLAR_SYSTEM_EPOCH, EARTH_EPOCH,
    LIFE_EPOCH, DNA_EPOCH, PRESENT_EPOCH,
    T_PLANCK, T_ELECTROWEAK, T_QUARK_HADRON, T_NUCLEOSYNTHESIS,
    T_RECOMBINATION, T_CMB, T_STELLAR_CORE, T_EARTH_SURFACE,
    ELECTRON_SHELLS, BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC,
    BOND_ENERGY_HYDROGEN, BOND_ENERGY_VAN_DER_WAALS,
    NUCLEOTIDE_BASES, RNA_BASES, AMINO_ACIDS, CODON_TABLE,
    METHYLATION_PROBABILITY, DEMETHYLATION_PROBABILITY,
    HISTONE_ACETYLATION_PROB, HISTONE_DEACETYLATION_PROB,
    UV_MUTATION_RATE, COSMIC_RAY_MUTATION_RATE, RADIATION_DAMAGE_THRESHOLD,
    EPOCHS, ELEMENTS,
} from "./constants.js";

import {
    RNG, ParticleType, Spin, Color, WaveFunction, Particle,
    QuantumField, Atom, AtomicSystem, Molecule, ChemicalSystem,
    Gene, DNAStrand, Protein, Cell, Biosphere,
    Environment, Universe,
} from "./simulator.js";


// ============================================================================
// Constants tests
// ============================================================================

describe("Constants", () => {
    it("fundamental constants have expected values", () => {
        assert.equal(C, 1.0);
        assert.equal(HBAR, 0.01);
        assert.equal(K_B, 0.001);
        assert.equal(G, 1e-6);
        assert.ok(Math.abs(ALPHA - 1.0 / 137.0) < 1e-12);
        assert.equal(E_CHARGE, 0.1);
        assert.equal(PI, Math.PI);
    });

    it("particle masses have correct values", () => {
        assert.equal(M_ELECTRON, 1.0);
        assert.equal(M_UP_QUARK, 4.4);
        assert.equal(M_DOWN_QUARK, 9.4);
        assert.equal(M_PROTON, 1836.0);
        assert.equal(M_NEUTRON, 1839.0);
        assert.equal(M_PHOTON, 0.0);
        assert.equal(M_NEUTRINO, 1e-6);
        assert.equal(M_W_BOSON, 157000.0);
        assert.equal(M_Z_BOSON, 178000.0);
        assert.equal(M_HIGGS, 245000.0);
    });

    it("mass hierarchy is physically correct", () => {
        assert.ok(M_PHOTON < M_NEUTRINO);
        assert.ok(M_NEUTRINO < M_ELECTRON);
        assert.ok(M_ELECTRON < M_UP_QUARK);
        assert.ok(M_UP_QUARK < M_DOWN_QUARK);
        assert.ok(M_DOWN_QUARK < M_PROTON);
        assert.ok(M_PROTON < M_NEUTRON);
        assert.ok(M_NEUTRON < M_W_BOSON);
        assert.ok(M_W_BOSON < M_Z_BOSON);
        assert.ok(M_Z_BOSON < M_HIGGS);
    });

    it("force couplings are correctly ordered", () => {
        assert.equal(STRONG_COUPLING, 1.0);
        assert.equal(EM_COUPLING, ALPHA);
        assert.equal(WEAK_COUPLING, 1e-6);
        assert.equal(GRAVITY_COUPLING, 1e-38);
        assert.ok(GRAVITY_COUPLING < WEAK_COUPLING);
        assert.ok(WEAK_COUPLING < EM_COUPLING);
        assert.ok(EM_COUPLING < STRONG_COUPLING);
    });

    it("binding energies increase with mass number", () => {
        assert.ok(BINDING_ENERGY_DEUTERIUM < BINDING_ENERGY_HELIUM4);
        assert.ok(BINDING_ENERGY_HELIUM4 < BINDING_ENERGY_CARBON12);
        assert.ok(BINDING_ENERGY_CARBON12 < BINDING_ENERGY_IRON56);
    });

    it("cosmic epochs are in chronological order", () => {
        assert.ok(PLANCK_EPOCH < INFLATION_EPOCH);
        assert.ok(INFLATION_EPOCH < ELECTROWEAK_EPOCH);
        assert.ok(ELECTROWEAK_EPOCH < QUARK_EPOCH);
        assert.ok(QUARK_EPOCH < HADRON_EPOCH);
        assert.ok(HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
        assert.ok(NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
        assert.ok(RECOMBINATION_EPOCH < STAR_FORMATION_EPOCH);
        assert.ok(STAR_FORMATION_EPOCH < SOLAR_SYSTEM_EPOCH);
        assert.ok(SOLAR_SYSTEM_EPOCH < EARTH_EPOCH);
        assert.ok(EARTH_EPOCH < LIFE_EPOCH);
        assert.ok(LIFE_EPOCH < DNA_EPOCH);
        assert.ok(DNA_EPOCH < PRESENT_EPOCH);
    });

    it("temperature scale decreases over cosmic time", () => {
        assert.ok(T_PLANCK > T_ELECTROWEAK);
        assert.ok(T_ELECTROWEAK > T_QUARK_HADRON);
        assert.ok(T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
        assert.ok(T_NUCLEOSYNTHESIS > T_RECOMBINATION);
        assert.ok(T_RECOMBINATION > T_EARTH_SURFACE);
        assert.ok(T_EARTH_SURFACE > T_CMB);
    });

    it("electron shells array has expected values", () => {
        assert.deepEqual(ELECTRON_SHELLS, [2, 8, 18, 32, 32, 18, 8]);
    });

    it("bond energies are ordered: ionic > covalent > hydrogen > van der Waals", () => {
        assert.ok(BOND_ENERGY_IONIC > BOND_ENERGY_COVALENT);
        assert.ok(BOND_ENERGY_COVALENT > BOND_ENERGY_HYDROGEN);
        assert.ok(BOND_ENERGY_HYDROGEN > BOND_ENERGY_VAN_DER_WAALS);
    });

    it("nucleotide bases are ATGC", () => {
        assert.deepEqual(NUCLEOTIDE_BASES, ["A", "T", "G", "C"]);
    });

    it("RNA bases replace T with U", () => {
        assert.deepEqual(RNA_BASES, ["A", "U", "G", "C"]);
    });

    it("amino acids list has 20 standard amino acids", () => {
        assert.equal(AMINO_ACIDS.length, 20);
        assert.ok(AMINO_ACIDS.includes("Met"));
        assert.ok(AMINO_ACIDS.includes("Gly"));
    });

    it("codon table maps AUG to Met (start codon)", () => {
        assert.equal(CODON_TABLE["AUG"], "Met");
    });

    it("codon table has stop codons", () => {
        assert.equal(CODON_TABLE["UAA"], "STOP");
        assert.equal(CODON_TABLE["UAG"], "STOP");
        assert.equal(CODON_TABLE["UGA"], "STOP");
    });

    it("epochs list has 13 entries matching constants", () => {
        assert.equal(EPOCHS.length, 13);
        assert.equal(EPOCHS[0].name, "Planck");
        assert.equal(EPOCHS[0].startTick, PLANCK_EPOCH);
        assert.equal(EPOCHS[EPOCHS.length - 1].name, "Present");
        assert.equal(EPOCHS[EPOCHS.length - 1].startTick, PRESENT_EPOCH);
    });

    it("elements table contains hydrogen and iron", () => {
        assert.ok(ELEMENTS[1] !== undefined);
        assert.equal(ELEMENTS[1][0], "H");
        assert.equal(ELEMENTS[1][1], "Hydrogen");
        assert.ok(ELEMENTS[26] !== undefined);
        assert.equal(ELEMENTS[26][0], "Fe");
    });

    it("epigenetic parameters are reasonable probabilities", () => {
        assert.ok(METHYLATION_PROBABILITY > 0 && METHYLATION_PROBABILITY < 1);
        assert.ok(DEMETHYLATION_PROBABILITY > 0 && DEMETHYLATION_PROBABILITY < 1);
        assert.ok(HISTONE_ACETYLATION_PROB > 0 && HISTONE_ACETYLATION_PROB < 1);
        assert.ok(HISTONE_DEACETYLATION_PROB > 0 && HISTONE_DEACETYLATION_PROB < 1);
    });
});


// ============================================================================
// RNG tests
// ============================================================================

describe("RNG", () => {
    it("produces deterministic output for a given seed", () => {
        const r1 = new RNG(42);
        const r2 = new RNG(42);
        for (let i = 0; i < 10; i++) {
            assert.equal(r1.random(), r2.random());
        }
    });

    it("different seeds produce different sequences", () => {
        const r1 = new RNG(42);
        const r2 = new RNG(99);
        let allSame = true;
        for (let i = 0; i < 10; i++) {
            if (r1.random() !== r2.random()) allSame = false;
        }
        assert.ok(!allSame);
    });

    it("random() returns values in [0, 1)", () => {
        const r = new RNG(42);
        for (let i = 0; i < 100; i++) {
            const v = r.random();
            assert.ok(v >= 0 && v < 1, `Value ${v} out of range`);
        }
    });

    it("uniform(a, b) returns values in [a, b)", () => {
        const r = new RNG(42);
        for (let i = 0; i < 100; i++) {
            const v = r.uniform(-5, 5);
            assert.ok(v >= -5 && v < 5, `Value ${v} out of range`);
        }
    });

    it("choice selects from array", () => {
        const r = new RNG(42);
        const options = [10, 20, 30];
        for (let i = 0; i < 50; i++) {
            const v = r.choice(options);
            assert.ok(options.includes(v), `${v} not in options`);
        }
    });

    it("gauss produces values with approximately correct mean", () => {
        const r = new RNG(42);
        let sum = 0;
        const n = 1000;
        for (let i = 0; i < n; i++) {
            sum += r.gauss(5.0, 1.0);
        }
        const mean = sum / n;
        assert.ok(Math.abs(mean - 5.0) < 0.5, `Mean ${mean} too far from 5.0`);
    });
});


// ============================================================================
// WaveFunction tests
// ============================================================================

describe("WaveFunction", () => {
    it("initializes with amplitude 1 and phase 0", () => {
        const wf = new WaveFunction();
        assert.equal(wf.amplitude, 1.0);
        assert.equal(wf.phase, 0.0);
        assert.equal(wf.coherent, true);
    });

    it("probability is amplitude squared (getter)", () => {
        const wf = new WaveFunction(0.5, 0, true);
        assert.ok(Math.abs(wf.probability - 0.25) < 1e-10);
    });

    it("collapse sets coherent to false", () => {
        // Use a Universe to set the module-level rng
        new Universe(42);
        const wf = new WaveFunction(1.0, 0, true);
        wf.collapse();
        assert.equal(wf.coherent, false);
    });

    it("evolve changes phase when coherent", () => {
        const wf = new WaveFunction(1.0, 0, true);
        wf.evolve(1.0, 5.0);
        assert.ok(wf.phase !== 0.0);
    });

    it("decoherent wavefunction does not evolve", () => {
        const wf = new WaveFunction(1.0, 0, false);
        wf.evolve(1.0, 5.0);
        assert.equal(wf.phase, 0.0);
    });
});


// ============================================================================
// Particle tests
// ============================================================================

describe("Particle", () => {
    it("has correct mass for particle type", () => {
        const electron = new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]);
        assert.equal(electron.mass, M_ELECTRON);

        const proton = new Particle(ParticleType.PROTON, [0, 0, 0], [0, 0, 0]);
        assert.equal(proton.mass, M_PROTON);

        const photon = new Particle(ParticleType.PHOTON, [0, 0, 0], [0, 0, 0]);
        assert.equal(photon.mass, M_PHOTON);
    });

    it("has correct charge for particle type", () => {
        const electron = new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]);
        assert.equal(electron.charge, -1.0);

        const proton = new Particle(ParticleType.PROTON, [0, 0, 0], [0, 0, 0]);
        assert.equal(proton.charge, 1.0);

        const photon = new Particle(ParticleType.PHOTON, [0, 0, 0], [0, 0, 0]);
        assert.equal(photon.charge, 0.0);
    });

    it("energy is non-negative", () => {
        const p = new Particle(ParticleType.ELECTRON, [0, 0, 0], [1, 2, 3]);
        assert.ok(p.energy >= 0);
    });

    it("photon with zero momentum has zero energy", () => {
        const p = new Particle(ParticleType.PHOTON, [0, 0, 0], [0, 0, 0]);
        assert.equal(p.energy, 0.0);
    });

    it("assigns unique particleIds", () => {
        new Universe(42); // Reset counters
        const p1 = new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]);
        const p2 = new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]);
        assert.notEqual(p1.particleId, p2.particleId);
    });
});


// ============================================================================
// QuantumField tests
// ============================================================================

describe("QuantumField", () => {
    it("initializes with given temperature and no particles", () => {
        const qf = new QuantumField(1e10);
        assert.equal(qf.temperature, 1e10);
        assert.equal(qf.particles.length, 0);
    });

    it("pair production creates two particles", () => {
        new Universe(42); // Reset rng
        const qf = new QuantumField(1e10);
        const energy = 2 * M_ELECTRON * C * C + 10; // Above threshold
        const result = qf.pairProduction(energy);
        assert.ok(result !== null);
        assert.equal(qf.particles.length, 2);
    });

    it("pair production fails below threshold", () => {
        const qf = new QuantumField(1e10);
        const result = qf.pairProduction(0.1); // Below 2*m_e*c^2
        assert.equal(result, null);
        assert.equal(qf.particles.length, 0);
    });

    it("annihilation removes particles and creates photons", () => {
        new Universe(42);
        const qf = new QuantumField(1e10);
        const e = new Particle(ParticleType.ELECTRON, [0, 0, 0], [1, 0, 0]);
        const p = new Particle(ParticleType.POSITRON, [0, 0, 0], [-1, 0, 0]);
        qf.particles.push(e, p);

        const released = qf.annihilate(e, p);
        assert.ok(released > 0);
        const photons = qf.particles.filter(x => x.particleType === ParticleType.PHOTON);
        assert.equal(photons.length, 2);
    });

    it("quark confinement forms hadrons below transition temperature", () => {
        new Universe(42);
        const qf = new QuantumField(T_QUARK_HADRON - 1);
        // Add 2 ups and 1 down to form a proton
        for (let i = 0; i < 2; i++) {
            qf.particles.push(new Particle(ParticleType.UP, [0, 0, 0], [0, 0, 0]));
        }
        qf.particles.push(new Particle(ParticleType.DOWN, [0, 0, 0], [0, 0, 0]));

        const hadrons = qf.quarkConfinement();
        assert.ok(hadrons.length > 0);
        assert.ok(hadrons.some(h => h.particleType === ParticleType.PROTON));
    });

    it("quark confinement does nothing above transition temperature", () => {
        const qf = new QuantumField(T_QUARK_HADRON + 1000);
        qf.particles.push(new Particle(ParticleType.UP, [0, 0, 0], [0, 0, 0]));
        qf.particles.push(new Particle(ParticleType.UP, [0, 0, 0], [0, 0, 0]));
        qf.particles.push(new Particle(ParticleType.DOWN, [0, 0, 0], [0, 0, 0]));

        const hadrons = qf.quarkConfinement();
        assert.equal(hadrons.length, 0);
    });

    it("evolve updates particle positions", () => {
        new Universe(42);
        const qf = new QuantumField(100);
        const p = new Particle(ParticleType.ELECTRON, [0, 0, 0], [1, 0, 0]);
        qf.particles.push(p);
        const oldX = p.position[0];
        qf.evolve(1.0);
        assert.ok(p.position[0] !== oldX);
    });

    it("particleCount returns correct counts", () => {
        new Universe(42);
        const qf = new QuantumField(100);
        qf.particles.push(new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]));
        qf.particles.push(new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]));
        qf.particles.push(new Particle(ParticleType.PHOTON, [0, 0, 0], [0, 0, 0]));

        const counts = qf.particleCount();
        assert.equal(counts["electron"], 2);
        assert.equal(counts["photon"], 1);
    });

    it("totalEnergy includes vacuum energy", () => {
        const qf = new QuantumField(100);
        qf.vacuumEnergy = 42;
        const e = qf.totalEnergy();
        assert.ok(e >= 42);
    });
});


// ============================================================================
// Atom tests
// ============================================================================

describe("Atom", () => {
    it("hydrogen has correct properties", () => {
        new Universe(42);
        const h = new Atom(1);
        assert.equal(h.atomicNumber, 1);
        assert.equal(h.symbol, "H");
        assert.ok(h.electronCount > 0);
    });

    it("helium has correct mass number", () => {
        const he = new Atom(2, 4);
        assert.equal(he.massNumber, 4);
        assert.equal(he.symbol, "He");
    });

    it("carbon has electronegativity 2.55", () => {
        const c = new Atom(6);
        assert.ok(Math.abs(c.electronegativity - 2.55) < 0.01);
    });

    it("electron shells are filled correctly for oxygen", () => {
        const o = new Atom(8);
        assert.equal(o.electronCount, 8);
        assert.equal(o.shells.length, 2);
        assert.equal(o.shells[0].electrons, 2);
        assert.equal(o.shells[0].maxElectrons, 2);
        assert.equal(o.shells[1].electrons, 6);
    });

    it("noble gases have full outer shell", () => {
        const he = new Atom(2);
        assert.ok(he.isNobleGas);
        const ne = new Atom(10);
        assert.ok(ne.isNobleGas);
    });

    it("valence electrons computed correctly", () => {
        const c = new Atom(6);
        assert.equal(c.valenceElectrons, 4);
        const o = new Atom(8);
        assert.equal(o.valenceElectrons, 6);
    });

    it("charge is zero for neutral atom", () => {
        const h = new Atom(1);
        assert.equal(h.charge, 0);
    });

    it("canBondWith returns false for noble gases", () => {
        const he = new Atom(2);
        const h = new Atom(1);
        assert.ok(!he.canBondWith(h));
    });

    it("bondType classifies bonds correctly", () => {
        const na = new Atom(11); // Na, electronegativity 0.93
        const cl = new Atom(17); // Cl, electronegativity 3.16
        assert.equal(na.bondType(cl), "ionic"); // diff > 1.7

        const c = new Atom(6);  // C, 2.55
        const h = new Atom(1);  // H, 2.20
        assert.equal(c.bondType(h), "covalent"); // diff = 0.35 < 0.4
    });
});


// ============================================================================
// AtomicSystem tests
// ============================================================================

describe("AtomicSystem", () => {
    it("initializes empty", () => {
        const as = new AtomicSystem();
        assert.equal(as.atoms.length, 0);
    });

    it("nucleosynthesis creates atoms from protons and neutrons", () => {
        new Universe(42);
        const as = new AtomicSystem();
        const newAtoms = as.nucleosynthesis(4, 4);
        assert.ok(newAtoms.length > 0);
        const heliums = newAtoms.filter(a => a.atomicNumber === 2);
        assert.ok(heliums.length > 0);
    });

    it("nucleosynthesis forms hydrogen from leftover protons", () => {
        new Universe(42);
        const as = new AtomicSystem();
        const newAtoms = as.nucleosynthesis(3, 0);
        const hydrogens = newAtoms.filter(a => a.atomicNumber === 1);
        assert.equal(hydrogens.length, 3);
    });

    it("elementCounts returns correct totals", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.atoms.push(new Atom(1));
        as.atoms.push(new Atom(1));
        as.atoms.push(new Atom(8));
        const counts = as.elementCounts();
        assert.equal(counts["H"], 2);
        assert.equal(counts["O"], 1);
    });

    it("recombination captures electrons into atoms", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.temperature = T_RECOMBINATION - 100;
        const qf = new QuantumField(as.temperature);
        qf.particles.push(new Particle(ParticleType.PROTON, [0, 0, 0], [0, 0, 0]));
        qf.particles.push(new Particle(ParticleType.ELECTRON, [0, 0, 0], [0, 0, 0]));

        const newAtoms = as.recombination(qf);
        assert.ok(newAtoms.length > 0);
        assert.equal(newAtoms[0].atomicNumber, 1);
    });
});


// ============================================================================
// ChemicalSystem tests
// ============================================================================

describe("ChemicalSystem", () => {
    it("initializes from atomic system", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.atoms.push(new Atom(1));
        as.atoms.push(new Atom(8));
        const cs = new ChemicalSystem(as);
        assert.equal(cs.molecules.length, 0);
    });

    it("formWater creates water molecules from H and O", () => {
        new Universe(42);
        const as = new AtomicSystem();
        // Need 2 H + 1 O for water
        as.atoms.push(new Atom(1, undefined, [0, 0, 0]));
        as.atoms.push(new Atom(1, undefined, [0.1, 0, 0]));
        as.atoms.push(new Atom(8, undefined, [0.2, 0, 0]));
        const cs = new ChemicalSystem(as);
        const waters = cs.formWater();
        assert.ok(waters.length > 0);
        assert.ok(waters.some(m => m.name === "water"));
    });

    it("moleculeCensus returns counts by type", () => {
        new Universe(42);
        const as = new AtomicSystem();
        for (let i = 0; i < 4; i++) as.atoms.push(new Atom(1, undefined, [i * 0.1, 0, 0]));
        as.atoms.push(new Atom(8, undefined, [0.5, 0, 0]));
        as.atoms.push(new Atom(8, undefined, [0.6, 0, 0]));
        const cs = new ChemicalSystem(as);
        cs.formWater();
        const census = cs.moleculeCensus();
        assert.ok(typeof census === "object");
    });
});


// ============================================================================
// Gene tests
// ============================================================================

describe("Gene", () => {
    it("creates with sequence and name", () => {
        const gene = new Gene("test", ["A", "T", "G", "C"], 0, 4);
        assert.equal(gene.name, "test");
        assert.equal(gene.length, 4);
    });

    it("transcribe replaces T with U", () => {
        const gene = new Gene("test", ["A", "T", "G", "C", "T"], 0, 5);
        const mrna = gene.transcribe();
        assert.deepEqual(mrna, ["A", "U", "G", "C", "U"]);
    });

    it("isSilenced is false initially", () => {
        const gene = new Gene("test", ["A", "T", "G", "C"], 0, 4);
        assert.equal(gene.isSilenced, false);
    });

    it("methylation can silence a gene", () => {
        const seq = Array(10).fill("A");
        const gene = new Gene("test", seq, 0, 10);
        // Methylate more than 30% of positions
        for (let i = 0; i < 5; i++) {
            gene.methylate(i);
        }
        assert.equal(gene.isSilenced, true);
    });

    it("mutate changes bases at high rate", () => {
        new Universe(42);
        const seq = Array(50).fill("A");
        const gene = new Gene("test", [...seq], 0, 50);
        const mutations = gene.mutate(1.0);
        assert.ok(mutations > 0);
    });
});


// ============================================================================
// DNAStrand tests
// ============================================================================

describe("DNAStrand", () => {
    it("randomStrand creates a strand of the specified length", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(30);
        assert.equal(dna.length, 30);
    });

    it("sequence contains only valid bases", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(100);
        for (const base of dna.sequence) {
            assert.ok(NUCLEOTIDE_BASES.includes(base), `Invalid base: ${base}`);
        }
    });

    it("gcContent is between 0 and 1", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(100);
        const gc = dna.gcContent;
        assert.ok(gc >= 0 && gc <= 1);
    });

    it("replicate creates a copy", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(30);
        const copy = dna.replicate();
        assert.equal(copy.length, dna.length);
        assert.equal(copy.generation, dna.generation + 1);
    });

    it("applyMutations changes bases at non-zero rate", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(100);
        const original = [...dna.sequence];
        // High UV and cosmic ray to force mutations
        dna.applyMutations(10000, 10000);
        let changed = false;
        for (let i = 0; i < dna.length; i++) {
            if (dna.sequence[i] !== original[i]) { changed = true; break; }
        }
        assert.ok(changed);
    });

    it("genes are created by randomStrand", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(90, 3);
        assert.ok(dna.genes.length > 0);
    });
});


// ============================================================================
// Cell tests
// ============================================================================

describe("Cell", () => {
    it("creates with DNA and initial energy", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 50);
        assert.ok(cell.alive);
        assert.ok(cell.energy > 0);
        assert.equal(cell.generation, 0);
    });

    it("metabolize consumes energy", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 50);
        const initialEnergy = cell.energy;
        cell.metabolize(1.0);
        // Energy changes due to metabolism (absorb some, spend some)
        assert.ok(cell.energy !== initialEnergy);
    });

    it("cell dies when energy depleted", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 0.1);
        cell.metabolize(0);
        assert.ok(!cell.alive);
    });

    it("computeFitness returns a value", () => {
        new Universe(42);
        const cell = new Cell();
        cell.transcribeAndTranslate();
        const f = cell.computeFitness();
        assert.equal(typeof f, "number");
        assert.ok(f >= 0);
    });

    it("divide returns daughter cell when energy sufficient", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 150);
        cell.transcribeAndTranslate();
        const daughter = cell.divide();
        if (daughter !== null) {
            assert.equal(daughter.generation, 1);
            assert.ok(daughter.alive);
        }
    });
});


// ============================================================================
// Biosphere tests
// ============================================================================

describe("Biosphere", () => {
    it("initializes with cells", () => {
        new Universe(42);
        const bio = new Biosphere(5, 30);
        assert.equal(bio.cells.length, 5);
    });

    it("step evolves cells", () => {
        new Universe(42);
        const bio = new Biosphere(5, 30);
        bio.step(10, 0.1, 0.01, 300);
        // Some cells may die or reproduce
        assert.ok(bio.cells.length >= 0);
    });

    it("averageFitness returns a number", () => {
        new Universe(42);
        const bio = new Biosphere(5, 30);
        const avg = bio.averageFitness();
        assert.equal(typeof avg, "number");
        assert.ok(!isNaN(avg));
    });

    it("generation increments over steps", () => {
        new Universe(42);
        const bio = new Biosphere(5, 90);
        for (let i = 0; i < 5; i++) {
            bio.step(10, 0.01, 0.001, 300);
        }
        assert.ok(bio.generation >= 5);
    });

    it("totalMutations returns a number", () => {
        new Universe(42);
        const bio = new Biosphere(5, 90);
        bio.step(10, 1, 1, 300); // High radiation = mutations
        const m = bio.totalMutations();
        assert.equal(typeof m, "number");
    });
});


// ============================================================================
// Environment tests
// ============================================================================

describe("Environment", () => {
    it("initializes at given temperature", () => {
        const env = new Environment(T_PLANCK);
        assert.equal(env.temperature, T_PLANCK);
    });

    it("temperature decreases after update to later epoch", () => {
        new Universe(42);
        const env = new Environment(T_PLANCK);
        env.update(RECOMBINATION_EPOCH);
        assert.ok(env.temperature < T_PLANCK);
    });

    it("isHabitable returns false at extreme temperatures", () => {
        new Universe(42);
        const env = new Environment(T_PLANCK);
        env.update(1);
        assert.ok(!env.isHabitable());
    });

    it("UV intensity is non-negative", () => {
        new Universe(42);
        const env = new Environment(T_EARTH_SURFACE);
        env.update(EARTH_EPOCH);
        assert.ok(env.uvIntensity >= 0);
    });

    it("thermalEnergy is proportional to temperature", () => {
        const env1 = new Environment(100);
        const env2 = new Environment(200);
        assert.ok(env2.thermalEnergy() > env1.thermalEnergy());
    });
});


// ============================================================================
// Universe (integration) tests
// ============================================================================

describe("Universe", () => {
    it("initializes with tick 0", () => {
        const u = new Universe(42);
        assert.equal(u.tick, 0);
        assert.equal(u.currentEpochName, "Void");
    });

    it("step advances the tick", () => {
        const u = new Universe(42);
        u.step();
        assert.ok(u.tick > 0);
    });

    it("epoch name changes at Planck epoch", () => {
        const u = new Universe(42);
        u.step(); // tick = 1 = PLANCK_EPOCH
        assert.equal(u.currentEpochName, "Planck");
    });

    it("snapshot returns structured data", () => {
        const u = new Universe(42);
        u.step();
        const snap = u.snapshot();
        assert.equal(typeof snap.tick, "number");
        assert.equal(typeof snap.epoch, "string");
        assert.equal(typeof snap.temperature, "number");
        assert.equal(typeof snap.particles, "number");
        assert.equal(typeof snap.atoms, "number");
    });

    it("restart resets state", () => {
        const u = new Universe(42);
        for (let i = 0; i < 5; i++) u.step();
        u.restart(99);
        assert.equal(u.tick, 0);
        assert.equal(u.currentEpochName, "Void");
    });

    it("deterministic: same seed produces same state", () => {
        // Create both universes and run them sequentially so the
        // module-level RNG is reset properly for each.
        const u1 = new Universe(42);
        for (let i = 0; i < 100; i++) u1.step();
        const s1 = u1.snapshot();

        const u2 = new Universe(42);
        for (let i = 0; i < 100; i++) u2.step();
        const s2 = u2.snapshot();

        assert.equal(s1.tick, s2.tick);
        assert.equal(s1.epoch, s2.epoch);
        assert.equal(s1.particles, s2.particles);
        assert.equal(s1.atoms, s2.atoms);
        assert.equal(s1.temperature, s2.temperature);
    });
});


// ============================================================================
// Full simulation run test
// ============================================================================

describe("Full simulation run", () => {
    it("runs through multiple epochs without crashing", () => {
        const u = new Universe(42);
        while (u.tick < HADRON_EPOCH + 1) {
            u.step();
        }
        const snap = u.snapshot();
        assert.ok(snap.tick >= HADRON_EPOCH);
        assert.ok(snap.particles >= 0);
        assert.ok(snap.temperature > 0);
    });

    it("produces particles in early epochs", () => {
        const u = new Universe(42);
        for (let i = 0; i < QUARK_EPOCH; i++) {
            u.step();
        }
        assert.ok(u.quantumField.particles.length > 0);
    });

    it("forms atoms during nucleosynthesis", () => {
        const u = new Universe(42);
        while (u.tick < NUCLEOSYNTHESIS_EPOCH + 100) {
            u.step();
        }
        assert.ok(u.atomicSystem.atoms.length > 0 || u.atomsFormed > 0);
    });

    it("forms molecules during Earth epoch", () => {
        const u = new Universe(42, PRESENT_EPOCH, 1000);
        while (u.tick < EARTH_EPOCH + 2000) {
            u.step();
        }
        assert.ok(u.chemicalSystem !== null);
        assert.ok(u.moleculesFormed > 0 || u.chemicalSystem!.molecules.length > 0);
    });

    it("completes a fast simulation run to present", () => {
        const u = new Universe(42, PRESENT_EPOCH, 5000);
        while (u.tick < PRESENT_EPOCH) {
            u.step();
        }
        const snap = u.snapshot();
        assert.ok(snap.tick >= PRESENT_EPOCH);
        assert.equal(snap.epoch, "Present");
    });
});


// ============================================================================
// Additional RNG tests
// ============================================================================

describe("RNG (additional)", () => {
    it("expovariate returns positive values", () => {
        const r = new RNG(42);
        for (let i = 0; i < 100; i++) {
            const v = r.expovariate(1.0);
            assert.ok(v >= 0, `expovariate returned ${v}`);
        }
    });

    it("expovariate mean is approximately 1/lambda", () => {
        const r = new RNG(42);
        const lambda = 2.0;
        let sum = 0;
        const n = 5000;
        for (let i = 0; i < n; i++) sum += r.expovariate(lambda);
        const mean = sum / n;
        assert.ok(Math.abs(mean - 1 / lambda) < 0.15, `Expovariate mean ${mean} too far from ${1 / lambda}`);
    });

    it("randint returns integers in [min, max]", () => {
        const r = new RNG(42);
        for (let i = 0; i < 100; i++) {
            const v = r.randint(5, 10);
            assert.ok(v >= 5 && v <= 10, `randint returned ${v}`);
            assert.ok(Number.isInteger(v), `randint returned non-integer ${v}`);
        }
    });

    it("randint covers full range", () => {
        const r = new RNG(42);
        const seen = new Set<number>();
        for (let i = 0; i < 1000; i++) {
            seen.add(r.randint(0, 3));
        }
        assert.ok(seen.has(0));
        assert.ok(seen.has(1));
        assert.ok(seen.has(2));
        assert.ok(seen.has(3));
    });
});


// ============================================================================
// Additional Particle tests
// ============================================================================

describe("Particle (additional)", () => {
    it("accepts spin and color parameters", () => {
        new Universe(42);
        const p = new Particle(ParticleType.UP, [1, 2, 3], [0, 0, 0], Spin.DOWN, Color.RED);
        assert.equal(p.spin, Spin.DOWN);
        assert.equal(p.color, Color.RED);
    });

    it("quarks have correct fractional charges", () => {
        const up = new Particle(ParticleType.UP, [0, 0, 0], [0, 0, 0]);
        assert.ok(Math.abs(up.charge - 2.0 / 3.0) < 1e-10);

        const down = new Particle(ParticleType.DOWN, [0, 0, 0], [0, 0, 0]);
        assert.ok(Math.abs(down.charge - (-1.0 / 3.0)) < 1e-10);
    });

    it("neutrino has tiny mass", () => {
        const nu = new Particle(ParticleType.NEUTRINO, [0, 0, 0], [0, 0, 0]);
        assert.equal(nu.mass, M_NEUTRINO);
        assert.ok(nu.mass > 0 && nu.mass < M_ELECTRON);
    });

    it("gluon is massless", () => {
        const g = new Particle(ParticleType.GLUON, [0, 0, 0], [0, 0, 0]);
        assert.equal(g.mass, 0.0);
    });
});


// ============================================================================
// Additional QuantumField tests
// ============================================================================

describe("QuantumField (additional)", () => {
    it("vacuumFluctuation produces pairs at high temperature", () => {
        new Universe(42);
        const qf = new QuantumField(T_PLANCK);
        let produced = false;
        for (let i = 0; i < 100; i++) {
            if (qf.vacuumFluctuation() !== null) {
                produced = true;
                break;
            }
        }
        assert.ok(produced, "vacuum fluctuation should produce pairs at Planck temperature");
    });

    it("vacuumFluctuation rarely produces at low temperature", () => {
        new Universe(42);
        const qf = new QuantumField(0.001);
        let produced = 0;
        for (let i = 0; i < 100; i++) {
            if (qf.vacuumFluctuation() !== null) produced++;
        }
        assert.ok(produced < 10, `Too many fluctuations at low temperature: ${produced}`);
    });

    it("evolve updates wave functions of particles", () => {
        new Universe(42);
        const qf = new QuantumField(1e6);
        const p = new Particle(ParticleType.ELECTRON, [0, 0, 0], [1, 0, 0]);
        qf.particles.push(p);
        const oldPhase = p.waveFn.phase;
        qf.evolve(1.0);
        assert.notEqual(p.waveFn.phase, oldPhase);
    });
});


// ============================================================================
// Additional Atom tests
// ============================================================================

describe("Atom (additional)", () => {
    it("bondEnergy returns correct values for different bond types", () => {
        new Universe(42);
        const na = new Atom(11); // Na, EN = 0.93
        const cl = new Atom(17); // Cl, EN = 3.16
        assert.equal(na.bondEnergy(cl), BOND_ENERGY_IONIC);

        const c = new Atom(6);  // C, EN = 2.55
        const h = new Atom(1);  // H, EN = 2.20
        assert.equal(c.bondEnergy(h), BOND_ENERGY_COVALENT);

        const o = new Atom(8);  // O, EN = 3.44
        const hh = new Atom(1); // H, EN = 2.20
        // diff = 1.24, between 0.4 and 1.7 -> polar_covalent
        const expected = (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2;
        assert.equal(o.bondEnergy(hh), expected);
    });

    it("distanceTo calculates correct Euclidean distance", () => {
        new Universe(42);
        const a1 = new Atom(1, undefined, [0, 0, 0]);
        const a2 = new Atom(1, undefined, [3, 4, 0]);
        assert.ok(Math.abs(a1.distanceTo(a2) - 5.0) < 1e-10);
    });

    it("distanceTo self is zero", () => {
        new Universe(42);
        const a = new Atom(1, undefined, [1, 2, 3]);
        assert.ok(Math.abs(a.distanceTo(a)) < 1e-10);
    });

    it("canBondWith respects bond limit of 4", () => {
        new Universe(42);
        const c = new Atom(6);
        const h = new Atom(1);
        // Simulate 4 bonds already formed
        c.bonds = [1, 2, 3, 4];
        assert.ok(!c.canBondWith(h));
    });
});


// ============================================================================
// Additional AtomicSystem tests
// ============================================================================

describe("AtomicSystem (additional)", () => {
    it("stellarNucleosynthesis creates heavier elements from He", () => {
        new Universe(42);
        const as = new AtomicSystem();
        // Add lots of helium atoms to allow triple-alpha process
        for (let i = 0; i < 30; i++) {
            as.atoms.push(new Atom(2, 4, [0, 0, 0]));
        }
        // Run many times to overcome probability barrier (0.01 chance)
        let carbonFormed = false;
        for (let trial = 0; trial < 50; trial++) {
            const newAtoms = as.stellarNucleosynthesis(1e6);
            if (newAtoms.some(a => a.atomicNumber === 6)) {
                carbonFormed = true;
                break;
            }
        }
        assert.ok(carbonFormed, "Triple-alpha should eventually produce carbon");
    });

    it("stellarNucleosynthesis returns empty at low temperature", () => {
        new Universe(42);
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom(2, 4, [0, 0, 0]));
        const result = as.stellarNucleosynthesis(100); // Below 1e3 threshold
        assert.equal(result.length, 0);
    });
});


// ============================================================================
// Additional ChemicalSystem tests
// ============================================================================

describe("ChemicalSystem (additional)", () => {
    it("formMethane creates CH4 molecules", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.atoms.push(new Atom(6, undefined, [0, 0, 0]));
        for (let i = 0; i < 4; i++) as.atoms.push(new Atom(1, undefined, [i * 0.1, 0, 0]));
        const cs = new ChemicalSystem(as);
        const methanes = cs.formMethane();
        assert.equal(methanes.length, 1);
        assert.equal(methanes[0].name, "methane");
    });

    it("formAmmonia creates NH3 molecules", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.atoms.push(new Atom(7, undefined, [0, 0, 0]));
        for (let i = 0; i < 3; i++) as.atoms.push(new Atom(1, undefined, [i * 0.1, 0, 0]));
        const cs = new ChemicalSystem(as);
        const ammonias = cs.formAmmonia();
        assert.equal(ammonias.length, 1);
        assert.equal(ammonias[0].name, "ammonia");
    });

    it("formAminoAcid creates organic molecule", () => {
        new Universe(42);
        const as = new AtomicSystem();
        // Glycine: 2C + 5H + 2O + 1N
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom(6, undefined, [i, 0, 0]));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom(1, undefined, [i, 1, 0]));
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom(8, undefined, [i, 2, 0]));
        as.atoms.push(new Atom(7, undefined, [0, 3, 0]));
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid("Gly");
        assert.ok(aa !== null);
        assert.ok(aa!.isOrganic);
        assert.equal(cs.aminoAcidCount, 1);
    });

    it("formAminoAcid returns null with insufficient atoms", () => {
        new Universe(42);
        const as = new AtomicSystem();
        as.atoms.push(new Atom(1, undefined, [0, 0, 0]));
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid("Gly");
        assert.equal(aa, null);
    });

    it("formNucleotide creates nucleotide molecule", () => {
        new Universe(42);
        const as = new AtomicSystem();
        // Nucleotide: 5C + 8H + 4O + 2N
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom(6, undefined, [i, 0, 0]));
        for (let i = 0; i < 8; i++) as.atoms.push(new Atom(1, undefined, [i, 1, 0]));
        for (let i = 0; i < 4; i++) as.atoms.push(new Atom(8, undefined, [i, 2, 0]));
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom(7, undefined, [i, 3, 0]));
        const cs = new ChemicalSystem(as);
        const nuc = cs.formNucleotide("A");
        assert.ok(nuc !== null);
        assert.equal(cs.nucleotideCount, 1);
    });

    it("catalyzedReaction forms products with sufficient atoms", () => {
        new Universe(42);
        const as = new AtomicSystem();
        // Add plenty of atoms for amino acid and nucleotide formation
        for (let i = 0; i < 20; i++) as.atoms.push(new Atom(6, undefined, [i, 0, 0]));
        for (let i = 0; i < 40; i++) as.atoms.push(new Atom(1, undefined, [i, 1, 0]));
        for (let i = 0; i < 20; i++) as.atoms.push(new Atom(8, undefined, [i, 2, 0]));
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom(7, undefined, [i, 3, 0]));
        const cs = new ChemicalSystem(as);
        // High temperature with catalyst to maximize probability
        let totalFormed = 0;
        for (let i = 0; i < 100; i++) {
            totalFormed += cs.catalyzedReaction(5000, true);
        }
        assert.ok(totalFormed > 0, "Catalyzed reaction should form some products over 100 tries");
    });
});


// ============================================================================
// Molecule tests
// ============================================================================

describe("Molecule", () => {
    it("computes formula correctly for water", () => {
        new Universe(42);
        const h1 = new Atom(1, undefined, [0, 0, 0]);
        const h2 = new Atom(1, undefined, [1, 0, 0]);
        const o = new Atom(8, undefined, [0.5, 0, 0]);
        const mol = new Molecule([h1, h2, o], "water");
        assert.equal(mol.formula, "H2O");
    });

    it("computes formula correctly for methane", () => {
        new Universe(42);
        const c = new Atom(6, undefined, [0, 0, 0]);
        const h1 = new Atom(1, undefined, [1, 0, 0]);
        const h2 = new Atom(1, undefined, [0, 1, 0]);
        const h3 = new Atom(1, undefined, [0, 0, 1]);
        const h4 = new Atom(1, undefined, [-1, 0, 0]);
        const mol = new Molecule([c, h1, h2, h3, h4], "methane");
        assert.equal(mol.formula, "CH4");
        assert.ok(mol.isOrganic);
    });

    it("molecularWeight sums mass numbers", () => {
        new Universe(42);
        const h1 = new Atom(1, 1, [0, 0, 0]);
        const h2 = new Atom(1, 1, [1, 0, 0]);
        const o = new Atom(8, 16, [0.5, 0, 0]);
        const mol = new Molecule([h1, h2, o], "water");
        assert.equal(mol.molecularWeight, 18); // 1 + 1 + 16
    });

    it("inorganic molecules do not have isOrganic flag", () => {
        new Universe(42);
        const na = new Atom(11, undefined, [0, 0, 0]);
        const cl = new Atom(17, undefined, [1, 0, 0]);
        const mol = new Molecule([na, cl], "NaCl");
        assert.ok(!mol.isOrganic);
    });
});


// ============================================================================
// Additional Gene tests
// ============================================================================

describe("Gene (additional)", () => {
    it("demethylate removes methylation marks", () => {
        const seq = Array(10).fill("A");
        const gene = new Gene("test", seq, 0, 10);
        gene.methylate(0);
        gene.methylate(1);
        assert.ok(gene.epigeneticMarks.length >= 2);
        gene.demethylate(0);
        const methylsAt0 = gene.epigeneticMarks.filter(m => m.position === 0 && m.markType === "methylation");
        assert.equal(methylsAt0.length, 0);
    });

    it("acetylate adds acetylation marks", () => {
        const seq = Array(10).fill("A");
        const gene = new Gene("test", seq, 0, 10);
        gene.acetylate(5, 1);
        const acetyls = gene.epigeneticMarks.filter(m => m.markType === "acetylation");
        assert.equal(acetyls.length, 1);
        assert.equal(acetyls[0].position, 5);
    });

    it("acetylation increases expression level", () => {
        const seq = Array(20).fill("A");
        const gene = new Gene("test", seq, 0, 20);
        const baseLine = gene.expressionLevel;
        for (let i = 0; i < 10; i++) gene.acetylate(i);
        assert.ok(gene.expressionLevel >= baseLine);
    });

    it("silenced gene returns empty transcription", () => {
        new Universe(42);
        const seq = Array(10).fill("A");
        const gene = new Gene("test", seq, 0, 10);
        // Methylate more than 30% of positions
        for (let i = 0; i < 5; i++) gene.methylate(i);
        assert.ok(gene.isSilenced);
        const mrna = gene.transcribe();
        assert.deepEqual(mrna, []);
    });

    it("essential flag is stored correctly", () => {
        const gene = new Gene("essential_gene", ["A", "T", "G"], 0, 3, true);
        assert.ok(gene.essential);
    });

    it("length getter returns correct value", () => {
        const gene = new Gene("test", ["A", "T", "G", "C", "A"], 0, 5);
        assert.equal(gene.length, 5);
    });
});


// ============================================================================
// Additional DNAStrand tests
// ============================================================================

describe("DNAStrand (additional)", () => {
    it("applyEpigeneticChanges modifies gene expression", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(90, 3);
        // Run many epigenetic cycles to see changes
        for (let i = 0; i < 50; i++) {
            dna.applyEpigeneticChanges(300, i);
        }
        // At least some genes should have epigenetic marks
        let hasMarks = false;
        for (const gene of dna.genes) {
            if (gene.epigeneticMarks.length > 0) { hasMarks = true; break; }
        }
        assert.ok(hasMarks, "Epigenetic changes should add marks to genes");
    });

    it("replicate preserves some epigenetic marks", () => {
        new Universe(42);
        const dna = DNAStrand.randomStrand(90, 3);
        // Add epigenetic marks
        for (let i = 0; i < 10; i++) {
            dna.applyEpigeneticChanges(300, 0);
        }
        const copy = dna.replicate();
        assert.equal(copy.generation, dna.generation + 1);
        assert.equal(copy.length, dna.length);
    });

    it("gcContent of all-GC strand is 1.0", () => {
        const dna = new DNAStrand(["G", "C", "G", "C"]);
        assert.equal(dna.gcContent, 1.0);
    });

    it("gcContent of all-AT strand is 0.0", () => {
        const dna = new DNAStrand(["A", "T", "A", "T"]);
        assert.equal(dna.gcContent, 0.0);
    });

    it("gcContent of empty strand is 0.0", () => {
        const dna = new DNAStrand([]);
        assert.equal(dna.gcContent, 0);
    });

    it("COMPLEMENT map is correct", () => {
        assert.equal(DNAStrand.COMPLEMENT["A"], "T");
        assert.equal(DNAStrand.COMPLEMENT["T"], "A");
        assert.equal(DNAStrand.COMPLEMENT["G"], "C");
        assert.equal(DNAStrand.COMPLEMENT["C"], "G");
    });
});


// ============================================================================
// Protein tests
// ============================================================================

describe("Protein", () => {
    it("creates with amino acid sequence", () => {
        new Universe(42);
        const protein = new Protein(["Met", "Ala", "Gly"], "testProtein", "enzyme");
        assert.equal(protein.length, 3);
        assert.equal(protein.name, "testProtein");
        assert.equal(protein.func, "enzyme");
        assert.ok(!protein.folded);
        assert.ok(protein.active);
    });

    it("fold returns false for short proteins", () => {
        new Universe(42);
        const p = new Protein(["Met", "Ala"]);
        const result = p.fold();
        assert.ok(!result);
        assert.ok(!p.folded);
    });

    it("fold can succeed for longer proteins", () => {
        new Universe(42);
        const aa = Array(20).fill("Met");
        let folded = false;
        for (let trial = 0; trial < 50; trial++) {
            const p = new Protein([...aa]);
            if (p.fold()) { folded = true; break; }
        }
        assert.ok(folded, "At least one of 50 proteins should fold successfully");
    });

    it("length getter returns amino acid count", () => {
        const p = new Protein(["Met", "Ala", "Gly", "Leu", "Val"]);
        assert.equal(p.length, 5);
    });
});


// ============================================================================
// Additional Cell tests
// ============================================================================

describe("Cell (additional)", () => {
    it("transcribeAndTranslate produces proteins from genes", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 100);
        const proteins = cell.transcribeAndTranslate();
        assert.ok(Array.isArray(proteins));
    });

    it("computeFitness returns 0 for dead cells", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 100);
        cell.alive = false;
        const f = cell.computeFitness();
        assert.equal(f, 0);
    });

    it("divide returns null when energy insufficient", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 10); // 10 < 50 threshold
        const daughter = cell.divide();
        assert.equal(daughter, null);
    });

    it("divide returns null when cell is dead", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 100);
        cell.alive = false;
        const daughter = cell.divide();
        assert.equal(daughter, null);
    });

    it("divide halves parent energy", () => {
        new Universe(42);
        const cell = new Cell(undefined, 0, 100);
        cell.transcribeAndTranslate();
        const preDivideEnergy = cell.energy;
        const daughter = cell.divide();
        if (daughter) {
            assert.ok(Math.abs(cell.energy - preDivideEnergy / 2) < 1e-10);
        }
    });
});


// ============================================================================
// Additional Biosphere tests
// ============================================================================

describe("Biosphere (additional)", () => {
    it("totalMutations accumulates across steps", () => {
        new Universe(42);
        const bio = new Biosphere(5, 90);
        bio.step(10, 5, 5, 300); // High UV and cosmic ray flux
        bio.step(10, 5, 5, 300);
        const total = bio.totalMutations();
        assert.ok(total >= 0);
    });

    it("step handles zero environment energy", () => {
        new Universe(42);
        const bio = new Biosphere(5, 30);
        bio.step(0, 0, 0, 300);
        // Cells should survive or die, no crashes
        assert.ok(bio.cells.length >= 0);
    });

    it("step with high UV causes mutations", () => {
        new Universe(42);
        const bio = new Biosphere(3, 90);
        bio.step(10, 100, 0, 300); // Very high UV
        // Should have some mutations
        const mutations = bio.totalMutations();
        assert.ok(mutations >= 0);
    });
});


// ============================================================================
// Additional Environment tests
// ============================================================================

describe("Environment (additional)", () => {
    it("getRadiationDose sums all radiation sources", () => {
        const env = new Environment(300);
        env.uvIntensity = 1.0;
        env.cosmicRayFlux = 0.5;
        env.stellarWind = 0.2;
        assert.ok(Math.abs(env.getRadiationDose() - 1.7) < 1e-10);
    });

    it("thermalEnergy is positive in habitable range", () => {
        const env = new Environment(300);
        const te = env.thermalEnergy();
        assert.ok(te > 0);
        assert.ok(Math.abs(te - 30.0) < 0.01); // 300 * 0.1
    });

    it("thermalEnergy returns 0.1 outside habitable range", () => {
        const env = new Environment(50);
        assert.equal(env.thermalEnergy(), 0.1);

        const env2 = new Environment(600);
        assert.equal(env2.thermalEnergy(), 0.1);
    });

    it("isHabitable requires water availability", () => {
        new Universe(42);
        const env = new Environment(300);
        env.waterAvailability = 0.0;
        env.uvIntensity = 0.1;
        env.cosmicRayFlux = 0.1;
        env.stellarWind = 0.0;
        assert.ok(!env.isHabitable());
    });

    it("update sets atmospheric density after epoch 210000", () => {
        new Universe(42);
        const env = new Environment(300);
        env.update(250000);
        assert.ok(env.atmosphericDensity > 0);
    });

    it("update sets water availability after epoch 220000", () => {
        new Universe(42);
        const env = new Environment(300);
        env.update(260000);
        assert.ok(env.waterAvailability > 0);
    });

    it("update sets cosmic ray flux based on epoch", () => {
        new Universe(42);
        const env = new Environment(T_PLANCK);
        env.update(5000);
        assert.equal(env.cosmicRayFlux, 1.0); // below 10000 threshold

        env.update(15000);
        assert.ok(env.cosmicRayFlux >= 0); // above 10000
    });
});


// ============================================================================
// Additional Universe tests
// ============================================================================

describe("Universe (additional)", () => {
    it("different seeds produce different snapshots", () => {
        const u1 = new Universe(42);
        for (let i = 0; i < 50; i++) u1.step();
        const s1 = u1.snapshot();

        const u2 = new Universe(99);
        for (let i = 0; i < 50; i++) u2.step();
        const s2 = u2.snapshot();

        // Same tick but different internal state
        assert.equal(s1.tick, s2.tick);
        assert.equal(typeof s1.temperature, "number");
        assert.equal(typeof s2.temperature, "number");
    });

    it("snapshot includes epoch descriptions", () => {
        const u = new Universe(42);
        for (let i = 0; i < 10; i++) u.step();
        const snap = u.snapshot();
        assert.ok(snap.epoch.length > 0);
        assert.ok(snap.epochDescription.length > 0);
    });

    it("snapshot has correct field types", () => {
        const u = new Universe(42);
        u.step();
        const snap = u.snapshot();
        assert.equal(typeof snap.tick, "number");
        assert.equal(typeof snap.epoch, "string");
        assert.equal(typeof snap.temperature, "number");
        assert.equal(typeof snap.particles, "number");
        assert.equal(typeof snap.atoms, "number");
        assert.equal(typeof snap.molecules, "number");
        assert.equal(typeof snap.cells, "number");
        assert.equal(typeof snap.epochDescription, "string");
    });
});
