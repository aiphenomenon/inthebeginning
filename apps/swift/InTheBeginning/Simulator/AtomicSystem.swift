// AtomicSystem.swift
// InTheBeginning
//
// Atomic physics simulation.
// Models atoms with electron shells, ionization, chemical bonding potential,
// and the periodic table. Atoms emerge from the quantum/nuclear level
// when temperature drops below recombination threshold.

import Foundation

// MARK: - Periodic Table Data

struct ElementData {
    let symbol: String
    let name: String
    let group: Int
    let period: Int
    let electronegativity: Double
}

enum PeriodicTable {
    static let elements: [Int: ElementData] = [
        1:  ElementData(symbol: "H",  name: "Hydrogen",   group: 1,  period: 1, electronegativity: 2.20),
        2:  ElementData(symbol: "He", name: "Helium",     group: 18, period: 1, electronegativity: 0.0),
        3:  ElementData(symbol: "Li", name: "Lithium",    group: 1,  period: 2, electronegativity: 0.98),
        4:  ElementData(symbol: "Be", name: "Beryllium",  group: 2,  period: 2, electronegativity: 1.57),
        5:  ElementData(symbol: "B",  name: "Boron",      group: 13, period: 2, electronegativity: 2.04),
        6:  ElementData(symbol: "C",  name: "Carbon",     group: 14, period: 2, electronegativity: 2.55),
        7:  ElementData(symbol: "N",  name: "Nitrogen",   group: 15, period: 2, electronegativity: 3.04),
        8:  ElementData(symbol: "O",  name: "Oxygen",     group: 16, period: 2, electronegativity: 3.44),
        9:  ElementData(symbol: "F",  name: "Fluorine",   group: 17, period: 2, electronegativity: 3.98),
        10: ElementData(symbol: "Ne", name: "Neon",       group: 18, period: 2, electronegativity: 0.0),
        11: ElementData(symbol: "Na", name: "Sodium",     group: 1,  period: 3, electronegativity: 0.93),
        12: ElementData(symbol: "Mg", name: "Magnesium",  group: 2,  period: 3, electronegativity: 1.31),
        13: ElementData(symbol: "Al", name: "Aluminum",   group: 13, period: 3, electronegativity: 1.61),
        14: ElementData(symbol: "Si", name: "Silicon",    group: 14, period: 3, electronegativity: 1.90),
        15: ElementData(symbol: "P",  name: "Phosphorus", group: 15, period: 3, electronegativity: 2.19),
        16: ElementData(symbol: "S",  name: "Sulfur",     group: 16, period: 3, electronegativity: 2.58),
        17: ElementData(symbol: "Cl", name: "Chlorine",   group: 17, period: 3, electronegativity: 3.16),
        18: ElementData(symbol: "Ar", name: "Argon",      group: 18, period: 3, electronegativity: 0.0),
        19: ElementData(symbol: "K",  name: "Potassium",  group: 1,  period: 4, electronegativity: 0.82),
        20: ElementData(symbol: "Ca", name: "Calcium",    group: 2,  period: 4, electronegativity: 1.00),
        26: ElementData(symbol: "Fe", name: "Iron",       group: 8,  period: 4, electronegativity: 1.83),
    ]
}

// MARK: - Electron Shell

struct ElectronShell {
    let n: Int             // Principal quantum number
    let maxElectrons: Int  // 2n^2
    var electrons: Int = 0

    var isFull: Bool { electrons >= maxElectrons }
    var isEmpty: Bool { electrons == 0 }

    mutating func addElectron() -> Bool {
        guard !isFull else { return false }
        electrons += 1
        return true
    }

    mutating func removeElectron() -> Bool {
        guard !isEmpty else { return false }
        electrons -= 1
        return true
    }
}

// MARK: - Atom

final class Atom: Identifiable {
    static let idGenerator = IDGenerator()

    let id: Int
    let atomicNumber: Int
    var massNumber: Int
    var electronCount: Int
    var position: SIMD3<Double>
    var velocity: SIMD3<Double>
    var shells: [ElectronShell] = []
    var bondIDs: [Int] = []
    var ionizationEnergy: Double = 0.0

    var symbol: String {
        PeriodicTable.elements[atomicNumber]?.symbol ?? "E\(atomicNumber)"
    }

    var name: String {
        PeriodicTable.elements[atomicNumber]?.name ?? "Element-\(atomicNumber)"
    }

    var electronegativity: Double {
        PeriodicTable.elements[atomicNumber]?.electronegativity ?? 1.0
    }

    var charge: Int { atomicNumber - electronCount }

    var valenceElectrons: Int {
        shells.last?.electrons ?? 0
    }

    var neededElectrons: Int {
        guard let last = shells.last else { return 0 }
        return last.maxElectrons - last.electrons
    }

    var isNobleGas: Bool {
        shells.last?.isFull ?? false
    }

    var isIon: Bool { charge != 0 }

    /// Color for rendering
    var displayColor: SIMD4<Float> {
        switch atomicNumber {
        case 1:  return SIMD4<Float>(1.0, 1.0, 1.0, 1.0)   // White
        case 2:  return SIMD4<Float>(0.9, 0.9, 0.5, 1.0)   // Yellow-white
        case 6:  return SIMD4<Float>(0.3, 0.3, 0.3, 1.0)   // Dark gray
        case 7:  return SIMD4<Float>(0.2, 0.3, 1.0, 1.0)   // Blue
        case 8:  return SIMD4<Float>(1.0, 0.2, 0.2, 1.0)   // Red
        case 15: return SIMD4<Float>(1.0, 0.5, 0.0, 1.0)   // Orange
        case 26: return SIMD4<Float>(0.7, 0.5, 0.2, 1.0)   // Bronze
        default: return SIMD4<Float>(0.6, 0.6, 0.6, 1.0)   // Gray
        }
    }

    init(
        atomicNumber: Int,
        massNumber: Int = 0,
        electronCount: Int = 0,
        position: SIMD3<Double> = .zero,
        velocity: SIMD3<Double> = .zero
    ) {
        self.id = Atom.idGenerator.next()
        self.atomicNumber = atomicNumber
        self.massNumber = massNumber == 0 ? (atomicNumber == 1 ? 1 : atomicNumber * 2) : massNumber
        self.electronCount = electronCount == 0 ? atomicNumber : electronCount
        self.position = position
        self.velocity = velocity

        buildShells()
        computeIonizationEnergy()
    }

    // MARK: - Shell Construction

    func buildShells() {
        shells.removeAll()
        var remaining = electronCount
        for (i, maxE) in ChemistryParams.electronShells.enumerated() {
            guard remaining > 0 else { break }
            let count = min(remaining, maxE)
            shells.append(ElectronShell(n: i + 1, maxElectrons: maxE, electrons: count))
            remaining -= count
        }
    }

    func computeIonizationEnergy() {
        guard let lastShell = shells.last, !lastShell.isEmpty else {
            ionizationEnergy = 0.0
            return
        }
        let n = Double(lastShell.n)
        let innerElectrons = shells.dropLast().reduce(0) { $0 + $1.electrons }
        let zEff = Double(atomicNumber - innerElectrons)
        ionizationEnergy = 13.6 * zEff * zEff / (n * n)
    }

    // MARK: - Ionization

    @discardableResult
    func ionize() -> Bool {
        guard electronCount > 0 else { return false }
        electronCount -= 1
        buildShells()
        computeIonizationEnergy()
        return true
    }

    @discardableResult
    func captureElectron() -> Bool {
        electronCount += 1
        buildShells()
        computeIonizationEnergy()
        return true
    }

    // MARK: - Bonding

    func canBond(with other: Atom) -> Bool {
        guard !isNobleGas && !other.isNobleGas else { return false }
        guard bondIDs.count < 4 && other.bondIDs.count < 4 else { return false }
        return true
    }

    func bondType(with other: Atom) -> String {
        let diff = abs(electronegativity - other.electronegativity)
        if diff > 1.7 { return "ionic" }
        if diff > 0.4 { return "polar_covalent" }
        return "covalent"
    }

    func bondEnergy(with other: Atom) -> Double {
        switch bondType(with: other) {
        case "ionic":          return ChemistryParams.bondEnergyIonic
        case "polar_covalent": return (ChemistryParams.bondEnergyCovalent + ChemistryParams.bondEnergyIonic) / 2.0
        default:               return ChemistryParams.bondEnergyCovalent
        }
    }

    func distance(to other: Atom) -> Double {
        simd_length(position - other.position)
    }
}

// MARK: - Atomic System

final class AtomicSystem {
    var atoms: [Atom] = []
    var temperature: Double
    var freeElectrons: [Particle] = []
    var bondsFormed: Int = 0
    var bondsBroken: Int = 0

    init(temperature: Double = TemperatureScale.recombination) {
        self.temperature = temperature
    }

    // MARK: - Recombination

    /// Capture free electrons into ions when T < T_recombination.
    func recombination(field: QuantumField) -> [Atom] {
        guard temperature <= TemperatureScale.recombination else { return [] }

        var newAtoms: [Atom] = []
        var protons = field.particles.filter { $0.particleType == .proton }
        var electrons = field.particles.filter { $0.particleType == .electron }

        for proton in protons {
            guard !electrons.isEmpty else { break }
            let electron = electrons.removeLast()

            let atom = Atom(
                atomicNumber: 1,
                massNumber: 1,
                position: proton.position,
                velocity: proton.momentum
            )
            newAtoms.append(atom)
            atoms.append(atom)

            field.particles.removeAll { $0.id == proton.id }
            field.particles.removeAll { $0.id == electron.id }
        }

        return newAtoms
    }

    // MARK: - Nucleosynthesis

    /// Form heavier elements through nuclear fusion.
    func nucleosynthesis(protons: Int, neutrons: Int) -> [Atom] {
        var newAtoms: [Atom] = []
        var p = protons
        var n = neutrons

        // Helium-4: 2 protons + 2 neutrons
        while p >= 2 && n >= 2 {
            let he = Atom(
                atomicNumber: 2,
                massNumber: 4,
                position: SIMD3<Double>.randomGaussian(sigma: 10.0)
            )
            newAtoms.append(he)
            atoms.append(he)
            p -= 2
            n -= 2
        }

        // Remaining protons become hydrogen
        for _ in 0..<p {
            let h = Atom(
                atomicNumber: 1,
                massNumber: 1,
                position: SIMD3<Double>.randomGaussian(sigma: 10.0)
            )
            newAtoms.append(h)
            atoms.append(h)
        }

        return newAtoms
    }

    // MARK: - Stellar Nucleosynthesis

    /// Form heavier elements in stellar cores.
    func stellarNucleosynthesis(temperature: Double) -> [Atom] {
        var newAtoms: [Atom] = []
        guard temperature >= 1e3 else { return newAtoms }

        // Triple-alpha process: 3 He -> C
        var heliums = atoms.filter { $0.atomicNumber == 2 }
        while heliums.count >= 3 && Double.random(in: 0...1) < 0.01 {
            for _ in 0..<3 {
                let he = heliums.removeLast()
                atoms.removeAll { $0.id == he.id }
            }
            let carbon = Atom(
                atomicNumber: 6,
                massNumber: 12,
                position: SIMD3<Double>.randomGaussian(sigma: 5.0)
            )
            newAtoms.append(carbon)
            atoms.append(carbon)
        }

        // C + He -> O
        var carbons = atoms.filter { $0.atomicNumber == 6 }
        heliums = atoms.filter { $0.atomicNumber == 2 }
        while !carbons.isEmpty && !heliums.isEmpty && Double.random(in: 0...1) < 0.02 {
            let c = carbons.removeLast()
            let he = heliums.removeLast()
            atoms.removeAll { $0.id == c.id || $0.id == he.id }
            let oxygen = Atom(
                atomicNumber: 8,
                massNumber: 16,
                position: c.position
            )
            newAtoms.append(oxygen)
            atoms.append(oxygen)
        }

        // O + He -> N (simplified chain)
        let oxygens = atoms.filter { $0.atomicNumber == 8 }
        heliums = atoms.filter { $0.atomicNumber == 2 }
        if !oxygens.isEmpty && !heliums.isEmpty && Double.random(in: 0...1) < 0.005 {
            let o = oxygens[0]
            let he = heliums[0]
            atoms.removeAll { $0.id == o.id || $0.id == he.id }
            let nitrogen = Atom(
                atomicNumber: 7,
                massNumber: 14,
                position: o.position
            )
            newAtoms.append(nitrogen)
            atoms.append(nitrogen)
        }

        return newAtoms
    }

    // MARK: - Bonding

    @discardableResult
    func attemptBond(_ a1: Atom, _ a2: Atom) -> Bool {
        guard a1.canBond(with: a2) else { return false }
        let dist = a1.distance(to: a2)
        let bondDist = 2.0
        guard dist < bondDist * 3 else { return false }

        let energyBarrier = a1.bondEnergy(with: a2)
        let thermalEnergy = PhysicsConstants.kB * temperature

        let prob: Double
        if thermalEnergy > 0 {
            prob = exp(-energyBarrier / thermalEnergy)
        } else {
            prob = dist < bondDist ? 1.0 : 0.0
        }

        guard Double.random(in: 0...1) < prob else { return false }

        a1.bondIDs.append(a2.id)
        a2.bondIDs.append(a1.id)
        bondsFormed += 1
        return true
    }

    @discardableResult
    func breakBond(_ a1: Atom, _ a2: Atom) -> Bool {
        guard a1.bondIDs.contains(a2.id) else { return false }

        let energyBarrier = a1.bondEnergy(with: a2)
        let thermalEnergy = PhysicsConstants.kB * temperature

        guard thermalEnergy > energyBarrier * 0.5 else { return false }

        let prob = exp(-energyBarrier / (thermalEnergy + 1e-20))
        guard Double.random(in: 0...1) < prob else { return false }

        a1.bondIDs.removeAll { $0 == a2.id }
        a2.bondIDs.removeAll { $0 == a1.id }
        bondsBroken += 1
        return true
    }

    // MARK: - Statistics

    func elementCounts() -> [String: Int] {
        var counts: [String: Int] = [:]
        for atom in atoms {
            counts[atom.symbol, default: 0] += 1
        }
        return counts
    }
}

// MARK: - SIMD3 Helpers

extension SIMD3 where Scalar == Double {
    static func randomGaussian(sigma: Double) -> SIMD3<Double> {
        SIMD3<Double>(
            gaussRandom() * sigma,
            gaussRandom() * sigma,
            gaussRandom() * sigma
        )
    }

    private static func gaussRandom() -> Double {
        // Box-Muller transform
        let u1 = Double.random(in: 0.001...1.0)
        let u2 = Double.random(in: 0.0...1.0)
        return sqrt(-2.0 * log(u1)) * cos(2.0 * .pi * u2)
    }
}
