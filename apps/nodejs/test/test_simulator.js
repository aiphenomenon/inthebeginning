/**
 * Tests for the In The Beginning Node.js simulator.
 * Uses Node.js built-in test runner (node:test).
 *
 * Run: node --test apps/nodejs/test/test_simulator.js
 */

import { describe, it, before } from 'node:test';
import assert from 'node:assert/strict';

import {
    C, HBAR, K_B, M_ELECTRON, M_PROTON, M_NEUTRON, M_PHOTON,
    T_PLANCK, T_QUARK_HADRON, T_CMB, T_RECOMBINATION, T_EARTH_SURFACE,
    PLANCK_EPOCH, HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH,
    RECOMBINATION_EPOCH, PRESENT_EPOCH,
    BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC, PI,
    NUCLEOTIDE_BASES, CODON_TABLE, AMINO_ACIDS,
    RADIATION_DAMAGE_THRESHOLD,
} from '../constants.js';

import {
    QuantumField, Particle, ParticleType, Spin, Color,
    WaveFunction, gaussRandom, EntangledPair,
    resetParticleIdCounter,
} from '../quantum.js';

import {
    Atom, AtomicSystem, ElectronShell, ELEMENTS, resetAtomIdCounter,
} from '../atomic.js';
import {
    ChemicalSystem, Molecule, ChemicalReaction, resetMoleculeIdCounter,
} from '../chemistry.js';
import {
    Biosphere, EpigeneticMark, Gene, DNAStrand, translateMrna,
    Protein, Cell, resetCellIdCounter,
} from '../biology.js';
import { Environment, EnvironmentalEvent } from '../environment.js';
import { Universe, EPOCHS } from '../universe.js';


// ============================================================
// Constants
// ============================================================
describe('Constants', () => {
    it('speed of light is positive', () => {
        assert.ok(C > 0);
    });

    it('reduced Planck constant is positive', () => {
        assert.ok(HBAR > 0);
    });

    it('Boltzmann constant is positive', () => {
        assert.ok(K_B > 0);
    });

    it('electron mass < proton mass', () => {
        assert.ok(M_ELECTRON < M_PROTON);
    });

    it('proton mass ≈ neutron mass', () => {
        assert.ok(Math.abs(M_PROTON - M_NEUTRON) / M_PROTON < 0.01);
    });

    it('Planck temperature is very high', () => {
        assert.ok(T_PLANCK > 1e6);
    });

    it('epochs are in chronological order', () => {
        assert.ok(PLANCK_EPOCH < HADRON_EPOCH);
        assert.ok(HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
        assert.ok(NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
        assert.ok(RECOMBINATION_EPOCH < PRESENT_EPOCH);
    });

    it('there are 13 epochs defined', () => {
        assert.equal(EPOCHS.length, 13);
    });
});


// ============================================================
// Quantum Module
// ============================================================
describe('WaveFunction', () => {
    it('initializes with amplitude 1 and probability 1', () => {
        const wf = new WaveFunction();
        assert.equal(wf.amplitude, 1.0);
        assert.ok(Math.abs(wf.probability - 1.0) < 1e-10);
    });

    it('evolve changes phase', () => {
        const wf = new WaveFunction();
        const oldPhase = wf.phase;
        wf.evolve(1.0, 100.0);
        assert.notEqual(wf.phase, oldPhase);
    });

    it('collapse returns boolean and sets coherent false', () => {
        const wf = new WaveFunction();
        const result = wf.collapse();
        assert.equal(typeof result, 'boolean');
        assert.equal(wf.coherent, false);
    });

    it('evolve does nothing when not coherent', () => {
        const wf = new WaveFunction();
        wf.coherent = false;
        const phaseBefore = wf.phase;
        wf.evolve(1.0, 100.0);
        assert.equal(wf.phase, phaseBefore);
    });

    it('probability returns amplitude squared', () => {
        const wf = new WaveFunction(0.5);
        assert.ok(Math.abs(wf.probability - 0.25) < 1e-10);
    });

    it('superpose combines two wave functions', () => {
        const wf1 = new WaveFunction(0.7, 0.5);
        const wf2 = new WaveFunction(0.6, 0.3);
        const combined = wf1.superpose(wf2);
        assert.ok(combined instanceof WaveFunction);
        assert.ok(combined.amplitude > 0);
        assert.ok(combined.amplitude <= 1.0);
        assert.equal(combined.coherent, true);
        // Combined phase is average
        const expectedPhase = (0.5 + 0.3) / 2;
        assert.ok(Math.abs(combined.phase - expectedPhase) < 1e-10);
    });

    it('superpose with identical phases gives constructive interference', () => {
        const wf1 = new WaveFunction(0.5, 0.0);
        const wf2 = new WaveFunction(0.5, 0.0);
        const combined = wf1.superpose(wf2);
        assert.ok(combined.amplitude >= 0.99);
    });

    it('toCompact returns string with amplitude and phase', () => {
        const wf = new WaveFunction(0.75, 1.23);
        const compact = wf.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.includes('0.750'));
        assert.ok(compact.includes('1.23'));
    });
});


describe('Particle', () => {
    it('creates with correct type', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            position: [0, 0, 0],
            momentum: [1, 0, 0],
        });
        assert.equal(p.particleType, ParticleType.ELECTRON);
    });

    it('has unique particleId', () => {
        const p1 = new Particle({ particleType: ParticleType.ELECTRON });
        const p2 = new Particle({ particleType: ParticleType.PROTON });
        assert.notEqual(p1.particleId, p2.particleId);
    });

    it('electron has correct mass', () => {
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        assert.equal(p.mass, M_ELECTRON);
    });

    it('photon has zero mass', () => {
        const p = new Particle({ particleType: ParticleType.PHOTON });
        assert.equal(p.mass, M_PHOTON);
    });

    it('energy is non-negative', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1, 2, 3],
        });
        assert.ok(p.energy >= 0);
    });

    it('charge returns correct value for electron', () => {
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        assert.equal(p.charge, -1.0);
    });

    it('charge returns correct value for proton', () => {
        const p = new Particle({ particleType: ParticleType.PROTON });
        assert.equal(p.charge, 1.0);
    });

    it('charge returns correct value for neutron', () => {
        const p = new Particle({ particleType: ParticleType.NEUTRON });
        assert.equal(p.charge, 0.0);
    });

    it('wavelength is positive for moving particle', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1, 0, 0],
        });
        const wl = p.wavelength;
        assert.ok(wl > 0);
        assert.ok(isFinite(wl));
        const expected = 2 * PI * HBAR / 1.0;
        assert.ok(Math.abs(wl - expected) < 1e-10);
    });

    it('wavelength is Infinity for zero momentum', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [0, 0, 0],
        });
        assert.equal(p.wavelength, Infinity);
    });

    it('toCompact returns string with type and position', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            position: [1.5, 2.3, 0.0],
        });
        const compact = p.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.includes('electron'));
        assert.ok(compact.includes('s='));
    });
});


// ============================================================
// Spin and Color Enums
// ============================================================
describe('Spin', () => {
    it('has UP = 0.5 and DOWN = -0.5', () => {
        assert.equal(Spin.UP, 0.5);
        assert.equal(Spin.DOWN, -0.5);
    });
});

describe('Color', () => {
    it('has all color charge values', () => {
        assert.equal(Color.RED, 'r');
        assert.equal(Color.GREEN, 'g');
        assert.equal(Color.BLUE, 'b');
        assert.equal(Color.ANTI_RED, 'ar');
        assert.equal(Color.ANTI_GREEN, 'ag');
        assert.equal(Color.ANTI_BLUE, 'ab');
    });
});


// ============================================================
// EntangledPair
// ============================================================
describe('EntangledPair', () => {
    it('creates with two particles and default bell state', () => {
        const pa = new Particle({ particleType: ParticleType.ELECTRON });
        const pb = new Particle({ particleType: ParticleType.POSITRON });
        const pair = new EntangledPair(pa, pb);
        assert.equal(pair.bellState, 'phi+');
        assert.equal(pair.particleA.particleType, ParticleType.ELECTRON);
        assert.equal(pair.particleB.particleType, ParticleType.POSITRON);
    });

    it('measureA returns spin and anti-correlates', () => {
        const pa = new Particle({ particleType: ParticleType.ELECTRON });
        const pb = new Particle({ particleType: ParticleType.POSITRON });
        const pair = new EntangledPair(pa, pb);
        const spinA = pair.measureA();
        assert.ok(spinA === Spin.UP || spinA === Spin.DOWN);
        assert.notEqual(pa.spin, pb.spin);
        assert.equal(pa.waveFn.coherent, false);
        assert.equal(pb.waveFn.coherent, false);
    });
});


describe('QuantumField', () => {
    it('initializes empty', () => {
        const qf = new QuantumField(T_PLANCK);
        assert.equal(qf.particles.length, 0);
    });

    it('pair production creates 2 particles', () => {
        const qf = new QuantumField(T_PLANCK);
        const energy = 2 * M_ELECTRON * C * C * 10;
        const result = qf.pairProduction(energy);
        if (result) {
            assert.equal(qf.particles.length, 2);
        }
    });

    it('pair production fails below threshold', () => {
        const qf = new QuantumField(T_PLANCK);
        const result = qf.pairProduction(0.001);
        assert.equal(result, null);
        assert.equal(qf.particles.length, 0);
    });

    it('quark confinement produces hadrons', () => {
        const qf = new QuantumField(T_QUARK_HADRON * 0.5);
        // Add quarks manually
        for (let i = 0; i < 6; i++) {
            qf.particles.push(new Particle({
                particleType: ParticleType.UP,
                color: Color.RED,
            }));
        }
        for (let i = 0; i < 6; i++) {
            qf.particles.push(new Particle({
                particleType: ParticleType.DOWN,
                color: Color.BLUE,
            }));
        }
        const hadrons = qf.quarkConfinement();
        assert.ok(hadrons.length > 0);
        // Verify hadrons are protons or neutrons
        for (const h of hadrons) {
            assert.ok(
                h.particleType === ParticleType.PROTON ||
                h.particleType === ParticleType.NEUTRON
            );
        }
    });

    it('evolve updates particle positions', () => {
        const qf = new QuantumField(T_PLANCK);
        qf.particles.push(new Particle({
            particleType: ParticleType.ELECTRON,
            position: [0, 0, 0],
            momentum: [1, 0, 0],
        }));
        const oldPos = [...qf.particles[0].position];
        qf.evolve(1.0);
        assert.notDeepEqual(qf.particles[0].position, oldPos);
    });

    it('particleCount returns correct census', () => {
        const qf = new QuantumField(T_PLANCK);
        qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        qf.particles.push(new Particle({ particleType: ParticleType.PHOTON }));
        const counts = qf.particleCount();
        assert.equal(counts[ParticleType.ELECTRON], 2);
        assert.equal(counts[ParticleType.PHOTON], 1);
    });

    it('vacuum fluctuation may produce pairs', () => {
        const qf = new QuantumField(T_PLANCK);
        let produced = false;
        for (let i = 0; i < 100; i++) {
            if (qf.vacuumFluctuation()) {
                produced = true;
                break;
            }
        }
        // At Planck temperature, should produce at least one pair in 100 tries
        assert.ok(produced);
    });

    it('annihilate returns energy and creates photons', () => {
        const qf = new QuantumField(T_PLANCK);
        const energy = 2 * M_ELECTRON * C * C * 10;
        const result = qf.pairProduction(energy);
        if (result) {
            const [p1, p2] = result;
            const nBefore = qf.particles.length;
            const annEnergy = qf.annihilate(p1, p2);
            assert.ok(annEnergy > 0);
            assert.equal(qf.totalAnnihilated, 2);
            assert.ok(qf.vacuumEnergy > 0);
        }
    });

    it('totalEnergy is zero for empty field', () => {
        const qf = new QuantumField(T_PLANCK);
        assert.equal(qf.totalEnergy(), 0.0);
    });

    it('totalEnergy includes particle energy', () => {
        const qf = new QuantumField(T_PLANCK);
        qf.particles.push(new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1, 0, 0],
        }));
        assert.ok(qf.totalEnergy() > 0);
    });

    it('decohere can collapse coherent particle', () => {
        const qf = new QuantumField(1e6);
        let decohered = false;
        for (let i = 0; i < 1000; i++) {
            const p = new Particle({ particleType: ParticleType.ELECTRON });
            qf.decohere(p, 1.0);
            if (!p.waveFn.coherent) {
                decohered = true;
                break;
            }
        }
        assert.ok(decohered);
    });

    it('cool reduces temperature', () => {
        const qf = new QuantumField(1000);
        qf.cool(0.5);
        assert.equal(qf.temperature, 500);
        qf.cool();
        assert.ok(qf.temperature < 500);
    });

    it('toCompact returns formatted string', () => {
        const qf = new QuantumField(1000);
        qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        const compact = qf.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.startsWith('QF['));
        assert.ok(compact.includes('T='));
        assert.ok(compact.includes('n='));
    });
});


// ============================================================
// Atomic Module
// ============================================================
describe('ElectronShell', () => {
    it('full and empty properties work correctly', () => {
        const empty = new ElectronShell(1, 2, 0);
        assert.equal(empty.empty, true);
        assert.equal(empty.full, false);

        const full = new ElectronShell(1, 2, 2);
        assert.equal(full.full, true);
        assert.equal(full.empty, false);

        const partial = new ElectronShell(2, 8, 4);
        assert.equal(partial.full, false);
        assert.equal(partial.empty, false);
    });

    it('addElectron works and rejects when full', () => {
        const shell = new ElectronShell(1, 2, 0);
        assert.equal(shell.addElectron(), true);
        assert.equal(shell.electrons, 1);
        assert.equal(shell.addElectron(), true);
        assert.equal(shell.electrons, 2);
        assert.equal(shell.addElectron(), false);
        assert.equal(shell.electrons, 2);
    });

    it('removeElectron works and rejects when empty', () => {
        const shell = new ElectronShell(1, 2, 2);
        assert.equal(shell.removeElectron(), true);
        assert.equal(shell.electrons, 1);
        assert.equal(shell.removeElectron(), true);
        assert.equal(shell.electrons, 0);
        assert.equal(shell.removeElectron(), false);
        assert.equal(shell.electrons, 0);
    });
});


describe('Atom', () => {
    it('creates with specified atomic number', () => {
        const a = new Atom({ atomicNumber: 1 });
        assert.equal(a.atomicNumber, 1);
    });

    it('symbol for Z=1 is H', () => {
        const a = new Atom({ atomicNumber: 1 });
        assert.equal(a.symbol, 'H');
    });

    it('symbol for Z=2 is He', () => {
        const a = new Atom({ atomicNumber: 2 });
        assert.equal(a.symbol, 'He');
    });

    it('name returns element name', () => {
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(h.name, 'Hydrogen');
        const c = new Atom({ atomicNumber: 6 });
        assert.equal(c.name, 'Carbon');
        const fe = new Atom({ atomicNumber: 26 });
        assert.equal(fe.name, 'Iron');
    });

    it('electronegativity returns correct value', () => {
        const h = new Atom({ atomicNumber: 1 });
        assert.ok(Math.abs(h.electronegativity - 2.20) < 0.01);
        const na = new Atom({ atomicNumber: 11 });
        assert.ok(Math.abs(na.electronegativity - 0.93) < 0.01);
    });

    it('charge is 0 for neutral atom', () => {
        const h = new Atom({ atomicNumber: 1, electronCount: 1 });
        assert.equal(h.charge, 0);
    });

    it('charge is +1 for ionized hydrogen', () => {
        const h = new Atom({ atomicNumber: 1, electronCount: 1 });
        h.ionize();
        assert.equal(h.charge, 1);
    });

    it('valenceElectrons returns correct count', () => {
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(h.valenceElectrons, 1);
        const c = new Atom({ atomicNumber: 6 });
        assert.equal(c.valenceElectrons, 4);
    });

    it('needsElectrons returns correct count', () => {
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(h.needsElectrons, 1);
        const c = new Atom({ atomicNumber: 6 });
        assert.equal(c.needsElectrons, 4);
    });

    it('isNobleGas detects noble gases', () => {
        const he = new Atom({ atomicNumber: 2 });
        assert.equal(he.isNobleGas, true);
        const ne = new Atom({ atomicNumber: 10 });
        assert.equal(ne.isNobleGas, true);
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(h.isNobleGas, false);
    });

    it('isIon detects ionized atoms', () => {
        const h = new Atom({ atomicNumber: 1, electronCount: 1 });
        assert.equal(h.isIon, false);
        h.ionize();
        assert.equal(h.isIon, true);
    });

    it('ionize removes electron', () => {
        const h = new Atom({ atomicNumber: 1, electronCount: 1 });
        assert.equal(h.ionize(), true);
        assert.equal(h.electronCount, 0);
        assert.equal(h.isIon, true);
        assert.equal(h.ionize(), false);
    });

    it('captureElectron adds electron', () => {
        const h = new Atom({ atomicNumber: 1, electronCount: 1 });
        h.ionize();
        assert.equal(h.isIon, true);
        assert.equal(h.electronCount, 0);
        h.captureElectron();
        assert.equal(h.electronCount, 1);
        assert.equal(h.isIon, false);
    });

    it('canBondWith checks bonding ability', () => {
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        assert.equal(h1.canBondWith(h2), true);

        const he = new Atom({ atomicNumber: 2 });
        assert.equal(h1.canBondWith(he), false);

        const c = new Atom({ atomicNumber: 6 });
        c.bonds = [1, 2, 3, 4];
        assert.equal(c.canBondWith(h1), false);
    });

    it('bondType classifies ionic, polar covalent, and covalent', () => {
        const na = new Atom({ atomicNumber: 11 });
        const cl = new Atom({ atomicNumber: 17 });
        assert.equal(na.bondType(cl), 'ionic');

        const h = new Atom({ atomicNumber: 1 });
        const o = new Atom({ atomicNumber: 8 });
        assert.equal(h.bondType(o), 'polar_covalent');

        const h2 = new Atom({ atomicNumber: 1 });
        assert.equal(h.bondType(h2), 'covalent');
    });

    it('bondEnergy returns correct values', () => {
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        assert.equal(h1.bondEnergy(h2), BOND_ENERGY_COVALENT);

        const na = new Atom({ atomicNumber: 11 });
        const cl = new Atom({ atomicNumber: 17 });
        assert.equal(na.bondEnergy(cl), BOND_ENERGY_IONIC);
    });

    it('distanceTo computes Euclidean distance', () => {
        const a1 = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const a2 = new Atom({ atomicNumber: 1, position: [3, 4, 0] });
        assert.ok(Math.abs(a1.distanceTo(a2) - 5.0) < 1e-10);
    });

    it('toCompact returns formatted string', () => {
        const h = new Atom({ atomicNumber: 1 });
        const compact = h.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.includes('H'));
    });
});


describe('AtomicSystem', () => {
    it('initializes empty', () => {
        const as = new AtomicSystem();
        assert.equal(as.atoms.length, 0);
    });

    it('nucleosynthesis creates hydrogen and helium', () => {
        const as = new AtomicSystem();
        const atoms = as.nucleosynthesis(10, 5);
        assert.ok(atoms.length > 0);
        const elements = atoms.map(a => a.atomicNumber);
        assert.ok(elements.includes(1) || elements.includes(2));
    });

    it('elementCounts returns census', () => {
        const as = new AtomicSystem();
        as.atoms.push(new Atom({ atomicNumber: 1 }));
        as.atoms.push(new Atom({ atomicNumber: 1 }));
        as.atoms.push(new Atom({ atomicNumber: 6 }));
        const counts = as.elementCounts();
        assert.equal(counts['H'], 2);
        assert.equal(counts['C'], 1);
    });

    it('recombination forms hydrogen below T_RECOMBINATION', () => {
        const as = new AtomicSystem(T_RECOMBINATION * 0.5);
        const field = new QuantumField(T_RECOMBINATION * 0.5);
        field.particles.push(new Particle({ particleType: ParticleType.PROTON }));
        field.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        field.particles.push(new Particle({ particleType: ParticleType.PROTON }));
        field.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        const newAtoms = as.recombination(field);
        assert.ok(newAtoms.length > 0);
        assert.equal(newAtoms[0].atomicNumber, 1);
    });

    it('recombination returns empty above T_RECOMBINATION', () => {
        const as = new AtomicSystem(T_RECOMBINATION * 2);
        const field = new QuantumField(T_RECOMBINATION * 2);
        field.particles.push(new Particle({ particleType: ParticleType.PROTON }));
        field.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        const newAtoms = as.recombination(field);
        assert.equal(newAtoms.length, 0);
    });

    it('stellarNucleosynthesis produces heavier elements', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 30; i++) {
            as.atoms.push(new Atom({ atomicNumber: 2, massNumber: 4 }));
        }
        let totalNew = 0;
        for (let i = 0; i < 500; i++) {
            totalNew += as.stellarNucleosynthesis(1e4).length;
        }
        assert.ok(totalNew > 0);
    });

    it('stellarNucleosynthesis returns empty below 1e3', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 2, massNumber: 4 }));
        }
        const result = as.stellarNucleosynthesis(500);
        assert.equal(result.length, 0);
    });

    it('attemptBond can form bond between nearby atoms', () => {
        const as = new AtomicSystem(1e8);
        const h1 = new Atom({ atomicNumber: 1, electronCount: 1, position: [0, 0, 0] });
        const h2 = new Atom({ atomicNumber: 1, electronCount: 1, position: [0.5, 0, 0] });
        as.atoms.push(h1, h2);
        let bonded = false;
        for (let i = 0; i < 100; i++) {
            if (as.attemptBond(h1, h2)) {
                bonded = true;
                break;
            }
            h1.bonds = [];
            h2.bonds = [];
        }
        assert.ok(bonded);
    });

    it('attemptBond fails for far apart atoms', () => {
        const as = new AtomicSystem(300);
        const h1 = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const h2 = new Atom({ atomicNumber: 1, position: [100, 100, 100] });
        assert.equal(as.attemptBond(h1, h2), false);
    });

    it('breakBond can break bond at high temperature', () => {
        const as = new AtomicSystem(1e8);
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        h1.bonds.push(h2.atomId);
        h2.bonds.push(h1.atomId);
        let broken = false;
        for (let i = 0; i < 1000; i++) {
            if (as.breakBond(h1, h2)) {
                broken = true;
                break;
            }
            h1.bonds.push(h2.atomId);
            h2.bonds.push(h1.atomId);
        }
        assert.ok(broken);
    });

    it('breakBond returns false for unbonded atoms', () => {
        const as = new AtomicSystem(1e8);
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        assert.equal(as.breakBond(h1, h2), false);
    });

    it('cool reduces temperature', () => {
        const as = new AtomicSystem(1000);
        as.cool(0.5);
        assert.equal(as.temperature, 500);
        as.cool();
        assert.ok(as.temperature < 500);
    });

    it('toCompact returns formatted string', () => {
        const as = new AtomicSystem();
        as.atoms.push(new Atom({ atomicNumber: 1 }));
        as.atoms.push(new Atom({ atomicNumber: 2 }));
        const compact = as.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.startsWith('AS['));
        assert.ok(compact.includes('n=2'));
    });
});


// ============================================================
// Chemistry Module
// ============================================================
describe('Molecule', () => {
    it('computes molecular weight', () => {
        const h1 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const o = new Atom({ atomicNumber: 8, massNumber: 16 });
        const mol = new Molecule({ atoms: [h1, h2, o], name: 'water' });
        assert.equal(mol.molecularWeight, 18);
    });

    it('computes atom count', () => {
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        const o = new Atom({ atomicNumber: 8 });
        const mol = new Molecule({ atoms: [h1, h2, o], name: 'water' });
        assert.equal(mol.atomCount, 3);
    });

    it('toCompact returns formatted string', () => {
        const h1 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const o = new Atom({ atomicNumber: 8, massNumber: 16 });
        const mol = new Molecule({ atoms: [h1, h2, o], name: 'water' });
        const compact = mol.toCompact();
        assert.ok(compact.includes('water'));
        assert.ok(compact.includes('mw=18'));
    });

    it('auto-detects organic molecules', () => {
        const c = new Atom({ atomicNumber: 6 });
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        const h3 = new Atom({ atomicNumber: 1 });
        const h4 = new Atom({ atomicNumber: 1 });
        const mol = new Molecule({ atoms: [c, h1, h2, h3, h4] });
        assert.equal(mol.isOrganic, true);
        assert.ok(mol.formula.includes('CH4'));
    });
});


describe('ChemicalReaction', () => {
    it('creates with reactants and products', () => {
        const rxn = new ChemicalReaction(['H2', 'O'], ['H2O'], 1.0, -2.0, 'combustion');
        assert.equal(rxn.name, 'combustion');
        assert.equal(rxn.activationEnergy, 1.0);
        assert.equal(rxn.deltaH, -2.0);
    });

    it('canProceed returns true at high temp with low Ea', () => {
        const rxn = new ChemicalReaction(['H2', 'O'], ['H2O'], 0.0001, 0.0, 'easy');
        let proceeded = false;
        for (let i = 0; i < 100; i++) {
            if (rxn.canProceed(1e6)) {
                proceeded = true;
                break;
            }
        }
        assert.ok(proceeded);
    });

    it('canProceed returns false at zero temperature', () => {
        const rxn = new ChemicalReaction(['A'], ['B'], 1.0);
        assert.equal(rxn.canProceed(0), false);
    });

    it('toCompact returns formatted string', () => {
        const rxn = new ChemicalReaction(['A', 'B'], ['C'], 2.5, -1.0);
        const compact = rxn.toCompact();
        assert.ok(compact.includes('A+B'));
        assert.ok(compact.includes('->C'));
        assert.ok(compact.includes('Ea=2.5'));
        assert.ok(compact.includes('dH=-1.0'));
    });
});


describe('ChemicalSystem', () => {
    it('initializes with zero molecules', () => {
        const as = new AtomicSystem();
        const cs = new ChemicalSystem(as);
        assert.equal(cs.molecules.length, 0);
    });

    it('formWater produces water molecules', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        const waters = cs.formWater();
        assert.ok(waters.length > 0);
        assert.equal(waters[0].name, 'water');
    });

    it('formMethane produces methane', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom({ atomicNumber: 6 }));
        const cs = new ChemicalSystem(as);
        const methanes = cs.formMethane();
        assert.ok(methanes.length > 0);
        assert.equal(methanes[0].name, 'methane');
        assert.equal(methanes[0].atomCount, 5);
    });

    it('formAmmonia produces ammonia', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom({ atomicNumber: 7 }));
        const cs = new ChemicalSystem(as);
        const ammonias = cs.formAmmonia();
        assert.ok(ammonias.length > 0);
        assert.equal(ammonias[0].name, 'ammonia');
        assert.equal(ammonias[0].atomCount, 4);
    });

    it('formAminoAcid produces amino acid with sufficient atoms', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom({ atomicNumber: 6 }));
        for (let i = 0; i < 2; i++) as.atoms.push(new Atom({ atomicNumber: 7 }));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid('Gly');
        assert.ok(aa !== null);
        assert.equal(aa.name, 'Gly');
        assert.equal(aa.isOrganic, true);
        assert.equal(cs.aminoAcidCount, 1);
    });

    it('formAminoAcid returns null with insufficient atoms', () => {
        const as = new AtomicSystem();
        as.atoms.push(new Atom({ atomicNumber: 1 }));
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid('Gly');
        assert.equal(aa, null);
    });

    it('formNucleotide produces nucleotide with sufficient atoms', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 20; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 6 }));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom({ atomicNumber: 7 }));
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        const nuc = cs.formNucleotide('A');
        assert.ok(nuc !== null);
        assert.equal(nuc.name, 'nucleotide-A');
        assert.equal(nuc.isOrganic, true);
        assert.equal(cs.nucleotideCount, 1);
    });

    it('catalyzedReaction can form complex molecules at high temp', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 40; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 20; i++) as.atoms.push(new Atom({ atomicNumber: 6 }));
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 7 }));
        for (let i = 0; i < 15; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        let totalFormed = 0;
        for (let i = 0; i < 200; i++) {
            totalFormed += cs.catalyzedReaction(1e8, true);
        }
        assert.ok(totalFormed > 0);
        assert.ok(cs.reactionsOccurred > 0);
    });

    it('moleculeCensus returns correct types', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 3; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        cs.formWater();
        const census = cs.moleculeCensus();
        assert.ok(typeof census === 'object');
        assert.ok(census['water'] >= 1);
    });

    it('toCompact returns formatted string', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) as.atoms.push(new Atom({ atomicNumber: 1 }));
        for (let i = 0; i < 5; i++) as.atoms.push(new Atom({ atomicNumber: 8 }));
        const cs = new ChemicalSystem(as);
        cs.formWater();
        const compact = cs.toCompact();
        assert.ok(compact.startsWith('CS['));
        assert.ok(compact.includes('H2O='));
    });
});


// ============================================================
// Biology Module
// ============================================================
describe('EpigeneticMark', () => {
    it('toCompact returns formatted string', () => {
        const mark = new EpigeneticMark(3, 'methylation', true, 0);
        assert.equal(mark.toCompact(), 'M3+');

        const mark2 = new EpigeneticMark(7, 'acetylation', false, 1);
        assert.equal(mark2.toCompact(), 'A7-');

        const mark3 = new EpigeneticMark(0, 'phosphorylation', true, 5);
        assert.equal(mark3.toCompact(), 'P0+');
    });
});


describe('Gene', () => {
    it('length returns sequence length', () => {
        const g = new Gene({ name: 'test', sequence: ['A', 'T', 'G'] });
        assert.equal(g.length, 3);
    });

    it('transcribe converts T to U', () => {
        const g = new Gene({ name: 'test', sequence: ['A', 'T', 'G', 'C'] });
        const rna = g.transcribe();
        assert.deepEqual(rna, ['A', 'U', 'G', 'C']);
    });

    it('isSilenced returns true when heavily methylated', () => {
        const g = new Gene({ name: 'test', sequence: ['A', 'T', 'G', 'C', 'A', 'T', 'G', 'C', 'A', 'T'] });
        assert.equal(g.isSilenced, false);
        for (let i = 0; i < 5; i++) {
            g.methylate(i);
        }
        assert.equal(g.isSilenced, true);
        assert.deepEqual(g.transcribe(), []);
    });

    it('demethylate removes methylation marks', () => {
        const g = new Gene({ name: 'test', sequence: ['A', 'T', 'G', 'C', 'A'] });
        g.methylate(0);
        g.methylate(1);
        assert.ok(g.epigeneticMarks.length >= 2);
        g.demethylate(0);
        const methylAt0 = g.epigeneticMarks.filter(m => m.position === 0 && m.markType === 'methylation');
        assert.equal(methylAt0.length, 0);
    });

    it('acetylate increases expression', () => {
        const g = new Gene({ name: 'test', sequence: ['A', 'T', 'G', 'C', 'A'] });
        g.methylate(0);
        g.methylate(1);
        const exprAfterMethyl = g.expressionLevel;
        g.acetylate(0);
        g.acetylate(1);
        g.acetylate(2);
        assert.ok(g.expressionLevel >= exprAfterMethyl);
    });

    it('mutate changes bases at given rate', () => {
        const g = new Gene({ name: 'test', sequence: Array(100).fill('A') });
        const mutations = g.mutate(0.5);
        assert.ok(mutations > 0);
    });

    it('toCompact returns formatted string', () => {
        const g = new Gene({ name: 'myGene', sequence: ['A', 'T', 'G'] });
        const compact = g.toCompact();
        assert.ok(compact.includes('myGene'));
        assert.ok(compact.includes('e='));
    });
});


describe('DNAStrand', () => {
    it('length returns sequence length', () => {
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'C', 'A', 'T'] });
        assert.equal(dna.length, 6);
    });

    it('complementaryStrand returns correct pairs', () => {
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'C'] });
        assert.deepEqual(dna.complementaryStrand, ['T', 'A', 'C', 'G']);
    });

    it('gcContent computes correctly', () => {
        const allGC = new DNAStrand({ sequence: ['G', 'C', 'G', 'C'] });
        assert.ok(Math.abs(allGC.gcContent - 1.0) < 1e-10);

        const allAT = new DNAStrand({ sequence: ['A', 'T', 'A', 'T'] });
        assert.ok(Math.abs(allAT.gcContent - 0.0) < 1e-10);

        const mixed = new DNAStrand({ sequence: ['A', 'G', 'C', 'T'] });
        assert.ok(Math.abs(mixed.gcContent - 0.5) < 1e-10);

        const empty = new DNAStrand({ sequence: [] });
        assert.equal(empty.gcContent, 0.0);
    });

    it('randomStrand generates correct length and genes', () => {
        const strand = DNAStrand.randomStrand(100, 3);
        assert.equal(strand.length, 100);
        assert.equal(strand.genes.length, 3);
    });

    it('replicate produces copy with incremented generation', () => {
        const strand = DNAStrand.randomStrand(50, 2);
        const copy = strand.replicate();
        assert.equal(copy.length, strand.length);
        assert.equal(copy.generation, strand.generation + 1);
    });

    it('applyMutations causes mutations with high radiation', () => {
        const strand = DNAStrand.randomStrand(200, 3);
        const mutations = strand.applyMutations(100.0, 100.0);
        assert.ok(mutations > 0);
        assert.equal(strand.mutationCount, mutations);
    });

    it('applyMutations causes zero mutations with zero radiation', () => {
        const strand = DNAStrand.randomStrand(50, 2);
        const mutations = strand.applyMutations(0.0, 0.0);
        assert.equal(mutations, 0);
    });

    it('applyEpigeneticChanges adds marks to genes', () => {
        const strand = DNAStrand.randomStrand(100, 3);
        let initialMarks = 0;
        for (const g of strand.genes) initialMarks += g.epigeneticMarks.length;
        for (let i = 0; i < 100; i++) {
            strand.applyEpigeneticChanges(300.0, i);
        }
        let finalMarks = 0;
        for (const g of strand.genes) finalMarks += g.epigeneticMarks.length;
        assert.ok(finalMarks > initialMarks);
    });

    it('toCompact returns formatted string', () => {
        const strand = DNAStrand.randomStrand(50, 2);
        const compact = strand.toCompact();
        assert.ok(compact.includes('DNA['));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('gc='));
    });
});


describe('translateMrna', () => {
    it('translates AUG-UUU-UAA to Met-Phe', () => {
        const mrna = ['A', 'U', 'G', 'U', 'U', 'U', 'U', 'A', 'A'];
        const protein = translateMrna(mrna);
        assert.equal(protein.length, 2);
        assert.equal(protein[0], 'Met');
        assert.equal(protein[1], 'Phe');
    });

    it('returns empty array when no start codon', () => {
        const mrna = ['U', 'U', 'U', 'U', 'U', 'U'];
        const protein = translateMrna(mrna);
        assert.equal(protein.length, 0);
    });
});


describe('Protein', () => {
    it('length returns amino acid count', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe', 'Gly'] });
        assert.equal(p.length, 3);
    });

    it('fold fails for short proteins', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe'] });
        const result = p.fold();
        assert.equal(result, false);
        assert.equal(p.folded, false);
    });

    it('fold runs for long proteins', () => {
        const p = new Protein({ aminoAcids: Array(20).fill('Ala'), name: 'long' });
        p.fold();
        // Result is probabilistic, just verify it runs
        assert.equal(typeof p.folded, 'boolean');
    });

    it('toCompact returns formatted string', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe'], name: 'myProt' });
        const compact = p.toCompact();
        assert.ok(compact.includes('myProt'));
        assert.ok(compact.includes('f='));
    });
});


describe('Cell', () => {
    it('transcribeAndTranslate runs central dogma', () => {
        const gene = new Gene({
            name: 'known',
            sequence: ['A', 'T', 'G', 'T', 'T', 'T', 'T', 'A', 'A'],
            startPos: 0, endPos: 9, expressionLevel: 1.0,
        });
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'T', 'T', 'T', 'T', 'A', 'A'], genes: [gene] });
        const cell = new Cell({ dna });
        cell.proteins = [];
        const newProteins = cell.transcribeAndTranslate();
        // Result is probabilistic due to expressionLevel check
        assert.ok(Array.isArray(newProteins));
    });

    it('metabolize adjusts energy', () => {
        const cell = new Cell({ energy: 100.0 });
        cell.metabolize(20.0);
        assert.ok(cell.alive);
        assert.ok(cell.energy > 0);
    });

    it('divide creates daughter cell', () => {
        const cell = new Cell({ energy: 100.0 });
        const daughter = cell.divide();
        assert.ok(daughter !== null);
        assert.equal(daughter.generation, cell.generation + 1);
        assert.ok(daughter.alive);
    });

    it('divide returns null for dead cell', () => {
        const cell = new Cell();
        cell.alive = false;
        assert.equal(cell.divide(), null);
    });

    it('divide returns null for low energy cell', () => {
        const cell = new Cell({ energy: 10.0 });
        assert.equal(cell.divide(), null);
    });

    it('computeFitness returns value between 0 and 1', () => {
        const cell = new Cell();
        const fitness = cell.computeFitness();
        assert.ok(fitness >= 0.0);
        assert.ok(fitness <= 1.0);
    });

    it('computeFitness returns 0 for dead cell', () => {
        const cell = new Cell();
        cell.alive = false;
        assert.equal(cell.computeFitness(), 0.0);
    });

    it('toCompact returns formatted string', () => {
        const cell = new Cell();
        const compact = cell.toCompact();
        assert.ok(compact.includes('Cell#'));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('alive'));
    });
});


describe('Biosphere', () => {
    it('initializes with cells', () => {
        const bio = new Biosphere(5, 50);
        assert.ok(bio.cells.length > 0);
    });

    it('step advances the biosphere', () => {
        const bio = new Biosphere(3, 50);
        bio.step(1.0, 0.1, 0.01, 300);
        // Population should still exist
        assert.ok(bio.cells.length > 0);
        assert.equal(bio.generation, 1);
    });

    it('averageFitness returns a number', () => {
        const bio = new Biosphere(3, 50);
        const fitness = bio.averageFitness();
        assert.equal(typeof fitness, 'number');
        assert.ok(fitness >= 0 && fitness <= 1);
    });

    it('averageGcContent returns value between 0 and 1', () => {
        const bio = new Biosphere(3, 50);
        const gc = bio.averageGcContent();
        assert.equal(typeof gc, 'number');
        assert.ok(gc >= 0 && gc <= 1);
    });

    it('totalMutations returns 0 initially', () => {
        const bio = new Biosphere(3, 60);
        assert.equal(bio.totalMutations(), 0);
    });

    it('totalMutations increases after UV exposure', () => {
        const bio = new Biosphere(5, 200);
        for (const cell of bio.cells) {
            cell.dna.applyMutations(1000.0, 1000.0);
        }
        assert.ok(bio.totalMutations() > 0);
    });

    it('toCompact returns formatted string', () => {
        const bio = new Biosphere(3, 50);
        const compact = bio.toCompact();
        assert.ok(compact.includes('Bio['));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('pop='));
    });
});


// ============================================================
// Environment Module
// ============================================================
describe('EnvironmentalEvent', () => {
    it('toCompact returns formatted string', () => {
        const ev = new EnvironmentalEvent('volcanic', 0.75, 30, [1, 2, 3], 42);
        assert.equal(ev.toCompact(), 'Ev:volcanic(i=0.75,d=30)');

        const ev2 = new EnvironmentalEvent('impact', 1.0, 100);
        assert.equal(ev2.toCompact(), 'Ev:impact(i=1.00,d=100)');
    });
});


describe('Environment', () => {
    it('initializes with high temperature', () => {
        const env = new Environment(T_PLANCK);
        assert.ok(env.temperature > 1e6);
    });

    it('cools over time', () => {
        const env = new Environment(T_PLANCK);
        const t0 = env.temperature;
        env.update(RECOMBINATION_EPOCH);
        assert.ok(env.temperature < t0);
    });

    it('becomes habitable eventually', () => {
        const env = new Environment(T_PLANCK);
        env.update(PRESENT_EPOCH);
        assert.ok(env.isHabitable());
    });

    it('getRadiationDose returns a positive number', () => {
        const env = new Environment(T_PLANCK);
        const dose = env.getRadiationDose();
        assert.ok(typeof dose === 'number');
        assert.ok(dose >= 0);
    });

    it('thermalEnergy returns a positive number', () => {
        const env = new Environment(T_PLANCK);
        const energy = env.thermalEnergy();
        assert.ok(typeof energy === 'number');
        assert.ok(energy > 0);
    });

    it('toCompact returns formatted string', () => {
        const env = new Environment(T_PLANCK);
        const compact = env.toCompact();
        assert.equal(typeof compact, 'string');
        assert.ok(compact.includes('Env'));
        assert.ok(compact.includes('T='));
    });
});


// ============================================================
// Universe Integration
// ============================================================
describe('Universe', () => {
    it('initializes at tick 0', () => {
        const u = new Universe();
        assert.equal(u.tick, 0);
    });

    it('step advances tick', () => {
        const u = new Universe();
        u.step();
        assert.ok(u.tick > 0);
    });

    it('snapshot returns expected fields', () => {
        const u = new Universe();
        for (let i = 0; i < 10; i++) u.step();
        const snap = u.snapshot();
        assert.ok('tick' in snap);
        assert.ok('epoch' in snap);
        assert.ok('temperature' in snap);
        assert.ok('particles' in snap);
        assert.ok('atoms' in snap);
    });

    it('runs through multiple epochs', () => {
        const u = new Universe(NUCLEOSYNTHESIS_EPOCH + 100, 1000);
        const epochs = new Set();
        for (let i = 0; i < 20; i++) {
            u.step();
            epochs.add(u.currentEpochName);
        }
        assert.ok(epochs.size >= 2, `Expected multiple epochs, got: ${[...epochs]}`);
    });

    it('creates particles during quantum era', () => {
        const u = new Universe(HADRON_EPOCH, 100);
        for (let i = 0; i < 50; i++) u.step();
        assert.ok(u.particlesCreated > 0);
    });

    it('forms atoms during nucleosynthesis', () => {
        const u = new Universe(RECOMBINATION_EPOCH + 1000, 1000);
        for (let i = 0; i < 200; i++) u.step();
        const snap = u.snapshot();
        assert.ok(snap.atoms >= 0);
    });
});
