package com.inthebeginning.simulator;

import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Biological system modeling DNA, proteins, lifeforms, and mutation.
 * Handles the emergence of self-replicating molecules, genetic code,
 * protein synthesis, and evolutionary mutation.
 */
public class BiologicalSystem {

    /** A strand of DNA represented as a sequence of nucleotide bases. */
    public static class DNA {
        private final List<String> sequence;
        private final Map<Integer, Boolean> methylation; // position -> methylated
        private int generation;
        private int mutations;

        public DNA(List<String> sequence) {
            this.sequence = new ArrayList<>(sequence);
            this.methylation = new HashMap<>();
            this.generation = 0;
            this.mutations = 0;
        }

        public List<String> sequence()   { return sequence; }
        public int length()              { return sequence.size(); }
        public int generation()          { return generation; }
        public int mutations()           { return mutations; }

        /** Transcribe DNA to RNA (T -> U). */
        public List<String> transcribeToRNA() {
            List<String> rna = new ArrayList<>();
            for (String base : sequence) {
                rna.add(base.equals("T") ? "U" : base);
            }
            return rna;
        }

        /** Translate RNA codons to amino acid sequence using the codon table. */
        public List<String> translate() {
            List<String> rna = transcribeToRNA();
            List<String> protein = new ArrayList<>();
            for (int i = 0; i + 2 < rna.size(); i += 3) {
                String codon = rna.get(i) + rna.get(i + 1) + rna.get(i + 2);
                String aa = CODON_TABLE.getOrDefault(codon, "???");
                if (aa.equals("STOP")) break;
                protein.add(aa);
            }
            return protein;
        }

        /** Replicate this DNA, potentially introducing mutations. */
        public DNA replicate(Random rng, double mutationRate) {
            List<String> newSeq = new ArrayList<>(sequence);
            int newMutations = 0;
            for (int i = 0; i < newSeq.size(); i++) {
                if (rng.nextDouble() < mutationRate) {
                    // Point mutation: replace with a random different base
                    String original = newSeq.get(i);
                    String[] bases = NUCLEOTIDE_BASES;
                    String replacement;
                    do {
                        replacement = bases[rng.nextInt(bases.length)];
                    } while (replacement.equals(original));
                    newSeq.set(i, replacement);
                    newMutations++;
                }
            }

            // Epigenetic inheritance: copy methylation pattern with noise
            DNA daughter = new DNA(newSeq);
            daughter.generation = this.generation + 1;
            daughter.mutations = this.mutations + newMutations;
            for (Map.Entry<Integer, Boolean> entry : methylation.entrySet()) {
                if (entry.getKey() < daughter.sequence.size()) {
                    if (rng.nextDouble() > DEMETHYLATION_PROBABILITY) {
                        daughter.methylation.put(entry.getKey(), entry.getValue());
                    }
                }
            }
            // Spontaneous methylation
            for (int i = 0; i < daughter.sequence.size(); i++) {
                if (!daughter.methylation.containsKey(i) &&
                    rng.nextDouble() < METHYLATION_PROBABILITY) {
                    daughter.methylation.put(i, true);
                }
            }

            return daughter;
        }

        /** Compute GC content (fraction of G and C bases). */
        public double gcContent() {
            if (sequence.isEmpty()) return 0.0;
            long gc = sequence.stream()
                    .filter(b -> b.equals("G") || b.equals("C"))
                    .count();
            return (double) gc / sequence.size();
        }

        public String toCompact() {
            String seq = sequence.size() <= 20
                    ? String.join("", sequence)
                    : String.join("", sequence.subList(0, 10)) + "..."
                      + String.join("", sequence.subList(sequence.size() - 10, sequence.size()));
            return String.format("DNA[len=%d gen=%d mut=%d gc=%.2f %s]",
                    length(), generation, mutations, gcContent(), seq);
        }

        @Override
        public String toString() { return toCompact(); }
    }

    /** A simple lifeform with a genome and fitness. */
    public static class Lifeform {
        private static final AtomicInteger idCounter = new AtomicInteger(0);

        private final int lifeformId;
        private final String species;
        private DNA genome;
        private double fitness;
        private int age;
        private boolean alive;
        private final List<String> proteins;

        public Lifeform(String species, DNA genome) {
            this.lifeformId = idCounter.incrementAndGet();
            this.species = species;
            this.genome = genome;
            this.fitness = 1.0;
            this.age = 0;
            this.alive = true;
            this.proteins = genome.translate();
        }

        public int lifeformId()        { return lifeformId; }
        public String species()        { return species; }
        public DNA genome()            { return genome; }
        public double fitness()        { return fitness; }
        public int age()               { return age; }
        public boolean alive()         { return alive; }
        public List<String> proteins() { return proteins; }

        public void setFitness(double f) { this.fitness = f; }
        public void kill()               { this.alive = false; }

        /** Age the lifeform by one tick; fitness decays slightly with age. */
        public void tick() {
            if (!alive) return;
            age++;
            fitness *= 0.9999; // slow aging
        }

        /** Reproduce with mutation. Returns offspring or null if dead. */
        public Lifeform reproduce(Random rng, double mutationRate) {
            if (!alive || fitness < 0.1) return null;
            DNA childGenome = genome.replicate(rng, mutationRate);
            Lifeform child = new Lifeform(species, childGenome);
            // Fitness varies around parent
            child.fitness = fitness * (0.8 + rng.nextDouble() * 0.4);
            return child;
        }

        public String toCompact() {
            return String.format("%s#%d[fit=%.3f age=%d genes=%d %s]",
                    species, lifeformId, fitness, age,
                    genome.length(), alive ? "ALIVE" : "DEAD");
        }

        @Override
        public String toString() { return toCompact(); }
    }

    // --- System state ---

    private final List<DNA> dnaStrands = new ArrayList<>();
    private final List<Lifeform> lifeforms = new ArrayList<>();
    private final Random rng;
    private int totalSpecies = 0;
    private int totalExtinctions = 0;
    private int totalReplicationEvents = 0;
    private double mutationRate;

    public BiologicalSystem(Random rng) {
        this(UV_MUTATION_RATE, rng);
    }

    public BiologicalSystem(double mutationRate, Random rng) {
        this.mutationRate = mutationRate;
        this.rng = rng;
    }

    // --- Accessors ---

    public List<DNA> getDnaStrands()        { return dnaStrands; }
    public List<Lifeform> getLifeforms()    { return lifeforms; }
    public int getTotalSpecies()            { return totalSpecies; }
    public int getTotalExtinctions()        { return totalExtinctions; }
    public int getTotalReplications()       { return totalReplicationEvents; }
    public double getMutationRate()         { return mutationRate; }
    public void setMutationRate(double r)   { this.mutationRate = r; }

    // --- Abiogenesis: create initial self-replicating molecules ---

    /**
     * Generate a random DNA strand of given length from available nucleotides.
     * Simulates abiogenesis: random assembly of nucleotides into a polymer.
     */
    public DNA abiogenesis(int length) {
        List<String> seq = new ArrayList<>();
        for (int i = 0; i < length; i++) {
            seq.add(NUCLEOTIDE_BASES[rng.nextInt(NUCLEOTIDE_BASES.length)]);
        }
        DNA dna = new DNA(seq);
        dnaStrands.add(dna);
        return dna;
    }

    /**
     * Spawn a lifeform with a random genome.
     * Returns the newly created Lifeform.
     */
    public Lifeform spawnLifeform(String species, int genomeLength) {
        DNA genome = abiogenesis(genomeLength);
        Lifeform lf = new Lifeform(species, genome);
        lifeforms.add(lf);
        totalSpecies++;
        return lf;
    }

    // --- Evolution ---

    /** Maximum population to prevent memory issues. */
    private static final int MAX_POPULATION = 200;

    /**
     * Run one evolutionary step:
     * 1. Age all lifeforms
     * 2. Kill unfit individuals
     * 3. Reproduce survivors (capped at MAX_POPULATION)
     * 4. Apply environmental selection
     * 5. Prune dead lifeforms to keep memory bounded
     */
    public void evolve(double environmentalPressure) {
        List<Lifeform> newborn = new ArrayList<>();
        int alive = aliveCount();

        for (Lifeform lf : lifeforms) {
            if (!lf.alive()) continue;

            lf.tick();

            // Environmental selection: harsh environment kills low-fitness
            if (lf.fitness() < environmentalPressure) {
                lf.kill();
                totalExtinctions++;
                alive--;
                continue;
            }

            // Reproduction probability proportional to fitness (capped population)
            if (alive + newborn.size() < MAX_POPULATION &&
                rng.nextDouble() < lf.fitness() * 0.1) {
                Lifeform child = lf.reproduce(rng, mutationRate);
                if (child != null) {
                    newborn.add(child);
                    totalReplicationEvents++;
                }
            }
        }

        lifeforms.addAll(newborn);

        // Prune dead lifeforms to keep list bounded (keep last 50 dead for history)
        if (lifeforms.size() > MAX_POPULATION * 2) {
            List<Lifeform> pruned = new ArrayList<>();
            int deadKept = 0;
            for (Lifeform lf : lifeforms) {
                if (lf.alive()) {
                    pruned.add(lf);
                } else if (deadKept < 50) {
                    pruned.add(lf);
                    deadKept++;
                }
            }
            lifeforms.clear();
            lifeforms.addAll(pruned);
        }
    }

    /** Maximum DNA strands to keep in memory. */
    private static final int MAX_DNA_STRANDS = 500;

    /**
     * Replicate a specific DNA strand with mutations.
     */
    public DNA replicateDNA(DNA template) {
        DNA copy = template.replicate(rng, mutationRate);
        dnaStrands.add(copy);
        totalReplicationEvents++;

        // Keep DNA list bounded
        if (dnaStrands.size() > MAX_DNA_STRANDS) {
            dnaStrands.subList(0, dnaStrands.size() - MAX_DNA_STRANDS).clear();
        }

        return copy;
    }

    /**
     * Apply UV radiation damage: increases mutation rate temporarily
     * and may kill organisms.
     */
    public void uvRadiationEvent(double intensity) {
        double boostedRate = mutationRate * (1.0 + intensity);
        for (Lifeform lf : lifeforms) {
            if (!lf.alive()) continue;
            if (rng.nextDouble() < intensity * 0.1) {
                // Radiation damage
                lf.setFitness(lf.fitness() * (1.0 - intensity * 0.5));
                if (lf.fitness() < 0.01) {
                    lf.kill();
                    totalExtinctions++;
                }
            }
        }
    }

    // --- Statistics ---

    public int aliveCount() {
        return (int) lifeforms.stream().filter(Lifeform::alive).count();
    }

    public double averageFitness() {
        return lifeforms.stream()
                .filter(Lifeform::alive)
                .mapToDouble(Lifeform::fitness)
                .average()
                .orElse(0.0);
    }

    public int maxGeneration() {
        return dnaStrands.stream()
                .mapToInt(DNA::generation)
                .max()
                .orElse(0);
    }

    public Map<String, Integer> speciesCensus() {
        Map<String, Integer> census = new LinkedHashMap<>();
        for (Lifeform lf : lifeforms) {
            if (lf.alive()) {
                census.merge(lf.species(), 1, Integer::sum);
            }
        }
        return census;
    }

    public String toCompact() {
        return String.format(
                "BIO[strands=%d life=%d/%d species=%d extinct=%d repl=%d avgFit=%.3f maxGen=%d]",
                dnaStrands.size(), aliveCount(), lifeforms.size(),
                totalSpecies, totalExtinctions, totalReplicationEvents,
                averageFitness(), maxGeneration());
    }
}
