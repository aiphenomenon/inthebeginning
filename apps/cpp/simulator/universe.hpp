#pragma once
/// Universe orchestrator - the top-level simulation driver.
///
/// Coordinates all subsystems (quantum, atomic, chemistry, biology,
/// environment) through 13 cosmic epochs from the Big Bang to the
/// emergence of complex life.

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "constants.hpp"
#include "quantum.hpp"
#include "atomic.hpp"
#include "chemistry.hpp"
#include "biology.hpp"
#include "environment.hpp"

namespace sim {

// ============================================================
// EpochState - snapshot of the universe at an epoch boundary
// ============================================================
struct EpochState {
    std::string epochName;
    int         tick            = 0;
    double      temperature     = 0.0;
    double      totalEnergy     = 0.0;
    int         particleCount   = 0;
    int         atomCount       = 0;
    int         moleculeCount   = 0;
    int         cellCount       = 0;
    double      scaleFactor     = 1.0;
    std::string details;
};

// ============================================================
// Universe
// ============================================================
class Universe {
public:
    Universe();

    /// Run the full simulation from Big Bang to present.
    /// The callback is invoked at each epoch boundary with state info.
    void simulate(std::function<void(const EpochState&)> onEpoch = nullptr);

    /// Run a single epoch by index (0-12).
    EpochState runEpoch(int epochIndex);

    /// Get all recorded epoch states after simulation.
    [[nodiscard]] const std::vector<EpochState>& epochHistory() const { return history_; }

    /// Current simulation tick.
    [[nodiscard]] int currentTick() const { return tick_; }

    // --- Public subsystems ---
    QuantumField   quantumField;
    AtomicSystem   atomicSystem;
    ChemicalSystem chemicalSystem;
    Environment    environment;

    // Biology is created on demand (only in later epochs)
    std::unique_ptr<Biosphere> biosphere;

private:
    int tick_ = 0;
    std::vector<EpochState> history_;

    // Epoch simulation methods
    EpochState simulatePlanck();
    EpochState simulateInflation();
    EpochState simulateElectroweak();
    EpochState simulateQuark();
    EpochState simulateHadron();
    EpochState simulateNucleosynthesis();
    EpochState simulateRecombination();
    EpochState simulateStarFormation();
    EpochState simulateSolarSystem();
    EpochState simulateEarth();
    EpochState simulateLife();
    EpochState simulateDNA();
    EpochState simulatePresent();

    /// Build an EpochState snapshot from current state.
    EpochState snapshot(const std::string& name, const std::string& details) const;

public:
    /// Big Bounce: reset the universe for a new cycle.
    /// Reconstructs the universe in-place for a fresh start.
    void bigBounce() {
        biosphere.reset();
        // Reconstruct in-place to handle non-movable members
        this->~Universe();
        new (this) Universe();
    }
};

} // namespace sim
