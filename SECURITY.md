# Security policy

## Supported versions

Security fixes are applied to the latest release.

## Reporting

Use GitHub private vulnerability reporting. Do not open a public issue with exploit details,
private prompts, account data, unpublished outputs, rater identities, or a reveal seed.

## Trust boundary

FrontierTrials reads local text and JSON, then writes local HTML, CSV, Markdown, and JSON. It does
not log in to a provider, execute model code, make network requests, or send telemetry.

Judging packets contain private prompts and captured responses. Anyone holding a packet can read
them. The packet's browser JavaScript only manages local state and downloads a ballot file, but
users should still review generated files before distribution.

The `secrets/reveal.json` file defeats candidate blinding. Keep it outside shared packet folders
and access-controlled until voting is locked. A seed fingerprint detects accidental mismatch but
does not let a rater reconstruct the seed.

Generated reports HTML-escape displayed values and JSON-escape embedded data. This reduces markup
injection but does not make sensitive content safe to publish.

Evidence seals are hashes, not signatures. They detect later byte changes but do not establish
capture origin or authorship.

