# Roadmap

## Product principle

FrontierTrials should make one useful personal comparison easy before it asks a user to learn a
research protocol. Additional rigor is progressive:

```text
Quick Compare → Personal Benchmark → Study Mode
```

## Shipped in 0.3

- Browser-local Quick Compare for two to four manually captured outputs.
- Anonymous pair order, task-level reveal, and an explicit masking-versus-memory warning.
- Personal history with aggregate preference, category coverage, price, and latency context.
- Portable JSON backup and self-contained HTML result export.
- A loopback-only `frontiertrials open` command with no runtime dependencies.

## Shipped in 0.3.1

- PyPI distribution with OIDC Trusted Publishing and public provenance attestations.
- PyPI-safe documentation links and a shareable large-image social preview.
- Structured issue forms for bugs and real comparison use cases.

## Shipped in 0.4.0

- Predictable keyboard focus and status announcements across capture, blind review, results, and
  history.
- Keyboard-scrollable long answers and result tables, visible focus indicators, field-linked errors,
  and narrow-screen progress labels.
- Desktop and mobile Playwright acceptance with automated WCAG A/AA checks across key states.
- Immutable workflow actions, CodeQL, and attested release artifacts.

## Shipped in 0.4.1

- Bulk capture: paste every product answer in one block separated by `===` name lines
  (optional `| $price/mo | 12s` header fields), or drop a `.txt`/`.md` file. Manual
  per-product pasting is now the fallback, not the default.

## Near term

- Complete a usability study with people who use NVDA, JAWS, or VoiceOver; automated semantics and
  keyboard checks do not substitute for that evidence.
- Add currency selection and subscription-plan snapshots.
- Add category-specific history and longitudinal capture waves.
- ~~Import plain Markdown~~ — shipped 2026-08-26: bulk paste with `===` block separators plus .txt/.md file drop. Conversation-export formats remain open.
- Publish a real, consented case study using recurring engineering and research tasks.
- Add optional incomplete block designs for larger Study Mode candidate sets.

## Later, only if user evidence supports the need

- A browser extension that assists capture without automating model submission.
- Multiple independent response draws per task and candidate.
- Rater-specific packet splitting by expertise and workload.
- Sensitivity analysis for rubric weights and decision thresholds.
- Signed capture and seal attestations.
- Ordinal mixed models behind an optional scientific dependency extra.

## Non-goals

- Automating consumer web apps or evading provider terms.
- Sending private prompts to a hidden model judge.
- Pretending on-screen masking erases reviewer memory.
- Claiming a small personal task set measures general intelligence.
- Publishing a live global leaderboard.
- Automatically deleting identity cues from captured responses.
