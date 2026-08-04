# Competitive landscape

FrontierTrials does not claim to invent pairwise evaluation, manual response input, or model
ranking. It combines those established ideas around a specific no-API subscription workflow.

| Tool or category | Strength | Different boundary in FrontierTrials |
|---|---|---|
| [Promptfoo](https://www.promptfoo.dev/docs/intro/) | Provider-driven prompt testing, assertions, red teaming, CI, and a manual-input provider | FrontierTrials specializes in asynchronous captured web outputs, content hashes, blind packet distribution, multi-rater allocation, reveal control, and human-bias diagnostics |
| [Inspect AI](https://inspect.aisi.org.uk/providers.html) | Executable evaluations across many APIs and local model providers | FrontierTrials never invokes a model and targets observed subscription interfaces |
| [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) | Standard academic tasks and reproducible model backends | FrontierTrials uses private user tasks and manual product-level captures |
| [Google LLM Comparator](https://ai.google.dev/responsible/docs/evaluation/llm_comparator) | Interactive analysis of side-by-side evaluation data | FrontierTrials covers capture, hashing, aliasing, allocation, offline voting, analysis, and sealing as one file-native lifecycle |
| Chatbot Arena / Arena | Anonymous public pairwise preferences and large-scale ranking | FrontierTrials is a small private decision study with a known task set and reviewer panel |
| Spreadsheet comparison | Flexible and familiar | FrontierTrials adds schema validation, order balance, identity separation, uncertainty, integrity, and a reproducible report |

## Design inference

The underserved combination is:

```text
manual consumer-interface capture
  + exact content hashes
  + private task set
  + deterministic blind aliases
  + balanced left/right order
  + offline multi-rater packets
  + pointwise and pairwise judgments
  + task-clustered uncertainty
  + bias and agreement diagnostics
  + reveal and evidence seal
```

Each component has precedent. The contribution is a dependency-free, auditable workflow that does
not require API keys, a hosted evaluator, or a second model acting as judge.

## Research motivations

Private benchmarks can reduce exposure to public benchmark contamination, although privacy alone
does not establish quality. Pairwise evaluation can exhibit position and other preference biases.
Bradley–Terry ranking and bootstrap intervals are used in large pairwise arenas. FrontierTrials
adopts these ideas conservatively and reports their limits rather than treating the rank as ground
truth.

