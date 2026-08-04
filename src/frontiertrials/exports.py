"""Portable CSV and Markdown exports."""

from __future__ import annotations

import csv
import io

from .analysis import analyze_trial
from .workspace import Trial


def ranking_csv(trial: Trial, *, bootstrap_samples: int = 400) -> str:
    result = analyze_trial(trial, bootstrap_samples=bootstrap_samples)
    output = io.StringIO(newline="")
    fields = [
        "rank",
        "candidate_id",
        "label",
        "provider",
        "model",
        "bt_strength",
        "bt_95_low",
        "bt_95_high",
        "wins",
        "losses",
        "ties",
        "appearances",
        "preference_rate",
        "rubric_mean",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for rank, item in enumerate(result["ranking"], 1):
        writer.writerow(
            {
                "rank": rank,
                "candidate_id": item["candidate_id"],
                "label": item["label"],
                "provider": item["provider"],
                "model": item["model"],
                "bt_strength": item["bt_strength"],
                "bt_95_low": item["bt_95"][0],
                "bt_95_high": item["bt_95"][1],
                "wins": item["wins"],
                "losses": item["losses"],
                "ties": item["ties"],
                "appearances": item["appearances"],
                "preference_rate": item["preference_rate"],
                "rubric_mean": item["rubric"]["weighted_mean"],
            }
        )
    return output.getvalue()


def protocol_markdown(trial: Trial) -> str:
    manifest = trial.manifest()
    lines = [
        f"# Trial protocol: {manifest['title']}",
        "",
        f"**Question:** {manifest['question']}",
        "",
        f"**State:** {manifest['state']}",
        "",
        "## Capture",
        "",
        f"- Tasks: {len(trial.all('task'))}",
        f"- Candidates: {len(trial.all('candidate'))}",
        f"- Captured responses: {len(trial.all('response'))}",
        "- Capture surfaces and observed model labels are recorded per candidate.",
        "- Response content is preserved verbatim and checked with SHA-256.",
        "",
        "## Blinding and allocation",
        "",
        f"- {manifest.get('protocol', {}).get('blinding', 'Not recorded.')}",
        f"- {manifest.get('protocol', {}).get('order_policy', 'Not recorded.')}",
        f"- Assigned reviews per pair: {manifest.get('reviews_per_pair', 'not frozen')}",
        "",
        "## Analysis",
        "",
        f"- {manifest.get('protocol', {}).get('tie_policy', 'Not recorded.')}",
        f"- {manifest.get('protocol', {}).get('analysis_unit', 'Not recorded.')}",
        "- Bradley-Terry strengths are accompanied by task-clustered bootstrap intervals.",
        "- Position, verbosity association, rubric scores, and reviewer agreement are reported.",
        "",
        "## Interpretation boundary",
        "",
        "Results apply to this prompt set, capture moment, interfaces, settings, and reviewer panel. "
        "They do not establish general model intelligence, factual correctness, or safety.",
        "",
    ]
    return "\n".join(lines)
