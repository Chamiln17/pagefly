"""The smoke script's run path, with fakes injected in place of real providers."""

import json

from langchain_core.messages import AIMessage

from fakes import fake_llm, make_fake_search
from scripts.smoke_run import run_smoke

HTML = (
    "<!DOCTYPE html><html><body><section id='hero'>Hi</section>"
    "<section id='features'></section><section id='cta'></section></body></html>"
)
COPY = {"sections": [{"id": "hero", "type": "hero", "copy": {"headline": "Hi"}}]}


def reply(content, tokens_in, tokens_out):
    return AIMessage(
        content=content,
        response_metadata={"model_name": "fake/model"},
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
