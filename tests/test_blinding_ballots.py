from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from common import ballot, make_trial

from frontiertrials.ballots import ballot_completeness, import_ballot_bundle
from frontiertrials.blinding import freeze_trial, read_reveal, reveal_trial
from frontiertrials.errors import BlindingError, ValidationError


class BlindingBallotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_freeze_pair_count(self) -> None:
        trial = make_trial(self.root / "t", tasks=2, candidates=3)
        result = freeze_trial(trial, seed="secret")
        self.assertEqual(result["pairing_count"], 6)

    def test_freeze_state(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="secret")
        self.assertEqual(trial.manifest()["state"], "frozen")

    def test_aliases_hide_candidate_ids(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="secret")
        aliases = read_reveal(trial)["candidate_aliases"].values()
        self.assertNotIn("candidate-1", aliases)

    def test_freeze_deterministic_aliases(self) -> None:
        first = make_trial(self.root / "a")
        second = make_trial(self.root / "b")
        freeze_trial(first, seed="secret")
        freeze_trial(second, seed="secret")
        self.assertEqual(
            read_reveal(first)["candidate_aliases"],
            read_reveal(second)["candidate_aliases"],
        )

    def test_empty_seed(self) -> None:
        trial = make_trial(self.root / "t")
        with self.assertRaises(ValidationError):
            freeze_trial(trial, seed="")

    def test_reviews_per_pair_limit(self) -> None:
        trial = make_trial(self.root / "t", raters=1)
        with self.assertRaises(BlindingError):
            freeze_trial(trial, seed="s", reviews_per_pair=2)

    def test_incomplete_matrix(self) -> None:
        trial = make_trial(self.root / "t")
        trial.path_for("response", "response-task-1-candidate-2").unlink()
        with self.assertRaises(BlindingError):
            freeze_trial(trial, seed="s")

    def test_order_balance(self) -> None:
        trial = make_trial(self.root / "t", tasks=4, candidates=4)
        result = freeze_trial(trial, seed="s")
        counts = list(result["left_counts"].values())
        self.assertLessEqual(max(counts) - min(counts), 1)

    def test_reveal_without_ballots(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="s")
        with self.assertRaises(BlindingError):
            reveal_trial(trial)

    def test_completeness_missing(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="s")
        self.assertFalse(ballot_completeness(trial)["complete"])

    def test_import_bundle(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="s")
        pairing = trial.all("pairing")[0]
        item = ballot("ballot-one", pairing["id"], "rater-1")
        source = self.root / "ballots.json"
        source.write_text(
            json.dumps(
                {
                    "format": "frontiertrials-ballots-v1",
                    "rater_id": "rater-1",
                    "ballots": [item],
                }
            ),
            encoding="utf-8",
        )
        result = import_ballot_bundle(trial, source)
        self.assertEqual(result["imported"], 1)
        self.assertTrue(ballot_completeness(trial)["complete"])

    def test_import_bad_format(self) -> None:
        trial = make_trial(self.root / "t")
        source = self.root / "bad.json"
        source.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValidationError):
            import_ballot_bundle(trial, source)

    def test_reveal_refuses_incomplete_matrix(self) -> None:
        trial = make_trial(self.root / "t", tasks=2)
        freeze_trial(trial, seed="s")
        pairing = trial.all("pairing")[0]
        trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1"))
        with self.assertRaises(BlindingError):
            reveal_trial(trial)

    def test_reveal_allows_explicit_incomplete_override(self) -> None:
        trial = make_trial(self.root / "t", tasks=2)
        freeze_trial(trial, seed="s")
        pairing = trial.all("pairing")[0]
        trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1"))
        reveal = reveal_trial(trial, allow_incomplete=True)
        self.assertEqual(len(reveal), 2)
        self.assertEqual(trial.manifest()["state"], "revealed")

    def test_reveal_complete_matrix(self) -> None:
        trial = make_trial(self.root / "t")
        freeze_trial(trial, seed="s")
        pairing = trial.all("pairing")[0]
        trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1"))
        reveal = reveal_trial(trial)
        self.assertEqual(len(reveal), 2)


if __name__ == "__main__":
    unittest.main()
