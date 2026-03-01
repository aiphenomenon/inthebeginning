package com.inthebeginning.simulator;

import java.util.*;
import java.util.stream.Collectors;

import static com.inthebeginning.simulator.Constants.*;

/**
 * Manages molecular assembly and chemical reactions.
 * Forms water, methane, ammonia, amino acids, and nucleotides from available atoms.
 */
public class ChemicalSystem {

    private final AtomicSystem atomic;
    private final List<Molecule> molecules = new ArrayList<>();
    private int reactionsOccurred = 0;
    private int waterCount = 0;
    private int aminoAcidCount = 0;
    private int nucleotideCount = 0;
    private final Random rng;

    public ChemicalSystem(AtomicSystem atomic, Random rng) {
        this.atomic = atomic;
        this.rng = rng;
    }

    // --- Accessors ---

    public List<Molecule> getMolecules()    { return molecules; }
    public int getWaterCount()              { return waterCount; }
    public int getAminoAcidCount()          { return aminoAcidCount; }
    public int getNucleotideCount()         { return nucleotideCount; }
    public int getReactionsOccurred()       { return reactionsOccurred; }

    // --- Molecule formation ---

    /** Form water molecules: 2H + O -> H2O */
    public List<Molecule> formWater() {
        List<Molecule> waters = new ArrayList<>();
        List<Atom> hydrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 1 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> oxygens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 8 && a.bonds().size() < 2)
                .collect(Collectors.toCollection(ArrayList::new));

        while (hydrogens.size() >= 2 && !oxygens.isEmpty()) {
            Atom h1 = hydrogens.remove(hydrogens.size() - 1);
            Atom h2 = hydrogens.remove(hydrogens.size() - 1);
            Atom o = oxygens.remove(oxygens.size() - 1);

            Molecule water = new Molecule(List.of(h1, h2, o), "water", o.position());
            waters.add(water);
            molecules.add(water);
            waterCount++;

            h1.bonds().add(o.atomId());
            h2.bonds().add(o.atomId());
            o.bonds().add(h1.atomId());
            o.bonds().add(h2.atomId());
        }
        return waters;
    }

    /** Form methane: C + 4H -> CH4 */
    public List<Molecule> formMethane() {
        List<Molecule> methanes = new ArrayList<>();
        List<Atom> carbons = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 6 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> hydrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 1 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));

        while (!carbons.isEmpty() && hydrogens.size() >= 4) {
            Atom c = carbons.remove(carbons.size() - 1);
            List<Atom> hs = new ArrayList<>();
            for (int i = 0; i < 4; i++) hs.add(hydrogens.remove(hydrogens.size() - 1));

            List<Atom> allAtoms = new ArrayList<>();
            allAtoms.add(c);
            allAtoms.addAll(hs);
            Molecule methane = new Molecule(allAtoms, "methane", c.position());
            methanes.add(methane);
            molecules.add(methane);

            for (Atom h : hs) {
                c.bonds().add(h.atomId());
                h.bonds().add(c.atomId());
            }
        }
        return methanes;
    }

    /** Form ammonia: N + 3H -> NH3 */
    public List<Molecule> formAmmonia() {
        List<Molecule> ammonias = new ArrayList<>();
        List<Atom> nitrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 7 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> hydrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 1 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));

        while (!nitrogens.isEmpty() && hydrogens.size() >= 3) {
            Atom n = nitrogens.remove(nitrogens.size() - 1);
            List<Atom> hs = new ArrayList<>();
            for (int i = 0; i < 3; i++) hs.add(hydrogens.remove(hydrogens.size() - 1));

            List<Atom> allAtoms = new ArrayList<>();
            allAtoms.add(n);
            allAtoms.addAll(hs);
            Molecule ammonia = new Molecule(allAtoms, "ammonia", n.position());
            ammonias.add(ammonia);
            molecules.add(ammonia);

            for (Atom h : hs) {
                n.bonds().add(h.atomId());
                h.bonds().add(n.atomId());
            }
        }
        return ammonias;
    }

    /**
     * Form an amino acid from available atoms.
     * Simplified: requires 2C + 5H + 2O + 1N minimum (glycine-like).
     */
    public Molecule formAminoAcid(String aaType) {
        List<Atom> carbons = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 6 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> hydrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 1 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> oxygens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 8 && a.bonds().size() < 2)
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> nitrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 7 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));

        if (carbons.size() < 2 || hydrogens.size() < 5 ||
            oxygens.size() < 2 || nitrogens.size() < 1) {
            return null;
        }

        List<Atom> atoms = new ArrayList<>();
        for (int i = 0; i < 2; i++) atoms.add(carbons.remove(carbons.size() - 1));
        for (int i = 0; i < 5; i++) atoms.add(hydrogens.remove(hydrogens.size() - 1));
        for (int i = 0; i < 2; i++) atoms.add(oxygens.remove(oxygens.size() - 1));
        atoms.add(nitrogens.remove(nitrogens.size() - 1));

        Molecule aa = new Molecule(atoms, aaType, atoms.get(0).position(),
                true, List.of("amino", "carboxyl"));
        molecules.add(aa);
        aminoAcidCount++;

        // Form internal bonds
        Atom first = atoms.get(0);
        for (int i = 1; i < atoms.size(); i++) {
            first.bonds().add(atoms.get(i).atomId());
            atoms.get(i).bonds().add(first.atomId());
        }

        return aa;
    }

    /**
     * Form a nucleotide (sugar + phosphate + base).
     * Simplified: requires C5 + H8 + O4 + N2.
     */
    public Molecule formNucleotide(String base) {
        List<Atom> carbons = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 6 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> hydrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 1 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> oxygens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 8 && a.bonds().size() < 2)
                .collect(Collectors.toCollection(ArrayList::new));
        List<Atom> nitrogens = atomic.getAtoms().stream()
                .filter(a -> a.atomicNumber() == 7 && a.bonds().isEmpty())
                .collect(Collectors.toCollection(ArrayList::new));

        if (carbons.size() < 5 || hydrogens.size() < 8 ||
            oxygens.size() < 4 || nitrogens.size() < 2) {
            return null;
        }

        List<Atom> atoms = new ArrayList<>();
        for (int i = 0; i < 5; i++) atoms.add(carbons.remove(carbons.size() - 1));
        for (int i = 0; i < 8; i++) atoms.add(hydrogens.remove(hydrogens.size() - 1));
        for (int i = 0; i < 4; i++) atoms.add(oxygens.remove(oxygens.size() - 1));
        for (int i = 0; i < 2; i++) atoms.add(nitrogens.remove(nitrogens.size() - 1));

        Molecule nuc = new Molecule(atoms, "nucleotide-" + base, atoms.get(0).position(),
                true, List.of("sugar", "phosphate", "base"));
        molecules.add(nuc);
        nucleotideCount++;

        Atom first = atoms.get(0);
        for (int i = 1; i < atoms.size(); i++) {
            first.bonds().add(atoms.get(i).atomId());
            atoms.get(i).bonds().add(first.atomId());
        }

        return nuc;
    }

    /**
     * Run catalyzed reactions to form complex molecules.
     * Activation energy is lower with catalyst.
     */
    public int catalyzedReaction(double temperature, boolean catalystPresent) {
        int formed = 0;
        double eaFactor = catalystPresent ? 0.3 : 1.0;
        double thermal = K_B * temperature;

        // Try to form amino acids
        if (thermal > 0 && atomic.getAtoms().size() > 10) {
            double aaProb = Math.exp(-5.0 * eaFactor / (thermal + 1e-20));
            if (rng.nextDouble() < aaProb) {
                String aaType = AMINO_ACIDS[rng.nextInt(AMINO_ACIDS.length)];
                if (formAminoAcid(aaType) != null) {
                    formed++;
                    reactionsOccurred++;
                }
            }
        }

        // Try to form nucleotides
        if (thermal > 0 && atomic.getAtoms().size() > 19) {
            double nucProb = Math.exp(-8.0 * eaFactor / (thermal + 1e-20));
            if (rng.nextDouble() < nucProb) {
                String[] bases = {"A", "T", "G", "C"};
                String base = bases[rng.nextInt(bases.length)];
                if (formNucleotide(base) != null) {
                    formed++;
                    reactionsOccurred++;
                }
            }
        }

        return formed;
    }

    /** Count molecules by type. */
    public Map<String, Integer> moleculeCensus() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (Molecule m : molecules) {
            String key = (m.name() != null && !m.name().isEmpty()) ? m.name() : m.formula();
            counts.merge(key, 1, Integer::sum);
        }
        return counts;
    }

    public String toCompact() {
        Map<String, Integer> counts = moleculeCensus();
        StringBuilder sb = new StringBuilder();
        counts.entrySet().stream().sorted(Map.Entry.comparingByKey())
                .forEach(e -> {
                    if (sb.length() > 0) sb.append(",");
                    sb.append(e.getKey()).append(":").append(e.getValue());
                });
        return String.format("CS[mol=%d H2O=%d aa=%d nuc=%d rxn=%d %s]",
                molecules.size(), waterCount, aminoAcidCount,
                nucleotideCount, reactionsOccurred, sb);
    }
}
