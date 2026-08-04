"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import __version__
from .analysis import analyze_trial
from .audit import audit_trial
from .ballots import ballot_completeness, import_ballot_bundle
from .blinding import freeze_trial, reveal_trial
from .capture import capture_response, verify_responses
from .demo import create_demo
from .errors import FrontierTrialsError
from .exports import protocol_markdown, ranking_csv
from .packet import build_packet
from .report import build_report
from .seal import verify_seal, write_seal
from .store import read_json
from .util import pretty_json
from .workspace import Trial


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frontiertrials",
        description="Run reproducible blind evaluations of manually captured AI outputs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create an empty trial")
    init.add_argument("trial")
    init.add_argument("--title", required=True)
    init.add_argument("--question", required=True)
    init.add_argument("--owner", default="")

    add = subparsers.add_parser("add", help="add a validated JSON artifact")
    add.add_argument(
        "kind",
        choices=("task", "candidate", "rubric", "rater", "pairing", "ballot", "response"),
    )
    add.add_argument("json_file")
    add.add_argument("--trial", "-t", default=".")
    add.add_argument("--replace", action="store_true")

    capture = subparsers.add_parser("capture", help="capture one exact response file")
    capture.add_argument("--trial", "-t", default=".")
    capture.add_argument("--id", required=True)
    capture.add_argument("--task", required=True)
    capture.add_argument("--candidate", required=True)
    capture.add_argument("--source", required=True)
    capture.add_argument("--captured-at")
    capture.add_argument("--latency-seconds", type=float)
    capture.add_argument("--notes", default="")
    capture.add_argument("--replace", action="store_true")

    freeze = subparsers.add_parser("freeze", help="create blind pairings and rater allocations")
    freeze.add_argument("--trial", "-t", default=".")
    seed_group = freeze.add_mutually_exclusive_group(required=True)
    seed_group.add_argument("--seed")
    seed_group.add_argument("--seed-file")
    freeze.add_argument("--reviews-per-pair", type=int, default=1)
    freeze.add_argument("--replace", action="store_true")

    packet = subparsers.add_parser("packet", help="build a self-contained blind judging packet")
    packet.add_argument("--trial", "-t", default=".")
    packet.add_argument("--rater", required=True)
    packet.add_argument("--output", "-o", required=True)

    ballots = subparsers.add_parser("import-ballots", help="import packet-downloaded ballots")
    ballots.add_argument("source")
    ballots.add_argument("--trial", "-t", default=".")
    ballots.add_argument("--replace", action="store_true")

    reveal = subparsers.add_parser("reveal", help="reveal candidate identities after rating")
    reveal.add_argument("--trial", "-t", default=".")

    for name, help_text in (
        ("status", "show matrix, assignment, and ballot progress"),
        ("audit", "check integrity, references, blinding, and ballots"),
        ("analyze", "calculate rankings and diagnostics"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--trial", "-t", default=".")
        command.add_argument("--output", "-o")
        if name == "analyze":
            command.add_argument("--bootstrap-samples", type=int, default=400)

    report = subparsers.add_parser("report", help="build a revealed public HTML report")
    report.add_argument("--trial", "-t", default=".")
    report.add_argument("--output", "-o", default="reports/trial-report.html")
    report.add_argument("--bootstrap-samples", type=int, default=400)

    export = subparsers.add_parser("export", help="export ranking CSV or protocol Markdown")
    export.add_argument("format", choices=("ranking-csv", "protocol-markdown"))
    export.add_argument("--trial", "-t", default=".")
    export.add_argument("--output", "-o")

    seal = subparsers.add_parser("seal", help="write a content-addressed trial seal")
    seal.add_argument("--trial", "-t", default=".")
    seal.add_argument("--output", "-o")

    verify = subparsers.add_parser("verify", help="verify a saved trial seal")
    verify.add_argument("--trial", "-t", default=".")
    verify.add_argument("--seal")

    demo = subparsers.add_parser("demo", help="create the fully fictional public demonstration")
    demo.add_argument("trial")
    demo.add_argument("--force", action="store_true")
    return parser


def _trial(args: argparse.Namespace) -> Trial:
    return Trial(args.trial).require()


def _emit(value: str, output: str | None) -> None:
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(value, encoding="utf-8", newline="\n")
        print(destination.resolve())
    else:
        print(value, end="" if value.endswith("\n") else "\n")


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def run(args: argparse.Namespace) -> int:
    if args.command == "init":
        trial = Trial.create(args.trial, title=args.title, question=args.question, owner=args.owner)
        print(trial.root)
        return 0
    if args.command == "demo":
        trial = create_demo(args.trial, force=args.force)
        _print_json({"trial": str(trial.root), "counts": trial.counts()})
        return 0
    trial = _trial(args)
    if args.command == "add":
        print(trial.add(args.kind, read_json(Path(args.json_file)), replace=args.replace))
        return 0
    if args.command == "capture":
        _print_json(
            capture_response(
                trial,
                response_id=args.id,
                task_id=args.task,
                candidate_id=args.candidate,
                source=args.source,
                captured_at=args.captured_at,
                latency_seconds=args.latency_seconds,
                notes=args.notes,
                replace=args.replace,
            )
        )
        return 0
    if args.command == "freeze":
        seed = (
            args.seed
            if args.seed is not None
            else Path(args.seed_file).read_text(encoding="utf-8").strip()
        )
        _print_json(
            freeze_trial(
                trial,
                seed=seed,
                reviews_per_pair=args.reviews_per_pair,
                replace=args.replace,
            )
        )
        return 0
    if args.command == "packet":
        print(build_packet(trial, args.rater, args.output))
        return 0
    if args.command == "import-ballots":
        _print_json(import_ballot_bundle(trial, args.source, replace=args.replace))
        return 0
    if args.command == "reveal":
        _print_json(reveal_trial(trial))
        return 0
    if args.command == "status":
        value = {
            "state": trial.manifest()["state"],
            "counts": trial.counts(),
            "response_integrity": verify_responses(trial),
            "ballots": ballot_completeness(trial),
        }
        _emit(pretty_json(value), args.output)
        return 0
    if args.command == "audit":
        value = audit_trial(trial)
        _emit(pretty_json(value), args.output)
        return 0 if value["status"] == "pass" else 2
    if args.command == "analyze":
        _emit(
            pretty_json(analyze_trial(trial, bootstrap_samples=args.bootstrap_samples)),
            args.output,
        )
        return 0
    if args.command == "report":
        destination = Path(args.output)
        if not destination.is_absolute():
            destination = trial.root / destination
        print(build_report(trial, destination, bootstrap_samples=args.bootstrap_samples))
        return 0
    if args.command == "export":
        value = ranking_csv(trial) if args.format == "ranking-csv" else protocol_markdown(trial)
        _emit(value, args.output)
        return 0
    if args.command == "seal":
        destination = Path(args.output) if args.output else None
        if destination and not destination.is_absolute():
            destination = trial.root / destination
        print(write_seal(trial, destination))
        return 0
    if args.command == "verify":
        source = Path(args.seal) if args.seal else None
        if source and not source.is_absolute():
            source = trial.root / source
        value = verify_seal(trial, source)
        _print_json(value)
        return 0 if value["status"] == "verified" else 3
    raise AssertionError(f"unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    try:
        code = run(parser.parse_args(argv))
    except (FrontierTrialsError, FileNotFoundError, PermissionError) as exc:
        parser.exit(1, f"frontiertrials: error: {exc}\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
