"""Small statistical routines with no numerical dependency."""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any

from .util import mean


def percentile(values: list[float], probability: float) -> float:
    """Linearly interpolated percentile for a sorted numeric sample."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def wilson_interval(successes: float, trials: float, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval, accepting half-successes for ties."""
    if trials <= 0:
        return (0.0, 0.0)
    proportion = successes / trials
    denominator = 1 + z * z / trials
    center = (proportion + z * z / (2 * trials)) / denominator
    spread = (
        z
        * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials))
        / denominator
    )
    return (max(0.0, center - spread), min(1.0, center + spread))


def bradley_terry(
    candidate_ids: list[str],
    comparisons: list[tuple[str, str, float]],
    *,
    iterations: int = 300,
    tolerance: float = 1e-10,
) -> dict[str, float]:
    """Fit Bradley-Terry strengths with the MM update and a weak symmetric prior.

    Each comparison is ``(left_id, right_id, left_score)`` where the score is
    1 for a left win, 0 for a right win, and 0.5 for a tie.
    """
    if not candidate_ids:
        return {}
    strengths = {identifier: 1.0 for identifier in candidate_ids}
    wins = Counter({identifier: 0.5 for identifier in candidate_ids})
    totals: Counter[tuple[str, str]] = Counter()
    for left, right, score in comparisons:
        wins[left] += score
        wins[right] += 1 - score
        pair = tuple(sorted((left, right)))
        totals[pair] += 1
    for _ in range(iterations):
        updated: dict[str, float] = {}
        for identifier in candidate_ids:
            denominator = 0.0
            for opponent in candidate_ids:
                if opponent == identifier:
                    continue
                games = totals[tuple(sorted((identifier, opponent)))]
                if games:
                    denominator += games / (strengths[identifier] + strengths[opponent])
            updated[identifier] = wins[identifier] / denominator if denominator else 1.0
        scale = mean(list(updated.values())) or 1.0
        updated = {identifier: value / scale for identifier, value in updated.items()}
        delta = max(abs(updated[item] - strengths[item]) for item in candidate_ids)
        strengths = updated
        if delta < tolerance:
            break
    return strengths


def bootstrap_bradley_terry(
    candidate_ids: list[str],
    records: list[dict[str, Any]],
    *,
    samples: int = 400,
    seed: int = 1729,
) -> dict[str, tuple[float, float]]:
    """Task-clustered bootstrap confidence intervals for BT strengths."""
    task_ids = sorted({record["task_id"] for record in records})
    if not task_ids or samples <= 0:
        return {identifier: (0.0, 0.0) for identifier in candidate_ids}
    by_task = {
        task_id: [record for record in records if record["task_id"] == task_id]
        for task_id in task_ids
    }
    generator = random.Random(seed)
    draws = {identifier: [] for identifier in candidate_ids}
    for _ in range(samples):
        sampled = [generator.choice(task_ids) for _ in task_ids]
        comparisons = []
        for task_id in sampled:
            for record in by_task[task_id]:
                comparisons.append(
                    (record["left_candidate"], record["right_candidate"], record["left_score"])
                )
        fitted = bradley_terry(candidate_ids, comparisons)
        for identifier in candidate_ids:
            draws[identifier].append(fitted.get(identifier, 1.0))
    return {
        identifier: (
            percentile(values, 0.025),
            percentile(values, 0.975),
        )
        for identifier, values in draws.items()
    }


def cohens_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> dict[str, float]:
    """Agreement and Cohen's kappa across paired categorical judgments."""
    if not pairs:
        return {"agreement": 0.0, "kappa": 0.0, "pairs": 0}
    agreement = sum(left == right for left, right in pairs) / len(pairs)
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / len(pairs)) * (right_counts[label] / len(pairs)) for label in labels
    )
    kappa = (agreement - expected) / (1 - expected) if expected < 1 else 1.0
    return {
        "agreement": round(agreement, 4),
        "kappa": round(kappa, 4),
        "pairs": len(pairs),
    }
