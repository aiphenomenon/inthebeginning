#include "quantum.hpp"

#include <algorithm>
#include <cmath>
#include <random>

namespace sim {

// Thread-local RNG
static std::mt19937& rng() {
    static thread_local std::mt19937 gen{42};
    return gen;
}

static double randUniform() {
    static thread_local std::uniform_real_distribution<double> dist(0.0, 1.0);
    return dist(rng());
}

static double randGauss(double mean, double stddev) {
    std::normal_distribution<double> dist(mean, stddev);
    return dist(rng());
}

static double randExpovariate(double lambda) {
    std::exponential_distribution<double> dist(lambda);
    return dist(rng());
}

// ============================================================
// WaveFunction
// ============================================================

void WaveFunction::evolve(double dt, double energy) {
    if (coherent) {
        phase += energy * dt / HBAR;
        phase = std::fmod(phase, 2.0 * PI);
    }
}

bool WaveFunction::collapse() {
    bool result = randUniform() < probability();
    amplitude = result ? 1.0 : 0.0;
    coherent = false;
    return result;
}

WaveFunction WaveFunction::superpose(const WaveFunction& other) const {
    double phaseDiff = phase - other.phase;
    double combinedAmp = std::sqrt(
        amplitude * amplitude + other.amplitude * other.amplitude
        + 2.0 * amplitude * other.amplitude * std::cos(phaseDiff)
    );
    double combinedPhase = (phase + other.phase) / 2.0;
    return WaveFunction{
        std::min(combinedAmp, 1.0),
        combinedPhase,
        true
    };
}

// ============================================================
// Particle
// ============================================================

double Particle::energy() const {
    double p2 = momentum[0]*momentum[0] + momentum[1]*momentum[1]
              + momentum[2]*momentum[2];
    double m = mass();
    return std::sqrt(p2 * C * C + m * m * C * C * C * C);
}

double Particle::wavelength() const {
    double p = std::sqrt(momentum[0]*momentum[0] + momentum[1]*momentum[1]
                       + momentum[2]*momentum[2]);
    if (p < 1e-20) return 1e30; // effectively infinite
    return 2.0 * PI * HBAR / p;
}

// ============================================================
// QuantumField
// ============================================================

QuantumField::QuantumField(double temp)
    : temperature(temp) {}

int QuantumField::nextParticleId() { return ++nextId_; }

bool QuantumField::pairProduction(double energy) {
    if (energy < 2.0 * M_ELECTRON * C * C)
        return false;

    ParticleType pType, apType;
    if (energy >= 2.0 * M_PROTON * C * C && randUniform() < 0.1) {
        pType  = ParticleType::Up;
        apType = ParticleType::Down;
    } else {
        pType  = ParticleType::Electron;
        apType = ParticleType::Positron;
    }

    double dx = randGauss(0, 1);
    double dy = randGauss(0, 1);
    double dz = randGauss(0, 1);
    double norm = std::sqrt(dx*dx + dy*dy + dz*dz);
    if (norm < 1e-20) norm = 1.0;
    double pMom = energy / (2.0 * C);

    Particle particle;
    particle.type = pType;
    particle.momentum = {dx/norm * pMom, dy/norm * pMom, dz/norm * pMom};
    particle.spin = Spin::Up;
    particle.particleId = nextParticleId();

    Particle antiparticle;
    antiparticle.type = apType;
    antiparticle.momentum = {-dx/norm * pMom, -dy/norm * pMom, -dz/norm * pMom};
    antiparticle.spin = Spin::Down;
    antiparticle.particleId = nextParticleId();

    particle.entangledWith = antiparticle.particleId;
    antiparticle.entangledWith = particle.particleId;

    particles.push_back(particle);
    particles.push_back(antiparticle);
    totalCreated += 2;
    return true;
}

double QuantumField::annihilate(size_t idx1, size_t idx2) {
    if (idx1 >= particles.size() || idx2 >= particles.size() || idx1 == idx2)
        return 0.0;

    double e = particles[idx1].energy() + particles[idx2].energy();
    vacuumEnergy += e * 0.01;

    // Remove in reverse order to keep indices valid
    if (idx1 > idx2) std::swap(idx1, idx2);
    particles.erase(particles.begin() + static_cast<long>(idx2));
    particles.erase(particles.begin() + static_cast<long>(idx1));
    totalAnnihilated += 2;

    // Create photons from annihilation
    Particle ph1;
    ph1.type = ParticleType::Photon;
    ph1.momentum = {e / (2.0 * C), 0.0, 0.0};
    ph1.particleId = nextParticleId();

    Particle ph2;
    ph2.type = ParticleType::Photon;
    ph2.momentum = {-e / (2.0 * C), 0.0, 0.0};
    ph2.particleId = nextParticleId();

    particles.push_back(ph1);
    particles.push_back(ph2);

    return e;
}

std::vector<Particle> QuantumField::quarkConfinement() {
    if (temperature > T_QUARK_HADRON) return {};

    std::vector<Particle> hadrons;

    // Collect ups and downs
    std::vector<size_t> upIdx, downIdx;
    for (size_t i = 0; i < particles.size(); ++i) {
        if (particles[i].type == ParticleType::Up)   upIdx.push_back(i);
        if (particles[i].type == ParticleType::Down)  downIdx.push_back(i);
    }

    std::vector<size_t> toRemove;

    // Form protons (uud)
    while (upIdx.size() >= 2 && downIdx.size() >= 1) {
        size_t ui1 = upIdx.back(); upIdx.pop_back();
        size_t ui2 = upIdx.back(); upIdx.pop_back();
        size_t di1 = downIdx.back(); downIdx.pop_back();

        auto& u1 = particles[ui1];
        auto& u2 = particles[ui2];
        auto& d1 = particles[di1];

        Particle proton;
        proton.type = ParticleType::Proton;
        proton.position = u1.position;
        proton.momentum = {
            u1.momentum[0] + u2.momentum[0] + d1.momentum[0],
            u1.momentum[1] + u2.momentum[1] + d1.momentum[1],
            u1.momentum[2] + u2.momentum[2] + d1.momentum[2],
        };
        proton.particleId = nextParticleId();

        hadrons.push_back(proton);
        toRemove.push_back(ui1);
        toRemove.push_back(ui2);
        toRemove.push_back(di1);
    }

    // Form neutrons (udd)
    while (upIdx.size() >= 1 && downIdx.size() >= 2) {
        size_t ui1 = upIdx.back(); upIdx.pop_back();
        size_t di1 = downIdx.back(); downIdx.pop_back();
        size_t di2 = downIdx.back(); downIdx.pop_back();

        auto& u1 = particles[ui1];
        auto& d1 = particles[di1];
        auto& d2 = particles[di2];

        Particle neutron;
        neutron.type = ParticleType::Neutron;
        neutron.position = u1.position;
        neutron.momentum = {
            u1.momentum[0] + d1.momentum[0] + d2.momentum[0],
            u1.momentum[1] + d1.momentum[1] + d2.momentum[1],
            u1.momentum[2] + d1.momentum[2] + d2.momentum[2],
        };
        neutron.particleId = nextParticleId();

        hadrons.push_back(neutron);
        toRemove.push_back(ui1);
        toRemove.push_back(di1);
        toRemove.push_back(di2);
    }

    // Remove quarks (reverse sort so indices stay valid)
    std::sort(toRemove.begin(), toRemove.end(), std::greater<>());
    for (auto idx : toRemove) {
        particles.erase(particles.begin() + static_cast<long>(idx));
    }

    // Add hadrons
    for (auto& h : hadrons) {
        particles.push_back(h);
    }

    return hadrons;
}

bool QuantumField::vacuumFluctuation() {
    double prob = std::min(0.5, temperature / T_PLANCK);
    if (randUniform() < prob) {
        double lambda = 1.0 / (temperature * 0.001);
        if (lambda <= 0.0) lambda = 1.0;
        double energy = randExpovariate(lambda);
        return pairProduction(energy);
    }
    return false;
}

void QuantumField::evolve(double dt) {
    for (auto& p : particles) {
        double m = p.mass();
        if (m > 0.0) {
            for (int i = 0; i < 3; ++i) {
                p.position[i] += p.momentum[i] / m * dt;
            }
        } else {
            double pMag = std::sqrt(p.momentum[0]*p.momentum[0]
                                  + p.momentum[1]*p.momentum[1]
                                  + p.momentum[2]*p.momentum[2]);
            if (pMag < 1e-20) pMag = 1.0;
            for (int i = 0; i < 3; ++i) {
                p.position[i] += p.momentum[i] / pMag * C * dt;
            }
        }
        p.waveFn.evolve(dt, p.energy());
    }
}

double QuantumField::totalEnergy() const {
    double total = vacuumEnergy;
    for (auto& p : particles) {
        total += p.energy();
    }
    return total;
}

} // namespace sim
