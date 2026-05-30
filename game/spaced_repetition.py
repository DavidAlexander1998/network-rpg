from collections import deque
from typing import List, Optional, Dict

REVIEW_THRESHOLD = 10


class SpacedRepetition:
    def __init__(self, review_threshold: int = REVIEW_THRESHOLD) -> None:
        self.failed_queue: deque = deque()
        self.correct_count: int = 0
        self.review_threshold: int = review_threshold
        self.encounter_history: Dict[str, List[bool]] = {}

    def sync_from_player(self, wrong_answer_ids: List[str]) -> None:
        """Restore queue from saved player state."""
        self.failed_queue = deque(
            enc_id for enc_id in wrong_answer_ids
            if enc_id not in self.failed_queue
        )

    def add_failed(self, encounter_id: str) -> None:
        if encounter_id not in self.failed_queue:
            self.failed_queue.append(encounter_id)
        if encounter_id not in self.encounter_history:
            self.encounter_history[encounter_id] = []
        self.encounter_history[encounter_id].append(False)

    def record_success(self, encounter_id: str) -> None:
        self.correct_count += 1
        if encounter_id not in self.encounter_history:
            self.encounter_history[encounter_id] = []
        self.encounter_history[encounter_id].append(True)

    def should_review(self) -> bool:
        return len(self.failed_queue) > 0 and self.correct_count >= self.review_threshold

    def get_next_review(self) -> Optional[str]:
        if self.should_review() and self.failed_queue:
            return self.failed_queue[0]
        return None

    def complete_review(self, encounter_id: str, is_correct: bool) -> None:
        if encounter_id in self.failed_queue:
            if is_correct:
                self.failed_queue.remove(encounter_id)
        self.correct_count = 0

    def get_queue(self) -> List[str]:
        return list(self.failed_queue)

    def get_queue_length(self) -> int:
        return len(self.failed_queue)

    def get_stats(self) -> Dict:
        total = sum(len(v) for v in self.encounter_history.values())
        correct = sum(sum(1 for r in v if r) for v in self.encounter_history.values())
        return {
            "queue_length": len(self.failed_queue),
            "correct_until_review": max(0, self.review_threshold - self.correct_count),
            "success_rate": (correct / total * 100) if total else 100.0,
        }

    def clear(self) -> None:
        self.failed_queue.clear()
        self.correct_count = 0
