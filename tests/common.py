from __future__ import annotations

from pathlib import Path

from frontiertrials.capture import capture_response
from frontiertrials.workspace import Trial


def make_trial(root: Path, *, tasks: int = 1, candidates: int = 2, raters: int = 1) -> Trial:
    trial = Trial.create(root, title="Test trial", question="Which response is more useful?")
    trial.add(
        "rubric",
        {
            "id": "quality",
            "title": "Quality",
            "criteria": [
                {
                    "id": "correctness",
                    "label": "Correctness",
                    "question": "Is it correct?",
                    "weight": 2,
                },
                {
                    "id": "clarity",
                    "label": "Clarity",
                    "question": "Is it clear?",
                    "weight": 1,
                },
            ],
        },
    )
    manifest = trial.manifest()
    manifest["default_rubric_id"] = "quality"
    from frontiertrials.store import write_json

    write_json(trial.manifest_path, manifest)
    for index in range(tasks):
        trial.add(
            "task",
            {
                "id": f"task-{index + 1}",
                "title": f"Task {index + 1}",
                "prompt": f"Answer task {index + 1}.",
                "category": "reasoning",
                "rubric_id": "quality",
            },
        )
    for index in range(candidates):
        trial.add(
            "candidate",
            {
                "id": f"candidate-{index + 1}",
                "label": f"Candidate {index + 1}",
                "provider": "Fictional",
                "model": f"Model {index + 1}",
                "surface": "web",
            },
        )
    for index in range(raters):
        trial.add(
            "rater",
            {"id": f"rater-{index + 1}", "label": f"Rater {index + 1}"},
        )
    source_root = root / "sources"
    source_root.mkdir()
    for task_index in range(tasks):
        for candidate_index in range(candidates):
            identifier = f"response-task-{task_index + 1}-candidate-{candidate_index + 1}"
            source = source_root / f"{identifier}.md"
            source.write_text(
                f"Response {candidate_index + 1} for task {task_index + 1}.\n",
                encoding="utf-8",
            )
            capture_response(
                trial,
                response_id=identifier,
                task_id=f"task-{task_index + 1}",
                candidate_id=f"candidate-{candidate_index + 1}",
                source=source,
                captured_at="2026-01-01T00:00:00Z",
            )
    return trial


def ballot(
    identifier: str,
    pairing_id: str,
    rater_id: str,
    choice: str = "left",
) -> dict:
    return {
        "id": identifier,
        "pairing_id": pairing_id,
        "rater_id": rater_id,
        "choice": choice,
        "confidence": 4,
        "left_scores": {"correctness": 5, "clarity": 4},
        "right_scores": {"correctness": 3, "clarity": 3},
        "rationale": "The left answer is more correct and clear.",
        "flags": [],
    }
