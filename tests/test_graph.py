import json

from fakes import fake_llm, make_fake_search
from langchain_core.messages import AIMessage

from workflow.graph import create_graph

LAYOUT = {
    "sections": [
        {"id": "hero", "type": "hero", "required_copy": ["headline"]},
    ]
}
IMAGE_REPLY = '{"visual_summary": "A black smart mug on a desk."}'
COPY = {
    "sections": [{"id": "hero", "type": "hero", "copy": {"headline": "Hot coffee"}}]
}
IMG = "<img src='https://example.com/mug.jpg' alt='Black smart mug'>"
HTML = (
    f"<!DOCTYPE html><html><body><section id='hero'>{IMG}Hot coffee</section>"
    "</body></html>"
)


def initial_state(angle=None):
    return {
        "product_name": "Smart Mug",
        "product_image_urls": ["https://example.com/mug.jpg"],
        "marketing_angle": angle,
        "fixed_layout_input": LAYOUT,
        "language": "en",
    }


def test_marketing_angle_given_skips_research():
    search, queries = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), HTML)

    state = create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    assert queries == []
    assert state.get("marketing_research") is None
    assert state["generated_html"] == HTML
    assert not state.get("error_message")


def test_without_marketing_angle_research_runs_and_feeds_the_copywriter():
    search, queries = make_fake_search()
    research_answer = {
        "recommended_angle": {
            "angle": "Coffee that stays hot through every meeting",
            "target_demographic": "Office workers",
            "keywords": ["hot coffee"],
            "justification": "Competitors stress battery life.",
        }
    }
    llm = fake_llm(
        IMAGE_REPLY,
        AIMessage(
            content="",
            tool_calls=[
                {"name": search.name, "args": {"query": "smart mug"}, "id": "c1"}
            ],
        ),
        json.dumps(research_answer),
        json.dumps(COPY),
        HTML,
    )

    state = create_graph(llm, search).invoke(initial_state())

    assert queries == ["smart mug"]
    assert state["marketing_research"] == research_answer["recommended_angle"]
    copywriter_prompt = next(
        str(p[0].content) for p in llm.prompts if "copywriter" in str(p[0].content)
    )
    assert "Coffee that stays hot through every meeting" in copywriter_prompt
    assert state["generated_html"] == HTML
    assert not state.get("error_message")


def test_agent_replies_are_parsed_into_state():
    search, _ = make_fake_search()
    llm = fake_llm(
        IMAGE_REPLY,
        'Here is my answer: {"recommended_angle": {"angle": "Always hot"}} Hope it helps.',
        "```json\n" + json.dumps(COPY) + "\n```",
        HTML,
    )

    state = create_graph(llm, search).invoke(initial_state())

    assert state["product_image_descriptions"] == [
        {
            "image_url": "https://example.com/mug.jpg",
            "product": "Smart Mug",
            "description": IMAGE_REPLY,
            "image_url_analyzed": "https://example.com/mug.jpg",
        }
    ]
    assert state["marketing_research"] == {"angle": "Always hot"}
    assert state["generated_copy"] == COPY
    assert state["generated_html"] == HTML


def test_failing_copywriter_makes_html_generation_skip():
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, "Sorry, I cannot write copy today.", HTML)

    state = create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    assert not state.get("generated_copy")
    assert state["error_message"]
    assert not state.get("generated_html")
    assert not any(
        "expert frontend developer" in str(p[0].content) for p in llm.prompts
    )


def test_image_descriptions_reach_the_copywriter():
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), HTML)

    create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    copywriter_prompt = next(
        str(p[0].content) for p in llm.prompts if "copywriter" in str(p[0].content)
    )
    assert "A black smart mug on a desk." in copywriter_prompt


def test_product_images_and_their_descriptions_reach_the_html_generator():
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), HTML)

    create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    coder_prompt = next(
        "\n".join(str(m.content) for m in p)
        for p in llm.prompts
        if "expert frontend developer" in str(p[0].content)
    )
    assert "https://example.com/mug.jpg" in coder_prompt
    assert "A black smart mug on a desk." in coder_prompt
    assert "DO NOT create `<img>`" not in coder_prompt


TWO_SECTION_LAYOUT = {
    "sections": [
        {"id": "hero", "type": "hero", "required_copy": ["headline"]},
        {"id": "pricing", "type": "pricing", "required_copy": ["price_text"]},
    ]
}


def run_with_html(html):
    """Runs the graph on a page the repair agent hands back unchanged."""
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), html, html)
    state = initial_state("Never drink cold coffee") | {
        "fixed_layout_input": TWO_SECTION_LAYOUT
    }
    return create_graph(llm, search).invoke(state)


def test_check_passes_a_clean_page():
    html = (
        "<!DOCTYPE html><html><body>"
        f"<section id='hero'>{IMG}</section>"
        "<div id='pricing'>4500 DZD</div></body></html>"
    )

    state = run_with_html(html)

    assert state["check_problems"] == []
    assert not state.get("error_message")
    assert state["generated_html"] == html


def test_check_reports_a_missing_layout_section():
    state = run_with_html(
        f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section></body></html>"
    )

    assert state["check_problems"] == [
        "Layout section 'pricing' has no element with id=\"pricing\"."
    ]
    assert "pricing" in state["error_message"]


def test_check_reports_images_without_alt_text():
    state = run_with_html(
        "<!DOCTYPE html><html><body><section id='hero'>"
        f"{IMG}<img src='a.jpg'><img src='b.jpg' alt='  '></section>"
        "<section id='pricing'></section></body></html>"
    )

    assert state["check_problems"] == [
        '<img src="a.jpg"> has no alt text.',
        '<img src="b.jpg"> has no alt text.',
    ]
    assert state["error_message"]


def test_check_reports_a_page_without_a_product_image():
    state = run_with_html(
        "<!DOCTYPE html><html><body><section id='hero'>"
        "<img src='https://other.example/stock.jpg' alt='Stock photo'></section>"
        "<section id='pricing'></section></body></html>"
    )

    assert state["check_problems"] == [
        (
            "No product image shown: add an <img> whose src is one of: "
            "https://example.com/mug.jpg"
        )
    ]
    assert state["error_message"]


def test_check_needs_no_product_image_when_the_run_has_none():
    search, _ = make_fake_search()
    html = "<!DOCTYPE html><html><body><section id='hero'>Hi</section></body></html>"
    llm = fake_llm(json.dumps(COPY), html)

    state = create_graph(llm, search).invoke(
        initial_state("Never drink cold coffee") | {"product_image_urls": []}
    )

    assert state["check_problems"] == []
    assert not state.get("error_message")


CLEAN_TWO_SECTION_HTML = (
    "<!DOCTYPE html><html><body>"
    f"<section id='hero'>{IMG}</section>"
    "<div id='pricing'>4500 DZD</div></body></html>"
)


def test_html_agent_keeps_only_the_html_document_from_a_chatty_reply():
    # A real model wrapped the page in prose and a markdown fence (smoke run, #19).
    chatty = (
        "Here is the complete HTML document:\n```html\n"
        + CLEAN_TWO_SECTION_HTML
        + "\n```\n### Notes\nThe palette is warm and minimal."
    )

    state = run_with_html(chatty)

    assert state["generated_html"] == CLEAN_TWO_SECTION_HTML
    assert state["check_problems"] == []


def test_check_reports_text_after_an_unclosed_html_document():
    state = run_with_html(
        "<!DOCTYPE html><html><body>"
        f"<section id='hero'>{IMG}</section><div id='pricing'></div></body>"
        "\nNotes: the palette is warm."
    )

    assert state["check_problems"] == [
        "Text outside the HTML document: the page must end with </html>."
    ]
    assert state["error_message"]


def test_check_reports_html_that_does_not_parse():
    state = run_with_html("Sorry, I cannot build this page.")

    assert state["check_problems"] == ["HTML does not parse: no <html> element."]
    assert state["error_message"]


def test_check_is_skipped_after_an_earlier_error():
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, "Sorry, I cannot write copy today.")

    state = create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    assert "check_problems" not in state
    assert state["error_message"].startswith("Error in Copywriting Node")


BROKEN_HTML = (
    f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section></body></html>"
)
FIXED_HTML = (
    f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section>"
    "<section id='pricing'>4500 DZD</section></body></html>"
)


def run_with_replies(*replies):
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), *replies)
    state = initial_state("Never drink cold coffee") | {
        "fixed_layout_input": TWO_SECTION_LAYOUT
    }
    return create_graph(llm, search).invoke(state), llm


def repair_prompts(llm):
    return [p for p in llm.prompts if "repair" in str(p[0].content).lower()]


def test_broken_page_is_fixed_in_one_repair_pass():
    state, llm = run_with_replies(BROKEN_HTML, "```html\n" + FIXED_HTML + "\n```")

    assert state["generated_html"] == FIXED_HTML
    assert state["check_problems"] == []
    assert state["repair_passes"] == 1
    assert not state.get("error_message")
    [prompt] = repair_prompts(llm)
    assert BROKEN_HTML in str(prompt[1].content)
    assert "Layout section 'pricing' has no element" in str(prompt[1].content)


def test_clean_page_never_calls_repair():
    state, llm = run_with_replies(FIXED_HTML)

    assert repair_prompts(llm) == []
    assert not state.get("repair_passes")
    assert not state.get("error_message")


def test_page_still_broken_after_repair_ends_in_error_without_a_second_pass():
    state, llm = run_with_replies(BROKEN_HTML, BROKEN_HTML, FIXED_HTML)

    assert len(repair_prompts(llm)) == 1
    assert state["repair_passes"] == 1
    assert state["generated_html"] == BROKEN_HTML
    assert state["error_message"].startswith("Page check failed:")
    assert "pricing" in state["error_message"]


def test_failing_repair_agent_ends_the_run_with_an_error():
    # The scripted model has no reply left for the repair call, so it raises.
    state, _llm = run_with_replies(BROKEN_HTML)

    assert state["repair_passes"] == 1
    assert state["error_message"].startswith("Error in Repair Node")


def test_failing_html_agent_ends_the_run_without_check_or_repair():
    # The scripted model has no reply left for the HTML call, so it raises.
    state, llm = run_with_replies()

    assert state["error_message"].startswith("Error in HTML Generation Node")
    assert "check_problems" not in state
    assert repair_prompts(llm) == []
