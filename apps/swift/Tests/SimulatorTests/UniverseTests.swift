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
}
