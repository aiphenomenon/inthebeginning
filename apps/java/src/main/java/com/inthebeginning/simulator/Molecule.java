package com.inthebeginning.simulator;

import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A molecule: a collection of bonded atoms.
 * Tracks formula, molecular weight, organic classification, and functional groups.
 */
public class Molecule {

    private static final AtomicInteger idCounter = new AtomicInteger(0);

    private final int moleculeId;
    private final List<Atom> atoms;
    private String name;
    private String formula;
    private double energy;
    private final double[] position;
    private boolean organic;
    private final List<String> functionalGroups;

    public Molecule(List<Atom> atoms, String name, double[] position) {
        this(atoms, name, position, false, new ArrayList<>());
    }

    public Molecule(List<Atom> atoms, String name, double[] position,
                    boolean organic, List<String> functionalGroups) {
        this.moleculeId = idCounter.incrementAndGet();
        this.atoms = new ArrayList<>(atoms);
        this.name = name;
        this.position = position.clone();
        this.organic = organic;
        this.functionalGroups = new ArrayList<>(functionalGroups);
        this.energy = 0.0;

        if (this.name == null || this.name.isEmpty()) {
            computeFormula();
        } else {
            computeFormula();
        }
    }

    private void computeFormula() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (Atom atom : atoms) {
            counts.merge(atom.symbol(), 1, Integer::sum);
        }

        StringBuilder parts = new StringBuilder();
        // Standard chemistry ordering: C, H, then alphabetical
        for (String sym : new String[]{"C", "H"}) {
            Integer n = counts.remove(sym);
            if (n != null) {
                parts.append(sym);
                if (n > 1) parts.append(n);
            }
        }
        counts.entrySet().stream().sorted(Map.Entry.comparingByKey())
                .forEach(e -> {
                    parts.append(e.getKey());
                    if (e.getValue() > 1) parts.append(e.getValue());
                });
        this.formula = parts.toString();

        boolean hasC = atoms.stream().anyMatch(a -> a.atomicNumber() == 6);
        boolean hasH = atoms.stream().anyMatch(a -> a.atomicNumber() == 1);
        this.organic = hasC && hasH;
    }

    // --- Accessors ---

    public int moleculeId()              { return moleculeId; }
    public List<Atom> atoms()            { return atoms; }
    public String name()                 { return name; }
    public String formula()              { return formula; }
    public double energy()               { return energy; }
    public double[] position()           { return position; }
    public boolean isOrganic()           { return organic; }
    public List<String> functionalGroups() { return functionalGroups; }

    public double molecularWeight() {
        return atoms.stream().mapToInt(Atom::massNumber).sum();
    }

    public int atomCount() {
        return atoms.size();
    }

    public String toCompact() {
        String label = (name != null && !name.isEmpty()) ? name : formula;
        return String.format("%s(mw=%.0f)", label, molecularWeight());
    }

    @Override
    public String toString() {
        return toCompact();
    }
}
