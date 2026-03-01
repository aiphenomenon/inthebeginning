/*
 * universe.c - Complete simulation engine.
 *
 * Faithful C port of the Python simulator package:
 *   quantum.py   -> quantum field, particles, wave functions
 *   atomic.py    -> atoms, electron shells, nucleosynthesis
 *   chemistry.py -> molecules, water, amino acids, nucleotides
 *   biology.py   -> DNA, RNA, proteins, cells, biosphere
 *   environment.py -> temperature, UV, cosmic rays, events
 *   universe.py  -> orchestrator
 */
#include "universe.h"

#include <math.h>
#include <string.h>
#include <stdlib.h>

/* ================================================================== */
/*  Deterministic RNG (xorshift32) - avoids global rand() state       */
/* ================================================================== */

static unsigned int xorshift32(unsigned int *state)
{
    unsigned int x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

/* Return a double in [0,1) */
static double rng_double(unsigned int *s)
{
    return (xorshift32(s) & 0x7FFFFFFF) / (double)0x7FFFFFFF;
}

/* Return a Gaussian(0,1) via Box-Muller */
static double rng_gauss(unsigned int *s)
{
    double u1 = rng_double(s) + 1e-30;
    double u2 = rng_double(s);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * SIM_PI * u2);
}

/* Return int in [0, n) */
static int rng_int(unsigned int *s, int n)
{
    if (n <= 0) return 0;
    return (int)(xorshift32(s) % (unsigned int)n);
}

/* Exponential variate with rate lambda */
static double rng_expo(unsigned int *s, double lambda)
{
    double u = rng_double(s) + 1e-30;
    return -log(u) / lambda;
}

/* ================================================================== */
/*  Lookup tables                                                     */
/* ================================================================== */

static const char *EPOCH_NAMES[EPOCH_COUNT] = {
    "Void", "Planck", "Inflation", "Electroweak",
    "Quark", "Hadron", "Nucleosynthesis", "Recombination",
    "Star Formation", "Solar System", "Earth", "Life",
    "DNA Era", "Present",
};

static const int EPOCH_TICKS[EPOCH_COUNT] = {
    0, PLANCK_EPOCH, INFLATION_EPOCH, ELECTROWEAK_EPOCH,
    QUARK_EPOCH, HADRON_EPOCH, NUCLEOSYNTHESIS_EPOCH,
    RECOMBINATION_EPOCH, STAR_FORMATION_EPOCH, SOLAR_SYSTEM_EPOCH,
    EARTH_EPOCH, LIFE_EPOCH, DNA_EPOCH, PRESENT_EPOCH,
};

static const char *PARTICLE_NAMES[PTYPE_COUNT] = {
    "up","down","electron","positron","neutrino",
    "photon","gluon","W","Z","proton","neutron",
};

static const double PARTICLE_MASSES[PTYPE_COUNT] = {
    M_UP_QUARK, M_DOWN_QUARK, M_ELECTRON, M_ELECTRON,
    M_NEUTRINO, M_PHOTON, M_PHOTON, M_W_BOSON,
    M_Z_BOSON, M_PROTON, M_NEUTRON,
};

static const double PARTICLE_CHARGES[PTYPE_COUNT] = {
    2.0/3.0, -1.0/3.0, -1.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
};

/* Periodic table: atomic_number -> (symbol, electronegativity) */
typedef struct { const char *sym; double en; } ElemInfo;
static const ElemInfo ELEMENTS[] = {
    {NULL, 0}, /* 0 unused */
    {"H",  2.20}, {"He", 0.00}, {"Li", 0.98}, {"Be", 1.57},
    {"B",  2.04}, {"C",  2.55}, {"N",  3.04}, {"O",  3.44},
    {"F",  3.98}, {"Ne", 0.00}, {"Na", 0.93}, {"Mg", 1.31},
    {"Al", 1.61}, {"Si", 1.90}, {"P",  2.19}, {"S",  2.58},
    {"Cl", 3.16}, {"Ar", 0.00}, {"K",  0.82}, {"Ca", 1.00},
    {NULL, 0}, {NULL, 0}, {NULL, 0}, {NULL, 0}, {NULL, 0}, {NULL, 0},
    {"Fe", 1.83},
};
#define ELEM_TABLE_SIZE 27

/* ================================================================== */
/*  Public lookup helpers                                             */
/* ================================================================== */

const char *epoch_name(EpochId e)
{
    if (e < 0 || e >= EPOCH_COUNT) return "Unknown";
    return EPOCH_NAMES[e];
}

const char *particle_type_name(ParticleType t)
{
    if (t < 0 || t >= PTYPE_COUNT) return "?";
    return PARTICLE_NAMES[t];
}

double particle_mass(ParticleType t)
{
    if (t < 0 || t >= PTYPE_COUNT) return 0.0;
    return PARTICLE_MASSES[t];
}

double particle_charge(ParticleType t)
{
    if (t < 0 || t >= PTYPE_COUNT) return 0.0;
    return PARTICLE_CHARGES[t];
}

const char *element_symbol(int z)
{
    if (z < 1 || z >= ELEM_TABLE_SIZE) return "??";
    if (!ELEMENTS[z].sym) return "??";
    return ELEMENTS[z].sym;
}

static double element_electronegativity(int z)
{
    if (z < 1 || z >= ELEM_TABLE_SIZE) return 1.0;
    if (!ELEMENTS[z].sym) return 1.0;
    return ELEMENTS[z].en;
}

/* ================================================================== */
/*  Wave Function                                                     */
/* ================================================================== */

static void wf_init(WaveFunction *w)
{
    w->amplitude = 1.0;
    w->phase     = 0.0;
    w->coherent  = true;
}

static void wf_evolve(WaveFunction *w, double dt, double energy)
{
    if (w->coherent) {
        w->phase += energy * dt / SIM_HBAR;
        w->phase = fmod(w->phase, 2.0 * SIM_PI);
    }
}

static bool wf_collapse(WaveFunction *w, unsigned int *rng)
{
    bool result = rng_double(rng) < (w->amplitude * w->amplitude);
    w->amplitude = result ? 1.0 : 0.0;
    w->coherent  = false;
    return result;
}

/* ================================================================== */
/*  Particle helpers                                                  */
/* ================================================================== */

static double particle_energy(const Particle *p)
{
    double p2 = p->momentum[0]*p->momentum[0]
              + p->momentum[1]*p->momentum[1]
              + p->momentum[2]*p->momentum[2];
    double m  = particle_mass(p->type);
    return sqrt(p2 * SIM_C * SIM_C + (m * SIM_C * SIM_C) * (m * SIM_C * SIM_C));
}

static Particle *qf_add_particle(QuantumField *qf, ParticleType type)
{
    if (qf->particle_count >= MAX_PARTICLES) return NULL;
    Particle *p   = &qf->particles[qf->particle_count++];
    memset(p, 0, sizeof(*p));
    p->type       = type;
    p->spin       = SPIN_UP;
    p->color      = COLOR_NONE;
    wf_init(&p->wave_fn);
    p->entangled_with = -1;
    p->id         = qf->next_id++;
    p->alive      = true;
    return p;
}

static void qf_remove_particle(QuantumField *qf, int idx)
{
    if (idx < 0 || idx >= qf->particle_count) return;
    qf->particles[idx] = qf->particles[qf->particle_count - 1];
    qf->particle_count--;
}

/* ================================================================== */
/*  Quantum Field                                                     */
/* ================================================================== */

static void qf_init(QuantumField *qf, double temperature)
{
    memset(qf, 0, sizeof(*qf));
    qf->temperature = temperature;
    qf->next_id = 1;
}

/* Pair production: create particle-antiparticle pair from energy */
static bool qf_pair_production(QuantumField *qf, double energy, unsigned int *rng)
{
    if (energy < 2.0 * M_ELECTRON * SIM_C * SIM_C) return false;
    if (qf->particle_count + 2 > MAX_PARTICLES) return false;

    ParticleType p_type, ap_type;
    if (energy >= 2.0 * M_PROTON * SIM_C * SIM_C && rng_double(rng) < 0.1) {
        p_type  = PTYPE_UP;
        ap_type = PTYPE_DOWN;
    } else {
        p_type  = PTYPE_ELECTRON;
        ap_type = PTYPE_POSITRON;
    }

    double dir[3];
    dir[0] = rng_gauss(rng);
    dir[1] = rng_gauss(rng);
    dir[2] = rng_gauss(rng);
    double norm = sqrt(dir[0]*dir[0]+dir[1]*dir[1]+dir[2]*dir[2]);
    if (norm < 1e-20) norm = 1.0;
    double p_momentum = energy / (2.0 * SIM_C);

    Particle *pa = qf_add_particle(qf, p_type);
    Particle *pb = qf_add_particle(qf, ap_type);
    if (!pa || !pb) return false;

    for (int i = 0; i < 3; i++) {
        pa->momentum[i] =  dir[i] / norm * p_momentum;
        pb->momentum[i] = -dir[i] / norm * p_momentum;
    }
    pa->spin = SPIN_UP;
    pb->spin = SPIN_DOWN;
    pa->entangled_with = pb->id;
    pb->entangled_with = pa->id;
    qf->total_created += 2;
    return true;
}

/* Vacuum fluctuation */
static bool qf_vacuum_fluctuation(QuantumField *qf, unsigned int *rng)
{
    double prob = qf->temperature / T_PLANCK;
    if (prob > 0.5) prob = 0.5;
    if (rng_double(rng) < prob) {
        double energy = rng_expo(rng, 1.0 / (qf->temperature * 0.001));
        return qf_pair_production(qf, energy, rng);
    }
    return false;
}

/* Quark confinement: combine quarks into hadrons */
static int qf_quark_confinement(QuantumField *qf, unsigned int *rng)
{
    if (qf->temperature > T_QUARK_HADRON) return 0;

    int hadrons = 0;

    /* Collect indices of ups and downs */
    int ups[MAX_PARTICLES], nu = 0;
    int downs[MAX_PARTICLES], nd = 0;
    for (int i = 0; i < qf->particle_count; i++) {
        if (qf->particles[i].type == PTYPE_UP)   ups[nu++]   = i;
        if (qf->particles[i].type == PTYPE_DOWN)  downs[nd++] = i;
    }

    /* Form protons (uud) */
    while (nu >= 2 && nd >= 1) {
        int iu1 = ups[--nu];
        int iu2 = ups[--nu];
        int id1 = downs[--nd];

        Particle *u1 = &qf->particles[iu1];
        Particle *u2 = &qf->particles[iu2];
        Particle *d1 = &qf->particles[id1];

        Particle *proton = qf_add_particle(qf, PTYPE_PROTON);
        if (!proton) break;

        for (int i = 0; i < 3; i++) {
            proton->position[i] = u1->position[i];
            proton->momentum[i] = u1->momentum[i]+u2->momentum[i]+d1->momentum[i];
        }

        u1->alive = false;
        u2->alive = false;
        d1->alive = false;
        hadrons++;
    }

    /* Form neutrons (udd) */
    while (nu >= 1 && nd >= 2) {
        int iu1 = ups[--nu];
        int id1 = downs[--nd];
        int id2 = downs[--nd];

        Particle *u1 = &qf->particles[iu1];
        Particle *d1 = &qf->particles[id1];
        Particle *d2 = &qf->particles[id2];

        Particle *neutron = qf_add_particle(qf, PTYPE_NEUTRON);
        if (!neutron) break;

        for (int i = 0; i < 3; i++) {
            neutron->position[i] = u1->position[i];
            neutron->momentum[i] = u1->momentum[i]+d1->momentum[i]+d2->momentum[i];
        }

        u1->alive = false;
        d1->alive = false;
        d2->alive = false;
        hadrons++;
    }

    /* Compact out dead particles */
    int w = 0;
    for (int r = 0; r < qf->particle_count; r++) {
        if (qf->particles[r].alive) {
            if (w != r) qf->particles[w] = qf->particles[r];
            w++;
        }
    }
    qf->particle_count = w;

    return hadrons;
}

/* Evolve all particles by dt */
static void qf_evolve(QuantumField *qf, double dt)
{
    for (int i = 0; i < qf->particle_count; i++) {
        Particle *p = &qf->particles[i];
        double m = particle_mass(p->type);
        if (m > 0) {
            for (int j = 0; j < 3; j++)
                p->position[j] += p->momentum[j] / m * dt;
        } else {
            double pmag = sqrt(p->momentum[0]*p->momentum[0]
                             + p->momentum[1]*p->momentum[1]
                             + p->momentum[2]*p->momentum[2]);
            if (pmag < 1e-30) pmag = 1.0;
            for (int j = 0; j < 3; j++)
                p->position[j] += p->momentum[j] / pmag * SIM_C * dt;
        }
        wf_evolve(&p->wave_fn, dt, particle_energy(p));
    }
}

/* Count particles of a given type */
static int qf_count_type(const QuantumField *qf, ParticleType t)
{
    int n = 0;
    for (int i = 0; i < qf->particle_count; i++)
        if (qf->particles[i].type == t) n++;
    return n;
}

/* ================================================================== */
/*  Atom helpers                                                      */
/* ================================================================== */

static void atom_build_shells(Atom *a)
{
    int remaining = a->electron_count;
    a->num_shells = 0;
    for (int i = 0; i < NUM_ELECTRON_SHELLS && remaining > 0; i++) {
        ElectronShell *s = &a->shells[i];
        s->n = i + 1;
        s->max_electrons = ELECTRON_SHELLS[i];
        s->electrons = remaining < s->max_electrons ? remaining : s->max_electrons;
        remaining -= s->electrons;
        a->num_shells = i + 1;
    }
}

static void atom_compute_ionization(Atom *a)
{
    if (a->num_shells == 0 || a->shells[a->num_shells-1].electrons == 0) {
        a->ionization_energy = 0.0;
        return;
    }
    int n = a->shells[a->num_shells-1].n;
    int inner_e = 0;
    for (int i = 0; i < a->num_shells - 1; i++)
        inner_e += a->shells[i].electrons;
    double z_eff = a->atomic_number - inner_e;
    a->ionization_energy = 13.6 * z_eff * z_eff / ((double)n * n);
}

static void atom_init(Atom *a, int z, int mass, AtomicSystem *as, unsigned int *rng)
{
    memset(a, 0, sizeof(*a));
    a->atomic_number  = z;
    a->mass_number    = mass > 0 ? mass : (z == 1 ? 1 : z * 2);
    a->electron_count = z;
    a->alive          = true;
    a->atom_id        = as->next_id++;
    for (int i = 0; i < 3; i++) {
        a->position[i] = rng_gauss(rng) * 5.0;
        a->velocity[i] = 0.0;
    }
    atom_build_shells(a);
    atom_compute_ionization(a);
}

static Atom *as_add_atom(AtomicSystem *as)
{
    if (as->atom_count >= MAX_ATOMS) return NULL;
    return &as->atoms[as->atom_count++];
}

static int atom_valence(const Atom *a)
{
    if (a->num_shells == 0) return 0;
    return a->shells[a->num_shells-1].electrons;
}

static bool atom_is_noble(const Atom *a)
{
    if (a->num_shells == 0) return false;
    const ElectronShell *s = &a->shells[a->num_shells-1];
    return s->electrons >= s->max_electrons;
}

/* ================================================================== */
/*  Atomic System                                                     */
/* ================================================================== */

static void as_init(AtomicSystem *as)
{
    memset(as, 0, sizeof(*as));
    as->temperature = T_RECOMBINATION;
    as->next_id = 1;
}

/* Nucleosynthesis: form He-4 and remaining H from proton/neutron counts */
static int as_nucleosynthesis(AtomicSystem *as, int protons, int neutrons,
                              unsigned int *rng)
{
    int formed = 0;

    /* He-4: 2p + 2n */
    while (protons >= 2 && neutrons >= 2) {
        Atom *a = as_add_atom(as);
        if (!a) break;
        atom_init(a, 2, 4, as, rng);
        protons  -= 2;
        neutrons -= 2;
        formed++;
    }

    /* Remaining protons -> hydrogen */
    while (protons > 0) {
        Atom *a = as_add_atom(as);
        if (!a) break;
        atom_init(a, 1, 1, as, rng);
        protons--;
        formed++;
    }
    return formed;
}

/* Recombination: capture electrons into protons from quantum field */
static int as_recombination(AtomicSystem *as, QuantumField *qf, unsigned int *rng)
{
    if (as->temperature > T_RECOMBINATION) return 0;
    int formed = 0;

    for (int i = qf->particle_count - 1; i >= 0; i--) {
        if (qf->particles[i].type != PTYPE_PROTON) continue;

        /* Find an electron */
        int ei = -1;
        for (int j = 0; j < qf->particle_count; j++) {
            if (qf->particles[j].type == PTYPE_ELECTRON) { ei = j; break; }
        }
        if (ei < 0) break;

        Atom *a = as_add_atom(as);
        if (!a) break;
        atom_init(a, 1, 1, as, rng);
        for (int k = 0; k < 3; k++)
            a->position[k] = qf->particles[i].position[k];

        /* Remove proton and electron (remove higher index first) */
        int hi = i > ei ? i : ei;
        int lo = i > ei ? ei : i;
        qf_remove_particle(qf, hi);
        qf_remove_particle(qf, lo);

        formed++;
        /* indices shifted, break to be safe */
        i -= 2;
        if (i < 0) break;
    }
    return formed;
}

/* Stellar nucleosynthesis: triple-alpha, C+He->O, O+He->N */
static int as_stellar_nucleosynthesis(AtomicSystem *as, double temperature,
                                      unsigned int *rng)
{
    int formed = 0;
    if (temperature < 1e3) return 0;

    /* Count He */
    int he_idx[MAX_ATOMS], nhe = 0;
    int c_idx[MAX_ATOMS],  nc  = 0;
    int o_idx[MAX_ATOMS],  no  = 0;
    for (int i = 0; i < as->atom_count; i++) {
        if (as->atoms[i].atomic_number == 2) he_idx[nhe++] = i;
        if (as->atoms[i].atomic_number == 6) c_idx[nc++]   = i;
        if (as->atoms[i].atomic_number == 8) o_idx[no++]   = i;
    }

    /* Triple-alpha: 3 He -> C */
    while (nhe >= 3 && rng_double(rng) < 0.01) {
        /* Mark 3 heliums as dead */
        for (int k = 0; k < 3; k++)
            as->atoms[he_idx[--nhe]].alive = false;

        Atom *c = as_add_atom(as);
        if (!c) break;
        atom_init(c, 6, 12, as, rng);
        formed++;
    }

    /* Refresh He/C lists after modifications */
    nhe = nc = no = 0;
    for (int i = 0; i < as->atom_count; i++) {
        if (!as->atoms[i].alive) continue;
        if (as->atoms[i].atomic_number == 2) he_idx[nhe++] = i;
        if (as->atoms[i].atomic_number == 6) c_idx[nc++]   = i;
        if (as->atoms[i].atomic_number == 8) o_idx[no++]   = i;
    }

    /* C + He -> O */
    while (nc > 0 && nhe > 0 && rng_double(rng) < 0.02) {
        as->atoms[c_idx[--nc]].alive  = false;
        as->atoms[he_idx[--nhe]].alive = false;

        Atom *o = as_add_atom(as);
        if (!o) break;
        atom_init(o, 8, 16, as, rng);
        formed++;
    }

    /* Refresh */
    nhe = no = 0;
    for (int i = 0; i < as->atom_count; i++) {
        if (!as->atoms[i].alive) continue;
        if (as->atoms[i].atomic_number == 2) he_idx[nhe++] = i;
        if (as->atoms[i].atomic_number == 8) o_idx[no++]   = i;
    }

    /* O + He -> N (simplified) */
    if (no > 0 && nhe > 0 && rng_double(rng) < 0.005) {
        as->atoms[o_idx[--no]].alive   = false;
        as->atoms[he_idx[--nhe]].alive = false;

        Atom *n = as_add_atom(as);
        if (n) {
            atom_init(n, 7, 14, as, rng);
            formed++;
        }
    }

    /* Compact out dead atoms */
    int w = 0;
    for (int r = 0; r < as->atom_count; r++) {
        if (as->atoms[r].alive) {
            if (w != r) as->atoms[w] = as->atoms[r];
            w++;
        }
    }
    as->atom_count = w;

    return formed;
}

/* ================================================================== */
/*  Chemical System                                                   */
/* ================================================================== */

static void cs_init(ChemicalSystem *cs)
{
    memset(cs, 0, sizeof(*cs));
    cs->next_id = 1;
    cs->initialised = true;
}

static Molecule *cs_add_molecule(ChemicalSystem *cs, const char *name)
{
    if (cs->molecule_count >= MAX_MOLECULES) return NULL;
    Molecule *m = &cs->molecules[cs->molecule_count++];
    memset(m, 0, sizeof(*m));
    strncpy(m->name, name, sizeof(m->name)-1);
    m->molecule_id = cs->next_id++;
    m->alive = true;
    return m;
}

/* Find first unbonded atom of given atomic_number; return index or -1 */
static int find_unbonded(const AtomicSystem *as, int z)
{
    for (int i = 0; i < as->atom_count; i++) {
        if (as->atoms[i].alive && as->atoms[i].atomic_number == z
            && as->atoms[i].bond_count == 0)
            return i;
    }
    return -1;
}

/* Find atom with fewer than max_bonds bonds */
static int find_partially_bonded(const AtomicSystem *as, int z, int max_bonds)
{
    for (int i = 0; i < as->atom_count; i++) {
        if (as->atoms[i].alive && as->atoms[i].atomic_number == z
            && as->atoms[i].bond_count < max_bonds)
            return i;
    }
    return -1;
}

/* Form water: 2H + O -> H2O */
static int cs_form_water(ChemicalSystem *cs, AtomicSystem *as)
{
    int formed = 0;
    for (;;) {
        int h1 = find_unbonded(as, 1);
        if (h1 < 0) break;
        int h2 = -1;
        for (int i = h1+1; i < as->atom_count; i++) {
            if (as->atoms[i].alive && as->atoms[i].atomic_number == 1
                && as->atoms[i].bond_count == 0) { h2 = i; break; }
        }
        if (h2 < 0) break;
        int oi = find_partially_bonded(as, 8, 2);
        if (oi < 0) break;

        Molecule *m = cs_add_molecule(cs, "water");
        if (!m) break;
        strncpy(m->formula, "H2O", sizeof(m->formula)-1);
        for (int k = 0; k < 3; k++)
            m->position[k] = as->atoms[oi].position[k];

        /* Record bonds */
        as->atoms[h1].bonds[as->atoms[h1].bond_count++] = as->atoms[oi].atom_id;
        as->atoms[h2].bonds[as->atoms[h2].bond_count++] = as->atoms[oi].atom_id;
        as->atoms[oi].bonds[as->atoms[oi].bond_count++] = as->atoms[h1].atom_id;
        if (as->atoms[oi].bond_count < MAX_BONDS)
            as->atoms[oi].bonds[as->atoms[oi].bond_count++] = as->atoms[h2].atom_id;

        cs->water_count++;
        formed++;
    }
    return formed;
}

/* Form methane: C + 4H -> CH4 */
static int cs_form_methane(ChemicalSystem *cs, AtomicSystem *as)
{
    int formed = 0;
    for (;;) {
        int ci = find_unbonded(as, 6);
        if (ci < 0) break;
        int hs[4], nh = 0;
        for (int i = 0; i < as->atom_count && nh < 4; i++) {
            if (as->atoms[i].alive && as->atoms[i].atomic_number == 1
                && as->atoms[i].bond_count == 0) hs[nh++] = i;
        }
        if (nh < 4) break;

        Molecule *m = cs_add_molecule(cs, "methane");
        if (!m) break;
        strncpy(m->formula, "CH4", sizeof(m->formula)-1);
        m->is_organic = true;
        for (int k = 0; k < 3; k++)
            m->position[k] = as->atoms[ci].position[k];

        for (int j = 0; j < 4; j++) {
            if (as->atoms[ci].bond_count < MAX_BONDS)
                as->atoms[ci].bonds[as->atoms[ci].bond_count++] = as->atoms[hs[j]].atom_id;
            as->atoms[hs[j]].bonds[as->atoms[hs[j]].bond_count++] = as->atoms[ci].atom_id;
        }
        formed++;
    }
    return formed;
}

/* Form ammonia: N + 3H -> NH3 */
static int cs_form_ammonia(ChemicalSystem *cs, AtomicSystem *as)
{
    int formed = 0;
    for (;;) {
        int ni = find_unbonded(as, 7);
        if (ni < 0) break;
        int hs[3], nh = 0;
        for (int i = 0; i < as->atom_count && nh < 3; i++) {
            if (as->atoms[i].alive && as->atoms[i].atomic_number == 1
                && as->atoms[i].bond_count == 0) hs[nh++] = i;
        }
        if (nh < 3) break;

        Molecule *m = cs_add_molecule(cs, "ammonia");
        if (!m) break;
        strncpy(m->formula, "NH3", sizeof(m->formula)-1);
        for (int k = 0; k < 3; k++)
            m->position[k] = as->atoms[ni].position[k];

        for (int j = 0; j < 3; j++) {
            if (as->atoms[ni].bond_count < MAX_BONDS)
                as->atoms[ni].bonds[as->atoms[ni].bond_count++] = as->atoms[hs[j]].atom_id;
            as->atoms[hs[j]].bonds[as->atoms[hs[j]].bond_count++] = as->atoms[ni].atom_id;
        }
        formed++;
    }
    return formed;
}

/* Catalysed reaction: form amino acids and nucleotides */
static int cs_catalyzed_reaction(ChemicalSystem *cs, AtomicSystem *as,
                                 double temperature, bool catalyst,
                                 unsigned int *rng)
{
    int formed = 0;
    double ea_factor = catalyst ? 0.3 : 1.0;
    double thermal = SIM_K_B * temperature;
    if (thermal <= 0) return 0;

    /* Try amino acid: needs 2C + 5H + 2O + 1N (simplified glycine) */
    double aa_prob = exp(-5.0 * ea_factor / (thermal + 1e-20));
    if (rng_double(rng) < aa_prob && as->atom_count > 10) {
        /* Check availability */
        int nc=0, nh=0, no=0, nn=0;
        for (int i = 0; i < as->atom_count; i++) {
            if (!as->atoms[i].alive) continue;
            if (as->atoms[i].bond_count > 0) continue;
            switch (as->atoms[i].atomic_number) {
                case 6: nc++; break;
                case 1: nh++; break;
                case 8: no++; break;
                case 7: nn++; break;
            }
        }
        if (nc >= 2 && nh >= 5 && no >= 2 && nn >= 1) {
            Molecule *m = cs_add_molecule(cs, AMINO_ACIDS[rng_int(rng, NUM_AMINO_ACIDS)]);
            if (m) {
                m->is_organic = true;
                cs->amino_acid_count++;
                cs->reactions_occurred++;
                formed++;
                /* Bond 2C + 5H + 2O + 1N */
                int need[] = {6,6, 1,1,1,1,1, 8,8, 7};
                for (int k = 0; k < 10; k++) {
                    int idx = find_unbonded(as, need[k]);
                    if (idx >= 0) as->atoms[idx].bond_count = 1; /* mark used */
                }
            }
        }
    }

    /* Try nucleotide: needs 5C + 8H + 4O + 2N */
    double nuc_prob = exp(-8.0 * ea_factor / (thermal + 1e-20));
    if (rng_double(rng) < nuc_prob && as->atom_count > 19) {
        int nc=0, nh=0, no=0, nn=0;
        for (int i = 0; i < as->atom_count; i++) {
            if (!as->atoms[i].alive) continue;
            if (as->atoms[i].bond_count > 0) continue;
            switch (as->atoms[i].atomic_number) {
                case 6: nc++; break;
                case 1: nh++; break;
                case 8: no++; break;
                case 7: nn++; break;
            }
        }
        if (nc >= 5 && nh >= 8 && no >= 4 && nn >= 2) {
            const char *bases[] = {"A","T","G","C"};
            char name[32];
            snprintf(name, sizeof(name), "nucleotide-%s",
                     bases[rng_int(rng, 4)]);
            Molecule *m = cs_add_molecule(cs, name);
            if (m) {
                m->is_organic = true;
                cs->nucleotide_count++;
                cs->reactions_occurred++;
                formed++;
                int need[] = {6,6,6,6,6, 1,1,1,1,1,1,1,1, 8,8,8,8, 7,7};
                for (int k = 0; k < 19; k++) {
                    int idx = find_unbonded(as, need[k]);
                    if (idx >= 0) as->atoms[idx].bond_count = 1;
                }
            }
        }
    }

    return formed;
}

/* ================================================================== */
/*  DNA / Gene helpers                                                */
/* ================================================================== */

static void gene_init(Gene *g, const char *name, int start, int end,
                       const char *seq, int seq_len, bool essential)
{
    memset(g, 0, sizeof(*g));
    strncpy(g->name, name, sizeof(g->name)-1);
    g->start_pos = start;
    g->end_pos   = end;
    g->essential = essential;
    g->expression_level = 1.0;
    g->length = end - start;
    if (g->length > MAX_DNA_LENGTH) g->length = MAX_DNA_LENGTH;
    if (g->length > seq_len - start) g->length = seq_len - start;
    memcpy(g->sequence, seq + start, g->length);
}

static void gene_update_expression(Gene *g)
{
    int methyl = 0, acetyl = 0;
    for (int i = 0; i < g->mark_count; i++) {
        if (g->marks[i].mark_type == 'M' && g->marks[i].active) methyl++;
        if (g->marks[i].mark_type == 'A' && g->marks[i].active) acetyl++;
    }
    double suppression = methyl / (double)(g->length > 0 ? g->length : 1) * 3.0;
    if (suppression > 1.0) suppression = 1.0;
    double activation = acetyl / (double)(g->length > 0 ? g->length : 1) * 5.0;
    if (activation > 1.0) activation = 1.0;
    g->expression_level = 1.0 - suppression + activation;
    if (g->expression_level < 0.0) g->expression_level = 0.0;
    if (g->expression_level > 1.0) g->expression_level = 1.0;
}

static bool gene_is_silenced(const Gene *g)
{
    int methyl = 0;
    for (int i = 0; i < g->mark_count; i++)
        if (g->marks[i].mark_type == 'M' && g->marks[i].active) methyl++;
    return methyl > g->length * 0.3;
}

static int gene_mutate(Gene *g, double rate, unsigned int *rng)
{
    int mutations = 0;
    for (int i = 0; i < g->length; i++) {
        if (rng_double(rng) < rate) {
            char old = g->sequence[i];
            char choices[3];
            int ci = 0;
            for (int j = 0; j < 4; j++)
                if (NUCLEOTIDE_BASES[j] != old)
                    choices[ci++] = NUCLEOTIDE_BASES[j];
            g->sequence[i] = choices[rng_int(rng, 3)];
            mutations++;
        }
    }
    return mutations;
}

/* Transcribe gene DNA->mRNA (T->U) into buf; returns length */
static int gene_transcribe(const Gene *g, char *buf, int bufsize)
{
    if (gene_is_silenced(g)) return 0;
    int len = g->length < bufsize ? g->length : bufsize;
    for (int i = 0; i < len; i++)
        buf[i] = (g->sequence[i] == 'T') ? 'U' : g->sequence[i];
    return len;
}

/* ================================================================== */
/*  DNA Strand                                                        */
/* ================================================================== */

static void dna_random(DNAStrand *d, int length, int num_genes, unsigned int *rng)
{
    memset(d, 0, sizeof(*d));
    d->length = length < MAX_DNA_LENGTH ? length : MAX_DNA_LENGTH;
    for (int i = 0; i < d->length; i++)
        d->sequence[i] = NUCLEOTIDE_BASES[rng_int(rng, 4)];

    d->gene_count = num_genes < MAX_GENES ? num_genes : MAX_GENES;
    int gene_len = d->length / (d->gene_count + 1);
    for (int i = 0; i < d->gene_count; i++) {
        int start = i * gene_len + rng_int(rng, gene_len / 4 + 1);
        int end   = start + gene_len / 2;
        if (end > d->length) end = d->length;
        char name[16];
        snprintf(name, sizeof(name), "gene_%d", i);
        gene_init(&d->genes[i], name, start, end,
                  d->sequence, d->length, (i == 0));
    }
}

static int dna_apply_mutations(DNAStrand *d, double uv, double cosmic,
                               unsigned int *rng)
{
    int total = 0;
    double rate = UV_MUTATION_RATE * uv + COSMIC_RAY_MUTATION_RATE * cosmic;
    for (int i = 0; i < d->gene_count; i++)
        total += gene_mutate(&d->genes[i], rate, rng);
    /* Non-genic mutations */
    for (int i = 0; i < d->length; i++) {
        if (rng_double(rng) < rate) {
            char old = d->sequence[i];
            char ch[3]; int ci=0;
            for (int j=0;j<4;j++) if (NUCLEOTIDE_BASES[j]!=old) ch[ci++]=NUCLEOTIDE_BASES[j];
            d->sequence[i] = ch[rng_int(rng,3)];
            total++;
        }
    }
    d->mutation_count += total;
    return total;
}

static void dna_apply_epigenetics(DNAStrand *d, double temperature, int generation,
                                  unsigned int *rng)
{
    for (int g = 0; g < d->gene_count; g++) {
        Gene *gene = &d->genes[g];

        /* Methylation */
        if (rng_double(rng) < METHYLATION_PROBABILITY && gene->mark_count < MAX_EPIGENETIC) {
            EpigeneticMark *m = &gene->marks[gene->mark_count++];
            m->position = rng_int(rng, gene->length > 0 ? gene->length : 1);
            m->mark_type = 'M';
            m->active = true;
            m->generation_added = generation;
            gene_update_expression(gene);
        }
        /* Demethylation */
        if (rng_double(rng) < DEMETHYLATION_PROBABILITY) {
            for (int i = gene->mark_count - 1; i >= 0; i--) {
                if (gene->marks[i].mark_type == 'M') {
                    gene->marks[i] = gene->marks[--gene->mark_count];
                    gene_update_expression(gene);
                    break;
                }
            }
        }
        /* Histone acetylation */
        double thermal_factor = temperature / 300.0;
        if (thermal_factor > 2.0) thermal_factor = 2.0;
        if (rng_double(rng) < HISTONE_ACETYLATION_PROB * thermal_factor
            && gene->mark_count < MAX_EPIGENETIC) {
            EpigeneticMark *m = &gene->marks[gene->mark_count++];
            m->position = rng_int(rng, gene->length > 0 ? gene->length : 1);
            m->mark_type = 'A';
            m->active = true;
            m->generation_added = generation;
            gene_update_expression(gene);
        }
        /* Histone deacetylation */
        if (rng_double(rng) < HISTONE_DEACETYLATION_PROB) {
            for (int i = 0; i < gene->mark_count; i++) {
                if (gene->marks[i].mark_type == 'A' && gene->marks[i].active) {
                    gene->marks[i].active = false;
                    gene_update_expression(gene);
                    break;
                }
            }
        }
    }
}

static void dna_replicate(const DNAStrand *src, DNAStrand *dst, unsigned int *rng)
{
    memcpy(dst->sequence, src->sequence, src->length);
    dst->length = src->length;
    dst->generation = src->generation + 1;
    dst->mutation_count = 0;
    dst->gene_count = src->gene_count;
    for (int i = 0; i < src->gene_count; i++) {
        const Gene *sg = &src->genes[i];
        Gene *dg = &dst->genes[i];
        memcpy(dg, sg, sizeof(Gene));
        dg->mark_count = 0;
        /* Partially inherit epigenetic marks */
        for (int j = 0; j < sg->mark_count; j++) {
            if (rng_double(rng) < 0.7 && dg->mark_count < MAX_EPIGENETIC) {
                dg->marks[dg->mark_count] = sg->marks[j];
                dg->marks[dg->mark_count].active =
                    sg->marks[j].active && rng_double(rng) < 0.8;
                dg->mark_count++;
            }
        }
        gene_update_expression(dg);
    }
}

/* ================================================================== */
/*  Protein translation                                               */
/* ================================================================== */

/* Simple codon lookup - returns index into AMINO_ACIDS or -1 for stop, -2 for unknown */
static int translate_codon(char c1, char c2, char c3)
{
    /* AUG -> Met (start/Met=12) */
    if (c1=='A'&&c2=='U'&&c3=='G') return 12;
    /* Stop codons */
    if (c1=='U'&&c2=='A'&&c3=='A') return -1;
    if (c1=='U'&&c2=='A'&&c3=='G') return -1;
    if (c1=='U'&&c2=='G'&&c3=='A') return -1;
    /* Phe */
    if (c1=='U'&&c2=='U'&&(c3=='U'||c3=='C')) return 13;
    /* Leu */
    if (c1=='U'&&c2=='U'&&(c3=='A'||c3=='G')) return 10;
    if (c1=='C'&&c2=='U') return 10;
    /* Ile */
    if (c1=='A'&&c2=='U'&&(c3=='U'||c3=='C'||c3=='A')) return 9;
    /* Val */
    if (c1=='G'&&c2=='U') return 19;
    /* Ser (UCx) */
    if (c1=='U'&&c2=='C') return 15;
    /* Pro */
    if (c1=='C'&&c2=='C') return 14;
    /* Thr */
    if (c1=='A'&&c2=='C') return 16;
    /* Ala */
    if (c1=='G'&&c2=='C') return 0;
    /* Tyr */
    if (c1=='U'&&c2=='A'&&(c3=='U'||c3=='C')) return 18;
    /* His */
    if (c1=='C'&&c2=='A'&&(c3=='U'||c3=='C')) return 8;
    /* Gln */
    if (c1=='C'&&c2=='A'&&(c3=='A'||c3=='G')) return 5;
    /* Asn */
    if (c1=='A'&&c2=='A'&&(c3=='U'||c3=='C')) return 2;
    /* Lys */
    if (c1=='A'&&c2=='A'&&(c3=='A'||c3=='G')) return 11;
    /* Asp */
    if (c1=='G'&&c2=='A'&&(c3=='U'||c3=='C')) return 3;
    /* Glu */
    if (c1=='G'&&c2=='A'&&(c3=='A'||c3=='G')) return 6;
    /* Cys */
    if (c1=='U'&&c2=='G'&&(c3=='U'||c3=='C')) return 4;
    /* Trp */
    if (c1=='U'&&c2=='G'&&c3=='G') return 17;
    /* Arg (CGx) */
    if (c1=='C'&&c2=='G') return 1;
    /* Ser (AGU/AGC) */
    if (c1=='A'&&c2=='G'&&(c3=='U'||c3=='C')) return 15;
    /* Arg (AGx) */
    if (c1=='A'&&c2=='G'&&(c3=='A'||c3=='G')) return 1;
    /* Gly */
    if (c1=='G'&&c2=='G') return 7;

    return -2; /* unknown */
}

/* ================================================================== */
/*  Cell                                                              */
/* ================================================================== */

static int cell_id_counter = 0;

static void cell_init(Cell *c, int dna_len, unsigned int *rng)
{
    memset(c, 0, sizeof(*c));
    c->alive = true;
    c->fitness = 1.0;
    c->energy = 100.0;
    c->cell_id = ++cell_id_counter;
    dna_random(&c->dna, dna_len, 3, rng);
}

static void cell_transcribe_translate(Cell *c, unsigned int *rng)
{
    char mrna[MAX_DNA_LENGTH];
    for (int g = 0; g < c->dna.gene_count; g++) {
        Gene *gene = &c->dna.genes[g];
        if (gene->expression_level < 0.1) continue;
        int rna_len = gene_transcribe(gene, mrna, MAX_DNA_LENGTH);
        if (rna_len < 3) continue;

        /* Translate */
        bool started = false;
        int prot_idx = c->protein_count;
        if (prot_idx >= MAX_PROTEINS) break;

        Protein *p = &c->proteins[prot_idx];
        memset(p, 0, sizeof(*p));
        p->length = 0;
        p->active = true;

        for (int i = 0; i + 2 < rna_len; i += 3) {
            int aa = translate_codon(mrna[i], mrna[i+1], mrna[i+2]);
            if (aa == 12 && !started) {
                started = true;
                strncpy(p->amino_acids[p->length++], AMINO_ACIDS[12], 3);
            } else if (started) {
                if (aa == -1) break; /* stop */
                if (aa >= 0 && aa < NUM_AMINO_ACIDS && p->length < MAX_PROTEIN_LENGTH) {
                    strncpy(p->amino_acids[p->length++], AMINO_ACIDS[aa], 3);
                }
            }
        }

        if (p->length >= 3 && rng_double(rng) < gene->expression_level) {
            snprintf(p->name, sizeof(p->name), "prot_%s", gene->name);
            const char funcs[] = {'e', 's', 'g'};
            p->function = funcs[rng_int(rng, 3)];
            /* Fold */
            double fold_prob = 0.5 + 0.1 * log(p->length + 1);
            if (fold_prob > 0.9) fold_prob = 0.9;
            p->folded = rng_double(rng) < fold_prob;
            c->protein_count++;
        }
    }
}

static void cell_metabolize(Cell *c, double env_energy)
{
    int enzymes = 0;
    for (int i = 0; i < c->protein_count; i++)
        if (c->proteins[i].function == 'e' && c->proteins[i].folded && c->proteins[i].active)
            enzymes++;
    double efficiency = 0.3 + 0.15 * enzymes;
    c->energy += env_energy * efficiency;
    c->energy -= 3.0;
    if (c->energy > 200.0) c->energy = 200.0;
    if (c->energy <= 0) c->alive = false;
}

static double cell_compute_fitness(Cell *c)
{
    if (!c->alive) { c->fitness = 0.0; return 0.0; }

    /* Essential genes must be active */
    for (int i = 0; i < c->dna.gene_count; i++) {
        if (c->dna.genes[i].essential && gene_is_silenced(&c->dna.genes[i])) {
            c->fitness = 0.1;
            return 0.1;
        }
    }

    int functional = 0;
    for (int i = 0; i < c->protein_count; i++)
        if (c->proteins[i].folded && c->proteins[i].active) functional++;

    double prot_fit = (double)functional / (c->dna.gene_count > 0 ? c->dna.gene_count : 1);
    if (prot_fit > 1.0) prot_fit = 1.0;

    double energy_fit = c->energy / 100.0;
    if (energy_fit > 1.0) energy_fit = 1.0;

    /* GC content */
    int gc = 0;
    for (int i = 0; i < c->dna.length; i++)
        if (c->dna.sequence[i] == 'G' || c->dna.sequence[i] == 'C') gc++;
    double gc_ratio = (double)gc / (c->dna.length > 0 ? c->dna.length : 1);
    double gc_fit = 1.0 - fabs(gc_ratio - 0.5) * 2.0;

    c->fitness = prot_fit * 0.4 + energy_fit * 0.3 + gc_fit * 0.3;
    return c->fitness;
}

static bool cell_divide(const Cell *parent, Cell *daughter, unsigned int *rng)
{
    if (!parent->alive || parent->energy < 50.0) return false;

    memset(daughter, 0, sizeof(*daughter));
    daughter->alive = true;
    daughter->cell_id = ++cell_id_counter;
    daughter->generation = parent->generation + 1;
    daughter->energy = parent->energy / 2.0;
    daughter->fitness = 1.0;

    dna_replicate(&parent->dna, &daughter->dna, rng);
    cell_transcribe_translate(daughter, rng);
    return true;
}

/* ================================================================== */
/*  Biosphere                                                         */
/* ================================================================== */

static void bio_init(Biosphere *bio, int initial_cells, int dna_length,
                     unsigned int *rng)
{
    memset(bio, 0, sizeof(*bio));
    bio->dna_length = dna_length;
    bio->initialised = true;

    int n = initial_cells < MAX_CELLS ? initial_cells : MAX_CELLS;
    for (int i = 0; i < n; i++) {
        cell_init(&bio->cells[i], dna_length, rng);
        cell_transcribe_translate(&bio->cells[i], rng);
        bio->cell_count++;
        bio->total_born++;
    }
}

/* Compare fitness for qsort (descending) */
static int cmp_fitness_desc(const void *a, const void *b)
{
    const Cell *ca = (const Cell *)a;
    const Cell *cb = (const Cell *)b;
    if (cb->fitness > ca->fitness) return 1;
    if (cb->fitness < ca->fitness) return -1;
    return 0;
}

static void bio_step(Biosphere *bio, double env_energy, double uv,
                     double cosmic, double temperature, unsigned int *rng)
{
    bio->generation++;

    /* Metabolize */
    for (int i = 0; i < bio->cell_count; i++)
        cell_metabolize(&bio->cells[i], env_energy);

    /* Mutate & epigenetics */
    for (int i = 0; i < bio->cell_count; i++) {
        if (!bio->cells[i].alive) continue;
        dna_apply_mutations(&bio->cells[i].dna, uv, cosmic, rng);
        dna_apply_epigenetics(&bio->cells[i].dna, temperature,
                              bio->generation, rng);
    }

    /* Transcribe / translate */
    for (int i = 0; i < bio->cell_count; i++)
        if (bio->cells[i].alive)
            cell_transcribe_translate(&bio->cells[i], rng);

    /* Fitness */
    for (int i = 0; i < bio->cell_count; i++)
        cell_compute_fitness(&bio->cells[i]);

    /* Selection: sort by fitness, top 50% reproduce */
    int alive = 0;
    for (int i = 0; i < bio->cell_count; i++)
        if (bio->cells[i].alive) alive++;

    if (alive > 0) {
        /* Sort live cells to front */
        qsort(bio->cells, bio->cell_count, sizeof(Cell), cmp_fitness_desc);

        int cutoff = alive / 2;
        if (cutoff < 1) cutoff = 1;

        Cell daughters[MAX_CELLS];
        int nd = 0;
        for (int i = 0; i < cutoff && nd < MAX_CELLS - bio->cell_count; i++) {
            if (cell_divide(&bio->cells[i], &daughters[nd], rng)) {
                bio->cells[i].energy /= 2.0;  /* parent loses energy */
                bio->total_born++;
                nd++;
            }
        }
        /* Append daughters */
        for (int i = 0; i < nd && bio->cell_count < MAX_CELLS; i++)
            bio->cells[bio->cell_count++] = daughters[i];
    }

    /* Remove dead */
    int w = 0;
    for (int r = 0; r < bio->cell_count; r++) {
        if (bio->cells[r].alive) {
            if (w != r) bio->cells[w] = bio->cells[r];
            w++;
        } else {
            bio->total_died++;
        }
    }
    bio->cell_count = w;

    /* Population cap */
    if (bio->cell_count > MAX_CELLS) {
        qsort(bio->cells, bio->cell_count, sizeof(Cell), cmp_fitness_desc);
        bio->total_died += bio->cell_count - MAX_CELLS;
        bio->cell_count = MAX_CELLS;
    }
}

static double bio_average_fitness(const Biosphere *bio)
{
    if (bio->cell_count == 0) return 0.0;
    double sum = 0;
    for (int i = 0; i < bio->cell_count; i++)
        sum += bio->cells[i].fitness;
    return sum / bio->cell_count;
}

static int bio_total_mutations(const Biosphere *bio)
{
    int total = 0;
    for (int i = 0; i < bio->cell_count; i++)
        total += bio->cells[i].dna.mutation_count;
    return total;
}

/* ================================================================== */
/*  Environment                                                       */
/* ================================================================== */

static void env_init(Environment *e, double initial_temp)
{
    memset(e, 0, sizeof(*e));
    e->temperature = initial_temp;
}

static bool env_is_habitable(const Environment *e)
{
    double rad = e->uv_intensity + e->cosmic_ray_flux + e->stellar_wind;
    return (e->temperature > 200 && e->temperature < 400
            && e->water_availability > 0.1
            && rad < RADIATION_DAMAGE_THRESHOLD);
}

static double env_thermal_energy(const Environment *e)
{
    if (e->temperature < 100 || e->temperature > 500) return 0.1;
    double te = e->temperature * 0.1;
    return te > 0.1 ? te : 0.1;
}

static void env_apply_event(Environment *e, EnvironmentalEvent *ev)
{
    if (strncmp(ev->event_type, "volcanic", 8) == 0) {
        e->temperature += ev->intensity * 2;
        e->atmospheric_density += 0.01;
        if (e->atmospheric_density > 1.0) e->atmospheric_density = 1.0;
        e->uv_intensity *= 0.9;
    } else if (strncmp(ev->event_type, "asteroid", 8) == 0) {
        e->temperature -= ev->intensity * 5;
        e->cosmic_ray_flux += ev->intensity;
        e->uv_intensity *= 0.5;
    } else if (strncmp(ev->event_type, "solar_fl", 8) == 0) {
        e->uv_intensity += ev->intensity;
        e->cosmic_ray_flux += ev->intensity * 0.5;
    } else if (strncmp(ev->event_type, "ice_age", 7) == 0) {
        e->temperature -= ev->intensity * 20;
        e->water_availability *= 0.8;
    }
}

static void env_update(Environment *e, int epoch, unsigned int *rng)
{
    e->tick++;

    /* Temperature evolution */
    if (epoch < 1000) {
        e->temperature = T_PLANCK * exp(-(double)epoch / 200.0);
    } else if (epoch < 50000) {
        double t = T_PLANCK * exp(-(double)epoch / 200.0);
        e->temperature = t > T_CMB ? t : T_CMB;
    } else if (epoch < 200000) {
        e->temperature = T_CMB + rng_gauss(rng) * 0.5;
    } else {
        e->temperature = T_EARTH_SURFACE + rng_gauss(rng) * 5.0;
        e->day_night_cycle = fmod(e->tick, 100) / 100.0;
        double temp_mod = 10.0 * sin(e->day_night_cycle * 2.0 * SIM_PI);
        e->temperature += temp_mod;
        e->season = fmod(e->tick, 1000) / 1000.0;
        double season_mod = 15.0 * sin(e->season * 2.0 * SIM_PI);
        e->temperature += season_mod;
    }

    /* UV */
    if (epoch > 100000) {
        double base_uv = 1.0;
        if (e->day_night_cycle > 0.25 && e->day_night_cycle < 0.75) {
            e->uv_intensity = base_uv *
                sin((e->day_night_cycle - 0.25) * 2.0 * SIM_PI);
        } else {
            e->uv_intensity = 0.0;
        }
    } else {
        e->uv_intensity = 0.0;
    }

    /* Cosmic ray flux */
    if (epoch > 10000) {
        e->cosmic_ray_flux = 0.1 + rng_expo(rng, 10.0);
    } else {
        e->cosmic_ray_flux = 1.0;
    }

    /* Atmospheric density */
    if (epoch > 210000) {
        e->atmospheric_density = (double)(epoch - 210000) / 50000.0;
        if (e->atmospheric_density > 1.0) e->atmospheric_density = 1.0;
        e->uv_intensity *= (1.0 - e->atmospheric_density * 0.7);
        e->cosmic_ray_flux *= (1.0 - e->atmospheric_density * 0.5);
    }

    /* Water */
    if (epoch > 220000) {
        e->water_availability = (double)(epoch - 220000) / 30000.0;
        if (e->water_availability > 1.0) e->water_availability = 1.0;
    }

    /* Random events */
    if (epoch > 210000 && rng_double(rng) < 0.005) {
        if (e->event_count < MAX_EVENTS) {
            EnvironmentalEvent *ev = &e->events[e->event_count++];
            strncpy(ev->event_type, "volcanic", sizeof(ev->event_type)-1);
            ev->intensity = 0.5 + rng_double(rng) * 2.5;
            ev->duration = 10 + rng_int(rng, 90);
            ev->tick_occurred = e->tick;
        }
    }
    if (rng_double(rng) < 0.0001) {
        if (e->event_count < MAX_EVENTS) {
            EnvironmentalEvent *ev = &e->events[e->event_count++];
            strncpy(ev->event_type, "asteroid", sizeof(ev->event_type)-1);
            ev->intensity = 1.0 + rng_double(rng) * 9.0;
            ev->duration = 50 + rng_int(rng, 450);
            ev->tick_occurred = e->tick;
        }
    }
    if (epoch > 100000 && rng_double(rng) < 0.01) {
        if (e->event_count < MAX_EVENTS) {
            EnvironmentalEvent *ev = &e->events[e->event_count++];
            strncpy(ev->event_type, "solar_flare", sizeof(ev->event_type)-1);
            ev->intensity = 0.1 + rng_double(rng) * 1.9;
            ev->duration = 5 + rng_int(rng, 15);
            ev->tick_occurred = e->tick;
        }
    }
    if (epoch > 250000 && rng_double(rng) < 0.001) {
        if (e->event_count < MAX_EVENTS) {
            EnvironmentalEvent *ev = &e->events[e->event_count++];
            strncpy(ev->event_type, "ice_age", sizeof(ev->event_type)-1);
            ev->intensity = 0.5 + rng_double(rng) * 1.0;
            ev->duration = 500 + rng_int(rng, 1500);
            ev->tick_occurred = e->tick;
        }
    }

    /* Process events */
    int w = 0;
    for (int i = 0; i < e->event_count; i++) {
        int elapsed = e->tick - e->events[i].tick_occurred;
        if (elapsed < e->events[i].duration) {
            env_apply_event(e, &e->events[i]);
            if (w != i) e->events[w] = e->events[i];
            w++;
        }
    }
    e->event_count = w;
}

/* ================================================================== */
/*  Universe - orchestrator                                           */
/* ================================================================== */

static EpochId get_epoch_id(int tick)
{
    EpochId id = EPOCH_VOID;
    for (int i = 1; i < EPOCH_COUNT; i++) {
        if (tick >= EPOCH_TICKS[i])
            id = (EpochId)i;
    }
    return id;
}

static void seed_early_universe(Universe *u)
{
    /* 30 up quarks */
    for (int i = 0; i < 30; i++) {
        Particle *p = qf_add_particle(&u->qf, PTYPE_UP);
        if (!p) break;
        for (int j = 0; j < 3; j++) {
            p->position[j] = rng_gauss(&u->rng_state);
            p->momentum[j] = rng_gauss(&u->rng_state) * 5.0;
        }
        p->spin  = rng_int(&u->rng_state, 2) ? SPIN_UP : SPIN_DOWN;
        p->color = (Color)(1 + rng_int(&u->rng_state, 3));
    }
    /* 20 down quarks */
    for (int i = 0; i < 20; i++) {
        Particle *p = qf_add_particle(&u->qf, PTYPE_DOWN);
        if (!p) break;
        for (int j = 0; j < 3; j++) {
            p->position[j] = rng_gauss(&u->rng_state);
            p->momentum[j] = rng_gauss(&u->rng_state) * 5.0;
        }
        p->spin  = rng_int(&u->rng_state, 2) ? SPIN_UP : SPIN_DOWN;
        p->color = (Color)(1 + rng_int(&u->rng_state, 3));
    }
    /* 40 electrons */
    for (int i = 0; i < 40; i++) {
        Particle *p = qf_add_particle(&u->qf, PTYPE_ELECTRON);
        if (!p) break;
        for (int j = 0; j < 3; j++) {
            p->position[j] = rng_gauss(&u->rng_state) * 2.0;
            p->momentum[j] = rng_gauss(&u->rng_state) * 3.0;
        }
    }
    /* 5 photons */
    for (int i = 0; i < 5; i++) {
        Particle *p = qf_add_particle(&u->qf, PTYPE_PHOTON);
        if (!p) break;
        for (int j = 0; j < 3; j++)
            p->momentum[j] = rng_gauss(&u->rng_state) * 10.0;
    }
    u->particles_created += u->qf.particle_count;
}

void universe_init(Universe *u, unsigned int seed)
{
    memset(u, 0, sizeof(*u));
    u->rng_state    = seed ? seed : 42;
    u->max_ticks    = PRESENT_EPOCH;
    u->step_size    = 1;
    u->current_epoch = EPOCH_VOID;

    qf_init(&u->qf, T_PLANCK);
    as_init(&u->as);
    /* cs and bio are initialised on demand */
    env_init(&u->env, T_PLANCK);
}

void universe_step(Universe *u)
{
    u->tick += u->step_size;

    /* Epoch transition */
    EpochId new_epoch = get_epoch_id(u->tick);
    u->current_epoch = new_epoch;

    /* Environment */
    env_update(&u->env, u->tick, &u->rng_state);

    /* === Quantum level === */
    if (u->tick <= HADRON_EPOCH) {
        u->qf.temperature = u->env.temperature;

        /* Seed on first quantum tick */
        if (u->qf.particle_count == 0 && u->env.temperature > 100)
            seed_early_universe(u);

        /* Pair production */
        if (u->env.temperature > 100) {
            int n_attempts = (int)(u->env.temperature / 1000.0);
            if (n_attempts < 1) n_attempts = 1;
            if (n_attempts > 5) n_attempts = 5;
            for (int i = 0; i < n_attempts; i++) {
                if (qf_vacuum_fluctuation(&u->qf, &u->rng_state))
                    u->particles_created += 2;
            }
        }

        qf_evolve(&u->qf, (double)u->step_size);
    }

    /* === Hadron formation === */
    if (u->tick >= HADRON_EPOCH - u->step_size
        && u->tick <= HADRON_EPOCH + u->step_size) {
        u->qf.temperature = u->env.temperature;
        int h = qf_quark_confinement(&u->qf, &u->rng_state);
        u->particles_created += h;
    }

    /* === Nucleosynthesis === */
    if (u->tick >= NUCLEOSYNTHESIS_EPOCH && u->tick < RECOMBINATION_EPOCH) {
        int protons  = qf_count_type(&u->qf, PTYPE_PROTON);
        int neutrons = qf_count_type(&u->qf, PTYPE_NEUTRON);
        if (protons > 0 || neutrons > 0) {
            int formed = as_nucleosynthesis(&u->as, protons, neutrons,
                                            &u->rng_state);
            u->atoms_formed += formed;

            /* Remove used protons and neutrons */
            int w = 0;
            for (int i = 0; i < u->qf.particle_count; i++) {
                if (u->qf.particles[i].type != PTYPE_PROTON
                    && u->qf.particles[i].type != PTYPE_NEUTRON) {
                    if (w != i) u->qf.particles[w] = u->qf.particles[i];
                    w++;
                }
            }
            u->qf.particle_count = w;
        }
    }

    /* === Recombination === */
    if (u->tick >= RECOMBINATION_EPOCH - u->step_size
        && u->tick <= RECOMBINATION_EPOCH + u->step_size) {
        u->as.temperature = u->env.temperature;
        int formed = as_recombination(&u->as, &u->qf, &u->rng_state);
        u->atoms_formed += formed;
    }

    /* === Star formation === */
    if (u->tick >= STAR_FORMATION_EPOCH && u->tick < SOLAR_SYSTEM_EPOCH) {
        u->as.temperature = u->env.temperature;
        int formed = as_stellar_nucleosynthesis(&u->as,
            u->env.temperature * 100, &u->rng_state);
        u->atoms_formed += formed;
    }

    /* === Chemistry === */
    if (u->tick >= EARTH_EPOCH) {
        if (!u->cs.initialised) cs_init(&u->cs);

        /* Seed essential elements at Earth epoch */
        if (u->tick >= EARTH_EPOCH - u->step_size
            && u->tick <= EARTH_EPOCH + u->step_size) {
            struct { int z; int count; } seed_elems[] = {
                {1, 40}, {2, 10}, {6, 15}, {7, 10}, {8, 15}, {15, 3}
            };
            for (int s = 0; s < 6; s++) {
                for (int c = 0; c < seed_elems[s].count; c++) {
                    Atom *a = as_add_atom(&u->as);
                    if (!a) break;
                    atom_init(a, seed_elems[s].z, 0, &u->as, &u->rng_state);
                    u->atoms_formed++;
                }
            }

            /* Form basic molecules */
            u->molecules_formed += cs_form_water(&u->cs, &u->as);
            u->molecules_formed += cs_form_methane(&u->cs, &u->as);
            u->molecules_formed += cs_form_ammonia(&u->cs, &u->as);
        }

        /* Catalysed reactions */
        if (u->tick > EARTH_EPOCH) {
            int formed = cs_catalyzed_reaction(&u->cs, &u->as,
                u->env.temperature, (u->tick > LIFE_EPOCH), &u->rng_state);
            u->molecules_formed += formed;
        }
    }

    /* === Biology === */
    if (u->tick >= LIFE_EPOCH && env_is_habitable(&u->env)) {
        if (!u->bio.initialised) {
            bio_init(&u->bio, 3, 90, &u->rng_state);
            u->cells_born += 3;
        }
        bio_step(&u->bio, env_thermal_energy(&u->env),
                 u->env.uv_intensity, u->env.cosmic_ray_flux,
                 u->env.temperature, &u->rng_state);

        u->cells_born = u->bio.total_born;
        u->mutations  = bio_total_mutations(&u->bio);
    }
}

Snapshot universe_snapshot(const Universe *u)
{
    Snapshot s;
    memset(&s, 0, sizeof(s));
    s.tick            = u->tick;
    s.epoch           = u->current_epoch;
    s.temperature     = u->env.temperature;
    s.particle_count  = u->qf.particle_count;
    s.atom_count      = u->as.atom_count;
    s.molecule_count  = u->cs.molecule_count;
    s.cell_count      = u->bio.cell_count;
    s.average_fitness = bio_average_fitness(&u->bio);
    s.generation      = u->bio.generation;
    s.total_mutations = u->mutations;
    s.habitable       = env_is_habitable(&u->env);
    return s;
}
