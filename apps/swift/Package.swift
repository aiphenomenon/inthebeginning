// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

var targets: [Target] = [
    // Simulator library (pure Foundation, no UI dependencies — works on Linux)
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

    // Simulator tests (pure XCTest, works on Linux)
    .testTarget(
        name: "SimulatorTests",
        dependencies: ["InTheBeginningSimulator"],
        path: "Tests/SimulatorTests"
    ),
]

// The app executable requires SwiftUI/Metal/AVFoundation (Apple platforms only).
// Skip it when SKIP_APP_TARGET is set (CI simulator-only builds).
#if os(macOS) || os(iOS) || os(tvOS)
if ProcessInfo.processInfo.environment["SKIP_APP_TARGET"] == nil {
    targets.append(
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
        )
    )
}
#endif

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
    targets: targets
)
