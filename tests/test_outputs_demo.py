from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common import ballot, make_trial

from frontiertrials.blinding import freeze_trial, reveal_trial
from frontiertrials.demo import create_demo
from frontiertrials.exports import protocol_markdown, ranking_csv
from frontiertrials.packet import build_packet
from frontiertrials.report import build_report
from frontiertrials.seal import build_seal, verify_seal, write_seal


def revealed_trial(root: Path):
    trial = make_trial(root)
    freeze_trial(trial, seed="s")
    pairing = trial.all("pairing")[0]
    trial.add("ballot", ballot("ballot-one", pairing["id"], "rater-1"))
    reveal_trial(trial)
    return trial


class OutputDemoTests(unittest.TestCase):
    def test_packet_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="s")
            text = build_packet(trial, "rater-1", Path(directory) / "packet.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("Download ballots", text)
            self.assertNotIn("Candidate 1", text)

    def test_packet_requires_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t", raters=2)
            freeze_trial(trial, seed="s", reviews_per_pair=1)
            assigned = trial.all("pairing")[0]["assigned_rater_ids"][0]
            other = "rater-2" if assigned == "rater-1" else "rater-1"
            from frontiertrials.errors import BlindingError

            with self.assertRaises(BlindingError):
                build_packet(trial, other, Path(directory) / "packet.html")

    def test_report_requires_reveal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = make_trial(Path(directory) / "t")
            freeze_trial(trial, seed="s")
            from frontiertrials.errors import BlindingError

            with self.assertRaises(BlindingError):
                build_report(trial, Path(directory) / "report.html")

    def test_report_contains_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = build_report(
                revealed_trial(Path(directory) / "t"),
                Path(directory) / "report.html",
                bootstrap_samples=10,
            ).read_text(encoding="utf-8")
            self.assertIn("does not establish factual correctness", text)

    def test_ranking_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = ranking_csv(revealed_trial(Path(directory) / "t"), bootstrap_samples=10)
            self.assertTrue(text.startswith("rank,candidate_id"))

    def test_protocol_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = protocol_markdown(revealed_trial(Path(directory) / "t"))
            self.assertIn("## Interpretation boundary", text)

    def test_seal_verify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = revealed_trial(Path(directory) / "t")
            write_seal(trial)
            self.assertEqual(verify_seal(trial)["status"], "verified")

    def test_seal_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = revealed_trial(Path(directory) / "t")
            write_seal(trial)
            response = trial.all("response")[0]
            (trial.root / response["content_path"]).write_text("changed", encoding="utf-8")
            self.assertEqual(verify_seal(trial)["status"], "changed")

    def test_seal_excludes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = revealed_trial(Path(directory) / "t")
            first = build_seal(trial)["root"]
            (trial.root / "reports" / "x.txt").write_text("x", encoding="utf-8")
            self.assertEqual(first, build_seal(trial)["root"])

    def test_demo_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = create_demo(Path(directory) / "demo")
            self.assertEqual(trial.counts()["ballot"], 96)
            self.assertEqual(trial.counts()["pairing"], 48)

    def test_demo_audit_and_seal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial = create_demo(Path(directory) / "demo")
            from frontiertrials.audit import audit_trial

            self.assertEqual(audit_trial(trial)["status"], "pass")
            self.assertEqual(verify_seal(trial)["status"], "verified")

    def test_demo_refuses_nonempty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            root.mkdir()
            (root / "keep").write_text("x", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                create_demo(root)


if __name__ == "__main__":
    unittest.main()
