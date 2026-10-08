"""The smoke script's run path, with fakes injected in place of real providers."""

import json

from langchain_core.messages import AIMessage

from fakes import fake_llm, make_fake_search
from scripts.smoke_run import IMAGE_URL, run_smoke

IMG = f"<img src='{IMAGE_URL}' alt='Coffee mug'>"
HTML = (
    f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section>"
    "<section id='features'></section><section id='cta'></section></body></html>"
)
COPY = {"sections": [{"id": "hero", "type": "hero", "copy": {"headline": "Hi"}}]}


def reply(content, tokens_in, tokens_out, cost=None):
    # ChatOpenAI copies the provider's raw `usage` (OpenRouter adds `cost`) into
    # response_metadata["token_usage"]; usage_metadata keeps token counts only.
    token_usage = {"prompt_tokens": tokens_in, "completion_tokens": tokens_out}
    if cost is not None:
        token_usage["cost"] = cost
    return AIMessage(
        content=content,
        response_metadata={"model_name": "fake/model", "token_usage": token_usage},
        usage_metadata={
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
        },
    )


def test_smoke_run_writes_html_and_reports_route_check_and_tokens(tmp_path):
    search, queries = make_fake_search()
    llm = fake_llm(
        reply('{"visual_summary": "A mug."}', 100, 10),
        reply(json.dumps(COPY), 200, 20),
        reply(HTML, 300, 30),
    )
    out = tmp_path / "page.html"

    summary = run_smoke(llm, search, angle="Always hot", out_path=out)

    assert queries == []
    assert out.read_text(encoding="utf-8") == HTML
    assert "route: skip_research" in summary
    assert "check: passed" in summary
    assert "repair passes: 0" in summary
    assert "fake/model: input 600, output 60, total 660" in summary


def test_smoke_run_without_angle_takes_research_route(tmp_path):
    search, queries = make_fake_search()
    llm = fake_llm(
        '{"visual_summary": "A mug."}',
        '{"recommended_angle": {"angle": "Always hot"}}',
        json.dumps(COPY),
        HTML,
    )

    summary = run_smoke(llm, search, angle=None, out_path=tmp_path / "page.html")

    assert "route: run_research" in summary
    assert "tokens: none reported" in summary


def test_smoke_run_reports_a_repair_pass(tmp_path):
    search, _ = make_fake_search()
    broken = (
        f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section></body></html>"
    )
    llm = fake_llm('{"visual_summary": "A mug."}', json.dumps(COPY), broken, HTML)

    summary = run_smoke(llm, search, angle="Always hot", out_path=tmp_path / "p.html")

    assert "check: passed" in summary
    assert "repair passes: 1" in summary


def test_smoke_run_sums_provider_reported_cost(tmp_path):
    search, _ = make_fake_search()
    llm = fake_llm(
        reply('{"visual_summary": "A mug."}', 100, 10, cost=0.001),
        reply(json.dumps(COPY), 200, 20, cost=0.002),
        reply(HTML, 300, 30, cost=0.0035),
    )

    summary = run_smoke(llm, search, angle="Always hot", out_path=tmp_path / "p.html")

    assert "cost: 0.006500" in summary


def test_smoke_run_says_cost_not_reported_when_provider_omits_it(tmp_path):
    search, _ = make_fake_search()
    llm = fake_llm(
        reply('{"visual_summary": "A mug."}', 100, 10),
        reply(json.dumps(COPY), 200, 20),
        reply(HTML, 300, 30),
    )

    summary = run_smoke(llm, search, angle="Always hot", out_path=tmp_path / "p.html")

    assert "cost: not reported" in summary


def test_smoke_run_passes_language_to_the_copywriter(tmp_path):
    search, _ = make_fake_search()
    llm = fake_llm('{"visual_summary": "A mug."}', json.dumps(COPY), HTML)

    run_smoke(
        llm, search, angle="Always hot", out_path=tmp_path / "p.html", language="fr"
    )

    copywriter_prompt = llm.prompts[1][0].content
    assert "Write in the target language: **fr**" in copywriter_prompt
