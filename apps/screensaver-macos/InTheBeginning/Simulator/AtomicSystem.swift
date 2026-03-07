// AtomicSystem.swift
// InTheBeginning – macOS Screensaver
//
// Atomic physics simulation.
// Models atoms with electron shells, ionization, chemical bonding,
// and the periodic table. Atoms emerge from the quantum/nuclear level
// when temperature drops below recombination threshold.

import Foundation

// MARK: - Periodic Table

struct ElementInfo {
    let symbol: String
    let name: String
    let group: Int
    let period: Int
    let electronegativity: Double
}

let kElements: [Int: ElementInfo] = [
    1:  ElementInfo(symbol: "H",  name: "Hydrogen",   group: 1,  period: 1, electronegativity: 2.20),
    2:  ElementInfo(symbol: "He", name: "Helium",     group: 18, period: 1, electronegativity: 0.0),
    3:  ElementInfo(symbol: "Li", name: "Lithium",    group: 1,  period: 2, electronegativity: 0.98),
    4:  ElementInfo(symbol: "Be", name: "Beryllium",  group: 2,  period: 2, electronegativity: 1.57),
    5:  ElementInfo(symbol: "B",  name: "Boron",      group: 13, period: 2, electronegativity: 2.04),
    6:  ElementInfo(symbol: "C",  name: "Carbon",     group: 14, period: 2, electronegativity: 2.55),
    7:  ElementInfo(symbol: "N",  name: "Nitrogen",   group: 15, period: 2, electronegativity: 3.04),
    8:  ElementInfo(symbol: "O",  name: "Oxygen",     group: 16, period: 2, electronegativity: 3.44),
    9:  ElementInfo(symbol: "F",  name: "Fluorine",   group: 17, period: 2, electronegativity: 3.98),
    10: ElementInfo(symbol: "Ne", name: "Neon",       group: 18, period: 2, electronegativity: 0.0),
    11: ElementInfo(symbol: "Na", name: "Sodium",     group: 1,  period: 3, electronegativity: 0.93),
    12: ElementInfo(symbol: "Mg", name: "Magnesium",  group: 2,  period: 3, electronegativity: 1.31),
    13: ElementInfo(symbol: "Al", name: "Aluminum",   group: 13, period: 3, electronegativity: 1.61),
    14: ElementInfo(symbol: "Si", name: "Silicon",    group: 14, period: 3, electronegativity: 1.90),
    15: ElementInfo(symbol: "P",  name: "Phosphorus", group: 15, period: 3, electronegativity: 2.19),
    16: ElementInfo(symbol: "S",  name: "Sulfur",     group: 16, period: 3, electronegativity: 2.58),
    17: ElementInfo(symbol: "Cl", name: "Chlorine",   group: 17, period: 3, electronegativity: 3.16),
    18: ElementInfo(symbol: "Ar", name: "Argon",      group: 18, period: 3, electronegativity: 0.0),
    19: ElementInfo(symbol: "K",  name: "Potassium",  group: 1,  period: 4, electronegativity: 0.82),
    20: ElementInfo(symbol: "Ca", name: "Calcium",    group: 2,  period: 4, electronegativity: 1.00),
    26: ElementInfo(symbol: "Fe", name: "Iron",       group: 8,  period: 4, electronegativity: 1.83),
]

// MARK: - Electron Shell

struct ElectronShell {
    let n: Int              // Principal quantum number
    let maxElectrons: Int   // 2n^2
    var electrons: Int = 0

    var isFull: Bool  { electrons >= maxElectrons }
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

private var _atomIDCounter: Int = 0

final class Atom {
    let atomID: Int
    var atomicNumber: Int
    var massNumber: Int
    var electronCount: Int
    var position: SIMD3<Double>
    var velocity: SIMD3<Double>
    var shells: [ElectronShell] = []
    var bonds: [Int] = []   // IDs of bonded atoms
    var ionizationEnergy: Double = 0.0

    var symbol: String {
        kElements[atomicNumber]?.symbol ?? "E\(atomicNumber)"
    }

    var name: String {
        kElements[atomicNumber]?.name ?? "Element-\(atomicNumber)"
    }

    var electronegativity: Double {
        kElements[atomicNumber]?.electronegativity ?? 1.0
    }

    var charge: Int { atomicNumber - electronCount }

    var valenceElectrons: Int {
        shells.last?.electrons ?? 0
    }

    var needsElectrons: Int {
        guard let last = shells.last else { return 0 }
        return last.maxElectrons - last.electrons
    }

    var isNobleGas: Bool {
        shells.last?.isFull ?? false
    }

    var isIon: Bool { charge != 0 }

    init(atomicNumber: Int,
         massNumber: Int = 0,
         electronCount: Int = 0,
         position: SIMD3<Double> = .zero,
         velocity: SIMD3<Double> = .zero) {
        _atomIDCounter += 1
        self.atomID = _atomIDCounter
        self.atomicNumber = atomicNumber
        self.massNumber = massNumber == 0
            ? (atomicNumber == 1 ? 1 : atomicNumber * 2)
            : massNumber
        self.electronCount = electronCount == 0 ? atomicNumber : electronCount
        self.position = position
        self.velocity = velocity
        buildShells()
        computeIonizationEnergy()
    }

    private func buildShells() {
        shells = []
        var remaining = electronCount
        for (i, maxE) in kElectronShells.enumerated() {
            guard remaining > 0 else { break }
            let e = min(remaining, maxE)
            shells.append(ElectronShell(n: i + 1, maxElectrons: maxE, electrons: e))
            remaining -= e
        }
    }

    private func computeIonizationEnergy() {
        guard let last = shells.last, !last.isEmpty else {
            ionizationEnergy = 0.0
            return
        }
        let innerElectrons = shells.dropLast().reduce(0) { $0 + $1.electrons }
        let zEff = Double(atomicNumber - innerElectrons)
        let n = Double(last.n)
        ionizationEnergy = 13.6 * zEff * zEff / (n * n)
    }

    func canBondWith(_ other: Atom) -> Bool {
        if isNobleGas || other.isNobleGas { return false }
        if bonds.count >= 4 || other.bonds.count >= 4 { return false }
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
        case "ionic":          return kBondEnergyIonic
        case "polar_covalent": return (kBondEnergyCovalent + kBondEnergyIonic) / 2.0
        default:               return kBondEnergyCovalent
        }
    }

    func distanceTo(_ other: Atom) -> Double {
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

    init(temperature: Double = kTempRecombination) {
        self.temperature = temperature
    }

    /// Reset the atomic system to initial conditions for a new cycle.
    func reset(temperature: Double) {
        self.temperature = temperature
        atoms.removeAll()
        freeElectrons.removeAll()
        bondsFormed = 0
        bondsBroken = 0
    }

    // MARK: Recombination

    /// Capture free electrons into ions when T < T_recombination.
    func recombination(field: QuantumField) -> [Atom] {
        guard temperature <= kTempRecombination else { return [] }

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

            field.particles.removeAll { $0 === proton || $0 === electron }
        }
        return newAtoms
    }

    // MARK: Nucleosynthesis

    /// Form heavier elements through nuclear fusion.
    func nucleosynthesis(protons: Int, neutrons: Int) -> [Atom] {
        var newAtoms: [Atom] = []
        var p = protons
        var n = neutrons

        // Helium-4: 2p + 2n
        while p >= 2 && n >= 2 {
            let he = Atom(
                atomicNumber: 2,
                massNumber: 4,
                position: SIMD3(
                    Double.random(in: -10...10),
                    Double.random(in: -10...10),
                    Double.random(in: -10...10)
                )
            )
            newAtoms.append(he)
            atoms.append(he)
            p -= 2; n -= 2
        }

        // Remaining protons -> hydrogen
        for _ in 0..<p {
            let h = Atom(
                atomicNumber: 1,
                massNumber: 1,
                position: SIMD3(
                    Double.random(in: -10...10),
                    Double.random(in: -10...10),
                    Double.random(in: -10...10)
                )
            )
            newAtoms.append(h)
            atoms.append(h)
        }
        return newAtoms
    }

    // MARK: Stellar Nucleosynthesis

    /// Form heavier elements in stellar cores: C, N, O, and up to Fe.
    func stellarNucleosynthesis(temperature: Double) -> [Atom] {
        var newAtoms: [Atom] = []
        guard temperature >= 1e3 else { return newAtoms }

        var heliums = atoms.filter { $0.atomicNumber == 2 }

        // Triple-alpha: 3 He -> C
        while heliums.count >= 3 && Double.random(in: 0..<1) < 0.01 {
            for _ in 0..<3 {
                let he = heliums.removeLast()
                atoms.removeAll { $0 === he }
            }
            let carbon = Atom(
                atomicNumber: 6, massNumber: 12,
                position: SIMD3(
                    Double.random(in: -5...5),
                    Double.random(in: -5...5),
                    Double.random(in: -5...5)
                )
            )
            newAtoms.append(carbon)
            atoms.append(carbon)
        }

        // C + He -> O
        var carbons = atoms.filter { $0.atomicNumber == 6 }
        heliums = atoms.filter { $0.atomicNumber == 2 }
        while !carbons.isEmpty && !heliums.isEmpty && Double.random(in: 0..<1) < 0.02 {
            let c = carbons.removeLast()
            let he = heliums.removeLast()
            atoms.removeAll { $0 === c || $0 === he }
            let oxygen = Atom(
                atomicNumber: 8, massNumber: 16,
                position: c.position
            )
            newAtoms.append(oxygen)
            atoms.append(oxygen)
        }

        // O + He -> N (simplified chain)
        let oxygens = atoms.filter { $0.atomicNumber == 8 }
        heliums = atoms.filter { $0.atomicNumber == 2 }
        if !oxygens.isEmpty && !heliums.isEmpty && Double.random(in: 0..<1) < 0.005 {
            let o = oxygens[0]
            let he = heliums[0]
            atoms.removeAll { $0 === o || $0 === he }
            let nitrogen = Atom(
                atomicNumber: 7, massNumber: 14,
                position: o.position
            )
            newAtoms.append(nitrogen)
            atoms.append(nitrogen)
        }
        return newAtoms
    }

    // MARK: Bonding

    func attemptBond(_ a1: Atom, _ a2: Atom) -> Bool {
        guard a1.canBondWith(a2) else { return false }
        let dist = a1.distanceTo(a2)
        let bondDist = 2.0
        guard dist <= bondDist * 3.0 else { return false }

        let energyBarrier = a1.bondEnergy(with: a2)
        let thermalEnergy = kBoltzmann * temperature
        let prob: Double
        if thermalEnergy > 0 {
            prob = exp(-energyBarrier / thermalEnergy)
        } else {
            prob = dist < bondDist ? 1.0 : 0.0
        }

        if Double.random(in: 0..<1) < prob {
            a1.bonds.append(a2.atomID)
            a2.bonds.append(a1.atomID)
            bondsFormed += 1
            return true
        }
        return false
    }

    func elementCounts() -> [String: Int] {
        var counts: [String: Int] = [:]
        for a in atoms {
            counts[a.symbol, default: 0] += 1
        }
        return counts
    }
}
