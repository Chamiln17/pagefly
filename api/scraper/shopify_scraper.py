import asyncio
import functools
import ipaddress
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, TypedDict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScrapeError(Exception):
    """The URL is not a public address, or neither the product JSON nor the product
    page gave enough product data."""


class ScrapedProduct(TypedDict):
    product_name: str
    product_price: float
    currency: str
    images: list[str]


Resolver = Callable[[str], Awaitable[list[str]]]


async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    """FastAPI dependency: the HTTP client the scraper fetches the shop with."""
    async with httpx.AsyncClient() as client:
        yield client


async def resolve_host(host: str) -> list[str]:
    """Every address DNS gives for `host`."""
    infos = await asyncio.get_running_loop().getaddrinfo(host, None)
    return [str(info[4][0]) for info in infos]


def host_resolver() -> Resolver:
    """FastAPI dependency: how the scraper resolves a shop's host name."""
    return resolve_host


async def scrape_shopify_data(
    url: str, client: httpx.AsyncClient, resolve: Resolver
) -> ScrapedProduct:
    """Read Shopify's public product JSON; fall back to the product page HTML.
    Refuses (ScrapeError) any URL or redirect whose host is not a public address."""
    product_url = httpx.URL(url)
    json_url = product_url.copy_with(
        path=product_url.path.rstrip("/") + ".json", query=None
    )
    get = functools.partial(_get, client, resolve)
    product = await _get_json_product(get, json_url, product_url.params.get("variant"))
    try:
        html = (await get(product_url)).content
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
    get: Callable[[httpx.URL], Awaitable[httpx.Response]],
    json_url: httpx.URL,
    variant_id: str | None,
) -> dict[str, Any]:
    """Map Shopify's `<product url>.json`; empty dict when unusable. The price is
    the variant `variant_id` names, else the first variant's."""
    try:
        response = await get(json_url)
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


async def _get(
    client: httpx.AsyncClient, resolve: Resolver, url: httpx.URL
) -> httpx.Response:
    """GET `url`, following redirects by hand so every hop is checked to be public."""
    for _ in range(client.max_redirects + 1):
        await _require_public(url, resolve)
        response = await client.get(url, follow_redirects=False)
        if response.next_request is None:
            return response
        url = response.next_request.url
    raise httpx.TooManyRedirects("Too many redirects.", request=response.request)


async def _require_public(url: httpx.URL, resolve: Resolver) -> None:
    """Raise ScrapeError unless `url` is http(s) and every address of its host is
    globally routable.
    ponytail: the client resolves the host again when it connects, so DNS rebinding
    between this check and the connect gets through; pin the checked address in a
    custom transport if that matters."""
    if url.scheme not in ("http", "https"):
        raise ScrapeError(f"Refusing to fetch {url}: only http and https are allowed.")
    try:
        addresses = [ipaddress.ip_address(url.host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(a) for a in await resolve(url.host)]
        except OSError as exc:
            raise ScrapeError(f"Cannot resolve {url.host}: {exc}") from exc
    if not addresses or any(not a.is_global or a.is_multicast for a in addresses):
        raise ScrapeError(f"Refusing to fetch {url.host}: not a public address.")


def _page_currency(html: bytes) -> str | None:
    """The ISO currency Shopify themes publish in `og:price:currency`."""
    tag = BeautifulSoup(html, "html.parser").select_one(
        'meta[property="og:price:currency"]'
    )
    content = tag.get("content") if tag else None
    return content if isinstance(content, str) and content else None


def _from_html(html: bytes) -> dict[str, Any]:
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
