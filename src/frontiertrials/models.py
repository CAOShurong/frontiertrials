"""Dependency-free artifact validators."""

from __future__ import annotations

from typing import Any

from .constants import (
    BALLOT_CHOICES,
    CAPTURE_SURFACES,
    PAIRING_STATES,
    RATING_SCALE,
    RESPONSE_STATES,
    TASK_CATEGORIES,
)
from .errors import ValidationError
from .util import ensure_id, ensure_text


def _ids(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list")
    return [ensure_id(item, field) for item in value]


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValidationError(f"{field} must be a list of strings")
    return value


def validate_task(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "task.id")
    ensure_text(value.get("title"), "task.title")
    ensure_text(value.get("prompt"), "task.prompt")
    if value.get("category", "other") not in TASK_CATEGORIES:
        raise ValidationError("task.category is not recognized")
    _string_list(value.get("tags"), "task.tags")
    for field in ("system_instruction", "context", "reference", "notes"):
        if field in value and not isinstance(value[field], str):
            raise ValidationError(f"task.{field} must be a string")
    return value


def validate_candidate(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "candidate.id")
    ensure_text(value.get("label"), "candidate.label")
    ensure_text(value.get("provider"), "candidate.provider")
    ensure_text(value.get("model"), "candidate.model")
    if value.get("surface", "manual") not in CAPTURE_SURFACES:
        raise ValidationError("candidate.surface is not recognized")
    for field in ("plan", "version", "settings", "notes"):
        if field in value and not isinstance(value[field], (str, dict)):
            raise ValidationError(f"candidate.{field} must be a string or object")
    return value


def validate_response(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "response.id")
    ensure_id(value.get("task_id"), "response.task_id")
    ensure_id(value.get("candidate_id"), "response.candidate_id")
    ensure_text(value.get("content_path"), "response.content_path")
    ensure_text(value.get("sha256"), "response.sha256")
    ensure_text(value.get("captured_at"), "response.captured_at")
    if value.get("state", "captured") not in RESPONSE_STATES:
        raise ValidationError("response.state is not recognized")
    for field in ("latency_seconds", "input_tokens", "output_tokens"):
        number = value.get(field)
        if number is not None and (not isinstance(number, (int, float)) or number < 0):
            raise ValidationError(f"response.{field} must be non-negative")
    return value


def validate_rubric(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "rubric.id")
    ensure_text(value.get("title"), "rubric.title")
    criteria = value.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise ValidationError("rubric.criteria must be a non-empty list")
    seen: set[str] = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise ValidationError("rubric.criteria[] must be an object")
        identifier = ensure_id(criterion.get("id"), "rubric.criteria[].id")
        if identifier in seen:
            raise ValidationError(f"duplicate criterion: {identifier}")
        seen.add(identifier)
        ensure_text(criterion.get("label"), "rubric.criteria[].label")
        ensure_text(criterion.get("question"), "rubric.criteria[].question")
        weight = criterion.get("weight", 1)
        if not isinstance(weight, (int, float)) or weight <= 0:
            raise ValidationError("criterion weight must be positive")
        anchors = criterion.get("anchors", {})
        if not isinstance(anchors, dict):
            raise ValidationError("criterion anchors must be an object")
    return value


def validate_pairing(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "pairing.id")
    ensure_id(value.get("task_id"), "pairing.task_id")
    ensure_id(value.get("rubric_id"), "pairing.rubric_id")
    left = ensure_id(value.get("left_response_id"), "pairing.left_response_id")
    right = ensure_id(value.get("right_response_id"), "pairing.right_response_id")
    if left == right:
        raise ValidationError("pairing responses must differ")
    ensure_text(value.get("left_alias"), "pairing.left_alias")
    ensure_text(value.get("right_alias"), "pairing.right_alias")
    if value.get("state", "ready") not in PAIRING_STATES:
        raise ValidationError("pairing.state is not recognized")
    return value


def validate_ballot(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "ballot.id")
    ensure_id(value.get("pairing_id"), "ballot.pairing_id")
    ensure_id(value.get("rater_id"), "ballot.rater_id")
    if value.get("choice") not in BALLOT_CHOICES:
        raise ValidationError("ballot.choice is not recognized")
    confidence = value.get("confidence")
    if confidence not in RATING_SCALE:
        raise ValidationError("ballot.confidence must be an integer from 1 to 5")
    for side in ("left_scores", "right_scores"):
        scores = value.get(side)
        if not isinstance(scores, dict):
            raise ValidationError(f"ballot.{side} must be an object")
        for criterion, score in scores.items():
            ensure_id(criterion, f"ballot.{side} criterion")
            if score not in RATING_SCALE:
                raise ValidationError(f"ballot.{side}.{criterion} must be 1 to 5")
    ensure_text(value.get("rationale"), "ballot.rationale")
    _string_list(value.get("flags"), "ballot.flags")
    return value


def validate_rater(value: dict[str, Any]) -> dict[str, Any]:
    ensure_id(value.get("id"), "rater.id")
    ensure_text(value.get("label"), "rater.label")
    if "expertise" in value:
        _string_list(value["expertise"], "rater.expertise")
    if "notes" in value and not isinstance(value["notes"], str):
        raise ValidationError("rater.notes must be a string")
    return value


VALIDATORS = {
    "task": validate_task,
    "candidate": validate_candidate,
    "response": validate_response,
    "rubric": validate_rubric,
    "pairing": validate_pairing,
    "ballot": validate_ballot,
    "rater": validate_rater,
}


def validate(kind: str, value: dict[str, Any]) -> dict[str, Any]:
    try:
        validator = VALIDATORS[kind]
    except KeyError as exc:
        raise ValidationError(f"unknown artifact kind: {kind}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{kind} must be an object")
    return validator(value)
