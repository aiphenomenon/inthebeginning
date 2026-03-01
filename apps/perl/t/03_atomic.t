#!/usr/bin/env perl
# Tests for Atomic module

use strict;
use warnings;
use Test::More tests => 8;

use lib 'apps/perl/lib';
use Constants qw($T_PLANCK);
use Atomic;

# Atom creation
{
    my $a = Atom->new(atomic_number => 1);
    ok(defined $a, 'Atom created');
    is($a->{atomic_number}, 1, 'Hydrogen Z=1');
    is($a->symbol(), 'H', 'Hydrogen symbol is H');

    my $he = Atom->new(atomic_number => 2);
    is($he->symbol(), 'He', 'Helium symbol is He');
}

# AtomicSystem
{
    my $as = AtomicSystem->new();
    ok(defined $as, 'AtomicSystem created');
    is(scalar @{$as->{atoms}}, 0, 'Starts empty');

    # Nucleosynthesis
    my @atoms = $as->nucleosynthesis(10, 5);
    ok(scalar @atoms > 0, 'Nucleosynthesis produces atoms');

    # Element counts
    my %counts = $as->element_counts();
    ok(defined \%counts, 'element_counts returns hash');
}
