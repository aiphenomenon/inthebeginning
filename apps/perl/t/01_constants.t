#!/usr/bin/env perl
# Tests for Constants module

use strict;
use warnings;
use Test::More tests => 12;

use lib 'apps/perl/lib';
use Constants qw(
    $C $HBAR $K_B $M_ELECTRON $M_PROTON $M_NEUTRON
    $T_PLANCK $T_QUARK_HADRON $T_CMB $T_EARTH_SURFACE
    $PLANCK_EPOCH $PRESENT_EPOCH
);

# Fundamental constants are positive
ok($C > 0, 'Speed of light is positive');
ok($HBAR > 0, 'Reduced Planck constant is positive');
ok($K_B > 0, 'Boltzmann constant is positive');

# Mass ordering
ok($M_ELECTRON < $M_PROTON, 'Electron mass < proton mass');
ok(abs($M_PROTON - $M_NEUTRON) / $M_PROTON < 0.01, 'Proton ≈ neutron mass');

# Temperature ordering
ok($T_PLANCK > $T_QUARK_HADRON, 'Planck T > quark-hadron T');
ok($T_QUARK_HADRON > $T_CMB, 'Quark-hadron T > CMB T');
ok($T_CMB > 0, 'CMB temperature is positive');
ok($T_EARTH_SURFACE > 200, 'Earth surface temperature is reasonable');
ok($T_EARTH_SURFACE < 400, 'Earth surface temperature is reasonable');

# Epoch ordering
ok($PLANCK_EPOCH < $PRESENT_EPOCH, 'Planck epoch < Present epoch');
ok($PRESENT_EPOCH > 100000, 'Present epoch is large');
