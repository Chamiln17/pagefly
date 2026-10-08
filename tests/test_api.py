import importlib
import json
from pathlib import Path

import httpx
import pytest
from fakes import fake_llm, make_fake_search
from fastapi.testclient import TestClient

import api.main
from api.generator import SECTIONS, get_graph
from api.scraper.shopify_scraper import host_resolver, http_client
from api.storage import page_store
from workflow.graph import create_graph

FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT_JSON = (FIXTURES / "shopify_product.json").read_bytes()
PRODUCT_HTML = (FIXTURES / "shopify_product.html").read_bytes()
SHOP_URL = "https://shop.example.com/products/smart-mug?variant=808950811"
PUBLIC_IP = "93.184.215.14"
SHOP_IMAGE = "https://cdn.shopify.com/s/files/1/0001/products/mug-1.jpg"
IMAGE_REPLY = '{"visual_summary": "A black smart mug on a desk."}'
COPY = {
    "sections": [{"id": "hero", "type": "hero", "copy": {"headline": "Hot coffee"}}]
}
IMG = "<img src='https://example.com/mug.jpg' alt='Black smart mug'>"
HTML = f"<!DOCTYPE html><html><body><section id='hero'>{IMG}</section></body></html>"


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
    assert response.json()["detail"].startswith("Error in Copywriting Node")
    assert page_store == {}


def test_failing_page_check_returns_502_and_stores_nothing(client):
    # The repair agent hands the page back unchanged, so the check fails again.
    use_graph(IMAGE_REPLY, json.dumps(COPY), HTML, HTML)

    response = client.post(
        "/generate", json=request_body(is_hero=True, is_pricing=True)
    )

    assert response.status_code == 502
    assert "pricing" in response.json()["detail"]
    assert page_store == {}


def serve_shop(routes):
    """Point the real scraper at a fake shop; `routes` maps a path to (status, body),
    where a 3xx body is the redirect target. Returns the URLs the shop was asked for."""
    requested = []

    def handler(request):
        requested.append(str(request.url))
        status, body = routes.get(request.url.path, (404, b"Not Found"))
        if 300 <= status < 400:
            return httpx.Response(status, headers={"location": body.decode()})
        return httpx.Response(status, content=body)

    async def fake_shop_client():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            yield c

    api.main.app.dependency_overrides[http_client] = fake_shop_client
    resolve_hosts({"shop.example.com": [PUBLIC_IP]})
    return requested


def resolve_hosts(hosts):
    """Resolve host names from `hosts` (name -> addresses) instead of DNS."""

    async def resolve(host):
        return hosts[host]

    api.main.app.dependency_overrides[host_resolver] = lambda: resolve


def assert_refused(response, requested, llm):
    assert response.status_code == 422
    assert "not a public address" in response.json()["detail"]
    assert requested == []
    assert page_store == {}
    assert llm.prompts == []


@pytest.mark.parametrize(
    "host", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "[::1]", "[fd00::1]"]
)
def test_scrape_shopify_refuses_a_non_public_ip(client, host):
    requested = serve_shop({"/products/smart-mug": (200, PRODUCT_HTML)})
    llm = use_graph()

    response = client.post(
        "/scrape-shopify", json={"url": f"http://{host}/products/smart-mug"}
    )

    assert_refused(response, requested, llm)


def test_scrape_shopify_refuses_a_host_that_resolves_to_a_private_address(client):
    requested = serve_shop({"/products/smart-mug": (200, PRODUCT_HTML)})
    resolve_hosts({"intranet.example.com": [PUBLIC_IP, "192.168.1.10"]})
    llm = use_graph()

    response = client.post(
        "/scrape-shopify",
        json={"url": "https://intranet.example.com/products/smart-mug"},
    )

    assert_refused(response, requested, llm)


def test_scrape_shopify_refuses_a_redirect_to_a_private_address(client):
    internal = "http://127.0.0.1/products/smart-mug"
    requested = serve_shop(
        {
            "/products/smart-mug.json": (302, f"{internal}.json".encode()),
            "/products/smart-mug": (302, internal.encode()),
        }
    )
    llm = use_graph()

    response = client.post("/scrape-shopify", json={"url": SHOP_URL})

    assert_refused(response, [u for u in requested if "127.0.0.1" in u], llm)


def test_scrape_shopify_returns_422_when_scraping_finds_too_little(client):
    serve_shop({"/products/smart-mug": (200, b"<html><body>Sold out</body></html>")})
    llm = use_graph()

    response = client.post("/scrape-shopify", json={"url": SHOP_URL})

    assert response.status_code == 422
    assert response.json()["detail"] == "Insufficient product data extracted."
    assert page_store == {}
    assert llm.prompts == []


def test_scrape_shopify_returns_422_for_an_unsupported_currency(client):
    gbp_page = PRODUCT_HTML.replace(
        b'og:price:currency" content="DZD"', b'og:price:currency" content="GBP"'
    )
    serve_shop(
        {
            "/products/smart-mug.json": (200, PRODUCT_JSON),
            "/products/smart-mug": (200, gbp_page),
        }
    )
    llm = use_graph()

    response = client.post("/scrape-shopify", json={"url": SHOP_URL})

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Unsupported currency 'GBP': supported currencies are DZD, EUR, USD."
    )
    assert page_store == {}
    assert llm.prompts == []


def test_scrape_shopify_generates_through_the_graph(client):
    serve_shop(
        {
            "/products/smart-mug.json": (200, PRODUCT_JSON),
            "/products/smart-mug": (200, PRODUCT_HTML),
        }
    )
    shop_img = f"<img src='{SHOP_IMAGE}' alt='Black smart mug'>"
    sections = "".join(f"<section id='{s['id']}'></section>" for s in SECTIONS.values())
    full_page = f"<!DOCTYPE html><html><body>{shop_img}{sections}</body></html>"
    llm = use_graph(*[IMAGE_REPLY] * 6, json.dumps(COPY), full_page)

    response = client.post(
        "/scrape-shopify", json={"url": SHOP_URL, "marketing_angle": "Stay warm"}
    )

    assert response.status_code == 200
    assert client.get(response.json()["preview_url"]).text == full_page
    assert "Stay warm" in copywriter_prompt(llm)
    assert "4700.0 DZD" in coder_prompt(llm)


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
