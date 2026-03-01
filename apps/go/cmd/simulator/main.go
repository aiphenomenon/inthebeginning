package main

import (
	"fmt"
	"math"
	"strings"
	"time"

	"inthebeginning/go-sse/simulator"
)

const (
	bannerWidth = 72
	barWidth    = 40
)

func main() {
	printBanner()

	seed := time.Now().UnixNano()
	universe := simulator.NewUniverse(seed)

	fmt.Printf("  Seed: %d\n\n", seed)

	startTime := time.Now()

	epochIndex := 0
	totalEpochs := len(simulator.Epochs)

	universe.OnEpochComplete = func(result simulator.EpochResult) {
		epochIndex++
		printEpochResult(epochIndex, totalEpochs, result, simulator.Epochs[epochIndex-1])
	}

	universe.Run()

	elapsed := time.Since(startTime)

	printDivider()
	printSummary(universe, elapsed)
	printFooter()
}

// printBanner prints the opening ASCII art banner.
func printBanner() {
	fmt.Println()
	fmt.Println(line('='))
	fmt.Println(center("IN THE BEGINNING"))
	fmt.Println(center("A Cosmic Evolution Simulator"))
	fmt.Println(line('-'))
	fmt.Println(center("From the Planck epoch to the emergence of life"))
	fmt.Println(center("13.8 billion years in the blink of an eye"))
	fmt.Println(line('='))
	fmt.Println()
}

// printEpochResult prints a single epoch's results with a progress bar.
func printEpochResult(index, total int, result simulator.EpochResult, epoch simulator.EpochInfo) {
	// Progress bar
	progress := float64(index) / float64(total)
	filled := int(math.Round(progress * float64(barWidth)))
	bar := strings.Repeat(epoch.Symbol, filled) + strings.Repeat(" ", barWidth-filled)

	// Epoch header
	fmt.Printf("  [%2d/%2d] %-18s [%s] %3.0f%%\n",
		index, total, epoch.Name, bar, progress*100)

	// Description
	fmt.Printf("         %s\n", epoch.Description)

	// Stats line
	stats := fmt.Sprintf("         T=%.2e K", result.Temperature)
	if result.ParticleCount > 0 {
		stats += fmt.Sprintf(" | particles: %d", result.ParticleCount)
	}
	if result.AtomCount > 0 {
		stats += fmt.Sprintf(" | atoms: %d", result.AtomCount)
	}
	if result.MoleculeCount > 0 {
		stats += fmt.Sprintf(" | molecules: %d", result.MoleculeCount)
	}
	if result.CellCount > 0 {
		stats += fmt.Sprintf(" | cells: %d", result.CellCount)
	}
	fmt.Println(stats)

	// Events
	for _, event := range result.Events {
		fmt.Printf("           >> %s\n", event)
	}

	fmt.Println()
}

// printSummary prints the final simulation summary.
func printSummary(u *simulator.Universe, elapsed time.Duration) {
	fmt.Println()
	fmt.Println(center("SIMULATION COMPLETE"))
	fmt.Println(line('-'))
	fmt.Println()

	fmt.Println("  --- Final State of the Universe ---")
	fmt.Println()
	fmt.Printf("  %-30s %d ticks\n", "Universe age:", u.Age)
	fmt.Printf("  %-30s %.3f s\n", "Wall-clock time:", elapsed.Seconds())
	fmt.Println()

	// Quantum field
	fmt.Println("  [Quantum Field]")
	fmt.Printf("    Particles remaining:    %d\n", len(u.Field.Particles))
	fmt.Printf("    Total created:          %d\n", u.Field.TotalCreated)
	fmt.Printf("    Total annihilated:      %d\n", u.Field.TotalAnnihilated)
	fmt.Printf("    Total field energy:     %.2f SU\n", u.Field.TotalEnergy())
	counts := u.Field.ParticleCount()
	if len(counts) > 0 {
		fmt.Printf("    Particle census:        ")
		first := true
		for name, count := range counts {
			if !first {
				fmt.Printf(", ")
			}
			fmt.Printf("%s=%d", name, count)
			first = false
		}
		fmt.Println()
	}
	fmt.Println()

	// Atoms
	fmt.Println("  [Atomic System]")
	fmt.Printf("    Total atoms:            %d\n", len(u.Atoms.Atoms))
	fmt.Printf("    Bonds formed:           %d\n", u.Atoms.BondsFormed)
	elemCounts := u.Atoms.ElementCounts()
	if len(elemCounts) > 0 {
		fmt.Printf("    Element census:         ")
		first := true
		for sym, count := range elemCounts {
			if !first {
				fmt.Printf(", ")
			}
			fmt.Printf("%s=%d", sym, count)
			first = false
		}
		fmt.Println()
	}
	fmt.Println()

	// Chemistry
	fmt.Println("  [Chemical System]")
	fmt.Printf("    Total molecules:        %d\n", len(u.Chemistry.Molecules))
	fmt.Printf("    Water molecules:        %d\n", u.Chemistry.WaterCount)
	fmt.Printf("    Amino acids:            %d\n", u.Chemistry.AminoAcidCount)
	fmt.Printf("    Nucleotides:            %d\n", u.Chemistry.NucleotideCount)
	fmt.Printf("    Reactions occurred:      %d\n", u.Chemistry.ReactionsOccurred)
	fmt.Println()

	// Biology
	if u.Biosphere != nil {
		fmt.Println("  [Biosphere]")
		fmt.Printf("    Living cells:           %d\n", len(u.Biosphere.Cells))
		fmt.Printf("    Total born:             %d\n", u.Biosphere.TotalBorn)
		fmt.Printf("    Total died:             %d\n", u.Biosphere.TotalDied)
		fmt.Printf("    Generations:            %d\n", u.Biosphere.Generation)
		fmt.Printf("    Average fitness:        %.4f\n", u.Biosphere.AverageFitness())
		fmt.Printf("    Average GC content:     %.4f\n", u.Biosphere.AverageGCContent())
		fmt.Printf("    Total mutations:        %d\n", u.Biosphere.TotalMutations())
		fmt.Println()
	}

	// Environment
	fmt.Println("  [Environment]")
	fmt.Printf("    Temperature:            %.2f K\n", u.Env.Temperature)
	fmt.Printf("    UV intensity:           %.4f\n", u.Env.UVIntensity)
	fmt.Printf("    Cosmic ray flux:        %.4f\n", u.Env.CosmicRayFlux)
	fmt.Printf("    Atmospheric density:    %.4f\n", u.Env.AtmosphericDensity)
	fmt.Printf("    Water availability:     %.4f\n", u.Env.WaterAvailability)
	habitable := "No"
	if u.Env.IsHabitable() {
		habitable = "Yes"
	}
	fmt.Printf("    Habitable:              %s\n", habitable)
	fmt.Printf("    Environmental events:   %d\n", len(u.Env.EventHistory))
	fmt.Println()
}

// printFooter prints the closing banner.
func printFooter() {
	fmt.Println(line('='))
	fmt.Println(center("And so, from quantum foam to living cells,"))
	fmt.Println(center("the universe wrote itself into existence."))
	fmt.Println(line('='))
	fmt.Println()
}

// printDivider prints a divider line.
func printDivider() {
	fmt.Println(line('-'))
}

// line returns a line of the given character, bannerWidth wide.
func line(ch byte) string {
	return "  " + strings.Repeat(string(ch), bannerWidth)
}

// center returns a centered string within bannerWidth.
func center(s string) string {
	if len(s) >= bannerWidth {
		return "  " + s
	}
	pad := (bannerWidth - len(s)) / 2
	return "  " + strings.Repeat(" ", pad) + s
}
