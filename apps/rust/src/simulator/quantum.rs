//! Quantum and subatomic physics simulation.
//!
//! Models quantum fields, particles, wave functions, superposition,
//! entanglement (simplified), and the quark-hadron transition.
//! Quantum effects influence atomic-level phenomena through
//! measurement/decoherence events.

use rand::Rng;
use std::sync::atomic::{AtomicU64, Ordering};

use super::constants::*;

// Global particle ID counter.
static PARTICLE_ID_COUNTER: AtomicU64 = AtomicU64::new(0);

fn next_particle_id() -> u64 {
    PARTICLE_ID_COUNTER.fetch_add(1, Ordering::Relaxed) + 1
}

// ---------------------------------------------------------------------------
// WaveFunction
// ---------------------------------------------------------------------------

/// Simplified quantum wave function with amplitude and phase.
#[derive(Debug, Clone)]
pub struct WaveFunction {
    pub amplitude: f64,
    pub phase: f64,
    pub coherent: bool,
}

impl Default for WaveFunction {
    fn default() -> Self {
        Self {
            amplitude: 1.0,
            phase: 0.0,
            coherent: true,
        }
    }
}

impl WaveFunction {
    /// Born rule: |psi|^2
    pub fn probability(&self) -> f64 {
        self.amplitude * self.amplitude
    }

    /// Time evolution: phase rotation by E*dt/hbar.
    pub fn evolve(&mut self, dt: f64, energy: f64) {
        if self.coherent {
            self.phase += energy * dt / HBAR;
            self.phase %= 2.0 * PI;
        }
    }

    /// Measurement: collapse to eigenstate. Returns `true` if detected.
    pub fn collapse(&mut self) -> bool {
        let mut rng = rand::thread_rng();
        let result = rng.gen::<f64>() < self.probability();
        self.amplitude = if result { 1.0 } else { 0.0 };
        self.coherent = false;
        result
    }

    /// Superposition of two states.
    pub fn superpose(&self, other: &WaveFunction) -> WaveFunction {
        let phase_diff = self.phase - other.phase;
        let combined_amp = (self.amplitude.powi(2)
            + other.amplitude.powi(2)
            + 2.0 * self.amplitude * other.amplitude * phase_diff.cos())
        .sqrt();
        let combined_phase = (self.phase + other.phase) / 2.0;
        WaveFunction {
            amplitude: combined_amp.min(1.0),
            phase: combined_phase,
            coherent: true,
        }
    }
}

// ---------------------------------------------------------------------------
// Particle
// ---------------------------------------------------------------------------

/// A quantum particle with position, momentum, and quantum numbers.
#[derive(Debug, Clone)]
pub struct Particle {
    pub particle_type: ParticleType,
    pub position: [f64; 3],
    pub momentum: [f64; 3],
    pub spin: Spin,
    pub color: Option<Color>,
    pub wave_fn: WaveFunction,
    pub entangled_with: Option<u64>,
    pub particle_id: u64,
}

impl Particle {
    pub fn new(particle_type: ParticleType) -> Self {
        Self {
            particle_type,
            position: [0.0; 3],
            momentum: [0.0; 3],
            spin: Spin::Up,
            color: None,
            wave_fn: WaveFunction::default(),
            entangled_with: None,
            particle_id: next_particle_id(),
        }
    }

    pub fn with_position(mut self, pos: [f64; 3]) -> Self {
        self.position = pos;
        self
    }

    pub fn with_momentum(mut self, mom: [f64; 3]) -> Self {
        self.momentum = mom;
        self
    }

    pub fn with_spin(mut self, spin: Spin) -> Self {
        self.spin = spin;
        self
    }

    pub fn with_color(mut self, color: Color) -> Self {
        self.color = Some(color);
        self
    }

    pub fn mass(&self) -> f64 {
        self.particle_type.mass()
    }

    pub fn charge(&self) -> f64 {
        self.particle_type.charge()
    }

    /// E = sqrt(p^2*c^2 + m^2*c^4)
    pub fn energy(&self) -> f64 {
        let p2: f64 = self.momentum.iter().map(|p| p * p).sum();
        let m = self.mass();
        (p2 * C * C + (m * C * C).powi(2)).sqrt()
    }

    /// de Broglie wavelength: lambda = h / p
    pub fn wavelength(&self) -> f64 {
        let p: f64 = self.momentum.iter().map(|p| p * p).sum::<f64>().sqrt();
        if p < 1e-20 {
            return f64::INFINITY;
        }
        2.0 * PI * HBAR / p
    }
}

// ---------------------------------------------------------------------------
// EntangledPair
// ---------------------------------------------------------------------------

/// A pair of entangled particles (EPR pair).
#[derive(Debug, Clone)]
pub struct EntangledPair {
    pub particle_a_id: u64,
    pub particle_b_id: u64,
}

// ---------------------------------------------------------------------------
// QuantumField
// ---------------------------------------------------------------------------

/// Represents a quantum field that can create and annihilate particles.
pub struct QuantumField {
    pub temperature: f64,
    pub particles: Vec<Particle>,
    pub entangled_pairs: Vec<EntangledPair>,
    pub vacuum_energy: f64,
    pub total_created: u64,
    pub total_annihilated: u64,
}

impl QuantumField {
    pub fn new(temperature: f64) -> Self {
        Self {
            temperature,
            particles: Vec::new(),
            entangled_pairs: Vec::new(),
            vacuum_energy: 0.0,
            total_created: 0,
            total_annihilated: 0,
        }
    }

    /// Create particle-antiparticle pair from vacuum energy.
    /// Requires E >= 2mc^2 for the lightest possible pair.
    pub fn pair_production(&mut self, energy: f64) -> Option<(u64, u64)> {
        if energy < 2.0 * M_ELECTRON * C * C {
            return None;
        }

        let mut rng = rand::thread_rng();

        // Determine what we can produce
        let (p_type, ap_type) =
            if energy >= 2.0 * M_PROTON * C * C && rng.gen::<f64>() < 0.1 {
                (ParticleType::Up, ParticleType::Down)
            } else {
                (ParticleType::Electron, ParticleType::Positron)
            };

        let direction: [f64; 3] = [
            rng.gen::<f64>() * 2.0 - 1.0,
            rng.gen::<f64>() * 2.0 - 1.0,
            rng.gen::<f64>() * 2.0 - 1.0,
        ];
        let norm = direction.iter().map(|d| d * d).sum::<f64>().sqrt().max(1e-10);
        let p_momentum = energy / (2.0 * C);

        let particle = Particle::new(p_type)
            .with_momentum([
                direction[0] / norm * p_momentum,
                direction[1] / norm * p_momentum,
                direction[2] / norm * p_momentum,
            ])
            .with_spin(Spin::Up);

        let antiparticle = Particle::new(ap_type)
            .with_momentum([
                -direction[0] / norm * p_momentum,
                -direction[1] / norm * p_momentum,
                -direction[2] / norm * p_momentum,
            ])
            .with_spin(Spin::Down);

        let pid = particle.particle_id;
        let apid = antiparticle.particle_id;

        let mut p = particle;
        p.entangled_with = Some(apid);
        let mut ap = antiparticle;
        ap.entangled_with = Some(pid);

        self.particles.push(p);
        self.particles.push(ap);
        self.entangled_pairs.push(EntangledPair {
            particle_a_id: pid,
            particle_b_id: apid,
        });
        self.total_created += 2;

        Some((pid, apid))
    }

    /// Annihilate particle-antiparticle pair, returning energy.
    pub fn annihilate(&mut self, idx_a: usize, idx_b: usize) -> f64 {
        // Ensure idx_a > idx_b so removal order is safe.
        let (first, second) = if idx_a > idx_b {
            (idx_a, idx_b)
        } else {
            (idx_b, idx_a)
        };

        let energy = self.particles[first].energy() + self.particles[second].energy();
        self.particles.remove(first);
        self.particles.remove(second);
        self.total_annihilated += 2;
        self.vacuum_energy += energy * 0.01;

        // Create photons from annihilation
        let photon1 = Particle::new(ParticleType::Photon)
            .with_momentum([energy / (2.0 * C), 0.0, 0.0]);
        let photon2 = Particle::new(ParticleType::Photon)
            .with_momentum([-energy / (2.0 * C), 0.0, 0.0]);
        self.particles.push(photon1);
        self.particles.push(photon2);

        energy
    }

    /// Combine quarks into hadrons when temperature drops enough.
    pub fn quark_confinement(&mut self) -> Vec<Particle> {
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
        let mut new_particles = Vec::new();

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

            let proton = Particle::new(ParticleType::Proton)
                .with_position(pos)
                .with_momentum(mom);
            hadrons.push(proton.clone());
            new_particles.push(proton);
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

            let neutron = Particle::new(ParticleType::Neutron)
                .with_position(pos)
                .with_momentum(mom);
            hadrons.push(neutron.clone());
            new_particles.push(neutron);
        }

        // Remove quarks (sort descending so indices stay valid)
        to_remove.sort_unstable();
        to_remove.dedup();
        for idx in to_remove.into_iter().rev() {
            self.particles.remove(idx);
        }

        self.particles.extend(new_particles);
        hadrons
    }

    /// Spontaneous virtual particle pair from vacuum energy.
    pub fn vacuum_fluctuation(&mut self) -> Option<(u64, u64)> {
        let mut rng = rand::thread_rng();
        let prob = (self.temperature / T_PLANCK).min(0.5);
        if rng.gen::<f64>() < prob {
            let lambda = 1.0 / (self.temperature * 0.001).max(1e-20);
            let energy = -lambda * rng.gen::<f64>().ln(); // exponential variate
            self.pair_production(energy)
        } else {
            None
        }
    }

    /// Environmental decoherence of a particle's wave function.
    pub fn decohere(&mut self, idx: usize, environment_coupling: f64) {
        let temp = self.temperature;
        let p = &mut self.particles[idx];
        if p.wave_fn.coherent {
            let decoherence_rate = environment_coupling * temp;
            let mut rng = rand::thread_rng();
            if rng.gen::<f64>() < decoherence_rate {
                p.wave_fn.collapse();
            }
        }
    }

    /// Cool the field (universe expansion).
    pub fn cool(&mut self, factor: f64) {
        self.temperature *= factor;
    }

    /// Evolve all particles by one time step.
    pub fn evolve(&mut self, dt: f64) {
        for p in &mut self.particles {
            let mass = p.mass();
            if mass > 0.0 {
                for i in 0..3 {
                    p.position[i] += p.momentum[i] / mass * dt;
                }
            } else {
                // Massless particles move at c
                let p_mag = p.momentum.iter().map(|x| x * x).sum::<f64>().sqrt().max(1e-20);
                for i in 0..3 {
                    p.position[i] += p.momentum[i] / p_mag * C * dt;
                }
            }

            let energy = p.energy();
            p.wave_fn.evolve(dt, energy);
        }
    }

    /// Count particles by type.
    pub fn particle_count(&self) -> std::collections::HashMap<ParticleType, usize> {
        let mut counts = std::collections::HashMap::new();
        for p in &self.particles {
            *counts.entry(p.particle_type).or_insert(0) += 1;
        }
        counts
    }

    /// Total energy in the field.
    pub fn total_energy(&self) -> f64 {
        self.particles.iter().map(|p| p.energy()).sum::<f64>() + self.vacuum_energy
    }

    /// Compact state representation.
    pub fn to_compact(&self) -> String {
        let counts = self.particle_count();
        let mut parts: Vec<String> = counts
            .iter()
            .map(|(k, v)| format!("{}:{}", k.label(), v))
            .collect();
        parts.sort();
        format!(
            "QF[T={:.1e} E={:.1e} n={} {}]",
            self.temperature,
            self.total_energy(),
            self.particles.len(),
            parts.join(",")
        )
    }
}
