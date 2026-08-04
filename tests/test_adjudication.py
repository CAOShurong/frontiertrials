from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from common import ballot, make_trial

from frontiertrials.adjudication import (
    adjudication_csv,
    adjudication_markdown,
    build_adjudication_queue,
)
from frontiertrials.blinding import freeze_trial
from frontiertrials.errors import BlindingError


class AdjudicationTests(unittest.TestCase):
    def test_requires_frozen_trial(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(BlindingError):
            build_adjudication_queue(make_trial(Path(directory) / "t"))

    def test_requires_ballot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="secret")
            with self.assertRaises(BlindingError):
                build_adjudication_queue(trial)

    def test_flags_disagreement_without_candidate_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t", raters=2)
            freeze_trial(trial, seed="secret", reviews_per_pair=2)
            pairing = trial.all("pairing")[0]
            trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1", "left"))
            trial.add("ballot", ballot("ballot-two", pairing["id"], "rater-2", "right"))
            queue = build_adjudication_queue(trial)
            self.assertEqual(queue["summary"]["queued_pairings"], 1)
            self.assertIn("reviewer_disagreement", queue["items"][0]["reasons"])
            serialized = json.dumps(queue)
            self.assertNotIn("candidate-1", serialized)
            self.assertNotIn("Model 1", serialized)

    def test_low_confidence_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="secret")
            pairing = trial.all("pairing")[0]
            item = ballot("ballot-one", pairing["id"], "rater-1")
            item["confidence"] = 2
            trial.add("ballot", item)
            queue = build_adjudication_queue(trial)
            self.assertIn("low_confidence", queue["items"][0]["reasons"])
            self.assertIn("pairing_id", adjudication_csv(queue))
            self.assertIn("# Blind adjudication queue", adjudication_markdown(queue))

    def test_clear_pairing_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="secret")
            pairing = trial.all("pairing")[0]
            item = ballot("ballot-one", pairing["id"], "rater-1")
            item["flags"] = []
            item["confidence"] = 4
            trial.add("ballot", item)
            self.assertEqual(build_adjudication_queue(trial)["items"], [])
            self.assertEqual(len(build_adjudication_queue(trial, include_clear=True)["items"]), 1)


if __name__ == "__main__":
    unittest.main()
