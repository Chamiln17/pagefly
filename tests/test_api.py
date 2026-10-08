import importlib
import json

import pytest
from fastapi.testclient import TestClient

import api.main
from api.generator import SECTIONS, get_graph
from api.storage import page_store
from fakes import fake_llm, make_fake_search
from workflow.graph import create_graph

IMAGE_REPLY = '{"visual_summary": "A black smart mug on a desk."}'
COPY = {
    "sections": [{"id": "hero", "type": "hero", "copy": {"headline": "Hot coffee"}}]
}
HTML = "<!DOCTYPE html><html><body><section id='hero'>Hot</section></body></html>"


def request_body(**overrides):
    body = {
        "images": ["https://example.com/mug.jpg"],
        "product_name": "Smart Mug",
        "product_price": 4500,
        "currency": "DZD",
        "marketing_angle": "Never drink cold coffee",
    }
    return body | overrides


@pytest.fixture
def client():
    page_store.clear()
    yield TestClient(api.main.app)
    api.main.app.dependency_overrides.clear()
    page_store.clear()


def use_graph(*replies):
    """Serve a graph built on a fake model scripted with `replies`; return the model."""
    llm = fake_llm(*replies)
    search, _ = make_fake_search()
    graph = create_graph(llm, search)
    api.main.app.dependency_overrides[get_graph] = lambda: graph
    return llm


def prompt_containing(llm, marker):
    return next(
        "\n".join(str(m.content) for m in p) for p in llm.prompts if marker in str(p)
    )


def copywriter_prompt(llm):
    return prompt_containing(llm, "copywriter")


def coder_prompt(llm):
    return prompt_containing(llm, "expert frontend developer")


def layout_ids(llm):
    prompt = copywriter_prompt(llm)
    layout = prompt.split("Required Landing Page Structure")[1].split("```json")[1]
    return [s["id"] for s in json.loads(layout.split("```")[0])["sections"]]


def test_switches_produce_the_matching_sections(client):
    llm = use_graph(IMAGE_REPLY, json.dumps(COPY), HTML)

    client.post(
        "/generate", json=request_body(is_hero=True, is_pricing=True, is_footer=True)
    )

    assert layout_ids(llm) == ["hero", "pricing", "footer"]


def test_request_fields_reach_the_graph(client):
    llm = use_graph(IMAGE_REPLY, json.dumps(COPY), HTML)

    client.post("/generate", json=request_body(is_hero=True, language="fr"))

    image_prompt = str(llm.prompts[0])
    assert "https://example.com/mug.jpg" in image_prompt
    copy_prompt = copywriter_prompt(llm)
    assert "Never drink cold coffee" in copy_prompt
    assert "fr language" in copy_prompt
    assert "4500" in copy_prompt and "DZD" in copy_prompt
    html_prompt = coder_prompt(llm)
    assert "4500" in html_prompt and "DZD" in html_prompt


def test_language_defaults_to_arabic(client):
    llm = use_graph(IMAGE_REPLY, json.dumps(COPY), HTML)

    client.post("/generate", json=request_body(is_hero=True))

    assert "ar language" in copywriter_prompt(llm)


def test_success_returns_a_working_preview_link(client):
    use_graph(IMAGE_REPLY, json.dumps(COPY), HTML)

    response = client.post("/generate", json=request_body(is_hero=True))

    assert response.status_code == 200
    preview = client.get(response.json()["preview_url"])
    assert preview.status_code == 200
    assert preview.text == HTML


def test_graph_error_returns_502_and_stores_nothing(client):
    use_graph(IMAGE_REPLY, "Sorry, I cannot write copy today.")

    response = client.post("/generate", json=request_body(is_hero=True))

    assert response.status_code == 502
    assert response.json()["detail"] == "Error reported in generated_copy."
    assert page_store == {}


def test_failing_page_check_returns_502_and_stores_nothing(client):
    use_graph(IMAGE_REPLY, json.dumps(COPY), HTML)

    response = client.post(
        "/generate", json=request_body(is_hero=True, is_pricing=True)
    )

    assert response.status_code == 502
    assert "pricing" in response.json()["detail"]
    assert page_store == {}


def test_scrape_shopify_generates_through_the_graph(client, monkeypatch):
    async def fake_scrape(url):
        return {
            "product_name": "Smart Mug",
            "product_price": 4500.0,
            "currency": "DZD",
            "images": ["https://example.com/mug.jpg"],
        }

    monkeypatch.setattr("api.routes.scrape_shopify_data", fake_scrape)
    full_page = "<!DOCTYPE html><html><body>%s</body></html>" % "".join(
        f"<section id='{s['id']}'></section>" for s in SECTIONS.values()
    )
    llm = use_graph(IMAGE_REPLY, json.dumps(COPY), full_page)

    response = client.post(
        "/scrape-shopify",
        json={"url": "https://shop.example.com/p", "marketing_angle": "Stay warm"},
    )

    assert response.status_code == 200
    assert client.get(response.json()["preview_url"]).text == full_page
    assert "Stay warm" in copywriter_prompt(llm)


def preflight(app, origin):
    return TestClient(app).options(
        "/generate",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_cors_allows_only_the_default_localhost_origins(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    app = importlib.reload(api.main).app

    assert preflight(app, "http://localhost:5173").status_code == 200
    assert preflight(app, "https://evil.example").status_code == 400


def test_cors_origins_come_from_env(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://shop.example, https://admin.example")
    app = importlib.reload(api.main).app

    assert preflight(app, "https://admin.example").status_code == 200
    assert preflight(app, "http://localhost:3000").status_code == 400
