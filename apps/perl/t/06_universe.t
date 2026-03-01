#!/usr/bin/env perl
# Tests for Universe orchestrator

use strict;
use warnings;
use Test::More tests => 8;

use lib 'apps/perl/lib';
use Constants qw($PLANCK_EPOCH $NUCLEOSYNTHESIS_EPOCH $PRESENT_EPOCH);
use Quantum;
use Atomic;
use Chemistry;
use Biology;
use Environment;
use Universe;

# Creation
{
    my $u = Universe->new();
    ok(defined $u, 'Universe created');
    is($u->{current_tick}, 0, 'Starts at tick 0');
}

# run_epoch
{
    my $u = Universe->new(ticks_per_epoch => 10);
    # Initialize subsystems
    $u->{quantum_field}   = QuantumField->new();
    $u->{atomic_system}   = AtomicSystem->new();
    $u->{environment}     = Environment->new();
    $u->{chemical_system} = ChemicalSystem->new(atomic_system => $u->{atomic_system});
    $u->{biosphere}       = Biosphere->new();

    my $result = $u->run_epoch(0);
    ok(ref $result eq 'HASH', 'run_epoch returns hashref');
    ok(exists $result->{epoch}, 'Result has epoch name');
    ok(exists $result->{temperature}, 'Result has temperature');
    ok(exists $result->{stats}, 'Result has stats');
}

# Full run
{
    my $u = Universe->new(ticks_per_epoch => 5);
    my $results = $u->run();
    ok(ref $results eq 'ARRAY', 'run returns arrayref');
    is(scalar @$results, 13, 'Runs all 13 epochs');
}
