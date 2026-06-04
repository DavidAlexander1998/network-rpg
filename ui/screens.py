import os
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

    header = (
        f"[bold bright_cyan]{player.name}[/]  "
        f"[bright_yellow]Lvl {player.level}[/]  "
        f"HP: {_hp_bar(player.hp, player.max_hp)} [{hp_color}]{player.hp}/{player.max_hp}[/]  "
        f"XP: {_xp_bar(player.xp, xp_needed)} [bright_cyan]{player.xp}/{xp_needed}[/]  "
        f"[bright_green]💰 {player.bits} BITS[/]  "
        f"{mode_tag}"
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
            questionary.Choice("⚔   Story Mode     (zones unlock sequentially)", value="story"),
            questionary.Choice("📚  Free Study      (all zones open — pick any node)", value="free"),
            questionary.Choice("🎯  Weak Spot Drill (auto-targets your worst objectives)", value="drill"),
            questionary.Choice("🧮  Subnetting Trainer (unlimited generated problems)", value="subnet"),
            questionary.Choice("📝  Exam Simulator   (timed 90Q mock, scored 100-900)", value="exam"),
            questionary.Choice("🗓   30-Day Plan     (what should I do today?)", value="plan"),
            questionary.Choice("🔤  Acronym Drill", value="acronym"),
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

    choices.append(questionary.Choice("← Back", value=None))

    result = questionary.select("Select zone:", choices=choices, style=_QSTYLE).ask()
    return result


def show_node_map(zone: Zone, player: Player) -> Optional[float]:
    clear()
    show_header(player)
    console.print()
    console.print(Rule(f"[bold bright_cyan]{ZONE_NAMES.get(zone.number, zone.name)}[/]", style="bright_blue"))
    console.print()

    choices = []
    for node in zone.nodes:
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

        label = f"Node {node.id}: {node.name}  {status}"
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

    choices.append(questionary.Choice("← Back", value=None))

    result = questionary.select("Select node:", choices=choices, style=_QSTYLE).ask()
    return result


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

    choices.append(questionary.Choice("← Back", value=None))
    return questionary.select("Select slot:", choices=choices, style=_QSTYLE).ask()


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
# Subnetting Trainer
# ---------------------------------------------------------------------------

def show_subnet_intro() -> Optional[int]:
    clear()
    console.print()
    console.print(Rule("[bold bright_cyan]🧮 SUBNETTING TRAINER[/]", style="bright_blue"))
    console.print()
    console.print("  [dim]Fresh randomized problems every time — network/broadcast addresses,[/]")
    console.print("  [dim]usable hosts, masks, ranges. No HP risk. Build muscle memory.[/]")
    console.print()
    choice = questionary.select(
        "How many problems?",
        choices=[
            questionary.Choice("10 — quick warm-up", value=10),
            questionary.Choice("20 — solid set", value=20),
            questionary.Choice("50 — grind to fluency", value=50),
            questionary.Choice("← Back", value=None),
        ],
        style=_QSTYLE,
    ).ask()
    return choice


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


def show_study_menu(node: Node) -> str:
    """Return 'study' | 'quiz' | 'back'."""
    clear()
    card_count = len(node.study_cards)
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
