package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * The Universe orchestrator.
 * Drives cosmic evolution through 13 epochs from the Planck era to the present,
 * coordinating the quantum field, atomic system, chemical system, environment,
 * and biological system.
 */
public class Universe {

    /** Current simulation tick. */
    private int tick = 0;

    /** Current epoch index. */
    private int currentEpochIndex = 0;

    /** Scale factor (expansion of the universe). */
    private double scaleFactor = 1e-30;

    /** Cosmic temperature. */
    private double temperature;

    /** Total energy. */
    private double totalEnergy = 0.0;

    /** Big Bounce cycle counter (0 = first run). */
    private int cycle = 0;

    /** Sub-systems. */
    private QuantumField quantumField;
    private AtomicSystem atomicSystem;
    private ChemicalSystem chemicalSystem;
    private Environment environment;
    private BiologicalSystem biologicalSystem;

    /** Random number generator (seeded for reproducibility). */
    private final Random rng;

    /** Event log. */
    private final List<String> eventLog = new ArrayList<>();

    public Universe(long seed) {
        this.rng = new Random(seed);
        this.temperature = T_PLANCK;

        this.quantumField = new QuantumField(T_PLANCK, rng);
        this.atomicSystem = new AtomicSystem(T_PLANCK, rng);
        this.chemicalSystem = new ChemicalSystem(atomicSystem, rng);
        this.environment = new Environment(rng);
        this.biologicalSystem = new BiologicalSystem(rng);
    }

    // --- Accessors ---

    public int getTick()                        { return tick; }
    public double getTemperature()              { return temperature; }
    public double getScaleFactor()              { return scaleFactor; }
    public double getTotalEnergy()              { return totalEnergy; }
    public int getCycle()                       { return cycle; }
    public QuantumField getQuantumField()       { return quantumField; }
    public AtomicSystem getAtomicSystem()       { return atomicSystem; }
    public ChemicalSystem getChemicalSystem()   { return chemicalSystem; }
    public Environment getEnvironment()         { return environment; }
    public BiologicalSystem getBiologicalSystem(){ return biologicalSystem; }
    public List<String> getEventLog()           { return eventLog; }

    /**
     * Determine which epoch we are in based on the current tick.
     */
    public EpochInfo currentEpoch() {
        EpochInfo current = EPOCHS.get(0);
        for (int i = 0; i < EPOCHS.size(); i++) {
            if (tick >= EPOCHS.get(i).startTick()) {
                current = EPOCHS.get(i);
                currentEpochIndex = i;
            }
        }
        return current;
    }

    /**
     * Advance the simulation by one tick.
     * Delegates to the appropriate epoch handler.
     */
    public void step() {
        tick++;

        EpochInfo epoch = currentEpoch();

        // Universe expansion: scale factor grows, temperature drops
        expandUniverse();

        // Dispatch to epoch-specific physics
        if (tick <= INFLATION_EPOCH) {
            stepPlanck();
        } else if (tick <= ELECTROWEAK_EPOCH) {
            stepInflation();
        } else if (tick <= QUARK_EPOCH) {
            stepElectroweak();
        } else if (tick <= HADRON_EPOCH) {
            stepQuark();
        } else if (tick <= NUCLEOSYNTHESIS_EPOCH) {
            stepHadron();
        } else if (tick <= RECOMBINATION_EPOCH) {
            stepNucleosynthesis();
        } else if (tick <= STAR_FORMATION_EPOCH) {
            stepRecombination();
        } else if (tick <= SOLAR_SYSTEM_EPOCH) {
            stepStarFormation();
        } else if (tick <= EARTH_EPOCH) {
            stepSolarSystem();
        } else if (tick <= LIFE_EPOCH) {
            stepEarth();
        } else if (tick <= DNA_EPOCH) {
            stepLife();
        } else {
            stepDNA(); // Present epoch continues DNA-era processes
        }

        // Update total energy
        totalEnergy = quantumField.totalEnergy();
    }

    /**
     * Run the simulation from current tick to targetTick.
     * Calls the epochCallback whenever an epoch boundary is crossed.
     */
    public void runTo(int targetTick, EpochCallback callback) {
        int lastEpochIndex = -1;
        while (tick < targetTick) {
            step();
            EpochInfo ep = currentEpoch();
            if (currentEpochIndex != lastEpochIndex) {
                lastEpochIndex = currentEpochIndex;
                if (callback != null) {
                    callback.onEpochEnter(currentEpochIndex, ep, this);
                }
            }
        }
    }

    /** Functional interface for epoch transition callbacks. */
    @FunctionalInterface
    public interface EpochCallback {
        void onEpochEnter(int epochIndex, EpochInfo epoch, Universe universe);
    }

    // --- Big Bounce ---

    /**
     * Reset the universe for a new cosmic cycle (Big Bounce).
     * <p>
     * Clears the tick counter, resets the epoch to Planck, restores the initial
     * Planck temperature, reinitializes all subsystems (quantum field, atomic
     * system, chemical system, environment, biosphere), clears internal epoch
     * flags, and increments the cycle counter. The event log is cleared so that
     * old events do not accumulate across cycles.
     * <p>
     * The random number generator is <b>not</b> reseeded, allowing each cycle
     * to explore a different evolutionary trajectory. This method is safe to
     * call indefinitely without leaking memory because every collection and
     * subsystem is replaced or cleared.
     */
    public void bigBounce() {
        cycle++;

        // Reset simulation clock and epoch
        tick = 0;
        currentEpochIndex = 0;

        // Reset cosmological state
        temperature = T_PLANCK;
        scaleFactor = 1e-30;
        totalEnergy = 0.0;

        // Reinitialize all subsystems (old instances become eligible for GC)
        quantumField = new QuantumField(T_PLANCK, rng);
        atomicSystem = new AtomicSystem(T_PLANCK, rng);
        chemicalSystem = new ChemicalSystem(atomicSystem, rng);
        environment = new Environment(rng);
        biologicalSystem = new BiologicalSystem(rng);

        // Reset internal epoch-progression flags
        bbnDone = false;
        solarSystemInitialized = false;
        earthInitialized = false;

        // Clear the event log for the new cycle
        eventLog.clear();
    }

    // --- Epoch handlers ---

    /** Planck epoch: all forces unified, extreme conditions. */
    private void stepPlanck() {
        // Vacuum fluctuations at maximum
        quantumField.vacuumFluctuation();
        quantumField.evolve(1e-10);
    }

    /** Inflation: exponential expansion, quantum fluctuations seed structure. */
    private void stepInflation() {
        // Rapid expansion
        scaleFactor *= 1.1;
        // Massive pair production from the inflationary energy
        // Create many particles -- these will eventually become atoms
        for (int i = 0; i < 20; i++) {
            double energy = K_B * temperature * (1.0 + rng.nextDouble() * 5.0);
            quantumField.pairProduction(energy);
        }
        quantumField.evolve(1e-8);
    }

    /** Electroweak: EM and weak forces separate, W/Z bosons appear. */
    private void stepElectroweak() {
        quantumField.vacuumFluctuation();
        // Continue pair production at lower rate
        if (rng.nextDouble() < 0.3) {
            double energy = K_B * temperature;
            quantumField.pairProduction(energy);
        }
        quantumField.evolve(1e-6);
    }

    /** Quark epoch: free quarks in quark-gluon plasma. */
    private void stepQuark() {
        quantumField.vacuumFluctuation();
        quantumField.evolve(1e-4);
    }

    /** Hadron epoch: quarks confined into protons and neutrons. */
    private void stepHadron() {
        // Force temperature below confinement threshold so quarkConfinement triggers
        List<Particle> hadrons = quantumField.quarkConfinement();
        if (!hadrons.isEmpty() && eventLog.size() < 100) {
            int protons = 0, neutrons = 0;
            for (Particle h : hadrons) {
                if (h.type() == ParticleType.PROTON) protons++;
                else if (h.type() == ParticleType.NEUTRON) neutrons++;
            }
            if (protons + neutrons > 0) {
                eventLog.add(String.format("t=%d Confinement: %d protons, %d neutrons",
                        tick, protons, neutrons));
            }
        }
        quantumField.evolve(1e-3);
    }

    private boolean bbnDone = false;

    /** Nucleosynthesis: light nuclei form (H, He, Li). */
    private void stepNucleosynthesis() {
        // Count protons and neutrons for BBN
        int protons = 0, neutrons = 0;
        for (Particle p : quantumField.getParticles()) {
            if (p.type() == ParticleType.PROTON) protons++;
            else if (p.type() == ParticleType.NEUTRON) neutrons++;
        }

        if (!bbnDone && protons > 0 && neutrons > 0) {
            bbnDone = true;
            List<Atom> nuclei = atomicSystem.nucleosynthesis(protons, neutrons);
            if (!nuclei.isEmpty()) {
                // Remove the used protons/neutrons from the quantum field
                Iterator<Particle> it = quantumField.getParticles().iterator();
                while (it.hasNext()) {
                    Particle p = it.next();
                    if (p.type() == ParticleType.PROTON || p.type() == ParticleType.NEUTRON) {
                        it.remove();
                    }
                }
                eventLog.add(String.format("t=%d BBN: formed %d nuclei (%s)",
                        tick, nuclei.size(), atomicSystem.elementCounts()));
            }
        }

        // If no hadrons were available (quarks didn't confine), seed atoms directly
        if (!bbnDone && tick >= NUCLEOSYNTHESIS_EPOCH + 100) {
            bbnDone = true;
            // Seed a substantial number of atoms for interesting chemistry later.
            // Real BBN: ~75% H, ~25% He by mass => ~92% H, ~8% He by number.
            // We need enough C, N, O atoms eventually from stellar nucleosynthesis,
            // so start with a good number of He (which will fuse into C, O, N).
            int nH = 120;
            int nHe = 40;
            // nucleosynthesis(protons, neutrons): He needs 2p+2n each
            List<Atom> nuclei = atomicSystem.nucleosynthesis(nH + nHe * 2, nHe * 2);
            eventLog.add(String.format("t=%d BBN (direct): formed %d nuclei (%s)",
                    tick, nuclei.size(), atomicSystem.elementCounts()));
        }

        atomicSystem.setTemperature(temperature);
        quantumField.evolve(0.01);
    }

    /** Recombination: atoms form, universe becomes transparent. */
    private void stepRecombination() {
        // Force temperature to recombination regime for this epoch
        atomicSystem.setTemperature(T_RECOMBINATION * 0.9);
        List<Atom> atoms = atomicSystem.recombination(quantumField);
        if (!atoms.isEmpty() && eventLog.size() < 100) {
            eventLog.add(String.format("t=%d Recombination: %d atoms formed",
                    tick, atoms.size()));
        }
        quantumField.evolve(0.1);
    }

    /** Star formation: first stars ignite, heavier elements forged. */
    private void stepStarFormation() {
        // Stellar nucleosynthesis: forge heavier elements
        // Only run occasionally to preserve a good elemental mix (H, He, C, N, O)
        if (rng.nextDouble() < 0.002) {
            double stellarTemp = T_STELLAR_CORE * (1.0 + rng.nextDouble() * 0.5);
            List<Atom> heavyElements = atomicSystem.stellarNucleosynthesis(stellarTemp);
            if (!heavyElements.isEmpty() && eventLog.size() < 100) {
                Map<String, Integer> counts = new LinkedHashMap<>();
                for (Atom a : heavyElements) {
                    counts.merge(a.symbol(), 1, Integer::sum);
                }
                eventLog.add(String.format("t=%d Stellar forge: %s", tick, counts));
            }
        }
        quantumField.evolve(1.0);
    }

    private boolean solarSystemInitialized = false;

    /** Solar system formation. */
    private void stepSolarSystem() {
        if (!solarSystemInitialized) {
            solarSystemInitialized = true;
            // Supernova enrichment: a nearby supernova seeds the protoplanetary disk
            // with heavier elements essential for rocky planets and chemistry.
            // This supplements what stellar nucleosynthesis has already produced.
            int nC = 15, nN = 10, nO = 20;
            for (int i = 0; i < nC; i++) {
                atomicSystem.getAtoms().add(new Atom(6, 12, 0,
                        new double[]{rng.nextGaussian(), rng.nextGaussian(), rng.nextGaussian()}));
            }
            for (int i = 0; i < nN; i++) {
                atomicSystem.getAtoms().add(new Atom(7, 14, 0,
                        new double[]{rng.nextGaussian(), rng.nextGaussian(), rng.nextGaussian()}));
            }
            for (int i = 0; i < nO; i++) {
                atomicSystem.getAtoms().add(new Atom(8, 16, 0,
                        new double[]{rng.nextGaussian(), rng.nextGaussian(), rng.nextGaussian()}));
            }
            eventLog.add(String.format("t=%d Supernova enrichment: +%dC +%dN +%dO",
                    tick, nC, nN, nO));

            // Form molecules from the enriched element mix
            chemicalSystem.formWater();
            chemicalSystem.formMethane();
            chemicalSystem.formAmmonia();
            eventLog.add(String.format("t=%d Solar system forms. Elements: %s  Molecules: %s",
                    tick, atomicSystem.elementCounts(), chemicalSystem.moleculeCensus()));
        }
    }

    private boolean earthInitialized = false;

    /** Earth formation: planet forms, oceans appear. */
    private void stepEarth() {
        // Initialize planetary environment (once)
        if (!earthInitialized) {
            earthInitialized = true;
            environment.initializeEarlyEarth();
            eventLog.add(String.format("t=%d Earth forms! %s", tick, environment.toCompact()));
        }

        // Geological cooling
        environment.geologicalCooling(2.0);

        // More chemistry on the cooling planet
        chemicalSystem.formWater();
        boolean catalystPresent = environment.hasLiquidWater();
        chemicalSystem.catalyzedReaction(environment.getSurfaceTemperature(), catalystPresent);

        // Atmosphere evolution (no photosynthesis yet)
        environment.evolveAtmosphere(false);
    }

    /** Life epoch: first self-replicating molecules. */
    private void stepLife() {
        // Continue geological and chemical processes
        environment.geologicalCooling(0.5);
        environment.evolveAtmosphere(false);

        double surfTemp = environment.getSurfaceTemperature();
        boolean catalystPresent = environment.hasLiquidWater();
        chemicalSystem.catalyzedReaction(surfTemp, catalystPresent);

        // Abiogenesis: when conditions are right, life emerges
        // Life can emerge once we have liquid water (we relax the amino acid requirement
        // because the simulation may not produce them depending on atom availability)
        if (environment.hasLiquidWater()) {
            if (tick == LIFE_EPOCH || biologicalSystem.getLifeforms().isEmpty()) {
                // First self-replicating molecules!
                BiologicalSystem.DNA firstDNA = biologicalSystem.abiogenesis(30);
                eventLog.add(String.format("t=%d ABIOGENESIS! First self-replicating molecule: %s",
                        tick, firstDNA.toCompact()));

                // Spawn first lifeform
                BiologicalSystem.Lifeform firstLife =
                        biologicalSystem.spawnLifeform("protocell", 30);
                eventLog.add(String.format("t=%d First lifeform: %s",
                        tick, firstLife.toCompact()));
            }

            // Evolve existing life
            double envPressure = environment.environmentalPressure();
            biologicalSystem.evolve(envPressure);
        }
    }

    /** DNA era: DNA-based life, epigenetics emerge. */
    private void stepDNA() {
        environment.geologicalCooling(0.1);

        // Photosynthesis begins if we have enough lifeforms
        boolean photosynthesis = biologicalSystem.aliveCount() > 3;
        environment.evolveAtmosphere(photosynthesis);

        double surfTemp = environment.getSurfaceTemperature();
        boolean catalystPresent = environment.hasLiquidWater();
        chemicalSystem.catalyzedReaction(surfTemp, catalystPresent);

        // Spawn more diverse species over time
        if (rng.nextDouble() < 0.01 && biologicalSystem.aliveCount() < 50) {
            String[] species = {"cyanobacteria", "archaea", "eukaryote",
                                "algae", "fungus", "invertebrate", "fish",
                                "amphibian", "reptile", "mammal"};
            int idx = Math.min(species.length - 1,
                    (tick - DNA_EPOCH) * species.length / (PRESENT_EPOCH - DNA_EPOCH));
            biologicalSystem.spawnLifeform(species[idx], 60 + rng.nextInt(60));
        }

        // Evolve
        double envPressure = environment.environmentalPressure();
        biologicalSystem.evolve(envPressure);

        // Occasional UV radiation events
        if (rng.nextDouble() < 0.005) {
            double intensity = rng.nextDouble() * 0.3;
            biologicalSystem.uvRadiationEvent(intensity);
        }

        // DNA replication for surviving strands
        if (!biologicalSystem.getDnaStrands().isEmpty() && rng.nextDouble() < 0.05) {
            int idx = rng.nextInt(biologicalSystem.getDnaStrands().size());
            biologicalSystem.replicateDNA(biologicalSystem.getDnaStrands().get(idx));
        }
    }

    // --- Universe expansion ---

    /**
     * Temperature targets at each epoch boundary, so the physics
     * at each stage operates in the correct regime.
     */
    private static final double[] EPOCH_TEMPERATURES = {
        T_PLANCK,           // Planck
        T_PLANCK * 0.8,     // Inflation
        T_ELECTROWEAK,      // Electroweak
        T_QUARK_HADRON * 2, // Quark  (above confinement threshold)
        T_QUARK_HADRON * 0.5,// Hadron (below confinement threshold)
        T_NUCLEOSYNTHESIS,  // Nucleosynthesis
        T_RECOMBINATION,    // Recombination
        T_STELLAR_CORE,     // Star Formation
        T_STELLAR_CORE * 0.8,// Solar System
        T_EARTH_SURFACE * 2,// Earth
        T_EARTH_SURFACE,    // Life
        T_EARTH_SURFACE,    // DNA Era
        T_CMB               // Present
    };

    private void expandUniverse() {
        // Determine which epoch interval we are in and interpolate temperature
        int fromEpochIdx = 0;
        for (int i = 0; i < EPOCHS.size(); i++) {
            if (tick >= EPOCHS.get(i).startTick()) {
                fromEpochIdx = i;
            }
        }

        int toEpochIdx = Math.min(fromEpochIdx + 1, EPOCHS.size() - 1);
        int fromTick = EPOCHS.get(fromEpochIdx).startTick();
        int toTick = (toEpochIdx < EPOCHS.size())
                ? EPOCHS.get(toEpochIdx).startTick() : PRESENT_EPOCH;

        double fromTemp = EPOCH_TEMPERATURES[fromEpochIdx];
        double toTemp = EPOCH_TEMPERATURES[toEpochIdx];

        // Logarithmic interpolation between epoch boundary temperatures
        if (toTick > fromTick) {
            double frac = (double)(tick - fromTick) / (toTick - fromTick);
            frac = Math.max(0, Math.min(1, frac));
            temperature = fromTemp * Math.pow(toTemp / fromTemp, frac);
        }

        // Scale factor grows inversely with temperature
        if (tick <= INFLATION_EPOCH) {
            scaleFactor *= 2.0;
        } else {
            scaleFactor *= 1.0 + 1e-5;
        }

        quantumField.setTemperature(temperature);
    }

    // --- Summary ---

    public String summary() {
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("=== Universe at t=%d ===\n", tick));
        sb.append(String.format("  Epoch: %s\n", currentEpoch().name()));
        sb.append(String.format("  Temperature: %.3e K\n", temperature));
        sb.append(String.format("  Scale factor: %.3e\n", scaleFactor));
        sb.append(String.format("  Total energy: %.3e\n", totalEnergy));
        sb.append(String.format("  Particles: %d\n", quantumField.getParticles().size()));
        sb.append(String.format("  Atoms: %d\n", atomicSystem.getAtoms().size()));
        sb.append(String.format("  Molecules: %d\n", chemicalSystem.getMolecules().size()));
        sb.append(String.format("  Lifeforms: %d alive\n", biologicalSystem.aliveCount()));
        return sb.toString();
    }
}
