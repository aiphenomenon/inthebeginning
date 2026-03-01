/**
 * Universe orchestrator - drives the full cosmic simulation through 13 epochs.
 *
 * Coordinates quantum, atomic, chemical, and biological subsystems as the
 * universe cools from the Big Bang to the emergence of complex life.
 */

import {
    T_PLANCK, T_QUARK_HADRON, T_CMB, T_EARTH_SURFACE,
    T_RECOMBINATION,
    PLANCK_EPOCH, INFLATION_EPOCH, ELECTROWEAK_EPOCH, QUARK_EPOCH,
    HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH, RECOMBINATION_EPOCH,
    STAR_FORMATION_EPOCH, SOLAR_SYSTEM_EPOCH, EARTH_EPOCH,
    LIFE_EPOCH, DNA_EPOCH, PRESENT_EPOCH,
} from './constants.js';

import {
    QuantumField, Particle, ParticleType, Spin, Color, gaussRandom,
} from './quantum.js';

import { Atom, AtomicSystem } from './atomic.js';
import { ChemicalSystem } from './chemistry.js';
import { Biosphere } from './biology.js';
import { Environment } from './environment.js';


// Epoch timeline with descriptions
const EPOCHS = [
    { name: "Planck",          startTick: PLANCK_EPOCH,          description: "All forces unified, T~10^32K" },
    { name: "Inflation",       startTick: INFLATION_EPOCH,       description: "Exponential expansion, quantum fluctuations seed structure" },
    { name: "Electroweak",     startTick: ELECTROWEAK_EPOCH,     description: "Electromagnetic and weak forces separate" },
    { name: "Quark",           startTick: QUARK_EPOCH,           description: "Quark-gluon plasma, free quarks" },
    { name: "Hadron",          startTick: HADRON_EPOCH,          description: "Quarks confined into protons and neutrons" },
    { name: "Nucleosynthesis", startTick: NUCLEOSYNTHESIS_EPOCH, description: "Light nuclei form: H, He, Li" },
    { name: "Recombination",   startTick: RECOMBINATION_EPOCH,   description: "Atoms form, universe becomes transparent" },
    { name: "Star Formation",  startTick: STAR_FORMATION_EPOCH,  description: "First stars ignite, heavier elements forged" },
    { name: "Solar System",    startTick: SOLAR_SYSTEM_EPOCH,    description: "Our solar system coalesces from stellar debris" },
    { name: "Earth",           startTick: EARTH_EPOCH,           description: "Earth forms, oceans appear" },
    { name: "Life",            startTick: LIFE_EPOCH,            description: "First self-replicating molecules" },
    { name: "DNA Era",         startTick: DNA_EPOCH,             description: "DNA-based life, epigenetics emerge" },
    { name: "Present",         startTick: PRESENT_EPOCH,         description: "Complex life, intelligence" },
];


export class Universe {
    constructor(maxTicks = PRESENT_EPOCH, stepSize = 1) {
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

    _getEpochName() {
        let name = "Void";
        for (const epoch of EPOCHS) {
            if (this.tick >= epoch.startTick) name = epoch.name;
        }
        return name;
    }

    _getEpochDescription() {
        let desc = "";
        for (const epoch of EPOCHS) {
            if (this.tick >= epoch.startTick) desc = epoch.description;
        }
        return desc;
    }

    /** Seed the early universe with quarks, electrons, and photons. */
    _seedEarlyUniverse() {
        // Up quarks
        for (let i = 0; i < 30; i++) {
            this.quantumField.particles.push(new Particle({
                particleType: ParticleType.UP,
                position: [gaussRandom(0, 1), gaussRandom(0, 1), gaussRandom(0, 1)],
                momentum: [gaussRandom(0, 5), gaussRandom(0, 5), gaussRandom(0, 5)],
                spin: Math.random() < 0.5 ? Spin.UP : Spin.DOWN,
                color: [Color.RED, Color.GREEN, Color.BLUE][Math.floor(Math.random() * 3)],
            }));
        }
        // Down quarks
        for (let i = 0; i < 20; i++) {
            this.quantumField.particles.push(new Particle({
                particleType: ParticleType.DOWN,
                position: [gaussRandom(0, 1), gaussRandom(0, 1), gaussRandom(0, 1)],
                momentum: [gaussRandom(0, 5), gaussRandom(0, 5), gaussRandom(0, 5)],
                spin: Math.random() < 0.5 ? Spin.UP : Spin.DOWN,
                color: [Color.RED, Color.GREEN, Color.BLUE][Math.floor(Math.random() * 3)],
            }));
        }
        // Electrons
        for (let i = 0; i < 40; i++) {
            this.quantumField.particles.push(new Particle({
                particleType: ParticleType.ELECTRON,
                position: [gaussRandom(0, 2), gaussRandom(0, 2), gaussRandom(0, 2)],
                momentum: [gaussRandom(0, 3), gaussRandom(0, 3), gaussRandom(0, 3)],
            }));
        }
        // Photons
        for (let i = 0; i < 5; i++) {
            this.quantumField.particles.push(new Particle({
                particleType: ParticleType.PHOTON,
                position: [0, 0, 0],
                momentum: [gaussRandom(0, 10), gaussRandom(0, 10), gaussRandom(0, 10)],
            }));
        }
        this.particlesCreated += this.quantumField.particles.length;
    }

    /** Advance the simulation by one step. */
    step() {
        this.tick += this.stepSize;

        // Check epoch transition
        const newEpoch = this._getEpochName();
        const epochChanged = newEpoch !== this.currentEpochName;
        if (epochChanged) {
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
            const protons = this.quantumField.particles.filter(
                p => p.particleType === ParticleType.PROTON
            ).length;
            const neutrons = this.quantumField.particles.filter(
                p => p.particleType === ParticleType.NEUTRON
            ).length;

            if (protons > 0 || neutrons > 0) {
                const newAtoms = this.atomicSystem.nucleosynthesis(protons, neutrons);
                // Remove used particles from quantum field
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

        // === Star formation and stellar nucleosynthesis ===
        if (this.tick >= STAR_FORMATION_EPOCH && this.tick < SOLAR_SYSTEM_EPOCH) {
            this.atomicSystem.temperature = this.environment.temperature;
            const newHeavy = this.atomicSystem.stellarNucleosynthesis(this.environment.temperature * 100);
            this.atomsFormed += newHeavy.length;
        }

        // === Chemistry (Earth epoch and beyond) ===
        if (this.tick >= EARTH_EPOCH) {
            if (this.chemicalSystem === null) {
                this.chemicalSystem = new ChemicalSystem(this.atomicSystem);
            }

            // Seed elements when Earth forms
            if (EARTH_EPOCH - this.stepSize < this.tick && this.tick <= EARTH_EPOCH + this.stepSize) {
                const elementsToSeed = [
                    [1, 40],   // Hydrogen
                    [2, 10],   // Helium
                    [6, 15],   // Carbon
                    [7, 10],   // Nitrogen
                    [8, 15],   // Oxygen
                    [15, 3],   // Phosphorus
                ];
                for (const [z, count] of elementsToSeed) {
                    for (let i = 0; i < count; i++) {
                        const a = new Atom({
                            atomicNumber: z,
                            position: [gaussRandom(0, 5), gaussRandom(0, 5), gaussRandom(0, 5)],
                        });
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

            // Ongoing catalyzed reactions
            if (this.tick > EARTH_EPOCH) {
                const formed = this.chemicalSystem.catalyzedReaction(
                    this.environment.temperature,
                    this.tick > LIFE_EPOCH, // catalyst present after life epoch
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

        return epochChanged;
    }

    /** Take a snapshot of current simulation state. */
    snapshot() {
        const dnaSequences = [];
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
}

export { EPOCHS };
