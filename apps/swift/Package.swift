// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "InTheBeginning",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
        .tvOS(.v17),
    ],
    products: [
        .library(
            name: "InTheBeginningSimulator",
            targets: ["InTheBeginningSimulator"]
        ),
    ],
    targets: [
        // Simulator library (pure Foundation, no UI dependencies)
        .target(
            name: "InTheBeginningSimulator",
            dependencies: [],
            path: "InTheBeginning/Simulator",
            sources: [
                "Constants.swift",
                "QuantumField.swift",
                "AtomicSystem.swift",
                "ChemicalSystem.swift",
                "Biosphere.swift",
                "Environment.swift",
                "Universe.swift",
            ]
        ),

        // Main app executable
        .executableTarget(
            name: "InTheBeginning",
            dependencies: ["InTheBeginningSimulator"],
            path: "InTheBeginning",
            exclude: ["Simulator"],
            sources: [
                "App.swift",
                "Views/SimulationView.swift",
                "Views/EpochTimelineView.swift",
                "Views/SettingsView.swift",
                "Renderer/MetalRenderer.swift",
                "Audio/AudioEngine.swift",
            ],
            resources: [
                .process("Renderer/Shaders.metal"),
            ]
        ),
    ]
)
