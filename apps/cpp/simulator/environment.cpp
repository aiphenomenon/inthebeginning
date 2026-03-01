#include "environment.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <iomanip>

namespace sim {

// ============================================================
// RadiationField
// ============================================================

void RadiationField::update(int tick, double temperature) {
    // Early universe: dominated by gamma rays
    if (tick < RECOMBINATION_EPOCH) {
        gammaRayFlux = temperature / T_PLANCK * 100.0;
        uvIntensity  = temperature / T_PLANCK * 50.0;
        cosmicRayFlux = 0.0;
        irIntensity  = 0.0;
        visibleLight = 0.0;
    }
    // Post-recombination, pre-stars
    else if (tick < STAR_FORMATION_EPOCH) {
        gammaRayFlux = 0.01;
        uvIntensity  = 0.01;
        cosmicRayFlux = 0.1;
        irIntensity  = temperature / 1000.0;
        visibleLight = 0.001;
    }
    // Stellar era
    else if (tick < EARTH_EPOCH) {
        gammaRayFlux = 0.001;
        uvIntensity  = 5.0;
        cosmicRayFlux = 1.0;
        irIntensity  = 2.0;
        visibleLight = 10.0;
    }
    // Earth era
    else {
        gammaRayFlux  = 0.0001;
        uvIntensity   = 3.0;
        cosmicRayFlux = 0.5;
        irIntensity   = 5.0;
        visibleLight  = 15.0;
    }
}

double RadiationField::totalIonizing() const {
    return gammaRayFlux + uvIntensity * 0.3 + cosmicRayFlux;
}

// ============================================================
// Atmosphere
// ============================================================

void Atmosphere::update(int tick) {
    if (tick < EARTH_EPOCH) {
        // No planetary atmosphere before Earth forms
        pressure = 0.0;
        hydrogenFraction = 1.0;
        heliumFraction = 0.0;
        nitrogenFraction = 0.0;
        oxygenFraction = 0.0;
        co2Fraction = 0.0;
        methaneFraction = 0.0;
        waterVaporFraction = 0.0;
        return;
    }

    // Early Earth: reducing atmosphere
    if (tick < LIFE_EPOCH) {
        pressure = 1.0;
        hydrogenFraction   = 0.05;
        heliumFraction     = 0.01;
        nitrogenFraction   = 0.60;
        oxygenFraction     = 0.001;
        co2Fraction        = 0.20;
        methaneFraction    = 0.05;
        waterVaporFraction = 0.089;
    }
    // After life: gradual oxygenation
    else if (tick < DNA_EPOCH) {
        double progress = static_cast<double>(tick - LIFE_EPOCH) /
                          static_cast<double>(DNA_EPOCH - LIFE_EPOCH);
        pressure = 1.0;
        hydrogenFraction   = 0.05 * (1.0 - progress);
        heliumFraction     = 0.01;
        nitrogenFraction   = 0.70 + 0.08 * progress;
        oxygenFraction     = 0.001 + 0.10 * progress;
        co2Fraction        = 0.20 * (1.0 - 0.8 * progress);
        methaneFraction    = 0.05 * (1.0 - 0.7 * progress);
        waterVaporFraction = 0.01 + 0.02 * progress;
    }
    // Modern atmosphere
    else {
        pressure = 1.0;
        hydrogenFraction   = 0.0001;
        heliumFraction     = 0.0005;
        nitrogenFraction   = 0.7808;
        oxygenFraction     = 0.2095;
        co2Fraction        = 0.0004;
        methaneFraction    = 0.00018;
        waterVaporFraction = 0.01;
    }
}

double Atmosphere::greenhouseEffect() const {
    // CO2 and methane are greenhouse gases
    return 1.0 + 30.0 * co2Fraction + 80.0 * methaneFraction
               + 5.0 * waterVaporFraction;
}

double Atmosphere::uvShielding() const {
    // Ozone (derived from O2) shields UV
    // Simplified: shielding proportional to O2 fraction
    return std::min(1.0, oxygenFraction * 5.0);
}

// ============================================================
// Ocean
// ============================================================

void Ocean::update(int tick, double surfaceTemp, const Atmosphere& atm) {
    if (tick < EARTH_EPOCH) {
        exists = false;
        volume = 0.0;
        return;
    }

    exists = (surfaceTemp > 273.0 && surfaceTemp < 373.0) || tick >= EARTH_EPOCH;

    if (!exists) return;

    // Ocean forms and grows
    double progress = std::min(1.0,
        static_cast<double>(tick - EARTH_EPOCH) /
        static_cast<double>(LIFE_EPOCH - EARTH_EPOCH));
    volume = 100.0 * progress;

    temperature = surfaceTemp - 15.0; // ocean slightly cooler
    if (temperature < 273.0) temperature = 273.0;

    // pH: early oceans were slightly acidic due to CO2
    pH = 7.0 + 1.0 * (1.0 - atm.co2Fraction * 5.0);
    pH = std::clamp(pH, 5.0, 9.0);

    salinity = 35.0 * progress; // modern ocean ~35 ppt

    dissolvedO2  = atm.oxygenFraction * 10.0;
    dissolvedCO2 = atm.co2Fraction * 50.0;
}

double Ocean::ventEnergy() const {
    if (!exists) return 0.0;
    // Hydrothermal vents provide constant energy
    return 15.0;
}

// ============================================================
// Environment
// ============================================================

Environment::Environment(double initialTemp)
    : temperature_(initialTemp) {}

void Environment::update(int tick) {
    currentTick_ = tick;

    // Cosmological temperature evolution
    // T ~ T_initial / a(t), where a(t) grows with time
    if (tick <= PLANCK_EPOCH) {
        temperature_ = T_PLANCK;
        scaleFactor_ = 1.0;
    } else if (tick <= INFLATION_EPOCH) {
        // Exponential expansion during inflation
        double frac = static_cast<double>(tick - PLANCK_EPOCH) /
                      static_cast<double>(INFLATION_EPOCH - PLANCK_EPOCH);
        scaleFactor_ = std::exp(60.0 * frac); // e-folds
        temperature_ = T_PLANCK / std::pow(scaleFactor_, 0.25);
    } else if (tick <= RECOMBINATION_EPOCH) {
        // Radiation-dominated: T ~ 1/a, a ~ t^(1/2)
        double baseSF = std::exp(60.0);
        double frac = static_cast<double>(tick - INFLATION_EPOCH) /
                      static_cast<double>(RECOMBINATION_EPOCH - INFLATION_EPOCH);
        scaleFactor_ = baseSF * (1.0 + 1000.0 * frac);
        temperature_ = T_PLANCK / std::pow(scaleFactor_, 0.25);
        temperature_ = std::max(temperature_, T_RECOMBINATION);
    } else if (tick <= STAR_FORMATION_EPOCH) {
        // Matter-dominated, cooling to CMB levels
        double frac = static_cast<double>(tick - RECOMBINATION_EPOCH) /
                      static_cast<double>(STAR_FORMATION_EPOCH - RECOMBINATION_EPOCH);
        temperature_ = T_RECOMBINATION * std::exp(-frac * 5.0);
        temperature_ = std::max(temperature_, T_CMB);
        scaleFactor_ *= (1.0 + frac);
    } else if (tick < EARTH_EPOCH) {
        // Stellar era: background is CMB, but local environments vary
        temperature_ = T_CMB;
    } else {
        // Earth surface temperature
        atmosphere.update(tick);
        double greenhouse = atmosphere.greenhouseEffect();
        temperature_ = T_EARTH_SURFACE * greenhouse /
                       (1.0 + (greenhouse - 1.0) * 0.5);
        // Keep within habitable range
        temperature_ = std::clamp(temperature_, 250.0, 350.0);
    }

    // Update subsystems
    radiation.update(tick, temperature_);
    atmosphere.update(tick);
    ocean.update(tick, temperature_, atmosphere);
}

double Environment::radiationDensity() const {
    // Stefan-Boltzmann-like: proportional to T^4
    return K_B * temperature_ * temperature_ * temperature_ * temperature_ * 1e-30;
}

double Environment::biologicalEnergy() const {
    if (currentTick_ < EARTH_EPOCH) return 0.0;

    double energy = 0.0;

    // Stellar radiation (photosynthesis potential)
    energy += radiation.visibleLight * 0.5;

    // Geothermal / hydrothermal
    energy += ocean.ventEnergy();

    // Atmospheric shielding allows more energy to be used biologically
    energy *= (1.0 + atmosphere.uvShielding() * 0.5);

    return energy;
}

std::string Environment::summary() const {
    std::ostringstream oss;
    oss << std::scientific << std::setprecision(3);
    oss << "T=" << temperature_ << "K"
        << " a=" << scaleFactor_
        << " rad=" << radiation.totalIonizing();

    if (currentTick_ >= EARTH_EPOCH) {
        oss << std::fixed << std::setprecision(1);
        oss << " O2=" << (atmosphere.oxygenFraction * 100.0) << "%"
            << " CO2=" << (atmosphere.co2Fraction * 100.0) << "%";
        if (ocean.exists) {
            oss << " ocean(pH=" << std::setprecision(1) << ocean.pH << ")";
        }
    }

    return oss.str();
}

} // namespace sim
