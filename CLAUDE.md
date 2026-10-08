# CLAUDE.md

PageFly backend: a LangGraph pipeline of LLM agents that writes single-file HTML landing pages, served by FastAPI. Read the code for the state fields and graph nodes (`core/state.py`, `workflow/graph.py`).

## Commands

Uses `uv` only. Run from the repo root.

```shell
uv sync --all-extras --dev
uv run pytest                                  # offline, no keys needed
uv run pytest tests/test_graph.py::test_name   # single test
uv run ruff check . && uv run ruff format --check .
uv run mypy .                                  # not gating
uv lock --check                                # uv.lock matches pyproject.toml
uv run --env-file .env uvicorn api.main:app    # API
uv run python scripts/smoke_run.py --help      # real run makes PAID calls; never run it without authorisation
```

CI (`.github/workflows/ci.yml`) runs sync, lock check, pytest and both ruff checks on every push and pull request.

## Environment gotchas

- The API does not load `.env`; start it with `--env-file .env`. Variables are listed in `.env.example`.
- In a sandboxed session pytest's default temp dir may be denied; pass `--basetemp <writable dir>`.

## Error convention

Agents raise on failure and never return placeholder output. `guarded()` in `workflow/graph.py` wraps every node except `finish`, turns the exception into `error_message = "Error in <Node>: ..."`, and skips the node when `error_message` is already set. `finish` turns remaining `check_problems` into `error_message`.

## Further reading

- `GLOSSARY.md`: domain vocabulary.
- `CODING_STANDARDS.md`: review rules.
- `docs/agents/`: issue tracker, triage labels, domain docs.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `Chamiln17/Astro-Page-Agents`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
