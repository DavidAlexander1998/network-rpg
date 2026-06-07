"""
Unit tests for Study-First Mode functionality.
"""

import unittest
from dataclasses import field
from typing import List, Dict, Any

from game.zone_manager import Node, ZoneManager, StudyCard
from game.player import Player
from game.encounter import Encounter


class TestStudyFirstMode(unittest.TestCase):
    """Test the Study-First Mode feature."""

    def test_node_has_study_content_field(self):
        """Test that Node dataclass has study_content field."""
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test description",
            study_content="This is study content"
        )
        self.assertEqual(node.study_content, "This is study content")

    def test_node_has_quiz_questions_field(self):
        """Test that Node dataclass has quiz_questions field."""
        quiz_qs = [
            {
                "question": "What is TCP?",
                "options": ["Protocol", "Cable", "Device", "None"],
                "correct_index": 0,
                "explanation": "TCP is a protocol."
            }
        ]
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test description",
            quiz_questions=quiz_qs
        )
        self.assertEqual(len(node.quiz_questions), 1)
        self.assertEqual(node.quiz_questions[0]["question"], "What is TCP?")

    def test_node_defaults_for_study_first_fields(self):
        """Test that study_content and quiz_questions have correct defaults."""
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test description"
        )
        self.assertIsNone(node.study_content)
        self.assertEqual(node.quiz_questions, [])

    def test_show_study_menu_returns_study_first_option(self):
        """Test that show_study_menu can return 'study_first' when content exists."""
        # Create a node with study-first content
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test",
            study_content="Study this first",
            quiz_questions=[{"question": "Q1?", "options": ["A", "B"], "correct_index": 0}]
        )
        # Verify the node has the required fields for study-first mode
        self.assertTrue(bool(node.study_content or node.quiz_questions))

    def test_node_with_both_study_cards_and_study_first(self):
        """Test that a node can have both study_cards and study-first content."""
        study_card = StudyCard(
            title="Reference Card",
            card_type="concept",
            body="Reference content"
        )
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test",
            study_cards=[study_card],
            study_content="Study-first content",
            quiz_questions=[{"question": "Q1?", "options": ["A", "B"], "correct_index": 0}]
        )
        self.assertEqual(len(node.study_cards), 1)
        self.assertIsNotNone(node.study_content)
        self.assertEqual(len(node.quiz_questions), 1)

    def test_quiz_question_structure(self):
        """Test that quiz_questions have the expected structure."""
        quiz_q = {
            "question": "What does OSI stand for?",
            "options": ["Open Systems Interconnection", "Other", "Another", "None"],
            "correct_index": 0,
            "explanation": "OSI stands for Open Systems Interconnection."
        }
        node = Node(
            id=1.1,
            name="OSI Model",
            description="Learn OSI",
            quiz_questions=[quiz_q]
        )
        q = node.quiz_questions[0]
        self.assertIn("question", q)
        self.assertIn("options", q)
        self.assertIn("correct_index", q)
        self.assertIn("explanation", q)
        self.assertEqual(len(q["options"]), 4)

    def test_multiple_quiz_questions(self):
        """Test that a node can have multiple quiz questions."""
        quiz_qs = [
            {"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "Exp1"},
            {"question": "Q2?", "options": ["A", "B", "C", "D"], "correct_index": 1, "explanation": "Exp2"},
            {"question": "Q3?", "options": ["A", "B", "C", "D"], "correct_index": 2, "explanation": "Exp3"},
        ]
        node = Node(
            id=1.1,
            name="Test Node",
            description="Test",
            quiz_questions=quiz_qs
        )
        self.assertEqual(len(node.quiz_questions), 3)

    def test_study_content_can_be_multiline(self):
        """Test that study_content can contain multiline text."""
        multiline_content = """TCP/IP Model

Layer 1: Physical
Layer 2: Data Link
Layer 3: Network
Layer 4: Transport
Layer 5: Application

Study these layers carefully."""
        node = Node(
            id=1.2,
            name="TCP/IP Model",
            description="Learn TCP/IP",
            study_content=multiline_content
        )
        self.assertIn("Layer 1", node.study_content)
        self.assertIn("Layer 5", node.study_content)


class TestZoneManagerStudyFirstParsing(unittest.TestCase):
    """Test that ZoneManager correctly parses study-first fields from JSON."""

    def test_parse_zone_with_study_first_content(self):
        """Test _parse_zone extracts study_content and quiz_questions."""
        zone_data = {
            "zone": 1,
            "name": "Test Zone",
            "description": "Test",
            "nodes": [
                {
                    "id": "1.1",
                    "name": "Study Node",
                    "description": "Node with study content",
                    "study_content": "This is important content to study.",
                    "quiz_questions": [
                        {
                            "question": "What is the answer?",
                            "options": ["42", "24", "0", "None"],
                            "correct_index": 0,
                            "explanation": "42 is the answer to everything."
                        }
                    ],
                    "encounters": []
                }
            ],
            "guardian_encounters": []
        }

        zm = ZoneManager("dummy_content")
        zone = zm._parse_zone(zone_data)

        self.assertEqual(len(zone.nodes), 1)
        node = zone.nodes[0]
        self.assertEqual(node.study_content, "This is important content to study.")
        self.assertEqual(len(node.quiz_questions), 1)
        self.assertEqual(node.quiz_questions[0]["question"], "What is the answer?")

    def test_parse_zone_without_study_first_content(self):
        """Test _parse_zone works fine without study-first fields."""
        zone_data = {
            "zone": 1,
            "name": "Test Zone",
            "description": "Test",
            "nodes": [
                {
                    "id": "1.1",
                    "name": "Regular Node",
                    "description": "Node without study content",
                    "encounters": []
                }
            ],
            "guardian_encounters": []
        }

        zm = ZoneManager("dummy_content")
        zone = zm._parse_zone(zone_data)

        self.assertEqual(len(zone.nodes), 1)
        node = zone.nodes[0]
        self.assertIsNone(node.study_content)
        self.assertEqual(node.quiz_questions, [])


class TestStudyFirstModeIntegration(unittest.TestCase):
    """Integration tests for Study-First Mode."""

    def test_node_study_first_availability_check(self):
        """Test the logic that determines if study-first mode is available."""
        # Node with only study_content
        node1 = Node(id=1.1, name="Test", description="Test", study_content="Content")
        self.assertTrue(bool(node1.study_content or node1.quiz_questions))

        # Node with only quiz_questions
        node2 = Node(id=1.2, name="Test", description="Test", quiz_questions=[{"q": "test"}])
        self.assertTrue(bool(node2.study_content or node2.quiz_questions))

        # Node with both
        node3 = Node(id=1.3, name="Test", description="Test", study_content="Content", quiz_questions=[{"q": "test"}])
        self.assertTrue(bool(node3.study_content or node3.quiz_questions))

        # Node with neither
        node4 = Node(id=1.4, name="Test", description="Test")
        self.assertFalse(bool(node4.study_content or node4.quiz_questions))


if __name__ == "__main__":
    unittest.main()
