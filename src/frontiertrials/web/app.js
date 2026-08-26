"use strict";

const STORAGE_KEY = "frontiertrials.personal.v1";
const FORMAT = "frontiertrials-personal-v1";
const MAX_CANDIDATES = 4;
const ALIASES = ["Aster", "Cedar", "Dahlia", "Kestrel"];

const app = {
  candidates: [],
  trial: null,
  pairIndex: 0,
  saved: false,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function focusElement(element) {
  if (!element) return;
  element.focus({ preventScroll: true });
  element.scrollIntoView({ behavior: "auto", block: "center" });
}

function makeId(prefix = "id") {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return `${prefix}-${globalThis.crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function shuffled(values) {
  const copy = [...values];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const secureRandom = globalThis.crypto && typeof globalThis.crypto.getRandomValues === "function";
    const target = secureRandom
      ? (() => {
          const random = new Uint32Array(1);
          globalThis.crypto.getRandomValues(random);
          return random[0] % (index + 1);
        })()
      : Math.floor(Math.random() * (index + 1));
    [copy[index], copy[target]] = [copy[target], copy[index]];
  }
  return copy;
}

function textLength(value) {
  return [...value.trim()].length;
}

function lengthLabel(value) {
  return `${textLength(value).toLocaleString()} characters`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "Not recorded";
  return `USD ${Number(value).toFixed(2)} / month`;
}

function latency(value) {
  return value === null || value === undefined || Number.isNaN(value)
    ? "Not recorded"
    : `${Number(value).toFixed(1)} s`;
}

function readHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeHistory(history) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function createCandidate(values = {}) {
  if (app.candidates.length >= MAX_CANDIDATES) return;
  const candidate = {
    id: makeId("candidate"),
    name: values.name || "",
    price: values.price ?? "",
    response: values.response || "",
    latency: values.latency ?? "",
  };
  app.candidates.push(candidate);
  renderCandidates();
}

function syncCandidates() {
  $$(".candidate-card", $("#candidate-grid")).forEach((card) => {
    const candidate = app.candidates.find((item) => item.id === card.dataset.candidateId);
    if (!candidate) return;
    candidate.name = $(".candidate-name", card).value.trim();
    candidate.price = $(".candidate-price", card).value;
    candidate.latency = $(".candidate-latency", card).value;
    candidate.response = $(".candidate-response", card).value;
  });
}

function renderCandidates() {
  const grid = $("#candidate-grid");
  const template = $("#candidate-template");
  grid.textContent = "";
  app.candidates.forEach((candidate, index) => {
    const node = template.content.cloneNode(true);
    const card = $(".candidate-card", node);
    card.dataset.candidateId = candidate.id;
    const productLabel = `Product ${String.fromCharCode(65 + index)}`;
    const candidateTitle = `candidate-${candidate.id}-title`;
    card.setAttribute("aria-labelledby", candidateTitle);
    $(".candidate-number", card).id = candidateTitle;
    $(".candidate-number", card).textContent = productLabel;
    $(".candidate-name", card).value = candidate.name;
    $(".candidate-price", card).value = candidate.price;
    $(".candidate-latency", card).value = candidate.latency;
    $(".candidate-response", card).value = candidate.response;
    $(".character-count", card).textContent = `${textLength(candidate.response).toLocaleString()} characters`;
    $(".remove-candidate", card).hidden = app.candidates.length <= 2;
    $(".remove-candidate", card).setAttribute("aria-label", `Remove ${candidate.name || productLabel}`);
    $(".remove-candidate", card).addEventListener("click", () => {
      syncCandidates();
      app.candidates = app.candidates.filter((item) => item.id !== candidate.id);
      renderCandidates();
      focusElement($("#add-candidate"));
    });
    $(".candidate-response", card).addEventListener("input", (event) => {
      $(".character-count", card).textContent = `${textLength(event.target.value).toLocaleString()} characters`;
    });
    grid.append(node);
  });
  $("#add-candidate").disabled = app.candidates.length >= MAX_CANDIDATES;
}

const BULK_SPLIT = /^\s*(?:={3,}|-{3,}|#{3,}|\*{3,}|_{3,})\s*(.*)$/;
const PRICE_RE = /\$\s?(\d+(?:\.\d+)?)\s*\/?\s*(?:mo|month|monthly|m\b)?/i;

function parseBulkHeader(line) {
  const parts = line.split("|").map((part) => part.trim());
  const name = parts[0] || "";
  let price = "";
  let latency = "";
  parts.slice(1).forEach((part) => {
    const priceMatch = part.match(PRICE_RE);
    if (priceMatch && !price) {
      price = priceMatch[1];
      return;
    }
    const latencyMatch = part.match(/(\d+(?:\.\d+)?)\s*s\b/i);
    if (latencyMatch && !latency) latency = latencyMatch[1];
  });
  return { name, price, latency };
}

function parseBulkText(raw) {
  const lines = raw.replace(/\r\n?/g, "\n").split("\n");
  const blocks = [];
  let current = null;
  lines.forEach((line) => {
    const split = line.match(BULK_SPLIT);
    if (split) {
      if (current && (current.name || current.body.trim())) blocks.push(current);
      current = { name: "", price: "", latency: "", body: "" };
      if (split[1]) Object.assign(current, parseBulkHeader(split[1]));
      return;
    }
    if (!current) current = { name: "", price: "", latency: "", body: "" };
    if (!current.name && !current.body.trim() && line.trim()) current.name = line.trim();
    else current.body += `${line}\n`;
  });
  if (current && (current.name || current.body.trim())) blocks.push(current);
  return blocks
    .map((block) => ({ ...block, body: block.body.trim() }))
    .filter((block) => block.body || block.name);
}

function applyBulkBlocks(blocks) {
  if (blocks.length < 2 || blocks.length > MAX_CANDIDATES) {
    return { ok: false, message: `Found ${blocks.length} answer${blocks.length === 1 ? "" : "s"}. Separate 2 to ${MAX_CANDIDATES} products with a === line.` };
  }
  const names = blocks.map((block) => block.name);
  if (names.some((name) => !name)) {
    return { ok: false, message: "Every block needs a product name on its first line (or after ===)." };
  }
  const lower = names.map((name) => name.toLowerCase());
  if (new Set(lower).size !== lower.length) {
    return { ok: false, message: "Use a different product name for each block." };
  }
  app.candidates = blocks.map((block) => ({
    id: makeId("candidate"),
    name: block.name,
    price: block.price,
    latency: block.latency,
    response: block.body,
  }));
  renderCandidates();
  return { ok: true, message: `Filled ${blocks.length} products. Check the answers, then start the blind review.` };
}

function bulkStatus(message, isError = false) {
  const status = $("#bulk-status");
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function fillFromBulkText() {
  const raw = $("#bulk-text").value;
  if (!raw.trim()) {
    bulkStatus("Paste all answers first.", true);
    focusElement($("#bulk-text"));
    return;
  }
  const result = applyBulkBlocks(parseBulkText(raw));
  bulkStatus(result.message, !result.ok);
  if (result.ok) focusElement($("#start-review"));
}

function readFileAsText(file) {
  if (globalThis.File && file instanceof File && file.text) return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

async function fillFromBulkFile(file) {
  if (!file) return;
  let raw = "";
  try {
    raw = await readFileAsText(file);
  } catch {
    bulkStatus("That file could not be read as text.", true);
    return;
  }
  if (/\.json$/i.test(file.name)) {
    bulkStatus("History JSON belongs in History → Import JSON. Paste answers as text here.", true);
    return;
  }
  $("#bulk-text").value = raw;
  fillFromBulkText();
}

function captureValues() {
  syncCandidates();
  return {
    title: $("#task-title").value.trim(),
    category: $("#task-category").value,
    prompt: $("#task-prompt").value.trim(),
    candidates: app.candidates.map((candidate) => ({
      id: candidate.id,
      name: candidate.name.trim(),
      price: candidate.price === "" ? null : Number(candidate.price),
      latency: candidate.latency === "" ? null : Number(candidate.latency),
      response: candidate.response.trim(),
    })),
  };
}

function captureError(message, selector, index = 0) {
  return { message, target: $$(selector)[index] };
}

function validateCapture(value) {
  if (!value.title) return captureError("Give this task a short title.", "#task-title");
  if (!value.prompt) return captureError("Paste the exact prompt or task.", "#task-prompt");
  if (value.candidates.length < 2) return { message: "Add at least two products.", target: $("#add-candidate") };
  const missingName = value.candidates.findIndex((candidate) => !candidate.name);
  if (missingName >= 0) return captureError("Name every product or plan.", ".candidate-name", missingName);
  const duplicateName = value.candidates.findIndex((candidate, index, candidates) =>
    candidates.findIndex((other) => other.name.toLowerCase() === candidate.name.toLowerCase()) !== index);
  if (duplicateName >= 0) return captureError("Use a different name for each product.", ".candidate-name", duplicateName);
  const missingResponse = value.candidates.findIndex((candidate) => !candidate.response);
  if (missingResponse >= 0) return captureError("Paste the complete answer from every product.", ".candidate-response", missingResponse);
  const invalidPrice = value.candidates.findIndex((candidate) => candidate.price !== null && candidate.price < 0);
  if (invalidPrice >= 0) return captureError("Monthly prices cannot be negative.", ".candidate-price", invalidPrice);
  const invalidLatency = value.candidates.findIndex((candidate) => candidate.latency !== null && candidate.latency < 0);
  if (invalidLatency >= 0) return captureError("Observed latency cannot be negative.", ".candidate-latency", invalidLatency);
  return { message: "", target: null };
}

function clearCaptureErrors() {
  $$('[aria-describedby="capture-message"]').forEach((element) => element.removeAttribute("aria-describedby"));
  $$('[aria-invalid="true"]').forEach((element) => element.removeAttribute("aria-invalid"));
}

function buildPairs(candidates) {
  const pairs = [];
  for (let left = 0; left < candidates.length; left += 1) {
    for (let right = left + 1; right < candidates.length; right += 1) {
      const pair = [candidates[left].id, candidates[right].id];
      if (pairs.length % 2 === 1) pair.reverse();
      pairs.push({ id: makeId("pair"), leftId: pair[0], rightId: pair[1] });
    }
  }
  return shuffled(pairs);
}

function startReview() {
  const value = captureValues();
  $("#capture-status").textContent = "";
  clearCaptureErrors();
  const error = validateCapture(value);
  $("#capture-message").textContent = error.message;
  if (error.message) {
    error.target?.setAttribute("aria-invalid", "true");
    error.target?.setAttribute("aria-describedby", "capture-message");
    focusElement(error.target);
    return;
  }
  const aliases = shuffled(ALIASES).slice(0, value.candidates.length);
  app.trial = {
    format: FORMAT,
    id: makeId("trial"),
    createdAt: new Date().toISOString(),
    title: value.title,
    category: value.category,
    prompt: value.prompt,
    candidates: value.candidates.map((candidate, index) => ({ ...candidate, alias: aliases[index] })),
    pairs: buildPairs(value.candidates),
    votes: [],
  };
  app.pairIndex = 0;
  app.saved = false;
  renderReview();
  setStage("review");
}

function setStage(stage) {
  $$("[data-stage]").forEach((panel) => {
    const active = panel.dataset.stage === stage;
    panel.hidden = !active;
    panel.classList.toggle("active", active);
  });
  const order = ["capture", "review", "result"];
  const current = order.indexOf(stage);
  $$(".stepper li").forEach((item, index) => {
    item.classList.toggle("active", index === current);
    item.classList.toggle("complete", index < current);
    if (index === current) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
  focusElement($(`#${stage}-title`));
}

function candidateById(id) {
  return app.trial.candidates.find((candidate) => candidate.id === id);
}

function clearReviewFields() {
  $("#review-note").value = "";
  $$('input[name="reason"]').forEach((input) => { input.checked = false; });
}

function renderReview() {
  const pair = app.trial.pairs[app.pairIndex];
  const left = candidateById(pair.leftId);
  const right = candidateById(pair.rightId);
  $("#review-progress").textContent = `Comparison ${app.pairIndex + 1} of ${app.trial.pairs.length}`;
  $("#review-task-title").textContent = app.trial.title;
  $("#review-prompt").textContent = app.trial.prompt;
  $("#left-alias").textContent = left.alias;
  $("#right-alias").textContent = right.alias;
  $("#left-answer").textContent = left.response;
  $("#right-answer").textContent = right.response;
  $("#left-latency").textContent = latency(left.latency);
  $("#right-latency").textContent = latency(right.latency);
  $("#left-length").textContent = lengthLabel(left.response);
  $("#right-length").textContent = lengthLabel(right.response);
  clearReviewFields();
}

function castVote(choice) {
  const pair = app.trial.pairs[app.pairIndex];
  const reasons = $$('input[name="reason"]:checked').map((input) => input.value);
  app.trial.votes.push({
    pairId: pair.id,
    leftId: pair.leftId,
    rightId: pair.rightId,
    choice,
    winnerId: choice === "left" ? pair.leftId : choice === "right" ? pair.rightId : null,
    reasons,
    note: $("#review-note").value.trim(),
  });
  app.pairIndex += 1;
  if (app.pairIndex < app.trial.pairs.length) {
    renderReview();
    focusElement($("#review-title"));
    return;
  }
  renderResult();
  setStage("result");
}

function summarize(trial) {
  const rows = trial.candidates.map((candidate) => ({
    ...candidate,
    wins: 0,
    losses: 0,
    ties: 0,
    skipped: 0,
    decisions: 0,
    points: 0,
  }));
  const byId = Object.fromEntries(rows.map((row) => [row.id, row]));
  trial.votes.forEach((vote) => {
    const left = byId[vote.leftId];
    const right = byId[vote.rightId];
    if (vote.choice === "skip") {
      left.skipped += 1;
      right.skipped += 1;
      return;
    }
    left.decisions += 1;
    right.decisions += 1;
    if (vote.choice === "tie") {
      left.ties += 1;
      right.ties += 1;
      left.points += .5;
      right.points += .5;
      return;
    }
    const winner = byId[vote.winnerId];
    const loser = vote.winnerId === vote.leftId ? right : left;
    winner.wins += 1;
    winner.points += 1;
    loser.losses += 1;
  });
  rows.forEach((row) => {
    row.score = row.decisions ? row.points / row.decisions : 0;
  });
  return rows.sort((a, b) => b.score - a.score || b.wins - a.wins || a.name.localeCompare(b.name));
}

function resultCall(rows, trial) {
  const decisive = trial.votes.filter((vote) => vote.choice !== "skip");
  if (!decisive.length) {
    return {
      title: "No product is favored.",
      copy: "Every comparison was skipped. Record a task that you can judge or add a clearer decision criterion.",
    };
  }
  const leaders = rows.filter((row) => row.score === rows[0].score);
  if (leaders.length > 1) {
    return {
      title: "This task does not separate the leaders.",
      copy: `${leaders.map((item) => item.name).join(" and ")} share the highest pairwise score. Treat that as a tie, not hidden precision.`,
    };
  }
  return {
    title: `${rows[0].name} was preferred on this task.`,
    copy: `The result covers ${decisive.length} judged pair${decisive.length === 1 ? "" : "s"} in ${trial.category}. Save varied tasks before changing a subscription.`,
  };
}

function scoreCell(row) {
  const cell = document.createElement("td");
  cell.className = "score-cell";
  const wrap = document.createElement("div");
  wrap.className = "score-bar";
  const track = document.createElement("i");
  const fill = document.createElement("b");
  fill.style.width = `${Math.round(row.score * 100)}%`;
  track.append(fill);
  const value = document.createElement("strong");
  value.textContent = `${Math.round(row.score * 100)}%`;
  wrap.append(track, value);
  cell.append(wrap);
  return cell;
}

function renderResult() {
  const rows = summarize(app.trial);
  const call = resultCall(rows, app.trial);
  $("#result-date").textContent = new Date(app.trial.createdAt).toLocaleDateString();
  $("#decision-title").textContent = call.title;
  $("#decision-copy").textContent = call.copy;
  const body = $("#result-body");
  body.textContent = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    const product = document.createElement("td");
    product.innerHTML = `<strong></strong><br><small></small>`;
    $("strong", product).textContent = row.name;
    $("small", product).textContent = `Previously shown as ${row.alias}`;
    const record = document.createElement("td");
    record.textContent = `${row.wins} W · ${row.ties} T · ${row.losses} L`;
    const price = document.createElement("td");
    price.textContent = money(row.price);
    const observed = document.createElement("td");
    observed.textContent = latency(row.latency);
    tr.append(product, scoreCell(row), record, price, observed);
    body.append(tr);
  });
  $("#save-status").textContent = "";
  $("#save-result").disabled = false;
}

function saveResult() {
  if (app.saved) {
    $("#save-status").textContent = "This comparison is already in local history.";
    return;
  }
  const history = readHistory();
  history.push(app.trial);
  writeHistory(history);
  app.saved = true;
  $("#save-result").disabled = true;
  $("#save-status").textContent = "Saved in this browser. Export JSON for a portable backup.";
  renderHistory();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function reportHtml(trial) {
  const rows = summarize(trial);
  const call = resultCall(rows, trial);
  const rowHtml = rows.map((row) => `
    <tr>
      <td><strong>${escapeHtml(row.name)}</strong></td>
      <td>${Math.round(row.score * 100)}%</td>
      <td>${row.wins} W · ${row.ties} T · ${row.losses} L</td>
      <td>${escapeHtml(money(row.price))}</td>
      <td>${escapeHtml(latency(row.latency))}</td>
    </tr>`).join("");
  const voteHtml = trial.votes.map((vote) => {
    const left = trial.candidates.find((candidate) => candidate.id === vote.leftId);
    const right = trial.candidates.find((candidate) => candidate.id === vote.rightId);
    const choice = vote.choice === "left" ? left.name : vote.choice === "right" ? right.name : vote.choice;
    return `<li><strong>${escapeHtml(left.name)} vs ${escapeHtml(right.name)}:</strong> ${escapeHtml(choice)}${vote.reasons.length ? ` · ${escapeHtml(vote.reasons.join(", "))}` : ""}${vote.note ? `<br>${escapeHtml(vote.note)}` : ""}</li>`;
  }).join("");
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escapeHtml(trial.title)} · FrontierTrials</title>
<style>
body{max-width:920px;margin:0 auto;padding:48px 24px;background:#f4f1e8;color:#17232a;font:16px/1.65 system-ui,sans-serif}
h1,h2{font-family:Georgia,serif;letter-spacing:-.02em}.k{color:#965247;font:700 11px ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase}
.box{margin:24px 0;padding:20px;border:1px solid #c9c5ba;background:#fffdf7}.call{border-top:5px solid #a47a36}
table{width:100%;border-collapse:collapse;background:#fff}th,td{padding:10px;border:1px solid #c9c5ba;text-align:left;font-size:13px}
th{background:#e9e6dd}.limit{color:#637078;font-size:13px}pre{white-space:pre-wrap;font:14px/1.55 system-ui,sans-serif}
@media print{body{background:#fff;padding:0}.box{break-inside:avoid}}
</style></head><body>
<p class="k">FrontierTrials · Personal result · ${escapeHtml(new Date(trial.createdAt).toLocaleDateString())}</p>
<h1>${escapeHtml(trial.title)}</h1>
<div class="box"><p class="k">Recorded task</p><pre>${escapeHtml(trial.prompt)}</pre></div>
<div class="box call"><p class="k">Decision note</p><h2>${escapeHtml(call.title)}</h2><p>${escapeHtml(call.copy)}</p></div>
<table><thead><tr><th>Product</th><th>Pairwise score</th><th>Record</th><th>Monthly price (USD)</th><th>Latency</th></tr></thead><tbody>${rowHtml}</tbody></table>
<div class="box"><p class="k">Recorded decisions</p><ul>${voteHtml}</ul></div>
<p class="limit"><strong>Boundary.</strong> This result describes one recorded task, interface, date, and reviewer. It is not a universal model ranking. Masking labels reduces visible brand cues but cannot erase remembered identities.</p>
<p class="limit">Generated locally by FrontierTrials. No API or hosted judge was used.</p>
</body></html>`;
}

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
}

function safeName(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/gu, "-").replace(/^-|-$/gu, "") || "comparison";
}

function downloadReport() {
  downloadFile(`${safeName(app.trial.title)}-frontiertrials.html`, reportHtml(app.trial), "text/html;charset=utf-8");
}

function resetCapture() {
  app.trial = null;
  app.pairIndex = 0;
  app.saved = false;
  $("#task-title").value = "";
  $("#task-prompt").value = "";
  $("#task-category").value = "research";
  app.candidates = [];
  createCandidate();
  createCandidate();
  $("#capture-message").textContent = "";
  $("#capture-status").textContent = "";
  setStage("capture");
}

function aggregateHistory(history) {
  const aggregate = new Map();
  history.forEach((trial) => {
    const rows = summarize(trial);
    rows.forEach((row) => {
      const key = row.name.trim().toLowerCase();
      if (!aggregate.has(key)) {
        aggregate.set(key, {
          name: row.name,
          wins: 0,
          losses: 0,
          ties: 0,
          decisions: 0,
          points: 0,
          price: row.price,
          categories: new Set(),
        });
      }
      const item = aggregate.get(key);
      item.name = row.name;
      item.wins += row.wins;
      item.losses += row.losses;
      item.ties += row.ties;
      item.decisions += row.decisions;
      item.points += row.points;
      if (row.price !== null) item.price = row.price;
      item.categories.add(trial.category);
    });
  });
  return [...aggregate.values()]
    .map((item) => ({ ...item, score: item.decisions ? item.points / item.decisions : 0 }))
    .sort((a, b) => b.score - a.score || b.wins - a.wins || a.name.localeCompare(b.name));
}

function overallCall(rows, history) {
  const decisions = history.reduce((sum, trial) => sum + trial.votes.filter((vote) => vote.choice !== "skip").length, 0);
  if (!rows.length) return "No saved comparisons yet.";
  if (decisions < 5) return `Early signal only: ${rows[0].name} currently leads after ${decisions} decision${decisions === 1 ? "" : "s"}.`;
  const tied = rows.length > 1 && rows[0].score === rows[1].score;
  if (tied) return `No clear leader after ${decisions} decisions. Add tasks from underrepresented categories.`;
  return `${rows[0].name} leads your personal record after ${decisions} decisions. Inspect category coverage before changing a subscription.`;
}

function renderHistory() {
  const history = readHistory();
  const rows = aggregateHistory(history);
  const decisionCount = history.reduce((sum, trial) => sum + trial.votes.filter((vote) => vote.choice !== "skip").length, 0);
  $("#history-trials").textContent = history.length;
  $("#history-decisions").textContent = decisionCount;
  $("#history-products").textContent = rows.length;
  $("#history-call").textContent = overallCall(rows, history);

  const ranking = $("#history-ranking");
  ranking.textContent = "";
  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.textContent = "No saved evidence yet.";
    tr.append(td);
    ranking.append(tr);
  } else {
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const product = document.createElement("td");
      product.textContent = row.name;
      const record = document.createElement("td");
      record.textContent = `${row.wins} W · ${row.ties} T · ${row.losses} L`;
      const categories = document.createElement("td");
      categories.textContent = [...row.categories].sort().join(", ");
      const price = document.createElement("td");
      price.textContent = money(row.price);
      tr.append(product, scoreCell(row), record, categories, price);
      ranking.append(tr);
    });
  }

  const list = $("#trial-list");
  list.textContent = "";
  history.slice().reverse().forEach((trial) => {
    const rowsForTrial = summarize(trial);
    const call = resultCall(rowsForTrial, trial);
    const item = document.createElement("article");
    item.className = "trial-row";
    const copy = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = trial.title;
    const meta = document.createElement("p");
    meta.textContent = `${new Date(trial.createdAt).toLocaleDateString()} · ${trial.category} · ${trial.candidates.length} products`;
    copy.append(title, meta);
    const aside = document.createElement("aside");
    const result = document.createElement("strong");
    result.textContent = call.title;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete";
    remove.setAttribute("aria-label", `Delete ${trial.title}`);
    remove.addEventListener("click", () => {
      writeHistory(readHistory().filter((itemInHistory) => itemInHistory.id !== trial.id));
      renderHistory();
      $("#history-status").textContent = `Deleted ${trial.title}.`;
      focusElement($("#trial-list button") || $("#history-title"));
    });
    aside.append(result, remove);
    item.append(copy, aside);
    list.append(item);
  });
  $("#history-empty").hidden = history.length > 0;
}

function showView(name) {
  $$("[data-view]").forEach((view) => {
    const active = view.dataset.view === name;
    view.hidden = !active;
    view.classList.toggle("active", active);
  });
  $$("[data-view-target]").forEach((button) => {
    const active = button.dataset.viewTarget === name;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (name === "history") renderHistory();
  focusElement(name === "history" ? $("#history-title") : $("#capture-title"));
}

function loadExample() {
  $("#task-title").value = "Choose a useful explanation";
  $("#task-category").value = "engineering";
  $("#task-prompt").value = "Explain why a low-pass RC filter attenuates high frequencies, and give one practical design implication.";
  app.candidates = [];
  createCandidate({
    name: "Northstar Plus",
    price: "20",
    latency: "18",
    response: "At high frequency, the capacitor's reactance becomes small, so more of the input signal is shunted to ground. The output across the capacitor therefore falls as frequency rises. The cutoff is fc = 1/(2πRC). In practice, choose R and C for the desired cutoff while checking that the load impedance is much larger than R; otherwise the load shifts the response.",
  });
  createCandidate({
    name: "Harbor Pro",
    price: "25",
    latency: "12",
    response: "An RC low-pass filter passes slowly changing signals and reduces rapid changes. The capacitor charges and discharges through the resistor, which smooths the voltage. Its nominal cutoff frequency is 1/(2πRC). A larger resistor or capacitor lowers the cutoff, but large component values can increase noise, loading, leakage, or settling-time problems.",
  });
  $("#capture-message").textContent = "";
  $("#capture-status").textContent = "Fictional example loaded. Replace it with exact outputs for a real decision.";
}

function exportHistory() {
  const payload = { format: FORMAT, exportedAt: new Date().toISOString(), trials: readHistory() };
  downloadFile("frontiertrials-personal-history.json", JSON.stringify(payload, null, 2), "application/json");
}

async function importHistory(event) {
  const [file] = event.target.files;
  event.target.value = "";
  if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    if (payload.format !== FORMAT || !Array.isArray(payload.trials)) throw new Error("Unsupported format");
    const existing = readHistory();
    const byId = new Map(existing.map((trial) => [trial.id, trial]));
    payload.trials.forEach((trial) => {
      if (trial && trial.format === FORMAT && trial.id && Array.isArray(trial.candidates) && Array.isArray(trial.votes)) {
        byId.set(trial.id, trial);
      }
    });
    writeHistory([...byId.values()]);
    renderHistory();
    $("#history-status").textContent = `Imported ${payload.trials.length} comparison${payload.trials.length === 1 ? "" : "s"}. Existing IDs were updated.`;
  } catch {
    $("#history-status").textContent = "That file is not a valid FrontierTrials personal-history export.";
  }
}

function init() {
  createCandidate();
  createCandidate();
  renderHistory();

  $("#add-candidate").addEventListener("click", () => {
    syncCandidates();
    createCandidate();
    focusElement($$(".candidate-name").at(-1));
  });
  $("#load-example").addEventListener("click", loadExample);
  $("#parse-bulk").addEventListener("click", fillFromBulkText);
  $("#bulk-file").addEventListener("change", (event) => {
    fillFromBulkFile(event.target.files && event.target.files[0]);
    event.target.value = "";
  });
  const dropZone = $("#bulk-drop");
  dropZone.addEventListener("click", () => $("#bulk-file").click());
  dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      $("#bulk-file").click();
    }
  });
  ["dragenter", "dragover"].forEach((type) => {
    dropZone.addEventListener(type, (event) => {
      event.preventDefault();
      dropZone.classList.add("dragover");
    });
  });
  ["dragleave", "drop"].forEach((type) => {
    dropZone.addEventListener(type, (event) => {
      event.preventDefault();
      dropZone.classList.remove("dragover");
    });
  });
  dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
    if (file) fillFromBulkFile(file);
  });
  $("#start-review").addEventListener("click", startReview);
  $("#exit-review").addEventListener("click", () => setStage("capture"));
  $$("[data-vote]").forEach((button) => button.addEventListener("click", () => castVote(button.dataset.vote)));
  $("#save-result").addEventListener("click", saveResult);
  $("#download-report").addEventListener("click", downloadReport);
  $("#new-comparison").addEventListener("click", resetCapture);
  $$("[data-view-target]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewTarget)));
  $("#export-history").addEventListener("click", exportHistory);
  $("#import-history").addEventListener("change", importHistory);
  $("#clear-history").addEventListener("click", () => {
    if (confirm("Delete every FrontierTrials comparison stored in this browser? Export first if you need a backup.")) {
      localStorage.removeItem(STORAGE_KEY);
      renderHistory();
      $("#history-status").textContent = "Local history cleared.";
    }
  });
}

document.addEventListener("DOMContentLoaded", init);
