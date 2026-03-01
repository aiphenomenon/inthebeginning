// EnvironmentTests.swift
// Tests for Environment.swift

import XCTest
@testable import InTheBeginningSimulator

final class EnvironmentTests: XCTestCase {

    // MARK: - RadiationType

    func testRadiationTypeAllCases() {
        XCTAssertEqual(RadiationType.allCases.count, 7)
    }

    func testRadiationTypeEnergy() {
        XCTAssertGreaterThan(RadiationType.gammaRay.energy, RadiationType.xRay.energy)
        XCTAssertGreaterThan(RadiationType.xRay.energy, RadiationType.ultraviolet.energy)
        XCTAssertGreaterThan(RadiationType.ultraviolet.energy, RadiationType.visible.energy)
        XCTAssertGreaterThan(RadiationType.visible.energy, RadiationType.infrared.energy)
        XCTAssertGreaterThan(RadiationType.infrared.energy, RadiationType.microwave.energy)
        XCTAssertGreaterThan(RadiationType.microwave.energy, RadiationType.radio.energy)
    }

    func testRadiationTypeMutagenicPotential() {
        XCTAssertEqual(RadiationType.gammaRay.mutagenicPotential, 1.0)
        XCTAssertGreaterThan(RadiationType.gammaRay.mutagenicPotential, RadiationType.xRay.mutagenicPotential)
        XCTAssertGreaterThan(RadiationType.xRay.mutagenicPotential, RadiationType.ultraviolet.mutagenicPotential)
        XCTAssertEqual(RadiationType.visible.mutagenicPotential, 0.0)
        XCTAssertEqual(RadiationType.infrared.mutagenicPotential, 0.0)
        XCTAssertEqual(RadiationType.radio.mutagenicPotential, 0.0)
    }

    // MARK: - AtmosphericGas

    func testAtmosphericGasGreenhouse() {
        let co2 = AtmosphericGas(name: "CO2", molecularWeight: 44.0, fraction: 0.04)
        XCTAssertTrue(co2.isGreenhouse)

        let ch4 = AtmosphericGas(name: "CH4", molecularWeight: 16.0, fraction: 0.01)
        XCTAssertTrue(ch4.isGreenhouse)

        let h2o = AtmosphericGas(name: "H2O", molecularWeight: 18.0, fraction: 0.01)
        XCTAssertTrue(h2o.isGreenhouse)

        let n2 = AtmosphericGas(name: "N2", molecularWeight: 28.0, fraction: 0.78)
        XCTAssertFalse(n2.isGreenhouse)

        let o2 = AtmosphericGas(name: "O2", molecularWeight: 32.0, fraction: 0.21)
        XCTAssertFalse(o2.isGreenhouse)
    }

    // MARK: - Atmosphere

    func testAtmosphereInit() {
        let atm = Atmosphere()
        XCTAssertEqual(atm.pressure, 1.0)
        XCTAssertEqual(atm.ozoneLayerStrength, 0.0)
        XCTAssertFalse(atm.gases.isEmpty)
    }

    func testAtmosphereFractionLookup() {
        let atm = Atmosphere()
        XCTAssertEqual(atm.fraction(of: "CO2"), 0.5)
        XCTAssertEqual(atm.fraction(of: "H2O"), 0.3)
        XCTAssertEqual(atm.fraction(of: "CH4"), 0.1)
        XCTAssertEqual(atm.fraction(of: "nonexistent"), 0.0)
    }

    func testAtmosphereSetFraction() {
        var atm = Atmosphere()
        atm.setFraction(of: "O2", to: 0.21)
        XCTAssertEqual(atm.fraction(of: "O2"), 0.21)
    }

    func testAtmosphereSetFractionClamped() {
        var atm = Atmosphere()
        atm.setFraction(of: "O2", to: 5.0)
        XCTAssertEqual(atm.fraction(of: "O2"), 1.0)

        atm.setFraction(of: "O2", to: -1.0)
        XCTAssertEqual(atm.fraction(of: "O2"), 0.0)
    }

    func testAtmosphereGreenhouseEffect() {
        let atm = Atmosphere()
        // CO2=0.5, CH4=0.1, H2O=0.3 -> all greenhouse
        XCTAssertGreaterThan(atm.greenhouseEffect, 0.0)
    }

    func testAtmosphereUVTransmission() {
        var atm = Atmosphere()
        XCTAssertEqual(atm.uvTransmission, 1.0) // No ozone

        atm.ozoneLayerStrength = 0.5
        XCTAssertEqual(atm.uvTransmission, 0.5, accuracy: 1e-10)

        atm.ozoneLayerStrength = 1.0
        XCTAssertEqual(atm.uvTransmission, 0.0, accuracy: 1e-10)
    }

    func testAtmosphereEvolveWithoutLife() {
        var atm = Atmosphere()
        let initialCO2 = atm.fraction(of: "CO2")
        atm.evolve(hasLife: false, tick: 1000)
        // CO2 should decrease (geological weathering)
        XCTAssertLessThan(atm.fraction(of: "CO2"), initialCO2)
        // N2 should increase
    }

    func testAtmosphereEvolveWithLife() {
        var atm = Atmosphere()
        let initialO2 = atm.fraction(of: "O2")
        atm.evolve(hasLife: true, tick: 1000)
        // O2 should increase (photosynthesis)
        XCTAssertGreaterThan(atm.fraction(of: "O2"), initialO2)
        // Ozone should build up from O2
        XCTAssertGreaterThan(atm.ozoneLayerStrength, 0.0)
    }

    func testAtmosphereEvolveMethanDecreases() {
        var atm = Atmosphere()
        let initialCH4 = atm.fraction(of: "CH4")
        atm.evolve(hasLife: false, tick: 1000)
        XCTAssertLessThan(atm.fraction(of: "CH4"), initialCH4)
    }

    // MARK: - RadiationField

    func testRadiationFieldInit() {
        let field = RadiationField()
        XCTAssertEqual(field.totalIntensity, 0.0)
        XCTAssertEqual(field.mutagenicIntensity, 0.0)
    }

    func testRadiationFieldSetIntensity() {
        var field = RadiationField()
        field.setIntensity(.gammaRay, 100.0)
        XCTAssertEqual(field.intensities[.gammaRay], 100.0)
    }

    func testRadiationFieldSetIntensityClamped() {
        var field = RadiationField()
        field.setIntensity(.gammaRay, -10.0)
        XCTAssertEqual(field.intensities[.gammaRay], 0.0)
    }

    func testRadiationFieldTotalIntensity() {
        var field = RadiationField()
        field.setIntensity(.visible, 10.0)
        field.setIntensity(.infrared, 5.0)
        XCTAssertEqual(field.totalIntensity, 15.0, accuracy: 1e-10)
    }

    func testRadiationFieldMutagenicIntensity() {
        var field = RadiationField()
        field.setIntensity(.gammaRay, 10.0)
        // gammaRay mutagenic potential = 1.0
        XCTAssertEqual(field.mutagenicIntensity, 10.0, accuracy: 1e-10)
    }

    func testRadiationFieldMutagenicExcludesNonMutagenic() {
        var field = RadiationField()
        field.setIntensity(.visible, 100.0) // mutagenic potential = 0
        XCTAssertEqual(field.mutagenicIntensity, 0.0, accuracy: 1e-10)
    }

    func testRadiationFieldEvolvePlanck() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .planck, atmosphere: atm)
        XCTAssertGreaterThan(field.intensities[.gammaRay] ?? 0, 0)
        XCTAssertGreaterThan(field.totalIntensity, 0)
    }

    func testRadiationFieldEvolvePresent() {
        var field = RadiationField()
        var atm = Atmosphere()
        atm.ozoneLayerStrength = 0.8
        field.evolve(epoch: .present, atmosphere: atm)
        // UV should be reduced by ozone
        let uv = field.intensities[.ultraviolet] ?? 0
        XCTAssertGreaterThan(uv, 0)
        // Visible light should be strong
        let visible = field.intensities[.visible] ?? 0
        XCTAssertGreaterThan(visible, uv)
    }

    func testRadiationFieldEvolveEarlyVsLateEpoch() {
        var fieldEarly = RadiationField()
        var fieldLate = RadiationField()
        let atm = Atmosphere()
        fieldEarly.evolve(epoch: .planck, atmosphere: atm)
        fieldLate.evolve(epoch: .present, atmosphere: atm)
        // Early universe should have much more gamma radiation
        XCTAssertGreaterThan(fieldEarly.intensities[.gammaRay] ?? 0,
                             fieldLate.intensities[.gammaRay] ?? 0)
    }

    // MARK: - Environment

    func testEnvironmentInit() {
        let env = Environment()
        XCTAssertEqual(env.temperature, TemperatureScale.planck)
        XCTAssertFalse(env.hasLiquidWater)
        XCTAssertFalse(env.hasMagneticField)
        XCTAssertEqual(env.tectonicActivity, 0.0)
        XCTAssertEqual(env.oceanCoverage, 0.0)
        XCTAssertEqual(env.currentEpoch, .planck)
    }

    func testEnvironmentCustomTemp() {
        let env = Environment(temperature: 300.0)
        XCTAssertEqual(env.temperature, 300.0)
    }

    func testTemperatureForEpoch() {
        let env = Environment()
        XCTAssertEqual(env.temperatureForEpoch(.planck), TemperatureScale.planck)
        XCTAssertEqual(env.temperatureForEpoch(.recombination), TemperatureScale.recombination)
        XCTAssertEqual(env.temperatureForEpoch(.present), TemperatureScale.earthSurface)
    }

    func testTemperatureDecreasesThroughEpochs() {
        let env = Environment()
        var prevTemp = env.temperatureForEpoch(.planck)
        for epoch in Epoch.allCases.dropFirst() {
            let temp = env.temperatureForEpoch(epoch)
            // Temperature generally decreases (star formation has an exception)
            if epoch == .starFormation || epoch == .solarSystem || epoch == .earth || epoch == .life {
                // These are planetary-scale temperatures, not cosmic
                continue
            }
            if epoch.rawValue <= Epoch.recombination.rawValue {
                XCTAssertLessThan(temp, prevTemp,
                    "Temperature should decrease from \(prevTemp) at previous epoch to \(temp) at \(epoch.displayName)")
            }
            prevTemp = temp
        }
    }

    func testUpdatePlanckEpoch() {
        let env = Environment()
        env.update(epoch: .planck, tick: 1)
        XCTAssertEqual(env.currentEpoch, .planck)
        XCTAssertFalse(env.hasLiquidWater)
        XCTAssertFalse(env.hasMagneticField)
    }

    func testUpdateEarthEpoch() {
        let env = Environment()
        env.update(epoch: .earth, tick: Epoch.earth.tick)
        XCTAssertEqual(env.currentEpoch, .earth)
        XCTAssertTrue(env.hasMagneticField)
        // Temperature near Earth surface -> may have liquid water
        let temp = env.temperature
        if temp > 273.0 && temp < 373.0 {
            XCTAssertTrue(env.hasLiquidWater)
        }
    }

    func testUpdateLifeEpoch() {
        let env = Environment()
        env.update(epoch: .life, tick: Epoch.life.tick)
        XCTAssertEqual(env.currentEpoch, .life)
        XCTAssertTrue(env.hasMagneticField)
    }

    func testBioavailableEnergyRequiresWater() {
        let env = Environment(temperature: 300.0)
        env.hasLiquidWater = false
        XCTAssertEqual(env.bioavailableEnergy, 0.0)

        env.hasLiquidWater = true
        env.tectonicActivity = 0.5
        // Even without radiation, tectonic activity provides energy
        XCTAssertGreaterThan(env.bioavailableEnergy, 0.0)
    }

    func testBioavailableEnergyFromRadiation() {
        let env = Environment(temperature: 300.0)
        env.hasLiquidWater = true
        env.radiationField.setIntensity(.visible, 30.0)
        XCTAssertGreaterThanOrEqual(env.bioavailableEnergy, 30.0)
    }

    func testEnvironmentalMutationRate() {
        let env = Environment()
        XCTAssertGreaterThan(env.environmentalMutationRate, 0.0)
    }

    func testEnvironmentalMutationRateWithUV() {
        let env = Environment()
        let baseMutRate = env.environmentalMutationRate

        env.radiationField.setIntensity(.ultraviolet, 100.0)
        let uvMutRate = env.environmentalMutationRate
        XCTAssertGreaterThan(uvMutRate, baseMutRate)
    }

    func testEnvironmentalMutationRateCapped() {
        let env = Environment()
        env.radiationField.setIntensity(.gammaRay, 1e10)
        env.radiationField.setIntensity(.ultraviolet, 1e10)
        XCTAssertLessThanOrEqual(env.environmentalMutationRate, 0.1)
    }

    func testHabitabilityScorePlanck() {
        let env = Environment(temperature: TemperatureScale.planck)
        XCTAssertEqual(env.habitabilityScore, 0.0, accuracy: 0.01)
    }

    func testHabitabilityScoreEarthLike() {
        let env = Environment(temperature: 288.0) // Optimal temp
        env.hasLiquidWater = true
        env.hasMagneticField = true
        env.radiationField.setIntensity(.ultraviolet, 2.0)
        XCTAssertGreaterThan(env.habitabilityScore, 0.5)
    }

    func testHabitabilityScoreComponents() {
        let env = Environment(temperature: 288.0)
        let base = env.habitabilityScore

        env.hasLiquidWater = true
        let withWater = env.habitabilityScore
        XCTAssertGreaterThan(withWater, base)

        env.hasMagneticField = true
        let withMagnetic = env.habitabilityScore
        XCTAssertGreaterThan(withMagnetic, withWater)
    }

    func testHabitabilityScoreCapped() {
        let env = Environment(temperature: 288.0)
        env.hasLiquidWater = true
        env.hasMagneticField = true
        env.radiationField.setIntensity(.ultraviolet, 2.0)
        XCTAssertLessThanOrEqual(env.habitabilityScore, 1.0)
    }

    func testAtmosphereDescription() {
        let env = Environment()
        let desc = env.atmosphereDescription
        XCTAssertFalse(desc.isEmpty)
        XCTAssertTrue(desc.contains("CO2"))
    }

    func testOceanCoverageGrows() {
        let env = Environment()
        env.update(epoch: .earth, tick: Epoch.earth.tick)
        let coverage1 = env.oceanCoverage
        env.update(epoch: .earth, tick: Epoch.earth.tick + 100)
        let coverage2 = env.oceanCoverage
        XCTAssertGreaterThanOrEqual(coverage2, coverage1)
    }

    // MARK: - Additional RadiationType Coverage

    func testRadiationTypeRawValues() {
        XCTAssertEqual(RadiationType.gammaRay.rawValue, "gamma")
        XCTAssertEqual(RadiationType.xRay.rawValue, "xray")
        XCTAssertEqual(RadiationType.ultraviolet.rawValue, "uv")
        XCTAssertEqual(RadiationType.visible.rawValue, "visible")
        XCTAssertEqual(RadiationType.infrared.rawValue, "infrared")
        XCTAssertEqual(RadiationType.microwave.rawValue, "microwave")
        XCTAssertEqual(RadiationType.radio.rawValue, "radio")
    }

    func testRadiationTypeDisplayColorAllTypes() {
        for rType in RadiationType.allCases {
            let color = rType.displayColor
            XCTAssertGreaterThanOrEqual(color.x, 0.0)
            XCTAssertLessThanOrEqual(color.x, 1.0)
            XCTAssertGreaterThanOrEqual(color.y, 0.0)
            XCTAssertLessThanOrEqual(color.y, 1.0)
            XCTAssertGreaterThanOrEqual(color.z, 0.0)
            XCTAssertLessThanOrEqual(color.z, 1.0)
            XCTAssertGreaterThan(color.w, 0.0)
        }
    }

    func testRadiationTypeEnergyValues() {
        XCTAssertEqual(RadiationType.gammaRay.energy, 1e6)
        XCTAssertEqual(RadiationType.xRay.energy, 1e4)
        XCTAssertEqual(RadiationType.ultraviolet.energy, 100.0)
        XCTAssertEqual(RadiationType.visible.energy, 2.0)
        XCTAssertEqual(RadiationType.infrared.energy, 0.1)
        XCTAssertEqual(RadiationType.microwave.energy, 0.001)
        XCTAssertEqual(RadiationType.radio.energy, 1e-6)
    }

    func testRadiationTypeMutagenicPotentialValues() {
        XCTAssertEqual(RadiationType.gammaRay.mutagenicPotential, 1.0)
        XCTAssertEqual(RadiationType.xRay.mutagenicPotential, 0.8)
        XCTAssertEqual(RadiationType.ultraviolet.mutagenicPotential, 0.3)
        XCTAssertEqual(RadiationType.visible.mutagenicPotential, 0.0)
        XCTAssertEqual(RadiationType.infrared.mutagenicPotential, 0.0)
        XCTAssertEqual(RadiationType.microwave.mutagenicPotential, 0.0)
        XCTAssertEqual(RadiationType.radio.mutagenicPotential, 0.0)
    }

    // MARK: - Additional AtmosphericGas Coverage

    func testAtmosphericGasProperties() {
        let gas = AtmosphericGas(name: "He", molecularWeight: 4.0, fraction: 0.01)
        XCTAssertEqual(gas.name, "He")
        XCTAssertEqual(gas.molecularWeight, 4.0)
        XCTAssertEqual(gas.fraction, 0.01)
        XCTAssertFalse(gas.isGreenhouse)
    }

    func testAtmosphericGasH2OIsGreenhouse() {
        let h2o = AtmosphericGas(name: "H2O", molecularWeight: 18.0, fraction: 0.01)
        XCTAssertTrue(h2o.isGreenhouse)
    }

    // MARK: - Additional Atmosphere Coverage

    func testAtmosphereGasCount() {
        let atm = Atmosphere()
        XCTAssertEqual(atm.gases.count, 7)
    }

    func testAtmosphereSetFractionNonExistent() {
        var atm = Atmosphere()
        atm.setFraction(of: "Xe", to: 0.01)
        // Should not crash; non-existent gas is simply not found
        XCTAssertEqual(atm.fraction(of: "Xe"), 0.0)
    }

    func testAtmosphereGreenhouseEffectValue() {
        let atm = Atmosphere()
        // CO2=0.5, CH4=0.1, H2O=0.3 are greenhouse gases
        // greenhouse = (0.5 + 0.1 + 0.3) * 2.0 = 1.8
        XCTAssertEqual(atm.greenhouseEffect, 1.8, accuracy: 0.01)
    }

    func testAtmosphereEvolveN2Increase() {
        var atm = Atmosphere()
        let initialN2 = atm.fraction(of: "N2")
        atm.evolve(hasLife: false, tick: 1000)
        XCTAssertGreaterThan(atm.fraction(of: "N2"), initialN2)
    }

    func testAtmosphereEvolveOzoneFromO2() {
        var atm = Atmosphere()
        atm.setFraction(of: "O2", to: 0.1)
        atm.evolve(hasLife: true, tick: 1000)
        // Ozone = min(1.0, O2_fraction * 3.0)
        XCTAssertGreaterThan(atm.ozoneLayerStrength, 0.0)
    }

    // MARK: - Additional RadiationField Coverage

    func testRadiationFieldEvolveQuarkEpoch() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .quark, atmosphere: atm)
        XCTAssertEqual(field.intensities[.gammaRay], 1e4)
        XCTAssertEqual(field.intensities[.xRay], 1e3)
        XCTAssertEqual(field.intensities[.ultraviolet], 1e2)
    }

    func testRadiationFieldEvolveHadronEpoch() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .hadron, atmosphere: atm)
        XCTAssertEqual(field.intensities[.gammaRay], 1e4)
    }

    func testRadiationFieldEvolveNucleosynthesis() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .nucleosynthesis, atmosphere: atm)
        XCTAssertEqual(field.intensities[.gammaRay], 100.0)
        XCTAssertEqual(field.intensities[.xRay], 50.0)
        XCTAssertEqual(field.intensities[.visible], 5.0)
    }

    func testRadiationFieldEvolveRecombination() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .recombination, atmosphere: atm)
        // CMB photons dominate
        XCTAssertEqual(field.intensities[.microwave], 10.0)
        XCTAssertEqual(field.intensities[.visible], 2.0)
        XCTAssertEqual(field.intensities[.gammaRay], 0.1)
    }

    func testRadiationFieldEvolveStarFormation() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .starFormation, atmosphere: atm)
        XCTAssertEqual(field.intensities[.visible], 20.0)
        XCTAssertEqual(field.intensities[.infrared], 15.0)
    }

    func testRadiationFieldEvolveSolarSystem() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .solarSystem, atmosphere: atm)
        XCTAssertEqual(field.intensities[.visible], 30.0)
        XCTAssertEqual(field.intensities[.infrared], 20.0)
    }

    func testRadiationFieldEvolveEarth() {
        var field = RadiationField()
        var atm = Atmosphere()
        atm.ozoneLayerStrength = 0.5
        field.evolve(epoch: .earth, atmosphere: atm)
        // UV should be reduced by atmosphere
        let uv = field.intensities[.ultraviolet] ?? 0
        XCTAssertEqual(uv, 5.0 * 0.5, accuracy: 0.01)
    }

    func testRadiationFieldEvolveLifeEpoch() {
        var field = RadiationField()
        var atm = Atmosphere()
        atm.ozoneLayerStrength = 0.8
        field.evolve(epoch: .life, atmosphere: atm)
        let uv = field.intensities[.ultraviolet] ?? 0
        XCTAssertEqual(uv, 2.0 * 0.2, accuracy: 0.01)
        XCTAssertEqual(field.intensities[.visible], 30.0)
    }

    func testRadiationFieldEvolveDNAEpoch() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .dna, atmosphere: atm)
        XCTAssertEqual(field.intensities[.visible], 30.0)
        XCTAssertEqual(field.intensities[.infrared], 25.0)
    }

    func testRadiationFieldEvolveInflation() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .inflation, atmosphere: atm)
        XCTAssertEqual(field.intensities[.gammaRay], 1e6)
    }

    func testRadiationFieldEvolveElectroweak() {
        var field = RadiationField()
        let atm = Atmosphere()
        field.evolve(epoch: .electroweak, atmosphere: atm)
        XCTAssertEqual(field.intensities[.gammaRay], 1e6)
        XCTAssertEqual(field.intensities[.xRay], 1e5)
    }

    // MARK: - Additional Environment Coverage

    func testUpdateSolarSystemEpoch() {
        let env = Environment()
        env.update(epoch: .solarSystem, tick: Epoch.solarSystem.tick)
        XCTAssertEqual(env.currentEpoch, .solarSystem)
        XCTAssertFalse(env.hasLiquidWater)
        XCTAssertFalse(env.hasMagneticField)
        XCTAssertEqual(env.tectonicActivity, 0.0)
        XCTAssertEqual(env.oceanCoverage, 0.0)
    }

    func testUpdateRecombinationEpoch() {
        let env = Environment()
        env.update(epoch: .recombination, tick: Epoch.recombination.tick)
        XCTAssertEqual(env.currentEpoch, .recombination)
        XCTAssertFalse(env.hasLiquidWater)
        XCTAssertFalse(env.hasMagneticField)
    }

    func testUpdatePresentEpoch() {
        let env = Environment()
        env.update(epoch: .present, tick: Epoch.present.tick)
        XCTAssertEqual(env.currentEpoch, .present)
        XCTAssertTrue(env.hasMagneticField)
    }

    func testUpdateDNAEpoch() {
        let env = Environment()
        env.update(epoch: .dna, tick: Epoch.dna.tick)
        XCTAssertEqual(env.currentEpoch, .dna)
        XCTAssertTrue(env.hasMagneticField)
    }

    func testTemperatureForEpochAll() {
        let env = Environment()
        // Verify all epoch temperatures return correct values
        XCTAssertEqual(env.temperatureForEpoch(.inflation), TemperatureScale.planck * 0.1)
        XCTAssertEqual(env.temperatureForEpoch(.electroweak), TemperatureScale.electroweak)
        XCTAssertEqual(env.temperatureForEpoch(.quark), TemperatureScale.quarkHadron * 10.0)
        XCTAssertEqual(env.temperatureForEpoch(.hadron), TemperatureScale.quarkHadron)
        XCTAssertEqual(env.temperatureForEpoch(.nucleosynthesis), TemperatureScale.nucleosynthesis)
        XCTAssertEqual(env.temperatureForEpoch(.starFormation), 100.0)
        XCTAssertEqual(env.temperatureForEpoch(.solarSystem), 500.0)
        XCTAssertEqual(env.temperatureForEpoch(.earth), TemperatureScale.earthSurface + 50.0)
        XCTAssertEqual(env.temperatureForEpoch(.life), TemperatureScale.earthSurface + 10.0)
        XCTAssertEqual(env.temperatureForEpoch(.dna), TemperatureScale.earthSurface)
    }

    func testBioavailableEnergyWithAtmosphere() {
        let env = Environment(temperature: 300.0)
        env.hasLiquidWater = true
        env.atmosphere.setFraction(of: "CH4", to: 0.1)
        env.atmosphere.setFraction(of: "H2", to: 0.04)
        let energy = env.bioavailableEnergy
        // Should include CH4 * 5.0 + H2 * 3.0 = 0.5 + 0.12 = 0.62
        XCTAssertGreaterThan(energy, 0.5)
    }

    func testBioavailableEnergyWithTectonics() {
        let env = Environment(temperature: 300.0)
        env.hasLiquidWater = true
        env.tectonicActivity = 1.0
        let energy = env.bioavailableEnergy
        // tectonic contribution: 1.0 * 10.0 = 10.0
        XCTAssertGreaterThanOrEqual(energy, 10.0)
    }

    func testHabitabilityScoreTemperatureOutOfRange() {
        let envCold = Environment(temperature: 100.0) // Below 250
        XCTAssertLessThan(envCold.habitabilityScore, 0.3)

        let envHot = Environment(temperature: 500.0) // Above 400
        XCTAssertLessThan(envHot.habitabilityScore, 0.3)
    }

    func testHabitabilityScoreAtmospherePressure() {
        let env = Environment(temperature: 288.0)
        env.atmosphere.pressure = 1.0 // In range 0.5-2.0
        let score1 = env.habitabilityScore

        env.atmosphere.pressure = 5.0 // Out of range
        let score2 = env.habitabilityScore

        XCTAssertGreaterThan(score1, score2)
    }

    func testHabitabilityScoreRadiationRange() {
        let env = Environment(temperature: 288.0)
        env.hasLiquidWater = true
        env.hasMagneticField = true
        env.atmosphere.pressure = 1.0

        // Moderate mutagenic radiation (in range 0.001 to 5.0)
        env.radiationField.setIntensity(.ultraviolet, 1.0)
        let score = env.habitabilityScore
        XCTAssertGreaterThan(score, 0.5)
    }

    func testAtmosphereDescriptionFiltersSmallFractions() {
        let env = Environment()
        // Default atmosphere has some gases with very small fractions
        let desc = env.atmosphereDescription
        // Only gases with fraction > 0.01 should appear
        XCTAssertTrue(desc.contains("CO2"))
        XCTAssertTrue(desc.contains("H2O"))
        XCTAssertTrue(desc.contains("CH4"))
    }

    func testAtmosphereDescriptionSorted() {
        let env = Environment()
        let desc = env.atmosphereDescription
        // CO2 (0.5) should appear before H2O (0.3)
        if let co2Range = desc.range(of: "CO2"), let h2oRange = desc.range(of: "H2O") {
            XCTAssertLessThan(co2Range.lowerBound, h2oRange.lowerBound)
        }
    }

    func testOceanCoverageCapped() {
        let env = Environment()
        // Run update many times
        for i in 0..<2000 {
            env.update(epoch: .present, tick: Epoch.present.tick + i)
        }
        XCTAssertLessThanOrEqual(env.oceanCoverage, 0.71)
    }

    func testTectonicActivityDecreases() {
        let env = Environment()
        env.update(epoch: .earth, tick: Epoch.earth.tick)
        let tectonic1 = env.tectonicActivity
        env.update(epoch: .earth, tick: Epoch.earth.tick + 100000)
        let tectonic2 = env.tectonicActivity
        XCTAssertLessThan(tectonic2, tectonic1)
    }

    func testTectonicActivityNonNegative() {
        let env = Environment()
        env.update(epoch: .present, tick: 999999999)
        XCTAssertGreaterThanOrEqual(env.tectonicActivity, 0.0)
    }

    func testEnvironmentalMutationRateComponents() {
        let env = Environment()
        // Base rate includes cosmic ray mutation rate
        let baseRate = env.environmentalMutationRate
        XCTAssertGreaterThan(baseRate, 0.0)

        // Add gamma radiation
        env.radiationField.setIntensity(.gammaRay, 100.0)
        let gammaRate = env.environmentalMutationRate
        XCTAssertGreaterThan(gammaRate, baseRate)
    }
}
