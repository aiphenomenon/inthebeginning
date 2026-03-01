// InTheBeginningView.swift
// InTheBeginning – macOS Screensaver
//
// Main ScreenSaverView subclass.
// Renders the cosmic evolution simulation using Metal (preferred) with
// a Core Graphics fallback. Each frame advances the simulation by
// kTicksPerFrame ticks and draws all entities as colored points with
// epoch-based visual themes.
//
// Build instructions:
//   1. Open Terminal and cd to the project root.
//   2. Build with xcodebuild:
//
//      xcodebuild -project InTheBeginning.xcodeproj \
//                 -scheme InTheBeginning \
//                 -configuration Release \
//                 build
//
//   3. Copy the resulting .saver bundle to ~/Library/Screen Savers/
//   4. Select "InTheBeginning" in System Preferences > Screen Saver.

import ScreenSaver
import Metal
import MetalKit

// MARK: - InTheBeginningView

final class InTheBeginningView: ScreenSaverView {

    // MARK: Properties

    private var universe: Universe!
    private var currentSnapshot: UniverseSnapshot?
    private let backgroundColor = NSColor.black

    // Metal rendering
    private var metalView: MTKView?
    private var metalRenderer: MetalRenderer?
    private var usesMetal: Bool = false

    // Label rendering (used for HUD overlay in both paths)
    private let labelFont = NSFont.monospacedSystemFont(ofSize: 12.0, weight: .regular)
    private let epochFont = NSFont.monospacedSystemFont(ofSize: 16.0, weight: .bold)
    private let labelColor = NSColor(white: 0.85, alpha: 0.9)

    // MARK: Initialization

    override init?(frame: NSRect, isPreview: Bool) {
        super.init(frame: frame, isPreview: isPreview)
        commonInit()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        commonInit()
    }

    private func commonInit() {
        animationTimeInterval = 1.0 / 30.0   // 30 fps
        universe = Universe(seed: UInt64.random(in: 1...UInt64.max))
        setupMetal()
    }

    // MARK: Metal Setup

    private func setupMetal() {
        guard let device = MTLCreateSystemDefaultDevice() else {
            // Metal unavailable -- fall back to Core Graphics
            usesMetal = false
            return
        }

        let mtkView = MTKView(frame: bounds, device: device)
        mtkView.colorPixelFormat = .bgra8Unorm
        mtkView.clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 1)
        mtkView.isPaused = true                // We drive rendering manually
        mtkView.enableSetNeedsDisplay = false  // No automatic display
        mtkView.autoresizingMask = [.width, .height]
        mtkView.layer?.isOpaque = true

        do {
            let renderer = try MetalRenderer(device: device, pixelFormat: mtkView.colorPixelFormat)
            self.metalRenderer = renderer
            self.metalView = mtkView
            self.usesMetal = true
            addSubview(mtkView)
        } catch {
            // If pipeline creation fails, fall back to Core Graphics
            usesMetal = false
        }
    }

    override func layout() {
        super.layout()
        metalView?.frame = bounds
    }

    // MARK: ScreenSaverView Overrides

    override func animateOneFrame() {
        // Advance simulation
        for _ in 0..<kTicksPerFrame {
            universe.step()
        }
        currentSnapshot = universe.snapshot()

        if usesMetal, let mtkView = metalView, let renderer = metalRenderer,
           let snap = currentSnapshot {
            // Metal path: render particles and progress bar via GPU
            renderer.render(snapshot: snap, in: mtkView)
            // Trigger a CG draw pass for the text HUD overlay
            setNeedsDisplay(bounds)
        } else {
            // Core Graphics fallback
            setNeedsDisplay(bounds)
        }
    }

    override var hasConfigureSheet: Bool { false }
    override var configureSheet: NSWindow? { nil }

    // MARK: Drawing

    override func draw(_ rect: NSRect) {
        guard let ctx = NSGraphicsContext.current?.cgContext else { return }
        let width = bounds.width
        let height = bounds.height

        if usesMetal {
            // Metal handles particle rendering; we only draw the text HUD here.
            // The Metal view is a subview, so its content shows through.
            // Draw HUD overlay on top.
            guard let snap = currentSnapshot else { return }
            drawHUD(ctx: ctx, snap: snap, width: width, height: height)
        } else {
            // Full Core Graphics fallback path
            ctx.setFillColor(backgroundColor.cgColor)
            ctx.fill(bounds)

            drawBackgroundGlow(ctx: ctx, width: width, height: height)

            guard let snap = currentSnapshot else { return }

            for entity in snap.entities {
                drawEntity(ctx: ctx, entity: entity, width: width, height: height)
            }

            drawHUD(ctx: ctx, snap: snap, width: width, height: height)
        }
    }

    // MARK: Background Glow (CG fallback)

    private func drawBackgroundGlow(ctx: CGContext, width: CGFloat, height: CGFloat) {
        let epoch = universe.currentEpoch
        let (r, g, b, a) = epochBackgroundColor(epoch)

        guard a > 0.001 else { return }

        let centerX = width / 2.0
        let centerY = height / 2.0
        let radius = max(width, height) * 0.6

        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let components: [CGFloat] = [
            CGFloat(r), CGFloat(g), CGFloat(b), CGFloat(a),
            CGFloat(r * 0.2), CGFloat(g * 0.2), CGFloat(b * 0.2), 0.0,
        ]
        let locations: [CGFloat] = [0.0, 1.0]

        if let gradient = CGGradient(
            colorSpace: colorSpace,
            colorComponents: components,
            locations: locations,
            count: 2
        ) {
            ctx.drawRadialGradient(
                gradient,
                startCenter: CGPoint(x: centerX, y: centerY),
                startRadius: 0,
                endCenter: CGPoint(x: centerX, y: centerY),
                endRadius: radius,
                options: [.drawsAfterEndLocation]
            )
        }
    }

    private func epochBackgroundColor(_ epoch: Epoch) -> (Double, Double, Double, Double) {
        switch epoch {
        case .planck:          return (1.0, 1.0, 0.9, 0.4)    // White-hot
        case .inflation:       return (1.0, 0.8, 0.5, 0.3)    // Fiery orange
        case .electroweak:     return (0.6, 0.3, 0.9, 0.2)    // Violet
        case .quark:           return (0.8, 0.2, 0.2, 0.15)   // Red plasma
        case .hadron:          return (0.7, 0.4, 0.2, 0.1)    // Warm brown
        case .nucleosynthesis: return (0.5, 0.3, 0.1, 0.08)   // Dim orange
        case .recombination:   return (0.3, 0.2, 0.1, 0.05)   // Fading glow
        case .starFormation:   return (0.1, 0.1, 0.3, 0.06)   // Deep blue
        case .solarSystem:     return (0.2, 0.15, 0.05, 0.05) // Nebula gold
        case .earth:           return (0.05, 0.1, 0.2, 0.04)  // Ocean hint
        case .life:            return (0.02, 0.1, 0.05, 0.04) // Green tint
        case .dna:             return (0.02, 0.12, 0.06, 0.05)// Brighter green
        case .present:         return (0.03, 0.08, 0.15, 0.05)// Blue-green
        }
    }

    // MARK: Entity Rendering (CG fallback)

    private func drawEntity(ctx: CGContext, entity: RenderableEntity,
                            width: CGFloat, height: CGFloat) {
        let worldScale = min(width, height) / CGFloat(kWorldRadius * 2.0)
        let cx = width / 2.0
        let cy = height / 2.0

        let screenX = cx + CGFloat(entity.position.x) * worldScale
        let screenY = cy + CGFloat(entity.position.y) * worldScale

        guard screenX > -20 && screenX < width + 20 &&
              screenY > -20 && screenY < height + 20 else { return }

        let size = CGFloat(entity.size) * worldScale * 0.1
        let drawSize = max(1.5, min(size, 12.0))

        let color = CGColor(
            red: CGFloat(entity.red),
            green: CGFloat(entity.green),
            blue: CGFloat(entity.blue),
            alpha: CGFloat(entity.alpha)
        )

        // Glow
        let glowSize = drawSize * 2.5
        let glowAlpha = CGFloat(entity.alpha) * 0.2
        let glowColor = CGColor(
            red: CGFloat(entity.red),
            green: CGFloat(entity.green),
            blue: CGFloat(entity.blue),
            alpha: glowAlpha
        )
        ctx.setFillColor(glowColor)
        ctx.fillEllipse(in: CGRect(
            x: screenX - glowSize / 2.0,
            y: screenY - glowSize / 2.0,
            width: glowSize,
            height: glowSize
        ))

        // Core
        ctx.setFillColor(color)
        ctx.fillEllipse(in: CGRect(
            x: screenX - drawSize / 2.0,
            y: screenY - drawSize / 2.0,
            width: drawSize,
            height: drawSize
        ))
    }

    // MARK: HUD Overlay

    private func drawHUD(ctx: CGContext, snap: UniverseSnapshot,
                         width: CGFloat, height: CGFloat) {
        let margin: CGFloat = 16.0

        // Epoch name (top center)
        let epochAttrs: [NSAttributedString.Key: Any] = [
            .font: epochFont,
            .foregroundColor: labelColor,
        ]
        let epochStr = NSAttributedString(string: snap.epochName, attributes: epochAttrs)
        let epochSize = epochStr.size()
        epochStr.draw(at: NSPoint(
            x: (width - epochSize.width) / 2.0,
            y: height - margin - epochSize.height
        ))

        // Epoch description (below name)
        let descAttrs: [NSAttributedString.Key: Any] = [
            .font: labelFont,
            .foregroundColor: NSColor(white: 0.7, alpha: 0.8),
        ]
        let descStr = NSAttributedString(string: snap.epochDescription, attributes: descAttrs)
        let descSize = descStr.size()
        descStr.draw(at: NSPoint(
            x: (width - descSize.width) / 2.0,
            y: height - margin - epochSize.height - descSize.height - 4.0
        ))

        // Stats (bottom left)
        let statsAttrs: [NSAttributedString.Key: Any] = [
            .font: labelFont,
            .foregroundColor: NSColor(white: 0.6, alpha: 0.7),
        ]

        let tempStr: String
        if snap.temperature > 1e6 {
            tempStr = String(format: "%.1e K", snap.temperature)
        } else {
            tempStr = String(format: "%.0f K", snap.temperature)
        }

        let lines = [
            "tick \(snap.tick)  T=\(tempStr)",
            "particles:\(snap.particleCount)  atoms:\(snap.atomCount)  " +
            "molecules:\(snap.moleculeCount)  cells:\(snap.cellCount)",
        ]

        for (i, line) in lines.enumerated() {
            let str = NSAttributedString(string: line, attributes: statsAttrs)
            str.draw(at: NSPoint(x: margin, y: margin + CGFloat(i) * 16.0))
        }
    }
}
