"""Baked-in 30-day study plan for N10-009.

Tailored to a learner who is shaky (especially subnetting, security,
troubleshooting) with ~1-2 focused hours/day. Sequencing follows exam weight
(Troubleshooting 24%, Concepts 23%, Implementation 20%, Operations 19%,
Security 14%) and front-loads a baseline mock so weak-spot data exists early.

The plan is data-driven: each day has a theme and 2-3 concrete tasks that map
directly to the tool's modes. ``current_day`` derives the day number from the
player's start date so the tool can always answer "what do I do today?".
"""

from datetime import date
from typing import Dict, List, Optional

PLAN_LENGTH = 30


def _d(day: int, phase: str, focus: str, tasks: List[str]) -> Dict:
    return {"day": day, "phase": phase, "focus": focus, "tasks": tasks}


# fmt: off
PLAN: List[Dict] = [
    # ---- Week 1: Baseline + Networking Concepts (Domain 1, 23%) ----
    _d(1, "Foundations", "Baseline + orientation", [
        "Exam Simulator — take a full mock COLD to get your starting score (don't study first)",
        "Read your Study Report: note your weakest domains",
        "Acronym Drill x20 to warm up"]),
    _d(2, "Foundations", "Z1 — OSI & appliances", [
        "Story Mode: Zone 1, nodes 1.1 (OSI) + 1.2 (appliances) — study cards then quiz",
        "Subnetting Trainer x10"]),
    _d(3, "Foundations", "Z1 — cloud & ports/protocols", [
        "Story Mode: Zone 1, nodes 1.3 (cloud) + 1.4 (ports/protocols)",
        "Subnetting Trainer x10"]),
    _d(4, "Foundations", "Z1 — media & topologies", [
        "Story Mode: Zone 1, nodes 1.5 (media) + 1.6 (topologies)",
        "Subnetting Trainer x10"]),
    _d(5, "Foundations", "Z1 — IPv4 & modern concepts", [
        "Story Mode: Zone 1, nodes 1.7 (IPv4/subnetting) + 1.8 (SDN/ZTA/IPv6)",
        "Subnetting Trainer x20 — this is your weak spot, push it"]),
    _d(6, "Foundations", "Z1 Guardian + cleanup", [
        "Weak Spot Drill x15",
        "Challenge the Zone 1 Guardian (The OSI Overlord)",
        "Subnetting Trainer x10"]),
    _d(7, "Foundations", "Week 1 review", [
        "Weak Spot Drill x15",
        "Acronym Drill x20",
        "Re-check Study Report — Zone 1 should be trending green"]),

    # ---- Week 2: Implementation (20%) + Operations (19%) ----
    _d(8, "Implementation", "Z2 — routing", [
        "Story Mode: Zone 2, node 2.1 (routing: BGP/OSPF/EIGRP, AD/metric)",
        "Subnetting Trainer x10"]),
    _d(9, "Implementation", "Z2 — switching", [
        "Story Mode: Zone 2, node 2.2 (VLANs, 802.1Q, STP, LAG)",
        "Weak Spot Drill x15"]),
    _d(10, "Implementation", "Z2 — wireless & physical", [
        "Story Mode: Zone 2, nodes 2.3 (wireless) + 2.4 (physical/MDF-IDF)",
        "Subnetting Trainer x10"]),
    _d(11, "Implementation", "Z2 Guardian", [
        "Weak Spot Drill x15",
        "Challenge the Zone 2 Guardian (The Routing Warden)"]),
    _d(12, "Operations", "Z3 — monitoring & metrics", [
        "Story Mode: Zone 3, nodes 3.1 (monitoring/SNMP/syslog) + 3.2 (metrics/QoS)",
        "Subnetting Trainer x10"]),
    _d(13, "Operations", "Z3 — docs, HA, DR", [
        "Story Mode: Zone 3, nodes 3.3 (docs) + 3.4 (HA) + 3.5 (DR: RPO/RTO, sites)",
        "Weak Spot Drill x15"]),
    _d(14, "Operations", "Z3 Guardian + mid-point mock", [
        "Challenge the Zone 3 Guardian (The Sentinel of Ops)",
        "Exam Simulator — compare your score to Day 1"]),

    # ---- Week 3: Security (14%) + Troubleshooting (24%) ----
    _d(15, "Security", "Z4 — threats & attacks", [
        "Story Mode: Zone 4, node 4.1 (threat landscape) + 4.2 (attacks)",
        "Weak Spot Drill x15"]),
    _d(16, "Security", "Z4 — firewalls, VPN, PKI", [
        "Story Mode: Zone 4, nodes 4.3 (perimeter/VPN) + 4.4 (PKI/AAA/802.1X)",
        "Acronym Drill x20 (security-heavy)"]),
    _d(17, "Security", "Z4 Guardian", [
        "Weak Spot Drill x15",
        "Challenge the Zone 4 Guardian (The Shadow Firewall)"]),
    _d(18, "Troubleshooting", "Z5 — methodology & cabling", [
        "Story Mode: Zone 5, nodes 5.1 (the 7 steps — memorize order!) + 5.2 (cabling)",
        "Subnetting Trainer x10"]),
    _d(19, "Troubleshooting", "Z5 — commands & wireless", [
        "Story Mode: Zone 5, nodes 5.3 (commands) + 5.4 (wireless issues)",
        "Weak Spot Drill x15"]),
    _d(20, "Troubleshooting", "Z5 — services + Guardian", [
        "Story Mode: Zone 5, node 5.5 (services)",
        "Challenge the Zone 5 Guardian (The Chaos Engineer)"]),
    _d(21, "Checkpoint", "External calibration", [
        "Take a REAL third-party practice exam (Jason Dion / official CompTIA) — calibrate against an outside answer key",
        "Log which domains scored lowest"]),

    # ---- Week 4: Mocks + targeted remediation ----
    _d(22, "Remediation", "Attack your weakest domain", [
        "Weak Spot Drill x15 (twice)",
        "Re-study the worst objectives' cards from Story/Free Study"]),
    _d(23, "Remediation", "Full mock + review", [
        "Exam Simulator — full 90Q timed",
        "Drill every domain that scored under 80%"]),
    _d(24, "Remediation", "Subnetting fluency check", [
        "Subnetting Trainer x50 — you want 90%+ here, points are guaranteed",
        "Weak Spot Drill x15"]),
    _d(25, "Remediation", "Second weak domain", [
        "Weak Spot Drill x15 (twice)",
        "Acronym Drill — full run"]),
    _d(26, "Remediation", "Full mock", [
        "Exam Simulator — aim for 800+ now",
        "Drill anything still under 80%"]),
    _d(27, "Remediation", "Polish", [
        "Weak Spot Drill x15",
        "Subnetting Trainer x20",
        "Re-read security + troubleshooting study cards"]),
    _d(28, "Taper", "Final mock", [
        "Exam Simulator — last full timed run; you should be comfortably over 720",
        "Light drill on any red domains only"]),
    _d(29, "Taper", "Light review", [
        "Acronym Drill x20",
        "Skim study cards for your 3 weakest objectives — no heavy new material",
        "Rest your brain; sleep well"]),
    _d(30, "Exam Day", "Go pass it", [
        "Quick Acronym Drill x10 warm-up only",
        "Review the 7-step troubleshooting order + port numbers one last time",
        "Trust the prep. You've got this."]),
]
# fmt: on


def current_day(start_date: Optional[str], today: Optional[date] = None) -> int:
    """Day number (1-based) given an ISO start date. Clamps to >=1."""
    if not start_date:
        return 1
    today = today or date.today()
    try:
        start = date.fromisoformat(start_date)
    except (ValueError, TypeError):
        return 1
    return max(1, (today - start).days + 1)


def get_day(day: int) -> Optional[Dict]:
    if 1 <= day <= len(PLAN):
        return PLAN[day - 1]
    return None


def week_of(day: int) -> int:
    return (max(1, day) - 1) // 7 + 1


def days_until_exam(start_date: Optional[str], today: Optional[date] = None) -> int:
    """How many days remain in the 30-day plan (can go negative/zero past day 30)."""
    return PLAN_LENGTH - current_day(start_date, today) + 1
