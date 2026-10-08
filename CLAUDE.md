# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Backend for PageFly: a LangGraph pipeline of LLM agents that generates single-file HTML landing pages for e-commerce products, plus a FastAPI service that runs it and serves the pages. Generated copy defaults to Arabic (`language="ar"`). No frontend in this repo.

## Commands

Uses `uv` only (Python pinned to 3.13 in `.python-version`). Run from the repo root; packages import each other as top-level modules (`core`, `agents`, `workflow`, `api`, `scripts`).

```shell
uv sync --all-extras --dev
uv run pytest                                  # offline, no keys needed
uv run pytest tests/test_graph.py::test_name   # single test
uv run ruff check . && uv run ruff format --check .
uv run mypy .                                  # not gating
uv run --env-file .env uvicorn api.main:app    # API; does not load .env itself
uv run python scripts/smoke_run.py --help      # real run makes PAID calls; never run it without authorisation
```

## Environment

See `.env.example`. `core/llm.py` builds the only chat model (`make_llm`, OpenAI-compatible: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_MAX_TOKENS`) and search tool (`make_search_tool`, Tavily, `TAVILY_API_KEY`). `CORS_ORIGINS` is read by `api/main.py`. Only `scripts/smoke_run.py` calls `load_dotenv()`.

## Architecture

**Graph** (`workflow/graph.py`, state `core/state.py`): `create_graph(llm, search_tool)` injects deps into node closures; no module globals.

```
image_analyzer -(no Marketing Angle)-> marketing_researcher -> copywriter
image_analyzer -(Marketing Angle given)-> copywriter
copywriter -> html_generator -> checker -(problems, repair_passes < 1)-> repairer -> checker
checker -> finish -> END
```

- `PageState` (TypedDict) is the contract between nodes. Inputs: `product_name`, `product_description`, `product_image_urls`, `marketing_angle`, `product_price`, `currency`, `fixed_layout_input` (`{"sections": [{id, type, required_copy, ...}]}`), `language`. Outputs: `product_image_descriptions`, `marketing_research`, `generated_copy`, `generated_html`, `check_problems`, `repair_passes`, `error_message`.
- Each `agents/*_agent.py` exposes a `get_*_runnable(llm[, search_tool])` factory. Prompts live in the agent modules.
- Error convention: agents raise on failure, never return placeholder output; `guarded()` wraps every node except `finish`, turns the exception into `error_message = "Error in <Node>: ..."`, and skips the node when `error_message` is already set. `finish` turns remaining `check_problems` into `error_message`.
- `check_page` is deterministic: HTML parses, each layout section id exists, each `<img>` has alt text, and when the run has `product_image_urls` at least one of them is an `<img src>`. `MAX_REPAIR_PASSES = 1`.

**API** (`api/`):
- `generator.py`: `initial_state()` maps `LandingPageParams` to `PageState` (the `is_*` switches select sections from `SECTIONS`); `get_graph()` builds the real graph lazily and is a FastAPI dependency, so tests override it with fakes.
- `routes.py`: `POST /generate` and `POST /scrape-shopify` run the graph synchronously, store HTML in the in-memory `storage.page_store`, return `{"preview_url": "/preview/<key>"}`; graph error -> 502. `GET /preview/{key}` serves the page.
- `scraper/shopify_scraper.py`: httpx + BeautifulSoup, theme-specific selectors, untested.

**Tests** (`tests/`): `fakes.py` has `fake_llm(*replies)` (scripted, supports `bind_tools`, records prompts) and `make_fake_search()`. Tests assert final graph state and HTTP responses.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `Chamiln17/Astro-Page-Agents`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
