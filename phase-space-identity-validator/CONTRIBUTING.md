# Contributing

Contributions should preserve the distinction between structural validation and mathematical proof.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Pull requests

Each new rule should include:

- a stable diagnostic code;
- a minimal passing example;
- a minimal failing example;
- unit tests;
- a statement of assumptions and known false-positive risks.

Do not add universal physics claims without a citable derivation and explicit scope conditions.
