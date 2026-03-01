// Constants.swift
// InTheBeginning
//
// All physical constants and simulation parameters.
// Values are in simulation units (SU) scaled for computational tractability.
// Real-world proportions are maintained where possible.

import Foundation

// MARK: - Fundamental Constants (simulation-scaled)

enum PhysicsConstants {
    static let c: Double = 1.0                     // Speed of light (SU)
    static let hbar: Double = 0.01                 // Reduced Planck constant (SU)
    static let kB: Double = 0.001                  // Boltzmann constant (SU)
    static let G: Double = 1e-6                    // Gravitational constant (SU)
    static let alpha: Double = 1.0 / 137.0         // Fine structure constant
    static let eCharge: Double = 0.1               // Elementary charge (SU)
}

// MARK: - Particle Masses (SU, proportional to real)

enum ParticleMass {
    static let electron: Double = 1.0
    static let upQuark: Double = 4.4
    static let downQuark: Double = 9.4
    static let proton: Double = 1836.0
    static let neutron: Double = 1839.0
    static let photon: Double = 0.0
    static let neutrino: Double = 1e-6
    static let wBoson: Double = 157_000.0
    static let zBoson: Double = 178_000.0
    static let higgs: Double = 245_000.0
}

// MARK: - Force Coupling Strengths

enum ForceCoupling {
    static let strong: Double = 1.0
    static let electromagnetic: Double = PhysicsConstants.alpha
    static let weak: Double = 1e-6
    static let gravity: Double = 1e-38
}

// MARK: - Nuclear Parameters

enum NuclearParams {
    static let radius: Double = 0.01
    static let bindingEnergyDeuterium: Double = 2.22
    static let bindingEnergyHelium4: Double = 28.3
    static let bindingEnergyCarbon12: Double = 92.16
    static let bindingEnergyIron56: Double = 492.26
}

// MARK: - Cosmic Timeline (simulation ticks)

enum Epoch: Int, CaseIterable, Comparable, Identifiable {
    case planck           = 1
    case inflation        = 10
    case electroweak      = 100
    case quark            = 1000
    case hadron           = 5000
    case nucleosynthesis  = 10000
    case recombination    = 50000
    case starFormation    = 100000
    case solarSystem      = 200000
    case earth            = 210000
    case life             = 250000
    case dna              = 280000
    case present          = 300000

    var id: Int { rawValue }

    var tick: Int { rawValue }

    var displayName: String {
        switch self {
        case .planck:          return "Planck"
        case .inflation:       return "Inflation"
        case .electroweak:     return "Electroweak"
        case .quark:           return "Quark"
        case .hadron:          return "Hadron"
        case .nucleosynthesis: return "Nucleosynthesis"
        case .recombination:   return "Recombination"
        case .starFormation:   return "Star Formation"
        case .solarSystem:     return "Solar System"
        case .earth:           return "Earth"
        case .life:            return "Life"
        case .dna:             return "DNA Era"
        case .present:         return "Present"
        }
    }

    var description: String {
        switch self {
        case .planck:          return "All forces unified, T~10^32K"
        case .inflation:       return "Exponential expansion, quantum fluctuations seed structure"
        case .electroweak:     return "Electromagnetic and weak forces separate"
        case .quark:           return "Quark-gluon plasma, free quarks"
        case .hadron:          return "Quarks confined into protons and neutrons"
        case .nucleosynthesis: return "Light nuclei form: H, He, Li"
        case .recombination:   return "Atoms form, universe becomes transparent"
        case .starFormation:   return "First stars ignite, heavier elements forged"
        case .solarSystem:     return "Our solar system coalesces from stellar debris"
        case .earth:           return "Earth forms, oceans appear"
        case .life:            return "First self-replicating molecules"
        case .dna:             return "DNA-based life, epigenetics emerge"
        case .present:         return "Complex life, intelligence"
        }
    }

    /// Short icon for compact displays
    var icon: String {
        switch self {
        case .planck:          return "atom"
        case .inflation:       return "arrow.up.right.and.arrow.down.left.rectangle"
        case .electroweak:     return "bolt.fill"
        case .quark:           return "circle.grid.3x3.fill"
        case .hadron:          return "circle.hexagongrid.fill"
        case .nucleosynthesis: return "sun.min.fill"
        case .recombination:   return "sparkles"
        case .starFormation:   return "star.fill"
        case .solarSystem:     return "globe.americas.fill"
        case .earth:           return "globe.europe.africa.fill"
        case .life:            return "leaf.fill"
        case .dna:             return "allergens.fill"
        case .present:         return "brain.head.profile"
        }
    }

    static func < (lhs: Epoch, rhs: Epoch) -> Bool {
        lhs.rawValue < rhs.rawValue
    }

    /// Returns the current epoch for a given tick
    static func current(forTick tick: Int) -> Epoch {
        var result: Epoch = .planck
        for epoch in Epoch.allCases {
            if tick >= epoch.tick {
                result = epoch
            }
        }
        return result
    }
}

// MARK: - Temperature Scale (simulation Kelvin)

enum TemperatureScale {
    static let planck: Double = 1e10
    static let electroweak: Double = 1e8
    static let quarkHadron: Double = 1e6
    static let nucleosynthesis: Double = 1e4
    static let recombination: Double = 3000.0
    static let cmb: Double = 2.725
    static let stellarCore: Double = 1.5e4
    static let earthSurface: Double = 288.0
}

// MARK: - Chemistry Parameters

enum ChemistryParams {
    static let electronShells: [Int] = [2, 8, 18, 32, 32, 18, 8]
    static let bondEnergyCovalent: Double = 3.5
    static let bondEnergyIonic: Double = 5.0
    static let bondEnergyHydrogen: Double = 0.2
    static let bondEnergyVanDerWaals: Double = 0.01
}

// MARK: - Biology Parameters

enum BiologyParams {
    static let nucleotideBases: [Character] = ["A", "T", "G", "C"]
    static let rnaBases: [Character] = ["A", "U", "G", "C"]

    static let aminoAcids: [String] = [
        "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
        "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
        "Thr", "Trp", "Tyr", "Val",
    ]

    static let codonTable: [String: String] = [
        "AUG": "Met",
        "UUU": "Phe", "UUC": "Phe",
        "UUA": "Leu", "UUG": "Leu", "CUU": "Leu", "CUC": "Leu",
        "CUA": "Leu", "CUG": "Leu",
        "AUU": "Ile", "AUC": "Ile", "AUA": "Ile",
        "GUU": "Val", "GUC": "Val", "GUA": "Val", "GUG": "Val",
        "UCU": "Ser", "UCC": "Ser", "UCA": "Ser", "UCG": "Ser",
        "CCU": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro",
        "ACU": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr",
        "GCU": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala",
        "UAU": "Tyr", "UAC": "Tyr",
        "CAU": "His", "CAC": "His",
        "CAA": "Gln", "CAG": "Gln",
        "AAU": "Asn", "AAC": "Asn",
        "AAA": "Lys", "AAG": "Lys",
        "GAU": "Asp", "GAC": "Asp",
        "GAA": "Glu", "GAG": "Glu",
        "UGU": "Cys", "UGC": "Cys",
        "UGG": "Trp",
        "CGU": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg",
        "AGU": "Ser", "AGC": "Ser",
        "AGA": "Arg", "AGG": "Arg",
        "GGU": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly",
        "UAA": "STOP", "UAG": "STOP", "UGA": "STOP",
    ]
}

// MARK: - Epigenetic Parameters

enum EpigeneticParams {
    static let methylationProbability: Double = 0.03
    static let demethylationProbability: Double = 0.01
    static let histoneAcetylationProb: Double = 0.02
    static let histoneDeacetylationProb: Double = 0.015
    static let chromatinRemodelEnergy: Double = 1.5
}

// MARK: - Environmental Parameters

enum EnvironmentParams {
    static let uvMutationRate: Double = 1e-4
    static let cosmicRayMutationRate: Double = 1e-6
    static let thermalFluctuation: Double = 0.01
    static let radiationDamageThreshold: Double = 10.0
}

// MARK: - Simulation Limits

enum SimulationLimits {
    static let maxParticlesDefault: Int = 2000
    static let maxParticlesBattery: Int = 800
    static let maxParticlesLowPerf: Int = 500
    static let maxCells: Int = 100
    static let presentEpoch: Int = Epoch.present.tick
    static let frameTimeBudgetMs: Double = 20.0
}
