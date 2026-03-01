package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Represents a quantum field that can create and annihilate particles.
 * Manages pair production, annihilation, quark confinement, and vacuum fluctuations.
 */
public class QuantumField {

    private double temperature;
    private final List<Particle> particles = new ArrayList<>();
    private double vacuumEnergy = 0.0;
    private int totalCreated = 0;
    private int totalAnnihilated = 0;
    private final Random rng;

    public QuantumField(double temperature, Random rng) {
        this.temperature = temperature;
        this.rng = rng;
    }

    // --- Accessors ---

    public double getTemperature()          { return temperature; }
    public void setTemperature(double t)    { this.temperature = t; }
    public List<Particle> getParticles()    { return particles; }
    public double getVacuumEnergy()         { return vacuumEnergy; }
    public int getTotalCreated()            { return totalCreated; }
    public int getTotalAnnihilated()        { return totalAnnihilated; }

    // --- Pair production ---

    /**
     * Create particle-antiparticle pair from vacuum energy.
     * Requires E >= 2mc^2 for the lightest possible pair.
     * @return the created pair, or null if insufficient energy
     */
    public Particle[] pairProduction(double energy) {
        if (energy < 2 * M_ELECTRON * C * C) {
            return null;
        }

        ParticleType pType, apType;
        if (energy >= 2 * M_PROTON * C * C && rng.nextDouble() < 0.1) {
            pType = ParticleType.UP;
            apType = ParticleType.DOWN;
        } else {
            pType = ParticleType.ELECTRON;
            apType = ParticleType.POSITRON;
        }

        double[] direction = {rng.nextGaussian(), rng.nextGaussian(), rng.nextGaussian()};
        double norm = Math.sqrt(direction[0]*direction[0] + direction[1]*direction[1] + direction[2]*direction[2]);
        if (norm < 1e-20) norm = 1.0;
        double pMomentum = energy / (2 * C);

        double[] mom1 = new double[3];
        double[] mom2 = new double[3];
        for (int i = 0; i < 3; i++) {
            mom1[i] = direction[i] / norm * pMomentum;
            mom2[i] = -direction[i] / norm * pMomentum;
        }

        Particle particle = new Particle(pType, new double[]{0,0,0}, mom1,
                Particle.Spin.UP, null);
        Particle antiparticle = new Particle(apType, new double[]{0,0,0}, mom2,
                Particle.Spin.DOWN, null);

        particle.setEntangledWith(antiparticle.particleId());
        antiparticle.setEntangledWith(particle.particleId());

        particles.add(particle);
        particles.add(antiparticle);
        totalCreated += 2;

        return new Particle[]{particle, antiparticle};
    }

    /**
     * Annihilate particle-antiparticle pair, returning energy as photons.
     */
    public double annihilate(Particle p1, Particle p2) {
        double energy = p1.energy() + p2.energy();
        particles.remove(p1);
        particles.remove(p2);
        totalAnnihilated += 2;
        vacuumEnergy += energy * 0.01;

        Particle photon1 = new Particle(ParticleType.PHOTON,
                new double[]{0,0,0}, new double[]{energy / (2*C), 0, 0});
        Particle photon2 = new Particle(ParticleType.PHOTON,
                new double[]{0,0,0}, new double[]{-energy / (2*C), 0, 0});
        particles.add(photon1);
        particles.add(photon2);
        return energy;
    }

    /**
     * Combine quarks into hadrons (protons and neutrons) when temperature drops below T_QUARK_HADRON.
     */
    public List<Particle> quarkConfinement() {
        if (temperature > T_QUARK_HADRON) {
            return Collections.emptyList();
        }

        List<Particle> hadrons = new ArrayList<>();
        List<Particle> ups = new ArrayList<>();
        List<Particle> downs = new ArrayList<>();

        for (Particle p : particles) {
            if (p.type() == ParticleType.UP) ups.add(p);
            else if (p.type() == ParticleType.DOWN) downs.add(p);
        }

        // Form protons (uud)
        while (ups.size() >= 2 && downs.size() >= 1) {
            Particle u1 = ups.remove(ups.size() - 1);
            Particle u2 = ups.remove(ups.size() - 1);
            Particle d1 = downs.remove(downs.size() - 1);

            u1.setColor(Particle.Color.RED);
            u2.setColor(Particle.Color.GREEN);
            d1.setColor(Particle.Color.BLUE);

            double[] mom = new double[3];
            for (int i = 0; i < 3; i++) {
                mom[i] = u1.momentum()[i] + u2.momentum()[i] + d1.momentum()[i];
            }

            Particle proton = new Particle(ParticleType.PROTON,
                    u1.position().clone(), mom);

            particles.remove(u1);
            particles.remove(u2);
            particles.remove(d1);
            particles.add(proton);
            hadrons.add(proton);
        }

        // Form neutrons (udd)
        while (ups.size() >= 1 && downs.size() >= 2) {
            Particle u1 = ups.remove(ups.size() - 1);
            Particle d1 = downs.remove(downs.size() - 1);
            Particle d2 = downs.remove(downs.size() - 1);

            u1.setColor(Particle.Color.RED);
            d1.setColor(Particle.Color.GREEN);
            d2.setColor(Particle.Color.BLUE);

            double[] mom = new double[3];
            for (int i = 0; i < 3; i++) {
                mom[i] = u1.momentum()[i] + d1.momentum()[i] + d2.momentum()[i];
            }

            Particle neutron = new Particle(ParticleType.NEUTRON,
                    u1.position().clone(), mom);

            particles.remove(u1);
            particles.remove(d1);
            particles.remove(d2);
            particles.add(neutron);
            hadrons.add(neutron);
        }

        return hadrons;
    }

    /**
     * Spontaneous virtual particle pair from vacuum energy.
     * Probability scales with temperature.
     */
    public Particle[] vacuumFluctuation() {
        double prob = Math.min(0.5, temperature / T_PLANCK);
        if (rng.nextDouble() < prob) {
            // Exponential variate with mean = temperature * 0.001
            double lambda = 1.0 / (temperature * 0.001);
            double energy = -Math.log(1.0 - rng.nextDouble()) / lambda;
            return pairProduction(energy);
        }
        return null;
    }

    /**
     * Cool the field (universe expansion).
     */
    public void cool(double factor) {
        temperature *= factor;
    }

    /**
     * Evolve all particles by one time step.
     */
    public void evolve(double dt) {
        for (Particle p : particles) {
            p.updatePosition(dt);
            p.evolveWaveFunction(dt, p.energy());
        }
    }

    /** Count particles by type. */
    public Map<String, Integer> particleCount() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (Particle p : particles) {
            counts.merge(p.type().label(), 1, Integer::sum);
        }
        return counts;
    }

    /** Total energy in the field. */
    public double totalEnergy() {
        double sum = vacuumEnergy;
        for (Particle p : particles) {
            sum += p.energy();
        }
        return sum;
    }

    public String toCompact() {
        Map<String, Integer> counts = particleCount();
        StringBuilder sb = new StringBuilder();
        counts.entrySet().stream().sorted(Map.Entry.comparingByKey())
                .forEach(e -> {
                    if (sb.length() > 0) sb.append(",");
                    sb.append(e.getKey()).append(":").append(e.getValue());
                });
        return String.format("QF[T=%.1e E=%.1e n=%d %s]",
                temperature, totalEnergy(), particles.size(), sb);
    }
}
