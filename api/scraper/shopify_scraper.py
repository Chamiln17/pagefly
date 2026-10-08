import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, TypedDict

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)


class ScrapeError(Exception):
    """Neither the product JSON nor the product page gave enough product data."""


class ScrapedProduct(TypedDict):
    product_name: str
    product_price: float
    currency: str
    images: list[str]


async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    """FastAPI dependency: the HTTP client the scraper fetches the shop with."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        yield client


async def scrape_shopify_data(url: str, client: httpx.AsyncClient) -> ScrapedProduct:
    """Read Shopify's public product JSON; fall back to the product page HTML."""
    product_url = httpx.URL(url)
    json_url = product_url.copy_with(
        path=product_url.path.rstrip("/") + ".json", query=None
    )
    product = await _get_json_product(
        client, json_url, product_url.params.get("variant")
    )
    try:
        html = (await client.get(product_url)).content
    except httpx.HTTPError as exc:
        logger.debug("product page request failed: %s", exc)
        html = b""

    if product:
        # Shopify's product JSON has no currency; take it from the page, else the
        # HTML extraction's USD default.
        product["currency"] = _page_currency(html) or "USD"
    else:
        product = _from_html(html)
    if not (product["product_name"] and product["product_price"] and product["images"]):
        raise ScrapeError("Insufficient product data extracted.")
    return ScrapedProduct(
        product_name=product["product_name"],
        product_price=product["product_price"],
        currency=product["currency"],
        images=product["images"],
    )


async def _get_json_product(
    client: httpx.AsyncClient, json_url: httpx.URL, variant_id: str | None
) -> Dict[str, Any]:
    """Map Shopify's `<product url>.json`; empty dict when unusable. The price is
    the variant `variant_id` names, else the first variant's."""
    try:
        response = await client.get(json_url)
        response.raise_for_status()
        product = response.json()["product"]
        variants = product["variants"]
        variant = next((v for v in variants if str(v["id"]) == variant_id), variants[0])
        scraped = {
            "product_name": product["title"],
            "product_price": float(variant["price"]),
            "images": [image["src"] for image in product["images"]][:6],
        }
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
        logger.debug("product JSON unusable, falling back to HTML: %r", exc)
        return {}
    return scraped if all(scraped.values()) else {}


def _page_currency(html: bytes) -> str | None:
    """The ISO currency Shopify themes publish in `og:price:currency`."""
    tag = BeautifulSoup(html, "html.parser").select_one(
        'meta[property="og:price:currency"]'
    )
    content = tag.get("content") if tag else None
    return content if isinstance(content, str) and content else None


def _from_html(html: bytes) -> Dict[str, Any]:
    """Reads name, price, currency and product images from the product page with
    CSS selectors tuned to a few Shopify themes; missing fields come back empty."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract product title
    title_tag = soup.select_one("h1.logo a[aria-label]")
    product_name = title_tag.get("aria-label") if title_tag else None
    logger.debug("product_name=%s", product_name)

    #  Extract price and compare at price (with currency symbols)
    price_tag = soup.select_one(".product__price--regular")
    compare_tag = soup.select_one(".product__price--compare")
    logger.debug("price_tag=%s compare_tag=%s", price_tag, compare_tag)
    price_raw = None
    if price_tag:
        content = price_tag.get("content")
        # `content` is single-valued, so bs4 always returns a str here
        price_raw = price_tag.get_text(strip=True) or (
            content if isinstance(content, str) else None
        )
    # compare_raw = compare_tag.text.strip() if compare_tag else None
    logger.debug("price_raw=%s", price_raw)

    # 🧽Detect currency symbol
    currency_symbol = ""
    for symbol in ["$", "€", "دج", "DA"]:
        if price_raw and symbol in price_raw:
            currency_symbol = symbol
            break

    currency = {"$": "USD", "€": "EUR", "دج": "DZD", "DA": "DZD"}.get(
        currency_symbol, "USD"
    )  # default fallback
    logger.debug("currency_symbol=%s", currency_symbol)

    # 🧹 Clean price strings to float
    def clean_price(p: str | None) -> float | None:
        if not p:
            return None
        return float("".join(c for c in p if c.isdigit() or c == "."))

    product_price = clean_price(price_raw)

    # Limit to 6 valid image URLs
    # 🖼️ Extract high-quality product images (prefer "products" in URL)
    images = []
    media_tags = soup.select("img, source")

    for tag in media_tags:
        src = (
            tag.get("src")
            or tag.get("data-src")
            or tag.get("srcset")
            or tag.get("content")
        )
        logger.debug("candidate image src=%s", src)
        # src/srcset/content are single-valued, so bs4 always returns a str here
        if not src or not isinstance(src, str):
            continue

        # Convert protocol-relative to https
        if src.startswith("//"):
            src = "https:" + src

        # Skip non-product images
        if any(
            skip in src.lower() for skip in ["flags", "icons", "logo", "svg", "avatar"]
        ):
            continue

        # Optional: Prioritize images with "products" or from Shopify CDN
        if "products" in src or "touchelab.com/cdn" in src or "mnml.la/cdn/shop" in src:
            images.append(src)

        if len(images) >= 6:
            break
    # Remove duplicates
    images = list(dict.fromkeys(images))
    logger.debug("images=%s", images)

    return {
        "product_name": product_name,
        "product_price": product_price,
        "currency": currency,
        "images": images,
    }
