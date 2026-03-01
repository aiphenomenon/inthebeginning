// Environment.swift
// InTheBeginning
//
// Environmental conditions simulation.
// Models temperature, radiation fields, atmospheric composition,
// and planetary surface conditions that evolve over cosmic time.
// The environment drives selection pressures and enables or
// constrains chemical and biological processes.

import Foundation

// MARK: - Radiation Type

enum RadiationType: String, CaseIterable, Sendable {
    case gammaRay = "gamma"
    case xRay = "xray"
    case ultraviolet = "uv"
    case visible = "visible"
    case infrared = "infrared"
    case microwave = "microwave"
    case radio = "radio"

    var energy: Double {
        switch self {
        case .gammaRay:   return 1e6
        case .xRay:       return 1e4
        case .ultraviolet: return 100.0
        case .visible:    return 2.0
        case .infrared:   return 0.1
        case .microwave:  return 0.001
        case .radio:      return 1e-6
        }
    }

    var mutagenicPotential: Double {
        switch self {
        case .gammaRay:    return 1.0
        case .xRay:        return 0.8
        case .ultraviolet: return 0.3
        case .visible:     return 0.0
        case .infrared:    return 0.0
        case .microwave:   return 0.0
        case .radio:       return 0.0
        }
    }

    var displayColor: SIMD4<Float> {
        switch self {
        case .gammaRay:    return SIMD4<Float>(0.8, 0.0, 1.0, 0.9)
        case .xRay:        return SIMD4<Float>(0.5, 0.0, 1.0, 0.8)
        case .ultraviolet: return SIMD4<Float>(0.3, 0.1, 0.9, 0.7)
        case .visible:     return SIMD4<Float>(1.0, 1.0, 0.8, 0.9)
        case .infrared:    return SIMD4<Float>(1.0, 0.3, 0.1, 0.6)
        case .microwave:   return SIMD4<Float>(0.8, 0.6, 0.2, 0.4)
        case .radio:       return SIMD4<Float>(0.4, 0.4, 0.4, 0.3)
        }
    }
}

// MARK: - Atmospheric Gas

struct AtmosphericGas: Sendable {
    let name: String
    let molecularWeight: Double
    var fraction: Double  // Fraction of total atmosphere (0..1)

    /// Whether this gas is a greenhouse gas
    var isGreenhouse: Bool {
        name == "CO2" || name == "CH4" || name == "H2O"
    }
}

// MARK: - Atmosphere

struct Atmosphere: Sendable {
    var gases: [AtmosphericGas]
    var pressure: Double  // in simulation units (1.0 = 1 atm)
    var ozoneLayerStrength: Double = 0.0  // 0..1, shields UV

    init() {
        // Early Earth-like reducing atmosphere
        gases = [
            AtmosphericGas(name: "N2", molecularWeight: 28.0, fraction: 0.0),
            AtmosphericGas(name: "CO2", molecularWeight: 44.0, fraction: 0.5),
            AtmosphericGas(name: "H2O", molecularWeight: 18.0, fraction: 0.3),
            AtmosphericGas(name: "CH4", molecularWeight: 16.0, fraction: 0.1),
            AtmosphericGas(name: "NH3", molecularWeight: 17.0, fraction: 0.05),
            AtmosphericGas(name: "H2", molecularWeight: 2.0, fraction: 0.04),
            AtmosphericGas(name: "O2", molecularWeight: 32.0, fraction: 0.01),
        ]
        pressure = 1.0
    }

    /// Get the fraction of a specific gas by name.
    func fraction(of gasName: String) -> Double {
        gases.first(where: { $0.name == gasName })?.fraction ?? 0.0
    }

    /// Modify a gas fraction (will not renormalize automatically).
    mutating func setFraction(of gasName: String, to value: Double) {
        if let idx = gases.firstIndex(where: { $0.name == gasName }) {
            gases[idx].fraction = max(0.0, min(1.0, value))
        }
    }

    /// Total greenhouse effect multiplier.
    var greenhouseEffect: Double {
        gases.filter(\.isGreenhouse).reduce(0.0) { $0 + $1.fraction * 2.0 }
    }

    /// UV transmission factor (1.0 = full UV, 0.0 = fully blocked).
    var uvTransmission: Double {
        max(0.0, 1.0 - ozoneLayerStrength)
    }

    /// Evolve the atmosphere over time (simplified model).
    mutating func evolve(hasLife: Bool, tick: Int) {
        // Gradual nitrogen buildup from volcanic outgassing
        let n2Fraction = fraction(of: "N2")
        if n2Fraction < 0.78 {
            setFraction(of: "N2", to: n2Fraction + 0.0001)
        }

        // CO2 reduction (geological weathering, life absorption)
        let co2Fraction = fraction(of: "CO2")
        let co2Reduction = hasLife ? 0.0005 : 0.0001
        setFraction(of: "CO2", to: co2Fraction - co2Reduction)

        // Oxygen buildup from photosynthesis
        if hasLife {
            let o2Fraction = fraction(of: "O2")
            if o2Fraction < 0.21 {
                setFraction(of: "O2", to: o2Fraction + 0.0002)
            }

            // Ozone layer forms from O2
            ozoneLayerStrength = min(1.0, fraction(of: "O2") * 3.0)
        }

        // Methane reduction (UV breaks it down)
        let ch4Fraction = fraction(of: "CH4")
        setFraction(of: "CH4", to: ch4Fraction * 0.999)
    }
}

// MARK: - Radiation Field

struct RadiationField: Sendable {
    var intensities: [RadiationType: Double]

    init() {
        intensities = [:]
        for type in RadiationType.allCases {
            intensities[type] = 0.0
        }
    }

    /// Total radiation intensity across all bands.
    var totalIntensity: Double {
        intensities.values.reduce(0.0, +)
    }

    /// Total mutagenic radiation.
    var mutagenicIntensity: Double {
        intensities.reduce(0.0) { sum, pair in
            sum + pair.value * pair.key.mutagenicPotential
        }
    }

    /// Set intensity for a radiation type.
    mutating func setIntensity(_ type: RadiationType, _ value: Double) {
        intensities[type] = max(0.0, value)
    }

    /// Evolve radiation field based on cosmic epoch.
    mutating func evolve(epoch: Epoch, atmosphere: Atmosphere) {
        switch epoch {
        case .planck, .inflation, .electroweak:
            // Extreme radiation
            setIntensity(.gammaRay, 1e6)
            setIntensity(.xRay, 1e5)
            setIntensity(.ultraviolet, 1e4)

        case .quark, .hadron:
            // Still very high
            setIntensity(.gammaRay, 1e4)
            setIntensity(.xRay, 1e3)
            setIntensity(.ultraviolet, 1e2)

        case .nucleosynthesis:
            setIntensity(.gammaRay, 100.0)
            setIntensity(.xRay, 50.0)
            setIntensity(.ultraviolet, 20.0)
            setIntensity(.visible, 5.0)

        case .recombination:
            // CMB photons dominate
            setIntensity(.gammaRay, 0.1)
            setIntensity(.xRay, 0.1)
            setIntensity(.ultraviolet, 1.0)
            setIntensity(.visible, 2.0)
            setIntensity(.microwave, 10.0)

        case .starFormation:
            setIntensity(.gammaRay, 1.0)
            setIntensity(.xRay, 2.0)
            setIntensity(.ultraviolet, 10.0)
            setIntensity(.visible, 20.0)
            setIntensity(.infrared, 15.0)

        case .solarSystem, .earth:
            // Solar radiation reaching planetary surface
            setIntensity(.gammaRay, 0.01)
            setIntensity(.xRay, 0.1)
            setIntensity(.ultraviolet, 5.0 * atmosphere.uvTransmission)
            setIntensity(.visible, 30.0)
            setIntensity(.infrared, 20.0)

        case .life, .dna, .present:
            // Stabilized with ozone
            setIntensity(.gammaRay, 0.001)
            setIntensity(.xRay, 0.01)
            setIntensity(.ultraviolet, 2.0 * atmosphere.uvTransmission)
            setIntensity(.visible, 30.0)
            setIntensity(.infrared, 25.0)
            setIntensity(.microwave, 0.01)  // CMB remnant
        }
    }
}

// MARK: - Environment

final class Environment {
    var temperature: Double
    var atmosphere: Atmosphere
    var radiationField: RadiationField
    var hasLiquidWater: Bool = false
    var hasMagneticField: Bool = false
    var tectonicActivity: Double = 0.0  // 0..1
    var oceanCoverage: Double = 0.0     // 0..1 fraction of surface
    var currentEpoch: Epoch = .planck

    init(temperature: Double = TemperatureScale.planck) {
        self.temperature = temperature
        self.atmosphere = Atmosphere()
        self.radiationField = RadiationField()
    }

    // MARK: - Temperature Evolution

    /// Compute temperature for a given epoch.
    func temperatureForEpoch(_ epoch: Epoch) -> Double {
        switch epoch {
        case .planck:          return TemperatureScale.planck
        case .inflation:       return TemperatureScale.planck * 0.1
        case .electroweak:     return TemperatureScale.electroweak
        case .quark:           return TemperatureScale.quarkHadron * 10.0
        case .hadron:          return TemperatureScale.quarkHadron
        case .nucleosynthesis: return TemperatureScale.nucleosynthesis
        case .recombination:   return TemperatureScale.recombination
        case .starFormation:   return 100.0  // Interstellar medium
        case .solarSystem:     return 500.0  // Protoplanetary disk average
        case .earth:           return TemperatureScale.earthSurface + 50.0  // Early hot Earth
        case .life:            return TemperatureScale.earthSurface + 10.0
        case .dna:             return TemperatureScale.earthSurface
        case .present:         return TemperatureScale.earthSurface
        }
    }

    // MARK: - Update

    /// Update environment for the current cosmic epoch.
    func update(epoch: Epoch, tick: Int) {
        currentEpoch = epoch
        temperature = temperatureForEpoch(epoch)

        // Add small stochastic fluctuations
        temperature += EnvironmentParams.thermalFluctuation * Double.random(in: -1...1) * temperature * 0.01

        // Radiation
        radiationField.evolve(epoch: epoch, atmosphere: atmosphere)

        // Planetary conditions
        switch epoch {
        case .earth, .life, .dna, .present:
            hasLiquidWater = temperature > 273.0 && temperature < 373.0
            hasMagneticField = true
            tectonicActivity = max(0.0, 0.8 - Double(tick - Epoch.earth.tick) * 0.000001)

            // Ocean coverage builds up
            if epoch >= .earth {
                oceanCoverage = min(0.71, oceanCoverage + 0.001)
            }

            // Atmosphere evolves with life
            atmosphere.evolve(hasLife: epoch >= .life, tick: tick)

        case .solarSystem:
            hasLiquidWater = false
            hasMagneticField = false
            tectonicActivity = 0.0
            oceanCoverage = 0.0

        default:
            hasLiquidWater = false
            hasMagneticField = false
            tectonicActivity = 0.0
            oceanCoverage = 0.0
        }
    }

    // MARK: - Energy Available for Life

    /// Compute available energy for biological processes.
    var bioavailableEnergy: Double {
        guard hasLiquidWater else { return 0.0 }

        var energy = 0.0

        // Solar visible light (photosynthesis potential)
        energy += radiationField.intensities[.visible] ?? 0.0

        // Geothermal (hydrothermal vents)
        energy += tectonicActivity * 10.0

        // Chemical energy from atmosphere
        energy += atmosphere.fraction(of: "CH4") * 5.0
        energy += atmosphere.fraction(of: "H2") * 3.0

        return energy
    }

    /// Effective mutation rate from environmental factors.
    var environmentalMutationRate: Double {
        var rate = EnvironmentParams.cosmicRayMutationRate

        // UV contribution
        rate += (radiationField.intensities[.ultraviolet] ?? 0.0) * EnvironmentParams.uvMutationRate

        // Cosmic ray contribution
        rate += (radiationField.intensities[.gammaRay] ?? 0.0) * EnvironmentParams.cosmicRayMutationRate

        return min(0.1, rate)
    }

    // MARK: - Habitability

    /// Overall habitability score for the environment (0..1).
    var habitabilityScore: Double {
        var score = 0.0

        // Temperature in habitable range
        if temperature > 250.0 && temperature < 400.0 {
            let optimalDist = abs(temperature - 288.0)
            score += max(0.0, 1.0 - optimalDist / 150.0) * 0.3
        }

        // Liquid water
        if hasLiquidWater {
            score += 0.25
        }

        // Magnetic field shields from radiation
        if hasMagneticField {
            score += 0.15
        }

        // Moderate radiation (not too much, not too little)
        let mutRate = radiationField.mutagenicIntensity
        if mutRate > 0.001 && mutRate < 5.0 {
            score += 0.15
        }

        // Atmosphere provides pressure and resources
        if atmosphere.pressure > 0.5 && atmosphere.pressure < 2.0 {
            score += 0.15
        }

        return min(1.0, score)
    }

    // MARK: - Statistics

    var atmosphereDescription: String {
        atmosphere.gases
            .filter { $0.fraction > 0.01 }
            .sorted { $0.fraction > $1.fraction }
            .map { "\($0.name): \(String(format: "%.1f", $0.fraction * 100))%" }
            .joined(separator: ", ")
    }
}
