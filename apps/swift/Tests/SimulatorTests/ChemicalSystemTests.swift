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

    // MARK: - Additional BondType Coverage

    func testBondTypeRawValues() {
        XCTAssertEqual(BondType.covalent.rawValue, "covalent")
        XCTAssertEqual(BondType.ionic.rawValue, "ionic")
        XCTAssertEqual(BondType.polarCovalent.rawValue, "polar_covalent")
        XCTAssertEqual(BondType.hydrogen.rawValue, "hydrogen")
        XCTAssertEqual(BondType.vanDerWaals.rawValue, "van_der_waals")
    }

    // MARK: - Additional MoleculeType Coverage

    func testMoleculeTypeDisplayNameAll() {
        XCTAssertEqual(MoleculeType.carbonDioxide.displayName, "Carbon Dioxide")
        XCTAssertEqual(MoleculeType.ammonia.displayName, "Ammonia")
        XCTAssertEqual(MoleculeType.hydrogenCyanide.displayName, "Hydrogen Cyanide")
        XCTAssertEqual(MoleculeType.formaldehyde.displayName, "Formaldehyde")
        XCTAssertEqual(MoleculeType.aminoAcid.displayName, "Amino Acid")
        XCTAssertEqual(MoleculeType.nucleotide.displayName, "Nucleotide")
        XCTAssertEqual(MoleculeType.phospholipid.displayName, "Phospholipid")
        XCTAssertEqual(MoleculeType.genericOrganic.displayName, "Organic Molecule")
        XCTAssertEqual(MoleculeType.genericInorganic.displayName, "Inorganic Molecule")
    }

    func testMoleculeTypeRawValues() {
        XCTAssertEqual(MoleculeType.water.rawValue, "H2O")
        XCTAssertEqual(MoleculeType.carbonDioxide.rawValue, "CO2")
        XCTAssertEqual(MoleculeType.methane.rawValue, "CH4")
        XCTAssertEqual(MoleculeType.ammonia.rawValue, "NH3")
        XCTAssertEqual(MoleculeType.hydrogenCyanide.rawValue, "HCN")
        XCTAssertEqual(MoleculeType.formaldehyde.rawValue, "CH2O")
        XCTAssertEqual(MoleculeType.aminoAcid.rawValue, "amino_acid")
        XCTAssertEqual(MoleculeType.nucleotide.rawValue, "nucleotide")
        XCTAssertEqual(MoleculeType.phospholipid.rawValue, "phospholipid")
        XCTAssertEqual(MoleculeType.genericOrganic.rawValue, "organic")
        XCTAssertEqual(MoleculeType.genericInorganic.rawValue, "inorganic")
    }

    func testMoleculeTypeDisplayColorAllTypes() {
        for mType in MoleculeType.allCases {
            let color = mType.displayColor
            XCTAssertGreaterThanOrEqual(color.x, 0.0)
            XCTAssertLessThanOrEqual(color.x, 1.0)
            XCTAssertGreaterThanOrEqual(color.y, 0.0)
            XCTAssertLessThanOrEqual(color.y, 1.0)
            XCTAssertGreaterThanOrEqual(color.z, 0.0)
            XCTAssertLessThanOrEqual(color.z, 1.0)
            XCTAssertGreaterThan(color.w, 0.0)
        }
    }

    // MARK: - Additional Molecule Coverage

    func testMoleculeDisplayColorFromType() {
        let water = Molecule(atomIDs: [1, 2, 3], formula: "H2O", moleculeType: .water)
        XCTAssertEqual(water.displayColor, MoleculeType.water.displayColor)
    }

    func testMoleculeCustomProperties() {
        let mol = Molecule(
            atomIDs: [1, 2],
            formula: "XY",
            moleculeType: .genericInorganic,
            position: SIMD3<Double>(1, 2, 3),
            velocity: SIMD3<Double>(0.1, 0.2, 0.3),
            energy: 5.0,
            isStable: false
        )
        XCTAssertEqual(mol.position, SIMD3<Double>(1, 2, 3))
        XCTAssertEqual(mol.velocity, SIMD3<Double>(0.1, 0.2, 0.3))
        XCTAssertEqual(mol.energy, 5.0)
        XCTAssertFalse(mol.isStable)
    }

    // MARK: - Nucleotide Synthesis Coverage

    func testSynthesizeNucleotidesWithPrecursors() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        chemSys.catalystPresent = true
        // Need 2+ organics and 1+ water
        var produced = false
        for _ in 0..<300 {
            // Reset precursors
            let organic1 = Molecule(atomIDs: [1, 2, 3, 4, 5], formula: "CH4", moleculeType: .methane)
            let organic2 = Molecule(atomIDs: [6, 7, 8, 9, 10], formula: "CH2O", moleculeType: .formaldehyde)
            let water = Molecule(atomIDs: [11, 12, 13], formula: "H2O", moleculeType: .water)
            chemSys.molecules.append(contentsOf: [organic1, organic2, water])

            let nucs = chemSys.synthesizeNucleotides(energyInput: 5000.0)
            if !nucs.isEmpty {
                produced = true
                break
            }
        }
        XCTAssertTrue(produced, "Should eventually synthesize nucleotides with organics and energy")
    }

    func testSynthesizeNucleotidesNoPrecursors() {
        let chemSys = ChemicalSystem()
        let nucs = chemSys.synthesizeNucleotides(energyInput: 5000.0)
        XCTAssertTrue(nucs.isEmpty)
    }

    func testSynthesizeNucleotidesInsufficientOrganics() {
        let chemSys = ChemicalSystem()
        let organic1 = Molecule(atomIDs: [1], formula: "CH4", moleculeType: .methane)
        let water = Molecule(atomIDs: [2], formula: "H2O", moleculeType: .water)
        chemSys.molecules.append(contentsOf: [organic1, water])
        let nucs = chemSys.synthesizeNucleotides(energyInput: 5000.0)
        XCTAssertTrue(nucs.isEmpty, "Should not synthesize with only 1 organic")
    }

    // MARK: - Phospholipid Synthesis Coverage

    func testSynthesizePhospholipidsWithPrecursors() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        chemSys.catalystPresent = true
        var produced = false
        for _ in 0..<300 {
            let aa1 = Molecule(atomIDs: [1, 2], formula: "Gly", moleculeType: .aminoAcid)
            let aa2 = Molecule(atomIDs: [3, 4], formula: "Ala", moleculeType: .aminoAcid)
            let water = Molecule(atomIDs: [5, 6, 7], formula: "H2O", moleculeType: .water)
            chemSys.molecules.append(contentsOf: [aa1, aa2, water])

            let pls = chemSys.synthesizePhospholipids()
            if !pls.isEmpty {
                produced = true
                break
            }
        }
        XCTAssertTrue(produced, "Should eventually synthesize phospholipids with catalyst")
    }

    func testSynthesizePhospholipidsNoPrecursors() {
        let chemSys = ChemicalSystem()
        let pls = chemSys.synthesizePhospholipids()
        XCTAssertTrue(pls.isEmpty)
    }

    func testSynthesizePhospholipidsInsufficientOrganics() {
        let chemSys = ChemicalSystem()
        let aa1 = Molecule(atomIDs: [1], formula: "Gly", moleculeType: .aminoAcid)
        let water = Molecule(atomIDs: [2], formula: "H2O", moleculeType: .water)
        chemSys.molecules.append(contentsOf: [aa1, water])
        let pls = chemSys.synthesizePhospholipids()
        XCTAssertTrue(pls.isEmpty)
    }

    // MARK: - Thermal Decomposition Coverage

    func testThermalDecompositionAboveThreshold() {
        let chemSys = ChemicalSystem(temperature: 5000.0) // Very high temp
        for _ in 0..<20 {
            let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .genericOrganic, isStable: false)
            chemSys.molecules.append(mol)
        }
        var totalDecomposed = 0
        for _ in 0..<100 {
            totalDecomposed += chemSys.thermalDecomposition()
            if totalDecomposed > 0 { break }
            // Re-add molecules if all decomposed
            if chemSys.molecules.isEmpty {
                for _ in 0..<20 {
                    chemSys.molecules.append(Molecule(atomIDs: [1], formula: "X", moleculeType: .genericOrganic, isStable: false))
                }
            }
        }
        XCTAssertGreaterThan(totalDecomposed, 0, "High temperature should decompose unstable molecules")
    }

    func testThermalDecompositionStableMolecules() {
        let chemSys = ChemicalSystem(temperature: 600.0) // Just above threshold
        let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .genericInorganic,
                          bonds: [Bond(atomA: 1, atomB: 2, type: .covalent, energy: 100.0)],
                          isStable: true)
        chemSys.molecules.append(mol)
        // May or may not decompose - just verify no crash
        let _ = chemSys.thermalDecomposition()
    }

    // MARK: - Evolve Coverage

    func testEvolveStabilityCheck() {
        let chemSys = ChemicalSystem(temperature: 600.0)
        let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .genericOrganic,
                          velocity: SIMD3<Double>(1, 0, 0),
                          isStable: true)
        chemSys.molecules.append(mol)
        chemSys.evolve(dt: 1.0)
        // At 600 > 500, stability depends on bondEnergy vs temperature * kB
        // With 0 bonds, bondEnergy = 0, so molecule should become unstable
        XCTAssertFalse(mol.isStable)
    }

    func testEvolvePositionUpdate() {
        let chemSys = ChemicalSystem(temperature: 0.001) // Very low temp for minimal Brownian motion
        let mol = Molecule(atomIDs: [1], formula: "X", moleculeType: .water,
                          velocity: SIMD3<Double>(10, 0, 0))
        chemSys.molecules.append(mol)
        chemSys.evolve(dt: 1.0)
        // Position should have moved approximately 10 units in x
        XCTAssertGreaterThan(mol.position.x, 5.0)
    }

    // MARK: - Statistics Additional Coverage

    func testMoleculeCountsEmpty() {
        let chemSys = ChemicalSystem()
        let counts = chemSys.moleculeCounts()
        XCTAssertTrue(counts.isEmpty)
    }

    func testMoleculeCountsMultipleSameType() {
        let chemSys = ChemicalSystem()
        chemSys.molecules.append(Molecule(atomIDs: [1], formula: "H2O", moleculeType: .water))
        chemSys.molecules.append(Molecule(atomIDs: [2], formula: "H2O", moleculeType: .water))
        chemSys.molecules.append(Molecule(atomIDs: [3], formula: "H2O", moleculeType: .water))
        let counts = chemSys.moleculeCounts()
        XCTAssertEqual(counts["H2O"], 3)
    }

    func testOrganicCountIncludesAllOrganicTypes() {
        let chemSys = ChemicalSystem()
        chemSys.molecules.append(Molecule(atomIDs: [1], formula: "CH4", moleculeType: .methane))
        chemSys.molecules.append(Molecule(atomIDs: [2], formula: "HCN", moleculeType: .hydrogenCyanide))
        chemSys.molecules.append(Molecule(atomIDs: [3], formula: "CH2O", moleculeType: .formaldehyde))
        chemSys.molecules.append(Molecule(atomIDs: [4], formula: "nuc", moleculeType: .nucleotide))
        chemSys.molecules.append(Molecule(atomIDs: [5], formula: "pl", moleculeType: .phospholipid))
        chemSys.molecules.append(Molecule(atomIDs: [6], formula: "org", moleculeType: .genericOrganic))
        XCTAssertEqual(chemSys.organicCount, 6)
    }

    // MARK: - Amino Acid Synthesis Additional Coverage

    func testSynthesizeAminoAcidsWithCatalyst() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        chemSys.catalystPresent = true
        var produced = false
        for _ in 0..<200 {
            let methane = Molecule(atomIDs: [1, 2, 3, 4, 5], formula: "CH4", moleculeType: .methane)
            let ammonia = Molecule(atomIDs: [6, 7, 8, 9], formula: "NH3", moleculeType: .ammonia)
            let water = Molecule(atomIDs: [10, 11, 12], formula: "H2O", moleculeType: .water)
            chemSys.molecules.append(contentsOf: [methane, ammonia, water])

            let aas = chemSys.synthesizeAminoAcids(energyInput: 500.0)
            if !aas.isEmpty {
                produced = true
                XCTAssertEqual(aas.first?.moleculeType, .aminoAcid)
                break
            }
        }
        XCTAssertTrue(produced, "Catalyst should boost amino acid synthesis")
    }

    func testSynthesizeAminoAcidsConsumesReactants() {
        let chemSys = ChemicalSystem(temperature: 300.0)
        let methane = Molecule(atomIDs: [1], formula: "CH4", moleculeType: .methane)
        let ammonia = Molecule(atomIDs: [2], formula: "NH3", moleculeType: .ammonia)
        let water = Molecule(atomIDs: [3], formula: "H2O", moleculeType: .water)
        chemSys.molecules.append(contentsOf: [methane, ammonia, water])

        // With very high energy, synthesis probability approaches 0.05
        var consumed = false
        for _ in 0..<300 {
            let aas = chemSys.synthesizeAminoAcids(energyInput: 10000.0)
            if !aas.isEmpty {
                consumed = true
                break
            }
            // Re-add if molecules were consumed
            if chemSys.molecules.filter({ $0.moleculeType == .methane }).isEmpty {
                chemSys.molecules.append(Molecule(atomIDs: [1], formula: "CH4", moleculeType: .methane))
                chemSys.molecules.append(Molecule(atomIDs: [2], formula: "NH3", moleculeType: .ammonia))
                chemSys.molecules.append(Molecule(atomIDs: [3], formula: "H2O", moleculeType: .water))
            }
        }
        if consumed {
            XCTAssertGreaterThan(chemSys.totalReactions, 0)
        }
    }

    func testSynthesizeAminoAcidStability() {
        let chemSys = ChemicalSystem(temperature: 300.0) // Below 400.0
        chemSys.catalystPresent = true
        var produced = false
        for _ in 0..<300 {
            let methane = Molecule(atomIDs: [1, 2, 3, 4, 5], formula: "CH4", moleculeType: .methane)
            let ammonia = Molecule(atomIDs: [6, 7, 8, 9], formula: "NH3", moleculeType: .ammonia)
            let water = Molecule(atomIDs: [10, 11, 12], formula: "H2O", moleculeType: .water)
            chemSys.molecules.append(contentsOf: [methane, ammonia, water])

            let aas = chemSys.synthesizeAminoAcids(energyInput: 1000.0)
            if let aa = aas.first {
                XCTAssertTrue(aa.isStable, "Amino acid should be stable below 400K")
                produced = true
                break
            }
        }
    }

    // MARK: - Form Water Additional Coverage

    func testFormWaterMultiple() {
        let atomSys = AtomicSystem()
        for _ in 0..<6 {
            atomSys.atoms.append(Atom(atomicNumber: 1, massNumber: 1))
        }
        for _ in 0..<3 {
            atomSys.atoms.append(Atom(atomicNumber: 8, massNumber: 16))
        }

        let chemSys = ChemicalSystem()
        let water = chemSys.formWater(atomicSystem: atomSys)
        XCTAssertEqual(water.count, 3)
        XCTAssertEqual(chemSys.waterCount, 3)
    }

    func testFormWaterBondProperties() {
        let atomSys = AtomicSystem()
        let h1 = Atom(atomicNumber: 1, massNumber: 1)
        let h2 = Atom(atomicNumber: 1, massNumber: 1)
        let o = Atom(atomicNumber: 8, massNumber: 16)
        atomSys.atoms.append(contentsOf: [h1, h2, o])

        let chemSys = ChemicalSystem()
        let water = chemSys.formWater(atomicSystem: atomSys)
        if let w = water.first {
            XCTAssertEqual(w.bonds.count, 2)
            XCTAssertEqual(w.bonds[0].type, .polarCovalent)
            XCTAssertEqual(w.bonds[1].type, .polarCovalent)
            XCTAssertEqual(w.atomIDs.count, 3)
        }
    }

    // MARK: - pH Coverage

    func testChemicalSystempH() {
        let chemSys = ChemicalSystem()
        XCTAssertEqual(chemSys.pH, 7.0)
        chemSys.pH = 3.0
        XCTAssertEqual(chemSys.pH, 3.0)
    }
}
