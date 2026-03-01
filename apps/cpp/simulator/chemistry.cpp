#include "chemistry.hpp"

#include <algorithm>
#include <cmath>
#include <random>

namespace sim {

static thread_local std::mt19937& rng() {
    static thread_local std::mt19937 gen{456};
    return gen;
}

static double randUniform() {
    static thread_local std::uniform_real_distribution<double> dist(0.0, 1.0);
    return dist(rng());
}

// ============================================================
// ChemicalSystem
// ============================================================

ChemicalSystem::ChemicalSystem(AtomicSystem& as)
    : atomic(as) {}

int ChemicalSystem::nextMoleculeId() { return ++nextId_; }

std::vector<size_t> ChemicalSystem::findUnbonded(int z) const {
    std::vector<size_t> result;
    for (size_t i = 0; i < atomic.atoms.size(); ++i) {
        if (atomic.atoms[i].atomicNumber == z && atomic.atoms[i].bonds.empty())
            result.push_back(i);
    }
    return result;
}

std::vector<size_t> ChemicalSystem::findWithBondsBelow(int z, size_t maxBonds) const {
    std::vector<size_t> result;
    for (size_t i = 0; i < atomic.atoms.size(); ++i) {
        if (atomic.atoms[i].atomicNumber == z && atomic.atoms[i].bonds.size() < maxBonds)
            result.push_back(i);
    }
    return result;
}

std::vector<Molecule> ChemicalSystem::formWater() {
    std::vector<Molecule> waters;

    auto hydrogens = findUnbonded(1);
    auto oxygens   = findWithBondsBelow(8, 2);

    while (hydrogens.size() >= 2 && !oxygens.empty()) {
        size_t hi1 = hydrogens.back(); hydrogens.pop_back();
        size_t hi2 = hydrogens.back(); hydrogens.pop_back();
        size_t oi  = oxygens.back();   oxygens.pop_back();

        auto& h1 = atomic.atoms[hi1];
        auto& h2 = atomic.atoms[hi2];
        auto& o  = atomic.atoms[oi];

        Molecule water;
        water.moleculeId = nextMoleculeId();
        water.name = "water";
        water.formula = "H2O";
        water.position = o.position;
        water.atomIds = {h1.atomId, h2.atomId, o.atomId};

        h1.bonds.push_back(o.atomId);
        h2.bonds.push_back(o.atomId);
        o.bonds.push_back(h1.atomId);
        o.bonds.push_back(h2.atomId);

        waters.push_back(water);
        molecules.push_back(water);
        ++waterCount;
    }

    return waters;
}

std::vector<Molecule> ChemicalSystem::formMethane() {
    std::vector<Molecule> methanes;

    auto carbons   = findUnbonded(6);
    auto hydrogens = findUnbonded(1);

    while (!carbons.empty() && hydrogens.size() >= 4) {
        size_t ci = carbons.back(); carbons.pop_back();

        std::vector<size_t> hIndices;
        for (int k = 0; k < 4; ++k) {
            hIndices.push_back(hydrogens.back());
            hydrogens.pop_back();
        }

        auto& c = atomic.atoms[ci];
        Molecule methane;
        methane.moleculeId = nextMoleculeId();
        methane.name = "methane";
        methane.formula = "CH4";
        methane.position = c.position;
        methane.isOrganic = true;
        methane.atomIds.push_back(c.atomId);

        for (auto hi : hIndices) {
            auto& h = atomic.atoms[hi];
            c.bonds.push_back(h.atomId);
            h.bonds.push_back(c.atomId);
            methane.atomIds.push_back(h.atomId);
        }

        methanes.push_back(methane);
        molecules.push_back(methane);
    }

    return methanes;
}

std::vector<Molecule> ChemicalSystem::formAmmonia() {
    std::vector<Molecule> ammonias;

    auto nitrogens = findUnbonded(7);
    auto hydrogens = findUnbonded(1);

    while (!nitrogens.empty() && hydrogens.size() >= 3) {
        size_t ni = nitrogens.back(); nitrogens.pop_back();

        std::vector<size_t> hIndices;
        for (int k = 0; k < 3; ++k) {
            hIndices.push_back(hydrogens.back());
            hydrogens.pop_back();
        }

        auto& n = atomic.atoms[ni];
        Molecule ammonia;
        ammonia.moleculeId = nextMoleculeId();
        ammonia.name = "ammonia";
        ammonia.formula = "NH3";
        ammonia.position = n.position;
        ammonia.atomIds.push_back(n.atomId);

        for (auto hi : hIndices) {
            auto& h = atomic.atoms[hi];
            n.bonds.push_back(h.atomId);
            h.bonds.push_back(n.atomId);
            ammonia.atomIds.push_back(h.atomId);
        }

        ammonias.push_back(ammonia);
        molecules.push_back(ammonia);
    }

    return ammonias;
}

bool ChemicalSystem::formAminoAcid(const std::string& aaType) {
    // Glycine-like: 2C + 5H + 2O + 1N minimum
    auto carbons   = findUnbonded(6);
    auto hydrogens = findUnbonded(1);
    auto oxygens   = findWithBondsBelow(8, 2);
    auto nitrogens = findUnbonded(7);

    if (carbons.size() < 2 || hydrogens.size() < 5 ||
        oxygens.size() < 2 || nitrogens.empty())
        return false;

    Molecule aa;
    aa.moleculeId = nextMoleculeId();
    aa.name = aaType;
    aa.isOrganic = true;
    aa.functionalGroups = {"amino", "carboxyl"};

    // Use atoms: 2C, 5H, 2O, 1N
    std::vector<size_t> used;
    for (int k = 0; k < 2; ++k) { used.push_back(carbons.back()); carbons.pop_back(); }
    for (int k = 0; k < 5; ++k) { used.push_back(hydrogens.back()); hydrogens.pop_back(); }
    for (int k = 0; k < 2; ++k) { used.push_back(oxygens.back()); oxygens.pop_back(); }
    used.push_back(nitrogens.back()); nitrogens.pop_back();

    aa.position = atomic.atoms[used[0]].position;
    int firstId = atomic.atoms[used[0]].atomId;
    for (auto idx : used) {
        auto& a = atomic.atoms[idx];
        aa.atomIds.push_back(a.atomId);
        // Bond all to the first atom (simplified)
        if (a.atomId != firstId) {
            atomic.atoms[used[0]].bonds.push_back(a.atomId);
            a.bonds.push_back(firstId);
        }
    }

    molecules.push_back(aa);
    ++aminoAcidCount;
    return true;
}

bool ChemicalSystem::formNucleotide(const std::string& base) {
    // Simplified: 5C + 8H + 4O + 2N
    auto carbons   = findUnbonded(6);
    auto hydrogens = findUnbonded(1);
    auto oxygens   = findWithBondsBelow(8, 2);
    auto nitrogens = findUnbonded(7);

    if (carbons.size() < 5 || hydrogens.size() < 8 ||
        oxygens.size() < 4 || nitrogens.size() < 2)
        return false;

    Molecule nuc;
    nuc.moleculeId = nextMoleculeId();
    nuc.name = "nucleotide-" + base;
    nuc.isOrganic = true;
    nuc.functionalGroups = {"sugar", "phosphate", "base"};

    std::vector<size_t> used;
    for (int k = 0; k < 5; ++k) { used.push_back(carbons.back()); carbons.pop_back(); }
    for (int k = 0; k < 8; ++k) { used.push_back(hydrogens.back()); hydrogens.pop_back(); }
    for (int k = 0; k < 4; ++k) { used.push_back(oxygens.back()); oxygens.pop_back(); }
    for (int k = 0; k < 2; ++k) { used.push_back(nitrogens.back()); nitrogens.pop_back(); }

    nuc.position = atomic.atoms[used[0]].position;
    int firstId = atomic.atoms[used[0]].atomId;
    for (auto idx : used) {
        auto& a = atomic.atoms[idx];
        nuc.atomIds.push_back(a.atomId);
        if (a.atomId != firstId) {
            atomic.atoms[used[0]].bonds.push_back(a.atomId);
            a.bonds.push_back(firstId);
        }
    }

    molecules.push_back(nuc);
    ++nucleotideCount;
    return true;
}

int ChemicalSystem::catalyzedReaction(double temperature, bool catalystPresent) {
    int formed = 0;
    double eaFactor = catalystPresent ? 0.3 : 1.0;
    double thermal  = K_B * temperature;

    // Amino acids
    if (thermal > 0.0 && atomic.atoms.size() > 10) {
        double aaProb = std::exp(-5.0 * eaFactor / (thermal + 1e-20));
        if (randUniform() < aaProb) {
            int idx = static_cast<int>(randUniform() * AMINO_ACIDS.size());
            if (idx >= static_cast<int>(AMINO_ACIDS.size())) idx = 0;
            if (formAminoAcid(std::string(AMINO_ACIDS[idx]))) {
                ++formed;
                ++reactionsOccurred;
            }
        }
    }

    // Nucleotides
    if (thermal > 0.0 && atomic.atoms.size() > 19) {
        double nucProb = std::exp(-8.0 * eaFactor / (thermal + 1e-20));
        if (randUniform() < nucProb) {
            const char* bases[] = {"A", "T", "G", "C"};
            int idx = static_cast<int>(randUniform() * 4);
            if (idx >= 4) idx = 0;
            if (formNucleotide(bases[idx])) {
                ++formed;
                ++reactionsOccurred;
            }
        }
    }

    return formed;
}

} // namespace sim
