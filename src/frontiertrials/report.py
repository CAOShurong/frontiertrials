"""Self-contained public trial report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .analysis import analyze_trial
from .audit import audit_trial
from .blinding import read_reveal
from .errors import BlindingError
from .seal import build_seal
from .util import html_escape
from .workspace import Trial


def _json_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def _ranking_rows(ranking: list[dict[str, Any]]) -> str:
    peak = max((item["bt_strength"] for item in ranking), default=1)
    rows = []
    for rank, item in enumerate(ranking, 1):
        width = 100 * item["bt_strength"] / peak if peak else 0
        rows.append(
            "<tr>"
            f'<td class="rank">{rank}</td><td><strong>{html_escape(item["label"])}</strong>'
            f"<small>{html_escape(item['provider'])} · {html_escape(item['model'])}</small></td>"
            f'<td><div class="strength"><i style="width:{width:.2f}%"></i></div>'
            f"<b>{item['bt_strength']:.3f}</b><small>95% {item['bt_95'][0]:.3f}–{item['bt_95'][1]:.3f}</small></td>"
            f"<td>{item['wins']} / {item['losses']} / {item['ties']}</td>"
            f"<td>{100 * item['preference_rate']:.1f}%</td>"
            f"<td>{item['rubric']['weighted_mean']:.2f} / 5</td></tr>"
        )
    return "\n".join(rows)


def _criterion_cards(ranking: list[dict[str, Any]]) -> str:
    criterion_ids = sorted(
        {criterion for item in ranking for criterion in item["rubric"].get("criteria", {})}
    )
    cards = []
    for criterion in criterion_ids:
        values = [
            (
                item["label"],
                item["rubric"].get("criteria", {}).get(criterion, 0),
            )
            for item in ranking
        ]
        bars = "".join(
            f'<div class="mini-row"><span>{html_escape(label)}</span>'
            f'<div><i style="width:{score / 5 * 100:.1f}%"></i></div><b>{score:.2f}</b></div>'
            for label, score in values
        )
        cards.append(
            f'<article class="criterion"><h3>{html_escape(criterion.replace("-", " ").title())}</h3>{bars}</article>'
        )
    return "\n".join(cards)


def _category_table(result: dict[str, Any], labels: dict[str, str]) -> str:
    candidates = [item["candidate_id"] for item in result["ranking"]]
    header = "".join(f"<th>{html_escape(labels[item])}</th>" for item in candidates)
    rows = []
    for category, scores in result["category_scores"].items():
        cells = "".join(
            f"<td>{100 * scores.get(candidate, 0):.1f}%</td>" for candidate in candidates
        )
        rows.append(f"<tr><th>{html_escape(category.title())}</th>{cells}</tr>")
    return (
        f"<table><thead><tr><th>Task category</th>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _panel_rows(result: dict[str, Any]) -> str:
    rows = []
    for item in result["panel_diagnostics"]["raters"]:
        alignment = (
            f"{100 * item['consensus_alignment']:.1f}%"
            if item["consensus_alignment"] is not None
            else "n/a"
        )
        rows.append(
            "<tr>"
            f"<td><strong>{html_escape(item['label'])}</strong>"
            f"<small>{html_escape(item['rater_id'])}</small></td>"
            f"<td>{item['ballot_count']}</td>"
            f"<td>{item['mean_confidence']:.2f} / 5</td>"
            f"<td>{100 * item['left_win_rate']:.1f}%</td>"
            f"<td>{100 * item['longer_win_rate']:.1f}%</td>"
            f"<td>{alignment}</td>"
            f"<td>{item['flag_count']}</td></tr>"
        )
    return "\n".join(rows)


def _sensitivity_rows(result: dict[str, Any], labels: dict[str, str]) -> str:
    rows = []
    for removal in result["ranking_sensitivity"]["leave_one_rater_out"]:
        if removal["status"] != "estimated":
            rows.append(
                "<tr>"
                f"<td>{html_escape(removal['removed_rater_id'])}</td>"
                '<td colspan="3">Insufficient retained ballots</td></tr>'
            )
            continue
        leader = removal["ranking"][0]["candidate_id"]
        rows.append(
            "<tr>"
            f"<td>{html_escape(removal['removed_rater_id'])}</td>"
            f"<td>{html_escape(labels.get(leader, leader))}</td>"
            f"<td>{'yes' if removal['leader_changed'] else 'no'}</td>"
            f"<td>{removal['max_absolute_rank_shift']}</td></tr>"
        )
    return "\n".join(rows)


def build_report(
    trial: Trial,
    output: str | Path,
    *,
    bootstrap_samples: int = 400,
) -> Path:
    """Generate a portable report after candidate identities are revealed."""
    if trial.manifest()["state"] != "revealed":
        raise BlindingError(
            "public reports require a revealed trial; use judge packets before reveal"
        )
    result = analyze_trial(trial, bootstrap_samples=bootstrap_samples)
    audit = audit_trial(trial)
    seal = build_seal(trial)
    manifest = trial.manifest()
    reveal = read_reveal(trial)
    labels = {item["candidate_id"]: item["label"] for item in result["ranking"]}
    top = result["ranking"][0] if result["ranking"] else None
    position = result["bias_diagnostics"]["position"]
    verbosity = result["bias_diagnostics"]["verbosity"]
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="FrontierTrials 0.2.0"><title>{html_escape(manifest["title"])} · FrontierTrials report</title>
<style>
:root{{--ink:#1c252c;--muted:#5f676c;--paper:#f5f2eb;--panel:#fffefa;--navy:#24384c;--blue:#526f87;
--brick:#934b45;--ochre:#a4772d;--sage:#6c7d6c;--line:#cfc9bd}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.58 system-ui,-apple-system,Segoe UI,sans-serif}}
header{{position:sticky;top:0;z-index:5;background:var(--paper);color:var(--ink);padding:16px max(22px,calc((100vw - 1240px)/2));
display:flex;justify-content:space-between;border-bottom:2px solid var(--navy)}}header b{{letter-spacing:.12em}}header nav a{{color:var(--navy);margin-left:20px;text-decoration:none;font-size:12px}}
main{{max-width:1240px;margin:auto;padding:58px 22px 90px}}.hero{{display:grid;grid-template-columns:1.3fr .7fr;gap:38px;align-items:end;border-bottom:1px solid var(--line);padding-bottom:34px}}
.eyebrow{{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--brick);font-weight:850}}h1,h2{{font-family:Georgia,serif;letter-spacing:-.025em}}
h1{{font-size:clamp(42px,6vw,72px);line-height:1;margin:12px 0 18px}}h2{{font-size:30px;margin:0}}.question{{font-size:18px;color:#465158}}
.verdict{{background:var(--panel);color:var(--ink);padding:22px;border:1px solid var(--line);border-top:4px solid var(--brick)}}.verdict .top{{color:var(--navy);
font:700 38px Georgia,serif}}.verdict p{{color:var(--muted)}}.verdict code{{color:var(--blue);font-size:10px;overflow-wrap:anywhere}}
.stats{{display:grid;grid-template-columns:repeat(5,1fr);margin:34px 0 62px;border:1px solid var(--line)}}.stat{{background:var(--panel);
padding:17px;border-right:1px solid var(--line)}}.stat:last-child{{border-right:0}}.stat b{{display:block;font:700 28px Georgia,serif}}.stat span{{color:var(--muted);font-size:11px}}
section{{margin-top:60px}}.section-head{{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:18px}}
.section-head p{{max-width:610px;color:var(--muted);font-size:12px;text-align:right;margin:0}}.table-wrap{{overflow:auto;border:1px solid var(--line);background:var(--panel)}}
table{{border-collapse:collapse;width:100%;min-width:900px}}th,td{{padding:13px;border-bottom:1px solid #e5dfd2;text-align:left}}thead th{{font-size:10px;
text-transform:uppercase;letter-spacing:.08em;background:#e9e5dc}}td small{{display:block;color:var(--muted);font-size:10px}}.rank{{font:700 24px Georgia,serif}}
.strength{{display:inline-block;width:120px;height:7px;background:#e3ded2;margin-right:8px;overflow:hidden}}.strength i{{display:block;height:100%;background:var(--brick)}}
.criteria{{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}}.criterion{{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--ochre);padding:18px}}
.criterion h3{{margin:0 0 12px}}.mini-row{{display:grid;grid-template-columns:90px 1fr 34px;gap:8px;align-items:center;margin:7px 0;font-size:11px}}.mini-row div{{height:7px;background:#e4dfd4}}
.mini-row i{{display:block;height:100%;background:var(--ochre)}}.diagnostics{{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line)}}.diag{{background:var(--panel);
border-right:1px solid var(--line);padding:20px}}.diag:last-child{{border-right:0}}.diag strong{{font:700 38px Georgia,serif;color:var(--navy)}}.diag p{{color:var(--muted);font-size:12px}}
.boundary{{border-left:5px solid var(--brick);padding:20px;background:var(--panel);color:var(--muted)}}.alias-grid{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line)}}
.alias{{background:var(--panel);padding:14px;border-right:1px solid var(--line)}}.alias:last-child{{border-right:0}}.alias b{{color:var(--brick)}}@media(max-width:850px){{.hero{{grid-template-columns:1fr}}.stats{{grid-template-columns:repeat(2,1fr)}}
.criteria,.diagnostics,.alias-grid{{grid-template-columns:1fr}}header nav{{display:none}}.section-head{{display:block}}.section-head p{{text-align:left;margin-top:8px}}}}
@media print{{header{{display:none}}body{{background:white}}section{{break-inside:avoid}}}}
</style></head><body><header><b>FRONTIERTRIALS</b><nav><a href="#ranking">Ranking</a><a href="#rubric">Rubric</a>
<a href="#bias">Diagnostics</a><a href="#method">Boundary</a></nav></header><main>
<div class="hero"><div><div class="eyebrow">Revealed blind evaluation</div><h1>{html_escape(manifest["title"])}</h1>
<div class="question">{html_escape(manifest["question"])}</div></div><aside class="verdict">
<div class="eyebrow">Observed leader</div><div class="top">{html_escape(top["label"] if top else "No result")}</div>
<p>Highest fitted pairwise strength in this trial. Overlapping intervals may make the order unstable.</p>
<code>{html_escape(seal["root"])}</code></aside></div>
<div class="stats"><div class="stat"><b>{result["summary"]["task_count"]}</b><span>Private tasks</span></div>
<div class="stat"><b>{result["summary"]["candidate_count"]}</b><span>Captured candidates</span></div>
<div class="stat"><b>{result["summary"]["pairing_count"]}</b><span>Blind pairings</span></div>
<div class="stat"><b>{result["summary"]["ballot_count"]}</b><span>Human ballots</span></div>
<div class="stat"><b>{audit["status"].upper()}</b><span>Structural audit</span></div></div>
<section id="ranking"><div class="section-head"><h2>Preference model</h2><p>Bradley–Terry strengths with task-clustered 95% bootstrap intervals.
Ties contribute half a win to each candidate.</p></div><div class="table-wrap"><table><thead><tr><th>#</th><th>Candidate</th>
<th>Strength and interval</th><th>W / L / T</th><th>Preference</th><th>Rubric mean</th></tr></thead>
<tbody>{_ranking_rows(result["ranking"])}</tbody></table></div></section>
<section id="rubric"><div class="section-head"><h2>Independent rubric scores</h2><p>Reviewers score each response before selecting an overall preference.
These pointwise ratings expose why a pairwise result moved.</p></div><div class="criteria">{_criterion_cards(result["ranking"])}</div></section>
<section><div class="section-head"><h2>Task-category sensitivity</h2><p>Preference rates can reverse across task families. Empty cells are zero, not evidence of inferiority.</p></div>
<div class="table-wrap">{_category_table(result, labels)}</div></section>
<section id="bias"><div class="section-head"><h2>Bias and reliability diagnostics</h2><p>Diagnostics describe the collected ballots; small samples produce wide uncertainty.</p></div>
<div class="diagnostics"><article class="diag"><span class="eyebrow">Left position</span><strong>{100 * position["left_win_rate"]:.1f}%</strong>
<p>{position["left_wins"]} left wins among {position["decisive_ballots"]} decisive ballots. Wilson 95%:
{100 * position["wilson_95"][0]:.1f}–{100 * position["wilson_95"][1]:.1f}%.</p></article>
<article class="diag"><span class="eyebrow">Longer answer wins</span><strong>{100 * verbosity["longer_win_rate"]:.1f}%</strong>
<p>{verbosity["longer_response_wins"]} of {verbosity["comparable_ballots"]} comparable decisive ballots. Association is not causation.</p></article>
<article class="diag"><span class="eyebrow">Reviewer agreement</span><strong>{100 * result["agreement"]["agreement"]:.1f}%</strong>
<p>Cohen's κ = {result["agreement"]["kappa"]:.3f} across {result["agreement"]["pairs"]} overlapping rater pairs.</p></article></div></section>
<section id="panel"><div class="section-head"><h2>Panel sensitivity</h2><p>Per-reviewer summaries are descriptive.
They are not reviewer grades, and removing one reviewer is a sensitivity analysis rather than a correction.</p></div>
<div class="table-wrap"><table><thead><tr><th>Reviewer</th><th>Ballots</th><th>Mean confidence</th>
<th>Left wins</th><th>Longer wins</th><th>Consensus alignment</th><th>Flags</th></tr></thead>
<tbody>{_panel_rows(result)}</tbody></table></div>
<div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Reviewer removed</th>
<th>Re-fitted leader</th><th>Leader changed</th><th>Maximum rank shift</th></tr></thead>
<tbody>{_sensitivity_rows(result, labels)}</tbody></table></div></section>
<section><div class="section-head"><h2>Identity reveal</h2><p>Aliases are disclosed only after ballot collection in the recorded protocol.</p></div>
<div class="alias-grid">{"".join(f'<div class="alias"><b>{html_escape(alias)}</b><br>{html_escape(labels.get(candidate, candidate))}</div>' for candidate, alias in sorted(reveal["candidate_aliases"].items()))}</div></section>
<section id="method"><div class="section-head"><h2>Interpretation boundary</h2><p>A polished chart does not widen the evidence.</p></div>
<div class="boundary">This ranking applies only to the recorded prompts, capture dates, web surfaces, settings, and reviewers.
Web products may route requests through changing models and tools. Human preference does not establish factual correctness,
safety, general intelligence, or statistical significance. The audit validates files, references, assignments, and hashes;
it does not verify answer truth. The demonstration bundled with FrontierTrials is entirely fictional.</div></section>
</main><script id="frontiertrials-data" type="application/json">{_json_script({"manifest": manifest, "analysis": result, "audit": audit, "seal": seal, "reveal": reveal})}</script>
</body></html>"""
    destination.write_text(html, encoding="utf-8", newline="\n")
    return destination
