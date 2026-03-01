//! Quantum and subatomic physics simulation.
//!
//! Models quantum fields, particles, pair production, annihilation,
//! and the quark-hadron transition. Lightweight port of the Python
//! `simulator/quantum.py` focused on tracking particle counts and
//! positions for rendering.

use rand::Rng;

use crate::constants::*;

// ---------------------------------------------------------------------------
// Particle types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ParticleType {
    Up,
    Down,
    Electron,
    Positron,
    Neutrino,
    Photon,
    Gluon,
    WBoson,
    ZBoson,
    Proton,
    Neutron,
}

impl ParticleType {
    pub fn mass(self) -> f64 {
        match self {
            Self::Up => M_UP_QUARK,
            Self::Down => M_DOWN_QUARK,
            Self::Electron | Self::Positron => M_ELECTRON,
            Self::Neutrino => M_NEUTRINO,
            Self::Photon | Self::Gluon => M_PHOTON,
            Self::WBoson => M_W_BOSON,
            Self::ZBoson => M_Z_BOSON,
            Self::Proton => M_PROTON,
            Self::Neutron => M_NEUTRON,
        }
    }

    pub fn charge(self) -> f64 {
        match self {
            Self::Up => 2.0 / 3.0,
            Self::Down => -1.0 / 3.0,
            Self::Electron => -1.0,
            Self::Positron => 1.0,
            Self::Proton => 1.0,
            _ => 0.0,
        }
    }

    /// Display label for HUD.
    pub fn label(self) -> &'static str {
        match self {
            Self::Up => "up",
            Self::Down => "down",
            Self::Electron => "e-",
            Self::Positron => "e+",
            Self::Neutrino => "nu",
            Self::Photon => "gamma",
            Self::Gluon => "gluon",
            Self::WBoson => "W",
            Self::ZBoson => "Z",
            Self::Proton => "p+",
            Self::Neutron => "n0",
        }
    }

    /// Color for rendering: [r, g, b, a]
    pub fn render_color(self) -> [f32; 4] {
        match self {
            Self::Up => [1.0, 0.2, 0.2, 1.0],       // red
            Self::Down => [0.2, 1.0, 0.2, 1.0],      // green
            Self::Electron => [1.0, 1.0, 0.2, 1.0],  // yellow
            Self::Positron => [1.0, 0.6, 0.2, 1.0],  // orange-ish
            Self::Neutrino => [0.6, 0.6, 1.0, 0.4],  // faint blue
            Self::Photon => [1.0, 1.0, 1.0, 0.9],    // white
            Self::Gluon => [0.3, 0.3, 1.0, 0.6],     // blue
            Self::WBoson => [0.8, 0.3, 0.8, 0.6],    // purple
            Self::ZBoson => [0.3, 0.8, 0.8, 0.6],    // cyan
            Self::Proton => [1.0, 0.55, 0.0, 1.0],   // orange
            Self::Neutron => [0.6, 0.6, 0.6, 1.0],   // gray
        }
    }

    /// Point size for rendering.
    pub fn render_size(self) -> f32 {
        match self {
            Self::Proton | Self::Neutron => 6.0,
            Self::Electron | Self::Positron => 3.0,
            Self::Up | Self::Down => 2.5,
            Self::Photon => 2.0,
            Self::Neutrino => 1.5,
            _ => 2.0,
        }
    }
}

// ---------------------------------------------------------------------------
// Color charge (for quarks)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ColorCharge {
    Red,
    Green,
    Blue,
}

// ---------------------------------------------------------------------------
// Spin
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Spin {
    Up,
    Down,
}

// ---------------------------------------------------------------------------
// Particle
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct Particle {
    pub id: u32,
    pub particle_type: ParticleType,
    pub position: [f64; 3],
    pub momentum: [f64; 3],
    pub spin: Spin,
    pub color: Option<ColorCharge>,
}

impl Particle {
    pub fn energy(&self) -> f64 {
        let p2: f64 = self.momentum.iter().map(|p| p * p).sum();
        let m = self.particle_type.mass();
        (p2 * C * C + (m * C * C).powi(2)).sqrt()
    }
}

// ---------------------------------------------------------------------------
// Quantum field
// ---------------------------------------------------------------------------

pub struct QuantumField {
    pub temperature: f64,
    pub particles: Vec<Particle>,
    pub vacuum_energy: f64,
    pub total_created: u64,
    pub total_annihilated: u64,
    next_id: u32,
}

impl QuantumField {
    pub fn new(temperature: f64) -> Self {
        Self {
            temperature,
            particles: Vec::new(),
            vacuum_energy: 0.0,
            total_created: 0,
            total_annihilated: 0,
            next_id: 1,
        }
    }

    fn alloc_id(&mut self) -> u32 {
        let id = self.next_id;
        self.next_id = self.next_id.wrapping_add(1);
        id
    }

    /// Seed the early universe with quarks and leptons.
    pub fn seed_early_universe(&mut self, rng: &mut impl Rng) {
        // 30 up quarks
        for _ in 0..30 {
            let id = self.alloc_id();
            self.particles.push(Particle {
                id,
                particle_type: ParticleType::Up,
                position: [gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0)],
                momentum: [gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0)],
                spin: random_spin(rng),
                color: Some(random_color(rng)),
            });
        }
        // 20 down quarks
        for _ in 0..20 {
            let id = self.alloc_id();
            self.particles.push(Particle {
                id,
                particle_type: ParticleType::Down,
                position: [gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0)],
                momentum: [gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0), gauss(rng, 0.0, 5.0)],
                spin: random_spin(rng),
                color: Some(random_color(rng)),
            });
        }
        // 40 electrons
        for _ in 0..40 {
            let id = self.alloc_id();
            self.particles.push(Particle {
                id,
                particle_type: ParticleType::Electron,
                position: [gauss(rng, 0.0, 2.0), gauss(rng, 0.0, 2.0), gauss(rng, 0.0, 2.0)],
                momentum: [gauss(rng, 0.0, 3.0), gauss(rng, 0.0, 3.0), gauss(rng, 0.0, 3.0)],
                spin: random_spin(rng),
                color: None,
            });
        }
        // 5 photons
        for _ in 0..5 {
            let id = self.alloc_id();
            self.particles.push(Particle {
                id,
                particle_type: ParticleType::Photon,
                position: [0.0, 0.0, 0.0],
                momentum: [gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0), gauss(rng, 0.0, 10.0)],
                spin: Spin::Up,
                color: None,
            });
        }
        self.total_created += self.particles.len() as u64;
    }

    /// Pair production from vacuum energy.
    pub fn pair_production(&mut self, energy: f64, rng: &mut impl Rng) -> bool {
        if energy < 2.0 * M_ELECTRON * C * C {
            return false;
        }

        let (p_type, ap_type) = if energy >= 2.0 * M_PROTON * C * C && rng.gen::<f64>() < 0.1 {
            (ParticleType::Up, ParticleType::Down)
        } else {
            (ParticleType::Electron, ParticleType::Positron)
        };

        let dir = [gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0), gauss(rng, 0.0, 1.0)];
        let norm = (dir[0] * dir[0] + dir[1] * dir[1] + dir[2] * dir[2]).sqrt().max(1e-10);
        let p_mag = energy / (2.0 * C);

        let id1 = self.alloc_id();
        let id2 = self.alloc_id();

        self.particles.push(Particle {
            id: id1,
            particle_type: p_type,
            position: [0.0, 0.0, 0.0],
            momentum: [dir[0] / norm * p_mag, dir[1] / norm * p_mag, dir[2] / norm * p_mag],
            spin: Spin::Up,
            color: if p_type == ParticleType::Up {
                Some(random_color(rng))
            } else {
                None
            },
        });
        self.particles.push(Particle {
            id: id2,
            particle_type: ap_type,
            position: [0.0, 0.0, 0.0],
            momentum: [
                -dir[0] / norm * p_mag,
                -dir[1] / norm * p_mag,
                -dir[2] / norm * p_mag,
            ],
            spin: Spin::Down,
            color: if ap_type == ParticleType::Down {
                Some(random_color(rng))
            } else {
                None
            },
        });

        self.total_created += 2;
        true
    }

    /// Vacuum fluctuation: spontaneous pair from vacuum energy.
    pub fn vacuum_fluctuation(&mut self, rng: &mut impl Rng) -> bool {
        let prob = (self.temperature / T_PLANCK).min(0.5);
        if rng.gen::<f64>() < prob {
            // Exponential distribution with mean = temperature * 0.001
            let lambda = 1.0 / (self.temperature * 0.001).max(1e-20);
            let energy = -lambda.recip() * (1.0 - rng.gen::<f64>()).ln();
            return self.pair_production(energy, rng);
        }
        false
    }

    /// Quark confinement: combine quarks into hadrons.
    pub fn quark_confinement(&mut self, rng: &mut impl Rng) -> Vec<Particle> {
        if self.temperature > T_QUARK_HADRON {
            return Vec::new();
        }

        let mut hadrons = Vec::new();

        // Collect indices of ups and downs
        let mut up_indices: Vec<usize> = self
            .particles
            .iter()
            .enumerate()
            .filter(|(_, p)| p.particle_type == ParticleType::Up)
            .map(|(i, _)| i)
            .collect();
        let mut down_indices: Vec<usize> = self
            .particles
            .iter()
            .enumerate()
            .filter(|(_, p)| p.particle_type == ParticleType::Down)
            .map(|(i, _)| i)
            .collect();

        let mut to_remove = Vec::new();

        // Form protons (uud)
        while up_indices.len() >= 2 && !down_indices.is_empty() {
            let u1_idx = up_indices.pop().unwrap();
            let u2_idx = up_indices.pop().unwrap();
            let d1_idx = down_indices.pop().unwrap();

            let pos = self.particles[u1_idx].position;
            let mom = [
                self.particles[u1_idx].momentum[0]
                    + self.particles[u2_idx].momentum[0]
                    + self.particles[d1_idx].momentum[0],
                self.particles[u1_idx].momentum[1]
                    + self.particles[u2_idx].momentum[1]
                    + self.particles[d1_idx].momentum[1],
                self.particles[u1_idx].momentum[2]
                    + self.particles[u2_idx].momentum[2]
                    + self.particles[d1_idx].momentum[2],
            ];

            to_remove.push(u1_idx);
            to_remove.push(u2_idx);
            to_remove.push(d1_idx);

            let id = self.alloc_id();
            let proton = Particle {
                id,
                particle_type: ParticleType::Proton,
                position: pos,
                momentum: mom,
                spin: random_spin(rng),
                color: None,
            };
            hadrons.push(proton);
        }

        // Form neutrons (udd)
        while !up_indices.is_empty() && down_indices.len() >= 2 {
            let u1_idx = up_indices.pop().unwrap();
            let d1_idx = down_indices.pop().unwrap();
            let d2_idx = down_indices.pop().unwrap();

            let pos = self.particles[u1_idx].position;
            let mom = [
                self.particles[u1_idx].momentum[0]
                    + self.particles[d1_idx].momentum[0]
                    + self.particles[d2_idx].momentum[0],
                self.particles[u1_idx].momentum[1]
                    + self.particles[d1_idx].momentum[1]
                    + self.particles[d2_idx].momentum[1],
                self.particles[u1_idx].momentum[2]
                    + self.particles[d1_idx].momentum[2]
                    + self.particles[d2_idx].momentum[2],
            ];

            to_remove.push(u1_idx);
            to_remove.push(d1_idx);
            to_remove.push(d2_idx);

            let id = self.alloc_id();
            let neutron = Particle {
                id,
                particle_type: ParticleType::Neutron,
                position: pos,
                momentum: mom,
                spin: random_spin(rng),
                color: None,
            };
            hadrons.push(neutron);
        }

        // Remove consumed quarks (sort descending to keep indices valid)
        to_remove.sort_unstable();
        to_remove.dedup();
        for &idx in to_remove.iter().rev() {
            if idx < self.particles.len() {
                self.particles.swap_remove(idx);
            }
        }

        // Add new hadrons
        for h in &hadrons {
            self.particles.push(h.clone());
        }
        self.total_created += hadrons.len() as u64;

        hadrons
    }

    /// Evolve all particles by one time step.
    pub fn evolve(&mut self, dt: f64) {
        for p in &mut self.particles {
            let m = p.particle_type.mass();
            if m > 0.0 {
                for i in 0..3 {
                    p.position[i] += p.momentum[i] / m * dt;
                }
            } else {
                let p_mag = (p.momentum[0].powi(2) + p.momentum[1].powi(2) + p.momentum[2].powi(2))
                    .sqrt()
                    .max(1e-20);
                for i in 0..3 {
                    p.position[i] += p.momentum[i] / p_mag * C * dt;
                }
            }
        }
    }

    /// Count particles by type.
    pub fn particle_counts(&self) -> Vec<(ParticleType, usize)> {
        use std::collections::HashMap;
        let mut map: HashMap<ParticleType, usize> = HashMap::new();
        for p in &self.particles {
            *map.entry(p.particle_type).or_insert(0) += 1;
        }
        let mut v: Vec<_> = map.into_iter().collect();
        v.sort_by_key(|(pt, _)| *pt as u8);
        v
    }

    /// Count of protons.
    pub fn proton_count(&self) -> usize {
        self.particles
            .iter()
            .filter(|p| p.particle_type == ParticleType::Proton)
            .count()
    }

    /// Count of neutrons.
    pub fn neutron_count(&self) -> usize {
        self.particles
            .iter()
            .filter(|p| p.particle_type == ParticleType::Neutron)
            .count()
    }

    /// Remove all protons and neutrons (after nucleosynthesis consumes them).
    pub fn remove_hadrons(&mut self) {
        self.particles.retain(|p| {
            p.particle_type != ParticleType::Proton && p.particle_type != ParticleType::Neutron
        });
    }

    /// Remove protons and electrons used in recombination.
    pub fn remove_for_recombination(&mut self, proton_count: usize, electron_count: usize) {
        let mut p_left = proton_count;
        let mut e_left = electron_count;
        self.particles.retain(|p| {
            if p_left > 0 && p.particle_type == ParticleType::Proton {
                p_left -= 1;
                return false;
            }
            if e_left > 0 && p.particle_type == ParticleType::Electron {
                e_left -= 1;
                return false;
            }
            true
        });
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn gauss(rng: &mut impl Rng, mean: f64, std: f64) -> f64 {
    // Box-Muller transform
    let u1: f64 = rng.gen::<f64>().max(1e-15);
    let u2: f64 = rng.gen::<f64>();
    mean + std * (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos()
}

fn random_spin(rng: &mut impl Rng) -> Spin {
    if rng.gen::<bool>() {
        Spin::Up
    } else {
        Spin::Down
    }
}

fn random_color(rng: &mut impl Rng) -> ColorCharge {
    match rng.gen_range(0..3) {
        0 => ColorCharge::Red,
        1 => ColorCharge::Green,
        _ => ColorCharge::Blue,
    }
}
