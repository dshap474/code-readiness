---
name: openapi-sync
description: Regenerate and verify the committed OpenAPI document after API changes.
---
# OpenAPI Sync

Use this skill when routes, request models, or response models change.

## Workflow

1. Update the FastAPI app or schema-bearing route code.
2. Run `just docs-generate`.
3. Run `just docs-check`.
4. Report API surface changes with the updated `docs/api/openapi.yaml`.
