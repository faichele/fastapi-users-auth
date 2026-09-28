# Issue tracker: GitHub

Issues and specs for this repository live in GitHub Issues. Use the `gh` CLI for all operations.

## Conventions

- **Create:** `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read:** `gh issue view <number> --comments`, including labels where relevant.
- **List:** `gh issue list --state open` with suitable `--label` filters.
- **Comment:** `gh issue comment <number> --body "..."`.
- **Label:** `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- **Close:** `gh issue close <number> --comment "..."`.

Infer the repository from `origin` (`faichele/fastapi-users-auth`); `gh` does this automatically inside this clone.

## Pull requests as a triage surface

**PRs as a request surface: no.** Set this to `yes` only if external pull requests should enter the same triage workflow as issues.

## Skill routing

When a skill says to publish to the issue tracker, create a GitHub issue. When it asks for the relevant ticket, run `gh issue view <number> --comments`.
