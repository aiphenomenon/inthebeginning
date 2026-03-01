#include "atomic.hpp"

#include <algorithm>
#include <cmath>
#include <random>

namespace sim {

static thread_local std::mt19937& rng() {
    static thread_local std::mt19937 gen{123};
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

// ============================================================
// Atom
// ============================================================

void Atom::init(int z, int mass, std::array<double,3> pos, std::array<double,3> vel) {
    atomicNumber = z;
    position = pos;
    velocity = vel;

    if (mass == 0) {
        massNumber = (z == 1) ? 1 : z * 2;
    } else {
        massNumber = mass;
    }

    electronCount = atomicNumber;  // neutral
    buildShells();
    computeIonizationEnergy();
}

void Atom::buildShells() {
    shells.clear();
    int remaining = electronCount;
    for (size_t i = 0; i < ELECTRON_SHELLS.size(); ++i) {
        if (remaining <= 0) break;
        ElectronShell sh;
        sh.n = static_cast<int>(i) + 1;
        sh.maxElectrons = ELECTRON_SHELLS[i];
        sh.electrons = std::min(remaining, sh.maxElectrons);
        shells.push_back(sh);
        remaining -= sh.electrons;
    }
}

void Atom::computeIonizationEnergy() {
    if (shells.empty() || shells.back().isEmpty()) {
        ionizationEnergy = 0.0;
        return;
    }
    int n = shells.back().n;
    int shielding = 0;
    for (size_t i = 0; i + 1 < shells.size(); ++i)
        shielding += shells[i].electrons;
    double zEff = static_cast<double>(atomicNumber - shielding);
    ionizationEnergy = 13.6 * zEff * zEff / (n * n);
}

const char* Atom::symbol() const {
    auto& el = elements();
    auto it = el.find(atomicNumber);
    return it != el.end() ? it->second.symbol : "?";
}

const char* Atom::name() const {
    auto& el = elements();
    auto it = el.find(atomicNumber);
    return it != el.end() ? it->second.name : "Unknown";
}

double Atom::electronegativity() const {
    auto& el = elements();
    auto it = el.find(atomicNumber);
    return it != el.end() ? it->second.electronegativity : 1.0;
}

int Atom::valenceElectrons() const {
    if (shells.empty()) return 0;
    return shells.back().electrons;
}

int Atom::needsElectrons() const {
    if (shells.empty()) return 0;
    return shells.back().maxElectrons - shells.back().electrons;
}

bool Atom::isNobleGas() const {
    if (shells.empty()) return false;
    return shells.back().isFull();
}

bool Atom::canBondWith(const Atom& other) const {
    if (isNobleGas() || other.isNobleGas()) return false;
    if (bonds.size() >= 4 || other.bonds.size() >= 4) return false;
    return true;
}

std::string Atom::bondType(const Atom& other) const {
    double diff = std::abs(electronegativity() - other.electronegativity());
    if (diff > 1.7) return "ionic";
    if (diff > 0.4) return "polar_covalent";
    return "covalent";
}

double Atom::bondEnergy(const Atom& other) const {
    auto bt = bondType(other);
    if (bt == "ionic") return BOND_ENERGY_IONIC;
    if (bt == "polar_covalent") return (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2.0;
    return BOND_ENERGY_COVALENT;
}

double Atom::distanceTo(const Atom& other) const {
    double dx = position[0] - other.position[0];
    double dy = position[1] - other.position[1];
    double dz = position[2] - other.position[2];
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

bool Atom::ionize() {
    if (electronCount > 0) {
        --electronCount;
        buildShells();
        computeIonizationEnergy();
        return true;
    }
    return false;
}

bool Atom::captureElectron() {
    ++electronCount;
    buildShells();
    computeIonizationEnergy();
    return true;
}

// ============================================================
// AtomicSystem
// ============================================================

AtomicSystem::AtomicSystem(double temp)
    : temperature(temp) {}

int AtomicSystem::nextAtomId() { return ++nextId_; }

std::vector<Atom> AtomicSystem::recombination(QuantumField& field) {
    if (temperature > T_RECOMBINATION) return {};

    std::vector<Atom> newAtoms;

    std::vector<size_t> protonIdx, electronIdx;
    for (size_t i = 0; i < field.particles.size(); ++i) {
        if (field.particles[i].type == ParticleType::Proton)   protonIdx.push_back(i);
        if (field.particles[i].type == ParticleType::Electron) electronIdx.push_back(i);
    }

    std::vector<size_t> toRemove;
    size_t eIdx = 0;
    for (auto pi : protonIdx) {
        if (eIdx >= electronIdx.size()) break;

        Atom atom;
        atom.atomId = nextAtomId();
        atom.init(1, 1, field.particles[pi].position,
                  field.particles[pi].momentum);
        newAtoms.push_back(atom);
        atoms.push_back(atom);

        toRemove.push_back(pi);
        toRemove.push_back(electronIdx[eIdx]);
        ++eIdx;
    }

    // Remove consumed particles (reverse order)
    std::sort(toRemove.begin(), toRemove.end(), std::greater<>());
    // Deduplicate
    toRemove.erase(std::unique(toRemove.begin(), toRemove.end()), toRemove.end());
    for (auto idx : toRemove) {
        if (idx < field.particles.size())
            field.particles.erase(field.particles.begin() + static_cast<long>(idx));
    }

    return newAtoms;
}

std::vector<Atom> AtomicSystem::nucleosynthesis(int protons, int neutrons) {
    std::vector<Atom> newAtoms;

    // He-4: 2p + 2n
    while (protons >= 2 && neutrons >= 2) {
        Atom he;
        he.atomId = nextAtomId();
        he.init(2, 4, {randGauss(0,10), randGauss(0,10), randGauss(0,10)});
        newAtoms.push_back(he);
        atoms.push_back(he);
        protons  -= 2;
        neutrons -= 2;
    }

    // Remaining protons -> hydrogen
    for (int i = 0; i < protons; ++i) {
        Atom h;
        h.atomId = nextAtomId();
        h.init(1, 1, {randGauss(0,10), randGauss(0,10), randGauss(0,10)});
        newAtoms.push_back(h);
        atoms.push_back(h);
    }

    return newAtoms;
}

std::vector<Atom> AtomicSystem::stellarNucleosynthesis(double temp) {
    std::vector<Atom> newAtoms;
    if (temp < 1e3) return newAtoms;

    // Triple-alpha: 3 He -> C
    {
        std::vector<size_t> heIdx;
        for (size_t i = 0; i < atoms.size(); ++i)
            if (atoms[i].atomicNumber == 2) heIdx.push_back(i);

        while (heIdx.size() >= 3 && randUniform() < 0.01) {
            std::vector<size_t> used;
            for (int k = 0; k < 3; ++k) {
                used.push_back(heIdx.back());
                heIdx.pop_back();
            }
            // Remove heliums (reverse)
            std::sort(used.begin(), used.end(), std::greater<>());
            for (auto idx : used)
                atoms.erase(atoms.begin() + static_cast<long>(idx));

            Atom c;
            c.atomId = nextAtomId();
            c.init(6, 12, {randGauss(0,5), randGauss(0,5), randGauss(0,5)});
            newAtoms.push_back(c);
            atoms.push_back(c);

            // Rebuild heIdx
            heIdx.clear();
            for (size_t i = 0; i < atoms.size(); ++i)
                if (atoms[i].atomicNumber == 2) heIdx.push_back(i);
        }
    }

    // C + He -> O
    {
        auto findFirst = [&](int z) -> int {
            for (size_t i = 0; i < atoms.size(); ++i)
                if (atoms[i].atomicNumber == z) return static_cast<int>(i);
            return -1;
        };

        while (randUniform() < 0.02) {
            int ci = findFirst(6);
            int hi = findFirst(2);
            if (ci < 0 || hi < 0) break;

            auto pos = atoms[ci].position;
            if (ci > hi) { atoms.erase(atoms.begin()+ci); atoms.erase(atoms.begin()+hi); }
            else         { atoms.erase(atoms.begin()+hi); atoms.erase(atoms.begin()+ci); }

            Atom o;
            o.atomId = nextAtomId();
            o.init(8, 16, pos);
            newAtoms.push_back(o);
            atoms.push_back(o);
        }
    }

    // O + He -> N (simplified chain)
    {
        auto findFirst = [&](int z) -> int {
            for (size_t i = 0; i < atoms.size(); ++i)
                if (atoms[i].atomicNumber == z) return static_cast<int>(i);
            return -1;
        };

        if (randUniform() < 0.005) {
            int oi = findFirst(8);
            int hi = findFirst(2);
            if (oi >= 0 && hi >= 0) {
                auto pos = atoms[oi].position;
                if (oi > hi) { atoms.erase(atoms.begin()+oi); atoms.erase(atoms.begin()+hi); }
                else         { atoms.erase(atoms.begin()+hi); atoms.erase(atoms.begin()+oi); }

                Atom n;
                n.atomId = nextAtomId();
                n.init(7, 14, pos);
                newAtoms.push_back(n);
                atoms.push_back(n);
            }
        }
    }

    return newAtoms;
}

} // namespace sim
