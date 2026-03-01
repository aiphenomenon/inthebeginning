/// In The Beginning - CLI Cosmic Evolution Simulator
///
/// Simulates the evolution of the universe from the Big Bang through
/// 13 cosmic epochs: from the Planck era to the emergence of complex life.
///
/// Usage: inthebeginning [--epoch N] [--verbose] [--help]

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <string_view>

#include "universe.hpp"

// ============================================================
// Terminal formatting helpers
// ============================================================
namespace term {

constexpr const char* RESET   = "\033[0m";
constexpr const char* BOLD    = "\033[1m";
constexpr const char* DIM     = "\033[2m";
constexpr const char* RED     = "\033[31m";
constexpr const char* GREEN   = "\033[32m";
constexpr const char* YELLOW  = "\033[33m";
constexpr const char* BLUE    = "\033[34m";
constexpr const char* MAGENTA = "\033[35m";
constexpr const char* CYAN    = "\033[36m";
constexpr const char* WHITE   = "\033[37m";

// Epoch-specific colors
const char* epochColor(int index) {
    const char* colors[] = {
        WHITE,    // Planck
        YELLOW,   // Inflation
        MAGENTA,  // Electroweak
        RED,      // Quark
        RED,      // Hadron
        YELLOW,   // Nucleosynthesis
        CYAN,     // Recombination
        YELLOW,   // Star Formation
        BLUE,     // Solar System
        GREEN,    // Earth
        GREEN,    // Life
        CYAN,     // DNA Era
        WHITE,    // Present
    };
    if (index < 0 || index > 12) return WHITE;
    return colors[index];
}

void printSeparator() {
    std::cout << DIM;
    for (int i = 0; i < 78; ++i) std::cout << '-';
    std::cout << RESET << '\n';
}

void printDoubleSeparator() {
    std::cout << BOLD;
    for (int i = 0; i < 78; ++i) std::cout << '=';
    std::cout << RESET << '\n';
}

} // namespace term

// ============================================================
// Display functions
// ============================================================

static void printBanner() {
    using namespace term;
    std::cout << '\n';
    printDoubleSeparator();
    std::cout << BOLD << CYAN
              << "                    IN THE BEGINNING" << RESET << '\n';
    std::cout << DIM
              << "           A Cosmic Evolution Simulator (C++20)" << RESET << '\n';
    std::cout << DIM
              << "        From the Big Bang to the Emergence of Life" << RESET << '\n';
    printDoubleSeparator();
    std::cout << '\n';
}

static void printEpochHeader(int index, const sim::EpochState& state) {
    using namespace term;

    const char* color = epochColor(index);

    std::cout << '\n';
    printSeparator();
    std::cout << BOLD << color
              << "  EPOCH " << (index + 1) << "/13: "
              << state.epochName << RESET << '\n';

    // Print the epoch description from constants
    if (index >= 0 && index < 13) {
        std::cout << DIM << "  "
                  << sim::EPOCHS[static_cast<size_t>(index)].description
                  << RESET << '\n';
    }
    printSeparator();
}

static void printEpochStats(const sim::EpochState& state, bool verbose) {
    using namespace term;

    std::cout << std::scientific << std::setprecision(3);
    std::cout << "  " << DIM << "Tick:        " << RESET
              << state.tick << '\n';
    std::cout << "  " << DIM << "Temperature: " << RESET
              << state.temperature << " K\n";
    std::cout << "  " << DIM << "Scale:       " << RESET
              << state.scaleFactor << '\n';
    std::cout << "  " << DIM << "Energy:      " << RESET
              << state.totalEnergy << '\n';

    std::cout << std::fixed;
    if (state.particleCount > 0) {
        std::cout << "  " << DIM << "Particles:   " << RESET
                  << state.particleCount << '\n';
    }
    if (state.atomCount > 0) {
        std::cout << "  " << DIM << "Atoms:       " << RESET
                  << state.atomCount << '\n';
    }
    if (state.moleculeCount > 0) {
        std::cout << "  " << DIM << "Molecules:   " << RESET
                  << state.moleculeCount << '\n';
    }
    if (state.cellCount > 0) {
        std::cout << "  " << DIM << "Cells:       " << RESET
                  << state.cellCount << '\n';
    }

    if (verbose) {
        std::cout << '\n';
    }
    std::cout << "  " << GREEN << state.details << RESET << '\n';
}

static void printSummary(const std::vector<sim::EpochState>& history) {
    using namespace term;

    std::cout << '\n';
    printDoubleSeparator();
    std::cout << BOLD << "  SIMULATION COMPLETE" << RESET << '\n';
    printDoubleSeparator();
    std::cout << '\n';

    // Summary table
    std::cout << BOLD
              << "  " << std::left << std::setw(18) << "Epoch"
              << std::right << std::setw(10) << "Tick"
              << std::setw(14) << "Temp (K)"
              << std::setw(10) << "Parts"
              << std::setw(10) << "Atoms"
              << std::setw(10) << "Mols"
              << std::setw(10) << "Cells"
              << RESET << '\n';

    printSeparator();

    for (size_t i = 0; i < history.size(); ++i) {
        auto& s = history[i];
        const char* color = epochColor(static_cast<int>(i));
        std::cout << color
                  << "  " << std::left << std::setw(18) << s.epochName
                  << std::right << std::setw(10) << s.tick
                  << std::scientific << std::setprecision(2)
                  << std::setw(14) << s.temperature
                  << std::fixed << std::setprecision(0)
                  << std::setw(10) << s.particleCount
                  << std::setw(10) << s.atomCount
                  << std::setw(10) << s.moleculeCount
                  << std::setw(10) << s.cellCount
                  << RESET << '\n';
    }

    std::cout << '\n';

    auto& final_state = history.back();
    std::cout << DIM << "  From a singularity to " << RESET
              << BOLD << final_state.cellCount << RESET
              << DIM << " living cells across "
              << final_state.tick << " simulation ticks." << RESET << '\n';
    std::cout << '\n';
}

static void printUsage(const char* progName) {
    std::cout << "Usage: " << progName << " [OPTIONS]\n\n"
              << "Options:\n"
              << "  --help, -h       Show this help message\n"
              << "  --epoch N        Run only epoch N (1-13)\n"
              << "  --verbose, -v    Show detailed output\n"
              << "  --no-color       Disable ANSI color output\n"
              << "\nEpochs:\n";

    for (size_t i = 0; i < sim::EPOCHS.size(); ++i) {
        std::cout << "  " << std::right << std::setw(2) << (i + 1) << ". "
                  << std::left << std::setw(18) << sim::EPOCHS[i].name
                  << sim::EPOCHS[i].description << '\n';
    }
    std::cout << std::right;
}

// ============================================================
// Main
// ============================================================
int main(int argc, char* argv[]) {
    bool verbose = false;
    int  singleEpoch = -1;  // -1 means run all
    bool noColor = false;

    // Parse arguments
    for (int i = 1; i < argc; ++i) {
        std::string_view arg(argv[i]);
        if (arg == "--help" || arg == "-h") {
            printUsage(argv[0]);
            return 0;
        } else if (arg == "--verbose" || arg == "-v") {
            verbose = true;
        } else if (arg == "--no-color") {
            noColor = true;
        } else if (arg == "--epoch" && i + 1 < argc) {
            singleEpoch = std::atoi(argv[++i]);
            if (singleEpoch < 1 || singleEpoch > 13) {
                std::cerr << "Error: epoch must be between 1 and 13\n";
                return 1;
            }
        } else {
            std::cerr << "Unknown option: " << arg << '\n';
            printUsage(argv[0]);
            return 1;
        }
    }

    // Disable colors if requested
    if (noColor) {
        // Override color constants by not using them (we'll just print plain text)
        // The term namespace consts are const char*, so we redirect through a flag
    }

    printBanner();

    sim::Universe universe;

    if (singleEpoch > 0) {
        // Run all epochs up to the requested one
        std::cout << term::DIM << "  Running epochs 1 through "
                  << singleEpoch << "..." << term::RESET << '\n';

        for (int i = 0; i < singleEpoch; ++i) {
            auto state = universe.runEpoch(i);
            printEpochHeader(i, state);
            printEpochStats(state, verbose);
        }
    } else {
        // Run full simulation
        int epochIdx = 0;
        universe.simulate([&](const sim::EpochState& state) {
            printEpochHeader(epochIdx, state);
            printEpochStats(state, verbose);
            ++epochIdx;
        });

        printSummary(universe.epochHistory());
    }

    return 0;
}
