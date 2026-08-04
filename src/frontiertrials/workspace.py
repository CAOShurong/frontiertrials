"""Trial workspace lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import DIRECTORIES, FORMAT_VERSION, KINDS
from .errors import ValidationError
from .models import validate
from .store import load_directory, read_json, write_json
from .util import ensure_id, ensure_text, utc_now


class Trial:
    """A file-native blind evaluation trial."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    @property
    def manifest_path(self) -> Path:
        return self.root / "frontiertrials.json"

    @classmethod
    def create(
        cls,
        root: str | Path,
        *,
        title: str,
        question: str,
        owner: str = "",
        overwrite: bool = False,
    ) -> Trial:
        trial = cls(root)
        if trial.manifest_path.exists() and not overwrite:
            raise ValidationError(f"trial already exists: {trial.root}")
        trial.root.mkdir(parents=True, exist_ok=True)
        for directory in (*DIRECTORIES.values(), "outputs", "packets", "reports", "secrets"):
            (trial.root / directory).mkdir(exist_ok=True)
        manifest = {
            "format_version": FORMAT_VERSION,
            "title": ensure_text(title, "title"),
            "question": ensure_text(question, "question"),
            "owner": owner,
            "created_at": utc_now(),
            "state": "collecting",
            "description": "",
            "protocol": {
                "blinding": "candidate identity hidden during rating",
                "order_policy": "balanced deterministic pair order",
                "tie_policy": "ties contribute half a win to each candidate",
                "analysis_unit": "ballot with task-clustered bootstrap",
            },
            "exclusions": [],
            "tags": [],
        }
        write_json(trial.manifest_path, manifest)
        return trial

    def manifest(self) -> dict[str, Any]:
        value = read_json(self.manifest_path)
        if value.get("format_version") != FORMAT_VERSION:
            raise ValidationError(f"unsupported format_version: {value.get('format_version')!r}")
        ensure_text(value.get("title"), "title")
        ensure_text(value.get("question"), "question")
        if value.get("state") not in {"collecting", "frozen", "revealed"}:
            raise ValidationError("manifest.state must be collecting, frozen, or revealed")
        return value

    def require(self) -> Trial:
        self.manifest()
        return self

    def path_for(self, kind: str, identifier: str) -> Path:
        if kind not in DIRECTORIES:
            raise ValidationError(f"unknown artifact kind: {kind}")
        return self.root / DIRECTORIES[kind] / f"{ensure_id(identifier)}.json"

    def add(
        self,
        kind: str,
        artifact: dict[str, Any],
        *,
        replace: bool = False,
    ) -> Path:
        self.require()
        value = validate(kind, artifact)
        path = self.path_for(kind, value["id"])
        if path.exists() and not replace:
            raise ValidationError(f"{kind} already exists: {value['id']}")
        write_json(path, value)
        return path

    def get(self, kind: str, identifier: str) -> dict[str, Any]:
        return validate(kind, read_json(self.path_for(kind, identifier)))

    def all(self, kind: str) -> list[dict[str, Any]]:
        if kind not in DIRECTORIES:
            raise ValidationError(f"unknown artifact kind: {kind}")
        return sorted(
            (validate(kind, item) for item in load_directory(self.root / DIRECTORIES[kind])),
            key=lambda item: item["id"],
        )

    def index(self, kind: str) -> dict[str, dict[str, Any]]:
        return {item["id"]: item for item in self.all(kind)}

    def counts(self) -> dict[str, int]:
        return {kind: len(self.all(kind)) for kind in KINDS}

    def set_state(self, state: str) -> None:
        if state not in {"collecting", "frozen", "revealed"}:
            raise ValidationError("invalid trial state")
        manifest = self.manifest()
        manifest["state"] = state
        write_json(self.manifest_path, manifest)
