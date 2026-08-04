from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from game.player import Player

MAX_SLOTS = 3


class SaveManager:
    def __init__(self, save_dir: str = "saves") -> None:
        self.save_dir: Path = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _get_save_path(self, slot: int) -> Path:
        return self.save_dir / f"save_{slot}.yaml"

    def _validate_slot(self, slot: int) -> None:
        if not (1 <= slot <= MAX_SLOTS):
            raise ValueError(f"Slot must be between 1 and {MAX_SLOTS}")

    def save(self, player: Player, slot: int) -> bool:
        self._validate_slot(slot)
        try:
            save_path = self._get_save_path(slot)
            if save_path.exists():
                bak_path = save_path.with_name(save_path.name + ".bak")
                if bak_path.exists():
                    bak_path.unlink()
                save_path.rename(bak_path)
            data = self._player_to_dict(player)
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            return True
        except (OSError, yaml.YAMLError) as e:
            print(f"Error saving: {e}")
            return False

    def load(self, slot: int) -> Optional[Player]:
        self._validate_slot(slot)
        save_path = self._get_save_path(slot)
        if not save_path.exists():
            return None
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return self._dict_to_player(data)
        except (OSError, yaml.YAMLError, KeyError, TypeError) as e:
            print(f"Error loading save: {e}")
            return None

    def restore_backup(self, slot: int) -> bool:
        self._validate_slot(slot)
        save_path = self._get_save_path(slot)
        bak_path = save_path.with_name(save_path.name + ".bak")
        if not bak_path.exists():
            return False
        try:
            if save_path.exists():
                save_path.unlink()
            bak_path.rename(save_path)
            return True
        except OSError as e:
            print(f"Error restoring backup: {e}")
            return False

    def list_saves(self) -> List[Dict[str, Any]]:
        saves = []
        for slot in range(1, MAX_SLOTS + 1):
            info: Dict[str, Any] = {"slot": slot, "exists": False, "name": None, "level": None}
            save_path = self._get_save_path(slot)
            if save_path.exists():
                try:
                    with open(save_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    info["exists"] = True
                    info["name"] = data.get("name", "Unknown")
                    info["level"] = data.get("level", 1)
                    info["bits"] = data.get("bits", 0)
                except (OSError, yaml.YAMLError):
                    info["exists"] = True
                    info["name"] = "Corrupted"
            saves.append(info)
        return saves

    def delete_save(self, slot: int) -> bool:
        self._validate_slot(slot)
        save_path = self._get_save_path(slot)
        if not save_path.exists():
            return True
        try:
            save_path.unlink()
            return True
        except OSError as e:
            print(f"Error deleting save: {e}")
            return False

    def _player_to_dict(self, player: Player) -> Dict[str, Any]:
        return {
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "xp": player.xp,
            "level": player.level,
            "bits": player.bits,
            "skills": player.skills,
            "inventory": player.inventory,
            "completed_nodes": player.completed_nodes,
            "guardian_defeated": player.guardian_defeated,
            "wrong_answer_ids": player.wrong_answer_ids,
            "encounter_results": player.encounter_results,
            "node_streaks": player.node_streaks,
            "attempts": player.attempts,
            "start_date": player.start_date,
            "free_study_mode": player.free_study_mode,
            "last_study_date": player.last_study_date,
            "streak_days": player.streak_days,
            "longest_streak": player.longest_streak,
            "daily_question_cap": player.daily_question_cap,
        }

    def _dict_to_player(self, data: Dict[str, Any]) -> Player:
        player = Player(data["name"])
        player.hp = data.get("hp", 100)
        player.max_hp = data.get("max_hp", 100)
        player.xp = data.get("xp", 0)
        player.level = data.get("level", 1)
        player.bits = data.get("bits", 0)
        player.skills = data.get("skills", [])
        player.inventory = data.get("inventory", {})
        player.completed_nodes = data.get("completed_nodes", [])
        player.guardian_defeated = data.get("guardian_defeated", [False] * 5)
        player.wrong_answer_ids = data.get("wrong_answer_ids", [])
        player.encounter_results = data.get("encounter_results", {})
        player.node_streaks = data.get("node_streaks", {})
        player.attempts = data.get("attempts", {})
        player.start_date = data.get("start_date", player.start_date)
        player.free_study_mode = data.get("free_study_mode", False)
        player.last_study_date = data.get("last_study_date", "")
        player.streak_days = data.get("streak_days", 0)
        player.longest_streak = data.get("longest_streak", 0)
        player.daily_question_cap = data.get("daily_question_cap", 20)
        return player
