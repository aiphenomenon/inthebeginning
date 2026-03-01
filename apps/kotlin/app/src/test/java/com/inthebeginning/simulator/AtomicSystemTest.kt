package com.inthebeginning.simulator

import com.inthebeginning.simulator.Constants.T_RECOMBINATION
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import kotlin.math.abs

class AtomicSystemTest {

    @Before
    fun resetIds() {
        Atom.resetIds()
        Particle.resetIds()
    }

    // --- Atom tests ---

    @Test
    fun hydrogenProperties() {
        val h = Atom(atomicNumber = 1, massNumber = 1)
        assertEquals(1, h.atomicNumber)
        assertEquals("H", h.symbol)
        assertEquals("Hydrogen", h.name)
        assertEquals(1, h.electronCount)
    }

    @Test
    fun heliumMassNumber() {
        val he = Atom(atomicNumber = 2, massNumber = 4)
        assertEquals(4, he.massNumber)
        assertEquals("He", he.symbol)
    }

    @Test
    fun carbonElectronegativity() {
        val c = Atom(atomicNumber = 6)
        assertEquals(2.55, c.electronegativity, 0.01)
    }

    @Test
    fun oxygenShells() {
        val o = Atom(atomicNumber = 8)
        assertEquals(8, o.electronCount)
        assertEquals(2, o.shells.size)
        assertEquals(2, o.shells[0].electrons)
        assertEquals(2, o.shells[0].maxElectrons)
        assertEquals(6, o.shells[1].electrons)
    }

    @Test
    fun nobleGasDetection() {
        val he = Atom(atomicNumber = 2)
        assertTrue(he.isNobleGas)
        val ne = Atom(atomicNumber = 10)
        assertTrue(ne.isNobleGas)
    }

    @Test
    fun valenceElectrons() {
        val c = Atom(atomicNumber = 6)
        assertEquals(4, c.valenceElectrons)
        val o = Atom(atomicNumber = 8)
        assertEquals(6, o.valenceElectrons)
    }

    @Test
    fun neutralAtomCharge() {
        val h = Atom(atomicNumber = 1)
        assertEquals(0, h.charge)
    }

    @Test
    fun ionization() {
        val h = Atom(atomicNumber = 1)
        assertTrue(h.ionize())
        assertEquals(1, h.charge)
    }

    @Test
    fun captureElectron() {
        val h = Atom(atomicNumber = 1)
        h.ionize()
        assertTrue(h.captureElectron())
        assertEquals(0, h.charge)
    }

    @Test
    fun nobleGasCannotBond() {
        val he = Atom(atomicNumber = 2)
        val h = Atom(atomicNumber = 1)
        assertFalse(he.canBondWith(h))
    }

    @Test
    fun bondTypeClassification() {
        val na = Atom(atomicNumber = 11)
        val cl = Atom(atomicNumber = 17)
        assertEquals("ionic", na.bondType(cl))

        val c = Atom(atomicNumber = 6)
        val h = Atom(atomicNumber = 1)
        assertEquals("covalent", c.bondType(h))
    }

    @Test
    fun bondEnergyValues() {
        val na = Atom(atomicNumber = 11)
        val cl = Atom(atomicNumber = 17)
        assertEquals(Constants.BOND_ENERGY_IONIC, na.bondEnergy(cl), 0.0)

        val c = Atom(atomicNumber = 6)
        val h = Atom(atomicNumber = 1)
        assertEquals(Constants.BOND_ENERGY_COVALENT, c.bondEnergy(h), 0.0)
    }

    @Test
    fun distanceTo() {
        val a1 = Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0))
        val a2 = Atom(atomicNumber = 1, position = doubleArrayOf(3.0, 4.0, 0.0))
        assertEquals(5.0, a1.distanceTo(a2), 1e-10)
    }

    // --- AtomicSystem tests ---

    @Test
    fun atomicSystemInit() {
        val sys = AtomicSystem()
        assertEquals(0, sys.atoms.size)
        assertEquals(0, sys.bondsFormed)
    }

    @Test
    fun nucleosynthesisCreatesAtoms() {
        val sys = AtomicSystem()
        val newAtoms = sys.nucleosynthesis(4, 4)
        assertTrue(newAtoms.isNotEmpty())
        val heliums = newAtoms.filter { it.atomicNumber == 2 }
        assertTrue(heliums.isNotEmpty())
    }

    @Test
    fun nucleosynthesisLeftoverHydrogen() {
        val sys = AtomicSystem()
        val newAtoms = sys.nucleosynthesis(3, 0)
        val hydrogens = newAtoms.filter { it.atomicNumber == 1 }
        assertEquals(3, hydrogens.size)
    }

    @Test
    fun elementCountsCorrect() {
        val sys = AtomicSystem()
        sys.atoms.add(Atom(atomicNumber = 1))
        sys.atoms.add(Atom(atomicNumber = 1))
        sys.atoms.add(Atom(atomicNumber = 8))

        val counts = sys.elementCounts()
        assertEquals(2, counts["H"])
        assertEquals(1, counts["O"])
    }

    @Test
    fun recombinationCapturesElectrons() {
        val sys = AtomicSystem(temperature = T_RECOMBINATION - 100)
        val qf = QuantumField(temperature = sys.temperature)
        qf.particles.add(Particle(ParticleType.PROTON))
        qf.particles.add(Particle(ParticleType.ELECTRON))

        val newAtoms = sys.recombination(qf)
        assertTrue(newAtoms.isNotEmpty())
        assertEquals(1, newAtoms[0].atomicNumber)
    }

    @Test
    fun recombinationDoesNothingAboveThreshold() {
        val sys = AtomicSystem(temperature = T_RECOMBINATION + 100)
        val qf = QuantumField(temperature = sys.temperature)
        qf.particles.add(Particle(ParticleType.PROTON))
        qf.particles.add(Particle(ParticleType.ELECTRON))

        val newAtoms = sys.recombination(qf)
        assertTrue(newAtoms.isEmpty())
    }

    @Test
    fun attemptBondBetweenCompatibleAtoms() {
        val sys = AtomicSystem(temperature = 300.0)
        val h1 = Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0))
        val h2 = Atom(atomicNumber = 1, position = doubleArrayOf(1.0, 0.0, 0.0))
        sys.atoms.add(h1)
        sys.atoms.add(h2)

        // Bond may or may not form depending on probability, but it should not crash
        sys.attemptBond(h1, h2)
    }
}
