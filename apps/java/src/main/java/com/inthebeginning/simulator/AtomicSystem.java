package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Collection of atoms with interactions.
 * Handles nucleosynthesis, recombination, stellar nucleosynthesis, and bonding.
 */
public class AtomicSystem {

    private final List<Atom> atoms = new ArrayList<>();
    private double temperature;
    private int bondsFormed = 0;
    private int bondsBroken = 0;
    private final Random rng;

    public AtomicSystem(Random rng) {
        this(T_RECOMBINATION, rng);
    }

    public AtomicSystem(double temperature, Random rng) {
        this.temperature = temperature;
        this.rng = rng;
    }

    // --- Accessors ---

    public List<Atom> getAtoms()        { return atoms; }
    public double getTemperature()      { return temperature; }
    public void setTemperature(double t){ this.temperature = t; }
    public int getBondsFormed()         { return bondsFormed; }

    // --- Recombination ---

    /**
     * Capture free electrons into ions when T < T_recombination.
     * Converts protons + electrons from the quantum field into hydrogen atoms.
     */
    public List<Atom> recombination(QuantumField field) {
        if (temperature > T_RECOMBINATION) {
            return Collections.emptyList();
        }

        List<Atom> newAtoms = new ArrayList<>();
        List<Particle> protons = new ArrayList<>();
        List<Particle> electrons = new ArrayList<>();

        for (Particle p : field.getParticles()) {
            if (p.type() == ParticleType.PROTON) protons.add(p);
            else if (p.type() == ParticleType.ELECTRON) electrons.add(p);
        }

        for (Particle proton : protons) {
            if (electrons.isEmpty()) break;
            Particle electron = electrons.remove(electrons.size() - 1);

            Atom atom = new Atom(1, 1, proton.position(), proton.momentum());
            newAtoms.add(atom);
            atoms.add(atom);

            field.getParticles().remove(proton);
            field.getParticles().remove(electron);
        }

        return newAtoms;
    }

    // --- Nucleosynthesis ---

    /**
     * Form heavier elements through nuclear fusion.
     * Combines protons and neutrons into nuclei (He-4, remaining H).
     */
    public List<Atom> nucleosynthesis(int protons, int neutrons) {
        List<Atom> newAtoms = new ArrayList<>();

        // Helium-4: 2 protons + 2 neutrons
        while (protons >= 2 && neutrons >= 2) {
            Atom he = new Atom(2, 4, 0,
                    new double[]{rng.nextGaussian() * 10, rng.nextGaussian() * 10, rng.nextGaussian() * 10});
            newAtoms.add(he);
            atoms.add(he);
            protons -= 2;
            neutrons -= 2;
        }

        // Remaining protons become hydrogen
        for (int i = 0; i < protons; i++) {
            Atom h = new Atom(1, 1, 0,
                    new double[]{rng.nextGaussian() * 10, rng.nextGaussian() * 10, rng.nextGaussian() * 10});
            newAtoms.add(h);
            atoms.add(h);
        }

        return newAtoms;
    }

    // --- Stellar nucleosynthesis ---

    /**
     * Form heavier elements in stellar cores.
     * Carbon (6), Nitrogen (7), Oxygen (8), up to Iron (26).
     */
    public List<Atom> stellarNucleosynthesis(double temperature) {
        List<Atom> newAtoms = new ArrayList<>();
        if (temperature < 1e3) return newAtoms;

        List<Atom> heliums = new ArrayList<>();
        for (Atom a : atoms) {
            if (a.atomicNumber() == 2) heliums.add(a);
        }

        // Triple-alpha process: 3 He -> C
        while (heliums.size() >= 3 && rng.nextDouble() < 0.01) {
            for (int i = 0; i < 3; i++) {
                Atom he = heliums.remove(heliums.size() - 1);
                atoms.remove(he);
            }
            Atom carbon = new Atom(6, 12, 0,
                    new double[]{rng.nextGaussian() * 5, rng.nextGaussian() * 5, rng.nextGaussian() * 5});
            newAtoms.add(carbon);
            atoms.add(carbon);
        }

        // C + He -> O
        List<Atom> carbons = new ArrayList<>();
        heliums.clear();
        for (Atom a : atoms) {
            if (a.atomicNumber() == 6) carbons.add(a);
            else if (a.atomicNumber() == 2) heliums.add(a);
        }

        while (!carbons.isEmpty() && !heliums.isEmpty() && rng.nextDouble() < 0.02) {
            Atom c = carbons.remove(carbons.size() - 1);
            Atom he = heliums.remove(heliums.size() - 1);
            atoms.remove(c);
            atoms.remove(he);

            Atom oxygen = new Atom(8, 16, 0, c.position().clone());
            newAtoms.add(oxygen);
            atoms.add(oxygen);
        }

        // O + He -> N (simplified chain)
        List<Atom> oxygens = new ArrayList<>();
        heliums.clear();
        for (Atom a : atoms) {
            if (a.atomicNumber() == 8) oxygens.add(a);
            else if (a.atomicNumber() == 2) heliums.add(a);
        }

        if (!oxygens.isEmpty() && !heliums.isEmpty() && rng.nextDouble() < 0.005) {
            Atom o = oxygens.get(0);
            Atom he = heliums.get(0);
            atoms.remove(o);
            atoms.remove(he);

            Atom nitrogen = new Atom(7, 14, 0, o.position().clone());
            newAtoms.add(nitrogen);
            atoms.add(nitrogen);
        }

        return newAtoms;
    }

    // --- Bonding ---

    public boolean attemptBond(Atom a1, Atom a2) {
        if (!a1.canBondWith(a2)) return false;

        double dist = a1.distanceTo(a2);
        double bondDist = 2.0;
        if (dist > bondDist * 3) return false;

        double energyBarrier = a1.bondEnergy(a2);
        double thermalEnergy = K_B * temperature;
        double prob;
        if (thermalEnergy > 0) {
            prob = Math.exp(-energyBarrier / thermalEnergy);
        } else {
            prob = dist < bondDist ? 1.0 : 0.0;
        }

        if (rng.nextDouble() < prob) {
            a1.bonds().add(a2.atomId());
            a2.bonds().add(a1.atomId());
            bondsFormed++;
            return true;
        }
        return false;
    }

    public boolean breakBond(Atom a1, Atom a2) {
        if (!a1.bonds().contains(a2.atomId())) return false;

        double energyBarrier = a1.bondEnergy(a2);
        double thermalEnergy = K_B * temperature;

        if (thermalEnergy > energyBarrier * 0.5) {
            double prob = Math.exp(-energyBarrier / (thermalEnergy + 1e-20));
            if (rng.nextDouble() < prob) {
                a1.bonds().remove(Integer.valueOf(a2.atomId()));
                a2.bonds().remove(Integer.valueOf(a1.atomId()));
                bondsBroken++;
                return true;
            }
        }
        return false;
    }

    /** Count atoms by element symbol. */
    public Map<String, Integer> elementCounts() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (Atom a : atoms) {
            counts.merge(a.symbol(), 1, Integer::sum);
        }
        return counts;
    }

    public String toCompact() {
        Map<String, Integer> counts = elementCounts();
        StringBuilder sb = new StringBuilder();
        counts.entrySet().stream().sorted(Map.Entry.comparingByKey())
                .forEach(e -> {
                    if (sb.length() > 0) sb.append(",");
                    sb.append(e.getKey()).append(":").append(e.getValue());
                });
        return String.format("AS[T=%.1e n=%d bonds=%d %s]",
                temperature, atoms.size(), bondsFormed, sb);
    }
}
