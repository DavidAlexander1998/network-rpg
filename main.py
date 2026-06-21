"""
Network+ RPG - Entry point
"""

import sys
import signal
import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

from game.player import Player
from game.combat import Combat
from game.encounter import Encounter
from game.zone_manager import ZoneManager, Zone, Node
from game.save_manager import SaveManager
from game.spaced_repetition import SpacedRepetition
from ui import screens

_save_manager = SaveManager("saves")
_zone_manager = ZoneManager("content")
_sr = SpacedRepetition()
_current_player: Optional[Player] = None
_current_slot: Optional[int] = None

# Standalone bonus content: CLI drills, topology challenges, narrative flavor text
_flavor_texts: Dict[str, Any] = {}
_cli_encounters: List[Encounter] = []
_topology_encounters: List[Encounter] = []
_zones_entered: set = set()


def _save_and_exit(signum=None, frame=None) -> None:
    if _current_player and _current_slot:
        _save_manager.save(_current_player, _current_slot)
        print("\nProgress saved. Goodbye.")
    sys.exit(0)


signal.signal(signal.SIGINT, _save_and_exit)


def _preload_zones() -> None:
    for i in range(1, 6):
        _zone_manager.load_zone(i)


def _load_extra_content() -> None:
    """Load standalone bonus content: CLI drills, topology challenges, flavor texts."""
    content_dir = Path("content")

    flavor_file = content_dir / "flavor-texts.json"
    if flavor_file.exists():
        with open(flavor_file, "r", encoding="utf-8") as f:
            _flavor_texts.update(json.load(f))

    sources = (
        ("cli-encounters.json", _cli_encounters),
        ("topology-encounters.json", _topology_encounters),
    )
    for filename, bucket in sources:
        path = content_dir / filename
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            for enc_data in json.load(f):
                try:
                    bucket.append(Encounter.from_dict(enc_data))
                except (KeyError, ValueError) as e:
                    print(f"Warning: skipping encounter in {filename}: {e}")


def _maybe_show_zone_entry(zone_num: int) -> None:
    """Show the zone's narrative entry text the first time it's visited this session."""
    if zone_num in _zones_entered:
        return
    _zones_entered.add(zone_num)
    text = _flavor_texts.get("zone_entries", {}).get(str(zone_num))
    if text:
        screens.show_zone_entry(zone_num, text)


def _flash_node_transition() -> None:
    transitions = _flavor_texts.get("node_transitions") or []
    if transitions:
        screens.show_flavor_line(random.choice(transitions))


def _maybe_flash_encounter_intro() -> None:
    intros = _flavor_texts.get("encounter_intros") or []
    if intros and random.random() < 0.3:
        screens.show_flavor_line(random.choice(intros))


def _run_encounter_session(player: Player, zone: Zone, node: Node) -> bool:
    """Run all encounters in a node. Returns True if node was completed."""
    encounters = list(node.encounters)
    old_level = player.level
    current_streak = 0

    for idx, encounter in enumerate(encounters):
        if not player.is_alive():
            break

        # Offer SR review before new encounter (every threshold)
        review_id = _sr.get_next_review()
        if review_id:
            review_enc = _zone_manager.get_encounter_by_id(review_id)
            if review_enc:
                screens.console.print(
                    "\n  [bright_yellow]📌 Spaced Repetition Review — this question tripped you up earlier.[/]\n"
                )
                selected = screens.show_encounter(review_enc, player, question_num=0, total=0)
                if selected is None:
                    break
                result = Combat(player, review_enc).process_answer(selected)
                _sr.complete_review(review_id, result.is_correct)
                screens.show_combat_result(result, player)
                if player.level > old_level:
                    screens.show_level_up(player, old_level)
                    old_level = player.level

        if not player.is_alive():
            break

        _maybe_flash_encounter_intro()

        if encounter.encounter_type == "cli_encounter":
            answer = screens.show_cli_encounter(encounter, player, question_num=idx + 1, total=len(encounters))
            if answer is None:
                break
            result = Combat(player, encounter).process_cli_answer(answer)
        else:
            selected = screens.show_encounter(encounter, player, question_num=idx + 1, total=len(encounters))
            if selected is None:
                break
            result = Combat(player, encounter).process_answer(selected)

        if result.is_correct:
            _sr.record_success(encounter.id)
            current_streak += 1
            player.record_node_streak(str(node.id), current_streak)
        else:
            _sr.add_failed(encounter.id)
            current_streak = 0

        screens.show_combat_result(result, player)

        if player.level > old_level:
            screens.show_level_up(player, old_level)
            old_level = player.level

    if _current_slot:
        _save_manager.save(player, _current_slot)

    completed = node.is_node_completed(player)
    if completed and str(node.id) not in player.completed_nodes:
        _zone_manager.mark_node_completed(str(node.id), player)
        screens.show_node_complete(node)

    return completed


def _run_guardian_battle(player: Player, zone: Zone) -> bool:
    """Run the guardian exam. Returns True if passed."""
    screens.show_guardian_intro(zone)

    encounters = zone.guardian_encounters
    if not encounters:
        screens.console.print("[red]No guardian encounters loaded for this zone.[/]")
        return False

    score = 0
    old_level = player.level

    for idx, encounter in enumerate(encounters):
        if not player.is_alive():
            break
        selected = screens.show_encounter(encounter, player, question_num=idx + 1, total=len(encounters))
        if selected is None:
            break
        result = Combat(player, encounter).process_answer(selected)
        if result.is_correct:
            score += 1
        screens.show_combat_result(result, player)
        if player.level > old_level:
            screens.show_level_up(player, old_level)
            old_level = player.level

    passed = score >= int(len(encounters) * 0.75)

    if passed:
        player.add_xp(1000)
        player.add_bits(200)
        _zone_manager.defeat_guardian(zone.number, player)

    screens.show_guardian_result(passed, score, len(encounters), player, zone.number)

    if _current_slot:
        _save_manager.save(player, _current_slot)

    return passed


def _play_zone(player: Player, zone_num: int) -> None:
    zone = _zone_manager.get_zone(zone_num)
    if not zone:
        screens.console.print(f"[red]Zone {zone_num} content not loaded.[/]")
        return

    _maybe_show_zone_entry(zone_num)

    while True:
        node_choice = screens.show_node_map(zone, player)
        if node_choice is None:
            break

        if node_choice == -1.0:
            _run_guardian_battle(player, zone)
            continue

        node = next((n for n in zone.nodes if n.id == node_choice), None)
        if node:
            # Study gate: offer study guide before quiz
            menu_choice = screens.show_study_menu(node)
            if menu_choice == "back":
                continue
            if menu_choice == "study":
                screens.show_study_mode(node)
            elif menu_choice == "study_first":
                screens.show_study_first_mode(node, player)
            # "quiz" or after finishing study cards / study-first mode → run encounters
            _flash_node_transition()
            _run_encounter_session(player, zone, node)


def _story_mode(player: Player) -> None:
    player.free_study_mode = False
    while True:
        zone_choice = screens.show_zone_select(_zone_manager, player)
        if zone_choice is None:
            break
        if not _zone_manager.is_zone_accessible(zone_choice, player):
            continue
        _play_zone(player, zone_choice)


def _free_study_mode(player: Player) -> None:
    player.free_study_mode = True
    while True:
        zone_choice = screens.show_zone_select(_zone_manager, player)
        if zone_choice is None:
            player.free_study_mode = False
            break
        _play_zone(player, zone_choice)
    player.free_study_mode = False


def _save_load_menu(player: Player) -> Optional[Player]:
    global _current_slot
    while True:
        saves = _save_manager.list_saves()
        slot = screens.show_save_menu(saves)
        if slot is None:
            return player

        import questionary
        action = questionary.select(
            f"Slot {slot}:",
            choices=[
                questionary.Choice("Save current game here", value="save"),
                questionary.Choice("Load this save", value="load"),
                questionary.Choice("← Back", value="back"),
            ],
        ).ask()

        if action == "save":
            ok = _save_manager.save(player, slot)
            _current_slot = slot
            screens.console.print(f"[bright_green]Saved to slot {slot}.[/]" if ok else "[red]Save failed.[/]")
            input("  Press Enter...")
        elif action == "load":
            loaded = _save_manager.load(slot)
            if loaded:
                _current_slot = slot
                _sr.sync_from_player(loaded.wrong_answer_ids)
                screens.console.print(f"[bright_green]Loaded {loaded.name} (Level {loaded.level}).[/]")
                input("  Press Enter...")
                return loaded
            else:
                screens.console.print("[red]No save in that slot.[/]")
                input("  Press Enter...")

    return player


def _main_loop(player: Player) -> None:
    global _current_player
    _current_player = player

    while True:
        choice = screens.show_main_menu(player)

        if choice == "story":
            _story_mode(player)
        elif choice == "free":
            _free_study_mode(player)
        elif choice == "drill":
            _weak_spot_drill(player)
        elif choice == "subnet":
            _subnetting_trainer(player)
        elif choice == "exam":
            _exam_simulator(player)
        elif choice == "labs":
            _hands_on_labs(player)
        elif choice == "plan":
            screens.show_study_plan(player)
        elif choice == "acronym":
            _acronym_drill(player)
        elif choice == "field":
            _field_exercises(player)
        elif choice == "report":
            screens.show_study_report(player, _zone_manager)
        elif choice == "save":
            player = _save_load_menu(player)
            _current_player = player
        elif choice == "quit":
            _save_and_exit()
            break


def _run_drill_set(player: Player, encounters: List[Encounter], label: str) -> None:
    if not encounters:
        screens.console.print(f"[yellow]No {label.lower()} loaded — skipping.[/]")
        input("  Press Enter...")
        return

    drills = list(encounters)
    random.shuffle(drills)
    old_level = player.level

    for idx, encounter in enumerate(drills):
        if not player.is_alive():
            break

        if encounter.encounter_type == "cli_encounter":
            answer = screens.show_cli_encounter(encounter, player, question_num=idx + 1, total=len(drills))
            if answer is None:
                break
            result = Combat(player, encounter).process_cli_answer(answer)
        else:
            selected = screens.show_encounter(encounter, player, question_num=idx + 1, total=len(drills))
            if selected is None:
                break
            result = Combat(player, encounter).process_answer(selected)

        if result.is_correct:
            _sr.record_success(encounter.id)
        else:
            _sr.add_failed(encounter.id)

        screens.show_combat_result(result, player)

        if player.level > old_level:
            screens.show_level_up(player, old_level)
            old_level = player.level


def _weak_spot_drill(player: Player) -> None:
    """Adaptive drill — serves the questions the player most needs right now."""
    from game import mastery

    DRILL_SIZE = 15
    queue = mastery.build_drill_queue(player, _zone_manager, limit=DRILL_SIZE)

    if not queue:
        screens.show_drill_empty(player, _zone_manager)
        return

    screens.show_drill_intro(player, _zone_manager, len(queue))

    # Drilling is low-stakes study: no HP damage on misses.
    prev_free = player.free_study_mode
    player.free_study_mode = True
    correct = 0
    old_level = player.level
    try:
        for idx, encounter in enumerate(queue):
            selected = screens.show_encounter(encounter, player, question_num=idx + 1, total=len(queue))
            if selected is None:
                break
            result = Combat(player, encounter).process_answer(selected)
            if result.is_correct:
                correct += 1
                _sr.record_success(encounter.id)
            else:
                _sr.add_failed(encounter.id)
            screens.show_combat_result(result, player)
            if player.level > old_level:
                screens.show_level_up(player, old_level)
                old_level = player.level
    finally:
        player.free_study_mode = prev_free

    if _current_slot:
        _save_manager.save(player, _current_slot)

    screens.show_drill_summary(correct, len(queue), player, _zone_manager)


def _field_exercises(player: Player) -> None:
    import questionary
    while True:
        choice = questionary.select(
            "Field Exercises:",
            choices=[
                questionary.Choice(f"🖥️   CLI Command Drills    ({len(_cli_encounters)} scenarios — type real commands)", value="cli"),
                questionary.Choice(f"🗺️   Topology Challenges   ({len(_topology_encounters)} ASCII diagrams)", value="topo"),
                questionary.Choice("← Back", value="back"),
            ],
            style=screens._QSTYLE,
        ).ask()

        if choice in (None, "back"):
            return
        elif choice == "cli":
            _run_drill_set(player, _cli_encounters, "CLI command drills")
        elif choice == "topo":
            _run_drill_set(player, _topology_encounters, "topology challenges")


def _subnetting_trainer(player: Player) -> None:
    """Generated subnetting problems — multiple-choice or type-the-answer."""
    from game import subnetting

    intro = screens.show_subnet_intro()
    if not intro:
        return
    count, mode = intro

    correct = 0
    answered = 0
    prev_free = player.free_study_mode
    player.free_study_mode = True
    try:
        for i in range(count):
            problem = subnetting.generate_problem()
            if mode == "type":
                expected = problem.get_correct_answer()
                ans = screens.show_subnet_free(
                    problem, i + 1, count, subnetting.answer_hint(expected))
                if ans is None:
                    break
                answered += 1
                is_correct = subnetting.check_free_answer(expected, ans)
                if is_correct:
                    correct += 1
                screens.show_subnet_free_result(is_correct, expected, problem.explanation)
            else:
                selected = screens.show_encounter(problem, player, question_num=i + 1, total=count)
                if selected is None:
                    break
                answered += 1
                result = Combat(player, problem).process_answer(selected)
                if result.is_correct:
                    correct += 1
                screens.show_combat_result(result, player)
    finally:
        player.free_study_mode = prev_free

    screens.show_subnet_summary(correct, answered)


def _exam_simulator(player: Player) -> None:
    """Timed, domain-weighted 90-question mock exam scored on the 100-900 scale."""
    from game import exam

    if not screens.show_exam_intro():
        return

    questions = exam.build_exam(_zone_manager)
    session = exam.ExamSession(questions)
    session.start()

    answered = 0
    prev_free = player.free_study_mode
    player.free_study_mode = True
    try:
        for idx, encounter in enumerate(questions):
            if session.time_up():
                screens.console.print("\n  [bright_red]⏰ Time's up![/]\n")
                break
            selected = screens.show_exam_question(
                encounter, player, idx + 1, len(questions), session.seconds_remaining()
            )
            if selected is None:
                break
            answered += 1
            result = Combat(player, encounter).process_answer(selected)
            session.record(encounter, result.is_correct)
            # Real practice → feed the adaptive engine, but no answer/explanation
            # shown mid-exam (just like the real test).
            if result.is_correct:
                _sr.record_success(encounter.id)
            else:
                _sr.add_failed(encounter.id)
    finally:
        player.free_study_mode = prev_free

    if _current_slot:
        _save_manager.save(player, _current_slot)

    screens.show_exam_result(session.result(answered), _zone_manager)


def _hands_on_labs(player: Player) -> None:
    while True:
        choice = screens.show_labs_menu()
        if choice in (None, "back"):
            return
        if choice == "command":
            _command_lab(player)
        elif choice == "pbq":
            _pbq_drill(player)


def _command_lab(player: Player) -> None:
    """Simulated terminal: run diagnostic commands, then commit to a diagnosis."""
    from game import command_lab

    scenario = screens.show_command_lab_select(command_lab.SCENARIOS)
    if scenario is None:
        return

    screens.show_command_lab_brief(scenario)
    # Command loop
    while True:
        raw = screens.command_lab_prompt(scenario)
        if raw is None:
            return
        cmd = raw.strip().lower()
        if cmd in ("quit", "exit"):
            return
        if cmd in ("solve", "answer", "diagnose"):
            break
        if cmd in ("help", "?", ""):
            screens.show_command_lab_help(scenario)
            continue
        screens.show_command_output(raw, scenario.run_command(raw))

    # Diagnosis question
    selected = screens.show_lab_question(scenario.question, scenario.options)
    if selected is None:
        return
    is_correct = (selected == scenario.answer_index)
    screens.show_lab_answer(is_correct, scenario.options[scenario.answer_index], scenario.explanation)


def _pbq_drill(player: Player) -> None:
    """Ordering and matching performance-based-style tasks."""
    from game import tasks_pbq

    kind = screens.show_pbq_menu()
    if kind in (None, "back"):
        return

    if kind == "order":
        task = screens.pick_pbq(tasks_pbq.ORDERING_TASKS, "Pick an ordering task:")
        if task is None:
            return
        user_order = screens.run_ordering_task(task)
        if user_order is None:
            return
        correct = (user_order == task.ordered)
        screens.show_pbq_result(correct, task.ordered, task.explanation)
    elif kind == "match":
        task = screens.pick_pbq(tasks_pbq.MATCHING_TASKS, "Pick a matching task:")
        if task is None:
            return
        result = screens.run_matching_task(task)
        if result is None:
            return
        correct, n_right, n_total = result
        screens.show_pbq_match_result(correct, n_right, n_total, task.pairs, task.explanation)


def _acronym_drill(player: Player) -> None:
    acro_file = Path("content/acronyms.json")
    if not acro_file.exists():
        screens.console.print("[yellow]acronyms.json not found — skipping drill.[/]")
        input("  Press Enter...")
        return

    with open(acro_file, "r", encoding="utf-8") as f:
        acronyms = json.load(f)

    random.shuffle(acronyms)

    for item in acronyms:
        acro = item.get("acronym", "")
        full = item.get("full_name", "")
        defn = item.get("definition", "")
        answer = screens.show_acronym_drill_entry(acro)
        if answer.lower() in ("q", "quit", "exit"):
            break
        correct = answer.lower() == full.lower() or answer.lower() in full.lower()
        screens.show_acronym_result(acro, full, defn, correct)


def main() -> None:
    global _current_slot

    _preload_zones()
    _load_extra_content()

    saves = _save_manager.list_saves()
    has_saves = any(s["exists"] for s in saves)

    if has_saves:
        import questionary
        screens.clear()
        screens.console.print()
        screens.console.print("[bold bright_cyan]  NETWORK+ RPG[/]")
        screens.console.print()
        start_choice = questionary.select(
            "Welcome back:",
            choices=[
                questionary.Choice("Continue (load save)", value="load"),
                questionary.Choice("New Game", value="new"),
            ],
            style=screens._QSTYLE,
        ).ask()
    else:
        start_choice = "new"

    if start_choice == "load":
        slot = screens.show_save_menu(saves)
        if slot:
            player = _save_manager.load(slot)
            if player:
                _current_slot = slot
                _sr.sync_from_player(player.wrong_answer_ids)
            else:
                screens.console.print("[red]Failed to load. Starting new game.[/]")
                player = None
        else:
            player = None

        if player is None:
            start_choice = "new"

    if start_choice == "new":
        name = screens.show_new_game_prompt()
        if not name:
            print("No name entered. Exiting.")
            return
        player = Player(name)
        _current_slot = 1
        _save_manager.save(player, _current_slot)

    _main_loop(player)


if __name__ == "__main__":
    main()
