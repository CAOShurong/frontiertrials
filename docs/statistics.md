# Statistical analysis

The analysis is designed to expose instability, not to manufacture certainty from a small trial.

## Bradley–Terry strengths

For candidates *i* and *j*, the Bradley–Terry model represents the probability that *i* is
preferred as:

```text
P(i beats j) = strength_i / (strength_i + strength_j)
```

FrontierTrials fits strengths with a minorization-maximization update and a weak symmetric
half-win prior. The mean strength is normalized to one. Absolute values have no meaning outside the
fitted candidate set.

Ties contribute 0.5 to each candidate. Abstentions are excluded.

## Task-clustered bootstrap

Ballots from the same task share prompt difficulty and content. Treating them as independent would
overstate effective sample size. FrontierTrials resamples task IDs with replacement, brings along
all ballots for each selected task, refits the model, and reports the 2.5th and 97.5th percentiles.

The interval reflects sensitivity to this finite task set under the resampling model. It does not
cover capture drift, rater selection bias, unrecorded interface changes, or an invalid rubric.

## Pointwise rubric

For one side of a ballot:

```text
weighted score = Σ(criterion rating × criterion weight) / Σ(weights)
```

Scores are averaged over appearances. They are descriptive ordinal summaries; the distance from
1 to 2 need not equal the distance from 4 to 5.

## Agreement

Exact preference agreement and Cohen's kappa are calculated when two or more raters evaluate the
same pairing. Kappa adjusts for agreement expected from marginal choice frequencies. It can be
unstable with few overlaps or highly imbalanced choices.

## Position diagnostic

Left wins among decisive ballots are shown with a Wilson 95% interval. A rate near 50% with a wide
interval is inconclusive. The tool does not automatically reweight ballots based on this diagnostic.

## Verbosity diagnostic

The report counts how often the longer response won and the mean winner-minus-loser word difference.
This is an association. Better answers may legitimately need more words, and length may proxy for
another quality.

## Multiple comparisons and claims

Version 0.1.0 does not produce p-values or correct for multiple comparisons. Do not use overlapping
or non-overlapping bootstrap intervals as a formal hypothesis test without a protocol designed for
that inference.

