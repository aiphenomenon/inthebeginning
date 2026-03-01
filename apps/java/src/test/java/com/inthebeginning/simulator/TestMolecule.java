package com.inthebeginning.simulator;

import java.util.*;

/**
 * Tests for Molecule: constructors, formula computation, molecular weight,
 * organic detection, functional groups, compact representation, and toString.
 */
public class TestMolecule {

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

    public static int[] runAll() {
        passed = 0;
        failed = 0;

        System.out.println("  [TestMolecule]");

        testSimpleConstructor();
        testFullConstructor();
        testMoleculeId();
        testAtomsAccessor();
        testNameAccessor();
        testFormulaComputation();
        testFormulaWithCarbonFirst();
        testFormulaNoName();
        testEnergyAccessor();
        testPositionAccessor();
        testIsOrganic();
        testNotOrganic();
        testFunctionalGroups();
        testMolecularWeight();
        testAtomCount();
        testToCompactWithName();
        testToCompactWithoutName();
        testToStringDelegatesToCompact();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testSimpleConstructor() {
        Atom h1 = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h1, o), "HO", new double[]{1.0, 2.0, 3.0});
        assertEquals("Name is HO", "HO", m.name());
        assertNotNull("Formula computed", m.formula());
    }

    private static void testFullConstructor() {
        Atom c = new Atom(6);
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(c, h), "methyl", new double[]{0, 0, 0},
                true, List.of("amino", "carboxyl"));
        assertEquals("Name is methyl", "methyl", m.name());
        assertTrue("Organic flag from constructor", m.isOrganic());
        assertEquals("2 functional groups", 2, m.functionalGroups().size());
        assertEquals("First functional group", "amino", m.functionalGroups().get(0));
        assertEquals("Second functional group", "carboxyl", m.functionalGroups().get(1));
    }

    private static void testMoleculeId() {
        Atom h = new Atom(1);
        Molecule m1 = new Molecule(List.of(h), "H", new double[]{0, 0, 0});
        Molecule m2 = new Molecule(List.of(h), "H", new double[]{0, 0, 0});
        assertTrue("Molecule IDs are unique", m1.moleculeId() != m2.moleculeId());
        assertTrue("Molecule ID > 0", m1.moleculeId() > 0);
    }

    private static void testAtomsAccessor() {
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h1, h2, o), "water", new double[]{0, 0, 0});
        assertEquals("3 atoms", 3, m.atoms().size());
    }

    private static void testNameAccessor() {
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(h), "hydrogen", new double[]{0, 0, 0});
        assertEquals("Name", "hydrogen", m.name());
    }

    private static void testFormulaComputation() {
        // H2O: 2 hydrogen, 1 oxygen
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h1, h2, o), "water", new double[]{0, 0, 0});
        assertEquals("Water formula", "H2O", m.formula());
    }

    private static void testFormulaWithCarbonFirst() {
        // CH4: carbon first, then hydrogen
        Atom c = new Atom(6);
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom h3 = new Atom(1);
        Atom h4 = new Atom(1);
        Molecule m = new Molecule(List.of(c, h1, h2, h3, h4), "methane", new double[]{0, 0, 0});
        assertEquals("Methane formula is CH4", "CH4", m.formula());
    }

    private static void testFormulaNoName() {
        // Molecule with empty name should still compute formula
        Atom n = new Atom(7);
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom h3 = new Atom(1);
        Molecule m = new Molecule(List.of(n, h1, h2, h3), "", new double[]{0, 0, 0});
        assertEquals("NH3 formula", "H3N", m.formula());
    }

    private static void testEnergyAccessor() {
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(h), "H", new double[]{0, 0, 0});
        assertApprox("Initial energy = 0", 0.0, m.energy(), 1e-10);
    }

    private static void testPositionAccessor() {
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(h), "H", new double[]{1.5, 2.5, 3.5});
        assertApprox("Position x", 1.5, m.position()[0], 1e-10);
        assertApprox("Position y", 2.5, m.position()[1], 1e-10);
        assertApprox("Position z", 3.5, m.position()[2], 1e-10);
    }

    private static void testIsOrganic() {
        // Organic: has both C and H
        Atom c = new Atom(6);
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(c, h), "CH", new double[]{0, 0, 0});
        assertTrue("CH is organic", m.isOrganic());
    }

    private static void testNotOrganic() {
        // No carbon => not organic
        Atom h = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h, o), "HO", new double[]{0, 0, 0});
        assertTrue("HO is not organic", !m.isOrganic());

        // Carbon but no hydrogen => not organic
        Atom c = new Atom(6);
        Atom o2 = new Atom(8);
        Molecule m2 = new Molecule(List.of(c, o2), "CO", new double[]{0, 0, 0});
        assertTrue("CO is not organic (no H)", !m2.isOrganic());
    }

    private static void testFunctionalGroups() {
        Atom c = new Atom(6);
        Atom h = new Atom(1);
        // No functional groups by default
        Molecule m1 = new Molecule(List.of(c, h), "CH", new double[]{0, 0, 0});
        assertTrue("No functional groups by default", m1.functionalGroups().isEmpty());

        // With functional groups
        Molecule m2 = new Molecule(List.of(c, h), "CH", new double[]{0, 0, 0},
                true, List.of("hydroxyl", "methyl"));
        assertEquals("2 functional groups", 2, m2.functionalGroups().size());
        assertEquals("First is hydroxyl", "hydroxyl", m2.functionalGroups().get(0));
        assertEquals("Second is methyl", "methyl", m2.functionalGroups().get(1));
    }

    private static void testMolecularWeight() {
        // NH3: N=14, H=1*3 = 17
        Atom n = new Atom(7);
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom h3 = new Atom(1);
        Molecule m = new Molecule(List.of(n, h1, h2, h3), "ammonia", new double[]{0, 0, 0});
        assertApprox("NH3 molecular weight", 17.0, m.molecularWeight(), 0.01);
    }

    private static void testAtomCount() {
        Atom c = new Atom(6);
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Molecule m = new Molecule(List.of(c, h1, h2), "CH2", new double[]{0, 0, 0});
        assertEquals("Atom count = 3", 3, m.atomCount());
    }

    private static void testToCompactWithName() {
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h1, h2, o), "water", new double[]{0, 0, 0});
        String compact = m.toCompact();
        assertTrue("Compact contains 'water'", compact.contains("water"));
        assertTrue("Compact contains 'mw='", compact.contains("mw="));
    }

    private static void testToCompactWithoutName() {
        Atom h = new Atom(1);
        Atom o = new Atom(8);
        Molecule m = new Molecule(List.of(h, o), "", new double[]{0, 0, 0});
        String compact = m.toCompact();
        // When name is empty, formula is used
        assertNotNull("Compact not null", compact);
        assertTrue("Compact contains formula", compact.contains("HO"));
    }

    private static void testToStringDelegatesToCompact() {
        Atom c = new Atom(6);
        Atom h = new Atom(1);
        Molecule m = new Molecule(List.of(c, h), "methyl", new double[]{0, 0, 0});
        assertEquals("toString equals toCompact", m.toCompact(), m.toString());
    }
}
