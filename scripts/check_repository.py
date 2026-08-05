"""Repository-level release checks beyond unit behavior."""

from __future__ import annotations

import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from frontiertrials import __version__  # noqa: E402
from frontiertrials.adjudication import build_adjudication_queue  # noqa: E402
from frontiertrials.audit import audit_trial  # noqa: E402
from frontiertrials.constants import APP_VERSION  # noqa: E402
from frontiertrials.seal import verify_seal  # noqa: E402
from frontiertrials.workspace import Trial  # noqa: E402

EXPECTED_VERSION = "0.3.0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_versions() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(__version__ == EXPECTED_VERSION, "package version mismatch")
    require(APP_VERSION == EXPECTED_VERSION, "application version mismatch")
    require(pyproject["project"]["version"] == EXPECTED_VERSION, "pyproject version mismatch")
    require(f"version: {EXPECTED_VERSION}" in citation, "citation version mismatch")
    require(f"## [{EXPECTED_VERSION}]" in changelog, "changelog release missing")
    require(
        pyproject["project"]["authors"] == [{"name": "Shurong Cao"}],
        "package authorship must name Shurong Cao only",
    )


def check_install_claims() -> None:
    release_url = (
        "https://github.com/CAOShurong/frontiertrials/releases/download/"
        f"v{EXPECTED_VERSION}/frontiertrials-{EXPECTED_VERSION}-py3-none-any.whl"
    )
    for relative in ("README.md", "site/index.html"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        require(release_url in text, f"{relative} lacks the versioned release wheel")
        require(
            "python -m pip install frontiertrials\n" not in text,
            f"{relative} makes an unsupported PyPI install claim",
        )


def check_figures() -> None:
    for relative in ("docs/assets/hero.svg", "docs/assets/workflow.svg"):
        path = ROOT / relative
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        require(root.tag.endswith("svg"), f"{relative} is not SVG")
        require(root.get("viewBox") is not None, f"{relative} lacks a viewBox")
        text = path.read_text(encoding="utf-8")
        require("linearGradient" not in text, f"{relative} uses a gradient")
        require("<filter" not in text, f"{relative} uses a decorative filter")


def check_personal_lab() -> None:
    for relative in (
        "src/frontiertrials/web/index.html",
        "src/frontiertrials/web/styles.css",
        "src/frontiertrials/web/app.js",
    ):
        require((ROOT / relative).exists(), f"personal-lab asset missing: {relative}")
    html = (ROOT / "src/frontiertrials/web/index.html").read_text(encoding="utf-8")
    script = (ROOT / "src/frontiertrials/web/app.js").read_text(encoding="utf-8")
    homepage = (ROOT / "site/index.html").read_text(encoding="utf-8")
    require("Which AI subscription earns a place" in html, "personal-lab promise missing")
    require("Your text stays in this browser" in html, "personal-lab privacy notice missing")
    require("localStorage" in script, "personal-lab persistence missing")
    require("fetch(" not in script, "personal-lab script makes a network request")
    require("XMLHttpRequest" not in script, "personal-lab script makes a network request")
    require('href="try/"' in homepage, "homepage does not link to Personal Lab")


def check_relative_readme_links() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
        if "://" in target or target.startswith("#"):
            continue
        path_text = target.split("#", 1)[0]
        if path_text:
            require((ROOT / path_text).exists(), f"README link target is missing: {target}")


def check_committed_demo() -> None:
    trial = Trial(ROOT / "examples" / "demo").require()
    audit = audit_trial(trial)
    verification = verify_seal(trial)
    adjudication = build_adjudication_queue(trial)
    require(audit["status"] == "pass", "committed demo audit failed")
    require(verification["status"] == "verified", "committed demo seal changed")
    require(adjudication["blind_safe"], "adjudication export is not marked blind-safe")
    serialized = str(adjudication)
    for candidate in trial.all("candidate"):
        require(candidate["id"] not in serialized, "adjudication leaks a candidate ID")
        require(candidate["model"] not in serialized, "adjudication leaks a model label")
    report = (trial.root / "reports" / "trial-report.html").read_text(encoding="utf-8")
    packet = (trial.root / "packets" / "reviewer-one.html").read_text(encoding="utf-8")
    require("Panel sensitivity" in report, "demo report lacks panel sensitivity")
    require("<script src=" not in report + packet, "generated HTML loads an external script")
    require('rel="stylesheet"' not in report + packet, "generated HTML loads a stylesheet")


def main() -> None:
    check_versions()
    check_install_claims()
    check_figures()
    check_personal_lab()
    check_relative_readme_links()
    check_committed_demo()
    print("repository checks: pass")


if __name__ == "__main__":
    main()
