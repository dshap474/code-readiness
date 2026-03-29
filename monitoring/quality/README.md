# Quality Report

## Owner

- engineering

## Source Of Truth

- `.github/workflows/ci.yml` uploads `build-metrics.json`
- `just ci` runs lint, typecheck, docs drift checks, packaging, tests, and flaky-test detection
- `pytest` coverage output is part of the fast proof surface

## Signals

- build timing from `build-metrics.json`
- coverage threshold from `pytest`
- lint, typing, dependency, and architecture checks from `just ci`
