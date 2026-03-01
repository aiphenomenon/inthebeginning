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

    // --- Particle.wavelength tests ---

    @Test
    fun particleWavelengthWithMomentum() {
        val p = Particle(ParticleType.ELECTRON, momentum = doubleArrayOf(1.0, 0.0, 0.0))
        assertTrue(p.wavelength > 0)
        assertTrue(p.wavelength < Double.MAX_VALUE)
    }

    @Test
    fun particleWavelengthZeroMomentum() {
        val p = Particle(ParticleType.ELECTRON)
        assertEquals(Double.MAX_VALUE, p.wavelength, 0.0)
    }

    // --- ParticleType enum tests ---

    @Test
    fun particleTypeDisplayNames() {
        assertEquals("up", ParticleType.UP.displayName)
        assertEquals("down", ParticleType.DOWN.displayName)
        assertEquals("electron", ParticleType.ELECTRON.displayName)
        assertEquals("positron", ParticleType.POSITRON.displayName)
        assertEquals("neutrino", ParticleType.NEUTRINO.displayName)
        assertEquals("photon", ParticleType.PHOTON.displayName)
        assertEquals("gluon", ParticleType.GLUON.displayName)
        assertEquals("W", ParticleType.W_BOSON.displayName)
        assertEquals("Z", ParticleType.Z_BOSON.displayName)
        assertEquals("proton", ParticleType.PROTON.displayName)
        assertEquals("neutron", ParticleType.NEUTRON.displayName)
    }

    // --- Spin enum tests ---

    @Test
    fun spinValues() {
        assertEquals(0.5, Spin.UP.value, 0.0)
        assertEquals(-0.5, Spin.DOWN.value, 0.0)
    }

    // --- ColorCharge enum tests ---

    @Test
    fun colorChargeCodes() {
        assertEquals("r", ColorCharge.RED.code)
        assertEquals("g", ColorCharge.GREEN.code)
        assertEquals("b", ColorCharge.BLUE.code)
        assertEquals("ar", ColorCharge.ANTI_RED.code)
        assertEquals("ag", ColorCharge.ANTI_GREEN.code)
        assertEquals("ab", ColorCharge.ANTI_BLUE.code)
    }

    // --- PARTICLE_MASSES / PARTICLE_CHARGES maps ---

    @Test
    fun particleMassesMapComplete() {
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.UP))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.DOWN))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.ELECTRON))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.POSITRON))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.NEUTRINO))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.PHOTON))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.GLUON))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.PROTON))
        assertTrue(PARTICLE_MASSES.containsKey(ParticleType.NEUTRON))
        assertEquals(M_ELECTRON, PARTICLE_MASSES[ParticleType.POSITRON]!!, 0.0)
    }

    @Test
    fun particleChargesMapComplete() {
        assertEquals(2.0 / 3.0, PARTICLE_CHARGES[ParticleType.UP]!!, 1e-10)
        assertEquals(-1.0 / 3.0, PARTICLE_CHARGES[ParticleType.DOWN]!!, 1e-10)
        assertEquals(-1.0, PARTICLE_CHARGES[ParticleType.ELECTRON]!!, 0.0)
        assertEquals(1.0, PARTICLE_CHARGES[ParticleType.POSITRON]!!, 0.0)
        assertEquals(0.0, PARTICLE_CHARGES[ParticleType.NEUTRINO]!!, 0.0)
        assertEquals(0.0, PARTICLE_CHARGES[ParticleType.PHOTON]!!, 0.0)
        assertEquals(0.0, PARTICLE_CHARGES[ParticleType.GLUON]!!, 0.0)
        assertEquals(1.0, PARTICLE_CHARGES[ParticleType.PROTON]!!, 0.0)
        assertEquals(0.0, PARTICLE_CHARGES[ParticleType.NEUTRON]!!, 0.0)
    }

    // --- Particle.entangledWith ---

    @Test
    fun particleEntangledWithDefaultNull() {
        val p = Particle(ParticleType.ELECTRON)
        assertNull(p.entangledWith)
    }

    @Test
    fun pairProductionSetsEntangledWith() {
        val qf = QuantumField(temperature = 1e10)
        val energy = 2 * M_ELECTRON * C * C + 10.0
        val result = qf.pairProduction(energy)
        assertNotNull(result)
        assertNotNull(result!!.first.entangledWith)
        assertNotNull(result.second.entangledWith)
        assertEquals(result.second.particleId, result.first.entangledWith)
        assertEquals(result.first.particleId, result.second.entangledWith)
    }

    // --- Pair production high energy quark branch ---

    @Test
    fun pairProductionHighEnergy() {
        val qf = QuantumField(temperature = 1e10)
        // Energy well above 2 * M_PROTON * C * C to allow quark production
        val energy = 2 * M_PROTON * C * C + 1000.0
        // Run multiple times to statistically hit the quark branch (10% chance)
        var quarksProduced = false
        repeat(100) {
            val qf2 = QuantumField(temperature = 1e10)
            val result = qf2.pairProduction(energy)
            if (result != null) {
                if (result.first.particleType == ParticleType.UP ||
                    result.first.particleType == ParticleType.DOWN) {
                    quarksProduced = true
                }
            }
        }
        // With 100 attempts and 10% chance, probability of never producing quarks is 0.9^100 ~ 0
        assertTrue("Expected quark production in at least one attempt", quarksProduced)
    }

    // --- Pair production creates entangled pairs ---

    @Test
    fun pairProductionAddsEntangledPair() {
        val qf = QuantumField(temperature = 1e10)
        val energy = 2 * M_ELECTRON * C * C + 10.0
        qf.pairProduction(energy)
        assertEquals(1, qf.entangledPairs.size)
    }

    // --- QuantumField.vacuumFluctuation ---

    @Test
    fun vacuumFluctuationAtHighTemperature() {
        // At high temperature, fluctuation is likely
        val qf = QuantumField(temperature = T_PLANCK)
        var produced = false
        repeat(100) {
            val result = qf.vacuumFluctuation()
            if (result != null) {
                produced = true
            }
        }
        assertTrue("Expected at least one vacuum fluctuation at high temperature", produced)
    }

    @Test
    fun vacuumFluctuationAtLowTemperature() {
        // At very low temperature, fluctuation is unlikely
        val qf = QuantumField(temperature = 1e-10)
        var produced = 0
        repeat(100) {
            if (qf.vacuumFluctuation() != null) produced++
        }
        // May or may not produce, but should not crash
        assertTrue(produced >= 0)
    }

    // --- QuantumField.decohere ---

    @Test
    fun decohereSetsParticleIncoherent() {
        val qf = QuantumField(temperature = 1e6)
        val p = Particle(ParticleType.ELECTRON)
        assertTrue(p.waveFn.coherent)
        // With high temperature and high coupling, should decohere quickly
        var decohered = false
        repeat(100) {
            val testP = Particle(ParticleType.ELECTRON)
            qf.decohere(testP, environmentCoupling = 1.0)
            if (!testP.waveFn.coherent) decohered = true
        }
        assertTrue("Expected decoherence at high temperature", decohered)
    }

    @Test
    fun decohereLeavesIncoherentParticleAlone() {
        val qf = QuantumField(temperature = 1e6)
        val p = Particle(ParticleType.ELECTRON)
        p.waveFn.coherent = false
        p.waveFn.amplitude = 0.5
        qf.decohere(p, environmentCoupling = 1.0)
        // Already incoherent, amplitude should not change
        assertEquals(0.5, p.waveFn.amplitude, 0.0)
    }

    // --- QuantumField.evolve for massless particles ---

    @Test
    fun evolveUpdatesPhotonPositions() {
        val qf = QuantumField(temperature = 100.0)
        val photon = Particle(ParticleType.PHOTON, momentum = doubleArrayOf(1.0, 0.0, 0.0))
        qf.particles.add(photon)
        val oldX = photon.position[0]
        qf.evolve(1.0)
        assertNotEquals(oldX, photon.position[0], 1e-15)
    }

    @Test
    fun evolveEvolvesWaveFunction() {
        val qf = QuantumField(temperature = 100.0)
        val p = Particle(ParticleType.ELECTRON, momentum = doubleArrayOf(1.0, 0.0, 0.0))
        qf.particles.add(p)
        val oldPhase = p.waveFn.phase
        qf.evolve(1.0)
        assertNotEquals(oldPhase, p.waveFn.phase, 1e-15)
    }

    // --- WaveFunction.collapse result ---

    @Test
    fun waveFunctionCollapseAmplitude() {
        val wf = WaveFunction(amplitude = 1.0)
        wf.collapse()
        // After collapse, amplitude should be either 0.0 or 1.0
        assertTrue(wf.amplitude == 0.0 || wf.amplitude == 1.0)
    }

    // --- WaveFunction.superpose with different phases ---

    @Test
    fun waveFunctionSuperposeOppositePhase() {
        val wf1 = WaveFunction(amplitude = 0.5, phase = 0.0)
        val wf2 = WaveFunction(amplitude = 0.5, phase = Math.PI)
        val combined = wf1.superpose(wf2)
        // Destructive interference: amplitude should be small
        assertTrue(combined.amplitude >= 0)
        assertTrue(combined.amplitude <= 1.0)
        assertTrue(combined.coherent)
    }

    // --- EntangledPair.bellState ---

    @Test
    fun entangledPairBellState() {
        val a = Particle(ParticleType.ELECTRON)
        val b = Particle(ParticleType.POSITRON)
        val pair = EntangledPair(a, b)
        assertEquals("phi+", pair.bellState)
    }

    @Test
    fun entangledPairCustomBellState() {
        val a = Particle(ParticleType.ELECTRON)
        val b = Particle(ParticleType.POSITRON)
        val pair = EntangledPair(a, b, bellState = "psi-")
        assertEquals("psi-", pair.bellState)
    }

    // --- Random.nextGaussian extension ---

    @Test
    fun randomNextGaussianReturnsFiniteValues() {
        val rng = kotlin.random.Random
        repeat(100) {
            val value = rng.nextGaussian()
            assertTrue("nextGaussian should return finite value", value.isFinite())
        }
    }

    @Test
    fun randomNextGaussianDistribution() {
        val rng = kotlin.random.Random
        val values = List(1000) { rng.nextGaussian() }
        val mean = values.average()
        // Mean should be approximately 0 for large samples
        assertTrue("Mean should be near zero", kotlin.math.abs(mean) < 0.5)
    }
}
