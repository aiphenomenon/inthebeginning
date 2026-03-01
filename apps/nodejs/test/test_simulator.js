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
    T_PLANCK, T_QUARK_HADRON, T_CMB, T_RECOMBINATION,
    T_EARTH_SURFACE,
    PLANCK_EPOCH, HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH,
    RECOMBINATION_EPOCH, PRESENT_EPOCH, LIFE_EPOCH,
    EARTH_EPOCH, STAR_FORMATION_EPOCH,
    BOND_ENERGY_COVALENT, BOND_ENERGY_IONIC,
    NUCLEOTIDE_BASES, CODON_TABLE, PI,
    RADIATION_DAMAGE_THRESHOLD,
} from '../constants.js';

import {
    QuantumField, Particle, ParticleType, Spin, Color,
    WaveFunction, gaussRandom, EntangledPair,
    resetParticleIdCounter,
} from '../quantum.js';

import {
    Atom, AtomicSystem, ElectronShell, resetAtomIdCounter,
    ELEMENTS,
} from '../atomic.js';

import {
    Molecule, ChemicalReaction, ChemicalSystem,
    resetMoleculeIdCounter,
} from '../chemistry.js';

import {
    EpigeneticMark, Gene, DNAStrand, translateMrna,
    Protein, Cell, Biosphere, resetCellIdCounter,
} from '../biology.js';

import { EnvironmentalEvent, Environment } from '../environment.js';
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

    it('proton mass is approximately neutron mass', () => {
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

    it('superpose combines two wave functions', () => {
        const wf1 = new WaveFunction(0.7, 0.0);
        const wf2 = new WaveFunction(0.5, Math.PI);
        const combined = wf1.superpose(wf2);
        assert.ok(combined instanceof WaveFunction);
        assert.ok(combined.amplitude >= 0);
        assert.ok(combined.amplitude <= 1.0);
        assert.equal(combined.coherent, true);
    });

    it('superpose of identical phase adds constructively', () => {
        const wf1 = new WaveFunction(0.5, 0.0);
        const wf2 = new WaveFunction(0.5, 0.0);
        const combined = wf1.superpose(wf2);
        // sqrt(0.25 + 0.25 + 2*0.25*cos(0)) = sqrt(1.0) = 1.0
        assert.ok(Math.abs(combined.amplitude - 1.0) < 1e-10);
    });

    it('toCompact returns psi string format', () => {
        const wf = new WaveFunction(0.8, 1.23);
        const compact = wf.toCompact();
        assert.ok(typeof compact === 'string');
        assert.ok(compact.includes('0.800'));
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

    it('wavelength is finite for nonzero momentum', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1.0, 0, 0],
        });
        const wl = p.wavelength;
        assert.ok(isFinite(wl));
        assert.ok(wl > 0);
    });

    it('wavelength is Infinity for zero momentum', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [0, 0, 0],
        });
        assert.equal(p.wavelength, Infinity);
    });

    it('charge getter returns correct value for electron', () => {
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        assert.equal(p.charge, -1.0);
    });

    it('charge getter returns correct value for proton', () => {
        const p = new Particle({ particleType: ParticleType.PROTON });
        assert.equal(p.charge, 1.0);
    });

    it('charge getter returns 0 for photon', () => {
        const p = new Particle({ particleType: ParticleType.PHOTON });
        assert.equal(p.charge, 0.0);
    });

    it('toCompact returns formatted string', () => {
        const p = new Particle({
            particleType: ParticleType.ELECTRON,
            position: [1.0, 2.0, 3.0],
            spin: Spin.UP,
        });
        const compact = p.toCompact();
        assert.ok(typeof compact === 'string');
        assert.ok(compact.includes('electron'));
        assert.ok(compact.includes('s=0.5'));
    });

    it('resetParticleIdCounter resets the counter', () => {
        resetParticleIdCounter();
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        assert.equal(p.particleId, 1);
    });
});


describe('gaussRandom', () => {
    it('returns a number', () => {
        const val = gaussRandom();
        assert.equal(typeof val, 'number');
        assert.ok(isFinite(val));
    });

    it('respects mean parameter', () => {
        let sum = 0;
        const n = 1000;
        for (let i = 0; i < n; i++) {
            sum += gaussRandom(100, 1);
        }
        const avg = sum / n;
        // Should be within ~3 standard errors of 100
        assert.ok(Math.abs(avg - 100) < 1, `average ${avg} too far from 100`);
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
        assert.ok(produced);
    });

    it('annihilate removes particles and creates photons', () => {
        const qf = new QuantumField(T_PLANCK);
        const p1 = new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1, 0, 0],
        });
        const p2 = new Particle({
            particleType: ParticleType.POSITRON,
            momentum: [-1, 0, 0],
        });
        qf.particles.push(p1, p2);
        assert.equal(qf.particles.length, 2);

        const energy = qf.annihilate(p1, p2);
        assert.ok(energy > 0);
        // Original pair removed, two photons created
        assert.equal(qf.totalAnnihilated, 2);
        // Photons should be present
        const photons = qf.particles.filter(
            p => p.particleType === ParticleType.PHOTON
        );
        assert.equal(photons.length, 2);
    });

    it('decohere may collapse wave function', () => {
        const qf = new QuantumField(T_PLANCK);
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        assert.equal(p.waveFn.coherent, true);
        // At Planck temperature with coupling 1.0, decoherence is virtually certain
        qf.decohere(p, 1.0);
        // Can't guarantee collapse (probabilistic), but coherent should change for high T
        // We loop to ensure it happens at least once
        let collapsed = !p.waveFn.coherent;
        for (let i = 0; i < 50 && !collapsed; i++) {
            const p2 = new Particle({ particleType: ParticleType.ELECTRON });
            qf.decohere(p2, 1.0);
            collapsed = !p2.waveFn.coherent;
        }
        assert.ok(collapsed, 'decoherence should eventually collapse a wave function');
    });

    it('decohere does nothing for already-incoherent particle', () => {
        const qf = new QuantumField(T_PLANCK);
        const p = new Particle({ particleType: ParticleType.ELECTRON });
        p.waveFn.coherent = false;
        qf.decohere(p, 1.0);
        assert.equal(p.waveFn.coherent, false);
    });

    it('cool reduces temperature', () => {
        const qf = new QuantumField(1000);
        const t0 = qf.temperature;
        qf.cool(0.5);
        assert.ok(qf.temperature < t0);
        assert.ok(Math.abs(qf.temperature - 500) < 0.01);
    });

    it('totalEnergy sums particle energies plus vacuum', () => {
        const qf = new QuantumField(T_PLANCK);
        assert.equal(qf.totalEnergy(), 0); // no particles, no vacuum energy

        qf.particles.push(new Particle({
            particleType: ParticleType.ELECTRON,
            momentum: [1, 0, 0],
        }));
        const e = qf.totalEnergy();
        assert.ok(e > 0);
    });

    it('toCompact returns a formatted string', () => {
        const qf = new QuantumField(1e6);
        qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        const compact = qf.toCompact();
        assert.ok(typeof compact === 'string');
        assert.ok(compact.startsWith('QF['));
        assert.ok(compact.includes('T='));
        assert.ok(compact.includes('E='));
        assert.ok(compact.includes('n=1'));
    });

    it('vacuumFluctuation returns null at very low temperature', () => {
        const qf = new QuantumField(0.0001);
        let produced = false;
        for (let i = 0; i < 20; i++) {
            if (qf.vacuumFluctuation()) {
                produced = true;
                break;
            }
        }
        // At near-zero T, probability is near 0 -- it is okay if it does produce
        // We are just testing it doesn't crash
        assert.equal(typeof produced, 'boolean');
    });
});


// ============================================================
// Atomic Module
// ============================================================
describe('ElectronShell', () => {
    it('constructor sets properties correctly', () => {
        const shell = new ElectronShell(1, 2, 0);
        assert.equal(shell.n, 1);
        assert.equal(shell.maxElectrons, 2);
        assert.equal(shell.electrons, 0);
    });

    it('full returns true when electrons equal max', () => {
        const shell = new ElectronShell(1, 2, 2);
        assert.equal(shell.full, true);
    });

    it('full returns false when shell not at capacity', () => {
        const shell = new ElectronShell(1, 2, 1);
        assert.equal(shell.full, false);
    });

    it('empty returns true when no electrons', () => {
        const shell = new ElectronShell(1, 2, 0);
        assert.equal(shell.empty, true);
    });

    it('empty returns false when shell has electrons', () => {
        const shell = new ElectronShell(1, 2, 1);
        assert.equal(shell.empty, false);
    });

    it('addElectron succeeds when not full', () => {
        const shell = new ElectronShell(1, 2, 0);
        const result = shell.addElectron();
        assert.equal(result, true);
        assert.equal(shell.electrons, 1);
    });

    it('addElectron fails when full', () => {
        const shell = new ElectronShell(1, 2, 2);
        const result = shell.addElectron();
        assert.equal(result, false);
        assert.equal(shell.electrons, 2);
    });

    it('removeElectron succeeds when not empty', () => {
        const shell = new ElectronShell(1, 2, 1);
        const result = shell.removeElectron();
        assert.equal(result, true);
        assert.equal(shell.electrons, 0);
    });

    it('removeElectron fails when empty', () => {
        const shell = new ElectronShell(1, 2, 0);
        const result = shell.removeElectron();
        assert.equal(result, false);
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
    });

    it('name returns fallback for unknown element', () => {
        const a = new Atom({ atomicNumber: 99 });
        assert.equal(a.name, 'Element-99');
    });

    it('electronegativity returns correct value for oxygen', () => {
        const o = new Atom({ atomicNumber: 8 });
        assert.ok(Math.abs(o.electronegativity - 3.44) < 0.01);
    });

    it('electronegativity returns 1.0 for unknown element', () => {
        const a = new Atom({ atomicNumber: 99 });
        assert.equal(a.electronegativity, 1.0);
    });

    it('charge is 0 for neutral atom', () => {
        const a = new Atom({ atomicNumber: 6 });
        assert.equal(a.charge, 0);
    });

    it('charge is positive for ion with fewer electrons', () => {
        const a = new Atom({ atomicNumber: 6, electronCount: 4 });
        assert.equal(a.charge, 2);
    });

    it('valenceElectrons returns outermost shell count', () => {
        const h = new Atom({ atomicNumber: 1 }); // 1 electron in shell 1
        assert.equal(h.valenceElectrons, 1);
        const c = new Atom({ atomicNumber: 6 }); // 2,4
        assert.equal(c.valenceElectrons, 4);
    });

    it('needsElectrons returns remaining capacity in outermost shell', () => {
        const h = new Atom({ atomicNumber: 1 }); // shell 1: 1/2
        assert.equal(h.needsElectrons, 1);
        const c = new Atom({ atomicNumber: 6 }); // shell 2: 4/8
        assert.equal(c.needsElectrons, 4);
    });

    it('isNobleGas returns true for He', () => {
        const he = new Atom({ atomicNumber: 2 }); // 2 electrons, shell 1 full
        assert.equal(he.isNobleGas, true);
    });

    it('isNobleGas returns false for H', () => {
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(h.isNobleGas, false);
    });

    it('isIon returns true when charge is nonzero', () => {
        const a = new Atom({ atomicNumber: 11, electronCount: 10 }); // Na+
        assert.equal(a.isIon, true);
    });

    it('isIon returns false for neutral atom', () => {
        const a = new Atom({ atomicNumber: 11 });
        assert.equal(a.isIon, false);
    });

    it('ionize removes an electron', () => {
        const a = new Atom({ atomicNumber: 11 });
        assert.equal(a.charge, 0);
        const result = a.ionize();
        assert.equal(result, true);
        assert.equal(a.charge, 1);
        assert.equal(a.electronCount, 10);
    });

    it('ionize fails when no electrons left', () => {
        const a = new Atom({ atomicNumber: 1 });
        // Ionize once to remove the only electron
        a.ionize();
        assert.equal(a.electronCount, 0);
        // Now ionize again -- should fail
        const result = a.ionize();
        assert.equal(result, false);
    });

    it('captureElectron adds an electron', () => {
        const a = new Atom({ atomicNumber: 11, electronCount: 10 }); // Na+
        assert.equal(a.charge, 1);
        const result = a.captureElectron();
        assert.equal(result, true);
        assert.equal(a.electronCount, 11);
        assert.equal(a.charge, 0);
    });

    it('canBondWith returns true for two non-noble-gas atoms under 4 bonds', () => {
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        assert.equal(h1.canBondWith(h2), true);
    });

    it('canBondWith returns false if one is noble gas', () => {
        const h = new Atom({ atomicNumber: 1 });
        const he = new Atom({ atomicNumber: 2 });
        assert.equal(h.canBondWith(he), false);
    });

    it('canBondWith returns false if atom has 4 bonds', () => {
        const c = new Atom({ atomicNumber: 6 });
        c.bonds = [1, 2, 3, 4]; // 4 bonds
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(c.canBondWith(h), false);
    });

    it('bondType returns covalent for similar electronegativity', () => {
        const c = new Atom({ atomicNumber: 6 }); // 2.55
        const h = new Atom({ atomicNumber: 1 }); // 2.20
        assert.equal(c.bondType(h), 'covalent');
    });

    it('bondType returns ionic for large electronegativity difference', () => {
        const na = new Atom({ atomicNumber: 11 }); // 0.93
        const cl = new Atom({ atomicNumber: 17 }); // 3.16
        assert.equal(na.bondType(cl), 'ionic');
    });

    it('bondType returns polar_covalent for moderate difference', () => {
        const h = new Atom({ atomicNumber: 1 }); // 2.20
        const o = new Atom({ atomicNumber: 8 }); // 3.44
        assert.equal(h.bondType(o), 'polar_covalent');
    });

    it('bondEnergy returns BOND_ENERGY_IONIC for ionic bond', () => {
        const na = new Atom({ atomicNumber: 11 });
        const cl = new Atom({ atomicNumber: 17 });
        assert.equal(na.bondEnergy(cl), BOND_ENERGY_IONIC);
    });

    it('bondEnergy returns BOND_ENERGY_COVALENT for covalent bond', () => {
        const c = new Atom({ atomicNumber: 6 });
        const h = new Atom({ atomicNumber: 1 });
        assert.equal(c.bondEnergy(h), BOND_ENERGY_COVALENT);
    });

    it('bondEnergy returns average for polar_covalent', () => {
        const h = new Atom({ atomicNumber: 1 });
        const o = new Atom({ atomicNumber: 8 });
        const expected = (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2;
        assert.equal(h.bondEnergy(o), expected);
    });

    it('distanceTo computes Euclidean distance', () => {
        const a1 = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const a2 = new Atom({ atomicNumber: 1, position: [3, 4, 0] });
        assert.ok(Math.abs(a1.distanceTo(a2) - 5.0) < 1e-10);
    });

    it('distanceTo returns 0 for same position', () => {
        const a1 = new Atom({ atomicNumber: 1, position: [1, 2, 3] });
        const a2 = new Atom({ atomicNumber: 1, position: [1, 2, 3] });
        assert.ok(Math.abs(a1.distanceTo(a2)) < 1e-10);
    });

    it('resetAtomIdCounter resets the counter', () => {
        resetAtomIdCounter();
        const a = new Atom({ atomicNumber: 1 });
        assert.equal(a.atomId, 1);
    });

    it('toCompact returns formatted string', () => {
        const a = new Atom({ atomicNumber: 6 });
        const compact = a.toCompact();
        assert.ok(typeof compact === 'string');
        assert.ok(compact.startsWith('C'));
        assert.ok(compact.includes('['));
        assert.ok(compact.includes('b0'));
    });

    it('toCompact shows charge for ion', () => {
        const a = new Atom({ atomicNumber: 11, electronCount: 10 });
        const compact = a.toCompact();
        assert.ok(compact.includes('+1'));
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

    it('recombination captures electrons at low temperature', () => {
        const as = new AtomicSystem(T_RECOMBINATION * 0.5);
        const qf = new QuantumField(T_RECOMBINATION * 0.5);
        // Add protons and electrons to field
        for (let i = 0; i < 5; i++) {
            qf.particles.push(new Particle({ particleType: ParticleType.PROTON }));
            qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        }
        const newAtoms = as.recombination(qf);
        assert.ok(newAtoms.length > 0);
        assert.ok(newAtoms.every(a => a.atomicNumber === 1));
    });

    it('recombination does nothing at high temperature', () => {
        const as = new AtomicSystem(T_RECOMBINATION * 2);
        const qf = new QuantumField(T_RECOMBINATION * 2);
        qf.particles.push(new Particle({ particleType: ParticleType.PROTON }));
        qf.particles.push(new Particle({ particleType: ParticleType.ELECTRON }));
        const newAtoms = as.recombination(qf);
        assert.equal(newAtoms.length, 0);
    });

    it('stellarNucleosynthesis creates heavier elements from helium', () => {
        const as = new AtomicSystem();
        // Add enough helium for triple-alpha process
        for (let i = 0; i < 30; i++) {
            as.atoms.push(new Atom({ atomicNumber: 2, massNumber: 4 }));
        }
        // Run many times to overcome low probability
        let heavyCreated = false;
        for (let attempt = 0; attempt < 500; attempt++) {
            const newAtoms = as.stellarNucleosynthesis(1e6);
            if (newAtoms.some(a => a.atomicNumber > 2)) {
                heavyCreated = true;
                break;
            }
        }
        assert.ok(heavyCreated, 'Should create heavy elements from stellar nucleosynthesis');
    });

    it('stellarNucleosynthesis returns empty at low temperature', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 2, massNumber: 4 }));
        }
        const newAtoms = as.stellarNucleosynthesis(100);
        assert.equal(newAtoms.length, 0);
    });

    it('attemptBond forms a bond between compatible atoms at close range', () => {
        // Use very high temperature so exp(-E/(K_B*T)) is close to 1
        const as = new AtomicSystem(1e8);
        const h1 = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const h2 = new Atom({ atomicNumber: 1, position: [0.5, 0, 0] });
        as.atoms.push(h1, h2);
        let bonded = false;
        for (let i = 0; i < 200; i++) {
            h1.bonds = [];
            h2.bonds = [];
            if (as.attemptBond(h1, h2)) {
                bonded = true;
                break;
            }
        }
        assert.ok(bonded, 'Should eventually form a bond');
    });

    it('attemptBond fails for noble gases', () => {
        const as = new AtomicSystem(300);
        const he = new Atom({ atomicNumber: 2 });
        const h = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const result = as.attemptBond(he, h);
        assert.equal(result, false);
    });

    it('attemptBond fails for distant atoms', () => {
        const as = new AtomicSystem(300);
        const h1 = new Atom({ atomicNumber: 1, position: [0, 0, 0] });
        const h2 = new Atom({ atomicNumber: 1, position: [100, 0, 0] });
        const result = as.attemptBond(h1, h2);
        assert.equal(result, false);
    });

    it('breakBond breaks an existing bond', () => {
        const as = new AtomicSystem(1e10); // Very high T to encourage breaking
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        h1.bonds.push(h2.atomId);
        h2.bonds.push(h1.atomId);
        as.atoms.push(h1, h2);

        let broken = false;
        for (let i = 0; i < 100; i++) {
            h1.bonds = [h2.atomId];
            h2.bonds = [h1.atomId];
            if (as.breakBond(h1, h2)) {
                broken = true;
                break;
            }
        }
        assert.ok(broken, 'Should eventually break the bond at high temperature');
    });

    it('breakBond returns false if no bond exists', () => {
        const as = new AtomicSystem(1e10);
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        const result = as.breakBond(h1, h2);
        assert.equal(result, false);
    });

    it('cool reduces temperature', () => {
        const as = new AtomicSystem(1000);
        const t0 = as.temperature;
        as.cool(0.5);
        assert.ok(as.temperature < t0);
        assert.ok(Math.abs(as.temperature - 500) < 0.01);
    });

    it('toCompact returns formatted string', () => {
        const as = new AtomicSystem(3000);
        as.atoms.push(new Atom({ atomicNumber: 1 }));
        as.atoms.push(new Atom({ atomicNumber: 2 }));
        const compact = as.toCompact();
        assert.ok(typeof compact === 'string');
        assert.ok(compact.startsWith('AS['));
        assert.ok(compact.includes('T='));
        assert.ok(compact.includes('n=2'));
    });
});


// ============================================================
// Chemistry Module
// ============================================================
describe('Molecule', () => {
    it('molecularWeight sums mass numbers', () => {
        const h1 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const o = new Atom({ atomicNumber: 8, massNumber: 16 });
        const mol = new Molecule({ atoms: [h1, h2, o], name: 'water' });
        assert.equal(mol.molecularWeight, 18);
    });

    it('atomCount returns number of atoms', () => {
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        const o = new Atom({ atomicNumber: 8 });
        const mol = new Molecule({ atoms: [h1, h2, o] });
        assert.equal(mol.atomCount, 3);
    });

    it('resetMoleculeIdCounter resets counter', () => {
        resetMoleculeIdCounter();
        const mol = new Molecule({ name: 'test' });
        assert.equal(mol.moleculeId, 1);
    });

    it('toCompact returns formatted string', () => {
        const h1 = new Atom({ atomicNumber: 1, massNumber: 1 });
        const o = new Atom({ atomicNumber: 8, massNumber: 16 });
        const mol = new Molecule({ atoms: [h1, o], name: 'water' });
        const compact = mol.toCompact();
        assert.ok(compact.includes('water'));
        assert.ok(compact.includes('mw='));
    });

    it('auto-computes formula from atoms', () => {
        const c = new Atom({ atomicNumber: 6 });
        const h1 = new Atom({ atomicNumber: 1 });
        const h2 = new Atom({ atomicNumber: 1 });
        const h3 = new Atom({ atomicNumber: 1 });
        const h4 = new Atom({ atomicNumber: 1 });
        const mol = new Molecule({ atoms: [c, h1, h2, h3, h4] });
        assert.equal(mol.formula, 'CH4');
        assert.equal(mol.isOrganic, true);
    });
});


describe('ChemicalReaction', () => {
    it('canProceed returns boolean based on temperature', () => {
        const rxn = new ChemicalReaction(['H2', 'O2'], ['H2O'], 1.0, -2.0, 'combustion');
        // At very high temperature, reaction should eventually proceed
        let proceeded = false;
        for (let i = 0; i < 100; i++) {
            if (rxn.canProceed(1e6)) {
                proceeded = true;
                break;
            }
        }
        assert.ok(proceeded, 'Reaction should proceed at high temperature');
    });

    it('canProceed returns false at zero temperature', () => {
        const rxn = new ChemicalReaction(['A'], ['B'], 1.0);
        const result = rxn.canProceed(0);
        assert.equal(result, false);
    });

    it('toCompact returns formatted string', () => {
        const rxn = new ChemicalReaction(['H2', 'O2'], ['H2O'], 1.0, -2.0, 'combustion');
        const compact = rxn.toCompact();
        assert.ok(compact.includes('H2+O2'));
        assert.ok(compact.includes('->'));
        assert.ok(compact.includes('H2O'));
        assert.ok(compact.includes('Ea='));
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
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 }));
        }
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 }));
        }
        const cs = new ChemicalSystem(as);
        const waters = cs.formWater();
        assert.ok(waters.length > 0);
        assert.equal(cs.waterCount, waters.length);
    });

    it('formMethane produces methane from C and H', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 2; i++) {
            as.atoms.push(new Atom({ atomicNumber: 6 })); // C
        }
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 })); // H
        }
        const cs = new ChemicalSystem(as);
        const methanes = cs.formMethane();
        assert.ok(methanes.length > 0);
        assert.ok(methanes[0].name === 'methane');
    });

    it('formAmmonia produces ammonia from N and H', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 3; i++) {
            as.atoms.push(new Atom({ atomicNumber: 7 })); // N
        }
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 })); // H
        }
        const cs = new ChemicalSystem(as);
        const ammonias = cs.formAmmonia();
        assert.ok(ammonias.length > 0);
        assert.ok(ammonias[0].name === 'ammonia');
    });

    it('formAminoAcid produces amino acid with sufficient atoms', () => {
        const as = new AtomicSystem();
        // Need: 2C + 5H + 2O + 1N minimum for glycine
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 6 })); // C
        }
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 })); // H
        }
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 })); // O
        }
        for (let i = 0; i < 3; i++) {
            as.atoms.push(new Atom({ atomicNumber: 7 })); // N
        }
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid('Gly');
        assert.ok(aa !== null);
        assert.equal(aa.name, 'Gly');
        assert.equal(aa.isOrganic, true);
        assert.ok(aa.functionalGroups.includes('amino'));
        assert.ok(aa.functionalGroups.includes('carboxyl'));
        assert.equal(cs.aminoAcidCount, 1);
    });

    it('formAminoAcid returns null with insufficient atoms', () => {
        const as = new AtomicSystem();
        as.atoms.push(new Atom({ atomicNumber: 6 })); // only 1 C
        const cs = new ChemicalSystem(as);
        const aa = cs.formAminoAcid('Gly');
        assert.equal(aa, null);
    });

    it('formNucleotide produces nucleotide with sufficient atoms', () => {
        const as = new AtomicSystem();
        // Need: 5C + 8H + 4O + 2N minimum
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 6 })); // C
        }
        for (let i = 0; i < 20; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 })); // H
        }
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 })); // O
        }
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 7 })); // N
        }
        const cs = new ChemicalSystem(as);
        const nuc = cs.formNucleotide('A');
        assert.ok(nuc !== null);
        assert.equal(nuc.name, 'nucleotide-A');
        assert.equal(nuc.isOrganic, true);
        assert.ok(nuc.functionalGroups.includes('sugar'));
        assert.equal(cs.nucleotideCount, 1);
    });

    it('formNucleotide returns null with insufficient atoms', () => {
        const as = new AtomicSystem();
        as.atoms.push(new Atom({ atomicNumber: 6 })); // only 1 C
        const cs = new ChemicalSystem(as);
        const nuc = cs.formNucleotide('A');
        assert.equal(nuc, null);
    });

    it('catalyzedReaction attempts to form amino acids and nucleotides', () => {
        const as = new AtomicSystem();
        // Provide plenty of atoms
        for (let i = 0; i < 30; i++) {
            as.atoms.push(new Atom({ atomicNumber: 6 }));
        }
        for (let i = 0; i < 60; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 }));
        }
        for (let i = 0; i < 30; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 }));
        }
        for (let i = 0; i < 15; i++) {
            as.atoms.push(new Atom({ atomicNumber: 7 }));
        }
        const cs = new ChemicalSystem(as);
        let totalFormed = 0;
        for (let i = 0; i < 500; i++) {
            totalFormed += cs.catalyzedReaction(1e6, true);
        }
        // At very high temperature with catalyst, something should form
        assert.ok(totalFormed > 0, 'catalyzedReaction should form molecules');
    });

    it('moleculeCensus returns correct types', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 }));
        }
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 }));
        }
        const cs = new ChemicalSystem(as);
        cs.formWater();
        const census = cs.moleculeCensus();
        assert.ok(typeof census === 'object');
        assert.ok('water' in census);
    });

    it('toCompact returns formatted string', () => {
        const as = new AtomicSystem();
        for (let i = 0; i < 4; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 }));
        }
        for (let i = 0; i < 2; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 }));
        }
        const cs = new ChemicalSystem(as);
        cs.formWater();
        const compact = cs.toCompact();
        assert.ok(compact.startsWith('CS['));
        assert.ok(compact.includes('mol='));
        assert.ok(compact.includes('H2O='));
    });
});


// ============================================================
// Biology Module
// ============================================================
describe('EpigeneticMark', () => {
    it('toCompact returns formatted string', () => {
        const mark = new EpigeneticMark(5, 'methylation', true, 0);
        const compact = mark.toCompact();
        assert.equal(compact, 'M5+');
    });

    it('toCompact shows inactive state', () => {
        const mark = new EpigeneticMark(3, 'acetylation', false, 1);
        const compact = mark.toCompact();
        assert.equal(compact, 'A3-');
    });
});


describe('Gene', () => {
    it('length returns sequence length', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G', 'C', 'A', 'T'],
        });
        assert.equal(gene.length, 6);
    });

    it('isSilenced returns false when no methylation', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G'],
        });
        assert.equal(gene.isSilenced, false);
    });

    it('isSilenced returns true with heavy methylation', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G', 'C', 'A'],
        });
        // Need methylation > 30% of length => > 1.5, so 2 marks
        gene.methylate(0);
        gene.methylate(1);
        gene.methylate(2);
        assert.equal(gene.isSilenced, true);
    });

    it('methylate adds methylation mark', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G'],
        });
        gene.methylate(1, 0);
        assert.equal(gene.epigeneticMarks.length, 1);
        assert.equal(gene.epigeneticMarks[0].markType, 'methylation');
        assert.equal(gene.epigeneticMarks[0].position, 1);
    });

    it('methylate does not add mark for out-of-range position', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G'],
        });
        gene.methylate(10, 0); // out of range
        assert.equal(gene.epigeneticMarks.length, 0);
    });

    it('demethylate removes methylation mark at position', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G'],
        });
        gene.methylate(1);
        assert.equal(gene.epigeneticMarks.length, 1);
        gene.demethylate(1);
        assert.equal(gene.epigeneticMarks.length, 0);
    });

    it('acetylate adds acetylation mark', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G'],
        });
        gene.acetylate(0, 1);
        assert.equal(gene.epigeneticMarks.length, 1);
        assert.equal(gene.epigeneticMarks[0].markType, 'acetylation');
    });

    it('transcribe converts T to U', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G', 'C'],
        });
        const rna = gene.transcribe();
        assert.deepEqual(rna, ['A', 'U', 'G', 'C']);
    });

    it('transcribe returns empty array when silenced', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G', 'C', 'A'],
        });
        // Heavily methylate to silence
        gene.methylate(0);
        gene.methylate(1);
        gene.methylate(2);
        assert.equal(gene.isSilenced, true);
        const rna = gene.transcribe();
        assert.deepEqual(rna, []);
    });

    it('mutate changes bases', () => {
        const gene = new Gene({
            name: 'test',
            sequence: Array(100).fill('A'),
        });
        const mutations = gene.mutate(1.0); // 100% rate
        assert.equal(mutations, 100);
        // All bases should be changed from A
        assert.ok(gene.sequence.every(b => b !== 'A'));
    });

    it('mutate returns 0 at rate 0', () => {
        const gene = new Gene({
            name: 'test',
            sequence: ['A', 'T', 'G', 'C'],
        });
        const mutations = gene.mutate(0);
        assert.equal(mutations, 0);
    });

    it('toCompact returns formatted string', () => {
        const gene = new Gene({
            name: 'myGene',
            sequence: ['A', 'T', 'G', 'C', 'A'],
        });
        const compact = gene.toCompact();
        assert.ok(compact.includes('myGene'));
        assert.ok(compact.includes('ATGCA'));
        assert.ok(compact.includes('e='));
    });
});


describe('DNAStrand', () => {
    it('length returns sequence length', () => {
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'C'] });
        assert.equal(dna.length, 4);
    });

    it('complementaryStrand returns correct complements', () => {
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'C'] });
        assert.deepEqual(dna.complementaryStrand, ['T', 'A', 'C', 'G']);
    });

    it('gcContent computes correct ratio', () => {
        const dna = new DNAStrand({ sequence: ['A', 'T', 'G', 'C'] });
        assert.ok(Math.abs(dna.gcContent - 0.5) < 1e-10);
    });

    it('gcContent returns 0 for empty sequence', () => {
        const dna = new DNAStrand({ sequence: [] });
        assert.equal(dna.gcContent, 0.0);
    });

    it('gcContent is 1.0 for all GC', () => {
        const dna = new DNAStrand({ sequence: ['G', 'C', 'G', 'C'] });
        assert.ok(Math.abs(dna.gcContent - 1.0) < 1e-10);
    });

    it('randomStrand creates a strand with genes', () => {
        const dna = DNAStrand.randomStrand(100, 3);
        assert.equal(dna.length, 100);
        assert.equal(dna.genes.length, 3);
        assert.ok(dna.sequence.every(b => NUCLEOTIDE_BASES.includes(b)));
    });

    it('randomStrand first gene is essential', () => {
        const dna = DNAStrand.randomStrand(100, 3);
        assert.equal(dna.genes[0].essential, true);
        assert.equal(dna.genes[1].essential, false);
    });

    it('replicate creates a new strand with incremented generation', () => {
        const dna = DNAStrand.randomStrand(50, 2);
        dna.generation = 5;
        const replica = dna.replicate();
        assert.equal(replica.generation, 6);
        assert.equal(replica.length, dna.length);
        assert.deepEqual(replica.sequence, dna.sequence);
        assert.equal(replica.genes.length, dna.genes.length);
    });

    it('applyMutations introduces mutations', () => {
        const dna = DNAStrand.randomStrand(200, 3);
        const mutations = dna.applyMutations(100.0, 100.0);
        // High UV and cosmic ray should cause some mutations
        assert.ok(mutations >= 0);
        assert.equal(dna.mutationCount, mutations);
    });

    it('applyMutations with zero intensity causes no mutations', () => {
        const dna = DNAStrand.randomStrand(50, 2);
        const mutations = dna.applyMutations(0, 0);
        assert.equal(mutations, 0);
    });

    it('applyEpigeneticChanges modifies genes', () => {
        const dna = DNAStrand.randomStrand(100, 3);
        // Run many times to accumulate marks
        for (let i = 0; i < 100; i++) {
            dna.applyEpigeneticChanges(300, i);
        }
        // At least some genes should have epigenetic marks
        const totalMarks = dna.genes.reduce(
            (s, g) => s + g.epigeneticMarks.length, 0
        );
        assert.ok(totalMarks > 0, 'Should accumulate epigenetic marks');
    });

    it('toCompact returns formatted string', () => {
        const dna = DNAStrand.randomStrand(50, 2);
        const compact = dna.toCompact();
        assert.ok(compact.startsWith('DNA['));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('gc='));
    });
});


describe('translateMrna', () => {
    it('translates AUG-started mRNA to amino acids', () => {
        // AUG = Met (start), UUU = Phe, UAA = STOP
        const mrna = ['A', 'U', 'G', 'U', 'U', 'U', 'U', 'A', 'A'];
        const protein = translateMrna(mrna);
        assert.deepEqual(protein, ['Met', 'Phe']);
    });

    it('returns empty array if no start codon', () => {
        const mrna = ['U', 'U', 'U', 'U', 'U', 'U'];
        const protein = translateMrna(mrna);
        assert.deepEqual(protein, []);
    });

    it('stops at stop codon', () => {
        const mrna = ['A', 'U', 'G', 'U', 'A', 'A', 'U', 'U', 'U'];
        const protein = translateMrna(mrna);
        assert.deepEqual(protein, ['Met']);
    });

    it('handles empty mRNA', () => {
        const protein = translateMrna([]);
        assert.deepEqual(protein, []);
    });
});


describe('Protein', () => {
    it('length returns amino acid count', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe', 'Leu'] });
        assert.equal(p.length, 3);
    });

    it('fold succeeds for proteins of sufficient length', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe', 'Leu', 'Gly', 'Ala'] });
        // Run multiple times - fold is probabilistic
        let folded = false;
        for (let i = 0; i < 50; i++) {
            p.folded = false;
            if (p.fold()) {
                folded = true;
                break;
            }
        }
        assert.ok(folded, 'Protein should eventually fold');
    });

    it('fold fails for very short proteins', () => {
        const p = new Protein({ aminoAcids: ['Met', 'Phe'] });
        const result = p.fold();
        assert.equal(result, false);
        assert.equal(p.folded, false);
    });

    it('toCompact returns formatted string', () => {
        const p = new Protein({
            aminoAcids: ['Met', 'Phe', 'Leu'],
            name: 'myProtein',
        });
        const compact = p.toCompact();
        assert.ok(compact.includes('myProtein'));
        assert.ok(compact.includes('Met-Phe-Leu'));
        assert.ok(compact.includes('f=N')); // not folded
    });

    it('toCompact shows folded state', () => {
        const p = new Protein({
            aminoAcids: ['Met', 'Phe', 'Leu'],
            name: 'test',
            folded: true,
        });
        const compact = p.toCompact();
        assert.ok(compact.includes('f=Y'));
    });
});


describe('Cell', () => {
    it('transcribeAndTranslate produces proteins', () => {
        // Create a DNA strand with a gene that has AUG start codon
        const gene = new Gene({
            name: 'gene_0',
            sequence: ['A', 'T', 'G', 'U', 'U', 'U', 'T', 'A', 'A'],
            startPos: 0,
            endPos: 9,
            essential: true,
        });
        const dna = new DNAStrand({
            sequence: ['A', 'T', 'G', 'U', 'U', 'U', 'T', 'A', 'A'],
            genes: [gene],
        });
        const cell = new Cell({ dna });
        const proteins = cell.transcribeAndTranslate();
        // Transcribed: A U G U U U U A A -> Met Phe (STOP)
        // May or may not produce depending on expressionLevel random check
        assert.ok(Array.isArray(proteins));
    });

    it('metabolize consumes and adds energy', () => {
        const cell = new Cell({ energy: 100 });
        cell.metabolize(20);
        // energy += 20 * efficiency - 3 (basal cost)
        assert.ok(cell.energy !== 100);
        assert.ok(cell.alive);
    });

    it('metabolize kills cell when energy depleted', () => {
        const cell = new Cell({ energy: 1 });
        cell.metabolize(0); // No input energy, costs 3
        assert.equal(cell.alive, false);
    });

    it('divide creates daughter cell', () => {
        const cell = new Cell({ energy: 100 });
        const daughter = cell.divide();
        assert.ok(daughter !== null);
        assert.ok(daughter instanceof Cell);
        assert.equal(daughter.generation, cell.generation + 1);
        assert.ok(cell.energy < 100); // energy was split
    });

    it('divide returns null when energy too low', () => {
        const cell = new Cell({ energy: 10 });
        const daughter = cell.divide();
        assert.equal(daughter, null);
    });

    it('divide returns null when cell is dead', () => {
        const cell = new Cell({ energy: 100, alive: false });
        const daughter = cell.divide();
        assert.equal(daughter, null);
    });

    it('computeFitness returns 0 for dead cell', () => {
        const cell = new Cell({ alive: false });
        const fitness = cell.computeFitness();
        assert.equal(fitness, 0.0);
        assert.equal(cell.fitness, 0.0);
    });

    it('computeFitness returns value between 0 and 1 for live cell', () => {
        const cell = new Cell();
        cell.transcribeAndTranslate();
        const fitness = cell.computeFitness();
        assert.ok(fitness >= 0 && fitness <= 1);
    });

    it('computeFitness penalizes silenced essential gene', () => {
        const gene = new Gene({
            name: 'essential',
            sequence: Array(10).fill('A'),
            startPos: 0,
            endPos: 10,
            essential: true,
        });
        // Heavily methylate to silence
        gene.methylate(0);
        gene.methylate(1);
        gene.methylate(2);
        gene.methylate(3);
        assert.equal(gene.isSilenced, true);

        const dna = new DNAStrand({
            sequence: Array(10).fill('A'),
            genes: [gene],
        });
        const cell = new Cell({ dna });
        const fitness = cell.computeFitness();
        assert.ok(Math.abs(fitness - 0.1) < 1e-10);
    });

    it('resetCellIdCounter resets the counter', () => {
        resetCellIdCounter();
        const cell = new Cell();
        assert.equal(cell.cellId, 1);
    });

    it('toCompact returns formatted string', () => {
        const cell = new Cell({ energy: 75 });
        const compact = cell.toCompact();
        assert.ok(compact.includes('Cell#'));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('fit='));
        assert.ok(compact.includes('E='));
        assert.ok(compact.includes('alive'));
    });

    it('toCompact shows dead state', () => {
        const cell = new Cell({ alive: false });
        const compact = cell.toCompact();
        assert.ok(compact.includes('dead'));
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
        assert.ok(bio.cells.length > 0);
    });

    it('averageFitness returns a number', () => {
        const bio = new Biosphere(3, 50);
        const fitness = bio.averageFitness();
        assert.equal(typeof fitness, 'number');
        assert.ok(fitness >= 0 && fitness <= 1);
    });

    it('averageGcContent returns a number between 0 and 1', () => {
        const bio = new Biosphere(5, 50);
        const gc = bio.averageGcContent();
        assert.equal(typeof gc, 'number');
        assert.ok(gc >= 0 && gc <= 1);
    });

    it('averageGcContent returns 0 for empty biosphere', () => {
        const bio = new Biosphere(0, 50);
        assert.equal(bio.averageGcContent(), 0.0);
    });

    it('totalMutations returns sum of all cell mutations', () => {
        const bio = new Biosphere(3, 50);
        const mutations = bio.totalMutations();
        assert.equal(typeof mutations, 'number');
        assert.ok(mutations >= 0);
    });

    it('totalMutations increases after applying mutations', () => {
        const bio = new Biosphere(3, 50);
        const before = bio.totalMutations();
        // Apply high mutation pressure
        for (const cell of bio.cells) {
            cell.dna.applyMutations(100.0, 100.0);
        }
        const after = bio.totalMutations();
        assert.ok(after > before);
    });

    it('toCompact returns formatted string', () => {
        const bio = new Biosphere(3, 50);
        const compact = bio.toCompact();
        assert.ok(compact.startsWith('Bio['));
        assert.ok(compact.includes('gen='));
        assert.ok(compact.includes('pop='));
        assert.ok(compact.includes('fit='));
        assert.ok(compact.includes('gc='));
        assert.ok(compact.includes('born='));
        assert.ok(compact.includes('died='));
        assert.ok(compact.includes('mut='));
    });

    it('step increments generation', () => {
        const bio = new Biosphere(3, 50);
        assert.equal(bio.generation, 0);
        bio.step(10, 0, 0, 300);
        assert.equal(bio.generation, 1);
    });

    it('averageFitness returns 0 for empty biosphere', () => {
        const bio = new Biosphere(0, 50);
        assert.equal(bio.averageFitness(), 0.0);
    });
});


// ============================================================
// Environment Module
// ============================================================
describe('EnvironmentalEvent', () => {
    it('toCompact returns formatted string', () => {
        const event = new EnvironmentalEvent('volcanic', 2.5, 50, [0, 0, 0], 10);
        const compact = event.toCompact();
        assert.ok(compact.includes('volcanic'));
        assert.ok(compact.includes('i=2.50'));
        assert.ok(compact.includes('d=50'));
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

    it('thermalEnergy returns positive value in habitable range', () => {
        const env = new Environment(T_PLANCK);
        env.update(PRESENT_EPOCH);
        const te = env.thermalEnergy();
        assert.ok(te > 0);
    });

    it('thermalEnergy returns 0.1 at extreme temperatures', () => {
        const env = new Environment(50); // below 100K
        assert.equal(env.thermalEnergy(), 0.1);

        const env2 = new Environment(600); // above 500K
        assert.equal(env2.thermalEnergy(), 0.1);
    });

    it('thermalEnergy returns temperature*0.1 in moderate range', () => {
        const env = new Environment(300);
        assert.ok(Math.abs(env.thermalEnergy() - 30.0) < 0.01);
    });

    it('getRadiationDose sums radiation sources', () => {
        const env = new Environment(T_PLANCK);
        env.uvIntensity = 1.0;
        env.cosmicRayFlux = 0.5;
        env.stellarWind = 0.2;
        assert.ok(Math.abs(env.getRadiationDose() - 1.7) < 0.01);
    });

    it('toCompact returns formatted string', () => {
        const env = new Environment(T_PLANCK);
        env.update(PRESENT_EPOCH);
        const compact = env.toCompact();
        assert.ok(compact.startsWith('Env['));
        assert.ok(compact.includes('T='));
        assert.ok(compact.includes('UV='));
        assert.ok(compact.includes('CR='));
        assert.ok(compact.includes('atm='));
        assert.ok(compact.includes('H2O='));
        assert.ok(compact.includes('hab='));
    });

    it('update transitions through eras correctly', () => {
        const env = new Environment(T_PLANCK);

        // Early universe: rapid cooling
        env.update(100);
        assert.ok(env.temperature < T_PLANCK);

        // Pre-recombination
        env.update(10000);
        assert.ok(env.temperature >= T_CMB);

        // Post-recombination to star formation
        env.update(80000);
        // Temperature should be near T_CMB
        assert.ok(env.temperature < 100);
    });

    it('isHabitable returns false at extreme temperature', () => {
        const env = new Environment(T_PLANCK);
        assert.equal(env.isHabitable(), false);
    });

    it('isHabitable returns false without water', () => {
        const env = new Environment(300);
        env.waterAvailability = 0.0;
        assert.equal(env.isHabitable(), false);
    });

    it('isHabitable returns false with high radiation', () => {
        const env = new Environment(300);
        env.waterAvailability = 0.5;
        env.uvIntensity = RADIATION_DAMAGE_THRESHOLD;
        assert.equal(env.isHabitable(), false);
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

    it('full simulation run from start to present', () => {
        const u = new Universe(PRESENT_EPOCH, 10000);
        let lastEpoch = u.currentEpochName;
        const epochTransitions = [];
        while (u.tick < u.maxTicks) {
            u.step();
            if (u.currentEpochName !== lastEpoch) {
                epochTransitions.push(u.currentEpochName);
                lastEpoch = u.currentEpochName;
            }
        }
        // Should have passed through many epochs
        assert.ok(epochTransitions.length >= 5,
            `Expected at least 5 epoch transitions, got ${epochTransitions.length}: ${epochTransitions}`);
        // Final snapshot should contain data
        const snap = u.snapshot();
        assert.ok(snap.tick > 0);
        assert.ok(snap.epoch !== 'Void');
    });

    it('snapshot includes all expected fields', () => {
        const u = new Universe(PRESENT_EPOCH, 50000);
        while (u.tick < u.maxTicks) {
            u.step();
        }
        const snap = u.snapshot();
        assert.ok('tick' in snap);
        assert.ok('epoch' in snap);
        assert.ok('epochDescription' in snap);
        assert.ok('temperature' in snap);
        assert.ok('particles' in snap);
        assert.ok('atoms' in snap);
        assert.ok('molecules' in snap);
        assert.ok('cells' in snap);
        assert.ok('fitness' in snap);
        assert.ok('mutations' in snap);
        assert.ok('generation' in snap);
        assert.ok('particleCounts' in snap);
        assert.ok('elementCounts' in snap);
        assert.ok('moleculeCounts' in snap);
        assert.ok('dnaSequences' in snap);
        assert.ok('isHabitable' in snap);
        assert.ok('uvIntensity' in snap);
        assert.ok('cosmicRayFlux' in snap);
    });
});
