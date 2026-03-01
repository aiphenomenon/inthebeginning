// Constants.swift
// InTheBeginning – macOS Screensaver
//
// Physical constants and simulation parameters.
// All values in simulation units (SU), scaled for computational tractability.
// Real-world proportions maintained where possible.

import Foundation

// MARK: - Fundamental Constants (simulation-scaled)

let kSpeedOfLight: Double       = 1.0
let kHBar: Double               = 0.01
let kBoltzmann: Double          = 0.001
let kGravitational: Double      = 1e-6
let kFineStructure: Double      = 1.0 / 137.0
let kElementaryCharge: Double   = 0.1
let kPi: Double                 = Double.pi

// MARK: - Particle Masses (SU, proportional to real)

let kMassElectron: Double       = 1.0
let kMassUpQuark: Double        = 4.4
let kMassDownQuark: Double      = 9.4
let kMassProton: Double         = 1836.0
let kMassNeutron: Double        = 1839.0
let kMassPhoton: Double         = 0.0
let kMassNeutrino: Double       = 1e-6
let kMassWBoson: Double         = 157000.0
let kMassZBoson: Double         = 178000.0
let kMassHiggs: Double          = 245000.0

// MARK: - Force Coupling Strengths

let kStrongCoupling: Double     = 1.0
let kEMCoupling: Double         = kFineStructure
let kWeakCoupling: Double       = 1e-6
let kGravityCoupling: Double    = 1e-38

// MARK: - Nuclear Parameters

let kNuclearRadius: Double              = 0.01
let kBindingEnergyDeuterium: Double     = 2.22
let kBindingEnergyHelium4: Double       = 28.3
let kBindingEnergyCarbon12: Double      = 92.16
let kBindingEnergyIron56: Double        = 492.26

// MARK: - Cosmic Timeline (simulation ticks)

enum Epoch: Int, CaseIterable, Comparable {
    case planck            = 1
    case inflation         = 10
    case electroweak       = 100
    case quark             = 1000
    case hadron            = 5000
    case nucleosynthesis   = 10000
    case recombination     = 50000
    case starFormation     = 100000
    case solarSystem       = 200000
    case earth             = 210000
    case life              = 250000
    case dna               = 280000
    case present           = 300000

    static func < (lhs: Epoch, rhs: Epoch) -> Bool {
        lhs.rawValue < rhs.rawValue
    }

    var name: String {
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
        case .planck:          return "All forces unified, T~10^32 K"
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

    /// Determine the current epoch from a tick count.
    static func current(forTick tick: Int) -> Epoch {
        var result: Epoch = .planck
        for epoch in Epoch.allCases {
            if tick >= epoch.rawValue {
                result = epoch
            }
        }
        return result
    }
}

// MARK: - Temperature Scale (simulation Kelvin)

let kTempPlanck: Double         = 1e10
let kTempElectroweak: Double    = 1e8
let kTempQuarkHadron: Double    = 1e6
let kTempNucleosynthesis: Double = 1e4
let kTempRecombination: Double  = 3000.0
let kTempCMB: Double            = 2.725
let kTempStellarCore: Double    = 1.5e4
let kTempEarthSurface: Double   = 288.0

// MARK: - Chemistry Parameters

let kElectronShells: [Int]          = [2, 8, 18, 32, 32, 18, 8]
let kBondEnergyCovalent: Double     = 3.5
let kBondEnergyIonic: Double        = 5.0
let kBondEnergyHydrogen: Double     = 0.2
let kBondEnergyVanDerWaals: Double  = 0.01

// MARK: - Biology Parameters

let kNucleotideBases: [Character]   = ["A", "T", "G", "C"]
let kRNABases: [Character]          = ["A", "U", "G", "C"]

let kAminoAcids: [String] = [
    "Ala", "Arg", "Asn", "Asp", "Cys", "Gln", "Glu", "Gly",
    "His", "Ile", "Leu", "Lys", "Met", "Phe", "Pro", "Ser",
    "Thr", "Trp", "Tyr", "Val",
]

/// Codon -> amino acid lookup. "STOP" marks a stop codon.
let kCodonTable: [String: String] = [
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

// MARK: - Epigenetic Parameters

let kMethylationProbability: Double         = 0.03
let kDemethylationProbability: Double       = 0.01
let kHistoneAcetylationProb: Double         = 0.02
let kHistoneDeacetylationProb: Double       = 0.015
let kChromatinRemodelEnergy: Double         = 1.5

// MARK: - Environmental Parameters

let kUVMutationRate: Double                 = 1e-4
let kCosmicRayMutationRate: Double          = 1e-6
let kThermalFluctuation: Double             = 0.01
let kRadiationDamageThreshold: Double       = 10.0

// MARK: - Rendering Constants

/// The simulation runs faster than real cosmic time. This controls how many
/// simulation ticks advance per screen frame at 30 fps.
let kTicksPerFrame: Int = 100

/// Maximum number of renderable entities to avoid GPU overload.
let kMaxRenderableParticles: Int = 512
let kMaxRenderableAtoms: Int     = 256
let kMaxRenderableCells: Int     = 128

/// World-space bounds for the simulation viewport.
let kWorldRadius: Float = 40.0
