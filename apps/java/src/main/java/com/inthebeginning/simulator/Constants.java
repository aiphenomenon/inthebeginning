package com.inthebeginning.simulator;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Physical constants and simulation parameters.
 * All values are in simulation units (SU) scaled for computational tractability.
 * Real-world proportions are maintained where possible.
 */
public final class Constants {

    private Constants() {}

    // === Fundamental Constants (simulation-scaled) ===
    public static final double C = 1.0;                    // Speed of light (SU)
    public static final double HBAR = 0.01;               // Reduced Planck constant (SU)
    public static final double K_B = 0.001;               // Boltzmann constant (SU)
    public static final double G = 1e-6;                  // Gravitational constant (SU)
    public static final double ALPHA = 1.0 / 137.0;       // Fine structure constant
    public static final double E_CHARGE = 0.1;            // Elementary charge (SU)
    public static final double PI = Math.PI;

    // === Particle masses (SU, proportional to real) ===
    public static final double M_ELECTRON = 1.0;
    public static final double M_UP_QUARK = 4.4;
    public static final double M_DOWN_QUARK = 9.4;
    public static final double M_PROTON = 1836.0;
    public static final double M_NEUTRON = 1839.0;
    public static final double M_PHOTON = 0.0;
    public static final double M_NEUTRINO = 1e-6;
    public static final double M_W_BOSON = 157000.0;
    public static final double M_Z_BOSON = 178000.0;
    public static final double M_HIGGS = 245000.0;

    // === Force coupling strengths (dimensionless) ===
    public static final double STRONG_COUPLING = 1.0;
    public static final double EM_COUPLING = ALPHA;
    public static final double WEAK_COUPLING = 1e-6;
    public static final double GRAVITY_COUPLING = 1e-38;

    // === Nuclear parameters ===
    public static final double NUCLEAR_RADIUS = 0.01;
    public static final double BINDING_ENERGY_DEUTERIUM = 2.22;
    public static final double BINDING_ENERGY_HELIUM4 = 28.3;
    public static final double BINDING_ENERGY_CARBON12 = 92.16;
    public static final double BINDING_ENERGY_IRON56 = 492.26;

    // === Cosmic timeline (simulation ticks) ===
    public static final int PLANCK_EPOCH = 1;
    public static final int INFLATION_EPOCH = 10;
    public static final int ELECTROWEAK_EPOCH = 100;
    public static final int QUARK_EPOCH = 1000;
    public static final int HADRON_EPOCH = 5000;
    public static final int NUCLEOSYNTHESIS_EPOCH = 10000;
    public static final int RECOMBINATION_EPOCH = 50000;
    public static final int STAR_FORMATION_EPOCH = 100000;
    public static final int SOLAR_SYSTEM_EPOCH = 200000;
    public static final int EARTH_EPOCH = 210000;
    public static final int LIFE_EPOCH = 250000;
    public static final int DNA_EPOCH = 280000;
    public static final int PRESENT_EPOCH = 300000;

    // === Temperature scale (simulation Kelvin) ===
    public static final double T_PLANCK = 1e10;
    public static final double T_ELECTROWEAK = 1e8;
    public static final double T_QUARK_HADRON = 1e6;
    public static final double T_NUCLEOSYNTHESIS = 1e4;
    public static final double T_RECOMBINATION = 3000.0;
    public static final double T_CMB = 2.725;
    public static final double T_STELLAR_CORE = 1.5e4;
    public static final double T_EARTH_SURFACE = 288.0;

    // === Chemistry parameters ===
    public static final int[] ELECTRON_SHELLS = {2, 8, 18, 32, 32, 18, 8};
    public static final double BOND_ENERGY_COVALENT = 3.5;
    public static final double BOND_ENERGY_IONIC = 5.0;
    public static final double BOND_ENERGY_HYDROGEN = 0.2;
    public static final double BOND_ENERGY_VAN_DER_WAALS = 0.01;

    // === Biology parameters ===
    public static final String[] NUCLEOTIDE_BASES = {"A", "T", "G", "C"};
    public static final String[] RNA_BASES = {"A", "U", "G", "C"};
    public static final String[] AMINO_ACIDS = {
        "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
        "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
        "Thr", "Trp", "Tyr", "Val"
    };

    /** Codon table mapping RNA triplets to amino acids. */
    public static final Map<String, String> CODON_TABLE;
    static {
        Map<String, String> ct = new LinkedHashMap<>();
        ct.put("AUG", "Met");   // Start
        ct.put("UUU", "Phe"); ct.put("UUC", "Phe");
        ct.put("UUA", "Leu"); ct.put("UUG", "Leu"); ct.put("CUU", "Leu"); ct.put("CUC", "Leu");
        ct.put("CUA", "Leu"); ct.put("CUG", "Leu");
        ct.put("AUU", "Ile"); ct.put("AUC", "Ile"); ct.put("AUA", "Ile");
        ct.put("GUU", "Val"); ct.put("GUC", "Val"); ct.put("GUA", "Val"); ct.put("GUG", "Val");
        ct.put("UCU", "Ser"); ct.put("UCC", "Ser"); ct.put("UCA", "Ser"); ct.put("UCG", "Ser");
        ct.put("CCU", "Pro"); ct.put("CCC", "Pro"); ct.put("CCA", "Pro"); ct.put("CCG", "Pro");
        ct.put("ACU", "Thr"); ct.put("ACC", "Thr"); ct.put("ACA", "Thr"); ct.put("ACG", "Thr");
        ct.put("GCU", "Ala"); ct.put("GCC", "Ala"); ct.put("GCA", "Ala"); ct.put("GCG", "Ala");
        ct.put("UAU", "Tyr"); ct.put("UAC", "Tyr");
        ct.put("CAU", "His"); ct.put("CAC", "His");
        ct.put("CAA", "Gln"); ct.put("CAG", "Gln");
        ct.put("AAU", "Asn"); ct.put("AAC", "Asn");
        ct.put("AAA", "Lys"); ct.put("AAG", "Lys");
        ct.put("GAU", "Asp"); ct.put("GAC", "Asp");
        ct.put("GAA", "Glu"); ct.put("GAG", "Glu");
        ct.put("UGU", "Cys"); ct.put("UGC", "Cys");
        ct.put("UGG", "Trp");
        ct.put("CGU", "Arg"); ct.put("CGC", "Arg"); ct.put("CGA", "Arg"); ct.put("CGG", "Arg");
        ct.put("AGU", "Ser"); ct.put("AGC", "Ser");
        ct.put("AGA", "Arg"); ct.put("AGG", "Arg");
        ct.put("GGU", "Gly"); ct.put("GGC", "Gly"); ct.put("GGA", "Gly"); ct.put("GGG", "Gly");
        ct.put("UAA", "STOP"); ct.put("UAG", "STOP"); ct.put("UGA", "STOP");
        CODON_TABLE = Collections.unmodifiableMap(ct);
    }

    // === Epigenetic parameters ===
    public static final double METHYLATION_PROBABILITY = 0.03;
    public static final double DEMETHYLATION_PROBABILITY = 0.01;
    public static final double HISTONE_ACETYLATION_PROB = 0.02;
    public static final double HISTONE_DEACETYLATION_PROB = 0.015;
    public static final double CHROMATIN_REMODEL_ENERGY = 1.5;

    // === Environmental parameters ===
    public static final double UV_MUTATION_RATE = 1e-4;
    public static final double COSMIC_RAY_MUTATION_RATE = 1e-6;
    public static final double THERMAL_FLUCTUATION = 0.01;
    public static final double RADIATION_DAMAGE_THRESHOLD = 10.0;

    // === Periodic table data: atomicNumber -> (symbol, name, group, period, electronegativity) ===
    public record ElementInfo(String symbol, String name, int group, int period, double electronegativity) {}

    public static final Map<Integer, ElementInfo> ELEMENTS;
    static {
        Map<Integer, ElementInfo> e = new LinkedHashMap<>();
        e.put(1,  new ElementInfo("H",  "Hydrogen",   1,  1, 2.20));
        e.put(2,  new ElementInfo("He", "Helium",    18,  1, 0.0));
        e.put(3,  new ElementInfo("Li", "Lithium",    1,  2, 0.98));
        e.put(4,  new ElementInfo("Be", "Beryllium",  2,  2, 1.57));
        e.put(5,  new ElementInfo("B",  "Boron",     13,  2, 2.04));
        e.put(6,  new ElementInfo("C",  "Carbon",    14,  2, 2.55));
        e.put(7,  new ElementInfo("N",  "Nitrogen",  15,  2, 3.04));
        e.put(8,  new ElementInfo("O",  "Oxygen",    16,  2, 3.44));
        e.put(9,  new ElementInfo("F",  "Fluorine",  17,  2, 3.98));
        e.put(10, new ElementInfo("Ne", "Neon",      18,  2, 0.0));
        e.put(11, new ElementInfo("Na", "Sodium",     1,  3, 0.93));
        e.put(12, new ElementInfo("Mg", "Magnesium",  2,  3, 1.31));
        e.put(13, new ElementInfo("Al", "Aluminum",  13,  3, 1.61));
        e.put(14, new ElementInfo("Si", "Silicon",   14,  3, 1.90));
        e.put(15, new ElementInfo("P",  "Phosphorus",15,  3, 2.19));
        e.put(16, new ElementInfo("S",  "Sulfur",    16,  3, 2.58));
        e.put(17, new ElementInfo("Cl", "Chlorine",  17,  3, 3.16));
        e.put(18, new ElementInfo("Ar", "Argon",     18,  3, 0.0));
        e.put(19, new ElementInfo("K",  "Potassium",  1,  4, 0.82));
        e.put(20, new ElementInfo("Ca", "Calcium",    2,  4, 1.00));
        e.put(26, new ElementInfo("Fe", "Iron",       8,  4, 1.83));
        ELEMENTS = Collections.unmodifiableMap(e);
    }

    // === Epoch info for display ===
    public record EpochInfo(String name, int startTick, String description) {}

    public static final List<EpochInfo> EPOCHS = List.of(
        new EpochInfo("Planck",          PLANCK_EPOCH,          "All forces unified, T~10^32K"),
        new EpochInfo("Inflation",       INFLATION_EPOCH,       "Exponential expansion, quantum fluctuations seed structure"),
        new EpochInfo("Electroweak",     ELECTROWEAK_EPOCH,     "Electromagnetic and weak forces separate"),
        new EpochInfo("Quark",           QUARK_EPOCH,           "Quark-gluon plasma, free quarks"),
        new EpochInfo("Hadron",          HADRON_EPOCH,          "Quarks confined into protons and neutrons"),
        new EpochInfo("Nucleosynthesis", NUCLEOSYNTHESIS_EPOCH, "Light nuclei form: H, He, Li"),
        new EpochInfo("Recombination",   RECOMBINATION_EPOCH,   "Atoms form, universe becomes transparent"),
        new EpochInfo("Star Formation",  STAR_FORMATION_EPOCH,  "First stars ignite, heavier elements forged"),
        new EpochInfo("Solar System",    SOLAR_SYSTEM_EPOCH,    "Our solar system coalesces from stellar debris"),
        new EpochInfo("Earth",           EARTH_EPOCH,           "Earth forms, oceans appear"),
        new EpochInfo("Life",            LIFE_EPOCH,            "First self-replicating molecules"),
        new EpochInfo("DNA Era",         DNA_EPOCH,             "DNA-based life, epigenetics emerge"),
        new EpochInfo("Present",         PRESENT_EPOCH,         "Complex life, intelligence")
    );
}
