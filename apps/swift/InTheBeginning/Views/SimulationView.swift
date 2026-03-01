// SimulationView.swift
// InTheBeginning
//
// Main simulation view with Canvas-based particle rendering,
// control panel, and real-time statistics overlay.

import SwiftUI

// MARK: - Main Simulation View

struct SimulationView: View {
    @Bindable var universe: Universe
    @State private var showStats = true
    @State private var showLog = false
    @State private var showSettings = false
    @State private var speed: Double = 1.0
    @State private var displayLink: Timer?
    @State private var audioEnabled = false
    @State private var visualizationStyle: VisualizationStyle = .particles
    #if canImport(AVFoundation)
    @StateObject private var audioEngine = AudioEngine()
    #endif

    var body: some View {
        ZStack {
            // Background gradient based on epoch
            epochBackground

            VStack(spacing: 0) {
                // Top bar with epoch info
                topBar

                // Main canvas
                GeometryReader { geometry in
                    ZStack {
                        particleCanvas(size: geometry.size)

                        // Statistics overlay
                        if showStats {
                            statsOverlay
                                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                                .padding()
                        }

                        // Event log overlay
                        if showLog {
                            logOverlay
                                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
                                .padding()
                        }
                    }
                }

                // Epoch timeline
                EpochTimelineView(
                    currentEpoch: universe.currentEpoch,
                    progress: universe.progress
                )
                .frame(height: 80)

                // Control bar
                controlBar
            }
        }
        .sheet(isPresented: $showSettings) {
            SettingsView(
                universe: universe,
                isPresented: $showSettings,
                audioEnabled: $audioEnabled,
                visualizationStyle: $visualizationStyle
            )
        }
        .onChange(of: audioEnabled) { _, newValue in
            #if canImport(AVFoundation)
            audioEngine.isEnabled = newValue
            #endif
        }
        .gesture(
            DragGesture(minimumDistance: 30)
                .onEnded { value in
                    let horizontal = value.translation.width
                    if horizontal > 50 {
                        speed = min(20.0, speed + 1.0)
                        universe.ticksPerFrame = max(1, Int(speed))
                    } else if horizontal < -50 {
                        speed = max(0.25, speed - 1.0)
                        universe.ticksPerFrame = max(1, Int(speed))
                    }
                }
        )
        .onDisappear {
            stopSimulation()
        }
    }

    // MARK: - Background

    private var epochBackground: some View {
        let colors = backgroundColors(for: universe.currentEpoch)
        return LinearGradient(
            gradient: Gradient(colors: colors),
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()
        .animation(.easeInOut(duration: 2.0), value: universe.currentEpoch)
    }

    private func backgroundColors(for epoch: Epoch) -> [Color] {
        switch epoch {
        case .planck:
            return [Color.white, Color(red: 1.0, green: 0.9, blue: 0.7)]
        case .inflation:
            return [Color(red: 1.0, green: 0.8, blue: 0.4), Color(red: 0.8, green: 0.3, blue: 0.1)]
        case .electroweak:
            return [Color(red: 0.9, green: 0.5, blue: 0.1), Color(red: 0.6, green: 0.1, blue: 0.3)]
        case .quark:
            return [Color(red: 0.7, green: 0.1, blue: 0.2), Color(red: 0.3, green: 0.0, blue: 0.3)]
        case .hadron:
            return [Color(red: 0.4, green: 0.0, blue: 0.3), Color(red: 0.1, green: 0.0, blue: 0.2)]
        case .nucleosynthesis:
            return [Color(red: 0.2, green: 0.0, blue: 0.3), Color(red: 0.05, green: 0.0, blue: 0.15)]
        case .recombination:
            return [Color(red: 0.1, green: 0.0, blue: 0.15), Color(red: 0.02, green: 0.02, blue: 0.08)]
        case .starFormation:
            return [Color(red: 0.02, green: 0.02, blue: 0.1), Color.black]
        case .solarSystem:
            return [Color(red: 0.05, green: 0.03, blue: 0.12), Color.black]
        case .earth:
            return [Color(red: 0.0, green: 0.1, blue: 0.2), Color(red: 0.0, green: 0.05, blue: 0.1)]
        case .life:
            return [Color(red: 0.0, green: 0.1, blue: 0.15), Color(red: 0.0, green: 0.05, blue: 0.08)]
        case .dna:
            return [Color(red: 0.0, green: 0.08, blue: 0.12), Color(red: 0.02, green: 0.04, blue: 0.08)]
        case .present:
            return [Color(red: 0.0, green: 0.05, blue: 0.15), Color(red: 0.0, green: 0.02, blue: 0.06)]
        }
    }

    // MARK: - Top Bar

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(universe.currentEpoch.displayName)
                    .font(.title2.bold())
                    .foregroundStyle(.white)

                Text(universe.currentEpoch.description)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.7))
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text(universe.cosmicTimeDescription)
                    .font(.subheadline.monospacedDigit())
                    .foregroundStyle(.white)

                Text("Tick \(universe.tick)")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.white.opacity(0.5))
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial.opacity(0.3))
    }

    // MARK: - Particle Canvas

    private func particleCanvas(size: CGSize) -> some View {
        Canvas { context, canvasSize in
            let centerX = canvasSize.width / 2.0
            let centerY = canvasSize.height / 2.0
            let scale = min(canvasSize.width, canvasSize.height) / 200.0

            for entity in universe.renderables {
                // Project 3D position to 2D
                let x = centerX + entity.position.x * scale
                let y = centerY + entity.position.y * scale

                // Skip if outside canvas bounds
                guard x > -20 && x < canvasSize.width + 20 &&
                      y > -20 && y < canvasSize.height + 20 else {
                    continue
                }

                let color = Color(
                    red: Double(entity.color.x),
                    green: Double(entity.color.y),
                    blue: Double(entity.color.z),
                    opacity: Double(entity.color.w)
                )

                let radius = CGFloat(entity.radius) * scale * 0.1

                // Draw glow effect for particles
                if entity.category == .particle {
                    let glowRect = CGRect(
                        x: x - radius * 2,
                        y: y - radius * 2,
                        width: radius * 4,
                        height: radius * 4
                    )
                    context.opacity = Double(entity.color.w) * 0.3
                    context.fill(
                        Circle().path(in: glowRect),
                        with: .color(color)
                    )
                    context.opacity = 1.0
                }

                // Draw entity
                let rect = CGRect(
                    x: x - radius,
                    y: y - radius,
                    width: radius * 2,
                    height: radius * 2
                )

                switch entity.category {
                case .cell:
                    // Cells are drawn as rounded shapes
                    context.fill(
                        RoundedRectangle(cornerRadius: radius * 0.3)
                            .path(in: rect),
                        with: .color(color)
                    )
                    // Cell membrane
                    context.stroke(
                        Circle().path(in: rect.insetBy(dx: -1, dy: -1)),
                        with: .color(color.opacity(0.5)),
                        lineWidth: 1
                    )
                default:
                    context.fill(
                        Circle().path(in: rect),
                        with: .color(color)
                    )
                }
            }
        }
    }

    // MARK: - Stats Overlay

    private var statsOverlay: some View {
        VStack(alignment: .leading, spacing: 4) {
            let s = universe.snapshot

            Group {
                statRow("Temperature", formatTemp(s.temperature))
                statRow("Particles", "\(s.particleCount)")
                statRow("Atoms", "\(s.atomCount)")
                statRow("Molecules", "\(s.moleculeCount)")

                if s.waterCount > 0 {
                    statRow("Water", "\(s.waterCount)")
                }
                if s.aminoAcidCount > 0 {
                    statRow("Amino Acids", "\(s.aminoAcidCount)")
                }
                if s.cellCount > 0 {
                    statRow("Cells", "\(s.cellCount)")
                    statRow("Avg Fitness", String(format: "%.3f", s.averageFitness))
                    statRow("Max Gen", "\(s.maxGeneration)")
                    statRow("Diversity", String(format: "%.2f", s.geneticDiversity))
                }
                if s.habitability > 0 {
                    statRow("Habitability", String(format: "%.0f%%", s.habitability * 100))
                }
            }
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(.black.opacity(0.5))
        )
        .font(.caption.monospacedDigit())
        .foregroundStyle(.white)
    }

    private func statRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .foregroundStyle(.white.opacity(0.6))
            Spacer(minLength: 8)
            Text(value)
                .foregroundStyle(.white)
        }
        .frame(minWidth: 160)
    }

    private func formatTemp(_ temp: Double) -> String {
        if temp >= 1e9 {
            return String(format: "%.1e K", temp)
        } else if temp >= 1e6 {
            return String(format: "%.1f MK", temp / 1e6)
        } else if temp >= 1000 {
            return String(format: "%.0f K", temp)
        } else {
            return String(format: "%.1f K", temp)
        }
    }

    // MARK: - Log Overlay

    private var logOverlay: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("Event Log")
                .font(.caption.bold())
                .foregroundStyle(.white.opacity(0.8))

            ScrollView {
                LazyVStack(alignment: .leading, spacing: 1) {
                    ForEach(universe.eventLog.suffix(15), id: \.self) { entry in
                        Text(entry)
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.green.opacity(0.8))
                    }
                }
            }
            .frame(maxHeight: 150)
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(.black.opacity(0.7))
        )
        .frame(maxWidth: 400)
    }

    // MARK: - Control Bar

    private var controlBar: some View {
        HStack(spacing: 16) {
            // Play/Pause button
            Button(action: toggleSimulation) {
                Image(systemName: universe.state == .running ? "pause.circle.fill" : "play.circle.fill")
                    .font(.title)
                    .foregroundStyle(.white)
            }

            // Reset button
            Button(action: {
                stopSimulation()
                universe.reset()
            }) {
                Image(systemName: "arrow.counterclockwise.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.white.opacity(0.7))
            }

            Divider()
                .frame(height: 24)
                .background(.white.opacity(0.3))

            // Speed control
            HStack(spacing: 4) {
                Image(systemName: "gauge.with.dots.needle.33percent")
                    .foregroundStyle(.white.opacity(0.6))
                    .font(.caption)

                Slider(value: $speed, in: 0.25...10.0, step: 0.25)
                    .frame(width: 100)
                    .onChange(of: speed) { _, newValue in
                        universe.ticksPerFrame = max(1, Int(newValue))
                    }

                Text("\(String(format: "%.1f", speed))x")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.white.opacity(0.7))
                    .frame(width: 35)
            }

            Spacer()

            // Toggle buttons
            Button(action: { showStats.toggle() }) {
                Image(systemName: showStats ? "chart.bar.fill" : "chart.bar")
                    .foregroundStyle(.white.opacity(showStats ? 1.0 : 0.5))
            }

            Button(action: { showLog.toggle() }) {
                Image(systemName: showLog ? "text.alignleft" : "text.alignleft")
                    .foregroundStyle(.white.opacity(showLog ? 1.0 : 0.5))
            }

            Button(action: { showSettings = true }) {
                Image(systemName: "gearshape.fill")
                    .foregroundStyle(.white.opacity(0.7))
            }

            // Progress
            Text(String(format: "%.1f%%", universe.progress * 100))
                .font(.caption.monospacedDigit())
                .foregroundStyle(.white.opacity(0.6))
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
        .background(.ultraThinMaterial.opacity(0.3))
    }

    // MARK: - Simulation Control

    private func toggleSimulation() {
        switch universe.state {
        case .idle:
            universe.start()
            startDisplayLink()
        case .running:
            universe.pause()
            stopSimulation()
        case .paused:
            universe.resume()
            startDisplayLink()
        case .completed:
            universe.reset()
            universe.start()
            startDisplayLink()
        }
    }

    private func startDisplayLink() {
        guard displayLink == nil else { return }
        displayLink = Timer.scheduledTimer(withTimeInterval: 1.0 / 60.0, repeats: true) { _ in
            universe.advanceFrame()
            #if canImport(AVFoundation)
            audioEngine.update(
                particleCount: universe.snapshot.particleCount,
                temperature: universe.snapshot.temperature,
                epoch: universe.currentEpoch
            )
            #endif
            if universe.state != .running {
                stopSimulation()
            }
        }
    }

    private func stopSimulation() {
        displayLink?.invalidate()
        displayLink = nil
    }
}

// MARK: - Preview

#Preview {
    SimulationView(universe: Universe())
}
