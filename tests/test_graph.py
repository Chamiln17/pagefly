import json

from langchain_core.messages import AIMessage

from fakes import fake_llm, make_fake_search
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
HTML = (
    "<!DOCTYPE html><html><body><section id='hero'>Hot coffee</section></body></html>"
)


def initial_state(angle=None):
    return {
        "product_name": "Smart Mug",
        "product_image_urls": ["https://example.com/mug.jpg"],
        "marketing_angle_input": angle,
        "fixed_layout_input": LAYOUT,
        "language": "en",
    }


def test_marketing_angle_given_skips_research():
    search, queries = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, json.dumps(COPY), HTML)

    state = create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    assert queries == []
    assert state.get("marketing_strategy") is None
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
    assert state["marketing_strategy"] == research_answer["recommended_angle"]
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
    assert state["marketing_strategy"] == {"angle": "Always hot"}
    assert state["generated_copy"] == COPY
    assert state["generated_html"] == HTML


def test_failing_copywriter_makes_html_generation_skip():
    search, _ = make_fake_search()
    llm = fake_llm(IMAGE_REPLY, "Sorry, I cannot write copy today.", HTML)

    state = create_graph(llm, search).invoke(initial_state("Never drink cold coffee"))

    assert "error" in state["generated_copy"]
    assert state["error_message"]
    assert state["generated_html"] != HTML
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
