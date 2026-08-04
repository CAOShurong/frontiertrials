# Validation evidence

Version 0.1.0 has four validation layers.

## Behavioral tests

Eighty-five standard-library tests cover:

- identifiers, deterministic digests, escaping, word counts, and descriptive statistics;
- all seven artifact validators;
- workspace creation, states, exact capture, and integrity failures;
- alias determinism, complete matrices, order balance, rater limits, reveal guards, and ballot import;
- percentiles, Wilson intervals, Bradley–Terry fitting, task-clustered bootstrap, and kappa;
- ranking, rubrics, categories, position diagnostics, agreement, and audit errors;
- offline packets, public report guards, CSV and Markdown exports, seals, and the full demo.

## Static checks

```bash
ruff check src tests
ruff format --check src tests
python -m compileall -q src tests
```

## Deterministic fictional trial

The demo creates 8 tasks, 4 fictional candidates, 32 exact outputs, 48 pairings, 2 raters, and 96
ballots. It audits without errors or warnings, has exactly balanced left exposure, and verifies a
224-file evidence seal.

## Package smoke test

CI builds wheel and source distributions, installs the wheel into a clean environment, creates the
complete demo, verifies the seal, audits the workspace, and regenerates reports and packets.

## Matrix

- Windows and Ubuntu
- Python 3.11 and 3.13

Other systems may work but are not claimed by version 0.1.0.

