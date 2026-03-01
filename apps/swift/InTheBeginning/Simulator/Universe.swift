// Universe.swift
// InTheBeginning
//
// Top-level orchestrator for the cosmic evolution simulation.
// Manages all subsystems (quantum, atomic, chemical, biological, environmental)
// and coordinates their interactions across 13 cosmic epochs from the
// Planck era through the emergence of complex life.

import Foundation
import Observation

// MARK: - Simulation State

enum SimulationState: String, Sendable {
    case idle = "idle"
    case running = "running"
    case paused = "paused"
    case completed = "completed"
}

// MARK: - Simulation Statistics Snapshot

struct SimulationSnapshot: Sendable {
    let tick: Int
    let epoch: Epoch
    let temperature: Double
    let particleCount: Int
    let atomCount: Int
    let moleculeCount: Int
    let cellCount: Int
    let waterCount: Int
    let aminoAcidCount: Int
    let averageFitness: Double
    let maxGeneration: Int
    let habitability: Double
    let totalEnergy: Double
    let geneticDiversity: Double
    let atmosphereDescription: String

    static let empty = SimulationSnapshot(
        tick: 0, epoch: .planck, temperature: 0, particleCount: 0,
        atomCount: 0, moleculeCount: 0, cellCount: 0, waterCount: 0,
        aminoAcidCount: 0, averageFitness: 0, maxGeneration: 0,
        habitability: 0, totalEnergy: 0, geneticDiversity: 0,
        atmosphereDescription: ""
    )
}

// MARK: - Renderable Entity

/// A lightweight struct for the rendering layer to display.
struct RenderableEntity: Identifiable, Sendable {
    let id: Int
    let position: SIMD3<Double>
    let color: SIMD4<Float>
    let radius: Float
    let label: String
    let category: EntityCategory
}

enum EntityCategory: String, Sendable {
    case particle
    case atom
    case molecule
    case cell
}

// MARK: - Universe

@Observable
final class Universe {
    // MARK: - Subsystems

    private(set) var quantumField: QuantumField
    private(set) var atomicSystem: AtomicSystem
    private(set) var chemicalSystem: ChemicalSystem
    private(set) var biosphere: Biosphere
    private(set) var environment: Environment

    // MARK: - Simulation State

    private(set) var tick: Int = 0
    private(set) var currentEpoch: Epoch = .planck
    private(set) var state: SimulationState = .idle
    private(set) var snapshot: SimulationSnapshot = .empty
    private(set) var renderables: [RenderableEntity] = []

    /// Ticks to advance per frame (speed control).
    var ticksPerFrame: Int = 1

    /// Maximum particles to simulate.
    var maxParticles: Int = SimulationLimits.maxParticlesDefault

    /// Spatial scale for rendering (zoom).
    var spatialScale: Double = 1.0

    // MARK: - Event Log

    private(set) var eventLog: [String] = []
    private let maxLogEntries = 50

    // MARK: - Initialization

    init() {
        quantumField = QuantumField(temperature: TemperatureScale.planck)
        atomicSystem = AtomicSystem(temperature: TemperatureScale.recombination)
        chemicalSystem = ChemicalSystem(temperature: TemperatureScale.earthSurface)
        biosphere = Biosphere()
        environment = Environment(temperature: TemperatureScale.planck)
    }

    // MARK: - Control

    func start() {
        guard state == .idle || state == .paused else { return }
        state = .running
        log("Simulation started at epoch: \(currentEpoch.displayName)")
    }

    func pause() {
        guard state == .running else { return }
        state = .paused
        log("Simulation paused at tick \(tick)")
    }

    func resume() {
        guard state == .paused else { return }
        state = .running
        log("Simulation resumed")
    }

    func reset() {
        tick = 0
        currentEpoch = .planck
        state = .idle
        quantumField = QuantumField(temperature: TemperatureScale.planck)
        atomicSystem = AtomicSystem(temperature: TemperatureScale.recombination)
        chemicalSystem = ChemicalSystem(temperature: TemperatureScale.earthSurface)
        biosphere = Biosphere()
        environment = Environment(temperature: TemperatureScale.planck)
        renderables = []
        snapshot = .empty
        eventLog.removeAll()
        log("Simulation reset")
    }

    // MARK: - Main Simulation Loop

    /// Advance the simulation by one frame (may contain multiple ticks).
    func advanceFrame() {
        guard state == .running else { return }

        for _ in 0..<ticksPerFrame {
            advanceTick()

            if tick >= SimulationLimits.presentEpoch {
                state = .completed
                log("Simulation complete: reached the Present epoch")
                break
            }
        }

        updateSnapshot()
        updateRenderables()
    }

    /// Advance the simulation by exactly one tick.
    private func advanceTick() {
        tick += 1

        let previousEpoch = currentEpoch
        currentEpoch = Epoch.current(forTick: tick)

        // Log epoch transitions
        if currentEpoch != previousEpoch {
            log("Epoch transition: \(currentEpoch.displayName) - \(currentEpoch.description)")
        }

        // Update environment
        environment.update(epoch: currentEpoch, tick: tick)

        // Run epoch-specific physics
        switch currentEpoch {
        case .planck:
            simulatePlanckEra()
        case .inflation:
            simulateInflation()
        case .electroweak:
            simulateElectroweak()
        case .quark:
            simulateQuarkEra()
        case .hadron:
            simulateHadronEra()
        case .nucleosynthesis:
            simulateNucleosynthesis()
        case .recombination:
            simulateRecombination()
        case .starFormation:
            simulateStarFormation()
        case .solarSystem:
            simulateSolarSystem()
        case .earth:
            simulateEarth()
        case .life:
            simulateLife()
        case .dna:
            simulateDNAEra()
        case .present:
            simulatePresent()
        }
    }

    // MARK: - Epoch Simulations

    private func simulatePlanckEra() {
        // All forces unified, extreme energy density
        quantumField.temperature = environment.temperature

        // Vacuum fluctuations produce virtual particles
        if quantumField.particles.count < maxParticles / 4 {
            _ = quantumField.vacuumFluctuation()
        }

        quantumField.evolve(dt: 0.001)
    }

    private func simulateInflation() {
        // Exponential expansion, quantum fluctuations seed large-scale structure
        quantumField.temperature = environment.temperature

        // Rapid pair production from inflaton field energy
        let pairsToCreate = min(10, maxParticles / 20)
        for _ in 0..<pairsToCreate {
            guard quantumField.particles.count < maxParticles / 2 else { break }
            let energy = environment.temperature * PhysicsConstants.kB * Double.random(in: 0.5...2.0)
            _ = quantumField.pairProduction(energy: energy)
        }

        quantumField.cool(factor: 0.99)
        quantumField.evolve(dt: 0.01)
    }

    private func simulateElectroweak() {
        // Electromagnetic and weak force separate
        quantumField.temperature = environment.temperature

        // Continue pair production but more orderly
        if quantumField.particles.count < maxParticles / 2 {
            let energy = environment.temperature * PhysicsConstants.kB
            _ = quantumField.pairProduction(energy: energy)
        }

        // Decoherence increases
        for p in quantumField.particles.prefix(50) {
            quantumField.decohere(p, environmentCoupling: 0.01)
        }

        quantumField.cool(factor: 0.995)
        quantumField.evolve(dt: 0.1)
    }

    private func simulateQuarkEra() {
        // Quark-gluon plasma
        quantumField.temperature = environment.temperature

        // Quarks roam freely
        if quantumField.particles.count < maxParticles {
            let energy = environment.temperature * PhysicsConstants.kB * 0.5
            _ = quantumField.pairProduction(energy: energy)
        }

        quantumField.cool(factor: 0.998)
        quantumField.evolve(dt: 0.5)
    }

    private func simulateHadronEra() {
        // Quarks confine into protons and neutrons
        quantumField.temperature = environment.temperature
        quantumField.cool(factor: 0.999)

        let hadrons = quantumField.quarkConfinement()
        if !hadrons.isEmpty {
            log("Quark confinement: \(hadrons.count) hadrons formed")
        }

        // Electron-positron annihilation
        let electrons = quantumField.particles.filter { $0.particleType == .electron }
        let positrons = quantumField.particles.filter { $0.particleType == .positron }
        if let e = electrons.first, let p = positrons.first {
            _ = quantumField.annihilate(e, p)
        }

        quantumField.evolve(dt: 1.0)
    }

    private func simulateNucleosynthesis() {
        // Light nuclei form (H, He, Li)
        quantumField.temperature = environment.temperature
        quantumField.cool(factor: 0.9995)

        // Continue confinement
        _ = quantumField.quarkConfinement()

        // Count available nucleons
        let protons = quantumField.particles.filter { $0.particleType == .proton }.count
        let neutrons = quantumField.particles.filter { $0.particleType == .neutron }.count

        if protons >= 2 && neutrons >= 2 {
            let newAtoms = atomicSystem.nucleosynthesis(protons: min(protons, 10), neutrons: min(neutrons, 10))
            if !newAtoms.isEmpty {
                log("Big Bang nucleosynthesis: \(newAtoms.map(\.symbol).joined(separator: ", "))")
                // Remove consumed nucleons from quantum field
                var pRemaining = newAtoms.reduce(0) { $0 + $1.atomicNumber }
                var nRemaining = newAtoms.reduce(0) { $0 + ($1.massNumber - $1.atomicNumber) }
                quantumField.particles.removeAll { p in
                    if p.particleType == .proton && pRemaining > 0 {
                        pRemaining -= 1
                        return true
                    }
                    if p.particleType == .neutron && nRemaining > 0 {
                        nRemaining -= 1
                        return true
                    }
                    return false
                }
            }
        }

        quantumField.evolve(dt: 1.0)
    }

    private func simulateRecombination() {
        // Atoms form: electrons captured by nuclei
        quantumField.temperature = environment.temperature
        atomicSystem.temperature = environment.temperature
        quantumField.cool(factor: 0.9998)

        let newAtoms = atomicSystem.recombination(field: quantumField)
        if !newAtoms.isEmpty {
            log("Recombination: \(newAtoms.count) atoms formed, universe becomes transparent")
        }

        // Decohere remaining particles
        for p in quantumField.particles.prefix(20) {
            quantumField.decohere(p, environmentCoupling: 0.5)
        }

        quantumField.evolve(dt: 1.0)
    }

    private func simulateStarFormation() {
        // First stars ignite, heavier elements forged
        atomicSystem.temperature = environment.temperature
        quantumField.temperature = environment.temperature

        // Continue recombination of remaining free particles
        _ = atomicSystem.recombination(field: quantumField)

        // Stellar nucleosynthesis creates heavier elements
        let newElements = atomicSystem.stellarNucleosynthesis(temperature: TemperatureScale.stellarCore)
        if !newElements.isEmpty {
            let symbols = newElements.map(\.symbol)
            let unique = Set(symbols)
            log("Stellar fusion: created \(unique.joined(separator: ", "))")
        }

        quantumField.evolve(dt: 1.0)
    }

    private func simulateSolarSystem() {
        // Solar system coalesces from stellar debris
        atomicSystem.temperature = environment.temperature

        // More stellar nucleosynthesis for diversity
        _ = atomicSystem.stellarNucleosynthesis(temperature: TemperatureScale.stellarCore * 0.5)

        // Generate additional elements if we have too few
        if atomicSystem.atoms.filter({ $0.atomicNumber == 6 }).isEmpty {
            // Seed carbon, nitrogen, oxygen, phosphorus from supernova
            let elements: [(Int, Int)] = [(6, 12), (7, 14), (8, 16), (15, 31)]
            for (z, a) in elements {
                let atom = Atom(
                    atomicNumber: z,
                    massNumber: a,
                    position: SIMD3<Double>.randomGaussian(sigma: 30.0)
                )
                atomicSystem.atoms.append(atom)
            }
            log("Supernova remnants enrich the protoplanetary disk")
        }
    }

    private func simulateEarth() {
        // Earth forms, oceans appear
        atomicSystem.temperature = environment.temperature
        chemicalSystem.temperature = environment.temperature

        // Water formation
        let newWater = chemicalSystem.formWater(atomicSystem: atomicSystem)
        if !newWater.isEmpty && chemicalSystem.waterCount <= newWater.count {
            log("Water formation: \(chemicalSystem.waterCount) H2O molecules")
        }

        // Simple molecule formation
        _ = chemicalSystem.formSimpleMolecules(atomicSystem: atomicSystem)

        // Chemical evolution
        chemicalSystem.evolve(dt: 1.0)

        // Thermal decomposition at high temps
        _ = chemicalSystem.thermalDecomposition()

        // Ensure we have diverse atoms for chemistry
        ensureChemicalDiversity()
    }

    private func simulateLife() {
        // First self-replicating molecules
        chemicalSystem.temperature = environment.temperature

        // Continue water and molecule formation
        _ = chemicalSystem.formWater(atomicSystem: atomicSystem)
        _ = chemicalSystem.formSimpleMolecules(atomicSystem: atomicSystem)

        // Miller-Urey-like amino acid synthesis
        let energyInput = environment.bioavailableEnergy
        let newAA = chemicalSystem.synthesizeAminoAcids(energyInput: energyInput)
        if !newAA.isEmpty {
            log("Amino acid synthesis: \(chemicalSystem.aminoAcidCount) amino acids")
        }

        // Nucleotide synthesis
        let newNuc = chemicalSystem.synthesizeNucleotides(energyInput: energyInput)
        if !newNuc.isEmpty {
            log("Nucleotide formation: \(chemicalSystem.nucleotideCount) nucleotides")
        }

        // Phospholipid synthesis
        _ = chemicalSystem.synthesizePhospholipids()

        // Enable catalysts (clay minerals, metal ions)
        chemicalSystem.catalystPresent = true

        // Abiogenesis: spontaneous cell formation
        let newCells = biosphere.abiogenesis(
            aminoAcidCount: chemicalSystem.aminoAcidCount,
            nucleotideCount: chemicalSystem.nucleotideCount,
            hasWater: chemicalSystem.waterCount > 0,
            temperature: environment.temperature
        )
        if !newCells.isEmpty {
            log("Abiogenesis! First protocell emerges from primordial soup")
        }

        // Evolve existing cells
        biosphere.mutationRate = environment.environmentalMutationRate
        biosphere.evolve(
            temperature: environment.temperature,
            radiationLevel: environment.radiationField.mutagenicIntensity,
            energyAvailable: energyInput
        )

        chemicalSystem.evolve(dt: 1.0)
    }

    private func simulateDNAEra() {
        // DNA-based life, epigenetics emerge
        chemicalSystem.temperature = environment.temperature

        // Continue chemical processes
        let energyInput = environment.bioavailableEnergy
        _ = chemicalSystem.synthesizeAminoAcids(energyInput: energyInput)
        _ = chemicalSystem.synthesizeNucleotides(energyInput: energyInput)

        // Ensure cells exist (abiogenesis if needed)
        if biosphere.cells.isEmpty {
            _ = biosphere.abiogenesis(
                aminoAcidCount: max(5, chemicalSystem.aminoAcidCount),
                nucleotideCount: max(3, chemicalSystem.nucleotideCount),
                hasWater: true,
                temperature: environment.temperature
            )
        }

        // Evolution with natural selection
        biosphere.mutationRate = environment.environmentalMutationRate
        biosphere.evolve(
            temperature: environment.temperature,
            radiationLevel: environment.radiationField.mutagenicIntensity,
            energyAvailable: energyInput
        )

        // Log milestones
        if biosphere.maxGenerationReached > 0 && biosphere.maxGenerationReached % 50 == 0 {
            log("Generation \(biosphere.maxGenerationReached): avg fitness \(String(format: "%.3f", biosphere.averageFitness))")
        }

        chemicalSystem.evolve(dt: 1.0)
    }

    private func simulatePresent() {
        // Complex life, intelligence
        let energyInput = environment.bioavailableEnergy

        biosphere.mutationRate = environment.environmentalMutationRate * 0.5  // More stable genome
        biosphere.evolve(
            temperature: environment.temperature,
            radiationLevel: environment.radiationField.mutagenicIntensity,
            energyAvailable: energyInput * 2.0  // More energy available
        )

        chemicalSystem.evolve(dt: 1.0)
    }

    // MARK: - Helpers

    /// Ensure minimum chemical diversity for interesting simulation.
    private func ensureChemicalDiversity() {
        let counts = atomicSystem.elementCounts()
        let needed: [(String, Int, Int)] = [  // (symbol, atomicNumber, massNumber)
            ("H", 1, 1),
            ("O", 8, 16),
            ("C", 6, 12),
            ("N", 7, 14),
        ]

        for (symbol, z, a) in needed {
            if (counts[symbol] ?? 0) < 5 {
                for _ in 0..<3 {
                    let atom = Atom(
                        atomicNumber: z,
                        massNumber: a,
                        position: SIMD3<Double>.randomGaussian(sigma: 20.0)
                    )
                    atomicSystem.atoms.append(atom)
                }
            }
        }
    }

    // MARK: - Snapshot

    private func updateSnapshot() {
        snapshot = SimulationSnapshot(
            tick: tick,
            epoch: currentEpoch,
            temperature: environment.temperature,
            particleCount: quantumField.particles.count,
            atomCount: atomicSystem.atoms.count,
            moleculeCount: chemicalSystem.molecules.count,
            cellCount: biosphere.livingCellCount,
            waterCount: chemicalSystem.waterCount,
            aminoAcidCount: chemicalSystem.aminoAcidCount,
            averageFitness: biosphere.averageFitness,
            maxGeneration: biosphere.maxGenerationReached,
            habitability: environment.habitabilityScore,
            totalEnergy: quantumField.totalEnergy(),
            geneticDiversity: biosphere.geneticDiversity,
            atmosphereDescription: environment.atmosphereDescription
        )
    }

    // MARK: - Renderables

    private func updateRenderables() {
        var entities: [RenderableEntity] = []
        let limit = maxParticles

        // Particles (early epochs)
        if currentEpoch <= .recombination {
            for p in quantumField.particles.prefix(limit) {
                let scaledPos = p.position * spatialScale
                let color = ParticleProperties.displayColor(of: p.particleType)
                let radius: Float = p.particleType == .photon ? 1.5 : 3.0
                entities.append(RenderableEntity(
                    id: p.id,
                    position: scaledPos,
                    color: color,
                    radius: radius,
                    label: p.particleType.rawValue,
                    category: .particle
                ))
            }
        }

        // Atoms
        if currentEpoch >= .recombination {
            for atom in atomicSystem.atoms.prefix(limit / 2) {
                let scaledPos = atom.position * spatialScale
                entities.append(RenderableEntity(
                    id: atom.id + 1_000_000,
                    position: scaledPos,
                    color: atom.displayColor,
                    radius: Float(2.0 + Double(atom.atomicNumber) * 0.3),
                    label: atom.symbol,
                    category: .atom
                ))
            }
        }

        // Molecules
        if currentEpoch >= .earth {
            for mol in chemicalSystem.molecules.prefix(limit / 3) {
                let scaledPos = mol.position * spatialScale
                entities.append(RenderableEntity(
                    id: mol.id + 2_000_000,
                    position: scaledPos,
                    color: mol.displayColor,
                    radius: 5.0,
                    label: mol.formula,
                    category: .molecule
                ))
            }
        }

        // Cells
        if currentEpoch >= .life {
            for cell in biosphere.cells.prefix(SimulationLimits.maxCells) {
                let scaledPos = cell.position * spatialScale
                entities.append(RenderableEntity(
                    id: cell.id + 3_000_000,
                    position: scaledPos,
                    color: cell.displayColor,
                    radius: 8.0,
                    label: "Cell G\(cell.generation)",
                    category: .cell
                ))
            }
        }

        renderables = entities
    }

    // MARK: - Logging

    private func log(_ message: String) {
        let entry = "[\(currentEpoch.displayName) t=\(tick)] \(message)"
        eventLog.append(entry)
        if eventLog.count > maxLogEntries {
            eventLog.removeFirst(eventLog.count - maxLogEntries)
        }
    }

    // MARK: - Progress

    /// Progress through the full simulation (0..1).
    var progress: Double {
        Double(tick) / Double(SimulationLimits.presentEpoch)
    }

    /// Formatted elapsed time in cosmic scale.
    var cosmicTimeDescription: String {
        let fraction = progress
        if fraction < 0.001 {
            return "< 1 second"
        } else if fraction < 0.01 {
            return "\(String(format: "%.0f", fraction * 13.8e9)) years"
        } else {
            return "\(String(format: "%.2f", fraction * 13.8)) billion years"
        }
    }
}
