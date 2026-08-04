from __future__ import annotations

import unittest

from frontiertrials.errors import ValidationError
from frontiertrials.models import validate


class ModelTests(unittest.TestCase):
    def test_task_valid(self) -> None:
        item = {"id": "t", "title": "T", "prompt": "P"}
        self.assertIs(validate("task", item), item)

    def test_task_bad_category(self) -> None:
        with self.assertRaises(ValidationError):
            validate("task", {"id": "t", "title": "T", "prompt": "P", "category": "magic"})

    def test_candidate_requires_provider(self) -> None:
        with self.assertRaises(ValidationError):
            validate("candidate", {"id": "c", "label": "C", "model": "M"})

    def test_candidate_surface(self) -> None:
        with self.assertRaises(ValidationError):
            validate(
                "candidate",
                {"id": "c", "label": "C", "provider": "P", "model": "M", "surface": "api"},
            )

    def test_response_negative_latency(self) -> None:
        with self.assertRaises(ValidationError):
            validate(
                "response",
                {
                    "id": "r",
                    "task_id": "t",
                    "candidate_id": "c",
                    "content_path": "outputs/r.md",
                    "sha256": "sha256:x",
                    "captured_at": "now",
                    "latency_seconds": -1,
                },
            )

    def test_rubric_requires_criteria(self) -> None:
        with self.assertRaises(ValidationError):
            validate("rubric", {"id": "r", "title": "R", "criteria": []})

    def test_rubric_duplicate_criterion(self) -> None:
        criterion = {"id": "c", "label": "C", "question": "Q"}
        with self.assertRaises(ValidationError):
            validate("rubric", {"id": "r", "title": "R", "criteria": [criterion, criterion]})

    def test_pairing_same_response(self) -> None:
        with self.assertRaises(ValidationError):
            validate(
                "pairing",
                {
                    "id": "p",
                    "task_id": "t",
                    "rubric_id": "r",
                    "left_response_id": "x",
                    "right_response_id": "x",
                    "left_alias": "A",
                    "right_alias": "B",
                },
            )

    def test_ballot_bad_choice(self) -> None:
        with self.assertRaises(ValidationError):
            validate(
                "ballot",
                {
                    "id": "b",
                    "pairing_id": "p",
                    "rater_id": "r",
                    "choice": "both",
                    "confidence": 4,
                    "left_scores": {},
                    "right_scores": {},
                    "rationale": "x",
                },
            )

    def test_ballot_bad_score(self) -> None:
        with self.assertRaises(ValidationError):
            validate(
                "ballot",
                {
                    "id": "b",
                    "pairing_id": "p",
                    "rater_id": "r",
                    "choice": "tie",
                    "confidence": 4,
                    "left_scores": {"c": 6},
                    "right_scores": {"c": 2},
                    "rationale": "x",
                },
            )

    def test_rater_valid(self) -> None:
        item = {"id": "r", "label": "R", "expertise": ["EE"]}
        self.assertIs(validate("rater", item), item)

    def test_unknown_kind(self) -> None:
        with self.assertRaises(ValidationError):
            validate("ghost", {})


if __name__ == "__main__":
    unittest.main()
