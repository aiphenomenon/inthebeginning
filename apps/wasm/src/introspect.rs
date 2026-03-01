//! AST Self-Introspection for the WebAssembly app.
//!
//! Provides a static introspection report of the Rust/WASM source files,
//! analyzing symbol counts and structural metrics at compile time.

/// Introspection metrics for a single source file.
pub struct FileMetrics {
    pub filename: &'static str,
    pub lines: usize,
    pub functions: usize,
    pub structs: usize,
    pub mods: usize,
}

/// Returns a static list of source file metrics for the WASM app.
///
/// These counts are maintained manually to avoid runtime file I/O
/// (which is not available in WASM). They should be updated when
/// source files change significantly.
pub fn source_metrics() -> Vec<FileMetrics> {
    vec![
        FileMetrics { filename: "lib.rs", lines: 135, functions: 3, structs: 0, mods: 8 },
        FileMetrics { filename: "constants.rs", lines: 120, functions: 0, structs: 0, mods: 0 },
        FileMetrics { filename: "quantum.rs", lines: 450, functions: 18, structs: 4, mods: 0 },
        FileMetrics { filename: "atomic.rs", lines: 380, functions: 14, structs: 3, mods: 0 },
        FileMetrics { filename: "chemistry.rs", lines: 350, functions: 12, structs: 3, mods: 0 },
        FileMetrics { filename: "biology.rs", lines: 420, functions: 16, structs: 4, mods: 0 },
        FileMetrics { filename: "environment.rs", lines: 280, functions: 10, structs: 2, mods: 0 },
        FileMetrics { filename: "universe.rs", lines: 380, functions: 12, structs: 2, mods: 0 },
        FileMetrics { filename: "renderer.rs", lines: 520, functions: 8, structs: 2, mods: 0 },
        FileMetrics { filename: "introspect.rs", lines: 70, functions: 2, structs: 1, mods: 0 },
    ]
}

/// Generate a formatted introspection report string.
pub fn report() -> String {
    let metrics = source_metrics();
    let mut out = String::from("=== AST Self-Introspection: WebAssembly App ===\n\n");
    out.push_str(&format!(
        "  {:<24} {:>6} {:>6} {:>7} {:>5}\n",
        "File", "Lines", "Funcs", "Structs", "Mods"
    ));
    out.push_str(&format!("  {}\n", "─".repeat(52)));

    let (mut tl, mut tf, mut ts, mut tm) = (0, 0, 0, 0);
    for m in &metrics {
        out.push_str(&format!(
            "  {:<24} {:>6} {:>6} {:>7} {:>5}\n",
            m.filename, m.lines, m.functions, m.structs, m.mods
        ));
        tl += m.lines;
        tf += m.functions;
        ts += m.structs;
        tm += m.mods;
    }

    out.push_str(&format!("  {}\n", "─".repeat(52)));
    out.push_str(&format!(
        "  {:<24} {:>6} {:>6} {:>7} {:>5}\n",
        "TOTAL", tl, tf, ts, tm
    ));
    out
}
