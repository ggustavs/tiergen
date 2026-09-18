# Contributing

Read `nids-gen-dsl-design.md` first. Section 4 records decisions; section 18 lists the working
agreements this file expands on.

## Setup

```
uv sync
uv run pre-commit install
```

`uv sync` installs every workspace member editable plus the dev tools. `pre-commit install` adds
three git hooks: ruff on commit, the commit message check, and the branch name check on push.
Nothing here needs Docker.

## Before you push

```
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

CI runs the same four, plus `uv lock --check`. If you add or change a dependency or a workspace
member, run `uv lock` and commit `uv.lock`.

## Commits

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>(<scope>): <description>
```

The description is lowercase, imperative, at most 80 characters and has no trailing period. The
subject alone is usually enough; add a body in plain prose when the reason is not obvious.

Types: `feat` `fix` `docs` `build` `ci` `test` `refactor` `perf` `style` `chore` `revert`.

Scopes name a directory, so a scope always answers "where":

| scope | covers |
|---|---|
| `core` `protocols` `interfaces` `check` `cli` | the workspace member of that name |
| `impls` | `impls/_base` and every package under `impls/` |
| `backends` | every package under `backends/` |
| `examples` | `examples/` |
| `design` | `nids-gen-dsl-design.md` alone |
| `workspace` | root config, CI, tooling, this file |

The scope is optional for a change that has no single home. A commit that changes code and
amends the design doc to match takes the code's scope; the design doc asks for both in one
commit.

Mark a breaking change with `!` and say what broke in a footer. The IR's JSON form is an
interface other tools read, so a change to it counts even before 1.0:

```
feat(core)!: rename Scenario.seed to rng_seed

BREAKING CHANGE: IR JSON written by earlier versions no longer loads.
```

No merge, fixup or WIP commits on a branch you open a pull request from; squash those locally
first. No AI co-author or generated-by trailers.

## Branches

[Conventional Branch 1.1.0](https://conventionalbranch.org/): `<type>/<description>`, lowercase
letters, digits and single hyphens.

That spec has fewer types than the commit spec. The mapping:

| work | branch prefix |
|---|---|
| `feat` commits | `feat/` |
| `fix` commits | `fix/` |
| `build` `ci` `docs` `test` `refactor` `style` `chore` | `chore/` |
| urgent fix to a release | `hotfix/` |
| release preparation | `release/` (dots allowed for the version) |

Put the milestone in the description: `feat/m0-ir-json-roundtrip`.

## Pull requests

One concern per pull request. `main` is linear: rebase your branch on `origin/main` before
opening the pull request, and merge by rebase. Every commit lands on `main` as written, which is
why each one is checked.

The `conventions` CI job checks the branch name, that the branch sits on top of `origin/main`,
and every commit message in the pull request. The rules live in `cchk.toml`; the same file
drives the local hooks.

Repository settings that back this up (set by a maintainer, not by this repo): require the
`lint`, `types`, `test`, `lock` and `conventions` checks on `main`, require linear history, and
allow only rebase merging.
