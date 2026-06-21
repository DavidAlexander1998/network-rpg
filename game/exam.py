"""Exam Simulator — a timed, domain-weighted full-length mock.

Mirrors the real N10-009: ~90 questions drawn across the five domains at their
official weightings, a 90-minute clock, and a score reported on CompTIA's
100–900 scale (720 to pass). Its job is calibration and pacing — telling the
learner whether they're actually ready and where they bleed points by domain.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from game.player import Player
from game.zone_manager import ZoneManager
from game.encounter import Encounter

EXAM_QUESTIONS = 90
EXAM_MINUTES = 90
SCALE_MIN = 100
SCALE_MAX = 900
PASS_SCORE = 720

DOMAIN_NAMES = {
    1: "1.0 Networking Concepts",
    2: "2.0 Network Implementation",
    3: "3.0 Network Operations",
    4: "4.0 Network Security",
    5: "5.0 Network Troubleshooting",
}

# Official N10-009 domain weights.
DOMAIN_WEIGHTS = {1: 0.23, 2: 0.20, 3: 0.19, 4: 0.14, 5: 0.24}


def _question_counts(total: int) -> Dict[int, int]:
    """Split `total` questions across domains by weight, summing exactly to total."""
    counts = {z: int(total * w) for z, w in DOMAIN_WEIGHTS.items()}
    # Distribute rounding remainder to the heaviest domains first.
    remainder = total - sum(counts.values())
    for z in sorted(DOMAIN_WEIGHTS, key=lambda k: DOMAIN_WEIGHTS[k], reverse=True):
        if remainder <= 0:
            break
        counts[z] += 1
        remainder -= 1
    return counts


def _zone_pool(zm: ZoneManager, zone_num: int) -> List[Encounter]:
    zone = zm.get_zone(zone_num)
    if not zone:
        return []
    pool = [enc for node in zone.nodes for enc in node.encounters]
    pool += list(zone.guardian_encounters)
    return pool


def build_exam(zm: ZoneManager, total: int = EXAM_QUESTIONS,
               rng: Optional[random.Random] = None) -> List[Encounter]:
    """A shuffled, domain-weighted question set for one exam attempt."""
    rng = rng or random
    counts = _question_counts(total)
    selected: List[Encounter] = []
    for zone_num, want in counts.items():
        pool = _zone_pool(zm, zone_num)
        rng.shuffle(pool)
        selected.extend(pool[:want])
    rng.shuffle(selected)
    return selected


def scaled_score(correct: int, total: int) -> int:
    """Map raw accuracy onto CompTIA's 100–900 scale (linear approximation)."""
    if total <= 0:
        return SCALE_MIN
    frac = correct / total
    return round(SCALE_MIN + frac * (SCALE_MAX - SCALE_MIN))


@dataclass
class ExamResult:
    correct: int
    total: int
    seconds: float
    per_domain: Dict[int, Dict[str, int]] = field(default_factory=dict)

    @property
    def score(self) -> int:
        return scaled_score(self.correct, self.total)

    @property
    def passed(self) -> bool:
        return self.score >= PASS_SCORE

    @property
    def accuracy_pct(self) -> float:
        return (self.correct / self.total * 100) if self.total else 0.0

    @property
    def over_time(self) -> bool:
        return self.seconds > EXAM_MINUTES * 60


class ExamSession:
    """Tracks a single attempt's clock and per-domain tally."""

    def __init__(self, questions: List[Encounter]) -> None:
        self.questions = questions
        self.start_time: float = 0.0
        self.correct = 0
        self.per_domain: Dict[int, Dict[str, int]] = {
            z: {"correct": 0, "total": 0} for z in DOMAIN_NAMES
        }

    def start(self) -> None:
        self.start_time = time.monotonic()

    def seconds_remaining(self) -> float:
        elapsed = time.monotonic() - self.start_time
        return max(0.0, EXAM_MINUTES * 60 - elapsed)

    def time_up(self) -> bool:
        return self.seconds_remaining() <= 0

    def record(self, encounter: Encounter, is_correct: bool) -> None:
        zone = encounter.zone if encounter.zone in self.per_domain else 1
        self.per_domain[zone]["total"] += 1
        if is_correct:
            self.correct += 1
            self.per_domain[zone]["correct"] += 1

    def result(self, answered: int) -> ExamResult:
        return ExamResult(
            correct=self.correct,
            total=answered,
            seconds=time.monotonic() - self.start_time,
            per_domain={z: d for z, d in self.per_domain.items() if d["total"] > 0},
        )
