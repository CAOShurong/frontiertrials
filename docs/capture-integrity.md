# Capture integrity

## Exact text

`capture` reads a UTF-8 source, normalizes only the final newline, stores the Markdown under
`outputs/`, and hashes the stored bytes. It does not strip branding, repair formatting, or remove
reasoning traces.

If the provider offers rich artifacts that cannot be represented in text, record that limitation.
FrontierTrials v1 is a text-output evaluation tool.

## Metadata

Record:

- exact displayed provider and model labels;
- interface surface and subscription plan;
- capture time and timezone;
- reasoning or mode settings;
- enabled tools;
- retry policy;
- manually observed latency definition;
- any interruption, refusal, or rendering failure.

A displayed label is an observation, not an attestation of internal serving infrastructure.

## Hash checks

The audit recomputes every response digest. A mismatch is an error. The final seal also hashes the
manifest, every artifact, and every captured Markdown file into one ordered root.

The seal excludes reports, packets, and the reveal secret. Regenerating a visualization therefore
does not change the evidence root.

## Origin limitation

A digest proves that bytes did not change after capture. It does not prove which website produced
them. Stronger provenance could use a screen recording, signed capture log, independent witness, or
provider export, subject to privacy and terms.

