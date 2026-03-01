"""Terminal UI for the reality simulator.

Renders the simulation state to the terminal using Unicode
box-drawing characters and ANSI colors. Designed to work in
any terminal that supports basic ANSI escape codes.
"""
import sys
import os
import math

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BG_BLACK = "\033[40m"

# Box drawing
H_LINE = "\u2500"
V_LINE = "\u2502"
TL_CORNER = "\u250c"
TR_CORNER = "\u2510"
BL_CORNER = "\u2514"
BR_CORNER = "\u2518"
T_DOWN = "\u252c"
T_UP = "\u2534"
T_RIGHT = "\u251c"
T_LEFT = "\u2524"
CROSS = "\u253c"

# Block elements for charts
FULL_BLOCK = "\u2588"
HALF_BLOCK = "\u2584"
LIGHT_SHADE = "\u2591"
MED_SHADE = "\u2592"
DARK_SHADE = "\u2593"
BAR_CHARS = " " + LIGHT_SHADE + MED_SHADE + DARK_SHADE + FULL_BLOCK


def box(title: str, content: list[str], width: int = 60,
        color: str = WHITE) -> str:
    """Draw a box around content."""
    lines = []
    inner = width - 2
    title_str = f" {title} " if title else ""
    pad = inner - len(title_str)
    top = (TL_CORNER + H_LINE * (pad // 2) + title_str
           + H_LINE * (pad - pad // 2) + TR_CORNER)
    lines.append(f"{color}{top}{RESET}")

    for line in content:
        # Strip ANSI for length calculation
        visible = _strip_ansi(line)
        padding = inner - len(visible)
        if padding < 0:
            line = line[:inner]
            padding = 0
        lines.append(f"{color}{V_LINE}{RESET}{line}{' ' * padding}"
                     f"{color}{V_LINE}{RESET}")

    bottom = BL_CORNER + H_LINE * inner + BR_CORNER
    lines.append(f"{color}{bottom}{RESET}")
    return "\n".join(lines)


def _strip_ansi(s: str) -> str:
    """Remove ANSI escape codes for length calculation."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', s)


def progress_bar(value: float, max_val: float, width: int = 30,
                 color: str = GREEN) -> str:
    """Render a progress bar."""
    if max_val <= 0:
        ratio = 0.0
    else:
        ratio = min(1.0, value / max_val)
    filled = int(ratio * width)
    empty = width - filled
    pct = ratio * 100
    return (f"{color}{FULL_BLOCK * filled}{DIM}{LIGHT_SHADE * empty}"
            f"{RESET} {pct:5.1f}%")


def sparkline(values: list[float], width: int = 30) -> str:
    """Render a sparkline chart."""
    if not values:
        return ""
    spark_chars = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
    mn = min(values)
    mx = max(values)
    rng = mx - mn if mx > mn else 1.0

    # Sample values to fit width
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values

    result = ""
    for v in sampled:
        idx = int((v - mn) / rng * (len(spark_chars) - 1))
        result += spark_chars[idx]
    return result


def render_epoch_timeline(current_tick: int, max_ticks: int,
                          epochs: list, width: int = 56) -> list[str]:
    """Render the cosmic epoch timeline."""
    lines = []
    lines.append(f"  {BOLD}Cosmic Timeline{RESET}")
    lines.append(f"  {'=' * width}")

    for epoch in epochs:
        ratio = epoch.start_tick / max_ticks
        pos = int(ratio * (width - 10))
        is_current = (epoch.name == _get_current_epoch(current_tick, epochs))
        marker = f"{YELLOW}>{RESET}" if is_current else " "
        name_colored = (f"{BOLD}{CYAN}{epoch.name}{RESET}"
                        if is_current
                        else f"{DIM}{epoch.name}{RESET}")
        lines.append(f"  {marker} {name_colored}")

    lines.append(f"  {progress_bar(current_tick, max_ticks, width - 2)}")
    return lines


def _get_current_epoch(tick, epochs):
    name = "Void"
    for e in epochs:
        if tick >= e.start_tick:
            name = e.name
    return name


def render_particle_counts(counts: dict) -> list[str]:
    """Render particle type counts."""
    lines = []
    if not counts:
        lines.append(f"  {DIM}(no particles){RESET}")
        return lines
    max_count = max(counts.values()) if counts else 1
    for ptype, count in sorted(counts.items(), key=lambda x: -x[1]):
        bar = progress_bar(count, max_count, 20, MAGENTA)
        lines.append(f"  {ptype:>10}: {count:>5} {bar}")
    return lines


def render_element_counts(counts: dict) -> list[str]:
    """Render element counts with periodic table style."""
    lines = []
    if not counts:
        lines.append(f"  {DIM}(no atoms){RESET}")
        return lines
    max_count = max(counts.values()) if counts else 1
    for sym, count in sorted(counts.items(), key=lambda x: -x[1]):
        bar = progress_bar(count, max_count, 20, CYAN)
        lines.append(f"  {sym:>4}: {count:>5} {bar}")
    return lines


def render_biosphere(biosphere) -> list[str]:
    """Render biosphere statistics."""
    lines = []
    if not biosphere:
        lines.append(f"  {DIM}(no life yet){RESET}")
        return lines

    lines.append(f"  Population:  {BOLD}{len(biosphere.cells)}{RESET}")
    lines.append(f"  Generation:  {biosphere.generation}")
    lines.append(f"  Avg Fitness: "
                 f"{progress_bar(biosphere.average_fitness(), 1.0, 20, GREEN)}")
    lines.append(f"  Avg GC%%:     "
                 f"{progress_bar(biosphere.average_gc_content(), 1.0, 20, BLUE)}")
    lines.append(f"  Total Born:  {biosphere.total_born}")
    lines.append(f"  Total Died:  {biosphere.total_died}")
    lines.append(f"  Mutations:   {biosphere.total_mutations()}")

    # Show top cells
    if biosphere.cells:
        top = sorted(biosphere.cells, key=lambda c: c.fitness, reverse=True)
        lines.append(f"  {DIM}--- Top Cells ---{RESET}")
        for cell in top[:3]:
            lines.append(f"    {cell.to_compact()}")

    return lines


def render_environment(env) -> list[str]:
    """Render environment state."""
    lines = []
    lines.append(f"  Temperature: {env.temperature:>10.1f} K")
    lines.append(f"  UV:          {env.uv_intensity:>10.4f}")
    lines.append(f"  Cosmic Rays: {env.cosmic_ray_flux:>10.4f}")
    lines.append(f"  Atmosphere:  "
                 f"{progress_bar(env.atmospheric_density, 1.0, 20, BLUE)}")
    lines.append(f"  Water:       "
                 f"{progress_bar(env.water_availability, 1.0, 20, CYAN)}")
    hab = f"{GREEN}YES{RESET}" if env.is_habitable() else f"{RED}NO{RESET}"
    lines.append(f"  Habitable:   {hab}")

    if env.events:
        lines.append(f"  {YELLOW}Active Events:{RESET}")
        for ev in env.events[:3]:
            lines.append(f"    {ev.to_compact()}")

    return lines


def render_full_state(universe, width: int = 60) -> str:
    """Render the complete simulation state."""
    from simulator.universe import EPOCHS as EPOCH_LIST
    sections = []

    # Header
    header = box("IN THE BEGINNING", [
        f"  {BOLD}Reality Simulator{RESET} - Tick {universe.tick}/{universe.max_ticks}",
        f"  Epoch: {BOLD}{CYAN}{universe.current_epoch_name}{RESET}",
    ], width, YELLOW)
    sections.append(header)

    # Timeline
    timeline_lines = render_epoch_timeline(
        universe.tick, universe.max_ticks, EPOCH_LIST, width - 4
    )
    sections.append(box("Timeline", timeline_lines, width, BLUE))

    # Quantum Field
    qf_lines = [f"  Temperature: {universe.quantum_field.temperature:.2e} K",
                 f"  Particles:   {len(universe.quantum_field.particles)}"]
    counts = universe.quantum_field.particle_count()
    if counts:
        qf_lines.extend(render_particle_counts(counts))
    sections.append(box("Quantum Field", qf_lines, width, MAGENTA))

    # Atoms
    atom_lines = [f"  Total Atoms: {len(universe.atomic_system.atoms)}"]
    elem_counts = universe.atomic_system.element_counts()
    if elem_counts:
        atom_lines.extend(render_element_counts(elem_counts))
    sections.append(box("Atoms", atom_lines, width, CYAN))

    # Chemistry
    if universe.chemical_system:
        chem_lines = [
            f"  Molecules:   {len(universe.chemical_system.molecules)}",
            f"  Water:       {universe.chemical_system.water_count}",
            f"  Amino Acids: {universe.chemical_system.amino_acid_count}",
            f"  Nucleotides: {universe.chemical_system.nucleotide_count}",
        ]
        sections.append(box("Chemistry", chem_lines, width, GREEN))

    # Biology
    bio_lines = render_biosphere(universe.biosphere)
    sections.append(box("Biosphere", bio_lines, width, GREEN))

    # Environment
    env_lines = render_environment(universe.environment)
    sections.append(box("Environment", env_lines, width, YELLOW))

    # Metrics
    m = universe.metrics
    met_lines = [
        f"  Particles Created: {m.particles_created}",
        f"  Atoms Formed:      {m.atoms_formed}",
        f"  Molecules Formed:  {m.molecules_formed}",
        f"  Cells Born:        {m.cells_born}",
        f"  Total Mutations:   {m.mutations}",
    ]
    sections.append(box("Metrics", met_lines, width, WHITE))

    return "\n".join(sections)


def clear_screen():
    """Clear the terminal screen."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def render_final_report(universe) -> str:
    """Render final simulation report."""
    summary = universe.summary()
    m = summary["metrics"]

    lines = [
        "",
        f"{BOLD}{YELLOW}{'=' * 60}{RESET}",
        f"{BOLD}  SIMULATION COMPLETE - IN THE BEGINNING{RESET}",
        f"{BOLD}{YELLOW}{'=' * 60}{RESET}",
        "",
        f"{BOLD}Performance:{RESET}",
        f"  Wall Time:     {m['wall_time_s']:.3f}s",
        f"  CPU User:      {m['cpu_user_s']:.3f}s",
        f"  CPU System:    {m['cpu_system_s']:.3f}s",
        f"  Peak Memory:   {m['peak_memory_kb']} KB",
        f"  Ticks:         {m['ticks']}",
        "",
        f"{BOLD}Creation:{RESET}",
        f"  Particles:     {m['particles']}",
        f"  Atoms:         {m['atoms']}",
        f"  Molecules:     {m['molecules']}",
        f"  Cells Born:    {m['cells']}",
        f"  Mutations:     {m['mutations']}",
        "",
    ]

    if universe.biosphere and universe.biosphere.cells:
        lines.append(f"{BOLD}Final Biosphere:{RESET}")
        lines.append(f"  Population:    {len(universe.biosphere.cells)}")
        lines.append(f"  Avg Fitness:   "
                     f"{universe.biosphere.average_fitness():.4f}")
        lines.append(f"  Generations:   {universe.biosphere.generation}")
        lines.append(f"  GC Content:    "
                     f"{universe.biosphere.average_gc_content():.4f}")
        lines.append("")

        best = max(universe.biosphere.cells, key=lambda c: c.fitness)
        lines.append(f"  {BOLD}Best Cell:{RESET} {best.to_compact()}")
        lines.append(f"  DNA: {best.dna.to_compact()[:80]}")
        lines.append("")

    # Epoch transitions
    lines.append(f"{BOLD}Epoch Transitions:{RESET}")
    for trans in summary["epoch_transitions"]:
        lines.append(f"  t={trans['tick']:>8} : {trans['from']:>16} -> "
                     f"{CYAN}{trans['to']}{RESET}")
    lines.append("")

    # History sparkline
    if universe.history:
        temps = [s.get("temperature", 0) for s in universe.history]
        lines.append(f"{BOLD}Temperature History:{RESET}")
        lines.append(f"  {sparkline(temps, 50)}")

        if any("cells" in s for s in universe.history):
            pops = [s.get("cells", 0) for s in universe.history]
            lines.append(f"{BOLD}Population History:{RESET}")
            lines.append(f"  {sparkline(pops, 50)}")

    lines.append(f"\n{YELLOW}{'=' * 60}{RESET}")
    return "\n".join(lines)
