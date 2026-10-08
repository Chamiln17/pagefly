from typing import Dict
from bs4 import BeautifulSoup
import httpx


async def scrape_shopify_data(url: str) -> Dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(str(url))

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract product title
    title_tag = soup.select_one("h1.logo a[aria-label]")
    product_name = title_tag.get("aria-label") if title_tag else None
    print("titles++++555", product_name)

    #  Extract price and compare at price (with currency symbols)
    price_tag = soup.select_one(".product__price--regular")
    compare_tag = soup.select_one(".product__price--compare")
    print("titles++++555", price_tag, compare_tag)
    price_raw = None
    if price_tag:
        price_raw = price_tag.get_text(strip=True) or price_tag.get("content")
    # compare_raw = compare_tag.text.strip() if compare_tag else None
    print("titles++++555999", price_raw)

    # 🧽Detect currency symbol
    currency_symbol = ""
    for symbol in ["$", "€", "دج", "DA"]:
        if price_raw and symbol in price_raw:
            currency_symbol = symbol
            break

    currency = {"$": "USD", "€": "EUR", "دج": "DZD", "DA": "DZD"}.get(
        currency_symbol, "USD"
    )  # default fallback
    print("titles++++5uu", currency_symbol)

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
    # print("titles++++5uu", media_tags)

    for tag in media_tags:
        src = (
            tag.get("src")
            or tag.get("data-src")
            or tag.get("srcset")
            or tag.get("content")
        )
        print("titles++++5uu", src)
        if not src:
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
    print("titles++++5uu", images)

    return {
        "product_name": product_name,
        "product_price": product_price,
        "currency": currency,
        "images": images,
    }
