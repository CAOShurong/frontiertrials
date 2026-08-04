# Changelog

## [Unreleased]

## [0.2.0] - 2026-08-05

### Added

- Blind-safe adjudication queues in JSON, CSV, and Markdown for disagreement, low confidence,
  ballot flags, abstentions, and tie votes.
- Per-reviewer descriptive diagnostics and leave-one-rater-out ranking sensitivity.
- Academic print-inspired website, report, reviewer packet, and graphical abstracts.
- Versioned GitHub Release installation path, release automation, and repository audit.

### Changed

- Identity-bearing analysis now requires the revealed trial state.
- Reveal now requires the complete assigned-ballot matrix unless an explicit override is recorded.
- The fictional demo now includes adjudication artifacts and a deterministic seal timestamp.

## [0.1.0] - 2026-08-04

### Added

- Seven file-native artifact types for tasks, candidates, responses, rubrics, raters, pairings, and ballots.
- Exact Markdown capture with SHA-256 verification and optional observed latency.
- Complete-matrix checks, deterministic anonymous aliases, alternating pair orientation, and rater allocation.
- Self-contained offline judging packets with downloadable JSON ballots.
- Validated ballot-bundle import and completion tracking.
- Bradley–Terry ranking with task-clustered bootstrap intervals.
- Weighted pointwise rubrics, task-category sensitivity, reviewer agreement, position diagnostics, and verbosity association.
- Structural and blinding audits plus a content-addressed trial seal.
- A revealed portable report and a 191-artifact, fully fictional demonstration.
- Eighty-five standard-library tests, cross-platform CI, package smoke tests, and GitHub Pages.

[Unreleased]: https://github.com/CAOShurong/frontiertrials/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/CAOShurong/frontiertrials/releases/tag/v0.2.0
[0.1.0]: https://github.com/CAOShurong/frontiertrials/releases/tag/v0.1.0
