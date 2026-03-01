// ConstantsTests.swift
// Tests for Constants.swift

import XCTest
@testable import InTheBeginningSimulator

final class ConstantsTests: XCTestCase {

    // MARK: - PhysicsConstants

    func testSpeedOfLight() {
        XCTAssertEqual(PhysicsConstants.c, 1.0)
    }

    func testReducedPlanck() {
        XCTAssertEqual(PhysicsConstants.hbar, 0.01)
    }

    func testBoltzmann() {
        XCTAssertEqual(PhysicsConstants.kB, 0.001)
    }

    func testGravitational() {
        XCTAssertEqual(PhysicsConstants.G, 1e-6)
    }

    func testFineStructure() {
        XCTAssertEqual(PhysicsConstants.alpha, 1.0 / 137.0, accuracy: 1e-10)
    }

    func testElementaryCharge() {
        XCTAssertEqual(PhysicsConstants.eCharge, 0.1)
    }

    // MARK: - ParticleMass

    func testElectronMass() {
        XCTAssertEqual(ParticleMass.electron, 1.0)
    }

    func testProtonMass() {
        XCTAssertEqual(ParticleMass.proton, 1836.0)
    }

    func testNeutronMass() {
        XCTAssertEqual(ParticleMass.neutron, 1839.0)
    }

    func testPhotonMassless() {
        XCTAssertEqual(ParticleMass.photon, 0.0)
    }

    func testProtonHeavierThanElectron() {
        XCTAssertGreaterThan(ParticleMass.proton, ParticleMass.electron)
    }

    func testNeutronHeavierThanProton() {
        XCTAssertGreaterThan(ParticleMass.neutron, ParticleMass.proton)
    }

    func testHiggsHeaviest() {
        XCTAssertGreaterThan(ParticleMass.higgs, ParticleMass.wBoson)
        XCTAssertGreaterThan(ParticleMass.higgs, ParticleMass.zBoson)
    }

    // MARK: - ForceCoupling

    func testStrongForceStrongest() {
        XCTAssertEqual(ForceCoupling.strong, 1.0)
        XCTAssertGreaterThan(ForceCoupling.strong, ForceCoupling.electromagnetic)
        XCTAssertGreaterThan(ForceCoupling.electromagnetic, ForceCoupling.weak)
        XCTAssertGreaterThan(ForceCoupling.weak, ForceCoupling.gravity)
    }

    func testElectromagneticIsAlpha() {
        XCTAssertEqual(ForceCoupling.electromagnetic, PhysicsConstants.alpha)
    }

    // MARK: - NuclearParams

    func testNuclearBindingEnergies() {
        XCTAssertGreaterThan(NuclearParams.bindingEnergyHelium4, NuclearParams.bindingEnergyDeuterium)
        XCTAssertGreaterThan(NuclearParams.bindingEnergyCarbon12, NuclearParams.bindingEnergyHelium4)
        XCTAssertGreaterThan(NuclearParams.bindingEnergyIron56, NuclearParams.bindingEnergyCarbon12)
    }

    // MARK: - Epoch

    func testEpochOrdering() {
        let epochs = Epoch.allCases
        for i in 0..<(epochs.count - 1) {
            XCTAssertLessThan(epochs[i], epochs[i + 1],
                "\(epochs[i].displayName) should be before \(epochs[i + 1].displayName)")
        }
    }

    func testEpochCount() {
        XCTAssertEqual(Epoch.allCases.count, 13)
    }

    func testEpochTickMatchesRawValue() {
        for epoch in Epoch.allCases {
            XCTAssertEqual(epoch.tick, epoch.rawValue)
        }
    }

    func testPlanckIsFirst() {
        XCTAssertEqual(Epoch.allCases.first, .planck)
        XCTAssertEqual(Epoch.planck.rawValue, 1)
    }

    func testPresentIsLast() {
        XCTAssertEqual(Epoch.allCases.last, .present)
        XCTAssertEqual(Epoch.present.rawValue, 300_000)
    }

    func testEpochDisplayNames() {
        XCTAssertEqual(Epoch.planck.displayName, "Planck")
        XCTAssertEqual(Epoch.inflation.displayName, "Inflation")
        XCTAssertEqual(Epoch.present.displayName, "Present")
    }

    func testEpochCurrentForTick() {
        XCTAssertEqual(Epoch.current(forTick: 0), .planck)
        XCTAssertEqual(Epoch.current(forTick: 1), .planck)
        XCTAssertEqual(Epoch.current(forTick: 10), .inflation)
        XCTAssertEqual(Epoch.current(forTick: 100), .electroweak)
        XCTAssertEqual(Epoch.current(forTick: 1000), .quark)
        XCTAssertEqual(Epoch.current(forTick: 300_000), .present)
    }

    func testEpochCurrentBetweenTicks() {
        // Between inflation (10) and electroweak (100)
        XCTAssertEqual(Epoch.current(forTick: 50), .inflation)
        // Between quark (1000) and hadron (5000)
        XCTAssertEqual(Epoch.current(forTick: 3000), .quark)
    }

    func testEpochDescriptionNotEmpty() {
        for epoch in Epoch.allCases {
            XCTAssertFalse(epoch.description.isEmpty, "\(epoch.displayName) has empty description")
        }
    }

    func testEpochIconNotEmpty() {
        for epoch in Epoch.allCases {
            XCTAssertFalse(epoch.icon.isEmpty, "\(epoch.displayName) has empty icon")
        }
    }

    func testEpochIdentifiable() {
        for epoch in Epoch.allCases {
            XCTAssertEqual(epoch.id, epoch.rawValue)
        }
    }

    func testEpochComparable() {
        XCTAssertTrue(Epoch.planck < Epoch.inflation)
        XCTAssertTrue(Epoch.inflation < Epoch.present)
        XCTAssertFalse(Epoch.present < Epoch.planck)
    }

    // MARK: - TemperatureScale

    func testPlanckTemperatureHighest() {
        XCTAssertEqual(TemperatureScale.planck, 1e10)
        XCTAssertGreaterThan(TemperatureScale.planck, TemperatureScale.electroweak)
    }

    func testTemperaturesDecrease() {
        XCTAssertGreaterThan(TemperatureScale.planck, TemperatureScale.electroweak)
        XCTAssertGreaterThan(TemperatureScale.electroweak, TemperatureScale.quarkHadron)
        XCTAssertGreaterThan(TemperatureScale.quarkHadron, TemperatureScale.nucleosynthesis)
        XCTAssertGreaterThan(TemperatureScale.nucleosynthesis, TemperatureScale.recombination)
        XCTAssertGreaterThan(TemperatureScale.recombination, TemperatureScale.earthSurface)
        XCTAssertGreaterThan(TemperatureScale.earthSurface, TemperatureScale.cmb)
    }

    func testCMBTemperature() {
        XCTAssertEqual(TemperatureScale.cmb, 2.725)
    }

    func testEarthSurface() {
        XCTAssertEqual(TemperatureScale.earthSurface, 288.0)
    }

    // MARK: - ChemistryParams

    func testElectronShells() {
        XCTAssertEqual(ChemistryParams.electronShells, [2, 8, 18, 32, 32, 18, 8])
    }

    func testBondEnergiesOrdered() {
        XCTAssertGreaterThan(ChemistryParams.bondEnergyIonic, ChemistryParams.bondEnergyCovalent)
        XCTAssertGreaterThan(ChemistryParams.bondEnergyCovalent, ChemistryParams.bondEnergyHydrogen)
        XCTAssertGreaterThan(ChemistryParams.bondEnergyHydrogen, ChemistryParams.bondEnergyVanDerWaals)
    }

    // MARK: - BiologyParams

    func testNucleotideBases() {
        XCTAssertEqual(BiologyParams.nucleotideBases.count, 4)
        XCTAssertTrue(BiologyParams.nucleotideBases.contains("A"))
        XCTAssertTrue(BiologyParams.nucleotideBases.contains("T"))
        XCTAssertTrue(BiologyParams.nucleotideBases.contains("G"))
        XCTAssertTrue(BiologyParams.nucleotideBases.contains("C"))
    }

    func testRNABases() {
        XCTAssertEqual(BiologyParams.rnaBases.count, 4)
        XCTAssertTrue(BiologyParams.rnaBases.contains("U"))
        XCTAssertFalse(BiologyParams.rnaBases.contains("T"))
    }

    func testAminoAcids() {
        XCTAssertEqual(BiologyParams.aminoAcids.count, 20)
        XCTAssertTrue(BiologyParams.aminoAcids.contains("Met"))
        XCTAssertTrue(BiologyParams.aminoAcids.contains("Gly"))
    }

    func testCodonTableHasStartCodon() {
        XCTAssertEqual(BiologyParams.codonTable["AUG"], "Met")
    }

    func testCodonTableHasStopCodons() {
        XCTAssertEqual(BiologyParams.codonTable["UAA"], "STOP")
        XCTAssertEqual(BiologyParams.codonTable["UAG"], "STOP")
        XCTAssertEqual(BiologyParams.codonTable["UGA"], "STOP")
    }

    func testCodonTableNotEmpty() {
        XCTAssertGreaterThan(BiologyParams.codonTable.count, 60)
    }

    // MARK: - EpigeneticParams

    func testMethylationProbability() {
        XCTAssertGreaterThan(EpigeneticParams.methylationProbability, 0.0)
        XCTAssertLessThan(EpigeneticParams.methylationProbability, 1.0)
    }

    func testDemethylationProbability() {
        XCTAssertGreaterThan(EpigeneticParams.demethylationProbability, 0.0)
        XCTAssertLessThan(EpigeneticParams.demethylationProbability, 1.0)
    }

    // MARK: - EnvironmentParams

    func testUVMutationRate() {
        XCTAssertEqual(EnvironmentParams.uvMutationRate, 1e-4)
    }

    func testCosmicRayMutationRate() {
        XCTAssertEqual(EnvironmentParams.cosmicRayMutationRate, 1e-6)
    }

    // MARK: - SimulationLimits

    func testMaxParticlesDefault() {
        XCTAssertEqual(SimulationLimits.maxParticlesDefault, 2000)
    }

    func testMaxCells() {
        XCTAssertEqual(SimulationLimits.maxCells, 100)
    }

    func testPresentEpochLimit() {
        XCTAssertEqual(SimulationLimits.presentEpoch, Epoch.present.tick)
    }

    func testBatteryParticlesLessThanDefault() {
        XCTAssertLessThan(SimulationLimits.maxParticlesBattery, SimulationLimits.maxParticlesDefault)
    }
}
