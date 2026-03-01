/*
 * quantum.h - Quantum field simulation: particles, wave functions,
 *             pair production, quark confinement.
 */
#ifndef SIM_QUANTUM_H
#define SIM_QUANTUM_H

#include "constants.h"
#include <stdbool.h>

/* Particle types */
typedef enum {
    PTYPE_UP = 0,
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

typedef enum {
    SPIN_UP   = 0,
    SPIN_DOWN = 1
} Spin;

typedef enum {
    COLOR_NONE = 0,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_ANTI_RED,
    COLOR_ANTI_GREEN,
    COLOR_ANTI_BLUE
} ColorCharge;

/* Wave function */
typedef struct {
    float amplitude;
    float phase;
    bool  coherent;
} WaveFunction;

/* Particle */
typedef struct {
    ParticleType type;
    float        position[3];
    float        momentum[3];
    Spin         spin;
    ColorCharge  color;
    WaveFunction wave_fn;
    int          particle_id;
    int          entangled_with; /* -1 if none */
} Particle;

/* Quantum field */
typedef struct {
    Particle *particles;
    int       count;
    int       capacity;
    double    temperature;
    double    vacuum_energy;
    int       total_created;
    int       total_annihilated;
} QuantumField;

/* -- Particle helpers -- */
float  particle_mass(ParticleType t);
float  particle_charge(ParticleType t);
float  particle_energy(const Particle *p);
const char *particle_type_name(ParticleType t);

/* -- Wave function -- */
void  wf_init(WaveFunction *wf);
void  wf_evolve(WaveFunction *wf, float dt, float energy);
bool  wf_collapse(WaveFunction *wf);

/* -- Quantum field API -- */
void  qf_init(QuantumField *qf, double temperature);
void  qf_free(QuantumField *qf);
int   qf_add_particle(QuantumField *qf, const Particle *p);
void  qf_remove_particle(QuantumField *qf, int index);
void  qf_evolve(QuantumField *qf, float dt);
bool  qf_pair_production(QuantumField *qf, float energy);
bool  qf_vacuum_fluctuation(QuantumField *qf);
int   qf_quark_confinement(QuantumField *qf);
int   qf_particle_count(const QuantumField *qf, ParticleType type);
float qf_total_energy(const QuantumField *qf);

#endif /* SIM_QUANTUM_H */
