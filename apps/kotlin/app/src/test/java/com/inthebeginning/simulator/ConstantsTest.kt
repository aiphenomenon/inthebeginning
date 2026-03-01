package com.inthebeginning.simulator

import org.junit.Assert.*
import org.junit.Test

class ConstantsTest {

    @Test
    fun fundamentalConstants() {
        assertEquals(1.0, Constants.C, 0.0)
        assertEquals(0.01, Constants.HBAR, 0.0)
        assertEquals(0.001, Constants.K_B, 0.0)
        assertEquals(1e-6, Constants.G, 0.0)
        assertEquals(1.0 / 137.0, Constants.ALPHA, 1e-12)
        assertEquals(0.1, Constants.E_CHARGE, 0.0)
        assertEquals(Math.PI, Constants.PI_VAL, 1e-15)
    }

    @Test
    fun particleMasses() {
        assertEquals(1.0, Constants.M_ELECTRON, 0.0)
        assertEquals(4.4, Constants.M_UP_QUARK, 0.0)
        assertEquals(9.4, Constants.M_DOWN_QUARK, 0.0)
        assertEquals(1836.0, Constants.M_PROTON, 0.0)
        assertEquals(1839.0, Constants.M_NEUTRON, 0.0)
        assertEquals(0.0, Constants.M_PHOTON, 0.0)
        assertEquals(1e-6, Constants.M_NEUTRINO, 0.0)
    }

    @Test
    fun massHierarchy() {
        assertTrue(Constants.M_PHOTON < Constants.M_NEUTRINO)
        assertTrue(Constants.M_NEUTRINO < Constants.M_ELECTRON)
        assertTrue(Constants.M_ELECTRON < Constants.M_UP_QUARK)
        assertTrue(Constants.M_UP_QUARK < Constants.M_DOWN_QUARK)
        assertTrue(Constants.M_DOWN_QUARK < Constants.M_PROTON)
        assertTrue(Constants.M_PROTON < Constants.M_NEUTRON)
        assertTrue(Constants.M_NEUTRON < Constants.M_W_BOSON)
        assertTrue(Constants.M_W_BOSON < Constants.M_Z_BOSON)
        assertTrue(Constants.M_Z_BOSON < Constants.M_HIGGS)
    }

    @Test
    fun forceCouplings() {
        assertEquals(1.0, Constants.STRONG_COUPLING, 0.0)
        assertEquals(Constants.ALPHA, Constants.EM_COUPLING, 0.0)
        assertTrue(Constants.GRAVITY_COUPLING < Constants.WEAK_COUPLING)
        assertTrue(Constants.WEAK_COUPLING < Constants.EM_COUPLING)
        assertTrue(Constants.EM_COUPLING < Constants.STRONG_COUPLING)
    }

    @Test
    fun bindingEnergiesIncrease() {
        assertTrue(Constants.BINDING_ENERGY_DEUTERIUM < Constants.BINDING_ENERGY_HELIUM4)
        assertTrue(Constants.BINDING_ENERGY_HELIUM4 < Constants.BINDING_ENERGY_CARBON12)
        assertTrue(Constants.BINDING_ENERGY_CARBON12 < Constants.BINDING_ENERGY_IRON56)
    }

    @Test
    fun epochsInChronologicalOrder() {
        assertTrue(Constants.PLANCK_EPOCH < Constants.INFLATION_EPOCH)
        assertTrue(Constants.INFLATION_EPOCH < Constants.ELECTROWEAK_EPOCH)
        assertTrue(Constants.ELECTROWEAK_EPOCH < Constants.QUARK_EPOCH)
        assertTrue(Constants.QUARK_EPOCH < Constants.HADRON_EPOCH)
        assertTrue(Constants.HADRON_EPOCH < Constants.NUCLEOSYNTHESIS_EPOCH)
        assertTrue(Constants.NUCLEOSYNTHESIS_EPOCH < Constants.RECOMBINATION_EPOCH)
        assertTrue(Constants.RECOMBINATION_EPOCH < Constants.STAR_FORMATION_EPOCH)
        assertTrue(Constants.STAR_FORMATION_EPOCH < Constants.SOLAR_SYSTEM_EPOCH)
        assertTrue(Constants.SOLAR_SYSTEM_EPOCH < Constants.EARTH_EPOCH)
        assertTrue(Constants.EARTH_EPOCH < Constants.LIFE_EPOCH)
        assertTrue(Constants.LIFE_EPOCH < Constants.DNA_EPOCH)
        assertTrue(Constants.DNA_EPOCH < Constants.PRESENT_EPOCH)
    }

    @Test
    fun temperatureDecreases() {
        assertTrue(Constants.T_PLANCK > Constants.T_ELECTROWEAK)
        assertTrue(Constants.T_ELECTROWEAK > Constants.T_QUARK_HADRON)
        assertTrue(Constants.T_QUARK_HADRON > Constants.T_NUCLEOSYNTHESIS)
        assertTrue(Constants.T_NUCLEOSYNTHESIS > Constants.T_RECOMBINATION)
        assertTrue(Constants.T_RECOMBINATION > Constants.T_EARTH_SURFACE)
        assertTrue(Constants.T_EARTH_SURFACE > Constants.T_CMB)
    }

    @Test
    fun electronShells() {
        assertArrayEquals(intArrayOf(2, 8, 18, 32, 32, 18, 8), Constants.ELECTRON_SHELLS)
    }

    @Test
    fun bondEnergiesOrdered() {
        assertTrue(Constants.BOND_ENERGY_IONIC > Constants.BOND_ENERGY_COVALENT)
        assertTrue(Constants.BOND_ENERGY_COVALENT > Constants.BOND_ENERGY_HYDROGEN)
        assertTrue(Constants.BOND_ENERGY_HYDROGEN > Constants.BOND_ENERGY_VAN_DER_WAALS)
    }

    @Test
    fun nucleotideBases() {
        assertEquals(listOf("A", "T", "G", "C"), Constants.NUCLEOTIDE_BASES)
    }

    @Test
    fun rnaBases() {
        assertEquals(listOf("A", "U", "G", "C"), Constants.RNA_BASES)
    }

    @Test
    fun aminoAcidsList() {
        assertEquals(20, Constants.AMINO_ACIDS.size)
        assertTrue(Constants.AMINO_ACIDS.contains("Met"))
        assertTrue(Constants.AMINO_ACIDS.contains("Gly"))
    }

    @Test
    fun codonTableStartCodon() {
        assertEquals("Met", Constants.CODON_TABLE["AUG"])
    }

    @Test
    fun codonTableStopCodons() {
        assertEquals("STOP", Constants.CODON_TABLE["UAA"])
        assertEquals("STOP", Constants.CODON_TABLE["UAG"])
        assertEquals("STOP", Constants.CODON_TABLE["UGA"])
    }

    @Test
    fun epochsList() {
        assertEquals(13, EPOCHS.size)
        assertEquals("Planck", EPOCHS.first().name)
        assertEquals(Constants.PLANCK_EPOCH, EPOCHS.first().startTick)
        assertEquals("Present", EPOCHS.last().name)
        assertEquals(Constants.PRESENT_EPOCH, EPOCHS.last().startTick)
    }

    @Test
    fun epigeneticProbabilities() {
        assertTrue(Constants.METHYLATION_PROBABILITY > 0 && Constants.METHYLATION_PROBABILITY < 1)
        assertTrue(Constants.DEMETHYLATION_PROBABILITY > 0 && Constants.DEMETHYLATION_PROBABILITY < 1)
        assertTrue(Constants.HISTONE_ACETYLATION_PROB > 0 && Constants.HISTONE_ACETYLATION_PROB < 1)
        assertTrue(Constants.HISTONE_DEACETYLATION_PROB > 0 && Constants.HISTONE_DEACETYLATION_PROB < 1)
    }

    @Test
    fun nuclearParameters() {
        assertTrue(Constants.NUCLEAR_RADIUS > 0)
        assertTrue(Constants.BINDING_ENERGY_DEUTERIUM > 0)
        assertTrue(Constants.BINDING_ENERGY_HELIUM4 > 0)
        assertTrue(Constants.BINDING_ENERGY_CARBON12 > 0)
        assertTrue(Constants.BINDING_ENERGY_IRON56 > 0)
    }

    @Test
    fun bosonMasses() {
        assertEquals(157000.0, Constants.M_W_BOSON, 0.0)
        assertEquals(178000.0, Constants.M_Z_BOSON, 0.0)
        assertEquals(245000.0, Constants.M_HIGGS, 0.0)
    }

    @Test
    fun stellarCoreTemperature() {
        assertTrue(Constants.T_STELLAR_CORE > Constants.T_RECOMBINATION)
    }

    @Test
    fun chromatinRemodelEnergy() {
        assertTrue(Constants.CHROMATIN_REMODEL_ENERGY > 0)
    }

    @Test
    fun environmentalParameters() {
        assertTrue(Constants.UV_MUTATION_RATE > 0)
        assertTrue(Constants.COSMIC_RAY_MUTATION_RATE > 0)
        assertTrue(Constants.THERMAL_FLUCTUATION > 0)
        assertTrue(Constants.RADIATION_DAMAGE_THRESHOLD > 0)
    }

    @Test
    fun codonTableCoversAllStandardCodons() {
        // There should be 64 possible codons; table has entries for most
        assertTrue(Constants.CODON_TABLE.size > 50)
        // Verify a few specific mappings
        assertEquals("Phe", Constants.CODON_TABLE["UUU"])
        assertEquals("Leu", Constants.CODON_TABLE["UUA"])
        assertEquals("Ile", Constants.CODON_TABLE["AUU"])
        assertEquals("Val", Constants.CODON_TABLE["GUU"])
        assertEquals("Ser", Constants.CODON_TABLE["UCU"])
        assertEquals("Pro", Constants.CODON_TABLE["CCU"])
        assertEquals("Thr", Constants.CODON_TABLE["ACU"])
        assertEquals("Ala", Constants.CODON_TABLE["GCU"])
        assertEquals("Tyr", Constants.CODON_TABLE["UAU"])
        assertEquals("His", Constants.CODON_TABLE["CAU"])
        assertEquals("Gln", Constants.CODON_TABLE["CAA"])
        assertEquals("Asn", Constants.CODON_TABLE["AAU"])
        assertEquals("Lys", Constants.CODON_TABLE["AAA"])
        assertEquals("Asp", Constants.CODON_TABLE["GAU"])
        assertEquals("Glu", Constants.CODON_TABLE["GAA"])
        assertEquals("Cys", Constants.CODON_TABLE["UGU"])
        assertEquals("Trp", Constants.CODON_TABLE["UGG"])
        assertEquals("Arg", Constants.CODON_TABLE["CGU"])
        assertEquals("Gly", Constants.CODON_TABLE["GGU"])
    }

    @Test
    fun epochInfoKeyEventsIsMutable() {
        val epoch = EpochInfo("Test", 0, "Test epoch")
        assertTrue(epoch.keyEvents.isEmpty())
        epoch.keyEvents.add("Test event")
        assertEquals(1, epoch.keyEvents.size)
        assertEquals("Test event", epoch.keyEvents[0])
    }

    @Test
    fun epochInfoFields() {
        val epoch = EpochInfo("TestEpoch", 42, "A test description")
        assertEquals("TestEpoch", epoch.name)
        assertEquals(42, epoch.startTick)
        assertEquals("A test description", epoch.description)
    }

    @Test
    fun epochsDescriptionsNotEmpty() {
        for (epoch in EPOCHS) {
            assertTrue("Epoch ${epoch.name} has empty description", epoch.description.isNotEmpty())
            assertTrue("Epoch ${epoch.name} has empty name", epoch.name.isNotEmpty())
        }
    }

    @Test
    fun electronShellsSum() {
        // Sum of all possible electrons across shells
        val total = Constants.ELECTRON_SHELLS.sum()
        assertEquals(118, total) // Maximum electrons = sum of shell capacities
    }

    @Test
    fun chemistryBondEnergies() {
        assertEquals(3.5, Constants.BOND_ENERGY_COVALENT, 0.0)
        assertEquals(5.0, Constants.BOND_ENERGY_IONIC, 0.0)
        assertEquals(0.2, Constants.BOND_ENERGY_HYDROGEN, 0.0)
        assertEquals(0.01, Constants.BOND_ENERGY_VAN_DER_WAALS, 0.0)
    }
}
