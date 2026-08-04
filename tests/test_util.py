from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from frontiertrials.errors import ValidationError
from frontiertrials.util import (
    canonical_json,
    ensure_id,
    ensure_text,
    html_escape,
    keyed_digest,
    mean,
    sample_std,
    sha256_file,
    sha256_text,
    stable_int,
    word_count,
)


class UtilTests(unittest.TestCase):
    def test_ensure_id(self) -> None:
        self.assertEqual(ensure_id("task-one"), "task-one")

    def test_invalid_id(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_id("Task_One")

    def test_ensure_text_strips(self) -> None:
        self.assertEqual(ensure_text(" x ", "x"), "x")

    def test_blank_text(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_text("", "x")

    def test_canonical_json(self) -> None:
        self.assertEqual(canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_keyed_digest_stable(self) -> None:
        self.assertEqual(keyed_digest("s", "v"), keyed_digest("s", "v"))

    def test_keyed_digest_changes(self) -> None:
        self.assertNotEqual(keyed_digest("s", "v"), keyed_digest("s", "w"))

    def test_stable_int(self) -> None:
        self.assertIsInstance(stable_int("s", "v"), int)

    def test_sha_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x"
            path.write_text("hello", encoding="utf-8")
            self.assertEqual(sha256_file(path), sha256_text("hello"))

    def test_html_escape(self) -> None:
        self.assertEqual(html_escape("<b>&"), "&lt;b&gt;&amp;")

    def test_word_count(self) -> None:
        self.assertEqual(word_count("one two-three four's"), 3)

    def test_mean_empty(self) -> None:
        self.assertEqual(mean([]), 0)

    def test_sample_std(self) -> None:
        self.assertAlmostEqual(sample_std([1, 2, 3]), 1)


if __name__ == "__main__":
    unittest.main()
