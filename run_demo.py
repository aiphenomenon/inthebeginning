#!/usr/bin/env python3
"""Main entry point: run the reality simulator with AST introspection.

This demonstrates:
1. The AST DSL reactive agent pair analyzing the simulator code
2. The full physics simulation from Big Bang to Life
3. Performance metrics collection and reporting
"""
import json
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ast_dsl.core import ASTEngine, ASTQuery
from ast_dsl.reactive import ReactiveProtocol, CueSignal, CueType
from simulator.universe import Universe
from simulator.terminal_ui import (
    render_full_state, render_final_report, clear_screen,
    BOLD, RESET, CYAN, YELLOW, GREEN,
)


def run_ast_demo():
    """Demonstrate AST DSL capabilities on the simulator codebase."""
    print(f"\n{BOLD}{CYAN}=== AST DSL Reactive Agent Demo ==={RESET}\n")

    protocol = ReactiveProtocol(session_id="demo-session")

    # Self-cue 1: Parse the quantum module
    print(f"{YELLOW}[Cue 1] Parsing simulator/quantum.py...{RESET}")
    result = protocol.run_query(
        "parse",
        os.path.join(os.path.dirname(__file__), "simulator", "quantum.py"),
    )
    payload = result.payload
    if isinstance(payload, dict):
        print(f"  Nodes: {payload.get('ast_node_count', 'N/A')}")
        print(f"  Time: {payload.get('metrics', {}).get('wall_time_ms', 0):.1f}ms")
        print(f"  Memory: {payload.get('metrics', {}).get('peak_memory_kb', 0)}KB")

    # Self-cue 2: Find symbols
    print(f"\n{YELLOW}[Cue 2] Finding symbols in quantum.py...{RESET}")
    result = protocol.run_query(
        "symbols",
        os.path.join(os.path.dirname(__file__), "simulator", "quantum.py"),
    )
    if isinstance(result.payload, dict) and result.payload.get("success"):
        symbols = result.payload.get("data", [])
        print(f"  Found {len(symbols)} symbols:")
        for sym in symbols[:10]:
            print(f"    {sym.get('type', '?'):20s} {sym.get('name', '?'):30s} "
                  f"line {sym.get('line', '?')}")
        if len(symbols) > 10:
            print(f"    ... and {len(symbols) - 10} more")

    # Self-cue 3: Dependencies
    print(f"\n{YELLOW}[Cue 3] Extracting dependencies...{RESET}")
    result = protocol.run_query(
        "dependencies",
        os.path.join(os.path.dirname(__file__), "simulator", "quantum.py"),
    )
    if isinstance(result.payload, dict) and result.payload.get("success"):
        deps = result.payload.get("data", [])
        print(f"  Found {len(deps)} imports:")
        for dep in deps:
            print(f"    {dep.get('type', '?'):15s} {dep.get('module', '?')}")

    # Self-cue 4: Code metrics
    print(f"\n{YELLOW}[Cue 4] Computing code metrics...{RESET}")
    result = protocol.run_query(
        "metrics",
        os.path.join(os.path.dirname(__file__), "simulator", "quantum.py"),
    )
    if isinstance(result.payload, dict) and result.payload.get("success"):
        metrics = result.payload.get("data", {})
        print(f"  Total AST nodes:        {metrics.get('total_nodes', 'N/A')}")
        print(f"  Functions:              {metrics.get('functions', 'N/A')}")
        print(f"  Classes:                {metrics.get('classes', 'N/A')}")
        print(f"  Imports:                {metrics.get('imports', 'N/A')}")
        print(f"  Max depth:              {metrics.get('max_depth', 'N/A')}")
        print(f"  Cyclomatic complexity:   {metrics.get('cyclomatic_complexity', 'N/A')}")

    # Self-cue 5: Coverage map
    print(f"\n{YELLOW}[Cue 5] Generating coverage map...{RESET}")
    result = protocol.run_query(
        "coverage_map",
        os.path.join(os.path.dirname(__file__), "simulator", "quantum.py"),
    )
    if isinstance(result.payload, dict) and result.payload.get("success"):
        paths = result.payload.get("data", [])
        print(f"  Testable functions: {len(paths)}")
        for path in paths[:8]:
            print(f"    {path.get('function', '?'):25s} "
                  f"line {path.get('line', '?'):>4} "
                  f"branches={path.get('branches', 0)}")
        if len(paths) > 8:
            print(f"    ... and {len(paths) - 8} more")

    # Self-cue 6: Synthesize session
    print(f"\n{YELLOW}[Cue 6] Synthesizing session state...{RESET}")
    synth_cue = CueSignal(
        cue_type=CueType.SYNTHESIZE,
        sequence_id=100,
    )
    result = protocol.process_cue(synth_cue)
    if isinstance(result.payload, dict):
        state = result.payload.get("state", {})
        print(f"  Session: {state.get('session_id', 'N/A')}")
        print(f"  Turns: {state.get('turn', 'N/A')}")
        print(f"  Symbols found: {state.get('symbols_found', 'N/A')}")
        print(f"  Dependencies found: {state.get('deps_found', 'N/A')}")
        print(f"  Total tokens: {state.get('total_tokens', 'N/A')}")

    # Save session log
    session_log = protocol.get_session_log()
    log_path = os.path.join(os.path.dirname(__file__),
                            "ast_captures", "session_log.json")
    with open(log_path, "w") as f:
        f.write(session_log)
    print(f"\n  Session log saved to {log_path}")

    return protocol


def run_simulation():
    """Run the reality simulation."""
    print(f"\n{BOLD}{GREEN}=== Reality Simulation: Big Bang to Life ==={RESET}\n")

    universe = Universe(seed=42, max_ticks=300000, step_size=1000)

    print("Running simulation...")
    metrics = universe.run(progress_interval=30000)

    # Render final report
    report = render_final_report(universe)
    print(report)

    # Save results
    results_path = os.path.join(os.path.dirname(__file__),
                                "ast_captures", "simulation_results.json")
    with open(results_path, "w") as f:
        json.dump(universe.summary(), f, indent=2, default=str)
    print(f"\nResults saved to {results_path}")

    return universe


def run_introspection():
    """Run AST self-introspection across all application directories."""
    from ast_dsl.introspect import introspect_all_apps

    print(f"\n{BOLD}{CYAN}=== AST Self-Introspection: All Applications ==={RESET}\n")

    project_root = os.path.dirname(os.path.abspath(__file__))
    reports = introspect_all_apps(project_root)

    if not reports:
        print("  No applications found.")
        return

    # Table header
    print(f"  {'App':<22} {'Lang':<12} {'Files':>5} {'Lines':>7} "
          f"{'AST Nodes':>10} {'Funcs':>5} {'Classes':>7} {'Compact':>8}")
    print(f"  {'─'*22} {'─'*12} {'─'*5} {'─'*7} {'─'*10} {'─'*5} {'─'*7} {'─'*8}")

    total_files = 0
    total_lines = 0
    total_nodes = 0
    total_funcs = 0
    total_classes = 0

    for name in sorted(reports.keys()):
        r = reports[name]
        ratio_str = f"{r.avg_compaction_ratio:.1f}x" if r.avg_compaction_ratio > 0 else "N/A"
        print(f"  {name:<22} {r.language:<12} {len(r.files):>5} {r.total_lines:>7,} "
              f"{r.total_ast_nodes:>10,} {r.total_functions:>5} {r.total_classes:>7} {ratio_str:>8}")
        total_files += len(r.files)
        total_lines += r.total_lines
        total_nodes += r.total_ast_nodes
        total_funcs += r.total_functions
        total_classes += r.total_classes

    print(f"  {'─'*22} {'─'*12} {'─'*5} {'─'*7} {'─'*10} {'─'*5} {'─'*7} {'─'*8}")
    print(f"  {'TOTAL':<22} {'':12} {total_files:>5} {total_lines:>7,} "
          f"{total_nodes:>10,} {total_funcs:>5} {total_classes:>7}")

    # Save JSON report
    report_path = os.path.join(project_root, "ast_captures", "introspection_report.json")
    report_data = {name: r.to_dict() for name, r in sorted(reports.items())}
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"\n  Report saved to {report_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="In The Beginning: AST-Driven Reality Simulator"
    )
    parser.add_argument(
        "--ast-introspect", action="store_true",
        help="Run AST self-introspection across all apps and exit",
    )
    parser.add_argument(
        "--sim-only", action="store_true",
        help="Skip the AST demo and run only the simulation",
    )
    args = parser.parse_args()

    if args.ast_introspect:
        run_introspection()
        return

    print(f"\n{BOLD}{YELLOW}")
    print("  ╔══════════════════════════════════════════╗")
    print("  ║       IN THE BEGINNING                   ║")
    print("  ║  AST-Driven Reality Simulator             ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"{RESET}")

    # Phase 1: AST Demo
    if not args.sim_only:
        protocol = run_ast_demo()

    # Phase 2: Simulation
    universe = run_simulation()

    # Phase 3: AST analysis of simulation results
    print(f"\n{BOLD}{CYAN}=== Post-Simulation AST Analysis ==={RESET}\n")

    # Analyze all simulator modules
    engine = ASTEngine()
    sim_dir = os.path.join(os.path.dirname(__file__), "simulator")
    total_nodes = 0
    total_functions = 0
    total_classes = 0

    for fname in sorted(os.listdir(sim_dir)):
        if fname.endswith(".py") and not fname.startswith("__"):
            fpath = os.path.join(sim_dir, fname)
            result = engine.execute(ASTQuery(
                action="metrics", target=fpath, language="python"
            ))
            if result.success and isinstance(result.data, dict):
                d = result.data
                total_nodes += d.get("total_nodes", 0)
                total_functions += d.get("functions", 0)
                total_classes += d.get("classes", 0)
                print(f"  {fname:20s} nodes={d.get('total_nodes', 0):>5} "
                      f"funcs={d.get('functions', 0):>3} "
                      f"classes={d.get('classes', 0):>2} "
                      f"complexity={d.get('cyclomatic_complexity', 0):>3}")

    print(f"\n  {'TOTAL':20s} nodes={total_nodes:>5} "
          f"funcs={total_functions:>3} classes={total_classes:>2}")

    print(f"\n{BOLD}{YELLOW}Done!{RESET}\n")


if __name__ == "__main__":
    main()
