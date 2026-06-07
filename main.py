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
        else:
            _sr.add_failed(encounter.id)

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

    if _current_slot:
        _save_manager.save(player, _current_slot)


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
