/*
 * environment.h - Environmental systems for the cosmic simulation.
 *
 * Models atmosphere composition, temperature, radiation levels,
 * and resource availability across cosmic epochs.
 */
#ifndef SIM_ENVIRONMENT_H
#define SIM_ENVIRONMENT_H

#include "constants.h"
#include <stdbool.h>

/* Atmosphere composition (fractional, sums to ~1.0) */
typedef struct {
    float hydrogen;
    float helium;
    float nitrogen;
    float oxygen;
    float carbon_dioxide;
    float methane;
    float water_vapor;
    float other;
} AtmosphereComposition;

/* Environment state */
typedef struct {
    double                temperature;       /* Kelvin                      */
    double                radiation_level;   /* arbitrary units             */
    float                 uv_intensity;      /* UV flux for mutations       */
    float                 cosmic_ray_flux;   /* cosmic ray flux             */
    float                 available_energy;  /* energy available to life    */
    float                 water_fraction;    /* 0..1 surface water coverage */
    AtmosphereComposition atmosphere;
    bool                  has_magnetic_field;
    bool                  has_ozone_layer;
    int                   tick;              /* current simulation tick     */
} Environment;

/* -- API -- */
void  env_init(Environment *env);
void  env_update(Environment *env, int tick);
void  env_set_epoch_planck(Environment *env);
void  env_set_epoch_inflation(Environment *env);
void  env_set_epoch_electroweak(Environment *env);
void  env_set_epoch_quark(Environment *env);
void  env_set_epoch_hadron(Environment *env);
void  env_set_epoch_nucleosynthesis(Environment *env);
void  env_set_epoch_recombination(Environment *env);
void  env_set_epoch_star_formation(Environment *env);
void  env_set_epoch_solar_system(Environment *env);
void  env_set_epoch_earth(Environment *env);
void  env_set_epoch_life(Environment *env);
void  env_set_epoch_dna(Environment *env);
void  env_set_epoch_present(Environment *env);

const char *env_atmosphere_summary(const Environment *env, char *buf, int bufsize);

#endif /* SIM_ENVIRONMENT_H */
