package com.inthebeginning.simulator;

import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

import static com.inthebeginning.simulator.Constants.*;

/**
 * A quantum particle with position, momentum, and quantum numbers.
 * Tracks wave function amplitude/phase, spin, color charge, and entanglement.
 */
public class Particle {

    /** Spin eigenstate. */
    public enum Spin {
        UP(+0.5), DOWN(-0.5);
        private final double value;
        Spin(double v) { this.value = v; }
        public double value() { return value; }
    }

    /** Color charge for quarks. */
    public enum Color {
        RED, GREEN, BLUE, ANTI_RED, ANTI_GREEN, ANTI_BLUE
    }

    private static final AtomicInteger idCounter = new AtomicInteger(0);

    private final int particleId;
    private ParticleType type;
    private final double[] position;
    private final double[] momentum;
    private Spin spin;
    private Color color;

    // Simplified wave function
    private double wfAmplitude = 1.0;
    private double wfPhase = 0.0;
    private boolean wfCoherent = true;

    private int entangledWith = -1; // ID of entangled partner, -1 = none

    public Particle(ParticleType type) {
        this(type, new double[]{0, 0, 0}, new double[]{0, 0, 0}, Spin.UP, null);
    }

    public Particle(ParticleType type, double[] position, double[] momentum) {
        this(type, position, momentum, Spin.UP, null);
    }

    public Particle(ParticleType type, double[] position, double[] momentum,
                     Spin spin, Color color) {
        this.particleId = idCounter.incrementAndGet();
        this.type = type;
        this.position = position.clone();
        this.momentum = momentum.clone();
        this.spin = spin;
        this.color = color;
    }

    // --- Properties ---

    public int particleId()   { return particleId; }
    public ParticleType type(){ return type; }
    public void setType(ParticleType t) { this.type = t; }
    public double[] position(){ return position; }
    public double[] momentum(){ return momentum; }
    public Spin spin()        { return spin; }
    public void setSpin(Spin s) { this.spin = s; }
    public Color color()      { return color; }
    public void setColor(Color c) { this.color = c; }
    public int entangledWith(){ return entangledWith; }
    public void setEntangledWith(int id) { this.entangledWith = id; }

    public double mass()   { return type.mass(); }
    public double charge() { return type.charge(); }

    /** E = sqrt(p^2 c^2 + m^2 c^4) */
    public double energy() {
        double p2 = momentum[0]*momentum[0] + momentum[1]*momentum[1] + momentum[2]*momentum[2];
        return Math.sqrt(p2 * C * C + Math.pow(mass() * C * C, 2));
    }

    /** de Broglie wavelength: lambda = h / p */
    public double wavelength() {
        double p = Math.sqrt(momentum[0]*momentum[0] + momentum[1]*momentum[1] + momentum[2]*momentum[2]);
        if (p < 1e-20) return Double.POSITIVE_INFINITY;
        return 2 * PI * HBAR / p;
    }

    // --- Wave function ---

    public double wfAmplitude()  { return wfAmplitude; }
    public double wfPhase()      { return wfPhase; }
    public boolean wfCoherent()  { return wfCoherent; }
    public double wfProbability(){ return wfAmplitude * wfAmplitude; }

    /** Time evolution: phase rotation by E*dt/hbar. */
    public void evolveWaveFunction(double dt, double energy) {
        if (wfCoherent) {
            wfPhase += energy * dt / HBAR;
            wfPhase %= (2 * PI);
        }
    }

    /** Measurement: collapse to eigenstate. Returns true if 'detected'. */
    public boolean collapseWaveFunction(Random rng) {
        boolean result = rng.nextDouble() < wfProbability();
        wfAmplitude = result ? 1.0 : 0.0;
        wfCoherent = false;
        return result;
    }

    public void setWfCoherent(boolean c) { this.wfCoherent = c; }

    // --- Movement ---

    /** Update position from momentum for one time step. */
    public void updatePosition(double dt) {
        if (mass() > 0) {
            for (int i = 0; i < 3; i++) {
                position[i] += momentum[i] / mass() * dt;
            }
        } else {
            double pMag = Math.sqrt(momentum[0]*momentum[0] + momentum[1]*momentum[1] + momentum[2]*momentum[2]);
            if (pMag < 1e-30) pMag = 1.0;
            for (int i = 0; i < 3; i++) {
                position[i] += momentum[i] / pMag * C * dt;
            }
        }
    }

    public String toCompact() {
        return String.format("%s[%.1f,%.1f,%.1f]s=%.1f",
                type.label(), position[0], position[1], position[2], spin.value());
    }

    @Override
    public String toString() {
        return toCompact();
    }
}
