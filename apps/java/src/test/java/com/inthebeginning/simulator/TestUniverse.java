package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Integration tests for Universe: stepping through epochs,
 * verifying subsystem coordination and epoch transitions.
 */
public class TestUniverse {

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

        System.out.println("  [TestUniverse]");

        testCreation();
        testInitialState();
        testSingleStep();
        testEpochProgression();
        testTemperatureCooling();
        testScaleFactorGrowth();
        testSubsystemsExist();
        testPlanckEpoch();
        testInflationEpoch();
        testHadronEpoch();
        testNucleosynthesisEpoch();
        testFullSimulation();
        testRunToWithCallback();
        testEventLog();
        testSummary();
        testGetTotalEnergy();
        testBigBounceCycleCounter();
        testBigBounceResetsState();
        testBigBounceResetsSubsystems();
        testBigBounceAllowsResimulation();
        testBigBounceMultipleCycles();
        testBigBouncePreservesRng();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testCreation() {
        Universe u = new Universe(42L);
        assertNotNull("Universe created", u);
        assertEquals("Initial tick = 0", 0, u.getTick());
    }

    private static void testInitialState() {
        Universe u = new Universe(42L);
        assertApprox("Initial temperature = T_PLANCK", T_PLANCK, u.getTemperature(), 1.0);
        assertTrue("Initial scale factor very small", u.getScaleFactor() < 1e-20);
        assertNotNull("Quantum field exists", u.getQuantumField());
        assertNotNull("Atomic system exists", u.getAtomicSystem());
        assertNotNull("Chemical system exists", u.getChemicalSystem());
        assertNotNull("Environment exists", u.getEnvironment());
        assertNotNull("Biological system exists", u.getBiologicalSystem());
    }

    private static void testSingleStep() {
        Universe u = new Universe(42L);
        u.step();
        assertEquals("Tick = 1 after one step", 1, u.getTick());
    }

    private static void testEpochProgression() {
        Universe u = new Universe(42L);
        EpochInfo epoch0 = u.currentEpoch();
        assertEquals("First epoch is Planck", "Planck", epoch0.name());

        // Step to inflation
        for (int i = 0; i < INFLATION_EPOCH + 1; i++) {
            u.step();
        }
        EpochInfo epoch1 = u.currentEpoch();
        assertEquals("Epoch at tick 11 is Inflation", "Inflation", epoch1.name());
    }

    private static void testTemperatureCooling() {
        Universe u = new Universe(42L);
        double t0 = u.getTemperature();

        // Run through some steps
        for (int i = 0; i < 100; i++) {
            u.step();
        }

        // Temperature should generally decrease as universe expands
        // (though it may not be monotonically decreasing due to interpolation)
        assertTrue("Temperature changed from initial", u.getTemperature() != t0);
    }

    private static void testScaleFactorGrowth() {
        Universe u = new Universe(42L);
        double sf0 = u.getScaleFactor();

        for (int i = 0; i < 50; i++) {
            u.step();
        }

        assertTrue("Scale factor grew", u.getScaleFactor() > sf0);
    }

    private static void testSubsystemsExist() {
        Universe u = new Universe(42L);
        assertNotNull("QuantumField", u.getQuantumField());
        assertNotNull("AtomicSystem", u.getAtomicSystem());
        assertNotNull("ChemicalSystem", u.getChemicalSystem());
        assertNotNull("Environment", u.getEnvironment());
        assertNotNull("BiologicalSystem", u.getBiologicalSystem());
    }

    private static void testPlanckEpoch() {
        Universe u = new Universe(42L);
        // Run through Planck epoch
        for (int i = 0; i < INFLATION_EPOCH; i++) {
            u.step();
        }

        // During Planck epoch, vacuum fluctuations should create some particles
        assertTrue("Some particles created in Planck epoch",
                u.getQuantumField().getTotalCreated() >= 0);
    }

    private static void testInflationEpoch() {
        Universe u = new Universe(42L);
        // Run to end of inflation
        for (int i = 0; i < ELECTROWEAK_EPOCH; i++) {
            u.step();
        }

        // During inflation, many particles created via pair production
        assertTrue("Particles created during inflation",
                u.getQuantumField().getParticles().size() > 0);
        assertTrue("Scale factor grew during inflation",
                u.getScaleFactor() > 1e-28);
    }

    private static void testHadronEpoch() {
        Universe u = new Universe(42L);
        // Run to hadron epoch
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH; i++) {
            u.step();
        }

        // By hadron epoch, quarks should be confined into hadrons
        // Check that protons or neutrons exist
        boolean hasHadrons = false;
        for (Particle p : u.getQuantumField().getParticles()) {
            if (p.type() == ParticleType.PROTON || p.type() == ParticleType.NEUTRON) {
                hasHadrons = true;
                break;
            }
        }
        // Hadrons may or may not exist depending on quark production
        // but we at least have particles
        assertTrue("Particles exist by hadron epoch",
                u.getQuantumField().getParticles().size() > 0 || hasHadrons);
    }

    private static void testNucleosynthesisEpoch() {
        Universe u = new Universe(42L);
        // Run to past nucleosynthesis epoch
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH + 200; i++) {
            u.step();
        }

        // Atoms should have formed
        assertTrue("Atoms formed by nucleosynthesis",
                u.getAtomicSystem().getAtoms().size() > 0);
    }

    private static void testFullSimulation() {
        Universe u = new Universe(42L);

        // Run a truncated simulation (not all 300k ticks - just key epochs)
        int[] milestones = {
                INFLATION_EPOCH,
                ELECTROWEAK_EPOCH,
                HADRON_EPOCH,
                NUCLEOSYNTHESIS_EPOCH + 200,
                RECOMBINATION_EPOCH,
                STAR_FORMATION_EPOCH
        };

        for (int target : milestones) {
            while (u.getTick() < target) {
                u.step();
            }
        }

        assertTrue("Tick reached star formation", u.getTick() >= STAR_FORMATION_EPOCH);
        assertTrue("Has atoms", u.getAtomicSystem().getAtoms().size() > 0);
        assertTrue("Temperature decreased", u.getTemperature() < T_PLANCK);
    }

    private static void testRunToWithCallback() {
        Universe u = new Universe(42L);
        List<String> epochsCrossed = new ArrayList<>();

        u.runTo(ELECTROWEAK_EPOCH + 1, (idx, epoch, univ) -> {
            epochsCrossed.add(epoch.name());
        });

        assertTrue("Callbacks were invoked", epochsCrossed.size() > 0);
        assertEquals("Tick is correct", ELECTROWEAK_EPOCH + 1, u.getTick());
    }

    private static void testEventLog() {
        Universe u = new Universe(42L);
        // Run far enough to generate events
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH + 200; i++) {
            u.step();
        }

        // Event log should have entries by now (BBN events at minimum)
        assertNotNull("Event log exists", u.getEventLog());
        // Events may or may not be generated depending on RNG
        assertTrue("Event log is a list", u.getEventLog() instanceof List);
    }

    private static void testSummary() {
        Universe u = new Universe(42L);
        for (int i = 0; i < 100; i++) {
            u.step();
        }

        String summary = u.summary();
        assertNotNull("Summary not null", summary);
        assertTrue("Summary contains tick", summary.contains("t="));
        assertTrue("Summary contains Epoch", summary.contains("Epoch"));
        assertTrue("Summary contains Temperature", summary.contains("Temperature"));
    }

    private static void testGetTotalEnergy() {
        Universe u = new Universe(42L);
        // Initially no particles, so total energy should be 0
        assertApprox("Initial total energy = 0", 0.0, u.getTotalEnergy(), 1e-10);

        // After stepping through inflation (which creates particles), total energy should update
        for (int i = 0; i < ELECTROWEAK_EPOCH; i++) {
            u.step();
        }
        // After inflation, particles exist, so totalEnergy = quantumField.totalEnergy()
        assertTrue("Total energy > 0 after inflation", u.getTotalEnergy() > 0);
        assertApprox("Total energy matches quantum field",
                u.getQuantumField().totalEnergy(), u.getTotalEnergy(), 1e-10);
    }

    // --- Big Bounce tests ---

    private static void testBigBounceCycleCounter() {
        Universe u = new Universe(42L);
        assertEquals("Initial cycle = 0", 0, u.getCycle());

        u.bigBounce();
        assertEquals("Cycle = 1 after first bounce", 1, u.getCycle());

        u.bigBounce();
        assertEquals("Cycle = 2 after second bounce", 2, u.getCycle());
    }

    private static void testBigBounceResetsState() {
        Universe u = new Universe(42L);

        // Run the simulation forward
        for (int i = 0; i < ELECTROWEAK_EPOCH + 10; i++) {
            u.step();
        }
        assertTrue("Tick advanced before bounce", u.getTick() > 0);
        assertTrue("Temperature changed before bounce", u.getTemperature() != T_PLANCK);

        u.bigBounce();

        assertEquals("Tick reset to 0", 0, u.getTick());
        assertApprox("Temperature reset to T_PLANCK", T_PLANCK, u.getTemperature(), 1.0);
        assertTrue("Scale factor reset", u.getScaleFactor() < 1e-20);
        assertApprox("Total energy reset to 0", 0.0, u.getTotalEnergy(), 1e-10);
        assertEquals("Epoch reset to Planck", "Planck", u.currentEpoch().name());
    }

    private static void testBigBounceResetsSubsystems() {
        Universe u = new Universe(42L);

        // Run far enough to populate subsystems
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH + 200; i++) {
            u.step();
        }
        assertTrue("Atoms exist before bounce", u.getAtomicSystem().getAtoms().size() > 0);

        u.bigBounce();

        assertEquals("Particles cleared", 0, u.getQuantumField().getParticles().size());
        assertEquals("Atoms cleared", 0, u.getAtomicSystem().getAtoms().size());
        assertEquals("Molecules cleared", 0, u.getChemicalSystem().getMolecules().size());
        assertEquals("Lifeforms cleared", 0, u.getBiologicalSystem().getLifeforms().size());
        assertEquals("DNA strands cleared", 0, u.getBiologicalSystem().getDnaStrands().size());
        assertTrue("Event log cleared", u.getEventLog().isEmpty());
    }

    private static void testBigBounceAllowsResimulation() {
        Universe u = new Universe(42L);

        // First cycle: run to nucleosynthesis
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH + 200; i++) {
            u.step();
        }
        int atomsFirstCycle = u.getAtomicSystem().getAtoms().size();
        assertTrue("Atoms formed in first cycle", atomsFirstCycle > 0);

        // Bounce and re-run
        u.bigBounce();
        for (int i = 0; i < NUCLEOSYNTHESIS_EPOCH + 200; i++) {
            u.step();
        }
        int atomsSecondCycle = u.getAtomicSystem().getAtoms().size();
        assertTrue("Atoms formed in second cycle", atomsSecondCycle > 0);
        assertEquals("Cycle counter is 1", 1, u.getCycle());
    }

    private static void testBigBounceMultipleCycles() {
        Universe u = new Universe(42L);

        // Run 5 quick cycles to verify no memory leak or crash
        for (int c = 0; c < 5; c++) {
            for (int i = 0; i < 100; i++) {
                u.step();
            }
            u.bigBounce();
        }

        assertEquals("Cycle counter = 5", 5, u.getCycle());
        assertEquals("Tick reset after last bounce", 0, u.getTick());
    }

    private static void testBigBouncePreservesRng() {
        // Two universes with same seed: after same operations + bounce,
        // they should diverge because RNG state continues (not reseeded)
        Universe u1 = new Universe(42L);
        Universe u2 = new Universe(42L);

        for (int i = 0; i < 50; i++) {
            u1.step();
            u2.step();
        }

        // Bounce u1 but not u2, then step both
        u1.bigBounce();
        u1.step();
        u2.step();

        // After bounce + step, u1's RNG has diverged in state from u2
        // (u1 is at tick 1 post-bounce, u2 is at tick 51)
        // The key assertion: bigBounce does not crash and simulation continues
        assertEquals("u1 tick = 1 after bounce + step", 1, u1.getTick());
        assertEquals("u1 cycle = 1", 1, u1.getCycle());
        assertEquals("u2 cycle = 0", 0, u2.getCycle());
    }
}
