/*
 * universe.h - Universe orchestrator: epoch management and simulation driver.
 *
 * Coordinates all subsystems (quantum, atomic, chemistry, biology, environment)
 * through 13 cosmic epochs from the Planck era to the present day.
 */
#ifndef SIM_UNIVERSE_H
#define SIM_UNIVERSE_H

#include "constants.h"
#include "quantum.h"
#include "atomic.h"
#include "chemistry.h"
#include "biology.h"
#include "environment.h"
#include <stdbool.h>

/* Epoch identifiers */
typedef enum {
    EPOCH_PLANCK = 0,
    EPOCH_INFLATION,
    EPOCH_ELECTROWEAK,
    EPOCH_QUARK,
    EPOCH_HADRON,
    EPOCH_NUCLEOSYNTHESIS,
    EPOCH_RECOMBINATION,
    EPOCH_STAR_FORMATION,
    EPOCH_SOLAR_SYSTEM,
    EPOCH_EARTH,
    EPOCH_LIFE,
    EPOCH_DNA,
    EPOCH_PRESENT,
    EPOCH_COUNT
} EpochId;

/* Epoch descriptor */
typedef struct {
    EpochId     id;
    const char *name;
    int         start_tick;
    int         end_tick;
} EpochDescriptor;

/* Event log entry */
typedef struct {
    int         tick;
    EpochId     epoch;
    char        message[128];
} SimEvent;

/* Universe: top-level simulation state */
typedef struct {
    QuantumField   quantum;
    AtomicSystem   atomic;
    ChemicalSystem chemistry;
    Biosphere      biosphere;
    Environment    environment;

    int            current_tick;
    EpochId        current_epoch;

    SimEvent       events[MAX_EVENTS];
    int            event_count;

    bool           verbose;
} Universe;

/* -- API -- */
void        universe_init(Universe *u, bool verbose);
void        universe_free(Universe *u);
void        universe_run(Universe *u);
void        universe_step(Universe *u);
EpochId     universe_epoch_at_tick(int tick);
const char *universe_epoch_name(EpochId id);
void        universe_log_event(Universe *u, const char *msg);

void        universe_big_bounce(Universe *u);

/* Epoch table accessor */
const EpochDescriptor *universe_epoch_table(void);

#endif /* SIM_UNIVERSE_H */
