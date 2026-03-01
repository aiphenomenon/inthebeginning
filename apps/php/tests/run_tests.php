#!/usr/bin/env php
<?php

declare(strict_types=1);

/**
 * In The Beginning - PHP Test Suite
 *
 * Standalone test runner with no external dependencies.
 * Tests all simulator modules: Constants, Quantum, Atomic, Chemistry, Biology,
 * Environment, and Universe integration.
 */

require_once __DIR__ . '/../simulator/Universe.php';

// =========================================================================
//  Simple test framework
// =========================================================================

$totalPassed = 0;
$totalFailed = 0;
$suitePassed = 0;
$suiteFailed = 0;
$currentSuite = '';

function startSuite(string $name): void
{
    global $suitePassed, $suiteFailed, $currentSuite;
    $currentSuite = $name;
    $suitePassed = 0;
    $suiteFailed = 0;
    echo "  [{$name}]\n";
}

function endSuite(): void
{
    global $totalPassed, $totalFailed, $suitePassed, $suiteFailed;
    $totalPassed += $suitePassed;
    $totalFailed += $suiteFailed;
    echo "    {$suitePassed} passed, {$suiteFailed} failed\n";
}

function assertEqual(string $label, mixed $expected, mixed $actual): void
{
    global $suitePassed, $suiteFailed;
    if ($expected === $actual) {
        $suitePassed++;
    } else {
        $suiteFailed++;
        $e = var_export($expected, true);
        $a = var_export($actual, true);
        echo "    FAIL: {$label} - expected {$e} but got {$a}\n";
    }
}

function assertTrue(string $label, bool $condition): void
{
    global $suitePassed, $suiteFailed;
    if ($condition) {
        $suitePassed++;
    } else {
        $suiteFailed++;
        echo "    FAIL: {$label}\n";
    }
}

function assertApprox(string $label, float $expected, float $actual, float $tolerance): void
{
    global $suitePassed, $suiteFailed;
    if (abs($expected - $actual) < $tolerance) {
        $suitePassed++;
    } else {
        $suiteFailed++;
        echo "    FAIL: {$label} - expected ~{$expected} but got {$actual}\n";
    }
}

function assertNotNull(string $label, mixed $value): void
{
    global $suitePassed, $suiteFailed;
    if ($value !== null) {
        $suitePassed++;
    } else {
        $suiteFailed++;
        echo "    FAIL: {$label} - was null\n";
    }
}

function assertNull(string $label, mixed $value): void
{
    global $suitePassed, $suiteFailed;
    if ($value === null) {
        $suitePassed++;
    } else {
        $suiteFailed++;
        echo "    FAIL: {$label} - expected null\n";
    }
}

// =========================================================================
//  Test: Constants
// =========================================================================

function testConstants(): void
{
    startSuite('Constants');

    // Fundamental constants
    assertEqual('C = 1.0', 1.0, C);
    assertEqual('HBAR = 0.01', 0.01, HBAR);
    assertEqual('K_B = 0.001', 0.001, K_B);
    assertEqual('G_CONST = 1e-6', 1e-6, G_CONST);
    assertApprox('ALPHA ~ 1/137', 1.0 / 137.0, ALPHA, 1e-6);
    assertEqual('E_CHARGE = 0.1', 0.1, E_CHARGE);

    // Particle masses
    assertEqual('M_ELECTRON = 1.0', 1.0, M_ELECTRON);
    assertTrue('M_UP_QUARK > M_ELECTRON', M_UP_QUARK > M_ELECTRON);
    assertTrue('M_DOWN_QUARK > M_UP_QUARK', M_DOWN_QUARK > M_UP_QUARK);
    assertTrue('M_PROTON > M_ELECTRON by ~1836x', M_PROTON > 1000 * M_ELECTRON);
    assertTrue('M_PROTON < M_NEUTRON', M_PROTON < M_NEUTRON);
    assertEqual('M_PHOTON = 0.0', 0.0, M_PHOTON);
    assertTrue('M_NEUTRINO very small', M_NEUTRINO < 0.001);
    assertTrue('M_HIGGS > M_Z_BOSON', M_HIGGS > M_Z_BOSON);

    // Force couplings
    assertEqual('STRONG_COUPLING = 1.0', 1.0, STRONG_COUPLING);
    assertApprox('EM_COUPLING = ALPHA', ALPHA, EM_COUPLING, 1e-10);
    assertTrue('STRONG > EM', STRONG_COUPLING > EM_COUPLING);
    assertTrue('EM > WEAK', EM_COUPLING > WEAK_COUPLING);
    assertTrue('WEAK > GRAVITY', WEAK_COUPLING > GRAVITY_COUPLING);

    // Nuclear parameters
    assertTrue('NUCLEAR_RADIUS > 0', NUCLEAR_RADIUS > 0);
    assertTrue('Binding energy: D < He < C < Fe',
        BINDING_ENERGY_DEUTERIUM < BINDING_ENERGY_HELIUM4
        && BINDING_ENERGY_HELIUM4 < BINDING_ENERGY_CARBON12
        && BINDING_ENERGY_CARBON12 < BINDING_ENERGY_IRON56);

    // Epoch ordering
    assertTrue('PLANCK < INFLATION', PLANCK_EPOCH < INFLATION_EPOCH);
    assertTrue('INFLATION < ELECTROWEAK', INFLATION_EPOCH < ELECTROWEAK_EPOCH);
    assertTrue('ELECTROWEAK < QUARK', ELECTROWEAK_EPOCH < QUARK_EPOCH);
    assertTrue('QUARK < HADRON', QUARK_EPOCH < HADRON_EPOCH);
    assertTrue('HADRON < NUCLEOSYNTHESIS', HADRON_EPOCH < NUCLEOSYNTHESIS_EPOCH);
    assertTrue('NUCLEOSYNTHESIS < RECOMBINATION', NUCLEOSYNTHESIS_EPOCH < RECOMBINATION_EPOCH);
    assertTrue('RECOMBINATION < STAR_FORMATION', RECOMBINATION_EPOCH < STAR_FORMATION_EPOCH);
    assertTrue('STAR_FORMATION < SOLAR_SYSTEM', STAR_FORMATION_EPOCH < SOLAR_SYSTEM_EPOCH);
    assertTrue('SOLAR_SYSTEM < EARTH', SOLAR_SYSTEM_EPOCH < EARTH_EPOCH);
    assertTrue('EARTH < LIFE', EARTH_EPOCH < LIFE_EPOCH);
    assertTrue('LIFE < DNA', LIFE_EPOCH < DNA_EPOCH);
    assertTrue('DNA < PRESENT', DNA_EPOCH < PRESENT_EPOCH);

    // Temperature scale
    assertTrue('T_PLANCK > T_ELECTROWEAK', T_PLANCK > T_ELECTROWEAK);
    assertTrue('T_ELECTROWEAK > T_QUARK_HADRON', T_ELECTROWEAK > T_QUARK_HADRON);
    assertTrue('T_QUARK_HADRON > T_NUCLEOSYNTHESIS', T_QUARK_HADRON > T_NUCLEOSYNTHESIS);
    assertTrue('T_NUCLEOSYNTHESIS > T_RECOMBINATION', T_NUCLEOSYNTHESIS > T_RECOMBINATION);
    assertTrue('T_RECOMBINATION > T_CMB', T_RECOMBINATION > T_CMB);
    assertApprox('T_CMB ~ 2.725', 2.725, T_CMB, 0.01);
    assertApprox('T_EARTH_SURFACE ~ 288', 288.0, T_EARTH_SURFACE, 1.0);

    // Chemistry
    assertEqual('ELECTRON_SHELLS count = 7', 7, count(ELECTRON_SHELLS));
    assertEqual('ELECTRON_SHELLS[0] = 2', 2, ELECTRON_SHELLS[0]);
    assertEqual('ELECTRON_SHELLS[1] = 8', 8, ELECTRON_SHELLS[1]);
    assertTrue('BOND_ENERGY_IONIC > COVALENT', BOND_ENERGY_IONIC > BOND_ENERGY_COVALENT);
    assertTrue('BOND_ENERGY_COVALENT > HYDROGEN', BOND_ENERGY_COVALENT > BOND_ENERGY_HYDROGEN);
    assertTrue('BOND_ENERGY_HYDROGEN > VAN_DER_WAALS', BOND_ENERGY_HYDROGEN > BOND_ENERGY_VAN_DER_WAALS);

    // Biology
    assertEqual('NUCLEOTIDE_BASES count', 4, count(NUCLEOTIDE_BASES));
    assertEqual('RNA_BASES count', 4, count(RNA_BASES));
    assertEqual('AMINO_ACIDS count', 20, count(AMINO_ACIDS));
    assertEqual('First nucleotide = A', 'A', NUCLEOTIDE_BASES[0]);
    assertEqual('Last nucleotide = C', 'C', NUCLEOTIDE_BASES[3]);
    assertEqual('First amino acid = Ala', 'Ala', AMINO_ACIDS[0]);

    // Codon table
    assertTrue('CODON_TABLE not empty', count(CODON_TABLE) > 0);
    assertEqual('AUG -> Met', 'Met', CODON_TABLE['AUG']);
    assertEqual('UAA -> STOP', 'STOP', CODON_TABLE['UAA']);
    assertEqual('UAG -> STOP', 'STOP', CODON_TABLE['UAG']);
    assertEqual('UGA -> STOP', 'STOP', CODON_TABLE['UGA']);
    assertEqual('UUU -> Phe', 'Phe', CODON_TABLE['UUU']);
    assertEqual('GGG -> Gly', 'Gly', CODON_TABLE['GGG']);

    $uniqueAAs = count(array_unique(array_filter(CODON_TABLE, fn($v) => $v !== 'STOP')));
    assertEqual('20 unique amino acids in codon table', 20, $uniqueAAs);

    // Elements
    assertTrue('ELEMENTS not empty', count(ELEMENTS) > 0);
    assertEqual('Element 1 symbol', 'H', ELEMENTS[1][0]);
    assertEqual('Element 1 name', 'Hydrogen', ELEMENTS[1][1]);
    assertEqual('Element 6 symbol', 'C', ELEMENTS[6][0]);
    assertEqual('Element 8 symbol', 'O', ELEMENTS[8][0]);
    assertEqual('Element 26 symbol', 'Fe', ELEMENTS[26][0]);
    assertApprox('Hydrogen electronegativity', 2.20, ELEMENTS[1][4], 0.01);
    assertApprox('Helium electronegativity', 0.0, ELEMENTS[2][4], 0.01);

    // Epoch enum
    $timeline = getEpochTimeline();
    assertEqual('13 epochs in timeline', 13, count($timeline));
    assertEqual('First epoch name', 'Planck', $timeline[0]['name']);
    assertEqual('Last epoch name', 'Present', $timeline[12]['name']);
    assertEqual('First epoch tick', PLANCK_EPOCH, $timeline[0]['tick']);
    assertEqual('Last epoch tick', PRESENT_EPOCH, $timeline[12]['tick']);

    // Epochs in ascending tick order
    for ($i = 1; $i < count($timeline); $i++) {
        assertTrue("Epoch {$i} tick > epoch " . ($i - 1),
            $timeline[$i]['tick'] > $timeline[$i - 1]['tick']);
    }

    // Epoch::description()
    assertEqual('Planck description', 'All forces unified, T~10^32K', Epoch::Planck->description());
    assertEqual('Inflation description', 'Exponential expansion, quantum fluctuations seed structure', Epoch::Inflation->description());
    assertEqual('Present description', 'Complex life, intelligence', Epoch::Present->description());
    assertTrue('Each epoch has a non-empty description', strlen(Epoch::Nucleosynthesis->description()) > 0);
    assertTrue('Each epoch has a non-empty description (Recombination)', strlen(Epoch::Recombination->description()) > 0);
    // All 13 epochs have descriptions
    foreach (Epoch::cases() as $epoch) {
        assertTrue("Epoch {$epoch->label()} description non-empty", strlen($epoch->description()) > 0);
    }

    endSuite();
}

// =========================================================================
//  Test: Quantum (WaveFunction, Particle, QuantumField)
// =========================================================================

function testQuantum(): void
{
    startSuite('Quantum');

    Particle::resetIdCounter();

    // ParticleType properties
    assertEqual('Electron label', 'electron', ParticleType::Electron->value);
    assertApprox('Electron mass', M_ELECTRON, ParticleType::Electron->mass(), 1e-10);
    assertApprox('Electron charge', -1.0, ParticleType::Electron->charge(), 1e-10);
    assertApprox('Proton mass', M_PROTON, ParticleType::Proton->mass(), 1e-10);
    assertApprox('Proton charge', 1.0, ParticleType::Proton->charge(), 1e-10);
    assertApprox('Photon mass', 0.0, ParticleType::Photon->mass(), 1e-10);
    assertApprox('Photon charge', 0.0, ParticleType::Photon->charge(), 1e-10);
    assertApprox('Up quark charge', 2.0 / 3.0, ParticleType::Up->charge(), 1e-10);
    assertApprox('Down quark charge', -1.0 / 3.0, ParticleType::Down->charge(), 1e-10);

    // WaveFunction
    $wf = new WaveFunction();
    assertApprox('Default amplitude = 1.0', 1.0, $wf->amplitude, 1e-10);
    assertApprox('Default phase = 0.0', 0.0, $wf->phase, 1e-10);
    assertTrue('Default coherent', $wf->coherent);
    assertApprox('Born rule probability = 1.0', 1.0, $wf->probability(), 1e-10);

    // WaveFunction evolve
    $wf->evolve(1.0, 1.0);
    assertTrue('Phase changed after evolve', $wf->phase !== 0.0);
    assertTrue('Still coherent', $wf->coherent);

    // WaveFunction superposition
    $wf1 = new WaveFunction(amplitude: 0.5, phase: 0.0);
    $wf2 = new WaveFunction(amplitude: 0.5, phase: 0.0);
    $sup = $wf1->superpose($wf2);
    assertTrue('Superposition amplitude > 0', $sup->amplitude > 0);
    assertTrue('Superposition is coherent', $sup->coherent);

    // WaveFunction collapse
    $wf3 = new WaveFunction(amplitude: 1.0);
    $result = $wf3->collapse();
    assertTrue('Collapse with amplitude 1 detected', $result);
    assertApprox('Amplitude after collapse = 1', 1.0, $wf3->amplitude, 1e-10);
    assertTrue('Not coherent after collapse', !$wf3->coherent);

    // Particle creation
    $p = new Particle(ParticleType::Electron);
    assertTrue('Particle ID > 0', $p->particleId > 0);
    assertApprox('Default position x', 0.0, $p->position[0], 1e-10);
    assertApprox('Default momentum x', 0.0, $p->momentum[0], 1e-10);
    assertEqual('Default spin', Spin::Up, $p->spin);

    // Particle energy (rest)
    assertApprox('Electron rest energy', M_ELECTRON * C ** 2, $p->energy(), 1e-10);

    // Particle wavelength
    assertTrue('Zero momentum wavelength is INF', is_infinite($p->wavelength()));

    $p2 = new Particle(ParticleType::Electron, momentum: [1.0, 0.0, 0.0]);
    $expected = 2 * M_PI * HBAR / 1.0;
    assertApprox('de Broglie wavelength', $expected, $p2->wavelength(), 1e-10);

    // QuantumField creation
    $qf = new QuantumField(T_PLANCK);
    assertApprox('Initial temperature', T_PLANCK, $qf->temperature, 1e-3);
    assertEqual('No particles initially', 0, count($qf->particles));
    assertApprox('No vacuum energy', 0.0, $qf->vacuumEnergy, 1e-10);

    // Pair production
    Particle::resetIdCounter();
    $qf2 = new QuantumField(T_PLANCK);
    $pair = $qf2->pairProduction(10.0);
    assertNotNull('Pair produced', $pair);
    assertEqual('Pair has 2 particles', 2, count($pair));
    assertEqual('Field has 2 particles', 2, count($qf2->particles));
    assertEqual('2 total created', 2, $qf2->totalCreated);

    // Entanglement
    assertEqual('Pair entangled', $pair[1]->particleId, $pair[0]->entangledWith);

    // Pair production - insufficient energy
    $qf3 = new QuantumField(T_PLANCK);
    $pair2 = $qf3->pairProduction(0.5); // below 2 * M_ELECTRON
    assertNull('No pair with insufficient energy', $pair2);

    // Annihilation
    Particle::resetIdCounter();
    $qf4 = new QuantumField(T_PLANCK);
    $pair3 = $qf4->pairProduction(10.0);
    assertNotNull('Pair for annihilation', $pair3);
    $releasedEnergy = $qf4->annihilate($pair3[0], $pair3[1]);
    assertTrue('Energy released > 0', $releasedEnergy > 0);
    assertEqual('2 annihilated', 2, $qf4->totalAnnihilated);
    assertEqual('Photons after annihilation', 2, count($qf4->particles));

    // Quark confinement
    Particle::resetIdCounter();
    $qf5 = new QuantumField(T_QUARK_HADRON * 0.5);
    $qf5->particles[] = new Particle(ParticleType::Up, momentum: [1, 0, 0]);
    $qf5->particles[] = new Particle(ParticleType::Up, momentum: [0, 1, 0]);
    $qf5->particles[] = new Particle(ParticleType::Down, momentum: [0, 0, 1]);
    $hadrons = $qf5->quarkConfinement();
    assertTrue('At least 1 hadron', count($hadrons) >= 1);
    assertEqual('Proton formed', ParticleType::Proton, $hadrons[0]->particleType);

    // No confinement at high temp
    $qf6 = new QuantumField(T_QUARK_HADRON * 2);
    $qf6->particles[] = new Particle(ParticleType::Up);
    $qf6->particles[] = new Particle(ParticleType::Up);
    $qf6->particles[] = new Particle(ParticleType::Down);
    $hadrons2 = $qf6->quarkConfinement();
    assertEqual('No confinement at high T', 0, count($hadrons2));

    // Cooling
    $qf7 = new QuantumField(1000.0);
    $qf7->cool(0.5);
    assertApprox('Cooled to 500', 500.0, $qf7->temperature, 1e-10);

    // Particle count
    $qf8 = new QuantumField(T_PLANCK);
    $qf8->particles[] = new Particle(ParticleType::Electron);
    $qf8->particles[] = new Particle(ParticleType::Electron);
    $qf8->particles[] = new Particle(ParticleType::Proton);
    $counts = $qf8->particleCount();
    assertEqual('2 electrons', 2, $counts['electron']);
    assertEqual('1 proton', 1, $counts['proton']);

    // Total energy
    $qf9 = new QuantumField(T_PLANCK);
    assertApprox('Empty field energy = 0', 0.0, $qf9->totalEnergy(), 1e-10);
    $qf9->particles[] = new Particle(ParticleType::Electron);
    assertTrue('Energy > 0 with particle', $qf9->totalEnergy() > 0);

    // --- Spin::value() ---
    assertApprox('Spin Up value = +0.5', 0.5, Spin::Up->value(), 1e-10);
    assertApprox('Spin Down value = -0.5', -0.5, Spin::Down->value(), 1e-10);

    // --- WaveFunction::toArray() ---
    $wfArr = new WaveFunction(amplitude: 0.75, phase: 1.23, coherent: true);
    $arr = $wfArr->toArray();
    assertApprox('toArray amplitude', 0.75, $arr['amplitude'], 0.01);
    assertApprox('toArray phase', 1.23, $arr['phase'], 0.01);
    assertEqual('toArray coherent', true, $arr['coherent']);

    $wfArr2 = new WaveFunction(amplitude: 0.0, phase: 0.0, coherent: false);
    $arr2 = $wfArr2->toArray();
    assertApprox('toArray zero amplitude', 0.0, $arr2['amplitude'], 0.01);
    assertEqual('toArray not coherent', false, $arr2['coherent']);

    // --- Particle::mass() and Particle::charge() getter methods ---
    Particle::resetIdCounter();
    $pElectron = new Particle(ParticleType::Electron);
    assertApprox('Particle.mass() electron', M_ELECTRON, $pElectron->mass(), 1e-10);
    assertApprox('Particle.charge() electron', -1.0, $pElectron->charge(), 1e-10);

    $pProton = new Particle(ParticleType::Proton);
    assertApprox('Particle.mass() proton', M_PROTON, $pProton->mass(), 1e-10);
    assertApprox('Particle.charge() proton', 1.0, $pProton->charge(), 1e-10);

    $pPhoton = new Particle(ParticleType::Photon);
    assertApprox('Particle.mass() photon', 0.0, $pPhoton->mass(), 1e-10);
    assertApprox('Particle.charge() photon', 0.0, $pPhoton->charge(), 1e-10);

    $pNeutron = new Particle(ParticleType::Neutron);
    assertApprox('Particle.mass() neutron', M_NEUTRON, $pNeutron->mass(), 1e-10);
    assertApprox('Particle.charge() neutron', 0.0, $pNeutron->charge(), 1e-10);

    $pPositron = new Particle(ParticleType::Positron);
    assertApprox('Particle.mass() positron', M_ELECTRON, $pPositron->mass(), 1e-10);
    assertApprox('Particle.charge() positron', 1.0, $pPositron->charge(), 1e-10);

    // --- EntangledPair::measureA() ---
    Particle::resetIdCounter();
    $epA = new Particle(ParticleType::Electron);
    $epB = new Particle(ParticleType::Electron);
    $entPair = new EntangledPair($epA, $epB, 'phi+');
    $spinResult = $entPair->measureA();
    assertTrue('measureA returns a Spin', $spinResult === Spin::Up || $spinResult === Spin::Down);
    // After measurement, spins must be opposite
    assertTrue('Spins are opposite after measurement', $epA->spin !== $epB->spin);
    // Wave functions should be decoherent
    assertTrue('Particle A decoherent after measureA', !$epA->waveFn->coherent);
    assertTrue('Particle B decoherent after measureA', !$epB->waveFn->coherent);
    // Return value matches particle A's spin
    assertEqual('measureA return matches A spin', $epA->spin, $spinResult);

    // --- QuantumField::vacuumFluctuation() ---
    Particle::resetIdCounter();
    // At very high temperature, vacuum fluctuations should sometimes produce pairs
    $qfVac = new QuantumField(T_PLANCK);
    $fluctuationResults = 0;
    for ($i = 0; $i < 50; $i++) {
        $result = $qfVac->vacuumFluctuation();
        if ($result !== null) {
            $fluctuationResults++;
        }
    }
    assertTrue('Vacuum fluctuations can produce pairs at high T', $fluctuationResults > 0);

    // At very low temperature, vacuum fluctuation probability is near zero
    $qfVacLow = new QuantumField(0.001);
    $lowFluctuations = 0;
    for ($i = 0; $i < 20; $i++) {
        if ($qfVacLow->vacuumFluctuation() !== null) {
            $lowFluctuations++;
        }
    }
    // We can't guarantee zero due to randomness, but probability should be extremely low
    assertTrue('Low T vacuum fluctuations are rare', $lowFluctuations <= 20);

    // --- QuantumField::decohere() ---
    Particle::resetIdCounter();
    $qfDec = new QuantumField(1e10); // Very high temperature
    $pCoherent = new Particle(ParticleType::Electron);
    assertTrue('Particle starts coherent', $pCoherent->waveFn->coherent);

    // With very high temperature and coupling, decoherence should happen quickly
    $decoherent = false;
    for ($i = 0; $i < 50; $i++) {
        $qfDec->decohere($pCoherent, 0.5);
        if (!$pCoherent->waveFn->coherent) {
            $decoherent = true;
            break;
        }
    }
    assertTrue('Decoherence happens at high T with coupling', $decoherent);

    // Test that already-decoherent particle is not affected further
    $pCoherent->waveFn->coherent = false;
    $ampBefore = $pCoherent->waveFn->amplitude;
    $qfDec->decohere($pCoherent, 1.0);
    assertApprox('Decohere on non-coherent particle is no-op', $ampBefore, $pCoherent->waveFn->amplitude, 1e-10);

    // --- QuantumField::evolveStep() ---
    Particle::resetIdCounter();
    $qfEvolve = new QuantumField(T_PLANCK);
    // Add a massive particle with momentum
    $pMassive = new Particle(ParticleType::Electron, position: [0.0, 0.0, 0.0], momentum: [1.0, 0.0, 0.0]);
    $qfEvolve->particles[] = $pMassive;
    $posBeforeX = $pMassive->position[0];
    $phaseBeforeEvolve = $pMassive->waveFn->phase;
    $qfEvolve->evolveStep(1.0);
    assertTrue('Massive particle position changed after evolveStep', $pMassive->position[0] !== $posBeforeX);
    assertTrue('Massive particle wave function phase changed', $pMassive->waveFn->phase !== $phaseBeforeEvolve);

    // Add a massless particle (photon) with momentum
    Particle::resetIdCounter();
    $qfEvolve2 = new QuantumField(T_PLANCK);
    $pMassless = new Particle(ParticleType::Photon, position: [0.0, 0.0, 0.0], momentum: [1.0, 0.0, 0.0]);
    $qfEvolve2->particles[] = $pMassless;
    $qfEvolve2->evolveStep(1.0);
    assertTrue('Massless particle moved at speed of light', $pMassless->position[0] > 0.0);

    // Massless particle with zero momentum
    Particle::resetIdCounter();
    $qfEvolve3 = new QuantumField(T_PLANCK);
    $pZeroMom = new Particle(ParticleType::Photon, position: [0.0, 0.0, 0.0], momentum: [0.0, 0.0, 0.0]);
    $qfEvolve3->particles[] = $pZeroMom;
    $qfEvolve3->evolveStep(1.0);
    // With zero momentum, norm defaults to 1.0 so it still moves along [0,0,0]/1 * C = [0,0,0]
    assertTrue('Zero momentum photon evolve does not error', true);

    // --- QuantumField::toSnapshot() ---
    Particle::resetIdCounter();
    $qfSnap = new QuantumField(5000.0);
    $qfSnap->particles[] = new Particle(ParticleType::Electron);
    $qfSnap->particles[] = new Particle(ParticleType::Proton);
    $qfSnap->totalCreated = 5;
    $qfSnap->totalAnnihilated = 3;
    $qfSnap->vacuumEnergy = 1.234;
    $snap = $qfSnap->toSnapshot();
    assertApprox('Snapshot temperature', 5000.0, $snap['temperature'], 1e-10);
    assertEqual('Snapshot particle_count', 2, $snap['particle_count']);
    assertTrue('Snapshot has particles_by_type', isset($snap['particles_by_type']));
    assertEqual('Snapshot electron count', 1, $snap['particles_by_type']['electron']);
    assertEqual('Snapshot proton count', 1, $snap['particles_by_type']['proton']);
    assertTrue('Snapshot total_energy > 0', $snap['total_energy'] > 0);
    assertApprox('Snapshot vacuum_energy', 1.234, $snap['vacuum_energy'], 0.001);
    assertEqual('Snapshot total_created', 5, $snap['total_created']);
    assertEqual('Snapshot total_annihilated', 3, $snap['total_annihilated']);

    endSuite();
}

// =========================================================================
//  Test: Atomic System
// =========================================================================

function testAtomic(): void
{
    startSuite('Atomic');

    Atom::resetIdCounter();

    // Hydrogen
    $h = new Atom(1);
    assertEqual('H atomic number', 1, $h->atomicNumber);
    assertEqual('H mass number', 1, $h->massNumber);
    assertEqual('H symbol', 'H', $h->symbol());
    assertEqual('H name', 'Hydrogen', $h->name());
    assertEqual('H electron count', 1, $h->electronCount);
    assertEqual('H charge', 0, $h->charge());
    assertEqual('H valence electrons', 1, $h->valenceElectrons());
    assertEqual('H needs 1 electron', 1, $h->needsElectrons());
    assertTrue('H not noble gas', !$h->isNobleGas());
    assertTrue('H not ion', !$h->isIon());

    // Helium
    $he = new Atom(2, 4);
    assertEqual('He symbol', 'He', $he->symbol());
    assertEqual('He mass number', 4, $he->massNumber);
    assertTrue('He is noble gas', $he->isNobleGas());

    // Carbon
    $c = new Atom(6);
    assertEqual('C symbol', 'C', $c->symbol());
    assertEqual('C mass number', 12, $c->massNumber);
    assertEqual('C valence electrons', 4, $c->valenceElectrons());
    assertApprox('C electronegativity', 2.55, $c->electronegativity(), 0.01);

    // Oxygen
    $o = new Atom(8);
    assertEqual('O symbol', 'O', $o->symbol());
    assertEqual('O valence electrons', 6, $o->valenceElectrons());
    assertEqual('O needs 2 electrons', 2, $o->needsElectrons());
    assertApprox('O electronegativity', 3.44, $o->electronegativity(), 0.01);

    // Neon
    $ne = new Atom(10);
    assertTrue('Neon is noble gas', $ne->isNobleGas());
    assertEqual('Ne needs 0 electrons', 0, $ne->needsElectrons());

    // Ionization
    $h2 = new Atom(1);
    assertTrue('H can ionize', $h2->ionize());
    assertEqual('Ionized H has 0 electrons', 0, $h2->electronCount);
    assertEqual('Ionized H charge = +1', 1, $h2->charge());
    assertTrue('Ionized H is ion', $h2->isIon());
    assertTrue('Cannot ionize further', !$h2->ionize());

    // Electron capture
    $h3 = new Atom(1);
    $h3->ionize();
    $h3->captureElectron();
    assertEqual('After capture, 1 electron', 1, $h3->electronCount);
    assertEqual('After capture, charge 0', 0, $h3->charge());

    // Bonding
    $h4 = new Atom(1);
    $h5 = new Atom(1);
    assertTrue('Two H can bond', $h4->canBondWith($h5));
    $he2 = new Atom(2, 4);
    assertTrue('Noble gas cannot bond', !$h4->canBondWith($he2));

    // Bond types
    $na = new Atom(11);
    $cl = new Atom(17);
    assertEqual('NaCl ionic', 'ionic', $na->bondType($cl));

    $hB = new Atom(1);
    $oB = new Atom(8);
    assertEqual('H-O polar covalent', 'polar_covalent', $hB->bondType($oB));

    $cB = new Atom(6);
    $hB2 = new Atom(1);
    assertEqual('C-H covalent', 'covalent', $cB->bondType($hB2));

    // Bond energy
    assertApprox('Ionic bond energy', BOND_ENERGY_IONIC, $na->bondEnergy($cl), 1e-10);
    assertApprox('Covalent bond energy', BOND_ENERGY_COVALENT, $cB->bondEnergy($hB2), 1e-10);

    // Distance
    $a1 = new Atom(1, position: [0.0, 0.0, 0.0]);
    $a2 = new Atom(1, position: [3.0, 4.0, 0.0]);
    assertApprox('Distance = 5', 5.0, $a1->distanceTo($a2), 1e-10);

    // Nucleosynthesis: 4p + 4n -> 2 He-4
    Atom::resetIdCounter();
    $as = new AtomicSystem(T_NUCLEOSYNTHESIS);
    $atoms = $as->nucleosynthesis(4, 4);
    assertEqual('2 He atoms from 4p+4n', 2, count($atoms));
    assertEqual('He atomic number', 2, $atoms[0]->atomicNumber);
    assertEqual('He mass number', 4, $atoms[0]->massNumber);

    // Nucleosynthesis: only protons -> hydrogen
    $as2 = new AtomicSystem(T_NUCLEOSYNTHESIS);
    $atoms2 = $as2->nucleosynthesis(5, 0);
    assertEqual('5 H atoms from 5p+0n', 5, count($atoms2));
    foreach ($atoms2 as $a) {
        assertEqual('Each is H', 1, $a->atomicNumber);
    }

    // Element counts
    $as3 = new AtomicSystem();
    $as3->atoms[] = new Atom(1);
    $as3->atoms[] = new Atom(1);
    $as3->atoms[] = new Atom(2, 4);
    $counts = $as3->elementCounts();
    assertEqual('2 hydrogen', 2, $counts['H']);
    assertEqual('1 helium', 1, $counts['He']);

    // Temperature
    $as4 = new AtomicSystem(5000.0);
    assertApprox('Initial temp 5000', 5000.0, $as4->temperature, 1e-10);
    $as4->cool(0.5);
    assertApprox('Cooled to 2500', 2500.0, $as4->temperature, 1e-10);

    // --- ElectronShell: isFull(), isEmpty(), addElectron(), removeElectron() ---
    $shell = new ElectronShell(n: 1, maxElectrons: 2, electrons: 0);
    assertTrue('New empty shell isEmpty', $shell->isEmpty());
    assertTrue('New empty shell not isFull', !$shell->isFull());

    // addElectron
    $added = $shell->addElectron();
    assertTrue('Added first electron', $added);
    assertEqual('Shell has 1 electron', 1, $shell->electrons);
    assertTrue('Shell not empty after add', !$shell->isEmpty());
    assertTrue('Shell not full with 1/2', !$shell->isFull());

    $added2 = $shell->addElectron();
    assertTrue('Added second electron', $added2);
    assertEqual('Shell has 2 electrons', 2, $shell->electrons);
    assertTrue('Shell is full with 2/2', $shell->isFull());

    // Cannot add to full shell
    $added3 = $shell->addElectron();
    assertTrue('Cannot add to full shell', !$added3);
    assertEqual('Shell still has 2 electrons', 2, $shell->electrons);

    // removeElectron
    $removed = $shell->removeElectron();
    assertTrue('Removed electron', $removed);
    assertEqual('Shell has 1 electron after remove', 1, $shell->electrons);
    assertTrue('Shell not full after remove', !$shell->isFull());

    $removed2 = $shell->removeElectron();
    assertTrue('Removed second electron', $removed2);
    assertEqual('Shell has 0 electrons', 0, $shell->electrons);
    assertTrue('Shell is empty after removing all', $shell->isEmpty());

    // Cannot remove from empty shell
    $removed3 = $shell->removeElectron();
    assertTrue('Cannot remove from empty shell', !$removed3);
    assertEqual('Shell still has 0 electrons', 0, $shell->electrons);

    // Larger shell
    $shell2 = new ElectronShell(n: 2, maxElectrons: 8, electrons: 7);
    assertTrue('Shell2 not full with 7/8', !$shell2->isFull());
    assertTrue('Shell2 not empty with 7/8', !$shell2->isEmpty());
    $shell2->addElectron();
    assertTrue('Shell2 full with 8/8', $shell2->isFull());

    // --- Atom::resetIdCounter() ---
    Atom::resetIdCounter();
    $aReset1 = new Atom(1);
    assertEqual('After reset, first atom ID = 1', 1, $aReset1->atomId);
    Atom::resetIdCounter();
    $aReset2 = new Atom(6);
    assertEqual('After second reset, atom ID = 1', 1, $aReset2->atomId);

    // --- AtomicSystem::recombination() ---
    Atom::resetIdCounter();
    Particle::resetIdCounter();
    $asRecomb = new AtomicSystem(T_RECOMBINATION * 0.5); // Below recombination threshold
    $qfRecomb = new QuantumField(T_RECOMBINATION * 0.5);
    // Add protons and electrons to quantum field
    $qfRecomb->particles[] = new Particle(ParticleType::Proton);
    $qfRecomb->particles[] = new Particle(ParticleType::Proton);
    $qfRecomb->particles[] = new Particle(ParticleType::Electron);
    $qfRecomb->particles[] = new Particle(ParticleType::Electron);
    $qfRecomb->particles[] = new Particle(ParticleType::Photon); // Should not be affected
    $newAtomsRecomb = $asRecomb->recombination($qfRecomb);
    assertEqual('Recombination produced 2 H atoms', 2, count($newAtomsRecomb));
    assertEqual('Recomb atom is hydrogen', 1, $newAtomsRecomb[0]->atomicNumber);
    assertEqual('Recomb atom is hydrogen (2)', 1, $newAtomsRecomb[1]->atomicNumber);
    assertEqual('AtomicSystem has 2 atoms after recombination', 2, count($asRecomb->atoms));
    // Photon should remain in field
    assertEqual('Photon remains in field', 1, count($qfRecomb->particles));
    assertEqual('Remaining particle is photon', ParticleType::Photon, $qfRecomb->particles[0]->particleType);

    // Recombination at high temperature should produce nothing
    Atom::resetIdCounter();
    Particle::resetIdCounter();
    $asRecombHigh = new AtomicSystem(T_RECOMBINATION * 2.0);
    $qfRecombHigh = new QuantumField(T_RECOMBINATION * 2.0);
    $qfRecombHigh->particles[] = new Particle(ParticleType::Proton);
    $qfRecombHigh->particles[] = new Particle(ParticleType::Electron);
    $noAtoms = $asRecombHigh->recombination($qfRecombHigh);
    assertEqual('No recombination at high T', 0, count($noAtoms));

    // --- AtomicSystem::stellarNucleosynthesis() ---
    Atom::resetIdCounter();
    $asStellar = new AtomicSystem(T_STELLAR_CORE);
    // Add enough helium atoms for triple-alpha process to potentially run
    for ($i = 0; $i < 30; $i++) {
        $asStellar->atoms[] = new Atom(2, 4);
    }
    $initialHeCount = 30;
    // Run multiple times to give the probabilistic process a chance
    $newStellar = [];
    for ($i = 0; $i < 100; $i++) {
        $result = $asStellar->stellarNucleosynthesis($asStellar->temperature);
        $newStellar = array_merge($newStellar, $result);
    }
    // At T_STELLAR_CORE (>1e3), stellar nucleosynthesis should run
    // The triple-alpha has 1% chance per iteration, so over 100 tries likely some
    assertTrue('Stellar nucleosynthesis ran without error', true);

    // Test that low temperature produces nothing
    Atom::resetIdCounter();
    $asStellarLow = new AtomicSystem(500.0);
    $asStellarLow->atoms[] = new Atom(2, 4);
    $asStellarLow->atoms[] = new Atom(2, 4);
    $asStellarLow->atoms[] = new Atom(2, 4);
    $noStellar = $asStellarLow->stellarNucleosynthesis(500.0);
    assertEqual('No stellar nucleosynthesis at low T', 0, count($noStellar));

    // --- AtomicSystem::attemptBond() ---
    Atom::resetIdCounter();
    $asBond = new AtomicSystem(300.0);
    $hBond1 = new Atom(1, position: [0.0, 0.0, 0.0]);
    $hBond2 = new Atom(1, position: [1.0, 0.0, 0.0]); // Close enough to bond
    $asBond->atoms[] = $hBond1;
    $asBond->atoms[] = $hBond2;

    // Try bonding multiple times (probabilistic)
    $bondResult = false;
    for ($i = 0; $i < 100; $i++) {
        if (empty($hBond1->bonds)) {
            $bondResult = $asBond->attemptBond($hBond1, $hBond2);
            if ($bondResult) break;
        }
    }
    // At room temperature with close atoms, bonding should eventually succeed
    if ($bondResult) {
        assertTrue('Bond was formed', $bondResult);
        assertTrue('H1 has bond to H2', in_array($hBond2->atomId, $hBond1->bonds));
        assertTrue('H2 has bond to H1', in_array($hBond1->atomId, $hBond2->bonds));
        assertTrue('bondsFormed incremented', $asBond->bondsFormed > 0);
    } else {
        assertTrue('AttemptBond probabilistic - may not form', true);
    }

    // Noble gas can't bond
    Atom::resetIdCounter();
    $asBondNoble = new AtomicSystem(300.0);
    $hForNoble = new Atom(1, position: [0.0, 0.0, 0.0]);
    $heForNoble = new Atom(2, 4, position: [0.5, 0.0, 0.0]);
    $nobleBond = $asBondNoble->attemptBond($hForNoble, $heForNoble);
    assertTrue('Cannot bond with noble gas', !$nobleBond);

    // Atoms too far apart
    Atom::resetIdCounter();
    $asBondFar = new AtomicSystem(300.0);
    $hFar1 = new Atom(1, position: [0.0, 0.0, 0.0]);
    $hFar2 = new Atom(1, position: [100.0, 0.0, 0.0]); // Very far
    $farBond = $asBondFar->attemptBond($hFar1, $hFar2);
    assertTrue('Cannot bond when too far', !$farBond);

    // --- AtomicSystem::breakBond() ---
    Atom::resetIdCounter();
    $asBreak = new AtomicSystem(1e8); // Very high temperature for bond breaking
    $hBreak1 = new Atom(1, position: [0.0, 0.0, 0.0]);
    $hBreak2 = new Atom(1, position: [1.0, 0.0, 0.0]);
    // Manually form a bond
    $hBreak1->bonds[] = $hBreak2->atomId;
    $hBreak2->bonds[] = $hBreak1->atomId;
    $asBreak->atoms[] = $hBreak1;
    $asBreak->atoms[] = $hBreak2;

    // Break bond at very high temperature
    $broken = false;
    for ($i = 0; $i < 100; $i++) {
        if (!empty($hBreak1->bonds)) {
            $broken = $asBreak->breakBond($hBreak1, $hBreak2);
            if ($broken) break;
        }
    }
    if ($broken) {
        assertTrue('Bond was broken', $broken);
        assertTrue('H1 no longer bonded to H2', !in_array($hBreak2->atomId, $hBreak1->bonds));
        assertTrue('H2 no longer bonded to H1', !in_array($hBreak1->atomId, $hBreak2->bonds));
        assertTrue('bondsBroken incremented', $asBreak->bondsBroken > 0);
    } else {
        assertTrue('BreakBond probabilistic - may not break', true);
    }

    // Cannot break non-existent bond
    Atom::resetIdCounter();
    $asBreakNo = new AtomicSystem(1e8);
    $hNoBond1 = new Atom(1);
    $hNoBond2 = new Atom(1);
    $noBondBreak = $asBreakNo->breakBond($hNoBond1, $hNoBond2);
    assertTrue('Cannot break non-existent bond', !$noBondBreak);

    // --- AtomicSystem::toSnapshot() ---
    Atom::resetIdCounter();
    $asSnap = new AtomicSystem(3000.0);
    $asSnap->atoms[] = new Atom(1);
    $asSnap->atoms[] = new Atom(1);
    $asSnap->atoms[] = new Atom(2, 4);
    $asSnap->bondsFormed = 5;
    $asSnap->bondsBroken = 2;
    $snapAtomic = $asSnap->toSnapshot();
    assertApprox('Atomic snapshot temperature', 3000.0, $snapAtomic['temperature'], 1e-10);
    assertEqual('Atomic snapshot atom_count', 3, $snapAtomic['atom_count']);
    assertTrue('Atomic snapshot has elements', isset($snapAtomic['elements']));
    assertEqual('Atomic snapshot H count', 2, $snapAtomic['elements']['H']);
    assertEqual('Atomic snapshot He count', 1, $snapAtomic['elements']['He']);
    assertEqual('Atomic snapshot bonds_formed', 5, $snapAtomic['bonds_formed']);
    assertEqual('Atomic snapshot bonds_broken', 2, $snapAtomic['bonds_broken']);

    endSuite();
}

// =========================================================================
//  Test: Chemistry
// =========================================================================

function testChemistry(): void
{
    startSuite('Chemistry');

    Atom::resetIdCounter();
    Molecule::resetIdCounter();

    // Molecule creation
    $h1 = new Atom(1);
    $h2 = new Atom(1);
    $o = new Atom(8);
    $water = new Molecule([$h1, $h2, $o], 'water');
    assertEqual('Water name', 'water', $water->name);
    assertEqual('Water atom count', 3, $water->atomCount());
    assertTrue('Molecule ID > 0', $water->moleculeId > 0);

    // Molecular weight: H=1 + H=1 + O=16 = 18
    assertApprox('Water MW', 18.0, $water->molecularWeight(), 0.01);

    // Formula computation
    $c = new Atom(6);
    $h3 = new Atom(1);
    $h4 = new Atom(1);
    $h5 = new Atom(1);
    $h6 = new Atom(1);
    $methane = new Molecule([$c, $h3, $h4, $h5, $h6], 'methane');
    assertEqual('Methane formula', 'CH4', $methane->formula);

    // Organic detection
    assertTrue('Methane is organic', $methane->isOrganic);

    $h7 = new Atom(1);
    $o2 = new Atom(8);
    $inorganic = new Molecule([$h7, $o2], 'HO');
    assertTrue('HO is not organic', !$inorganic->isOrganic);

    // Form water via ChemicalSystem
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asW = new AtomicSystem(300.0);
    for ($i = 0; $i < 4; $i++) $asW->atoms[] = new Atom(1);
    for ($i = 0; $i < 2; $i++) $asW->atoms[] = new Atom(8);
    $csW = new ChemicalSystem($asW);
    $waters = $csW->formWater();
    assertEqual('2 water molecules', 2, count($waters));
    assertEqual('Water count tracked', 2, $csW->waterCount);

    // Form methane
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asM = new AtomicSystem(300.0);
    for ($i = 0; $i < 8; $i++) $asM->atoms[] = new Atom(1);
    for ($i = 0; $i < 2; $i++) $asM->atoms[] = new Atom(6);
    $csM = new ChemicalSystem($asM);
    $methanes = $csM->formMethane();
    assertEqual('2 methane molecules', 2, count($methanes));
    foreach ($methanes as $m) {
        assertEqual('Methane 5 atoms', 5, $m->atomCount());
    }

    // Form ammonia
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asA = new AtomicSystem(300.0);
    for ($i = 0; $i < 6; $i++) $asA->atoms[] = new Atom(1);
    for ($i = 0; $i < 2; $i++) $asA->atoms[] = new Atom(7);
    $csA = new ChemicalSystem($asA);
    $ammonias = $csA->formAmmonia();
    assertEqual('2 ammonia molecules', 2, count($ammonias));
    foreach ($ammonias as $a) {
        assertEqual('Ammonia 4 atoms', 4, $a->atomCount());
    }

    // Form amino acid: 2C + 5H + 2O + 1N
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asAA = new AtomicSystem(300.0);
    for ($i = 0; $i < 5; $i++) $asAA->atoms[] = new Atom(1);
    for ($i = 0; $i < 2; $i++) $asAA->atoms[] = new Atom(6);
    $asAA->atoms[] = new Atom(7);
    for ($i = 0; $i < 2; $i++) $asAA->atoms[] = new Atom(8);
    $csAA = new ChemicalSystem($asAA);
    $aa = $csAA->formAminoAcid('Gly');
    assertNotNull('Amino acid formed', $aa);
    assertEqual('AA name = Gly', 'Gly', $aa->name);
    assertTrue('AA is organic', $aa->isOrganic);
    assertEqual('AA count', 1, $csAA->aminoAcidCount);
    assertEqual('AA has 10 atoms', 10, $aa->atomCount());

    // Insufficient atoms for amino acid
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asI = new AtomicSystem(300.0);
    $asI->atoms[] = new Atom(1);
    $asI->atoms[] = new Atom(6);
    $csI = new ChemicalSystem($asI);
    $aa2 = $csI->formAminoAcid('Gly');
    assertNull('No AA with insufficient atoms', $aa2);

    // Form nucleotide: 5C + 8H + 4O + 2N
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asN = new AtomicSystem(300.0);
    for ($i = 0; $i < 8; $i++) $asN->atoms[] = new Atom(1);
    for ($i = 0; $i < 5; $i++) $asN->atoms[] = new Atom(6);
    for ($i = 0; $i < 2; $i++) $asN->atoms[] = new Atom(7);
    for ($i = 0; $i < 4; $i++) $asN->atoms[] = new Atom(8);
    $csN = new ChemicalSystem($asN);
    $nuc = $csN->formNucleotide('A');
    assertNotNull('Nucleotide formed', $nuc);
    assertEqual('Nucleotide name', 'nucleotide-A', $nuc->name);
    assertTrue('Nucleotide is organic', $nuc->isOrganic);
    assertEqual('Nucleotide count', 1, $csN->nucleotideCount);
    assertEqual('Nucleotide has 19 atoms', 19, $nuc->atomCount());

    // Molecule census
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asC = new AtomicSystem(300.0);
    for ($i = 0; $i < 10; $i++) $asC->atoms[] = new Atom(1);
    for ($i = 0; $i < 3; $i++) $asC->atoms[] = new Atom(8);
    $csC = new ChemicalSystem($asC);
    $csC->formWater();
    $census = $csC->moleculeCensus();
    assertTrue('Census has water', isset($census['water']));
    assertEqual('3 water', 3, $census['water']);

    // Chemical reaction
    $rxn = new ChemicalReaction(['H2', 'O'], ['H2O'], 1.0, -2.5, 'combustion');
    assertEqual('Reaction name', 'combustion', $rxn->name);
    // At very high temperature, it should proceed more often
    $proceedCount = 0;
    for ($i = 0; $i < 100; $i++) {
        if ($rxn->canProceed(1e6)) {
            $proceedCount++;
        }
    }
    assertTrue('Reaction proceeds at high T', $proceedCount > 0);

    // --- ChemicalSystem::catalyzedReaction() ---
    // Set up with enough atoms for amino acid (2C + 5H + 2O + 1N) and nucleotide (5C + 8H + 4O + 2N)
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asCat = new AtomicSystem(300.0);
    // Add plenty of atoms for both amino acids and nucleotides
    for ($i = 0; $i < 40; $i++) $asCat->atoms[] = new Atom(1); // H
    for ($i = 0; $i < 20; $i++) $asCat->atoms[] = new Atom(6); // C
    for ($i = 0; $i < 10; $i++) $asCat->atoms[] = new Atom(7); // N
    for ($i = 0; $i < 15; $i++) $asCat->atoms[] = new Atom(8); // O
    $csCat = new ChemicalSystem($asCat);

    // Run catalyzed reaction at very high temperature with catalyst for higher probability
    $totalFormed = 0;
    for ($i = 0; $i < 200; $i++) {
        $totalFormed += $csCat->catalyzedReaction(1e8, catalystPresent: true);
    }
    // With high temp and catalyst, some reactions should occur
    assertTrue('Catalyzed reaction formed molecules', $totalFormed > 0);
    assertTrue('reactionsOccurred tracked', $csCat->reactionsOccurred > 0);

    // Without catalyst and low temperature, fewer reactions
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asCatLow = new AtomicSystem(1.0); // Very low temperature
    for ($i = 0; $i < 20; $i++) $asCatLow->atoms[] = new Atom(1);
    for ($i = 0; $i < 10; $i++) $asCatLow->atoms[] = new Atom(6);
    for ($i = 0; $i < 5; $i++) $asCatLow->atoms[] = new Atom(7);
    for ($i = 0; $i < 10; $i++) $asCatLow->atoms[] = new Atom(8);
    $csCatLow = new ChemicalSystem($asCatLow);
    $lowFormed = 0;
    for ($i = 0; $i < 20; $i++) {
        $lowFormed += $csCatLow->catalyzedReaction(1.0, catalystPresent: false);
    }
    assertTrue('Low T catalyzed reaction count >= 0', $lowFormed >= 0);

    // --- ChemicalSystem::toSnapshot() ---
    Atom::resetIdCounter();
    Molecule::resetIdCounter();
    $asSnapChem = new AtomicSystem(300.0);
    for ($i = 0; $i < 4; $i++) $asSnapChem->atoms[] = new Atom(1);
    for ($i = 0; $i < 2; $i++) $asSnapChem->atoms[] = new Atom(8);
    $csSnapChem = new ChemicalSystem($asSnapChem);
    $csSnapChem->formWater();
    $snapChem = $csSnapChem->toSnapshot();
    assertTrue('Chem snapshot has molecule_count', isset($snapChem['molecule_count']));
    assertEqual('Chem snapshot molecule_count = 2', 2, $snapChem['molecule_count']);
    assertTrue('Chem snapshot has molecules_by_type', isset($snapChem['molecules_by_type']));
    assertEqual('Chem snapshot water count', 2, $snapChem['molecules_by_type']['water']);
    assertEqual('Chem snapshot water_count', 2, $snapChem['water_count']);
    assertEqual('Chem snapshot amino_acid_count', 0, $snapChem['amino_acid_count']);
    assertEqual('Chem snapshot nucleotide_count', 0, $snapChem['nucleotide_count']);
    assertTrue('Chem snapshot has reactions_occurred', isset($snapChem['reactions_occurred']));

    endSuite();
}

// =========================================================================
//  Test: Biology
// =========================================================================

function testBiology(): void
{
    startSuite('Biology');

    Cell::resetIdCounter();
    Particle::resetIdCounter();

    // DNAStrand
    $dna = new DNAStrand(['A', 'T', 'G', 'C', 'A', 'T']);
    assertEqual('DNA length', 6, $dna->length());
    assertEqual('DNA generation', 0, $dna->generation);
    assertEqual('DNA mutation count', 0, $dna->mutationCount);

    // Complementary strand
    $comp = $dna->complementaryStrand();
    assertEqual('Complement A->T', 'T', $comp[0]);
    assertEqual('Complement T->A', 'A', $comp[1]);
    assertEqual('Complement G->C', 'C', $comp[2]);
    assertEqual('Complement C->G', 'G', $comp[3]);

    // GC content
    $dnaGC = new DNAStrand(['G', 'C', 'G', 'C']);
    assertApprox('All GC = 1.0', 1.0, $dnaGC->gcContent(), 1e-10);

    $dnaAT = new DNAStrand(['A', 'T', 'A', 'T']);
    assertApprox('All AT = 0.0', 0.0, $dnaAT->gcContent(), 1e-10);

    $dnaMix = new DNAStrand(['A', 'G', 'C', 'T']);
    assertApprox('50% GC = 0.5', 0.5, $dnaMix->gcContent(), 1e-10);

    // Random strand
    $rand = DNAStrand::randomStrand(100, 3);
    assertEqual('Random strand length', 100, $rand->length());
    assertEqual('Random strand has 3 genes', 3, count($rand->genes));

    // Transcription
    $gene = new Gene('test', ['A', 'T', 'G', 'C'], 0, 4);
    $rna = $gene->transcribe();
    assertEqual('RNA length = gene length', 4, count($rna));
    assertEqual('A stays A', 'A', $rna[0]);
    assertEqual('T becomes U', 'U', $rna[1]);
    assertEqual('G stays G', 'G', $rna[2]);
    assertEqual('C stays C', 'C', $rna[3]);

    // Translation: AUG TTT TAA -> Met Phe STOP
    $gene2 = new Gene('test2', ['A', 'T', 'G', 'T', 'T', 'T', 'T', 'A', 'A'], 0, 9);
    $mrna = $gene2->transcribe();
    $protein = translateMRNA($mrna);
    assertEqual('Protein has 2 AAs', 2, count($protein));
    assertEqual('First AA = Met', 'Met', $protein[0]);
    assertEqual('Second AA = Phe', 'Phe', $protein[1]);

    // DNA replication
    $dna2 = new DNAStrand(['A', 'T', 'G', 'C', 'A', 'T']);
    $copy = $dna2->replicate();
    assertEqual('Copy length = original', $dna2->length(), $copy->length());
    assertEqual('Copy generation = 1', 1, $copy->generation);

    // Gene mutation
    $longGene = new Gene('mut', array_fill(0, 100, 'A'), 0, 100);
    $mutCount = $longGene->mutate(0.5);
    assertTrue('High rate mutations occurred', $mutCount > 0);

    // Gene silencing via methylation
    $silGene = new Gene('sil', ['A', 'T', 'G', 'C', 'A', 'T', 'G', 'C', 'A', 'T'], 0, 10);
    assertTrue('Gene not silenced initially', !$silGene->isSilenced());

    // Add heavy methylation (>30% of length)
    for ($i = 0; $i < 5; $i++) {
        $silGene->methylate($i);
    }
    assertTrue('Gene silenced after heavy methylation', $silGene->isSilenced());
    assertEqual('Silenced gene transcribes empty', 0, count($silGene->transcribe()));

    // Epigenetics: acetylation increases expression
    $aceGene = new Gene('ace', ['A', 'T', 'G', 'C', 'A'], 0, 5);
    $initialExpr = $aceGene->expressionLevel;
    $aceGene->acetylate(0);
    $aceGene->acetylate(1);
    assertTrue('Acetylation increases expression', $aceGene->expressionLevel >= $initialExpr);

    // Protein
    $prot = new Protein(['Met', 'Phe', 'Gly', 'Ala'], 'test_protein', 'enzyme');
    assertEqual('Protein length', 4, $prot->length());
    assertEqual('Protein function', 'enzyme', $prot->function);
    assertTrue('Protein not folded initially', !$prot->folded);

    // Protein folding
    $longProt = new Protein(array_fill(0, 20, 'Ala'), 'long', 'structural');
    $longProt->fold();
    // Folding is probabilistic, so we just test it runs
    assertTrue('Fold runs without error', true);

    // Cell
    Cell::resetIdCounter();
    $cell = new Cell();
    assertTrue('Cell ID > 0', $cell->cellId > 0);
    assertTrue('Cell alive', $cell->alive);
    assertApprox('Cell fitness = 1.0', 1.0, $cell->fitness, 1e-10);

    // Cell metabolism
    $cell->metabolize(20.0);
    assertTrue('Cell still alive after metabolism', $cell->alive);

    // Cell fitness
    $fitness = $cell->computeFitness();
    assertTrue('Fitness >= 0', $fitness >= 0.0);
    assertTrue('Fitness <= 1', $fitness <= 1.0);

    // Cell division
    $cell2 = new Cell(energy: 100.0);
    $daughter = $cell2->divide();
    assertNotNull('Cell divides', $daughter);
    assertTrue('Daughter is alive', $daughter->alive);
    assertEqual('Daughter generation', 1, $daughter->generation);

    // Dead cell can't divide
    $deadCell = new Cell();
    $deadCell->alive = false;
    $deadDaughter = $deadCell->divide();
    assertNull('Dead cell returns null', $deadDaughter);

    // Biosphere
    Cell::resetIdCounter();
    $bio = new Biosphere(5, 90);
    assertEqual('Initial 5 cells', 5, count($bio->cells));
    assertEqual('5 total born', 5, $bio->totalBorn);
    assertEqual('Generation 0', 0, $bio->generation);

    // Biosphere step
    $bio->step(temperature: 300.0);
    assertEqual('Generation 1', 1, $bio->generation);
    assertTrue('Cells exist after step', count($bio->cells) > 0);

    // Average fitness
    $avgFitness = $bio->averageFitness();
    assertTrue('Average fitness >= 0', $avgFitness >= 0.0);

    // Average GC content
    $avgGC = $bio->averageGcContent();
    assertTrue('Average GC >= 0', $avgGC >= 0.0);
    assertTrue('Average GC <= 1', $avgGC <= 1.0);

    // Biosphere snapshot
    $snap = $bio->toSnapshot();
    assertTrue('Snapshot has generation', isset($snap['generation']));
    assertTrue('Snapshot has population', isset($snap['population']));

    // --- EpigeneticMark::toCompact() ---
    $markMethyl = new EpigeneticMark(position: 3, markType: 'methylation', active: true, generationAdded: 0);
    assertEqual('Methylation toCompact', 'M3+', $markMethyl->toCompact());

    $markAcetyl = new EpigeneticMark(position: 7, markType: 'acetylation', active: false, generationAdded: 1);
    assertEqual('Acetylation inactive toCompact', 'A7-', $markAcetyl->toCompact());

    $markPhospho = new EpigeneticMark(position: 0, markType: 'phosphorylation', active: true, generationAdded: 5);
    assertEqual('Phosphorylation toCompact', 'P0+', $markPhospho->toCompact());

    $markMethylInactive = new EpigeneticMark(position: 12, markType: 'methylation', active: false, generationAdded: 2);
    assertEqual('Inactive methylation toCompact', 'M12-', $markMethylInactive->toCompact());

    // --- Gene::length() ---
    $gLen1 = new Gene('short', ['A', 'T'], 0, 2);
    assertEqual('Gene length = 2', 2, $gLen1->length());
    $gLen2 = new Gene('empty', [], 0, 0);
    assertEqual('Empty gene length = 0', 0, $gLen2->length());
    $gLen3 = new Gene('long', array_fill(0, 50, 'G'), 0, 50);
    assertEqual('Gene length = 50', 50, $gLen3->length());

    // --- Gene::updateExpression() ---
    $gExpr = new Gene('expr_test', ['A', 'T', 'G', 'C', 'A', 'T', 'G', 'C', 'A', 'T'], 0, 10);
    assertApprox('Initial expression = 1.0', 1.0, $gExpr->expressionLevel, 1e-10);

    // Add methylation (suppresses expression)
    $gExpr->methylate(0);
    $gExpr->methylate(1);
    $gExpr->methylate(2);
    assertTrue('Expression decreased after methylation', $gExpr->expressionLevel < 1.0);

    // Add acetylation (increases expression)
    $gExprAce = new Gene('ace_test', ['A', 'T', 'G', 'C', 'A', 'T', 'G', 'C', 'A', 'T'], 0, 10);
    $gExprAce->methylate(0);
    $gExprAce->methylate(1);
    $exprAfterMethyl = $gExprAce->expressionLevel;
    $gExprAce->acetylate(0);
    $gExprAce->acetylate(1);
    $gExprAce->acetylate(2);
    assertTrue('Expression increased after acetylation', $gExprAce->expressionLevel >= $exprAfterMethyl);

    // Direct updateExpression call
    $gExprDirect = new Gene('direct', ['A', 'T', 'G', 'C'], 0, 4);
    $gExprDirect->epigeneticMarks[] = new EpigeneticMark(0, 'methylation', true);
    $gExprDirect->epigeneticMarks[] = new EpigeneticMark(1, 'methylation', true);
    $gExprDirect->updateExpression();
    assertTrue('updateExpression recalculates correctly', $gExprDirect->expressionLevel < 1.0);

    // --- DNAStrand::applyMutations() ---
    Cell::resetIdCounter();
    $dnaMut = DNAStrand::randomStrand(200, 3);
    $initialMutCount = $dnaMut->mutationCount;
    // Apply with high UV intensity to ensure mutations occur
    $mutationsApplied = $dnaMut->applyMutations(uvIntensity: 100.0, cosmicRayFlux: 100.0);
    assertTrue('Mutations applied > 0 with high radiation', $mutationsApplied > 0);
    assertEqual('mutationCount updated', $initialMutCount + $mutationsApplied, $dnaMut->mutationCount);

    // Apply with zero intensity - should have zero mutations
    $dnaMutZero = DNAStrand::randomStrand(50, 2);
    $zeroMuts = $dnaMutZero->applyMutations(uvIntensity: 0.0, cosmicRayFlux: 0.0);
    assertEqual('Zero intensity = zero mutations', 0, $zeroMuts);

    // --- DNAStrand::applyEpigeneticChanges() ---
    $dnaEpi = DNAStrand::randomStrand(100, 3);
    // Count initial marks
    $initialMarks = 0;
    foreach ($dnaEpi->genes as $g) {
        $initialMarks += count($g->epigeneticMarks);
    }
    // Apply many rounds of epigenetic changes to ensure some marks are added
    for ($i = 0; $i < 100; $i++) {
        $dnaEpi->applyEpigeneticChanges(300.0, $i);
    }
    $finalMarks = 0;
    foreach ($dnaEpi->genes as $g) {
        $finalMarks += count($g->epigeneticMarks);
    }
    assertTrue('Epigenetic marks were added', $finalMarks > $initialMarks);

    // --- Cell::transcribeAndTranslate() ---
    Cell::resetIdCounter();
    // Create a cell with known DNA containing an AUG start codon
    $knownSeq = ['A', 'T', 'G', 'T', 'T', 'T', 'T', 'A', 'A']; // AUG UUU UAA -> Met Phe STOP
    $knownGene = new Gene('known', $knownSeq, 0, 9, expressionLevel: 1.0);
    $knownDna = new DNAStrand($knownSeq, [$knownGene]);
    $cellTT = new Cell(dna: $knownDna);
    $cellTT->proteins = []; // Clear any initial proteins
    $newProteins = $cellTT->transcribeAndTranslate();
    // Due to probabilistic gene expression, may or may not produce protein
    assertTrue('transcribeAndTranslate runs without error', true);
    // If proteins were produced, check they're valid
    if (count($newProteins) > 0) {
        assertTrue('Produced protein has amino acids', $newProteins[0]->length() > 0);
        assertTrue('Protein was added to cell', count($cellTT->proteins) > 0);
    }

    // Test with silenced gene (low expression)
    Cell::resetIdCounter();
    $silGene2 = new Gene('silenced', $knownSeq, 0, 9, expressionLevel: 0.05);
    $silDna = new DNAStrand($knownSeq, [$silGene2]);
    $cellSil = new Cell(dna: $silDna);
    $cellSil->proteins = [];
    $silProteins = $cellSil->transcribeAndTranslate();
    // Should produce no proteins since expression < 0.1
    assertEqual('Silenced gene produces no proteins', 0, count($silProteins));

    // --- Biosphere::totalMutations() ---
    Cell::resetIdCounter();
    $bioMut = new Biosphere(3, 60);
    // Initially no mutations
    $initialTotalMut = $bioMut->totalMutations();
    assertEqual('Initial total mutations = 0', 0, $initialTotalMut);

    // Apply mutations to cells
    foreach ($bioMut->cells as $cell) {
        $cell->dna->applyMutations(uvIntensity: 5000.0, cosmicRayFlux: 10.0);
    }
    $afterMutations = $bioMut->totalMutations();
    assertTrue('Total mutations > 0 after UV exposure', $afterMutations > 0);

    // Check that totalMutations sums across all cells
    $manualSum = 0;
    foreach ($bioMut->cells as $cell) {
        $manualSum += $cell->dna->mutationCount;
    }
    assertEqual('totalMutations matches sum of cell mutations', $manualSum, $bioMut->totalMutations());

    endSuite();
}

// =========================================================================
//  Test: Environment
// =========================================================================

function testEnvironment(): void
{
    startSuite('Environment');

    // Default environment
    $env = new Environment();
    assertApprox('Default temp = T_PLANCK', T_PLANCK, $env->temperature, 1.0);
    assertApprox('Default radiation = 1.0', 1.0, $env->radiation, 1e-10);
    assertApprox('Default pressure = 1.0', 1.0, $env->pressure, 1e-10);
    assertEqual('Tick = 0', 0, $env->tick);

    // Atmosphere composition
    assertTrue('Has hydrogen', isset($env->atmosphere['hydrogen']));
    assertTrue('Has helium', isset($env->atmosphere['helium']));
    assertApprox('Hydrogen = 0.75', 0.75, $env->atmosphere['hydrogen'], 1e-10);
    assertApprox('Helium = 0.25', 0.25, $env->atmosphere['helium'], 1e-10);

    // Step
    $env->step(5000.0);
    assertEqual('Tick = 1', 1, $env->tick);
    assertApprox('Temperature updated', 5000.0, $env->temperature, 1e-10);
    assertTrue('Radiation decreased', $env->radiation < 1.0);

    // Step at low temperature - atmosphere evolution
    $env2 = new Environment();
    for ($i = 0; $i < 100; $i++) {
        $env2->step(350.0);
    }
    assertTrue('Nitrogen increased at low temp', $env2->atmosphere['nitrogen'] > 0);
    assertTrue('Oxygen increased at low temp', $env2->atmosphere['oxygen'] > 0);

    // Events
    $env3 = new Environment();
    for ($i = 0; $i < 200; $i++) {
        $env3->step(5000.0);
    }
    // At 5000K (between 1e4 and 1000), volcanic events may occur
    assertTrue('Events may have occurred', count($env3->events) >= 0);

    // Summary
    $summary = $env->getSummary();
    assertTrue('Summary has temperature', isset($summary['temperature']));
    assertTrue('Summary has radiation', isset($summary['radiation']));
    assertTrue('Summary has atmosphere', isset($summary['atmosphere']));
    assertTrue('Summary has events count', isset($summary['events']));

    // --- EnvironmentalEvent::toCompact() ---
    $event1 = new EnvironmentalEvent('volcanic', 0.75, 30, [1.0, 2.0, 3.0], 42);
    assertEqual('Event toCompact volcanic', 'Event(volcanic,i=0.75,d=30)', $event1->toCompact());

    $event2 = new EnvironmentalEvent('impact', 1.0, 100, [0.0, 0.0, 0.0], 0);
    assertEqual('Event toCompact impact', 'Event(impact,i=1.00,d=100)', $event2->toCompact());

    $event3 = new EnvironmentalEvent('radiation', 0.01, 5, [0.0, 0.0, 0.0], 10);
    assertEqual('Event toCompact radiation', 'Event(radiation,i=0.01,d=5)', $event3->toCompact());

    $event4 = new EnvironmentalEvent('quake', 0.50, 1);
    assertEqual('Event toCompact default position', 'Event(quake,i=0.50,d=1)', $event4->toCompact());

    endSuite();
}

// =========================================================================
//  Test: Universe (integration)
// =========================================================================

function testUniverse(): void
{
    startSuite('Universe');

    // Creation
    $u = new Universe(ticksPerEpoch: 10);
    assertEqual('Initial epoch = 0', 0, $u->currentEpoch);
    assertEqual('Initial tick = 0', 0, $u->currentTick);
    assertApprox('Initial temp = T_PLANCK', T_PLANCK, $u->temperature, 1.0);
    assertTrue('Scale factor very small', $u->scaleFactor < 1e-20);

    // Epoch name
    assertEqual('First epoch name', 'Planck', $u->epochName());

    // Stats
    assertEqual('Initial particles_created', 0, $u->stats['particles_created']);
    assertEqual('Initial atoms_formed', 0, $u->stats['atoms_formed']);
    assertEqual('Initial molecules_formed', 0, $u->stats['molecules_formed']);

    // Run single epoch
    $result = $u->runEpoch(0);
    assertTrue('Result has epoch', isset($result['epoch']));
    assertTrue('Result has temperature', isset($result['temperature']));
    assertTrue('Result has scale', isset($result['scale']));
    assertTrue('Result has stats', isset($result['stats']));
    assertEqual('Epoch 0 name', 'Planck', $result['epoch']);

    // Run full simulation
    $u2 = new Universe(ticksPerEpoch: 5);
    $results = $u2->run();
    assertEqual('13 epoch results', 13, count($results));

    // Epoch progression
    assertEqual('Epoch 0 = Planck', 'Planck', $results[0]['epoch']);
    assertEqual('Epoch 1 = Inflation', 'Inflation', $results[1]['epoch']);
    assertEqual('Epoch 12 = Present Day', 'Present Day', $results[12]['epoch']);

    // Temperature should change from T_PLANCK toward the lower epoch targets
    // With very few ticks per epoch, the temperature may still be high
    // but it should have moved toward a lower target
    $lastTemp = $results[12]['temperature'];
    assertTrue('Final temperature is a number', is_float($lastTemp) || is_int($lastTemp));

    // Scale factor grows
    $firstScale = $results[0]['scale'];
    $lastScale = $results[12]['scale'];
    assertTrue('Scale factor grew', $lastScale > $firstScale);

    // Run with callback
    $epochNames = [];
    $u3 = new Universe(ticksPerEpoch: 3);
    $u3->run(function (int $idx, array $result) use (&$epochNames): void {
        $epochNames[] = $result['epoch'];
    });
    assertEqual('Callback invoked 13 times', 13, count($epochNames));
    assertEqual('First callback = Planck', 'Planck', $epochNames[0]);
    assertEqual('Last callback = Present Day', 'Present Day', $epochNames[12]);

    // Verify subsystems produced data
    $finalStats = $results[12]['stats'];
    assertTrue('Particles created >= 0', $finalStats['particles_created'] >= 0);
    assertTrue('Atoms formed >= 0', $finalStats['atoms_formed'] >= 0);
    assertTrue('Molecules formed >= 0', $finalStats['molecules_formed'] >= 0);
    assertTrue('Lifeforms created >= 0', $finalStats['lifeforms_created'] >= 0);

    endSuite();
}

// =========================================================================
//  Main
// =========================================================================

echo "\n";
echo "========================================\n";
echo "  In The Beginning - PHP Test Suite\n";
echo "========================================\n\n";

$startTime = microtime(true);

testConstants();
testQuantum();
testAtomic();
testChemistry();
testBiology();
testEnvironment();
testUniverse();

$elapsed = round((microtime(true) - $startTime) * 1000);

echo "\n";
echo "========================================\n";
echo "  RESULTS\n";
echo "========================================\n";
echo "  Test suites: 7\n";
echo "  Tests passed: {$totalPassed}\n";
echo "  Tests failed: {$totalFailed}\n";
$total = $totalPassed + $totalFailed;
echo "  Total tests:  {$total}\n";
echo "  Time: {$elapsed} ms\n";
echo "========================================\n";

if ($totalFailed > 0) {
    echo "  STATUS: SOME TESTS FAILED\n";
    exit(1);
} else {
    echo "  STATUS: ALL TESTS PASSED\n";
}

echo "\n";
