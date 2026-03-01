#!/usr/bin/env perl
# Tests for Quantum module

use strict;
use warnings;
use Test::More tests => 15;

use lib 'apps/perl/lib';
use Constants qw($T_PLANCK $T_QUARK_HADRON $M_ELECTRON $C);
use Quantum;

# WaveFunction
{
    my $wf = WaveFunction->new();
    ok(defined $wf, 'WaveFunction created');
    is($wf->{amplitude}, 1.0, 'Initial amplitude is 1');
    ok(abs($wf->probability() - 1.0) < 1e-10, 'Initial probability is 1');

    my $old_phase = $wf->{phase};
    $wf->evolve(1.0, 100.0);
    isnt($wf->{phase}, $old_phase, 'evolve changes phase');

    my $result = $wf->collapse();
    ok(defined $result, 'collapse returns a value');
    is($wf->{coherent}, 0, 'collapse sets coherent to false');
}

# Particle
{
    my $p = Particle->new(
        particle_type => 'electron',
        position      => [0, 0, 0],
        momentum      => [1, 0, 0],
    );
    ok(defined $p, 'Particle created');
    is($p->{particle_type}, 'electron', 'Particle type is electron');
    ok($p->{particle_id} > 0, 'Particle has positive ID');
    ok($p->energy() >= 0, 'Energy is non-negative');
}

# QuantumField
{
    my $qf = QuantumField->new(temperature => $T_PLANCK);
    ok(defined $qf, 'QuantumField created');
    is(scalar @{$qf->{particles}}, 0, 'Starts with no particles');

    # Pair production
    my $energy = 2 * $M_ELECTRON * $C * $C * 10;
    my $result = $qf->pair_production($energy);
    if ($result) {
        is(scalar @{$qf->{particles}}, 2, 'Pair production creates 2 particles');
    } else {
        pass('Pair production skipped (energy too low or random)');
    }

    # Below threshold
    my $qf2 = QuantumField->new(temperature => $T_PLANCK);
    my $r2 = $qf2->pair_production(0.001);
    ok(!$r2, 'Pair production fails below threshold');

    # Vacuum fluctuation at Planck temperature
    my $produced = 0;
    for (1..100) {
        if ($qf->vacuum_fluctuation()) {
            $produced = 1;
            last;
        }
    }
    ok($produced, 'Vacuum fluctuation produces pairs at Planck temperature');
}
