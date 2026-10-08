# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Python backend that generates single-file HTML landing pages for e-commerce products using a LangGraph pipeline of OpenAI (`gpt-4o`) agents, plus a FastAPI service that serves the generated pages. Generated copy is often Arabic/RTL (the target market prices in DZD). The root `README.md` describes the original plan (layout researcher → coder → evaluator); the code has since moved to a different agent chain, described below.

## Commands

Uses `uv` (Python pinned to 3.13 in `.python-version`; `pyproject.toml` requires >=3.11).

```shell
uv sync --all-extras --dev          # install incl. dev tools
uv run ruff check --fix && uv run ruff format
uv run mypy .
uv run pytest                        # no pytest tests exist yet
uv run pytest path/to/test_x.py::test_name   # single test

uv run uvicorn api.main:app --reload # API server
uv run python -m workflow.graph      # compile + run full graph on a sample product (makes real API calls)
uv run python -m agents.coder_agent  # most agent modules have a __main__ smoke test
```

Run everything from the repo root; modules import each other as top-level packages (`core`, `agents`, `workflow`, `api`).

## Environment

`.env` (loaded via `python-dotenv`) needs `OPENAI_API_KEY`, and `TAVILY_API_KEY` for the marketing research agent. `.env.example` only lists Azure OpenAI vars, which the graph does not use.

Several imports are not declared in `pyproject.toml` and must be installed separately: `apify` and `beautifulsoup4` (api), `langchain-community` (Tavily tool), `IPython` (imported at top of `workflow/graph.py`).

## Architecture

**Agent pipeline** (`workflow/graph.py`, state in `core/state.py`):

```
image_analyzer ──(marketing_angle_input set?)──yes──▶ copywriter ─▶ html_generator ─▶ END
                                   └──no──▶ marketing_researcher ─┘
```

- `PageState` (TypedDict) is the single contract between nodes. Inputs: `product_name`, `product_image_urls`, `marketing_angle_input`, `fixed_layout_input` (a dict with `sections` and optional `inspiration_image`), `language`. Outputs: `product_image_descriptions`, `marketing_strategy`, `generated_copy`, `generated_html`, `error_message`.
- Each `agents/*_agent.py` exposes a `get_*_runnable(llm)` factory returning a LangChain runnable that takes the whole state dict. `create_graph()` builds them into **module-level globals** that the node functions read; it ignores the `llm` argument and builds its own `ChatOpenAI` instances.
- Error handling convention: nodes catch exceptions and write `error_message`; downstream nodes skip when `error_message` is set (and the HTML node also skips when `generated_copy` contains an `error` key).
- The layout is fixed and user-supplied (`fixed_layout_input`); the copywriter fills the required copy per section, and the coder turns layout + copy + image descriptions into HTML.
- `agents/layout_agent.py` is from the older design and is not wired into the graph. `evaluation_agent.py` and `suggestion_agent.py` are empty placeholders.

**API** (`api/`):
- `POST /generate` (body `LandingPageParams`) and `POST /scrape-shopify` (scrapes a product URL, then generates) store HTML in the in-memory dict `api/storage.page_store` and return `{"preview_url": "/preview/<key>"}`; `GET /preview/{key}` serves it.
- `api/generator.generate_landing_page()` currently returns a **hardcoded sample HTML page**; it is the intended bridge to the agent graph but is not connected yet. `LandingPageParams` fields (`images`, `is_hero`, …) also do not map 1:1 onto `PageState`.
- `api/main.py` calls `apify.Actor.init()/exit()` in the FastAPI lifespan.

**Stale / scratch files:** `main.py` (root CLI) predates the current `PageState` and calls fields that no longer exist; `test_openai.py`, `test.azure.py`, `agents/tempCodeRunnerFile.py`, and the root `*.html` files are ad-hoc scratch outputs, not a test suite.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `Chamiln17/Astro-Page-Agents`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
