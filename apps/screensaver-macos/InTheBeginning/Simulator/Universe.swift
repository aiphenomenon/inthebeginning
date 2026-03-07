// Universe.swift
// InTheBeginning – macOS Screensaver
//
// Top-level orchestrator for the cosmic evolution simulation.
// Manages all subsystems (quantum field, atoms, chemistry, environment,
// biosphere) and advances them through 13 epochs from the Planck era
// to the present day.

import Foundation

// MARK: - Renderable Entity

/// Lightweight snapshot of an entity for the renderer.
struct RenderableEntity {
    var position: SIMD3<Double>
    var size: Double
    var red: Double
    var green: Double
    var blue: Double
    var alpha: Double
}

// MARK: - Universe Snapshot

/// Immutable snapshot of the simulation state for rendering.
struct UniverseSnapshot {
    let tick: Int
    let epoch: Epoch
    let temperature: Double
    let entities: [RenderableEntity]
    let particleCount: Int
    let atomCount: Int
    let moleculeCount: Int
    let cellCount: Int
    let epochName: String
    let epochDescription: String
}

// MARK: - Universe

final class Universe {
    // Subsystems
    let quantumField: QuantumField
    let atomicSystem: AtomicSystem
    let chemicalSystem: ChemicalSystem
    let environment: Environment
    let biosphere: Biosphere

    // State
    var tick: Int = 0
    var seed: UInt64
    private(set) var cycle: Int = 0

    /// Current epoch, derived from tick count.
    var currentEpoch: Epoch {
        Epoch.current(forTick: tick)
    }

    init(seed: UInt64 = 0) {
        self.seed = seed == 0 ? UInt64.random(in: 1...UInt64.max) : seed
        srand48(Int(self.seed & 0x7FFFFFFF))

        self.quantumField = QuantumField(temperature: kTempPlanck)
        self.atomicSystem = AtomicSystem(temperature: kTempRecombination)
        self.chemicalSystem = ChemicalSystem(atomicSystem: atomicSystem)
        self.environment = Environment(temperature: kTempPlanck)
        self.biosphere = Biosphere(carryingCapacity: kMaxRenderableCells)
    }

    // MARK: Big Bounce

    /// Reset the universe for a new cycle, simulating a Big Bounce.
    ///
    /// Resets the tick counter to zero, re-initialises all subsystems to their
    /// initial conditions, and increments the cycle counter. The RNG seed is
    /// preserved so that each cycle produces a different but deterministic
    /// evolution when the same initial seed is used.
    func bigBounce() {
        cycle += 1
        tick = 0

        // Re-seed RNG for the new cycle (derive from original seed + cycle)
        let newSeed = seed &+ UInt64(cycle)
        srand48(Int(newSeed & 0x7FFFFFFF))

        // Reset all subsystems
        quantumField.reset(temperature: kTempPlanck)
        atomicSystem.reset(temperature: kTempRecombination)
        chemicalSystem.reset()
        environment.reset(temperature: kTempPlanck)
        biosphere.reset()
    }

    // MARK: Step

    /// Advance the simulation by one tick.
    func step() {
        tick += 1
        let epoch = currentEpoch

        // Evolve environment
        environment.step(epoch: epoch)

        switch epoch {
        case .planck:
            stepPlanck()

        case .inflation:
            stepInflation()

        case .electroweak:
            stepElectroweak()

        case .quark:
            stepQuark()

        case .hadron:
            stepHadron()

        case .nucleosynthesis:
            stepNucleosynthesis()

        case .recombination:
            stepRecombination()

        case .starFormation:
            stepStarFormation()

        case .solarSystem:
            stepSolarSystem()

        case .earth:
            stepEarth()

        case .life:
            stepLife()

        case .dna:
            stepDNA()

        case .present:
            stepPresent()
        }

        // Evolve quantum field every tick
        quantumField.evolve(dt: 1.0)
    }

    // MARK: Epoch Handlers

    private func stepPlanck() {
        // All forces unified, extreme energy. Vacuum fluctuations dominate.
        quantumField.temperature = environment.temperature
        for _ in 0..<5 {
            quantumField.vacuumFluctuation()
        }
    }

    private func stepInflation() {
        // Exponential expansion. Rapid pair production.
        quantumField.temperature = environment.temperature
        for _ in 0..<10 {
            quantumField.vacuumFluctuation()
        }
        // Spread particles outward (inflation)
        for p in quantumField.particles {
            p.position *= 1.001
        }
    }

    private func stepElectroweak() {
        // Electroweak symmetry breaking. Particles acquire mass.
        quantumField.temperature = environment.temperature
        quantumField.vacuumFluctuation()
    }

    private func stepQuark() {
        // Quark-gluon plasma. Free quarks.
        quantumField.temperature = environment.temperature
        quantumField.vacuumFluctuation()

        // Begin confinement as temperature drops
        if environment.temperature < kTempQuarkHadron * 2.0 {
            _ = quantumField.quarkConfinement()
        }
    }

    private func stepHadron() {
        // Quarks confined into protons and neutrons.
        quantumField.temperature = environment.temperature
        _ = quantumField.quarkConfinement()

        // Annihilation of matter-antimatter pairs
        let electrons = quantumField.particles.filter { $0.particleType == .electron }
        let positrons = quantumField.particles.filter { $0.particleType == .positron }
        let pairs = min(electrons.count, positrons.count)
        for i in 0..<min(pairs, 5) {
            quantumField.annihilate(electrons[i], positrons[i])
        }
    }

    private func stepNucleosynthesis() {
        // Light nuclei form: H, He, Li.
        let protons = quantumField.particles.filter { $0.particleType == .proton }.count
        let neutrons = quantumField.particles.filter { $0.particleType == .neutron }.count
        if protons > 0 || neutrons > 0 {
            _ = atomicSystem.nucleosynthesis(protons: min(protons, 4), neutrons: min(neutrons, 4))
        }
        atomicSystem.temperature = environment.temperature
    }

    private func stepRecombination() {
        // Atoms form, universe becomes transparent.
        atomicSystem.temperature = environment.temperature
        _ = atomicSystem.recombination(field: quantumField)
    }

    private func stepStarFormation() {
        // First stars ignite, heavier elements forged.
        atomicSystem.temperature = kTempStellarCore
        _ = atomicSystem.stellarNucleosynthesis(temperature: kTempStellarCore)

        // Form simple molecules
        _ = chemicalSystem.formWater()
        _ = chemicalSystem.formMethane()
        _ = chemicalSystem.formAmmonia()
    }

    private func stepSolarSystem() {
        // Solar system coalesces from stellar debris.
        atomicSystem.temperature = environment.temperature
        _ = atomicSystem.stellarNucleosynthesis(temperature: environment.temperature)
        _ = chemicalSystem.formWater()
        _ = chemicalSystem.formMethane()
        _ = chemicalSystem.formAmmonia()
    }

    private func stepEarth() {
        // Earth forms, oceans appear.
        atomicSystem.temperature = environment.temperature
        _ = chemicalSystem.formWater()

        // Catalyzed reactions begin
        let catalystPresent = environment.waterPresent
        _ = chemicalSystem.catalyzedReaction(
            temperature: environment.temperature,
            catalystPresent: catalystPresent
        )
    }

    private func stepLife() {
        // First self-replicating molecules -> protocells.
        _ = chemicalSystem.catalyzedReaction(
            temperature: environment.temperature,
            catalystPresent: true
        )

        // Seed biosphere if conditions are right and not yet seeded
        if environment.isHabitable && biosphere.cells.isEmpty {
            biosphere.seed(count: 10)
        }

        // Evolve biosphere
        if !biosphere.cells.isEmpty {
            biosphere.step(
                environmentalEnergy: environment.biologicalEnergy,
                mutationModifier: environment.mutationModifier
            )
            biosphere.naturalSelection()
        }
    }

    private func stepDNA() {
        // DNA-based life, epigenetics emerge.
        if biosphere.cells.isEmpty {
            biosphere.seed(count: 20)
        }
        biosphere.step(
            environmentalEnergy: environment.biologicalEnergy,
            mutationModifier: environment.mutationModifier
        )
        biosphere.naturalSelection()
    }

    private func stepPresent() {
        // Complex life, intelligence.
        biosphere.step(
            environmentalEnergy: environment.biologicalEnergy,
            mutationModifier: 1.0
        )
        biosphere.naturalSelection()
    }

    // MARK: Snapshot

    /// Build a renderable snapshot of the current simulation state.
    func snapshot() -> UniverseSnapshot {
        var entities: [RenderableEntity] = []
        let epoch = currentEpoch

        // Quantum particles
        let particlesToRender = Array(quantumField.particles.prefix(kMaxRenderableParticles))
        for p in particlesToRender {
            let (r, g, b) = particleColor(p, epoch: epoch)
            entities.append(RenderableEntity(
                position: p.position,
                size: particleSize(p),
                red: r, green: g, blue: b,
                alpha: p.waveFn.probability
            ))
        }

        // Atoms
        let atomsToRender = Array(atomicSystem.atoms.prefix(kMaxRenderableAtoms))
        for a in atomsToRender {
            let (r, g, b) = atomColor(a, epoch: epoch)
            entities.append(RenderableEntity(
                position: a.position,
                size: Double(a.atomicNumber) * 0.3 + 1.0,
                red: r, green: g, blue: b,
                alpha: 1.0
            ))
        }

        // Molecules
        for m in chemicalSystem.molecules.prefix(kMaxRenderableAtoms) {
            let (r, g, b) = moleculeColor(m, epoch: epoch)
            entities.append(RenderableEntity(
                position: m.position,
                size: Double(m.atomCount) * 0.5 + 1.5,
                red: r, green: g, blue: b,
                alpha: 0.9
            ))
        }

        // Cells
        for c in biosphere.cells.prefix(kMaxRenderableCells) {
            let (r, g, b) = cellColor(c, epoch: epoch)
            entities.append(RenderableEntity(
                position: c.position,
                size: 3.0 + c.fitness,
                red: r, green: g, blue: b,
                alpha: min(1.0, c.energy / 5.0)
            ))
        }

        return UniverseSnapshot(
            tick: tick,
            epoch: epoch,
            temperature: environment.temperature,
            entities: entities,
            particleCount: quantumField.particles.count,
            atomCount: atomicSystem.atoms.count,
            moleculeCount: chemicalSystem.molecules.count,
            cellCount: biosphere.cells.count,
            epochName: epoch.name,
            epochDescription: epoch.description
        )
    }

    // MARK: Color Schemes

    private func particleColor(_ p: Particle, epoch: Epoch) -> (Double, Double, Double) {
        switch epoch {
        case .planck, .inflation:
            // White-hot plasma
            return (1.0, 1.0, 0.9)
        case .electroweak:
            // Violet – electroweak symmetry breaking
            return (0.7, 0.3, 1.0)
        case .quark:
            // Color charge representation
            switch p.color {
            case .red, .antiRed:     return (1.0, 0.2, 0.2)
            case .green, .antiGreen: return (0.2, 1.0, 0.2)
            case .blue, .antiBlue:   return (0.2, 0.2, 1.0)
            case nil:
                switch p.particleType {
                case .photon:   return (1.0, 1.0, 0.5)
                case .electron: return (0.3, 0.6, 1.0)
                case .positron: return (1.0, 0.6, 0.3)
                default:        return (0.8, 0.8, 0.8)
                }
            }
        case .hadron:
            switch p.particleType {
            case .proton:   return (1.0, 0.4, 0.4)
            case .neutron:  return (0.6, 0.6, 0.8)
            case .electron: return (0.3, 0.5, 1.0)
            case .photon:   return (1.0, 1.0, 0.3)
            default:        return (0.7, 0.7, 0.7)
            }
        default:
            switch p.particleType {
            case .proton:   return (0.9, 0.3, 0.3)
            case .neutron:  return (0.5, 0.5, 0.7)
            case .electron: return (0.2, 0.4, 1.0)
            case .photon:   return (1.0, 1.0, 0.2)
            default:        return (0.6, 0.6, 0.6)
            }
        }
    }

    private func atomColor(_ a: Atom, epoch: Epoch) -> (Double, Double, Double) {
        switch a.atomicNumber {
        case 1:  return (0.9, 0.9, 1.0)   // Hydrogen: white-blue
        case 2:  return (1.0, 0.9, 0.6)   // Helium: pale yellow
        case 6:  return (0.3, 0.3, 0.3)   // Carbon: dark gray
        case 7:  return (0.2, 0.3, 0.9)   // Nitrogen: blue
        case 8:  return (0.9, 0.2, 0.2)   // Oxygen: red
        case 26: return (0.8, 0.5, 0.2)   // Iron: orange-brown
        default: return (0.6, 0.7, 0.8)   // Others: steel blue
        }
    }

    private func moleculeColor(_ m: Molecule, epoch: Epoch) -> (Double, Double, Double) {
        if m.name == "water" {
            return (0.2, 0.5, 1.0)
        }
        if m.isOrganic {
            return (0.2, 0.8, 0.3)   // Organic: green
        }
        return (0.7, 0.6, 0.5)       // Inorganic: tan
    }

    private func cellColor(_ c: Cell, epoch: Epoch) -> (Double, Double, Double) {
        switch epoch {
        case .life:
            // Protocells: dim green
            let g = 0.4 + c.fitness * 0.3
            return (0.1, min(1.0, g), 0.2)
        case .dna:
            // DNA era: brighter, more varied
            let g = 0.5 + c.fitness * 0.25
            let b = 0.3 + Double(c.generation % 10) * 0.05
            return (0.1, min(1.0, g), min(1.0, b))
        case .present:
            // Complex life: full color
            let r = 0.2 + Double(c.dna.length % 50) * 0.01
            let g = 0.5 + c.fitness * 0.2
            let b = 0.3 + Double(c.generation % 20) * 0.03
            return (min(1.0, r), min(1.0, g), min(1.0, b))
        default:
            return (0.3, 0.6, 0.3)
        }
    }

    private func particleSize(_ p: Particle) -> Double {
        switch p.particleType {
        case .photon, .neutrino:          return 0.5
        case .electron, .positron:        return 1.0
        case .up, .down, .gluon:          return 1.2
        case .proton, .neutron:           return 2.0
        case .wBoson, .zBoson:            return 2.5
        }
    }
}
