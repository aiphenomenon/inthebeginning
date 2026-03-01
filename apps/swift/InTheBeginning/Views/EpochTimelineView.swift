// EpochTimelineView.swift
// InTheBeginning
//
// A horizontal timeline view showing the progression through
// all 13 cosmic epochs. Highlights the current epoch and
// displays overall simulation progress.

import SwiftUI

// MARK: - Epoch Timeline View

struct EpochTimelineView: View {
    let currentEpoch: Epoch
    let progress: Double

    @State private var selectedEpoch: Epoch?

    var body: some View {
        VStack(spacing: 4) {
            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    // Track
                    RoundedRectangle(cornerRadius: 2)
                        .fill(.white.opacity(0.1))
                        .frame(height: 4)

                    // Fill
                    RoundedRectangle(cornerRadius: 2)
                        .fill(
                            LinearGradient(
                                colors: [.blue, .purple, .orange, .green],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * CGFloat(progress), height: 4)
                        .animation(.linear(duration: 0.1), value: progress)
                }
                .frame(height: 4)
            }
            .frame(height: 4)
            .padding(.horizontal, 8)

            // Epoch markers
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 2) {
                    ForEach(Epoch.allCases) { epoch in
                        EpochMarkerView(
                            epoch: epoch,
                            isCurrent: epoch == currentEpoch,
                            isPast: epoch < currentEpoch,
                            isSelected: epoch == selectedEpoch
                        )
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                selectedEpoch = selectedEpoch == epoch ? nil : epoch
                            }
                        }
                    }
                }
                .padding(.horizontal, 8)
            }

            // Selected epoch detail
            if let selected = selectedEpoch {
                epochDetail(selected)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .padding(.vertical, 4)
        .background(.ultraThinMaterial.opacity(0.2))
    }

    private func epochDetail(_ epoch: Epoch) -> some View {
        HStack(spacing: 8) {
            Image(systemName: epoch.icon)
                .font(.caption)
                .foregroundStyle(colorForEpoch(epoch))

            VStack(alignment: .leading, spacing: 1) {
                Text(epoch.displayName)
                    .font(.caption.bold())
                    .foregroundStyle(.white)

                Text(epoch.description)
                    .font(.system(size: 9))
                    .foregroundStyle(.white.opacity(0.6))
                    .lineLimit(1)
            }

            Spacer()

            Text("t = \(epoch.tick)")
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.white.opacity(0.4))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
    }

    private func colorForEpoch(_ epoch: Epoch) -> Color {
        switch epoch {
        case .planck:          return .white
        case .inflation:       return .yellow
        case .electroweak:     return .orange
        case .quark:           return .red
        case .hadron:          return Color(red: 0.7, green: 0.1, blue: 0.3)
        case .nucleosynthesis: return .purple
        case .recombination:   return Color(red: 0.3, green: 0.2, blue: 0.8)
        case .starFormation:   return .blue
        case .solarSystem:     return .cyan
        case .earth:           return Color(red: 0.2, green: 0.6, blue: 0.8)
        case .life:            return .green
        case .dna:             return Color(red: 0.4, green: 0.9, blue: 0.4)
        case .present:         return Color(red: 0.3, green: 1.0, blue: 0.7)
        }
    }
}

// MARK: - Epoch Marker View

struct EpochMarkerView: View {
    let epoch: Epoch
    let isCurrent: Bool
    let isPast: Bool
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 2) {
            // Icon
            ZStack {
                Circle()
                    .fill(circleColor)
                    .frame(width: circleSize, height: circleSize)

                if isCurrent {
                    Circle()
                        .stroke(.white.opacity(0.8), lineWidth: 2)
                        .frame(width: circleSize + 4, height: circleSize + 4)
                }

                Image(systemName: epoch.icon)
                    .font(.system(size: iconSize))
                    .foregroundStyle(iconColor)
            }

            // Label
            Text(shortName)
                .font(.system(size: 7))
                .foregroundStyle(labelColor)
                .lineLimit(1)
                .frame(width: 40)
        }
        .padding(.vertical, 2)
        .padding(.horizontal, 1)
        .scaleEffect(isCurrent ? 1.1 : 1.0)
        .animation(.spring(response: 0.3), value: isCurrent)
    }

    private var circleSize: CGFloat {
        isCurrent ? 24 : (isSelected ? 22 : 18)
    }

    private var iconSize: CGFloat {
        isCurrent ? 10 : 8
    }

    private var circleColor: Color {
        if isCurrent {
            return epochColor.opacity(0.9)
        } else if isPast {
            return epochColor.opacity(0.4)
        } else {
            return .gray.opacity(0.2)
        }
    }

    private var iconColor: Color {
        if isCurrent || isPast {
            return .white
        } else {
            return .gray.opacity(0.5)
        }
    }

    private var labelColor: Color {
        if isCurrent {
            return .white
        } else if isPast {
            return .white.opacity(0.5)
        } else {
            return .white.opacity(0.3)
        }
    }

    private var epochColor: Color {
        switch epoch {
        case .planck:          return .white
        case .inflation:       return .yellow
        case .electroweak:     return .orange
        case .quark:           return .red
        case .hadron:          return Color(red: 0.7, green: 0.1, blue: 0.3)
        case .nucleosynthesis: return .purple
        case .recombination:   return Color(red: 0.3, green: 0.2, blue: 0.8)
        case .starFormation:   return .blue
        case .solarSystem:     return .cyan
        case .earth:           return Color(red: 0.2, green: 0.6, blue: 0.8)
        case .life:            return .green
        case .dna:             return Color(red: 0.4, green: 0.9, blue: 0.4)
        case .present:         return Color(red: 0.3, green: 1.0, blue: 0.7)
        }
    }

    private var shortName: String {
        switch epoch {
        case .planck:          return "Planck"
        case .inflation:       return "Inflate"
        case .electroweak:     return "EW"
        case .quark:           return "Quark"
        case .hadron:          return "Hadron"
        case .nucleosynthesis: return "Nucleo"
        case .recombination:   return "Recomb"
        case .starFormation:   return "Stars"
        case .solarSystem:     return "Solar"
        case .earth:           return "Earth"
        case .life:            return "Life"
        case .dna:             return "DNA"
        case .present:         return "Now"
        }
    }
}

// MARK: - Preview

#Preview {
    VStack {
        Spacer()
        EpochTimelineView(currentEpoch: .starFormation, progress: 0.35)
            .frame(height: 80)
    }
    .background(.black)
}
