package com.inthebeginning.simulator;

/**
 * Enumeration of all particle types in the simulation.
 * Includes quarks, leptons, gauge bosons, and composite particles.
 */
public enum ParticleType {
    // Quarks
    UP("up", Constants.M_UP_QUARK, 2.0 / 3.0),
    DOWN("down", Constants.M_DOWN_QUARK, -1.0 / 3.0),

    // Leptons
    ELECTRON("electron", Constants.M_ELECTRON, -1.0),
    POSITRON("positron", Constants.M_ELECTRON, 1.0),
    NEUTRINO("neutrino", Constants.M_NEUTRINO, 0.0),

    // Gauge bosons
    PHOTON("photon", Constants.M_PHOTON, 0.0),
    GLUON("gluon", Constants.M_PHOTON, 0.0),
    W_BOSON("W", Constants.M_W_BOSON, 0.0),
    Z_BOSON("Z", Constants.M_Z_BOSON, 0.0),

    // Composite
    PROTON("proton", Constants.M_PROTON, 1.0),
    NEUTRON("neutron", Constants.M_NEUTRON, 0.0);

    private final String label;
    private final double mass;
    private final double charge;

    ParticleType(String label, double mass, double charge) {
        this.label = label;
        this.mass = mass;
        this.charge = charge;
    }

    public String label() { return label; }
    public double mass()  { return mass; }
    public double charge() { return charge; }
}
