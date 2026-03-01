package com.inthebeginning.simulator;

import java.util.ArrayList;
import java.util.List;

import static com.inthebeginning.simulator.Constants.*;

/**
 * An atom with protons, neutrons, and electron shells.
 * Models electron shell structure, ionization, bonding potential,
 * and the periodic table.
 */
public class Atom {

    /** An electron shell with quantum numbers. */
    public static class ElectronShell {
        public final int n;           // Principal quantum number
        public final int maxElectrons;
        public int electrons;

        public ElectronShell(int n, int maxElectrons, int electrons) {
            this.n = n;
            this.maxElectrons = maxElectrons;
            this.electrons = electrons;
        }

        public boolean isFull()  { return electrons >= maxElectrons; }
        public boolean isEmpty() { return electrons == 0; }

        public boolean addElectron() {
            if (!isFull()) { electrons++; return true; }
            return false;
        }

        public boolean removeElectron() {
            if (!isEmpty()) { electrons--; return true; }
            return false;
        }
    }

    private static int idCounter = 0;

    private final int atomId;
    private final int atomicNumber;
    private int massNumber;
    private int electronCount;
    private final double[] position;
    private final double[] velocity;
    private final List<ElectronShell> shells = new ArrayList<>();
    private final List<Integer> bonds = new ArrayList<>(); // IDs of bonded atoms
    private double ionizationEnergy;

    public Atom(int atomicNumber) {
        this(atomicNumber, 0, 0, new double[]{0,0,0});
    }

    public Atom(int atomicNumber, double[] position) {
        this(atomicNumber, 0, 0, position);
    }

    public Atom(int atomicNumber, int massNumber, int electronCount, double[] position) {
        this.atomId = ++idCounter;
        this.atomicNumber = atomicNumber;
        this.position = position.clone();
        this.velocity = new double[]{0, 0, 0};

        if (massNumber == 0) {
            this.massNumber = (atomicNumber == 1) ? 1 : atomicNumber * 2;
        } else {
            this.massNumber = massNumber;
        }

        this.electronCount = (electronCount == 0) ? atomicNumber : electronCount;

        buildShells();
        computeIonizationEnergy();
    }

    // Extra constructor for full control
    public Atom(int atomicNumber, int massNumber, double[] position, double[] velocity) {
        this.atomId = ++idCounter;
        this.atomicNumber = atomicNumber;
        this.position = position.clone();
        this.velocity = velocity.clone();
        this.massNumber = (massNumber == 0) ? ((atomicNumber == 1) ? 1 : atomicNumber * 2) : massNumber;
        this.electronCount = atomicNumber;
        buildShells();
        computeIonizationEnergy();
    }

    private void buildShells() {
        shells.clear();
        int remaining = electronCount;
        for (int i = 0; i < ELECTRON_SHELLS.length; i++) {
            if (remaining <= 0) break;
            int maxE = ELECTRON_SHELLS[i];
            int fill = Math.min(remaining, maxE);
            shells.add(new ElectronShell(i + 1, maxE, fill));
            remaining -= fill;
        }
    }

    private void computeIonizationEnergy() {
        if (shells.isEmpty() || shells.get(shells.size() - 1).isEmpty()) {
            ionizationEnergy = 0.0;
            return;
        }
        int n = shells.get(shells.size() - 1).n;
        int shielding = 0;
        for (int i = 0; i < shells.size() - 1; i++) {
            shielding += shells.get(i).electrons;
        }
        double zEff = atomicNumber - shielding;
        ionizationEnergy = 13.6 * zEff * zEff / (n * n);
    }

    // --- Accessors ---

    public int atomId()           { return atomId; }
    public int atomicNumber()     { return atomicNumber; }
    public int massNumber()       { return massNumber; }
    public int electronCount()    { return electronCount; }
    public double[] position()    { return position; }
    public double[] velocity()    { return velocity; }
    public List<ElectronShell> shells() { return shells; }
    public List<Integer> bonds()  { return bonds; }
    public double ionizationEnergy() { return ionizationEnergy; }

    public String symbol() {
        Constants.ElementInfo info = ELEMENTS.get(atomicNumber);
        return info != null ? info.symbol() : "E" + atomicNumber;
    }

    public String name() {
        Constants.ElementInfo info = ELEMENTS.get(atomicNumber);
        return info != null ? info.name() : "Element-" + atomicNumber;
    }

    public double electronegativity() {
        Constants.ElementInfo info = ELEMENTS.get(atomicNumber);
        return info != null ? info.electronegativity() : 1.0;
    }

    public int charge() {
        return atomicNumber - electronCount;
    }

    public int valenceElectrons() {
        if (shells.isEmpty()) return 0;
        return shells.get(shells.size() - 1).electrons;
    }

    public int needsElectrons() {
        if (shells.isEmpty()) return 0;
        ElectronShell last = shells.get(shells.size() - 1);
        return last.maxElectrons - last.electrons;
    }

    public boolean isNobleGas() {
        if (shells.isEmpty()) return false;
        return shells.get(shells.size() - 1).isFull();
    }

    public boolean isIon() {
        return charge() != 0;
    }

    // --- Operations ---

    public boolean ionize() {
        if (electronCount > 0) {
            electronCount--;
            buildShells();
            computeIonizationEnergy();
            return true;
        }
        return false;
    }

    public void captureElectron() {
        electronCount++;
        buildShells();
        computeIonizationEnergy();
    }

    public boolean canBondWith(Atom other) {
        if (isNobleGas() || other.isNobleGas()) return false;
        if (bonds.size() >= 4 || other.bonds.size() >= 4) return false;
        return true;
    }

    public String bondType(Atom other) {
        double diff = Math.abs(electronegativity() - other.electronegativity());
        if (diff > 1.7) return "ionic";
        else if (diff > 0.4) return "polar_covalent";
        else return "covalent";
    }

    public double bondEnergy(Atom other) {
        String btype = bondType(other);
        return switch (btype) {
            case "ionic" -> BOND_ENERGY_IONIC;
            case "polar_covalent" -> (BOND_ENERGY_COVALENT + BOND_ENERGY_IONIC) / 2;
            default -> BOND_ENERGY_COVALENT;
        };
    }

    public double distanceTo(Atom other) {
        double dx = position[0] - other.position[0];
        double dy = position[1] - other.position[1];
        double dz = position[2] - other.position[2];
        return Math.sqrt(dx*dx + dy*dy + dz*dz);
    }

    public String toCompact() {
        StringBuilder chargeStr = new StringBuilder();
        if (charge() > 0) chargeStr.append("+").append(charge());
        else if (charge() < 0) chargeStr.append(charge());

        StringBuilder shellStr = new StringBuilder();
        for (int i = 0; i < shells.size(); i++) {
            if (i > 0) shellStr.append(".");
            shellStr.append(shells.get(i).electrons);
        }
        return String.format("%s%d%s[%s]b%d",
                symbol(), massNumber, chargeStr, shellStr, bonds.size());
    }

    @Override
    public String toString() {
        return toCompact();
    }
}
