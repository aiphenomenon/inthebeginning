//! Environmental systems simulation.
//!
//! Models the planetary environment: atmosphere composition, temperature,
//! available resources, radiation levels, and geological activity.
//! The environment influences chemistry and biology through selection pressures.

use rand::Rng;

use super::constants::*;

// ---------------------------------------------------------------------------
// Atmosphere
// ---------------------------------------------------------------------------

/// Atmospheric composition as fractional abundances.
#[derive(Debug, Clone)]
pub struct Atmosphere {
    pub hydrogen: f64,
    pub helium: f64,
    pub nitrogen: f64,
    pub oxygen: f64,
    pub carbon_dioxide: f64,
    pub methane: f64,
    pub water_vapor: f64,
    pub pressure: f64, // in atmospheres
}

impl Atmosphere {
    /// Early Earth: reducing atmosphere (no free oxygen).
    pub fn early_earth() -> Self {
        Self {
            hydrogen: 0.10,
            helium: 0.01,
            nitrogen: 0.40,
            oxygen: 0.0,
            carbon_dioxide: 0.30,
            methane: 0.10,
            water_vapor: 0.09,
            pressure: 1.5,
        }
    }

    /// Primordial: mostly hydrogen and helium.
    pub fn primordial() -> Self {
        Self {
            hydrogen: 0.75,
            helium: 0.24,
            nitrogen: 0.005,
            oxygen: 0.0,
            carbon_dioxide: 0.003,
            methane: 0.001,
            water_vapor: 0.001,
            pressure: 0.01,
        }
    }

    /// Evolve the atmosphere based on biological activity.
    pub fn evolve(&mut self, photosynthesis_rate: f64, volcanism: f64) {
        // Photosynthesis: CO2 -> O2
        let co2_consumed = self.carbon_dioxide * photosynthesis_rate * 0.001;
        self.carbon_dioxide -= co2_consumed;
        self.oxygen += co2_consumed;

        // Volcanism adds CO2 (very slowly over geological time)
        self.carbon_dioxide += volcanism * 1e-7;

        // Methane oxidation
        if self.oxygen > 0.01 {
            let ch4_oxidized = self.methane.min(self.oxygen * 0.01) * 0.001;
            self.methane -= ch4_oxidized;
            self.oxygen -= ch4_oxidized * 2.0;
            self.carbon_dioxide += ch4_oxidized;
            self.water_vapor += ch4_oxidized * 2.0;
        }

        // Normalize to sum to ~1.0
        let total = self.hydrogen
            + self.helium
            + self.nitrogen
            + self.oxygen
            + self.carbon_dioxide
            + self.methane
            + self.water_vapor;

        if total > 0.0 {
            self.hydrogen /= total;
            self.helium /= total;
            self.nitrogen /= total;
            self.oxygen /= total;
            self.carbon_dioxide /= total;
            self.methane /= total;
            self.water_vapor /= total;
        }
    }

    /// Whether the atmosphere can support complex aerobic life.
    pub fn is_oxygenated(&self) -> bool {
        self.oxygen > 0.05
    }

    /// Greenhouse effect estimate.
    /// Earth's real greenhouse effect adds ~33K to the 255K blackbody temp,
    /// so the factor is ~1.13. We scale accordingly.
    pub fn greenhouse_factor(&self) -> f64 {
        1.0 + self.carbon_dioxide * 0.5 + self.methane * 1.0 + self.water_vapor * 0.3
    }

    pub fn to_compact(&self) -> String {
        format!(
            "ATM[H2={:.1}% He={:.1}% N2={:.1}% O2={:.1}% CO2={:.1}% CH4={:.1}% H2O={:.1}% P={:.2}atm]",
            self.hydrogen * 100.0,
            self.helium * 100.0,
            self.nitrogen * 100.0,
            self.oxygen * 100.0,
            self.carbon_dioxide * 100.0,
            self.methane * 100.0,
            self.water_vapor * 100.0,
            self.pressure,
        )
    }
}

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------

/// The full planetary environment.
pub struct Environment {
    pub temperature: f64,       // Kelvin
    pub atmosphere: Atmosphere,
    pub ocean_coverage: f64,    // fraction 0..1
    pub land_coverage: f64,
    pub radiation_level: f64,   // arbitrary units
    pub magnetic_field: f64,    // 0..1 strength
    pub resources: f64,         // available chemical energy for life
    pub volcanism: f64,         // 0..1 activity level
    pub tidal_energy: f64,
    pub day_length: f64,        // hours
    pub year_length: f64,       // Earth days
}

impl Environment {
    /// Pre-planetary: interstellar conditions.
    pub fn interstellar() -> Self {
        Self {
            temperature: T_CMB,
            atmosphere: Atmosphere::primordial(),
            ocean_coverage: 0.0,
            land_coverage: 0.0,
            radiation_level: 1.0,
            magnetic_field: 0.0,
            resources: 0.0,
            volcanism: 0.0,
            tidal_energy: 0.0,
            day_length: 0.0,
            year_length: 0.0,
        }
    }

    /// Early Earth conditions (~4 billion years ago).
    pub fn early_earth() -> Self {
        Self {
            temperature: 400.0, // hot early Earth
            atmosphere: Atmosphere::early_earth(),
            ocean_coverage: 0.3,
            land_coverage: 0.15,
            radiation_level: 5.0, // high UV, weak ozone
            magnetic_field: 0.5,
            resources: 0.5,
            volcanism: 0.8,
            tidal_energy: 2.0,  // Moon was closer
            day_length: 6.0,    // fast rotation
            year_length: 365.0,
        }
    }

    /// Transition to habitable conditions.
    pub fn make_habitable(&mut self) {
        self.temperature = T_EARTH_SURFACE;
        self.ocean_coverage = 0.7;
        self.land_coverage = 0.3;
        self.radiation_level = 1.0;
        self.magnetic_field = 0.8;
        self.resources = 1.0;
        self.volcanism = 0.3;
        self.tidal_energy = 1.0;
        self.day_length = 24.0;
        // Adjust atmosphere to match habitable conditions.
        // CO2 and CH4 have been drawn down by weathering and early life.
        self.atmosphere.nitrogen = 0.78;
        self.atmosphere.oxygen = 0.01;      // trace O2 pre-Great Oxidation
        self.atmosphere.carbon_dioxide = 0.05;
        self.atmosphere.methane = 0.01;
        self.atmosphere.water_vapor = 0.02;
        self.atmosphere.hydrogen = 0.005;
        self.atmosphere.helium = 0.005;
        self.atmosphere.pressure = 1.0;
        // Normalize
        let total = self.atmosphere.hydrogen + self.atmosphere.helium
            + self.atmosphere.nitrogen + self.atmosphere.oxygen
            + self.atmosphere.carbon_dioxide + self.atmosphere.methane
            + self.atmosphere.water_vapor;
        if total > 0.0 {
            self.atmosphere.hydrogen /= total;
            self.atmosphere.helium /= total;
            self.atmosphere.nitrogen /= total;
            self.atmosphere.oxygen /= total;
            self.atmosphere.carbon_dioxide /= total;
            self.atmosphere.methane /= total;
            self.atmosphere.water_vapor /= total;
        }
    }

    /// Evolve the environment by one tick.
    pub fn tick(&mut self, population_size: usize) {
        let mut rng = rand::thread_rng();

        // Biological feedback on atmosphere
        let photosynthesis = if population_size > 10 {
            (population_size as f64).ln() * 0.1
        } else {
            0.0
        };
        self.atmosphere.evolve(photosynthesis, self.volcanism);

        // Temperature evolves with greenhouse effect
        let target_temp = T_EARTH_SURFACE * self.atmosphere.greenhouse_factor();
        self.temperature += (target_temp - self.temperature) * 0.001;

        // Volcanism slowly decreases
        self.volcanism *= 0.9999;
        self.volcanism += rng.gen::<f64>() * 0.0001; // occasional eruptions

        // Radiation: decreases as ozone forms from O2
        if self.atmosphere.oxygen > 0.05 {
            self.radiation_level *= 0.999;
            self.radiation_level = self.radiation_level.max(0.5);
        }

        // Resources scale with ocean coverage and temperature
        let temp_factor = if self.temperature > 250.0 && self.temperature < 350.0 {
            1.0
        } else {
            0.5
        };
        self.resources = self.ocean_coverage * temp_factor
            + self.volcanism * 0.2
            + self.tidal_energy * 0.1;

        // Day length slowly increases (tidal braking)
        self.day_length += 1e-7;

        // Random thermal fluctuations
        self.temperature += (rng.gen::<f64>() - 0.5) * THERMAL_FLUCTUATION * 10.0;
    }

    /// Is the environment habitable for carbon-based life?
    pub fn is_habitable(&self) -> bool {
        self.temperature > 250.0
            && self.temperature < 400.0
            && self.ocean_coverage > 0.1
            && self.resources > 0.1
    }

    pub fn to_compact(&self) -> String {
        format!(
            "ENV[T={:.1}K ocean={:.0}% land={:.0}% rad={:.2} mag={:.2} res={:.2} volc={:.2} hab={}]",
            self.temperature,
            self.ocean_coverage * 100.0,
            self.land_coverage * 100.0,
            self.radiation_level,
            self.magnetic_field,
            self.resources,
            self.volcanism,
            if self.is_habitable() { "YES" } else { "NO" },
        )
    }
}
