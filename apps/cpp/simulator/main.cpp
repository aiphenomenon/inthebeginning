/// In The Beginning - CLI Cosmic Evolution Simulator
///
/// Simulates the evolution of the universe from the Big Bang through
/// 13 cosmic epochs: from the Planck era to the emergence of complex life.
///
/// Usage: inthebeginning [--epoch N] [--verbose] [--ast-introspect] [--help]

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <regex>
#include <string>
#include <string_view>
#include <vector>

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
              << "  --ast-introspect Show AST self-introspection of source files\n"
              << "\nEpochs:\n";

    for (size_t i = 0; i < sim::EPOCHS.size(); ++i) {
        std::cout << "  " << std::right << std::setw(2) << (i + 1) << ". "
                  << std::left << std::setw(18) << sim::EPOCHS[i].name
                  << sim::EPOCHS[i].description << '\n';
    }
    std::cout << std::right;
}

// ============================================================
// AST Self-Introspection
// ============================================================

/// Scan all .cpp and .hpp files in the simulator/ directory and print
/// a summary table with lines, bytes, function count, and class count.
static void runAstIntrospection(const char* argv0) {
    namespace fs = std::filesystem;
    using namespace term;

    // Determine the simulator/ directory relative to the executable.
    // We walk from the executable path upward to find the simulator/ dir,
    // or fall back to the compile-time source location.
    fs::path simDir;

    // Try to resolve from argv[0] -- works when run from the build dir
    // inside the project tree (build/ is typically under apps/cpp/).
    fs::path exePath = fs::absolute(fs::path(argv0)).parent_path();
    for (auto p = exePath; p != p.root_path(); p = p.parent_path()) {
        if (fs::is_directory(p / "simulator")) {
            simDir = p / "simulator";
            break;
        }
    }

    // Fallback: use __FILE__ which is always inside simulator/
    if (simDir.empty()) {
        simDir = fs::path(__FILE__).parent_path();
    }

    if (!fs::is_directory(simDir)) {
        std::cerr << "Error: cannot locate simulator/ directory\n";
        return;
    }

    std::cout << '\n' << BOLD << CYAN
              << "=== AST Self-Introspection: C++ Simulator ===" << RESET
              << '\n' << '\n';

    // Collect .cpp and .hpp files
    std::vector<fs::path> files;
    for (const auto& entry : fs::directory_iterator(simDir)) {
        if (!entry.is_regular_file()) continue;
        auto ext = entry.path().extension().string();
        if (ext == ".cpp" || ext == ".hpp") {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());

    // Regex patterns for counting functions and classes
    //   Free functions:  return_type function_name(
    //   Class methods are also matched (they appear in .cpp as Type Class::method( )
    //   We match lines that look like definitions, not declarations inside classes.
    //   Pattern: optional qualifiers, a word (return type), optional template/ptr/ref
    //            decorators, then an identifier followed by '('.
    //   For simplicity we use two regexes:
    //     1. class/struct definitions: class Name or struct Name followed by { or :
    //     2. function definitions: lines with identifier( that are not control flow
    std::regex funcRe(
        R"((?:^|\s)(?:(?:static|inline|virtual|explicit|constexpr|const|auto|void|bool|int|long|unsigned|double|float|char|size_t|std::\w+)\s+))"
        R"((?:\w+::)?(\w+)\s*\()",
        std::regex_constants::ECMAScript);
    // Also catch functions whose return type is a project type (e.g. EpochState, WaveFunction)
    std::regex funcRe2(
        R"(^\s*\w[\w:<>,\s\*&]*\s+(\w+)\s*\([^;]*$)",
        std::regex_constants::ECMAScript);
    std::regex classRe(
        R"((?:^|\s)(?:class|struct)\s+(\w+)\s*[\{:])",
        std::regex_constants::ECMAScript);
    // Control flow keywords to exclude from function matches
    std::regex controlRe(
        R"(\b(if|else|for|while|switch|catch|return|throw|using|namespace|typedef|template)\b)");

    int totalLines     = 0;
    int totalBytes     = 0;
    int totalFunctions = 0;
    int totalClasses   = 0;

    // Print header
    std::cout << "  " << std::left  << std::setw(28) << "File"
              << std::right << std::setw(7)  << "Lines"
              << std::setw(9)  << "Bytes"
              << std::setw(7)  << "Funcs"
              << std::setw(9)  << "Classes"
              << '\n';
    std::cout << "  ";
    for (int i = 0; i < 28; ++i) std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 6; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 8; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 6; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 8; ++i)  std::cout << '-';
    std::cout << '\n';

    for (const auto& fpath : files) {
        std::ifstream ifs(fpath);
        if (!ifs) continue;

        std::string content((std::istreambuf_iterator<char>(ifs)),
                             std::istreambuf_iterator<char>());
        int fileBytes = static_cast<int>(content.size());

        // Count lines
        int lineCount = 0;
        for (char c : content) {
            if (c == '\n') ++lineCount;
        }
        if (!content.empty() && content.back() != '\n') ++lineCount;

        // Count functions and classes by scanning each line
        int funcCount  = 0;
        int classCount = 0;
        std::istringstream stream(content);
        std::string line;
        while (std::getline(stream, line)) {
            // Skip comment-only lines
            auto trimPos = line.find_first_not_of(" \t");
            if (trimPos != std::string::npos &&
                (line.substr(trimPos, 2) == "//" || line.substr(trimPos, 2) == "/*" ||
                 line.substr(trimPos, 1) == "*")) {
                continue;
            }

            // Check for class/struct definitions
            std::smatch cm;
            if (std::regex_search(line, cm, classRe)) {
                ++classCount;
                continue;  // A class line is not a function
            }

            // Skip control-flow lines
            std::smatch ctrlm;
            if (std::regex_search(line, ctrlm, controlRe)) {
                continue;
            }

            // Check for function definitions
            std::smatch fm;
            if (std::regex_search(line, fm, funcRe) ||
                std::regex_search(line, fm, funcRe2)) {
                ++funcCount;
            }
        }

        totalLines     += lineCount;
        totalBytes     += fileBytes;
        totalFunctions += funcCount;
        totalClasses   += classCount;

        std::string fname = fpath.filename().string();
        std::cout << "  " << std::left  << std::setw(28) << fname
                  << std::right << std::setw(7)  << lineCount
                  << std::setw(9)  << fileBytes
                  << std::setw(7)  << funcCount
                  << std::setw(9)  << classCount
                  << '\n';
    }

    // Print footer
    std::cout << "  ";
    for (int i = 0; i < 28; ++i) std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 6; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 8; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 6; ++i)  std::cout << '-';
    std::cout << ' ';
    for (int i = 0; i < 8; ++i)  std::cout << '-';
    std::cout << '\n';

    std::cout << "  " << BOLD
              << std::left  << std::setw(28) << "TOTAL"
              << std::right << std::setw(7)  << totalLines
              << std::setw(9)  << totalBytes
              << std::setw(7)  << totalFunctions
              << std::setw(9)  << totalClasses
              << RESET << '\n' << '\n';
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
        } else if (arg == "--ast-introspect") {
            runAstIntrospection(argv[0]);
            return 0;
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
