// App.swift
// InTheBeginning
//
// Main entry point for the In The Beginning cosmic evolution simulator.
// A SwiftUI app that models physics from the Big Bang through the
// emergence of life, rendered in real time.

import SwiftUI

@main
struct InTheBeginningApp: App {
    @State private var universe = Universe()

    var body: some Scene {
        WindowGroup {
            SimulationView(universe: universe)
                .preferredColorScheme(.dark)
        }
    }
}
