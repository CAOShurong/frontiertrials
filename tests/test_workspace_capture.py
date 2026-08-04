from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common import make_trial

from frontiertrials.capture import capture_response, response_text, verify_responses
from frontiertrials.errors import IntegrityError, ValidationError
from frontiertrials.workspace import Trial


class WorkspaceCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_create_layout(self) -> None:
        trial = Trial.create(self.root / "t", title="T", question="Q?")
        self.assertTrue((trial.root / "outputs").is_dir())

    def test_create_twice(self) -> None:
        Trial.create(self.root / "t", title="T", question="Q?")
        with self.assertRaises(ValidationError):
            Trial.create(self.root / "t", title="T", question="Q?")

    def test_manifest(self) -> None:
        trial = Trial.create(self.root / "t", title="Title", question="Q?")
        self.assertEqual(trial.manifest()["state"], "collecting")

    def test_add_get(self) -> None:
        trial = make_trial(self.root / "t")
        self.assertEqual(trial.get("task", "task-1")["title"], "Task 1")

    def test_duplicate_add(self) -> None:
        trial = make_trial(self.root / "t")
        with self.assertRaises(ValidationError):
            trial.add("rater", {"id": "rater-1", "label": "Again"})

    def test_counts(self) -> None:
        trial = make_trial(self.root / "t")
        self.assertEqual(trial.counts()["response"], 2)

    def test_response_text(self) -> None:
        trial = make_trial(self.root / "t")
        response = trial.all("response")[0]
        self.assertIn("Response", response_text(trial, response))

    def test_integrity_change(self) -> None:
        trial = make_trial(self.root / "t")
        response = trial.all("response")[0]
        (trial.root / response["content_path"]).write_text("changed", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            response_text(trial, response)

    def test_verify_changed(self) -> None:
        trial = make_trial(self.root / "t")
        response = trial.all("response")[0]
        (trial.root / response["content_path"]).write_text("changed", encoding="utf-8")
        self.assertIn("changed", {item["status"] for item in verify_responses(trial)})

    def test_capture_empty(self) -> None:
        trial = make_trial(self.root / "t")
        source = self.root / "empty.md"
        source.write_text("", encoding="utf-8")
        with self.assertRaises(ValidationError):
            capture_response(
                trial,
                response_id="empty",
                task_id="task-1",
                candidate_id="candidate-1",
                source=source,
            )

    def test_capture_after_freeze_rejected(self) -> None:
        trial = make_trial(self.root / "t")
        trial.set_state("frozen")
        source = self.root / "new.md"
        source.write_text("x", encoding="utf-8")
        with self.assertRaises(ValidationError):
            capture_response(
                trial,
                response_id="new",
                task_id="task-1",
                candidate_id="candidate-1",
                source=source,
            )

    def test_set_invalid_state(self) -> None:
        trial = make_trial(self.root / "t")
        with self.assertRaises(ValidationError):
            trial.set_state("done")


if __name__ == "__main__":
    unittest.main()
