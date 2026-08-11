# Validation evidence

Version 0.4.0 has seven validation layers.

## Behavioral tests

Ninety-eight standard-library tests cover:

- identifiers, deterministic digests, escaping, word counts, and descriptive statistics;
- all seven artifact validators;
- workspace creation, states, exact capture, and integrity failures;
- alias determinism, complete matrices, order balance, rater limits, reveal guards, and ballot import;
- percentiles, Wilson intervals, Bradley–Terry fitting, task-clustered bootstrap, and kappa;
- ranking, rubrics, categories, position diagnostics, agreement, and audit errors;
- offline packets, public report guards, CSV and Markdown exports, seals, and the full demo.
- frozen-state analysis rejection, complete-ballot reveal gating, blind-safe adjudication exports,
  panel summaries, and leave-one-rater-out ranking sensitivity.
- packaged Personal Lab assets, its loopback-only server, network-blocking browser policy, and
  command-line launcher.

## Browser workflow

Eight Playwright runs exercise the Personal Lab in desktop and mobile Chromium. They cover field-linked
validation errors, predictable focus through a three-pair review, keyboard scrolling of a long answer,
reveal, local save and history, visible file-import focus, narrow-screen containment, and automated
WCAG A/AA scans in key states. Release acceptance also captures and visually inspects desktop and
mobile screenshots.

These checks do not prove usability with NVDA, JAWS, VoiceOver, speech input, or other assistive
technology. A study with real assistive-technology users remains open work.

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
complete demo, verifies the seal, audits the workspace, exports the blind adjudication queue, and
regenerates reports and packets.

## Repository and publication audit

`python scripts/check_repository.py` checks the package version surfaces, required project files,
README links, public-install instructions, sole authorship metadata, workflow coverage, SVG
viewports, and forbidden legacy visual tokens. Release validation then installs the public wheel
URL into a new virtual environment and reruns the full demonstration.

## Matrix

- Windows and Ubuntu
- Python 3.11 and 3.13
- Desktop and mobile Chromium

Other systems may work but are not claimed by version 0.4.0.
