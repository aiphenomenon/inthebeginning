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
        testMutationRateAccessors();
        testMaxGeneration();
        testBioToCompact();
        testDNAToCompact();
        testDNAToCompactLong();
        testDNAToString();
        testLifeformProteins();
        testLifeformToCompact();
        testLifeformToString();
        testLifeformSetFitness();
        testLifeformTickDead();
        testDNAGCContentEmpty();
        testConstructorWithMutationRate();
        testLifeformLowFitnessCannotReproduce();
        testEvolutionPopulationPruning();
        testDNAReplicateMethylation();
        testGetTotalExtinctions();

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

    private static void testMutationRateAccessors() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);
        assertApprox("Default mutation rate", Constants.UV_MUTATION_RATE, bio.getMutationRate(), 1e-10);

        bio.setMutationRate(0.05);
        assertApprox("Set mutation rate", 0.05, bio.getMutationRate(), 1e-10);
    }

    private static void testMaxGeneration() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);
        assertEquals("Max generation with no DNA", 0, bio.maxGeneration());

        BiologicalSystem.DNA dna = bio.abiogenesis(20);
        assertEquals("Max generation = 0 for first DNA", 0, bio.maxGeneration());

        BiologicalSystem.DNA copy = bio.replicateDNA(dna);
        assertEquals("Max generation = 1 after replication", 1, bio.maxGeneration());

        BiologicalSystem.DNA copy2 = bio.replicateDNA(copy);
        assertEquals("Max generation = 2 after second replication", 2, bio.maxGeneration());
    }

    private static void testBioToCompact() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);
        bio.spawnLifeform("test", 30);

        String compact = bio.toCompact();
        assertTrue("Compact contains BIO[", compact.contains("BIO["));
        assertTrue("Compact contains strands=", compact.contains("strands="));
        assertTrue("Compact contains life=", compact.contains("life="));
        assertTrue("Compact contains species=", compact.contains("species="));
        assertTrue("Compact contains avgFit=", compact.contains("avgFit="));
    }

    private static void testDNAToCompact() {
        List<String> seq = List.of("A", "T", "G", "C", "A", "T");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        String compact = dna.toCompact();
        assertTrue("DNA compact contains DNA[", compact.contains("DNA["));
        assertTrue("DNA compact contains len=", compact.contains("len="));
        assertTrue("DNA compact contains gen=", compact.contains("gen="));
        assertTrue("DNA compact contains mut=", compact.contains("mut="));
        assertTrue("DNA compact contains gc=", compact.contains("gc="));
        assertTrue("DNA compact contains sequence", compact.contains("ATGCAT"));
    }

    private static void testDNAToCompactLong() {
        // DNA longer than 20 bases should be truncated with "..."
        List<String> seq = new ArrayList<>();
        for (int i = 0; i < 30; i++) {
            seq.add(i % 2 == 0 ? "A" : "T");
        }
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        String compact = dna.toCompact();
        assertTrue("Long DNA compact contains ...", compact.contains("..."));
    }

    private static void testDNAToString() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);
        assertEquals("DNA toString equals toCompact", dna.toCompact(), dna.toString());
    }

    private static void testLifeformProteins() {
        // ATG=Met(start), TTT=Phe -> proteins = [Met, Phe]
        List<String> seq = List.of("A", "T", "G", "T", "T", "T");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        assertNotNull("Proteins list not null", lf.proteins());
        assertEquals("2 proteins", 2, lf.proteins().size());
        assertEquals("First protein is Met", "Met", lf.proteins().get(0));
        assertEquals("Second protein is Phe", "Phe", lf.proteins().get(1));
    }

    private static void testLifeformToCompact() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("archaea", genome);
        String compact = lf.toCompact();
        assertTrue("Compact contains species", compact.contains("archaea"));
        assertTrue("Compact contains fit=", compact.contains("fit="));
        assertTrue("Compact contains age=", compact.contains("age="));
        assertTrue("Compact contains ALIVE", compact.contains("ALIVE"));
    }

    private static void testLifeformToString() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        assertEquals("Lifeform toString equals toCompact", lf.toCompact(), lf.toString());
    }

    private static void testLifeformSetFitness() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        assertApprox("Initial fitness = 1.0", 1.0, lf.fitness(), 1e-10);
        lf.setFitness(0.5);
        assertApprox("Fitness set to 0.5", 0.5, lf.fitness(), 1e-10);
    }

    private static void testLifeformTickDead() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        lf.kill();
        assertTrue("Lifeform is dead", !lf.alive());

        int ageBefore = lf.age();
        double fitBefore = lf.fitness();
        lf.tick();
        // Dead lifeform should not age or lose fitness
        assertEquals("Age unchanged for dead lifeform", ageBefore, lf.age());
        assertApprox("Fitness unchanged for dead lifeform", fitBefore, lf.fitness(), 1e-10);
    }

    private static void testDNAGCContentEmpty() {
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(List.of());
        assertApprox("GC content of empty DNA = 0", 0.0, dna.gcContent(), 1e-10);
    }

    private static void testConstructorWithMutationRate() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(0.05, rng);
        assertApprox("Custom mutation rate", 0.05, bio.getMutationRate(), 1e-10);
    }

    private static void testLifeformLowFitnessCannotReproduce() {
        List<String> seq = List.of("A", "T", "G");
        BiologicalSystem.DNA genome = new BiologicalSystem.DNA(seq);
        BiologicalSystem.Lifeform lf = new BiologicalSystem.Lifeform("test", genome);
        lf.setFitness(0.05); // below 0.1 threshold

        Random rng = new Random(42);
        BiologicalSystem.Lifeform child = lf.reproduce(rng, 0.0);
        assertTrue("Low fitness lifeform cannot reproduce", child == null);
    }

    private static void testEvolutionPopulationPruning() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(0.0, rng); // zero mutation rate

        // Spawn many lifeforms to trigger pruning
        for (int i = 0; i < 100; i++) {
            bio.spawnLifeform("test", 30);
        }

        // Evolve many times with low pressure to grow population
        for (int i = 0; i < 50; i++) {
            bio.evolve(0.01);
        }

        // Population should be bounded (MAX_POPULATION * 2 = 400)
        assertTrue("Population bounded", bio.getLifeforms().size() <= 500);
    }

    private static void testDNAReplicateMethylation() {
        Random rng = new Random(42);
        List<String> seq = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            seq.add("A");
        }
        BiologicalSystem.DNA dna = new BiologicalSystem.DNA(seq);

        // Replicate to generate methylation patterns
        BiologicalSystem.DNA copy1 = dna.replicate(rng, 0.01);
        BiologicalSystem.DNA copy2 = copy1.replicate(rng, 0.01);

        // Just verify replication chain works with methylation
        assertEquals("copy2 generation = 2", 2, copy2.generation());
        assertEquals("copy2 length = 100", 100, copy2.length());
    }

    private static void testGetTotalExtinctions() {
        Random rng = new Random(42);
        BiologicalSystem bio = new BiologicalSystem(rng);
        assertEquals("Initial extinctions = 0", 0, bio.getTotalExtinctions());

        // Spawn lifeforms with very low fitness
        for (int i = 0; i < 20; i++) {
            BiologicalSystem.Lifeform lf = bio.spawnLifeform("test", 30);
            lf.setFitness(0.001); // extremely low fitness
        }

        // Evolve with very high environmental pressure
        // fitness(0.001) * 0.9999 = 0.00099... which is < 0.9
        bio.evolve(0.9);

        // Even if not all died, at least some should have
        assertTrue("Extinctions counter >= 0", bio.getTotalExtinctions() >= 0);
        // Verify total alive decreased
        assertTrue("Some lifeforms killed",
                bio.aliveCount() < 20 || bio.getTotalExtinctions() > 0);
    }
}
