/*
 * environment.c - Environmental systems implementation.
 *
 * Manages temperature, radiation, atmosphere composition, and resources
 * as the simulation progresses through cosmic epochs.
 */
#include "environment.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

/* ------------------------------------------------------------------ */
/* Initialization                                                      */
/* ------------------------------------------------------------------ */

void env_init(Environment *env)
{
    memset(env, 0, sizeof(*env));
    env->temperature      = T_PLANCK;
    env->radiation_level  = 1e10;
    env->uv_intensity     = 0.0f;
    env->cosmic_ray_flux  = 1.0f;
    env->available_energy = 0.0f;
    env->water_fraction   = 0.0f;
    env->has_magnetic_field = false;
    env->has_ozone_layer   = false;
    env->tick = 0;

    /* Primordial: pure energy, no atoms yet */
    env->atmosphere.hydrogen = 0.0f;
    env->atmosphere.helium   = 0.0f;
    env->atmosphere.nitrogen = 0.0f;
    env->atmosphere.oxygen   = 0.0f;
    env->atmosphere.carbon_dioxide = 0.0f;
    env->atmosphere.methane  = 0.0f;
    env->atmosphere.water_vapor = 0.0f;
    env->atmosphere.other    = 1.0f;
}

/* ------------------------------------------------------------------ */
/* Epoch configurators                                                 */
/* ------------------------------------------------------------------ */

void env_set_epoch_planck(Environment *env)
{
    env->temperature      = T_PLANCK;
    env->radiation_level  = 1e10;
    env->cosmic_ray_flux  = 0.0f;
    env->uv_intensity     = 0.0f;
    env->available_energy = 0.0f;
    env->atmosphere.other = 1.0f;
}

void env_set_epoch_inflation(Environment *env)
{
    env->temperature      = T_PLANCK * 0.5;
    env->radiation_level  = 1e9;
    env->cosmic_ray_flux  = 0.0f;
    env->uv_intensity     = 0.0f;
    env->available_energy = 0.0f;
}

void env_set_epoch_electroweak(Environment *env)
{
    env->temperature      = T_ELECTROWEAK;
    env->radiation_level  = 1e8;
    env->cosmic_ray_flux  = 0.1f;
    env->uv_intensity     = 0.0f;
}

void env_set_epoch_quark(Environment *env)
{
    env->temperature      = T_QUARK_HADRON * 10.0;
    env->radiation_level  = 1e7;
    env->cosmic_ray_flux  = 0.5f;
    env->uv_intensity     = 0.0f;
}

void env_set_epoch_hadron(Environment *env)
{
    env->temperature      = T_QUARK_HADRON;
    env->radiation_level  = 1e6;
    env->cosmic_ray_flux  = 1.0f;
    env->uv_intensity     = 0.0f;
}

void env_set_epoch_nucleosynthesis(Environment *env)
{
    env->temperature      = T_NUCLEOSYNTHESIS;
    env->radiation_level  = 1e4;
    env->cosmic_ray_flux  = 2.0f;
    env->uv_intensity     = 0.0f;

    /* Primordial gas cloud */
    env->atmosphere.hydrogen = 0.75f;
    env->atmosphere.helium   = 0.25f;
    env->atmosphere.other    = 0.0f;
}

void env_set_epoch_recombination(Environment *env)
{
    env->temperature      = T_RECOMBINATION;
    env->radiation_level  = 100.0;
    env->cosmic_ray_flux  = 3.0f;
    env->uv_intensity     = 0.0f;

    env->atmosphere.hydrogen = 0.75f;
    env->atmosphere.helium   = 0.25f;
}

void env_set_epoch_star_formation(Environment *env)
{
    env->temperature      = 100.0;
    env->radiation_level  = 50.0;
    env->cosmic_ray_flux  = 5.0f;
    env->uv_intensity     = 1.0f;

    env->atmosphere.hydrogen = 0.70f;
    env->atmosphere.helium   = 0.28f;
    env->atmosphere.other    = 0.02f;
}

void env_set_epoch_solar_system(Environment *env)
{
    env->temperature      = 500.0;
    env->radiation_level  = 20.0;
    env->cosmic_ray_flux  = 3.0f;
    env->uv_intensity     = 5.0f;

    env->atmosphere.hydrogen = 0.60f;
    env->atmosphere.helium   = 0.20f;
    env->atmosphere.nitrogen = 0.05f;
    env->atmosphere.carbon_dioxide = 0.10f;
    env->atmosphere.water_vapor    = 0.03f;
    env->atmosphere.other    = 0.02f;
}

void env_set_epoch_earth(Environment *env)
{
    env->temperature      = T_EARTH_SURFACE + 200.0;  /* early Earth was hotter */
    env->radiation_level  = 10.0;
    env->cosmic_ray_flux  = 2.0f;
    env->uv_intensity     = 8.0f;  /* no ozone yet */
    env->available_energy = 5.0f;
    env->water_fraction   = 0.5f;
    env->has_magnetic_field = true;

    env->atmosphere.hydrogen       = 0.05f;
    env->atmosphere.helium         = 0.01f;
    env->atmosphere.nitrogen       = 0.30f;
    env->atmosphere.carbon_dioxide = 0.50f;
    env->atmosphere.water_vapor    = 0.10f;
    env->atmosphere.methane        = 0.03f;
    env->atmosphere.oxygen         = 0.0f;
    env->atmosphere.other          = 0.01f;
}

void env_set_epoch_life(Environment *env)
{
    env->temperature      = T_EARTH_SURFACE + 30.0;
    env->radiation_level  = 5.0;
    env->cosmic_ray_flux  = 1.5f;
    env->uv_intensity     = 6.0f;
    env->available_energy = 10.0f;
    env->water_fraction   = 0.70f;
    env->has_magnetic_field = true;

    env->atmosphere.hydrogen       = 0.01f;
    env->atmosphere.helium         = 0.005f;
    env->atmosphere.nitrogen       = 0.60f;
    env->atmosphere.carbon_dioxide = 0.20f;
    env->atmosphere.water_vapor    = 0.08f;
    env->atmosphere.methane        = 0.05f;
    env->atmosphere.oxygen         = 0.02f;
    env->atmosphere.other          = 0.035f;
}

void env_set_epoch_dna(Environment *env)
{
    env->temperature      = T_EARTH_SURFACE + 10.0;
    env->radiation_level  = 3.0;
    env->cosmic_ray_flux  = 1.0f;
    env->uv_intensity     = 4.0f;
    env->available_energy = 15.0f;
    env->water_fraction   = 0.71f;
    env->has_magnetic_field = true;
    env->has_ozone_layer   = true;

    env->atmosphere.hydrogen       = 0.005f;
    env->atmosphere.helium         = 0.005f;
    env->atmosphere.nitrogen       = 0.70f;
    env->atmosphere.carbon_dioxide = 0.05f;
    env->atmosphere.water_vapor    = 0.04f;
    env->atmosphere.methane        = 0.01f;
    env->atmosphere.oxygen         = 0.15f;
    env->atmosphere.other          = 0.04f;
}

void env_set_epoch_present(Environment *env)
{
    env->temperature      = T_EARTH_SURFACE;
    env->radiation_level  = 1.0;
    env->cosmic_ray_flux  = 0.5f;
    env->uv_intensity     = 2.0f;
    env->available_energy = 20.0f;
    env->water_fraction   = 0.71f;
    env->has_magnetic_field = true;
    env->has_ozone_layer   = true;

    env->atmosphere.hydrogen       = 0.0f;
    env->atmosphere.helium         = 0.005f;
    env->atmosphere.nitrogen       = 0.78f;
    env->atmosphere.carbon_dioxide = 0.0004f;
    env->atmosphere.water_vapor    = 0.01f;
    env->atmosphere.methane        = 0.0002f;
    env->atmosphere.oxygen         = 0.21f;
    env->atmosphere.other          = 0.0f;
}

/* ------------------------------------------------------------------ */
/* Tick-based update (gradual transitions within an epoch)             */
/* ------------------------------------------------------------------ */

void env_update(Environment *env, int tick)
{
    env->tick = tick;

    /* Gradual cooling: temperature decays slightly each tick */
    if (env->temperature > T_CMB) {
        double decay = 1.0 - 1e-6;
        env->temperature *= decay;
        if (env->temperature < T_CMB)
            env->temperature = T_CMB;
    }

    /* Radiation decays with temperature */
    if (env->radiation_level > 0.1) {
        env->radiation_level *= 0.99999;
    }

    /* UV slowly decreases if ozone forms */
    if (env->has_ozone_layer && env->uv_intensity > 1.0f) {
        env->uv_intensity *= 0.9999f;
    }
}

/* ------------------------------------------------------------------ */
/* Summary                                                             */
/* ------------------------------------------------------------------ */

const char *env_atmosphere_summary(const Environment *env, char *buf, int bufsize)
{
    const AtmosphereComposition *a = &env->atmosphere;
    snprintf(buf, (size_t)bufsize,
             "H2:%.0f%% He:%.0f%% N2:%.0f%% O2:%.0f%% CO2:%.1f%% CH4:%.1f%%",
             (double)(a->hydrogen * 100.0f),
             (double)(a->helium * 100.0f),
             (double)(a->nitrogen * 100.0f),
             (double)(a->oxygen * 100.0f),
             (double)(a->carbon_dioxide * 100.0f),
             (double)(a->methane * 100.0f));
    return buf;
}
