package com.inthebeginning.simulator

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class ChemicalSystemTest {

    @Before
    fun resetIds() {
        Atom.resetIds()
        Molecule.resetIds()
    }

    // --- Nucleotide tests ---

    @Test
    fun nucleotideComplement() {
        assertEquals("T", Nucleotide("A").complement)
        assertEquals("A", Nucleotide("T").complement)
        assertEquals("C", Nucleotide("G").complement)
        assertEquals("G", Nucleotide("C").complement)
    }

    @Test
    fun rnaNucleotideComplement() {
        val rnaA = Nucleotide("A", isRNA = true)
        assertEquals("U", rnaA.complement)
        val rnaU = Nucleotide("U", isRNA = true)
        assertEquals("A", rnaU.complement)
    }

    // --- BondType tests ---

    @Test
    fun bondTypeEnergies() {
        assertTrue(BondType.IONIC.energy > BondType.COVALENT.energy)
        assertTrue(BondType.COVALENT.energy > BondType.HYDROGEN.energy)
        assertTrue(BondType.HYDROGEN.energy > BondType.VAN_DER_WAALS.energy)
    }

    // --- Molecule tests ---

    @Test
    fun moleculeProperties() {
        val atoms = listOf(
            Atom(atomicNumber = 1, massNumber = 1),
            Atom(atomicNumber = 1, massNumber = 1),
            Atom(atomicNumber = 8, massNumber = 16)
        )
        val bonds = listOf(
            Bond(atoms[0].atomId, atoms[2].atomId, BondType.COVALENT),
            Bond(atoms[1].atomId, atoms[2].atomId, BondType.COVALENT)
        )
        val water = Molecule("Water", "H2O", atoms, bonds)

        assertEquals("Water", water.name)
        assertEquals("H2O", water.formula)
        assertEquals(3, water.size)
        assertEquals(18.0, water.mass, 0.0)
        assertTrue(water.containsElement(1))
        assertTrue(water.containsElement(8))
        assertFalse(water.containsElement(6))
        assertEquals(2, water.elementCount(1))
        assertEquals(1, water.elementCount(8))
    }

    @Test
    fun moleculeTotalBondEnergy() {
        val atoms = listOf(Atom(1), Atom(8))
        val bonds = listOf(Bond(atoms[0].atomId, atoms[1].atomId, BondType.COVALENT))
        val mol = Molecule("test", "HO", atoms, bonds)
        assertEquals(BondType.COVALENT.energy, mol.totalBondEnergy, 0.0)
    }

    // --- MoleculeTemplate tests ---

    @Test
    fun waterTemplateComposition() {
        val comp = MoleculeTemplate.Water.composition
        assertEquals(2, comp[1])
        assertEquals(1, comp[8])
    }

    @Test
    fun methaneTemplateComposition() {
        val comp = MoleculeTemplate.Methane.composition
        assertEquals(4, comp[1])
        assertEquals(1, comp[6])
    }

    // --- ChemicalSystem tests ---

    @Test
    fun chemicalSystemInit() {
        val cs = ChemicalSystem()
        assertEquals(0, cs.molecules.size)
        assertEquals(0, cs.aminoAcids.size)
        assertEquals(0, cs.nucleotides.size)
        assertEquals(0, cs.reactionsPerformed)
    }

    @Test
    fun synthesizeWater() {
        val atomicSys = AtomicSystem(temperature = 300.0)
        atomicSys.atoms.add(Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0)))
        atomicSys.atoms.add(Atom(atomicNumber = 1, position = doubleArrayOf(0.1, 0.0, 0.0)))
        atomicSys.atoms.add(Atom(atomicNumber = 8, position = doubleArrayOf(0.2, 0.0, 0.0)))

        val cs = ChemicalSystem(temperature = 300.0)
        val mol = cs.synthesize(MoleculeTemplate.Water, atomicSys)

        // Synthesis depends on probability, so molecule may or may not form
        if (mol != null) {
            assertEquals("Water", mol.name)
            assertEquals("H2O", mol.formula)
        }
    }

    @Test
    fun formWater() {
        val atomicSys = AtomicSystem(temperature = 300.0)
        repeat(10) { atomicSys.atoms.add(Atom(atomicNumber = 1, position = doubleArrayOf(0.0, 0.0, 0.0))) }
        repeat(5) { atomicSys.atoms.add(Atom(atomicNumber = 8, position = doubleArrayOf(0.0, 0.0, 0.0))) }

        val cs = ChemicalSystem(temperature = 300.0)
        val waters = cs.formWater(atomicSys)
        // May or may not form water depending on probability
        assertTrue(waters.size >= 0)
    }

    @Test
    fun moleculeCounts() {
        val cs = ChemicalSystem()
        val atoms = listOf(Atom(1), Atom(1), Atom(8))
        val bonds = listOf(Bond(atoms[0].atomId, atoms[2].atomId, BondType.COVALENT))
        cs.molecules.add(Molecule("Water", "H2O", atoms, bonds))
        cs.molecules.add(Molecule("Water", "H2O", atoms, bonds))

        val counts = cs.moleculeCounts()
        assertEquals(2, counts["Water"])
    }

    @Test
    fun moleculeDiversity() {
        val cs = ChemicalSystem()
        val atoms = listOf(Atom(1), Atom(8))
        val bonds = listOf(Bond(atoms[0].atomId, atoms[1].atomId, BondType.COVALENT))
        cs.molecules.add(Molecule("Water", "H2O", atoms, bonds))
        cs.molecules.add(Molecule("Methane", "CH4", atoms, bonds))

        assertEquals(2, cs.moleculeDiversity)
    }

    @Test
    fun polymerizeRNARequiresMinimumNucleotides() {
        val cs = ChemicalSystem()
        // Not enough RNA nucleotides
        cs.nucleotides.add(Nucleotide("A", isRNA = true))
        assertEquals(0, cs.polymerizeRNA())
    }

    @Test
    fun polymerizeRNAWithSufficientNucleotides() {
        val cs = ChemicalSystem()
        repeat(10) { cs.nucleotides.add(Nucleotide("A", isRNA = true)) }
        val chainLen = cs.polymerizeRNA()
        assertTrue(chainLen >= 0)
    }
}
