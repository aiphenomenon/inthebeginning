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

#[cfg(test)]
mod tests {
    use super::*;

    // -----------------------------------------------------------------------
    // Atmosphere
    // -----------------------------------------------------------------------

    /// Early Earth atmosphere has no free oxygen.
    #[test]
    fn early_earth_no_oxygen() {
        let atm = Atmosphere::early_earth();
        assert_eq!(atm.oxygen, 0.0);
    }

    /// Early Earth atmosphere sums to approximately 1.0.
    #[test]
    fn early_earth_sums_to_one() {
        let atm = Atmosphere::early_earth();
        let total = atm.hydrogen + atm.helium + atm.nitrogen + atm.oxygen
            + atm.carbon_dioxide + atm.methane + atm.water_vapor;
        assert!((total - 1.0).abs() < 1e-10);
    }

    /// Primordial atmosphere is mostly hydrogen and helium.
    #[test]
    fn primordial_mostly_h_he() {
        let atm = Atmosphere::primordial();
        assert!(atm.hydrogen > 0.5);
        assert!(atm.helium > 0.1);
        assert_eq!(atm.oxygen, 0.0);
    }

    /// Primordial atmosphere sums to approximately 1.0.
    #[test]
    fn primordial_sums_to_one() {
        let atm = Atmosphere::primordial();
        let total = atm.hydrogen + atm.helium + atm.nitrogen + atm.oxygen
            + atm.carbon_dioxide + atm.methane + atm.water_vapor;
        assert!((total - 1.0).abs() < 1e-10);
    }

    /// Evolve with photosynthesis converts CO2 to O2.
    #[test]
    fn atmosphere_evolve_photosynthesis() {
        let mut atm = Atmosphere::early_earth();
        let initial_co2 = atm.carbon_dioxide;
        let initial_o2 = atm.oxygen;
        atm.evolve(100.0, 0.0); // high photosynthesis, no volcanism
        assert!(atm.oxygen > initial_o2, "oxygen should increase");
        assert!(atm.carbon_dioxide < initial_co2, "CO2 should decrease");
    }

    /// Evolve normalizes the total to 1.0.
    #[test]
    fn atmosphere_evolve_normalizes() {
        let mut atm = Atmosphere::early_earth();
        atm.evolve(10.0, 0.5);
        let total = atm.hydrogen + atm.helium + atm.nitrogen + atm.oxygen
            + atm.carbon_dioxide + atm.methane + atm.water_vapor;
        assert!((total - 1.0).abs() < 1e-6);
    }

    /// Not oxygenated when oxygen < 5%.
    #[test]
    fn atmosphere_not_oxygenated_low_o2() {
        let atm = Atmosphere::early_earth();
        assert!(!atm.is_oxygenated());
    }

    /// Oxygenated when oxygen > 5%.
    #[test]
    fn atmosphere_oxygenated_high_o2() {
        let mut atm = Atmosphere::early_earth();
        atm.oxygen = 0.10;
        assert!(atm.is_oxygenated());
    }

    /// Greenhouse factor is >= 1.0.
    #[test]
    fn greenhouse_factor_at_least_one() {
        let atm = Atmosphere::early_earth();
        assert!(atm.greenhouse_factor() >= 1.0);
    }

    /// Higher CO2 means higher greenhouse factor.
    #[test]
    fn greenhouse_increases_with_co2() {
        let mut atm1 = Atmosphere::primordial();
        let mut atm2 = Atmosphere::primordial();
        atm1.carbon_dioxide = 0.01;
        atm2.carbon_dioxide = 0.30;
        assert!(atm2.greenhouse_factor() > atm1.greenhouse_factor());
    }

    /// Compact representation includes all gas fractions.
    #[test]
    fn atmosphere_compact_format() {
        let atm = Atmosphere::early_earth();
        let compact = atm.to_compact();
        assert!(compact.starts_with("ATM["));
        assert!(compact.contains("O2="));
        assert!(compact.contains("N2="));
    }

    // -----------------------------------------------------------------------
    // Environment
    // -----------------------------------------------------------------------

    /// Interstellar environment is at CMB temperature.
    #[test]
    fn interstellar_temperature() {
        let env = Environment::interstellar();
        assert_eq!(env.temperature, T_CMB);
    }

    /// Interstellar environment is not habitable.
    #[test]
    fn interstellar_not_habitable() {
        let env = Environment::interstellar();
        assert!(!env.is_habitable());
    }

    /// Early Earth is hot (400 K).
    #[test]
    fn early_earth_temperature() {
        let env = Environment::early_earth();
        assert_eq!(env.temperature, 400.0);
    }

    /// Early Earth has partial ocean coverage.
    #[test]
    fn early_earth_has_ocean() {
        let env = Environment::early_earth();
        assert!(env.ocean_coverage > 0.0);
    }

    /// Early Earth has high volcanism.
    #[test]
    fn early_earth_volcanism() {
        let env = Environment::early_earth();
        assert!(env.volcanism > 0.5);
    }

    /// make_habitable sets appropriate conditions.
    #[test]
    fn make_habitable_conditions() {
        let mut env = Environment::interstellar();
        env.make_habitable();
        assert_eq!(env.temperature, T_EARTH_SURFACE);
        assert_eq!(env.ocean_coverage, 0.7);
        assert_eq!(env.land_coverage, 0.3);
        assert_eq!(env.resources, 1.0);
        assert_eq!(env.day_length, 24.0);
    }

    /// Habitable environment is reported as habitable.
    #[test]
    fn habitable_after_make_habitable() {
        let mut env = Environment::interstellar();
        env.make_habitable();
        assert!(env.is_habitable());
    }

    /// is_habitable requires temperature in [250, 400].
    #[test]
    fn habitability_temperature_range() {
        let mut env = Environment::early_earth();
        env.ocean_coverage = 0.5;
        env.resources = 0.5;

        env.temperature = 200.0; // too cold
        assert!(!env.is_habitable());

        env.temperature = 300.0; // just right
        assert!(env.is_habitable());

        env.temperature = 450.0; // too hot
        assert!(!env.is_habitable());
    }

    /// is_habitable requires ocean coverage > 0.1.
    #[test]
    fn habitability_requires_ocean() {
        let mut env = Environment::early_earth();
        env.temperature = 300.0;
        env.resources = 0.5;
        env.ocean_coverage = 0.05;
        assert!(!env.is_habitable());
    }

    /// is_habitable requires resources > 0.1.
    #[test]
    fn habitability_requires_resources() {
        let mut env = Environment::early_earth();
        env.temperature = 300.0;
        env.ocean_coverage = 0.5;
        env.resources = 0.05;
        assert!(!env.is_habitable());
    }

    /// Tick evolves the atmosphere via photosynthesis.
    #[test]
    fn environment_tick_evolves_atmosphere() {
        let mut env = Environment::early_earth();
        env.make_habitable();
        let initial_o2 = env.atmosphere.oxygen;
        // Tick with a large population to trigger photosynthesis
        for _ in 0..100 {
            env.tick(1000);
        }
        assert!(env.atmosphere.oxygen > initial_o2,
            "oxygen should increase with large population");
    }

    /// Volcanism slowly decreases over time.
    #[test]
    fn environment_volcanism_decreases() {
        let mut env = Environment::early_earth();
        let initial_volcanism = env.volcanism;
        for _ in 0..10000 {
            env.tick(0);
        }
        // Volcanism decays by 0.9999 each tick, so over 10k ticks
        // it should be noticeably lower
        assert!(env.volcanism < initial_volcanism,
            "volcanism {} should decrease from {}",
            env.volcanism, initial_volcanism);
    }

    /// Radiation decreases when oxygen is present.
    #[test]
    fn environment_radiation_decreases_with_oxygen() {
        let mut env = Environment::early_earth();
        env.atmosphere.oxygen = 0.10;
        let initial_rad = env.radiation_level;
        for _ in 0..100 {
            env.tick(0);
        }
        assert!(env.radiation_level < initial_rad);
    }

    /// Radiation has a floor of 0.5.
    #[test]
    fn environment_radiation_floor() {
        let mut env = Environment::early_earth();
        env.atmosphere.oxygen = 0.20;
        env.radiation_level = 0.51;
        for _ in 0..10000 {
            env.tick(0);
        }
        assert!(env.radiation_level >= 0.5);
    }

    /// Day length slowly increases.
    #[test]
    fn environment_day_length_increases() {
        let mut env = Environment::early_earth();
        let initial = env.day_length;
        for _ in 0..1000 {
            env.tick(0);
        }
        assert!(env.day_length > initial);
    }

    /// Compact representation includes habitability.
    #[test]
    fn environment_compact_format() {
        let env = Environment::early_earth();
        let compact = env.to_compact();
        assert!(compact.starts_with("ENV["));
        assert!(compact.contains("hab="));
    }

    /// make_habitable normalizes atmosphere to sum to ~1.
    #[test]
    fn make_habitable_atmosphere_normalized() {
        let mut env = Environment::interstellar();
        env.make_habitable();
        let atm = &env.atmosphere;
        let total = atm.hydrogen + atm.helium + atm.nitrogen + atm.oxygen
            + atm.carbon_dioxide + atm.methane + atm.water_vapor;
        assert!((total - 1.0).abs() < 1e-6,
            "atmosphere total {} should be ~1.0", total);
    }
}
