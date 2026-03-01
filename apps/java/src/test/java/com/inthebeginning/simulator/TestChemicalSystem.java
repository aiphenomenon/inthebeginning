package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for Molecule formation and ChemicalSystem reactions.
 */
public class TestChemicalSystem {

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

    private static void assertNotNull(String label, Object obj) {
        if (obj != null) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - was null");
        }
    }

    private static void assertNull(String label, Object obj) {
        if (obj == null) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected null");
        }
    }

    public static int[] runAll() {
        passed = 0;
        failed = 0;

        System.out.println("  [TestChemicalSystem]");

        testMoleculeCreation();
        testMoleculeFormula();
        testMolecularWeight();
        testOrganicDetection();
        testFormWater();
        testFormMethane();
        testFormAmmonia();
        testFormAminoAcid();
        testFormAminoAcidInsufficient();
        testFormNucleotide();
        testFormNucleotideInsufficient();
        testMoleculeCensus();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testMoleculeCreation() {
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom o = new Atom(8);
        Molecule water = new Molecule(List.of(h1, h2, o), "water", new double[]{0, 0, 0});

        assertEquals("Water name", "water", water.name());
        assertEquals("Water atom count", 3, water.atomCount());
        assertTrue("Water molecule ID > 0", water.moleculeId() > 0);
    }

    private static void testMoleculeFormula() {
        Atom c = new Atom(6);
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom h3 = new Atom(1);
        Atom h4 = new Atom(1);
        Molecule methane = new Molecule(List.of(c, h1, h2, h3, h4), "methane", new double[]{0, 0, 0});

        assertEquals("Methane formula", "CH4", methane.formula());
    }

    private static void testMolecularWeight() {
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom o = new Atom(8);
        Molecule water = new Molecule(List.of(h1, h2, o), "water", new double[]{0, 0, 0});

        // H=1, H=1, O=16 -> 18
        assertApprox("Water molecular weight", 18.0, water.molecularWeight(), 0.01);
    }

    private static void testOrganicDetection() {
        // Organic: has both C and H
        Atom c = new Atom(6);
        Atom h = new Atom(1);
        Molecule organic = new Molecule(List.of(c, h), "CH", new double[]{0, 0, 0});
        assertTrue("CH is organic", organic.isOrganic());

        // Inorganic: no carbon
        Atom h1 = new Atom(1);
        Atom o = new Atom(8);
        Molecule inorganic = new Molecule(List.of(h1, o), "HO", new double[]{0, 0, 0});
        assertTrue("HO is not organic", !inorganic.isOrganic());
    }

    /** Helper to create an atomic system with specific element counts. */
    private static AtomicSystem createAtomicSystemWithElements(int nH, int nC, int nN, int nO) {
        Random rng = new Random(42);
        AtomicSystem as = new AtomicSystem(300.0, rng);
        for (int i = 0; i < nH; i++) as.getAtoms().add(new Atom(1));
        for (int i = 0; i < nC; i++) as.getAtoms().add(new Atom(6));
        for (int i = 0; i < nN; i++) as.getAtoms().add(new Atom(7));
        for (int i = 0; i < nO; i++) as.getAtoms().add(new Atom(8));
        return as;
    }

    private static void testFormWater() {
        AtomicSystem as = createAtomicSystemWithElements(4, 0, 0, 2);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        List<Molecule> waters = cs.formWater();
        assertEquals("2 water molecules formed", 2, waters.size());
        assertEquals("Water count tracked", 2, cs.getWaterCount());
        assertEquals("Total molecules = 2", 2, cs.getMolecules().size());
    }

    private static void testFormMethane() {
        AtomicSystem as = createAtomicSystemWithElements(8, 2, 0, 0);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        List<Molecule> methanes = cs.formMethane();
        assertEquals("2 methane molecules formed", 2, methanes.size());
        for (Molecule m : methanes) {
            assertEquals("Methane has 5 atoms", 5, m.atomCount());
        }
    }

    private static void testFormAmmonia() {
        AtomicSystem as = createAtomicSystemWithElements(6, 0, 2, 0);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        List<Molecule> ammonias = cs.formAmmonia();
        assertEquals("2 ammonia molecules formed", 2, ammonias.size());
        for (Molecule m : ammonias) {
            assertEquals("Ammonia has 4 atoms", 4, m.atomCount());
        }
    }

    private static void testFormAminoAcid() {
        // Amino acid requires: 2C + 5H + 2O + 1N
        AtomicSystem as = createAtomicSystemWithElements(5, 2, 1, 2);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        Molecule aa = cs.formAminoAcid("Gly");
        assertNotNull("Amino acid formed", aa);
        assertEquals("Amino acid name", "Gly", aa.name());
        assertTrue("Amino acid is organic", aa.isOrganic());
        assertEquals("Amino acid count", 1, cs.getAminoAcidCount());
        assertEquals("Amino acid has 10 atoms", 10, aa.atomCount());
    }

    private static void testFormAminoAcidInsufficient() {
        // Not enough atoms
        AtomicSystem as = createAtomicSystemWithElements(2, 1, 0, 1);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        Molecule aa = cs.formAminoAcid("Gly");
        assertNull("Amino acid not formed with insufficient atoms", aa);
        assertEquals("Amino acid count = 0", 0, cs.getAminoAcidCount());
    }

    private static void testFormNucleotide() {
        // Nucleotide requires: 5C + 8H + 4O + 2N
        AtomicSystem as = createAtomicSystemWithElements(8, 5, 2, 4);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        Molecule nuc = cs.formNucleotide("A");
        assertNotNull("Nucleotide formed", nuc);
        assertEquals("Nucleotide name", "nucleotide-A", nuc.name());
        assertTrue("Nucleotide is organic", nuc.isOrganic());
        assertEquals("Nucleotide count", 1, cs.getNucleotideCount());
        assertEquals("Nucleotide has 19 atoms", 19, nuc.atomCount());
    }

    private static void testFormNucleotideInsufficient() {
        AtomicSystem as = createAtomicSystemWithElements(2, 1, 0, 1);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        Molecule nuc = cs.formNucleotide("A");
        assertNull("Nucleotide not formed with insufficient atoms", nuc);
        assertEquals("Nucleotide count = 0", 0, cs.getNucleotideCount());
    }

    private static void testMoleculeCensus() {
        AtomicSystem as = createAtomicSystemWithElements(10, 0, 0, 3);
        Random rng = new Random(42);
        ChemicalSystem cs = new ChemicalSystem(as, rng);

        cs.formWater();
        Map<String, Integer> census = cs.moleculeCensus();
        assertTrue("Census contains water", census.containsKey("water"));
        assertEquals("3 water molecules", Integer.valueOf(3), census.get("water"));
    }
}
