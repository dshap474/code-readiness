# Plans

## Current Template Scope

This template now instantiates all nine hardened readiness sections:

- Style & Validation
- Build System
- Testing
- Documentation
- Development Environment
- Debugging & Observability
- Security
- Task Discovery
- Product & Experimentation

## Hosted-Only Evidence Gaps

The following criteria still require a hosted GitHub repo or live runtime usage to earn full
evidence:

- branch protection and required checks
- active Dependabot PRs
- secret-scanning alerts and push protection
- scheduled backlog-health runs
- real error-to-insight issue creation
- deployed dashboard, alert-routing, and post-deploy evidence

## Acceptance Target

The template should remain a clean, locally runnable FastAPI + Postgres service whose
setup, proof path, docs, control plane, and section contracts are deterministic from
source control alone.
