# Contributing

Thanks for your interest in PageFly. Bug reports, fixes and small improvements are welcome.

## Before you start

- For anything bigger than a small fix, open an issue first so we can agree on the approach.
- Report security problems privately, as described in [SECURITY.md](SECURITY.md).
- Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

PageFly uses [uv](https://docs.astral.sh/uv/) for everything.

```shell
uv sync --all-extras --dev
```

Copy `.env.example` to `.env` only if you want to make real model calls (the smoke script). The tests never need keys.

## Checks

These are the checks CI runs. Run them before you open a pull request:

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv lock --check
```

## Writing code

- Read [CODING_STANDARDS.md](CODING_STANDARDS.md) and use the vocabulary in [GLOSSARY.md](GLOSSARY.md).
- Write tests against the agent graph or the HTTP API with the fake models in `tests/`. Tests must run offline with no API keys.
- A change to an agent prompt should come with one real smoke run (`uv run python -m scripts.smoke_run`). Say in the pull request what it showed and what it cost.
- Add dependencies with `uv add`, never by editing the lock file by hand.

## Pull requests

- Keep one logical change per pull request, with a short description of what changed and why.
- CI must be green before a merge.
