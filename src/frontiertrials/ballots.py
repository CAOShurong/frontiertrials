"""Ballot bundle import and locking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .workspace import Trial


def import_ballot_bundle(
    trial: Trial,
    source: str | Path,
    *,
    replace: bool = False,
) -> dict[str, Any]:
    """Import the JSON downloaded by an offline judging packet."""
    try:
        bundle = json.loads(Path(source).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid ballot bundle: {exc}") from exc
    if not isinstance(bundle, dict) or bundle.get("format") != "frontiertrials-ballots-v1":
        raise ValidationError("unsupported ballot bundle format")
    rater_id = bundle.get("rater_id")
    trial.get("rater", rater_id)
    ballots = bundle.get("ballots")
    if not isinstance(ballots, list):
        raise ValidationError("ballot bundle ballots must be a list")
    imported = []
    pairings = trial.index("pairing")
    for ballot in ballots:
        if not isinstance(ballot, dict):
            raise ValidationError("each imported ballot must be an object")
        if ballot.get("rater_id") != rater_id:
            raise ValidationError("ballot rater does not match bundle rater")
        pairing = pairings.get(ballot.get("pairing_id"))
        if not pairing:
            raise ValidationError(f"unknown pairing: {ballot.get('pairing_id')}")
        if rater_id not in pairing.get("assigned_rater_ids", []):
            raise ValidationError(f"pairing is not assigned to rater {rater_id}")
        trial.add("ballot", ballot, replace=replace)
        imported.append(ballot["id"])
    return {"rater_id": rater_id, "imported": len(imported), "ballot_ids": imported}


def ballot_completeness(trial: Trial) -> dict[str, Any]:
    """Compare assigned reviews with imported ballots."""
    expected = {
        (pairing["id"], rater_id)
        for pairing in trial.all("pairing")
        if pairing.get("state", "ready") == "ready"
        for rater_id in pairing.get("assigned_rater_ids", [])
    }
    observed = {(ballot["pairing_id"], ballot["rater_id"]) for ballot in trial.all("ballot")}
    return {
        "expected": len(expected),
        "observed": len(observed),
        "missing": [
            {"pairing_id": pairing_id, "rater_id": rater_id}
            for pairing_id, rater_id in sorted(expected - observed)
        ],
        "unexpected": [
            {"pairing_id": pairing_id, "rater_id": rater_id}
            for pairing_id, rater_id in sorted(observed - expected)
        ],
        "complete": expected == observed,
    }
