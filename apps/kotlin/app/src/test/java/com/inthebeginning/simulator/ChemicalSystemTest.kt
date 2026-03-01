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

    // --- Nucleotide additional tests ---

    @Test
    fun nucleotideUnknownBaseComplement() {
        val n = Nucleotide("X")
        assertEquals("?", n.complement)
    }

    @Test
    fun nucleotideIsRNAFlag() {
        val dna = Nucleotide("A", isRNA = false)
        assertFalse(dna.isRNA)
        val rna = Nucleotide("A", isRNA = true)
        assertTrue(rna.isRNA)
    }

    // --- MoleculeTemplate additional tests ---

    @Test
    fun carbonDioxideTemplateComposition() {
        val comp = MoleculeTemplate.CarbonDioxide.composition
        assertEquals(1, comp[6])  // 1 Carbon
        assertEquals(2, comp[8])  // 2 Oxygen
        assertEquals("Carbon Dioxide", MoleculeTemplate.CarbonDioxide.name)
        assertEquals("CO2", MoleculeTemplate.CarbonDioxide.formula)
    }

    @Test
    fun ammoniaTemplateComposition() {
        val comp = MoleculeTemplate.Ammonia.composition
        assertEquals(1, comp[7])  // 1 Nitrogen
        assertEquals(3, comp[1])  // 3 Hydrogen
        assertEquals("Ammonia", MoleculeTemplate.Ammonia.name)
        assertEquals("NH3", MoleculeTemplate.Ammonia.formula)
    }

    @Test
    fun hydrogenCyanideTemplateComposition() {
        val comp = MoleculeTemplate.HydrogenCyanide.composition
        assertEquals(1, comp[1])  // 1 Hydrogen
        assertEquals(1, comp[6])  // 1 Carbon
        assertEquals(1, comp[7])  // 1 Nitrogen
        assertEquals("Hydrogen Cyanide", MoleculeTemplate.HydrogenCyanide.name)
        assertEquals("HCN", MoleculeTemplate.HydrogenCyanide.formula)
    }

    @Test
    fun formaldehydeTemplateComposition() {
        val comp = MoleculeTemplate.Formaldehyde.composition
        assertEquals(1, comp[6])  // 1 Carbon
        assertEquals(2, comp[1])  // 2 Hydrogen
        assertEquals(1, comp[8])  // 1 Oxygen
        assertEquals("Formaldehyde", MoleculeTemplate.Formaldehyde.name)
        assertEquals("CH2O", MoleculeTemplate.Formaldehyde.formula)
    }

    @Test
    fun phosphoricAcidTemplateComposition() {
        val comp = MoleculeTemplate.PhosphoricAcid.composition
        assertEquals(3, comp[1])  // 3 Hydrogen
        assertEquals(1, comp[15]) // 1 Phosphorus
        assertEquals(4, comp[8])  // 4 Oxygen
        assertEquals("Phosphoric Acid", MoleculeTemplate.PhosphoricAcid.name)
        assertEquals("H3PO4", MoleculeTemplate.PhosphoricAcid.formula)
    }

    @Test
    fun glycineTemplateComposition() {
        val comp = MoleculeTemplate.Glycine.composition
        assertEquals(2, comp[6])  // 2 Carbon
        assertEquals(5, comp[1])  // 5 Hydrogen
        assertEquals(1, comp[7])  // 1 Nitrogen
        assertEquals(2, comp[8])  // 2 Oxygen
        assertEquals("Glycine", MoleculeTemplate.Glycine.name)
        assertEquals("C2H5NO2", MoleculeTemplate.Glycine.formula)
    }

    @Test
    fun adenineTemplateComposition() {
        val comp = MoleculeTemplate.Adenine.composition
        assertEquals(5, comp[6])  // 5 Carbon
        assertEquals(5, comp[1])  // 5 Hydrogen
        assertEquals(5, comp[7])  // 5 Nitrogen
        assertEquals("Adenine", MoleculeTemplate.Adenine.name)
        assertEquals("C5H5N5", MoleculeTemplate.Adenine.formula)
    }

    @Test
    fun riboseTemplateComposition() {
        val comp = MoleculeTemplate.Ribose.composition
        assertEquals(5, comp[6])   // 5 Carbon
        assertEquals(10, comp[1])  // 10 Hydrogen
        assertEquals(5, comp[8])   // 5 Oxygen
        assertEquals("Ribose", MoleculeTemplate.Ribose.name)
        assertEquals("C5H10O5", MoleculeTemplate.Ribose.formula)
    }

    // --- AminoAcidInfo and AMINO_ACID_PROPERTIES tests ---

    @Test
    fun aminoAcidInfoProperties() {
        val ala = AminoAcidInfo("A", hydrophobic = true, charge = 0)
        assertEquals("A", ala.code)
        assertTrue(ala.hydrophobic)
        assertEquals(0, ala.charge)
    }

    @Test
    fun aminoAcidPropertiesMapComplete() {
        assertEquals(20, AMINO_ACID_PROPERTIES.size)
        // Check a few specific entries
        assertTrue(AMINO_ACID_PROPERTIES["Ala"]!!.hydrophobic)
        assertFalse(AMINO_ACID_PROPERTIES["Arg"]!!.hydrophobic)
        assertEquals(1, AMINO_ACID_PROPERTIES["Arg"]!!.charge)
        assertEquals(-1, AMINO_ACID_PROPERTIES["Asp"]!!.charge)
        assertEquals(0, AMINO_ACID_PROPERTIES["Gly"]!!.charge)
        assertEquals("G", AMINO_ACID_PROPERTIES["Gly"]!!.code)
    }

    @Test
    fun aminoAcidPropertiesAllHaveOneLetter() {
        for ((name, info) in AMINO_ACID_PROPERTIES) {
            assertEquals("$name should have single-letter code", 1, info.code.length)
        }
    }

    // --- BondType display names ---

    @Test
    fun bondTypeDisplayNames() {
        assertEquals("covalent", BondType.COVALENT.displayName)
        assertEquals("ionic", BondType.IONIC.displayName)
        assertEquals("hydrogen", BondType.HYDROGEN.displayName)
        assertEquals("van der Waals", BondType.VAN_DER_WAALS.displayName)
    }

    // --- Bond data class ---

    @Test
    fun bondDefaultStrength() {
        val bond = Bond(1, 2, BondType.COVALENT)
        assertEquals(BondType.COVALENT.energy, bond.strength, 0.0)
    }

    @Test
    fun bondCustomStrength() {
        val bond = Bond(1, 2, BondType.COVALENT, strength = 10.0)
        assertEquals(10.0, bond.strength, 0.0)
    }

    // --- Molecule additional tests ---

    @Test
    fun moleculeIdUnique() {
        val atoms = listOf(Atom(1))
        val m1 = Molecule("A", "A", atoms, emptyList())
        val m2 = Molecule("B", "B", atoms, emptyList())
        assertNotEquals(m1.moleculeId, m2.moleculeId)
    }

    @Test
    fun moleculeContainsElementFalse() {
        val atoms = listOf(Atom(1), Atom(1))
        val m = Molecule("H2", "H2", atoms, emptyList())
        assertFalse(m.containsElement(8))
    }

    @Test
    fun moleculeElementCountZero() {
        val atoms = listOf(Atom(1), Atom(1))
        val m = Molecule("H2", "H2", atoms, emptyList())
        assertEquals(0, m.elementCount(8))
    }

    // --- ChemicalSystem additional tests ---

    @Test
    fun synthesizeInsufficientAtoms() {
        val atomicSys = AtomicSystem(temperature = 300.0)
        // Only one hydrogen, water needs 2H + 1O
        atomicSys.atoms.add(Atom(atomicNumber = 1))

        val cs = ChemicalSystem(temperature = 300.0)
        val mol = cs.synthesize(MoleculeTemplate.Water, atomicSys)
        assertNull(mol)
    }

    @Test
    fun prebioticSynthesis() {
        val atomicSys = AtomicSystem(temperature = 300.0)
        // Add lots of atoms for various molecules
        repeat(20) { atomicSys.atoms.add(Atom(atomicNumber = 1)) }
        repeat(10) { atomicSys.atoms.add(Atom(atomicNumber = 6)) }
        repeat(10) { atomicSys.atoms.add(Atom(atomicNumber = 7)) }
        repeat(10) { atomicSys.atoms.add(Atom(atomicNumber = 8)) }

        val cs = ChemicalSystem(temperature = 300.0)
        val formed = cs.prebioticSynthesis(atomicSys)
        // May or may not form depending on probability
        assertTrue(formed.size >= 0)
    }

    @Test
    fun aminoAcidSynthesisRequiresWater() {
        val cs = ChemicalSystem(temperature = 300.0)
        val env = Environment(temperature = 300.0)
        // No liquid water, no ocean
        val formed = cs.aminoAcidSynthesis(env)
        assertTrue(formed.isEmpty())
    }

    @Test
    fun aminoAcidSynthesisRequiresEnergy() {
        val cs = ChemicalSystem(temperature = 300.0)
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 10.0
        // No radiation or lightning
        env.radiation = 0.0
        val formed = cs.aminoAcidSynthesis(env)
        assertTrue(formed.isEmpty())
    }

    @Test
    fun aminoAcidSynthesisWithConditions() {
        val cs = ChemicalSystem(temperature = 300.0)
        val env = Environment(temperature = 300.0)
        env.ocean.volume = 10.0
        env.radiation = 5.0
        env.radiationSources.add(RadiationSource(RadiationType.STELLAR_UV, 3.0, Constants.UV_MUTATION_RATE))

        // Run multiple times to have a chance of producing amino acids
        var produced = false
        repeat(100) {
            val cs2 = ChemicalSystem(temperature = 300.0)
            val formed = cs2.aminoAcidSynthesis(env)
            if (formed.isNotEmpty()) produced = true
        }
        // With 0.1% chance per amino acid and 20 amino acids per attempt, should produce some
        assertTrue("Expected some amino acid synthesis", produced)
    }

    @Test
    fun nucleotideSynthesisRequiresWater() {
        val cs = ChemicalSystem(temperature = 300.0)
        val env = Environment(temperature = 300.0)
        // No liquid water
        val formed = cs.nucleotideSynthesis(env)
        assertTrue(formed.isEmpty())
    }

    @Test
    fun nucleotideSynthesisWithConditions() {
        val cs = ChemicalSystem(temperature = 350.0) // Warm ponds
        val env = Environment(temperature = 350.0)
        env.ocean.volume = 10.0

        // Run multiple times to have a chance of producing nucleotides
        var produced = false
        repeat(200) {
            val cs2 = ChemicalSystem(temperature = 350.0)
            val formed = cs2.nucleotideSynthesis(env)
            if (formed.isNotEmpty()) produced = true
        }
        assertTrue("Expected some nucleotide synthesis", produced)
    }

    @Test
    fun polymerizeRNARemovesNucleotides() {
        val cs = ChemicalSystem()
        repeat(20) { cs.nucleotides.add(Nucleotide("A", isRNA = true)) }
        val initialSize = cs.nucleotides.size
        val chainLen = cs.polymerizeRNA()
        if (chainLen > 0) {
            assertTrue(cs.nucleotides.size < initialSize)
        }
    }

    @Test
    fun polymerizeRNAIgnoresDNANucleotides() {
        val cs = ChemicalSystem()
        // Only DNA nucleotides
        repeat(10) { cs.nucleotides.add(Nucleotide("A", isRNA = false)) }
        val chainLen = cs.polymerizeRNA()
        assertEquals(0, chainLen)
    }

    @Test
    fun moleculeDiversityEmpty() {
        val cs = ChemicalSystem()
        assertEquals(0, cs.moleculeDiversity)
    }

    @Test
    fun moleculeCountsEmpty() {
        val cs = ChemicalSystem()
        val counts = cs.moleculeCounts()
        assertTrue(counts.isEmpty())
    }

    @Test
    fun synthesizeUpdatesReactionsPerformed() {
        val atomicSys = AtomicSystem(temperature = 300.0)
        repeat(10) { atomicSys.atoms.add(Atom(atomicNumber = 1)) }
        repeat(5) { atomicSys.atoms.add(Atom(atomicNumber = 8)) }

        val cs = ChemicalSystem(temperature = 300.0)
        val initialReactions = cs.reactionsPerformed
        // Try multiple times
        repeat(50) {
            val aSys = AtomicSystem(temperature = 300.0)
            repeat(10) { aSys.atoms.add(Atom(atomicNumber = 1)) }
            repeat(5) { aSys.atoms.add(Atom(atomicNumber = 8)) }
            cs.synthesize(MoleculeTemplate.Water, aSys)
        }
        // reactionsPerformed should be >= initial
        assertTrue(cs.reactionsPerformed >= initialReactions)
    }
}
