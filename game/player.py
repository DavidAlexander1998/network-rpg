from typing import List, Dict

XP_THRESHOLDS = [500, 700, 1300, 2000, 3000]
HP_PER_LEVEL = 20

SKILL_UNLOCKS = {
    2: "double_xp",
    5: "answer_shield",
    7: "second_wind",
}


class Player:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.hp: int = 100
        self.max_hp: int = 100
        self.xp: int = 0
        self.level: int = 1
        self.bits: int = 0
        self.skills: List[str] = []
        self.inventory: Dict[str, int] = {}
        self.completed_nodes: List[str] = []
        self.guardian_defeated: List[bool] = [False] * 5
        self.wrong_answer_ids: List[str] = []
        self.encounter_results: Dict[str, bool] = {}
        self.free_study_mode: bool = False

    def _xp_for_next_level(self) -> int:
        idx = min(self.level - 1, len(XP_THRESHOLDS) - 1)
        return XP_THRESHOLDS[idx]

    def level_up(self) -> bool:
        xp_needed = self._xp_for_next_level()
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            self.max_hp += HP_PER_LEVEL
            self.hp = self.max_hp
            skill = SKILL_UNLOCKS.get(self.level)
            if skill and skill not in self.skills:
                self.skills.append(skill)
            return True
        return False

    def take_damage(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Damage cannot be negative")
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Heal cannot be negative")
        self.hp = min(self.max_hp, self.hp + amount)

    def add_xp(self, amount: int) -> bool:
        if amount < 0:
            raise ValueError("XP cannot be negative")
        self.xp += amount
        return self.level_up()

    def add_bits(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Bits cannot be negative")
        self.bits += amount

    def spend_bits(self, amount: int) -> bool:
        if self.bits < amount:
            return False
        self.bits -= amount
        return True

    def record_encounter(self, encounter_id: str, is_correct: bool) -> None:
        self.encounter_results[encounter_id] = is_correct
        if not is_correct:
            if encounter_id not in self.wrong_answer_ids:
                self.wrong_answer_ids.append(encounter_id)
        else:
            if encounter_id in self.wrong_answer_ids:
                self.wrong_answer_ids.remove(encounter_id)

    def is_alive(self) -> bool:
        return self.hp > 0

    def __repr__(self) -> str:
        return (
            f"Player(name='{self.name}', level={self.level}, "
            f"hp={self.hp}/{self.max_hp}, xp={self.xp}, bits={self.bits})"
        )
