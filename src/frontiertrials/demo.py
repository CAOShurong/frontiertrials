"""Deterministic, fully fictional no-API evaluation demonstration."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from .adjudication import adjudication_markdown, build_adjudication_queue
from .analysis import analyze_trial
from .audit import audit_trial
from .ballots import ballot_completeness
from .blinding import freeze_trial, reveal_trial
from .capture import capture_response, verify_responses
from .exports import protocol_markdown, ranking_csv
from .packet import build_packet
from .report import build_report
from .seal import write_seal
from .store import write_json, write_text
from .util import stable_int
from .workspace import Trial

DEMO_TIME = "2026-02-11T09:30:00Z"
DEMO_SEED = "frontiertrials-public-synthetic-demo-v1"


def _tasks() -> list[dict[str, Any]]:
    return [
        {
            "id": "rf-fault",
            "title": "Explain an RF anomaly without overclaiming",
            "category": "engineering",
            "prompt": (
                "A 2.4 GHz receiver shows a 7 dB sensitivity loss only when a nearby DC motor "
                "changes speed. Give a ranked diagnosis plan. Separate observations, hypotheses, "
                "tests, and stop conditions. Do not invent measurements."
            ),
            "context": "Lab has a spectrum analyzer, near-field probes, and a programmable supply.",
            "reference": "A good answer distinguishes conducted and radiated coupling.",
            "rubric_id": "general-quality",
            "tags": ["rf", "debugging"],
        },
        {
            "id": "converter-review",
            "title": "Review a converter compensation proposal",
            "category": "engineering",
            "prompt": (
                "Critique this proposal: 'Set the buck converter crossover to one half of the "
                "switching frequency and add phase boost until the simulation reaches 60 degrees.' "
                "Identify unsafe assumptions and propose a measurement-backed alternative."
            ),
            "context": "Switching frequency is 500 kHz; plant and layout parasitics are not measured.",
            "reference": "The response should discuss bandwidth limits, sampling, delays, and plant identification.",
            "rubric_id": "general-quality",
            "tags": ["power-electronics", "control"],
        },
        {
            "id": "csv-parser",
            "title": "Design a robust measurement CSV parser",
            "category": "coding",
            "prompt": (
                "Write a dependency-free Python function that reads instrument CSV text with "
                "comment lines, units in headers, missing values, and scientific notation. Return "
                "validated rows and explicit diagnostics. Explain edge cases and tests."
            ),
            "context": "Input is untrusted UTF-8 text; silently dropping malformed rows is forbidden.",
            "reference": "The design should avoid naive comma splitting and expose line numbers.",
            "rubric_id": "general-quality",
            "tags": ["python", "data"],
        },
        {
            "id": "paper-claim",
            "title": "Audit a paper claim from limited evidence",
            "category": "research",
            "prompt": (
                "A paper reports '23% lower inference energy' from one board and one workload, "
                "without uncertainty bars. Draft a concise review that separates what is supported, "
                "what is unknown, and the minimum additional evidence needed."
            ),
            "context": "No raw traces, board calibration record, or repeated-run table is available.",
            "reference": "Avoid converting a relative point estimate into a general hardware claim.",
            "rubric_id": "general-quality",
            "tags": ["review", "uncertainty"],
        },
        {
            "id": "bilingual-abstract",
            "title": "Rewrite a bilingual technical abstract",
            "category": "multilingual",
            "prompt": (
                "Rewrite the supplied concept as a 120-word English abstract followed by precise "
                "Traditional Chinese. Preserve the distinction between detection accuracy and "
                "calibration error. Do not add results."
            ),
            "context": "Concept: an edge fault detector adapts confidence under thermal drift; evaluation is planned but not completed.",
            "reference": "Both languages must state that evaluation remains future work.",
            "rubric_id": "general-quality",
            "tags": ["writing", "traditional-chinese"],
        },
        {
            "id": "bayes-sensor",
            "title": "Reason about a low-base-rate sensor alert",
            "category": "reasoning",
            "prompt": (
                "A fault affects 0.5% of units. A detector has 94% sensitivity and 97% specificity. "
                "Compute the probability of a fault after one positive alert, show the calculation, "
                "and explain one operational implication."
            ),
            "context": "Treat rates as fixed for this exercise.",
            "reference": "Bayes result is approximately 13.6%.",
            "rubric_id": "general-quality",
            "tags": ["bayes", "sensors"],
        },
        {
            "id": "replication-plan",
            "title": "Plan a small replication study",
            "category": "research",
            "prompt": (
                "Plan a two-week replication of an edge classifier latency claim using one desktop "
                "GPU and two embedded boards. Include freeze points, randomization, failure logging, "
                "resource estimates, and a decision rule."
            ),
            "context": "The original authors released code but no container or raw timing traces.",
            "reference": "A good plan separates environment reconstruction from measurement.",
            "rubric_id": "general-quality",
            "tags": ["replication", "planning"],
        },
        {
            "id": "table-reading",
            "title": "Interpret an incomplete benchmark table",
            "category": "analysis",
            "prompt": (
                "A table shows Model X: 88.2 accuracy, 41 ms; Model Y: 87.9 accuracy, 25 ms; "
                "Model Z: 89.0 accuracy, latency not reported. Explain what decisions the table "
                "supports, what it does not support, and which follow-up measurement has highest value."
            ),
            "context": "No confidence intervals, hardware identity, or batch size are reported.",
            "reference": "Do not declare a universal winner.",
            "rubric_id": "general-quality",
            "tags": ["benchmark", "tradeoffs"],
        },
    ]


def _candidates() -> list[dict[str, Any]]:
    return [
        {
            "id": "aurora",
            "label": "Aurora Large",
            "provider": "Fictional Northstar Lab",
            "model": "Aurora Large 2026-01",
            "surface": "web",
            "plan": "Synthetic Plus",
            "version": "observed 2026-02-11",
            "settings": {"reasoning": "standard", "tools": "off"},
            "notes": "Fictional candidate used only for the public demonstration.",
        },
        {
            "id": "boreal",
            "label": "Boreal Reasoner",
            "provider": "Fictional Borealis Research",
            "model": "Boreal R2",
            "surface": "web",
            "plan": "Synthetic Pro",
            "version": "observed 2026-02-11",
            "settings": {"reasoning": "extended", "tools": "off"},
            "notes": "Fictional candidate used only for the public demonstration.",
        },
        {
            "id": "cinder",
            "label": "Cinder Chat",
            "provider": "Fictional Ember Systems",
            "model": "Cinder Chat 4",
            "surface": "desktop",
            "plan": "Synthetic Standard",
            "version": "observed 2026-02-11",
            "settings": {"mode": "balanced", "tools": "off"},
            "notes": "Fictional candidate used only for the public demonstration.",
        },
        {
            "id": "delta",
            "label": "Delta Studio",
            "provider": "Fictional Delta Works",
            "model": "Delta Studio 3.2",
            "surface": "web",
            "plan": "Synthetic Research",
            "version": "observed 2026-02-11",
            "settings": {"mode": "precise", "tools": "off"},
            "notes": "Fictional candidate used only for the public demonstration.",
        },
    ]


def _rubric() -> dict[str, Any]:
    return {
        "id": "general-quality",
        "title": "Engineering and research response quality",
        "criteria": [
            {
                "id": "correctness",
                "label": "Correctness",
                "question": "Are calculations, claims, and causal statements supportable?",
                "weight": 1.5,
                "anchors": {
                    "1": "materially wrong",
                    "3": "mostly sound",
                    "5": "precise and correct",
                },
            },
            {
                "id": "instruction-fit",
                "label": "Instruction fit",
                "question": "Does the response satisfy every explicit constraint?",
                "weight": 1.25,
                "anchors": {"1": "misses the task", "3": "minor omissions", "5": "complete"},
            },
            {
                "id": "uncertainty",
                "label": "Uncertainty discipline",
                "question": "Does it separate evidence, assumptions, and unknowns?",
                "weight": 1.25,
                "anchors": {"1": "overclaims", "3": "mixed", "5": "clear boundaries"},
            },
            {
                "id": "actionability",
                "label": "Actionability",
                "question": "Can the reader execute or verify the proposed next steps?",
                "weight": 1.0,
                "anchors": {"1": "vague", "3": "usable", "5": "operational"},
            },
            {
                "id": "clarity",
                "label": "Clarity",
                "question": "Is the response organized without unnecessary complexity?",
                "weight": 0.75,
                "anchors": {"1": "confusing", "3": "readable", "5": "economical and clear"},
            },
        ],
    }


TASK_CORES = {
    "rf-fault": (
        "Start by reproducing the speed-correlated loss with a fixed receiver configuration. "
        "Capture supply ripple and a spectrum trace while stepping motor speed. Test conducted "
        "coupling by powering the motor separately, then test radiated coupling with distance, "
        "orientation, and near-field scans. Change one variable at a time. Stop when the sensitivity "
        "loss follows one coupling path and the mitigation restores the baseline in repeated runs."
    ),
    "converter-review": (
        "Half the switching frequency is not a defensible default crossover. Sampling, PWM delay, "
        "right-half-plane behavior where applicable, output-filter poles, ESR zeros, and layout "
        "parasitics constrain bandwidth. Measure or identify the plant across operating points, "
        "select a conservative crossover below unmodeled dynamics, design compensation, and verify "
        "gain/phase margin with loop injection plus load-step tests on hardware."
    ),
    "csv-parser": (
        "Use csv.reader over io.StringIO, retain physical line numbers, skip only explicitly defined "
        "comment rows, normalize headers into name and unit fields, and return a result containing "
        "valid rows plus structured diagnostics. Convert numeric cells with Decimal or float under "
        "an explicit policy; represent missing values as None. Test quoted commas, blank fields, "
        "duplicate headers, inconsistent columns, non-finite values, and malformed UTF-8 upstream."
    ),
    "paper-claim": (
        "The table supports only a 23% relative point difference for the tested board and workload "
        "under undocumented variability. It does not establish repeatability, measurement accuracy, "
        "or transfer to other hardware. Request per-run traces, repetitions, uncertainty intervals, "
        "power-instrument calibration, workload controls, and the exact aggregation rule. Reassess "
        "only after the interval and measurement error are small enough for the claimed effect."
    ),
    "bilingual-abstract": (
        "This work proposes an edge fault detector that adapts predictive confidence under thermal "
        "drift. The method distinguishes classification accuracy from calibration error so that "
        "correct labels are not mistaken for reliable probabilities. We define a temperature-aware "
        "recalibration stage and an evaluation protocol spanning controlled thermal conditions. "
        "Experiments have not yet been completed; therefore, no performance improvement is claimed. "
        "Future work will measure accuracy, calibration, latency, and energy with repeated trials."
    ),
    "bayes-sensor": (
        "For 10,000 units, expect 50 faults: about 47 positive alerts among faults. Of 9,950 healthy "
        "units, a 3% false-positive rate gives about 298.5 positive alerts. The positive predictive "
        "value is 47 / (47 + 298.5) = 0.136, or about 13.6%. A positive alert should trigger a "
        "confirmatory test rather than automatic replacement because most positives are false at "
        "this low base rate."
    ),
    "replication-plan": (
        "Days 1–3 freeze the code commit, datasets, board firmware, clocks, power modes, and timing "
        "definition; rebuild environments before measuring. Days 4–6 run smoke tests and log every "
        "failure. Days 7–10 randomize model and board order, warm-up policy, and repeated timing "
        "blocks while preserving raw traces. Days 11–12 analyze per-board distributions and "
        "sensitivity to setup choices. Reserve two days for reruns. Accept the claim only if the "
        "predeclared latency statistic and interval meet the stated tolerance on both boards."
    ),
    "table-reading": (
        "The table supports that Y has nearly the same reported accuracy as X with lower reported "
        "latency in the undisclosed setup. Z has the highest point accuracy but cannot enter a "
        "latency tradeoff. The table does not support significance, portability, or a universal "
        "winner because uncertainty, hardware, and batch size are absent. The highest-value next "
        "measurement is a controlled latency distribution for all three models on one named "
        "hardware and batch configuration, paired with repeated accuracy estimates."
    ),
}

STYLES = {
    "aurora": (
        "It uses a compact decision tree and explicit stop conditions.",
        "The main limitation is that each branch needs repeated measurements before attribution.",
    ),
    "boreal": (
        "It makes the calculation or causal chain explicit before giving the recommendation.",
        "A predeclared decision threshold prevents the analysis from moving after results are seen.",
    ),
    "cinder": (
        "It prioritizes a concise checklist that can be used at the bench.",
        "Some implementation detail should still be fixed in the lab record.",
    ),
    "delta": (
        "It separates supported conclusions from unresolved evidence in a short audit trail.",
        "The final decision remains conditional on the missing measurement.",
    ),
}


def _response(task_id: str, candidate_id: str) -> str:
    lead = {
        "aurora": "Recommended approach",
        "boreal": "Reasoning and result",
        "cinder": "Practical checklist",
        "delta": "Evidence-bounded answer",
    }[candidate_id]
    strength, caveat = STYLES[candidate_id]
    suffix = (
        " Record the exact interface, settings, timestamps, and raw observations so the result can "
        "be audited later."
    )
    if candidate_id == "cinder" and task_id in {"paper-claim", "table-reading"}:
        suffix = " The available point estimates are useful for triage but insufficient for a general conclusion."
    return f"# {lead}\n\n{TASK_CORES[task_id]}\n\n{strength} {caveat}{suffix}\n"


BASE_QUALITY = {"aurora": 4.2, "boreal": 4.45, "cinder": 3.65, "delta": 4.05}
TASK_ADJUST = {
    "rf-fault": {"aurora": 0.4, "boreal": 0.1, "cinder": 0.2, "delta": 0.0},
    "converter-review": {"aurora": 0.2, "boreal": 0.4, "cinder": -0.1, "delta": 0.1},
    "csv-parser": {"aurora": 0.1, "boreal": 0.3, "cinder": 0.0, "delta": 0.2},
    "paper-claim": {"aurora": 0.0, "boreal": 0.2, "cinder": -0.2, "delta": 0.5},
    "bilingual-abstract": {"aurora": 0.1, "boreal": -0.1, "cinder": 0.3, "delta": 0.4},
    "bayes-sensor": {"aurora": 0.0, "boreal": 0.5, "cinder": -0.1, "delta": 0.1},
    "replication-plan": {"aurora": 0.3, "boreal": 0.4, "cinder": -0.2, "delta": 0.2},
    "table-reading": {"aurora": 0.0, "boreal": 0.1, "cinder": -0.1, "delta": 0.5},
}


def _score(candidate_id: str, task_id: str, criterion: str, rater_id: str) -> int:
    value = BASE_QUALITY[candidate_id] + TASK_ADJUST[task_id][candidate_id]
    criterion_adjust = {
        "correctness": 0.15 if candidate_id == "boreal" else 0,
        "instruction-fit": 0.15 if candidate_id == "delta" else 0,
        "uncertainty": 0.2 if candidate_id == "delta" else -0.1 if candidate_id == "cinder" else 0,
        "actionability": 0.2 if candidate_id == "aurora" else 0,
        "clarity": 0.2 if candidate_id == "cinder" else 0,
    }[criterion]
    jitter = (
        (stable_int(DEMO_SEED, f"{candidate_id}:{task_id}:{criterion}:{rater_id}") % 5) - 2
    ) * 0.12
    return max(1, min(5, round(value + criterion_adjust + jitter)))


def _create_ballots(trial: Trial) -> None:
    responses = trial.index("response")
    for pairing in trial.all("pairing"):
        left_candidate = responses[pairing["left_response_id"]]["candidate_id"]
        right_candidate = responses[pairing["right_response_id"]]["candidate_id"]
        task_id = pairing["task_id"]
        for rater_id in pairing["assigned_rater_ids"]:
            criteria = ("correctness", "instruction-fit", "uncertainty", "actionability", "clarity")
            left_scores = {
                criterion: _score(left_candidate, task_id, criterion, rater_id)
                for criterion in criteria
            }
            right_scores = {
                criterion: _score(right_candidate, task_id, criterion, rater_id)
                for criterion in criteria
            }
            left_mean = sum(left_scores.values()) / len(left_scores)
            right_mean = sum(right_scores.values()) / len(right_scores)
            disagreement = stable_int(DEMO_SEED, f"disagree:{pairing['id']}:{rater_id}") % 19 == 0
            if abs(left_mean - right_mean) < 0.25:
                choice = "tie"
            elif left_mean > right_mean:
                choice = "right" if disagreement else "left"
            else:
                choice = "left" if disagreement else "right"
            confidence = 3 if choice == "tie" else 4
            ballot = {
                "id": f"ballot-{rater_id}-{pairing['order_index'] + 1:03d}",
                "pairing_id": pairing["id"],
                "rater_id": rater_id,
                "choice": choice,
                "confidence": confidence,
                "left_scores": left_scores,
                "right_scores": right_scores,
                "rationale": (
                    "Synthetic ballot: the preference follows the recorded criterion scores, "
                    "with a deterministic disagreement case included to exercise diagnostics."
                ),
                "flags": ["synthetic-demo"],
                "recorded_at": DEMO_TIME,
            }
            trial.add("ballot", ballot)


def create_demo(root: str | Path, *, force: bool = False) -> Trial:
    """Create a fully fictional trial with 191 JSON artifacts and 32 captured outputs."""
    root_path = Path(root).resolve()
    if root_path.exists() and any(root_path.iterdir()):
        if not force:
            raise FileExistsError(f"demo destination is not empty: {root_path}")
        shutil.rmtree(root_path)
    trial = Trial.create(
        root_path,
        title="Private EE & AI Task Trial",
        question=(
            "Which fictional assistant best supports careful engineering and research decisions "
            "across a small private task set?"
        ),
        owner="Synthetic demonstration",
    )
    manifest = trial.manifest()
    manifest.update(
        {
            "created_at": DEMO_TIME,
            "description": (
                "Every candidate, provider, response, ballot, timing, and result is fictional. "
                "The dataset demonstrates workflow mechanics only."
            ),
            "default_rubric_id": "general-quality",
            "exclusions": ["tool use", "web search", "file uploads", "multi-turn repair"],
            "tags": ["synthetic-demo", "electrical-engineering", "research", "no-api"],
        }
    )
    write_json(trial.manifest_path, manifest)
    for item in _tasks():
        trial.add("task", item)
    for item in _candidates():
        trial.add("candidate", item)
    trial.add("rubric", _rubric())
    for item in (
        {
            "id": "reviewer-one",
            "label": "Reviewer One",
            "expertise": ["electrical-engineering", "experiments"],
            "notes": "Fictional reviewer.",
        },
        {
            "id": "reviewer-two",
            "label": "Reviewer Two",
            "expertise": ["machine-learning", "technical-writing"],
            "notes": "Fictional reviewer.",
        },
    ):
        trial.add("rater", item)
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        for task in _tasks():
            for candidate in _candidates():
                response_id = f"response-{task['id']}-{candidate['id']}"
                source = temporary_root / f"{response_id}.md"
                write_text(source, _response(task["id"], candidate["id"]))
                latency = 18 + stable_int(DEMO_SEED, f"latency:{response_id}") % 73
                capture_response(
                    trial,
                    response_id=response_id,
                    task_id=task["id"],
                    candidate_id=candidate["id"],
                    source=source,
                    captured_at=DEMO_TIME,
                    latency_seconds=float(latency),
                    notes="Fictional output captured for the public demonstration.",
                )
    freeze_trial(trial, seed=DEMO_SEED, reviews_per_pair=2)
    frozen_manifest = trial.manifest()
    frozen_manifest["frozen_at"] = DEMO_TIME
    write_json(trial.manifest_path, frozen_manifest)
    for rater_id in ("reviewer-one", "reviewer-two"):
        build_packet(trial, rater_id, trial.root / "packets" / f"{rater_id}.html")
    _create_ballots(trial)
    adjudication = build_adjudication_queue(trial)
    reveal_trial(trial)
    reports = trial.root / "reports"
    write_json(reports / "audit.json", audit_trial(trial))
    write_json(
        reports / "status.json",
        {
            "state": trial.manifest()["state"],
            "counts": trial.counts(),
            "response_integrity": verify_responses(trial),
            "ballots": ballot_completeness(trial),
        },
    )
    write_json(reports / "adjudication.json", adjudication)
    write_text(reports / "adjudication.md", adjudication_markdown(adjudication))
    write_text(reports / "ranking.csv", ranking_csv(trial))
    write_text(reports / "protocol.md", protocol_markdown(trial))
    write_json(reports / "analysis.json", analyze_trial(trial))
    build_report(trial, reports / "trial-report.html")
    write_seal(trial, created_at=DEMO_TIME)
    return trial
