import random
from typing import List, Dict, Any, Optional


class Encounter:
    def __init__(
        self,
        id: str,
        question: str,
        options: List[str],
        correct_index: int,
        explanation: str,
        xp_reward: int = 20,
        bits_reward: int = 10,
        difficulty: str = "easy",
        encounter_type: str = "mob",
        zone: int = 0,
        node: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> None:
        if not options:
            raise ValueError("Options cannot be empty")
        if not (0 <= correct_index < len(options)):
            raise ValueError(f"correct_index {correct_index} out of range for {len(options)} options")

        self.id: str = id
        self.question: str = question
        self.options: List[str] = list(options)
        self.correct_index: int = correct_index
        self.explanation: str = explanation
        self.xp_reward: int = xp_reward
        self.bits_reward: int = bits_reward
        self.difficulty: str = difficulty
        self.encounter_type: str = encounter_type
        self.zone: int = zone
        self.node: float = node
        self.tags: List[str] = tags or []

    def shuffle_options(self) -> None:
        """Randomize option order and re-point correct_index.

        The source content has a heavy answer-position bias (~73% of correct
        answers sit at index 1). Shuffling at load time forces the player to
        read every option instead of pattern-matching a position, which is how
        the real exam presents answers.
        """
        correct_answer = self.options[self.correct_index]
        random.shuffle(self.options)
        self.correct_index = self.options.index(correct_answer)

    def check_answer(self, selected_index: int) -> bool:
        if not (0 <= selected_index < len(self.options)):
            raise ValueError(f"selected_index {selected_index} out of range")
        return selected_index == self.correct_index

    def get_correct_answer(self) -> str:
        return self.options[self.correct_index]

    @classmethod
    def from_dict(cls, data: Dict[str, Any], shuffle: bool = True) -> "Encounter":
        required = ["id", "question", "options", "correct_index", "explanation"]
        for key in required:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")
        enc = cls(
            id=data["id"],
            question=data["question"],
            options=data["options"],
            correct_index=data["correct_index"],
            explanation=data["explanation"],
            xp_reward=data.get("xp_reward", 20),
            bits_reward=data.get("bits_reward", 10),
            difficulty=data.get("difficulty", "easy"),
            encounter_type=data.get("type", "mob"),
            zone=data.get("zone", 0),
            node=data.get("node", 0.0),
            tags=data.get("tags", []),
        )
        if shuffle:
            enc.shuffle_options()
        return enc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "zone": self.zone,
            "node": self.node,
            "difficulty": self.difficulty,
            "type": self.encounter_type,
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "xp_reward": self.xp_reward,
            "bits_reward": self.bits_reward,
            "tags": self.tags,
        }

    def __repr__(self) -> str:
        return f"Encounter(id='{self.id}', difficulty='{self.difficulty}')"
