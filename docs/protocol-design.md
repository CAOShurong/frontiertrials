# Protocol design

FrontierTrials helps preserve a protocol; it cannot choose a defensible research question for you.

## Start with a decision

Prefer:

> Which assistant best supports first-pass EE paper review and bench-debug planning under our
> existing subscription interfaces?

Avoid:

> Which model is smartest?

The first question names a user, task family, access mode, and purpose. The second cannot be
answered by a small private trial.

## Freeze tasks before capture

Write each prompt, system instruction, supplied context, reference answer or decision criteria,
category, and exclusions before collecting candidate outputs. Do not improve a weak prompt for one
candidate after seeing its response.

Private tasks can reduce direct public-benchmark familiarity, but secrecy does not guarantee that
a task is novel or uncontaminated.

## Comparable conditions

Record the surface, displayed model label, account plan, date, settings, enabled tools, and retry
policy. A fair protocol may disable features that cannot be made comparable, or it may deliberately
compare complete products. State which question you are asking.

For stochastic systems, one response per task measures one observed interaction. Multiple
independent captures require separate trial design; do not quietly pick the best retry.

## Rubric before preference

Pointwise criterion scores make the preference rationale inspectable. Criteria should be concrete,
non-overlapping, and anchored. Weight changes after capture are a sensitivity analysis, not the
original protocol.

## Rater allocation

Two independent reviewers per pair enable an agreement diagnostic. More reviewers are useful when
preferences are subjective, tasks cross expertise areas, or decisions are high stakes. Reviewer
pseudonyms should not hide relevant conflicts or expertise from the trial owner.

## Predeclare exclusions and stopping

Examples:

- exclude a response when the interface fails before producing content;
- abstain when the prompt requires expertise the reviewer lacks;
- freeze after one capture per task/candidate;
- reveal only after all assigned ballots arrive;
- do not replace a ballot after identities are known.

FrontierTrials warns about incomplete reveal but does not enforce an institutional protocol.

