package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for BiologicalSystem: DNA, Lifeform, abiogenesis,
 * replication, mutation, evolution, and fitness.
 */
public class TestBiologicalSystem {

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

        System.out.println("  [TestBiologicalSystem]");

        testDNACreation();
        testDNATranscription();
        testDNATranslation();
        testDNAReplication();
        testDNAReplicationMutation();
        testDNAGCContent();
        testLifeformCreation();
        testLifeformTick();
        testLifeformReproduction();
        testLifeformDeadCannotReproduce();
        testAbiogenesis();
        testSpawnLifeform();
        testEvolution();
        testReplicateDNA();
        testUVRadiationEvent();
        testAliveCount();
        testAverageFitness();
        testSpeciesCensus();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testDNACreation() {
        List<String> seq = List.of("A", "T", "G", "C", "A", "T");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        assertEquals("DNA length", 6, dna.length());
        assertEquals("DNA generation", 0, dna.generation());
        assertEquals("DNA mutations", 0, dna.mutations());
    }

    private static void testDNATranscription() {
        List<String> seq = List.of("A", "T", "G", "C");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        List<String> rna = dna.transcribeToRNA();

        assertEquals("RNA length = DNA length", 4, rna.size());
        assertEquals("A stays A", "A", rna.get(0));
        assertEquals("T becomes U", "U", rna.get(1));
        assertEquals("G stays G", "G", rna.get(2));
        assertEquals("C stays C", "C", rna.get(3));
    }

    private static void testDNATranslation() {
        // AUG (Met), UUU (Phe), UAA (STOP) in DNA = ATG, TTT, TAA
        List<String> seq = List.of("A", "T", "G", "T", "T", "T", "T", "A", "A");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        List<String> protein = dna.translate();

        assertEquals("Protein has 2 amino acids", 2, protein.size());
        assertEquals("First AA is Met", "Met", protein.get(0));
        assertEquals("Second AA is Phe", "Phe", protein.get(1));
    }

    private static void testDNAReplication() {
        List<String> seq = List.of("A", "T", "G", "C", "A", "T");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        Random rng = new Random(42);

        // Replicate with zero mutation rate => exact copy
        BiologicalSystem.DNA copy = dna.replicate(rng, 0.0);
        assertEquals("Copy length = original length", dna.length(), copy.length());
        assertEquals("Copy generation = 1", 1, copy.generation());
        assertEquals("Copy mutations = 0", 0, copy.mutations());
        for (int i = 0; i < dna.length(); i++) {
            assertEquals("Base " + i + " copied", dna.sequence().get(i), copy.sequence().get(i));
        }
    }

    private static void testDNAReplicationMutation() {
        // Create a long DNA sequence
        List<String> seq = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            seq.add("A");
        }
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        Random rng = new Random(42);

        // Replicate with high mutation rate
        BiologicalSystem.DNA copy = dna.replicate(rng, 0.1);
        assertTrue("Some mutations occurred", copy.mutations() > 0);

        // Check that at least some bases changed
        int changed = 0;
        for (int i = 0; i < dna.length(); i++) {
            if (!dna.sequence().get(i).equals(copy.sequence().get(i))) {
                changed++;
            }
        }
        assertTrue("Mutations changed bases", changed > 0);
        assertTrue("Mutations within expected range", changed > 50 && changed < 200);
    }

    private static void testDNAGCContent() {
        List<String> seq = List.of("G", "C", "G", "C");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        assertApprox("All GC content = 1.0", 1.0, dna.gcContent(), 1e-10);

        List<String> seq2 = List.of("A", "T", "A", "T");
        BiologicalSystem.DNA dna2 = new BiologicalSystem.DNA(seq2);
        assertApprox("All AT content = 0.0", 0.0, dna2.gcContent(), 1e-10);

        List<String> seq3 = List.of("A", "G", "C", "T");
        BiologicalSystem.DNA dna3 = new BiologicalSystem.DNA(seq3);
        assertApprox("50% GC content", 0.5, dna3.gcContent(), 1e-10);
    }

    private static void testLifeformCreation() {
        List<String> seq = List.of("A", "T", "G", "T", "T", "T");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("protocell", genome);

        assertEquals("Species name", "protocell", lf.species());
        assertTrue("Lifeform ID > 0", lf.lifeformId() > 0);
        assertApprox("Initial fitness", 1.0, lf.fitness(), 1e-10);
        assertEquals("Initial age", 0, lf.age());
        assertTrue("Initially alive", lf.alive());
    }

    private static void testLifeformTick() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);

        lf.tick();
        assertEquals("Age after 1 tick", 1, lf.age());
        assertTrue("Fitness slightly decreased", lf.fitness() < 1.0);
        assertTrue("Still alive", lf.alive());
    }

    private static void testLifeformReproduction() {
        List<String> seq = List.of("A", "T", "G", "C", "A", "T");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        Random rng = new Random(42);

        BiologicalSystem.Lifeform child = lf.reproduce(rng, 0.0);
        assertNotNull("Child produced", child);
        assertEquals("Child species = parent", "test", child.species());
        assertEquals("Child genome generation = 1", 1, child.genome().generation());
    }

    private static void testLifeformDeadCannotReproduce() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        lf.kill();

        Random rng = new Random(42);
        BiologicalSystem.Lifeform child = lf.reproduce(rng, 0.0);
        assertTrue("Dead lifeform returns null child", child == null);
    }

    private static void testAbiogenesis() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        BiologicalSystem.DNA dna = bio.abiogenesis(30);
        assertEquals("Abiogenesis DNA length", 30, dna.length());
        assertEquals("1 DNA strand", 1, bio.getDnaStrands().size());

        // All bases should be valid
        for (String base : dna.sequence()) {
            assertTrue("Valid base: " + base,
                    base.equals("A") || base.equals("T") || base.equals("G") || base.equals("C"));
        }
    }

    private static void testSpawnLifeform() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        BiologicalSystem.Lifeform lf = bio.spawnLifeform("archaea", 50);
        assertEquals("Species", "archaea", lf.species());
        assertEquals("Genome length", 50, lf.genome().length());
        assertEquals("1 lifeform", 1, bio.getLifeforms().size());
        assertEquals("1 total species", 1, bio.getTotalSpecies());
    }

    private static void testEvolution() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        // Spawn some lifeforms
        for (int i = 0; i < 10; i++) {
            bio.spawnLifeform("test", 30);
        }

        int initialCount = bio.getLifeforms().size();
        bio.evolve(0.05); // low environmental pressure

        // After evolution, some may have reproduced
        assertTrue("Population changed or stayed", bio.getLifeforms().size() > 0);
    }

    private static void testReplicateDNA() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        BiologicalSystem.DNA original = bio.abiogenesis(20);
        BiologicalSystem.DNA copy = bio.replicateDNA(original);

        assertEquals("Copy generation = 1", 1, copy.generation());
        assertEquals("2 DNA strands", 2, bio.getDnaStrands().size());
        assertEquals("1 replication event", 1, bio.getTotalReplications());
    }

    private static void testUVRadiationEvent() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        for (int i = 0; i < 20; i++) {
            bio.spawnLifeform("test", 30);
        }

        double avgFitnessBefore = bio.averageFitness();
        bio.uvRadiationEvent(0.5);

        // Some lifeforms may have reduced fitness or died
        assertTrue("UV radiation had some effect",
                bio.averageFitness() <= avgFitnessBefore || bio.aliveCount() < 20);
    }

    private static void testAliveCount() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        bio.spawnLifeform("test", 30);
        bio.spawnLifeform("test", 30);
        assertEquals("2 alive", 2, bio.aliveCount());

        bio.getLifeforms().get(0).kill();
        assertEquals("1 alive after kill", 1, bio.aliveCount());
    }

    private static void testAverageFitness() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        bio.spawnLifeform("test", 30);
        bio.spawnLifeform("test", 30);

        double avg = bio.averageFitness();
        assertApprox("Average fitness ~ 1.0 for new lifeforms", 1.0, avg, 0.01);
    }

    private static void testSpeciesCensus() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);

        bio.spawnLifeform("archaea", 30);
        bio.spawnLifeform("archaea", 30);
        bio.spawnLifeform("bacteria", 30);

        Map<String, Integer> census = bio.speciesCensus();
        assertEquals("2 archaea", Integer.valueOf(2), census.get("archaea"));
        assertEquals("1 bacteria", Integer.valueOf(1), census.get("bacteria"));
    }
}
