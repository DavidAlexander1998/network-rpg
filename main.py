"""
Network+ RPG - Entry point
"""

import sys
import signal
from typing import Optional

from game.player import Player
from game.combat import Combat
from game.zone_manager import ZoneManager, Zone, Node
from game.save_manager import SaveManager
from game.spaced_repetition import SpacedRepetition
from ui import screens

_save_manager = SaveManager("saves")
_zone_manager = ZoneManager("content")
_sr = SpacedRepetition()
_current_player: Optional[Player] = None
_current_slot: Optional[int] = None


def _save_and_exit(signum=None, frame=None) -> None:
    if _current_player and _current_slot:
        _save_manager.save(_current_player, _current_slot)
        print("\nProgress saved. Goodbye.")
    sys.exit(0)


signal.signal(signal.SIGINT, _save_and_exit)


def _preload_zones() -> None:
    for i in range(1, 6):
        _zone_manager.load_zone(i)


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
            # "quiz" or after finishing study cards → run encounters
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
                questionary.Choice("← Back", value=None),
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
        elif choice == "plan":
            screens.show_study_plan(player)
        elif choice == "acronym":
            _acronym_drill(player)
        elif choice == "report":
            screens.show_study_report(player, _zone_manager)
        elif choice == "save":
            player = _save_load_menu(player)
            _current_player = player
        elif choice == "quit":
            _save_and_exit()
            break


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


def _subnetting_trainer(player: Player) -> None:
    """Endless generated subnetting problems until the player quits."""
    from game import subnetting

    count = screens.show_subnet_intro()
    if not count:
        return

    correct = 0
    answered = 0
    prev_free = player.free_study_mode
    player.free_study_mode = True
    try:
        for i in range(count):
            problem = subnetting.generate_problem()
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


def _acronym_drill(player: Player) -> None:
    import json
    from pathlib import Path
    acro_file = Path("content/acronyms.json")
    if not acro_file.exists():
        screens.console.print("[yellow]acronyms.json not found — skipping drill.[/]")
        input("  Press Enter...")
        return

    with open(acro_file, "r", encoding="utf-8") as f:
        acronyms = json.load(f)

    import random
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
