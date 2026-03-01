package com.inthebeginning.simulator;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for physical constants, epoch ordering, and simulation parameters.
 */
public class TestConstants {

    private static int passed = 0;
    private static int failed = 0;

    private static void assertEquals(String label, Object expected, Object actual) {
        if (expected.equals(actual)) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected " + expected + " but got " + actual);
        }
    }

    private static void assertTrue(String label, boolean condition) {
        if (condition) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label);
        }
    }

    private static void assertApprox(String label, double expected, double actual, double tolerance) {
        if (Math.abs(expected - actual) < tolerance) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected ~" + expected + " but got " + actual);
        }
    }

    public static int[] runAll() {
        passed = 0;
        failed = 0;

        System.out.println("  [TestConstants]");

        testFundamentalConstants();
        testParticleMasses();
        testForceCouplings();
        testNuclearParameters();
        testEpochOrdering();
        testTemperatureScale();
        testChemistryParameters();
        testBiologyParameters();
        testCodonTable();
        testElements();
        testEpochList();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testFundamentalConstants() {
        assertEquals("C = 1.0", 1.0, C);
        assertEquals("HBAR = 0.01", 0.01, HBAR);
        assertEquals("K_B = 0.001", 0.001, K_B);
        assertEquals("G = 1e-6", 1e-6, G);
        assertApprox("ALPHA ~ 1/137", 1.0 / 137.0, ALPHA, 1e-6);
        assertEquals("E_CHARGE = 0.1", 0.1, E_CHARGE);
        assertApprox("PI ~ 3.14159", Math.PI, PI, 1e-10);
    }

    private static void testParticleMasses() {
        assertEquals("M_ELECTRON = 1.0", 1.0, M_ELECTRON);
        assertTrue("M_UP_QUARK > M_ELECTRON", M_UP_QUARK > M_ELECTRON);
        assertTrue("M_DOWN_QUARK > M_UP_QUARK", M_DOWN_QUARK > M_UP_QUARK);
        assertTrue("M_PROTON > M_NEUTRON is false", M_PROTON < M_NEUTRON);
        assertTrue("M_PROTON >> M_ELECTRON", M_PROTON > 1000 * M_ELECTRON);
        assertEquals("M_PHOTON = 0.0", 0.0, M_PHOTON);
        assertTrue("M_NEUTRINO very small", M_NEUTRINO < 0.001);
        assertTrue("M_HIGGS > M_W_BOSON", M_HIGGS > M_W_BOSON);
        assertTrue("M_W_BOSON > M_Z_BOSON is false", M_W_BOSON < M_Z_BOSON);
    }

    private static void testForceCouplings() {
        assertEquals("STRONG_COUPLING = 1.0", 1.0, STRONG_COUPLING);
        assertApprox("EM_COUPLING = ALPHA", ALPHA, EM_COUPLING, 1e-10);
        assertTrue("STRONG > EM", STRONG_COUPLING > EM_COUPLING);
        assertTrue("EM > WEAK", EM_COUPLING > WEAK_COUPLING);
        assertTrue("WEAK > GRAVITY", WEAK_COUPLING > GRAVITY_COUPLING);
    }

    private static void testNuclearParameters() {
        assertTrue("NUCLEAR_RADIUS > 0", NUCLEAR_RADIUS > 0);
        assertTrue("Binding energy ordering: D < He < C < Fe",
                BINDING_ENERGY_DEUTERIUM < BINDING_ENERGY_HELIUM4
                && BINDING_ENERGY_HELIUM4 < BINDING_ENERGY_CARBON12
                && BINDING_ENERGY_CARBON12 < BINDING_ENERGY_IRON56);
    }

    private static void testEpochOrdering() {
        assertTrue("PLANCK < INFLATION", PLANCK_EPOCH < INFLATION_EPOCH);
        assertTrue("INFLATION < ELECTROWEAK", INFLATION_EPOCH < ELECTROWEAK_EPOCH);
        assertTrue("ELECTROWEAK < QUARK", ELECTROWEAK_EPOCH < QUARK_EPOCH);
        assertTrue("QUARK < HADRON", QUARK_EPOCH < HADRON_EPOCH);
        assertTrue("HADRON < NUCLEOSYNTHESIS", HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
        assertTrue("NUCLEOSYNTHESIS < RECOMBINATION", NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
        assertTrue("RECOMBINATION < STAR_FORMATION", RECOMBINATION_EPOCH < STAR_FORMATION_EPOCH);
        assertTrue("STAR_FORMATION < SOLAR_SYSTEM", STAR_FORMATION_EPOCH < SOLAR_SYSTEM_EPOCH);
        assertTrue("SOLAR_SYSTEM < EARTH", SOLAR_SYSTEM_EPOCH < EARTH_EPOCH);
        assertTrue("EARTH < LIFE", EARTH_EPOCH < LIFE_EPOCH);
        assertTrue("LIFE < DNA", LIFE_EPOCH < DNA_EPOCH);
        assertTrue("DNA < PRESENT", DNA_EPOCH < PRESENT_EPOCH);
    }

    private static void testTemperatureScale() {
        assertTrue("T_PLANCK highest", T_PLANCK > T_ELECTROWEAK);
        assertTrue("T_ELECTROWEAK > T_QUARK_HADRON", T_ELECTROWEAK > T_QUARK_HADRON);
        assertTrue("T_QUARK_HADRON > T_NUCLEOSYNTHESIS", T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
        assertTrue("T_NUCLEOSYNTHESIS > T_RECOMBINATION", T_NUCLEOSYNTHESIS > T_RECOMBINATION);
        assertTrue("T_RECOMBINATION > T_CMB", T_RECOMBINATION > T_CMB);
        assertTrue("T_EARTH_SURFACE > T_CMB", T_EARTH_SURFACE > T_CMB);
        assertApprox("T_CMB ~ 2.725", 2.725, T_CMB, 0.01);
        assertApprox("T_EARTH_SURFACE ~ 288", 288.0, T_EARTH_SURFACE, 1.0);
    }

    private static void testChemistryParameters() {
        assertEquals("ELECTRON_SHELLS length", 7, ELECTRON_SHELLS.length);
        assertEquals("ELECTRON_SHELLS[0] = 2", 2, ELECTRON_SHELLS[0]);
        assertEquals("ELECTRON_SHELLS[1] = 8", 8, ELECTRON_SHELLS[1]);
        assertTrue("BOND_ENERGY_IONIC > COVALENT", BOND_ENERGY_IONIC > BOND_ENERGY_COVALENT);
        assertTrue("BOND_ENERGY_COVALENT > HYDROGEN", BOND_ENERGY_COVALENT > BOND_ENERGY_HYDROGEN);
        assertTrue("BOND_ENERGY_HYDROGEN > VAN_DER_WAALS", BOND_ENERGY_HYDROGEN > BOND_ENERGY_VAN_DER_WAALS);
    }

    private static void testBiologyParameters() {
        assertEquals("NUCLEOTIDE_BASES count", 4, NUCLEOTIDE_BASES.length);
        assertEquals("RNA_BASES count", 4, RNA_BASES.length);
        assertEquals("AMINO_ACIDS count", 20, AMINO_ACIDS.length);
        assertEquals("First nucleotide", "A", NUCLEOTIDE_BASES[0]);
        assertEquals("Last nucleotide", "C", NUCLEOTIDE_BASES[3]);
        assertEquals("First amino acid", "Ala", AMINO_ACIDS[0]);
    }

    private static void testCodonTable() {
        assertTrue("CODON_TABLE not empty", !CODON_TABLE.isEmpty());
        assertEquals("AUG -> Met (start)", "Met", CODON_TABLE.get("AUG"));
        assertEquals("UAA -> STOP", "STOP", CODON_TABLE.get("UAA"));
        assertEquals("UAG -> STOP", "STOP", CODON_TABLE.get("UAG"));
        assertEquals("UGA -> STOP", "STOP", CODON_TABLE.get("UGA"));
        assertEquals("UUU -> Phe", "Phe", CODON_TABLE.get("UUU"));
        assertEquals("GGG -> Gly", "Gly", CODON_TABLE.get("GGG"));

        // Count unique amino acids mapped
        long uniqueAAs = CODON_TABLE.values().stream()
                .filter(v -> !v.equals("STOP"))
                .distinct().count();
        assertEquals("20 unique amino acids in codon table", 20L, uniqueAAs);
    }

    private static void testElements() {
        assertTrue("ELEMENTS not empty", !ELEMENTS.isEmpty());
        assertEquals("Element 1 symbol", "H", ELEMENTS.get(1).symbol());
        assertEquals("Element 1 name", "Hydrogen", ELEMENTS.get(1).name());
        assertEquals("Element 6 symbol", "C", ELEMENTS.get(6).symbol());
        assertEquals("Element 8 symbol", "O", ELEMENTS.get(8).symbol());
        assertEquals("Element 26 symbol", "Fe", ELEMENTS.get(26).symbol());
        assertApprox("Hydrogen electronegativity", 2.20, ELEMENTS.get(1).electronegativity(), 0.01);
        assertApprox("Helium electronegativity", 0.0, ELEMENTS.get(2).electronegativity(), 0.01);
    }

    private static void testEpochList() {
        assertEquals("13 epochs", 13, EPOCHS.size());
        assertEquals("First epoch name", "Planck", EPOCHS.get(0).name());
        assertEquals("Last epoch name", "Present", EPOCHS.get(12).name());
        assertEquals("First epoch tick", PLANCK_EPOCH, EPOCHS.get(0).startTick());
        assertEquals("Last epoch tick", PRESENT_EPOCH, EPOCHS.get(12).startTick());

        // Epochs should be in ascending tick order
        for (int i = 1; i < EPOCHS.size(); i++) {
            assertTrue("Epoch " + i + " tick > epoch " + (i - 1),
                    EPOCHS.get(i).startTick() > EPOCHS.get(i - 1).startTick());
        }
    }
}
