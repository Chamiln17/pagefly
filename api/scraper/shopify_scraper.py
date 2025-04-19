from typing import Dict
from bs4 import BeautifulSoup
import httpx
from apify import Actor

async def scrape_shopify_data(url: str, marketing_angle : str) -> Dict:
    await Actor.init()  # initialize Actor tools (logging, input, etc.)

    async with httpx.AsyncClient() as client:
        response = await client.get(str(url))

    soup = BeautifulSoup(response.content, 'html.parser')

     # Extract product title
    title_tag = soup.select_one("h1") or soup.select_one("h1.product-title")
    product_name = title_tag.text.strip() if title_tag else None

    #  Extract price and compare at price (with currency symbols)
    price_tag = soup.select_one("#ProductPrice, .product__price, [itemprop=price]")
    compare_tag = soup.select_one("#ComparePrice span.money, .compare-price, [id*=Compare] span")

    price_raw = price_tag.text.strip() if price_tag else None
    compare_raw = compare_tag.text.strip() if compare_tag else None

    # 🧽Detect currency symbol
    currency_symbol = ""
    for symbol in ["$", "€", "دج", "DA"]:
        if price_raw and symbol in price_raw:
            currency_symbol = symbol
            break

    currency = {
        "$": "USD",
        "€": "EUR",
        "دج": "DZD",
        "DA": "DZD"
    }.get(currency_symbol, "USD")  # default fallback

    # 🧹 Clean price strings to float
    def clean_price(p: str | None) -> float | None:
        if not p:
            return None
        return float("".join(c for c in p if c.isdigit() or c == "."))

    product_price = clean_price(price_raw)
    compare_at_price = clean_price(compare_raw)

    # Limit to 6 valid image URLs
     # 🖼️ Extract high-quality product images (prefer "products" in URL)
    images = []
    media_wrappers = soup.select("img, source")

    for tag in media_wrappers:
        src = tag.get("src") or tag.get("data-src") or tag.get("data-srcset")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            if src.startswith("http") and "products" in src:
                images.append(src)
        if len(images) >= 6:
            break

    # Remove duplicates
    images = list(dict.fromkeys(images))

    return {
        "product_name": product_name,
        "product_price": product_price,
        "compare_at_price": compare_at_price,
        "currency": currency,
        "images": images,
        "marketing_angle": marketing_angle
    }