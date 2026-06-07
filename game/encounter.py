from typing import List, Dict, Any, Optional


CLI_ENCOUNTER = "cli_encounter"
TOPOLOGY_ENCOUNTER = "topology_encounter"


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
        scenario: str = "",
        objective: str = "",
        command_prompt: str = "",
        correct_answers: Optional[List[str]] = None,
        accepts_partial: bool = False,
        hint: str = "",
        ascii_diagram: str = "",
    ) -> None:
        if encounter_type == CLI_ENCOUNTER:
            if not correct_answers:
                raise ValueError("cli_encounter requires at least one correct_answers entry")
        else:
            if not options:
                raise ValueError("Options cannot be empty")
            if not (0 <= correct_index < len(options)):
                raise ValueError(f"correct_index {correct_index} out of range for {len(options)} options")

        self.id: str = id
        self.question: str = question
        self.options: List[str] = options
        self.correct_index: int = correct_index
        self.explanation: str = explanation
        self.xp_reward: int = xp_reward
        self.bits_reward: int = bits_reward
        self.difficulty: str = difficulty
        self.encounter_type: str = encounter_type
        self.zone: int = zone
        self.node: float = node
        self.tags: List[str] = tags or []

        # cli_encounter fields
        self.scenario: str = scenario
        self.objective: str = objective
        self.command_prompt: str = command_prompt
        self.correct_answers: List[str] = correct_answers or []
        self.accepts_partial: bool = accepts_partial
        self.hint: str = hint

        # topology_encounter field (rendered above a normal multiple-choice question)
        self.ascii_diagram: str = ascii_diagram

    def check_answer(self, selected_index: int) -> bool:
        if not (0 <= selected_index < len(self.options)):
            raise ValueError(f"selected_index {selected_index} out of range")
        return selected_index == self.correct_index

    def check_cli_answer(self, answer: str) -> bool:
        normalized = " ".join(answer.strip().lower().split())
        if not normalized:
            return False
        for correct in self.correct_answers:
            correct_normalized = " ".join(correct.strip().lower().split())
            if normalized == correct_normalized:
                return True
            if self.accepts_partial and self._is_abbreviation(normalized, correct_normalized):
                return True
        return False

    @staticmethod
    def _is_abbreviation(typed: str, full: str) -> bool:
        """Cisco-style abbreviation match: each typed word is a non-empty prefix
        of the corresponding word in the full command (e.g. 'sh ip int br' -> 'show ip interface brief')."""
        typed_words = typed.split()
        full_words = full.split()
        if len(typed_words) != len(full_words):
            return False
        return all(
            typed_word and full_word.startswith(typed_word)
            for typed_word, full_word in zip(typed_words, full_words)
        )

    def get_correct_answer(self) -> str:
        if self.encounter_type == CLI_ENCOUNTER:
            return self.correct_answers[0]
        return self.options[self.correct_index]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Encounter":
        encounter_type = data.get("type", "mob")
        if encounter_type == CLI_ENCOUNTER:
            required = ["id", "scenario", "objective", "correct_answers", "explanation"]
        else:
            required = ["id", "question", "options", "correct_index", "explanation"]
        for key in required:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")
        return cls(
            id=data["id"],
            question=data.get("question", data.get("scenario", "")),
            options=data.get("options", []),
            correct_index=data.get("correct_index", 0),
            explanation=data["explanation"],
            xp_reward=data.get("xp_reward", 20),
            bits_reward=data.get("bits_reward", 10),
            difficulty=data.get("difficulty", "easy"),
            encounter_type=encounter_type,
            zone=data.get("zone", 0),
            node=data.get("node", 0.0),
            tags=data.get("tags", []),
            scenario=data.get("scenario", ""),
            objective=data.get("objective", ""),
            command_prompt=data.get("command_prompt", ""),
            correct_answers=data.get("correct_answers"),
            accepts_partial=data.get("accepts_partial", False),
            hint=data.get("hint", ""),
            ascii_diagram=data.get("ascii_diagram", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "id": self.id,
            "zone": self.zone,
            "node": self.node,
            "difficulty": self.difficulty,
            "type": self.encounter_type,
            "explanation": self.explanation,
            "xp_reward": self.xp_reward,
            "bits_reward": self.bits_reward,
            "tags": self.tags,
        }
        if self.encounter_type == CLI_ENCOUNTER:
            base.update({
                "scenario": self.scenario,
                "objective": self.objective,
                "command_prompt": self.command_prompt,
                "correct_answers": self.correct_answers,
                "accepts_partial": self.accepts_partial,
                "hint": self.hint,
            })
        else:
            base.update({
                "question": self.question,
                "options": self.options,
                "correct_index": self.correct_index,
            })
            if self.ascii_diagram:
                base["ascii_diagram"] = self.ascii_diagram
        return base

    def __repr__(self) -> str:
        return f"Encounter(id='{self.id}', difficulty='{self.difficulty}')"
