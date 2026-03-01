#include "biology.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <random>

namespace sim {

// Thread-local RNG
static std::mt19937& rng() {
    static thread_local std::mt19937 gen{789};
    return gen;
}

static double randUniform() {
    static thread_local std::uniform_real_distribution<double> dist(0.0, 1.0);
    return dist(rng());
}

static int randInt(int lo, int hi) {
    std::uniform_int_distribution<int> dist(lo, hi);
    return dist(rng());
}

static char randomBase() {
    return NUCLEOTIDE_BASES[static_cast<size_t>(randInt(0, 3))];
}

// ============================================================
// Gene
// ============================================================

bool Gene::isSilenced() const {
    int methylCount = 0;
    for (auto& mark : epigeneticMarks) {
        if (mark.active && mark.markType == "methylation")
            ++methylCount;
    }
    // Gene is silenced if >50% of its length is methylated
    return methylCount > length() / 2;
}

void Gene::methylate(int position, int generation) {
    EpigeneticMark mark;
    mark.position = position;
    mark.markType = "methylation";
    mark.active = true;
    mark.generationAdded = generation;
    epigeneticMarks.push_back(mark);
}

void Gene::demethylate(int position) {
    for (auto& mark : epigeneticMarks) {
        if (mark.position == position && mark.markType == "methylation")
            mark.active = false;
    }
}

void Gene::acetylate(int position, int generation) {
    EpigeneticMark mark;
    mark.position = position;
    mark.markType = "acetylation";
    mark.active = true;
    mark.generationAdded = generation;
    epigeneticMarks.push_back(mark);
}

std::vector<char> Gene::transcribe() const {
    if (isSilenced()) return {};

    std::vector<char> mrna;
    mrna.reserve(sequence.size());
    for (char base : sequence) {
        switch (base) {
            case 'T': mrna.push_back('U'); break;
            case 'A': mrna.push_back('A'); break;
            case 'G': mrna.push_back('G'); break;
            case 'C': mrna.push_back('C'); break;
            default:  mrna.push_back('N'); break;
        }
    }
    return mrna;
}

int Gene::mutate(double rate) {
    int count = 0;
    for (auto& base : sequence) {
        if (randUniform() < rate) {
            char newBase = randomBase();
            while (newBase == base) newBase = randomBase();
            base = newBase;
            ++count;
        }
    }
    return count;
}

void Gene::updateExpression() {
    int acetylCount = 0;
    int methylCount = 0;
    for (auto& mark : epigeneticMarks) {
        if (!mark.active) continue;
        if (mark.markType == "acetylation") ++acetylCount;
        if (mark.markType == "methylation") ++methylCount;
    }

    // Acetylation increases expression, methylation decreases it
    double modifier = 1.0
        + 0.1 * static_cast<double>(acetylCount)
        - 0.15 * static_cast<double>(methylCount);
    expressionLevel = std::clamp(modifier, 0.0, 2.0);
}

// ============================================================
// Protein
// ============================================================

bool Protein::fold() {
    // Simplified folding: success if protein is long enough and has
    // hydrophobic core (represented by non-polar amino acids)
    if (aminoAcids.size() < 3) {
        folded = false;
        return false;
    }

    // Check for structural diversity (simplified)
    int hydrophobic = 0;
    for (auto& aa : aminoAcids) {
        if (aa == "Ala" || aa == "Val" || aa == "Leu" ||
            aa == "Ile" || aa == "Phe" || aa == "Trp" || aa == "Met") {
            ++hydrophobic;
        }
    }

    double ratio = static_cast<double>(hydrophobic) / static_cast<double>(aminoAcids.size());
    folded = (ratio > 0.15 || aminoAcids.size() >= 5);
    active = folded;
    return folded;
}

// ============================================================
// translateMRNA
// ============================================================

std::vector<std::string> translateMRNA(const std::vector<char>& mrna) {
    std::vector<std::string> protein;
    auto& table = codonTable();

    // Scan for start codon AUG
    size_t startPos = 0;
    bool foundStart = false;
    for (size_t i = 0; i + 2 < mrna.size(); ++i) {
        if (mrna[i] == 'A' && mrna[i+1] == 'U' && mrna[i+2] == 'G') {
            startPos = i;
            foundStart = true;
            break;
        }
    }

    if (!foundStart) return protein;

    for (size_t i = startPos; i + 2 < mrna.size(); i += 3) {
        std::string codon;
        codon += mrna[i];
        codon += mrna[i+1];
        codon += mrna[i+2];

        auto it = table.find(codon);
        if (it == table.end()) continue;
        if (it->second == "STOP") break;

        protein.push_back(it->second);
    }

    return protein;
}

// ============================================================
// DNAStrand
// ============================================================

double DNAStrand::gcContent() const {
    if (sequence.empty()) return 0.0;
    int gc = 0;
    for (char c : sequence) {
        if (c == 'G' || c == 'C') ++gc;
    }
    return static_cast<double>(gc) / static_cast<double>(sequence.size());
}

DNAStrand DNAStrand::randomStrand(int length, int numGenes) {
    DNAStrand strand;
    strand.sequence.resize(static_cast<size_t>(length));
    for (auto& base : strand.sequence) {
        base = randomBase();
    }

    // Place genes evenly along the strand
    int geneLen = length / (numGenes + 1);
    if (geneLen < 9) geneLen = 9; // minimum gene length (3 codons)

    for (int g = 0; g < numGenes && (g + 1) * geneLen + geneLen <= length; ++g) {
        Gene gene;
        gene.name = "gene_" + std::to_string(g);
        gene.startPos = (g + 1) * geneLen;
        gene.endPos = gene.startPos + geneLen;
        gene.essential = (g == 0); // first gene is essential

        // Copy the gene sequence from the strand
        gene.sequence.assign(
            strand.sequence.begin() + gene.startPos,
            strand.sequence.begin() + gene.endPos
        );

        // Ensure we have a start codon (AUG -> ATG in DNA)
        if (gene.sequence.size() >= 3) {
            gene.sequence[0] = 'A';
            gene.sequence[1] = 'T';
            gene.sequence[2] = 'G';
            strand.sequence[static_cast<size_t>(gene.startPos)]     = 'A';
            strand.sequence[static_cast<size_t>(gene.startPos + 1)] = 'T';
            strand.sequence[static_cast<size_t>(gene.startPos + 2)] = 'G';
        }

        strand.genes.push_back(gene);
    }

    return strand;
}

DNAStrand DNAStrand::replicate() const {
    DNAStrand daughter;
    daughter.sequence = sequence;
    daughter.generation = generation + 1;
    daughter.mutationCount = mutationCount;

    // Replication errors (point mutations)
    for (auto& base : daughter.sequence) {
        if (randUniform() < 1e-4) {
            char newBase = randomBase();
            while (newBase == base) newBase = randomBase();
            base = newBase;
            ++daughter.mutationCount;
        }
    }

    // Copy genes with inherited epigenetic marks (partial)
    for (auto& gene : genes) {
        Gene newGene = gene;
        // Update sequence from the daughter strand
        if (newGene.endPos <= static_cast<int>(daughter.sequence.size())) {
            newGene.sequence.assign(
                daughter.sequence.begin() + newGene.startPos,
                daughter.sequence.begin() + newGene.endPos
            );
        }

        // Epigenetic inheritance: ~60% of marks are inherited
        std::vector<EpigeneticMark> inherited;
        for (auto& mark : newGene.epigeneticMarks) {
            if (mark.active && randUniform() < 0.6) {
                inherited.push_back(mark);
            }
        }
        newGene.epigeneticMarks = inherited;
        newGene.updateExpression();

        daughter.genes.push_back(newGene);
    }

    return daughter;
}

int DNAStrand::applyMutations(double uvIntensity, double cosmicRayFlux) {
    int totalMut = 0;

    // UV-induced mutations (pyrimidine dimers)
    double uvRate = UV_MUTATION_RATE * uvIntensity;
    for (auto& base : sequence) {
        if ((base == 'T' || base == 'C') && randUniform() < uvRate) {
            base = randomBase();
            ++totalMut;
        }
    }

    // Cosmic ray damage (random double-strand breaks, simplified)
    double crRate = COSMIC_RAY_MUTATION_RATE * cosmicRayFlux;
    for (auto& base : sequence) {
        if (randUniform() < crRate) {
            base = randomBase();
            ++totalMut;
        }
    }

    // Update gene sequences from the strand
    for (auto& gene : genes) {
        if (gene.endPos <= static_cast<int>(sequence.size())) {
            gene.sequence.assign(
                sequence.begin() + gene.startPos,
                sequence.begin() + gene.endPos
            );
        }
    }

    mutationCount += totalMut;
    return totalMut;
}

void DNAStrand::applyEpigeneticChanges(double temperature, int gen) {
    double tempFactor = std::abs(temperature - T_EARTH_SURFACE) / T_EARTH_SURFACE;

    for (auto& gene : genes) {
        for (int pos = 0; pos < gene.length(); ++pos) {
            // Methylation
            double methProb = METHYLATION_PROBABILITY * (1.0 + tempFactor);
            if (randUniform() < methProb) {
                gene.methylate(pos, gen);
            }
            // Demethylation
            if (randUniform() < DEMETHYLATION_PROBABILITY) {
                gene.demethylate(pos);
            }
            // Histone acetylation
            if (randUniform() < HISTONE_ACETYLATION_PROB) {
                gene.acetylate(pos, gen);
            }
        }
        gene.updateExpression();
    }
}

// ============================================================
// Cell
// ============================================================

std::vector<Protein> Cell::transcribeAndTranslate() {
    std::vector<Protein> newProteins;

    for (auto& gene : dna.genes) {
        if (gene.isSilenced()) continue;

        // Transcription: DNA -> mRNA
        auto mrna = gene.transcribe();
        if (mrna.empty()) continue;

        // Translation: mRNA -> amino acid chain
        auto aminoAcids = translateMRNA(mrna);
        if (aminoAcids.empty()) continue;

        Protein protein;
        protein.aminoAcids = aminoAcids;
        protein.name = gene.name + "_product";

        // Assign function based on simple heuristics
        if (protein.aminoAcids.size() > 10)
            protein.function = "enzyme";
        else if (protein.aminoAcids.size() > 5)
            protein.function = "structural";
        else
            protein.function = "signaling";

        // Attempt folding
        protein.fold();

        newProteins.push_back(protein);
        proteins.push_back(protein);
    }

    return newProteins;
}

void Cell::metabolize(double environmentEnergy) {
    // Basic energy metabolism
    double metabolicRate = 1.0;

    // Enzymes boost metabolism
    int enzymeCount = 0;
    for (auto& p : proteins) {
        if (p.folded && p.active && p.function == "enzyme")
            ++enzymeCount;
    }
    metabolicRate += 0.2 * enzymeCount;

    energy += environmentEnergy * metabolicRate * 0.1;
    energy -= 5.0; // basal metabolic cost

    if (energy <= 0.0) {
        alive = false;
        energy = 0.0;
    }
}

std::optional<Cell> Cell::divide() {
    if (!alive || energy < 50.0) return std::nullopt;

    Cell daughter;
    daughter.dna = dna.replicate();
    daughter.generation = generation + 1;
    daughter.alive = true;
    daughter.energy = energy * 0.5;
    daughter.fitness = 1.0;

    // Parent loses half its energy
    energy *= 0.5;

    // Daughter must express its own proteins
    daughter.transcribeAndTranslate();
    daughter.computeFitness();

    return daughter;
}

double Cell::computeFitness() {
    if (!alive) { fitness = 0.0; return 0.0; }

    double f = 0.5; // base fitness

    // Functional proteins contribute
    int functional = 0;
    for (auto& p : proteins) {
        if (p.folded && p.active) ++functional;
    }
    f += 0.1 * functional;

    // Essential gene integrity
    for (auto& gene : dna.genes) {
        if (gene.essential) {
            // Check start codon still intact
            if (gene.sequence.size() >= 3 &&
                gene.sequence[0] == 'A' &&
                gene.sequence[1] == 'T' &&
                gene.sequence[2] == 'G') {
                f += 0.2;
            } else {
                f -= 0.5;
            }
        }
    }

    // GC content near 0.5 is optimal
    double gc = dna.gcContent();
    f -= std::abs(gc - 0.5) * 0.3;

    // Energy contributes
    f += energy * 0.001;

    fitness = std::max(0.0, f);
    return fitness;
}

// ============================================================
// Biosphere
// ============================================================

Biosphere::Biosphere(int initialCells, int dnaLen)
    : dnaLength(dnaLen) {
    for (int i = 0; i < initialCells; ++i) {
        Cell cell;
        cell.cellId = nextCellId();
        cell.dna = DNAStrand::randomStrand(dnaLen, 3);
        cell.transcribeAndTranslate();
        cell.computeFitness();
        cells.push_back(cell);
        ++totalBorn;
    }
}

int Biosphere::nextCellId() { return ++nextCellId_; }

void Biosphere::step(double environmentEnergy, double uvIntensity,
                     double cosmicRayFlux, double temperature) {
    ++generation;

    // Apply mutations and epigenetics
    for (auto& cell : cells) {
        if (!cell.alive) continue;
        cell.dna.applyMutations(uvIntensity, cosmicRayFlux);
        cell.dna.applyEpigeneticChanges(temperature, generation);
    }

    // Metabolism
    for (auto& cell : cells) {
        if (!cell.alive) continue;
        cell.metabolize(environmentEnergy);
    }

    // Express proteins fresh each generation
    for (auto& cell : cells) {
        if (!cell.alive) continue;
        cell.proteins.clear();
        cell.transcribeAndTranslate();
        cell.computeFitness();
    }

    // Cell division for fit cells
    std::vector<Cell> newCells;
    for (auto& cell : cells) {
        if (!cell.alive) continue;
        if (cell.fitness > 0.7 && cell.energy > 50.0) {
            auto daughter = cell.divide();
            if (daughter) {
                daughter->cellId = nextCellId();
                newCells.push_back(*daughter);
                ++totalBorn;
            }
        }
    }
    for (auto& nc : newCells) cells.push_back(nc);

    // Remove dead cells, count deaths
    auto it = std::remove_if(cells.begin(), cells.end(),
        [](const Cell& c) { return !c.alive; });
    totalDied += static_cast<int>(std::distance(it, cells.end()));
    cells.erase(it, cells.end());

    // Natural selection: cap population
    constexpr int maxPop = 100;
    if (static_cast<int>(cells.size()) > maxPop) {
        std::sort(cells.begin(), cells.end(),
            [](const Cell& a, const Cell& b) {
                if (std::isnan(a.fitness)) return false;
                if (std::isnan(b.fitness)) return true;
                return a.fitness > b.fitness;
            });
        int excess = static_cast<int>(cells.size()) - maxPop;
        totalDied += excess;
        cells.resize(static_cast<size_t>(maxPop));
    }
}

double Biosphere::averageFitness() const {
    if (cells.empty()) return 0.0;
    double sum = 0.0;
    for (auto& c : cells) sum += c.fitness;
    return sum / static_cast<double>(cells.size());
}

double Biosphere::averageGcContent() const {
    if (cells.empty()) return 0.0;
    double sum = 0.0;
    for (auto& c : cells) sum += c.dna.gcContent();
    return sum / static_cast<double>(cells.size());
}

int Biosphere::totalMutations() const {
    int total = 0;
    for (auto& c : cells) total += c.dna.mutationCount;
    return total;
}

} // namespace sim
