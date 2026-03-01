//! Environmental effects simulation.
//!
//! Models temperature, radiation, atmospheric conditions, and habitability.
//! Port of the Python `simulator/environment.py`.

use rand::Rng;

use crate::constants::*;

// ---------------------------------------------------------------------------
// Environment
// ---------------------------------------------------------------------------

pub struct Environment {
    pub temperature: f64,
    pub uv_intensity: f64,
    pub cosmic_ray_flux: f64,
    pub atmospheric_density: f64,
    pub water_availability: f64,
    pub day_night_cycle: f64,
    pub season: f64,
    internal_tick: u64,
}

impl Environment {
    pub fn new(initial_temperature: f64) -> Self {
        Self {
            temperature: initial_temperature,
            uv_intensity: 0.0,
            cosmic_ray_flux: 0.0,
            atmospheric_density: 0.0,
            water_availability: 0.0,
            day_night_cycle: 0.0,
            season: 0.0,
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
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn gauss(rng: &mut impl Rng, mean: f64, std: f64) -> f64 {
    let u1: f64 = rng.gen::<f64>().max(1e-15);
    let u2: f64 = rng.gen::<f64>();
    mean + std * (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
}
