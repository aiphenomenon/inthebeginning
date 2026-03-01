package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Main entry point for the cosmic evolution simulator.
 * Runs the complete simulation from the Big Bang through 13 epochs
 * to the emergence of life, printing detailed physics data at each stage.
 */
public class SimulatorApp {

    // ANSI color codes for terminal output
    private static final String RESET  = "\033[0m";
    private static final String BOLD   = "\033[1m";
    private static final String RED    = "\033[31m";
    private static final String GREEN  = "\033[32m";
    private static final String YELLOW = "\033[33m";
    private static final String BLUE   = "\033[34m";
    private static final String MAGENTA= "\033[35m";
    private static final String CYAN   = "\033[36m";
    private static final String WHITE  = "\033[37m";

    private static final String[] EPOCH_COLORS = {
        RED, RED, YELLOW, YELLOW, MAGENTA, MAGENTA,
        CYAN, BLUE, GREEN, GREEN, GREEN, GREEN, WHITE
    };

    public static void main(String[] args) {
        long seed = 42L;
        if (args.length > 0) {
            try {
                seed = Long.parseLong(args[0]);
            } catch (NumberFormatException e) {
                // ignore, use default seed
            }
        }

        printBanner();

        Universe universe = new Universe(seed);

        System.out.println(BOLD + "\nBeginning cosmic simulation with seed: " + seed + RESET);
        System.out.println("Total epochs: " + EPOCHS.size());
        System.out.println("Total ticks: " + PRESENT_EPOCH);
        System.out.println();

        // Run the simulation, stepping through each epoch
        int lastEpochIndex = -1;

        for (int targetTick = 0; targetTick < EPOCHS.size(); targetTick++) {
            EpochInfo epoch = EPOCHS.get(targetTick);
            int endTick;
            if (targetTick + 1 < EPOCHS.size()) {
                endTick = EPOCHS.get(targetTick + 1).startTick();
            } else {
                endTick = PRESENT_EPOCH;
            }

            // Run to the start of this epoch
            int startTick = epoch.startTick();
            while (universe.getTick() < startTick) {
                universe.step();
            }

            // Print epoch header
            String color = EPOCH_COLORS[targetTick % EPOCH_COLORS.length];
            printEpochHeader(targetTick + 1, epoch, color);

            // Run through this epoch
            int stepsInEpoch = endTick - startTick;
            int stepSize = Math.max(1, stepsInEpoch / 10); // sample ~10 points per epoch
            int samplesShown = 0;

            while (universe.getTick() < endTick && samplesShown < 5) {
                // Advance by stepSize ticks
                int target = Math.min(universe.getTick() + stepSize, endTick);
                while (universe.getTick() < target) {
                    universe.step();
                }
                samplesShown++;
            }

            // Run any remaining ticks
            while (universe.getTick() < endTick) {
                universe.step();
            }

            // Print epoch summary
            printEpochSummary(universe, epoch, color);
        }

        // Final summary
        printFinalSummary(universe);
    }

    private static void printBanner() {
        System.out.println();
        System.out.println(BOLD + CYAN +
            "  ============================================================" + RESET);
        System.out.println(BOLD + CYAN +
            "  |                                                          |" + RESET);
        System.out.println(BOLD + CYAN +
            "  |        IN THE BEGINNING -- Cosmic Evolution Simulator    |" + RESET);
        System.out.println(BOLD + CYAN +
            "  |                                                          |" + RESET);
        System.out.println(BOLD + CYAN +
            "  |    From the Big Bang to Life: A Physics Simulation       |" + RESET);
        System.out.println(BOLD + CYAN +
            "  |                                                          |" + RESET);
        System.out.println(BOLD + CYAN +
            "  ============================================================" + RESET);
    }

    private static void printEpochHeader(int number, EpochInfo epoch, String color) {
        System.out.println();
        System.out.println(color + BOLD +
            "  ----------------------------------------------------------------" + RESET);
        System.out.printf(color + BOLD +
            "  EPOCH %d/13: %s  (tick %,d)%n" + RESET,
            number, epoch.name().toUpperCase(), epoch.startTick());
        System.out.println(color +
            "  " + epoch.description() + RESET);
        System.out.println(color + BOLD +
            "  ----------------------------------------------------------------" + RESET);
    }

    private static void printEpochSummary(Universe u, EpochInfo epoch, String color) {
        System.out.println();
        System.out.println(color + "  --- State at end of " + epoch.name() + " epoch ---" + RESET);

        // Physics data
        System.out.printf("    Temperature:     %12.4e K%n", u.getTemperature());
        System.out.printf("    Scale factor:    %12.4e%n", u.getScaleFactor());
        System.out.printf("    Total energy:    %12.4e%n", u.getTotalEnergy());

        // Quantum field
        QuantumField qf = u.getQuantumField();
        System.out.printf("    Particles:       %,12d  (created: %,d  annihilated: %,d)%n",
                qf.getParticles().size(), qf.getTotalCreated(), qf.getTotalAnnihilated());
        Map<String, Integer> pCounts = qf.particleCount();
        if (!pCounts.isEmpty()) {
            System.out.print("      Breakdown:     ");
            pCounts.forEach((type, count) ->
                System.out.printf("%s=%d ", type, count));
            System.out.println();
        }

        // Atoms
        AtomicSystem as = u.getAtomicSystem();
        if (!as.getAtoms().isEmpty()) {
            System.out.printf("    Atoms:           %,12d  (bonds: %,d)%n",
                    as.getAtoms().size(), as.getBondsFormed());
            Map<String, Integer> eCounts = as.elementCounts();
            if (!eCounts.isEmpty()) {
                System.out.print("      Elements:      ");
                eCounts.forEach((sym, count) ->
                    System.out.printf("%s=%d ", sym, count));
                System.out.println();
            }
        }

        // Molecules
        ChemicalSystem cs = u.getChemicalSystem();
        if (!cs.getMolecules().isEmpty()) {
            System.out.printf("    Molecules:       %,12d  (reactions: %,d)%n",
                    cs.getMolecules().size(), cs.getReactionsOccurred());
            System.out.printf("      Water: %d  Amino acids: %d  Nucleotides: %d%n",
                    cs.getWaterCount(), cs.getAminoAcidCount(), cs.getNucleotideCount());
        }

        // Environment
        Environment env = u.getEnvironment();
        if (env.getSurfaceTemperature() > 0) {
            System.out.printf("    Environment:     %s%n", env.toCompact());
            if (env.hasLiquidWater()) {
                System.out.printf("      Liquid water:  YES  (ocean coverage: %.0f%%)%n",
                        env.getOceanCoverage() * 100);
            }
            if (env.supportsComplexLife()) {
                System.out.printf("      Complex life:  " + GREEN + "SUPPORTED" + RESET + "%n");
            }
        }

        // Biology
        BiologicalSystem bio = u.getBiologicalSystem();
        if (!bio.getLifeforms().isEmpty()) {
            System.out.printf("    Lifeforms:       %,12d alive  (total species: %,d  extinct: %,d)%n",
                    bio.aliveCount(), bio.getTotalSpecies(), bio.getTotalExtinctions());
            System.out.printf("      Avg fitness:   %.4f  Max generation: %d%n",
                    bio.averageFitness(), bio.maxGeneration());
            System.out.printf("      DNA strands:   %,d  Replications: %,d%n",
                    bio.getDnaStrands().size(), bio.getTotalReplications());

            Map<String, Integer> census = bio.speciesCensus();
            if (!census.isEmpty()) {
                System.out.print("      Species:       ");
                census.forEach((sp, count) ->
                    System.out.printf("%s=%d ", sp, count));
                System.out.println();
            }
        }

        // Event log (last few events)
        List<String> events = u.getEventLog();
        if (!events.isEmpty()) {
            int start = Math.max(0, events.size() - 3);
            System.out.println("    Recent events:");
            for (int i = start; i < events.size(); i++) {
                System.out.println("      > " + events.get(i));
            }
        }
    }

    private static void printFinalSummary(Universe u) {
        System.out.println();
        System.out.println(BOLD + CYAN +
            "  ================================================================" + RESET);
        System.out.println(BOLD + CYAN +
            "  SIMULATION COMPLETE -- The Story of Everything" + RESET);
        System.out.println(BOLD + CYAN +
            "  ================================================================" + RESET);
        System.out.println();

        System.out.printf("  Total simulation ticks:    %,d%n", u.getTick());
        System.out.printf("  Final temperature:         %.4e K%n", u.getTemperature());
        System.out.printf("  Final scale factor:        %.4e%n", u.getScaleFactor());
        System.out.printf("  Total energy:              %.4e%n", u.getTotalEnergy());
        System.out.println();

        QuantumField qf = u.getQuantumField();
        System.out.printf("  Particles remaining:       %,d%n", qf.getParticles().size());
        System.out.printf("  Particles created:         %,d%n", qf.getTotalCreated());
        System.out.printf("  Particles annihilated:     %,d%n", qf.getTotalAnnihilated());
        System.out.println();

        AtomicSystem as = u.getAtomicSystem();
        System.out.printf("  Atoms formed:              %,d%n", as.getAtoms().size());
        System.out.printf("  Chemical bonds:            %,d%n", as.getBondsFormed());
        System.out.printf("  Elements: %s%n", as.elementCounts());
        System.out.println();

        ChemicalSystem cs = u.getChemicalSystem();
        System.out.printf("  Molecules:                 %,d%n", cs.getMolecules().size());
        System.out.printf("  Water molecules:           %,d%n", cs.getWaterCount());
        System.out.printf("  Amino acids:               %,d%n", cs.getAminoAcidCount());
        System.out.printf("  Nucleotides:               %,d%n", cs.getNucleotideCount());
        System.out.printf("  Chemical reactions:        %,d%n", cs.getReactionsOccurred());
        System.out.println();

        BiologicalSystem bio = u.getBiologicalSystem();
        System.out.printf("  Living organisms:          %,d%n", bio.aliveCount());
        System.out.printf("  Total species emerged:     %,d%n", bio.getTotalSpecies());
        System.out.printf("  Extinctions:               %,d%n", bio.getTotalExtinctions());
        System.out.printf("  DNA replications:          %,d%n", bio.getTotalReplications());
        System.out.printf("  Average fitness:           %.4f%n", bio.averageFitness());
        System.out.printf("  Max evolutionary gen:      %,d%n", bio.maxGeneration());
        System.out.println();

        Environment env = u.getEnvironment();
        System.out.printf("  Surface temperature:       %.1f K%n", env.getSurfaceTemperature());
        System.out.printf("  Habitability:              %.2f%n", env.getHabitability());
        System.out.printf("  Ocean coverage:            %.0f%%%n", env.getOceanCoverage() * 100);
        System.out.printf("  Atmosphere:                %s%n", env.getAtmosphere());
        System.out.println();

        if (bio.aliveCount() > 0) {
            System.out.println(BOLD + GREEN +
                "  >>> Life has emerged from the cosmos! <<<" + RESET);
        } else {
            System.out.println(BOLD + RED +
                "  >>> The universe remains lifeless. <<<" + RESET);
        }

        System.out.println();
        System.out.println(BOLD + CYAN +
            "  Total events logged: " + u.getEventLog().size() + RESET);
        System.out.println();
    }
}
