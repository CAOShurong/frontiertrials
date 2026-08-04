"""Self-contained offline judging packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .capture import response_text
from .errors import BlindingError
from .util import html_escape
from .workspace import Trial


def _packet_data(trial: Trial, rater_id: str) -> dict[str, Any]:
    rater = trial.get("rater", rater_id)
    tasks = trial.index("task")
    rubrics = trial.index("rubric")
    responses = trial.index("response")
    pairings = [
        item
        for item in trial.all("pairing")
        if rater_id in item.get("assigned_rater_ids", []) and item.get("state", "ready") == "ready"
    ]
    items = []
    for pairing in pairings:
        task = tasks[pairing["task_id"]]
        rubric = rubrics[pairing["rubric_id"]]
        left = responses[pairing["left_response_id"]]
        right = responses[pairing["right_response_id"]]
        items.append(
            {
                "pairing_id": pairing["id"],
                "task": {
                    "title": task["title"],
                    "prompt": task["prompt"],
                    "context": task.get("context", ""),
                    "reference": task.get("reference", ""),
                },
                "rubric": rubric,
                "left": {
                    "alias": pairing["left_alias"],
                    "content": response_text(trial, left),
                    "words": left.get("words", 0),
                },
                "right": {
                    "alias": pairing["right_alias"],
                    "content": response_text(trial, right),
                    "words": right.get("words", 0),
                },
            }
        )
    return {
        "trial_title": trial.manifest()["title"],
        "rater": {"id": rater["id"], "label": rater["label"]},
        "items": items,
        "instructions": (
            "Score each response independently against the rubric before choosing a preference. "
            "Do not infer candidate identity. Abstain when the task cannot be judged."
        ),
    }


def build_packet(trial: Trial, rater_id: str, output: str | Path) -> Path:
    """Build one offline HTML packet that downloads JSON ballots."""
    if trial.manifest()["state"] not in {"frozen", "revealed"}:
        raise BlindingError("freeze the trial before building packets")
    data = _packet_data(trial, rater_id)
    if not data["items"]:
        raise BlindingError(f"no pairings are assigned to rater {rater_id}")
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    title = html_escape(data["trial_title"])
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{title} · blind judging packet</title>
<style>
:root{{--ink:#121619;--muted:#657176;--paper:#eeeae0;--panel:#fffdf8;--navy:#142d36;--mint:#65d9c3;
--amber:#d89c50;--line:#d5cfc1}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.55 system-ui,sans-serif}}header{{position:sticky;top:0;z-index:3;background:var(--navy);color:white;
padding:14px max(20px,calc((100vw - 1400px)/2));display:flex;justify-content:space-between;align-items:center}}
header b{{letter-spacing:.08em}}header span{{font-size:12px;color:#b9ceca}}main{{max-width:1400px;margin:auto;padding:30px 20px 100px}}
.notice{{background:#e1f0eb;border:1px solid #b9d8cf;border-radius:10px;padding:14px;margin-bottom:20px}}h1{{font:700 31px Georgia,serif}}
.task{{background:var(--panel);border:1px solid var(--line);padding:20px;border-radius:12px;margin-bottom:18px}}.task h2{{margin:0 0 9px}}
.prompt{{white-space:pre-wrap;border-left:4px solid var(--amber);padding-left:14px}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.answer{{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}}.answer h3{{margin:0;padding:12px 16px;background:#e2ded3}}
.content{{white-space:pre-wrap;padding:18px;min-height:240px}}.scores{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:20px 0}}
.score-card{{background:var(--panel);border:1px solid var(--line);padding:16px;border-radius:12px}}label{{display:block;margin:9px 0;font-size:12px}}
select,textarea{{width:100%;padding:9px;border:1px solid #aaa498;border-radius:7px;background:white}}.choice{{display:flex;gap:8px;flex-wrap:wrap}}
.choice label{{padding:10px 15px;border:1px solid #aaa498;border-radius:99px;background:white;font-weight:700}}button{{border:0;border-radius:8px;
padding:12px 17px;background:var(--navy);color:white;font-weight:800;cursor:pointer}}button.secondary{{background:white;color:var(--ink);border:1px solid #aaa498}}
.footer{{position:fixed;bottom:0;left:0;right:0;background:#f7f4ec;border-top:1px solid var(--line);padding:12px;
display:flex;justify-content:center;gap:10px}}.hidden{{display:none}}.progress{{font-size:12px;color:var(--muted)}}@media(max-width:850px){{.columns,.scores{{grid-template-columns:1fr}}}}
</style></head><body><header><b>FRONTIERTRIALS</b><span>BLIND PACKET · {html_escape(data["rater"]["label"])}</span></header>
<main><h1>{title}</h1><div class="notice">{html_escape(data["instructions"])}</div><div id="mount"></div></main>
<div class="footer"><button class="secondary" id="prev">Previous</button><span class="progress" id="progress"></span>
<button id="next">Save &amp; next</button><button id="download" class="hidden">Download ballots</button></div>
<script id="packet-data" type="application/json">{serialized}</script><script>
const data=JSON.parse(document.querySelector("#packet-data").textContent), state={{index:0,ballots:{{}}}};
const mount=document.querySelector("#mount"),progress=document.querySelector("#progress");
function esc(s){{return String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function options(){{return '<option value="">Select</option>'+[1,2,3,4,5].map(x=>`<option>${{x}}</option>`).join('')}}
function render(){{const x=data.items[state.index], saved=state.ballots[x.pairing_id]||{{}};
mount.innerHTML=`<section class="task"><h2>${{esc(x.task.title)}}</h2><div class="prompt">${{esc(x.task.prompt)}}</div></section>
<div class="columns"><article class="answer"><h3>Left · ${{esc(x.left.alias)}}</h3><div class="content">${{esc(x.left.content)}}</div></article>
<article class="answer"><h3>Right · ${{esc(x.right.alias)}}</h3><div class="content">${{esc(x.right.content)}}</div></article></div>
<div class="scores"><section class="score-card"><h3>Score left independently</h3>${{x.rubric.criteria.map(c=>`<label>${{esc(c.label)}}<select data-side="left" data-id="${{c.id}}">${{options()}}</select></label>`).join('')}}</section>
<section class="score-card"><h3>Score right independently</h3>${{x.rubric.criteria.map(c=>`<label>${{esc(c.label)}}<select data-side="right" data-id="${{c.id}}">${{options()}}</select></label>`).join('')}}</section></div>
<section class="task"><h3>Overall preference</h3><div class="choice">${{['left','right','tie','abstain'].map(v=>`<label><input type="radio" name="choice" value="${{v}}"> ${{v}}</label>`).join('')}}</div>
<label>Confidence (1 low · 5 high)<select id="confidence">${{options()}}</select></label><label>Decision rationale<textarea id="rationale" rows="4"></textarea></label>
<label>Flags (comma separated)<textarea id="flags" rows="2"></textarea></label></section>`;
if(saved.choice)document.querySelector(`[name=choice][value="${{saved.choice}}"]`).checked=true;
document.querySelector('#confidence').value=saved.confidence||'';document.querySelector('#rationale').value=saved.rationale||'';
document.querySelector('#flags').value=(saved.flags||[]).join(', ');
for(const side of ['left','right'])for(const [id,val] of Object.entries(saved[side+'_scores']||{{}}))
document.querySelector(`[data-side="${{side}}"][data-id="${{id}}"]`).value=val;
progress.textContent=`${{state.index+1}} / ${{data.items.length}}`;document.querySelector('#prev').disabled=state.index===0;
document.querySelector('#next').classList.toggle('hidden',state.index===data.items.length-1);
document.querySelector('#download').classList.toggle('hidden',state.index!==data.items.length-1)}}
function collect(){{const x=data.items[state.index],choice=document.querySelector('[name=choice]:checked')?.value;
const confidence=Number(document.querySelector('#confidence').value),rationale=document.querySelector('#rationale').value.trim();
if(!choice||!confidence||!rationale){{alert('Choose a preference, confidence, and rationale.');return false}}
const ballot={{id:`ballot-${{data.rater.id}}-${{String(state.index+1).padStart(3,'0')}}`,pairing_id:x.pairing_id,
rater_id:data.rater.id,choice,confidence,rationale,flags:document.querySelector('#flags').value.split(',').map(x=>x.trim()).filter(Boolean),
left_scores:{{}},right_scores:{{}},recorded_at:new Date().toISOString()}};
for(const el of document.querySelectorAll('[data-side]')){{if(!el.value){{alert('Complete every criterion score.');return false}}
ballot[el.dataset.side+'_scores'][el.dataset.id]=Number(el.value)}}state.ballots[x.pairing_id]=ballot;return true}}
document.querySelector('#prev').onclick=()=>{{collect();state.index--;render()}};
document.querySelector('#next').onclick=()=>{{if(collect()){{state.index++;render()}}}};
document.querySelector('#download').onclick=()=>{{if(!collect())return;const blob=new Blob([JSON.stringify({{format:'frontiertrials-ballots-v1',
rater_id:data.rater.id,ballots:Object.values(state.ballots)}},null,2)],{{type:'application/json'}});const a=document.createElement('a');
a.href=URL.createObjectURL(blob);a.download=`ballots-${{data.rater.id}}.json`;a.click();URL.revokeObjectURL(a.href)}};render();
</script></body></html>"""
    destination.write_text(html, encoding="utf-8", newline="\n")
    return destination
