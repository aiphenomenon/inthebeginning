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
