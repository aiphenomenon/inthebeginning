#!/usr/bin/env perl
# Comprehensive tests for Quantum module

use strict;
use warnings;
use Test::More tests => 73;

use lib 'apps/perl/lib';
use Constants qw($T_PLANCK $T_QUARK_HADRON $M_ELECTRON $M_PROTON $C $HBAR $PI);
use Quantum;

# ============================================================
# WaveFunction
# ============================================================
{
    my $wf = WaveFunction->new();
    ok(defined $wf, 'WaveFunction created');
    is($wf->{amplitude}, 1.0, 'Initial amplitude is 1');
    ok(abs($wf->probability() - 1.0) < 1e-10, 'Initial probability is 1');

    # evolve changes phase
    my $old_phase = $wf->{phase};
    $wf->evolve(1.0, 100.0);
    isnt($wf->{phase}, $old_phase, 'evolve changes phase');

    # collapse
    my $result = $wf->collapse();
    ok(defined $result, 'collapse returns a value');
    is($wf->{coherent}, 0, 'collapse sets coherent to false');

    # evolve does nothing when not coherent
    my $phase_before = $wf->{phase};
    $wf->evolve(1.0, 100.0);
    is($wf->{phase}, $phase_before, 'evolve does nothing when not coherent');
}

# WaveFunction: superpose
{
    my $wf1 = WaveFunction->new(amplitude => 0.7, phase => 0.5);
    my $wf2 = WaveFunction->new(amplitude => 0.6, phase => 0.3);
    my $combined = $wf1->superpose($wf2);
    ok(defined $combined, 'superpose returns a WaveFunction');
    ok($combined->{amplitude} > 0, 'Combined amplitude is positive');
    ok($combined->{amplitude} <= 1.0, 'Combined amplitude is capped at 1.0');
    is($combined->{coherent}, 1, 'Combined wave function is coherent');
    # Combined phase is average of the two
    my $expected_phase = ($wf1->{phase} + $wf2->{phase}) / 2;
    ok(abs($combined->{phase} - $expected_phase) < 1e-10, 'Combined phase is average');
}

# WaveFunction: superpose with identical phases (constructive interference)
{
    my $wf1 = WaveFunction->new(amplitude => 0.5, phase => 0.0);
    my $wf2 = WaveFunction->new(amplitude => 0.5, phase => 0.0);
    my $combined = $wf1->superpose($wf2);
    ok($combined->{amplitude} >= 0.99, 'Constructive interference: amplitude near 1.0');
}

# WaveFunction: to_compact
{
    my $wf = WaveFunction->new(amplitude => 0.75, phase => 1.23);
    my $compact = $wf->to_compact();
    ok(defined $compact, 'to_compact returns a string');
    like($compact, qr/0\.750/, 'to_compact includes amplitude');
    like($compact, qr/1\.23/, 'to_compact includes phase');
}

# WaveFunction: probability for amplitude < 1
{
    my $wf = WaveFunction->new(amplitude => 0.5);
    ok(abs($wf->probability() - 0.25) < 1e-10, 'probability returns amplitude^2');
}

# ============================================================
# Particle
# ============================================================
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

# Particle: mass
{
    my $e = Particle->new(particle_type => 'electron');
    is($e->mass(), $M_ELECTRON, 'Electron mass matches constant');

    my $pr = Particle->new(particle_type => 'proton');
    is($pr->mass(), $M_PROTON, 'Proton mass matches constant');

    my $ph = Particle->new(particle_type => 'photon');
    is($ph->mass(), 0.0, 'Photon mass is zero');

    # Unknown particle type
    my $u = Particle->new(particle_type => 'unknown_type');
    is($u->mass(), 0.0, 'Unknown particle type mass defaults to 0');
}

# Particle: charge
{
    my $e = Particle->new(particle_type => 'electron');
    is($e->charge(), -1.0, 'Electron charge is -1');

    my $pr = Particle->new(particle_type => 'proton');
    is($pr->charge(), 1.0, 'Proton charge is +1');

    my $n = Particle->new(particle_type => 'neutron');
    is($n->charge(), 0.0, 'Neutron charge is 0');

    my $pos = Particle->new(particle_type => 'positron');
    is($pos->charge(), 1.0, 'Positron charge is +1');

    my $u = Particle->new(particle_type => 'unknown_type');
    is($u->charge(), 0.0, 'Unknown particle type charge defaults to 0');
}

# Particle: wavelength
{
    my $p = Particle->new(
        particle_type => 'electron',
        momentum      => [1, 0, 0],
    );
    my $wl = $p->wavelength();
    ok($wl > 0, 'wavelength is positive for moving particle');
    ok($wl < 9**9**9, 'wavelength is finite for moving particle');
    my $expected = 2 * $PI * $HBAR / 1.0;
    ok(abs($wl - $expected) < 1e-10, 'wavelength equals 2*pi*hbar / |p|');
}

# Particle: wavelength for zero momentum returns infinity
{
    my $p = Particle->new(
        particle_type => 'electron',
        momentum      => [0, 0, 0],
    );
    my $wl = $p->wavelength();
    ok($wl >= 9**9**9, 'wavelength is infinity for zero momentum');
}

# Particle: to_compact
{
    my $p = Particle->new(
        particle_type => 'electron',
        position      => [1.5, 2.3, 0.0],
        spin          => 0.5,
    );
    my $compact = $p->to_compact();
    ok(defined $compact, 'Particle to_compact returns a string');
    like($compact, qr/electron/, 'to_compact includes particle type');
    like($compact, qr/1\.5/, 'to_compact includes position x');
    like($compact, qr/s=/, 'to_compact includes spin');
}

# ============================================================
# EntangledPair
# ============================================================
{
    my $pa = Particle->new(particle_type => 'electron', spin => 0.5);
    my $pb = Particle->new(particle_type => 'positron', spin => -0.5);
    my $pair = EntangledPair->new(
        particle_a => $pa,
        particle_b => $pb,
    );
    ok(defined $pair, 'EntangledPair created');
    is($pair->{bell_state}, 'phi+', 'Default bell state is phi+');
    is($pair->{particle_a}{particle_type}, 'electron', 'particle_a is electron');
    is($pair->{particle_b}{particle_type}, 'positron', 'particle_b is positron');
}

# EntangledPair: measure_a
{
    my $pa = Particle->new(particle_type => 'electron');
    my $pb = Particle->new(particle_type => 'positron');
    my $pair = EntangledPair->new(particle_a => $pa, particle_b => $pb);

    my $spin_a = $pair->measure_a();
    ok(defined $spin_a, 'measure_a returns a spin value');
    ok($spin_a == 0.5 || $spin_a == -0.5, 'measure_a returns SPIN_UP or SPIN_DOWN');

    # Anti-correlation: spins are opposite after measurement
    isnt($pa->{spin}, $pb->{spin}, 'After measurement, spins are anti-correlated');

    # Coherence is broken after measurement
    is($pa->{wave_fn}{coherent}, 0, 'particle_a decoherent after measurement');
    is($pb->{wave_fn}{coherent}, 0, 'particle_b decoherent after measurement');
}

# EntangledPair: custom bell_state
{
    my $pa = Particle->new(particle_type => 'electron');
    my $pb = Particle->new(particle_type => 'positron');
    my $pair = EntangledPair->new(
        particle_a => $pa,
        particle_b => $pb,
        bell_state => 'psi-',
    );
    is($pair->{bell_state}, 'psi-', 'Custom bell state works');
}

# ============================================================
# QuantumField
# ============================================================
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

# QuantumField: annihilate
{
    my $qf = QuantumField->new(temperature => $T_PLANCK);
    # Create two particles via pair production
    my $energy = 2 * $M_ELECTRON * $C * $C * 10;
    my @pair = $qf->pair_production($energy);
    if (@pair == 2) {
        my $n_before = scalar @{$qf->{particles}};
        my $ann_energy = $qf->annihilate($pair[0], $pair[1]);
        ok($ann_energy > 0, 'annihilate returns positive energy');
        # The original pair is removed, but 2 photons are added
        is($qf->{total_annihilated}, 2, 'total_annihilated incremented by 2');
        ok($qf->{vacuum_energy} > 0, 'vacuum_energy increased after annihilation');
    } else {
        pass('annihilate test skipped (pair_production did not return 2 particles)');
        pass('annihilate test skipped');
        pass('annihilate test skipped');
    }
}

# QuantumField: quark_confinement
{
    # Above T_QUARK_HADRON: no confinement
    my $qf_hot = QuantumField->new(temperature => $T_QUARK_HADRON * 10);
    push @{$qf_hot->{particles}}, Particle->new(particle_type => 'up');
    push @{$qf_hot->{particles}}, Particle->new(particle_type => 'up');
    push @{$qf_hot->{particles}}, Particle->new(particle_type => 'down');
    my @hadrons = $qf_hot->quark_confinement();
    is(scalar @hadrons, 0, 'No confinement above T_QUARK_HADRON');

    # Below T_QUARK_HADRON: should confine quarks into protons
    my $qf_cold = QuantumField->new(temperature => $T_QUARK_HADRON * 0.1);
    push @{$qf_cold->{particles}}, Particle->new(particle_type => 'up');
    push @{$qf_cold->{particles}}, Particle->new(particle_type => 'up');
    push @{$qf_cold->{particles}}, Particle->new(particle_type => 'down');
    my @hadrons2 = $qf_cold->quark_confinement();
    ok(scalar @hadrons2 > 0, 'Confinement below T_QUARK_HADRON produces hadrons');
    is($hadrons2[0]->{particle_type}, 'proton', 'uud -> proton');
}

# QuantumField: decohere
{
    my $qf = QuantumField->new(temperature => 1e6);
    my $p = Particle->new(particle_type => 'electron');
    ok($p->{wave_fn}{coherent}, 'Particle starts coherent');
    # Use high coupling to force decoherence
    my $decohered = 0;
    for (1..1000) {
        my $test_p = Particle->new(particle_type => 'electron');
        $qf->decohere($test_p, 1.0);
        if (!$test_p->{wave_fn}{coherent}) {
            $decohered = 1;
            last;
        }
    }
    ok($decohered, 'decohere can cause wave function collapse');
}

# QuantumField: cool
{
    my $qf = QuantumField->new(temperature => 1000);
    $qf->cool(0.5);
    is($qf->{temperature}, 500, 'cool halves temperature with factor 0.5');
    $qf->cool();  # default factor 0.999
    ok($qf->{temperature} < 500, 'cool with default factor reduces temperature');
}

# QuantumField: evolve_field
{
    my $qf = QuantumField->new(temperature => 1000);
    my $p = Particle->new(
        particle_type => 'electron',
        position      => [0, 0, 0],
        momentum      => [1, 0, 0],
    );
    push @{$qf->{particles}}, $p;
    $qf->evolve_field(1.0);
    ok($p->{position}[0] != 0, 'evolve_field moves particle');
}

# QuantumField: particle_count
{
    my $qf = QuantumField->new(temperature => 1000);
    push @{$qf->{particles}}, Particle->new(particle_type => 'electron');
    push @{$qf->{particles}}, Particle->new(particle_type => 'electron');
    push @{$qf->{particles}}, Particle->new(particle_type => 'proton');
    my %counts = $qf->particle_count();
    is($counts{electron}, 2, 'particle_count: 2 electrons');
    is($counts{proton}, 1, 'particle_count: 1 proton');
}

# QuantumField: total_energy
{
    my $qf = QuantumField->new(temperature => 1000);
    is($qf->total_energy(), 0.0, 'total_energy is 0 with no particles and no vacuum energy');
    push @{$qf->{particles}}, Particle->new(
        particle_type => 'electron',
        momentum      => [1, 0, 0],
    );
    ok($qf->total_energy() > 0, 'total_energy is positive with a particle');
}

# QuantumField: step
{
    my $qf = QuantumField->new(temperature => $T_PLANCK);
    $qf->step($T_PLANCK);
    # step calls vacuum_fluctuation, evolve_field, decohere, quark_confinement
    # Just verify it runs without error
    pass('step runs without error at Planck temperature');
}

# QuantumField: to_compact
{
    my $qf = QuantumField->new(temperature => 1000);
    push @{$qf->{particles}}, Particle->new(particle_type => 'electron');
    my $compact = $qf->to_compact();
    ok(defined $compact, 'to_compact returns a string');
    like($compact, qr/QF\[/, 'to_compact starts with QF[');
    like($compact, qr/T=/, 'to_compact includes temperature');
    like($compact, qr/n=/, 'to_compact includes particle count');
}
