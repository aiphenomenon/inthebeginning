/// ASTIntrospection.swift
/// InTheBeginning Screensaver
///
/// Provides AST self-introspection for the macOS screensaver.
/// Analyzes Swift source files to report symbol counts and structural metrics.

import Foundation

/// AST self-introspection report for the macOS screensaver.
struct ASTIntrospection {

    /// File-level metrics from introspection.
    struct FileMetrics {
        let filename: String
        let lines: Int
        let bytes: Int
        let structs: Int
        let classes: Int
        let functions: Int
    }

    /// Analyze a Swift source string and return metrics.
    static func analyze(source: String, filename: String) -> FileMetrics {
        let lines = source.components(separatedBy: "\n").count
        let bytes = source.utf8.count

        let structCount = matches(in: source, pattern: "\\bstruct\\s+\\w+")
        let classCount = matches(in: source, pattern: "\\bclass\\s+\\w+")
        let funcCount = matches(in: source, pattern: "\\bfunc\\s+\\w+")

        return FileMetrics(
            filename: filename,
            lines: lines,
            bytes: bytes,
            structs: structCount,
            classes: classCount,
            functions: funcCount
        )
    }

    /// Generate a formatted introspection report string.
    static func report(metrics: [FileMetrics]) -> String {
        var output = "=== AST Self-Introspection: macOS Screensaver ===\n\n"

        let header = String(format: "  %-28s %6s %8s %6s %6s %6s",
                           "File", "Lines", "Bytes", "Struct", "Class", "Func")
        output += header + "\n"
        output += "  " + String(repeating: "─", count: 60) + "\n"

        var totals = (lines: 0, bytes: 0, structs: 0, classes: 0, functions: 0)

        for m in metrics {
            output += String(format: "  %-28s %6d %8d %6d %6d %6d\n",
                           (m.filename as NSString).utf8String ?? m.filename,
                           m.lines, m.bytes, m.structs, m.classes, m.functions)
            totals.lines += m.lines
            totals.bytes += m.bytes
            totals.structs += m.structs
            totals.classes += m.classes
            totals.functions += m.functions
        }

        output += "  " + String(repeating: "─", count: 60) + "\n"
        output += String(format: "  %-28s %6d %8d %6d %6d %6d\n",
                       "TOTAL", totals.lines, totals.bytes, totals.structs,
                       totals.classes, totals.functions)
        return output
    }

    /// Count regex matches in a string.
    private static func matches(in source: String, pattern: String) -> Int {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return 0 }
        let range = NSRange(source.startIndex..., in: source)
        return regex.numberOfMatches(in: source, range: range)
    }
}
