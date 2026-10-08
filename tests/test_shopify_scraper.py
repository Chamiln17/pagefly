"""The Shopify scraper against saved responses served by httpx.MockTransport."""

import asyncio
from pathlib import Path

import httpx
import pytest

from api.scraper.shopify_scraper import ScrapeError, scrape_shopify_data

FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT_JSON = (FIXTURES / "shopify_product.json").read_bytes()
PRODUCT_HTML = (FIXTURES / "shopify_product.html").read_bytes()
URL = "https://shop.example.com/products/smart-mug?variant=808950810"


async def resolve_public(host):
    return ["93.184.215.14"]


def scrape(routes, url=URL):
    """Run the scraper; `routes` maps a request path to (status, body)."""

    def handler(request):
        status, body = routes.get(request.url.path, (404, b"Not Found"))
        return httpx.Response(status, content=body)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await scrape_shopify_data(url, client, resolve_public)

    return asyncio.run(run())


def test_product_json_gives_name_price_currency_and_six_images():
    scraped = scrape(
        {
            "/products/smart-mug.json": (200, PRODUCT_JSON),
            "/products/smart-mug": (200, PRODUCT_HTML),
        }
    )

    assert scraped == {
        "product_name": "Smart Mug",
        "product_price": 4500.0,
        "currency": "DZD",
        "images": [
            f"https://cdn.shopify.com/s/files/1/0001/products/mug-{n}.jpg"
            for n in range(1, 7)
        ],
    }


@pytest.mark.parametrize(
    ("query", "price"),
    [("?variant=808950811", 4700.0), ("?variant=999", 4500.0), ("", 4500.0)],
)
def test_price_is_the_variant_in_the_url_else_the_first_variant(query, price):
    scraped = scrape(
        {"/products/smart-mug.json": (200, PRODUCT_JSON)},
        url="https://shop.example.com/products/smart-mug" + query,
    )

    assert scraped["product_price"] == price


def test_json_404_falls_back_to_the_product_page_html():
    scraped = scrape({"/products/smart-mug": (200, PRODUCT_HTML)})

    assert scraped == {
        "product_name": "Smart Mug",
        "product_price": 4500.0,
        "currency": "DZD",
        "images": [
            "https://shop.example.com/cdn/shop/products/mug-front.jpg",
            "https://shop.example.com/cdn/shop/products/mug-side.jpg",
        ],
    }


def test_json_and_html_both_failing_raises():
    with pytest.raises(ScrapeError):
        scrape({"/products/smart-mug": (200, b"<html><body>Sold out</body></html>")})
