#!/usr/bin/env perl
# Comprehensive tests for Environment module

use strict;
use warnings;
use Test::More tests => 24;

use lib 'apps/perl/lib';
use Constants qw($T_PLANCK $T_CMB $T_EARTH_SURFACE $RADIATION_DAMAGE_THRESHOLD);
use Environment;

# ============================================================
# Environment creation
# ============================================================
{
    my $env = Environment->new();
    ok(defined $env, 'Environment created');
    is($env->{temperature}, $T_PLANCK, 'Default temperature is T_PLANCK');
    is($env->{uv_intensity}, 0.0, 'UV intensity starts at 0');
    is($env->{cosmic_ray_flux}, 0.0, 'Cosmic ray flux starts at 0');
    is($env->{water_availability}, 0.0, 'Water availability starts at 0');
    is($env->{tick}, 0, 'Tick starts at 0');
}

# Environment: update early universe
{
    my $env = Environment->new();
    $env->update(100);  # Early universe epoch
    ok($env->{temperature} > 0, 'Temperature is positive after update');
    ok($env->{tick} == 1, 'Tick incremented to 1');
    is($env->{uv_intensity}, 0.0, 'No UV in early universe');
}

# Environment: update pre-recombination
{
    my $env = Environment->new();
    $env->update(10000);
    ok($env->{temperature} >= $T_CMB, 'Temperature >= CMB in pre-recombination');
}

# Environment: update post-recombination (pre-star)
{
    my $env = Environment->new();
    $env->update(100000);
    # Temperature should be near T_CMB
    ok($env->{temperature} > 0, 'Temperature positive in post-recombination');
}

# Environment: update planet era
{
    my $env = Environment->new();
    $env->update(250000);
    # Temperature should be near T_EARTH_SURFACE
    ok($env->{temperature} > 100, 'Temperature reasonable in planet era');
    ok($env->{temperature} < 500, 'Temperature not too high in planet era');
}

# Environment: update with stars enables UV
{
    my $env = Environment->new();
    # Force day_night_cycle to daytime range
    $env->{tick} = 30;  # Will make day_night_cycle = 30 % 100 / 100 = 0.30
    $env->update(150000);  # epoch > 100000 so UV is enabled
    # UV may or may not be > 0 depending on day_night_cycle
    ok($env->{uv_intensity} >= 0, 'UV intensity is non-negative with stars');
}

# Environment: get_radiation_dose
{
    my $env = Environment->new();
    $env->{uv_intensity} = 0.5;
    $env->{cosmic_ray_flux} = 0.3;
    $env->{stellar_wind} = 0.1;
    my $dose = $env->get_radiation_dose();
    ok(abs($dose - 0.9) < 1e-10, 'Radiation dose is sum of UV + CR + SW');
}

# Environment: is_habitable -- not habitable by default (T_PLANCK is too high)
{
    my $env = Environment->new();
    ok(!$env->is_habitable(), 'Not habitable at Planck temperature');
}

# Environment: is_habitable -- habitable conditions
{
    my $env = Environment->new();
    $env->{temperature} = 300;
    $env->{water_availability} = 0.5;
    $env->{uv_intensity} = 0.1;
    $env->{cosmic_ray_flux} = 0.1;
    $env->{stellar_wind} = 0.0;
    ok($env->is_habitable(), 'Habitable with proper conditions');
}

# Environment: is_habitable -- too cold
{
    my $env = Environment->new();
    $env->{temperature} = 100;
    $env->{water_availability} = 0.5;
    $env->{uv_intensity} = 0.1;
    $env->{cosmic_ray_flux} = 0.1;
    ok(!$env->is_habitable(), 'Not habitable when too cold');
}

# Environment: is_habitable -- no water
{
    my $env = Environment->new();
    $env->{temperature} = 300;
    $env->{water_availability} = 0.0;
    ok(!$env->is_habitable(), 'Not habitable without water');
}

# Environment: thermal_energy in habitable range
{
    my $env = Environment->new();
    $env->{temperature} = 300;
    my $te = $env->thermal_energy();
    ok($te > 0, 'Thermal energy is positive at 300K');
    ok(abs($te - 30.0) < 1e-10, 'Thermal energy at 300K is 30.0');
}

# Environment: thermal_energy at extreme temperature
{
    my $env = Environment->new();
    $env->{temperature} = 50;
    my $te = $env->thermal_energy();
    ok(abs($te - 0.1) < 1e-10, 'Thermal energy is 0.1 below 100K');
}

# Environment: to_compact
{
    my $env = Environment->new();
    $env->{temperature} = 300;
    $env->{uv_intensity} = 0.5;
    $env->{cosmic_ray_flux} = 0.1;
    $env->{atmospheric_density} = 0.8;
    $env->{water_availability} = 0.9;
    my $compact = $env->to_compact();
    ok(defined $compact, 'Environment to_compact returns a string');
    like($compact, qr/Env\[/, 'to_compact starts with Env[');
}
