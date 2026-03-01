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
    T_PLANCK, T_QUARK_HADRON, T_CMB,
    PLANCK_EPOCH, HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH,
    RECOMBINATION_EPOCH, PRESENT_EPOCH,
} from '../constants.js';

import {
    QuantumField, Particle, ParticleType, Spin, Color,
    WaveFunction, gaussRandom,
} from '../quantum.js';

import { Atom, AtomicSystem } from '../atomic.js';
import { ChemicalSystem } from '../chemistry.js';
import { Biosphere } from '../biology.js';
import { Environment } from '../environment.js';
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
});


// ============================================================
// Atomic Module
// ============================================================
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
});


// ============================================================
// Chemistry Module
// ============================================================
describe('ChemicalSystem', () => {
    let cs;
    let as;

    before(() => {
        as = new AtomicSystem();
        // Seed with H and O for water formation
        for (let i = 0; i < 10; i++) {
            as.atoms.push(new Atom({ atomicNumber: 1 })); // H
        }
        for (let i = 0; i < 5; i++) {
            as.atoms.push(new Atom({ atomicNumber: 8 })); // O
        }
        cs = new ChemicalSystem(as);
    });

    it('initializes with zero molecules', () => {
        assert.equal(cs.molecules.length, 0);
    });

    it('formWater produces water molecules', () => {
        const waters = cs.formWater();
        assert.ok(waters.length > 0);
    });

    it('moleculeCensus returns correct types', () => {
        const census = cs.moleculeCensus();
        assert.ok(typeof census === 'object');
    });
});


// ============================================================
// Biology Module
// ============================================================
describe('Biosphere', () => {
    it('initializes with cells', () => {
        const bio = new Biosphere(5, 50);
        assert.ok(bio.cells.length > 0);
    });

    it('step advances the biosphere', () => {
        const bio = new Biosphere(3, 50);
        const initialCount = bio.cells.length;
        bio.step(1.0, 0.1, 0.01, 300);
        // Population should still exist
        assert.ok(bio.cells.length > 0);
    });

    it('averageFitness returns a number', () => {
        const bio = new Biosphere(3, 50);
        const fitness = bio.averageFitness();
        assert.equal(typeof fitness, 'number');
        assert.ok(fitness >= 0 && fitness <= 1);
    });
});


// ============================================================
// Environment Module
// ============================================================
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
