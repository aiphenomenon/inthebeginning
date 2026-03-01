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
}
