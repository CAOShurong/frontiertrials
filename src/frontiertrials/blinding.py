"""Deterministic aliasing, order balancing, and trial freezing."""

from __future__ import annotations

import itertools
from collections import Counter
from typing import Any

from .ballots import ballot_completeness
from .capture import verify_responses
from .constants import ALIAS_WORDS
from .errors import BlindingError, ValidationError
from .store import write_json
from .util import keyed_digest, stable_int, utc_now
from .workspace import Trial


def _aliases(candidate_ids: list[str], seed: str) -> dict[str, str]:
    ordered = sorted(candidate_ids, key=lambda item: keyed_digest(seed, f"alias:{item}"))
    if len(ordered) > len(ALIAS_WORDS):
        raise BlindingError(f"at most {len(ALIAS_WORDS)} candidates are supported in v1")
    return {candidate_id: ALIAS_WORDS[index] for index, candidate_id in enumerate(ordered)}


def _response_matrix(trial: Trial) -> dict[tuple[str, str], dict[str, Any]]:
    matrix: dict[tuple[str, str], dict[str, Any]] = {}
    for response in trial.all("response"):
        if response.get("state") != "captured":
            continue
        key = (response["task_id"], response["candidate_id"])
        if key in matrix:
            raise BlindingError(f"multiple captured responses for task/candidate: {key}")
        matrix[key] = response
    return matrix


def freeze_trial(
    trial: Trial,
    *,
    seed: str,
    reviews_per_pair: int = 1,
    replace: bool = False,
) -> dict[str, Any]:
    """Freeze a complete response matrix into balanced blind pairings."""
    manifest = trial.manifest()
    if manifest["state"] != "collecting" and not replace:
        raise ValidationError("trial must be collecting before it can be frozen")
    if not seed:
        raise ValidationError("a non-empty secret seed is required")
    tasks = trial.all("task")
    candidates = trial.all("candidate")
    raters = trial.all("rater")
    rubrics = trial.all("rubric")
    if len(candidates) < 2:
        raise BlindingError("at least two candidates are required")
    if not tasks or not rubrics:
        raise BlindingError("at least one task and rubric are required")
    if not raters:
        raise BlindingError("at least one rater is required")
    if not 1 <= reviews_per_pair <= len(raters):
        raise BlindingError("reviews_per_pair must be between one and the rater count")
    failures = [item for item in verify_responses(trial) if item["status"] != "verified"]
    if failures:
        raise BlindingError("response integrity must pass before freezing")
    matrix = _response_matrix(trial)
    missing = [
        (task["id"], candidate["id"])
        for task in tasks
        for candidate in candidates
        if (task["id"], candidate["id"]) not in matrix
    ]
    if missing:
        preview = ", ".join(f"{task}/{candidate}" for task, candidate in missing[:8])
        raise BlindingError(f"incomplete response matrix: {preview}")

    alias_map = _aliases([item["id"] for item in candidates], seed)
    rubric_ids = {item["id"] for item in rubrics}
    default_rubric = manifest.get("default_rubric_id", rubrics[0]["id"])
    if default_rubric not in rubric_ids:
        raise BlindingError(f"default rubric does not exist: {default_rubric}")
    left_counts = {item["id"]: 0 for item in candidates}
    pair_meetings: Counter[tuple[str, str]] = Counter()
    pairings: list[dict[str, Any]] = []
    rater_ids = sorted(item["id"] for item in raters)
    serial = 0
    for task in tasks:
        rubric_id = task.get("rubric_id", default_rubric)
        if rubric_id not in rubric_ids:
            raise BlindingError(f"task {task['id']} references missing rubric {rubric_id}")
        candidate_pairs = list(itertools.combinations(sorted(item["id"] for item in candidates), 2))
        candidate_pairs.sort(
            key=lambda pair: keyed_digest(seed, f"pair:{task['id']}:{pair[0]}:{pair[1]}")
        )
        for first, second in candidate_pairs:
            pair_key = tuple(sorted((first, second)))
            occurrence = pair_meetings[pair_key]
            first_starts_left = stable_int(seed, f"side:{first}:{second}") % 2 == 1
            first_is_left = first_starts_left if occurrence % 2 == 0 else not first_starts_left
            pair_meetings[pair_key] += 1
            if first_is_left:
                left_candidate, right_candidate = first, second
            else:
                left_candidate, right_candidate = second, first
            left_counts[left_candidate] += 1
            pairing_id = f"pair-{task['id']}-{serial + 1:03d}"
            allocation_start = stable_int(seed, f"rater:{pairing_id}") % len(rater_ids)
            assigned = [
                rater_ids[(allocation_start + offset) % len(rater_ids)]
                for offset in range(reviews_per_pair)
            ]
            pairing = {
                "id": pairing_id,
                "task_id": task["id"],
                "rubric_id": rubric_id,
                "left_response_id": matrix[(task["id"], left_candidate)]["id"],
                "right_response_id": matrix[(task["id"], right_candidate)]["id"],
                "left_alias": alias_map[left_candidate],
                "right_alias": alias_map[right_candidate],
                "assigned_rater_ids": assigned,
                "state": "ready",
                "order_index": serial,
            }
            trial.add("pairing", pairing, replace=replace)
            pairings.append(pairing)
            serial += 1

    reveal = {
        "created_at": utc_now(),
        "seed_fingerprint": keyed_digest(seed, "frontiertrials")[:16],
        "candidate_aliases": alias_map,
        "pairing_count": len(pairings),
        "warning": "Keep this file away from raters until ballots are locked.",
    }
    write_json(trial.root / "secrets" / "reveal.json", reveal)
    manifest["state"] = "frozen"
    manifest["frozen_at"] = utc_now()
    manifest["seed_fingerprint"] = reveal["seed_fingerprint"]
    manifest["reviews_per_pair"] = reviews_per_pair
    write_json(trial.manifest_path, manifest)
    return {
        "pairing_count": len(pairings),
        "candidate_count": len(candidates),
        "task_count": len(tasks),
        "rater_count": len(raters),
        "reviews_per_pair": reviews_per_pair,
        "left_counts": dict(sorted(left_counts.items())),
        "seed_fingerprint": reveal["seed_fingerprint"],
    }


def reveal_trial(trial: Trial, *, allow_incomplete: bool = False) -> dict[str, Any]:
    """Reveal candidate aliases only after the assigned ballot matrix is complete."""
    if trial.manifest()["state"] not in {"frozen", "revealed"}:
        raise BlindingError("only a frozen trial can be revealed")
    completeness = ballot_completeness(trial)
    if not completeness["complete"] and not allow_incomplete:
        raise BlindingError(
            "refusing to reveal an incomplete ballot matrix; "
            f"{len(completeness['missing'])} assigned ballots are missing"
        )
    reveal = read_reveal(trial)
    trial.set_state("revealed")
    candidates = trial.index("candidate")
    return {
        alias: {
            "candidate_id": candidate_id,
            "label": candidates[candidate_id]["label"],
            "provider": candidates[candidate_id]["provider"],
            "model": candidates[candidate_id]["model"],
        }
        for candidate_id, alias in sorted(reveal["candidate_aliases"].items())
    }


def read_reveal(trial: Trial) -> dict[str, Any]:
    path = trial.root / "secrets" / "reveal.json"
    if not path.exists():
        raise BlindingError("reveal map is missing")
    from .store import read_json

    return read_json(path)
