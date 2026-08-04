<div align="center">
  <img src="docs/assets/hero.svg" alt="FrontierTrials turns web-app outputs into blind, reviewable model evaluations" width="100%">

  # FrontierTrials

  **Run reproducible, blind evaluations of AI web-app outputs — no API keys required.**

  [![CI](https://github.com/CAOShurong/frontiertrials/actions/workflows/ci.yml/badge.svg)](https://github.com/CAOShurong/frontiertrials/actions/workflows/ci.yml)
  [![Pages](https://github.com/CAOShurong/frontiertrials/actions/workflows/pages.yml/badge.svg)](https://caoshurong.github.io/frontiertrials/)
  [![Python](https://img.shields.io/badge/Python-3.11%2B-132d36)](https://www.python.org/)
  [![Runtime dependencies](https://img.shields.io/badge/runtime_dependencies-0-167e75)](#why-no-api)
  [![License: MIT](https://img.shields.io/badge/license-MIT-d69c4f)](LICENSE)
</div>

FrontierTrials is a local-first evaluation workbench for people who use AI through subscription
web apps, desktop apps, or other interfaces that do not expose an API. Capture exact responses,
freeze their hashes, build balanced blind comparisons, distribute self-contained judging packets,
import human ballots, triage contested cases while identities remain hidden, diagnose panel
sensitivity, reveal identities, and publish a portable report.

The application never logs into a provider, automates a consumer interface, calls a model, or
pretends that one leaderboard measures general intelligence. You collect outputs under the terms
that apply to your accounts; FrontierTrials makes the comparison auditable.

## Explore the complete fictional trial

- [Project website](https://caoshurong.github.io/frontiertrials/)
- [Revealed interactive report](https://caoshurong.github.io/frontiertrials/demo/trial-report.html)
- [Offline blind judging packet](https://caoshurong.github.io/frontiertrials/demo/reviewer-one.html)
- [Blind adjudication queue](https://caoshurong.github.io/frontiertrials/demo/adjudication.md)
- [Ranking CSV](examples/demo/reports/ranking.csv)
- [Protocol snapshot](examples/demo/reports/protocol.md)

Every candidate, provider, response, ballot, timing, and result in the demonstration is fictional.
It demonstrates mechanics, not the performance of a real product.

## Why this exists

Public leaderboards answer broad questions with public prompts. API evaluation frameworks execute
models that can be called programmatically. Subscription users often face a different decision:

> Which assistant works best for my actual engineering, research, coding, and writing tasks in the
> interfaces I already pay for?

Copying answers into a spreadsheet is easy. Making the conclusion reviewable is harder:

- model identity can bias the reviewer;
- left/right position and answer length can shift preferences;
- web products may silently change routing, tools, and system instructions;
- prompt edits, retries, or missing settings break comparability;
- a rank without uncertainty looks more stable than it is;
- private tasks should not be uploaded to another judging service.

FrontierTrials records those limits instead of hiding them.

## The workflow

```text
private tasks + rubric + observed candidate metadata
                         ↓
          manually capture exact web outputs
                         ↓
            SHA-256 integrity verification
                         ↓
        deterministic aliases + balanced order
                         ↓
       self-contained offline judging packets
                         ↓
        imported human ballots + rationales
                         ↓
   blind adjudication queue for contested cases
                         ↓
       complete-assignment gate + identity reveal
                         ↓
 ranking + intervals + panel sensitivity + bias checks
                         ↓
        evidence seal + portable public or private report
```

<img src="docs/assets/workflow.svg" alt="FrontierTrials evidence lifecycle from protocol design to blind adjudication, reveal, analysis, and sealing" width="100%">

## Quick start

FrontierTrials requires Python 3.11 or newer and has no runtime dependencies. It is not yet
published on PyPI, so use a versioned GitHub Release artifact:

```bash
python -m pip install \
  https://github.com/CAOShurong/frontiertrials/releases/download/v0.2.0/frontiertrials-0.2.0-py3-none-any.whl
frontiertrials demo my-fictional-trial
frontiertrials audit --trial my-fictional-trial
frontiertrials verify --trial my-fictional-trial
```

Alternatively:

```bash
python -m pip install "frontiertrials @ git+https://github.com/CAOShurong/frontiertrials.git@v0.2.0"
```

Open:

```text
my-fictional-trial/reports/trial-report.html
my-fictional-trial/packets/reviewer-one.html
```

Both are self-contained files. The packet works offline and downloads completed ballots as JSON.

## Build a real trial

### 1. Define the decision before seeing answers

```bash
frontiertrials init trials/assistant-choice \
  --title "My EE research assistant trial" \
  --question "Which subscription assistant best supports my weekly research workflow?" \
  --owner "Your name"
```

Record exclusions and the protocol in `frontiertrials.json`. Good exclusions might include web
search, tool use, file upload, or multi-turn repair when those capabilities cannot be held
comparable.

### 2. Add tasks, candidates, a rubric, and raters

```bash
frontiertrials add task task-rf-debug.json --trial trials/assistant-choice
frontiertrials add candidate candidate-a.json --trial trials/assistant-choice
frontiertrials add rubric engineering-quality.json --trial trials/assistant-choice
frontiertrials add rater reviewer-one.json --trial trials/assistant-choice
```

Candidate metadata should record the provider label shown by the interface, observed model label,
capture surface, account plan, date, and settings. This does not prove the provider's internal
routing.

### 3. Capture exact outputs manually

Run the same frozen task in each web app. Save the response as UTF-8 Markdown without cleaning,
rewriting, or removing inconvenient content.

```bash
frontiertrials capture \
  --trial trials/assistant-choice \
  --id response-rf-debug-candidate-a \
  --task rf-debug \
  --candidate candidate-a \
  --source captures/rf-debug-candidate-a.md \
  --captured-at 2026-08-04T09:00:00Z \
  --latency-seconds 42
```

FrontierTrials copies the text, records word and character counts, and stores a SHA-256 digest.
Latency is optional and remains a manually observed value.

### 4. Freeze pairings and assignments

Put a random secret in a local file that raters cannot read:

```bash
frontiertrials freeze \
  --trial trials/assistant-choice \
  --seed-file local-secret.txt \
  --reviews-per-pair 2
```

Freeze requires one captured response for every task/candidate combination. It creates all
candidate pairs for every task, alternates orientation for repeated matchups, allocates raters,
and writes the identity map to `secrets/reveal.json`.

Do not give raters the trial workspace. Give them only their packet.

### 5. Distribute offline packets

```bash
frontiertrials packet \
  --trial trials/assistant-choice \
  --rater reviewer-one \
  --output packets/reviewer-one.html
```

The packet contains prompts, anonymous outputs, rubric anchors, independent 1–5 scores, an overall
left/right/tie/abstain preference, confidence, flags, and a required rationale. It has no external
assets or network requests.

### 6. Import completed ballots

```bash
frontiertrials import-ballots ballots-reviewer-one.json \
  --trial trials/assistant-choice
frontiertrials status --trial trials/assistant-choice
frontiertrials audit --trial trials/assistant-choice
```

The importer rejects unknown pairings, rater mismatches, and unassigned work. The audit reports
missing ballots, duplicate votes, incomplete criterion scores, response hash failures, position
imbalance, and possible provider-name leakage inside response text.

### 7. Adjudicate while identities remain hidden

```bash
frontiertrials adjudicate \
  --trial trials/assistant-choice \
  --format markdown \
  --output reports/adjudication.md
```

The queue flags reviewer disagreement, low confidence, ballot flags, abstentions, and tie votes.
It contains pairing IDs, task titles, anonymous aliases, judgments, scores, confidence, rationales,
and flags—but not candidate IDs, provider names, model labels, response IDs, or the reveal map.
The command never changes a ballot; it tells the panel which records deserve review.

### 8. Reveal, analyze, seal, and report

```bash
frontiertrials reveal --trial trials/assistant-choice
frontiertrials analyze --trial trials/assistant-choice --output analysis.json
frontiertrials report --trial trials/assistant-choice
frontiertrials seal --trial trials/assistant-choice
frontiertrials verify --trial trials/assistant-choice
```

Reveal refuses an incomplete assigned-ballot matrix by default. An explicit
`--allow-incomplete` override exists for documented early termination. Identity-bearing analysis
and public reports require the revealed state; adjudication is the safe inspection path before it.

## What the analysis reports

### Pairwise preference

FrontierTrials fits Bradley–Terry strengths from left/right/tie ballots. Ties contribute half a win
to each candidate; abstentions do not enter the ranking. A weak symmetric prior prevents a single
undefeated candidate from producing an infinite estimate.

### Task-clustered uncertainty

The 95% interval resamples tasks, not individual ballots. This keeps multiple reviewers and
pairings from the same prompt together. It asks how sensitive the ranking is to the chosen task
set, which is usually more relevant than treating every vote as independent.

### Pointwise rubric scores

Reviewers score each answer before choosing an overall preference. Weighted criterion summaries
show whether a candidate won through correctness, instruction fit, uncertainty discipline,
actionability, or clarity.

### Reviewer agreement

When assignments overlap, the report includes exact agreement and Cohen's kappa. Kappa is
descriptive here: a small panel and uneven choice frequencies can make it unstable.

### Panel and ranking sensitivity

Per-reviewer summaries report ballot count, confidence, left and longer-answer preference,
consensus alignment, and flags. Leave-one-rater-out refits show whether the observed leader or
rank positions depend heavily on one panel member. These are descriptive stress tests, not
reviewer-quality scores and not automatic corrections.

### Position and verbosity diagnostics

The report shows left-response wins with a Wilson interval and how often the longer response won.
Neither is an automatic correction. A wide interval is inconclusive, and an association with
length does not prove that length caused the preference.

### Category sensitivity

Preference rates are broken down by task category. A global winner can still be the wrong choice
for a specific workflow.

## Durable artifacts

```text
trial/
├── frontiertrials.json       # question, state, and protocol
├── tasks/                    # frozen prompts and context
├── candidates/               # observed product/model metadata
├── outputs/                  # exact captured Markdown
├── responses/                # capture metadata and hashes
├── rubrics/                  # weighted criteria and anchors
├── raters/                   # pseudonymous reviewer records
├── pairings/                 # blind order and assignments
├── ballots/                  # imported judgments and rationales
├── packets/                  # generated offline judging HTML
├── secrets/reveal.json       # identity map; keep private until reveal
├── reports/                  # generated analysis and report
└── frontiertrials-seal.json  # content-addressed evidence snapshot
```

Seven published [JSON Schemas](schemas/) document the interchange format. Runtime validation uses
the same conservative vocabulary without a schema dependency.

## Commands

| Command | Purpose |
|---|---|
| `init` | Create a trial workspace |
| `add` | Add a validated artifact |
| `capture` | Preserve one exact response and digest |
| `freeze` | Verify the matrix, alias identities, balance order, and allocate reviews |
| `packet` | Build one offline judging packet |
| `import-ballots` | Import downloaded packet ballots |
| `adjudicate` | Export a blind-safe queue of contested or low-confidence pairings |
| `status` | Show integrity and completion progress |
| `audit` | Check structure, hashes, references, leakage, balance, and ballots |
| `reveal` | Disclose aliases after assigned ballots are complete |
| `analyze` | Calculate rankings, intervals, rubric scores, and diagnostics |
| `export` | Write ranking CSV or protocol Markdown |
| `report` | Build a revealed self-contained report |
| `seal` | Hash trial evidence |
| `verify` | Compare current evidence with a saved seal |
| `demo` | Generate the complete fictional trial |

## Why no API?

API frameworks are the right choice when the evaluated system is programmatic. FrontierTrials
serves a different constraint: a human already has legitimate access to a consumer interface and
wants to compare its observed outputs without buying API credits or uploading private prompts to
another service.

No-API does not mean free, automated, or provider-endorsed. You remain responsible for subscription
costs, interface terms, rate limits, manual collection, and accurate metadata. Do not automate a
web product merely because FrontierTrials can store the resulting text.

## What FrontierTrials does not prove

- A displayed model label may not describe internal routing.
- A response hash proves later byte equality, not authentic provider origin.
- Human preference is not factual correctness, safety, or scientific validity.
- A task-clustered interval does not repair a biased task set.
- A private prompt reduces public-benchmark contamination risk but does not guarantee novelty.
- A structural audit does not validate the answer content.
- A rank is not “general intelligence.”

## Documentation

- [Protocol design](docs/protocol-design.md)
- [Blinding and order balance](docs/blinding.md)
- [Statistical analysis](docs/statistics.md)
- [Capture integrity](docs/capture-integrity.md)
- [Data model](docs/data-model.md)
- [Privacy and safe sharing](docs/privacy.md)
- [Competitive landscape](docs/competitive-landscape.md)
- [Validation evidence](docs/validation.md)
- [Roadmap](docs/roadmap.md)

## Development

```bash
python -m unittest discover -s tests -v
ruff check src tests
ruff format --check src tests
python -m compileall -q src tests
python -m build
```

CI runs 94 tests on Windows and Ubuntu with Python 3.11 and 3.13, then installs the built wheel in
a clean environment and executes the full fictional trial.

## Contributing

Methodology proposals are welcome when they include a concrete workflow, evidence, and the impact
on the trust boundary. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License and citation

FrontierTrials is released under the [MIT License](LICENSE). Cite a versioned release using
[CITATION.cff](CITATION.cff).

Created and maintained by **Shurong Cao**.
