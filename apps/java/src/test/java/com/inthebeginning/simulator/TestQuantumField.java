package com.inthebeginning.simulator;

import java.util.*;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Tests for WaveFunction behavior (via Particle), Particle properties,
 * and QuantumField operations (pair production, annihilation, confinement).
 */
public class TestQuantumField {

    private static int passed = 0;
    private static int failed = 0;

    private static void assertEquals(String label, Object expected, Object actual) {
        if (expected.equals(actual)) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected " + expected + " but got " + actual);
        }
    }

    private static void assertTrue(String label, boolean condition) {
        if (condition) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label);
        }
    }

    private static void assertApprox(String label, double expected, double actual, double tolerance) {
        if (Math.abs(expected - actual) < tolerance) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected ~" + expected + " but got " + actual);
        }
    }

    private static void assertNotNull(String label, Object obj) {
        if (obj != null) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - was null");
        }
    }

    private static void assertNull(String label, Object obj) {
        if (obj == null) {
            passed++;
        } else {
            failed++;
            System.out.println("    FAIL: " + label + " - expected null but was " + obj);
        }
    }

    public static int[] runAll() {
        passed = 0;
        failed = 0;

        System.out.println("  [TestQuantumField]");

        testParticleTypeProperties();
        testParticleCreation();
        testParticleEnergy();
        testParticleWavelength();
        testParticleWaveFunction();
        testParticleWaveFunctionCollapse();
        testParticleMovement();
        testParticleEntanglement();
        testQuantumFieldCreation();
        testPairProduction();
        testPairProductionInsufficientEnergy();
        testAnnihilation();
        testQuarkConfinement();
        testQuarkConfinementHighTemp();
        testVacuumFluctuation();
        testFieldCooling();
        testFieldEvolution();
        testParticleCount();
        testTotalEnergy();
        testSpinValue();
        testParticleSetType();
        testParticleSetSpin();
        testParticleSetColor();
        testParticleSetWfCoherent();
        testParticleToCompact();
        testParticleToString();
        testQuantumFieldSetTemperature();
        testQuantumFieldToCompact();

        System.out.println("    " + passed + " passed, " + failed + " failed");
        return new int[]{passed, failed};
    }

    private static void testParticleTypeProperties() {
        assertEquals("Electron label", "electron", ParticleType.ELECTRON.label());
        assertApprox("Electron mass", M_ELECTRON, ParticleType.ELECTRON.mass(), 1e-10);
        assertApprox("Electron charge", -1.0, ParticleType.ELECTRON.charge(), 1e-10);

        assertEquals("Proton label", "proton", ParticleType.PROTON.label());
        assertApprox("Proton mass", M_PROTON, ParticleType.PROTON.mass(), 1e-10);
        assertApprox("Proton charge", 1.0, ParticleType.PROTON.charge(), 1e-10);

        assertEquals("Photon label", "photon", ParticleType.PHOTON.label());
        assertApprox("Photon mass", 0.0, ParticleType.PHOTON.mass(), 1e-10);
        assertApprox("Photon charge", 0.0, ParticleType.PHOTON.charge(), 1e-10);

        assertApprox("Up quark charge", 2.0 / 3.0, ParticleType.UP.charge(), 1e-10);
        assertApprox("Down quark charge", -1.0 / 3.0, ParticleType.DOWN.charge(), 1e-10);
    }

    private static void testParticleCreation() {
        Particle p = new Particle(ParticleType.ELECTRON);
        assertEquals("Default type", ParticleType.ELECTRON, p.type());
        assertEquals("Default spin", Particle.Spin.UP, p.spin());
        assertApprox("Default position x", 0.0, p.position()[0], 1e-10);
        assertApprox("Default momentum x", 0.0, p.momentum()[0], 1e-10);
        assertTrue("Particle ID > 0", p.particleId() > 0);

        Particle p2 = new Particle(ParticleType.PROTON,
                new double[]{1.0, 2.0, 3.0}, new double[]{4.0, 5.0, 6.0});
        assertApprox("Custom position x", 1.0, p2.position()[0], 1e-10);
        assertApprox("Custom momentum z", 6.0, p2.momentum()[2], 1e-10);
    }

    private static void testParticleEnergy() {
        // Particle at rest: E = mc^2
        Particle p = new Particle(ParticleType.ELECTRON);
        assertApprox("Electron rest energy", M_ELECTRON * C * C, p.energy(), 1e-10);

        // Photon with momentum
        Particle photon = new Particle(ParticleType.PHOTON,
                new double[]{0, 0, 0}, new double[]{1.0, 0, 0});
        assertApprox("Photon energy E=pc", 1.0 * C, photon.energy(), 1e-10);
    }

    private static void testParticleWavelength() {
        // Particle at rest: infinite wavelength
        Particle p = new Particle(ParticleType.ELECTRON);
        assertTrue("Zero-momentum wavelength is infinite", Double.isInfinite(p.wavelength()));

        // Particle with momentum
        Particle p2 = new Particle(ParticleType.ELECTRON,
                new double[]{0, 0, 0}, new double[]{1.0, 0, 0});
        double expected = 2 * PI * HBAR / 1.0;
        assertApprox("de Broglie wavelength", expected, p2.wavelength(), 1e-10);
    }

    private static void testParticleWaveFunction() {
        Particle p = new Particle(ParticleType.ELECTRON);
        assertApprox("Initial wf amplitude", 1.0, p.wfAmplitude(), 1e-10);
        assertApprox("Initial wf phase", 0.0, p.wfPhase(), 1e-10);
        assertTrue("Initially coherent", p.wfCoherent());
        assertApprox("Initial probability", 1.0, p.wfProbability(), 1e-10);

        // Evolve wave function
        p.evolveWaveFunction(1.0, 1.0);
        assertTrue("Phase changed after evolution", p.wfPhase() != 0.0);
        assertTrue("Still coherent after evolution", p.wfCoherent());
    }

    private static void testParticleWaveFunctionCollapse() {
        Random rng = new Random(42);
        Particle p = new Particle(ParticleType.ELECTRON);

        // With amplitude 1.0, probability is 1.0, so collapse should always detect
        boolean result = p.collapseWaveFunction(rng);
        assertTrue("Collapse with probability 1 should detect", result);
        assertApprox("Amplitude after collapse", 1.0, p.wfAmplitude(), 1e-10);
        assertTrue("Not coherent after collapse", !p.wfCoherent());
    }

    private static void testParticleMovement() {
        Particle p = new Particle(ParticleType.ELECTRON,
                new double[]{0, 0, 0}, new double[]{1.0, 0, 0});
        double dt = 1.0;
        p.updatePosition(dt);
        // position = momentum / mass * dt = 1.0 / 1.0 * 1.0 = 1.0
        assertApprox("Position after movement", 1.0, p.position()[0], 1e-10);
    }

    private static void testParticleEntanglement() {
        Particle p1 = new Particle(ParticleType.ELECTRON);
        Particle p2 = new Particle(ParticleType.POSITRON);
        assertEquals("Not entangled initially", -1, p1.entangledWith());
        p1.setEntangledWith(p2.particleId());
        p2.setEntangledWith(p1.particleId());
        assertEquals("p1 entangled with p2", p2.particleId(), p1.entangledWith());
        assertEquals("p2 entangled with p1", p1.particleId(), p2.entangledWith());
    }

    private static void testQuantumFieldCreation() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);
        assertApprox("Initial temperature", T_PLANCK, qf.getTemperature(), 1e-3);
        assertEquals("No particles initially", 0, qf.getParticles().size());
        assertApprox("No vacuum energy initially", 0.0, qf.getVacuumEnergy(), 1e-10);
    }

    private static void testPairProduction() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        double energy = 10.0; // well above 2 * M_ELECTRON
        Particle[] pair = qf.pairProduction(energy);
        assertNotNull("Pair produced", pair);
        assertEquals("Pair has 2 particles", 2, pair.length);
        assertEquals("Field has 2 particles", 2, qf.getParticles().size());
        assertEquals("2 total created", 2, qf.getTotalCreated());

        // Particles should be entangled with each other
        assertEquals("Pair entangled", pair[1].particleId(), pair[0].entangledWith());
    }

    private static void testPairProductionInsufficientEnergy() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        double energy = 0.5; // below 2 * M_ELECTRON = 2.0
        Particle[] pair = qf.pairProduction(energy);
        assertNull("No pair with insufficient energy", pair);
        assertEquals("No particles created", 0, qf.getParticles().size());
    }

    private static void testAnnihilation() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        Particle[] pair = qf.pairProduction(10.0);
        assertNotNull("Pair created for annihilation", pair);
        int sizeBeforeAnnihilation = qf.getParticles().size();

        double releasedEnergy = qf.annihilate(pair[0], pair[1]);
        assertTrue("Energy released > 0", releasedEnergy > 0);
        assertEquals("2 total annihilated", 2, qf.getTotalAnnihilated());
        // After annihilation, original pair removed, 2 photons added
        assertEquals("Photons created after annihilation", 2, qf.getParticles().size());
    }

    private static void testQuarkConfinement() {
        Random rng = new Random(42);
        // Temperature below T_QUARK_HADRON for confinement to trigger
        QuantumField qf = new QuantumField(T_QUARK_HADRON * 0.5, rng);

        // Manually add quarks: 2 up + 1 down = 1 proton
        Particle u1 = new Particle(ParticleType.UP, new double[]{0, 0, 0}, new double[]{1, 0, 0});
        Particle u2 = new Particle(ParticleType.UP, new double[]{0, 0, 0}, new double[]{0, 1, 0});
        Particle d1 = new Particle(ParticleType.DOWN, new double[]{0, 0, 0}, new double[]{0, 0, 1});
        qf.getParticles().add(u1);
        qf.getParticles().add(u2);
        qf.getParticles().add(d1);

        List<Particle> hadrons = qf.quarkConfinement();
        assertTrue("At least 1 hadron formed", hadrons.size() >= 1);
        assertEquals("Proton formed", ParticleType.PROTON, hadrons.get(0).type());
    }

    private static void testQuarkConfinementHighTemp() {
        Random rng = new Random(42);
        // Temperature above confinement threshold
        QuantumField qf = new QuantumField(T_QUARK_HADRON * 2, rng);

        Particle u1 = new Particle(ParticleType.UP);
        Particle u2 = new Particle(ParticleType.UP);
        Particle d1 = new Particle(ParticleType.DOWN);
        qf.getParticles().add(u1);
        qf.getParticles().add(u2);
        qf.getParticles().add(d1);

        List<Particle> hadrons = qf.quarkConfinement();
        assertEquals("No confinement at high temperature", 0, hadrons.size());
    }

    private static void testVacuumFluctuation() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        // Run many fluctuations - at T_PLANCK, probability is 0.5, so some should produce pairs
        int produced = 0;
        for (int i = 0; i < 100; i++) {
            if (qf.vacuumFluctuation() != null) {
                produced++;
            }
        }
        assertTrue("At least one vacuum fluctuation produced particles", produced > 0);
    }

    private static void testFieldCooling() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(1000.0, rng);
        qf.cool(0.5);
        assertApprox("Temperature halved", 500.0, qf.getTemperature(), 1e-10);
    }

    private static void testFieldEvolution() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(1000.0, rng);

        Particle p = new Particle(ParticleType.ELECTRON,
                new double[]{0, 0, 0}, new double[]{1.0, 0, 0});
        qf.getParticles().add(p);

        double posBefore = p.position()[0];
        qf.evolve(1.0);
        assertTrue("Position changed after evolve", p.position()[0] != posBefore);
    }

    private static void testParticleCount() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        qf.getParticles().add(new Particle(ParticleType.ELECTRON));
        qf.getParticles().add(new Particle(ParticleType.ELECTRON));
        qf.getParticles().add(new Particle(ParticleType.PROTON));

        Map<String, Integer> counts = qf.particleCount();
        assertEquals("2 electrons", Integer.valueOf(2), counts.get("electron"));
        assertEquals("1 proton", Integer.valueOf(1), counts.get("proton"));
    }

    private static void testTotalEnergy() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(T_PLANCK, rng);

        assertApprox("Empty field energy = 0", 0.0, qf.totalEnergy(), 1e-10);

        Particle p = new Particle(ParticleType.ELECTRON);
        qf.getParticles().add(p);
        assertTrue("Field energy > 0 with particle", qf.totalEnergy() > 0);
    }

    private static void testSpinValue() {
        assertApprox("Spin UP value = +0.5", 0.5, Particle.Spin.UP.value(), 1e-10);
        assertApprox("Spin DOWN value = -0.5", -0.5, Particle.Spin.DOWN.value(), 1e-10);
    }

    private static void testParticleSetType() {
        Particle p = new Particle(ParticleType.ELECTRON);
        assertEquals("Initial type is ELECTRON", ParticleType.ELECTRON, p.type());
        p.setType(ParticleType.PROTON);
        assertEquals("Type changed to PROTON", ParticleType.PROTON, p.type());
        assertApprox("Mass reflects PROTON", M_PROTON, p.mass(), 1e-10);
    }

    private static void testParticleSetSpin() {
        Particle p = new Particle(ParticleType.ELECTRON);
        assertEquals("Default spin is UP", Particle.Spin.UP, p.spin());
        p.setSpin(Particle.Spin.DOWN);
        assertEquals("Spin changed to DOWN", Particle.Spin.DOWN, p.spin());
    }

    private static void testParticleSetColor() {
        Particle p = new Particle(ParticleType.UP);
        assertNull("Default color is null", p.color());
        p.setColor(Particle.Color.RED);
        assertEquals("Color set to RED", Particle.Color.RED, p.color());
        p.setColor(Particle.Color.ANTI_GREEN);
        assertEquals("Color changed to ANTI_GREEN", Particle.Color.ANTI_GREEN, p.color());
    }

    private static void testParticleSetWfCoherent() {
        Particle p = new Particle(ParticleType.ELECTRON);
        assertTrue("Initially coherent", p.wfCoherent());
        p.setWfCoherent(false);
        assertTrue("Set to not coherent", !p.wfCoherent());
        p.setWfCoherent(true);
        assertTrue("Set back to coherent", p.wfCoherent());
    }

    private static void testParticleToCompact() {
        Particle p = new Particle(ParticleType.ELECTRON,
                new double[]{1.0, 2.0, 3.0}, new double[]{0, 0, 0},
                Particle.Spin.UP, null);
        String compact = p.toCompact();
        assertTrue("Compact contains type label", compact.contains("electron"));
        assertTrue("Compact contains position", compact.contains("1.0"));
        assertTrue("Compact contains spin", compact.contains("0.5"));
    }

    private static void testParticleToString() {
        Particle p = new Particle(ParticleType.PROTON,
                new double[]{0, 0, 0}, new double[]{1, 0, 0},
                Particle.Spin.DOWN, null);
        String str = p.toString();
        String compact = p.toCompact();
        assertEquals("toString equals toCompact", compact, str);
    }

    private static void testQuantumFieldSetTemperature() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(1000.0, rng);
        assertApprox("Initial temperature", 1000.0, qf.getTemperature(), 1e-10);
        qf.setTemperature(500.0);
        assertApprox("Temperature after set", 500.0, qf.getTemperature(), 1e-10);
        qf.setTemperature(0.0);
        assertApprox("Temperature set to 0", 0.0, qf.getTemperature(), 1e-10);
    }

    private static void testQuantumFieldToCompact() {
        Random rng = new Random(42);
        QuantumField qf = new QuantumField(1000.0, rng);
        qf.getParticles().add(new Particle(ParticleType.ELECTRON));
        qf.getParticles().add(new Particle(ParticleType.PROTON));

        String compact = qf.toCompact();
        assertTrue("Compact contains QF", compact.contains("QF"));
        assertTrue("Compact contains T=", compact.contains("T="));
        assertTrue("Compact contains E=", compact.contains("E="));
        assertTrue("Compact contains n=", compact.contains("n=2"));
    }
}
