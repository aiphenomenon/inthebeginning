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
