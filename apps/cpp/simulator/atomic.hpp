#pragma once
/// Atomic physics simulation.
///
/// Models atoms with electron shells, ionization, chemical bonding potential,
/// and the periodic table. Atoms emerge from the quantum/nuclear level
/// when temperature drops below recombination threshold.

#include <cmath>
#include <string>
#include <vector>

#include "constants.hpp"
#include "quantum.hpp"

namespace sim {

// ============================================================
// ElectronShell
// ============================================================
struct ElectronShell {
    int n             = 1;  // Principal quantum number
    int maxElectrons  = 2;  // 2n^2
    int electrons     = 0;

    [[nodiscard]] bool isFull()  const { return electrons >= maxElectrons; }
    [[nodiscard]] bool isEmpty() const { return electrons == 0; }

    bool addElectron()    { if (!isFull())  { ++electrons; return true; } return false; }
    bool removeElectron() { if (!isEmpty()) { --electrons; return true; } return false; }
};

// ============================================================
// Atom
// ============================================================
struct Atom {
    int atomicNumber   = 1;
    int massNumber     = 0;
    int electronCount  = 0;
    std::array<double, 3> position = {0.0, 0.0, 0.0};
    std::array<double, 3> velocity = {0.0, 0.0, 0.0};
    std::vector<ElectronShell> shells;
    std::vector<int> bonds;       // IDs of bonded atoms
    int    atomId            = 0;
    double ionizationEnergy  = 0.0;

    /// Construct and initialise shells.
    void init(int z, int mass = 0,
              std::array<double, 3> pos = {0,0,0},
              std::array<double, 3> vel = {0,0,0});

    [[nodiscard]] const char* symbol()   const;
    [[nodiscard]] const char* name()     const;
    [[nodiscard]] double electronegativity() const;
    [[nodiscard]] int  chargeState()       const { return atomicNumber - electronCount; }
    [[nodiscard]] int  valenceElectrons()   const;
    [[nodiscard]] int  needsElectrons()     const;
    [[nodiscard]] bool isNobleGas()         const;
    [[nodiscard]] bool isIon()              const { return chargeState() != 0; }

    [[nodiscard]] bool canBondWith(const Atom& other) const;
    [[nodiscard]] std::string bondType(const Atom& other) const;
    [[nodiscard]] double bondEnergy(const Atom& other) const;
    [[nodiscard]] double distanceTo(const Atom& other) const;

    bool ionize();
    bool captureElectron();

private:
    void buildShells();
    void computeIonizationEnergy();
};

// ============================================================
// AtomicSystem
// ============================================================
class AtomicSystem {
public:
    explicit AtomicSystem(double temperature = T_RECOMBINATION);

    /// Capture free electrons into ions when T < T_recombination.
    std::vector<Atom> recombination(QuantumField& field);

    /// Form helium / hydrogen from protons + neutrons.
    std::vector<Atom> nucleosynthesis(int protons, int neutrons);

    /// Form heavier elements in stellar cores.
    std::vector<Atom> stellarNucleosynthesis(double temperature);

    // --- Public state ---
    std::vector<Atom> atoms;
    double temperature;
    int bondsFormed  = 0;
    int bondsBroken  = 0;

private:
    int nextId_ = 0;
    int nextAtomId();
};

} // namespace sim
