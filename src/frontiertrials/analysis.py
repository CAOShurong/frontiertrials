"""Transparent preference, rubric, bias, and agreement analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .stats import (
    bootstrap_bradley_terry,
    bradley_terry,
    cohens_kappa,
    wilson_interval,
)
from .util import mean
from .workspace import Trial


def _records(trial: Trial) -> list[dict[str, Any]]:
    responses = trial.index("response")
    pairings = trial.index("pairing")
    tasks = trial.index("task")
    records = []
    for ballot in trial.all("ballot"):
        pairing = pairings[ballot["pairing_id"]]
        left = responses[pairing["left_response_id"]]
        right = responses[pairing["right_response_id"]]
        choice = ballot["choice"]
        left_score = 1.0 if choice == "left" else 0.0 if choice == "right" else 0.5
        records.append(
            {
                "ballot": ballot,
                "pairing": pairing,
                "task_id": pairing["task_id"],
                "category": tasks[pairing["task_id"]].get("category", "other"),
                "left_candidate": left["candidate_id"],
                "right_candidate": right["candidate_id"],
                "left_words": left.get("words", 0),
                "right_words": right.get("words", 0),
                "left_score": left_score,
                "abstain": choice == "abstain",
            }
        )
    return records


def _rubric_scores(trial: Trial, records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rubrics = trial.index("rubric")
    values: dict[str, list[float]] = defaultdict(list)
    criteria_values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        ballot = record["ballot"]
        rubric = rubrics[record["pairing"]["rubric_id"]]
        weights = {item["id"]: float(item.get("weight", 1)) for item in rubric["criteria"]}
        total_weight = sum(weights.values())
        for side in ("left", "right"):
            candidate = record[f"{side}_candidate"]
            scores = ballot[f"{side}_scores"]
            weighted = sum(scores[item] * weight for item, weight in weights.items()) / total_weight
            values[candidate].append(weighted)
            for criterion, score in scores.items():
                criteria_values[candidate][criterion].append(float(score))
    return {
        candidate: {
            "weighted_mean": round(mean(scores), 3),
            "rating_count": len(scores),
            "criteria": {
                criterion: round(mean(items), 3)
                for criterion, items in sorted(criteria_values[candidate].items())
            },
        }
        for candidate, scores in sorted(values.items())
    }


def _agreement(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_pairing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_pairing[record["pairing"]["id"]].append(record)
    pairs = []
    for group in by_pairing.values():
        for index, first in enumerate(group):
            for second in group[index + 1 :]:
                pairs.append((first["ballot"]["choice"], second["ballot"]["choice"]))
    result = cohens_kappa(pairs, ("left", "right", "tie", "abstain"))
    result["overlap_pairings"] = sum(len(group) > 1 for group in by_pairing.values())
    return result


def _position_and_length(records: list[dict[str, Any]]) -> dict[str, Any]:
    decisive = [record for record in records if record["ballot"]["choice"] in {"left", "right"}]
    left_wins = sum(record["ballot"]["choice"] == "left" for record in decisive)
    low, high = wilson_interval(left_wins, len(decisive))
    longer_wins = 0
    comparable = 0
    word_deltas = []
    for record in decisive:
        if record["left_words"] == record["right_words"]:
            continue
        comparable += 1
        winner_words = (
            record["left_words"] if record["ballot"]["choice"] == "left" else record["right_words"]
        )
        loser_words = (
            record["right_words"] if record["ballot"]["choice"] == "left" else record["left_words"]
        )
        longer_wins += winner_words > loser_words
        word_deltas.append(winner_words - loser_words)
    return {
        "position": {
            "decisive_ballots": len(decisive),
            "left_wins": left_wins,
            "left_win_rate": round(left_wins / len(decisive), 4) if decisive else 0.0,
            "wilson_95": [round(low, 4), round(high, 4)],
            "interpretation": "A wide interval around 0.5 is inconclusive, not proof of no bias.",
        },
        "verbosity": {
            "comparable_ballots": comparable,
            "longer_response_wins": longer_wins,
            "longer_win_rate": round(longer_wins / comparable, 4) if comparable else 0.0,
            "mean_winner_minus_loser_words": round(mean(word_deltas), 2),
            "interpretation": "Association does not show that length caused the preference.",
        },
    }


def analyze_trial(trial: Trial, *, bootstrap_samples: int = 400) -> dict[str, Any]:
    """Analyze ballots while retaining raw counts and methodological warnings."""
    candidates = trial.index("candidate")
    records = _records(trial)
    ranked_records = [record for record in records if not record["abstain"]]
    comparisons = [
        (record["left_candidate"], record["right_candidate"], record["left_score"])
        for record in ranked_records
    ]
    strengths = bradley_terry(sorted(candidates), comparisons)
    intervals = bootstrap_bradley_terry(
        sorted(candidates), ranked_records, samples=bootstrap_samples
    )
    counts = {
        candidate_id: Counter({"wins": 0, "losses": 0, "ties": 0, "appearances": 0})
        for candidate_id in candidates
    }
    head_to_head: dict[str, Counter[str]] = defaultdict(Counter)
    category_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in ranked_records:
        left = record["left_candidate"]
        right = record["right_candidate"]
        score = record["left_score"]
        counts[left]["appearances"] += 1
        counts[right]["appearances"] += 1
        category_scores[record["category"]][left].append(score)
        category_scores[record["category"]][right].append(1 - score)
        if score == 1:
            counts[left]["wins"] += 1
            counts[right]["losses"] += 1
            head_to_head[left][right] += 1
        elif score == 0:
            counts[right]["wins"] += 1
            counts[left]["losses"] += 1
            head_to_head[right][left] += 1
        else:
            counts[left]["ties"] += 1
            counts[right]["ties"] += 1
    rubric_scores = _rubric_scores(trial, records)
    ranking = []
    for candidate_id, candidate in candidates.items():
        lower, upper = intervals.get(candidate_id, (0.0, 0.0))
        appearances = counts[candidate_id]["appearances"]
        preference_points = counts[candidate_id]["wins"] + 0.5 * counts[candidate_id]["ties"]
        ranking.append(
            {
                "candidate_id": candidate_id,
                "label": candidate["label"],
                "provider": candidate["provider"],
                "model": candidate["model"],
                "bt_strength": round(strengths.get(candidate_id, 1.0), 4),
                "bt_95": [round(lower, 4), round(upper, 4)],
                "wins": counts[candidate_id]["wins"],
                "losses": counts[candidate_id]["losses"],
                "ties": counts[candidate_id]["ties"],
                "appearances": appearances,
                "preference_rate": round(preference_points / appearances, 4)
                if appearances
                else 0.0,
                "rubric": rubric_scores.get(
                    candidate_id, {"weighted_mean": 0.0, "rating_count": 0, "criteria": {}}
                ),
            }
        )
    ranking.sort(key=lambda item: (-item["bt_strength"], item["candidate_id"]))
    return {
        "ranking": ranking,
        "summary": {
            "candidate_count": len(candidates),
            "task_count": len(trial.all("task")),
            "pairing_count": len(trial.all("pairing")),
            "ballot_count": len(records),
            "decisive_or_tied_count": len(ranked_records),
            "abstention_count": len(records) - len(ranked_records),
            "bootstrap_samples": bootstrap_samples,
        },
        "category_scores": {
            category: {
                candidate: round(mean(values), 4)
                for candidate, values in sorted(by_candidate.items())
            }
            for category, by_candidate in sorted(category_scores.items())
        },
        "head_to_head_wins": {
            candidate: dict(sorted(opponents.items()))
            for candidate, opponents in sorted(head_to_head.items())
        },
        "agreement": _agreement(records),
        "bias_diagnostics": _position_and_length(records),
        "warnings": [
            "The ranking describes this prompt set, capture protocol, and reviewer panel.",
            "Overlapping confidence intervals should not be read as a stable total order.",
            "Web products can change model routing, tools, system prompts, and interfaces without notice.",
            "Human preferences do not establish factual correctness or safety.",
        ],
    }
