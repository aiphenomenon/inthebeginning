package com.inthebeginning.simulator;

/**
 * Test runner that executes all test classes and reports results.
 * Does not use JUnit or any external testing framework.
 */
public class AllTests {

    public static void main(String[] args) {
        System.out.println();
        System.out.println("========================================");
        System.out.println("  In The Beginning - Java Test Suite");
        System.out.println("========================================");
        System.out.println();

        int totalPassed = 0;
        int totalFailed = 0;
        int suitesRun = 0;
        long startTime = System.currentTimeMillis();

        int[] result;

        // 1. Constants
        result = TestConstants.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 2. Quantum Field (WaveFunction, Particle, QuantumField)
        result = TestQuantumField.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 3. Atomic System (Atom, AtomicSystem)
        result = TestAtomicSystem.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 4. Chemical System (Molecule, ChemicalSystem)
        result = TestChemicalSystem.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 5. Biological System (DNA, Lifeform, BiologicalSystem)
        result = TestBiologicalSystem.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 6. Environment
        result = TestEnvironment.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        // 7. Universe (integration tests)
        result = TestUniverse.runAll();
        totalPassed += result[0];
        totalFailed += result[1];
        suitesRun++;

        long elapsed = System.currentTimeMillis() - startTime;

        System.out.println();
        System.out.println("========================================");
        System.out.println("  RESULTS");
        System.out.println("========================================");
        System.out.printf("  Test suites: %d%n", suitesRun);
        System.out.printf("  Tests passed: %d%n", totalPassed);
        System.out.printf("  Tests failed: %d%n", totalFailed);
        System.out.printf("  Total tests:  %d%n", totalPassed + totalFailed);
        System.out.printf("  Time: %d ms%n", elapsed);
        System.out.println("========================================");

        if (totalFailed > 0) {
            System.out.println("  STATUS: SOME TESTS FAILED");
            System.exit(1);
        } else {
            System.out.println("  STATUS: ALL TESTS PASSED");
        }

        System.out.println();
    }
}
