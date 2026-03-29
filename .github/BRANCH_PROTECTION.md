# Branch Protection Manual Setup

This repository's `branch_protection` readiness signal depends on GitHub-enforced rules on `main`.
That cannot be fully enabled from tracked source files alone, so apply the settings in GitHub or via
the GitHub CLI.

## Recommended protection for `main`

- Require a pull request before merging
- Require at least 1 approval
- Dismiss stale approvals when new commits are pushed
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Block direct pushes to `main`
- Block force pushes
- Block branch deletion

## Suggested required checks

- `ci / proof`
- `security-review / review`
- `pr-review / review`

Use the exact check names shown in GitHub if they differ from the examples above.

## GitHub UI path

1. Open repository settings
2. Go to `Rules` or `Branches`
3. Create a ruleset or branch protection rule for `main`
4. Add the requirements listed above

## GitHub CLI inspection

```bash
gh api repos/dshap474/code-readiness/rulesets
gh api repos/dshap474/code-readiness/branches/main/protection
```

## Verification

After enabling protection, confirm:

- pushes to `main` are rejected without a PR
- required checks appear as blocking checks on pull requests
- merge is blocked until approval and green CI are present
