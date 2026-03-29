# Quality Report

## Owner

- engineering

## Source Of Truth

- `.github/workflows/ci.yml` uploads `build-metrics.json`
- `.github/workflows/ci.yml` uploads `fast-feedback.json` for the sub-10-minute PR gate
- `.github/workflows/ci.yml` uploads `ci-performance-summary.md` for human-readable CI timing review
- `just ci` runs lint, typecheck, docs drift checks, packaging, tests, and flaky-test detection
- `pytest` coverage output is part of the fast proof surface

## Signals

- fast feedback timing from `fast-feedback.json`
- build timing from `build-metrics.json`
- budget compliance and operator summary from `ci-performance-summary.md`
- coverage threshold from `pytest`
- lint, typing, dependency, and architecture checks from `just ci`
