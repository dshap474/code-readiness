---
name: release-check
description: Validate release readiness and rollout notes before publishing.
---
# Release Check

Use this skill when preparing a release, deploy, or publish event.

## Inputs

- release identifier
- proof command results
- rollout notes
- rollback pointer

## Workflow

1. Confirm the proof path is green.
2. Confirm release notes and rollout notes are present.
3. Confirm a rollback path exists and is current.
4. Report missing evidence before release.

## Output

- readiness summary
- blockers
- required follow-up
