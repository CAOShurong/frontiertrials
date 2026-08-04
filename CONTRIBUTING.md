# Contributing

FrontierTrials welcomes focused changes that make manual model evaluation more transparent.

## Suitable contributions

- Minimal import, allocation, integrity, or report bugs.
- Statistical corrections with references and tests.
- Accessibility and offline-packet improvements.
- Better leakage diagnostics that do not rewrite responses.
- Schema proposals grounded in a real evaluation workflow.

Do not submit private prompts, subscription exports, personal data, provider credentials, or
copyrighted material you cannot redistribute.

## Development

```bash
git clone https://github.com/CAOShurong/frontiertrials.git
cd frontiertrials
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip install ruff build
ruff check src tests
ruff format --check src tests
python -m build
```

## Pull requests

1. Keep one behavioral purpose per pull request.
2. Add tests for every changed outcome.
3. Update schemas and methodology docs for durable-format changes.
4. Describe any effect on blinding, order balance, privacy, or interpretation.
5. Preserve deterministic output and Windows/Linux portability.

By participating, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

