import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from game.player import Player
from game.encounter import Encounter

NODE_PASS_RATE = 0.70
STREAK_REQUIRED = 3


@dataclass
class StudyCard:
    """A single study/reference card shown before quiz mode."""
    title: str
    card_type: str          # "table" | "concept" | "mnemonic" | "list"
    body: str = ""
    key_points: List[str] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudyCard":
        return cls(
            title=data.get("title", ""),
            card_type=data.get("type", "concept"),
            body=data.get("body", ""),
            key_points=data.get("key_points", []),
            headers=data.get("headers", []),
            rows=data.get("rows", []),
        )


@dataclass
class Node:
    id: float
    name: str
    description: str
    encounters: List[Encounter] = field(default_factory=list)
    study_cards: List[StudyCard] = field(default_factory=list)

    def is_node_completed(self, player: Player) -> bool:
        if not self.encounters:
            return False
        total = len(self.encounters)
        correct = sum(
            1 for enc in self.encounters
            if player.encounter_results.get(enc.id) is True
        )
        pass_rate_ok = (correct / total) >= NODE_PASS_RATE
        streak_ok = player.node_streaks.get(str(self.id), 0) >= STREAK_REQUIRED
        return pass_rate_ok and streak_ok

    def get_completion_stats(self, player: Player) -> Tuple[int, int]:
        total = len(self.encounters)
        correct = sum(
            1 for enc in self.encounters
            if player.encounter_results.get(enc.id) is True
        )
        return (correct, total)


@dataclass
class Zone:
    number: int
    name: str
    description: str
    nodes: List[Node] = field(default_factory=list)
    guardian_encounters: List[Encounter] = field(default_factory=list)

    def is_completed(self, player: Player) -> bool:
        if self.number < 1 or self.number > 5:
            return False
        return player.guardian_defeated[self.number - 1]

    def all_nodes_completed(self, player: Player) -> bool:
        return all(node.is_node_completed(player) for node in self.nodes)

    def get_completion_stats(self, player: Player) -> Tuple[int, int]:
        total = len(self.nodes)
        completed = sum(1 for node in self.nodes if node.is_node_completed(player))
        return (completed, total)


class ZoneManager:
    def __init__(self, content_dir: str = "content") -> None:
        self.content_dir: Path = Path(content_dir)
        self.zones: Dict[int, Zone] = {}
        self._encounter_index: Dict[str, Encounter] = {}

    def load_zone(self, zone_number: int) -> Optional[Zone]:
        zone_file = self.content_dir / f"zone-{zone_number}.json"
        if not zone_file.exists():
            return None
        try:
            with open(zone_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            zone = self._parse_zone(data)
            self.zones[zone_number] = zone
            for node in zone.nodes:
                for enc in node.encounters:
                    self._encounter_index[enc.id] = enc
            for enc in zone.guardian_encounters:
                self._encounter_index[enc.id] = enc
            # Load companion study file if present (content/study-N.json)
            self._load_study_cards(zone, zone_number)
            return zone
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error loading zone {zone_number}: {e}")
            return None

    def _load_study_cards(self, zone: Zone, zone_number: int) -> None:
        """Merge study cards from study-N.json into zone nodes (optional companion file)."""
        study_file = self.content_dir / f"study-{zone_number}.json"
        if not study_file.exists():
            return
        try:
            with open(study_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Keys are node IDs as strings e.g. "1.1", "2.3"
            study_map: Dict[float, List[StudyCard]] = {
                float(k): [StudyCard.from_dict(c) for c in cards]
                for k, cards in raw.items()
            }
            for node in zone.nodes:
                if node.id in study_map:
                    node.study_cards = study_map[node.id]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            print(f"Warning: could not load study file for zone {zone_number}: {e}")

    def _parse_zone(self, data: Dict[str, Any]) -> Zone:
        nodes = []
        for node_data in data.get("nodes", []):
            encounters = []
            for enc_data in node_data.get("encounters", []):
                try:
                    encounters.append(Encounter.from_dict(enc_data))
                except (KeyError, ValueError) as e:
                    print(f"Warning: skipping encounter: {e}")
            study_cards = [
                StudyCard.from_dict(c)
                for c in node_data.get("study_cards", [])
            ]
            node = Node(
                id=float(node_data["id"]),
                name=node_data["name"],
                description=node_data.get("description", ""),
                encounters=encounters,
                study_cards=study_cards,
            )
            nodes.append(node)
        nodes.sort(key=lambda n: n.id)

        guardian_encounters = []
        for enc_data in data.get("guardian_encounters", []):
            try:
                guardian_encounters.append(Encounter.from_dict(enc_data))
            except (KeyError, ValueError) as e:
                print(f"Warning: skipping guardian encounter: {e}")

        return Zone(
            number=data["zone"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=nodes,
            guardian_encounters=guardian_encounters,
        )

    def get_zone(self, zone_number: int) -> Optional[Zone]:
        if zone_number in self.zones:
            return self.zones[zone_number]
        return self.load_zone(zone_number)

    def get_encounter_by_id(self, encounter_id: str) -> Optional[Encounter]:
        return self._encounter_index.get(encounter_id)

    def is_zone_accessible(self, zone_number: int, player: Player) -> bool:
        if player.free_study_mode:
            return True
        if zone_number == 1:
            return True
        return player.guardian_defeated[zone_number - 2]

    def get_locked_reason(self, zone_number: int, player: Player) -> str:
        if self.is_zone_accessible(zone_number, player):
            return ""
        return f"Defeat Zone {zone_number - 1} Guardian to unlock"

    def mark_node_completed(self, node_id_str: str, player: Player) -> None:
        if node_id_str not in player.completed_nodes:
            player.completed_nodes.append(node_id_str)

    def defeat_guardian(self, zone_number: int, player: Player) -> None:
        if 1 <= zone_number <= 5:
            player.guardian_defeated[zone_number - 1] = True

    def get_all_zones(self) -> List[int]:
        return [1, 2, 3, 4, 5]
