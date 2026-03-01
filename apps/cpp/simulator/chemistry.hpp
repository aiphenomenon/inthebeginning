#pragma once
/// Chemistry simulation - molecular assembly and reactions.
///
/// Models formation of molecules from atoms: water, amino acids,
/// nucleotides, and other biomolecules essential for life.

#include <string>
#include <vector>

#include "constants.hpp"
#include "atomic.hpp"

namespace sim {

// ============================================================
// Molecule
// ============================================================
struct Molecule {
    std::vector<int> atomIds;      // IDs of constituent atoms
    std::string name;
    std::string formula;
    int    moleculeId  = 0;
    double energy      = 0.0;
    std::array<double, 3> position = {0.0, 0.0, 0.0};
    bool   isOrganic   = false;
    std::vector<std::string> functionalGroups;
};

// ============================================================
// ChemicalSystem
// ============================================================
class ChemicalSystem {
public:
    explicit ChemicalSystem(AtomicSystem& atomicSystem);

    /// Form water molecules: 2H + O -> H2O
    std::vector<Molecule> formWater();

    /// Form methane: C + 4H -> CH4
    std::vector<Molecule> formMethane();

    /// Form ammonia: N + 3H -> NH3
    std::vector<Molecule> formAmmonia();

    /// Form an amino acid (simplified).
    bool formAminoAcid(const std::string& aaType = "Gly");

    /// Form a nucleotide (simplified).
    bool formNucleotide(const std::string& base = "A");

    /// Run catalyzed reactions at given temperature.
    int catalyzedReaction(double temperature, bool catalystPresent = false);

    // --- Public state ---
    AtomicSystem&         atomic;
    std::vector<Molecule> molecules;
    int reactionsOccurred = 0;
    int waterCount        = 0;
    int aminoAcidCount    = 0;
    int nucleotideCount   = 0;

private:
    int nextId_ = 0;
    int nextMoleculeId();

    /// Gather indices of unbonded atoms with a given Z.
    std::vector<size_t> findUnbonded(int atomicNumber) const;
    /// Gather indices of atoms with Z and fewer than maxBonds bonds.
    std::vector<size_t> findWithBondsBelow(int atomicNumber, size_t maxBonds) const;
};

} // namespace sim
