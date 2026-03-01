#pragma once
/// Quantum and subatomic physics simulation.
///
/// Models quantum fields, particles, wave functions, superposition,
/// entanglement (simplified), and the quark-hadron transition.

#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <vector>

#include "constants.hpp"

namespace sim {

// ============================================================
// WaveFunction
// ============================================================
struct WaveFunction {
    double amplitude = 1.0;
    double phase     = 0.0;
    bool   coherent  = true;

    /// Born rule: |psi|^2
    [[nodiscard]] double probability() const { return amplitude * amplitude; }

    /// Time evolution: phase rotation by E*dt/hbar.
    void evolve(double dt, double energy);

    /// Measurement: collapse to eigenstate.  Returns true if "detected".
    bool collapse();

    /// Superposition of two states (interference).
    [[nodiscard]] WaveFunction superpose(const WaveFunction& other) const;
};

// ============================================================
// Particle
// ============================================================
struct Particle {
    ParticleType type     = ParticleType::Photon;
    std::array<double, 3> position = {0.0, 0.0, 0.0};
    std::array<double, 3> momentum = {0.0, 0.0, 0.0};
    Spin         spin     = Spin::Up;
    Color        color    = Color::None;
    WaveFunction waveFn;
    int          entangledWith = -1;   // id of entangled partner, -1 = none
    int          particleId    = 0;

    [[nodiscard]] double mass()   const { return particleMass(type); }
    [[nodiscard]] double charge() const { return particleCharge(type); }

    /// E = sqrt(p^2 c^2 + m^2 c^4)
    [[nodiscard]] double energy() const;

    /// de Broglie wavelength
    [[nodiscard]] double wavelength() const;
};

// ============================================================
// QuantumField
// ============================================================
class QuantumField {
public:
    explicit QuantumField(double temperature = T_PLANCK);

    /// Pair production from vacuum energy.  Returns true on success.
    bool pairProduction(double energy);

    /// Annihilate particle-antiparticle pair, returning energy released.
    double annihilate(size_t idx1, size_t idx2);

    /// Combine quarks into hadrons when T drops below T_QUARK_HADRON.
    std::vector<Particle> quarkConfinement();

    /// Spontaneous virtual pair from vacuum energy.
    bool vacuumFluctuation();

    /// Evolve all particles by one time step.
    void evolve(double dt = 1.0);

    /// Total energy in the field.
    [[nodiscard]] double totalEnergy() const;

    // --- Public state ---
    double                temperature;
    std::vector<Particle> particles;
    double                vacuumEnergy    = 0.0;
    int                   totalCreated    = 0;
    int                   totalAnnihilated= 0;

private:
    int nextId_ = 0;
    int nextParticleId();
};

} // namespace sim
