package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.C
import com.inthebeginning.simulator.Constants.M_ELECTRON
import com.inthebeginning.simulator.Constants.M_PROTON
import com.inthebeginning.simulator.Constants.T_PLANCK
import com.inthebeginning.simulator.Constants.T_QUARK_HADRON
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sqrt

class QuantumFieldTest {

    @Before
    fun resetIds() {
        Particle.resetIds()
    }

    // --- WaveFunction tests ---

    @Test
    fun waveFunctionInitialValues() {
        val wf = WaveFunction()
        assertEquals(1.0, wf.amplitude, 0.0)
        assertEquals(0.0, wf.phase, 0.0)
        assertTrue(wf.coherent)
    }

    @Test
    fun waveFunctionProbability() {
        val wf = WaveFunction(amplitude = 0.5)
        assertEquals(0.25, wf.probability, 1e-10)
    }

    @Test
    fun waveFunctionEvolveChangesPhase() {
        val wf = WaveFunction()
        wf.evolve(1.0, 5.0)
        assertNotEquals(0.0, wf.phase, 1e-15)
    }

    @Test
    fun waveFunctionDecoherentDoesNotEvolve() {
        val wf = WaveFunction(coherent = false)
        wf.evolve(1.0, 5.0)
        assertEquals(0.0, wf.phase, 0.0)
    }

    @Test
    fun waveFunctionCollapseSetsIncoherent() {
        val wf = WaveFunction()
        wf.collapse()
        assertFalse(wf.coherent)
    }

    @Test
    fun waveFunctionSuperpose() {
        val wf1 = WaveFunction(amplitude = 0.7, phase = 0.0)
        val wf2 = WaveFunction(amplitude = 0.7, phase = 0.0)
        val combined = wf1.superpose(wf2)
        assertTrue(combined.coherent)
        assertTrue(combined.amplitude > 0)
        assertTrue(combined.amplitude <= 1.0)
    }

    // --- Particle tests ---

    @Test
    fun particleMass() {
        val electron = Particle(ParticleType.ELECTRON)
        assertEquals(M_ELECTRON, electron.mass, 0.0)

        val proton = Particle(ParticleType.PROTON)
        assertEquals(M_PROTON, proton.mass, 0.0)

        val photon = Particle(ParticleType.PHOTON)
        assertEquals(0.0, photon.mass, 0.0)
    }

    @Test
    fun particleCharge() {
        val electron = Particle(ParticleType.ELECTRON)
        assertEquals(-1.0, electron.charge, 0.0)

        val proton = Particle(ParticleType.PROTON)
        assertEquals(1.0, proton.charge, 0.0)

        val photon = Particle(ParticleType.PHOTON)
        assertEquals(0.0, photon.charge, 0.0)
    }

    @Test
    fun particleEnergyNonNegative() {
        val p = Particle(ParticleType.ELECTRON, momentum = doubleArrayOf(1.0, 2.0, 3.0))
        assertTrue(p.energy >= 0)
    }

    @Test
    fun photonZeroMomentumZeroEnergy() {
        val p = Particle(ParticleType.PHOTON)
        assertEquals(0.0, p.energy, 0.0)
    }

    @Test
    fun particleUniqueIds() {
        val p1 = Particle(ParticleType.ELECTRON)
        val p2 = Particle(ParticleType.ELECTRON)
        assertNotEquals(p1.particleId, p2.particleId)
    }

    // --- EntangledPair tests ---

    @Test
    fun entangledPairMeasureAntiCorrelates() {
        val a = Particle(ParticleType.ELECTRON)
        val b = Particle(ParticleType.POSITRON)
        val pair = EntangledPair(a, b)

        pair.measureA()
        // After measurement, spins should be opposite
        assertNotEquals(a.spin, b.spin)
        assertFalse(a.waveFn.coherent)
        assertFalse(b.waveFn.coherent)
    }

    // --- QuantumField tests ---

    @Test
    fun quantumFieldInit() {
        val qf = QuantumField(temperature = 1e10)
        assertEquals(1e10, qf.temperature, 0.0)
        assertEquals(0, qf.particles.size)
        assertEquals(0.0, qf.vacuumEnergy, 0.0)
    }

    @Test
    fun pairProductionCreatesParticles() {
        val qf = QuantumField(temperature = 1e10)
        val energy = 2 * M_ELECTRON * C * C + 10.0
        val result = qf.pairProduction(energy)

        assertNotNull(result)
        assertEquals(2, qf.particles.size)
        assertEquals(2, qf.totalCreated)
    }

    @Test
    fun pairProductionFailsBelowThreshold() {
        val qf = QuantumField(temperature = 1e10)
        val result = qf.pairProduction(0.1)

        assertNull(result)
        assertEquals(0, qf.particles.size)
    }

    @Test
    fun annihilateRemovesParticlesCreatesPhotons() {
        val qf = QuantumField(temperature = 1e10)
        val e = Particle(ParticleType.ELECTRON, momentum = doubleArrayOf(1.0, 0.0, 0.0))
        val p = Particle(ParticleType.POSITRON, momentum = doubleArrayOf(-1.0, 0.0, 0.0))
        qf.particles.add(e)
        qf.particles.add(p)

        val released = qf.annihilate(e, p)
        assertTrue(released > 0)
        val photons = qf.particles.filter { it.particleType == ParticleType.PHOTON }
        assertEquals(2, photons.size)
        assertEquals(2, qf.totalAnnihilated)
    }

    @Test
    fun quarkConfinementBelowTransition() {
        val qf = QuantumField(temperature = T_QUARK_HADRON - 1)
        // 2 ups + 1 down = 1 proton
        repeat(2) { qf.particles.add(Particle(ParticleType.UP)) }
        qf.particles.add(Particle(ParticleType.DOWN))

        val hadrons = qf.quarkConfinement()
        assertTrue(hadrons.isNotEmpty())
        assertTrue(hadrons.any { it.particleType == ParticleType.PROTON })
    }

    @Test
    fun quarkConfinementAboveTransition() {
        val qf = QuantumField(temperature = T_QUARK_HADRON + 1000)
        repeat(2) { qf.particles.add(Particle(ParticleType.UP)) }
        qf.particles.add(Particle(ParticleType.DOWN))

        val hadrons = qf.quarkConfinement()
        assertTrue(hadrons.isEmpty())
    }

    @Test
    fun quarkConfinementFormsNeutrons() {
        val qf = QuantumField(temperature = T_QUARK_HADRON - 1)
        // 1 up + 2 downs = 1 neutron
        qf.particles.add(Particle(ParticleType.UP))
        repeat(2) { qf.particles.add(Particle(ParticleType.DOWN)) }

        val hadrons = qf.quarkConfinement()
        assertTrue(hadrons.isNotEmpty())
        assertTrue(hadrons.any { it.particleType == ParticleType.NEUTRON })
    }

    @Test
    fun coolReducesTemperature() {
        val qf = QuantumField(temperature = 1000.0)
        qf.cool(0.9)
        assertEquals(900.0, qf.temperature, 1e-10)
    }

    @Test
    fun evolveUpdatesPositions() {
        val qf = QuantumField(temperature = 100.0)
        val p = Particle(ParticleType.ELECTRON, momentum = doubleArrayOf(1.0, 0.0, 0.0))
        qf.particles.add(p)
        val oldX = p.position[0]
        qf.evolve(1.0)
        assertNotEquals(oldX, p.position[0], 1e-15)
    }

    @Test
    fun particleCountReturnsCorrectCounts() {
        val qf = QuantumField(temperature = 100.0)
        qf.particles.add(Particle(ParticleType.ELECTRON))
        qf.particles.add(Particle(ParticleType.ELECTRON))
        qf.particles.add(Particle(ParticleType.PHOTON))

        val counts = qf.particleCount()
        assertEquals(2, counts["electron"])
        assertEquals(1, counts["photon"])
    }

    @Test
    fun totalEnergyIncludesVacuumEnergy() {
        val qf = QuantumField(temperature = 100.0)
        qf.vacuumEnergy = 42.0
        assertTrue(qf.totalEnergy() >= 42.0)
    }
}
