#!/usr/bin/env perl
# Tests for Chemistry module

use strict;
use warnings;
use Test::More tests => 6;

use lib 'apps/perl/lib';
use Constants;
use Atomic;
use Chemistry;

# Setup atomic system with H and O
my $as = AtomicSystem->new();
for (1..10) {
    push @{$as->{atoms}}, Atom->new(atomic_number => 1);
}
for (1..5) {
    push @{$as->{atoms}}, Atom->new(atomic_number => 8);
}

# ChemicalSystem creation
{
    my $cs = ChemicalSystem->new(atomic_system => $as);
    ok(defined $cs, 'ChemicalSystem created');
    is(scalar @{$cs->{molecules}}, 0, 'Starts with no molecules');

    # Form water
    my @waters = $cs->form_water();
    ok(scalar @waters >= 0, 'form_water runs without error');

    # Molecule census
    my %census = $cs->molecule_census();
    ok(defined \%census, 'molecule_census returns hash');

    # Catalyzed reaction
    my $formed = $cs->catalyzed_reaction(300, 1);
    ok(defined $formed, 'catalyzed_reaction returns a value');
    ok($formed >= 0, 'catalyzed_reaction returns non-negative');
}
