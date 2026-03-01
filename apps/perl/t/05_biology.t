#!/usr/bin/env perl
# Tests for Biology module

use strict;
use warnings;
use Test::More tests => 7;

use lib 'apps/perl/lib';
use Constants;
use Biology;

# Biosphere creation
{
    my $bio = Biosphere->new(initial_cells => 5, carrying_capacity => 50);
    ok(defined $bio, 'Biosphere created');
    ok(scalar @{$bio->{cells}} > 0, 'Has initial cells');

    # Step
    $bio->step(
        temperature        => 300,
        environment_energy => 1.0,
        uv_intensity       => 0.1,
        cosmic_ray_flux    => 0.01,
    );
    ok(scalar @{$bio->{cells}} > 0, 'Cells survive after step');

    # Average fitness
    my $fitness = $bio->average_fitness();
    ok(defined $fitness, 'average_fitness returns a value');
    ok($fitness >= 0, 'Fitness is non-negative');
    ok($fitness <= 2.0, 'Fitness is bounded');

    # Generation tracking
    ok($bio->{generation} >= 0, 'Generation is non-negative');
}
