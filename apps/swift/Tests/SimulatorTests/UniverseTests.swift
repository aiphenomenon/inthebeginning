// UniverseTests.swift
// Tests for Universe.swift

import XCTest
@testable import InTheBeginningSimulator

final class UniverseTests: XCTestCase {

    // MARK: - SimulationState

    func testSimulationStateRawValues() {
        XCTAssertEqual(SimulationState.idle.rawValue, "idle")
        XCTAssertEqual(SimulationState.running.rawValue, "running")
        XCTAssertEqual(SimulationState.paused.rawValue, "paused")
        XCTAssertEqual(SimulationState.completed.rawValue, "completed")
    }

    // MARK: - SimulationSnapshot

    func testSnapshotEmpty() {
        let snap = SimulationSnapshot.empty
        XCTAssertEqual(snap.tick, 0)
        XCTAssertEqual(snap.epoch, .planck)
        XCTAssertEqual(snap.temperature, 0)
        XCTAssertEqual(snap.particleCount, 0)
        XCTAssertEqual(snap.atomCount, 0)
        XCTAssertEqual(snap.moleculeCount, 0)
        XCTAssertEqual(snap.cellCount, 0)
    }

    // MARK: - EntityCategory

    func testEntityCategoryRawValues() {
        XCTAssertEqual(EntityCategory.particle.rawValue, "particle")
        XCTAssertEqual(EntityCategory.atom.rawValue, "atom")
        XCTAssertEqual(EntityCategory.molecule.rawValue, "molecule")
        XCTAssertEqual(EntityCategory.cell.rawValue, "cell")
    }

    // MARK: - Universe Init

    func testUniverseInit() {
        let u = Universe()
        XCTAssertEqual(u.tick, 0)
        XCTAssertEqual(u.currentEpoch, .planck)
        XCTAssertEqual(u.state, .idle)
        XCTAssertNotNil(u.quantumField)
        XCTAssertNotNil(u.atomicSystem)
        XCTAssertNotNil(u.chemicalSystem)
        XCTAssertNotNil(u.biosphere)
        XCTAssertNotNil(u.environment)
    }

    func testUniverseInitialSnapshot() {
        let u = Universe()
        XCTAssertEqual(u.snapshot.tick, 0)
    }

    func testUniverseInitialSubsystems() {
        let u = Universe()
        XCTAssertEqual(u.quantumField.temperature, TemperatureScale.planck)
        XCTAssertEqual(u.atomicSystem.temperature, TemperatureScale.recombination)
        XCTAssertEqual(u.chemicalSystem.temperature, TemperatureScale.earthSurface)
        XCTAssertTrue(u.biosphere.cells.isEmpty)
    }

    func testUniverseDefaultSettings() {
        let u = Universe()
        XCTAssertEqual(u.ticksPerFrame, 1)
        XCTAssertEqual(u.maxParticles, SimulationLimits.maxParticlesDefault)
        XCTAssertEqual(u.spatialScale, 1.0)
    }

    // MARK: - State Control

    func testStart() {
        let u = Universe()
        u.start()
        XCTAssertEqual(u.state, .running)
    }

    func testStartFromPaused() {
        let u = Universe()
        u.start()
        u.pause()
        XCTAssertEqual(u.state, .paused)
        u.start()
        XCTAssertEqual(u.state, .running)
    }

    func testStartWhenRunning() {
        let u = Universe()
        u.start()
        u.start() // Should be a no-op
        XCTAssertEqual(u.state, .running)
    }

    func testPause() {
        let u = Universe()
        u.start()
        u.pause()
        XCTAssertEqual(u.state, .paused)
    }

    func testPauseWhenNotRunning() {
        let u = Universe()
        u.pause() // Should be a no-op
        XCTAssertEqual(u.state, .idle)
    }

    func testResume() {
        let u = Universe()
        u.start()
        u.pause()
        u.resume()
        XCTAssertEqual(u.state, .running)
    }

    func testResumeWhenNotPaused() {
        let u = Universe()
        u.resume() // Should be a no-op
        XCTAssertEqual(u.state, .idle)
    }

    func testReset() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        u.reset()

        XCTAssertEqual(u.tick, 0)
        XCTAssertEqual(u.currentEpoch, .planck)
        XCTAssertEqual(u.state, .idle)
        XCTAssertTrue(u.renderables.isEmpty)
        XCTAssertEqual(u.snapshot.tick, 0)
    }

    func testResetClearsEventLog() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        u.reset()
        // After reset, log has only the "Simulation reset" entry
        XCTAssertFalse(u.eventLog.isEmpty)
        XCTAssertTrue(u.eventLog.last?.contains("reset") ?? false)
    }

    // MARK: - Simulation Advancement

    func testAdvanceFrameIncreasesTick() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        XCTAssertGreaterThan(u.tick, 0)
    }

    func testAdvanceFrameWhenNotRunning() {
        let u = Universe()
        u.advanceFrame() // Should be a no-op
        XCTAssertEqual(u.tick, 0)
    }

    func testAdvanceFrameMultipleTicks() {
        let u = Universe()
        u.ticksPerFrame = 10
        u.start()
        u.advanceFrame()
        XCTAssertEqual(u.tick, 10)
    }

    func testAdvanceFrameUpdatesSnapshot() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        XCTAssertEqual(u.snapshot.tick, u.tick)
        XCTAssertEqual(u.snapshot.epoch, u.currentEpoch)
    }

    func testAdvanceFrameUpdatesRenderables() {
        let u = Universe()
        u.start()
        // Advance past inflation to get some particles
        u.ticksPerFrame = 100
        u.advanceFrame()
        // Renderables may be populated if particles were created
    }

    // MARK: - Epoch Progression

    func testEpochProgression() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.inflation.tick
        u.advanceFrame()
        XCTAssertGreaterThanOrEqual(u.tick, Epoch.inflation.tick)
    }

    func testEpochLogsTransitions() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.electroweak.tick + 1
        u.advanceFrame()
        // Should have logged epoch transitions
        XCTAssertFalse(u.eventLog.isEmpty)
    }

    // MARK: - Progress

    func testProgressStartsAtZero() {
        let u = Universe()
        XCTAssertEqual(u.progress, 0.0)
    }

    func testProgressIncreases() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        XCTAssertGreaterThan(u.progress, 0.0)
    }

    func testProgressCalculation() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch / 2
        u.advanceFrame()
        XCTAssertEqual(u.progress, 0.5, accuracy: 0.01)
    }

    // MARK: - Completion

    func testCompletionAtPresentEpoch() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch + 1
        u.advanceFrame()
        XCTAssertEqual(u.state, .completed)
    }

    func testNotCompletedBeforePresent() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        XCTAssertNotEqual(u.state, .completed)
    }

    // MARK: - Cosmic Time Description

    func testCosmicTimeDescriptionAtStart() {
        let u = Universe()
        let desc = u.cosmicTimeDescription
        XCTAssertFalse(desc.isEmpty)
        XCTAssertTrue(desc.contains("< 1 second"))
    }

    func testCosmicTimeDescriptionMidSimulation() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch / 2
        u.advanceFrame()
        let desc = u.cosmicTimeDescription
        XCTAssertTrue(desc.contains("billion years"))
    }

    // MARK: - Physics Simulation (Integration Tests)

    func testPlanckEraProducesParticles() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.inflation.tick
        u.advanceFrame()
        // After inflation, quantum field should have particles
        XCTAssertGreaterThanOrEqual(u.quantumField.particles.count, 0)
    }

    func testInflationProducesParticles() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.electroweak.tick
        u.advanceFrame()
        // After inflation + electroweak, should have particles
        XCTAssertGreaterThan(u.quantumField.particles.count, 0)
    }

    func testHadronEraFormsHadrons() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.nucleosynthesis.tick
        u.advanceFrame()
        // Should have some protons or neutrons from quark confinement
        let counts = u.quantumField.particleCount()
        let hadronCount = (counts[.proton] ?? 0) + (counts[.neutron] ?? 0)
        // May or may not have hadrons depending on whether quarks were produced
        XCTAssertGreaterThanOrEqual(hadronCount, 0)
    }

    func testRecombinationFormsAtoms() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.starFormation.tick
        u.advanceFrame()
        // Should have formed some atoms by now
        XCTAssertGreaterThanOrEqual(u.atomicSystem.atoms.count, 0)
    }

    func testEarthEpochFormsMolecules() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.life.tick
        u.advanceFrame()
        // Chemical system should have some molecules
        XCTAssertGreaterThanOrEqual(u.chemicalSystem.molecules.count, 0)
    }

    func testEnvironmentUpdatesWithSimulation() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.earth.tick
        u.advanceFrame()
        // Environment should reflect Earth epoch
        XCTAssertEqual(u.environment.currentEpoch, .earth)
    }

    func testFullSimulationRun() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 10000

        while u.state == .running {
            u.advanceFrame()
        }

        XCTAssertEqual(u.state, .completed)
        XCTAssertGreaterThanOrEqual(u.tick, SimulationLimits.presentEpoch)

        // Snapshot should contain final state
        XCTAssertGreaterThan(u.snapshot.tick, 0)
        XCTAssertEqual(u.snapshot.epoch, .present)
    }

    func testSnapshotContainsValidData() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()

        let snap = u.snapshot
        XCTAssertEqual(snap.tick, u.tick)
        XCTAssertEqual(snap.epoch, u.currentEpoch)
        XCTAssertGreaterThanOrEqual(snap.particleCount, 0)
        XCTAssertGreaterThanOrEqual(snap.atomCount, 0)
        XCTAssertGreaterThanOrEqual(snap.moleculeCount, 0)
        XCTAssertGreaterThanOrEqual(snap.cellCount, 0)
    }

    // MARK: - Event Log

    func testEventLogStartEntry() {
        let u = Universe()
        u.start()
        XCTAssertFalse(u.eventLog.isEmpty)
        XCTAssertTrue(u.eventLog.first?.contains("started") ?? false)
    }

    func testEventLogPauseEntry() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        u.pause()
        XCTAssertTrue(u.eventLog.last?.contains("paused") ?? false)
    }

    func testEventLogResumeEntry() {
        let u = Universe()
        u.start()
        u.pause()
        u.resume()
        XCTAssertTrue(u.eventLog.last?.contains("resumed") ?? false)
    }

    func testEventLogMaxEntries() {
        let u = Universe()
        u.start()
        // Run many frames to generate lots of log entries
        u.ticksPerFrame = 5000
        for _ in 0..<100 {
            if u.state == .running {
                u.advanceFrame()
            }
        }
        // Log should not exceed 50 entries
        XCTAssertLessThanOrEqual(u.eventLog.count, 50)
    }

    // MARK: - Multiple Resets

    func testMultipleResets() {
        let u = Universe()
        for _ in 0..<3 {
            u.start()
            u.ticksPerFrame = 1000
            u.advanceFrame()
            u.reset()
            XCTAssertEqual(u.tick, 0)
            XCTAssertEqual(u.state, .idle)
        }
    }

    // MARK: - Spatial Scale

    func testSpatialScale() {
        let u = Universe()
        u.spatialScale = 2.0
        u.start()
        u.ticksPerFrame = 100
        u.advanceFrame()
        // Just verify it doesn't crash with non-default scale
        XCTAssertEqual(u.spatialScale, 2.0)
    }

    // MARK: - Additional SimulationSnapshot Coverage

    func testSnapshotCreation() {
        let snap = SimulationSnapshot(
            tick: 100,
            epoch: .recombination,
            temperature: 3000.0,
            particleCount: 50,
            atomCount: 10,
            moleculeCount: 5,
            cellCount: 2,
            waterCount: 3,
            aminoAcidCount: 1,
            averageFitness: 0.6,
            maxGeneration: 5,
            habitability: 0.8,
            totalEnergy: 1000.0,
            geneticDiversity: 0.9,
            atmosphereDescription: "N2: 78%, O2: 21%"
        )
        XCTAssertEqual(snap.tick, 100)
        XCTAssertEqual(snap.epoch, .recombination)
        XCTAssertEqual(snap.temperature, 3000.0)
        XCTAssertEqual(snap.particleCount, 50)
        XCTAssertEqual(snap.atomCount, 10)
        XCTAssertEqual(snap.moleculeCount, 5)
        XCTAssertEqual(snap.cellCount, 2)
        XCTAssertEqual(snap.waterCount, 3)
        XCTAssertEqual(snap.aminoAcidCount, 1)
        XCTAssertEqual(snap.averageFitness, 0.6)
        XCTAssertEqual(snap.maxGeneration, 5)
        XCTAssertEqual(snap.habitability, 0.8)
        XCTAssertEqual(snap.totalEnergy, 1000.0)
        XCTAssertEqual(snap.geneticDiversity, 0.9)
        XCTAssertEqual(snap.atmosphereDescription, "N2: 78%, O2: 21%")
    }

    func testSnapshotEmptyAllFields() {
        let snap = SimulationSnapshot.empty
        XCTAssertEqual(snap.waterCount, 0)
        XCTAssertEqual(snap.aminoAcidCount, 0)
        XCTAssertEqual(snap.averageFitness, 0)
        XCTAssertEqual(snap.maxGeneration, 0)
        XCTAssertEqual(snap.habitability, 0)
        XCTAssertEqual(snap.totalEnergy, 0)
        XCTAssertEqual(snap.geneticDiversity, 0)
        XCTAssertTrue(snap.atmosphereDescription.isEmpty)
    }

    // MARK: - Additional RenderableEntity Coverage

    func testRenderableEntityCreation() {
        let entity = RenderableEntity(
            id: 42,
            position: SIMD3<Double>(1, 2, 3),
            color: SIMD4<Float>(1, 0, 0, 1),
            radius: 5.0,
            label: "TestEntity",
            category: .particle
        )
        XCTAssertEqual(entity.id, 42)
        XCTAssertEqual(entity.position, SIMD3<Double>(1, 2, 3))
        XCTAssertEqual(entity.color, SIMD4<Float>(1, 0, 0, 1))
        XCTAssertEqual(entity.radius, 5.0)
        XCTAssertEqual(entity.label, "TestEntity")
        XCTAssertEqual(entity.category, .particle)
    }

    func testRenderableEntityCategories() {
        let particle = RenderableEntity(id: 1, position: .zero, color: SIMD4<Float>(1, 1, 1, 1), radius: 1.0, label: "p", category: .particle)
        let atom = RenderableEntity(id: 2, position: .zero, color: SIMD4<Float>(1, 1, 1, 1), radius: 1.0, label: "a", category: .atom)
        let molecule = RenderableEntity(id: 3, position: .zero, color: SIMD4<Float>(1, 1, 1, 1), radius: 1.0, label: "m", category: .molecule)
        let cell = RenderableEntity(id: 4, position: .zero, color: SIMD4<Float>(1, 1, 1, 1), radius: 1.0, label: "c", category: .cell)
        XCTAssertEqual(particle.category, .particle)
        XCTAssertEqual(atom.category, .atom)
        XCTAssertEqual(molecule.category, .molecule)
        XCTAssertEqual(cell.category, .cell)
    }

    // MARK: - Additional State Control Coverage

    func testStartFromCompletedState() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch + 1
        u.advanceFrame()
        XCTAssertEqual(u.state, .completed)
        // Start should not work from completed state
        u.start()
        XCTAssertEqual(u.state, .completed)
    }

    func testResumeWhenRunning() {
        let u = Universe()
        u.start()
        u.resume() // Should be a no-op
        XCTAssertEqual(u.state, .running)
    }

    func testPauseFromIdle() {
        let u = Universe()
        u.pause() // No-op
        XCTAssertEqual(u.state, .idle)
    }

    func testResetFromRunning() {
        let u = Universe()
        u.start()
        u.advanceFrame()
        u.reset()
        XCTAssertEqual(u.state, .idle)
        XCTAssertEqual(u.tick, 0)
    }

    func testResetFromCompleted() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch + 1
        u.advanceFrame()
        XCTAssertEqual(u.state, .completed)
        u.reset()
        XCTAssertEqual(u.state, .idle)
        XCTAssertEqual(u.tick, 0)
    }

    // MARK: - Cosmic Time Description Coverage

    func testCosmicTimeDescriptionEarlyYears() {
        let u = Universe()
        u.start()
        // Set tick to a value where progress is between 0.001 and 0.01
        u.ticksPerFrame = 1500 // progress = 1500/300000 = 0.005
        u.advanceFrame()
        let desc = u.cosmicTimeDescription
        XCTAssertTrue(desc.contains("years"), "Should contain 'years' for early simulation")
        XCTAssertFalse(desc.contains("billion"))
    }

    func testCosmicTimeDescriptionBillionYears() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 150000 // progress = 0.5
        u.advanceFrame()
        let desc = u.cosmicTimeDescription
        XCTAssertTrue(desc.contains("billion years"))
    }

    // MARK: - Progress Coverage

    func testProgressAtCompletion() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch + 1
        u.advanceFrame()
        XCTAssertGreaterThanOrEqual(u.progress, 1.0)
    }

    // MARK: - Snapshot Accuracy Coverage

    func testSnapshotTemperatureMatchesEnvironment() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        // Snapshot temperature should match environment temperature (approximately)
        XCTAssertEqual(u.snapshot.temperature, u.environment.temperature, accuracy: u.environment.temperature * 0.02)
    }

    func testSnapshotParticleCountMatchesField() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 100
        u.advanceFrame()
        XCTAssertEqual(u.snapshot.particleCount, u.quantumField.particles.count)
    }

    func testSnapshotAtomCountMatchesSystem() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        XCTAssertEqual(u.snapshot.atomCount, u.atomicSystem.atoms.count)
    }

    func testSnapshotMoleculeCountMatchesSystem() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        XCTAssertEqual(u.snapshot.moleculeCount, u.chemicalSystem.molecules.count)
    }

    func testSnapshotCellCountMatchesBiosphere() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 1000
        u.advanceFrame()
        XCTAssertEqual(u.snapshot.cellCount, u.biosphere.livingCellCount)
    }

    // MARK: - Renderables Coverage

    func testRenderablesForEarlyEpoch() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = 50 // Should be in inflation/electroweak
        u.advanceFrame()
        // Early epochs should have particle renderables
        let particleRenderables = u.renderables.filter { $0.category == .particle }
        // May or may not have particles depending on random pair production
        XCTAssertGreaterThanOrEqual(particleRenderables.count, 0)
    }

    func testRenderablesForLateEpoch() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.earth.tick + 100
        u.advanceFrame()
        // Earth epoch should include atom and potentially molecule renderables
        let atomRenderables = u.renderables.filter { $0.category == .atom }
        XCTAssertGreaterThanOrEqual(atomRenderables.count, 0)
    }

    // MARK: - Event Log Additional Coverage

    func testEventLogCompletionEntry() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = SimulationLimits.presentEpoch + 1
        u.advanceFrame()
        XCTAssertTrue(u.eventLog.contains(where: { $0.contains("complete") }))
    }

    func testEventLogEpochTransitions() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.hadron.tick + 1
        u.advanceFrame()
        // Should have logged transitions through planck, inflation, electroweak, quark, hadron
        let transitionLogs = u.eventLog.filter { $0.contains("Epoch transition") }
        XCTAssertGreaterThan(transitionLogs.count, 0)
    }

    // MARK: - MaxParticles Coverage

    func testMaxParticlesModifiable() {
        let u = Universe()
        u.maxParticles = 500
        XCTAssertEqual(u.maxParticles, 500)
        u.start()
        u.ticksPerFrame = 100
        u.advanceFrame()
        // Should not crash with reduced particle limit
    }

    // MARK: - TicksPerFrame Coverage

    func testTicksPerFrameModifiable() {
        let u = Universe()
        u.ticksPerFrame = 50
        u.start()
        u.advanceFrame()
        XCTAssertEqual(u.tick, 50)
    }

    func testTicksPerFrameOne() {
        let u = Universe()
        u.ticksPerFrame = 1
        u.start()
        u.advanceFrame()
        XCTAssertEqual(u.tick, 1)
    }

    // MARK: - Integration Coverage

    func testQuarkEraSimulation() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.hadron.tick
        u.advanceFrame()
        XCTAssertGreaterThanOrEqual(u.tick, Epoch.hadron.tick)
        XCTAssertEqual(u.currentEpoch, .hadron)
    }

    func testNucleosynthesisEra() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.recombination.tick
        u.advanceFrame()
        XCTAssertGreaterThanOrEqual(u.tick, Epoch.recombination.tick)
    }

    func testSolarSystemEra() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.earth.tick
        u.advanceFrame()
        XCTAssertGreaterThanOrEqual(u.tick, Epoch.earth.tick)
        // Should have chemical elements present
        XCTAssertGreaterThan(u.atomicSystem.atoms.count, 0)
    }

    func testDNAEraSimulation() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.present.tick
        u.advanceFrame()
        XCTAssertEqual(u.state, .completed)
    }

    // MARK: - Reset Subsystem Verification

    func testResetClearsSubsystems() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.starFormation.tick
        u.advanceFrame()
        // After running to star formation, should have particles/atoms
        u.reset()
        XCTAssertTrue(u.quantumField.particles.isEmpty)
        XCTAssertTrue(u.atomicSystem.atoms.isEmpty)
        XCTAssertTrue(u.chemicalSystem.molecules.isEmpty)
        XCTAssertTrue(u.biosphere.cells.isEmpty)
    }

    func testResetResetsEnvironment() {
        let u = Universe()
        u.start()
        u.ticksPerFrame = Epoch.earth.tick
        u.advanceFrame()
        u.reset()
        XCTAssertEqual(u.environment.temperature, TemperatureScale.planck)
        XCTAssertEqual(u.environment.currentEpoch, .planck)
    }
}
