"""Structural, integrity, assignment, and blinding diagnostics."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .ballots import ballot_completeness
from .capture import response_text
from .constants import KINDS, LEAKAGE_TERMS
from .errors import FrontierTrialsError
from .workspace import Trial


def _issue(level: str, code: str, message: str, artifact: str = "") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "artifact": artifact}


def audit_trial(trial: Trial) -> dict[str, Any]:
    """Run checks that can be established without calling a model or opening the web."""
    issues: list[dict[str, str]] = []
    records: dict[str, dict[str, dict[str, Any]]] = {}
    try:
        manifest = trial.manifest()
    except FrontierTrialsError as exc:
        manifest = {"state": "unknown"}
        issues.append(_issue("error", "manifest.invalid", str(exc), "frontiertrials.json"))
    for kind in KINDS:
        try:
            records[kind] = trial.index(kind)
        except FrontierTrialsError as exc:
            records[kind] = {}
            issues.append(_issue("error", f"{kind}.invalid", str(exc), kind))

    tasks = records["task"]
    candidates = records["candidate"]
    responses = records["response"]
    rubrics = records["rubric"]
    pairings = records["pairing"]
    raters = records["rater"]

    matrix: Counter[tuple[str, str]] = Counter()
    for response in responses.values():
        if response["task_id"] not in tasks:
            issues.append(
                _issue(
                    "error",
                    "response.task_missing",
                    f"task {response['task_id']} does not exist",
                    response["id"],
                )
            )
        if response["candidate_id"] not in candidates:
            issues.append(
                _issue(
                    "error",
                    "response.candidate_missing",
                    f"candidate {response['candidate_id']} does not exist",
                    response["id"],
                )
            )
        matrix[(response["task_id"], response["candidate_id"])] += 1
        try:
            content = response_text(trial, response)
        except FrontierTrialsError as exc:
            issues.append(_issue("error", "response.integrity", str(exc), response["id"]))
            continue
        lowered = content.lower()
        matches = sorted(term for term in LEAKAGE_TERMS if term in lowered)
        if matches:
            issues.append(
                _issue(
                    "warning",
                    "response.identity_leak",
                    f"possible model/provider identity terms: {', '.join(matches)}",
                    response["id"],
                )
            )
    for key, count in sorted(matrix.items()):
        if count > 1:
            issues.append(
                _issue(
                    "error",
                    "response.duplicate",
                    f"{count} responses for task/candidate {key[0]}/{key[1]}",
                    f"{key[0]}/{key[1]}",
                )
            )
    if tasks and candidates:
        for task_id in sorted(tasks):
            for candidate_id in sorted(candidates):
                if not matrix[(task_id, candidate_id)]:
                    issues.append(
                        _issue(
                            "warning",
                            "matrix.missing",
                            f"no response for {task_id}/{candidate_id}",
                            task_id,
                        )
                    )

    left_counts: Counter[str] = Counter()
    for pairing in pairings.values():
        if pairing["task_id"] not in tasks:
            issues.append(
                _issue(
                    "error",
                    "pairing.task_missing",
                    f"task {pairing['task_id']} does not exist",
                    pairing["id"],
                )
            )
        if pairing["rubric_id"] not in rubrics:
            issues.append(
                _issue(
                    "error",
                    "pairing.rubric_missing",
                    f"rubric {pairing['rubric_id']} does not exist",
                    pairing["id"],
                )
            )
        for side in ("left", "right"):
            response_id = pairing[f"{side}_response_id"]
            if response_id not in responses:
                issues.append(
                    _issue(
                        "error",
                        "pairing.response_missing",
                        f"response {response_id} does not exist",
                        pairing["id"],
                    )
                )
        left_response = responses.get(pairing["left_response_id"])
        if left_response:
            left_counts[left_response["candidate_id"]] += 1
        for rater_id in pairing.get("assigned_rater_ids", []):
            if rater_id not in raters:
                issues.append(
                    _issue(
                        "error",
                        "pairing.rater_missing",
                        f"rater {rater_id} does not exist",
                        pairing["id"],
                    )
                )
    if left_counts and max(left_counts.values()) - min(left_counts.values()) > 1:
        issues.append(
            _issue(
                "warning",
                "pairing.order_imbalance",
                f"left-position counts differ by more than one: {dict(sorted(left_counts.items()))}",
                "pairings",
            )
        )

    seen_ballots: Counter[tuple[str, str]] = Counter()
    for ballot in records["ballot"].values():
        pairing = pairings.get(ballot["pairing_id"])
        if not pairing:
            issues.append(
                _issue(
                    "error",
                    "ballot.pairing_missing",
                    f"pairing {ballot['pairing_id']} does not exist",
                    ballot["id"],
                )
            )
            continue
        if ballot["rater_id"] not in raters:
            issues.append(
                _issue(
                    "error",
                    "ballot.rater_missing",
                    f"rater {ballot['rater_id']} does not exist",
                    ballot["id"],
                )
            )
        if ballot["rater_id"] not in pairing.get("assigned_rater_ids", []):
            issues.append(
                _issue(
                    "error",
                    "ballot.unassigned",
                    "rater was not assigned this pairing",
                    ballot["id"],
                )
            )
        seen_ballots[(ballot["pairing_id"], ballot["rater_id"])] += 1
        rubric = rubrics.get(pairing["rubric_id"])
        if rubric:
            expected = {item["id"] for item in rubric["criteria"]}
            for side in ("left_scores", "right_scores"):
                if set(ballot[side]) != expected:
                    issues.append(
                        _issue(
                            "error",
                            "ballot.criteria_mismatch",
                            f"{side} does not match rubric criteria",
                            ballot["id"],
                        )
                    )
    for key, count in sorted(seen_ballots.items()):
        if count > 1:
            issues.append(
                _issue(
                    "error",
                    "ballot.duplicate",
                    f"{count} ballots for pairing/rater {key[0]}/{key[1]}",
                    key[0],
                )
            )

    completeness = (
        ballot_completeness(trial)
        if pairings
        else {
            "expected": 0,
            "observed": len(records["ballot"]),
            "missing": [],
            "unexpected": [],
            "complete": not records["ballot"],
        }
    )
    if manifest.get("state") == "revealed" and not completeness["complete"]:
        issues.append(
            _issue(
                "warning",
                "reveal.incomplete_ballots",
                f"trial was revealed with {len(completeness['missing'])} assigned ballots missing",
                "frontiertrials.json",
            )
        )
    counts = Counter(item["level"] for item in issues)
    issues.sort(
        key=lambda item: (
            {"error": 0, "warning": 1}.get(item["level"], 2),
            item["code"],
            item["artifact"],
        )
    )
    return {
        "status": "pass" if not counts["error"] else "fail",
        "trial_state": manifest.get("state"),
        "counts": {
            "errors": counts["error"],
            "warnings": counts["warning"],
            "artifacts": sum(len(items) for items in records.values()),
            **trial.counts(),
        },
        "ballot_completeness": completeness,
        "left_position_counts": dict(sorted(left_counts.items())),
        "issues": issues,
        "checks": [
            "artifact validation",
            "response matrix and SHA-256 integrity",
            "identity leakage terms",
            "pairing references and side balance",
            "rater assignments and duplicate ballots",
            "rubric score coverage",
            "reveal timing",
        ],
    }
