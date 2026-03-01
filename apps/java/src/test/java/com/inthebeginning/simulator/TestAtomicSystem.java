package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for Atom creation, electron shell structure, bonding properties,
 * and AtomicSystem nucleosynthesis and recombination.
 */
public class TestAtomicSystem {

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

        System.out.println("  [TestAtomicSystem]");

        testHydrogenAtom();
        testHeliumAtom();
        testCarbonAtom();
        testOxygenAtom();
        testNeonNobleGas();
        testIonization();
        testElectronCapture();
        testBondingPotential();
        testBondType();
        testBondEnergy();
        testDistance();
        testNucleosynthesis();
        testNucleosynthesisOnlyProtons();
        testStellarNucleosynthesis();
        testElementCounts();
        testAtomicSystemTemperature();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testHydrogenAtom() {
        Atom h = new Atom(1);
        assertEquals("Hydrogen atomic number", 1, h.atomicNumber());
        assertEquals("Hydrogen mass number", 1, h.massNumber());
        assertEquals("Hydrogen symbol", "H", h.symbol());
        assertEquals("Hydrogen name", "Hydrogen", h.name());
        assertEquals("Hydrogen electron count", 1, h.electronCount());
        assertEquals("Hydrogen charge", 0, h.charge());
        assertEquals("Hydrogen valence electrons", 1, h.valenceElectrons());
        assertEquals("Hydrogen needs 1 electron", 1, h.needsElectrons());
        assertTrue("Hydrogen not noble gas", !h.isNobleGas());
        assertTrue("Hydrogen not ion", !h.isIon());
    }

    private static void testHeliumAtom() {
        Atom he = new Atom(2, 4, 0, new double[]{0, 0, 0});
        assertEquals("Helium symbol", "He", he.symbol());
        assertEquals("Helium mass number", 4, he.massNumber());
        assertEquals("Helium electron count", 2, he.electronCount());
        assertTrue("Helium is noble gas", he.isNobleGas());
        assertEquals("Helium valence electrons", 2, he.valenceElectrons());
        assertEquals("Helium needs 0 electrons", 0, he.needsElectrons());
    }

    private static void testCarbonAtom() {
        Atom c = new Atom(6);
        assertEquals("Carbon symbol", "C", c.symbol());
        assertEquals("Carbon atomic number", 6, c.atomicNumber());
        assertEquals("Carbon mass number", 12, c.massNumber());
        assertEquals("Carbon electron count", 6, c.electronCount());
        assertEquals("Carbon valence electrons", 4, c.valenceElectrons());
        assertTrue("Carbon not noble gas", !c.isNobleGas());
        assertApprox("Carbon electronegativity", 2.55, c.electronegativity(), 0.01);
    }

    private static void testOxygenAtom() {
        Atom o = new Atom(8);
        assertEquals("Oxygen symbol", "O", o.symbol());
        assertEquals("Oxygen valence electrons", 6, o.valenceElectrons());
        assertEquals("Oxygen needs 2 electrons", 2, o.needsElectrons());
        assertApprox("Oxygen electronegativity", 3.44, o.electronegativity(), 0.01);
    }

    private static void testNeonNobleGas() {
        Atom ne = new Atom(10);
        assertEquals("Neon symbol", "Ne", ne.symbol());
        assertTrue("Neon is noble gas", ne.isNobleGas());
        assertEquals("Neon needs 0 electrons", 0, ne.needsElectrons());
    }

    private static void testIonization() {
        Atom h = new Atom(1);
        assertTrue("Hydrogen can ionize", h.ionize());
        assertEquals("Ionized hydrogen has 0 electrons", 0, h.electronCount());
        assertEquals("Ionized hydrogen charge = +1", 1, h.charge());
        assertTrue("Ionized hydrogen is ion", h.isIon());
        assertTrue("Cannot ionize further", !h.ionize());
    }

    private static void testElectronCapture() {
        Atom h = new Atom(1);
        h.ionize();
        h.captureElectron();
        assertEquals("After capture, 1 electron", 1, h.electronCount());
        assertEquals("After capture, charge = 0", 0, h.charge());
    }

    private static void testBondingPotential() {
        Atom h1 = new Atom(1);
        Atom h2 = new Atom(1);
        assertTrue("Two H atoms can bond", h1.canBondWith(h2));

        Atom he = new Atom(2, 4, 0, new double[]{0, 0, 0});
        assertTrue("Noble gas cannot bond", !h1.canBondWith(he));
        assertTrue("Cannot bond with noble gas", !he.canBondWith(h1));

        // Fill up bonds to 4
        Atom c = new Atom(6);
        for (int i = 0; i < 4; i++) {
            c.bonds().add(i + 100);
        }
        assertTrue("Cannot bond when 4 bonds already exist", !c.canBondWith(h1));
    }

    private static void testBondType() {
        Atom na = new Atom(11); // Na, electronegativity 0.93
        Atom cl = new Atom(17); // Cl, electronegativity 3.16
        assertEquals("NaCl is ionic", "ionic", na.bondType(cl));

        Atom h = new Atom(1);   // H, electronegativity 2.20
        Atom o = new Atom(8);   // O, electronegativity 3.44
        assertEquals("H-O is polar covalent", "polar_covalent", h.bondType(o));

        Atom c = new Atom(6);   // C, electronegativity 2.55
        Atom h2 = new Atom(1);  // H, electronegativity 2.20
        assertEquals("C-H is covalent", "covalent", c.bondType(h2));
    }

    private static void testBondEnergy() {
        Atom na = new Atom(11);
        Atom cl = new Atom(17);
        assertApprox("Ionic bond energy", BOND_ENERGY_IONIC, na.bondEnergy(cl), 1e-10);

        Atom c = new Atom(6);
        Atom h = new Atom(1);
        assertApprox("Covalent bond energy", BOND_ENERGY_COVALENT, c.bondEnergy(h), 1e-10);
    }

    private static void testDistance() {
        Atom a1 = new Atom(1, 0, 0, new double[]{0, 0, 0});
        Atom a2 = new Atom(1, 0, 0, new double[]{3, 4, 0});
        assertApprox("Distance between atoms", 5.0, a1.distanceTo(a2), 1e-10);
    }

    private static void testNucleosynthesis() {
        Random rng = new Random(42);
        AtomicSystem as = new AtomicSystem(T_NUCLEOSYNTHESIS, rng);

        // 4 protons + 4 neutrons -> 2 He-4
        List<Atom> atoms = as.nucleosynthesis(4, 4);
        assertEquals("2 He-4 atoms formed", 2, atoms.size());
        assertEquals("He-4 atomic number", 2, atoms.get(0).atomicNumber());
        assertEquals("He-4 mass number", 4, atoms.get(0).massNumber());
    }

    private static void testNucleosynthesisOnlyProtons() {
        Random rng = new Random(42);
        AtomicSystem as = new AtomicSystem(T_NUCLEOSYNTHESIS, rng);

        // 5 protons + 0 neutrons -> 5 hydrogen
        List<Atom> atoms = as.nucleosynthesis(5, 0);
        assertEquals("5 hydrogen atoms", 5, atoms.size());
        for (Atom a : atoms) {
            assertEquals("Each is hydrogen", 1, a.atomicNumber());
        }
    }

    private static void testStellarNucleosynthesis() {
        Random rng = new Random(0); // seed 0 for deterministic behavior
        AtomicSystem as = new AtomicSystem(T_STELLAR_CORE, rng);

        // Add lots of helium for triple-alpha
        for (int i = 0; i < 30; i++) {
            as.getAtoms().add(new Atom(2, 4, 0, new double[]{0, 0, 0}));
        }

        // Run multiple times to try to get carbon produced
        List<Atom> newAtoms = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            newAtoms.addAll(as.stellarNucleosynthesis(T_STELLAR_CORE));
        }

        // With 30 helium and 100 attempts, we should get some heavier elements
        boolean hasCarbonOrOxygen = false;
        for (Atom a : as.getAtoms()) {
            if (a.atomicNumber() == 6 || a.atomicNumber() == 8) {
                hasCarbonOrOxygen = true;
                break;
            }
        }
        assertTrue("Stellar nucleosynthesis produced C or O", hasCarbonOrOxygen);
    }

    private static void testElementCounts() {
        Random rng = new Random(42);
        AtomicSystem as = new AtomicSystem(rng);
        as.getAtoms().add(new Atom(1));
        as.getAtoms().add(new Atom(1));
        as.getAtoms().add(new Atom(2, 4, 0, new double[]{0, 0, 0}));

        Map<String, Integer> counts = as.elementCounts();
        assertEquals("2 hydrogen", Integer.valueOf(2), counts.get("H"));
        assertEquals("1 helium", Integer.valueOf(1), counts.get("He"));
    }

    private static void testAtomicSystemTemperature() {
        Random rng = new Random(42);
        AtomicSystem as = new AtomicSystem(5000.0, rng);
        assertApprox("Initial temperature", 5000.0, as.getTemperature(), 1e-10);
        as.setTemperature(1000.0);
        assertApprox("Set temperature", 1000.0, as.getTemperature(), 1e-10);
    }
}
