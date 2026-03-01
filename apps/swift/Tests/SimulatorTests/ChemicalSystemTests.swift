// ChemicalSystemTests.swift
// Tests for ChemicalSystem.swift

import XCTest
@testable import InTheBeginningSimulator

final class ChemicalSystemTests: XCTestCase {

    // MARK: - BondType

    func testBondTypeAllCases() {
        XCTAssertEqual(BondType.allCases.count, 5)
    }

    func testBondTypeStrength() {
        XCTAssertEqual(BondType.covalent.strength, ChemistryParams.bondEnergyCovalent)
        XCTAssertEqual(BondType.ionic.strength, ChemistryParams.bondEnergyIonic)
        XCTAssertEqual(BondType.hydrogen.strength, ChemistryParams.bondEnergyHydrogen)
        XCTAssertEqual(BondType.vanDerWaals.strength, ChemistryParams.bondEnergyVanDerWaals)
    }

    func testBondTypePolarCovalentStrength() {
        let expected = (ChemistryParams.bondEnergyCovalent + ChemistryParams.bondEnergyIonic) / 2.0
        XCTAssertEqual(BondType.polarCovalent.strength, expected, accuracy: 1e-10)
    }

    // MARK: - Bond

    func testBondCreation() {
        let bond = Bond(atomA: 1, atomB: 2, type: .covalent, energy: 3.5)
        XCTAssertEqual(bond.atomA, 1)
        XCTAssertEqual(bond.atomB, 2)
        XCTAssertEqual(bond.type, .covalent)
        XCTAssertEqual(bond.energy, 3.5)
    }

    func testBondUniqueIDs() {
        let b1 = Bond(atomA: 1, atomB: 2, type: .covalent, energy: 3.5)
        let b2 = Bond(atomA: 1, atomB: 3, type: .covalent, energy: 3.5)
        XCTAssertNotEqual(b1.id, b2.id)
    }

    // MARK: - MoleculeType

    func testMoleculeTypeAllCases() {
        XCTAssertEqual(MoleculeType.allCases.count, 11)
    }

    func testMoleculeTypeWater() {
        XCTAssertEqual(MoleculeType.water.rawValue, "H2O")
        XCTAssertEqual(MoleculeType.water.displayName, "Water")
        XCTAssertFalse(MoleculeType.water.isOrganic)
    }

    func testMoleculeTypeMethane() {
        XCTAssertEqual(MoleculeType.methane.rawValue, "CH4")
        XCTAssertTrue(MoleculeType.methane.isOrganic)
    }

    func testMoleculeTypeAminoAcidOrganic() {
        XCTAssertTrue(MoleculeType.aminoAcid.isOrganic)
    }

    func testMoleculeTypeInorganicNotOrganic() {
        XCTAssertFalse(MoleculeType.genericInorganic.isOrganic)
        XCTAssertFalse(MoleculeType.carbonDioxide.isOrganic)
        XCTAssertFalse(MoleculeType.water.isOrganic)
        XCTAssertFalse(MoleculeType.ammonia.isOrganic)
    }

    func testOrganicTypes() {
        let organics: [MoleculeType] = [.methane, .hydrogenCyanide, .formaldehyde,
                                         .aminoAcid, .nucleotide, .phospholipid, .genericOrganic]
        for t in organics {
            XCTAssertTrue(t.isOrganic, "\(t.rawValue) should be organic")
        }
    }

    // MARK: - Molecule

    func testMoleculeCreation() {
        let mol = Molecule(atomIDs: [1, 2, 3], formula: "H2O", moleculeType: .water)
        XCTAssertEqual(mol.atomIDs, [1, 2, 3])
        XCTAssertEqual(mol.formula, "H2O")
        XCTAssertEqual(mol.moleculeType, .water)
        XCTAssertTrue(mol.isStable)
        XCTAssertEqual(mol.position, .zero)
    }

    func testMoleculeUniqueIDs() {
        let m1 = Molecule(atomIDs: [1], formula: "X", moleculeType: .water)
        let m2 = Molecule(atomIDs: [2], formula: "Y", moleculeType: .water)
        XCTAssertNotEqual(m1.id, m2.id)
    }

    func testMoleculeBondEnergy() {
        let b1 = Bond(atomA: 1, atomB: 2, type: .covalent, energy: 3.5)
        let b2 = Bond(atomA: 1, atomB: 3, type: .covalent, energy: 3.5)
        let mol = Molecule(atomIDs: [1, 2, 3], formula: "H2O", moleculeType: .water, bonds: [b1, b2])
        XCTAssertEqual(mol.bondEnergy, 7.0, accuracy: 1e-10)
    }

    func testMoleculeNoBonds() {
        let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .genericInorganic)
        XCTAssertEqual(mol.bondEnergy, 0.0)
    }

    // MARK: - ChemicalSystem

    func testChemicalSystemInit() {
        let sys = ChemicalSystem()
        XCTAssertEqual(sys.temperature, TemperatureScale.earthSurface)
        XCTAssertTrue(sys.molecules.isEmpty)
        XCTAssertEqual(sys.pH, 7.0)
        XCTAssertFalse(sys.catalystPresent)
        XCTAssertEqual(sys.totalReactions, 0)
    }

    func testChemicalSystemCustomTemp() {
        let sys = ChemicalSystem(temperature: 500.0)
        XCTAssertEqual(sys.temperature, 500.0)
    }

    func testFormWater() {
        let atomSys = AtomicSystem()
        let h1 = Atom(atomicNumber: 1, massNumber: 1)
        let h2 = Atom(atomicNumber: 1, massNumber: 1)
        let o = Atom(atomicNumber: 8, massNumber: 16)
        atomSys.atoms.append(contentsOf: [h1, h2, o])

        let chemSys = ChemicalSystem()
        let water = chemSys.formWater(atomicSystem: atomSys)
        XCTAssertEqual(water.count, 1)
        XCTAssertEqual(water.first?.moleculeType, .water)
        XCTAssertEqual(water.first?.formula, "H2O")
        XCTAssertEqual(chemSys.waterCount, 1)
        XCTAssertGreaterThan(chemSys.totalReactions, 0)
    }

    func testFormWaterInsufficientHydrogen() {
        let atomSys = AtomicSystem()
        let h = Atom(atomicNumber: 1, massNumber: 1)
        let o = Atom(atomicNumber: 8, massNumber: 16)
        atomSys.atoms.append(contentsOf: [h, o])

        let chemSys = ChemicalSystem()
        let water = chemSys.formWater(atomicSystem: atomSys)
        XCTAssertTrue(water.isEmpty)
    }

    func testFormWaterNoOxygen() {
        let atomSys = AtomicSystem()
        let h1 = Atom(atomicNumber: 1, massNumber: 1)
        let h2 = Atom(atomicNumber: 1, massNumber: 1)
        atomSys.atoms.append(contentsOf: [h1, h2])

        let chemSys = ChemicalSystem()
        let water = chemSys.formWater(atomicSystem: atomSys)
        XCTAssertTrue(water.isEmpty)
    }

    func testFormSimpleMoleculesMethane() {
        let atomSys = AtomicSystem()
        let c = Atom(atomicNumber: 6, massNumber: 12)
        atomSys.atoms.append(c)
        for _ in 0..<4 {
            let h = Atom(atomicNumber: 1, massNumber: 1)
            atomSys.atoms.append(h)
        }

        let chemSys = ChemicalSystem()
        let mols = chemSys.formSimpleMolecules(atomicSystem: atomSys)
        let methanes = mols.filter { $0.moleculeType == .methane }
        XCTAssertEqual(methanes.count, 1)
    }

    func testFormSimpleMoleculesAmmonia() {
        let atomSys = AtomicSystem()
        let n = Atom(atomicNumber: 7, massNumber: 14)
        atomSys.atoms.append(n)
        for _ in 0..<3 {
            let h = Atom(atomicNumber: 1, massNumber: 1)
            atomSys.atoms.append(h)
        }

        let chemSys = ChemicalSystem()
        let mols = chemSys.formSimpleMolecules(atomicSystem: atomSys)
        let ammonias = mols.filter { $0.moleculeType == .ammonia }
        XCTAssertEqual(ammonias.count, 1)
    }

    func testFormSimpleMoleculesCO2() {
        let atomSys = AtomicSystem()
        let c = Atom(atomicNumber: 6, massNumber: 12)
        let o1 = Atom(atomicNumber: 8, massNumber: 16)
        let o2 = Atom(atomicNumber: 8, massNumber: 16)
        atomSys.atoms.append(contentsOf: [c, o1, o2])

        let chemSys = ChemicalSystem()
        let mols = chemSys.formSimpleMolecules(atomicSystem: atomSys)
        let co2s = mols.filter { $0.moleculeType == .carbonDioxide }
        XCTAssertEqual(co2s.count, 1)
    }

    func testMoleculeCounts() {
        let chemSys = ChemicalSystem()
        let water = Molecule(atomIDs: [1, 2, 3], formula: "H2O", moleculeType: .water)
        let methane = Molecule(atomIDs: [4, 5, 6, 7, 8], formula: "CH4", moleculeType: .methane)
        chemSys.molecules.append(contentsOf: [water, methane])

        let counts = chemSys.moleculeCounts()
        XCTAssertEqual(counts["H2O"], 1)
        XCTAssertEqual(counts["CH4"], 1)
    }

    func testWaterCount() {
        let chemSys = ChemicalSystem()
        XCTAssertEqual(chemSys.waterCount, 0)

        let water = Molecule(atomIDs: [1, 2, 3], formula: "H2O", moleculeType: .water)
        chemSys.molecules.append(water)
        XCTAssertEqual(chemSys.waterCount, 1)
    }

    func testAminoAcidCount() {
        let chemSys = ChemicalSystem()
        XCTAssertEqual(chemSys.aminoAcidCount, 0)

        let aa = Molecule(atomIDs: [1], formula: "Gly", moleculeType: .aminoAcid)
        chemSys.molecules.append(aa)
        XCTAssertEqual(chemSys.aminoAcidCount, 1)
    }

    func testNucleotideCount() {
        let chemSys = ChemicalSystem()
        XCTAssertEqual(chemSys.nucleotideCount, 0)

        let nuc = Molecule(atomIDs: [1], formula: "nucleotide", moleculeType: .nucleotide)
        chemSys.molecules.append(nuc)
        XCTAssertEqual(chemSys.nucleotideCount, 1)
    }

    func testOrganicCount() {
        let chemSys = ChemicalSystem()
        let methane = Molecule(atomIDs: [1], formula: "CH4", moleculeType: .methane)
        let water = Molecule(atomIDs: [2], formula: "H2O", moleculeType: .water)
        let aa = Molecule(atomIDs: [3], formula: "Gly", moleculeType: .aminoAcid)
        chemSys.molecules.append(contentsOf: [methane, water, aa])
        XCTAssertEqual(chemSys.organicCount, 2) // methane + aminoAcid
    }

    func testThermalDecompositionBelowThreshold() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .genericOrganic, isStable: true)
        chemSys.molecules.append(mol)
        let decomposed = chemSys.thermalDecomposition()
        XCTAssertEqual(decomposed, 0)
        XCTAssertEqual(chemSys.molecules.count, 1)
    }

    func testEvolve() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        let mol = Molecule(
            atomIDs: [1],
            formula: "X",
            moleculeType: .genericOrganic,
            velocity: SIMD3<Double>(1.0, 0.0, 0.0)
        )
        chemSys.molecules.append(mol)
        let posBefore = mol.position
        chemSys.evolve(dt: 1.0)
        XCTAssertNotEqual(mol.position, posBefore)
    }

    func testSynthesizeAminoAcidsWithPrecursors() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        // Add precursor molecules
        let methane = Molecule(atomIDs: [1, 2, 3, 4, 5], formula: "CH4", moleculeType: .methane)
        let ammonia = Molecule(atomIDs: [6, 7, 8, 9], formula: "NH3", moleculeType: .ammonia)
        let water = Molecule(atomIDs: [10, 11, 12], formula: "H2O", moleculeType: .water)
        chemSys.molecules.append(contentsOf: [methane, ammonia, water])

        // Try many times since it's probabilistic
        var produced = false
        for _ in 0..<200 {
            let aas = chemSys.synthesizeAminoAcids(energyInput: 1000.0)
            if !aas.isEmpty {
                produced = true
                break
            }
            // Re-add precursors if consumed
            if chemSys.molecules.filter({ $0.moleculeType == .methane }).isEmpty {
                chemSys.molecules.append(Molecule(atomIDs: [1, 2, 3, 4, 5], formula: "CH4", moleculeType: .methane))
            }
            if chemSys.molecules.filter({ $0.moleculeType == .ammonia }).isEmpty {
                chemSys.molecules.append(Molecule(atomIDs: [6, 7, 8, 9], formula: "NH3", moleculeType: .ammonia))
            }
            if chemSys.molecules.filter({ $0.moleculeType == .water }).isEmpty {
                chemSys.molecules.append(Molecule(atomIDs: [10, 11, 12], formula: "H2O", moleculeType: .water))
            }
        }
        XCTAssertTrue(produced, "Should eventually synthesize amino acids with precursors and energy")
    }

    func testSynthesizeAminoAcidsNoPrecursors() {
        let chemSys = ChemicalSystem()
        let aas = chemSys.synthesizeAminoAcids(energyInput: 1000.0)
        XCTAssertTrue(aas.isEmpty)
    }
}
