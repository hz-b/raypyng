# Contributing

This project uses a simple Git workflow:

- `main` is the stable branch.
- `develop` is the integration branch.
- feature work happens on dedicated branches created from `develop`.
- feature branches are merged into `develop`.
- releases are made by merging `develop` into `main` and creating a tag on `main`.
- notable user-facing changes should be recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Branch Strategy

Use these branch roles consistently:

- `main`: stable, release-ready history
- `develop`: ongoing integration branch for upcoming work
- `feature/<name>`: one feature or focused change per branch

For normal work:

1. update your local `develop`
2. create a new feature branch from `develop`
3. open the pull request back into `develop`

## Local Setup

raypyng uses `uv` for local development.

On Linux or macOS:

```bash
./tools/bootstrap.sh
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\tools\bootstrap_windows.ps1
.\.venv\Scripts\Activate.ps1
```

If you prefer to set up the environment manually:

```bash
uv venv --python 3.12
uv pip install -e '.[dev]'
```

## Development Workflow

Typical feature workflow:

1. start from the latest `develop`
2. create a dedicated feature branch, for example `feature/my-change`
3. make the code and documentation changes
4. run the relevant tests and local checks
5. update [`CHANGELOG.md`](CHANGELOG.md) if the change is user-visible
6. push the branch and open a pull request into `develop`

Keep pull requests focused. Smaller PRs are easier to review and safer to merge.

## Tests and Local Checks

Before opening a pull request, run the checks relevant to your change.

Common setup:

```bash
uv pip install -e '.[dev]'
pre-commit run --all-files
```

Common test commands:

```bash
uv run --python 3.12 pytest tests/unit
uv run --python 3.12 pytest -m "not requires_ray_ui"
```

Additional test commands are documented in [`tests/test.md`](tests/test.md), including:

- smoke tests
- platform tests
- functional regression tests that require local RAY-UI installations

GitHub Actions also runs CI-safe tests on pushes and pull requests targeting `develop`.

## Changelog

Update [`CHANGELOG.md`](CHANGELOG.md) when your change is relevant to users, contributors, or project behavior.

This usually includes:

- new features
- bug fixes
- behavior changes
- testing or workflow changes that contributors should know about
- documentation changes when they reflect a meaningful workflow update

Purely local refactors or internal cleanup can usually be omitted if they do not affect users or contributors.

## Releases

The release flow is:

1. integrate completed work into `develop`
2. make sure the relevant changelog entries are present
3. merge `develop` into `main`
4. create the release tag on `main`

`main` should always reflect stable, releasable project history.
