#pragma once
/// Biology simulation - DNA, RNA, proteins, and epigenetics.
///
/// Models DNA strand assembly, RNA transcription, protein translation
/// via codon table, epigenetic modifications, cell division with
/// mutation, and natural selection pressure.

#include <cmath>
#include <optional>
#include <string>
#include <vector>

#include "constants.hpp"

namespace sim {

// ============================================================
// EpigeneticMark
// ============================================================
struct EpigeneticMark {
    int         position        = 0;
    std::string markType;          // "methylation", "acetylation"
    bool        active          = true;
    int         generationAdded = 0;
};

// ============================================================
// Gene
// ============================================================
struct Gene {
    std::string            name;
    std::vector<char>      sequence;      // bases: A, T, G, C
    int                    startPos = 0;
    int                    endPos   = 0;
    double                 expressionLevel = 1.0;
    std::vector<EpigeneticMark> epigeneticMarks;
    bool                   essential = false;

    [[nodiscard]] int  length()     const { return static_cast<int>(sequence.size()); }
    [[nodiscard]] bool isSilenced() const;

    void methylate(int position, int generation = 0);
    void demethylate(int position);
    void acetylate(int position, int generation = 0);

    /// Transcribe DNA to mRNA (T -> U).
    [[nodiscard]] std::vector<char> transcribe() const;

    /// Apply random point mutations. Returns count.
    int mutate(double rate = 0.001);

    void updateExpression();
};

// ============================================================
// Protein
// ============================================================
struct Protein {
    std::vector<std::string> aminoAcids;
    std::string name;
    std::string function;   // "enzyme", "structural", "signaling"
    bool        folded = false;
    bool        active = true;

    [[nodiscard]] int length() const { return static_cast<int>(aminoAcids.size()); }

    /// Simplified protein folding.
    bool fold();
};

/// Translate mRNA to amino acid sequence.
std::vector<std::string> translateMRNA(const std::vector<char>& mrna);

// ============================================================
// DNAStrand
// ============================================================
struct DNAStrand {
    std::vector<char> sequence;   // template strand
    std::vector<Gene> genes;
    int generation    = 0;
    int mutationCount = 0;

    [[nodiscard]] int    length()    const { return static_cast<int>(sequence.size()); }
    [[nodiscard]] double gcContent() const;

    /// Generate a random strand with genes.
    static DNAStrand randomStrand(int length, int numGenes = 3);

    /// Semi-conservative replication with possible epigenetic inheritance.
    [[nodiscard]] DNAStrand replicate() const;

    /// Apply environmental mutations (UV, cosmic ray).
    int applyMutations(double uvIntensity = 0.0, double cosmicRayFlux = 0.0);

    /// Environmental epigenetic modifications.
    void applyEpigeneticChanges(double temperature, int generation = 0);
};

// ============================================================
// Cell
// ============================================================
struct Cell {
    DNAStrand             dna;
    std::vector<Protein>  proteins;
    double                fitness    = 1.0;
    bool                  alive      = true;
    int                   generation = 0;
    double                energy     = 100.0;
    int                   cellId     = 0;

    /// Central dogma: DNA -> mRNA -> Protein.
    std::vector<Protein> transcribeAndTranslate();

    /// Basic metabolism.
    void metabolize(double environmentEnergy = 10.0);

    /// Cell division with DNA replication.
    std::optional<Cell> divide();

    /// Compute fitness based on functional proteins and DNA integrity.
    double computeFitness();
};

// ============================================================
// Biosphere
// ============================================================
class Biosphere {
public:
    Biosphere(int initialCells = 5, int dnaLength = 90);

    /// One generation step.
    void step(double environmentEnergy = 10.0,
              double uvIntensity       = 0.0,
              double cosmicRayFlux     = 0.0,
              double temperature       = 300.0);

    [[nodiscard]] double averageFitness()   const;
    [[nodiscard]] double averageGcContent() const;
    [[nodiscard]] int    totalMutations()   const;

    // --- Public state ---
    std::vector<Cell> cells;
    int generation  = 0;
    int totalBorn   = 0;
    int totalDied   = 0;
    int dnaLength;

private:
    int nextCellId_ = 0;
    int nextCellId();
};

} // namespace sim
