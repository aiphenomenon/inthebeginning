// SettingsView.swift
// InTheBeginning
//
// Settings sheet for configuring the simulation.
// Provides controls for seed, speed, visualization style,
// and audio toggle.

import InTheBeginningSimulator
import SwiftUI

// MARK: - Visualization Style

enum VisualizationStyle: String, CaseIterable, Identifiable {
    case particles = "Particles"
    case glow = "Glow"
    case minimal = "Minimal"
    case heatmap = "Heatmap"

    var id: String { rawValue }

    var description: String {
        switch self {
        case .particles: return "Standard particle rendering with colors per type"
        case .glow:      return "Particles with enhanced glow and bloom effects"
        case .minimal:   return "Clean dots with reduced visual noise"
        case .heatmap:   return "Color by energy density and temperature"
        }
    }

    var iconName: String {
        switch self {
        case .particles: return "circle.grid.3x3.fill"
        case .glow:      return "sparkles"
        case .minimal:   return "circle.fill"
        case .heatmap:   return "thermometer.medium"
        }
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @Bindable var universe: Universe
    @Binding var isPresented: Bool
    @Binding var audioEnabled: Bool
    @Binding var visualizationStyle: VisualizationStyle

    @State private var seedText: String = "42"
    @State private var speedValue: Double = 1.0
    @State private var maxParticles: Double = Double(SimulationLimits.maxParticlesDefault)
    @State private var showConfirmReset: Bool = false

    var body: some View {
        NavigationStack {
            Form {
                // Simulation section
                Section("Simulation") {
                    HStack {
                        Label("Seed", systemImage: "dice.fill")
                        Spacer()
                        TextField("Seed", text: $seedText)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 120)
                            .foregroundStyle(.secondary)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Label("Speed: \(String(format: "%.1fx", speedValue))", systemImage: "gauge.with.dots.needle.67percent")
                        Slider(value: $speedValue, in: 0.25...20.0, step: 0.25)
                            .onChange(of: speedValue) { _, newValue in
                                universe.ticksPerFrame = max(1, Int(newValue))
                            }
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Label("Max Particles: \(Int(maxParticles))", systemImage: "atom")
                        Slider(value: $maxParticles,
                               in: Double(SimulationLimits.maxParticlesLowPerf)...Double(SimulationLimits.maxParticlesDefault),
                               step: 100)
                            .onChange(of: maxParticles) { _, newValue in
                                universe.maxParticles = Int(newValue)
                            }
                    }
                }

                // Visualization section
                Section("Visualization") {
                    Picker("Style", selection: $visualizationStyle) {
                        ForEach(VisualizationStyle.allCases) { style in
                            Label(style.rawValue, systemImage: style.iconName)
                                .tag(style)
                        }
                    }

                    Text(visualizationStyle.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                // Audio section
                Section("Audio") {
                    Toggle(isOn: $audioEnabled) {
                        Label("Sonification", systemImage: audioEnabled ? "speaker.wave.3.fill" : "speaker.slash.fill")
                    }

                    if audioEnabled {
                        Text("Maps cosmic epochs to sound: pitch, timbre, and rhythm change as the universe evolves.")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                // Info section
                Section("Current State") {
                    LabeledContent("Epoch", value: universe.currentEpoch.displayName)
                    LabeledContent("Tick", value: "\(universe.tick)")
                    LabeledContent("Progress", value: String(format: "%.2f%%", universe.progress * 100))
                    LabeledContent("Status", value: universe.state.rawValue.capitalized)
                }

                // Reset section
                Section {
                    Button(role: .destructive) {
                        showConfirmReset = true
                    } label: {
                        Label("Reset Simulation", systemImage: "arrow.counterclockwise")
                    }
                    .confirmationDialog("Reset Simulation?", isPresented: $showConfirmReset) {
                        Button("Reset", role: .destructive) {
                            universe.reset()
                            isPresented = false
                        }
                        Button("Cancel", role: .cancel) { }
                    } message: {
                        Text("This will reset the simulation to the Planck epoch. All progress will be lost.")
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        isPresented = false
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    SettingsView(
        universe: Universe(),
        isPresented: .constant(true),
        audioEnabled: .constant(true),
        visualizationStyle: .constant(.particles)
    )
}
