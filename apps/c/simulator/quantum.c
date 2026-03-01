/*
 * quantum.c - Quantum field simulation implementation.
 *
 * Models quantum fields, particles, wave functions, pair production,
 * quark-hadron transition. Faithfully ports the Python simulator logic.
 */
#include "quantum.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

static int g_particle_id_counter = 0;

static float randf(void)
{
    return (float)rand() / (float)RAND_MAX;
}

/* Box-Muller transform for Gaussian random numbers */
static float gaussf(float mean, float stddev)
{
    float u1 = randf();
    float u2 = randf();
    if (u1 < 1e-10f) u1 = 1e-10f;
    float z = sqrtf(-2.0f * logf(u1)) * cosf(2.0f * (float)SIM_PI * u2);
    return mean + stddev * z;
}

/* Exponential variate with rate lambda */
static float expovariatef(float lambda)
{
    float u = randf();
    if (u < 1e-10f) u = 1e-10f;
    return -logf(u) / lambda;
}

/* ------------------------------------------------------------------ */
/* Particle helpers                                                    */
/* ------------------------------------------------------------------ */

static const float MASS_TABLE[PTYPE_COUNT] = {
    [PTYPE_UP]       = M_UP_QUARK,
    [PTYPE_DOWN]     = M_DOWN_QUARK,
    [PTYPE_ELECTRON] = M_ELECTRON,
    [PTYPE_POSITRON] = M_ELECTRON,
    [PTYPE_NEUTRINO] = (float)M_NEUTRINO,
    [PTYPE_PHOTON]   = M_PHOTON,
    [PTYPE_GLUON]    = M_PHOTON,
    [PTYPE_W_BOSON]  = M_W_BOSON,
    [PTYPE_Z_BOSON]  = M_Z_BOSON,
    [PTYPE_PROTON]   = M_PROTON,
    [PTYPE_NEUTRON]  = M_NEUTRON,
};

static const float CHARGE_TABLE[PTYPE_COUNT] = {
    [PTYPE_UP]       =  2.0f / 3.0f,
    [PTYPE_DOWN]     = -1.0f / 3.0f,
    [PTYPE_ELECTRON] = -1.0f,
    [PTYPE_POSITRON] =  1.0f,
    [PTYPE_NEUTRINO] =  0.0f,
    [PTYPE_PHOTON]   =  0.0f,
    [PTYPE_GLUON]    =  0.0f,
    [PTYPE_W_BOSON]  =  1.0f,
    [PTYPE_Z_BOSON]  =  0.0f,
    [PTYPE_PROTON]   =  1.0f,
    [PTYPE_NEUTRON]  =  0.0f,
};

static const char *TYPE_NAMES[PTYPE_COUNT] = {
    "up", "down", "electron", "positron", "neutrino",
    "photon", "gluon", "W", "Z", "proton", "neutron"
};

float particle_mass(ParticleType t)
{
    if (t >= 0 && t < PTYPE_COUNT) return MASS_TABLE[t];
    return 0.0f;
}

float particle_charge(ParticleType t)
{
    if (t >= 0 && t < PTYPE_COUNT) return CHARGE_TABLE[t];
    return 0.0f;
}

float particle_energy(const Particle *p)
{
    float p2 = p->momentum[0] * p->momentum[0]
             + p->momentum[1] * p->momentum[1]
             + p->momentum[2] * p->momentum[2];
    float m  = particle_mass(p->type);
    float c  = (float)SIM_C;
    return sqrtf(p2 * c * c + m * m * c * c * c * c);
}

const char *particle_type_name(ParticleType t)
{
    if (t >= 0 && t < PTYPE_COUNT) return TYPE_NAMES[t];
    return "unknown";
}

/* ------------------------------------------------------------------ */
/* Wave function                                                       */
/* ------------------------------------------------------------------ */

void wf_init(WaveFunction *wf)
{
    wf->amplitude = 1.0f;
    wf->phase     = 0.0f;
    wf->coherent  = true;
}

void wf_evolve(WaveFunction *wf, float dt, float energy)
{
    if (wf->coherent) {
        wf->phase += energy * dt / (float)SIM_HBAR;
        wf->phase = fmodf(wf->phase, 2.0f * (float)SIM_PI);
    }
}

bool wf_collapse(WaveFunction *wf)
{
    float prob = wf->amplitude * wf->amplitude;
    bool result = randf() < prob;
    wf->amplitude = result ? 1.0f : 0.0f;
    wf->coherent  = false;
    return result;
}

/* ------------------------------------------------------------------ */
/* Quantum field                                                       */
/* ------------------------------------------------------------------ */

void qf_init(QuantumField *qf, double temperature)
{
    qf->capacity          = 256;
    qf->count             = 0;
    qf->particles         = (Particle *)calloc((size_t)qf->capacity, sizeof(Particle));
    qf->temperature       = temperature;
    qf->vacuum_energy     = 0.0;
    qf->total_created     = 0;
    qf->total_annihilated = 0;
}

void qf_free(QuantumField *qf)
{
    free(qf->particles);
    qf->particles = NULL;
    qf->count = 0;
    qf->capacity = 0;
}

static void qf_ensure_capacity(QuantumField *qf, int needed)
{
    if (qf->count + needed <= qf->capacity) return;
    int new_cap = qf->capacity * 2;
    while (new_cap < qf->count + needed) new_cap *= 2;
    if (new_cap > MAX_PARTICLES) new_cap = MAX_PARTICLES;
    qf->particles = (Particle *)realloc(qf->particles,
                                        (size_t)new_cap * sizeof(Particle));
    qf->capacity = new_cap;
}

int qf_add_particle(QuantumField *qf, const Particle *p)
{
    if (qf->count >= MAX_PARTICLES) return -1;
    qf_ensure_capacity(qf, 1);
    int idx = qf->count;
    qf->particles[idx] = *p;
    qf->particles[idx].particle_id = ++g_particle_id_counter;
    qf->count++;
    return idx;
}

void qf_remove_particle(QuantumField *qf, int index)
{
    if (index < 0 || index >= qf->count) return;
    /* Swap with last element for O(1) removal */
    qf->particles[index] = qf->particles[qf->count - 1];
    qf->count--;
}

void qf_evolve(QuantumField *qf, float dt)
{
    for (int i = 0; i < qf->count; i++) {
        Particle *p = &qf->particles[i];
        float m = particle_mass(p->type);

        if (m > 0.0f) {
            /* Massive particles: dp/m * dt */
            for (int j = 0; j < 3; j++) {
                p->position[j] += p->momentum[j] / m * dt;
            }
        } else {
            /* Massless: move at c */
            float p_mag = sqrtf(p->momentum[0] * p->momentum[0]
                              + p->momentum[1] * p->momentum[1]
                              + p->momentum[2] * p->momentum[2]);
            if (p_mag < 1e-20f) p_mag = 1.0f;
            for (int j = 0; j < 3; j++) {
                p->position[j] += p->momentum[j] / p_mag * (float)SIM_C * dt;
            }
        }

        /* Evolve wave function */
        float e = particle_energy(p);
        wf_evolve(&p->wave_fn, dt, e);
    }
}

bool qf_pair_production(QuantumField *qf, float energy)
{
    if (energy < 2.0f * M_ELECTRON * (float)(SIM_C * SIM_C))
        return false;
    if (qf->count + 2 > MAX_PARTICLES)
        return false;

    ParticleType p_type, ap_type;
    if (energy >= 2.0f * M_PROTON * (float)(SIM_C * SIM_C) && randf() < 0.1f) {
        p_type  = PTYPE_UP;
        ap_type = PTYPE_DOWN;
    } else {
        p_type  = PTYPE_ELECTRON;
        ap_type = PTYPE_POSITRON;
    }

    float dir[3];
    dir[0] = gaussf(0.0f, 1.0f);
    dir[1] = gaussf(0.0f, 1.0f);
    dir[2] = gaussf(0.0f, 1.0f);
    float norm = sqrtf(dir[0]*dir[0] + dir[1]*dir[1] + dir[2]*dir[2]);
    if (norm < 1e-10f) norm = 1.0f;
    float p_mom = energy / (2.0f * (float)SIM_C);

    Particle pa = {0}, pb = {0};
    pa.type = p_type;
    pb.type = ap_type;
    pa.spin = SPIN_UP;
    pb.spin = SPIN_DOWN;
    wf_init(&pa.wave_fn);
    wf_init(&pb.wave_fn);
    pa.entangled_with = -1;
    pb.entangled_with = -1;

    for (int i = 0; i < 3; i++) {
        pa.momentum[i] =  (dir[i] / norm) * p_mom;
        pb.momentum[i] = -(dir[i] / norm) * p_mom;
        pa.position[i] = 0.0f;
        pb.position[i] = 0.0f;
    }

    int ia = qf_add_particle(qf, &pa);
    int ib = qf_add_particle(qf, &pb);
    if (ia >= 0 && ib >= 0) {
        qf->particles[ia].entangled_with = qf->particles[ib].particle_id;
        qf->particles[ib].entangled_with = qf->particles[ia].particle_id;
    }
    qf->total_created += 2;
    return true;
}

bool qf_vacuum_fluctuation(QuantumField *qf)
{
    double prob = qf->temperature / T_PLANCK;
    if (prob > 0.5) prob = 0.5;
    if (randf() < (float)prob) {
        float inv_lambda = (float)(qf->temperature * 0.001);
        if (inv_lambda < 1e-10f) inv_lambda = 1e-10f;
        float energy = expovariatef(1.0f / inv_lambda);
        return qf_pair_production(qf, energy);
    }
    return false;
}

int qf_quark_confinement(QuantumField *qf)
{
    if (qf->temperature > T_QUARK_HADRON) return 0;

    int hadrons_formed = 0;

    /* Collect indices of ups and downs */
    int ups[MAX_PARTICLES], n_ups = 0;
    int downs[MAX_PARTICLES], n_downs = 0;

    for (int i = 0; i < qf->count; i++) {
        if (qf->particles[i].type == PTYPE_UP   && n_ups   < MAX_PARTICLES)
            ups[n_ups++] = i;
        if (qf->particles[i].type == PTYPE_DOWN && n_downs < MAX_PARTICLES)
            downs[n_downs++] = i;
    }

    /* Form protons: uud */
    while (n_ups >= 2 && n_downs >= 1) {
        int iu1 = ups[--n_ups];
        int iu2 = ups[--n_ups];
        int id1 = downs[--n_downs];

        Particle proton = {0};
        proton.type = PTYPE_PROTON;
        proton.spin = SPIN_UP;
        proton.entangled_with = -1;
        wf_init(&proton.wave_fn);

        for (int j = 0; j < 3; j++) {
            proton.position[j] = qf->particles[iu1].position[j];
            proton.momentum[j] = qf->particles[iu1].momentum[j]
                               + qf->particles[iu2].momentum[j]
                               + qf->particles[id1].momentum[j];
        }

        /* Mark quarks for removal (set type to count=invalid, handled below) */
        qf->particles[iu1].type = PTYPE_COUNT;
        qf->particles[iu2].type = PTYPE_COUNT;
        qf->particles[id1].type = PTYPE_COUNT;

        qf_add_particle(qf, &proton);
        hadrons_formed++;
    }

    /* Form neutrons: udd */
    while (n_ups >= 1 && n_downs >= 2) {
        int iu1 = ups[--n_ups];
        int id1 = downs[--n_downs];
        int id2 = downs[--n_downs];

        Particle neutron = {0};
        neutron.type = PTYPE_NEUTRON;
        neutron.spin = SPIN_UP;
        neutron.entangled_with = -1;
        wf_init(&neutron.wave_fn);

        for (int j = 0; j < 3; j++) {
            neutron.position[j] = qf->particles[iu1].position[j];
            neutron.momentum[j] = qf->particles[iu1].momentum[j]
                                + qf->particles[id1].momentum[j]
                                + qf->particles[id2].momentum[j];
        }

        qf->particles[iu1].type = PTYPE_COUNT;
        qf->particles[id1].type = PTYPE_COUNT;
        qf->particles[id2].type = PTYPE_COUNT;

        qf_add_particle(qf, &neutron);
        hadrons_formed++;
    }

    /* Compact: remove all particles marked as PTYPE_COUNT */
    int write = 0;
    for (int read = 0; read < qf->count; read++) {
        if (qf->particles[read].type != PTYPE_COUNT) {
            if (write != read)
                qf->particles[write] = qf->particles[read];
            write++;
        }
    }
    qf->count = write;

    return hadrons_formed;
}

int qf_particle_count(const QuantumField *qf, ParticleType type)
{
    int count = 0;
    for (int i = 0; i < qf->count; i++) {
        if (qf->particles[i].type == type) count++;
    }
    return count;
}

float qf_total_energy(const QuantumField *qf)
{
    float total = (float)qf->vacuum_energy;
    for (int i = 0; i < qf->count; i++) {
        total += particle_energy(&qf->particles[i]);
    }
    return total;
}
