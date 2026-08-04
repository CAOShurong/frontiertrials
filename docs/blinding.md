# Blinding and order balance

## What is hidden

When a trial is frozen, each candidate receives a neutral word alias. Pairings store anonymous
left and right labels. Judging packets include only the prompt, rubric, response content, and
aliases.

The main workspace still contains candidate IDs. Give raters packets, not the workspace.

## Identity leakage

A response may name its provider or model, reproduce a branded refusal, use a recognizable house
style, or include a link that reveals origin. FrontierTrials scans for a small public list of
identity terms and raises warnings. It never edits the response because editing would break exact
capture.

Blinding reduces one source of bias; it cannot guarantee that an experienced reviewer cannot infer
identity.

## Left/right order

For each repeated candidate pair, FrontierTrials alternates which candidate appears on the left.
When every pair appears an even number of times, each candidate receives equal left exposure. With
an odd number of tasks or missing pairings, exact equality may be impossible; the audit reports the
observed counts.

Order is derived from a secret seed so rerunning the same complete trial with the same seed
produces the same aliases, orientation, and assignments.

## Seed handling

Use `--seed-file` for real trials so the secret does not enter shell history. The workspace stores
only a fingerprint and a reveal map. The reveal map is excluded from the evidence seal because a
sealed public packet should not require disclosure of the secret.

## Reveal

The CLI refuses to reveal a frozen trial with zero ballots. It does not require every assigned
ballot because interrupted studies sometimes need analysis; the audit warns when a revealed trial
is incomplete.

