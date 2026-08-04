"""Exact-output capture with integrity metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import IntegrityError, ValidationError
from .store import write_text
from .util import sha256_file, utc_now, word_count
from .workspace import Trial


def capture_response(
    trial: Trial,
    *,
    response_id: str,
    task_id: str,
    candidate_id: str,
    source: str | Path,
    captured_at: str | None = None,
    latency_seconds: float | None = None,
    notes: str = "",
    replace: bool = False,
) -> dict[str, Any]:
    """Copy a UTF-8 response into the trial and record its exact digest."""
    trial.require()
    if trial.manifest()["state"] != "collecting":
        raise ValidationError("responses can only be captured while the trial is collecting")
    trial.get("task", task_id)
    trial.get("candidate", candidate_id)
    source_path = Path(source)
    content = source_path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValidationError("captured response is empty")
    destination = trial.root / "outputs" / f"{response_id}.md"
    if destination.exists() and not replace:
        raise ValidationError(f"response content already exists: {response_id}")
    write_text(destination, content.rstrip() + "\n")
    artifact = {
        "id": response_id,
        "task_id": task_id,
        "candidate_id": candidate_id,
        "content_path": destination.relative_to(trial.root).as_posix(),
        "sha256": sha256_file(destination),
        "captured_at": captured_at or utc_now(),
        "state": "captured",
        "latency_seconds": latency_seconds,
        "characters": len(content),
        "words": word_count(content),
        "notes": notes,
    }
    trial.add("response", artifact, replace=replace)
    return artifact


def response_text(trial: Trial, response: dict[str, Any]) -> str:
    path = (trial.root / response["content_path"]).resolve()
    try:
        path.relative_to(trial.root)
    except ValueError as exc:
        raise IntegrityError(f"response path escapes trial root: {path}") from exc
    if not path.is_file():
        raise IntegrityError(f"response content is missing: {path}")
    observed = sha256_file(path)
    if observed != response["sha256"]:
        raise IntegrityError(
            f"response content changed for {response['id']}: "
            f"expected {response['sha256']}, observed {observed}"
        )
    return path.read_text(encoding="utf-8")


def verify_responses(trial: Trial) -> list[dict[str, str]]:
    results = []
    for response in trial.all("response"):
        try:
            response_text(trial, response)
            results.append({"id": response["id"], "status": "verified"})
        except IntegrityError as exc:
            results.append({"id": response["id"], "status": "changed", "message": str(exc)})
    return results
