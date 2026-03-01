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
}
