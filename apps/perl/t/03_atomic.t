#!/usr/bin/env perl
# Comprehensive tests for Atomic module

use strict;
use warnings;
use Test::More tests => 80;

use lib 'apps/perl/lib';
use Constants qw($T_PLANCK $T_RECOMBINATION $K_B $BOND_ENERGY_COVALENT $BOND_ENERGY_IONIC);
use Quantum;
use Atomic;

# ============================================================
# ElectronShell
# ============================================================
{
    my $shell = ElectronShell->new(n => 1, max_electrons => 2, electrons => 0);
    ok(defined $shell, 'ElectronShell created');
    is($shell->{n}, 1, 'Shell number is 1');
    is($shell->{max_electrons}, 2, 'Max electrons is 2');
    is($shell->{electrons}, 0, 'Starts with 0 electrons');
}

# ElectronShell: full and empty
{
    my $empty_shell = ElectronShell->new(n => 1, max_electrons => 2, electrons => 0);
    ok($empty_shell->empty(), 'Shell with 0 electrons is empty');
    ok(!$empty_shell->full(), 'Shell with 0 electrons is not full');

    my $full_shell = ElectronShell->new(n => 1, max_electrons => 2, electrons => 2);
    ok($full_shell->full(), 'Shell with max electrons is full');
    ok(!$full_shell->empty(), 'Shell with max electrons is not empty');

    my $partial = ElectronShell->new(n => 2, max_electrons => 8, electrons => 4);
    ok(!$partial->full(), 'Partial shell is not full');
    ok(!$partial->empty(), 'Partial shell is not empty');
}

# ElectronShell: add_electron
{
    my $shell = ElectronShell->new(n => 1, max_electrons => 2, electrons => 0);
    my $r1 = $shell->add_electron();
    is($r1, 1, 'add_electron returns 1 on success');
    is($shell->{electrons}, 1, 'Electrons incremented to 1');

    my $r2 = $shell->add_electron();
    is($r2, 1, 'add_electron returns 1 on second add');
    is($shell->{electrons}, 2, 'Electrons incremented to 2 (full)');

    my $r3 = $shell->add_electron();
    is($r3, 0, 'add_electron returns 0 when shell is full');
    is($shell->{electrons}, 2, 'Electrons unchanged when full');
}

# ElectronShell: remove_electron
{
    my $shell = ElectronShell->new(n => 1, max_electrons => 2, electrons => 2);
    my $r1 = $shell->remove_electron();
    is($r1, 1, 'remove_electron returns 1 on success');
    is($shell->{electrons}, 1, 'Electrons decremented to 1');

    my $r2 = $shell->remove_electron();
    is($r2, 1, 'remove_electron returns 1');
    is($shell->{electrons}, 0, 'Electrons decremented to 0');

    my $r3 = $shell->remove_electron();
    is($r3, 0, 'remove_electron returns 0 when empty');
    is($shell->{electrons}, 0, 'Electrons unchanged when empty');
}

# ============================================================
# Atom
# ============================================================
{
    my $a = Atom->new(atomic_number => 1);
    ok(defined $a, 'Atom created');
    is($a->{atomic_number}, 1, 'Hydrogen Z=1');
    is($a->symbol(), 'H', 'Hydrogen symbol is H');

    my $he = Atom->new(atomic_number => 2);
    is($he->symbol(), 'He', 'Helium symbol is He');
}

# Atom: name
{
    my $h = Atom->new(atomic_number => 1);
    is($h->name(), 'Hydrogen', 'Hydrogen name');

    my $c = Atom->new(atomic_number => 6);
    is($c->name(), 'Carbon', 'Carbon name');

    my $fe = Atom->new(atomic_number => 26);
    is($fe->name(), 'Iron', 'Iron name');
}

# Atom: electronegativity
{
    my $h = Atom->new(atomic_number => 1);
    ok(abs($h->electronegativity() - 2.20) < 0.01, 'Hydrogen electronegativity is 2.20');

    my $na = Atom->new(atomic_number => 11);
    ok(abs($na->electronegativity() - 0.93) < 0.01, 'Sodium electronegativity is 0.93');
}

# Atom: charge (neutral atom has charge 0)
{
    my $h = Atom->new(atomic_number => 1);
    is($h->charge(), 0, 'Neutral hydrogen has charge 0');
}

# Atom: charge after ionize
{
    my $h = Atom->new(atomic_number => 1);
    $h->ionize();
    is($h->charge(), 1, 'Ionized hydrogen has charge +1');
}

# Atom: valence_electrons
{
    my $h = Atom->new(atomic_number => 1);
    is($h->valence_electrons(), 1, 'Hydrogen has 1 valence electron');

    my $c = Atom->new(atomic_number => 6);
    is($c->valence_electrons(), 4, 'Carbon has 4 valence electrons');

    my $he = Atom->new(atomic_number => 2);
    is($he->valence_electrons(), 2, 'Helium has 2 valence electrons (full shell)');
}

# Atom: needs_electrons
{
    my $h = Atom->new(atomic_number => 1);
    is($h->needs_electrons(), 1, 'Hydrogen needs 1 electron to fill shell');

    my $c = Atom->new(atomic_number => 6);
    is($c->needs_electrons(), 4, 'Carbon needs 4 electrons to fill shell');
}

# Atom: is_noble_gas
{
    my $he = Atom->new(atomic_number => 2);
    ok($he->is_noble_gas(), 'Helium is a noble gas');

    my $ne = Atom->new(atomic_number => 10);
    ok($ne->is_noble_gas(), 'Neon is a noble gas');

    my $h = Atom->new(atomic_number => 1);
    ok(!$h->is_noble_gas(), 'Hydrogen is not a noble gas');
}

# Atom: is_ion (neutral atom is not an ion, ionized atom is)
{
    my $h = Atom->new(atomic_number => 1);
    ok(!$h->is_ion(), 'Neutral atom is not an ion');

    $h->ionize();
    ok($h->is_ion(), 'Atom is an ion after ionize');
}

# Atom: ionize
{
    my $h = Atom->new(atomic_number => 1);
    my $r = $h->ionize();
    is($r, 1, 'ionize returns 1 on success');
    is($h->{electron_count}, 0, 'Electron removed by ionize');

    # Ionize again should fail (no electrons left)
    my $r2 = $h->ionize();
    is($r2, 0, 'ionize returns 0 when no electrons remain');
}

# Atom: capture_electron
{
    my $h = Atom->new(atomic_number => 1);
    $h->ionize();  # Remove electron first
    ok($h->is_ion(), 'Starts as ion after ionize');
    $h->capture_electron();
    is($h->{electron_count}, 1, 'Electron count increased after capture');
    ok(!$h->is_ion(), 'No longer an ion after capturing electron');
}

# Atom: can_bond_with
{
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    ok($h1->can_bond_with($h2), 'Two hydrogens can bond');

    # Noble gas cannot bond
    my $he = Atom->new(atomic_number => 2);
    ok(!$h1->can_bond_with($he), 'Hydrogen cannot bond with noble gas');

    # Atom with 4 bonds cannot bond further
    my $c = Atom->new(atomic_number => 6);
    $c->{bonds} = [1, 2, 3, 4];
    ok(!$c->can_bond_with($h1), 'Atom with 4 bonds cannot form more bonds');
}

# Atom: bond_type
{
    my $na = Atom->new(atomic_number => 11);  # EN=0.93
    my $cl = Atom->new(atomic_number => 17);  # EN=3.16
    is($na->bond_type($cl), 'ionic', 'Na-Cl bond is ionic (diff > 1.7)');

    my $h = Atom->new(atomic_number => 1);    # EN=2.20
    my $o = Atom->new(atomic_number => 8);    # EN=3.44
    is($h->bond_type($o), 'polar_covalent', 'H-O bond is polar covalent');

    my $h2 = Atom->new(atomic_number => 1);
    is($h->bond_type($h2), 'covalent', 'H-H bond is covalent');
}

# Atom: bond_energy
{
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    is($h1->bond_energy($h2), $BOND_ENERGY_COVALENT, 'H-H bond energy is covalent');

    my $na = Atom->new(atomic_number => 11);
    my $cl = Atom->new(atomic_number => 17);
    is($na->bond_energy($cl), $BOND_ENERGY_IONIC, 'Na-Cl bond energy is ionic');
}

# Atom: distance_to
{
    my $a1 = Atom->new(atomic_number => 1, position => [0, 0, 0]);
    my $a2 = Atom->new(atomic_number => 1, position => [3, 4, 0]);
    my $dist = $a1->distance_to($a2);
    ok(abs($dist - 5.0) < 1e-10, 'distance_to computes correctly (3-4-5 triangle)');
}

# Atom: to_compact
{
    my $h = Atom->new(atomic_number => 1);
    my $compact = $h->to_compact();
    ok(defined $compact, 'to_compact returns a string');
    like($compact, qr/H/, 'to_compact includes symbol');
    like($compact, qr/b\d/, 'to_compact includes bond count');
}

# ============================================================
# AtomicSystem
# ============================================================
{
    my $as = AtomicSystem->new();
    ok(defined $as, 'AtomicSystem created');
    is(scalar @{$as->{atoms}}, 0, 'Starts empty');

    my @atoms = $as->nucleosynthesis(10, 5);
    ok(scalar @atoms > 0, 'Nucleosynthesis produces atoms');

    my %counts = $as->element_counts();
    ok(defined \%counts, 'element_counts returns hash');
}

# AtomicSystem: recombination
{
    my $as = AtomicSystem->new(temperature => $T_RECOMBINATION * 0.5);
    my $field = QuantumField->new(temperature => $T_RECOMBINATION * 0.5);

    # Add protons and electrons to the field
    push @{$field->{particles}}, Particle->new(particle_type => 'proton');
    push @{$field->{particles}}, Particle->new(particle_type => 'electron');

    my @new_atoms = $as->recombination($field);
    ok(scalar @new_atoms > 0, 'Recombination produces atoms');
    is($new_atoms[0]->{atomic_number}, 1, 'Recombination produces hydrogen');
}

# AtomicSystem: recombination above T_RECOMBINATION returns nothing
{
    my $as = AtomicSystem->new(temperature => $T_RECOMBINATION * 2);
    my $field = QuantumField->new(temperature => $T_RECOMBINATION * 2);
    push @{$field->{particles}}, Particle->new(particle_type => 'proton');
    push @{$field->{particles}}, Particle->new(particle_type => 'electron');

    my @new_atoms = $as->recombination($field);
    is(scalar @new_atoms, 0, 'No recombination above T_RECOMBINATION');
}

# AtomicSystem: stellar_nucleosynthesis
{
    my $as = AtomicSystem->new();
    # Add helium atoms
    for (1..30) {
        push @{$as->{atoms}}, Atom->new(atomic_number => 2, mass_number => 4);
    }
    # Run stellar nucleosynthesis at high temperature many times
    my $total_new = 0;
    for (1..500) {
        my @new = $as->stellar_nucleosynthesis(1e4);
        $total_new += scalar @new;
    }
    ok($total_new > 0, 'stellar_nucleosynthesis produces heavier elements');
}

# AtomicSystem: stellar_nucleosynthesis below 1e3 returns nothing
{
    my $as = AtomicSystem->new();
    push @{$as->{atoms}}, Atom->new(atomic_number => 2, mass_number => 4) for 1..10;
    my @new = $as->stellar_nucleosynthesis(500);
    is(scalar @new, 0, 'No stellar nucleosynthesis below 1e3');
}

# AtomicSystem: attempt_bond and break_bond
{
    # Use zero temperature so prob = 1.0 when dist < bond_dist
    my $as = AtomicSystem->new(temperature => 0);
    my $h1 = Atom->new(atomic_number => 1, position => [0, 0, 0]);
    my $h2 = Atom->new(atomic_number => 1, position => [0.5, 0, 0]);
    push @{$as->{atoms}}, $h1, $h2;

    my $bonded = $as->attempt_bond($h1, $h2);
    is($bonded, 1, 'attempt_bond succeeds at T=0 for close atoms');
    is($as->{bonds_formed}, 1, 'bonds_formed incremented');
}

# AtomicSystem: attempt_bond fails for far-apart atoms
{
    my $as = AtomicSystem->new(temperature => 300);
    my $h1 = Atom->new(atomic_number => 1, position => [0, 0, 0]);
    my $h2 = Atom->new(atomic_number => 1, position => [100, 100, 100]);
    my $r = $as->attempt_bond($h1, $h2);
    is($r, 0, 'attempt_bond fails for atoms far apart (> 3*bond_dist)');
}

# AtomicSystem: break_bond fails for unbonded atoms
{
    my $as = AtomicSystem->new(temperature => 1e8);
    my $h1 = Atom->new(atomic_number => 1);
    my $h2 = Atom->new(atomic_number => 1);
    my $r = $as->break_bond($h1, $h2);
    is($r, 0, 'break_bond returns 0 for unbonded atoms');
}

# AtomicSystem: step
{
    my $as = AtomicSystem->new(temperature => 300);
    push @{$as->{atoms}}, Atom->new(atomic_number => 1, position => [0, 0, 0]);
    push @{$as->{atoms}}, Atom->new(atomic_number => 1, position => [0.1, 0, 0]);
    $as->step(300);
    pass('AtomicSystem step runs without error');
}

# AtomicSystem: cool
{
    my $as = AtomicSystem->new(temperature => 1000);
    $as->cool(0.5);
    is($as->{temperature}, 500, 'AtomicSystem cool halves temperature');
    $as->cool();  # default 0.999
    ok($as->{temperature} < 500, 'AtomicSystem cool with default factor');
}

# AtomicSystem: to_compact
{
    my $as = AtomicSystem->new();
    push @{$as->{atoms}}, Atom->new(atomic_number => 1);
    push @{$as->{atoms}}, Atom->new(atomic_number => 2);
    my $compact = $as->to_compact();
    ok(defined $compact, 'AtomicSystem to_compact returns a string');
    like($compact, qr/AS\[/, 'to_compact starts with AS[');
    like($compact, qr/n=2/, 'to_compact includes atom count');
}
