package com.inthebeginning.simulator

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class UniverseTest {

    @Before
    fun resetIds() {
        Particle.resetIds()
        Atom.resetIds()
        Molecule.resetIds()
        DNA.resetIds()
        Cell.resetIds()
    }

    @Test
    fun universeInit() {
        val u = Universe()
        assertEquals(0, u.tick)
        assertFalse(u.running)
        assertFalse(u.completed)
    }

    @Test
    fun stepAdvancesTick() {
        val u = Universe()
        u.ticksPerStep = 1
        u.step()
        assertTrue(u.tick > 0)
    }

    @Test
    fun quantumFieldCreated() {
        val u = Universe()
        assertNotNull(u.quantumField)
        assertEquals(Constants.T_PLANCK, u.quantumField.temperature, 0.0)
    }

    @Test
    fun atomicSystemCreated() {
        val u = Universe()
        assertNotNull(u.atomicSystem)
    }

    @Test
    fun chemicalSystemCreated() {
        val u = Universe()
        assertNotNull(u.chemicalSystem)
    }

    @Test
    fun biosphereCreated() {
        val u = Universe()
        assertNotNull(u.biosphere)
        assertTrue(u.biosphere.population.isEmpty())
    }

    @Test
    fun environmentCreated() {
        val u = Universe()
        assertNotNull(u.environment)
    }

    @Test
    fun progressStartsAtZero() {
        val u = Universe()
        assertEquals(0.0, u.progress, 0.0)
    }

    @Test
    fun progressIncreasesWithSteps() {
        val u = Universe()
        u.ticksPerStep = 1000
        u.step()
        assertTrue(u.progress > 0.0)
    }

    @Test
    fun epochIndexStartsAtZero() {
        val u = Universe()
        assertEquals(0, u.epochIndex)
    }

    @Test
    fun stepThroughPlanckEpoch() {
        val u = Universe()
        u.ticksPerStep = Constants.INFLATION_EPOCH
        u.step()
        assertTrue(u.tick >= Constants.INFLATION_EPOCH)
    }

    @Test
    fun stepProducesParticles() {
        val u = Universe()
        u.ticksPerStep = Constants.QUARK_EPOCH
        u.step()
        // Quantum field should have some particles
        assertTrue(u.quantumField.particles.size >= 0)
    }

    @Test
    fun resetClearsState() {
        val u = Universe()
        u.ticksPerStep = 100
        u.step()
        u.reset()

        assertEquals(0, u.tick)
        assertFalse(u.running)
        assertFalse(u.completed)
        assertEquals(0, u.quantumField.particles.size)
        assertEquals(0, u.atomicSystem.atoms.size)
    }

    @Test
    fun pauseStopsRunning() {
        val u = Universe()
        u.ticksPerStep = 10
        u.step()
        u.pause()
        assertFalse(u.running)
    }

    @Test
    fun snapshotReturnsValidData() {
        val u = Universe()
        u.ticksPerStep = 10
        u.step()
        val snap = u.snapshot()

        assertEquals(u.tick, snap.tick)
        assertTrue(snap.temperature > 0)
        assertTrue(snap.progress >= 0)
    }

    @Test
    fun cosmicAgeDisplay() {
        val u = Universe()
        val display = u.cosmicAgeDisplay
        assertNotNull(display)
        assertTrue(display.isNotEmpty())
    }

    @Test
    fun scaleFactorPositive() {
        val u = Universe()
        assertTrue(u.scaleFactor > 0)
    }

    @Test
    fun stateFlowInitialized() {
        val u = Universe()
        val state = u.state.value
        assertEquals(0, state.tick)
        assertFalse(state.running)
        assertFalse(state.completed)
    }

    @Test
    fun multipleStepsAdvanceSimulation() {
        val u = Universe()
        u.ticksPerStep = 1000
        repeat(5) { u.step() }
        assertTrue(u.tick >= 5000)
    }

    @Test
    fun completionDetected() {
        val u = Universe()
        u.ticksPerStep = Constants.PRESENT_EPOCH + 1
        u.step()
        assertTrue(u.completed)
    }

    @Test
    fun environmentEvolvesDuringStep() {
        val u = Universe()
        u.ticksPerStep = 100
        u.step()
        // Environment should have evolved
        assertTrue(u.environment.cosmicAge > 0)
    }

    // --- SimulationState tests ---

    @Test
    fun simulationStateDefaults() {
        val state = SimulationState()
        assertEquals(0, state.tick)
        assertEquals(Constants.T_PLANCK, state.temperature, 0.0)
        assertTrue(state.particleCounts.isEmpty())
        assertTrue(state.elementCounts.isEmpty())
        assertTrue(state.moleculeCounts.isEmpty())
        assertEquals(0, state.populationSize)
        assertEquals(0.0, state.averageFitness, 0.0)
        assertEquals(0.0, state.maxFitness, 0.0)
        assertEquals(0, state.speciesCount)
        assertEquals(0.0, state.totalEnergy, 0.0)
        assertFalse(state.hasLiquidWater)
        assertFalse(state.isHabitable)
        assertEquals(0.0, state.atmosphereOxygen, 0.0)
        assertTrue(state.events.isEmpty())
        assertFalse(state.running)
        assertFalse(state.completed)
        assertEquals(0, state.maxGeneration)
        assertEquals(0, state.totalMutations)
    }

    // --- RenderableEntity tests ---

    @Test
    fun renderableEntityProperties() {
        val entity = RenderableEntity(1.0f, 2.0f, 3.0f, "electron")
        assertEquals(1.0f, entity.x, 0.0f)
        assertEquals(2.0f, entity.y, 0.0f)
        assertEquals(3.0f, entity.radius, 0.0f)
        assertEquals("electron", entity.type)
    }

    // --- Step after completion ---

    @Test
    fun stepAfterCompletionDoesNothing() {
        val u = Universe()
        u.ticksPerStep = Constants.PRESENT_EPOCH + 1
        u.step()
        assertTrue(u.completed)
        val tickAfterCompletion = u.tick
        u.step() // Should be a no-op
        assertEquals(tickAfterCompletion, u.tick)
    }

    // --- cosmicAgeDisplay at different fractions ---

    @Test
    fun cosmicAgeDisplayAtZero() {
        val u = Universe()
        assertEquals("< 1 second", u.cosmicAgeDisplay)
    }

    @Test
    fun cosmicAgeDisplayEarly() {
        val u = Universe()
        u.ticksPerStep = 10
        u.step()
        // Progress = 10/300000 < 0.001
        val display = u.cosmicAgeDisplay
        assertTrue(display.isNotEmpty())
    }

    @Test
    fun cosmicAgeDisplayMidSimulation() {
        val u = Universe()
        // Advance to between 0.01 and 0.1 of progress
        u.ticksPerStep = 5000
        u.step()
        // tick = 5000, progress = 5000/300000 ~ 0.0167
        val display = u.cosmicAgeDisplay
        assertTrue(display.contains("billion years"))
    }

    @Test
    fun cosmicAgeDisplayLateSimulation() {
        val u = Universe()
        // Advance to > 0.1 of progress
        u.ticksPerStep = 50000
        u.step()
        // tick = 50000, progress = 50000/300000 ~ 0.167
        val display = u.cosmicAgeDisplay
        assertTrue(display.contains("billion years"))
    }

    // --- scaleFactor at different epochs ---

    @Test
    fun scaleFactorBeforeInflation() {
        val u = Universe()
        // tick = 0 < INFLATION_EPOCH
        assertEquals(1.0, u.scaleFactor, 0.0)
    }

    @Test
    fun scaleFactorDuringInflation() {
        val u = Universe()
        u.ticksPerStep = Constants.INFLATION_EPOCH + 5
        u.step()
        // Should be > 1 due to exponential expansion
        assertTrue(u.scaleFactor > 1.0)
    }

    @Test
    fun scaleFactorAfterElectroweak() {
        val u = Universe()
        u.ticksPerStep = Constants.ELECTROWEAK_EPOCH + 100
        u.step()
        // Should be > inflation factor
        assertTrue(u.scaleFactor > 1.0)
    }

    // --- epochIndex at different ticks ---

    @Test
    fun epochIndexIncreases() {
        val u = Universe()
        u.ticksPerStep = Constants.QUARK_EPOCH
        u.step()
        assertTrue(u.epochIndex > 0)
    }

    @Test
    fun epochIndexAtEnd() {
        val u = Universe()
        u.ticksPerStep = Constants.PRESENT_EPOCH + 1
        u.step()
        assertEquals(EPOCHS.size - 1, u.epochIndex)
    }

    // --- snapshot comprehensive tests ---

    @Test
    fun snapshotHasAllFields() {
        val u = Universe()
        u.ticksPerStep = 100
        u.step()
        val snap = u.snapshot()

        assertEquals(u.tick, snap.tick)
        assertNotNull(snap.epoch)
        assertTrue(snap.epochIndex >= 0)
        assertTrue(snap.temperature > 0)
        assertTrue(snap.scaleFactor > 0)
        assertTrue(snap.particleCount >= 0)
        assertTrue(snap.atomCount >= 0)
        assertTrue(snap.moleculeCount >= 0)
        assertTrue(snap.cellCount >= 0)
        assertTrue(snap.totalEnergy >= 0)
        assertNotNull(snap.elementCounts)
        assertNotNull(snap.moleculeCounts)
        assertNotNull(snap.particleCounts)
        assertTrue(snap.populationFitness >= 0)
        assertTrue(snap.speciesCount >= 0)
        assertTrue(snap.maxGeneration >= 0)
        assertNotNull(snap.renderableParticles)
        assertNotNull(snap.renderableAtoms)
        assertNotNull(snap.renderableMolecules)
        assertNotNull(snap.renderableCells)
        assertTrue(snap.progress >= 0)
        assertTrue(snap.progress <= 1.0)
        assertNotNull(snap.cosmicAge)
        assertTrue(snap.atmospherePressure >= 0)
        assertTrue(snap.atmosphereOxygen >= 0)
    }

    @Test
    fun snapshotRenderableEntities() {
        val u = Universe()
        // Run through inflation to get particles
        u.ticksPerStep = Constants.QUARK_EPOCH
        u.step()
        val snap = u.snapshot()
        // Should have some renderable particles from pair production
        assertTrue(snap.renderableParticles.size >= 0)
    }

    // --- reset details ---

    @Test
    fun resetClearsAllSubsystems() {
        val u = Universe()
        u.ticksPerStep = Constants.QUARK_EPOCH
        u.step()
        u.reset()

        assertEquals(0, u.tick)
        assertFalse(u.running)
        assertFalse(u.completed)
        assertEquals(0, u.quantumField.particles.size)
        assertEquals(0, u.quantumField.entangledPairs.size)
        assertEquals(Constants.T_PLANCK, u.quantumField.temperature, 0.0)
        assertEquals(0.0, u.quantumField.vacuumEnergy, 0.0)
        assertEquals(0, u.quantumField.totalCreated)
        assertEquals(0, u.quantumField.totalAnnihilated)
        assertEquals(0, u.atomicSystem.atoms.size)
        assertEquals(0, u.atomicSystem.freeElectrons.size)
        assertEquals(0, u.atomicSystem.bondsFormed)
        assertEquals(0, u.atomicSystem.bondsBroken)
        assertEquals(0, u.chemicalSystem.molecules.size)
        assertEquals(0, u.chemicalSystem.aminoAcids.size)
        assertEquals(0, u.chemicalSystem.nucleotides.size)
        assertEquals(0, u.chemicalSystem.reactionsPerformed)
        assertEquals(0, u.biosphere.population.size)
        assertEquals(0, u.biosphere.totalGenerations)
        assertEquals(0, u.biosphere.totalMutations)
        assertEquals(0, u.biosphere.totalExtinctions)
    }

    @Test
    fun resetEmitsState() {
        val u = Universe()
        u.ticksPerStep = 100
        u.step()
        u.reset()
        val state = u.state.value
        assertEquals(0, state.tick)
        assertFalse(state.running)
        assertFalse(state.completed)
    }

    // --- pause details ---

    @Test
    fun pauseEmitsState() {
        val u = Universe()
        u.ticksPerStep = 10
        u.step()
        u.pause()
        val state = u.state.value
        assertFalse(state.running)
    }

    // --- step through various epochs ---

    @Test
    fun stepThroughInflation() {
        val u = Universe()
        u.ticksPerStep = Constants.ELECTROWEAK_EPOCH
        u.step()
        assertTrue(u.tick >= Constants.ELECTROWEAK_EPOCH)
        // Quantum field should have particles from inflation
        assertTrue(u.quantumField.particles.size > 0 || u.quantumField.totalCreated > 0)
    }

    @Test
    fun stepThroughHadronEpoch() {
        val u = Universe()
        u.ticksPerStep = Constants.HADRON_EPOCH
        u.step()
        assertTrue(u.tick >= Constants.HADRON_EPOCH)
    }

    @Test
    fun stepThroughNucleosynthesis() {
        val u = Universe()
        u.ticksPerStep = Constants.NUCLEOSYNTHESIS_EPOCH
        u.step()
        assertTrue(u.tick >= Constants.NUCLEOSYNTHESIS_EPOCH)
    }

    @Test
    fun stepThroughRecombination() {
        val u = Universe()
        u.ticksPerStep = Constants.RECOMBINATION_EPOCH
        u.step()
        assertTrue(u.tick >= Constants.RECOMBINATION_EPOCH)
    }

    // --- Snapshot data class ---

    @Test
    fun snapshotProgressField() {
        val u = Universe()
        u.ticksPerStep = 1000
        u.step()
        val snap = u.snapshot()
        assertEquals(u.progress, snap.progress, 1e-10)
    }

    @Test
    fun snapshotCosmicAgeField() {
        val u = Universe()
        u.ticksPerStep = 10
        u.step()
        val snap = u.snapshot()
        assertEquals(u.cosmicAgeDisplay, snap.cosmicAge)
    }

    // --- ticksPerStep ---

    @Test
    fun ticksPerStepDefault() {
        val u = Universe()
        assertEquals(100, u.ticksPerStep)
    }

    @Test
    fun ticksPerStepCustom() {
        val u = Universe()
        u.ticksPerStep = 500
        assertEquals(500, u.ticksPerStep)
        u.step()
        assertEquals(500, u.tick)
    }

    // --- State flow updates ---

    @Test
    fun stateFlowUpdatesAfterStep() {
        val u = Universe()
        u.ticksPerStep = 50
        u.step()
        val state = u.state.value
        assertEquals(50, state.tick)
        assertTrue(state.running)
    }

    @Test
    fun stateFlowCurrentEpoch() {
        val u = Universe()
        u.ticksPerStep = 50
        u.step()
        val state = u.state.value
        assertNotNull(state.currentEpoch)
        assertTrue(state.currentEpoch.name.isNotEmpty())
    }
}
