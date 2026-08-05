# Competitive landscape

FrontierTrials does not claim to invent pairwise evaluation, manual response input, local storage,
or model ranking. Version 0.3 combines those established ideas around a progressive no-API
subscription workflow: one fast personal comparison, a longitudinal personal benchmark, and an
optional study-grade evidence lifecycle.

| Tool or category | Strength | Different boundary in FrontierTrials |
|---|---|---|
| [Arena](https://arena.ai/how-it-works) | Immediate anonymous public battles, selected-model comparisons, and crowd-powered leaderboards | Compares exact outputs captured from the subscription interfaces a user already uses; prompts, votes, and history remain local |
| [Promptfoo](https://www.promptfoo.dev/docs/providers/manual-input/) | Provider-driven prompt testing, assertions, red teaming, CI, and a manual-input provider | Personal Lab removes configuration before the first comparison; Study Mode specializes in captured web outputs, offline review, reveal control, and panel diagnostics |
| [Inspect AI](https://inspect.aisi.org.uk/providers.html) | Executable evaluations across API and local model providers | Never invokes a model and targets observed subscription interfaces |
| [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) | Standard academic tasks and reproducible model backends | Uses a person's private, recurring tasks and manually captured product outputs |
| [LLM Comparator](https://github.com/PAIR-code/llm-comparator) | Interactive slice-level analysis of prepared, scored side-by-side data | Covers capture, browser-local review, task history, and report export before advanced analysis |
| [LangSmith](https://docs.langchain.com/langsmith/annotation-queues) | Hosted annotation queues around application runs and experiments | Works without an instrumented application, API key, or hosted workspace |
| [Label Studio](https://labelstud.io/templates/llm_side_by_side) | General-purpose pairwise labeling and configurable annotation projects | Personal Lab requires no labeling project or schema; Study Mode adds a file-native reveal and audit lifecycle |
| Spreadsheet comparison | Flexible and familiar | Personal Lab removes setup; Study Mode adds validation, order balance, identity separation, uncertainty, integrity, and reproducible reports |

## Personal product boundary

The underserved personal combination is:

```text
exact outputs from consumer subscription interfaces
  + no API key or model invocation
  + no configuration before the first comparison
  + browser-local prompts, votes, and history
  + task category, observed latency, and subscription price together
  + honest task-level conclusions
  + portable JSON and self-contained HTML
```

Arena should be the default recommendation for casual public-model exploration. FrontierTrials is
for a different decision: which paid product works best on the user's private, recurring tasks in
the interfaces they actually use.

Personal Lab deliberately does not claim scientific blinding. Product names leave the review
screen, but a reviewer may remember answer style or what they pasted.

## Study Mode boundary

The stronger Study Mode combination is:

```text
manual consumer-interface capture
  + exact content hashes
  + private task set
  + deterministic blind aliases
  + balanced left/right order
  + offline multi-rater packets
  + pointwise and pairwise judgments
  + blind-safe adjudication triggers
  + task-clustered uncertainty
  + panel and leave-one-rater-out diagnostics
  + controlled reveal and evidence seal
```

Each component has precedent. The contribution is the enforced, file-native handoff across exact
capture, offline review, controlled reveal, sensitivity analysis, and evidence preservation.

## Research motivations

Private benchmarks can reduce exposure to public benchmark contamination, although privacy alone
does not establish task quality. Pairwise evaluation can exhibit position, verbosity, and other
preference biases. Bradley–Terry ranking and bootstrap intervals are established methods used in
large pairwise arenas.

FrontierTrials adopts these ideas conservatively. It attaches limitations to every result rather
than treating a rank as ground truth.

## Falsifiable product hypothesis

Personal Lab is useful only if people with two or more AI subscriptions can finish a first
comparison without documentation and then return to add real tasks. Product validation should
therefore measure:

- time to first completed comparison;
- completion without Python or JSON knowledge;
- return rate for a second task;
- diversity of saved task categories;
- whether the history changes a purchase, renewal, or workflow decision.

Repository stars alone cannot establish product usefulness.
