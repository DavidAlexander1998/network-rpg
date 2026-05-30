from dataclasses import dataclass

from game.player import Player
from game.encounter import Encounter

WRONG_ENCOURAGEMENT_XP = 5
HP_PENALTY = 10


@dataclass
class CombatResult:
    xp_gained: int
    bits_gained: int
    hp_lost: int
    is_correct: bool
    encounter: Encounter


class Combat:
    def __init__(self, player: Player, encounter: Encounter) -> None:
        self.player = player
        self.encounter = encounter

    def process_answer(self, selected_index: int) -> CombatResult:
        is_correct = self.encounter.check_answer(selected_index)

        if is_correct:
            xp_gained = self.encounter.xp_reward
            bits_gained = self.encounter.bits_reward
            hp_lost = 0
            self.player.add_xp(xp_gained)
            self.player.add_bits(bits_gained)
        else:
            xp_gained = WRONG_ENCOURAGEMENT_XP
            bits_gained = 0
            hp_lost = HP_PENALTY if not self.player.free_study_mode else 0
            self.player.add_xp(xp_gained)
            if hp_lost:
                self.player.take_damage(hp_lost)

        self.player.record_encounter(self.encounter.id, is_correct)

        return CombatResult(
            xp_gained=xp_gained,
            bits_gained=bits_gained,
            hp_lost=hp_lost,
            is_correct=is_correct,
            encounter=self.encounter,
        )

    def get_correct_answer_text(self) -> str:
        return self.encounter.get_correct_answer()

    def get_explanation(self) -> str:
        return self.encounter.explanation
