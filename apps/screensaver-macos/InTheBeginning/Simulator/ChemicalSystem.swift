// ChemicalSystem.swift
// InTheBeginning – macOS Screensaver
//
// Chemistry simulation -- molecular assembly and reactions.
// Models formation of molecules from atoms: water, amino acids,
// nucleotides, and other biomolecules essential for life.

import Foundation

// MARK: - Molecule

private var _moleculeIDCounter: Int = 0

final class Molecule {
    let moleculeID: Int
    var atoms: [Atom]
    var name: String
    var formula: String
    var energy: Double
    var position: SIMD3<Double>
    var isOrganic: Bool
    var functionalGroups: [String]

    var molecularWeight: Double {
        atoms.reduce(0.0) { $0 + Double($1.massNumber) }
    }

    var atomCount: Int { atoms.count }

    init(atoms: [Atom] = [],
         name: String = "",
         formula: String = "",
         energy: Double = 0.0,
         position: SIMD3<Double> = .zero,
         isOrganic: Bool = false,
         functionalGroups: [String] = []) {
        _moleculeIDCounter += 1
        self.moleculeID = _moleculeIDCounter
        self.atoms = atoms
        self.name = name
        self.energy = energy
        self.position = position
        self.isOrganic = isOrganic
        self.functionalGroups = functionalGroups

        if formula.isEmpty && !atoms.isEmpty {
            self.formula = Molecule.computeFormula(atoms: atoms)
        } else {
            self.formula = formula
        }

        // Detect organic
        if !self.isOrganic {
            let hasC = atoms.contains { $0.atomicNumber == 6 }
            let hasH = atoms.contains { $0.atomicNumber == 1 }
            self.isOrganic = hasC && hasH
        }
    }

    static func computeFormula(atoms: [Atom]) -> String {
        var counts: [String: Int] = [:]
        for a in atoms {
            counts[a.symbol, default: 0] += 1
        }
        // Standard chemistry ordering: C, H, then alphabetical
        var parts: [String] = []
        for sym in ["C", "H"] {
            if let n = counts.removeValue(forKey: sym) {
                parts.append(n > 1 ? "\(sym)\(n)" : sym)
            }
        }
        for sym in counts.keys.sorted() {
            let n = counts[sym]!
            parts.append(n > 1 ? "\(sym)\(n)" : sym)
        }
        return parts.joined()
    }
}

// MARK: - Chemical System

final class ChemicalSystem {
    let atomic: AtomicSystem
    var molecules: [Molecule] = []
    var reactionsOccurred: Int = 0
    var waterCount: Int = 0
    var aminoAcidCount: Int = 0
    var nucleotideCount: Int = 0

    init(atomicSystem: AtomicSystem) {
        self.atomic = atomicSystem
    }

    // MARK: Water: 2H + O -> H2O

    func formWater() -> [Molecule] {
        var waters: [Molecule] = []
        var hydrogens = atomic.atoms.filter { $0.atomicNumber == 1 && $0.bonds.isEmpty }
        var oxygens   = atomic.atoms.filter { $0.atomicNumber == 8 && $0.bonds.count < 2 }

        while hydrogens.count >= 2 && !oxygens.isEmpty {
            let h1 = hydrogens.removeLast()
            let h2 = hydrogens.removeLast()
            let o  = oxygens.removeLast()

            let water = Molecule(
                atoms: [h1, h2, o],
                name: "water",
                position: o.position
            )
            waters.append(water)
            molecules.append(water)
            waterCount += 1

            h1.bonds.append(o.atomID)
            h2.bonds.append(o.atomID)
            o.bonds.append(contentsOf: [h1.atomID, h2.atomID])
        }
        return waters
    }

    // MARK: Methane: C + 4H -> CH4

    func formMethane() -> [Molecule] {
        var methanes: [Molecule] = []
        var carbons   = atomic.atoms.filter { $0.atomicNumber == 6 && $0.bonds.isEmpty }
        var hydrogens = atomic.atoms.filter { $0.atomicNumber == 1 && $0.bonds.isEmpty }

        while !carbons.isEmpty && hydrogens.count >= 4 {
            let c = carbons.removeLast()
            let hs = (0..<4).map { _ in hydrogens.removeLast() }

            let methane = Molecule(
                atoms: [c] + hs,
                name: "methane",
                position: c.position
            )
            methanes.append(methane)
            molecules.append(methane)

            for h in hs {
                c.bonds.append(h.atomID)
                h.bonds.append(c.atomID)
            }
        }
        return methanes
    }

    // MARK: Ammonia: N + 3H -> NH3

    func formAmmonia() -> [Molecule] {
        var ammonias: [Molecule] = []
        var nitrogens = atomic.atoms.filter { $0.atomicNumber == 7 && $0.bonds.isEmpty }
        var hydrogens = atomic.atoms.filter { $0.atomicNumber == 1 && $0.bonds.isEmpty }

        while !nitrogens.isEmpty && hydrogens.count >= 3 {
            let n  = nitrogens.removeLast()
            let hs = (0..<3).map { _ in hydrogens.removeLast() }

            let ammonia = Molecule(
                atoms: [n] + hs,
                name: "ammonia",
                position: n.position
            )
            ammonias.append(ammonia)
            molecules.append(ammonia)

            for h in hs {
                n.bonds.append(h.atomID)
                h.bonds.append(n.atomID)
            }
        }
        return ammonias
    }

    // MARK: Amino Acid (simplified glycine-like)

    func formAminoAcid(type: String = "Gly") -> Molecule? {
        let carbons   = atomic.atoms.filter { $0.atomicNumber == 6 && $0.bonds.isEmpty }
        let hydrogens = atomic.atoms.filter { $0.atomicNumber == 1 && $0.bonds.isEmpty }
        let oxygens   = atomic.atoms.filter { $0.atomicNumber == 8 && $0.bonds.count < 2 }
        let nitrogens = atomic.atoms.filter { $0.atomicNumber == 7 && $0.bonds.isEmpty }

        guard carbons.count >= 2 && hydrogens.count >= 5 &&
              oxygens.count >= 2 && nitrogens.count >= 1 else { return nil }

        var used: [Atom] = []
        used.append(contentsOf: carbons.suffix(2))
        used.append(contentsOf: hydrogens.suffix(5))
        used.append(contentsOf: oxygens.suffix(2))
        used.append(nitrogens.last!)

        let aa = Molecule(
            atoms: used,
            name: type,
            position: used[0].position,
            isOrganic: true,
            functionalGroups: ["amino", "carboxyl"]
        )
        molecules.append(aa)
        aminoAcidCount += 1

        // Form internal bonds
        let anchor = used[0]
        for atom in used.dropFirst() {
            anchor.bonds.append(atom.atomID)
            atom.bonds.append(anchor.atomID)
        }
        return aa
    }

    // MARK: Nucleotide (simplified)

    func formNucleotide(base: String = "A") -> Molecule? {
        let carbons   = atomic.atoms.filter { $0.atomicNumber == 6 && $0.bonds.isEmpty }
        let hydrogens = atomic.atoms.filter { $0.atomicNumber == 1 && $0.bonds.isEmpty }
        let oxygens   = atomic.atoms.filter { $0.atomicNumber == 8 && $0.bonds.count < 2 }
        let nitrogens = atomic.atoms.filter { $0.atomicNumber == 7 && $0.bonds.isEmpty }

        guard carbons.count >= 5 && hydrogens.count >= 8 &&
              oxygens.count >= 4 && nitrogens.count >= 2 else { return nil }

        var used: [Atom] = []
        used.append(contentsOf: carbons.suffix(5))
        used.append(contentsOf: hydrogens.suffix(8))
        used.append(contentsOf: oxygens.suffix(4))
        used.append(contentsOf: nitrogens.suffix(2))

        let nuc = Molecule(
            atoms: used,
            name: "nucleotide-\(base)",
            position: used[0].position,
            isOrganic: true,
            functionalGroups: ["sugar", "phosphate", "base"]
        )
        molecules.append(nuc)
        nucleotideCount += 1

        let anchor = used[0]
        for atom in used.dropFirst() {
            anchor.bonds.append(atom.atomID)
            atom.bonds.append(anchor.atomID)
        }
        return nuc
    }

    // MARK: Catalyzed Reactions

    func catalyzedReaction(temperature: Double, catalystPresent: Bool) -> Int {
        var formed = 0
        let eaFactor = catalystPresent ? 0.3 : 1.0
        let thermal = kBoltzmann * temperature

        // Try amino acids
        if thermal > 0 && atomic.atoms.count > 10 {
            let prob = exp(-5.0 * eaFactor / (thermal + 1e-20))
            if Double.random(in: 0..<1) < prob {
                let aaType = kAminoAcids.randomElement()!
                if formAminoAcid(type: aaType) != nil {
                    formed += 1
                    reactionsOccurred += 1
                }
            }
        }

        // Try nucleotides
        if thermal > 0 && atomic.atoms.count > 19 {
            let prob = exp(-8.0 * eaFactor / (thermal + 1e-20))
            if Double.random(in: 0..<1) < prob {
                let base = ["A", "T", "G", "C"].randomElement()!
                if formNucleotide(base: base) != nil {
                    formed += 1
                    reactionsOccurred += 1
                }
            }
        }
        return formed
    }

    func moleculeCensus() -> [String: Int] {
        var counts: [String: Int] = [:]
        for m in molecules {
            let key = m.name.isEmpty ? m.formula : m.name
            counts[key, default: 0] += 1
        }
        return counts
    }
}
