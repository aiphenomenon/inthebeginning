// Environment.swift
// InTheBeginning – macOS Screensaver
//
// Environmental systems simulation.
// Models temperature, radiation, atmospheric composition, and geological
// conditions that influence chemistry and biology. Conditions evolve
// over cosmic time from extreme heat to habitable ranges.

import Foundation

// MARK: - Atmospheric Gas

enum AtmosphericGas: String, CaseIterable {
    case hydrogen      = "H2"
    case helium        = "He"
    case methane       = "CH4"
    case ammonia       = "NH3"
    case water         = "H2O"
    case carbonDioxide = "CO2"
    case nitrogen      = "N2"
    case oxygen        = "O2"
    case ozone         = "O3"
}

// MARK: - Surface Type

enum SurfaceType: String, CaseIterable {
    case plasma         = "plasma"
    case gas            = "gas"
    case moltenRock     = "molten_rock"
    case rock           = "rock"
    case ocean          = "ocean"
    case land           = "land"
    case ice            = "ice"
}

// MARK: - Environment

final class Environment {
    var temperature: Double
    var radiation: Double
    var pressure: Double
    var atmosphere: [AtmosphericGas: Double]
    var surfaceType: SurfaceType
    var waterPresent: Bool
    var magneticField: Double
    var uvFlux: Double
    var cosmicRayFlux: Double
    var age: Int = 0

    /// Whether conditions are suitable for chemistry.
    var isChemicallyActive: Bool {
        temperature > 100.0 && temperature < 5000.0
    }

    /// Whether conditions can support liquid water and organic chemistry.
    var isHabitable: Bool {
        temperature > 273.0 && temperature < 373.0 &&
        waterPresent &&
        radiation < kRadiationDamageThreshold
    }

    /// Mutation rate modifier based on radiation levels.
    var mutationModifier: Double {
        let uvFactor = uvFlux / 1.0
        let crFactor = cosmicRayFlux / 1.0
        return max(1.0, uvFactor + crFactor * 0.1)
    }

    /// Available energy for biological processes.
    var biologicalEnergy: Double {
        guard isHabitable else { return 0.0 }
        let thermalComponent = kBoltzmann * temperature
        let solarComponent = uvFlux * 0.1
        return thermalComponent + solarComponent
    }

    init(temperature: Double = kTempPlanck,
         radiation: Double = 1e8,
         pressure: Double = 1e30) {
        self.temperature = temperature
        self.radiation = radiation
        self.pressure = pressure
        self.atmosphere = [:]
        self.surfaceType = .plasma
        self.waterPresent = false
        self.magneticField = 0.0
        self.uvFlux = radiation * 0.01
        self.cosmicRayFlux = radiation * 0.001
    }

    // MARK: Step

    /// Advance the environment by one tick.
    func step(epoch: Epoch) {
        age += 1

        switch epoch {
        case .planck, .inflation, .electroweak:
            // Extreme early universe: rapid cooling
            temperature *= 0.999
            radiation *= 0.999
            pressure *= 0.999
            surfaceType = .plasma

        case .quark, .hadron:
            // Quark-hadron transition: cooling continues
            temperature *= 0.9995
            radiation *= 0.9995
            pressure *= 0.999
            surfaceType = .plasma

        case .nucleosynthesis:
            // Big Bang nucleosynthesis: H, He forming
            temperature *= 0.9998
            radiation *= 0.9998
            pressure *= 0.9995
            atmosphere[.hydrogen] = 0.75
            atmosphere[.helium] = 0.25
            surfaceType = .gas

        case .recombination:
            // Atoms form, universe becomes transparent
            temperature = max(temperature * 0.9999, kTempCMB)
            radiation *= 0.999
            pressure *= 0.9990
            surfaceType = .gas

        case .starFormation:
            // Stars ignite, local heating
            temperature = kTempCMB + 50.0
            radiation = 10.0
            pressure = 1e5
            atmosphere[.hydrogen] = 0.90
            atmosphere[.helium] = 0.09
            surfaceType = .gas

        case .solarSystem:
            // Protoplanetary disk: varied conditions
            temperature = 1500.0
            radiation = 5.0
            pressure = 1e4
            atmosphere[.hydrogen] = 0.60
            atmosphere[.helium] = 0.20
            atmosphere[.methane] = 0.05
            atmosphere[.ammonia] = 0.05
            atmosphere[.water] = 0.10
            surfaceType = .moltenRock

        case .earth:
            // Early Earth: cooling, outgassing
            temperature = max(temperature * 0.9999, 500.0)
            radiation = max(radiation * 0.999, 2.0)
            pressure = 1e5
            atmosphere[.carbonDioxide] = 0.80
            atmosphere[.nitrogen] = 0.10
            atmosphere[.water] = 0.10
            atmosphere[.hydrogen] = nil
            atmosphere[.helium] = nil
            surfaceType = temperature > 1000.0 ? .moltenRock : .rock
            magneticField = 30.0
            uvFlux = 3.0
            cosmicRayFlux = 0.5

            // Oceans form when temperature drops
            if temperature < 373.0 {
                waterPresent = true
                surfaceType = .ocean
            }

        case .life:
            // Habitable Earth: liquid water, reduced radiation
            temperature = max(temperature * 0.99999, kTempEarthSurface + 20.0)
            radiation = max(radiation * 0.999, 1.0)
            atmosphere[.carbonDioxide] = max((atmosphere[.carbonDioxide] ?? 0.5) - 0.0001, 0.10)
            atmosphere[.nitrogen] = min((atmosphere[.nitrogen] ?? 0.10) + 0.00005, 0.78)
            atmosphere[.oxygen] = min((atmosphere[.oxygen] ?? 0.0) + 0.00001, 0.01)
            waterPresent = true
            surfaceType = .ocean
            uvFlux = max(uvFlux * 0.9999, 1.5)
            cosmicRayFlux = max(cosmicRayFlux * 0.999, 0.1)

        case .dna:
            // Photosynthesis era: oxygen rises
            temperature = max(temperature * 0.99999, kTempEarthSurface + 5.0)
            atmosphere[.oxygen] = min((atmosphere[.oxygen] ?? 0.01) + 0.0001, 0.15)
            atmosphere[.ozone] = min((atmosphere[.ozone] ?? 0.0) + 0.00001, 0.001)
            atmosphere[.carbonDioxide] = max((atmosphere[.carbonDioxide] ?? 0.10) - 0.0001, 0.03)
            atmosphere[.nitrogen] = 0.78
            waterPresent = true
            surfaceType = .ocean
            // Ozone layer reduces UV
            uvFlux = max(uvFlux * 0.9999, 0.5)
            cosmicRayFlux = 0.05

        case .present:
            // Modern Earth
            temperature = kTempEarthSurface
            radiation = 0.5
            pressure = 101325.0
            atmosphere = [
                .nitrogen: 0.78,
                .oxygen: 0.21,
                .carbonDioxide: 0.0004,
                .water: 0.01,
                .ozone: 0.0001,
            ]
            waterPresent = true
            surfaceType = .land
            magneticField = 50.0
            uvFlux = 0.3
            cosmicRayFlux = 0.01
        }
    }

    // MARK: Census

    func atmosphereDescription() -> String {
        atmosphere
            .sorted { $0.value > $1.value }
            .map { "\($0.key.rawValue): \(String(format: "%.2f%%", $0.value * 100))" }
            .joined(separator: ", ")
    }

    func summary() -> String {
        "T=\(String(format: "%.1f", temperature))K, " +
        "P=\(String(format: "%.0f", pressure))Pa, " +
        "surface=\(surfaceType.rawValue), " +
        "habitable=\(isHabitable)"
    }
}
