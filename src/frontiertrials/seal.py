"""Content-addressed trial evidence seals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import KINDS
from .store import write_json
from .util import canonical_json, sha256_file, sha256_text, utc_now
from .workspace import Trial


def build_seal(trial: Trial) -> dict[str, Any]:
    files = [trial.manifest_path]
    for kind in KINDS:
        files.extend(sorted(trial.path_for(kind, "placeholder").parent.glob("*.json")))
    files.extend(sorted((trial.root / "outputs").glob("*.md")))
    entries = [
        {
            "path": path.relative_to(trial.root).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(set(files))
    ]
    return {
        "algorithm": "sha256",
        "root": sha256_text(canonical_json(entries)),
        "file_count": len(entries),
        "files": entries,
        "exclusions": ["secrets/", "packets/", "reports/", "frontiertrials-seal.json"],
    }


def write_seal(
    trial: Trial,
    output: str | Path | None = None,
    *,
    created_at: str | None = None,
) -> Path:
    destination = Path(output) if output else trial.root / "frontiertrials-seal.json"
    seal = build_seal(trial)
    seal["created_at"] = created_at or utc_now()
    write_json(destination, seal)
    return destination


def verify_seal(trial: Trial, source: str | Path | None = None) -> dict[str, Any]:
    path = Path(source) if source else trial.root / "frontiertrials-seal.json"
    expected = json.loads(path.read_text(encoding="utf-8"))
    observed = build_seal(trial)
    return {
        "status": "verified" if expected.get("root") == observed["root"] else "changed",
        "expected_root": expected.get("root"),
        "observed_root": observed["root"],
        "expected_file_count": expected.get("file_count"),
        "observed_file_count": observed["file_count"],
    }
