//! Environmental effects simulation.
//!
//! Models temperature, radiation, atmospheric conditions, and habitability.
//! Port of the Python `simulator/environment.py`.

use rand::Rng;

use crate::constants::*;

// ---------------------------------------------------------------------------
// Environmental events
// ---------------------------------------------------------------------------

/// Types of environmental events.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EventType {
    Volcanic,
    Asteroid,
    SolarFlare,
    IceAge,
}

/// An environmental event that affects the simulation.
#[derive(Debug, Clone)]
pub struct EnvironmentalEvent {
    pub event_type: EventType,
    pub intensity: f64,
    pub duration: u32,
    pub position: [f64; 3],
    pub remaining: u32,
}

impl EnvironmentalEvent {
    pub fn is_active(&self) -> bool {
        self.remaining > 0
    }

    pub fn tick(&mut self) {
        if self.remaining > 0 {
            self.remaining -= 1;
        }
    }
}

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------

pub struct Environment {
    pub temperature: f64,
    pub uv_intensity: f64,
    pub cosmic_ray_flux: f64,
    pub stellar_wind: f64,
    pub atmospheric_density: f64,
    pub water_availability: f64,
    pub day_night_cycle: f64,
    pub season: f64,
    pub events: Vec<EnvironmentalEvent>,
    pub event_history: Vec<EnvironmentalEvent>,
    internal_tick: u64,
}

impl Environment {
    pub fn new(initial_temperature: f64) -> Self {
        Self {
            temperature: initial_temperature,
            uv_intensity: 0.0,
            cosmic_ray_flux: 0.0,
            stellar_wind: 0.0,
            atmospheric_density: 0.0,
            water_availability: 0.0,
            day_night_cycle: 0.0,
            season: 0.0,
            events: Vec::new(),
            event_history: Vec::new(),
            internal_tick: 0,
        }
    }

    /// Update environment based on cosmic epoch (tick).
    pub fn update(&mut self, epoch_tick: u64, rng: &mut impl Rng) {
        self.internal_tick += 1;

        // Temperature evolution (logarithmic cooling)
        if epoch_tick < 1_000 {
            self.temperature = T_PLANCK * (-((epoch_tick as f64) / 200.0)).exp();
        } else if epoch_tick < 50_000 {
            self.temperature = T_CMB.max(T_PLANCK * (-((epoch_tick as f64) / 200.0)).exp());
        } else if epoch_tick < 200_000 {
            self.temperature = T_CMB + gauss(rng, 0.0, 0.5);
        } else {
            self.temperature = T_EARTH_SURFACE + gauss(rng, 0.0, 5.0);
            // Day/night
            self.day_night_cycle = (self.internal_tick % 100) as f64 / 100.0;
            let temp_mod = 10.0 * (self.day_night_cycle * 2.0 * PI).sin();
            self.temperature += temp_mod;
            // Seasons
            self.season = (self.internal_tick % 1000) as f64 / 1000.0;
            let season_mod = 15.0 * (self.season * 2.0 * PI).sin();
            self.temperature += season_mod;
        }

        // UV intensity (appears with stars)
        if epoch_tick > 100_000 {
            let base_uv = 1.0;
            if self.day_night_cycle > 0.25 && self.day_night_cycle < 0.75 {
                self.uv_intensity =
                    base_uv * ((self.day_night_cycle - 0.25) * 2.0 * PI).sin();
            } else {
                self.uv_intensity = 0.0;
            }
        } else {
            self.uv_intensity = 0.0;
        }

        // Cosmic ray flux
        if epoch_tick > 10_000 {
            // Exponential random variate
            let u: f64 = rng.gen::<f64>().max(1e-15);
            self.cosmic_ray_flux = 0.1 + (-u.ln() / 10.0);
        } else {
            self.cosmic_ray_flux = 1.0;
        }

        // Atmospheric density
        if epoch_tick > 210_000 {
            self.atmospheric_density =
                ((epoch_tick - 210_000) as f64 / 50_000.0).min(1.0);
            self.uv_intensity *= 1.0 - self.atmospheric_density * 0.7;
            self.cosmic_ray_flux *= 1.0 - self.atmospheric_density * 0.5;
        }

        // Water availability
        if epoch_tick > 220_000 {
            self.water_availability =
                ((epoch_tick - 220_000) as f64 / 30_000.0).min(1.0);
        }

        // Stellar wind
        if epoch_tick > STAR_FORMATION_EPOCH {
            self.stellar_wind = 0.5 + gauss(rng, 0.0, 0.1).abs();
        }

        // Generate environmental events (only in habitable epochs)
        if epoch_tick > EARTH_EPOCH {
            // Tick existing events
            for event in &mut self.events {
                event.tick();
            }
            // Archive finished events
            let (active, finished): (Vec<_>, Vec<_>) =
                self.events.drain(..).partition(|e| e.is_active());
            self.events = active;
            self.event_history.extend(finished);

            // Volcanic
            if rng.gen::<f64>() < 0.005 {
                self.events.push(EnvironmentalEvent {
                    event_type: EventType::Volcanic,
                    intensity: rng.gen::<f64>() * 5.0,
                    duration: rng.gen_range(10..50),
                    position: [gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0), 0.0],
                    remaining: rng.gen_range(10..50),
                });
            }
            // Asteroid
            if rng.gen::<f64>() < 0.0001 {
                self.events.push(EnvironmentalEvent {
                    event_type: EventType::Asteroid,
                    intensity: rng.gen::<f64>() * 10.0,
                    duration: rng.gen_range(5..20),
                    position: [gauss(rng, 0.0, 20.0), gauss(rng, 0.0, 20.0), 0.0],
                    remaining: rng.gen_range(5..20),
                });
            }
            // Solar flare
            if rng.gen::<f64>() < 0.01 {
                self.events.push(EnvironmentalEvent {
                    event_type: EventType::SolarFlare,
                    intensity: rng.gen::<f64>() * 3.0,
                    duration: rng.gen_range(2..10),
                    position: [0.0; 3],
                    remaining: rng.gen_range(2..10),
                });
            }
            // Ice age
            if rng.gen::<f64>() < 0.001 {
                self.events.push(EnvironmentalEvent {
                    event_type: EventType::IceAge,
                    intensity: rng.gen::<f64>() * 2.0,
                    duration: rng.gen_range(50..200),
                    position: [0.0; 3],
                    remaining: rng.gen_range(50..200),
                });
            }

            // Apply event effects
            for event in &self.events {
                match event.event_type {
                    EventType::Volcanic => {
                        self.temperature += event.intensity * 0.5;
                        self.atmospheric_density = (self.atmospheric_density + 0.01).min(1.0);
                    }
                    EventType::Asteroid => {
                        self.temperature -= event.intensity * 0.3;
                        self.cosmic_ray_flux += event.intensity * 0.1;
                    }
                    EventType::SolarFlare => {
                        self.uv_intensity += event.intensity;
                        self.cosmic_ray_flux += event.intensity * 0.5;
                    }
                    EventType::IceAge => {
                        self.temperature -= event.intensity * 5.0;
                    }
                }
            }
        }
    }

    /// Check if conditions support life.
    pub fn is_habitable(&self) -> bool {
        (200.0..400.0).contains(&self.temperature)
            && self.water_availability > 0.1
            && self.get_radiation_dose() < RADIATION_DAMAGE_THRESHOLD
    }

    /// Total radiation dose.
    pub fn get_radiation_dose(&self) -> f64 {
        self.uv_intensity + self.cosmic_ray_flux
    }

    /// Thermal energy available for biological processes.
    pub fn thermal_energy(&self) -> f64 {
        if self.temperature < 100.0 || self.temperature > 500.0 {
            return 0.1;
        }
        (self.temperature * 0.1).max(0.1)
    }

    /// Compact state representation.
    pub fn to_compact(&self) -> String {
        format!(
            "Env[T={:.1} UV={:.2} CR={:.2} atm={:.2} H2O={:.2} events={}]",
            self.temperature,
            self.uv_intensity,
            self.cosmic_ray_flux,
            self.atmospheric_density,
            self.water_availability,
            self.events.len(),
        )
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn gauss(rng: &mut impl Rng, mean: f64, std: f64) -> f64 {
    let u1: f64 = rng.gen::<f64>().max(1e-15);
    let u2: f64 = rng.gen::<f64>();
    mean + std * (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::SmallRng;
    use rand::SeedableRng;

    fn make_rng() -> SmallRng {
        SmallRng::seed_from_u64(42)
    }

    #[test]
    fn test_environment_new() {
        let env = Environment::new(T_PLANCK);
        assert_eq!(env.temperature, T_PLANCK);
        assert_eq!(env.uv_intensity, 0.0);
        assert_eq!(env.cosmic_ray_flux, 0.0);
        assert_eq!(env.atmospheric_density, 0.0);
        assert_eq!(env.water_availability, 0.0);
    }

    #[test]
    fn test_environment_early_universe_cooling() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);
        let initial_temp = env.temperature;

        env.update(500, &mut rng);
        // Temperature should decrease in early universe
        assert!(env.temperature < initial_temp);
    }

    #[test]
    fn test_environment_no_uv_before_stars() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        env.update(50_000, &mut rng);
        // No UV before star formation (tick 100_000)
        assert_eq!(env.uv_intensity, 0.0);
    }

    #[test]
    fn test_environment_cosmic_rays_early() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        env.update(5_000, &mut rng);
        // Before tick 10_000: cosmic ray flux = 1.0
        assert_eq!(env.cosmic_ray_flux, 1.0);
    }

    #[test]
    fn test_environment_cosmic_rays_later() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        env.update(15_000, &mut rng);
        // After tick 10_000: cosmic ray flux should be recalculated
        assert!(env.cosmic_ray_flux > 0.0);
    }

    #[test]
    fn test_environment_atmosphere_earth() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        env.update(215_000, &mut rng);
        // Atmospheric density should be non-zero after Earth epoch (210_000)
        assert!(env.atmospheric_density > 0.0);
    }

    #[test]
    fn test_environment_water_availability() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        env.update(225_000, &mut rng);
        // Water should be available after tick 220_000
        assert!(env.water_availability > 0.0);
    }

    #[test]
    fn test_environment_is_habitable() {
        let mut env = Environment::new(T_PLANCK);
        // Create habitable conditions manually
        env.temperature = 300.0;
        env.water_availability = 0.5;
        env.uv_intensity = 1.0;
        env.cosmic_ray_flux = 1.0;

        assert!(env.is_habitable());
    }

    #[test]
    fn test_environment_not_habitable_too_hot() {
        let mut env = Environment::new(T_PLANCK);
        env.temperature = 500.0; // Too hot
        env.water_availability = 0.5;
        env.uv_intensity = 1.0;
        env.cosmic_ray_flux = 1.0;

        assert!(!env.is_habitable());
    }

    #[test]
    fn test_environment_not_habitable_no_water() {
        let mut env = Environment::new(T_PLANCK);
        env.temperature = 300.0;
        env.water_availability = 0.05; // Too little water
        env.uv_intensity = 1.0;
        env.cosmic_ray_flux = 1.0;

        assert!(!env.is_habitable());
    }

    #[test]
    fn test_environment_not_habitable_too_much_radiation() {
        let mut env = Environment::new(T_PLANCK);
        env.temperature = 300.0;
        env.water_availability = 0.5;
        env.uv_intensity = 8.0;
        env.cosmic_ray_flux = 5.0;
        // Total radiation = 13.0 > threshold 10.0

        assert!(!env.is_habitable());
    }

    #[test]
    fn test_get_radiation_dose() {
        let mut env = Environment::new(T_PLANCK);
        env.uv_intensity = 3.0;
        env.cosmic_ray_flux = 2.0;

        assert_eq!(env.get_radiation_dose(), 5.0);
    }

    #[test]
    fn test_thermal_energy() {
        let mut env = Environment::new(T_PLANCK);

        env.temperature = 50.0; // Too cold
        assert_eq!(env.thermal_energy(), 0.1);

        env.temperature = 600.0; // Too hot
        assert_eq!(env.thermal_energy(), 0.1);

        env.temperature = 300.0; // Goldilocks
        assert_eq!(env.thermal_energy(), 30.0); // 300 * 0.1
    }

    #[test]
    fn test_environment_earth_surface_temp() {
        let mut rng = make_rng();
        let mut env = Environment::new(T_PLANCK);

        // Run many updates at Earth epoch
        for _ in 0..100 {
            env.update(250_000, &mut rng);
        }
        // Temperature should be near Earth surface temperature
        assert!(env.temperature > 200.0 && env.temperature < 400.0,
                "Temperature {} should be near Earth surface temp", env.temperature);
    }
}
