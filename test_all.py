"""Test suite for Network+ RPG."""

print("=== TEST 1: Player Creation ===")
from game.player import Player, XP_THRESHOLDS
p = Player("Davido")
assert p.name == "Davido"
assert p.hp == 100
assert p.max_hp == 100
assert p.level == 1
assert p.xp == 0
assert p.bits == 0
assert p.skills == []
assert p.inventory == {}
assert p.wrong_answer_ids == []
assert p.encounter_results == {}
assert p.free_study_mode is False
assert len(p.guardian_defeated) == 5
print("[OK] Player creation")

print("\n=== TEST 2: Player XP / Level Thresholds ===")
# Level 1 -> 2 requires 500 XP
assert XP_THRESHOLDS[0] == 500
leveled = p.add_xp(499)
assert leveled is False
assert p.level == 1
leveled = p.add_xp(1)
assert leveled is True
assert p.level == 2
assert p.max_hp == 120  # +20 per level
assert p.xp == 0        # XP consumed on level up
print(f"[OK] Level up: now Level {p.level}, max_hp={p.max_hp}")

print("\n=== TEST 3: Player Combat Methods ===")
p.take_damage(30)
assert p.hp == 90
p.heal(15)
assert p.hp == 105
p.heal(9999)
assert p.hp == p.max_hp  # capped at max_hp
p.add_bits(50)
assert p.bits == 50
assert p.spend_bits(30) is True
assert p.bits == 20
assert p.spend_bits(999) is False  # not enough
assert p.bits == 20
print("[OK] Combat methods")

print("\n=== TEST 4: Player record_encounter ===")
p.record_encounter("z1-n1-001", False)
assert "z1-n1-001" in p.wrong_answer_ids
assert p.encounter_results["z1-n1-001"] is False
p.record_encounter("z1-n1-001", True)
assert "z1-n1-001" not in p.wrong_answer_ids  # cleared on correct
assert p.encounter_results["z1-n1-001"] is True
print("[OK] record_encounter")

print("\n=== TEST 5: Encounter Creation ===")
from game.encounter import Encounter
e = Encounter(
    id="z1-001",
    question="What port does HTTP use?",
    options=["21", "80", "443", "8080"],
    correct_index=1,
    explanation="HTTP uses port 80.",
    xp_reward=20,
    bits_reward=10,
    difficulty="easy",
    encounter_type="mob",
    tags=["Ports", "HTTP"],
)
assert e.check_answer(1) is True
assert e.check_answer(0) is False
assert e.get_correct_answer() == "80"
assert e.difficulty == "easy"
assert e.encounter_type == "mob"
assert e.tags == ["Ports", "HTTP"]
print("[OK] Encounter creation")

print("\n=== TEST 6: Encounter from_dict / to_dict ===")
data = {
    "id": "z1-n1-001", "zone": 1, "node": 1.1, "difficulty": "easy", "type": "mob",
    "question": "Test question?", "options": ["A", "B", "C", "D"],
    "correct_index": 0, "explanation": "A is correct.",
    "xp_reward": 20, "bits_reward": 10, "tags": ["OSI"],
}
enc = Encounter.from_dict(data, shuffle=False)
assert enc.correct_index == 0  # preserved when shuffle disabled
assert enc.id == "z1-n1-001"
assert enc.encounter_type == "mob"   # 'type' mapped to encounter_type
assert enc.zone == 1
assert enc.tags == ["OSI"]
out = enc.to_dict()
assert out["type"] == "mob"          # serialized back as 'type'
assert out["zone"] == 1
print("[OK] from_dict / to_dict")

print("\n=== TEST 6b: Option shuffling preserves the correct answer ===")
import random as _random
_random.seed(1)  # deterministic for the test
moved = 0
for _ in range(50):
    e = Encounter.from_dict(data)  # shuffle=True by default
    # The correct answer TEXT must always still be "A" (the original correct option)
    assert e.get_correct_answer() == "A"
    # check_answer must agree with the (possibly moved) correct_index
    assert e.check_answer(e.correct_index) is True
    if e.correct_index != 0:
        moved += 1
# Over 50 shuffles the correct index should land off position 0 most of the time
assert moved > 0
print(f"[OK] Shuffling: correct answer preserved, moved off index 0 in {moved}/50 runs")

print("\n=== TEST 7: Combat — correct answer ===")
from game.combat import Combat, CombatResult
p2 = Player("TestUser")
result = Combat(p2, enc).process_answer(0)
assert result.is_correct is True
assert result.xp_gained == 20
assert result.bits_gained == 10
assert result.hp_lost == 0
assert p2.encounter_results["z1-n1-001"] is True
print("[OK] Combat correct answer")

print("\n=== TEST 8: Combat — wrong answer gives encouragement XP and HP penalty ===")
p3 = Player("TestUser2")
result2 = Combat(p3, enc).process_answer(1)
assert result2.is_correct is False
assert result2.xp_gained == 5        # encouragement XP
assert result2.bits_gained == 0
assert result2.hp_lost == 10
assert p3.hp == 90
assert p3.encounter_results["z1-n1-001"] is False
assert "z1-n1-001" in p3.wrong_answer_ids
print("[OK] Combat wrong answer")

print("\n=== TEST 9: Combat — free study mode no HP penalty ===")
p4 = Player("FreeStudy")
p4.free_study_mode = True
result3 = Combat(p4, enc).process_answer(1)
assert result3.is_correct is False
assert result3.hp_lost == 0
assert p4.hp == 100  # no damage in free study
print("[OK] Free study mode no HP penalty")

print("\n=== TEST 10: Save / Load with new fields ===")
from game.save_manager import SaveManager
import os
sm = SaveManager("saves")
p5 = Player("SaveTest")
p5.level = 2
p5.xp = 150
p5.skills = ["double_xp"]
p5.inventory = {"health_packet": 2}
p5.wrong_answer_ids = ["z1-n1-001"]
p5.encounter_results = {"z1-n1-001": False}
p5.guardian_defeated[0] = True
ok = sm.save(p5, 1)
assert ok is True
# Backup file created on second save
ok2 = sm.save(p5, 1)
assert ok2 is True
bak = "saves/save_1.yaml.bak"
assert os.path.exists(bak), "Backup file not created"
loaded = sm.load(1)
assert loaded.name == "SaveTest"
assert loaded.level == 2
assert loaded.skills == ["double_xp"]
assert loaded.wrong_answer_ids == ["z1-n1-001"]
assert loaded.encounter_results == {"z1-n1-001": False}
assert loaded.guardian_defeated[0] is True
print("[OK] Save / Load with full fields")

print("\n=== TEST 11: ZoneManager ===")
from game.zone_manager import ZoneManager, Zone, Node
zm = ZoneManager("content")
z = zm.load_zone(1)
assert z is not None
assert z.number == 1
assert len(z.nodes) == 8, f"Expected 8 nodes, got {len(z.nodes)}"
assert len(z.guardian_encounters) == 20, f"Expected 20 guardian questions, got {len(z.guardian_encounters)}"
total_encounters = sum(len(n.encounters) for n in z.nodes)
assert total_encounters == 96, f"Expected 96 encounters, got {total_encounters}"
# Check node IDs match spec (clean sequential 1.1 .. 1.8)
node_ids = [n.id for n in z.nodes]
assert node_ids == [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8], f"Unexpected node ids: {node_ids}"
# Every node needs at least a couple encounters to be playable
for node in z.nodes:
    assert len(node.encounters) >= 2, f"Node {node.id} has only {len(node.encounters)} encounters"
print(f"[OK] Zone 1: {len(z.nodes)} nodes, {len(z.guardian_encounters)} guardian questions")

print("\n=== TEST 12: Zone accessibility ===")
p_test = Player("ZoneTest")
assert zm.is_zone_accessible(1, p_test) is True
assert zm.is_zone_accessible(2, p_test) is False   # story mode, guardian 1 not defeated
p_test.free_study_mode = True
assert zm.is_zone_accessible(2, p_test) is True    # free study bypasses
p_test.free_study_mode = False
p_test.guardian_defeated[0] = True
assert zm.is_zone_accessible(2, p_test) is True    # guardian 1 defeated
print("[OK] Zone accessibility")

print("\n=== TEST 13: Node completion (70% threshold + streak gate) ===")
import math
from game.zone_manager import NODE_PASS_RATE
p_node = Player("NodeTest")
z1 = zm.get_zone(1)
node_1_1 = z1.nodes[0]
total = len(node_1_1.encounters)
# Smallest correct-count that actually clears the pass rate (avoids rounding
# mismatches on nodes that aren't an even multiple of 10 encounters)
need = math.ceil(total * NODE_PASS_RATE)
for i, enc_obj in enumerate(node_1_1.encounters):
    p_node.record_encounter(enc_obj.id, i < need)
# 70% correct but NO streak recorded -> not complete (anti-guessing gate)
assert node_1_1.is_node_completed(p_node) is False
# Once a 3-in-a-row streak is achieved, it completes
p_node.record_node_streak(str(node_1_1.id), 3)
assert node_1_1.is_node_completed(p_node) is True
# A streak alone without the pass rate is not enough
p_bad = Player("BadTest")
for i, enc_obj in enumerate(node_1_1.encounters):
    p_bad.record_encounter(enc_obj.id, i < total // 2)
p_bad.record_node_streak(str(node_1_1.id), 5)
assert node_1_1.is_node_completed(p_bad) is False
# record_node_streak only keeps the best
p_node.record_node_streak(str(node_1_1.id), 2)
assert p_node.node_streaks[str(node_1_1.id)] == 3
print("[OK] Node completion threshold + streak gate")

print("\n=== TEST 14: SpacedRepetition ===")
from game.spaced_repetition import SpacedRepetition
sr = SpacedRepetition(review_threshold=3)
sr.add_failed("q1")
sr.add_failed("q2")
assert sr.get_next_review() is None   # threshold not reached
sr.record_success("q3")
sr.record_success("q4")
sr.record_success("q5")
assert sr.get_next_review() == "q1"   # threshold reached
sr.complete_review("q1", True)        # answered correctly
assert "q1" not in sr.get_queue()
sr.add_failed("q1")                   # answer wrong again, re-queued
assert "q1" in sr.get_queue()
print("[OK] SpacedRepetition")

print("\n=== TEST 15: Validators ===")
from utils.validators import validate_non_empty_string, validate_int_in_range, validate_slot_number
assert validate_non_empty_string("  hello  ") == "hello"
assert validate_int_in_range("5", 1, 10) == 5
assert validate_slot_number("2") == 2
try:
    validate_slot_number("99")
    assert False, "Should have raised"
except ValueError:
    pass
print("[OK] Validators")

print("\n=== TEST 16: cli_encounter — creation, matching, Combat ===")
cli_data = {
    "id": "z1-cli-001", "zone": 1, "node": 1.1, "type": "cli_encounter", "difficulty": "easy",
    "scenario": "The link light is dark.", "objective": "Check interface status.",
    "command_prompt": "Router>",
    "correct_answers": ["show ip interface brief", "sh ip int br", "show ip interface"],
    "accepts_partial": True,
    "hint": "Try 'show' + 'ip interface brief'.",
    "explanation": "show ip interface brief summarizes interface status.",
    "xp_reward": 50, "bits_reward": 25, "tags": ["CLI", "Cisco"],
}
cli_enc = Encounter.from_dict(cli_data)
assert cli_enc.encounter_type == "cli_encounter"
assert cli_enc.scenario == "The link light is dark."
assert cli_enc.get_correct_answer() == "show ip interface brief"
# Exact match
assert cli_enc.check_cli_answer("show ip interface brief") is True
# Listed alternate, case/whitespace tolerant
assert cli_enc.check_cli_answer("  SH IP INT BR  ") is True
# Abbreviation matching not in the explicit list ("show" -> "sh", "interface" -> "iface" should NOT match)
assert cli_enc.check_cli_answer("sh ip interface brief") is True
assert cli_enc.check_cli_answer("show interface brief") is False  # missing 'ip' word
assert cli_enc.check_cli_answer("configure terminal") is False
assert cli_enc.check_cli_answer("") is False

p_cli = Player("CliTester")
cli_result = Combat(p_cli, cli_enc).process_cli_answer("sh ip int br")
assert cli_result.is_correct is True
assert cli_result.xp_gained == 50
assert cli_result.bits_gained == 25
assert p_cli.encounter_results["z1-cli-001"] is True

p_cli_wrong = Player("CliTester2")
cli_result_wrong = Combat(p_cli_wrong, cli_enc).process_cli_answer("ping 8.8.8.8")
assert cli_result_wrong.is_correct is False
assert cli_result_wrong.hp_lost == 10

# Exact-only matching (accepts_partial False) rejects abbreviations
ping_data = dict(cli_data)
ping_data.update({
    "id": "z1-cli-003", "correct_answers": ["ping 192.168.50.10"], "accepts_partial": False,
})
ping_enc = Encounter.from_dict(ping_data)
assert ping_enc.check_cli_answer("ping 192.168.50.10") is True
assert ping_enc.check_cli_answer("ping 192.168.50.1") is False
print("[OK] cli_encounter creation, matching, Combat")

print("\n=== TEST 17: topology_encounter — diagram + multiple choice ===")
topo_data = {
    "id": "topo-001", "type": "topology_encounter", "name": "The Lonely Hub", "difficulty": "easy",
    "ascii_diagram": "[H1]---[S1]---[H2]",
    "question": "What is the single point of failure?",
    "options": ["The Router", "The Central Switch [S1]", "The Host H1", "The Cables"],
    "correct_index": 1,
    "explanation": "If S1 fails, all hosts lose connectivity.",
    "xp_reward": 40, "bits_reward": 20, "tags": ["topology"],
}
topo_enc = Encounter.from_dict(topo_data)
assert topo_enc.encounter_type == "topology_encounter"
assert topo_enc.ascii_diagram == "[H1]---[S1]---[H2]"
assert topo_enc.check_answer(1) is True
assert topo_enc.check_answer(0) is False
assert topo_enc.get_correct_answer() == "The Central Switch [S1]"

p_topo = Player("TopoTester")
topo_result = Combat(p_topo, topo_enc).process_answer(1)
assert topo_result.is_correct is True
assert topo_result.xp_gained == 40
print("[OK] topology_encounter creation, Combat")

print("\n=== TEST 18: Bonus content files load cleanly ===")
import json as _json
from pathlib import Path as _Path
for fname, expect_min in (("cli-encounters.json", 5), ("topology-encounters.json", 5)):
    raw = _json.load(open(_Path("content") / fname, encoding="utf-8"))
    assert isinstance(raw, list) and len(raw) >= expect_min
    for item in raw:
        loaded = Encounter.from_dict(item)
        assert loaded.id
flavor = _json.load(open(_Path("content") / "flavor-texts.json", encoding="utf-8"))
assert set(flavor.keys()) >= {"zone_entries", "node_transitions", "encounter_intros"}
assert all(str(z) in flavor["zone_entries"] for z in range(1, 6))
assert len(flavor["node_transitions"]) >= 5
assert len(flavor["encounter_intros"]) >= 5
print("[OK] Bonus content files (cli-encounters, topology-encounters, flavor-texts)")

print("\n=== TEST 19: Attempt history persists ===")
p_att = Player("AttemptTest")
p_att.record_encounter("z1-n1-001", False)
p_att.record_encounter("z1-n1-001", True)
assert p_att.attempts["z1-n1-001"] == [False, True]
import tempfile as _tf
sm2 = SaveManager(_tf.mkdtemp())
sm2.save(p_att, 1)
reloaded = sm2.load(1)
assert reloaded.attempts == {"z1-n1-001": [False, True]}
print("[OK] Attempt history persists")

print("\n=== TEST 20: Mastery engine — weak spots & drill queue ===")
from game import mastery
zm2 = ZoneManager("content")
for _z in range(1, 6):
    zm2.load_zone(_z)
p_m = Player("MasteryTest")
z1m = zm2.get_zone(1)
n_a, n_b = z1m.nodes[0], z1m.nodes[1]
# Node A: answer everything correctly twice -> learned/strong
for enc in n_a.encounters:
    p_m.record_encounter(enc.id, True)
    p_m.record_encounter(enc.id, True)
# Node B: answer everything wrong -> weak
for enc in n_b.encounters:
    p_m.record_encounter(enc.id, False)

stats = {s.node_id: s for s in mastery.objective_stats(p_m, zm2)}
assert stats[str(n_a.id)].band == "strong"
assert stats[str(n_b.id)].band == "weak"
assert stats[str(n_a.id)].learned == n_a.encounters.__len__()
assert stats[str(n_b.id)].learned == 0

weak = mastery.weak_objectives(p_m, zm2, limit=5)
assert weak and weak[0].node_id == str(n_b.id)  # worst objective surfaces first

# Drill queue must prioritize the wrong (node B) questions and skip learned (node A)
q = mastery.build_drill_queue(p_m, zm2, limit=10)
qids = {e.id for e in q}
a_ids = {e.id for e in n_a.encounters}
b_ids = {e.id for e in n_b.encounters}
assert qids & b_ids, "weak questions should be queued"
assert not (qids & a_ids), "learned questions should be skipped"

# question_priority sanity
assert mastery.question_priority([]) == 50          # unseen
assert mastery.question_priority([False]) == 100    # just missed
assert mastery.question_priority([True]) == 70       # shaky (one correct)
assert mastery.question_priority([True, True]) == 0   # learned
print("[OK] Mastery engine")

print("\n=== TEST 21: Subnetting generator ===")
from game import subnetting
import ipaddress as _ip
_rng = __import__("random").Random(42)
for _ in range(300):
    prob = subnetting.generate_problem(_rng)
    assert len(prob.options) == 4, prob.options
    assert len(set(prob.options)) == 4, f"duplicate options: {prob.options}"
    assert 0 <= prob.correct_index < 4
    # The correct answer must be retrievable and consistent
    assert prob.get_correct_answer() == prob.options[prob.correct_index]
    assert prob.id == subnetting.GEN_ID
# Spot-check a known network-address calculation is actually correct
random_check = 0
for _ in range(200):
    p = subnetting._gen_network_address(_rng)
    # Parse the question's IP/prefix and verify the correct option is the real network
    q = p.question
    token = [t for t in q.replace("?", "").split() if "/" in t][0]
    net = _ip.ip_network(token, strict=False)
    assert p.get_correct_answer() == str(net.network_address)
    random_check += 1
assert random_check == 200
print(f"[OK] Subnetting generator ({random_check} network-address checks verified)")

print("\n=== TEST 22: Exam simulator build + scoring ===")
from game import exam
zm3 = ZoneManager("content")
for _z in range(1, 6):
    zm3.load_zone(_z)
qs = exam.build_exam(zm3)
assert len(qs) == exam.EXAM_QUESTIONS, len(qs)
counts = exam._question_counts(90)
assert sum(counts.values()) == 90
# Z5 (24%) and Z1 (23%) are heaviest and absorb the rounding remainder
assert counts == {1: 21, 2: 18, 3: 17, 4: 12, 5: 22}, counts
# Scoring scale
assert exam.scaled_score(0, 90) == 100
assert exam.scaled_score(90, 90) == 900
sc = exam.scaled_score(72, 90)   # 80%
assert sc == round(100 + 0.8 * 800) == 740
# Session tally + pass logic
sess = exam.ExamSession(qs)
sess.start()
for i, e in enumerate(qs):
    sess.record(e, i % 5 != 0)  # 80% correct
res = sess.result(len(qs))
assert res.total == 90
assert res.passed is True       # 80% -> 740 >= 720
assert all(d["total"] > 0 for d in res.per_domain.values())
print(f"[OK] Exam simulator (sample score {res.score}, passed={res.passed})")

print("\n=== TEST 23: 30-day study plan ===")
from game import study_plan
from datetime import date, timedelta
assert len(study_plan.PLAN) == study_plan.PLAN_LENGTH == 30
# Every day is well-formed and numbered in sequence
for i, day in enumerate(study_plan.PLAN, start=1):
    assert day["day"] == i
    assert day["focus"] and day["phase"]
    assert len(day["tasks"]) >= 2
# current_day math
assert study_plan.current_day(None) == 1
start = (date.today() - timedelta(days=4)).isoformat()
assert study_plan.current_day(start) == 5
assert study_plan.current_day("garbage") == 1
assert study_plan.week_of(1) == 1 and study_plan.week_of(8) == 2 and study_plan.week_of(30) == 5
assert study_plan.get_day(1)["focus"]
assert study_plan.get_day(31) is None
# start_date persists on the player
p_sd = Player("PlanTester")
assert p_sd.start_date == date.today().isoformat()
sm3 = SaveManager(_tf.mkdtemp())
sm3.save(p_sd, 1)
assert sm3.load(1).start_date == p_sd.start_date
print("[OK] 30-day study plan")

print("\n=== TEST 24: Study content integrity (incl. new Phase-4 cards) ===")
import json as _json
from pathlib import Path as _Path
VALID_TYPES = {"table", "concept", "mnemonic", "list"}
total_cards = 0
for sf in sorted(_Path("content").glob("study-*.json")):
    raw = _json.load(open(sf, encoding="utf-8"))
    for obj, cards in raw.items():
        for c in cards:
            total_cards += 1
            assert c.get("type") in VALID_TYPES, f"{sf} {obj}: bad type {c.get('type')}"
            assert c.get("title"), f"{sf} {obj}: missing title"
            # mnemonic/concept cards must actually have teaching content
            if c["type"] in ("mnemonic", "concept"):
                assert c.get("body"), f"{sf} {obj} '{c['title']}': empty body"
# Confirm the specific new cards landed and parse via the real loader
zm4 = ZoneManager("content")
for _z in range(1, 6):
    zm4.load_zone(_z)
n51 = next(n for n in zm4.get_zone(5).nodes if str(n.id) == "5.1")
assert any(c.card_type == "mnemonic" and "7-Step" in c.title for c in n51.study_cards)
print(f"[OK] Study content integrity ({total_cards} cards across all study files)")

print("\n=== TEST 25: Subnetting free-entry checking ===")
from game import subnetting as _sub
# IP answers: tolerant of surrounding text, exact IP match required
assert _sub.check_free_answer("192.168.10.64", "192.168.10.64") is True
assert _sub.check_free_answer("192.168.10.64", " the network is 192.168.10.64 ") is True
assert _sub.check_free_answer("192.168.10.64", "192.168.10.65") is False
# range answers (two IPs, order matters)
assert _sub.check_free_answer("10.0.0.1 – 10.0.0.62", "10.0.0.1 - 10.0.0.62") is True
assert _sub.check_free_answer("10.0.0.1 – 10.0.0.62", "10.0.0.62 - 10.0.0.1") is False
# CIDR: accept with or without slash
assert _sub.check_free_answer("/26", "26") is True and _sub.check_free_answer("/26", "/26") is True
# host counts: ignore commas
assert _sub.check_free_answer("62", "62") is True and _sub.check_free_answer("16382", "16,382") is True
assert _sub.check_free_answer("62", "63") is False
assert _sub.check_free_answer("62", "") is False and _sub.check_free_answer("62", None) is False
# generated problems are answerable by their own correct text
for _ in range(200):
    pr = _sub.generate_problem(_random.Random())
    assert _sub.check_free_answer(pr.get_correct_answer(), pr.get_correct_answer()) is True
    assert _sub.answer_hint(pr.get_correct_answer())  # non-empty hint
print("[OK] Subnetting free-entry checking")

print("\n=== TEST 26: Command Lab scenarios ===")
from game import command_lab
assert len(command_lab.SCENARIOS) >= 3
for s in command_lab.SCENARIOS:
    assert 0 <= s.answer_index < len(s.options)
    assert s.brief and s.question and s.explanation
    # every advertised command (canonical, ignoring args note) returns real output
    for c in s.commands:
        assert s.run_command(c) == s.commands[c]
    # whitespace/case tolerance
    any_cmd = next(iter(s.commands))
    assert s.run_command("  " + any_cmd.upper() + " ") == s.commands[any_cmd]
    # unknown command gives guidance, not a crash
    assert "not recognized" in s.run_command("frobnicate the router").lower()
# alias resolves
dns = command_lab.get_scenario("dns")
assert dns.run_command("nslookup") == dns.commands["nslookup google.com"]
print(f"[OK] Command Lab ({len(command_lab.SCENARIOS)} scenarios)")

print("\n=== TEST 27: PBQ ordering/matching tasks ===")
from game import tasks_pbq
assert tasks_pbq.ORDERING_TASKS and tasks_pbq.MATCHING_TASKS
for t in tasks_pbq.ORDERING_TASKS:
    assert len(t.ordered) == len(set(t.ordered)) >= 3   # unique, non-trivial
    assert t.prompt and t.explanation
for t in tasks_pbq.MATCHING_TASKS:
    lefts = [l for l, r in t.pairs]
    rights = [r for l, r in t.pairs]
    assert len(lefts) == len(set(lefts))      # unique left keys
    assert len(rights) == len(set(rights))    # unique right answers (matchable)
    assert t.prompt and t.explanation
# 7-step troubleshooting task is present and correctly ordered
ts = tasks_pbq.get_ordering("troubleshoot-steps")
assert ts.ordered[0].startswith("Identify") and ts.ordered[-1].startswith("Document")
print(f"[OK] PBQ tasks ({len(tasks_pbq.ORDERING_TASKS)} ordering, {len(tasks_pbq.MATCHING_TASKS)} matching)")

print("\n=== ALL TESTS PASSED ===")
