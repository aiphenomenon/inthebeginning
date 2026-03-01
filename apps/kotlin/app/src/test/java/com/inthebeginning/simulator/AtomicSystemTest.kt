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

    // --- ElectronShell tests ---

    @Test
    fun electronShellAddElectron() {
        val shell = ElectronShell(n = 1, maxElectrons = 2, electrons = 0)
        assertTrue(shell.isEmpty)
        assertFalse(shell.isFull)
        assertTrue(shell.addElectron())
        assertEquals(1, shell.electrons)
        assertFalse(shell.isEmpty)
    }

    @Test
    fun electronShellAddElectronWhenFull() {
        val shell = ElectronShell(n = 1, maxElectrons = 2, electrons = 2)
        assertTrue(shell.isFull)
        assertFalse(shell.addElectron())
        assertEquals(2, shell.electrons)
    }

    @Test
    fun electronShellRemoveElectron() {
        val shell = ElectronShell(n = 1, maxElectrons = 2, electrons = 1)
        assertTrue(shell.removeElectron())
        assertEquals(0, shell.electrons)
        assertTrue(shell.isEmpty)
    }

    @Test
    fun electronShellRemoveElectronWhenEmpty() {
        val shell = ElectronShell(n = 1, maxElectrons = 2, electrons = 0)
        assertTrue(shell.isEmpty)
        assertFalse(shell.removeElectron())
        assertEquals(0, shell.electrons)
    }

    @Test
    fun electronShellIsFull() {
        val shell = ElectronShell(n = 1, maxElectrons = 2, electrons = 2)
        assertTrue(shell.isFull)

        val shell2 = ElectronShell(n = 2, maxElectrons = 8, electrons = 7)
        assertFalse(shell2.isFull)
    }

    // --- Atom additional tests ---

    @Test
    fun atomNeedsElectrons() {
        val c = Atom(atomicNumber = 6) // Carbon: 4 valence electrons, needs 4 more
        assertTrue(c.needsElectrons > 0)

        val he = Atom(atomicNumber = 2) // Helium: full shell
        assertEquals(0, he.needsElectrons)
    }

    @Test
    fun atomIsIon() {
        val h = Atom(atomicNumber = 1)
        assertFalse(h.isIon)
        h.ionize()
        assertTrue(h.isIon)
        assertEquals(1, h.charge)
    }

    @Test
    fun atomIonizationEnergyPositive() {
        val h = Atom(atomicNumber = 1)
        assertTrue(h.ionizationEnergy > 0)
    }

    @Test
    fun atomIonizationEnergyUpdatesOnIonize() {
        val h = Atom(atomicNumber = 1)
        val beforeIE = h.ionizationEnergy
        h.ionize()
        // After ionization, the atom has no electrons, ionization energy should be 0
        assertEquals(0.0, h.ionizationEnergy, 0.0)
    }

    @Test
    fun atomSymbolUnknownElement() {
        // Element 99 is not in our ELEMENTS map
        val unknown = Atom(atomicNumber = 99)
        assertEquals("E99", unknown.symbol)
    }

    @Test
    fun atomNameUnknownElement() {
        val unknown = Atom(atomicNumber = 99)
        assertEquals("Element-99", unknown.name)
    }

    @Test
    fun atomElectronegativityUnknownElement() {
        val unknown = Atom(atomicNumber = 99)
        assertEquals(1.0, unknown.electronegativity, 0.0) // default
    }

    @Test
    fun atomBondTypePolarCovalent() {
        // C (2.55) and O (3.44): diff = 0.89 -> polar_covalent (0.4 < diff <= 1.7)
        val c = Atom(atomicNumber = 6)
        val o = Atom(atomicNumber = 8)
        assertEquals("polar_covalent", c.bondType(o))
    }

    @Test
    fun atomBondEnergyPolarCovalent() {
        val c = Atom(atomicNumber = 6)
        val o = Atom(atomicNumber = 8)
        val expected = (Constants.BOND_ENERGY_COVALENT + Constants.BOND_ENERGY_IONIC) / 2.0
        assertEquals(expected, c.bondEnergy(o), 0.0)
    }

    @Test
    fun atomCanBondWithTooManyBonds() {
        val h1 = Atom(atomicNumber = 1)
        val h2 = Atom(atomicNumber = 1)
        // Simulate 4 existing bonds
        repeat(4) { h1.bonds.add(it) }
        assertFalse(h1.canBondWith(h2))
    }

    @Test
    fun atomCanBondWithOtherTooManyBonds() {
        val h1 = Atom(atomicNumber = 1)
        val h2 = Atom(atomicNumber = 1)
        repeat(4) { h2.bonds.add(it) }
        assertFalse(h1.canBondWith(h2))
    }

    @Test
    fun atomDefaultMassNumber() {
        // For hydrogen, default mass = 1
        val h = Atom(atomicNumber = 1)
        assertEquals(1, h.massNumber)

        // For carbon, default mass = 12 (atomicNumber * 2)
        val c = Atom(atomicNumber = 6)
        assertEquals(12, c.massNumber)
    }

    @Test
    fun atomDefaultElectronCount() {
        val o = Atom(atomicNumber = 8)
        assertEquals(8, o.electronCount) // Neutral atom
    }

    @Test
    fun atomCaptureElectronMakesNegativeIon() {
        val h = Atom(atomicNumber = 1)
        h.captureElectron()
        assertEquals(-1, h.charge)
        assertTrue(h.isIon)
    }

    @Test
    fun atomIonizeFailsWithNoElectrons() {
        val h = Atom(atomicNumber = 1)
        assertTrue(h.ionize())  // Remove 1 electron
        assertFalse(h.ionize()) // Can't ionize further
    }

    @Test
    fun atomDistanceToSelf() {
        val a = Atom(atomicNumber = 1, position = doubleArrayOf(1.0, 2.0, 3.0))
        assertEquals(0.0, a.distanceTo(a), 1e-10)
    }

    @Test
    fun atomUniqueIds() {
        val a1 = Atom(atomicNumber = 1)
        val a2 = Atom(atomicNumber = 1)
        assertNotEquals(a1.atomId, a2.atomId)
    }

    // --- ElementData tests ---

    @Test
    fun elementDataProperties() {
        val hydrogen = ELEMENTS[1]!!
        assertEquals("H", hydrogen.symbol)
        assertEquals("Hydrogen", hydrogen.name)
        assertEquals(1, hydrogen.group)
        assertEquals(1, hydrogen.period)
        assertEquals(2.20, hydrogen.electronegativity, 0.01)
    }

    @Test
    fun elementsMapContainsExpected() {
        assertTrue(ELEMENTS.containsKey(1))  // H
        assertTrue(ELEMENTS.containsKey(2))  // He
        assertTrue(ELEMENTS.containsKey(6))  // C
        assertTrue(ELEMENTS.containsKey(8))  // O
        assertTrue(ELEMENTS.containsKey(26)) // Fe
    }

    // --- AtomicSystem additional tests ---

    @Test
    fun stellarNucleosynthesisBelowThreshold() {
        val sys = AtomicSystem()
        // Temperature below 1e3 should return empty
        val newAtoms = sys.stellarNucleosynthesis(500.0)
        assertTrue(newAtoms.isEmpty())
    }

    @Test
    fun stellarNucleosynthesisWithHelium() {
        val sys = AtomicSystem()
        // Add enough helium for triple-alpha process
        repeat(30) {
            sys.atoms.add(Atom(atomicNumber = 2, massNumber = 4))
        }
        // Run multiple times because the triple-alpha process has 1% probability
        var producedCarbon = false
        repeat(200) {
            val sys2 = AtomicSystem()
            repeat(30) {
                sys2.atoms.add(Atom(atomicNumber = 2, massNumber = 4))
            }
            val newAtoms = sys2.stellarNucleosynthesis(1e4)
            if (newAtoms.any { it.atomicNumber == 6 }) {
                producedCarbon = true
            }
        }
        assertTrue("Expected carbon production from triple-alpha process", producedCarbon)
    }

    @Test
    fun attemptBondTooFarApart() {
        val sys = AtomicSystem(temperature = 300.0)
        val h1 = Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0))
        val h2 = Atom(atomicNumber = 1, position = doubleArrayOf(100.0, 0.0, 0.0))
        sys.atoms.add(h1)
        sys.atoms.add(h2)
        // Too far apart, should not bond
        assertFalse(sys.attemptBond(h1, h2))
    }

    @Test
    fun attemptBondNobleGasReturns() {
        val sys = AtomicSystem(temperature = 300.0)
        val he = Atom(atomicNumber = 2)
        val h = Atom(atomicNumber = 1)
        // Noble gas cannot bond
        assertFalse(sys.attemptBond(he, h))
    }

    @Test
    fun attemptBondAtZeroTemperatureCloseAtoms() {
        val sys = AtomicSystem(temperature = 0.0)
        val h1 = Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0))
        val h2 = Atom(atomicNumber = 1, position = doubleArrayOf(0.5, 0.0, 0.0))
        sys.atoms.add(h1)
        sys.atoms.add(h2)
        // At zero temperature and close distance, should bond (prob = 1.0)
        val bonded = sys.attemptBond(h1, h2)
        assertTrue(bonded)
        assertEquals(1, sys.bondsFormed)
    }

    @Test
    fun nucleosynthesisHeliumAndHydrogen() {
        val sys = AtomicSystem()
        // 5 protons and 4 neutrons: 2 He + 1 H
        val newAtoms = sys.nucleosynthesis(5, 4)
        val heliums = newAtoms.filter { it.atomicNumber == 2 }
        val hydrogens = newAtoms.filter { it.atomicNumber == 1 }
        assertEquals(2, heliums.size) // 2 He-4
        assertEquals(1, hydrogens.size) // 1 leftover proton
    }

    @Test
    fun recombinationRemovesParticlesFromField() {
        val sys = AtomicSystem(temperature = T_RECOMBINATION - 100)
        val qf = QuantumField(temperature = sys.temperature)
        qf.particles.add(Particle(ParticleType.PROTON))
        qf.particles.add(Particle(ParticleType.ELECTRON))

        val initialParticles = qf.particles.size
        val newAtoms = sys.recombination(qf)
        assertTrue(newAtoms.isNotEmpty())
        assertTrue(qf.particles.size < initialParticles)
    }
}
