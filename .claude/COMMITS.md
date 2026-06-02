# Commit conventions

How commits are written in this repo. Follow these whenever you create a commit.

## Format

```
type(SCOPE): short subject in lowercase

Optional body — wrap at ~72 chars. Explain the *why*,
not the *what*. The diff already shows the what.
```

- **type**: one of the allowed types below.
- **SCOPE**: the current ticket id, zero-padded to 4 digits — e.g. `TMW-0013`. Set in [commitlint.config.js](../commitlint.config.js). Update that file whenever a new branch starts.
- **subject**: lowercase, no trailing period, under ~72 chars. Imperative mood (`add`, `fix`, `regenerate` — not `added`, `fixed`).
- **body**: **default to no body.** Most commits are subject-only. Add a body *only* when the *why* is non-obvious — a constraint, prior incident, surprising design choice, or behaviour that would surprise a future reader. Mechanical changes (adopt pattern X across N files, rename, regenerate, lint fix, follow-up to commit Y) do **not** need a body — the diff plus subject already explain them.
- **body length** (when one is justified): **max 3 lines**, wrapped at ~72 chars. If you need more than 3 lines, the commit is probably doing two things — split it instead of explaining at length. Never restate what the subject already says.
- **NEVER add `Co-Authored-By:` trailers.** Commits must show as authored solely by the human committer.

## Allowed types

| Type     | When to use                                                                 |
|----------|------------------------------------------------------------------------------|
| `feat`   | New user-facing feature or new endpoint                                      |
| `fix`    | Bug fix — runtime behavior wrong, or type/test broken                        |
| `test`   | Adding or updating tests                                                     |
| `chore`  | Tooling, deps, generated files (SDK regen, lockfile), no user-visible change |
| `refactor` | Internal restructure with no behavior change                               |
| `perf`   | Performance / bundle improvement with no behavior change                      |
| `style`  | Formatting / lint fixes only — no logic change                               |
| `docs`   | Documentation only                                                           |
| `build`  | Build system, package manager, CI config                                     |

If a commit fits two types, pick the one that best describes the *user-visible* effect (`feat` over `chore`, `fix` over `test`).

## Grouping rules

One commit = one buildable, reviewable unit of change.

- **Yes** — group all files needed for a single logical change. A new endpoint (api + service + repo) is one commit. A new page (page + its hooks + its route wiring) is one commit.
- **Yes** — separate tests from the code they cover when the test commit is large enough to stand alone. Otherwise bundle them.
- **No** — don't commit per-file when files are halves of the same change (e.g. router without service won't compile).
- **No** — don't mix unrelated changes in one commit just because they're in the same area. A latent type fix found while writing a feature goes in its own `fix(...)` commit.
- **No** — never use `git add -A` or `git add .`. Stage by explicit path.

## Examples from this repo

Good (subject-only is the norm):

```
fix(TMW-0013): send full update payloads to match backend put dtos
```

```
chore(TMW-0013): regenerate openapi client and adapt tenant hooks
```

```
test(TMW-0013): cover list_for_user at api, service and repository layers
```

```
feat(TMW-0014): apply per-user rate limits to authenticated routes
```

Good (body justified — explains a non-obvious *why*):

```
feat(TMW-0013): add list endpoint for caller's tenants

Frontend tenant switcher and onboarding redirect already called this
endpoint, but it didn't exist on the backend.
```

Avoid:

- `update file.py` — no type, no scope, vague subject
- `feat(TMW-0013): added new audit page` — past tense
- `feat: audit page` — missing scope
- `fix: typo fix and refactor login and update README` — multiple concerns, should be three commits
- **Long body restating the diff** — e.g. listing every router touched, naming the dependency the patch swaps in, describing both sides of a before/after. The reader can see this in the diff. If the subject conveys the change, stop writing.

## Mechanics

- Pre-commit hooks run ruff (backend) and commitlint. If a hook fails, **fix the issue and create a NEW commit** — never `--amend` after a hook failure (the original commit didn't happen; `--amend` would modify the *previous* one).
- Never use `--no-verify` to bypass hooks unless explicitly asked.
- Never use `--amend` on a commit that's already been pushed.
- Pass multi-line bodies via HEREDOC so newlines survive:

```bash
git commit -m "$(cat <<'EOF'
feat(TMW-0013): one-line subject

Body paragraph with the why.
EOF
)"
```

## Branch naming

Branches use the same ticket id but **without** padding: `TMW-13`, `TMW-013`, `TMW-0013` — pick one and stay consistent on that branch. The **scope inside the commit message** is always the padded 4-digit form (`TMW-0013`) regardless of branch name, because that's what commitlint enforces.

When starting a new branch, bump the scope in [commitlint.config.js](../commitlint.config.js) in the first commit of that branch (style or chore type).
