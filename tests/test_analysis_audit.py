from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common import ballot, make_trial

from frontiertrials.analysis import analyze_trial
from frontiertrials.audit import audit_trial
from frontiertrials.blinding import freeze_trial, reveal_trial
from frontiertrials.errors import BlindingError


def rated_trial(root: Path, *, raters: int = 1):
    trial = make_trial(root, tasks=2, candidates=2, raters=raters)
    freeze_trial(trial, seed="secret", reviews_per_pair=raters)
    for pairing in trial.all("pairing"):
        for rater_id in pairing["assigned_rater_ids"]:
            identifier = f"ballot-{rater_id}-{pairing['order_index'] + 1}"
            trial.add("ballot", ballot(identifier, pairing["id"], rater_id))
    reveal_trial(trial)
    return trial


class AnalysisAuditTests(unittest.TestCase):
    def test_ranking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(rated_trial(Path(directory) / "t"), bootstrap_samples=10)
            self.assertEqual(len(result["ranking"]), 2)

    def test_left_candidate_wins(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = rated_trial(Path(directory) / "t")
            result = analyze_trial(trial, bootstrap_samples=10)
            self.assertGreater(result["ranking"][0]["wins"], 0)

    def test_summary_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(rated_trial(Path(directory) / "t"), bootstrap_samples=10)
            self.assertEqual(result["summary"]["ballot_count"], 2)

    def test_category_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(rated_trial(Path(directory) / "t"), bootstrap_samples=10)
            self.assertIn("reasoning", result["category_scores"])

    def test_position_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(rated_trial(Path(directory) / "t"), bootstrap_samples=10)
            self.assertEqual(result["bias_diagnostics"]["position"]["left_win_rate"], 1)

    def test_rubric_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(rated_trial(Path(directory) / "t"), bootstrap_samples=10)
            means = [item["rubric"]["weighted_mean"] for item in result["ranking"]]
            self.assertTrue(all(value > 0 for value in means))

    def test_agreement_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(
                rated_trial(Path(directory) / "t", raters=2), bootstrap_samples=10
            )
            self.assertEqual(result["agreement"]["agreement"], 1)

    def test_analysis_refuses_frozen_trial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="secret")
            pairing = trial.all("pairing")[0]
            trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1"))
            with self.assertRaises(BlindingError):
                analyze_trial(trial, bootstrap_samples=10)

    def test_panel_and_leave_one_out_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_trial(
                rated_trial(Path(directory) / "t", raters=2), bootstrap_samples=10
            )
            self.assertEqual(len(result["panel_diagnostics"]["raters"]), 2)
            self.assertEqual(len(result["ranking_sensitivity"]["leave_one_rater_out"]), 2)

    def test_audit_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(audit_trial(rated_trial(Path(directory) / "t"))["status"], "pass")

    def test_audit_missing_matrix_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            trial.path_for("response", "response-task-1-candidate-2").unlink()
            result = audit_trial(trial)
            self.assertGreater(result["counts"]["warnings"], 0)

    def test_audit_changed_response_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            response = trial.all("response")[0]
            (trial.root / response["content_path"]).write_text("changed", encoding="utf-8")
            self.assertEqual(audit_trial(trial)["status"], "fail")

    def test_audit_side_balance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = rated_trial(Path(directory) / "t")
            counts = audit_trial(trial)["left_position_counts"]
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)


if __name__ == "__main__":
    unittest.main()
