/*
 * universe.h - Complete simulation engine.
 *
 * Combines quantum field, atomic system, chemistry, biology, and
 * environment layers into one header/source pair.  Faithfully ported
 * from the Python simulator package.
 */
#ifndef ITB_UNIVERSE_H
#define ITB_UNIVERSE_H

#include "constants.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ */
/*  Enumerations                                                      */
/* ------------------------------------------------------------------ */

typedef enum {
    PTYPE_UP,
    PTYPE_DOWN,
    PTYPE_ELECTRON,
    PTYPE_POSITRON,
    PTYPE_NEUTRINO,
    PTYPE_PHOTON,
    PTYPE_GLUON,
    PTYPE_W_BOSON,
    PTYPE_Z_BOSON,
    PTYPE_PROTON,
    PTYPE_NEUTRON,
    PTYPE_COUNT
} ParticleType;

typedef enum { SPIN_UP = 0, SPIN_DOWN = 1 } Spin;
typedef enum { COLOR_NONE=0, COLOR_RED, COLOR_GREEN, COLOR_BLUE,
               COLOR_ANTI_RED, COLOR_ANTI_GREEN, COLOR_ANTI_BLUE } Color;

typedef enum {
    EPOCH_VOID = 0,
    EPOCH_PLANCK,
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

/* ------------------------------------------------------------------ */
/*  Quantum / Particle structs                                        */
/* ------------------------------------------------------------------ */

typedef struct {
    double amplitude;
    double phase;
    bool   coherent;
} WaveFunction;

typedef struct {
    ParticleType type;
    double  position[3];
    double  momentum[3];
    Spin    spin;
    Color   color;
    WaveFunction wave_fn;
    int     entangled_with;   /* -1 = none */
    int     id;
    bool    alive;
} Particle;

typedef struct {
    double  temperature;
    Particle particles[MAX_PARTICLES];
    int     particle_count;
    double  vacuum_energy;
    int     total_created;
    int     total_annihilated;
    int     next_id;
} QuantumField;

/* ------------------------------------------------------------------ */
/*  Atomic structs                                                    */
/* ------------------------------------------------------------------ */

typedef struct {
    int n;
    int max_electrons;
    int electrons;
} ElectronShell;

typedef struct {
    int    atomic_number;
    int    mass_number;
    int    electron_count;
    double position[3];
    double velocity[3];
    ElectronShell shells[NUM_ELECTRON_SHELLS];
    int    num_shells;
    int    bonds[MAX_BONDS];
    int    bond_count;
    int    atom_id;
    double ionization_energy;
    bool   alive;
} Atom;

typedef struct {
    Atom   atoms[MAX_ATOMS];
    int    atom_count;
    double temperature;
    int    bonds_formed;
    int    bonds_broken;
    int    next_id;
} AtomicSystem;

/* ------------------------------------------------------------------ */
/*  Chemistry structs                                                 */
/* ------------------------------------------------------------------ */

typedef struct {
    int    atom_indices[32];   /* indices into AtomicSystem.atoms */
    int    atom_count;
    char   name[32];
    char   formula[32];
    double position[3];
    double energy;
    bool   is_organic;
    int    molecule_id;
    bool   alive;
} Molecule;

typedef struct {
    Molecule molecules[MAX_MOLECULES];
    int      molecule_count;
    int      reactions_occurred;
    int      water_count;
    int      amino_acid_count;
    int      nucleotide_count;
    int      next_id;
    bool     initialised;
} ChemicalSystem;

/* ------------------------------------------------------------------ */
/*  Biology structs                                                   */
/* ------------------------------------------------------------------ */

typedef struct {
    int  position;
    char mark_type;       /* 'M' methylation, 'A' acetylation */
    bool active;
    int  generation_added;
} EpigeneticMark;

typedef struct {
    char  name[16];
    char  sequence[MAX_DNA_LENGTH];
    int   length;
    int   start_pos;
    int   end_pos;
    double expression_level;
    EpigeneticMark marks[MAX_EPIGENETIC];
    int   mark_count;
    bool  essential;
} Gene;

typedef struct {
    char  sequence[MAX_DNA_LENGTH];
    int   length;
    Gene  genes[MAX_GENES];
    int   gene_count;
    int   generation;
    int   mutation_count;
} DNAStrand;

typedef struct {
    char  amino_acids[MAX_PROTEIN_LENGTH][4]; /* 3-letter codes */
    int   length;
    char  name[32];
    char  function;     /* 'e'=enzyme, 's'=structural, 'g'=signaling */
    bool  folded;
    bool  active;
} Protein;

typedef struct {
    DNAStrand dna;
    Protein   proteins[MAX_PROTEINS];
    int       protein_count;
    double    fitness;
    bool      alive;
    int       generation;
    double    energy;
    int       cell_id;
} Cell;

typedef struct {
    Cell  cells[MAX_CELLS];
    int   cell_count;
    int   generation;
    int   total_born;
    int   total_died;
    int   dna_length;
    bool  initialised;
} Biosphere;

/* ------------------------------------------------------------------ */
/*  Environment                                                       */
/* ------------------------------------------------------------------ */

typedef struct {
    char   event_type[16];
    double intensity;
    int    duration;
    int    tick_occurred;
} EnvironmentalEvent;

typedef struct {
    double temperature;
    double uv_intensity;
    double cosmic_ray_flux;
    double stellar_wind;
    double atmospheric_density;
    double water_availability;
    double day_night_cycle;
    double season;
    EnvironmentalEvent events[MAX_EVENTS];
    int    event_count;
    int    tick;
} Environment;

/* ------------------------------------------------------------------ */
/*  Universe - top-level orchestrator                                  */
/* ------------------------------------------------------------------ */

typedef struct {
    int    tick;
    int    max_ticks;
    int    step_size;
    EpochId current_epoch;

    QuantumField   qf;
    AtomicSystem   as;
    ChemicalSystem cs;
    Biosphere      bio;
    Environment    env;

    /* Cumulative metrics */
    int particles_created;
    int atoms_formed;
    int molecules_formed;
    int cells_born;
    int mutations;

    unsigned int rng_state;   /* xorshift32 seed */
} Universe;

/* ------------------------------------------------------------------ */
/*  Snapshot (read by the GL renderer)                                */
/* ------------------------------------------------------------------ */

typedef struct {
    int     tick;
    EpochId epoch;
    double  temperature;
    int     particle_count;
    int     atom_count;
    int     molecule_count;
    int     cell_count;
    double  average_fitness;
    int     generation;
    int     total_mutations;
    bool    habitable;
} Snapshot;

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */

/* Initialise the universe with a random seed.                        */
void universe_init(Universe *u, unsigned int seed);

/* Advance the simulation by one step.                                */
void universe_step(Universe *u);

/* Take a snapshot of the current state (lock-free for the renderer). */
Snapshot universe_snapshot(const Universe *u);

/* Return a human-readable epoch name.                                */
const char *epoch_name(EpochId e);

/* Particle type helpers */
const char *particle_type_name(ParticleType t);
double      particle_mass(ParticleType t);
double      particle_charge(ParticleType t);

/* Element helpers */
const char *element_symbol(int atomic_number);

#ifdef __cplusplus
}
#endif

#endif /* ITB_UNIVERSE_H */
