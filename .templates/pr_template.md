# [type(scope)]: Short title (max 72 chars)

## What and why
<!--
What does this PR do and why is it needed?
1-3 sentences max. Focus on the motivation, not the implementation.
-->

## Changes
<!--
Bullet list of the meaningful changes. Group by area if needed.
Skip obvious things (e.g. "updated imports"). Focus on what a reviewer needs to understand.
-->
-
-

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no functional change)
- [ ] Chore / tooling
- [ ] Docs

## How to test
<!--
Steps to verify this works. Be specific enough that someone unfamiliar with the code can follow.
Include: setup needed, commands to run, what to look for.
-->
1.
2.

## Architecture / design notes
<!--
Fill this in only if the PR introduces non-obvious design decisions, tradeoffs, or constraints future devs should know about.
Delete this section if not applicable.
-->

## Risk assessment
**Level:** `Low` / `Medium` / `High` ← delete the ones that don't apply

| Factor | Notes |
|--------|-------|
| Affects production data | Yes / No |
| Requires migration | Yes / No |
| Touches auth / permissions | Yes / No |
| Has external side effects (emails, webhooks, payments) | Yes / No |
| Rollback complexity | Easy / Hard — describe how |

<!--
Low   — isolated change, fully tested, easy to revert
Medium — touches shared code or has some external effect, tested but with caveats
High  — data migration, auth change, external service, or hard to revert
-->

## Checklist
- [ ] Tests added or updated
- [ ] Mypy passes (`uv run mypy .`)
- [ ] Ruff passes (`uv run ruff check .`)
- [ ] No unrelated changes in the diff
- [ ] PR title follows conventional commits format

## Related issues / tickets
<!--
Link to Linear, GitHub issues, or any relevant context.
-->
Closes #
