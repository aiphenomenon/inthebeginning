// ChemicalSystem.swift
// InTheBeginning
//
// Chemical system simulation.
// Models molecules, chemical reactions, water formation, and amino acid synthesis.
// Builds on the AtomicSystem by assembling atoms into molecular structures
// that become the precursors to life.

import Foundation

// MARK: - Bond

struct Bond: Identifiable {
    static let idGenerator = IDGenerator()

    let id: Int
    let atomA: Int  // Atom ID
    let atomB: Int  // Atom ID
    let type: BondType
    let energy: Double

    init(atomA: Int, atomB: Int, type: BondType, energy: Double) {
        self.id = Bond.idGenerator.next()
        self.atomA = atomA
        self.atomB = atomB
        self.type = type
        self.energy = energy
    }
}

enum BondType: String, CaseIterable, Sendable {
    case covalent = "covalent"
    case ionic = "ionic"
    case polarCovalent = "polar_covalent"
    case hydrogen = "hydrogen"
    case vanDerWaals = "van_der_waals"

    var strength: Double {
        switch self {
        case .covalent:      return ChemistryParams.bondEnergyCovalent
        case .ionic:         return ChemistryParams.bondEnergyIonic
        case .polarCovalent: return (ChemistryParams.bondEnergyCovalent + ChemistryParams.bondEnergyIonic) / 2.0
        case .hydrogen:      return ChemistryParams.bondEnergyHydrogen
        case .vanDerWaals:   return ChemistryParams.bondEnergyVanDerWaals
        }
    }
}

// MARK: - Molecule

final class Molecule: Identifiable {
    static let idGenerator = IDGenerator()

    let id: Int
    var atomIDs: [Int]
    var formula: String
    var moleculeType: MoleculeType
    var bonds: [Bond]
    var position: SIMD3<Double>
    var velocity: SIMD3<Double>
    var energy: Double
    var isStable: Bool

    var displayColor: SIMD4<Float> {
        moleculeType.displayColor
    }

    init(
        atomIDs: [Int],
        formula: String,
        moleculeType: MoleculeType,
        bonds: [Bond] = [],
        position: SIMD3<Double> = .zero,
        velocity: SIMD3<Double> = .zero,
        energy: Double = 0.0,
        isStable: Bool = true
    ) {
        self.id = Molecule.idGenerator.next()
        self.atomIDs = atomIDs
        self.formula = formula
        self.moleculeType = moleculeType
        self.bonds = bonds
        self.position = position
        self.velocity = velocity
        self.energy = energy
        self.isStable = isStable
    }

    var bondEnergy: Double {
        bonds.reduce(0.0) { $0 + $1.energy }
    }
}

// MARK: - Molecule Type

enum MoleculeType: String, CaseIterable, Sendable {
    case water = "H2O"
    case carbonDioxide = "CO2"
    case methane = "CH4"
    case ammonia = "NH3"
    case hydrogenCyanide = "HCN"
    case formaldehyde = "CH2O"
    case aminoAcid = "amino_acid"
    case nucleotide = "nucleotide"
    case phospholipid = "phospholipid"
    case genericOrganic = "organic"
    case genericInorganic = "inorganic"

    var displayName: String {
        switch self {
        case .water:            return "Water"
        case .carbonDioxide:    return "Carbon Dioxide"
        case .methane:          return "Methane"
        case .ammonia:          return "Ammonia"
        case .hydrogenCyanide:  return "Hydrogen Cyanide"
        case .formaldehyde:     return "Formaldehyde"
        case .aminoAcid:        return "Amino Acid"
        case .nucleotide:       return "Nucleotide"
        case .phospholipid:     return "Phospholipid"
        case .genericOrganic:   return "Organic Molecule"
        case .genericInorganic: return "Inorganic Molecule"
        }
    }

    var displayColor: SIMD4<Float> {
        switch self {
        case .water:            return SIMD4<Float>(0.3, 0.5, 1.0, 0.8)
        case .carbonDioxide:    return SIMD4<Float>(0.5, 0.5, 0.5, 0.7)
        case .methane:          return SIMD4<Float>(0.6, 0.8, 0.4, 0.8)
        case .ammonia:          return SIMD4<Float>(0.4, 0.4, 0.9, 0.8)
        case .hydrogenCyanide:  return SIMD4<Float>(0.8, 0.3, 0.5, 0.8)
        case .formaldehyde:     return SIMD4<Float>(0.7, 0.6, 0.3, 0.8)
        case .aminoAcid:        return SIMD4<Float>(0.2, 1.0, 0.4, 1.0)
        case .nucleotide:       return SIMD4<Float>(1.0, 0.7, 0.2, 1.0)
        case .phospholipid:     return SIMD4<Float>(0.8, 0.6, 0.9, 1.0)
        case .genericOrganic:   return SIMD4<Float>(0.5, 0.8, 0.3, 0.8)
        case .genericInorganic: return SIMD4<Float>(0.6, 0.6, 0.6, 0.7)
        }
    }

    /// Whether this molecule is considered organic (carbon-based)
    var isOrganic: Bool {
        switch self {
        case .methane, .hydrogenCyanide, .formaldehyde,
             .aminoAcid, .nucleotide, .phospholipid, .genericOrganic:
            return true
        default:
            return false
        }
    }
}

// MARK: - Chemical System

final class ChemicalSystem {
    var molecules: [Molecule] = []
    var temperature: Double
    var pH: Double = 7.0
    var catalystPresent: Bool = false
    var totalReactions: Int = 0

    init(temperature: Double = TemperatureScale.earthSurface) {
        self.temperature = temperature
    }

    // MARK: - Water Formation

    /// Combine hydrogen and oxygen atoms into water molecules.
    /// 2H + O -> H2O
    func formWater(atomicSystem: AtomicSystem) -> [Molecule] {
        var newMolecules: [Molecule] = []
        var hydrogens = atomicSystem.atoms.filter { $0.atomicNumber == 1 && $0.bondIDs.isEmpty }
        var oxygens = atomicSystem.atoms.filter { $0.atomicNumber == 8 && $0.bondIDs.isEmpty }

        while hydrogens.count >= 2 && !oxygens.isEmpty {
            let h1 = hydrogens.removeLast()
            let h2 = hydrogens.removeLast()
            let o = oxygens.removeLast()

            let bondOH1 = Bond(
                atomA: o.id, atomB: h1.id,
                type: .polarCovalent,
                energy: ChemistryParams.bondEnergyCovalent
            )
            let bondOH2 = Bond(
                atomA: o.id, atomB: h2.id,
                type: .polarCovalent,
                energy: ChemistryParams.bondEnergyCovalent
            )

            // Mark atoms as bonded
            atomicSystem.attemptBond(o, h1)
            atomicSystem.attemptBond(o, h2)

            let water = Molecule(
                atomIDs: [h1.id, h2.id, o.id],
                formula: "H2O",
                moleculeType: .water,
                bonds: [bondOH1, bondOH2],
                position: o.position,
                velocity: (h1.velocity + h2.velocity + o.velocity) / 3.0,
                energy: bondOH1.energy + bondOH2.energy,
                isStable: true
            )
            newMolecules.append(water)
            molecules.append(water)
            totalReactions += 1
        }

        return newMolecules
    }

    // MARK: - Simple Molecule Formation

    /// Form simple molecules from available atoms.
    func formSimpleMolecules(atomicSystem: AtomicSystem) -> [Molecule] {
        var newMolecules: [Molecule] = []

        // Methane: C + 4H -> CH4
        var carbons = atomicSystem.atoms.filter { $0.atomicNumber == 6 && $0.bondIDs.isEmpty }
        var hydrogens = atomicSystem.atoms.filter { $0.atomicNumber == 1 && $0.bondIDs.isEmpty }

        while !carbons.isEmpty && hydrogens.count >= 4 {
            let c = carbons.removeLast()
            var hAtoms: [Atom] = []
            for _ in 0..<4 {
                hAtoms.append(hydrogens.removeLast())
            }

            var bonds: [Bond] = []
            for h in hAtoms {
                bonds.append(Bond(
                    atomA: c.id, atomB: h.id,
                    type: .covalent,
                    energy: ChemistryParams.bondEnergyCovalent
                ))
                atomicSystem.attemptBond(c, h)
            }

            let methane = Molecule(
                atomIDs: [c.id] + hAtoms.map(\.id),
                formula: "CH4",
                moleculeType: .methane,
                bonds: bonds,
                position: c.position,
                energy: bonds.reduce(0.0) { $0 + $1.energy }
            )
            newMolecules.append(methane)
            molecules.append(methane)
            totalReactions += 1
        }

        // Ammonia: N + 3H -> NH3
        var nitrogens = atomicSystem.atoms.filter { $0.atomicNumber == 7 && $0.bondIDs.isEmpty }
        hydrogens = atomicSystem.atoms.filter { $0.atomicNumber == 1 && $0.bondIDs.isEmpty }

        while !nitrogens.isEmpty && hydrogens.count >= 3 {
            let n = nitrogens.removeLast()
            var hAtoms: [Atom] = []
            for _ in 0..<3 {
                hAtoms.append(hydrogens.removeLast())
            }

            var bonds: [Bond] = []
            for h in hAtoms {
                bonds.append(Bond(
                    atomA: n.id, atomB: h.id,
                    type: .covalent,
                    energy: ChemistryParams.bondEnergyCovalent
                ))
                atomicSystem.attemptBond(n, h)
            }

            let ammonia = Molecule(
                atomIDs: [n.id] + hAtoms.map(\.id),
                formula: "NH3",
                moleculeType: .ammonia,
                bonds: bonds,
                position: n.position,
                energy: bonds.reduce(0.0) { $0 + $1.energy }
            )
            newMolecules.append(ammonia)
            molecules.append(ammonia)
            totalReactions += 1
        }

        // CO2: C + 2O -> CO2
        carbons = atomicSystem.atoms.filter { $0.atomicNumber == 6 && $0.bondIDs.isEmpty }
        var oxygens = atomicSystem.atoms.filter { $0.atomicNumber == 8 && $0.bondIDs.isEmpty }

        while !carbons.isEmpty && oxygens.count >= 2 {
            let c = carbons.removeLast()
            let o1 = oxygens.removeLast()
            let o2 = oxygens.removeLast()

            let bond1 = Bond(atomA: c.id, atomB: o1.id, type: .covalent, energy: ChemistryParams.bondEnergyCovalent * 2)
            let bond2 = Bond(atomA: c.id, atomB: o2.id, type: .covalent, energy: ChemistryParams.bondEnergyCovalent * 2)
            atomicSystem.attemptBond(c, o1)
            atomicSystem.attemptBond(c, o2)

            let co2 = Molecule(
                atomIDs: [c.id, o1.id, o2.id],
                formula: "CO2",
                moleculeType: .carbonDioxide,
                bonds: [bond1, bond2],
                position: c.position,
                energy: bond1.energy + bond2.energy
            )
            newMolecules.append(co2)
            molecules.append(co2)
            totalReactions += 1
        }

        return newMolecules
    }

    // MARK: - Amino Acid Synthesis

    /// Synthesize amino acids from precursor molecules under specific conditions.
    /// Requires: CH4, NH3, H2O, and energy (temperature/UV/lightning).
    func synthesizeAminoAcids(energyInput: Double) -> [Molecule] {
        var newMolecules: [Molecule] = []

        let methanes = molecules.filter { $0.moleculeType == .methane }
        let ammonias = molecules.filter { $0.moleculeType == .ammonia }
        let waters = molecules.filter { $0.moleculeType == .water }

        guard !methanes.isEmpty && !ammonias.isEmpty && !waters.isEmpty else {
            return newMolecules
        }

        // Miller-Urey-like synthesis probability
        let reactionProbability = min(0.05, energyInput / 1000.0)
        let catalystBoost = catalystPresent ? 5.0 : 1.0

        guard Double.random(in: 0...1) < reactionProbability * catalystBoost else {
            return newMolecules
        }

        // Consume precursors
        if let methane = methanes.first,
           let ammonia = ammonias.first,
           let water = waters.first {
            molecules.removeAll { $0.id == methane.id }
            molecules.removeAll { $0.id == ammonia.id }
            molecules.removeAll { $0.id == water.id }

            let aminoAcidName = BiologyParams.aminoAcids.randomElement() ?? "Gly"

            let aminoAcid = Molecule(
                atomIDs: methane.atomIDs + ammonia.atomIDs + water.atomIDs,
                formula: aminoAcidName,
                moleculeType: .aminoAcid,
                position: methane.position,
                velocity: methane.velocity,
                energy: methane.bondEnergy + ammonia.bondEnergy + energyInput * 0.1,
                isStable: temperature < 400.0
            )
            newMolecules.append(aminoAcid)
            molecules.append(aminoAcid)
            totalReactions += 1
        }

        return newMolecules
    }

    // MARK: - Nucleotide Synthesis

    /// Synthesize nucleotide precursors from organic molecules.
    func synthesizeNucleotides(energyInput: Double) -> [Molecule] {
        var newMolecules: [Molecule] = []

        let organics = molecules.filter { $0.moleculeType.isOrganic }
        let waters = molecules.filter { $0.moleculeType == .water }

        guard organics.count >= 2 && !waters.isEmpty else {
            return newMolecules
        }

        let prob = min(0.02, energyInput / 5000.0)
        let catalystBoost = catalystPresent ? 10.0 : 1.0

        guard Double.random(in: 0...1) < prob * catalystBoost else {
            return newMolecules
        }

        let o1 = organics[0]
        let o2 = organics[1]
        molecules.removeAll { $0.id == o1.id }
        molecules.removeAll { $0.id == o2.id }

        let nucleotide = Molecule(
            atomIDs: o1.atomIDs + o2.atomIDs,
            formula: "nucleotide",
            moleculeType: .nucleotide,
            position: o1.position,
            velocity: (o1.velocity + o2.velocity) / 2.0,
            energy: o1.bondEnergy + o2.bondEnergy + energyInput * 0.05,
            isStable: temperature < 350.0
        )
        newMolecules.append(nucleotide)
        molecules.append(nucleotide)
        totalReactions += 1

        return newMolecules
    }

    // MARK: - Phospholipid Synthesis

    /// Create phospholipid molecules for cell membrane formation.
    func synthesizePhospholipids() -> [Molecule] {
        var newMolecules: [Molecule] = []

        let organics = molecules.filter { $0.moleculeType == .aminoAcid || $0.moleculeType == .genericOrganic }
        let waters = molecules.filter { $0.moleculeType == .water }

        guard organics.count >= 2 && !waters.isEmpty else {
            return newMolecules
        }

        let prob = catalystPresent ? 0.02 : 0.002
        guard Double.random(in: 0...1) < prob else {
            return newMolecules
        }

        let o1 = organics[0]
        let o2 = organics[1]
        molecules.removeAll { $0.id == o1.id }
        molecules.removeAll { $0.id == o2.id }

        let phospholipid = Molecule(
            atomIDs: o1.atomIDs + o2.atomIDs,
            formula: "phospholipid",
            moleculeType: .phospholipid,
            position: o1.position,
            energy: o1.bondEnergy + o2.bondEnergy,
            isStable: true
        )
        newMolecules.append(phospholipid)
        molecules.append(phospholipid)
        totalReactions += 1

        return newMolecules
    }

    // MARK: - Thermal Decomposition

    /// Break down unstable molecules at high temperatures.
    func thermalDecomposition() -> Int {
        var decomposed = 0
        let threshold = 500.0

        guard temperature > threshold else { return 0 }

        molecules.removeAll { molecule in
            if !molecule.isStable || temperature > threshold * 2.0 {
                let prob = (temperature - threshold) / (threshold * 10.0)
                if Double.random(in: 0...1) < prob {
                    decomposed += 1
                    return true
                }
            }
            return false
        }

        return decomposed
    }

    // MARK: - Evolve

    /// Evolve molecular positions and energies.
    func evolve(dt: Double = 1.0) {
        for molecule in molecules {
            molecule.position += molecule.velocity * dt

            // Brownian motion proportional to temperature
            let brownian = SIMD3<Double>(
                Double.random(in: -1...1),
                Double.random(in: -1...1),
                Double.random(in: -1...1)
            )
            let thermalScale = sqrt(PhysicsConstants.kB * temperature) * 0.01
            molecule.velocity += brownian * thermalScale

            // Stability check
            molecule.isStable = temperature < 500.0 || molecule.bondEnergy > temperature * PhysicsConstants.kB
        }
    }

    // MARK: - Statistics

    func moleculeCounts() -> [String: Int] {
        var counts: [String: Int] = [:]
        for molecule in molecules {
            counts[molecule.moleculeType.rawValue, default: 0] += 1
        }
        return counts
    }

    var waterCount: Int {
        molecules.filter { $0.moleculeType == .water }.count
    }

    var aminoAcidCount: Int {
        molecules.filter { $0.moleculeType == .aminoAcid }.count
    }

    var nucleotideCount: Int {
        molecules.filter { $0.moleculeType == .nucleotide }.count
    }

    var organicCount: Int {
        molecules.filter { $0.moleculeType.isOrganic }.count
    }
}
