# Contributing to `handy`

First off — thank you for considering a contribution. This project aims to stay
small, dependency-free, and boring in the best way.

## Code of Conduct

By participating, you agree to uphold the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Getting started

```bash
# 1. Fork and clone your fork
git clone https://github.com/<you>/handy.git
cd handy

# 2. Create an isolated environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install in editable mode (no third-party runtime deps)
python -m pip install -e .

# 4. Run the test suite (standard library only)
make test
# or: python -m unittest discover -s tests -v
```

## Making changes

- Keep scope tight: one logical change per pull request.
- Add or extend tests under `tests/` using the standard-library `unittest`
  module (the project deliberately avoids a test-framework dependency).
- Preserve the **zero runtime dependency** guarantee. New features must use
  only the Python standard library.
- Add type hints and concise docstrings to every public symbol.
- Update `CHANGELOG.md` under the `Unreleased` heading.
- Run `make lint` before pushing.

## Commit & PR guidelines

- Write clear, imperative commit messages ("Add token-bucket limiter").
- Fill in the pull-request template; link the related issue with
  `Closes #<n>` when applicable.
- Ensure the CI workflow is green before requesting review.

## Reporting bugs & ideas

Use the issue templates (`bug_report`, `feature_request`) so we capture the
details needed to help you quickly. For security-sensitive reports, follow
[SECURITY.md](SECURITY.md) instead of opening a public issue.

## Releasing

Maintainers cut releases via git tags (`vX.Y.Z`). The CI workflow builds and
publishes to PyPI on tagged pushes.
