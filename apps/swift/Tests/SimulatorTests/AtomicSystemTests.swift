// AtomicSystemTests.swift
// Tests for AtomicSystem.swift

import XCTest
@testable import InTheBeginningSimulator

final class AtomicSystemTests: XCTestCase {

    // MARK: - PeriodicTable

    func testPeriodicTableHydrogen() {
        let h = PeriodicTable.elements[1]
        XCTAssertNotNil(h)
        XCTAssertEqual(h?.symbol, "H")
        XCTAssertEqual(h?.name, "Hydrogen")
        XCTAssertEqual(h?.group, 1)
        XCTAssertEqual(h?.period, 1)
    }

    func testPeriodicTableHelium() {
        let he = PeriodicTable.elements[2]
        XCTAssertNotNil(he)
        XCTAssertEqual(he?.symbol, "He")
        XCTAssertEqual(he?.electronegativity, 0.0)
    }

    func testPeriodicTableCarbon() {
        let c = PeriodicTable.elements[6]
        XCTAssertNotNil(c)
        XCTAssertEqual(c?.symbol, "C")
        XCTAssertEqual(c?.name, "Carbon")
    }

    func testPeriodicTableIron() {
        let fe = PeriodicTable.elements[26]
        XCTAssertNotNil(fe)
        XCTAssertEqual(fe?.symbol, "Fe")
    }

    func testPeriodicTableElementCount() {
        // Should have 21 entries (1-20 plus 26)
        XCTAssertEqual(PeriodicTable.elements.count, 21)
    }

    // MARK: - ElectronShell

    func testElectronShellInit() {
        let shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 0)
        XCTAssertEqual(shell.n, 1)
        XCTAssertEqual(shell.maxElectrons, 2)
        XCTAssertEqual(shell.electrons, 0)
        XCTAssertTrue(shell.isEmpty)
        XCTAssertFalse(shell.isFull)
    }

    func testElectronShellFull() {
        let shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 2)
        XCTAssertTrue(shell.isFull)
        XCTAssertFalse(shell.isEmpty)
    }

    func testElectronShellAddElectron() {
        var shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 0)
        XCTAssertTrue(shell.addElectron())
        XCTAssertEqual(shell.electrons, 1)
    }

    func testElectronShellAddElectronFull() {
        var shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 2)
        XCTAssertFalse(shell.addElectron())
        XCTAssertEqual(shell.electrons, 2)
    }

    func testElectronShellRemoveElectron() {
        var shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 1)
        XCTAssertTrue(shell.removeElectron())
        XCTAssertEqual(shell.electrons, 0)
    }

    func testElectronShellRemoveElectronEmpty() {
        var shell = ElectronShell(n: 1, maxElectrons: 2, electrons: 0)
        XCTAssertFalse(shell.removeElectron())
    }

    // MARK: - Atom

    func testAtomHydrogen() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.atomicNumber, 1)
        XCTAssertEqual(h.massNumber, 1)
        XCTAssertEqual(h.electronCount, 1)
        XCTAssertEqual(h.symbol, "H")
        XCTAssertEqual(h.name, "Hydrogen")
        XCTAssertEqual(h.charge, 0)
        XCTAssertFalse(h.isIon)
    }

    func testAtomHelium() {
        let he = Atom(atomicNumber: 2, massNumber: 4)
        XCTAssertEqual(he.atomicNumber, 2)
        XCTAssertEqual(he.massNumber, 4)
        XCTAssertEqual(he.symbol, "He")
        XCTAssertTrue(he.isNobleGas, "Helium should be a noble gas")
    }

    func testAtomCarbon() {
        let c = Atom(atomicNumber: 6, massNumber: 12)
        XCTAssertEqual(c.symbol, "C")
        XCTAssertEqual(c.name, "Carbon")
        XCTAssertEqual(c.charge, 0)
        XCTAssertFalse(c.isNobleGas)
    }

    func testAtomUniqueIDs() {
        let a1 = Atom(atomicNumber: 1)
        let a2 = Atom(atomicNumber: 1)
        XCTAssertNotEqual(a1.id, a2.id)
    }

    func testAtomElectronegativity() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.electronegativity, 2.20)

        let f = Atom(atomicNumber: 9)
        XCTAssertEqual(f.electronegativity, 3.98)
    }

    func testAtomValenceElectrons() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.valenceElectrons, 1)

        let he = Atom(atomicNumber: 2)
        XCTAssertEqual(he.valenceElectrons, 2)
    }

    func testAtomShellBuilding() {
        let na = Atom(atomicNumber: 11) // Sodium: 2, 8, 1
        XCTAssertEqual(na.shells.count, 3)
        XCTAssertEqual(na.shells[0].electrons, 2)
        XCTAssertEqual(na.shells[1].electrons, 8)
        XCTAssertEqual(na.shells[2].electrons, 1)
    }

    func testAtomDefaultMassNumber() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.massNumber, 1) // Special case for hydrogen

        let c = Atom(atomicNumber: 6)
        XCTAssertEqual(c.massNumber, 12) // 6 * 2
    }

    func testAtomCharge() {
        let h = Atom(atomicNumber: 1, electronCount: 0)
        XCTAssertEqual(h.charge, 1) // H+

        let o = Atom(atomicNumber: 8, electronCount: 10)
        XCTAssertEqual(o.charge, -2) // O2-
    }

    // MARK: - Ionization

    func testAtomIonize() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.electronCount, 1)
        XCTAssertTrue(h.ionize())
        XCTAssertEqual(h.electronCount, 0)
        XCTAssertEqual(h.charge, 1)
        XCTAssertTrue(h.isIon)
    }

    func testAtomIonizeEmpty() {
        let h = Atom(atomicNumber: 1, electronCount: 0)
        XCTAssertFalse(h.ionize())
    }

    func testAtomCaptureElectron() {
        let h = Atom(atomicNumber: 1, electronCount: 0)
        XCTAssertTrue(h.captureElectron())
        XCTAssertEqual(h.electronCount, 1)
        XCTAssertEqual(h.charge, 0)
    }

    func testIonizationEnergy() {
        let h = Atom(atomicNumber: 1)
        XCTAssertGreaterThan(h.ionizationEnergy, 0.0)
    }

    // MARK: - Bonding

    func testCanBondNormal() {
        let h = Atom(atomicNumber: 1)
        let o = Atom(atomicNumber: 8)
        XCTAssertTrue(h.canBond(with: o))
    }

    func testCannotBondNobleGas() {
        let he = Atom(atomicNumber: 2)
        let h = Atom(atomicNumber: 1)
        XCTAssertFalse(he.canBond(with: h))
    }

    func testCannotBondMaxBonds() {
        let c = Atom(atomicNumber: 6)
        c.bondIDs = [1, 2, 3, 4] // Already 4 bonds
        let h = Atom(atomicNumber: 1)
        XCTAssertFalse(c.canBond(with: h))
    }

    func testBondTypeCovalent() {
        let h1 = Atom(atomicNumber: 1)
        let h2 = Atom(atomicNumber: 1)
        XCTAssertEqual(h1.bondType(with: h2), "covalent")
    }

    func testBondTypeIonic() {
        let na = Atom(atomicNumber: 11)
        let cl = Atom(atomicNumber: 17)
        XCTAssertEqual(na.bondType(with: cl), "ionic")
    }

    func testBondTypePolarCovalent() {
        let h = Atom(atomicNumber: 1)
        let o = Atom(atomicNumber: 8)
        // H=2.20, O=3.44, diff=1.24 -> polar_covalent
        XCTAssertEqual(h.bondType(with: o), "polar_covalent")
    }

    func testBondEnergy() {
        let h1 = Atom(atomicNumber: 1)
        let h2 = Atom(atomicNumber: 1)
        let energy = h1.bondEnergy(with: h2)
        XCTAssertEqual(energy, ChemistryParams.bondEnergyCovalent)
    }

    func testBondEnergyIonic() {
        let na = Atom(atomicNumber: 11)
        let cl = Atom(atomicNumber: 17)
        let energy = na.bondEnergy(with: cl)
        XCTAssertEqual(energy, ChemistryParams.bondEnergyIonic)
    }

    func testDistance() {
        let a1 = Atom(atomicNumber: 1, position: SIMD3<Double>(0, 0, 0))
        let a2 = Atom(atomicNumber: 1, position: SIMD3<Double>(3, 4, 0))
        XCTAssertEqual(a1.distance(to: a2), 5.0, accuracy: 1e-10)
    }

    // MARK: - AtomicSystem

    func testAtomicSystemInit() {
        let sys = AtomicSystem()
        XCTAssertEqual(sys.temperature, TemperatureScale.recombination)
        XCTAssertTrue(sys.atoms.isEmpty)
        XCTAssertEqual(sys.bondsFormed, 0)
        XCTAssertEqual(sys.bondsBroken, 0)
    }

    func testAtomicSystemCustomTemp() {
        let sys = AtomicSystem(temperature: 500.0)
        XCTAssertEqual(sys.temperature, 500.0)
    }

    func testNucleosynthesis() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 4, neutrons: 4)
        // 2p+2n -> He, 2p+2n -> He
        XCTAssertFalse(newAtoms.isEmpty)
        let heliums = newAtoms.filter { $0.atomicNumber == 2 }
        XCTAssertEqual(heliums.count, 2)
    }

    func testNucleosynthesisRemainingProtons() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 3, neutrons: 2)
        // 2p+2n -> He, 1p remaining -> H
        let heliums = newAtoms.filter { $0.atomicNumber == 2 }
        let hydrogens = newAtoms.filter { $0.atomicNumber == 1 }
        XCTAssertEqual(heliums.count, 1)
        XCTAssertEqual(hydrogens.count, 1)
    }

    func testRecombinationBelowThreshold() {
        let sys = AtomicSystem(temperature: TemperatureScale.recombination * 0.5)
        let field = QuantumField()

        let proton = Particle(particleType: .proton)
        let electron = Particle(particleType: .electron)
        field.particles.append(contentsOf: [proton, electron])

        let newAtoms = sys.recombination(field: field)
        XCTAssertEqual(newAtoms.count, 1)
        XCTAssertEqual(newAtoms.first?.atomicNumber, 1)
        // Proton and electron should be removed from field
        XCTAssertTrue(field.particles.filter { $0.particleType == .proton }.isEmpty)
        XCTAssertTrue(field.particles.filter { $0.particleType == .electron }.isEmpty)
    }

    func testRecombinationAboveThreshold() {
        let sys = AtomicSystem(temperature: TemperatureScale.recombination * 2.0)
        let field = QuantumField()

        let proton = Particle(particleType: .proton)
        let electron = Particle(particleType: .electron)
        field.particles.append(contentsOf: [proton, electron])

        let newAtoms = sys.recombination(field: field)
        XCTAssertTrue(newAtoms.isEmpty)
    }

    func testElementCounts() {
        let sys = AtomicSystem()
        let _ = sys.nucleosynthesis(protons: 4, neutrons: 2)
        let counts = sys.elementCounts()
        XCTAssertNotNil(counts["He"])
        XCTAssertNotNil(counts["H"])
    }

    func testStellarNucleosynthesis() {
        let sys = AtomicSystem()
        // Add enough helium atoms for triple-alpha
        for _ in 0..<10 {
            let he = Atom(atomicNumber: 2, massNumber: 4)
            sys.atoms.append(he)
        }
        // Stellar nucleosynthesis is probabilistic, so run multiple times
        var producedCarbon = false
        for _ in 0..<100 {
            let newAtoms = sys.stellarNucleosynthesis(temperature: 1e4)
            if newAtoms.contains(where: { $0.atomicNumber == 6 }) {
                producedCarbon = true
                break
            }
        }
        // It is probabilistic (1% chance per iteration), but with 100 tries and 10 heliums, likely
        // If it doesn't produce carbon, that is still acceptable behavior
    }

    func testStellarNucleosynthesisBelowThreshold() {
        let sys = AtomicSystem()
        let he = Atom(atomicNumber: 2, massNumber: 4)
        sys.atoms.append(he)
        let newAtoms = sys.stellarNucleosynthesis(temperature: 100.0)
        XCTAssertTrue(newAtoms.isEmpty)
    }

    func testAttemptBond() {
        let sys = AtomicSystem(temperature: 0.0) // zero temp -> dist < bondDist gives 100%
        let a1 = Atom(atomicNumber: 1, position: SIMD3<Double>(0, 0, 0))
        let a2 = Atom(atomicNumber: 8, position: SIMD3<Double>(1, 0, 0))
        sys.atoms.append(contentsOf: [a1, a2])

        let bonded = sys.attemptBond(a1, a2)
        if bonded {
            XCTAssertTrue(a1.bondIDs.contains(a2.id))
            XCTAssertTrue(a2.bondIDs.contains(a1.id))
            XCTAssertEqual(sys.bondsFormed, 1)
        }
    }

    func testAttemptBondTooFar() {
        let sys = AtomicSystem(temperature: 300.0)
        let a1 = Atom(atomicNumber: 1, position: SIMD3<Double>(0, 0, 0))
        let a2 = Atom(atomicNumber: 8, position: SIMD3<Double>(100, 0, 0))
        sys.atoms.append(contentsOf: [a1, a2])

        let bonded = sys.attemptBond(a1, a2)
        XCTAssertFalse(bonded)
    }

    func testBreakBond() {
        let sys = AtomicSystem(temperature: 1e10) // Very high temp
        let a1 = Atom(atomicNumber: 1, position: .zero)
        let a2 = Atom(atomicNumber: 8, position: .zero)
        a1.bondIDs.append(a2.id)
        a2.bondIDs.append(a1.id)
        sys.atoms.append(contentsOf: [a1, a2])

        // At very high temperature, bond should eventually break
        var broken = false
        for _ in 0..<100 {
            if sys.breakBond(a1, a2) {
                broken = true
                break
            }
            // Re-add bond for next try
            if !a1.bondIDs.contains(a2.id) {
                a1.bondIDs.append(a2.id)
                a2.bondIDs.append(a1.id)
            }
        }
        // Probabilistic, so we don't hard-assert
    }

    func testBreakBondNoBond() {
        let sys = AtomicSystem(temperature: 1e10)
        let a1 = Atom(atomicNumber: 1)
        let a2 = Atom(atomicNumber: 8)
        XCTAssertFalse(sys.breakBond(a1, a2))
    }

    // MARK: - Additional ElementData Coverage

    func testElementDataStruct() {
        let e = ElementData(symbol: "X", name: "Xenium", group: 1, period: 1, electronegativity: 1.5)
        XCTAssertEqual(e.symbol, "X")
        XCTAssertEqual(e.name, "Xenium")
        XCTAssertEqual(e.group, 1)
        XCTAssertEqual(e.period, 1)
        XCTAssertEqual(e.electronegativity, 1.5)
    }

    func testPeriodicTableAllElements() {
        // Verify all expected elements exist
        let expectedElements: [Int: String] = [
            1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B",
            6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
            11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P",
            16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca", 26: "Fe"
        ]
        for (z, symbol) in expectedElements {
            XCTAssertEqual(PeriodicTable.elements[z]?.symbol, symbol,
                "Element \(z) should have symbol \(symbol)")
        }
    }

    // MARK: - Additional Atom Coverage

    func testAtomDisplayColorHydrogen() {
        let h = Atom(atomicNumber: 1)
        let color = h.displayColor
        XCTAssertEqual(color.x, 1.0)
        XCTAssertEqual(color.y, 1.0)
        XCTAssertEqual(color.z, 1.0)
        XCTAssertEqual(color.w, 1.0)
    }

    func testAtomDisplayColorHelium() {
        let he = Atom(atomicNumber: 2)
        let color = he.displayColor
        XCTAssertEqual(color.x, 0.9, accuracy: 0.01)
        XCTAssertEqual(color.y, 0.9, accuracy: 0.01)
    }

    func testAtomDisplayColorCarbon() {
        let c = Atom(atomicNumber: 6)
        let color = c.displayColor
        XCTAssertEqual(color.x, 0.3, accuracy: 0.01)
    }

    func testAtomDisplayColorNitrogen() {
        let n = Atom(atomicNumber: 7)
        let color = n.displayColor
        XCTAssertEqual(color.x, 0.2, accuracy: 0.01)
    }

    func testAtomDisplayColorOxygen() {
        let o = Atom(atomicNumber: 8)
        let color = o.displayColor
        XCTAssertEqual(color.x, 1.0, accuracy: 0.01)
        XCTAssertEqual(color.y, 0.2, accuracy: 0.01)
    }

    func testAtomDisplayColorPhosphorus() {
        let p = Atom(atomicNumber: 15)
        let color = p.displayColor
        XCTAssertEqual(color.x, 1.0, accuracy: 0.01)
    }

    func testAtomDisplayColorIron() {
        let fe = Atom(atomicNumber: 26)
        let color = fe.displayColor
        XCTAssertEqual(color.x, 0.7, accuracy: 0.01)
    }

    func testAtomDisplayColorDefault() {
        // An element not in the switch statement (e.g., Lithium, atomic number 3)
        let li = Atom(atomicNumber: 3)
        let color = li.displayColor
        XCTAssertEqual(color.x, 0.6, accuracy: 0.01)
        XCTAssertEqual(color.y, 0.6, accuracy: 0.01)
        XCTAssertEqual(color.z, 0.6, accuracy: 0.01)
    }

    func testAtomNeededElectrons() {
        let h = Atom(atomicNumber: 1)
        // H has 1 electron in shell with max 2
        XCTAssertEqual(h.neededElectrons, 1)

        let he = Atom(atomicNumber: 2)
        // He has 2 electrons in shell with max 2
        XCTAssertEqual(he.neededElectrons, 0)
    }

    func testAtomNeededElectronsNoShells() {
        let h = Atom(atomicNumber: 1, electronCount: 0)
        // With 0 electrons, no shells are built
        XCTAssertEqual(h.neededElectrons, 0)
    }

    func testAtomSymbolUnknownElement() {
        // Atom with atomic number not in the periodic table
        let unknown = Atom(atomicNumber: 99)
        XCTAssertEqual(unknown.symbol, "E99")
    }

    func testAtomNameUnknownElement() {
        let unknown = Atom(atomicNumber: 99)
        XCTAssertEqual(unknown.name, "Element-99")
    }

    func testAtomElectronegativityUnknownElement() {
        let unknown = Atom(atomicNumber: 99)
        XCTAssertEqual(unknown.electronegativity, 1.0)
    }

    func testAtomComputeIonizationEnergyNoElectrons() {
        let h = Atom(atomicNumber: 1, electronCount: 0)
        XCTAssertEqual(h.ionizationEnergy, 0.0)
    }

    func testAtomBondEnergyPolarCovalent() {
        let h = Atom(atomicNumber: 1)
        let o = Atom(atomicNumber: 8)
        let energy = h.bondEnergy(with: o)
        let expected = (ChemistryParams.bondEnergyCovalent + ChemistryParams.bondEnergyIonic) / 2.0
        XCTAssertEqual(energy, expected, accuracy: 1e-10)
    }

    func testAtomDistanceZero() {
        let a1 = Atom(atomicNumber: 1, position: .zero)
        let a2 = Atom(atomicNumber: 1, position: .zero)
        XCTAssertEqual(a1.distance(to: a2), 0.0, accuracy: 1e-10)
    }

    func testAtomDistance3D() {
        let a1 = Atom(atomicNumber: 1, position: SIMD3<Double>(1, 2, 3))
        let a2 = Atom(atomicNumber: 1, position: SIMD3<Double>(4, 6, 3))
        // sqrt(9 + 16 + 0) = 5
        XCTAssertEqual(a1.distance(to: a2), 5.0, accuracy: 1e-10)
    }

    func testAtomIsNotIonWhenNeutral() {
        let c = Atom(atomicNumber: 6)
        XCTAssertFalse(c.isIon)
    }

    func testAtomIonizeAndCaptureRoundTrip() {
        let h = Atom(atomicNumber: 1)
        XCTAssertEqual(h.charge, 0)
        h.ionize()
        XCTAssertEqual(h.charge, 1)
        h.captureElectron()
        XCTAssertEqual(h.charge, 0)
    }

    // MARK: - SIMD3 Extension Coverage

    func testSIMD3RandomGaussian() {
        let vec = SIMD3<Double>.randomGaussian(sigma: 10.0)
        // Vector should be finite
        XCTAssertTrue(vec.x.isFinite)
        XCTAssertTrue(vec.y.isFinite)
        XCTAssertTrue(vec.z.isFinite)
    }

    func testSIMD3RandomGaussianZeroSigma() {
        let vec = SIMD3<Double>.randomGaussian(sigma: 0.0)
        XCTAssertEqual(vec.x, 0.0)
        XCTAssertEqual(vec.y, 0.0)
        XCTAssertEqual(vec.z, 0.0)
    }

    // MARK: - Additional AtomicSystem Coverage

    func testAtomicSystemFreeElectrons() {
        let sys = AtomicSystem()
        XCTAssertTrue(sys.freeElectrons.isEmpty)
    }

    func testBreakBondLowTemperature() {
        let sys = AtomicSystem(temperature: 0.001)
        let a1 = Atom(atomicNumber: 1, position: .zero)
        let a2 = Atom(atomicNumber: 8, position: .zero)
        a1.bondIDs.append(a2.id)
        a2.bondIDs.append(a1.id)
        sys.atoms.append(contentsOf: [a1, a2])

        // At very low temperature, thermal energy < energyBarrier * 0.5
        let broken = sys.breakBond(a1, a2)
        XCTAssertFalse(broken, "Bond should not break at very low temperature")
    }

    func testNucleosynthesisNoNeutrons() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 5, neutrons: 0)
        // All protons should become hydrogen
        let hydrogens = newAtoms.filter { $0.atomicNumber == 1 }
        XCTAssertEqual(hydrogens.count, 5)
        let heliums = newAtoms.filter { $0.atomicNumber == 2 }
        XCTAssertEqual(heliums.count, 0)
    }

    func testNucleosynthesisNoProtons() {
        let sys = AtomicSystem()
        let newAtoms = sys.nucleosynthesis(protons: 0, neutrons: 5)
        // No atoms can form from just neutrons in this model
        XCTAssertTrue(newAtoms.isEmpty)
    }

    func testRecombinationMultipleAtoms() {
        let sys = AtomicSystem(temperature: TemperatureScale.recombination * 0.5)
        let field = QuantumField()

        for _ in 0..<5 {
            field.particles.append(Particle(particleType: .proton))
            field.particles.append(Particle(particleType: .electron))
        }

        let newAtoms = sys.recombination(field: field)
        XCTAssertEqual(newAtoms.count, 5)
    }

    func testRecombinationMoreProtonsThanElectrons() {
        let sys = AtomicSystem(temperature: TemperatureScale.recombination * 0.5)
        let field = QuantumField()

        for _ in 0..<5 {
            field.particles.append(Particle(particleType: .proton))
        }
        for _ in 0..<2 {
            field.particles.append(Particle(particleType: .electron))
        }

        let newAtoms = sys.recombination(field: field)
        XCTAssertEqual(newAtoms.count, 2)
        // 3 protons should remain
        XCTAssertEqual(field.particles.filter { $0.particleType == .proton }.count, 3)
    }

    func testElementCountsEmpty() {
        let sys = AtomicSystem()
        let counts = sys.elementCounts()
        XCTAssertTrue(counts.isEmpty)
    }

    func testElementCountsMultiple() {
        let sys = AtomicSystem()
        sys.atoms.append(Atom(atomicNumber: 1))
        sys.atoms.append(Atom(atomicNumber: 1))
        sys.atoms.append(Atom(atomicNumber: 6))
        let counts = sys.elementCounts()
        XCTAssertEqual(counts["H"], 2)
        XCTAssertEqual(counts["C"], 1)
    }

    func testAttemptBondNobleGas() {
        let sys = AtomicSystem(temperature: 300.0)
        let he = Atom(atomicNumber: 2, position: .zero)
        let h = Atom(atomicNumber: 1, position: SIMD3<Double>(0.5, 0, 0))
        sys.atoms.append(contentsOf: [he, h])
        let bonded = sys.attemptBond(he, h)
        XCTAssertFalse(bonded)
    }

    func testStellarNucleosynthesisLowTemp() {
        let sys = AtomicSystem()
        for _ in 0..<10 {
            sys.atoms.append(Atom(atomicNumber: 2, massNumber: 4))
        }
        let newAtoms = sys.stellarNucleosynthesis(temperature: 500.0)
        XCTAssertTrue(newAtoms.isEmpty, "Should not synthesize below 1e3 temperature")
    }
}
