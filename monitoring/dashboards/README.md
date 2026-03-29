# Dashboards

## Quality Dashboard Contract

This template expects one shared dashboard or owned report surface that answers:

- Is request success or latency trending in the wrong direction?
- Are widget actions still flowing after a release?
- Are code-quality signals such as CI health and coverage stable?

## Repo-Owned Local Proof

Before the repo is hosted, the primary quality evidence lives in:

- `monitoring/quality/README.md`
- the `build-metrics.json` artifact uploaded by `.github/workflows/ci.yml`
- `/metrics` for runtime counters and latency

If the repo later adopts a hosted dashboard, keep this file as the map from that hosted view
back to the repo-owned contracts.
