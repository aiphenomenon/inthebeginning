package com.inthebeginning.simulator

import kotlin.math.PI

/**
 * Physical constants and simulation parameters.
 *
 * All values are in simulation units (SU) scaled for computational tractability.
 * Real-world proportions are maintained where possible.
 */
object Constants {

    // === Fundamental Constants (simulation-scaled) ===
    const val C = 1.0                       // Speed of light (SU)
    const val HBAR = 0.01                   // Reduced Planck constant (SU)
    const val K_B = 0.001                   // Boltzmann constant (SU)
    const val G = 1e-6                      // Gravitational constant (SU)
    const val ALPHA = 1.0 / 137.0           // Fine structure constant (dimensionless)
    const val E_CHARGE = 0.1                // Elementary charge (SU)
    const val PI_VAL = PI

    // === Particle masses (SU, proportional to real) ===
    const val M_ELECTRON = 1.0
    const val M_UP_QUARK = 4.4              // ~2.2 MeV / 0.511 MeV
    const val M_DOWN_QUARK = 9.4            // ~4.7 MeV / 0.511 MeV
    const val M_PROTON = 1836.0             // Real ratio to electron
    const val M_NEUTRON = 1839.0
    const val M_PHOTON = 0.0
    const val M_NEUTRINO = 1e-6
    const val M_W_BOSON = 157000.0
    const val M_Z_BOSON = 178000.0
    const val M_HIGGS = 245000.0

    // === Force coupling strengths (dimensionless) ===
    const val STRONG_COUPLING = 1.0
    const val EM_COUPLING = ALPHA
    const val WEAK_COUPLING = 1e-6
    const val GRAVITY_COUPLING = 1e-38

    // === Nuclear parameters ===
    const val NUCLEAR_RADIUS = 0.01         // SU
    const val BINDING_ENERGY_DEUTERIUM = 2.22   // MeV equivalent
    const val BINDING_ENERGY_HELIUM4 = 28.3
    const val BINDING_ENERGY_CARBON12 = 92.16
    const val BINDING_ENERGY_IRON56 = 492.26

    // === Cosmic timeline (simulation ticks) ===
    const val PLANCK_EPOCH = 1
    const val INFLATION_EPOCH = 10
    const val ELECTROWEAK_EPOCH = 100
    const val QUARK_EPOCH = 1000
    const val HADRON_EPOCH = 5000
    const val NUCLEOSYNTHESIS_EPOCH = 10000
    const val RECOMBINATION_EPOCH = 50000
    const val STAR_FORMATION_EPOCH = 100000
    const val SOLAR_SYSTEM_EPOCH = 200000
    const val EARTH_EPOCH = 210000
    const val LIFE_EPOCH = 250000
    const val DNA_EPOCH = 280000
    const val PRESENT_EPOCH = 300000

    // === Temperature scale (simulation Kelvin) ===
    const val T_PLANCK = 1e10
    const val T_ELECTROWEAK = 1e8
    const val T_QUARK_HADRON = 1e6
    const val T_NUCLEOSYNTHESIS = 1e4
    const val T_RECOMBINATION = 3000.0
    const val T_CMB = 2.725
    const val T_STELLAR_CORE = 1.5e4
    const val T_EARTH_SURFACE = 288.0

    // === Chemistry parameters ===
    val ELECTRON_SHELLS = intArrayOf(2, 8, 18, 32, 32, 18, 8)
    const val BOND_ENERGY_COVALENT = 3.5    // eV equivalent
    const val BOND_ENERGY_IONIC = 5.0
    const val BOND_ENERGY_HYDROGEN = 0.2
    const val BOND_ENERGY_VAN_DER_WAALS = 0.01

    // === Biology parameters ===
    val NUCLEOTIDE_BASES = listOf("A", "T", "G", "C")
    val RNA_BASES = listOf("A", "U", "G", "C")
    val AMINO_ACIDS = listOf(
        "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
        "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
        "Thr", "Trp", "Tyr", "Val"
    )

    val CODON_TABLE: Map<String, String> = mapOf(
        "AUG" to "Met",  // Start codon
        "UUU" to "Phe", "UUC" to "Phe",
        "UUA" to "Leu", "UUG" to "Leu", "CUU" to "Leu", "CUC" to "Leu",
        "CUA" to "Leu", "CUG" to "Leu",
        "AUU" to "Ile", "AUC" to "Ile", "AUA" to "Ile",
        "GUU" to "Val", "GUC" to "Val", "GUA" to "Val", "GUG" to "Val",
        "UCU" to "Ser", "UCC" to "Ser", "UCA" to "Ser", "UCG" to "Ser",
        "CCU" to "Pro", "CCC" to "Pro", "CCA" to "Pro", "CCG" to "Pro",
        "ACU" to "Thr", "ACC" to "Thr", "ACA" to "Thr", "ACG" to "Thr",
        "GCU" to "Ala", "GCC" to "Ala", "GCA" to "Ala", "GCG" to "Ala",
        "UAU" to "Tyr", "UAC" to "Tyr",
        "CAU" to "His", "CAC" to "His",
        "CAA" to "Gln", "CAG" to "Gln",
        "AAU" to "Asn", "AAC" to "Asn",
        "AAA" to "Lys", "AAG" to "Lys",
        "GAU" to "Asp", "GAC" to "Asp",
        "GAA" to "Glu", "GAG" to "Glu",
        "UGU" to "Cys", "UGC" to "Cys",
        "UGG" to "Trp",
        "CGU" to "Arg", "CGC" to "Arg", "CGA" to "Arg", "CGG" to "Arg",
        "AGU" to "Ser", "AGC" to "Ser",
        "AGA" to "Arg", "AGG" to "Arg",
        "GGU" to "Gly", "GGC" to "Gly", "GGA" to "Gly", "GGG" to "Gly",
        "UAA" to "STOP", "UAG" to "STOP", "UGA" to "STOP"
    )

    // === Epigenetic parameters ===
    const val METHYLATION_PROBABILITY = 0.03
    const val DEMETHYLATION_PROBABILITY = 0.01
    const val HISTONE_ACETYLATION_PROB = 0.02
    const val HISTONE_DEACETYLATION_PROB = 0.015
    const val CHROMATIN_REMODEL_ENERGY = 1.5

    // === Environmental parameters ===
    const val UV_MUTATION_RATE = 1e-4
    const val COSMIC_RAY_MUTATION_RATE = 1e-6
    const val THERMAL_FLUCTUATION = 0.01
    const val RADIATION_DAMAGE_THRESHOLD = 10.0
}

/**
 * Information about a cosmic epoch.
 */
data class EpochInfo(
    val name: String,
    val startTick: Int,
    val description: String,
    val keyEvents: MutableList<String> = mutableListOf()
)

/**
 * All cosmic epochs in chronological order.
 */
val EPOCHS = listOf(
    EpochInfo(
        "Planck", Constants.PLANCK_EPOCH,
        "All forces unified, T~10^32K"
    ),
    EpochInfo(
        "Inflation", Constants.INFLATION_EPOCH,
        "Exponential expansion, quantum fluctuations seed structure"
    ),
    EpochInfo(
        "Electroweak", Constants.ELECTROWEAK_EPOCH,
        "Electromagnetic and weak forces separate"
    ),
    EpochInfo(
        "Quark", Constants.QUARK_EPOCH,
        "Quark-gluon plasma, free quarks"
    ),
    EpochInfo(
        "Hadron", Constants.HADRON_EPOCH,
        "Quarks confined into protons and neutrons"
    ),
    EpochInfo(
        "Nucleosynthesis", Constants.NUCLEOSYNTHESIS_EPOCH,
        "Light nuclei form: H, He, Li"
    ),
    EpochInfo(
        "Recombination", Constants.RECOMBINATION_EPOCH,
        "Atoms form, universe becomes transparent"
    ),
    EpochInfo(
        "Star Formation", Constants.STAR_FORMATION_EPOCH,
        "First stars ignite, heavier elements forged"
    ),
    EpochInfo(
        "Solar System", Constants.SOLAR_SYSTEM_EPOCH,
        "Our solar system coalesces from stellar debris"
    ),
    EpochInfo(
        "Earth", Constants.EARTH_EPOCH,
        "Earth forms, oceans appear"
    ),
    EpochInfo(
        "Life", Constants.LIFE_EPOCH,
        "First self-replicating molecules"
    ),
    EpochInfo(
        "DNA Era", Constants.DNA_EPOCH,
        "DNA-based life, epigenetics emerge"
    ),
    EpochInfo(
        "Present", Constants.PRESENT_EPOCH,
        "Complex life, intelligence"
    )
)
