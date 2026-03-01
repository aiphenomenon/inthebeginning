#pragma once
/// Environmental systems simulation.
///
/// Models the physical environment through cosmic history:
/// radiation fields, temperature evolution, atmospheric composition,
/// ocean chemistry, and energy sources that drive chemistry and biology.

#include <array>
#include <cmath>
#include <string>
#include <vector>

#include "constants.hpp"

namespace sim {

// ============================================================
// RadiationField
// ============================================================
struct RadiationField {
    double uvIntensity     = 0.0;   // arbitrary units
    double cosmicRayFlux   = 0.0;
    double irIntensity     = 0.0;   // infrared
    double visibleLight    = 0.0;
    double gammaRayFlux    = 0.0;

    /// Update radiation based on epoch tick and temperature.
    void update(int tick, double temperature);

    /// Total ionizing radiation dose.
    [[nodiscard]] double totalIonizing() const;
};

// ============================================================
// Atmosphere
// ============================================================
struct Atmosphere {
    double hydrogenFraction  = 1.0;
    double heliumFraction    = 0.0;
    double nitrogenFraction  = 0.0;
    double oxygenFraction    = 0.0;
    double co2Fraction       = 0.0;
    double methaneFraction   = 0.0;
    double waterVaporFraction= 0.0;
    double pressure          = 0.0;   // atmospheres

    /// Update composition based on epoch.
    void update(int tick);

    /// Greenhouse effect: temperature modifier.
    [[nodiscard]] double greenhouseEffect() const;

    /// UV shielding factor (0 = no shielding, 1 = full).
    [[nodiscard]] double uvShielding() const;
};

// ============================================================
// Ocean
// ============================================================
struct Ocean {
    bool   exists        = false;
    double volume        = 0.0;     // arbitrary units
    double pH            = 7.0;
    double salinity      = 0.0;     // parts per thousand
    double temperature   = 0.0;
    double dissolvedO2   = 0.0;
    double dissolvedCO2  = 0.0;

    /// Update ocean state based on atmospheric conditions.
    void update(int tick, double surfaceTemp, const Atmosphere& atm);

    /// Energy available from hydrothermal vents.
    [[nodiscard]] double ventEnergy() const;
};

// ============================================================
// Environment
// ============================================================
class Environment {
public:
    explicit Environment(double initialTemp = T_PLANCK);

    /// Advance the environment by one simulation tick.
    void update(int tick);

    /// Temperature at current tick (cosmological cooling).
    [[nodiscard]] double currentTemperature() const { return temperature_; }

    /// Scale factor a(t) - cosmic expansion.
    [[nodiscard]] double scaleFactor() const { return scaleFactor_; }

    /// Energy density of radiation field.
    [[nodiscard]] double radiationDensity() const;

    /// Energy available for biological processes.
    [[nodiscard]] double biologicalEnergy() const;

    /// Summary string for display.
    [[nodiscard]] std::string summary() const;

    // --- Public sub-systems ---
    RadiationField radiation;
    Atmosphere     atmosphere;
    Ocean          ocean;

private:
    double temperature_  = T_PLANCK;
    double scaleFactor_  = 1.0;
    int    currentTick_  = 0;
};

} // namespace sim
