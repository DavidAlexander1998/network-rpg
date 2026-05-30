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
enc = Encounter.from_dict(data)
assert enc.id == "z1-n1-001"
assert enc.encounter_type == "mob"   # 'type' mapped to encounter_type
assert enc.zone == 1
assert enc.tags == ["OSI"]
out = enc.to_dict()
assert out["type"] == "mob"          # serialized back as 'type'
assert out["zone"] == 1
print("[OK] from_dict / to_dict")

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
# Check node IDs match spec
node_ids = [n.id for n in z.nodes]
assert 1.1 in node_ids
assert 1.8 in node_ids
# Each node should have 10 encounters
for node in z.nodes:
    assert len(node.encounters) >= 10, f"Node {node.id} has only {len(node.encounters)} encounters"
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

print("\n=== TEST 13: Node completion (70% threshold) ===")
p_node = Player("NodeTest")
z1 = zm.get_zone(1)
node_1_1 = z1.nodes[0]
total = len(node_1_1.encounters)
# Mark 70% correct
threshold = int(total * 0.70)
for i, enc_obj in enumerate(node_1_1.encounters):
    p_node.record_encounter(enc_obj.id, i < threshold)
assert node_1_1.is_node_completed(p_node) is True
# Mark only 50% correct
p_bad = Player("BadTest")
for i, enc_obj in enumerate(node_1_1.encounters):
    p_bad.record_encounter(enc_obj.id, i < total // 2)
assert node_1_1.is_node_completed(p_bad) is False
print("[OK] Node completion threshold")

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

print("\n=== ALL TESTS PASSED ===")
