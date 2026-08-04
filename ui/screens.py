import os
import random
import time
from typing import List, Optional, Dict, Any

import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns

from game.player import Player, XP_THRESHOLDS
from game.encounter import Encounter
from game.zone_manager import Zone, Node, ZoneManager, StudyCard, NODE_PASS_RATE, STREAK_REQUIRED
from game.combat import CombatResult
from ui.themes import GameTheme, Symbols, Styles, get_hp_color

console = Console()

_QSTYLE = QStyle([
    ("qmark", "fg:#00ffff bold"),
    ("question", "fg:white bold"),
    ("selected", "fg:#00ffff bold"),
    ("pointer", "fg:#00ffff bold"),
    ("answer", "fg:#00ff00 bold"),
    ("highlighted", "fg:#00ffff"),
])

ZONE_NAMES = {
    1: "Zone 1 — The Plains of Concepts",
    2: "Zone 2 — The Forge of Implementation",
    3: "Zone 3 — The Engine Room",
    4: "Zone 4 — The Security Citadel",
    5: "Zone 5 — The Abyss of Debugging",
}

BOSS_NAMES = {
    1: "The OSI Overlord",
    2: "The Routing Warden",
    3: "The Sentinel of Ops",
    4: "The Shadow Firewall",
    5: "The Chaos Engineer",
}


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _hp_bar(hp: int, max_hp: int, width: int = 10) -> str:
    pct = hp / max_hp if max_hp > 0 else 0
    filled = int(pct * width)
    color = get_hp_color(hp, max_hp)
    bar = f"[{color}]{'█' * filled}[/][dim]{'░' * (width - filled)}[/]"
    return bar


def _xp_bar(xp: int, needed: int, width: int = 10) -> str:
    pct = min(xp / needed, 1.0) if needed > 0 else 0
    filled = int(pct * width)
    bar = f"[bright_cyan]{'█' * filled}[/][dim]{'░' * (width - filled)}[/]"
    return bar


def show_header(player: Player) -> None:
    xp_needed = player._xp_for_next_level()
    hp_color = get_hp_color(player.hp, player.max_hp)
    mode_tag = "[bright_yellow]FREE STUDY[/]" if player.free_study_mode else "[dim white]STORY[/]"
    streak_tag = f"  [bright_red]🔥 Streak: {player.streak_days}[/]" if player.streak_days > 0 else ""

    header = (
        f"[bold bright_cyan]{player.name}[/]  "
        f"[bright_yellow]Lvl {player.level}[/]  "
        f"HP: {_hp_bar(player.hp, player.max_hp)} [{hp_color}]{player.hp}/{player.max_hp}[/]  "
        f"XP: {_xp_bar(player.xp, xp_needed)} [bright_cyan]{player.xp}/{xp_needed}[/]  "
        f"[bright_green]💰 {player.bits} BITS[/]  "
        f"{mode_tag}"
        f"{streak_tag}"
    )
    console.print(Panel(header, border_style="bright_blue", padding=(0, 1)))


def show_main_menu(player: Player) -> str:
    clear()
    show_header(player)
    console.print()
    console.print("[bold bright_cyan]  NETWORK+ RPG[/]  [bright_blue]— Restore The Grid. Defeat the 5 Domain Guardians.[/]")
    console.print()

    zones_done = sum(player.guardian_defeated)
    console.print(f"  [dim]Campaign: {zones_done}/5 Guardians defeated[/]")
    console.print()

    choice = questionary.select(
        "Main Menu:",
        choices=[
            questionary.Choice("📅  Daily Study     (today's capped session — build your streak)", value="daily"),
            questionary.Choice("⚔   Story Mode     (zones unlock sequentially)", value="story"),
            questionary.Choice("📚  Free Study      (all zones open — pick any node)", value="free"),
            questionary.Choice("🎯  Weak Spot Drill (auto-targets your worst objectives)", value="drill"),
            questionary.Choice("🧮  Subnetting Trainer (unlimited generated problems)", value="subnet"),
            questionary.Choice("🧪  Hands-On Labs    (command terminal + drag-style PBQs)", value="labs"),
            questionary.Choice("📝  Exam Simulator   (timed 90Q mock, scored 100-900)", value="exam"),
            questionary.Choice("🗓   30-Day Plan     (what should I do today?)", value="plan"),
            questionary.Choice("🔤  Acronym Drill", value="acronym"),
            questionary.Choice("🖧   Field Exercises (CLI Drills & Topology)", value="field"),
            questionary.Choice("📊  Study Report", value="report"),
            questionary.Choice("💾  Save / Load", value="save"),
            questionary.Choice("❌  Quit", value="quit"),
        ],
        style=_QSTYLE,
    ).ask()
    return choice or "quit"


def show_zone_select(zone_manager: ZoneManager, player: Player) -> Optional[int]:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold bright_cyan]WORLD MAP[/]", style="bright_blue"))
    console.print()

    choices = []
    for zone_num in range(1, 6):
        zone = zone_manager.get_zone(zone_num)
        accessible = zone_manager.is_zone_accessible(zone_num, player)
        boss = BOSS_NAMES.get(zone_num, "")
        defeated = player.guardian_defeated[zone_num - 1]

        if zone:
            completed, total = zone.get_completion_stats(player)
            progress = f"{completed}/{total} nodes"
        else:
            progress = "no content"

        if defeated:
            status = "[green]✓ CLEARED[/]"
        elif not accessible:
            status = f"[dim]🔒 {zone_manager.get_locked_reason(zone_num, player)}[/]"
        else:
            status = "[bright_white]UNLOCKED[/]"

        label = f"Zone {zone_num}: {ZONE_NAMES.get(zone_num, '')}  [{progress}]  {boss}"
        if accessible:
            choices.append(questionary.Choice(label, value=zone_num))
        else:
            choices.append(questionary.Choice(f"[LOCKED] Zone {zone_num} — {zone_manager.get_locked_reason(zone_num, player)}", value=None, disabled="locked"))

    choices.append(questionary.Choice("← Back", value="back"))

    result = questionary.select("Select zone:", choices=choices, style=_QSTYLE).ask()
    return None if result in (None, "back") else result


def _get_node_category(node_id: float) -> str:
    """Group nodes by category for cleaner display."""
    if node_id < 1.1:
        return "📚 PREREQUISITES (Start Here)"
    elif node_id < 1.4:
        return "🎯 CORE CONCEPTS"
    elif node_id < 1.41:
        return "🔧 NETWORK SERVICES"
    elif node_id < 1.44:
        return "🔌 FIBER OPTIC (Expanded)"
    elif node_id < 1.5:
        return "🔌 COPPER CABLING (Expanded)"
    elif node_id < 1.6:
        return "💻 ADVANCED TOPICS"
    elif node_id < 1.7:
        return "🗺️  NETWORK DESIGN"
    elif node_id < 1.8:
        return "📍 ADDRESSING"
    else:
        return "🌊 MODERN TECH"


def show_node_map(zone: Zone, player: Player) -> Optional[float]:
    clear()
    show_header(player)
    console.print()
    console.print(Rule(f"[bold bright_cyan]{ZONE_NAMES.get(zone.number, zone.name)}[/]", style="bright_blue"))
    console.print()

    # Group nodes by category
    from collections import OrderedDict
    categorized = OrderedDict()
    for node in zone.nodes:
        cat = _get_node_category(node.id)
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(node)

    choices = []

    for cat, nodes in categorized.items():
        # Add category header
        choices.append(questionary.Choice(f"[bold bright_blue]\n{cat}[/]", value=None, disabled=True))

        for node in nodes:
            correct, total = node.get_completion_stats(player)
            completed = node.is_node_completed(player)
            node_id_str = str(node.id)

            if completed:
                icon = "[green]●[/]"
                status = f"[green]DONE ({correct}/{total})[/]"
            else:
                icon = "[bright_white]○[/]"
                if correct > 0:
                    status = f"[dim]{correct}/{total} correct[/]"
                    # If the pass rate is met but the streak gate isn't, say so —
                    # otherwise a 70%+ node that won't complete looks like a bug.
                    pass_rate_ok = total > 0 and (correct / total) >= NODE_PASS_RATE
                    best_streak = player.node_streaks.get(node_id_str, 0)
                    if pass_rate_ok and best_streak < STREAK_REQUIRED:
                        status += f"  [yellow]needs {STREAK_REQUIRED}-in-a-row (best {best_streak})[/]"
                else:
                    status = "[dim]not started[/]"

            label = f"  {icon} {node.name[:45]:<45} {status}"
            choices.append(questionary.Choice(label, value=node.id))

    # Guardian row
    guardian_count = len(zone.guardian_encounters)
    all_done = zone.all_nodes_completed(player)
    guardian_defeated = player.guardian_defeated[zone.number - 1]

    if guardian_defeated:
        g_label = f"[yellow]👹[/] GUARDIAN: {BOSS_NAMES.get(zone.number)} — [green]DEFEATED[/]"
    elif all_done:
        g_label = f"[yellow]👹[/] GUARDIAN: {BOSS_NAMES.get(zone.number)} — [bright_red]CHALLENGE ({guardian_count} questions)[/]"
    else:
        g_label = f"[dim]👹 GUARDIAN: {BOSS_NAMES.get(zone.number)} — Complete all nodes first[/]"

    if guardian_defeated or all_done:
        choices.append(questionary.Choice(g_label, value=-1.0))
    else:
        choices.append(questionary.Choice(g_label, value=None, disabled="complete all nodes first"))

    choices.append(questionary.Choice("← Back", value="back"))

    result = questionary.select("Select node:", choices=choices, style=_QSTYLE).ask()
    return None if result in (None, "back") else result


def show_encounter(encounter: Encounter, player: Player, question_num: int = 1, total: int = 1) -> Optional[int]:
    clear()
    show_header(player)
    console.print()

    diff_color = {"easy": "green", "medium": "yellow", "hard": "red", "boss": "bright_red"}.get(
        encounter.difficulty, "white"
    )
    console.print(
        f"  [dim]Question {question_num}/{total}[/]  "
        f"[{diff_color}]{encounter.difficulty.upper()}[/]  "
        f"[dim]ID: {encounter.id}[/]"
    )
    if encounter.tags:
        console.print(f"  [dim]Tags: {', '.join(encounter.tags)}[/]")
    console.print()

    # Show scenario/study content first (if present)
    if encounter.scenario:
        console.print(Panel(
            f"[bright_white]{encounter.scenario}[/]",
            border_style="bright_blue",
            title="[bright_blue]STUDY CONTENT[/]",
            padding=(1, 2),
        ))
        console.print()

    if encounter.ascii_diagram:
        console.print(Panel(
            f"[bright_white]{encounter.ascii_diagram}[/]",
            border_style="bright_magenta",
            title="[bright_magenta]NETWORK TOPOLOGY[/]",
            padding=(1, 2),
        ))
        console.print()

    console.print(Panel(
        f"[bold bright_white]{encounter.question}[/]",
        border_style="bright_cyan",
        title="[bright_cyan]QUESTION[/]",
        padding=(1, 2),
    ))
    console.print()

    option_labels = ["A", "B", "C", "D"]
    choices = []
    for i, option in enumerate(encounter.options):
        label = f"  [{option_labels[i]}]  {option}"
        choices.append(questionary.Choice(label, value=i))

    result = questionary.select("Your answer:", choices=choices, style=_QSTYLE).ask()
    if result is None:
        return None
    return result


def show_cli_encounter(encounter: Encounter, player: Player, question_num: int = 1, total: int = 1) -> Optional[str]:
    clear()
    show_header(player)
    console.print()

    diff_color = {"easy": "green", "medium": "yellow", "hard": "red", "boss": "bright_red"}.get(
        encounter.difficulty, "white"
    )
    console.print(
        f"  [dim]Question {question_num}/{total}[/]  "
        f"[{diff_color}]{encounter.difficulty.upper()}[/]  "
        f"[dim]ID: {encounter.id}[/]"
    )
    if encounter.tags:
        console.print(f"  [dim]Tags: {', '.join(encounter.tags)}[/]")
    console.print()

    console.print(Panel(
        f"[bright_white]{encounter.scenario}[/]\n\n"
        f"[bold bright_cyan]Objective:[/] {encounter.objective}",
        border_style="bright_cyan",
        title="[bright_cyan]CLI CHALLENGE[/]",
        padding=(1, 2),
    ))
    console.print()

    prompt_label = f"{encounter.command_prompt} " if encounter.command_prompt else "$ "

    answer = questionary.text(prompt_label, style=_QSTYLE).ask()
    if answer is None:
        return None
    answer = answer.strip()

    if not encounter.check_cli_answer(answer) and encounter.hint:
        console.print(f"\n  [yellow]💡 Hint: {encounter.hint}[/]")
        console.print("  [dim]One more try...[/]\n")
        retry = questionary.text(prompt_label, style=_QSTYLE).ask()
        if retry is None:
            return answer
        answer = retry.strip()

    return answer


def show_combat_result(result: CombatResult, player: Player) -> None:
    console.print()
    enc = result.encounter
    option_labels = ["A", "B", "C", "D"]

    if result.is_correct:
        console.print(Panel(
            f"[bold bright_green]✓ CORRECT![/]\n\n"
            f"[bright_green]+{result.xp_gained} XP[/]  [bright_green]+{result.bits_gained} BITS[/]",
            border_style="green",
            title="[green]HIT[/]",
        ))
    else:
        correct_letter = option_labels[enc.correct_index] if enc.correct_index < len(option_labels) else "?"
        console.print(Panel(
            f"[bold red]✗ WRONG[/]  [dim](+{result.xp_gained} XP encouragement)[/]\n\n"
            f"[bright_white]Correct answer: [{correct_letter}] {enc.get_correct_answer()}[/]",
            border_style="red",
            title="[red]MISS — {0} HP[/]".format(result.hp_lost) if result.hp_lost else "[red]MISS[/]",
        ))

    console.print()
    console.print(Panel(
        f"[bright_blue]{enc.explanation}[/]",
        border_style="bright_blue",
        title="[bright_blue]EXPLANATION[/]",
        padding=(1, 2),
    ))

    if player.hp <= 0:
        console.print("\n[bold red]⚠ YOU HAVE RUN OUT OF HP. Session ended.[/]")
        console.print("[dim]HP resets next session. Your progress is saved.[/]\n")

    console.print()
    input("  Press Enter to continue...")


def show_level_up(player: Player, old_level: int) -> None:
    clear()
    console.print()
    console.print(Panel(
        f"[bold bright_yellow]★ LEVEL UP! ★[/]\n\n"
        f"[dim]Level {old_level}[/] → [bold bright_yellow]Level {player.level}[/]\n\n"
        f"[bright_green]Max HP: {player.max_hp}[/]\n"
        f"[bright_cyan]New XP threshold: {player._xp_for_next_level()}[/]"
        + (f"\n[bright_magenta]Skill unlocked: {player.skills[-1]}[/]" if player.skills else ""),
        border_style="bright_yellow",
        title="[bold bright_yellow]LEVEL UP[/]",
        padding=(1, 4),
    ))
    console.print()
    input("  Press Enter to continue...")


def show_node_complete(node: Node) -> None:
    console.print()
    console.print(Panel(
        f"[bold bright_green]NODE CLEARED[/]\n\n"
        f"[bright_white]{node.name}[/] — complete!\n"
        f"[dim]Spaced repetition will reinforce weak questions.[/]",
        border_style="green",
        title="[green]✓ NODE COMPLETE[/]",
    ))
    console.print()
    input("  Press Enter to continue...")


def show_guardian_intro(zone: Zone) -> None:
    clear()
    boss = BOSS_NAMES.get(zone.number, "The Guardian")
    q_count = len(zone.guardian_encounters)
    console.print()
    console.print(Panel(
        f"[bold bright_red]⚠ GUARDIAN BATTLE[/]\n\n"
        f"[bright_red]{boss}[/] awaits.\n\n"
        f"[white]{q_count} questions — score ≥75% (≥{int(q_count * 0.75)} correct) to defeat the guardian.[/]\n\n"
        f"[dim]Wrong answers still cost HP (unless Free Study).\n"
        f"Retry available after completing 10 more encounters.[/]",
        border_style="bright_red",
        title="[bright_red]GUARDIAN BATTLE[/]",
        padding=(1, 2),
    ))
    console.print()
    proceed = questionary.confirm("Enter battle?", default=True, style=_QSTYLE).ask()
    if not proceed:
        return


def show_guardian_result(passed: bool, score: int, total: int, player: Player, zone_num: int) -> None:
    clear()
    pct = int(score / total * 100) if total else 0
    boss = BOSS_NAMES.get(zone_num, "Guardian")
    if passed:
        console.print(Panel(
            f"[bold bright_green]✓ GUARDIAN DEFEATED[/]\n\n"
            f"[bright_white]{boss}[/] has fallen!\n\n"
            f"Score: [bright_green]{score}/{total} ({pct}%)[/]\n\n"
            f"[bright_yellow]+1000 XP  +200 BITS  Zone Badge[/]\n"
            + (f"[dim]Zone {zone_num + 1} is now accessible.[/]" if zone_num < 5 else "[bright_yellow]ALL ZONES CLEARED![/]"),
            border_style="bright_green",
            title="[bright_green]VICTORY[/]",
            padding=(1, 2),
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ GUARDIAN NOT DEFEATED[/]\n\n"
            f"Score: [red]{score}/{total} ({pct}%)[/]  Need ≥75%\n\n"
            f"[dim]Complete 10 more encounters to retry, or spend BITS for instant retry.[/]",
            border_style="red",
            title="[red]DEFEAT[/]",
            padding=(1, 2),
        ))
    console.print()
    input("  Press Enter to continue...")


def show_save_menu(saves: List[Dict[str, Any]]) -> Optional[int]:
    clear()
    console.print()
    console.print(Rule("[bold bright_cyan]SAVE / LOAD[/]", style="bright_blue"))
    console.print()

    choices = []
    for s in saves:
        slot = s["slot"]
        if s["exists"] and s["name"] != "Corrupted":
            label = f"Slot {slot}: {s['name']}  (Level {s['level']}, 💰 {s.get('bits', 0)} BITS)"
        elif s["exists"]:
            label = f"Slot {slot}: [CORRUPTED]"
        else:
            label = f"Slot {slot}: — empty —"
        choices.append(questionary.Choice(label, value=slot))

    choices.append(questionary.Choice("← Back", value="back"))
    result = questionary.select("Select slot:", choices=choices, style=_QSTYLE).ask()
    return None if result in (None, "back") else result


def show_new_game_prompt() -> Optional[str]:
    clear()
    console.print()
    console.print(Rule("[bold bright_cyan]NEW GAME[/]", style="bright_blue"))
    console.print()
    name = questionary.text(
        "Enter your Network Initiate name:",
        validate=lambda x: len(x.strip()) > 0 or "Name cannot be empty",
        style=_QSTYLE,
    ).ask()
    return name.strip() if name else None


# ---------------------------------------------------------------------------
# Daily Study
# ---------------------------------------------------------------------------

def show_daily_intro(console: Console, player: Player, question_count: int) -> None:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold bright_cyan]📅 DAILY STUDY[/]", style="bright_blue"))
    console.print()
    if player.streak_days > 0:
        streak_line = (
            f"[bright_red]🔥 Current streak: {player.streak_days} day(s)[/]  "
            f"[dim](longest: {player.longest_streak})[/]"
        )
    else:
        streak_line = "[dim]Start your streak today![/]"
    console.print(f"  Welcome back, [bold bright_cyan]{player.name}[/]. {streak_line}")
    console.print(
        f"  [dim]{question_count} questions queued (daily cap: {player.daily_question_cap}).[/]"
    )
    console.print(
        "  [dim]HP works like hearts — wrong answers cost HP, hitting 0 ends the session early.[/]"
    )
    console.print()
    input("  Press Enter to begin today's session...")


def show_daily_already_done(console: Console, player: Player) -> None:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold bright_cyan]📅 DAILY STUDY[/]", style="bright_blue"))
    console.print()
    console.print(Panel(
        f"[bold bright_green]✓ Already done for today![/]\n\n"
        f"[bright_red]🔥 Streak: {player.streak_days} day(s)[/]  "
        f"[dim](longest: {player.longest_streak})[/]\n\n"
        f"[dim]Come back tomorrow to keep your streak alive.[/]",
        border_style="bright_green",
        title="[green]DAILY STUDY[/]",
        padding=(1, 2),
    ))
    console.print()
    input("  Press Enter to continue...")


def show_daily_summary(console: Console, player: Player, results: Dict[str, Any]) -> None:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold bright_cyan]📅 DAILY STUDY COMPLETE[/]", style="bright_blue"))
    console.print()

    attempted = results.get("attempted", 0)
    correct = results.get("correct", 0)
    pct = int(correct / attempted * 100) if attempted else 0
    color = "bright_green" if pct >= 80 else ("yellow" if pct >= 60 else "red")
    hp_lost = results.get("hp_lost", 0)

    console.print(Panel(
        f"[bold {color}]{correct}/{attempted} correct ({pct}%)[/]\n\n"
        f"[bright_yellow]+{results.get('xp_gained', 0)} XP[/]  "
        f"[bright_green]+{results.get('bits_gained', 0)} BITS[/]"
        + (f"  [red]-{hp_lost} HP[/]" if hp_lost else "")
        + f"\n\n[bright_red]🔥 Streak: {player.streak_days} day(s)[/]  "
        f"[dim](longest: {player.longest_streak})[/]",
        border_style=color,
        title="[bold]DAILY STUDY RESULTS[/]",
        padding=(1, 2),
    ))
    console.print()
    input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Subnetting Trainer
# ---------------------------------------------------------------------------

def show_subnet_intro():
    """Returns (count, mode) where mode is 'mc' or 'type', or None to cancel."""
    clear()
    console.print()
    console.print(Rule("[bold bright_cyan]🧮 SUBNETTING TRAINER[/]", style="bright_blue"))
    console.print()
    console.print("  [dim]Fresh randomized problems every time — network/broadcast addresses,[/]")
    console.print("  [dim]usable hosts, masks, ranges. No HP risk. Build muscle memory.[/]")
    console.print()
    mode = questionary.select(
        "Answer format?",
        choices=[
            questionary.Choice("⌨   Type the answer  (real calculation — recommended)", value="type"),
            questionary.Choice("☰   Multiple choice  (recognition)", value="mc"),
            questionary.Choice("← Back", value=None),
        ],
        style=_QSTYLE,
    ).ask()
    if mode is None:
        return None
    count = questionary.select(
        "How many problems?",
        choices=[
            questionary.Choice("10 — quick warm-up", value=10),
            questionary.Choice("20 — solid set", value=20),
            questionary.Choice("50 — grind to fluency", value=50),
            questionary.Choice("← Back", value=None),
        ],
        style=_QSTYLE,
    ).ask()
    if count is None:
        return None
    return (count, mode)


def show_subnet_free(problem, num: int, total: int, hint: str) -> Optional[str]:
    """Free-entry subnetting question. Returns the typed answer, or None to quit."""
    clear()
    console.print()
    console.print(f"  [dim]Problem {num}/{total}[/]   [dim]({hint})[/]")
    console.print()
    console.print(Panel(
        f"[bold bright_white]{problem.question}[/]",
        border_style="bright_cyan", title="[bright_cyan]SUBNETTING[/]", padding=(1, 2),
    ))
    console.print()
    ans = questionary.text("Your answer (or 'q' to stop):", style=_QSTYLE).ask()
    if ans is None or ans.strip().lower() in ("q", "quit", "exit"):
        return None
    return ans


def show_subnet_free_result(is_correct: bool, expected: str, explanation: str) -> None:
    console.print()
    if is_correct:
        console.print(Panel("[bold bright_green]✓ CORRECT[/]", border_style="green", title="[green]HIT[/]"))
    else:
        console.print(Panel(
            f"[bold red]✗ NOT QUITE[/]\n\n[bright_white]Correct answer: {expected}[/]",
            border_style="red", title="[red]MISS[/]",
        ))
    console.print(Panel(f"[bright_blue]{explanation}[/]", border_style="bright_blue", padding=(1, 2)))
    console.print()
    input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Hands-On Labs: Command Lab (simulated terminal) + PBQ ordering/matching
# ---------------------------------------------------------------------------

def show_labs_menu() -> Optional[str]:
    clear()
    console.print()
    console.print(Rule("[bold bright_magenta]🧪 HANDS-ON LABS[/]", style="bright_magenta"))
    console.print()
    console.print("  [dim]Do the task instead of recognizing an answer — closest thing to the[/]")
    console.print("  [dim]exam's performance-based questions (PBQs).[/]")
    console.print()
    return questionary.select(
        "Choose a lab:",
        choices=[
            questionary.Choice("💻  Command Lab    — diagnose a broken network in a simulated terminal", value="command"),
            questionary.Choice("🔀  PBQ Drills     — order steps / match items (drag-style)", value="pbq"),
            questionary.Choice("← Back", value="back"),
        ],
        style=_QSTYLE,
    ).ask()


def show_command_lab_select(scenarios):
    clear()
    console.print()
    console.print(Rule("[bold bright_magenta]💻 COMMAND LAB[/]", style="bright_magenta"))
    console.print()
    choices = [questionary.Choice(f"{s.title}", value=s) for s in scenarios]
    choices.append(questionary.Choice("← Back", value=None))
    return questionary.select("Pick a scenario to troubleshoot:", choices=choices, style=_QSTYLE).ask()


def show_command_lab_brief(scenario) -> None:
    clear()
    console.print()
    console.print(Rule(f"[bold bright_magenta]💻 {scenario.title}[/]", style="bright_magenta"))
    console.print()
    console.print(Panel(f"[bright_white]{scenario.brief}[/]", border_style="yellow",
                        title="[yellow]TICKET[/]", padding=(1, 2)))
    console.print()
    console.print("  [dim]Type commands to investigate. 'help' lists commands, "
                  "'solve' to diagnose, 'quit' to leave.[/]")
    console.print()


def show_command_lab_help(scenario) -> None:
    console.print()
    console.print("  [bright_cyan]Commands you can try here:[/]")
    for c in scenario.available:
        console.print(f"    [bright_green]$[/] {c}")
    console.print("    [dim]help · solve · quit[/]")
    console.print()


def command_lab_prompt(scenario) -> Optional[str]:
    return questionary.text(f"{scenario.id}$", qmark="", style=_QSTYLE).ask()


def show_command_output(cmd: str, output: str) -> None:
    console.print()
    console.print(f"  [bright_green]$ {cmd}[/]")
    console.print(Panel(f"[white]{output}[/]", border_style="bright_black", padding=(0, 2)))


def show_lab_question(question: str, options: List[str]) -> Optional[int]:
    console.print()
    console.print(Panel(f"[bold bright_white]{question}[/]", border_style="bright_cyan",
                        title="[bright_cyan]DIAGNOSIS[/]", padding=(1, 2)))
    labels = ["A", "B", "C", "D", "E"]
    choices = [questionary.Choice(f"  [{labels[i]}]  {o}", value=i) for i, o in enumerate(options)]
    return questionary.select("Your diagnosis:", choices=choices, style=_QSTYLE).ask()


def show_lab_answer(is_correct: bool, correct_text: str, explanation: str) -> None:
    console.print()
    if is_correct:
        console.print(Panel("[bold bright_green]✓ CORRECT DIAGNOSIS[/]", border_style="green", title="[green]SOLVED[/]"))
    else:
        console.print(Panel(f"[bold red]✗ NOT THE ROOT CAUSE[/]\n\n[bright_white]Correct: {correct_text}[/]",
                            border_style="red", title="[red]MISS[/]"))
    console.print(Panel(f"[bright_blue]{explanation}[/]", border_style="bright_blue", padding=(1, 2)))
    console.print()
    input("  Press Enter to continue...")


def show_pbq_menu() -> Optional[str]:
    clear()
    console.print()
    console.print(Rule("[bold bright_magenta]🔀 PBQ DRILLS[/]", style="bright_magenta"))
    console.print()
    return questionary.select(
        "Task type:",
        choices=[
            questionary.Choice("🔢  Ordering   — put steps/layers in the right sequence", value="order"),
            questionary.Choice("🔗  Matching   — match items to their pair", value="match"),
            questionary.Choice("← Back", value="back"),
        ],
        style=_QSTYLE,
    ).ask()


def pick_pbq(tasks, prompt: str):
    choices = [questionary.Choice(t.prompt, value=t) for t in tasks]
    choices.append(questionary.Choice("← Back", value=None))
    return questionary.select(prompt, choices=choices, style=_QSTYLE).ask()


def run_ordering_task(task) -> Optional[List[str]]:
    """Build an order by picking each position from the remaining items."""
    clear()
    console.print()
    console.print(Panel(f"[bold bright_white]{task.prompt}[/]", border_style="bright_cyan",
                        title="[bright_cyan]ORDER THE STEPS[/]", padding=(1, 2)))
    remaining = list(task.ordered)
    random.shuffle(remaining)
    chosen: List[str] = []
    for position in range(1, len(task.ordered) + 1):
        choices = [questionary.Choice(item, value=item) for item in remaining]
        choices.append(questionary.Choice("✗ Cancel", value=None))
        pick = questionary.select(f"Position {position}:", choices=choices, style=_QSTYLE).ask()
        if pick is None:
            return None
        chosen.append(pick)
        remaining.remove(pick)
    return chosen


def show_pbq_result(is_correct: bool, correct_order: List[str], explanation: str) -> None:
    console.print()
    if is_correct:
        console.print(Panel("[bold bright_green]✓ PERFECT ORDER[/]", border_style="green", title="[green]CORRECT[/]"))
    else:
        body = "[bold red]✗ Not quite.[/] [bright_white]Correct order:[/]\n\n" + \
            "\n".join(f"  [bright_green]{i}.[/] {s}" for i, s in enumerate(correct_order, 1))
        console.print(Panel(body, border_style="red", title="[red]REVIEW[/]", padding=(1, 2)))
    console.print(Panel(f"[bright_blue]{explanation}[/]", border_style="bright_blue", padding=(1, 2)))
    console.print()
    input("  Press Enter to continue...")


def run_matching_task(task):
    """For each left item, pick its match from the (shuffled) right options.

    Returns (all_correct, num_right, total) or None if cancelled.
    """
    clear()
    console.print()
    console.print(Panel(f"[bold bright_white]{task.prompt}[/]", border_style="bright_cyan",
                        title="[bright_cyan]MATCH THE PAIRS[/]", padding=(1, 2)))
    rights = [r for _l, r in task.pairs]
    shuffled = list(rights)
    random.shuffle(shuffled)
    n_right = 0
    for left, correct_right in task.pairs:
        choices = [questionary.Choice(r, value=r) for r in shuffled]
        choices.append(questionary.Choice("✗ Cancel", value=None))
        pick = questionary.select(f"{left}  →", choices=choices, style=_QSTYLE).ask()
        if pick is None:
            return None
        if pick == correct_right:
            n_right += 1
    return (n_right == len(task.pairs), n_right, len(task.pairs))


def show_pbq_match_result(is_correct: bool, n_right: int, total: int, pairs, explanation: str) -> None:
    console.print()
    color = "green" if is_correct else "red"
    head = "✓ ALL MATCHED" if is_correct else f"✗ {n_right}/{total} correct"
    console.print(Panel(f"[bold bright_{color}]{head}[/]", border_style=color, title=f"[{color}]RESULT[/]"))
    if not is_correct:
        body = "[bright_white]Correct pairs:[/]\n\n" + \
            "\n".join(f"  [bright_green]{l}[/] → {r}" for l, r in pairs)
        console.print(Panel(body, border_style="bright_black", padding=(1, 2)))
    console.print(Panel(f"[bright_blue]{explanation}[/]", border_style="bright_blue", padding=(1, 2)))
    console.print()
    input("  Press Enter to continue...")


def show_subnet_summary(correct: int, total: int) -> None:
    console.print()
    if total == 0:
        return
    pct = int(correct / total * 100)
    color = "bright_green" if pct >= 80 else ("yellow" if pct >= 60 else "red")
    console.print(Panel(
        f"[bold {color}]Subnetting set complete — {correct}/{total} correct ({pct}%)[/]\n"
        f"[dim]Aim for 90%+ before exam day; subnetting points are guaranteed if you're fluent.[/]",
        border_style=color,
        title="[bold]🧮 RESULTS[/]",
    ))
    console.print()
    input("  Press Enter to continue...")


# ---------------------------------------------------------------------------
# Exam Simulator
# ---------------------------------------------------------------------------

def show_exam_intro() -> bool:
    from game import exam
    clear()
    console.print()
    console.print(Rule("[bold bright_red]📝 EXAM SIMULATOR[/]", style="bright_red"))
    console.print()
    console.print(Panel(
        f"[bright_white]{exam.EXAM_QUESTIONS} questions • {exam.EXAM_MINUTES} minute clock • "
        f"scored {exam.SCALE_MIN}–{exam.SCALE_MAX} ({exam.PASS_SCORE} to pass)[/]\n\n"
        "[dim]Questions are domain-weighted like the real N10-009. No answers or\n"
        "explanations shown until the end — just like the real thing. Your answers\n"
        "still feed weak-spot tracking. Treat it like the real exam: no notes.[/]",
        border_style="bright_red",
        title="[bright_red]MOCK EXAM[/]",
    ))
    console.print()
    confirm = questionary.confirm("Start the timed exam now?", default=False, style=_QSTYLE).ask()
    return bool(confirm)


def _fmt_clock(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def show_exam_question(encounter: Encounter, player: Player, num: int, total: int,
                       seconds_remaining: float) -> Optional[int]:
    clear()
    time_color = "bright_green" if seconds_remaining > 600 else (
        "yellow" if seconds_remaining > 120 else "bright_red")
    console.print()
    console.print(
        f"  [dim]Question {num}/{total}[/]        "
        f"[{time_color}]⏱  {_fmt_clock(seconds_remaining)} remaining[/]"
    )
    console.print()
    console.print(Panel(
        f"[bold bright_white]{encounter.question}[/]",
        border_style="bright_cyan",
        title="[bright_cyan]EXAM QUESTION[/]",
        padding=(1, 2),
    ))
    console.print()
    option_labels = ["A", "B", "C", "D"]
    choices = [
        questionary.Choice(f"  [{option_labels[i]}]  {opt}", value=i)
        for i, opt in enumerate(encounter.options)
    ]
    return questionary.select("Your answer:", choices=choices, style=_QSTYLE).ask()


def show_exam_result(result, zone_manager: ZoneManager) -> None:
    from game import exam
    clear()
    console.print()
    console.print(Rule("[bold bright_red]📝 EXAM RESULTS[/]", style="bright_red"))
    console.print()

    verdict_color = "bright_green" if result.passed else "red"
    verdict = "PASS ✓" if result.passed else "FAIL ✗"
    over = "  [bright_red](over the {0}-min limit)[/]".format(exam.EXAM_MINUTES) if result.over_time else ""
    console.print(Panel(
        f"[bold {verdict_color}]{verdict}   Scaled score: {result.score} / {exam.SCALE_MAX}[/]\n"
        f"[bright_white]{result.correct}/{result.total} correct ({result.accuracy_pct:.0f}%)[/]   "
        f"[dim]Pass line: {exam.PASS_SCORE}[/]\n"
        f"[dim]Time: {_fmt_clock(result.seconds)}{over}[/]",
        border_style=verdict_color,
        title="[bold]VERDICT[/]",
    ))
    console.print(
        "  [dim]Scaled score is a linear estimate of CompTIA's scale — treat it as a "
        "guide, not a guarantee.[/]"
    )
    console.print()

    dt = Table(title="Score by Domain", title_style="bold bright_cyan")
    dt.add_column("Domain", style="white")
    dt.add_column("Score", style="white")
    dt.add_column("Bar", style="white")
    for zone_num, d in sorted(result.per_domain.items()):
        pct = int(d["correct"] / d["total"] * 100) if d["total"] else 0
        c = "bright_green" if pct >= 80 else ("yellow" if pct >= 70 else "red")
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        dt.add_row(
            exam.DOMAIN_NAMES.get(zone_num, str(zone_num)),
            f"[{c}]{d['correct']}/{d['total']} ({pct}%)[/]",
            f"[{c}]{bar}[/]",
        )
    console.print(dt)
    console.print()

    weakest = min(result.per_domain.items(),
                  key=lambda kv: (kv[1]["correct"] / kv[1]["total"]) if kv[1]["total"] else 1.0,
                  default=None)
    if weakest and weakest[1]["total"]:
        wpct = int(weakest[1]["correct"] / weakest[1]["total"] * 100)
        if wpct < 80:
            console.print(
                f"  [yellow]➜ Focus next: {exam.DOMAIN_NAMES.get(weakest[0])} "
                f"({wpct}%). Run Weak Spot Drill on it.[/]"
            )
    console.print()
    input("  Press Enter to continue...")


def show_study_plan(player: Player) -> None:
    """Show today's plan + let the player browse the full 30-day schedule."""
    from game import study_plan

    view_day = study_plan.current_day(player.start_date)
    while True:
        clear()
        show_header(player)
        console.print()
        console.print(Rule("[bold bright_cyan]🗓  30-DAY STUDY PLAN[/]", style="bright_blue"))
        console.print()

        today = study_plan.current_day(player.start_date)
        remaining = study_plan.days_until_exam(player.start_date)
        if today <= study_plan.PLAN_LENGTH:
            rc = "bright_green" if remaining > 10 else ("yellow" if remaining > 3 else "bright_red")
            console.print(
                f"  [dim]Today is[/] [bold]Day {today}[/] [dim]of {study_plan.PLAN_LENGTH}[/]   "
                f"[{rc}]{max(0, remaining - 1)} days left until exam day[/]"
            )
        else:
            console.print(f"  [bright_green]You're past Day {study_plan.PLAN_LENGTH} — exam time! Keep drilling weak spots.[/]")
        console.print()

        plan = study_plan.get_day(view_day)
        if plan:
            tag = " [bright_yellow](TODAY)[/]" if view_day == today else ""
            console.print(Panel(
                f"[bold bright_white]Day {plan['day']} — {plan['focus']}[/]{tag}\n"
                f"[dim]Phase: {plan['phase']}  •  Week {study_plan.week_of(view_day)}[/]\n\n"
                + "\n".join(f"  [bright_green]☐[/] {t}" for t in plan["tasks"]),
                border_style="bright_cyan" if view_day == today else "bright_blue",
                padding=(1, 2),
            ))
        console.print()

        nav = []
        if view_day > 1:
            nav.append(questionary.Choice("← Previous day", value="prev"))
        if view_day < study_plan.PLAN_LENGTH:
            nav.append(questionary.Choice("Next day →", value="next"))
        if view_day != today and today <= study_plan.PLAN_LENGTH:
            nav.append(questionary.Choice("⊙  Jump to today", value="today"))
        nav.append(questionary.Choice("↩  Back to menu", value="back"))

        action = questionary.select(f"Day {view_day}:", choices=nav, style=_QSTYLE).ask()
        if action in (None, "back"):
            return
        elif action == "prev":
            view_day = max(1, view_day - 1)
        elif action == "next":
            view_day = min(study_plan.PLAN_LENGTH, view_day + 1)
        elif action == "today":
            view_day = min(study_plan.PLAN_LENGTH, today)


def show_study_report(player: Player, zone_manager: ZoneManager) -> None:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold bright_cyan]STUDY REPORT[/]", style="bright_blue"))
    console.print()

    table = Table(
        title="Zone Accuracy",
        border_style="bright_blue",
        header_style="bold bright_cyan",
    )
    table.add_column("Zone", style="bright_white")
    table.add_column("Domain", style="white")
    table.add_column("Nodes", style="white")
    table.add_column("Accuracy", style="white")
    table.add_column("Status", style="white")

    total_answered = len(player.encounter_results)
    total_correct = sum(1 for v in player.encounter_results.values() if v)

    zone_domains = {
        1: "Networking Concepts (23%)",
        2: "Network Implementation (20%)",
        3: "Network Operations (19%)",
        4: "Network Security (14%)",
        5: "Network Troubleshooting (24%)",
    }

    for zone_num in range(1, 6):
        zone = zone_manager.get_zone(zone_num)
        domain = zone_domains.get(zone_num, "")
        status = "[green]✓ CLEARED[/]" if player.guardian_defeated[zone_num - 1] else (
            "[bright_white]In Progress[/]" if zone_manager.is_zone_accessible(zone_num, player) else "[dim]Locked[/]"
        )

        if zone:
            completed, total_nodes = zone.get_completion_stats(player)
            nodes_str = f"{completed}/{total_nodes}"

            zone_enc_ids = {enc.id for node in zone.nodes for enc in node.encounters}
            zone_enc_ids |= {enc.id for enc in zone.guardian_encounters}
            answered = [player.encounter_results[eid] for eid in zone_enc_ids if eid in player.encounter_results]
            if answered:
                pct = int(sum(answered) / len(answered) * 100)
                acc_color = "bright_green" if pct >= 75 else ("yellow" if pct >= 50 else "red")
                acc_str = f"[{acc_color}]{pct}% ({sum(answered)}/{len(answered)})[/]"
            else:
                acc_str = "[dim]No data[/]"
        else:
            nodes_str = "[dim]no content[/]"
            acc_str = "[dim]—[/]"

        table.add_row(f"Zone {zone_num}", domain, nodes_str, acc_str, status)

    console.print(table)
    console.print()

    if total_answered > 0:
        overall_pct = int(total_correct / total_answered * 100)
        color = "bright_green" if overall_pct >= 75 else ("yellow" if overall_pct >= 50 else "red")
        console.print(f"  Overall accuracy: [{color}]{overall_pct}% ({total_correct}/{total_answered})[/]")

        sr_count = len(player.wrong_answer_ids)
        if sr_count:
            console.print(f"  [yellow]{sr_count} questions queued for spaced repetition review[/]")

    _show_mastery_breakdown(player, zone_manager)

    console.print()
    input("  Press Enter to continue...")


def _show_mastery_breakdown(player: Player, zone_manager: ZoneManager) -> None:
    """Readiness summary + the objectives most in need of work."""
    from game import mastery

    rd = mastery.overall_readiness(player, zone_manager)
    console.print()
    m_color = "bright_green" if rd["mastery_pct"] >= 80 else ("yellow" if rd["mastery_pct"] >= 50 else "red")
    console.print(
        f"  [bold]Exam readiness:[/] [{m_color}]{rd['mastery_pct']:.0f}% mastered[/]  "
        f"[dim]({rd['learned']}/{rd['total_questions']} questions learned • "
        f"{rd['coverage_pct']:.0f}% seen • {rd['accuracy_pct']:.0f}% lifetime accuracy)[/]"
    )

    weak = mastery.weak_objectives(player, zone_manager, limit=6)
    if not weak:
        console.print("  [dim]Answer more questions to reveal your weak spots.[/]")
        return

    console.print()
    wt = Table(title="🎯 Your Weakest Objectives — drill these first", title_style="bold yellow")
    wt.add_column("Zone", style="bright_white")
    wt.add_column("Objective", style="white")
    wt.add_column("Accuracy", style="white")
    wt.add_column("Mastered", style="white")
    for s in weak:
        acc = int(s.accuracy * 100)
        acc_color = "red" if acc < 70 else "yellow"
        wt.add_row(
            f"Z{s.zone}", s.name,
            f"[{acc_color}]{acc}%[/]",
            f"[dim]{s.learned}/{s.total_questions}[/]",
        )
    console.print(wt)


def show_drill_intro(player: Player, zone_manager: ZoneManager, count: int) -> None:
    from game import mastery
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold yellow]🎯 WEAK SPOT DRILL[/]", style="yellow"))
    console.print()
    weak = mastery.weak_objectives(player, zone_manager, limit=3)
    if weak:
        names = ", ".join(s.name for s in weak)
        console.print(f"  Targeting your weakest objectives: [yellow]{names}[/]")
    console.print(
        f"  [dim]{count} questions queued — recently-missed and not-yet-mastered first.[/]"
    )
    console.print(f"  [dim]No HP risk here — this is pure study.[/]")
    console.print()
    input("  Press Enter to begin...")


def show_drill_empty(player: Player, zone_manager: ZoneManager) -> None:
    clear()
    show_header(player)
    console.print()
    console.print(Rule("[bold yellow]🎯 WEAK SPOT DRILL[/]", style="yellow"))
    console.print()
    console.print(
        "  [bright_green]Nothing to drill right now — every question you've seen is "
        "mastered![/]\n"
        "  [dim]Play Story or Free Study to expose new questions, then come back.[/]"
    )
    console.print()
    input("  Press Enter to continue...")


def show_drill_summary(correct: int, total: int, player: Player, zone_manager: ZoneManager) -> None:
    from game import mastery
    console.print()
    pct = int(correct / total * 100) if total else 0
    color = "bright_green" if pct >= 80 else ("yellow" if pct >= 60 else "red")
    console.print(Panel(
        f"[bold {color}]Drill complete — {correct}/{total} correct ({pct}%)[/]",
        border_style=color,
        title="[bold]🎯 RESULTS[/]",
    ))
    rd = mastery.overall_readiness(player, zone_manager)
    console.print(
        f"  [dim]Overall mastery now: {rd['mastery_pct']:.0f}% "
        f"({rd['learned']}/{rd['total_questions']} questions learned)[/]"
    )
    console.print()
    input("  Press Enter to continue...")


def show_study_first_mode(node: Node, player: Player) -> None:
    """Study-first mode: show study content then mini-quiz before full encounters."""
    clear()
    show_header(player)
    console.print()
    console.print(Rule(f"[bold bright_cyan]📚 STUDY-FIRST MODE: {node.name}[/]", style="bright_blue"))
    console.print()

    # Show study content if available
    if node.study_content:
        console.print(Panel(
            f"[bright_white]{node.study_content}[/]",
            border_style="bright_cyan",
            title="[bright_cyan]STUDY CONTENT[/]",
            padding=(1, 2),
        ))
        console.print()
        input("  Press Enter to continue to mini-quiz...")

    # Show quiz questions if available
    if node.quiz_questions:
        correct_count = 0
        for i, q in enumerate(node.quiz_questions, 1):
            clear()
            show_header(player)
            console.print()
            console.print(f"[dim]Mini-Quiz Question {i}/{len(node.quiz_questions)}[/]")
            console.print()
            console.print(Panel(
                f"[bold bright_white]{q.get('question', 'Question')}[/]",
                border_style="bright_cyan",
                title="[bright_cyan]QUESTION[/]",
                padding=(1, 2),
            ))
            console.print()

            options = q.get('options', [])
            option_labels = ["A", "B", "C", "D"]
            choices = []
            for idx, option in enumerate(options):
                label = f"  [{option_labels[idx]}]  {option}"
                choices.append(questionary.Choice(label, value=idx))

            result = questionary.select("Your answer:", choices=choices, style=_QSTYLE).ask()
            correct_idx = q.get('correct_index', 0)

            if result == correct_idx:
                console.print(f"\n  [bright_green]✓ Correct![/]")
                correct_count += 1
            else:
                correct_letter = option_labels[correct_idx] if correct_idx < len(option_labels) else "?"
                console.print(f"\n  [red]✗ Wrong[/] — Correct answer: [{correct_letter}] {options[correct_idx] if correct_idx < len(options) else '?'}")

            explanation = q.get('explanation', '')
            if explanation:
                console.print(f"  [bright_blue]{explanation}[/]")
            console.print()
            input("  Press Enter to continue...")

        clear()
        show_header(player)
        console.print()
        pct = int(correct_count / len(node.quiz_questions) * 100) if node.quiz_questions else 0
        color = "bright_green" if pct >= 70 else ("yellow" if pct >= 50 else "red")
        console.print(Panel(
            f"[bold]Mini-Quiz Complete[/]\n\n"
            f"Score: [{color}]{correct_count}/{len(node.quiz_questions)} ({pct}%)[/]\n\n"
            f"[dim]Proceeding to full encounters...[/]",
            border_style="bright_blue",
            padding=(1, 2),
        ))
        console.print()
        input("  Press Enter to start full quiz...")


def show_study_menu(node: Node) -> str:
    """Return 'study' | 'quiz' | 'study_first' | 'back'."""
    clear()
    card_count = len(node.study_cards)
    has_study_first = bool(node.study_content or node.quiz_questions)
    console.print()
    console.print(Rule(f"[bold bright_cyan]Node {node.id}: {node.name}[/]", style="bright_blue"))
    console.print()
    console.print(f"  [dim]{node.description}[/]")
    console.print()

    choices = []
    if card_count:
        choices.append(questionary.Choice(
            f"📖  Study Guide  ({card_count} reference cards — read before quiz)",
            value="study",
        ))
    if has_study_first:
        choices.append(questionary.Choice(
            "📚  Study-First Mode  (review content + mini-quiz before full encounters)",
            value="study_first",
        ))
    choices += [
        questionary.Choice("⚔   Start Quiz  (go straight to encounters)", value="quiz"),
        questionary.Choice("←   Back", value="back"),
    ]

    result = questionary.select("Choose:", choices=choices, style=_QSTYLE).ask()
    return result or "back"


def _render_study_card(card: StudyCard, idx: int, total: int) -> None:
    """Render a single study card using Rich."""
    clear()
    console.print()
    console.print(Rule(
        f"[bold bright_cyan]{card.title}[/]  [dim]({idx}/{total})[/]",
        style="bright_blue",
    ))
    console.print()

    if card.card_type == "table" and card.headers and card.rows:
        t = Table(
            border_style="bright_blue",
            header_style="bold bright_cyan",
            show_lines=True,
            expand=False,
        )
        for h in card.headers:
            t.add_column(h, style="white")
        for row in card.rows:
            t.add_row(*row)
        console.print(t)

    elif card.card_type == "mnemonic":
        console.print(Panel(
            f"[bold bright_yellow]{card.body}[/]",
            border_style="bright_yellow",
            title="[bright_yellow]MNEMONIC[/]",
            padding=(1, 3),
        ))

    else:
        if card.body:
            console.print(Panel(
                f"[bright_white]{card.body}[/]",
                border_style="bright_cyan",
                padding=(1, 2),
            ))

    if card.key_points:
        console.print()
        console.print("  [bold bright_green]Key Points:[/]")
        for pt in card.key_points:
            console.print(f"  [bright_green]▶[/] [white]{pt}[/]")

    console.print()


def show_study_mode(node: Node) -> None:
    """Page through all study cards for a node. Returns when done or skipped."""
    cards = node.study_cards
    if not cards:
        return

    idx = 0
    while True:
        card = cards[idx]
        _render_study_card(card, idx + 1, len(cards))

        nav_choices = []
        if idx > 0:
            nav_choices.append(questionary.Choice("← Previous", value="prev"))
        if idx < len(cards) - 1:
            nav_choices.append(questionary.Choice("Next →", value="next"))
        nav_choices.append(questionary.Choice("✓  Done — start quiz", value="done"))
        nav_choices.append(questionary.Choice("↩  Back to node menu", value="back"))

        action = questionary.select(
            f"Card {idx + 1}/{len(cards)}:",
            choices=nav_choices,
            style=_QSTYLE,
        ).ask()

        if action == "next":
            idx = min(idx + 1, len(cards) - 1)
        elif action == "prev":
            idx = max(idx - 1, 0)
        elif action in ("done", "back", None):
            break


def show_acronym_drill_entry(acronym: str, hint: str = "") -> str:
    clear()
    console.print()
    console.print(Rule("[bold bright_cyan]ACRONYM DRILL[/]", style="bright_blue"))
    console.print()
    console.print(Panel(
        f"[bold bright_white]{acronym}[/]"
        + (f"\n\n[dim]{hint}[/]" if hint else ""),
        title="[bright_cyan]What does this stand for?[/]",
        border_style="bright_cyan",
        padding=(2, 4),
    ))
    console.print()
    answer = questionary.text("Your answer (or 'skip'):", style=_QSTYLE).ask()
    return (answer or "").strip()


def show_acronym_result(acronym: str, full_name: str, definition: str, correct: bool) -> None:
    console.print()
    if correct:
        console.print(f"  [bright_green]✓ Correct! {acronym} = {full_name}[/]")
    else:
        console.print(f"  [red]✗ {acronym} = {full_name}[/]")
    console.print(f"  [bright_blue]{definition}[/]")
    console.print()
    input("  Press Enter to continue...")


def show_zone_entry(zone_num: int, text: str) -> None:
    """Full-screen narrative panel shown the first time a zone is entered."""
    if not text:
        return
    clear()
    console.print()
    console.print(Rule(f"[bold bright_cyan]{ZONE_NAMES.get(zone_num, f'Zone {zone_num}')}[/]", style="bright_blue"))
    console.print()
    console.print(Panel(
        f"[italic bright_white]{text}[/]",
        border_style="bright_magenta",
        title="[bright_magenta]ENTERING THE ZONE[/]",
        padding=(1, 2),
    ))
    console.print()
    input("  Press Enter to step through...")


def show_flavor_line(text: str, pause: float = 1.6) -> None:
    """A short atmospheric line flashed before a node or encounter begins, then cleared."""
    if not text:
        return
    clear()
    console.print()
    console.print(f"  [italic dim bright_magenta]» {text}[/]")
    console.print()
    time.sleep(pause)
