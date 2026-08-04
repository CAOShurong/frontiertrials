"""Blind-safe adjudication queues for contested or low-confidence pairings."""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from typing import Any

from .errors import BlindingError
from .workspace import Trial


def _reasons(ballots: list[dict[str, Any]]) -> list[str]:
    reasons = []
    decisive = {item["choice"] for item in ballots if item["choice"] != "abstain"}
    if len(decisive) > 1:
        reasons.append("reviewer_disagreement")
    if any(item["confidence"] <= 2 for item in ballots):
        reasons.append("low_confidence")
    if any(item.get("flags") for item in ballots):
        reasons.append("ballot_flags")
    if any(item["choice"] == "abstain" for item in ballots):
        reasons.append("abstention")
    if any(item["choice"] == "tie" for item in ballots):
        reasons.append("tie_vote")
    return reasons


def build_adjudication_queue(
    trial: Trial,
    *,
    include_clear: bool = False,
) -> dict[str, Any]:
    """Build a deterministic queue without loading candidate identities or reveal secrets."""
    if trial.manifest()["state"] not in {"frozen", "revealed"}:
        raise BlindingError("freeze the trial before building an adjudication queue")
    pairings = trial.index("pairing")
    tasks = trial.index("task")
    raters = trial.index("rater")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ballot in trial.all("ballot"):
        grouped[ballot["pairing_id"]].append(ballot)
    if not grouped:
        raise BlindingError("at least one ballot is required for adjudication")

    items = []
    reason_counts: Counter[str] = Counter()
    for pairing_id, ballots in sorted(grouped.items()):
        pairing = pairings[pairing_id]
        reasons = _reasons(ballots)
        if not reasons and not include_clear:
            continue
        reason_counts.update(reasons)
        reviews = [
            {
                "rater_id": ballot["rater_id"],
                "rater_label": raters[ballot["rater_id"]]["label"],
                "choice": ballot["choice"],
                "confidence": ballot["confidence"],
                "left_scores": ballot["left_scores"],
                "right_scores": ballot["right_scores"],
                "rationale": ballot["rationale"],
                "flags": ballot.get("flags", []),
            }
            for ballot in sorted(ballots, key=lambda item: item["rater_id"])
        ]
        items.append(
            {
                "pairing_id": pairing_id,
                "task_id": pairing["task_id"],
                "task_title": tasks[pairing["task_id"]]["title"],
                "left_alias": pairing["left_alias"],
                "right_alias": pairing["right_alias"],
                "ballot_count": len(ballots),
                "choice_counts": dict(sorted(Counter(item["choice"] for item in ballots).items())),
                "minimum_confidence": min(item["confidence"] for item in ballots),
                "reasons": reasons,
                "suggested_action": (
                    "Review rationales and rubric scores while aliases remain blinded."
                    if reasons
                    else "No adjudication trigger; retain the original ballots."
                ),
                "reviews": reviews,
            }
        )
    return {
        "format": "frontiertrials-adjudication-v1",
        "blind_safe": True,
        "trial_state": trial.manifest()["state"],
        "summary": {
            "balloted_pairings": len(grouped),
            "queued_pairings": len(items),
            "reason_counts": dict(sorted(reason_counts.items())),
        },
        "items": items,
        "interpretation": (
            "The queue prioritizes review; it does not modify ballots, resolve disputes, "
            "or reveal candidate identities."
        ),
    }


def adjudication_csv(queue: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    fields = [
        "pairing_id",
        "task_id",
        "task_title",
        "left_alias",
        "right_alias",
        "ballot_count",
        "choice_counts",
        "minimum_confidence",
        "reasons",
        "suggested_action",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for item in queue["items"]:
        writer.writerow(
            {
                **{field: item.get(field, "") for field in fields},
                "choice_counts": "; ".join(
                    f"{key}={value}" for key, value in item["choice_counts"].items()
                ),
                "reasons": "; ".join(item["reasons"]),
            }
        )
    return output.getvalue()


def adjudication_markdown(queue: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    summary = queue["summary"]
    lines = [
        "# Blind adjudication queue",
        "",
        f"- Balloted pairings: {summary['balloted_pairings']}",
        f"- Queued pairings: {summary['queued_pairings']}",
        f"- Candidate identities included: {'no' if queue['blind_safe'] else 'yes'}",
        "",
        "| Pairing | Task | Aliases | Ballots | Minimum confidence | Triggers |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in queue["items"]:
        lines.append(
            f"| {cell(item['pairing_id'])} | {cell(item['task_title'])} | "
            f"{cell(item['left_alias'])} vs {cell(item['right_alias'])} | "
            f"{item['ballot_count']} | {item['minimum_confidence']} | "
            f"{cell(', '.join(item['reasons']) or 'none')} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            queue["interpretation"],
            "",
        ]
    )
    return "\n".join(lines)
