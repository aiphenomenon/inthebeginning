"""Tests for quantum physics simulation."""
import math
import os
import sys
import unittest
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.quantum import (
    WaveFunction, Particle, ParticleType, Spin, Color,
    EntangledPair, QuantumField, PARTICLE_MASSES, PARTICLE_CHARGES,
)
from simulator.constants import T_PLANCK, T_QUARK_HADRON, HBAR, PI, C


class TestWaveFunction(unittest.TestCase):
    def test_default(self):
        wf = WaveFunction()
        self.assertEqual(wf.amplitude, 1.0)
        self.assertEqual(wf.phase, 0.0)
        self.assertTrue(wf.coherent)

    def test_probability(self):
        wf = WaveFunction(amplitude=0.5)
        self.assertAlmostEqual(wf.probability, 0.25)

    def test_evolve(self):
        wf = WaveFunction(phase=0.0)
        wf.evolve(dt=1.0, energy=HBAR * PI)
        self.assertAlmostEqual(wf.phase, PI, places=5)

    def test_evolve_wraps(self):
        wf = WaveFunction(phase=0.0)
        wf.evolve(dt=1.0, energy=HBAR * 3 * PI)
        self.assertTrue(0 <= wf.phase < 2 * PI)

    def test_evolve_incoherent(self):
        wf = WaveFunction(coherent=False, phase=0.5)
        wf.evolve(dt=1.0, energy=10.0)
        self.assertEqual(wf.phase, 0.5)  # No change when incoherent

    def test_collapse_detected(self):
        random.seed(42)
        wf = WaveFunction(amplitude=1.0)
        result = wf.collapse()
        self.assertTrue(result)
        self.assertEqual(wf.amplitude, 1.0)
        self.assertFalse(wf.coherent)

    def test_collapse_zero_amplitude(self):
        wf = WaveFunction(amplitude=0.0)
        result = wf.collapse()
        self.assertFalse(result)
        self.assertEqual(wf.amplitude, 0.0)

    def test_superpose(self):
        wf1 = WaveFunction(amplitude=0.7, phase=0.0)
        wf2 = WaveFunction(amplitude=0.7, phase=0.0)
        combined = wf1.superpose(wf2)
        self.assertTrue(combined.coherent)
        self.assertGreater(combined.amplitude, 0)

    def test_superpose_destructive(self):
        wf1 = WaveFunction(amplitude=0.5, phase=0.0)
        wf2 = WaveFunction(amplitude=0.5, phase=PI)
        combined = wf1.superpose(wf2)
        self.assertLess(combined.amplitude, 0.5)

    def test_to_compact(self):
        wf = WaveFunction(amplitude=0.5, phase=1.0)
        compact = wf.to_compact()
        self.assertIn("0.500", compact)


class TestParticle(unittest.TestCase):
    def test_creation(self):
        p = Particle(particle_type=ParticleType.ELECTRON)
        self.assertEqual(p.particle_type, ParticleType.ELECTRON)
        self.assertGreater(p.particle_id, 0)

    def test_mass(self):
        e = Particle(particle_type=ParticleType.ELECTRON)
        p = Particle(particle_type=ParticleType.PROTON)
        self.assertGreater(p.mass, e.mass)

    def test_charge(self):
        e = Particle(particle_type=ParticleType.ELECTRON)
        self.assertEqual(e.charge, -1.0)
        p = Particle(particle_type=ParticleType.PROTON)
        self.assertEqual(p.charge, 1.0)
        n = Particle(particle_type=ParticleType.NEUTRON)
        self.assertEqual(n.charge, 0.0)

    def test_energy(self):
        p = Particle(
            particle_type=ParticleType.ELECTRON,
            momentum=[1.0, 0.0, 0.0],
        )
        self.assertGreater(p.energy, 0)

    def test_wavelength(self):
        p = Particle(
            particle_type=ParticleType.ELECTRON,
            momentum=[1.0, 0.0, 0.0],
        )
        self.assertGreater(p.wavelength, 0)
        self.assertNotEqual(p.wavelength, float("inf"))

    def test_wavelength_zero_momentum(self):
        p = Particle(particle_type=ParticleType.ELECTRON)
        self.assertEqual(p.wavelength, float("inf"))

    def test_to_compact(self):
        p = Particle(
            particle_type=ParticleType.PHOTON,
            position=[1.0, 2.0, 3.0],
        )
        compact = p.to_compact()
        self.assertIn("photon", compact)

    def test_quark_charges(self):
        up = Particle(particle_type=ParticleType.UP)
        self.assertAlmostEqual(up.charge, 2.0 / 3.0)
        down = Particle(particle_type=ParticleType.DOWN)
        self.assertAlmostEqual(down.charge, -1.0 / 3.0)

    def test_spin(self):
        p = Particle(particle_type=ParticleType.ELECTRON, spin=Spin.DOWN)
        self.assertEqual(p.spin, Spin.DOWN)
        self.assertEqual(p.spin.value, -0.5)

    def test_color(self):
        p = Particle(
            particle_type=ParticleType.UP,
            color=Color.RED,
        )
        self.assertEqual(p.color, Color.RED)

    def test_entanglement_id(self):
        p = Particle(
            particle_type=ParticleType.ELECTRON,
            entangled_with=42,
        )
        self.assertEqual(p.entangled_with, 42)


class TestEntangledPair(unittest.TestCase):
    def test_creation(self):
        a = Particle(particle_type=ParticleType.ELECTRON)
        b = Particle(particle_type=ParticleType.POSITRON)
        pair = EntangledPair(particle_a=a, particle_b=b)
        self.assertEqual(pair.bell_state, "phi+")

    def test_measure(self):
        random.seed(42)
        a = Particle(particle_type=ParticleType.ELECTRON)
        b = Particle(particle_type=ParticleType.POSITRON)
        pair = EntangledPair(particle_a=a, particle_b=b)
        spin_a = pair.measure_a()
        # After measurement, spins are anti-correlated
        if spin_a == Spin.UP:
            self.assertEqual(pair.particle_b.spin, Spin.DOWN)
        else:
            self.assertEqual(pair.particle_b.spin, Spin.UP)
        self.assertFalse(a.wave_fn.coherent)
        self.assertFalse(b.wave_fn.coherent)


class TestQuantumField(unittest.TestCase):
    def test_creation(self):
        qf = QuantumField()
        self.assertEqual(qf.temperature, T_PLANCK)
        self.assertEqual(len(qf.particles), 0)

    def test_pair_production_sufficient_energy(self):
        random.seed(42)
        qf = QuantumField()
        result = qf.pair_production(energy=5.0)
        self.assertIsNotNone(result)
        p, ap = result
        self.assertGreater(len(qf.particles), 0)
        self.assertEqual(qf.total_created, 2)

    def test_pair_production_insufficient_energy(self):
        qf = QuantumField()
        result = qf.pair_production(energy=0.001)
        self.assertIsNone(result)

    def test_pair_production_high_energy(self):
        random.seed(0)  # Seed to make quark production path hit
        qf = QuantumField()
        # Very high energy - may produce quark-antiquark
        for _ in range(20):
            qf.pair_production(energy=10000.0)
        self.assertGreater(qf.total_created, 0)

    def test_annihilate(self):
        qf = QuantumField()
        p1 = Particle(
            particle_type=ParticleType.ELECTRON,
            momentum=[1.0, 0.0, 0.0],
        )
        p2 = Particle(
            particle_type=ParticleType.POSITRON,
            momentum=[-1.0, 0.0, 0.0],
        )
        qf.particles.extend([p1, p2])
        energy = qf.annihilate(p1, p2)
        self.assertGreater(energy, 0)
        self.assertEqual(qf.total_annihilated, 2)
        # Should have photons now
        photons = [p for p in qf.particles
                   if p.particle_type == ParticleType.PHOTON]
        self.assertEqual(len(photons), 2)

    def test_quark_confinement_too_hot(self):
        qf = QuantumField(temperature=T_PLANCK)
        hadrons = qf.quark_confinement()
        self.assertEqual(len(hadrons), 0)

    def test_quark_confinement_cool(self):
        qf = QuantumField(temperature=T_QUARK_HADRON - 1)
        # Add quarks for a proton (uud)
        for _ in range(2):
            qf.particles.append(Particle(particle_type=ParticleType.UP))
        qf.particles.append(Particle(particle_type=ParticleType.DOWN))
        hadrons = qf.quark_confinement()
        self.assertEqual(len(hadrons), 1)
        self.assertEqual(hadrons[0].particle_type, ParticleType.PROTON)

    def test_quark_confinement_neutron(self):
        qf = QuantumField(temperature=T_QUARK_HADRON - 1)
        qf.particles.append(Particle(particle_type=ParticleType.UP))
        for _ in range(2):
            qf.particles.append(Particle(particle_type=ParticleType.DOWN))
        hadrons = qf.quark_confinement()
        self.assertEqual(len(hadrons), 1)
        self.assertEqual(hadrons[0].particle_type, ParticleType.NEUTRON)

    def test_vacuum_fluctuation(self):
        random.seed(42)
        qf = QuantumField(temperature=T_PLANCK)
        got_pair = False
        for _ in range(50):
            result = qf.vacuum_fluctuation()
            if result:
                got_pair = True
                break
        self.assertTrue(got_pair)

    def test_vacuum_fluctuation_cold(self):
        qf = QuantumField(temperature=0.001)
        results = [qf.vacuum_fluctuation() for _ in range(100)]
        # Most should be None at low temperature
        non_none = [r for r in results if r is not None]
        self.assertLess(len(non_none), 50)

    def test_decohere(self):
        qf = QuantumField(temperature=1000)
        p = Particle(particle_type=ParticleType.ELECTRON)
        self.assertTrue(p.wave_fn.coherent)
        # High coupling + temperature should decohere
        for _ in range(100):
            qf.decohere(p, environment_coupling=1.0)
        # Should have decohered by now
        self.assertFalse(p.wave_fn.coherent)

    def test_cool(self):
        qf = QuantumField(temperature=1000)
        qf.cool(0.5)
        self.assertEqual(qf.temperature, 500)

    def test_evolve(self):
        qf = QuantumField()
        p = Particle(
            particle_type=ParticleType.ELECTRON,
            position=[0.0, 0.0, 0.0],
            momentum=[1.0, 0.0, 0.0],
        )
        qf.particles.append(p)
        qf.evolve(dt=1.0)
        self.assertNotEqual(p.position[0], 0.0)

    def test_evolve_massless(self):
        qf = QuantumField()
        p = Particle(
            particle_type=ParticleType.PHOTON,
            position=[0.0, 0.0, 0.0],
            momentum=[1.0, 0.0, 0.0],
        )
        qf.particles.append(p)
        qf.evolve(dt=1.0)
        self.assertGreater(p.position[0], 0)

    def test_particle_count(self):
        qf = QuantumField()
        qf.particles.append(Particle(particle_type=ParticleType.ELECTRON))
        qf.particles.append(Particle(particle_type=ParticleType.ELECTRON))
        qf.particles.append(Particle(particle_type=ParticleType.PROTON))
        counts = qf.particle_count()
        self.assertEqual(counts["electron"], 2)
        self.assertEqual(counts["proton"], 1)

    def test_total_energy(self):
        qf = QuantumField()
        qf.particles.append(Particle(
            particle_type=ParticleType.ELECTRON,
            momentum=[1.0, 0.0, 0.0],
        ))
        self.assertGreater(qf.total_energy(), 0)

    def test_to_compact(self):
        qf = QuantumField(temperature=1000)
        compact = qf.to_compact()
        self.assertIn("QF[", compact)
        self.assertIn("T=", compact)


class TestParticleTypes(unittest.TestCase):
    def test_all_types_have_mass(self):
        for pt in PARTICLE_MASSES:
            self.assertIsInstance(PARTICLE_MASSES[pt], (int, float))

    def test_all_types_have_charge(self):
        for pt in PARTICLE_CHARGES:
            self.assertIsInstance(PARTICLE_CHARGES[pt], (int, float))

    def test_photon_massless(self):
        self.assertEqual(PARTICLE_MASSES[ParticleType.PHOTON], 0.0)

    def test_proton_heavier_than_electron(self):
        self.assertGreater(
            PARTICLE_MASSES[ParticleType.PROTON],
            PARTICLE_MASSES[ParticleType.ELECTRON],
        )


if __name__ == "__main__":
    unittest.main()
