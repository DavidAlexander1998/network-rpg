"""Adaptive mastery + weak-spot targeting engine.

Pure functions over a Player's attempt history and the loaded content. This is
the backbone of the study tool: it converts raw attempt data into (1) a
per-objective mastery picture so the learner sees exactly where they're shaky,
and (2) a prioritized drill queue that serves the questions most worth doing
next — recently-missed items first, then seen-but-not-yet-learned, then fresh
questions from the weakest objectives.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from game.player import Player
from game.zone_manager import ZoneManager
from game.encounter import Encounter

# Accuracy bands for labelling an objective.
MASTERED_THRESHOLD = 0.85
WEAK_THRESHOLD = 0.70
# A question is treated as "learned" once answered correctly this many times
# in a row — it then drops out of the active drill rotation.
LEARNED_STREAK = 2
# Minimum attempts before an objective's accuracy is considered meaningful.
MIN_SEEN_FOR_SIGNAL = 3


@dataclass
class ObjectiveStat:
    zone: int
    node_id: str
    name: str
    total_questions: int
    seen: int           # distinct questions attempted at least once
    attempts: int       # total attempts (includes repeats)
    correct: int        # total correct attempts
    learned: int        # questions answered correctly LEARNED_STREAK times in a row

    @property
    def accuracy(self) -> float:
        return (self.correct / self.attempts) if self.attempts else 0.0

    @property
    def coverage(self) -> float:
        return (self.seen / self.total_questions) if self.total_questions else 0.0

    @property
    def mastery(self) -> float:
        """Fraction of the objective's questions that are 'learned'."""
        return (self.learned / self.total_questions) if self.total_questions else 0.0

    @property
    def band(self) -> str:
        if self.attempts < MIN_SEEN_FOR_SIGNAL:
            return "unknown"
        if self.accuracy >= MASTERED_THRESHOLD:
            return "strong"
        if self.accuracy >= WEAK_THRESHOLD:
            return "ok"
        return "weak"


def _consecutive_correct(history: List[bool]) -> int:
    n = 0
    for result in reversed(history):
        if result:
            n += 1
        else:
            break
    return n


def is_learned(history: List[bool]) -> bool:
    return _consecutive_correct(history) >= LEARNED_STREAK


def question_priority(history: List[bool]) -> int:
    """Urgency score for drilling a single question — higher = sooner.

    100  most recent attempt was WRONG (re-test immediately, spaced-rep style)
     70  seen but not yet learned (only one correct, still shaky)
     50  never seen (needs first exposure)
      0  learned (correct LEARNED_STREAK times in a row) — rest it
    """
    if not history:
        return 50
    if not history[-1]:
        return 100
    if is_learned(history):
        return 0
    return 70


def _all_node_encounters(zm: ZoneManager):
    """Yield (zone_num, node, encounter) for every non-guardian question."""
    for zone_num in range(1, 6):
        zone = zm.get_zone(zone_num)
        if not zone:
            continue
        for node in zone.nodes:
            for enc in node.encounters:
                yield zone_num, node, enc


def objective_stats(player: Player, zm: ZoneManager) -> List[ObjectiveStat]:
    """One ObjectiveStat per node (= one exam objective), sorted weakest-first."""
    buckets: Dict[str, ObjectiveStat] = {}
    for zone_num, node, enc in _all_node_encounters(zm):
        node_id = str(node.id)
        stat = buckets.get(node_id)
        if stat is None:
            stat = ObjectiveStat(
                zone=zone_num, node_id=node_id, name=node.name,
                total_questions=0, seen=0, attempts=0, correct=0, learned=0,
            )
            buckets[node_id] = stat
        stat.total_questions += 1
        history = player.attempts.get(enc.id, [])
        if history:
            stat.seen += 1
            stat.attempts += len(history)
            stat.correct += sum(1 for r in history if r)
            if is_learned(history):
                stat.learned += 1

    stats = list(buckets.values())
    # Weakest first: unknown/low-coverage and low-accuracy float to the top.
    stats.sort(key=lambda s: (s.band != "weak", s.mastery, s.accuracy))
    return stats


def weak_objectives(player: Player, zm: ZoneManager, limit: int = 5) -> List[ObjectiveStat]:
    """Objectives most in need of work: started, with sub-mastery performance."""
    stats = objective_stats(player, zm)
    candidates = [s for s in stats if s.attempts >= MIN_SEEN_FOR_SIGNAL and s.mastery < 1.0]
    candidates.sort(key=lambda s: (s.accuracy, s.mastery))
    return candidates[:limit]


def build_drill_queue(
    player: Player,
    zm: ZoneManager,
    focus_node_ids: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Encounter]:
    """Prioritized list of questions to drill next.

    Ordered by per-question urgency (recently-missed > shaky > unseen > learned),
    with the weakest objectives breaking ties so attention flows to trouble
    areas. ``focus_node_ids`` restricts the pool to specific objectives.
    """
    import random

    # Per-objective accuracy, used as a tie-breaker (lower = drilled first).
    obj_accuracy = {s.node_id: s.accuracy for s in objective_stats(player, zm)}

    scored = []
    for _zone_num, node, enc in _all_node_encounters(zm):
        node_id = str(node.id)
        if focus_node_ids and node_id not in focus_node_ids:
            continue
        history = player.attempts.get(enc.id, [])
        priority = question_priority(history)
        if priority == 0:
            continue  # already learned — skip
        # Sort key: high priority first, then weakest objective, then random.
        scored.append((-priority, obj_accuracy.get(node_id, 0.0), random.random(), enc))

    scored.sort(key=lambda t: (t[0], t[1], t[2]))
    return [enc for *_rest, enc in scored[:limit]]


def overall_readiness(player: Player, zm: ZoneManager) -> Dict[str, float]:
    """Coarse readiness summary across all objectives (0-100 scale)."""
    stats = objective_stats(player, zm)
    total_q = sum(s.total_questions for s in stats)
    learned = sum(s.learned for s in stats)
    seen = sum(s.seen for s in stats)
    attempts = sum(s.attempts for s in stats)
    correct = sum(s.correct for s in stats)
    return {
        "mastery_pct": (learned / total_q * 100) if total_q else 0.0,
        "coverage_pct": (seen / total_q * 100) if total_q else 0.0,
        "accuracy_pct": (correct / attempts * 100) if attempts else 0.0,
        "total_questions": total_q,
        "learned": learned,
    }
