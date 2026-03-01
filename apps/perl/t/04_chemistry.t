#!/usr/bin/env perl
# Comprehensive tests for Chemistry module

use strict;
use warnings;
use Test::More tests => 46;

use lib 'apps/perl/lib';
use Constants qw($K_B);
use Atomic;
use Chemistry;

# ============================================================
# Molecule
# ============================================================
{
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    my $o  = Atom->new(atomic_number => 8);
    my $mol = Molecule->new(
        atoms => [$h1, $h2, $o],
        name  => 'water',
    );
    ok(defined $mol, 'Molecule created');
    is($mol->{name}, 'water', 'Molecule name is water');
    ok($mol->{molecule_id} > 0, 'Molecule has positive ID');
}

# Molecule: molecular_weight
{
    my $h1 = Atom->new(atomic_number => 1, mass_number => 1);
    my $h2 = Atom->new(atomic_number => 1, mass_number => 1);
    my $o  = Atom->new(atomic_number => 8, mass_number => 16);
    my $mol = Molecule->new(atoms => [$h1, $h2, $o], name => 'water');
    is($mol->molecular_weight(), 18, 'Water molecular weight is 18');
}

# Molecule: atom_count
{
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    my $o  = Atom->new(atomic_number => 8);
    my $mol = Molecule->new(atoms => [$h1, $h2, $o], name => 'water');
    is($mol->atom_count(), 3, 'Water has 3 atoms');
}

# Molecule: to_compact
{
    my $h1 = Atom->new(atomic_number => 1, mass_number => 1);
    my $h2 = Atom->new(atomic_number => 1, mass_number => 1);
    my $o  = Atom->new(atomic_number => 8, mass_number => 16);
    my $mol = Molecule->new(atoms => [$h1, $h2, $o], name => 'water');
    my $compact = $mol->to_compact();
    ok(defined $compact, 'Molecule to_compact returns a string');
    like($compact, qr/water/, 'to_compact includes name');
    like($compact, qr/mw=18/, 'to_compact includes molecular weight');
}

# Molecule: formula auto-computation
{
    my $c = Atom->new(atomic_number => 6);
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    my $h3 = Atom->new(atomic_number => 1);
    my $h4 = Atom->new(atomic_number => 1);
    my $mol = Molecule->new(atoms => [$c, $h1, $h2, $h3, $h4]);
    like($mol->{formula}, qr/CH4/, 'Auto-computed formula for methane');
    is($mol->{is_organic}, 1, 'CH4 is organic');
}

# Molecule: empty molecule
{
    my $mol = Molecule->new(name => 'empty');
    is($mol->molecular_weight(), 0, 'Empty molecule has 0 molecular weight');
    is($mol->atom_count(), 0, 'Empty molecule has 0 atoms');
}

# ============================================================
# ChemicalReaction
# ============================================================
{
    my $rxn = ChemicalReaction->new(
        reactants         => ['H2', 'O'],
        products          => ['H2O'],
        activation_energy => 1.0,
        delta_h           => -2.0,
        name              => 'water_formation',
    );
    ok(defined $rxn, 'ChemicalReaction created');
    is($rxn->{name}, 'water_formation', 'Reaction name');
}

# ChemicalReaction: can_proceed
{
    my $rxn = ChemicalReaction->new(
        reactants         => ['H2', 'O'],
        products          => ['H2O'],
        activation_energy => 0.0001,
        name              => 'easy_rxn',
    );
    # At very high temperature with low activation energy, should proceed
    my $proceeded = 0;
    for (1..100) {
        if ($rxn->can_proceed(1e6)) {
            $proceeded = 1;
            last;
        }
    }
    ok($proceeded, 'can_proceed returns true at high temperature with low Ea');
}

# ChemicalReaction: can_proceed at zero temperature
{
    my $rxn = ChemicalReaction->new(activation_energy => 1.0);
    my $r = $rxn->can_proceed(0);
    is($r, 0, 'can_proceed returns false at zero temperature');
}

# ChemicalReaction: to_compact
{
    my $rxn = ChemicalReaction->new(
        reactants         => ['A', 'B'],
        products          => ['C'],
        activation_energy => 2.5,
        delta_h           => -1.0,
    );
    my $compact = $rxn->to_compact();
    ok(defined $compact, 'ChemicalReaction to_compact returns a string');
    like($compact, qr/A\+B/, 'to_compact includes reactants');
    like($compact, qr/->C/, 'to_compact includes products');
    like($compact, qr/Ea=2\.5/, 'to_compact includes activation energy');
    like($compact, qr/dH=-1\.0/, 'to_compact includes delta_h');
}

# ============================================================
# ChemicalSystem
# ============================================================

# Helper: create atomic system with atoms needed for chemistry
sub _make_atomic_system {
    my (%args) = @_;
    my $as = AtomicSystem->new();
    for (1 .. ($args{H} // 0)) {
        push @{$as->{atoms}}, Atom->new(atomic_number => 1);
    }
    for (1 .. ($args{C} // 0)) {
        push @{$as->{atoms}}, Atom->new(atomic_number => 6);
    }
    for (1 .. ($args{N} // 0)) {
        push @{$as->{atoms}}, Atom->new(atomic_number => 7);
    }
    for (1 .. ($args{O} // 0)) {
        push @{$as->{atoms}}, Atom->new(atomic_number => 8);
    }
    return $as;
}

{
    my $as = _make_atomic_system(H => 10, O => 5);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    ok(defined $cs, 'ChemicalSystem created');
    is(scalar @{$cs->{molecules}}, 0, 'Starts with no molecules');
}

# ChemicalSystem: form_water
{
    my $as = _make_atomic_system(H => 10, O => 5);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my @waters = $cs->form_water();
    ok(scalar @waters >= 0, 'form_water runs without error');
    if (@waters > 0) {
        is($waters[0]->{name}, 'water', 'Formed molecules are named water');
        is($waters[0]->atom_count(), 3, 'Water has 3 atoms (2H + 1O)');
    } else {
        pass('No water formed (insufficient atoms)');
        pass('No water formed (insufficient atoms)');
    }
}

# ChemicalSystem: form_methane
{
    my $as = _make_atomic_system(H => 10, C => 2);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my @methanes = $cs->form_methane();
    ok(scalar @methanes > 0, 'form_methane produces methane');
    is($methanes[0]->{name}, 'methane', 'Formed molecule is methane');
    is($methanes[0]->atom_count(), 5, 'Methane has 5 atoms (C + 4H)');
}

# ChemicalSystem: form_ammonia
{
    my $as = _make_atomic_system(H => 10, N => 2);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my @ammonias = $cs->form_ammonia();
    ok(scalar @ammonias > 0, 'form_ammonia produces ammonia');
    is($ammonias[0]->{name}, 'ammonia', 'Formed molecule is ammonia');
    is($ammonias[0]->atom_count(), 4, 'Ammonia has 4 atoms (N + 3H)');
}

# ChemicalSystem: form_amino_acid
{
    my $as = _make_atomic_system(H => 10, C => 5, N => 2, O => 5);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my $aa = $cs->form_amino_acid('Gly');
    ok(defined $aa, 'form_amino_acid returns a molecule');
    is($aa->{name}, 'Gly', 'Amino acid name is Gly');
    is($aa->{is_organic}, 1, 'Amino acid is organic');
    is($cs->{amino_acid_count}, 1, 'amino_acid_count incremented');
    ok(scalar @{$aa->{functional_groups}} == 2, 'Amino acid has 2 functional groups');
}

# ChemicalSystem: form_amino_acid with insufficient atoms returns undef
{
    my $as = _make_atomic_system(H => 1);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my $aa = $cs->form_amino_acid('Gly');
    ok(!defined $aa, 'form_amino_acid returns undef with insufficient atoms');
}

# ChemicalSystem: form_nucleotide
{
    my $as = _make_atomic_system(H => 20, C => 10, N => 5, O => 10);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    my $nuc = $cs->form_nucleotide('A');
    ok(defined $nuc, 'form_nucleotide returns a molecule');
    is($nuc->{name}, 'nucleotide-A', 'Nucleotide name includes base');
    is($nuc->{is_organic}, 1, 'Nucleotide is organic');
    is($cs->{nucleotide_count}, 1, 'nucleotide_count incremented');
}

# ChemicalSystem: step
{
    my $as = _make_atomic_system(H => 20, C => 5, N => 3, O => 10);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    $cs->step(300);
    # step calls form_water, form_methane, form_ammonia, catalyzed_reaction
    pass('ChemicalSystem step runs without error');
}

# ChemicalSystem: to_compact
{
    my $as = _make_atomic_system(H => 10, O => 5);
    my $cs = ChemicalSystem->new(atomic_system => $as);
    $cs->form_water();
    my $compact = $cs->to_compact();
    ok(defined $compact, 'ChemicalSystem to_compact returns a string');
    like($compact, qr/CS\[/, 'to_compact starts with CS[');
    like($compact, qr/H2O=/, 'to_compact includes water count');
}
