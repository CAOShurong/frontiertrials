from __future__ import annotations

import unittest

from frontiertrials.stats import (
    bootstrap_bradley_terry,
    bradley_terry,
    cohens_kappa,
    percentile,
    wilson_interval,
)


class StatsTests(unittest.TestCase):
    def test_percentile_empty(self) -> None:
        self.assertEqual(percentile([], 0.5), 0)

    def test_percentile_median(self) -> None:
        self.assertEqual(percentile([1, 2, 3], 0.5), 2)

    def test_percentile_interpolation(self) -> None:
        self.assertEqual(percentile([0, 10], 0.25), 2.5)

    def test_wilson_bounds(self) -> None:
        low, high = wilson_interval(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_wilson_empty(self) -> None:
        self.assertEqual(wilson_interval(0, 0), (0, 0))

    def test_bt_clear_winner(self) -> None:
        scores = bradley_terry(["a", "b"], [("a", "b", 1)] * 5)
        self.assertGreater(scores["a"], scores["b"])

    def test_bt_tie_equal(self) -> None:
        scores = bradley_terry(["a", "b"], [("a", "b", 0.5)] * 4)
        self.assertAlmostEqual(scores["a"], scores["b"])

    def test_bt_empty_candidates(self) -> None:
        self.assertEqual(bradley_terry([], []), {})

    def test_bt_unplayed_equal(self) -> None:
        scores = bradley_terry(["a", "b"], [])
        self.assertEqual(scores, {"a": 1.0, "b": 1.0})

    def test_bootstrap_keys(self) -> None:
        records = [
            {
                "task_id": "t",
                "left_candidate": "a",
                "right_candidate": "b",
                "left_score": 1,
            }
        ]
        self.assertEqual(set(bootstrap_bradley_terry(["a", "b"], records, samples=5)), {"a", "b"})

    def test_kappa_perfect(self) -> None:
        result = cohens_kappa([("left", "left"), ("right", "right")], ("left", "right"))
        self.assertEqual(result["kappa"], 1)

    def test_kappa_empty(self) -> None:
        self.assertEqual(cohens_kappa([], ("left", "right"))["pairs"], 0)


if __name__ == "__main__":
    unittest.main()
